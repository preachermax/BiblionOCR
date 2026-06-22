from PyQt5 import QtCore as qtc
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg

class ImageLoadWorker(qtc.QObject):


    progress = qtc.pyqtSignal(int)
    finished = qtc.pyqtSignal(object)
    error = qtc.pyqtSignal(str)

    def __init__(self, path):
        super().__init__()
        self.path = path

    def run(self):
        try:
            from PyQt5 import QtGui as qtg
            import time

            self.progress.emit(5)

            # --- simulate staged loading (works even for fast loads)
            time.sleep(0.01)
            self.progress.emit(25)

            image = qtg.QImage(self.path)

            if image.isNull():
                self.error.emit("Failed to load image")
                return

            self.progress.emit(75)

            time.sleep(0.01)
            self.progress.emit(100)

            self.finished.emit(image)

        except Exception as e:
            self.error.emit(str(e))