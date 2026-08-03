import sys
import os
import cv2
import numpy as np

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtCore import Qt
# Explicitly register the standard Ubuntu/Debian system plugin directories
QCoreApplication.addLibraryPath("/usr/lib/aarch64-linux-gnu/qt5/plugins")
QCoreApplication.addLibraryPath("/usr/lib/plugins")
from PyQt5.QtGui import QImageReader
formats = QImageReader.supportedImageFormats()
print("PyQt5 can natively read:", [f.data().decode('utf-8') for f in formats])

from PyQt5.QtCore import QCoreApplication, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QImageReader
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFileDialog, QSlider, QSplitter)

# Explicitly register the standard Ubuntu/Debian system plugin directories
QCoreApplication.addLibraryPath("/usr/lib/aarch64-linux-gnu/qt5/plugins")
QCoreApplication.addLibraryPath("/usr/lib/plugins")

class ImageLoaderWorker(QThread):
    image_loaded = pyqtSignal(np.ndarray)
    error_occurred = pyqtSignal(str)
    status_msg = pyqtSignal(str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        try:
            self.status_msg.emit("Reading raw TIFF pixel arrays...")
            # Load as direct grayscale matrix to perfectly match mono text profiles
            cv_img = cv2.imread(self.file_path, cv2.IMREAD_GRAYSCALE)
            
            if cv_img is None:
                raise ValueError("Could not read or parse target TIFF file structure.")
                
            self.image_loaded.emit(cv_img)
        except Exception as e:
            self.error_occurred.emit(str(e))


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.raw_cv_image = None       
        self.processed_cv_image = None 
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("OCR Pre-Processing Studio (Tesseract Font Optimizer)")
        self.resize(1100, 650)
        
        main_layout = QHBoxLayout()
        
        # --- LEFT PANEL: RE-RANGED PARAMETER CONTROLS ---
        controls_layout = QVBoxLayout()
        
        self.btn_load = QPushButton("1. Import Raw TIFF")
        self.btn_load.clicked.connect(self.select_image)
        controls_layout.addWidget(self.btn_load)
        
        self.lbl_status = QLabel("Status: Idle")
        self.lbl_status.setWordWrap(True)
        controls_layout.addWidget(self.lbl_status)
        
        # Slider 1: Kernel Matrix Radius
        controls_layout.addWidget(QLabel("\nKernel Structure Size (Odd):"))
        self.slider_kernel = QSlider(Qt.Horizontal)
        self.slider_kernel.setRange(1, 10)  # Maps natively to odd sizes: 1x1 to 19x19
        self.slider_kernel.setValue(1)
        self.slider_kernel.setEnabled(False)
        self.slider_kernel.valueChanged.connect(self.apply_morphology)
        controls_layout.addWidget(self.slider_kernel)
        self.lbl_kernel_val = QLabel("Value: 1x1")
        controls_layout.addWidget(self.lbl_kernel_val)
        
        # Slider 2: Operations Loop Count
        controls_layout.addWidget(QLabel("\nFilter Execution Iterations:"))
        self.slider_iterations = QSlider(Qt.Horizontal)
        self.slider_iterations.setRange(0, 5)
        self.slider_iterations.setValue(0)
        self.slider_iterations.setEnabled(False)
        self.slider_iterations.valueChanged.connect(self.apply_morphology)
        controls_layout.addWidget(self.slider_iterations)
        self.lbl_iter_val = QLabel("Value: 0 (Bypass)")
        controls_layout.addWidget(self.lbl_iter_val)
        
        # Slider 3: Text Correction Engine Target Selector
        controls_layout.addWidget(QLabel("\nMorphology Mode Selection:\n(0:Orig, 1:Erode, 2:Dilate, 3:Open, 4:Close)"))
        self.slider_op = QSlider(Qt.Horizontal)
        self.slider_op.setRange(0, 4)
        self.slider_op.setValue(0)
        self.slider_op.setEnabled(False)
        self.slider_op.valueChanged.connect(self.apply_morphology)
        controls_layout.addWidget(self.slider_op)
        self.lbl_op_val = QLabel("Mode: Bypass Filter")
        controls_layout.addWidget(self.lbl_op_val)
        
        # Action Export Tool
        controls_layout.addSpacing(30)
        self.btn_export = QPushButton("2. Export Optimized TIFF")
        self.btn_export.setEnabled(False)
        self.btn_export.setStyleSheet("background-color: #2E7D32; color: white; font-weight: bold;")
        self.btn_export.clicked.connect(self.export_processed_tiff)
        controls_layout.addWidget(self.btn_export)
        
        controls_layout.addStretch()
        main_layout.addLayout(controls_layout, stretch=1)
        
        # --- RIGHT PANEL: SPLIT PREVIEW COMPARISON WINDOW ---
        preview_splitter = QSplitter(Qt.Horizontal)
        
        # Left Side of Splitter: Original Document Baseline
        orig_container = QVBoxLayout()
        orig_container.addWidget(QLabel("<b>[BASELINE ORIGINAL]</b>"))
        self.preview_orig = QLabel("No baseline image loaded.")
        self.preview_orig.setAlignment(Qt.AlignCenter)
        orig_widget = QWidget()
        orig_widget.setLayout(orig_container)
        orig_container.addWidget(self.preview_orig, stretch=1)
        preview_splitter.addWidget(orig_widget)
        
        # Right Side of Splitter: Modified Text Output Channel
        proc_container = QVBoxLayout()
        proc_container.addWidget(QLabel("<b>[MORPHOLOGY LIVE PREVIEW]</b>"))
        self.preview_proc = QLabel("Awaiting morphological adjustments.")
        self.preview_proc.setAlignment(Qt.AlignCenter)
        proc_widget = QWidget()
        proc_widget.setLayout(proc_container)
        proc_container.addWidget(self.preview_proc, stretch=1)
        preview_splitter.addWidget(proc_widget)
        
        main_layout.addWidget(preview_splitter, stretch=4)
        self.setLayout(main_layout)
        self.worker = None

    def select_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Input Mono TIFF", "", "TIFF Images (*.tif *.tiff)"
        )
        if not file_path:
            return

        self.btn_load.setEnabled(False)
        self.lbl_status.setText("Status: Allocating system memory thread...")
        
        self.worker = ImageLoaderWorker(file_path)
        self.worker.status_msg.connect(self.lbl_status.setText)
        self.worker.image_loaded.connect(self.on_image_loaded)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.finished.connect(lambda: self.btn_load.setEnabled(True))
        self.worker.start()

    def on_image_loaded(self, cv_matrix):
        self.raw_cv_image = cv_matrix
        self.processed_cv_image = cv_matrix.copy()
        self.lbl_status.setText("Status: File parsing ready.")
        
        self.slider_kernel.setEnabled(True)
        self.slider_iterations.setEnabled(True)
        self.slider_op.setEnabled(True)
        self.btn_export.setEnabled(True)
        
        self.display_matrix(self.raw_cv_image, self.preview_orig)
        self.display_matrix(self.processed_cv_image, self.preview_proc)

    def apply_morphology(self):
        if self.raw_cv_image is None:
            return
            
        k_size = (self.slider_kernel.value() * 2) - 1
        self.lbl_kernel_val.setText(f"Value: {k_size}x{k_size}")
        
        iters = self.slider_iterations.value()
        self.lbl_iter_val.setText(f"Value: {iters}")
        
        op_type = self.slider_op.value()
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k_size, k_size))
        
        if op_type == 0 or iters == 0:
            self.lbl_op_val.setText("Mode: Bypass Filter")
            self.processed_cv_image = self.raw_cv_image.copy()
        else:
            if op_type == 1:
                self.lbl_op_val.setText("Mode: Erosion (Thins bleeding ink text)")
                self.processed_cv_image = cv2.erode(self.raw_cv_image, kernel, iterations=iters)
            elif op_type == 2:
                self.lbl_op_val.setText("Mode: Dilation (Thickens thin/broken fonts)")
                self.processed_cv_image = cv2.dilate(self.raw_cv_image, kernel, iterations=iters)
            elif op_type == 3:
                self.lbl_op_val.setText("Mode: Opening (Removes background speckles/noise)")
                self.processed_cv_image = cv2.morphologyEx(self.raw_cv_image, cv2.MORPH_OPEN, kernel, iterations=iters)
            elif op_type == 4:
                self.lbl_op_val.setText("Mode: Closing (Fills missing gaps within characters)")
                self.processed_cv_image = cv2.morphologyEx(self.raw_cv_image, cv2.MORPH_CLOSE, kernel, iterations=iters)

        self.display_matrix(self.processed_cv_image, self.preview_proc)

    def display_matrix(self, cv_matrix, target_label):
        """Converts an OpenCV grayscale matrix safely to a scaled QPixmap container."""
        if cv_matrix is None:
            return
        h, w = cv_matrix.shape
        bytes_per_line = w  # 1 byte per pixel for grayscale images
        
        # Build raw frame view link safely
        q_img = QImage(cv_matrix.data, w, h, bytes_per_line, QImage.Format_Grayscale8)
        pixmap = QPixmap.fromImage(q_img)
        
        # Scale to cleanly fit target viewport container layout bounds
        scaled_pixmap = pixmap.scaled(target_label.size(), aspectRatioMode=Qt.KeepAspectRatio)
        target_label.setPixmap(scaled_pixmap)

    def export_processed_tiff(self):
        if self.processed_cv_image is None:
            return
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Optimized TIFF", "", "TIFF Images (*.tif *.tiff)"
        )
        if save_path:
            cv2.imwrite(save_path, self.processed_cv_image)
            self.lbl_status.setText(f"Status: Saved to {os.path.basename(save_path)}")

    def handle_error(self, error_message):
        self.lbl_status.setText(f"Status: Failed.\n{error_message}")

    def resizeEvent(self, event):
        
        if self.processed_cv_image and not self.processed.isNull():
            self.display_matrix(self.processed_cv_image, self.preview_proc)

        super().resizeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())