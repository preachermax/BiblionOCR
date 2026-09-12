import importlib.util
import os
import sys
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MAIN_UI_DIR = ROOT / "ViewController" / "0-MainUI"
if str(MAIN_UI_DIR) not in sys.path:
    sys.path.insert(0, str(MAIN_UI_DIR))

SPEC = importlib.util.spec_from_file_location(
    "test_myserver_module_launches_module",
    MAIN_UI_DIR / "MyServer.py",
)
assert SPEC is not None
assert SPEC.loader is not None
MYSERVER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MYSERVER)


EXPECTED_MODULE_PATHS = {
    "OpenWithMyScanner": ROOT / "ViewController" / "0-MainUI" / "MyScanner.py",
    "OpenWithMyExplorer": ROOT / "ViewController" / "0-MainUI" / "MyExplorer.py",
    "OpenWithMyPixler": ROOT / "ViewController" / "1-PreProcess" / "MyPixler.py",
    "OpenWithMyBoxer": ROOT / "ViewController" / "1-PreProcess" / "MyBoxer.py",
    "OpenWithMyGlypher": ROOT / "ViewController" / "1-PreProcess" / "MyGlypher.py",
    "OpenWithMyReader": ROOT / "ViewController" / "2-TrainTesseract" / "MyReader.py",
    "OpenWithMyGrounder": ROOT / "ViewController" / "2-TrainTesseract" / "MyGrounder.py",
    "OpenWithMyTrainer": ROOT / "ViewController" / "2-TrainTesseract" / "MyTrainer.py",
    "OpenWithMyLexer": ROOT / "ViewController" / "3-Process" / "MyLexer.py",
    "OpenWithMyResolver": ROOT / "ViewController" / "3-Process" / "MyResolver.py",
    "OpenWithMyVersifier": ROOT / "ViewController" / "3-Process" / "MyVersifier.py",
    "OpenWithMyWriter": ROOT / "ViewController" / "4-PostProcess" / "MyWriter.py",
}


def test_myserver_module_launch_actions_resolve_existing_stage_scripts() -> None:
    window = MYSERVER.MainWindow.__new__(MYSERVER.MainWindow)
    window.imgpath = ""
    window._stack_path = ""

    launched_commands = []

    def record_launch(command, **_kwargs):
        launched_commands.append(command)
        return mock.Mock(pid=1234)

    with mock.patch.object(MYSERVER.subprocess, "Popen", side_effect=record_launch), mock.patch.object(
        MYSERVER.MainWindow,
        "_projects_base_path",
        return_value=str(ROOT),
    ):
        for handler_name in EXPECTED_MODULE_PATHS:
            getattr(window, handler_name)()

    launched_by_name = {
        os.path.basename(command[1]): Path(command[1]).resolve()
        for command in launched_commands
    }
    expected_by_name = {
        path.name: path.resolve()
        for path in EXPECTED_MODULE_PATHS.values()
    }

    assert launched_by_name == expected_by_name
    assert all(path.is_file() for path in launched_by_name.values())


def test_myserver_sends_current_image_and_caller_to_mypixler(tmp_path) -> None:
    source_path = tmp_path / "page.tif"
    source_path.write_bytes(b"source")
    return_path = tmp_path / "returned.tif"
    window = MYSERVER.MainWindow.__new__(MYSERVER.MainWindow)
    window.imgpath = str(source_path)
    window._stack_path = ""
    window.pending_pixler_source_path = ""
    window.pixler_return_path = ""

    with mock.patch.object(MYSERVER.subprocess, "Popen", return_value=mock.Mock(pid=1234)) as popen, mock.patch.object(
        MYSERVER.MainWindow,
        "_sync_project_page_state",
    ), mock.patch.object(
        MYSERVER.MainWindow,
        "_create_pixler_return_path",
        return_value=str(return_path),
    ), mock.patch.object(
        MYSERVER.MainWindow,
        "_start_pixler_return_monitor",
    ) as start_monitor:
        window.OpenWithMyPixler()

    command = popen.call_args.args[0]
    assert Path(command[1]).resolve() == EXPECTED_MODULE_PATHS["OpenWithMyPixler"].resolve()
    assert command[2:] == [
        "--subprocess-mode",
        "--return-path",
        str(return_path),
        "--caller",
        "MyServer",
        str(source_path),
    ]
    assert window.pending_pixler_source_path == str(source_path)
    start_monitor.assert_called_once_with()


def test_myserver_launches_biblion_scheduler_wrapper() -> None:
    window = MYSERVER.MainWindow.__new__(MYSERVER.MainWindow)

    with mock.patch.object(MYSERVER.subprocess, "Popen", return_value=mock.Mock(pid=1234)) as popen:
        window.OpenWithBiblionScheduler()

    launcher = ROOT / "launchers" / "run-biblionscheduler.sh"
    assert launcher.is_file()
    popen.assert_called_once_with([str(launcher)])