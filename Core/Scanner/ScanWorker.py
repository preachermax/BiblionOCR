from PyQt5 import QtCore as qtc


class ScanWorker(qtc.QObject):
    progress = qtc.pyqtSignal(int)
    finished = qtc.pyqtSignal(object)
    error = qtc.pyqtSignal(str)

    def __init__(self, scan_manager, request):
        super().__init__()
        self.scan_manager = scan_manager
        self.request = request

    def run(self):
        try:
            self.progress.emit(10)
            result = self.scan_manager.run_scan(self.request)
            self.progress.emit(100)
            self.finished.emit(result)
        except Exception as exc:
            self.error.emit(str(exc))