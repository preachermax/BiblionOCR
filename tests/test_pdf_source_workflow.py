from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5 import QtCore as qtc
from PyQt5 import QtWidgets as qtw

from Core.engine import ProjectCreationEngine
from Core.project_database import load_project_database_record, project_metadata_database_path
from Core.source_documents import copy_pdf_source_readonly, find_project_pdf_source, project_pdf_source_path


ROOT_DIR = Path(__file__).resolve().parents[1]
RENDERER_PATH = ROOT_DIR / "ViewController" / "0-MainUI" / "helpers" / "qt_pdf_renderer.py"
HELPERS_DIR = ROOT_DIR / "ViewController" / "0-MainUI" / "helpers"
if str(HELPERS_DIR) not in sys.path:
    sys.path.insert(0, str(HELPERS_DIR))

from project_creation_wizard_dialog import ProjectCreationWizardDialog
from pdf_viewer_dialog import PdfViewerDialog, PdfViewerDock


class _DummyEventBus:
    def emit(self, _event):
        return None


def _create_test_pdf(pdf_path: Path) -> None:
    script = """
import os
from PyQt6 import QtGui
app = QtGui.QGuiApplication([])
writer = QtGui.QPdfWriter(os.environ['PDF_PATH'])
painter = QtGui.QPainter(writer)
painter.drawText(100, 100, 'Page one')
writer.newPage()
painter.drawText(100, 100, 'Page two')
painter.end()
"""
    environment = dict(os.environ, PDF_PATH=str(pdf_path), QT_QPA_PLATFORM="offscreen")
    subprocess.run([sys.executable, "-c", script], check=True, env=environment)


def test_qtpdf_renderer_reports_and_renders_pages(tmp_path) -> None:
    pdf_path = tmp_path / "source.pdf"
    output_path = tmp_path / "page.png"
    _create_test_pdf(pdf_path)

    metadata_result = subprocess.run(
        [sys.executable, str(RENDERER_PATH), "metadata", str(pdf_path)],
        check=True,
        capture_output=True,
        text=True,
        env=dict(os.environ, QT_QPA_PLATFORM="offscreen"),
    )
    metadata = json.loads(metadata_result.stdout)
    assert metadata["page_count"] == 2

    subprocess.run(
        [sys.executable, str(RENDERER_PATH), "render", str(pdf_path), "1", "800", str(output_path)],
        check=True,
        env=dict(os.environ, QT_QPA_PLATFORM="offscreen"),
    )
    assert output_path.stat().st_size > 0


def test_pdf_viewer_renders_and_navigates_pages(tmp_path) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    pdf_path = tmp_path / "source.pdf"
    _create_test_pdf(pdf_path)

    viewer = PdfViewerDialog(str(pdf_path))

    assert viewer.page_count == 2
    assert viewer.page_index == 0
    assert viewer.page_label.pixmap() is not None
    assert not viewer.page_label.pixmap().isNull()
    assert not viewer.previous_button.isEnabled()
    assert viewer.next_button.isEnabled()

    viewer.zoom_in()
    assert viewer.zoom_percent == 125
    assert not viewer.fit_width
    assert viewer.page_label.pixmap().width() == 1000

    viewer.zoom_out()
    assert viewer.zoom_percent == 100
    assert viewer.page_label.pixmap().width() == 800

    viewer.fit_to_width()
    assert viewer.fit_width

    viewer.show()
    viewer.resize(400, 400)
    app.processEvents()
    viewer.zoom_slider.setValue(150)
    app.processEvents()
    assert viewer.zoom_percent == 150
    assert viewer.page_label.pixmap().width() == 1200
    assert viewer.scroll_area.horizontalScrollBar().maximum() > 0

    viewer.next_page()
    assert viewer.page_index == 1
    assert viewer.page_spin.value() == 2
    assert viewer.previous_button.isEnabled()
    assert not viewer.next_button.isEnabled()

    viewer.previous_page()
    assert viewer.page_index == 0
    assert app is not None
    viewer.close()


def test_pdf_viewer_toolbar_tools_fit_at_narrow_docked_width(tmp_path) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    pdf_path = tmp_path / "source.pdf"
    _create_test_pdf(pdf_path)
    window = qtw.QMainWindow()
    host = qtw.QWidget(window)
    host.setLayout(qtw.QVBoxLayout())
    host.setFixedWidth(360)
    window.setCentralWidget(host)
    dock = PdfViewerDock(str(pdf_path), window, embedded_host=host)
    window.addDockWidget(qtc.Qt.LeftDockWidgetArea, dock)
    window.resize(360, 500)
    window.show()
    dock.dock_in_host()
    app.processEvents()
    viewer = dock.viewer

    tools = (
        viewer.previous_button,
        viewer.next_button,
        viewer.page_spin,
        viewer.page_count_label,
        viewer.zoom_out_button,
        viewer.zoom_combo,
        viewer.zoom_slider,
        viewer.zoom_in_button,
        viewer.fit_width_button,
        viewer.dock_toggle_button,
        viewer.hide_button,
        viewer.close_button,
    )
    toolbar_rect = viewer.toolbar_widget.rect()
    for tool in tools:
        tool_rect = qtc.QRect(tool.mapTo(viewer.toolbar_widget, qtc.QPoint(0, 0)), tool.size())
        assert tool.isVisible()
        assert toolbar_rect.contains(tool_rect), tool.toolTip() or tool.objectName()

    assert viewer.zoom_slider.minimumWidth() == 72
    assert viewer.toolbar_widget.height() < viewer.scroll_area.height()
    dock.close_automatically()
    window.close()


def test_pdf_viewer_docks_floats_hides_and_confirms_manual_close(tmp_path, monkeypatch) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    pdf_path = tmp_path / "source.pdf"
    _create_test_pdf(pdf_path)
    window = qtw.QMainWindow()
    dock = PdfViewerDock(str(pdf_path), window)
    window.addDockWidget(qtc.Qt.LeftDockWidgetArea, dock)
    window.show()
    dock.show()
    app.processEvents()

    assert window.dockWidgetArea(dock) == qtc.Qt.LeftDockWidgetArea
    dock.toggle_floating()
    assert dock.isFloating()

    dock.viewer.hideRequested.emit()
    assert not dock.isVisible()
    dock.show()

    monkeypatch.setattr(qtw.QMessageBox, "question", lambda *_args, **_kwargs: qtw.QMessageBox.No)
    assert not dock.close()
    assert dock.isVisible()

    monkeypatch.setattr(qtw.QMessageBox, "question", lambda *_args, **_kwargs: qtw.QMessageBox.Yes)
    assert dock.close()
    window.close()


def test_pdf_viewer_embeds_in_host_and_can_hide_float_redock_and_close(tmp_path, monkeypatch) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    pdf_path = tmp_path / "source.pdf"
    _create_test_pdf(pdf_path)
    window = qtw.QMainWindow()
    host = qtw.QWidget(window)
    host.setLayout(qtw.QVBoxLayout())
    window.setCentralWidget(host)
    dock = PdfViewerDock(str(pdf_path), window, embedded_host=host)
    window.addDockWidget(qtc.Qt.LeftDockWidgetArea, dock)
    window.show()
    dock.dock_in_host()
    app.processEvents()

    assert dock.is_viewer_visible()
    assert not dock.is_viewer_floating()
    assert dock.viewer.parentWidget() is host

    dock.viewer.hideRequested.emit()
    assert not dock.is_viewer_visible()
    dock.show_viewer()
    assert dock.is_viewer_visible()

    dock.toggle_floating()
    assert dock.is_viewer_floating()
    assert dock.viewer.parentWidget() is dock

    dock.toggle_floating()
    assert not dock.is_viewer_floating()
    assert dock.viewer.parentWidget() is host

    monkeypatch.setattr(qtw.QMessageBox, "question", lambda *_args, **_kwargs: qtw.QMessageBox.No)
    assert not dock.close()
    assert dock.is_viewer_visible()

    monkeypatch.setattr(qtw.QMessageBox, "question", lambda *_args, **_kwargs: qtw.QMessageBox.Yes)
    assert dock.close()
    assert not host.isVisible()
    window.close()


def test_pdf_source_is_copied_to_project_as_read_only(tmp_path) -> None:
    source_path = tmp_path / "source.pdf"
    source_path.write_bytes(b"%PDF-1.4\n")
    project_root = tmp_path / "Project"

    destination = Path(copy_pdf_source_readonly(str(source_path), str(project_root)))

    assert destination == Path(project_pdf_source_path(str(project_root), source_path.name))
    assert destination.read_bytes() == source_path.read_bytes()
    assert destination.stat().st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH) == 0


def test_project_pdf_source_is_resolved_from_canonical_directory(tmp_path) -> None:
    project_root = tmp_path / "Project"
    first_path = Path(project_pdf_source_path(str(project_root), "b-source.pdf"))
    second_path = Path(project_pdf_source_path(str(project_root), "a-source.PDF"))
    first_path.parent.mkdir(parents=True)
    first_path.write_bytes(b"%PDF-1.4\n")
    second_path.write_bytes(b"%PDF-1.4\n")
    (first_path.parent / "notes.txt").write_text("not a PDF", encoding="utf-8")

    assert find_project_pdf_source(str(project_root)) == str(second_path)


def test_engine_reports_created_source_document_path(tmp_path) -> None:
    engine = ProjectCreationEngine(str(tmp_path), _DummyEventBus())
    engine.context = {
        "project_name": "Project",
        "SourceImageDocumentName": "source.pdf",
    }

    assert engine._created_source_document_path() == project_pdf_source_path(
        str(tmp_path / "Project"),
        "source.pdf",
    )


def test_engine_persists_protected_source_location_in_metadata_mirrors(tmp_path) -> None:
    source_path = tmp_path / "source.pdf"
    source_path.write_bytes(b"%PDF-1.4\n")
    engine = ProjectCreationEngine(str(tmp_path), _DummyEventBus())

    result = engine.create_project({
        "project_name": "Project",
        "project_purpose": "OCR",
        "creation_trigger": "New project wizard",
        "source_context": "Selected PDF source",
        "user_intent_summary": "Test protected PDF source persistence.",
        "SourceImageDocument": str(source_path),
        "NumberPages": 2,
        "NumberColumns": 1,
    })

    assert result["status"] == "ok"
    protected_path = project_pdf_source_path(str(tmp_path / "Project"), source_path.name)
    record = load_project_database_record(project_metadata_database_path(str(tmp_path / "Project")))
    assert record["SourceDocumentPath"] == protected_path
    assert record["SourceDocumentDirectory"] == os.path.dirname(protected_path)
    assert record["SourceType"] == "PDF"
    assert record["NumberPages"] == 2
    assert record["SourcePageSectionCount"] == 3
    assert [section["name"] for section in record["SourcePageSections"]] == [
        "Front Matter",
        "Scripture",
        "Back Matter",
    ]

    metadata_dir = tmp_path / "Project" / "Model" / "Project" / "Data" / "SQLite"
    json_record = json.loads((metadata_dir / "project_metadata.json").read_text(encoding="utf-8"))
    assert json_record["SourceDocumentPath"] == protected_path
    assert json_record["NumberPages"] == 2
    assert len(json_record["SourcePageSections"]) == 3
    assert protected_path in (metadata_dir / "project_metadata.csv").read_text(encoding="utf-8")

    for stage in ("Workflow", "Complete"):
        for section in ("FrontMatter", "Scripture", "BackMatter"):
            assert (tmp_path / "Project" / "Model" / "Project" / "Images" / stage / "Source" / section).is_dir()


def test_project_wizard_includes_selected_source_document(tmp_path) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    source_path = tmp_path / "source.pdf"
    source_path.write_bytes(b"%PDF-1.4\n")
    dialog = ProjectCreationWizardDialog(str(tmp_path))
    dialog.source_document_edit.setText(str(source_path))

    payload = dialog.get_payload()

    assert payload["SourceImageDocument"] == str(source_path)
    assert app is not None
    dialog.close()


def test_project_wizard_resolves_provenance_pdf_and_sets_page_baselines(tmp_path) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    pdf_path = tmp_path / "source.pdf"
    provenance_path = tmp_path / "source.ris"
    _create_test_pdf(pdf_path)
    provenance_path.write_text(f"TY  - BOOK\nL1  - {pdf_path.name}\nER  -\n", encoding="utf-8")

    dialog = ProjectCreationWizardDialog(str(tmp_path))
    payload = dialog._load_provenance_file(str(provenance_path))
    dialog._apply_ris_payload(payload)
    dialog.columns_per_page_spin.setValue(2)
    project_payload = dialog.get_payload()

    assert dialog.source_document_edit.text() == str(pdf_path)
    assert project_payload["SourceImageDocument"] == str(pdf_path)
    assert project_payload["NumberPages"] == 2
    assert project_payload["NumberColumns"] == 2
    assert project_payload["TotalProjectPages"] == 4
    assert app is not None
    dialog.close()