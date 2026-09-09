from __future__ import annotations

import json
import importlib.util
import inspect
import os
import stat
import subprocess
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt5 import QtCore as qtc
from PyQt5 import QtWidgets as qtw
from PIL import Image
from pypdf import PdfReader, PdfWriter

from Core.engine import ProjectCreationEngine
from Core.page_workflow import PageWorkflowStep, advance_page_workflow_files
from Core.project_database import create_project_database, load_project_database_record, project_metadata_database_path
from Core.source_documents import (
    combine_project_source_pdfs,
    complete_project_staged_pdf_handoff,
    convert_pdf_pages_to_tiff,
    convert_scan_to_project_pdf,
    copy_pdf_source_readonly,
    copy_source_document_readonly,
    find_project_pdf_source,
    find_project_staged_pdf,
    find_project_source_document,
    extract_pdf_page_range,
    extract_pdf_pages,
    extract_pdf_source_pages,
    project_pdf_source_path,
    project_source_document_path,
    stage_combined_project_pdf,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
RENDERER_PATH = ROOT_DIR / "ViewController" / "0-MainUI" / "helpers" / "qt_pdf_renderer.py"
HELPERS_DIR = ROOT_DIR / "ViewController" / "0-MainUI" / "helpers"
if str(HELPERS_DIR) not in sys.path:
    sys.path.insert(0, str(HELPERS_DIR))

from project_creation_wizard_dialog import ProjectCreationWizardDialog
from ProjectCreationWizardDialogUI import Ui_ProjectCreationWizardDialog
import source_reader
from source_reader import SourceReaderDialog, SourceReaderDock


def _load_mypixler_module():
    module_path = ROOT_DIR / "ViewController" / "1-PreProcess" / "MyPixler.py"
    spec = importlib.util.spec_from_file_location("mypixler_pdf_test", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_myserver_module():
    module_path = ROOT_DIR / "ViewController" / "0-MainUI" / "MyServer.py"
    spec = importlib.util.spec_from_file_location("myserver_pdf_test", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_mypixler_myexplorer_action_launches_with_active_project(
    tmp_path,
    monkeypatch,
) -> None:
    mypixler = _load_mypixler_module()
    launched = []
    owner = type("WorkflowOwner", (), {})()
    owner.current_project_root = str(tmp_path)
    owner._shared_active_project_root = lambda: ""
    monkeypatch.setattr(
        mypixler.subprocess,
        "Popen",
        lambda command: launched.append(command) or object(),
    )

    result = mypixler.PixlerMain.open_myexplorer(owner)

    assert result is not None
    assert launched == [[
        sys.executable,
        str(ROOT_DIR / "ViewController/0-MainUI/MyExplorer.py"),
        str(tmp_path),
    ]]
    assert "actionMyExplorer.triggered.connect(self.open_myexplorer)" in inspect.getsource(
        mypixler.PixlerMain.initMenubar
    )


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


def test_mypixler_pdf_tiff_workflow_actions_dispatch_to_controller_methods() -> None:
    mypixler = _load_mypixler_module()
    app = qtw.QApplication.instance() or qtw.QApplication([])
    window = qtw.QMainWindow()
    window.ui = mypixler.Ui_Pixler()
    window.ui.setupUi(window)
    expected_callbacks = {
        "actionStage_pdf": "actionstage_pdf",
        "actionExtract_pdf": "actionextract_pdf",
        "actionpdf_For_tiff": "actionpdf_for_tiff",
        "actionpdf_To_tiff": "actionpdf_to_tiff",
        "actiontiff_indexed": "actiontiff_to_mono",
        "actionDeskew_indexed": "actiondeskew_mono",
        "actionManually_Crop_Language_Pages": "actionCropImage",
        "actionAuto_Crop": "actionCrop_Languages",
        "actionDeskew_Greek_tiff": "actionDeskew_Greek_tiff",
        "actionDeskew_Latin_tiff": "actionDeskew_Latin_tiff",
    }
    dispatched = []
    for callback_name in expected_callbacks.values():
        setattr(
            window,
            callback_name,
            lambda _checked=False, name=callback_name: dispatched.append(name),
        )

    mypixler.PixlerMain.initWorkflowActions(window)

    for action_name, callback_name in expected_callbacks.items():
        getattr(window.ui, action_name).trigger()
        assert dispatched.pop() == callback_name

    window.close()
    app.processEvents()


def test_mypixler_stage_action_seeds_empty_workflow_from_myserver_handoff(tmp_path, monkeypatch) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    mypixler = _load_mypixler_module()
    staged_source = (
        tmp_path
        / "Model/Project/Images/MyPixler/SourceStaged/Workflow/pdf_staged_src_image/source.pdf"
    )
    staged_source.parent.mkdir(parents=True)
    staged_source.write_bytes(b"project source")
    messages = []
    owner = type("WorkflowOwner", (), {})()
    owner.current_project_root = str(tmp_path)
    owner.projecthome = str(ROOT_DIR)
    owner._shared_active_project_root = lambda: str(tmp_path)
    owner._workflow_step_for_method = lambda _method: None
    owner._first_workflow_source_document = mypixler.PixlerMain._first_workflow_source_document
    owner.statusBar = lambda: type(
        "StatusBar",
        (),
        {"showMessage": lambda _self, message, _timeout: messages.append(message)},
    )()
    monkeypatch.setattr(qtw.QDialog, "exec_", lambda _dialog: qtw.QDialog.Accepted)
    warnings = []
    monkeypatch.setattr(qtw.QMessageBox, "warning", lambda *args: warnings.append(args))

    mypixler.PixlerMain.actionstage_pdf(owner)

    assert not staged_source.exists()
    complete_source = (
        tmp_path
        / "Model/Project/Images/MyPixler/SourceStaged/Complete/pdf_staged_src_image/source.pdf"
    )
    assert complete_source.read_bytes() == b"project source"
    assert messages == [f"Staged source PDF accepted: {complete_source}"]
    assert warnings == []
    app.processEvents()


def test_mypixler_stage_action_does_not_accept_handoff_when_cancelled(tmp_path, monkeypatch) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    mypixler = _load_mypixler_module()
    staged_source = (
        tmp_path
        / "Model/Project/Images/MyPixler/SourceStaged/Workflow/pdf_staged_src_image/source.pdf"
    )
    staged_source.parent.mkdir(parents=True)
    staged_source.write_bytes(b"project source")
    owner = type("WorkflowOwner", (), {})()
    owner.current_project_root = str(tmp_path)
    owner.projecthome = str(ROOT_DIR)
    owner._shared_active_project_root = lambda: str(tmp_path)
    owner._workflow_step_for_method = lambda _method: None
    owner._first_workflow_source_document = mypixler.PixlerMain._first_workflow_source_document
    monkeypatch.setattr(qtw.QDialog, "exec_", lambda _dialog: qtw.QDialog.Rejected)

    mypixler.PixlerMain.actionstage_pdf(owner)

    assert staged_source.exists()
    assert not (
        tmp_path
        / "Model/Project/Images/MyPixler/SourceStaged/Complete/pdf_staged_src_image/source.pdf"
    ).exists()
    app.processEvents()


def test_mypixler_stage_action_advances_current_section_pdf(tmp_path, monkeypatch) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    mypixler = _load_mypixler_module()
    step = PageWorkflowStep(
        sequence="SSHF",
        description="stage front matter",
        milestone_name="src_pages_front_matter_staged",
        page_section="FrontSection",
        module="MyPixler",
        ui_trigger="actionStage_pdf.triggered",
        method="actionstage_pdf",
        dialog_ui="StageDialog",
        notes="",
        workflow_source="workflow/section",
        complete_destination="complete/section",
        workflow_handshake="workflow/extract",
    )
    source_path = tmp_path / step.workflow_source / "section.pdf"
    source_path.parent.mkdir(parents=True)
    source_path.write_bytes(b"section source")
    finished = []
    messages = []
    owner = type("WorkflowOwner", (), {})()
    owner.current_project_root = str(tmp_path)
    owner.projecthome = str(ROOT_DIR)
    owner._shared_active_project_root = lambda: str(tmp_path)
    owner._workflow_step_for_method = lambda _method: step
    owner._workflow_step_paths = lambda selected_step: (
        str(tmp_path / selected_step.workflow_source),
        str(tmp_path / selected_step.complete_destination),
        str(tmp_path / selected_step.workflow_handshake),
    )
    owner._first_workflow_source_document = mypixler.PixlerMain._first_workflow_source_document

    def finish(selected_step, **kwargs):
        advance_page_workflow_files(str(tmp_path), selected_step, stage_source=True)
        finished.append((selected_step, kwargs))

    owner._finish_page_workflow_step = finish
    owner.statusBar = lambda: type(
        "StatusBar",
        (),
        {"showMessage": lambda _self, message, _timeout: messages.append(message)},
    )()
    monkeypatch.setattr(qtw.QDialog, "exec_", lambda _dialog: qtw.QDialog.Accepted)

    mypixler.PixlerMain.actionstage_pdf(owner)

    assert not source_path.exists()
    assert (tmp_path / "complete/section/section.pdf").read_bytes() == b"section source"
    assert (tmp_path / "workflow/extract/section.pdf").read_bytes() == b"section source"
    assert finished == [
        (
            step,
            {"details": {"source": "actionstage_pdf"}, "stage_source": True},
        )
    ]
    assert messages == [f"Staged source PDF accepted: {tmp_path / 'complete/section/section.pdf'}"]
    app.processEvents()


def test_mypixler_extract_action_populates_all_section_staging_folders(tmp_path, monkeypatch) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    mypixler = _load_mypixler_module()
    source_path = (
        tmp_path
        / "Model/Project/Images/MyPixler/SourceStaged/Complete/pdf_staged_src_image/source.pdf"
    )
    source_path.parent.mkdir(parents=True)
    _create_test_pdf(source_path)
    section_names = ("FrontSection", "MiddleSections", "VerseSections", "BackSection")
    steps = [
        PageWorkflowStep(
            sequence=f"SSH{index}",
            description=f"stage {section_name}",
            milestone_name=f"{section_name}_staged",
            page_section=section_name,
            module="MyPixler",
            ui_trigger="actionStage_pdf.triggered",
            method="actionstage_pdf",
            dialog_ui="StageDialog",
            notes="",
            workflow_source=(
                f"workflow/{index}_{section_name}/_book_40_Matthew"
                if section_name == "VerseSections"
                else f"workflow/{index}_{section_name}"
            ),
            complete_destination=(
                f"complete/{index}_{section_name}/_book_40_Matthew"
                if section_name == "VerseSections"
                else f"complete/{index}_{section_name}"
            ),
            workflow_handshake=(
                f"workflow/next_{index}/_book_40_Matthew"
                if section_name == "VerseSections"
                else f"workflow/next_{index}"
            ),
        )
        for index, section_name in enumerate(section_names, start=1)
    ]
    owner = type("WorkflowOwner", (), {})()
    owner.current_project_root = str(tmp_path)
    owner.projecthome = str(ROOT_DIR)
    owner._shared_active_project_root = lambda: str(tmp_path)
    owner._workflow_step_for_method = lambda _method: None
    owner._first_workflow_source_document = mypixler.PixlerMain._first_workflow_source_document
    owner._workflow_steps_for_method = lambda _method: steps
    owner._pending_dialog_workflow_steps = lambda _method, _root: steps
    owner._extract_source_pdf_sections = (
        lambda: mypixler.PixlerMain._extract_source_pdf_sections(owner)
    )
    saved_states = []
    owner._load_extract_dialog_state = lambda _root: {}
    owner._save_extract_dialog_state = lambda _root, state: saved_states.append(
        json.loads(json.dumps(state))
    )
    dialog_uis = {}

    class CapturingExtractDialog(mypixler.Ui_ExtractDialog):
        def setupUi(self, dialog):
            super().setupUi(dialog)
            dialog_uis[dialog] = self

    monkeypatch.setattr(mypixler, "Ui_ExtractDialog", CapturingExtractDialog)
    owner._install_extract_context_menu = lambda _dialog, _ui, _skip_result, **_kwargs: None

    def accept_dialog(dialog):
        if "VerseSections" in dialog.windowTitle():
            dialog_uis[dialog].DestinationLineEdit.setText(
                str(tmp_path / "workflow/3_VerseSections")
            )
        return qtw.QDialog.Accepted

    owner._run_non_modal_dialog = accept_dialog
    owner._confirm_extract_overwrite = lambda _dialog, _destination: True
    completed_steps = []
    owner._finish_page_workflow_step = lambda selected_step, **kwargs: (
        advance_page_workflow_files(str(tmp_path), selected_step, stage_source=True),
        completed_steps.append((selected_step, kwargs)),
    )
    owner.workflow_tracker = type(
        "Tracker",
        (),
        {
            "_load_project_context": lambda _self, _root: {
                "NumberPages": 2,
                "SourcePageSections": [],
            }
        },
    )()
    messages = []
    owner.statusBar = lambda: type(
        "StatusBar",
        (),
        {"showMessage": lambda _self, message, _timeout: messages.append(message)},
    )()
    extracted_paths = mypixler.PixlerMain.actionextract_pdf(owner)

    assert len(extracted_paths) == 4
    for index, section_name in enumerate(section_names, start=1):
        destination = tmp_path / f"complete/{index}_{section_name}"
        if section_name == "VerseSections":
            destination /= "_book_40_Matthew"
        assert Path(extracted_paths[index - 1]).parent == destination
        assert Path(extracted_paths[index - 1]).is_file()
    assert len(completed_steps) == 4
    assert all(kwargs["stage_source"] is True for _step, kwargs in completed_steps)
    assert messages == ["Extracted source PDF into 4 section staging folders."]
    assert saved_states[-1]["section_index"] == 0
    assert {
        section_state["status"]
        for section_state in saved_states[-1]["sections"].values()
    } == {"complete"}
    app.processEvents()


def test_extract_dialog_keeps_parent_enabled_and_processes_events() -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    mypixler = _load_mypixler_module()
    parent = qtw.QMainWindow()
    dialog = qtw.QDialog(parent)
    observed = []

    def accept_while_parent_is_available():
        observed.append(parent.isEnabled())
        dialog.accept()

    qtc.QTimer.singleShot(0, accept_while_parent_is_available)
    result = mypixler.PixlerMain._run_non_modal_dialog(dialog)

    assert result == qtw.QDialog.Accepted
    assert observed == [True]
    assert dialog.windowModality() == qtc.Qt.NonModal
    parent.close()
    app.processEvents()


def test_extraction_progress_indicator_is_temporary_and_non_modal() -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    mypixler = _load_mypixler_module()
    parent = qtw.QMainWindow()
    parent.show()

    progress = mypixler.PixlerMain._show_extraction_progress(
        object(),
        parent,
        "Extracting source pages...",
    )

    assert progress.isVisible()
    assert progress.minimum() == 0
    assert progress.maximum() == 0
    assert progress.windowModality() == qtc.Qt.NonModal
    assert parent.isEnabled()
    assert progress.labelText() == "Extracting source pages..."

    mypixler.PixlerMain._close_extraction_progress(progress)

    assert not progress.isVisible()
    parent.close()
    app.processEvents()


def test_extract_dialog_exposes_workflow_controls_and_persists_state(tmp_path) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    mypixler = _load_mypixler_module()
    dialog = qtw.QDialog()
    ui = mypixler.Ui_ExtractDialog()
    ui.setupUi(dialog)
    owner = type("WorkflowOwner", (), {})()
    owner._extract_dialog_state_manager = mypixler.PixlerMain._extract_dialog_state_manager
    state = {"section_index": 2, "sections": {"SSHV": {"first_page": "7"}}}

    mypixler.PixlerMain._save_extract_dialog_state(owner, str(tmp_path), state)
    restored = mypixler.PixlerMain._load_extract_dialog_state(owner, str(tmp_path))

    assert dialog.windowModality() == qtc.Qt.NonModal
    assert ui.MakeDefaultCheckBox.isEnabled() is False
    assert ui.MilestoneOverrideCheckBox.isChecked() is False
    assert ui.PreviousButton.text() == "Previous"
    assert ui.NextButton.text() == "Next"
    assert ui.SkipButton.text() == "Skip"
    assert ui.HelpButton.text() == "Help"
    assert restored == state
    dialog.close()
    app.processEvents()


def test_extract_overwrite_warning_can_preserve_existing_output(tmp_path, monkeypatch) -> None:
    mypixler = _load_mypixler_module()
    existing = tmp_path / "existing.pdf"
    existing.write_bytes(b"keep")
    monkeypatch.setattr(
        qtw.QMessageBox,
        "warning",
        lambda *_args, **_kwargs: qtw.QMessageBox.No,
    )

    accepted = mypixler.PixlerMain._confirm_extract_overwrite(None, str(tmp_path))

    assert accepted is False
    assert existing.read_bytes() == b"keep"


def test_extract_skip_override_records_progress_milestone(tmp_path) -> None:
    mypixler = _load_mypixler_module()
    recorded = []
    synchronized = []
    refreshed = []
    step = type(
        "WorkflowStep",
        (),
        {"milestone_name": "src_pages_front_matter_staged"},
    )()
    owner = type("WorkflowOwner", (), {})()
    owner.refimgpath = ""
    owner.current_project_page = 3
    owner._page_number_from_path = lambda _path, fallback: fallback
    owner.workflow_tracker = type(
        "Tracker",
        (),
        {
            "record_page_milestone": lambda _self, *args, **kwargs: recorded.append(
                (args, kwargs)
            )
        },
    )()
    owner._sync_project_page_state = lambda *args, **kwargs: synchronized.append(
        (args, kwargs)
    )
    owner._refresh_project_status = lambda root: refreshed.append(root)

    mypixler.PixlerMain._record_extract_skip_override(owner, str(tmp_path), step)

    assert recorded == [
        (
            (str(tmp_path), 3, "src_pages_front_matter_staged"),
            {
                "module_name": "MyPixler",
                "details": {"source": "extract_dialog_skip", "override": True},
            },
        )
    ]
    assert synchronized == [
        ((str(tmp_path),), {"page_milestone": "src_pages_front_matter_staged"})
    ]
    assert refreshed == [str(tmp_path)]


def test_single_page_extraction_skip_persists_complete_status(
    tmp_path,
    monkeypatch,
) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    mypixler = _load_mypixler_module()
    step = PageWorkflowStep(
        sequence="ES2M",
        description="extract middle matter pages",
        milestone_name="src_pages_middle_matter_extracted",
        page_section="MiddleSections",
        module="MyPixler",
        ui_trigger="actionExtract_pdf.triggered",
        method="actionextract_pdf",
        dialog_ui="ExtractDialog",
        notes="",
        workflow_source="workflow/8/_book_40_Matthew",
        complete_destination="complete/8/_book_40_Matthew",
        workflow_handshake="workflow/9/_book_40_Matthew",
    )
    source_dir = tmp_path / step.workflow_source
    source_dir.mkdir(parents=True)
    _create_test_pdf(source_dir / "middle.pdf")
    state = {}
    recorded = []
    owner = type("WorkflowOwner", (), {})()
    owner.current_project_root = str(tmp_path)
    owner.projecthome = str(ROOT_DIR)
    owner._shared_active_project_root = lambda: str(tmp_path)
    owner._workflow_step_paths = lambda selected_step: (
        str(tmp_path / selected_step.workflow_source),
        str(tmp_path / selected_step.complete_destination),
        str(tmp_path / selected_step.workflow_handshake),
    )
    owner._first_workflow_source_document = mypixler.PixlerMain._first_workflow_source_document
    owner._load_extract_dialog_state = lambda _root: state
    owner._save_extract_dialog_state = lambda _root, _state: None
    owner._install_extract_context_menu = lambda *_args, **_kwargs: None
    owner._record_extract_skip_override = lambda _root, selected_step: recorded.append(selected_step)

    def skip_dialog(dialog):
        ui = dialog.findChild(qtw.QPushButton, "SkipButton")
        assert ui is not None
        ui.click()
        return dialog.result()

    owner._run_non_modal_dialog = skip_dialog
    monkeypatch.setattr(
        qtw.QMessageBox,
        "question",
        lambda *_args, **_kwargs: qtw.QMessageBox.Yes,
    )

    extracted = mypixler.PixlerMain.actionextract_staged_pdf_pages(owner, step)

    saved = state["single_page_sections"]["ES2M"]
    assert extracted == []
    assert saved["status"] == "complete"
    assert saved["completion_source"] == "skip"
    assert recorded == [step]
    app.processEvents()


def test_completed_dialog_steps_leave_and_reenter_when_tracker_changes(tmp_path) -> None:
    mypixler = _load_mypixler_module()
    completed_step = type("WorkflowStep", (), {"milestone_name": "front_done"})()
    pending_step = type("WorkflowStep", (), {"milestone_name": "middle_pending"})()
    tracking_state = {
        "page_milestones": {
            "4": {
                "front_done": {"complete": True},
                "middle_pending": {"complete": False},
            }
        }
    }
    owner = type("WorkflowOwner", (), {})()
    owner.current_project_page = 4
    owner.workflow_tracker = type(
        "Tracker",
        (),
        {
            "_load_project_context": lambda _self, _root: {"CurrentProjectPage": 4},
            "load_tracking_state": lambda _self, _root: tracking_state,
        },
    )()
    owner._workflow_steps_for_method = lambda _method: [completed_step, pending_step]
    owner._completed_page_milestones = lambda root: (
        mypixler.PixlerMain._completed_page_milestones(owner, root)
    )

    pending = mypixler.PixlerMain._pending_dialog_workflow_steps(
        owner,
        "actionstage_pdf",
        str(tmp_path),
    )
    assert pending == [pending_step]

    tracking_state["page_milestones"]["4"]["front_done"]["complete"] = False
    pending = mypixler.PixlerMain._pending_dialog_workflow_steps(
        owner,
        "actionstage_pdf",
        str(tmp_path),
    )
    assert pending == [completed_step, pending_step]


def test_all_complete_section_loop_reports_sequences_before_source_lookup(
    tmp_path,
    monkeypatch,
) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    mypixler = _load_mypixler_module()
    steps = [
        type(
            "WorkflowStep",
            (),
            {
                "sequence": sequence,
                "milestone_name": milestone_name,
            },
        )()
        for sequence, milestone_name in (
            ("SSHF", "src_pages_front_matter_staged"),
            ("SSHM", "src_pages_middle_matter_staged"),
            ("SSHV", "src_pages_verses_staged"),
            ("SSHB", "src_pages_back_matter_staged"),
        )
    ]
    reports = []
    messages = []
    owner = type("WorkflowOwner", (), {})()
    owner.current_project_root = str(tmp_path)
    owner.projecthome = str(ROOT_DIR)
    owner._shared_active_project_root = lambda: str(tmp_path)
    owner._workflow_steps_for_method = lambda _method: steps
    owner._pending_dialog_workflow_steps = lambda _method, _root: []
    owner.statusBar = lambda: type(
        "StatusBar",
        (),
        {"showMessage": lambda _self, message, _timeout: messages.append(message)},
    )()
    monkeypatch.setattr(
        qtw.QMessageBox,
        "information",
        lambda _parent, title, message: reports.append((title, message)),
    )

    result = mypixler.PixlerMain._extract_source_pdf_sections(owner)

    assert result == []
    assert reports[0][0] == "Source Section Extraction"
    for step in steps:
        assert f"{step.sequence} - {step.milestone_name}" in reports[0][1]
    assert "MyServer > Project Settings > Milestone Settings" in reports[0][1]
    assert messages == ["Source Section Extraction is complete: SSHF, SSHM, SSHV, SSHB"]
    app.processEvents()


def test_complete_book_extraction_reports_milestone_before_source_lookup(
    tmp_path,
    monkeypatch,
) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    mypixler = _load_mypixler_module()
    step = PageWorkflowStep(
        sequence="EM2B",
        description="extract middle matter pages to books",
        milestone_name="middle_matter_pages_extracted_to_books",
        page_section="MiddleSections",
        module="MyPixler",
        ui_trigger="actionExtract_pdf.triggered",
        method="actionextract_pdf",
        dialog_ui="ExtractDialog",
        notes="",
        workflow_source="missing/workflow/source",
        complete_destination="missing/complete/destination",
        workflow_handshake="missing/workflow/handshake",
    )
    reports = []
    owner = type("WorkflowOwner", (), {})()
    owner.current_project_root = str(tmp_path)
    owner.projecthome = str(ROOT_DIR)
    owner._shared_active_project_root = lambda: str(tmp_path)
    owner._completed_page_milestones = lambda _root: {step.milestone_name}
    owner.statusBar = lambda: type("StatusBar", (), {"showMessage": lambda *_args: None})()
    monkeypatch.setattr(
        qtw.QMessageBox,
        "information",
        lambda _parent, title, message: reports.append((title, message)),
    )

    result = mypixler.PixlerMain.actionextract_book_pages(owner, step)

    assert result == []
    assert reports[0][0] == "MiddleSections Book Extraction"
    assert "EM2B - middle_matter_pages_extracted_to_books" in reports[0][1]
    app.processEvents()


def test_extract_completion_repaints_dialog_and_project_progress(
    tmp_path,
    monkeypatch,
) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    mypixler = _load_mypixler_module()
    refreshed = []
    processed = []
    ui = type("Ui", (), {"ProgressLabel": qtw.QLabel("pending")})()
    owner = type("WorkflowOwner", (), {})()
    owner._refresh_project_status = lambda root: refreshed.append(root)
    monkeypatch.setattr(
        qtw.QApplication,
        "processEvents",
        lambda *_args, **_kwargs: processed.append(True),
    )

    mypixler.PixlerMain._refresh_extract_completion_progress(
        owner,
        str(tmp_path),
        ui,
        "SSHV - src_pages_verses_staged | complete",
    )

    assert refreshed == [str(tmp_path)]
    assert ui.ProgressLabel.text() == "SSHV - src_pages_verses_staged | complete"
    assert processed == [True]
    app.processEvents()


def test_section_extraction_restores_saved_sequence_after_complete_steps_are_filtered(
    tmp_path,
) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    mypixler = _load_mypixler_module()
    source_path = (
        tmp_path
        / "Model/Project/Images/MyPixler/SourceStaged/Complete/pdf_staged_src_image/source.pdf"
    )
    source_path.parent.mkdir(parents=True)
    _create_test_pdf(source_path)
    section_names = ("FrontSection", "MiddleSections", "VerseSections", "BackSection")
    steps = [
        PageWorkflowStep(
            sequence=f"SSH{index}",
            description=f"stage {section_name}",
            milestone_name=f"{section_name}_staged",
            page_section=section_name,
            module="MyPixler",
            ui_trigger="actionStage_pdf.triggered",
            method="actionstage_pdf",
            dialog_ui="StageDialog",
            notes="",
            workflow_source=f"workflow/{index}_{section_name}",
            complete_destination=f"complete/{index}_{section_name}",
            workflow_handshake=f"workflow/next_{index}",
        )
        for index, section_name in enumerate(section_names, start=1)
    ]
    state = {
        "section_index": 2,
        "sections": {
            "SSH3": {
                "status": "complete",
                "destination": str(tmp_path / "workflow/3_VerseSections"),
            }
        },
    }
    shown_titles = []
    owner = type("WorkflowOwner", (), {})()
    owner.current_project_root = str(tmp_path)
    owner.projecthome = str(ROOT_DIR)
    owner._shared_active_project_root = lambda: str(tmp_path)
    owner._first_workflow_source_document = mypixler.PixlerMain._first_workflow_source_document
    owner._workflow_steps_for_method = lambda _method: steps
    owner._pending_dialog_workflow_steps = lambda _method, _root: steps[2:]
    owner._load_extract_dialog_state = lambda _root: state
    owner._save_extract_dialog_state = lambda _root, _state: None
    owner._install_extract_context_menu = lambda *_args, **_kwargs: None
    owner._run_non_modal_dialog = lambda dialog: (
        shown_titles.append(dialog.windowTitle()) or qtw.QDialog.Rejected
    )
    owner.workflow_tracker = type(
        "Tracker",
        (),
        {"_load_project_context": lambda _self, _root: {"NumberPages": 2}},
    )()
    owner.statusBar = lambda: type("StatusBar", (), {"showMessage": lambda *_args: None})()

    mypixler.PixlerMain._extract_source_pdf_sections(owner)

    assert shown_titles == ["Extract VerseSections source pages"]
    assert state["sections"]["SSH3"]["status"] == "pending"
    app.processEvents()


@pytest.mark.parametrize("shared_complete_folder", [False, True])
def test_mypixler_extracts_staged_section_into_single_page_workflow(
    tmp_path,
    monkeypatch,
    shared_complete_folder,
) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    mypixler = _load_mypixler_module()
    step = PageWorkflowStep(
        sequence="ES2F",
        description="extract front matter pages",
        milestone_name="src_pages_front_matter_extracted",
        page_section="FrontSection",
        module="MyPixler",
        ui_trigger="actionExtract_pdf.triggered",
        method="actionextract_pdf",
        dialog_ui="ExtractDialog",
        notes="",
        workflow_source="workflow/section",
        complete_destination=(
            "workflow/section" if shared_complete_folder else "complete/pages"
        ),
        workflow_handshake="workflow/next",
    )
    source_path = tmp_path / step.workflow_source / "section.pdf"
    source_path.parent.mkdir(parents=True)
    _create_test_pdf(source_path)
    messages = []
    finished = []
    owner = type("WorkflowOwner", (), {})()
    owner.current_project_root = str(tmp_path)
    owner.projecthome = str(ROOT_DIR)
    owner._shared_active_project_root = lambda: str(tmp_path)
    owner._workflow_step_for_method = lambda _method: step
    owner._workflow_step_paths = lambda selected_step: (
        str(tmp_path / selected_step.workflow_source),
        str(tmp_path / selected_step.complete_destination),
        str(tmp_path / selected_step.workflow_handshake),
    )
    owner._first_workflow_source_document = mypixler.PixlerMain._first_workflow_source_document

    def finish(selected_step, **kwargs):
        advance_page_workflow_files(str(tmp_path), selected_step)
        finished.append((selected_step, kwargs))

    owner._finish_page_workflow_step = finish
    owner.actionextract_staged_pdf_pages = (
        lambda selected_step=None: mypixler.PixlerMain.actionextract_staged_pdf_pages(
            owner,
            selected_step,
        )
    )
    owner._install_extract_context_menu = lambda _dialog, _ui, _skip_result, **_kwargs: None
    owner._run_non_modal_dialog = lambda _dialog: qtw.QDialog.Accepted
    owner._confirm_extract_overwrite = lambda _dialog, _destination, preserved_paths=(): True
    owner._load_extract_dialog_state = lambda _root: {}
    owner._save_extract_dialog_state = lambda _root, _state: None
    owner.statusBar = lambda: type(
        "StatusBar",
        (),
        {"showMessage": lambda _self, message, _timeout: messages.append(message)},
    )()
    extracted_paths = mypixler.PixlerMain.actionextract_pdf(owner)

    assert len(extracted_paths) == 2
    assert not source_path.exists()
    complete_names = sorted(
        path.name for path in (tmp_path / step.complete_destination).iterdir()
    )
    handshake_names = sorted(path.name for path in (tmp_path / "workflow/next").iterdir())
    assert complete_names == ["section_Page_001.pdf", "section_Page_002.pdf"]
    assert handshake_names == complete_names
    assert finished == [
        (
            step,
            {
                "details": {
                    "source": "actionextract_staged_pdf_pages",
                    "page_count": 2,
                }
            },
        )
    ]
    assert messages == ["Extracted 2 single-page PDFs for FrontSection."]
    app.processEvents()


@pytest.mark.parametrize(
    ("sequence", "page_section", "source_stage", "complete_stage", "handshake_stage"),
    [
        ("EM2B", "MiddleSections", "9", "9", "10"),
        ("EV2B", "VerseSections", "16", "16", "17"),
    ],
)
def test_mypixler_extracts_section_pages_into_each_book_folder(
    tmp_path,
    monkeypatch,
    sequence,
    page_section,
    source_stage,
    complete_stage,
    handshake_stage,
) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    mypixler = _load_mypixler_module()
    step = PageWorkflowStep(
        sequence=sequence,
        description="extract section pages to books",
        milestone_name=f"{page_section}_pages_extracted_to_books",
        page_section=page_section,
        module="MyPixler",
        ui_trigger="actionExtract_pdf.triggered",
        method="actionextract_pdf",
        dialog_ui="ExtractDialog",
        notes="",
        workflow_source=f"workflow/{source_stage}/_book_40_Matthew",
        complete_destination=f"complete/{complete_stage}/_book_40_Matthew",
        workflow_handshake=f"workflow/{handshake_stage}/_book_40_Matthew",
    )
    source_dir = tmp_path / step.workflow_source
    source_dir.mkdir(parents=True)
    _create_test_pdf(source_dir / "section.pdf")
    complete_root = tmp_path / f"complete/{complete_stage}"
    for book_name in ("book_40_Matthew", "book_41_Mark"):
        (complete_root / book_name).mkdir(parents=True)
    state = {}
    messages = []
    finished = []
    owner = type("WorkflowOwner", (), {})()
    owner.current_project_root = str(tmp_path)
    owner.projecthome = str(ROOT_DIR)
    owner._shared_active_project_root = lambda: str(tmp_path)
    owner._workflow_step_for_method = lambda _method: step
    owner._workflow_step_paths = lambda selected_step: (
        str(tmp_path / selected_step.workflow_source),
        str(tmp_path / selected_step.complete_destination),
        str(tmp_path / selected_step.workflow_handshake),
    )
    owner._first_workflow_source_document = mypixler.PixlerMain._first_workflow_source_document
    owner._book_stage_directories = mypixler.PixlerMain._book_stage_directories
    owner._book_stage_root = mypixler.PixlerMain._book_stage_root
    owner._load_extract_dialog_state = lambda _root: state
    owner._save_extract_dialog_state = lambda _root, _state: None
    owner._install_extract_context_menu = lambda *_args, **_kwargs: None
    owner._run_non_modal_dialog = lambda _dialog: qtw.QDialog.Accepted
    owner._confirm_extract_overwrite = lambda *_args, **_kwargs: True

    def finish(selected_step, **kwargs):
        advance_page_workflow_files(str(tmp_path), selected_step)
        finished.append((selected_step, kwargs))

    owner._finish_page_workflow_step = finish
    owner.actionextract_book_pages = lambda selected_step: (
        mypixler.PixlerMain.actionextract_book_pages(owner, selected_step)
    )
    owner.statusBar = lambda: type(
        "StatusBar",
        (),
        {"showMessage": lambda _self, message, _timeout: messages.append(message)},
    )()

    extracted_paths = mypixler.PixlerMain.actionextract_pdf(owner)

    assert len(extracted_paths) == 2
    assert (complete_root / "book_40_Matthew/section_Page_001.pdf").is_file()
    assert (complete_root / "book_41_Mark/section_Page_002.pdf").is_file()
    assert (tmp_path / f"workflow/{handshake_stage}/book_40_Matthew/section_Page_001.pdf").is_file()
    assert (tmp_path / f"workflow/{handshake_stage}/book_41_Mark/section_Page_002.pdf").is_file()
    assert not source_dir.exists()
    assert finished[0][0].workflow_source == f"workflow/{source_stage}"
    assert finished[0][1]["details"] == {
        "source": "actionextract_book_pages",
        "book_count": 2,
        "page_count": 2,
    }
    assert messages == ["Extracted 2 pages into 2 book folders."]
    session_items = json.loads(
        (tmp_path / "Model/Project/Data/json/Session.json").read_text(encoding="utf-8")
    )
    session_values = {item["Setting"]: item["CurrentValue"] for item in session_items}
    assert session_values["self.bookabbr"] == "Mar"
    assert session_values["self.bookmarkdown"] == "_book_41_Mark"
    assert session_values["self.current_book_folder"] == "book_41_Mark"
    app.processEvents()


def test_mypixler_middle_matter_skips_do_not_consume_source_pages(
    tmp_path,
    monkeypatch,
) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    mypixler = _load_mypixler_module()
    step = PageWorkflowStep(
        sequence="EM2B",
        description="extract middle matter pages to books",
        milestone_name="MiddleSections_pages_extracted_to_books",
        page_section="MiddleSections",
        module="MyPixler",
        ui_trigger="actionExtract_pdf.triggered",
        method="actionextract_pdf",
        dialog_ui="ExtractDialog",
        notes="",
        workflow_source="workflow/9/_book_40_Matthew",
        complete_destination="complete/9/_book_40_Matthew",
        workflow_handshake="workflow/10/_book_40_Matthew",
    )
    source_dir = tmp_path / step.workflow_source
    source_dir.mkdir(parents=True)
    _create_test_pdf(source_dir / "middle.pdf")
    complete_root = tmp_path / "complete/9"
    book_names = ("book_40_Matthew", "book_41_Mark", "book_42_Luke")
    for book_name in book_names:
        (complete_root / book_name).mkdir(parents=True)

    state = {}
    finished = []
    messages = []
    dialog_results = iter(
        (
            qtw.QDialog.Accepted + 3,
            qtw.QDialog.Accepted,
            qtw.QDialog.Accepted + 3,
        )
    )
    owner = type("WorkflowOwner", (), {})()
    owner.current_project_root = str(tmp_path)
    owner.projecthome = str(ROOT_DIR)
    owner._shared_active_project_root = lambda: str(tmp_path)
    owner._workflow_step_paths = lambda selected_step: (
        str(tmp_path / selected_step.workflow_source),
        str(tmp_path / selected_step.complete_destination),
        str(tmp_path / selected_step.workflow_handshake),
    )
    owner._book_stage_directories = mypixler.PixlerMain._book_stage_directories
    owner._book_stage_root = mypixler.PixlerMain._book_stage_root
    owner._load_extract_dialog_state = lambda _root: state
    owner._save_extract_dialog_state = lambda _root, _state: None
    owner._install_extract_context_menu = lambda *_args, **_kwargs: None
    owner._run_non_modal_dialog = lambda _dialog: next(dialog_results)
    owner._confirm_extract_overwrite = lambda *_args, **_kwargs: True
    owner.statusBar = lambda: type(
        "StatusBar",
        (),
        {"showMessage": lambda _self, message, _timeout: messages.append(message)},
    )()

    def finish(selected_step, **kwargs):
        advance_page_workflow_files(str(tmp_path), selected_step)
        finished.append((selected_step, kwargs))

    owner._finish_page_workflow_step = finish
    monkeypatch.setattr(
        qtw.QMessageBox,
        "question",
        lambda *_args, **_kwargs: qtw.QMessageBox.Yes,
    )

    extracted_paths = mypixler.PixlerMain.actionextract_book_pages(owner, step)

    book_states = state["book_extractions"]["EM2B"]["books"]
    assert len(extracted_paths) == 1
    assert book_states["book_40_Matthew"]["status"] == "complete"
    assert book_states["book_40_Matthew"]["completion_source"] == "skip"
    assert book_states["book_40_Matthew"]["milestone_override"] is True
    assert book_states["book_41_Mark"]["status"] == "complete"
    assert book_states["book_41_Mark"]["completion_source"] == "extraction"
    assert book_states["book_41_Mark"]["first_page"] == "1"
    assert book_states["book_41_Mark"]["last_page"] == "1"
    assert book_states["book_42_Luke"]["status"] == "complete"
    assert book_states["book_42_Luke"]["completion_source"] == "skip"
    assert book_states["book_42_Luke"]["milestone_override"] is True
    assert finished[0][1]["details"]["page_count"] == 1
    assert not any("paused" in message.lower() for message in messages)
    app.processEvents()


def test_mypixler_book_loop_omits_complete_dialogs(tmp_path) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    mypixler = _load_mypixler_module()
    step = PageWorkflowStep(
        sequence="EM2B",
        description="extract middle matter pages to books",
        milestone_name="middle_matter_pages_extracted_to_books",
        page_section="MiddleSections",
        module="MyPixler",
        ui_trigger="actionExtract_pdf.triggered",
        method="actionextract_pdf",
        dialog_ui="ExtractDialog",
        notes="",
        workflow_source="workflow/9/_book_40_Matthew",
        complete_destination="complete/9/_book_40_Matthew",
        workflow_handshake="workflow/10/_book_40_Matthew",
    )
    source_dir = tmp_path / step.workflow_source
    source_dir.mkdir(parents=True)
    _create_test_pdf(source_dir / "middle.pdf")
    complete_root = tmp_path / "complete/9"
    for book_name in ("book_40_Matthew", "book_41_Mark", "book_42_Luke"):
        (complete_root / book_name).mkdir(parents=True)
    state = {
        "book_extractions": {
            "EM2B": {
                "book_index": 0,
                "milestone_complete": False,
                "books": {
                    "book_40_Matthew": {
                        "status": "complete",
                        "completion_source": "skip",
                    },
                    "book_41_Mark": {"status": "pending"},
                    "book_42_Luke": {
                        "status": "complete",
                        "completion_source": "extraction",
                    },
                },
            }
        }
    }
    shown_titles = []
    owner = type("WorkflowOwner", (), {})()
    owner.current_project_root = str(tmp_path)
    owner.projecthome = str(ROOT_DIR)
    owner._shared_active_project_root = lambda: str(tmp_path)
    owner._workflow_step_paths = lambda selected_step: (
        str(tmp_path / selected_step.workflow_source),
        str(tmp_path / selected_step.complete_destination),
        str(tmp_path / selected_step.workflow_handshake),
    )
    owner._first_workflow_source_document = mypixler.PixlerMain._first_workflow_source_document
    owner._book_stage_directories = mypixler.PixlerMain._book_stage_directories
    owner._book_stage_root = mypixler.PixlerMain._book_stage_root
    owner._load_extract_dialog_state = lambda _root: state
    owner._save_extract_dialog_state = lambda _root, _state: None
    owner._install_extract_context_menu = lambda *_args, **_kwargs: None
    owner._run_non_modal_dialog = lambda dialog: (
        shown_titles.append(dialog.windowTitle()) or qtw.QDialog.Rejected
    )
    owner.statusBar = lambda: type("StatusBar", (), {"showMessage": lambda *_args: None})()

    mypixler.PixlerMain.actionextract_book_pages(owner, step)

    assert shown_titles == ["Extract MiddleSections: book_41_Mark"]
    app.processEvents()


def test_mypixler_unchecked_book_milestone_restores_complete_dialogs_and_source(
    tmp_path,
) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    mypixler = _load_mypixler_module()
    predecessor = PageWorkflowStep(
        sequence="ES2M",
        description="extract middle matter source pages",
        milestone_name="src_pages_middle_matter_extracted",
        page_section="MiddleSections",
        module="MyPixler",
        ui_trigger="actionExtract_pdf.triggered",
        method="actionextract_pdf",
        dialog_ui="ExtractDialog",
        notes="",
        workflow_source="workflow/8/_book_40_Matthew",
        complete_destination="complete/8/_book_40_Matthew",
        workflow_handshake="workflow/9/_book_40_Matthew",
    )
    step = PageWorkflowStep(
        sequence="EM2B",
        description="extract middle matter pages to books",
        milestone_name="middle_matter_pages_extracted_to_books",
        page_section="MiddleSections",
        module="MyPixler",
        ui_trigger="actionExtract_pdf.triggered",
        method="actionextract_pdf",
        dialog_ui="ExtractDialog",
        notes="",
        workflow_source="workflow/9/_book_40_Matthew",
        complete_destination="complete/9/_book_40_Matthew",
        workflow_handshake="workflow/10/_book_40_Matthew",
    )
    recovered_source = tmp_path / predecessor.complete_destination
    recovered_source.mkdir(parents=True)
    _create_test_pdf(recovered_source / "middle_Page_001.pdf")
    complete_root = tmp_path / "complete/9"
    for book_name in ("book_40_Matthew", "book_41_Mark"):
        (complete_root / book_name).mkdir(parents=True)
    state = {
        "book_extractions": {
            "EM2B": {
                "book_index": 1,
                "milestone_complete": True,
                "books": {
                    "book_40_Matthew": {"status": "complete"},
                    "book_41_Mark": {"status": "complete"},
                },
            }
        }
    }
    shown = []
    owner = type("WorkflowOwner", (), {})()
    owner.current_project_root = str(tmp_path)
    owner.projecthome = str(ROOT_DIR)
    owner._shared_active_project_root = lambda: str(tmp_path)
    owner._workflow_step_paths = lambda selected_step: (
        str(tmp_path / selected_step.workflow_source),
        str(tmp_path / selected_step.complete_destination),
        str(tmp_path / selected_step.workflow_handshake),
    )
    owner._workflow_steps_for_method = lambda _method: [predecessor, step]
    owner._first_workflow_source_document = mypixler.PixlerMain._first_workflow_source_document
    owner._book_stage_directories = mypixler.PixlerMain._book_stage_directories
    owner._book_stage_root = mypixler.PixlerMain._book_stage_root
    owner._load_extract_dialog_state = lambda _root: state
    owner._save_extract_dialog_state = lambda _root, _state: None
    owner._install_extract_context_menu = lambda *_args, **_kwargs: None
    owner._run_non_modal_dialog = lambda dialog: (
        shown.append((dialog.windowTitle(), dialog.findChild(qtw.QLineEdit).text()))
        or qtw.QDialog.Rejected
    )
    owner.statusBar = lambda: type("StatusBar", (), {"showMessage": lambda *_args: None})()

    mypixler.PixlerMain.actionextract_book_pages(owner, step)

    books = state["book_extractions"]["EM2B"]["books"]
    assert shown[0][0] == "Extract MiddleSections: book_41_Mark"
    assert all(book["status"] == "pending" for book in books.values())
    assert state["book_extractions"]["EM2B"]["milestone_complete"] is False
    app.processEvents()


def test_combined_pdf_is_staged_for_mypixler(tmp_path) -> None:
    project_root = tmp_path / "Project"
    combined_path = (
        project_root
        / "Model/Project/Images/MyServer/source_images/pdf_combined_src_images/combined.pdf"
    )
    combined_path.parent.mkdir(parents=True)
    combined_path.write_bytes(b"combined source")

    staged_path = Path(stage_combined_project_pdf(str(project_root), str(combined_path)))

    assert staged_path == (
        project_root
        / "Model/Project/Images/MyPixler/SourceStaged/Workflow/pdf_staged_src_image/combined.pdf"
    )
    assert staged_path.read_bytes() == b"combined source"
    assert find_project_staged_pdf(str(project_root)) == str(staged_path)

    complete_path = Path(complete_project_staged_pdf_handoff(str(project_root)))

    assert not staged_path.exists()
    assert complete_path == (
        project_root
        / "Model/Project/Images/MyPixler/SourceStaged/Complete/pdf_staged_src_image/combined.pdf"
    )
    assert complete_path.read_bytes() == b"combined source"
    assert find_project_staged_pdf(str(project_root)) == str(complete_path)


def test_staged_pdf_handoff_respects_disabled_override(tmp_path) -> None:
    project_root = tmp_path / "Project"
    workflow_path = (
        project_root
        / "Model/Project/Images/MyPixler/SourceStaged/Workflow/pdf_staged_src_image/source.pdf"
    )
    complete_path = (
        project_root
        / "Model/Project/Images/MyPixler/SourceStaged/Complete/pdf_staged_src_image/source.pdf"
    )
    workflow_path.parent.mkdir(parents=True)
    complete_path.parent.mkdir(parents=True)
    workflow_path.write_bytes(b"new source")
    complete_path.write_bytes(b"existing source")

    with pytest.raises(FileExistsError):
        complete_project_staged_pdf_handoff(str(project_root), override=False)

    assert workflow_path.read_bytes() == b"new source"
    assert complete_path.read_bytes() == b"existing source"


def test_myserver_stage_action_completes_first_handoff(tmp_path, monkeypatch) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    myserver = _load_myserver_module()
    project_root = tmp_path / "Project"
    combined_path = (
        project_root
        / "Model/Project/Images/MyServer/source_images/pdf_combined_src_images/combined.pdf"
    )
    combined_path.parent.mkdir(parents=True)
    combined_path.write_bytes(b"combined source")
    recorded = []
    messages = []
    owner = type("WorkflowOwner", (), {})()
    owner.actionCombineSourcePages = lambda: str(combined_path)
    owner._active_project_root_for_source = lambda: str(project_root)
    owner._record_project_milestone = (
        lambda milestone, path, details=None: recorded.append((milestone, path, details))
    )
    owner.statusBar = lambda: type(
        "StatusBar",
        (),
        {"showMessage": lambda _self, message, _timeout: messages.append(message)},
    )()
    stage_dialogs = []

    class CapturingStageDialog(myserver.Ui_StageDialog):
        def setupUi(self, dialog):
            super().setupUi(dialog)
            stage_dialogs.append(self)

    monkeypatch.setattr(myserver, "Ui_StageDialog", CapturingStageDialog)
    monkeypatch.setattr(myserver, "stage_combined_project_pdf", stage_combined_project_pdf)
    monkeypatch.setattr(qtw.QDialog, "exec_", lambda _dialog: qtw.QDialog.Accepted)

    staged_path = myserver.MainWindow.actionStageSourcePages(owner)

    assert staged_path == find_project_staged_pdf(str(project_root))
    assert recorded == [
        (
            "combined_src_images_staged",
            staged_path,
            {"source": "combined_source_pdf"},
        )
    ]
    assert messages == [f"Staged source PDF for MyPixler: {staged_path}"]
    assert stage_dialogs[0].ProgressBar.value() == 100
    assert "Source PDF staged in MyPixler" in stage_dialogs[0].StatusLabel.text()
    app.processEvents()


@pytest.mark.parametrize(
    ("project_values", "expected_abbreviation"),
    [
        ({"self.bookmarkdown": "_book_41_Mark"}, "Mar"),
        ({}, "Mat"),
    ],
)
def test_myserver_restores_project_book_context(
    project_values,
    expected_abbreviation,
) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    myserver = _load_myserver_module()

    class ProjectSession:
        def values(self, _filename, _keys=None):
            return project_values

    owner = type("BookOwner", (), {})()
    owner.ui = type("Ui", (), {"bookComboBox": qtw.QComboBox()})()
    owner.ui.bookComboBox.addItems(["Mat", "Mar", "Luk"])
    owner.bookabbr = ""
    owner.bookmarkdown = ""
    owner._last_synced_book_markdown = ""
    owner._active_project_session_manager = lambda: ProjectSession()
    owner._apply_book_reference = lambda reference, persist=False: (
        myserver.MainWindow._apply_book_reference(owner, reference, persist=persist)
    )

    myserver.MainWindow._sync_book_combo_from_project_session(owner)

    assert owner.bookabbr == expected_abbreviation
    assert owner.ui.bookComboBox.currentText() == expected_abbreviation
    app.processEvents()


def test_myserver_manual_book_selection_updates_project_extraction_state() -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    myserver = _load_myserver_module()
    updates = []
    extraction_state = {
        "book_extractions": {
            "EM2B": {"book_index": 0},
            "EV2B": {"book_index": 0},
        }
    }

    class Session:
        def update(self, filename, values):
            updates.append((filename, values.copy()))

        def values(self, filename, _keys=None):
            if filename == "PixlerSession.json":
                return {"self.pdf_extraction_state": extraction_state}
            return {}

    owner = type("BookOwner", (), {})()
    owner.ui = type("Ui", (), {"bookComboBox": qtw.QComboBox()})()
    owner.ui.bookComboBox.addItems(["Mat", "Mar", "Luk"])
    owner.ui.bookComboBox.setCurrentText("Luk")
    owner.session_manager = Session()
    owner._last_synced_book_markdown = ""
    owner._active_project_session_manager = lambda: Session()
    owner._apply_book_reference = lambda reference, persist=False: (
        myserver.MainWindow._apply_book_reference(owner, reference, persist=persist)
    )

    myserver.MainWindow.selectBookCombo(owner)

    assert owner.bookabbr == "Luk"
    assert owner.bookmarkdown == "_book_42_Luke"
    assert extraction_state["book_extractions"]["EM2B"]["book_index"] == 2
    assert extraction_state["book_extractions"]["EV2B"]["book_index"] == 2
    assert any(
        filename == "Session.json" and values["self.bookmarkdown"] == "_book_42_Luke"
        for filename, values in updates
    )
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


def _create_single_page_pdf(pdf_path: Path) -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=80, height=120)
    with pdf_path.open("wb") as output_file:
        writer.write(output_file)


def _create_single_page_tiff(tiff_path: Path) -> None:
    Image.new("RGB", (80, 120), "white").save(tiff_path, format="TIFF")


def _wait_for_dock_load(dock: SourceReaderDock, timeout_ms: int = 10000) -> None:
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


def test_source_reader_dock_opens_without_waiting_for_source_preparation(tmp_path, monkeypatch) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    pdf_path = tmp_path / "source.pdf"
    _create_test_pdf(pdf_path)
    original_page_count = source_reader._source_page_count

    def delayed_page_count(source_path):
        time.sleep(0.25)
        return original_page_count(source_path)

    monkeypatch.setattr(source_reader, "_source_page_count", delayed_page_count)
    window = qtw.QMainWindow()
    window.show()
    app.processEvents()
    started_at = time.monotonic()
    dock = SourceReaderDock(str(pdf_path), window)
    window.addDockWidget(qtc.Qt.LeftDockWidgetArea, dock)
    dock.show_reader()
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


def test_pdf_source_collection_extracts_selected_pages_into_book_folder(tmp_path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    for page_number in range(1, 3):
        _create_test_pdf(source_dir / f"section_Part_{page_number:03d}.pdf")
    destination = tmp_path / "book_41_Mark"

    extracted = extract_pdf_source_pages(source_dir, destination, 2, 3)

    assert [Path(path).name for path in extracted] == [
        "section_Part_001_Page_002.pdf",
        "section_Part_002_Page_001.pdf",
    ]
    assert all(len(PdfReader(path).pages) == 1 for path in extracted)


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


def test_source_reader_renders_and_navigates_pages(tmp_path) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    pdf_path = tmp_path / "source.pdf"
    _create_test_pdf(pdf_path)

    viewer = SourceReaderDialog(str(pdf_path))

    assert type(viewer.source_reader_ui).__name__ == "Ui_SourceReader"
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

    viewer = SourceReaderDialog(str(tiff_path))

    assert viewer.page_count == 3
    assert viewer.page_index == 0
    assert viewer.page_label.pixmap() is not None
    assert not viewer.page_label.pixmap().isNull()
    viewer.next_page()
    assert viewer.page_index == 1
    assert viewer.page_spin.value() == 2
    assert app is not None
    viewer.close()


@pytest.mark.parametrize("extension", [".pdf", ".tif"])
def test_source_reader_rejects_single_page_documents(tmp_path, extension) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    source_path = tmp_path / f"single-page{extension}"
    if extension == ".pdf":
        _create_single_page_pdf(source_path)
    else:
        _create_single_page_tiff(source_path)

    with pytest.raises(ValueError, match="at least two pages"):
        SourceReaderDialog(str(source_path))

    assert app is not None


def test_source_reader_opens_another_document_without_project_registration_signal(
    tmp_path,
    monkeypatch,
) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    first_path = tmp_path / "first.pdf"
    replacement_path = tmp_path / "replacement.tif"
    _create_test_pdf(first_path)
    _create_test_tiff(replacement_path)
    window = qtw.QMainWindow()
    window.setCentralWidget(qtw.QWidget(window))
    dock = SourceReaderDock(str(first_path), window)
    window.addDockWidget(qtc.Qt.LeftDockWidgetArea, dock)
    window.show()
    dock.show_reader()
    _wait_for_dock_load(dock)
    initial_loads = []
    replacements = []
    dock.documentLoaded.connect(lambda path, pages: initial_loads.append((path, pages)))
    dock.documentReplaced.connect(lambda path, pages: replacements.append((path, pages)))
    monkeypatch.setattr(
        source_reader,
        "_choose_source_document",
        lambda _parent, _current: str(replacement_path),
    )

    dock.viewer.openRequested.emit()
    deadline = qtc.QDeadlineTimer(10000)
    while not replacements and not deadline.hasExpired():
        app.processEvents(qtc.QEventLoop.AllEvents, 50)

    assert not dock.is_loading
    assert initial_loads == []
    assert replacements == [(str(replacement_path), 3)]
    assert dock.pdf_path == str(replacement_path)
    assert dock.viewer.pdf_path == str(replacement_path)
    assert dock.page_count == 3
    assert dock.isVisible()
    assert window.isVisible()
    dock.close_automatically()
    app.processEvents()
    window.close()


def test_standalone_source_reader_opens_another_document_and_remains_modeless(
    tmp_path,
    monkeypatch,
) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    first_path = tmp_path / "first.pdf"
    replacement_path = tmp_path / "replacement.tif"
    _create_test_pdf(first_path)
    _create_test_tiff(replacement_path)
    parent = qtw.QDialog()
    reader = SourceReaderDialog(str(first_path), parent)
    parent.show()
    reader.show()
    monkeypatch.setattr(
        source_reader,
        "_choose_source_document",
        lambda _parent, _current: str(replacement_path),
    )

    reader.viewer.openRequested.emit()
    app.processEvents()

    assert not reader.isModal()
    assert reader.windowModality() == qtc.Qt.NonModal
    assert reader.viewer.pdf_path == str(replacement_path)
    assert reader.page_count == 3
    assert reader.isVisible()
    assert parent.isEnabled()
    reader.close()
    parent.close()


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
    monkeypatch.setattr("project_creation_wizard_dialog.SourceReaderDialog", FakeReader)

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


def test_source_reader_toolbar_tools_fit_at_narrow_docked_width(tmp_path) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    pdf_path = tmp_path / "source.pdf"
    _create_test_pdf(pdf_path)
    window = qtw.QMainWindow()
    host = qtw.QWidget(window)
    host.setLayout(qtw.QVBoxLayout())
    host.setFixedWidth(360)
    window.setCentralWidget(host)
    dock = SourceReaderDock(str(pdf_path), window, embedded_host=host)
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
        viewer.open_button,
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


def test_source_reader_docks_floats_hides_and_confirms_manual_close(tmp_path, monkeypatch) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    pdf_path = tmp_path / "source.pdf"
    _create_test_pdf(pdf_path)
    window = qtw.QMainWindow()
    central_widget = qtw.QWidget(window)
    window.setCentralWidget(central_widget)
    dock = SourceReaderDock(str(pdf_path), window)
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

    dock = SourceReaderDock(str(pdf_path), window)
    window.addDockWidget(qtc.Qt.LeftDockWidgetArea, dock)
    dock.show_reader()
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

    first_dock = SourceReaderDock(str(pdf_path), window)
    window.addDockWidget(qtc.Qt.LeftDockWidgetArea, first_dock)
    first_dock.show_reader()
    app.processEvents()
    _wait_for_dock_load(first_dock)
    assert window.width() > default_geometry.width()

    replacement_dock = SourceReaderDock(str(pdf_path), window)
    first_dock.close_automatically()
    window.addDockWidget(qtc.Qt.LeftDockWidgetArea, replacement_dock)
    replacement_dock.show_reader()
    app.processEvents()
    _wait_for_dock_load(replacement_dock)
    assert window.width() > default_geometry.width()

    replacement_dock.close_automatically()
    app.processEvents()
    assert window.geometry() == default_geometry
    window.close()


def test_source_reader_embeds_in_host_and_can_hide_float_redock_and_close(tmp_path, monkeypatch) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    pdf_path = tmp_path / "source.pdf"
    _create_test_pdf(pdf_path)
    window = qtw.QMainWindow()
    host = qtw.QWidget(window)
    host.setLayout(qtw.QVBoxLayout())
    window.setCentralWidget(host)
    dock = SourceReaderDock(str(pdf_path), window, embedded_host=host)
    window.addDockWidget(qtc.Qt.LeftDockWidgetArea, dock)
    window.show()
    dock.dock_in_host()
    app.processEvents()
    _wait_for_dock_load(dock)

    assert dock.is_reader_visible()
    assert not dock.is_reader_floating()
    assert dock.viewer.parentWidget() is host
    assert dock.viewer.isVisible()

    dock.viewer.hideRequested.emit()
    assert not dock.is_reader_visible()
    assert not dock.viewer.isVisible()
    dock.show_reader()
    assert dock.is_reader_visible()
    assert dock.viewer.isVisible()

    dock.toggle_floating()
    assert dock.is_reader_floating()
    assert dock.viewer.parentWidget() is dock

    dock.toggle_floating()
    assert not dock.is_reader_floating()
    assert dock.viewer.parentWidget() is host

    monkeypatch.setattr(qtw.QMessageBox, "question", lambda *_args, **_kwargs: qtw.QMessageBox.No)
    assert not dock.close()
    assert dock.is_reader_visible()

    monkeypatch.setattr(qtw.QMessageBox, "question", lambda *_args, **_kwargs: qtw.QMessageBox.Yes)
    assert dock.close()
    assert not host.isVisible()
    window.close()


def test_mypixler_displays_active_project_pdf_in_source_reader(tmp_path, monkeypatch) -> None:
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
    window.source_reader = None
    window.view_source_document_action = qtw.QAction("Open Source Reader", window)
    window.source_reader_visibility_action = qtw.QAction("Show Source Reader", window)
    window.source_reader_visibility_action.setCheckable(True)
    monkeypatch.setattr(window, "_shared_active_project_root", lambda: str(project_root))
    window.show()
    app.processEvents()

    assert window._project_source_pdf() == str(pdf_path)
    assert window._open_project_source_pdf_on_startup()
    assert window.source_reader is not None
    _wait_for_dock_load(window.source_reader)
    assert window.source_reader.pdf_path == str(pdf_path)
    assert window.pdf_page_count == 2
    assert window.dockWidgetArea(window.source_reader) == qtc.Qt.LeftDockWidgetArea
    assert not window.source_reader.is_reader_floating()
    assert window.source_reader.is_reader_visible()
    assert window.source_reader_visibility_action.isEnabled()
    assert window.source_reader_visibility_action.isChecked()

    window._set_source_reader_visibility(False)
    assert not window.source_reader.is_reader_visible()
    window._set_source_reader_visibility(True)
    assert window.source_reader.is_reader_visible()

    window._close_source_reader_automatically()
    assert window.source_reader is None
    assert not window.source_reader_visibility_action.isEnabled()
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