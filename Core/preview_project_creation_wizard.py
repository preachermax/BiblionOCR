import argparse
import os
import sys


def _repo_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _mainui_dir():
    return os.path.join(_repo_root(), "ViewController", "0-MainUI")


def _ensure_paths():
    root = _repo_root()
    mainui = _mainui_dir()
    if root not in sys.path:
        sys.path.insert(0, root)
    if mainui not in sys.path:
        sys.path.insert(0, mainui)


def _sanitize_runtime_env():
    _ensure_paths()
    from helpers.gui_runtime_env import sanitize_current_process_and_reexec

    sanitize_current_process_and_reexec()


def _default_projects_base_path():
    return os.path.join(_repo_root(), "Model", "Project")


def run_preview(projects_base_path, smoke_test=False):
    _sanitize_runtime_env()

    from PyQt5 import QtWidgets as qtw
    from helpers.project_creation_wizard_dialog import ProjectCreationWizardDialog

    app = qtw.QApplication.instance() or qtw.QApplication(sys.argv)
    dialog = ProjectCreationWizardDialog(projects_base_path=projects_base_path)

    if smoke_test:
        app.processEvents()
        print("ProjectCreationWizardDialog instantiated successfully")
        return 0

    dialog.show()
    dialog.raise_()
    dialog.activateWindow()
    return app.exec_()


def main():
    parser = argparse.ArgumentParser(description="Preview the Project Creation Wizard dialog")
    parser.add_argument(
        "--projects-base-path",
        default=_default_projects_base_path(),
        help="Base path used by the wizard when browsing provenance files",
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Instantiate the dialog and exit immediately",
    )
    args = parser.parse_args()

    exit_code = run_preview(
        projects_base_path=os.path.abspath(args.projects_base_path),
        smoke_test=args.smoke_test,
    )
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
