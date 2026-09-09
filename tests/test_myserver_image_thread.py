from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys
from types import MethodType, SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MAIN_UI_DIR = ROOT / "ViewController" / "0-MainUI"
HELPERS_DIR = MAIN_UI_DIR / "helpers"
for import_path in (ROOT, MAIN_UI_DIR, HELPERS_DIR):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

os.environ.setdefault("BIBLION_GUI_ENV_SANITIZED", "1")

SPEC = importlib.util.spec_from_file_location("test_myserver_thread_module", MAIN_UI_DIR / "MyServer.py")
assert SPEC is not None and SPEC.loader is not None
MYSERVER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MYSERVER)


class FakeSignal:
    def __init__(self):
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)

    def emit(self, *args):
        for callback in list(self.callbacks):
            callback(*args)


class FakeThread:
    instances = []

    def __init__(self):
        self.started = FakeSignal()
        self.finished = FakeSignal()
        self.running = False
        self.__class__.instances.append(self)

    def start(self):
        self.running = True

    def quit(self, *_args):
        self.running = False
        self.finished.emit()

    def isRunning(self):
        return self.running

    def deleteLater(self, *_args):
        return None


class FakeWorker:
    instances = []

    def __init__(self, path):
        self.path = path
        self.progress = FakeSignal()
        self.finished = FakeSignal()
        self.error = FakeSignal()
        self.__class__.instances.append(self)

    def moveToThread(self, _thread):
        return None

    def run(self):
        return None

    def deleteLater(self, *_args):
        return None


def _server_probe():
    progress_bar = SimpleNamespace(
        setValue=lambda _value: None,
        setVisible=lambda _visible: None,
    )
    probe = SimpleNamespace(
        _thread=None,
        _worker=None,
        _active_tiff_load_path="",
        _pending_tiff_load_path="",
        _stack_path="",
        progress_bar=progress_bar,
        on_load_progress=lambda _value: None,
        on_image_loaded=lambda _image: None,
        on_load_error=lambda _message: None,
    )
    probe._on_tiff_stack_loaded = MethodType(MYSERVER.MainWindow._on_tiff_stack_loaded, probe)
    probe._on_tiff_stack_error = MethodType(MYSERVER.MainWindow._on_tiff_stack_error, probe)
    probe._on_tiff_stack_thread_finished = MethodType(
        MYSERVER.MainWindow._on_tiff_stack_thread_finished,
        probe,
    )
    probe.loadImageStackFromFile = MethodType(MYSERVER.MainWindow.loadImageStackFromFile, probe)
    return probe


def test_duplicate_tiff_request_keeps_running_thread_owned_and_error_releases_it(tmp_path) -> None:
    image_path = tmp_path / "scan_000003.tif"
    image_path.write_bytes(b"image")
    probe = _server_probe()
    FakeThread.instances.clear()
    FakeWorker.instances.clear()

    with patch.object(MYSERVER.qtc, "QThread", FakeThread), patch.object(
        MYSERVER,
        "TiffStackWorker",
        FakeWorker,
    ):
        assert probe.loadImageStackFromFile(str(image_path)) is True
        active_thread = probe._thread
        assert active_thread is not None and active_thread.isRunning()

        assert probe.loadImageStackFromFile(str(image_path)) is False
        assert probe._thread is active_thread
        assert len(FakeThread.instances) == 1
        assert len(FakeWorker.instances) == 1

        FakeWorker.instances[0].error.emit("decode failed")
        assert probe._thread is None
        assert not active_thread.isRunning()


def test_myserver_opens_project_source_pdf_docked_on_startup(tmp_path) -> None:
    pdf_path = tmp_path / "source.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n")
    open_calls = []
    probe = SimpleNamespace(
        source_reader=None,
        _project_source_pdf=lambda: str(pdf_path),
        _open_pdf_source=lambda path, floating: open_calls.append((path, floating)) or True,
    )

    result = MYSERVER.MainWindow._open_project_source_pdf_on_startup(probe)

    assert result is True
    assert open_calls == [(str(pdf_path), False)]