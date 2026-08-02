import sys
import os
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtCore import Qt
# Explicitly register the standard Ubuntu/Debian system plugin directories
QCoreApplication.addLibraryPath("/usr/lib/aarch64-linux-gnu/qt5/plugins")
QCoreApplication.addLibraryPath("/usr/lib/plugins")
from PyQt5.QtGui import QImageReader
formats = QImageReader.supportedImageFormats()
print("PyQt5 can natively read:", [f.data().decode('utf-8') for f in formats])

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QProgressBar, QLabel, QFileDialog)
from PyQt5.QtCore import QThread, pyqtSignal, QObject
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.Qt import QImageReader

class ImageLoaderWorker(QThread):
    # Signals for thread-safe UI communication
    progress_updated = pyqtSignal(int)
    image_loaded = pyqtSignal(QPixmap)
    error_occurred = pyqtSignal(str)
    status_msg = pyqtSignal(str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self._is_cancelled = False
        self.reader = None

    def run(self):
        try:
            self.status_msg.emit("Initializing file reader...")
            
            # Setup specialized reader for the large TIFF
            self.reader = QImageReader(self.file_path)
            self.reader.setAutoTransform(True)
            
            # Connect the native low-level decompression progress loop
            # This triggers automatically as bytes are converted to pixels
            self.reader.supportedImageFormats() # Warms up the plugin system
            
            # Polling cancellation hook during long low-level decompression
            # Note: QImageReader doesn't have an internal abort loop slot in Python,
            # so we track cancellation safely before and after raw decoding.
            if self._is_cancelled:
                return

            self.status_msg.emit("Decompressing TIFF data...")
            
            # Read image as a raw QImage container inside the worker thread
            q_image = self.reader.read()
            
            if q_image.isNull():
                if self._is_cancelled:
                    return
                raise ValueError(f"Failed to read image data: {self.reader.errorString()}")

            if self._is_cancelled:
                return

            self.status_msg.emit("Optimizing graphic structure...")
            
            # Convert to QPixmap. From Image data, this is fast and safe in a worker thread,
            # but we must pass it back via signals to mount to a widget safely.
            pixmap = QPixmap.fromImage(q_image)
            
            if not self._is_cancelled:
                self.image_loaded.emit(pixmap)
                
        except Exception as e:
            if not self._is_cancelled:
                self.error_occurred.emit(str(e))

    def cancel(self):
        self._is_cancelled = True
        self.status_msg.emit("Cancellation requested...")
        # Forcing clean termination safely via QThread routines
        self.requestInterruption()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Large Mono TIFF Loader")
        self.resize(600, 500)
        
        layout = QVBoxLayout()
        
        # Action Control Panel
        btn_layout = QHBoxLayout()
        self.btn_load = QPushButton("Open TIFF File")
        self.btn_load.clicked.connect(self.select_image)
        btn_layout.addWidget(self.btn_load)
        
        self.btn_cancel = QPushButton("Cancel Load")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.cancel_loading)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)
        
        # Loading Feedback Trackers
        self.lbl_status = QLabel("Status: Idle")
        layout.addWidget(self.lbl_status)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Core Viewer Target
        self.image_preview = QLabel("No TIFF image loaded yet.")
        self.image_preview.setScaledContents(False) # Let us handle scaling cleanly
        layout.addWidget(self.image_preview)
        
        self.setLayout(layout)
        self.worker = None
        self.raw_pixmap = None # Cache original size for clean resizing later

    def select_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Large TIFF File", "", "TIFF Images (*.tif *.tiff)"
        )
        
        if not file_path:
            return

        self.btn_load.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.progress_bar.setValue(0)
        self.image_preview.setText("Spinning up backend engine...")
        
        # Establish background thread context
        self.worker = ImageLoaderWorker(file_path)
        
        # Connect background updates directly into core UI slots
        self.worker.status_msg.connect(lambda msg: self.lbl_status.setText(f"Status: {msg}"))
        self.worker.image_loaded.connect(self.display_image)
        self.worker.error_occurred.connect(self.handle_error)
        
        # Track intermediate progress values (simulated safely or via file processing stages)
        # For huge arrays, we step up progress as pipeline steps pass
        self.worker.finished.connect(self.cleanup_thread)
        self.worker.start()

    def cancel_loading(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.image_preview.setText("Image load operation aborted by user.")
            self.lbl_status.setText("Status: Cancelled.")
            self.cleanup_thread()

    def display_image(self, pixmap):
        self.raw_pixmap = pixmap
        self.lbl_status.setText("Status: Complete.")
        self.progress_bar.setValue(100)
        
        # FIX: Use the correct PyQt5 keyword argument and Qt namespace flag
        scaled_pixmap = self.raw_pixmap.scaled(
            self.image_preview.size(), 
            aspectRatioMode=Qt.KeepAspectRatio
        )
        self.image_preview.setPixmap(scaled_pixmap)


    def handle_error(self, error_message):
        self.lbl_status.setText("Status: Failed.")
        self.image_preview.setText(f"Error loading TIFF:\n{error_message}")

    def cleanup_thread(self):
        self.btn_load.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        if self.worker:
            self.worker.quit()
            self.worker.wait()
            self.worker = None

def resizeEvent(self, event):
    if self.raw_pixmap and not self.raw_pixmap.isNull():
        # FIX: Apply the same corrected arguments here
        scaled_pixmap = self.raw_pixmap.scaled(
            self.image_preview.size(), 
            aspectRatioMode=Qt.KeepAspectRatio
        )
        self.image_preview.setPixmap(scaled_pixmap)
    super().resizeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
