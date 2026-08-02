import json
import os
import shutil
import sys
import tempfile


def _build_fake_project(project_root):
    json_dir = os.path.join(project_root, "Model", "Project", "Data", "json")
    os.makedirs(json_dir, exist_ok=True)

    workflow_path = os.path.join(json_dir, "Workflow.json")
    with open(workflow_path, "w", encoding="utf-8") as handle:
        json.dump([
            {"Sequence": "SP1", "DialogUi": "Smoke", "DefaultSource": "Source"}
        ], handle, indent=2)


def main():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    module_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(module_dir, "..", ".."))

    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    from PyQt5 import QtWidgets
    from SessionManager import SessionManager
    from project_status_controller import ProjectStatusController
    from ProjectTrackingDialog import ProjectTrackingDialog

    temp_dir = tempfile.mkdtemp(prefix="biblion_project_status_")
    project_root = os.path.join(temp_dir, "SmokeProject")
    _build_fake_project(project_root)

    session_manager = SessionManager()
    session_path = session_manager.session_path("Session.json")
    original_session = None
    if os.path.exists(session_path):
        with open(session_path, "r", encoding="utf-8") as handle:
            original_session = handle.read()

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    original_message_box = QtWidgets.QMessageBox.information

    try:
        session_manager.set_active_project(project_root)

        window = QtWidgets.QMainWindow()
        controller = ProjectStatusController(
            window,
            "SmokeModule",
            session_manager=session_manager,
            refresh_interval_ms=60000,
        )

        QtWidgets.QApplication.processEvents()

        assert controller.resolve_project_root() == os.path.normpath(project_root)
        assert controller.project_name_status_label.text() == "Project: SmokeProject"
        assert controller.project_tracking_button.text() == "Milestones"

        dialog = ProjectTrackingDialog(controller.workflow_tracker, project_root, "SmokeModule", window)
        assert dialog.table.rowCount() > 0

        row_widgets = dialog._row_widgets["source_acquired"]
        row_widgets["weight"].setValue(25)
        row_widgets["complete"].setChecked(True)

        QtWidgets.QMessageBox.information = lambda *args, **kwargs: None
        dialog.save_rows()

        tracking_path = controller.workflow_tracker.tracking_file_path(project_root)
        with open(tracking_path, "r", encoding="utf-8") as handle:
            tracking_state = json.load(handle)

        source_milestone = tracking_state["milestones"]["source_acquired"]
        assert source_milestone["complete"] is True
        assert source_milestone["weight"] == 25
        assert source_milestone["updated_by"] == "SmokeModule:manual"

        controller.refresh_status(project_root)
        QtWidgets.QApplication.processEvents()

        assert "Project:" in controller.project_name_status_label.text()
        assert controller.project_overall_status_bar.value() > 0
        assert "Next:" in controller.workflow_status_label.text() or "Complete" in controller.workflow_status_label.text()

        print("TEST_OK")
        return 0
    finally:
        QtWidgets.QMessageBox.information = original_message_box
        if original_session is None:
            if os.path.exists(session_path):
                os.remove(session_path)
        else:
            with open(session_path, "w", encoding="utf-8") as handle:
                handle.write(original_session)
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())