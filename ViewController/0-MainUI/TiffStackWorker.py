# TiffStackWorker.py

from PyQt5 import QtCore as qtc

class TiffStackWorker(qtc.QObject):
    progress = qtc.pyqtSignal(int)
    finished = qtc.pyqtSignal(object)  # QImage
    error = qtc.pyqtSignal(str)

    def __init__(self, filepath):
        super().__init__()
        self.filepath = filepath  # ✅ THIS WAS MISSING

    def run(self):
        try:
            import tiffcapture
            import qimage2ndarray

            self.progress.emit(5)

            tif = tiffcapture.opentiff(self.filepath)

            if tif is None:
                raise RuntimeError("Failed to open TIFF")

            total = max(1, tif.length)

            self.progress.emit(25)

            frame = tif.find_and_read(0)

            if frame is None:
                raise RuntimeError("Failed to read first frame")

            qimage = qimage2ndarray.array2qimage(frame, normalize=True)

            self.progress.emit(100)

            self.finished.emit(qimage)

        except Exception as e:
            self.error.emit(f"Invalid TIFF: {str(e)}")

# class TiffStackWorker(qtc.QObject):
    # """
    # Worker for loading multi-page TIFF stacks using tiffcapture.

    # Emits:
    #     progress(int): Loading progress (0–100)
    #     finished(object): Loaded tiffcapture handle
    #     error(str): Error message
    # """

    # progress = qtc.pyqtSignal(int)
    # finished = qtc.pyqtSignal(object)
    # error = qtc.pyqtSignal(str)

    # def __init__(self, path):
    #     super().__init__()
    #     self.path = path

    # def run(self):
    #     try:
    #         import tiffcapture

    #         tif = tiffcapture.opentiff(self.filepath)

    #         if tif is None:
    #             raise RuntimeError("Failed to open TIFF")

    #         # total frames
    #         total = max(1, tif.length)

    #         # load first frame (like your app does)
    #         frame = tif.find_and_read(0)

    #         if frame is None:
    #             raise RuntimeError("Failed to read first frame")

    #         # emit some progress (fake but useful)
    #         self.progress.emit(25)

    #         import qimage2ndarray
    #         qimage = qimage2ndarray.array2qimage(frame, normalize=True)

    #         self.progress.emit(100)

    #         self.finished.emit(qimage)

    #     except Exception as e:
    #         self.error.emit(f"Invalid TIFF: {str(e)}")

    # def run(self):
    #     try:
    #         import tiffcapture

    #         self.progress.emit(5)

    #         # -------------------------
    #         # Open TIFF
    #         # -------------------------
    #         handle = tiffcapture.opentiff(self.path)

    #         if handle is None:
    #             self.error.emit("Failed to open TIFF")
    #             return

    #         self.progress.emit(25)

    #         # -------------------------
    #         # Validate by reading first frame
    #         # -------------------------
    #         try:
    #             _ = handle.get_frame(0)
    #         except Exception as e:
    #             self.error.emit(f"Invalid TIFF: {e}")
    #             return

    #         self.progress.emit(75)

    #         # -------------------------
    #         # Done
    #         # -------------------------
    #         self.progress.emit(100)
    #         self.finished.emit(handle)

    #     except Exception as e:
    #         self.error.emit(str(e))