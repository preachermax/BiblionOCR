from __future__ import annotations

import json
import importlib.util
import os
import stat
import subprocess
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5 import QtCore as qtc
from PyQt5 import QtWidgets as qtw
from PIL import Image
from pypdf import PdfReader

from Core.engine import ProjectCreationEngine
from Core.project_database import create_project_database, load_project_database_record, project_metadata_database_path
from Core.source_documents import (
    combine_project_source_pdfs,
    convert_pdf_pages_to_tiff,
    convert_scan_to_project_pdf,
    copy_pdf_source_readonly,
    copy_source_document_readonly,
    find_project_pdf_source,
    find_project_source_document,
    extract_pdf_page_range,
    extract_pdf_pages,
    project_pdf_source_path,
    project_source_document_path,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
RENDERER_PATH = ROOT_DIR / "ViewController" / "0-MainUI" / "helpers" / "qt_pdf_renderer.py"
HELPERS_DIR = ROOT_DIR / "ViewController" / "0-MainUI" / "helpers"
if str(HELPERS_DIR) not in sys.path:
    sys.path.insert(0, str(HELPERS_DIR))

from project_creation_wizard_dialog import ProjectCreationWizardDialog
from ProjectCreationWizardDialogUI import Ui_ProjectCreationWizardDialog
import pdf_viewer_dialog
from pdf_viewer_dialog import PdfViewerDialog, PdfViewerDock


def _load_mypixler_module():
    module_path = ROOT_DIR / "ViewController" / "1-PreProcess" / "MyPixler.py"
    spec = importlib.util.spec_from_file_location("mypixler_pdf_test", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_mypixler_prefers_installed_workflow_definition_over_project_snapshot(tmp_path) -> None:
    mypixler = _load_mypixler_module()
    project_workflow = tmp_path / "Model" / "Project" / "Data" / "csv"
    project_workflow.mkdir(parents=True)
    (project_workflow / "page_workflow.csv").write_text("stale project snapshot\n", encoding="utf-8")

    owner = type("WorkflowOwner", (), {})()
    owner.current_project_root = str(tmp_path)
    owner.projecthome = str(ROOT_DIR)
    owner._shared_active_project_root = lambda: str(tmp_path)

    assert mypixler.PixlerMain._workflow_definition_root(owner) == str(ROOT_DIR)


def test_mypixler_stage_source_toolbar_button_is_icon_only() -> None:
    mypixler = _load_mypixler_module()
    expected_ui_path = (
        ROOT_DIR / "ViewController" / "1-PreProcess" / "MyPixlerUI.py"
    ).resolve()

    assert Path(mypixler._UI_MODULE.__file__).resolve() == expected_ui_path

    app = qtw.QApplication.instance() or qtw.QApplication([])
    window = qtw.QMainWindow()
    ui = mypixler.Ui_Pixler()
    ui.setupUi(window)
    stage_button = ui.SourceToolBar.widgetForAction(ui.actionStage_pdf)

    assert ui.SourceToolBar.toolButtonStyle() == qtc.Qt.ToolButtonIconOnly
    assert stage_button.toolButtonStyle() == qtc.Qt.ToolButtonIconOnly
    assert ui.actionStage_pdf.text() == "Stage Source PDF"
    assert not ui.actionStage_pdf.icon().isNull()

    window.close()
    app.processEvents()


class _DummyEventBus:
    def emit(self, _event):
        return None


def test_generated_project_wizard_ui_defines_all_five_pages() -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    shell = qtw.QDialog()
    ui = Ui_ProjectCreationWizardDialog()

    ui.setupUi(shell)

    assert ui.page_stack.count() == 5
    assert ui.ris_editor_table is not None
    assert ui.source_document_edit is not None
    assert ui.project_db_table is not None
    assert ui.milestones_table is not None
    assert ui.handshake_table is not None
    assert ui.folder_selection_stack is not None
    shell.close()
    app.processEvents()


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


def _create_test_tiff(tiff_path: Path) -> None:
    pages = [Image.new("RGB", (80, 120), color) for color in ("white", "gray", "black")]
    pages[0].save(tiff_path, save_all=True, append_images=pages[1:], format="TIFF")


def _wait_for_dock_load(dock: PdfViewerDock, timeout_ms: int = 10000) -> None:
    if dock.viewer is not None:
        return
    loop = qtc.QEventLoop()
    errors = []
    dock.documentLoaded.connect(loop.quit)
    dock.loadFailed.connect(lambda message: (errors.append(message), loop.quit()))
    qtc.QTimer.singleShot(timeout_ms, loop.quit)
    loop.exec_()
    assert not errors, errors[0] if errors else ""
    assert dock.viewer is not None, "Source reader did not finish loading"


def test_pdf_viewer_dock_opens_without_waiting_for_source_preparation(tmp_path, monkeypatch) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    pdf_path = tmp_path / "source.pdf"
    _create_test_pdf(pdf_path)
    original_page_count = pdf_viewer_dialog._source_page_count

    def delayed_page_count(source_path):
        time.sleep(0.25)
        return original_page_count(source_path)

    monkeypatch.setattr(pdf_viewer_dialog, "_source_page_count", delayed_page_count)
    window = qtw.QMainWindow()
    window.show()
    app.processEvents()
    started_at = time.monotonic()
    dock = PdfViewerDock(str(pdf_path), window)
    window.addDockWidget(qtc.Qt.LeftDockWidgetArea, dock)
    dock.show_viewer()
    elapsed = time.monotonic() - started_at

    assert elapsed < 0.15
    assert dock.is_loading
    assert dock.viewer is None
    assert dock._loading_progress.isVisible()
    _wait_for_dock_load(dock)
    assert dock.page_count == 2
    dock.close_automatically()
    app.processEvents()
    window.close()


def test_scan_conversion_and_project_pdf_combination(tmp_path) -> None:
    project_root = tmp_path / "project"
    acquired_pdf = project_root / "Model/Project/Images/MyServer/source_images/pdf_acq_src_image/acquired.pdf"
    acquired_pdf.parent.mkdir(parents=True)
    _create_test_pdf(acquired_pdf)
    scan_path = tmp_path / "scan.tif"
    _create_test_tiff(scan_path)

    scanned_pdf = Path(convert_scan_to_project_pdf(str(scan_path), str(project_root)))
    combined_pdf = Path(combine_project_source_pdfs(str(project_root)))

    assert scanned_pdf.parent.name == "pdf_scan_src_image"
    assert len(PdfReader(str(scanned_pdf)).pages) == 3
    assert combined_pdf.parent.name == "pdf_combined_src_images"
    assert len(PdfReader(str(combined_pdf)).pages) == 5


def test_pdf_page_range_extraction_preserves_all_selected_page_content(tmp_path) -> None:
    source_path = tmp_path / "source.pdf"
    destination_dir = tmp_path / "section"
    _create_test_pdf(source_path)

    extracted_path = Path(extract_pdf_page_range(source_path, destination_dir, 1, 2))
    extracted_pages = PdfReader(str(extracted_path)).pages

    assert len(extracted_pages) == 2
    assert "Page\tone" in extracted_pages[0].extract_text()
    assert "Page\ttwo" in extracted_pages[1].extract_text()


def test_section_pdf_extracts_to_individual_page_pdfs_then_tiffs(tmp_path) -> None:
    section_pdf = tmp_path / "section.pdf"
    page_pdf_dir = tmp_path / "page-pdfs"
    selected_page_dir = tmp_path / "selected-page-pdfs"
    tiff_dir = tmp_path / "tiffs"
    _create_test_pdf(section_pdf)

    page_paths = [Path(path) for path in extract_pdf_pages(section_pdf, page_pdf_dir)]
    selected_paths = [Path(path) for path in extract_pdf_pages(section_pdf, selected_page_dir, 2, 2)]
    tiff_paths = [Path(path) for path in convert_pdf_pages_to_tiff(page_pdf_dir, tiff_dir, 10)]

    assert [path.name for path in page_paths] == ["section_Page_001.pdf", "section_Page_002.pdf"]
    assert [len(PdfReader(str(path)).pages) for path in page_paths] == [1, 1]
    assert "Page\tone" in PdfReader(str(page_paths[0])).pages[0].extract_text()
    assert "Page\ttwo" in PdfReader(str(page_paths[1])).pages[0].extract_text()
    assert [path.name for path in selected_paths] == ["section_Page_002.pdf"]
    assert "Page\ttwo" in PdfReader(str(selected_paths[0])).pages[0].extract_text()
    assert [path.name for path in tiff_paths] == [
        "section_Page_001_010.tif",
        "section_Page_002_011.tif",
    ]
    with Image.open(tiff_paths[0]) as first_tiff:
        assert first_tiff.width > 0
        assert first_tiff.height > 0


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
    assert viewer.fit_width
    assert abs(viewer.page_label.pixmap().width() - viewer.scroll_area.viewport().width()) <= 4
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


def test_source_reader_renders_and_navigates_multipage_tiff(tmp_path) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    tiff_path = tmp_path / "source.tif"
    _create_test_tiff(tiff_path)

    viewer = PdfViewerDialog(str(tiff_path))

    assert viewer.page_count == 3
    assert viewer.page_index == 0
    assert viewer.page_label.pixmap() is not None
    assert not viewer.page_label.pixmap().isNull()
    viewer.next_page()
    assert viewer.page_index == 1
    assert viewer.page_spin.value() == 2
    assert app is not None
    viewer.close()


def test_project_wizard_updates_source_path_before_showing_reader(tmp_path, monkeypatch) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    source_path = tmp_path / "source.tif"
    _create_test_tiff(source_path)
    observed_paths = []

    class FakeReader:
        page_count = 3

        def __init__(self, _source_path, parent, **_kwargs):
            observed_paths.append(parent.source_document_edit.text())

        def setAttribute(self, *_args):
            return None

        def show(self):
            return None

    dialog = ProjectCreationWizardDialog(str(tmp_path))
    monkeypatch.setattr(
        "project_creation_wizard_dialog.run_myexplorer_selection",
        lambda *_args: str(source_path),
    )
    monkeypatch.setattr("project_creation_wizard_dialog.PdfViewerDialog", FakeReader)

    dialog._browse_for_source_document()

    deadline = qtc.QDeadlineTimer(5000)
    while dialog.source_load_thread is not None and not deadline.hasExpired():
        app.processEvents(qtc.QEventLoop.AllEvents, 50)

    assert dialog.source_document_edit.text() == str(source_path)
    assert observed_paths == [str(source_path)]
    assert dialog.source_pages_combo.currentText() == "3"
    assert dialog.source_load_progress_bar.value() == 100
    assert app is not None
    dialog.close()


def test_project_wizard_rejects_unsupported_source_document(tmp_path, monkeypatch) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    source_path = tmp_path / "source.png"
    source_path.write_bytes(b"not a source document")
    warnings = []
    dialog = ProjectCreationWizardDialog(str(tmp_path))
    monkeypatch.setattr(
        "project_creation_wizard_dialog.run_myexplorer_selection",
        lambda *_args: str(source_path),
    )
    monkeypatch.setattr(
        qtw.QMessageBox,
        "warning",
        lambda _parent, title, message: warnings.append((title, message)),
    )

    dialog._browse_for_source_document()

    assert dialog.source_document_edit.text() == ""
    assert warnings == [("Source Document", "Select a PDF or multi-page TIFF source document.")]
    assert app is not None
    dialog.close()


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
    _wait_for_dock_load(dock)
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
    central_widget = qtw.QWidget(window)
    window.setCentralWidget(central_widget)
    dock = PdfViewerDock(str(pdf_path), window)
    window.addDockWidget(qtc.Qt.LeftDockWidgetArea, dock)
    window.resize(1200, 800)
    window.show()
    dock.show()
    window.resizeDocks([dock], [420], qtc.Qt.Horizontal)
    app.processEvents()
    _wait_for_dock_load(dock)

    assert window.dockWidgetArea(dock) == qtc.Qt.LeftDockWidgetArea
    assert dock.width() <= 500
    assert central_widget.isVisible()
    assert central_widget.width() >= 600
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


def test_docked_source_reader_expands_and_restores_parent_window(tmp_path, monkeypatch) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    pdf_path = tmp_path / "source.pdf"
    _create_test_pdf(pdf_path)
    window = qtw.QMainWindow()
    window.setCentralWidget(qtw.QWidget(window))
    window.setGeometry(40, 40, 500, 480)
    window.show()
    app.processEvents()
    default_geometry = window.geometry()

    dock = PdfViewerDock(str(pdf_path), window)
    window.addDockWidget(qtc.Qt.LeftDockWidgetArea, dock)
    dock.show_viewer()
    app.processEvents()
    _wait_for_dock_load(dock)

    assert window.width() > default_geometry.width()
    dock.toggle_floating()
    app.processEvents()
    assert window.geometry() == default_geometry

    dock.toggle_floating()
    app.processEvents()
    assert window.width() > default_geometry.width()

    monkeypatch.setattr(qtw.QMessageBox, "question", lambda *_args, **_kwargs: qtw.QMessageBox.Yes)
    assert dock.close()
    app.processEvents()
    assert window.geometry() == default_geometry
    window.close()


def test_replacing_docked_source_reader_preserves_default_window_geometry(tmp_path) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    pdf_path = tmp_path / "source.pdf"
    _create_test_pdf(pdf_path)
    window = qtw.QMainWindow()
    window.setCentralWidget(qtw.QWidget(window))
    window.setGeometry(40, 40, 500, 480)
    window.show()
    app.processEvents()
    default_geometry = window.geometry()

    first_dock = PdfViewerDock(str(pdf_path), window)
    window.addDockWidget(qtc.Qt.LeftDockWidgetArea, first_dock)
    first_dock.show_viewer()
    app.processEvents()
    _wait_for_dock_load(first_dock)
    assert window.width() > default_geometry.width()

    replacement_dock = PdfViewerDock(str(pdf_path), window)
    first_dock.close_automatically()
    window.addDockWidget(qtc.Qt.LeftDockWidgetArea, replacement_dock)
    replacement_dock.show_viewer()
    app.processEvents()
    _wait_for_dock_load(replacement_dock)
    assert window.width() > default_geometry.width()

    replacement_dock.close_automatically()
    app.processEvents()
    assert window.geometry() == default_geometry
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
    _wait_for_dock_load(dock)

    assert dock.is_viewer_visible()
    assert not dock.is_viewer_floating()
    assert dock.viewer.parentWidget() is host
    assert dock.viewer.isVisible()

    dock.viewer.hideRequested.emit()
    assert not dock.is_viewer_visible()
    assert not dock.viewer.isVisible()
    dock.show_viewer()
    assert dock.is_viewer_visible()
    assert dock.viewer.isVisible()

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


def test_mypixler_displays_active_project_pdf_in_shared_viewer(tmp_path, monkeypatch) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    project_root = tmp_path / "Project"
    pdf_path = Path(project_pdf_source_path(str(project_root), "source.pdf"))
    pdf_path.parent.mkdir(parents=True)
    _create_test_pdf(pdf_path)
    monkeypatch.setenv("BIBLION_GUI_ENV_SANITIZED", "1")
    mypixler = _load_mypixler_module()
    window = mypixler.PixlerMain.__new__(mypixler.PixlerMain)
    qtw.QMainWindow.__init__(window)
    window.current_project_root = str(project_root)
    window.pdf_source_path = ""
    window.pdf_page_count = 0
    window.pdf_viewer_dialog = None
    window.view_source_document_action = qtw.QAction("Display Source Document", window)
    window.source_viewer_visibility_action = qtw.QAction("Show Source Document Viewer", window)
    window.source_viewer_visibility_action.setCheckable(True)
    monkeypatch.setattr(window, "_shared_active_project_root", lambda: str(project_root))
    window.show()
    app.processEvents()

    assert window._project_source_pdf() == str(pdf_path)
    assert window._open_project_source_pdf_on_startup()
    assert window.pdf_viewer_dialog is not None
    _wait_for_dock_load(window.pdf_viewer_dialog)
    assert window.pdf_viewer_dialog.pdf_path == str(pdf_path)
    assert window.pdf_page_count == 2
    assert window.dockWidgetArea(window.pdf_viewer_dialog) == qtc.Qt.LeftDockWidgetArea
    assert not window.pdf_viewer_dialog.is_viewer_floating()
    assert window.pdf_viewer_dialog.is_viewer_visible()
    assert window.source_viewer_visibility_action.isEnabled()
    assert window.source_viewer_visibility_action.isChecked()

    window._set_pdf_viewer_visibility(False)
    assert not window.pdf_viewer_dialog.is_viewer_visible()
    window._set_pdf_viewer_visibility(True)
    assert window.pdf_viewer_dialog.is_viewer_visible()

    window._close_pdf_viewer_automatically()
    assert window.pdf_viewer_dialog is None
    assert not window.source_viewer_visibility_action.isEnabled()
    app.processEvents()
    window.deleteLater()


def test_pdf_source_is_copied_to_project_as_read_only(tmp_path) -> None:
    source_path = tmp_path / "source.pdf"
    source_path.write_bytes(b"%PDF-1.4\n")
    project_root = tmp_path / "Project"

    destination = Path(copy_pdf_source_readonly(str(source_path), str(project_root)))

    assert destination == Path(project_pdf_source_path(str(project_root), source_path.name))
    assert destination.read_bytes() == source_path.read_bytes()
    assert destination.stat().st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH) == 0


def test_tiff_source_is_copied_to_tiff_source_folder_as_read_only(tmp_path) -> None:
    source_path = tmp_path / "source.tif"
    _create_test_tiff(source_path)
    project_root = tmp_path / "Project"

    destination = Path(copy_source_document_readonly(str(source_path), str(project_root)))

    assert destination == Path(project_source_document_path(str(project_root), source_path.name))
    assert destination.parent.name == "tif_acq_src_image"
    assert destination.read_bytes() == source_path.read_bytes()
    assert destination.stat().st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH) == 0
    assert find_project_source_document(str(project_root)) == str(destination)


def test_project_pdf_source_is_resolved_from_canonical_directory(tmp_path) -> None:
    project_root = tmp_path / "Project"
    first_path = Path(project_pdf_source_path(str(project_root), "b-source.pdf"))
    second_path = Path(project_pdf_source_path(str(project_root), "a-source.PDF"))
    first_path.parent.mkdir(parents=True)
    first_path.write_bytes(b"%PDF-1.4\n")
    second_path.write_bytes(b"%PDF-1.4\n")
    (first_path.parent / "notes.txt").write_text("not a PDF", encoding="utf-8")

    assert find_project_pdf_source(str(project_root)) == str(second_path)


def test_project_pdf_source_prefers_registered_legacy_source_path(tmp_path) -> None:
    project_root = tmp_path / "Project"
    legacy_path = project_root / "Model" / "Project" / "Images" / "MyServer" / "Source" / "pdf" / "legacy.pdf"
    legacy_path.parent.mkdir(parents=True)
    legacy_path.write_bytes(b"%PDF-1.4\n")
    create_project_database(
        project_metadata_database_path(str(project_root)),
        {
            "ProjectName": "Project",
            "SourceType": "PDF",
            "SourceDocumentPath": str(legacy_path),
        },
    )

    assert find_project_pdf_source(str(project_root)) == str(legacy_path)


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


def test_engine_persists_tiff_source_type_and_location(tmp_path) -> None:
    source_path = tmp_path / "source.tiff"
    _create_test_tiff(source_path)
    engine = ProjectCreationEngine(str(tmp_path), _DummyEventBus())

    result = engine.create_project({
        "project_name": "TiffProject",
        "project_purpose": "OCR",
        "creation_trigger": "New project wizard",
        "source_context": "Selected TIFF source",
        "user_intent_summary": "Test protected TIFF source persistence.",
        "SourceImageDocument": str(source_path),
        "NumberPages": 3,
        "NumberColumns": 1,
    })

    assert result["status"] == "ok"
    protected_path = project_source_document_path(str(tmp_path / "TiffProject"), source_path.name)
    record = load_project_database_record(project_metadata_database_path(str(tmp_path / "TiffProject")))
    assert result["source_document_path"] == protected_path
    assert record["SourceDocumentPath"] == protected_path
    assert record["SourceType"] == "TIFF"


def test_engine_copies_loaded_ris_to_project_provenance_folder(tmp_path) -> None:
    provenance_path = tmp_path / "Original Export.ris"
    provenance_text = "TY  - BOOK\nTI  - Test source\nER  -\n"
    provenance_path.write_text(provenance_text, encoding="utf-8")
    engine = ProjectCreationEngine(str(tmp_path), _DummyEventBus())

    result = engine.create_project({
        "project_name": "RisProject",
        "project_purpose": "OCR",
        "creation_trigger": "New project wizard",
        "source_context": "Loaded RIS provenance",
        "user_intent_summary": "Test provenance preservation.",
        "source_provenance_path": str(provenance_path),
        "NumberPages": 1,
        "NumberColumns": 1,
    })

    assert result["status"] == "ok"
    copied_path = (
        tmp_path
        / "RisProject"
        / "Model"
        / "Project"
        / "Images"
        / "MyServer"
        / "source_images"
        / "provenance"
        / provenance_path.name
    )
    assert copied_path.read_text(encoding="utf-8") == provenance_text
    record = load_project_database_record(project_metadata_database_path(str(tmp_path / "RisProject")))
    assert record["ProvenancePath"] == str(copied_path)


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


def test_project_wizard_uses_generated_designer_ui(tmp_path) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])

    dialog = ProjectCreationWizardDialog(str(tmp_path))

    assert dialog.ui.page_stack is dialog.page_stack
    assert dialog.ui.back_button is dialog.back_button
    assert dialog.ui.next_button is dialog.next_button
    assert dialog.ui.create_button is dialog.create_button
    assert dialog.ui.source_load_status_label is dialog.source_load_status_label
    assert dialog.ui.source_load_progress_bar is dialog.source_load_progress_bar
    assert dialog.page_stack.count() == 5
    assert app is not None
    dialog.close()


def test_project_wizard_font_selector_does_not_overlap_column_editor(tmp_path) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    dialog = ProjectCreationWizardDialog(str(tmp_path))
    dialog.page_stack.setCurrentIndex(1)
    dialog.show()
    app.processEvents()

    font_rect = dialog.ui_font_combo.geometry()
    column_editor_rect = dialog.column_config_group.geometry()

    assert font_rect.bottom() < column_editor_rect.top()
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
    assert project_payload["source_provenance_path"] == str(provenance_path)
    assert project_payload["SourceImageDocument"] == str(pdf_path)
    assert project_payload["NumberPages"] == 2
    assert project_payload["NumberColumns"] == 2
    assert project_payload["TotalProjectPages"] == 4
    assert app is not None
    dialog.close()