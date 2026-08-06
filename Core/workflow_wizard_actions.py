import os
import subprocess
import sys
from typing import Optional

from PyQt5 import QtWidgets as qtw


def _launcher_script_path() -> str:
    core_dir = os.path.abspath(os.path.dirname(__file__))
    project_root = os.path.abspath(os.path.join(core_dir, ".."))
    return os.path.join(project_root, "ViewController", "0-MainUI", "MyLauncher.py")


def _find_menu_from_window(window) -> Optional[qtw.QMenu]:
    ui = getattr(window, "ui", None)

    # Prefer explicit Project menu, then File, then Help fallback.
    for menu_name in ("menuProject", "menuFile", "menuHelp"):
        menu = getattr(window, menu_name, None)
        if isinstance(menu, qtw.QMenu):
            return menu
        if ui is not None:
            menu = getattr(ui, menu_name, None)
            if isinstance(menu, qtw.QMenu):
                return menu

    menu_bar = window.menuBar() if hasattr(window, "menuBar") else None
    if menu_bar is None:
        return None

    for action in menu_bar.actions():
        menu = action.menu()
        if menu is None:
            continue
        title = (menu.title() or "").strip().lower()
        if title == "project":
            return menu

    for action in menu_bar.actions():
        menu = action.menu()
        if menu is None:
            continue
        title = (menu.title() or "").strip().lower()
        if title == "file":
            return menu

    return menu_bar.addMenu("Project")


def _open_launcher_wizard(window, mode: str, requested_module: Optional[str] = None) -> None:
    launcher_path = _launcher_script_path()
    if not os.path.exists(launcher_path):
        qtw.QMessageBox.warning(
            window,
            "Workflow Wizard",
            f"MyLauncher entrypoint not found: {launcher_path}",
        )
        return

    creationflags = 0
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)

    command = [sys.executable, launcher_path, "--workflow-wizard", mode]
    if requested_module:
        command.extend(["--workflow-module", requested_module])

    subprocess.Popen(command, creationflags=creationflags)


def install_workflow_wizard_menu_actions(
    window,
    module_name: str,
    *,
    include_project_wizard: Optional[bool] = None,
    include_page_wizard: bool = True,
) -> None:
    menu = _find_menu_from_window(window)
    if menu is None:
        return

    if include_project_wizard is None:
        include_project_wizard = module_name == "MyServer"

    project_action_name = "actionProject_Workflow_Wizard"
    page_action_name = "actionPage_Workflow_Wizard"

    existing_project_action = getattr(window, project_action_name, None)
    if existing_project_action is None:
        existing_project_action = getattr(getattr(window, "ui", None), project_action_name, None)

    existing_page_action = getattr(window, page_action_name, None)
    if existing_page_action is None:
        existing_page_action = getattr(getattr(window, "ui", None), page_action_name, None)

    if not include_project_wizard and isinstance(existing_project_action, qtw.QAction):
        parent_menu = existing_project_action.parentWidget()
        if isinstance(parent_menu, qtw.QMenu):
            parent_menu.removeAction(existing_project_action)
        else:
            menu.removeAction(existing_project_action)
        existing_project_action.setVisible(False)
        existing_project_action.setEnabled(False)
        if getattr(window, project_action_name, None) is not None:
            setattr(window, project_action_name, None)

    if include_project_wizard and not isinstance(existing_project_action, qtw.QAction):
        project_action = qtw.QAction("Project Workflow Wizard", window)
        project_action.setObjectName(project_action_name)
        project_action.setStatusTip(f"Open project workflow wizard from {module_name}")
        project_action.triggered.connect(
            lambda: _open_launcher_wizard(window, "project", module_name)
        )
        setattr(window, project_action_name, project_action)
        menu.addAction(project_action)
    elif include_project_wizard and isinstance(existing_project_action, qtw.QAction):
        existing_project_action.setVisible(True)
        existing_project_action.setEnabled(True)
        setattr(window, project_action_name, existing_project_action)

    if include_page_wizard and not isinstance(existing_page_action, qtw.QAction):
        page_action = qtw.QAction("Page Workflow Wizard", window)
        page_action.setObjectName(page_action_name)
        page_action.setStatusTip(f"Open page workflow wizard from {module_name}")
        page_action.triggered.connect(
            lambda: _open_launcher_wizard(window, "page", module_name)
        )
        setattr(window, page_action_name, page_action)
        menu.addAction(page_action)
    elif include_page_wizard and isinstance(existing_page_action, qtw.QAction):
        existing_page_action.setVisible(True)
        existing_page_action.setEnabled(True)
        setattr(window, page_action_name, existing_page_action)
