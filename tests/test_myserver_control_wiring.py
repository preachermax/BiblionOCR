import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN_UI_DIR = ROOT / "ViewController" / "0-MainUI"


def _control_names(pattern: str, source: str) -> set[str]:
    return set(re.findall(pattern, source))


def test_myserver_module_toolbar_actions_are_connected() -> None:
    ui_source = (MAIN_UI_DIR / "MyServerUI.py").read_text(encoding="utf-8")
    runtime_source = (MAIN_UI_DIR / "MyServer.py").read_text(encoding="utf-8")

    toolbar_actions = _control_names(
        r"self\.ModulesToolBar\.addAction\(self\.(\w+)\)",
        ui_source,
    )
    connected_actions = _control_names(
        r"self\.ui\.(\w+)\.triggered\.connect\(",
        runtime_source,
    )

    assert toolbar_actions
    assert toolbar_actions <= connected_actions


def test_myserver_pushbuttons_are_connected() -> None:
    ui_source = (MAIN_UI_DIR / "MyServerUI.py").read_text(encoding="utf-8")
    runtime_source = (MAIN_UI_DIR / "MyServer.py").read_text(encoding="utf-8")

    pushbuttons = _control_names(
        r"self\.(\w+) = QtWidgets\.QPushButton\(self\.centralwidget\)",
        ui_source,
    )
    connected_pushbuttons = _control_names(
        r"self\.ui\.(\w+)\.clicked\.connect\(",
        runtime_source,
    )

    assert pushbuttons
    assert pushbuttons <= connected_pushbuttons


def test_myserver_uses_authoritative_scripture_project_manifest() -> None:
    runtime_source = (MAIN_UI_DIR / "MyServer.py").read_text(encoding="utf-8")

    assert 'os.pardir, "ScriptureProjectFolderList.txt"' in runtime_source
    assert 'folder_list_path=os.path.join(script_dir, "ProjectFolderList.txt")' not in runtime_source