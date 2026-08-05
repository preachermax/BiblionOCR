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


def _open_launcher_wizard(window, mode: str) -> None:
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

    subprocess.Popen(
        [sys.executable, launcher_path, "--workflow-wizard", mode],
        creationflags=creationflags,
    )


def install_workflow_wizard_menu_actions(window, module_name: str) -> None:
    menu = _find_menu_from_window(window)
    if menu is None:
        return

    project_action_name = "actionProject_Workflow_Wizard"
    page_action_name = "actionPage_Workflow_Wizard"

    if getattr(window, project_action_name, None) is None:
        project_action = qtw.QAction("Project Workflow Wizard", window)
        project_action.setObjectName(project_action_name)
        project_action.setStatusTip(f"Open project workflow wizard from {module_name}")
        project_action.triggered.connect(lambda: _open_launcher_wizard(window, "project"))
        setattr(window, project_action_name, project_action)
        menu.addAction(project_action)

    if getattr(window, page_action_name, None) is None:
        page_action = qtw.QAction("Page Workflow Wizard", window)
        page_action.setObjectName(page_action_name)
        page_action.setStatusTip(f"Open page workflow wizard from {module_name}")
        page_action.triggered.connect(lambda: _open_launcher_wizard(window, "page"))
        setattr(window, page_action_name, page_action)
        menu.addAction(page_action)
