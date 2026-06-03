import sys
import io
import os
from datetime import datetime
import sane
from PIL import Image
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QComboBox, QLabel, 
                             QMessageBox, QFileDialog, QGroupBox, QFormLayout)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class AdvancedScanWorker(QThread):
    """Handles the scanning hardware logic with parameters in a background thread."""
    scan_complete = pyqtSignal(bytes, dict)
    scan_failed = pyqtSignal(str)

    def __init__(self, device_name, mode, dpi):
        super().__init__()
        self.device_name = device_name
        self.mode = mode
        self.dpi = int(dpi)

    def run(self):
        try:
            sane.init()
            dev = sane.open(self.device_name)
            
            # Apply user selections safely to the backend hardware parameters
            try:
                dev.mode = self.mode
            except AttributeError:
                pass # Fallback if specific hardware doesn't support the exact text string

            try:
                dev.resolution = self.dpi
            except AttributeError:
                pass 
            
            # Trigger hardware optical sensor scanning
            pil_img = dev.start()
            
            if pil_img:
                # Keep a pristine uncompressed copy in memory to avoid decompression artifacts
                buffer = io.BytesIO()
                pil_img.save(buffer, format="PNG")
                
                # Pass back settings metadata to assist the output save operations
                metadata = {"mode": self.mode, "dpi": self.dpi}
                self.scan_complete.emit(buffer.getvalue(), metadata)
            else:
                self.scan_failed.emit("Hardware backend returned empty image.")
            
            dev.close()
        except Exception as e:
            self.scan_failed.emit(str(e))
        finally:
            sane.exit()

class AdvancedScannerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Open Source Document Digitization Suite")
        self.resize(900, 650)
        self.output_directory = os.path.expanduser("~/Documents")
        self.last_scanned_pil = None
        self.current_metadata = {}
        
        self.init_ui()
        self.refresh_devices()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        h_master = QHBoxLayout(central_widget)

        # ================= LEFT SIDE PANEL (CONTROLS) =================
        left_panel = QVBoxLayout()
        
        # Group 1: Hardware Selection
        hw_group = QGroupBox("Hardware Source")
        hw_layout = QVBoxLayout()
        self.device_combo = QComboBox()
        self.refresh_btn = QPushButton("Refresh Device Registry")
        self.refresh_btn.clicked.connect(self.refresh_devices)
        hw_layout.addWidget(self.device_combo)
        hw_layout.addWidget(self.refresh_btn)
        hw_group.setLayout(hw_layout)
        left_panel.addWidget(hw_group)

        # Group 2: Imaging Parameters
        param_group = QGroupBox("Optics & Capture Profile")
        param_layout = QFormLayout()
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Color", "Gray", "Lineart"])
        param_layout.addRow(QLabel("Color Matrix Mode:"), self.mode_combo)
        
        self.dpi_combo = QComboBox()
        self.dpi_combo.addItems(["150", "300", "600", "1200"])
        self.dpi_combo.setCurrentText("300")
        param_layout.addRow(QLabel("Target Density (DPI):"), self.dpi_combo)
        param_group.setLayout(param_layout)
        left_panel.addWidget(param_group)

        # Group 3: Output & Pipeline Options
        out_group = QGroupBox("Target Storage Pipeline")
        out_layout = QVBoxLayout()
        
        self.dir_label = QLabel(f"Destination: ...{self.output_directory[-25:]}")
        self.dir_btn = QPushButton("Select Output Folder")
        self.dir_btn.clicked.connect(self.choose_directory)
        
        form_layout = QFormLayout()
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PDF", "TIFF"])
        form_layout.addRow(QLabel("Export Format:"), self.format_combo)
        
        out_layout.addWidget(self.dir_label)
        out_layout.addWidget(self.dir_btn)
        out_layout.addLayout(form_layout)
        out_group.setLayout(out_layout)
        left_panel.addWidget(out_group)

        # Action Buttons
        self.scan_btn = QPushButton("Initiate Hardware Scan")
        self.scan_btn.setStyleSheet("background-color: #228B22; color: white; font-weight: bold; padding: 10px;")
        self.scan_btn.clicked.connect(self.start_scan)
        left_panel.addWidget(self.scan_btn)

        self.save_btn = QPushButton("Export and Save Image")
        self.save_btn.setStyleSheet("background-color: #007ACC; color: white; font-weight: bold; padding: 10px;")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save_document)
        left_panel.addWidget(self.save_btn)

        left_panel.addStretch(1)
        h_master.addLayout(left_panel, stretch=1)

        # ================= RIGHT SIDE PANEL (PREVIEW) =================
        self.preview_label = QLabel("Scanner Preview Sandbox")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("border: 3px dashed #A0A0A0; background-color: #FFFFFF; font-weight: bold; color: #555;")
        h_master.addWidget(self.preview_label, stretch=2)

    def refresh_devices(self):
        self.device_combo.clear()
        try:
            sane.init()
            devices = sane.get_devices()
            sane.exit()

            if not devices:
                self.device_combo.addItem("No Connected Scanners Detected")
                self.scan_btn.setEnabled(False)
                return

            for dev in devices:
                display = f"{dev[1]} {dev[2]} ({dev[0]})"
                self.device_combo.addItem(display, dev[0])
            
            self.scan_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Driver Fault", f"Failed parsing hardware layer:\n{str(e)}")

    def choose_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Output Directory", self.output_directory)
        if dir_path:
            self.output_directory = dir_path
            self.dir_label.setText(f"Destination: ...{dir_path[-25:]}")

    def start_scan(self):
        dev_name = self.device_combo.currentData()
        if not dev_name: return

        self.scan_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.scan_btn.setText("Capturing Optical Data...")

        self.worker = AdvancedScanWorker(dev_name, self.mode_combo.currentText(), self.dpi_combo.currentText())
        self.worker.scan_complete.connect(self.on_scan_success)
        self.worker.scan_failed.connect(self.on_scan_error)
        self.worker.start()

    def on_scan_success(self, img_bytes, metadata):
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("Initiate Hardware Scan")
        
        # Load back to Pillow to prepare for saving natively to PDF/TIFF
        self.last_scanned_pil = Image.open(io.BytesIO(img_bytes))
        self.current_metadata = metadata

        # Bind to standard UI for visual layout rendering
        qimage = QImage.fromData(img_bytes)
        pixmap = QPixmap.fromImage(qimage)
        scaled = pixmap.scaled(self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.preview_label.setPixmap(scaled)
        self.save_btn.setEnabled(True)

    def on_scan_error(self, err):
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("Initiate Hardware Scan")
        QMessageBox.warning(self, "Hardware Execution Error", f"SANE reported an exception:\n{err}")

    def save_document(self):
        if not self.last_scanned_pil: return
        
        fmt = self.format_combo.currentText().lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Scan_{timestamp}.{fmt}"
        full_path = os.path.join(self.output_directory, filename)

        try:
            dpi_val = self.current_metadata.get("dpi", 300)
            
            # PDF / TIFF encoding execution block
            if fmt == "pdf":
                # Convert color mode explicitly for the PDF structure format matrix
                out_img = self.last_scanned_pil.convert("RGB") if self.last_scanned_pil.mode != "RGB" else self.last_scanned_pil
                out_img.save(full_path, format="PDF", resolution=dpi_val)
            elif fmt == "tiff":
                self.last_scanned_pil.save(full_path, format="TIFF", dpi=(dpi_val, dpi_val))

            QMessageBox.information(self, "File Saved", f"Successfully exported asset directly to:\n{full_path}")
        except Exception as e:
            QMessageBox.critical(self, "Write IO Error", f"Could not export file down to disk layer:\n{str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AdvancedScannerApp()
    window.show()
    sys.exit(app.exec_())