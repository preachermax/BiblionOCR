from __future__ import annotations

import os
from pathlib import Path
import sys
import threading
from types import SimpleNamespace

from PyQt5 import QtCore as qtc
from PyQt5 import QtWidgets as qtw


ROOT = Path(__file__).resolve().parents[1]
HELPERS_DIR = ROOT / "ViewController" / "0-MainUI" / "helpers"
if str(HELPERS_DIR) not in sys.path:
    sys.path.insert(0, str(HELPERS_DIR))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from document_assembly import start_image_folder_assembly


def test_image_folder_assembly_runs_off_ui_thread_and_cleans_up(tmp_path) -> None:
    application = qtw.QApplication.instance() or qtw.QApplication([])
    owner = qtw.QMainWindow()
    action = qtw.QAction(owner)
    owner.ui = SimpleNamespace(actionAssembleImageFolder=action)
    source_dir = tmp_path / "pages"
    source_dir.mkdir()
    destination_path = tmp_path / "assembled.pdf"
    started = threading.Event()
    release = threading.Event()
    main_thread_id = threading.get_ident()
    worker_thread_ids = []
    completed_paths = []
    failures = []

    def assembler(_source_dir, output_path):
        worker_thread_ids.append(threading.get_ident())
        started.set()
        assert release.wait(2)
        Path(output_path).write_bytes(b"assembled")
        return str(output_path)

    assert start_image_folder_assembly(
        owner,
        str(source_dir),
        str(destination_path),
        completed_paths.append,
        failures.append,
        assembler=assembler,
    )
    assert started.wait(1)
    assert worker_thread_ids != [main_thread_id]
    assert not action.isEnabled()

    event_loop = qtc.QEventLoop()
    owner._document_assembly_thread.finished.connect(event_loop.quit)
    release.set()
    qtc.QTimer.singleShot(3000, event_loop.quit)
    event_loop.exec_()
    application.processEvents()

    assert failures == []
    assert completed_paths == [str(destination_path)]
    assert destination_path.read_bytes() == b"assembled"
    assert action.isEnabled()
    assert owner._document_assembly_thread is None
    assert owner._document_assembly_worker is None
    assert owner._document_assembly_progress is None
    owner.close()
