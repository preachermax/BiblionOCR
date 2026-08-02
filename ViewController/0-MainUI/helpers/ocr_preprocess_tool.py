import os
import cv2
import numpy as np
import tiffcapture
#import MyServer
from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt

class OCRPreprocessTool(QtWidgets.QDialog):
    def __init__(self, parent=None, initial_pixmap=None):
        super().__init__(parent)

        ui_path = os.path.join(os.path.dirname(__file__), "ocr_preprocess_tool.ui")
        uic.loadUi(ui_path, self)

        # ✅ Initialize FIRST
        self.processed_image = None
        self.raw_image = None

        # Signals
        self.btnLoad.clicked.connect(self.load_tiff)
        self.sliderZoom.valueChanged.connect(self.update_display)
        self.sliderKernel.valueChanged.connect(self.process)
        self.sliderIterations.valueChanged.connect(self.process)
        self.sliderOp.valueChanged.connect(self.process)
        self.btnExport.clicked.connect(self.export_tiff)
        self.btn_Close.clicked.connect(self.close)

        # ✅ Load pixmap AFTER everything is ready
        if initial_pixmap is not None:
            self.load_from_pixmap(initial_pixmap)
    
    def load_from_pixmap(self, pixmap):
        from PyQt5.QtGui import QImage
        import numpy as np

        if pixmap is None or pixmap.isNull():
            self.lblStatus.setText("Invalid pixmap")
            return

        qimg = pixmap.toImage()

        # ✅ Force grayscale safely
        if qimg.format() != QImage.Format_Grayscale8:
            qimg = qimg.convertToFormat(QImage.Format_Grayscale8)

        width = qimg.width()
        height = qimg.height()

        ptr = qimg.bits()
        ptr.setsize(height * width)

        arr = np.frombuffer(ptr, np.uint8).reshape((height, width))

        self.raw_image = arr.copy()
        self.processed_image = arr.copy()

        self.lblStatus.setText("Loaded from main viewer")
        self.update_display()
        self.process()   # ✅ ADD THIS
    # ✅ YOUR TIFFCAPTURE PIPELINE (preserved)
    def load_tiff(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open TIFF", "", "TIFF Files (*.tif *.tiff)"
        )
        if not path:
            return

        cap = tiffcapture.opentiff(path)
        success, frame = cap.read()

        if not success:
            self.lblStatus.setText("Failed to load TIFF")
            return

        if len(frame.shape) == 3:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        self.raw_image = frame
        self.processed_image = frame.copy()

        self.lblStatus.setText("Loaded successfully")
        self.update_display()
        self.process()   # ✅ ADD THIS

    def process(self):
        if self.raw_image is None:
            return

        k = max(1, (self.sliderKernel.value() * 2) - 1)
        iters = self.sliderIterations.value()
        op = self.sliderOp.value()

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k, k))

        if op == 0 or iters == 0:
            self.processed_image = self.raw_image.copy()
            self.lblOperation.setText("Bypass")
        elif op == 1:
            self.processed_image = cv2.erode(self.raw_image, kernel, iterations=iters)
            self.lblOperation.setText("Erode")
        elif op == 2:
            self.processed_image = cv2.dilate(self.raw_image, kernel, iterations=iters)
            self.lblOperation.setText("Dilate")
        elif op == 3:
            self.processed_image = cv2.morphologyEx(
                self.raw_image, cv2.MORPH_OPEN, kernel, iterations=iters
            )
            self.lblOperation.setText("Open")
        elif op == 4:
            self.processed_image = cv2.morphologyEx(
                self.raw_image, cv2.MORPH_CLOSE, kernel, iterations=iters
            )
            self.lblOperation.setText("Close")

        self.lblKernel.setText(f"{k}x{k}")
        self.lblIterations.setText(f"{iters}")

        self.update_display()
        QtWidgets.QApplication.processEvents()  # optional but helps UI refresh

    # def process(self):
    #     print("PROCESS CALLED", self.raw_image is not None)
    #     if self.raw_image is None:
    #         return

    #     k = max(1, (self.sliderKernel.value() * 2) - 1)
    #     iters = self.sliderIterations.value()
    #     op = self.sliderOp.value()

    #     kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k, k))

    #     if op == 0 or iters == 0:
    #         self.processed_image = self.raw_image.copy()
    #         self.lblOperation.setText("Bypass")
    #     elif op == 1:
    #         self.processed_image = cv2.erode(self.raw_image, kernel, iterations=iters)
    #         self.lblOperation.setText("Erode")
    #     elif op == 2:
    #         self.processed_image = cv2.dilate(self.raw_image, kernel, iterations=iters)
    #         self.lblOperation.setText("Dilate")
    #     elif op == 3:
    #         self.processed_image = cv2.morphologyEx(
    #             self.raw_image, cv2.MORPH_OPEN, kernel, iterations=iters
    #         )
    #         self.lblOperation.setText("Open")
    #     elif op == 4:
    #         self.processed_image = cv2.morphologyEx(
    #             self.raw_image, cv2.MORPH_CLOSE, kernel, iterations=iters
    #         )
    #         self.lblOperation.setText("Close")

    #     self.lblKernel.setText(f"{k}x{k}")
    #     self.lblIterations.setText(f"{iters}")

    #     self.update_display()
    #     QtWidgets.QApplication.processEvents()  # optional but helps UI refresh

    def update_display(self):
        self.lblZoom.setText(f"{self.sliderZoom.value()}%")
        self.show_image(self.raw_image, self.previewOriginal)
        self.show_image(self.processed_image, self.previewProcessed)

    def show_image(self, img, label):
        if img is None:
            return

        h, w = img.shape

        qimg = QImage(img.data, w, h, w, QImage.Format_Grayscale8)
        pix = QPixmap.fromImage(qimg)

        # ✅ Get zoom factor
        zoom = self.sliderZoom.value() / 100.0

        new_w = int(w * zoom)
        new_h = int(h * zoom)

        scaled = pix.scaled(
            new_w,
            new_h,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        label.setPixmap(scaled)
    
    # def show_image(self, img, label):
    #     if img is None:
    #         return

    #     h, w = img.shape

    #     qimg = QImage(img.data, w, h, w, QImage.Format_Grayscale8)
    #     pix = QPixmap.fromImage(qimg)

    #     # ✅ Let QLabel handle scaling
    #     label.setScaledContents(True)

    #     # ✅ Set pixmap WITHOUT pre-scaling
    #     label.setPixmap(pix)

    # def show_image(self, img, label):
    #     if img is None:
    #         return

    #     h, w = img.shape
    #     qimg = QImage(img.copy().data, w, h, w, QImage.Format_Grayscale8)
    #     pix = QPixmap.fromImage(qimg)
    #     label.setPixmap(pix.scaled(label.size(), Qt.KeepAspectRatio))

    def export_tiff(self):
        if self.processed_image is None:
            return

        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save TIFF", "", "TIFF Files (*.tif *.tiff)"
        )

        if path:
            cv2.imwrite(path, self.processed_image)
            self.lblStatus.setText(f"Saved: {os.path.basename(path)}")