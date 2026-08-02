from PyQt5 import QtCore as qtc
from PyQt5 import QtWidgets as qtw

from Core.Scanner import ScanWorker


def start_scan_workflow(
    owner,
    scanner_manager,
    request,
    on_progress,
    on_result,
    on_error,
    on_finished,
    before_start=None,
):
    if getattr(owner, "_scan_thread", None) is not None:
        qtw.QMessageBox.information(
            owner,
            "Scan In Progress",
            "Wait for the current scan task to finish.",
        )
        return None

    owner._scan_thread = qtc.QThread()
    owner._scan_worker = ScanWorker(scanner_manager, request)
    owner._scan_worker.moveToThread(owner._scan_thread)

    owner._scan_thread.started.connect(owner._scan_worker.run)
    owner._scan_worker.progress.connect(on_progress)
    owner._scan_worker.finished.connect(on_result)
    owner._scan_worker.error.connect(on_error)

    owner._scan_worker.finished.connect(owner._scan_thread.quit)
    owner._scan_worker.finished.connect(owner._scan_worker.deleteLater)
    owner._scan_worker.error.connect(owner._scan_thread.quit)
    owner._scan_worker.error.connect(owner._scan_worker.deleteLater)
    owner._scan_thread.finished.connect(owner._scan_thread.deleteLater)
    owner._scan_thread.finished.connect(on_finished)

    if before_start is not None:
        before_start()

    owner._scan_thread.start()
    return request