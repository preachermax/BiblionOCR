import sys
import os
import io
import platform
import PIL.Image
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, 
                             QVBoxLayout, QWidget, QFileDialog, QComboBox, 
                             QFormLayout, QHBoxLayout, QMessageBox, QProgressBar)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QObject

# --- Cross-Platform Environment Inspection ---
OS_TYPE = platform.system()  # Returns 'Windows', 'Linux', or 'Darwin'

if OS_TYPE == 'Windows':
    import twain
elif OS_TYPE == 'Linux':
    import sane
else:
    print("Warning: Unsupported Operating System. Scanner backends disabled.")


# ==============================================================================
# 1. WINDOWS BACKEND WORKER (TWAIN)
# ==============================================================================
class WindowsScanWorker(QObject):
    page_scanned = pyqtSignal(bytes, int)
    scan_complete = pyqtSignal(list)
    scan_error = pyqtSignal(str)
    status_msg = pyqtSignal(str)

    def __init__(self, win_id, config):
        super().__init__()
        self.win_id = win_id
        self.config = config

    @pyqtSlot()
    def run_scan(self):
        scanned_pages = []
        try:
            self.status_msg.emit("Connecting to Windows TWAIN Source Manager...")
            with twain.SourceManager(self.win_id) as sm:
                src = sm.open_source()
                if not src:
                    self.scan_complete.emit([])
                    return

                # Configure Color Modes
                pixel_type_map = {
                    'Color (RGB)': twain.TWPT_RGB,
                    'Grayscale': twain.TWPT_GRAY,
                    'Black & White': twain.TWPT_BW
                }
                try:
                    src.set_capability(twain.ICAP_PIXELTYPE, twain.TWTY_UINT16, pixel_type_map[self.config['color_mode']])
                    src.set_capability(twain.ICAP_XRESOLUTION, twain.TWTY_FIX32, self.config['dpi'])
                    src.set_capability(twain.ICAP_YRESOLUTION, twain.TWTY_FIX32, self.config['dpi'])
                except Exception as ce:
                    print(f"TWAIN Capability warning: {ce}")

                # Configure ADF Tray
                if self.config['use_adf']:
                    try:
                        src.set_capability(twain.CAP_FEEDERENABLED, twain.TWTY_BOOL, True)
                        src.set_capability(twain.CAP_AUTOFEED, twain.TWTY_BOOL, True)
                    except Exception as fe:
                        self.scan_error.emit(f"ADF capability rejected by TWAIN driver: {fe}")
                        return

                src.request_acquire(show_ui=False, modal_ui=False)
                more_pages = True
                page_index = 1
                
                while more_pages:
                    self.status_msg.emit(f"Transferring page {page_index}...")
                    rv = src.xfer_image_natively()
                    if rv:
                        handle, remaining_count = rv
                        bmp_bytes = twain.dib_to_bm_file(handle)
                        
                        pil_img = PIL.Image.open(io.BytesIO(bmp_bytes))
                        scanned_pages.append(pil_img)
                        
                        self.page_scanned.emit(bmp_bytes, page_index)
                        page_index += 1
                        more_pages = (remaining_count != 0) and self.config['use_adf']
                    else:
                        break

                self.scan_complete.emit(scanned_pages)
        except Exception as e:
            self.scan_error.emit(str(e))


# ==============================================================================
# 2. LINUX BACKEND WORKER (SANE)
# ==============================================================================
class LinuxScanWorker(QObject):
    page_scanned = pyqtSignal(bytes, int)
    scan_complete = pyqtSignal(list)
    scan_error = pyqtSignal(str)
    status_msg = pyqtSignal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config

    @pyqtSlot()
    def run_scan(self):
        scanned_pages = []
        try:
            self.status_msg.emit("Initializing Linux SANE Interface...")
            sane.init()
            devices = sane.get_devices()
            if not devices:
                self.scan_error.emit("No system-linked SANE compliance hardware detected.")
                return
            
            scanner = sane.open(devices[0][0])
            
            color_map = {'Color (RGB)': 'Color', 'Grayscale': 'Gray', 'Black & White': 'Lineart'}
            try:
                scanner.mode = color_map[self.config['color_mode']]
                scanner.resolution = int(self.config['dpi'])
                if self.config['use_adf']:
                    scanner.source = 'ADF'
                else:
                    scanner.source = 'Flatbed'
            except Exception as ce:
                print(f"SANE driver setup adjustment skipped: {ce}")

            page_index = 1
            more_pages = True
            
            while more_pages:
                self.status_msg.emit(f"Pulling sheet {page_index}...")
                pil_image = scanner.scan()
                if pil_image:
                    scanned_pages.append(pil_image)
                    
                    buf = io.BytesIO()
                    pil_image.save(buf, format="BMP")
                    self.page_scanned.emit(buf.getvalue(), page_index)
                    
                    page_index += 1
                    if not self.config['use_adf']:
                        break
                else:
                    break
        except StopIteration:
            self.status_msg.emit("ADF Paper tray empty.")
        except Exception as e:
            self.scan_error.emit(str(e))
            return
        finally:
            try:
                scanner.close()
                sane.exit()
            except:
                pass
                
        self.scan_complete.emit(scanned_pages)


# ==============================================================================
# 3. UNIFIED MAIN GUI INTERFACE
# ==============================================================================
class UniversalScannerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.scanned_pages = []
        self.scan_thread = None
        self.worker = None
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle(f'Universal Scanner Interface [{OS_TYPE} Mode]')
        self.setGeometry(100, 100, 520, 680)
        
        main_layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        self.color_mode_combo = QComboBox()
        self.color_mode_combo.addItems(['Color (RGB)', 'Grayscale', 'Black & White'])
        form_layout.addRow('Color Mode:', self.color_mode_combo)
        
        self.dpi_combo = QComboBox()
        self.dpi_combo.addItems(['150', '200', '300', '600'])
        self.dpi_combo.setCurrentText('300')
        form_layout.addRow('Resolution (DPI):', self.dpi_combo)

        self.source_combo = QComboBox()
        self.source_combo.addItems(['Flatbed Glass', 'Automatic Document Feeder (ADF)'])
        form_layout.addRow('Paper Source:', self.source_combo)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(['PDF', 'TIFF', 'PNG', 'JPEG'])
        self.format_combo.currentTextChanged.connect(self.toggle_compression_ui)
        form_layout.addRow('Save Format:', self.format_combo)

        self.compression_combo = QComboBox()
        self.compression_combo.addItems(['LZW Compression', 'None (Uncompressed)'])
        form_layout.addRow('Compression:', self.compression_combo)
        
        main_layout.addLayout(form_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel(f"Platform engine active: Running on {OS_TYPE}")
        main_layout.addWidget(self.status_label)
        
        btn_layout = QHBoxLayout()
        self.scan_button = QPushButton('Start Scanning', self)
        self.scan_button.clicked.connect(self.initiate_cross_platform_scan)
        btn_layout.addWidget(self.scan_button)
        
        self.save_button = QPushButton('Save Document...', self)
        self.save_button.clicked.connect(self.save_document)
        self.save_button.setEnabled(False)
        btn_layout.addWidget(self.save_button)
        main_layout.addLayout(btn_layout)
        
        self.preview_label = QLabel('Ready to capture scanner preview array', self)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("border: 1px dashed #aaa; background-color: #f9f9f9;")
        main_layout.addWidget(self.preview_label, stretch=1)
        
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def toggle_compression_ui(self, selected_format):
        self.compression_combo.setEnabled(selected_format == 'TIFF')

    def initiate_cross_platform_scan(self):
        """Inspects runtime flags and anchors the correct OS subsystem worker thread."""
        config = {
            'color_mode': self.color_mode_combo.currentText(),
            'dpi': float(self.dpi_combo.currentText()),
            'use_adf': self.source_combo.currentText() == 'Automatic Document Feeder (ADF)'
        }
        
        self.scan_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.progress_bar.show()
        
        self.scan_thread = QThread()
        
        # Branch architecture based on OS evaluation
        if OS_TYPE == 'Windows':
            self.worker = WindowsScanWorker(self.winId(), config)
        elif OS_TYPE == 'Linux':
            self.worker = LinuxScanWorker(config)
        else:
            QMessageBox.critical(self, "Unsupported OS", "Scanning is not supported on this operating system.")
            self.scan_button.setEnabled(True)
            self.progress_bar.hide()
            return