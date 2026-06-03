import sys
import io
import sane
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QComboBox, QLabel, 
                             QMessageBox)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class ScanWorker(QThread):
    """Handles the scanning process in a background thread."""
    scan_complete = pyqtSignal(bytes)
    scan_failed = pyqtSignal(str)

    def __init__(self, device_name):
        super().__init__()
        self.device_name = device_name

    def run(self):
        try:
            # Initialize SANE inside the worker thread
            sane.init()
            dev = sane.open(self.device_name)
            
            # Start scanning and capture the PIL Image object
            pil_img = dev.start()
            
            if pil_img:
                # Save PIL image to a byte buffer as a PNG
                buffer = io.BytesIO()
                pil_img.save(buffer, format="PNG")
                self.scan_complete.emit(buffer.getvalue())
            else:
                self.scan_failed.emit("No image data received from scanner.")
            
            dev.close()
        except Exception as e:
            self.scan_failed.emit(str(e))
        finally:
            sane.exit()

class ScannerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt5 Open Source Scanner")
        self.resize(600, 500)
        self.init_ui()
        self.refresh_devices()

    def init_ui(self):
        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Controls Layout (Top)
        controls_layout = QHBoxLayout()
        
        self.device_combo = QComboBox()
        controls_layout.addWidget(QLabel("Scanner:"))
        controls_layout.addWidget(self.device_combo)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_devices)
        controls_layout.addWidget(self.refresh_btn)

        self.scan_btn = QPushButton("Scan Document")
        self.scan_btn.setStyleSheet("background-color: #007ACC; color: white; font-weight: bold;")
        self.scan_btn.clicked.connect(self.start_scan)
        controls_layout.addWidget(self.scan_btn)

        main_layout.addLayout(controls_layout)

        # Preview Area (Center)
        self.preview_label = QLabel("No document scanned yet.")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("border: 2px dashed #999; background-color: #F0F0F0;")
        main_layout.addWidget(self.preview_label, stretch=1)

    def refresh_devices(self):
        """Detects connected hardware scanners."""
        self.device_combo.clear()
        try:
            sane.init()
            devices = sane.get_devices()
            sane.exit()

            if not devices:
                self.device_combo.addItem("No scanners found")
                self.scan_btn.setEnabled(False)
                return

            for device in devices:
                # device format: (device_name, vendor, model, type)
                display_name = f"{device[1]} {device[2]}"
                self.device_combo.addItem(display_name, device[0])
            
            self.scan_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "SANE Error", f"Could not initialize SANE:\n{str(e)}")

    def start_scan(self):
        """Prepares UI and triggers the background thread."""
        device_name = self.device_combo.currentData()
        if not device_name:
            return

        self.scan_btn.setEnabled(False)
        self.scan_btn.setText("Scanning...")
        self.preview_label.setText("Reading from scanner... Please wait.")

        # Start the background worker thread
        self.worker = ScanWorker(device_name)
        self.worker.scan_complete.connect(self.on_scan_success)
        self.worker.scan_failed.connect(self.on_scan_error)
        self.worker.start()

    def on_scan_success(self, img_bytes):
        """Displays the resulting image data in the UI layout."""
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("Scan Document")

        # Convert byte data to QPixmap
        qimage = QImage.fromData(img_bytes)
        pixmap = QPixmap.fromImage(qimage)

        # Scale the image smoothly to fit the preview window
        scaled_pixmap = pixmap.scaled(self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.preview_label.setPixmap(scaled_pixmap)

    def on_scan_error(self, error_msg):
        """Handles scan failures gracefully."""
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("Scan Document")
        self.preview_label.setText("Scan failed.")
        QMessageBox.warning(self, "Scan Error", f"An error occurred during scanning:\n{error_msg}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScannerApp()
    window.show()
    sys.exit(app.exec_())