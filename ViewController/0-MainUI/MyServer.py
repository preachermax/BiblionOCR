print("RUNNING:", __file__)
# See dev_notebook.md for architecture + debugging notes
#print(len(locals()))
# Integrated with ChatGPT:
# OCR Preprocess Tool (OpenCV morphology + tiffcapture bridge)
# Next steps: OCR preview, multi-page TIFF, pipeline integration
# Python imports
import importlib.util
import sys
import os
import re
import subprocess
import tempfile
#import glob
import shutil
import json
import time
import hashlib
from enum import Enum
from gui_runtime_env import build_sanitized_env, sanitize_current_process_and_reexec
from SessionManager import SessionManager


sanitize_current_process_and_reexec()


# Path configuration and directory setup
RUNTIME_PATHS = SessionManager.export_runtime_paths(
    globals(),
    __file__,
    add_developer_view=True,
)

# Debug (optional toggle)
DEBUG_PATHS = True
if DEBUG_PATHS:
    print(f"project_root: {RUNTIME_PATHS.project_root}")
    print(f"script_dir: {RUNTIME_PATHS.script_dir}")


SCAN_ICON_RESOURCES = (
    ":/Icons/Icons/scanner.png",
    ":/Icons/Icons/BiblionScanner.png",
)
SCAN_ICON_FILES = (
    os.path.join(RUNTIME_PATHS.script_dir, "Icons", "scanner.png"),
    os.path.join(RUNTIME_PATHS.script_dir, "Icons", "BiblionScanner1.png"),
)


SCANNED_FOLDER = os.path.join(
    RUNTIME_PATHS.project_root,
    "Model",
    "Project",
    "Images",
    "Scanned"
)
os.makedirs(SCANNED_FOLDER, exist_ok=True)


def _sanitized_child_process_env():
    return build_sanitized_env(os.environ)

from ocr_preprocess_tool import OCRPreprocessTool
#from subprocess import Popen, PIPE, CalledProcessError
import pytesseract
import tiffcapture
import qimage2ndarray
from ext import mainfind
from HelpSystem import add_help_menu
from Dialogs.ProjectSettingsDialog import ProjectSettingsDialog
from Core.engine import ProjectCreationEngine as CoreProjectCreationEngine
from Core.project_tracking import ProjectWorkflowTracker
from Core.Scanner import ScanManager
from scan_runtime import start_scan_workflow
# EventBus is still defined below in this module during the Core migration.
# ProjectCreationEngine remains below as a temporary fallback, but runtime wiring now uses CoreProjectCreationEngine.
# Do not import MainWindow from MainUI.py; that file only contains the generated Ui_MainUI class.

# PyQt5 imports
import platform
if 'Windows' in platform.system():
    print("Platform:  ", platform.system())
    print("Windows platform detected. AirScan, TWAIN or WIA scanning will be used.")
elif 'Linux' in platform.system():
    print("Platform:  ", platform.system())
    print("Linux platform detected. Airscan or sane will be used for scanning.")
    #import sane
else:
    print("Platform:  ", platform.system(), platform.release(), platform.version())
    print("Unsupported platform. Some features may not work as expected.")

from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5.QtCore import Qt

# Custom imports
from MyServerUI import Ui_MainUI
from PreProcess import PreProcess as pp
import ChrReference as chrref
import MyVersifier as versify
from ProjectTrackingDialog import ProjectTrackingDialog
import MyGrounder as gtr
import ImageLoadWorker
from ProjectCreationWorker import ProjectCreationWorker
from Training import Train as tr
from TiffStackWorker import TiffStackWorker
from LocalFileDrop import LocalFileDropMixin
from ScanWorkflow import ScanWizardDialog as SharedScanWizardDialog
# Dialog Imports
from Dialogs.ExtractDialog import Ui_ExtractDialog
from Dialogs.pdf4tifDialog import Ui_pdf4tifDialog
from Dialogs.pdf2tifDialog import Ui_pdf2tifDialog
from Dialogs.tif2monoDialog import Ui_tif2monoDialog
from Dialogs.mono2pngDialog import Ui_mono2pngDialog
from Dialogs.deskew_monoDialog import Ui_deskew_monoDialog
from Dialogs.crop_languagesDialog import Ui_crop_languagesDialog
from Dialogs.greekmono2pngDialog import Ui_greekmono2pngDialog
from Dialogs.deskew_greekmonoDialog import Ui_deskew_greekmonoDialog
from Dialogs.greekresizepngDialog import Ui_greekresizepngDialog
from Dialogs.latinmono2pngDialog import Ui_latinmono2pngDialog
from Dialogs.deskew_latinmonoDialog import Ui_deskew_latinmonoDialog
from Dialogs.latinresizepngDialog import Ui_latinresizepngDialog
from Dialogs.crop_greek_linesDialog import Ui_crop_greek_linesDialog
from Dialogs.crop_latin_linesDialog import Ui_crop_latin_linesDialog
from Dialogs.tif_greek_lines_renameDialog import Ui_tifgreekrenamelinesDialog
from Dialogs.tif_greek_lines_moveDialog import Ui_tifgreekmovelinesDialog
from Dialogs.tif_latin_lines_renameDialog import Ui_tiflatinrenamelinesDialog
from Dialogs.tif_latin_lines_moveDialog import Ui_tiflatinmovelinesDialog
from Dialogs.ImageTextPairDialog import Ui_ImageTextPairDialog
from Developer.developer_services import DeveloperServices

#import MyPixler as pixler
#import CropTif as croptif
#import QtCropImage as cropimg
from project_creation_wizard_dialog import ProjectCreationWizardDialog
#from MultiPreProcess import MultiPreProcess as mpp
def configure_tesseract():

    import pytesseract
    import shutil
    import platform
    import os

    if shutil.which("tesseract"):
        return

    if platform.system() == "Windows":
        possible_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
        ]

        for path in possible_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                print(f"Using Tesseract at: {path}")
                return

    print("Ã¢Å¡Â Ã¯Â¸Â Tesseract not found.")


class MainWindow(LocalFileDropMixin, qtw.QMainWindow):

# Menu and Toolbar Action Methods
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._progress_bar_scale = 10

        configure_tesseract()

        # -------------------------
        # Core State
        # -------------------------
        self.imgfileList = []
        self.sorted_imgfilelist = []
        self.current_img_index = -1

        self._thread = None
        self._worker = None
        self._project_thread = None
        self._project_worker = None
        self._scan_thread = None
        self._scan_worker = None
        self._project_success_title = ""
        self._project_success_message = ""
        self.developer_services = None
        self.runtime_inspector_panel = None
        self.runtime_inspector_dock = None
        self._developer_services_active = False
        self.current_project_root = None
        self._pending_project_root = None

        # self.networkScanner = NetworkScanner()
        # self.networkScanner.deviceFound.connect(self.onDeviceFound)
        # self.networkScanner.progress.connect(self.onScanProgress)
        # self.networkScanner.finished.connect(self.onScanFinished)

        # -------------------------
        # UI Setup
        # -------------------------
        self.ui = Ui_MainUI()
        self.ui.setupUi(self)
        self.install_local_file_drop(
            [self, getattr(self.ui, 'centralwidget', None)],
            image_handler=self.showImage,
            text_handler=self.showText,
        )
        self._apply_scan_icon()
        # self.ui.NetworkTable = QTableWidget(self.ui.centralwidget)
        # self.ui.NetworkTable.setGeometry(10, 10, 600, 300)
        # self.ui.NetworkTable.setColumnCount(2)
        # self.ui.NetworkTable.setHorizontalHeaderLabels(["IP", "MAC"])
        # self.ui.verticalLayout.addWidget(self.ui.NetworkTable)
        self.scannerManager = ScanManager()

        self.session_manager = SessionManager()
        self.current_project_root = self.session_manager.get_active_project_root() or self.current_project_root

        # -------------------------
        # Progress Bar (FIXED)
        # -------------------------
        self.progress_bar = qtw.QProgressBar()
        self.progress_bar.setRange(0, 100 * self._progress_bar_scale)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self._init_project_status_widgets()
        self.statusBar().addPermanentWidget(self.progress_bar)

        # -------------------------
        # Help System
        # -------------------------
        add_help_menu(self, 'MyServer')
        self._setup_developer_mode_ui()

        # -------------------------
        # Actions / Signals
        # -------------------------
        self.ui.actionNewProject.setText("New Project")
        self.ui.actionNewProject.triggered.connect(self.on_new_project_clicked)
        if hasattr(self.ui, "actionOpen_Project"):
            self.ui.actionOpen_Project.triggered.connect(self.on_open_project_clicked)

        self.ui.actionOpen_Image.triggered.connect(self.loadImage)
        self.ui.actionextract_pdf_tb.triggered.connect(self.actionextract_pdf)
        self.ui.actionpdf_for_tiff_tb.triggered.connect(self.actionpdf_for_tiff)
        self.ui.actionpdf_to_tiff_tb.triggered.connect(self.actionpdf_to_tiff)
        self.ui.actiontiff_to_mono_tb.triggered.connect(self.actiontiff_to_mono)
        self.ui.actiondeskew_mono.triggered.connect(self.actiondeskew_mono)
        self.ui.actionmono_to_png_tb.triggered.connect(self.actionmono_to_png)
        self.ui.actionCrop_Languages_tb.triggered.connect(self.actionCrop_Languages)
        #self.ui.actionManual_Crop_Image_tb.triggered.connect(self.actionCropImage)

        self.ui.actionConvert_Greek_tiff_To_png.triggered.connect(self.actionConvert_Greek_tiff_To_png)
        self.ui.actionDeskewGreek_tiff_tb.triggered.connect(self.actionDeskewGreek_tiff)
        self.ui.actionResizeGreek_png_tb.triggered.connect(self.actionResizeGreek_png)

        self.ui.actionConvert_Latin_tiff_To_png.triggered.connect(self.actionConvert_Latin_tiff_To_png)
        self.ui.actionDeskewLatin_tiff_tb.triggered.connect(self.actionDeskewLatin_tiff)
        self.ui.actionResizeLatin_png_tb.triggered.connect(self.actionResizeLatin_png)

        self.ui.actionAutoCrop_Greek_to_tif_Lines_tb.triggered.connect(self.actionCrop_Greek_To_tiff_Lines)
        self.ui.actionRename_Greek_tif_Lines_tb.triggered.connect(self.actionRename_Greek_tiff_Lines)
        self.ui.actionMove_Greek_tif_Lines_tb.triggered.connect(self.actionMove_Greek_tiff_Lines)

        self.ui.actionAutoCrop_Latin_To_tif_Lines_tb.triggered.connect(self.actionCrop_Latin_To_tiff_Lines)
        self.ui.actionRename_Latin_tif_Lines_tb.triggered.connect(self.actionRename_Latin_tiff_Lines)
        self.ui.actionMove_Latin_tif_Lines_tb.triggered.connect(self.actionMove_Latin_tiff_Lines)

        self.ui.actionSplitGreek_text_lines_tb.triggered.connect(self.actionSplitGreek_text_lines)
        self.ui.actionRenameGreek_text_lines_tb.triggered.connect(self.actionRenameGreek_text_lines)

        self.ui.actionSplit_Latin_Text_Lines_tb.triggered.connect(self.actionSplit_Latin_Text_Lines)
        self.ui.actionRename_Latin_Text_Lines_tb.triggered.connect(self.actionRename_Latin_Text_Lines)

        self.ui.actionUpdate_Wordlist_tb.triggered.connect(self.actionUpdate_Wordlist)
        self.ui.actionCorrect_OCR_tb.triggered.connect(self.actionCorrect_OCR)

        self.ui.actionFind_and_Replace.triggered.connect(mainfind.Find(self).show)
        self.ui.actionPrefernces.triggered.connect(self.open_project_settings_dialog)

        self.ui.actionToggle_Greek_Toolbars.triggered.connect(self.toggleGreekToolbars)
        self.ui.actionToggle_Latin_Toolbars.triggered.connect(self.toggleLatinToolbars)

        # -------------------------
        # Buttons / Navigation
        # -------------------------
        self.ui.imageScannerbutton.clicked.connect(self.actionScanNetwork)

        self.ui.OpenImageFilebutton.clicked.connect(self.loadImage)
        self.ui.FindReplacebutton.clicked.connect(mainfind.Find(self).show)

        self.ui.BothLoadButton.clicked.connect(self.bothLoad)
        self.ui.BothPrevButton.clicked.connect(self.prevImage)
        self.ui.BothPrevButton.clicked.connect(self.prevText)
        self.ui.BothNextButton.clicked.connect(self.nextImage)
        self.ui.BothNextButton.clicked.connect(self.nextText)

        self.ui.PrevImgButton.clicked.connect(self.prevImage)
        self.ui.NextImgButton.clicked.connect(self.nextImage)
        self.ui.PrevTxtButton.clicked.connect(self.prevText)
        self.ui.NextTxtButton.clicked.connect(self.nextText)

        # -------------------------
        # Zoom
        # -------------------------
        self.ui.Zoombutton.clicked.connect(self.get_zoom)
        self.ui.ZoomComboBox.currentTextChanged.connect(self.on_zoom)
        self.ui.Zoomslider.valueChanged.connect(self.on_zoomslider)
        self.ui.Zoomslider.sliderReleased.connect(self.DisableZoomSlider)
        self.ui.Zoomslider.hide()

        # -------------------------
        # Image Tools
        # -------------------------
        #self.ui.Cropbutton.clicked.connect(self.actionCropImage)
        #self.ui.Deskewbutton.clicked.connect(self.actionDeskewImage)

        # -------------------------
        # OCR
        # -------------------------
        self.ui.OCRbutton.clicked.connect(self.GetRawOCRtext)
        self.ui.LHDialogtbutton.clicked.connect(self.GetLineSpacing)
        self.ui.LHslider.valueChanged.connect(self.SetLineSpacing)
        self.ui.LHslider.sliderReleased.connect(self.DisableLHSlider)
        self.ui.LHlineEdit.textChanged.connect(self.MoveLHSlider)
        self.ui.LHslider.hide()

        # -------------------------
        # Text Editing
        # -------------------------
        self.ui.EditCorrectedTextbutton.clicked.connect(self.loadText)
        self.ui.SaveAsOCRCorrTextbutton.clicked.connect(self.SaveAsCorrectedTextFileDialog)
        self.ui.SaveOCRCorrTextbutton.clicked.connect(self.SaveCorrectedTextFileDialog)

        # -------------------------
        # External Modules
        # -------------------------

        # Menu Modules
        self.ui.actionImageScanner.triggered.connect(self.actionScanNetwork)
        self.ui.actionImageScanner_tb.triggered.connect(self.actionScanNetwork)

        self.ui.actionMyExplorer.triggered.connect(self.OpenWithMyExplorer)
        self.ui.actionMyBoxer.triggered.connect(lambda: self.open_module("MyBoxer"))
        self.ui.actionMyGlypher.triggered.connect(lambda: self.open_module("MyGlypher"))
        self.ui.actionMyVersifier.triggered.connect(lambda: self.open_module("MyVersifier"))
        self.ui.actionMyResolver.triggered.connect(lambda: self.open_module("MyResolver"))
        self.ui.actionMyLexer.triggered.connect(lambda: self.open_module("MyLexer"))
        self.ui.actionMyGrounder.triggered.connect(lambda: self.open_module("MyGrounder"))
        self.ui.actionMyTrainer.triggered.connect(lambda: self.open_module("MyTrainer"))

        # Button Modules
        self.ui.MyExplorerbutton.clicked.connect(self.OpenWithMyExplorer)
        self.ui.MyWriterbutton.clicked.connect(lambda: self.open_module("MyWriter"))
        self.ui.MyPixlerbutton.clicked.connect(self.OpenWithMyPixler)

        # -------------------------
        # Misc UI
        # -------------------------
        self.ui.reloadImagebutton.clicked.connect(self.ReloadImage)
        self.ui.reloadTextbutton.clicked.connect(self.ReloadText)

        self.ui.fontComboBox.currentFontChanged.connect(self.on_font_update)
        self.ui.fontSizeBox.valueChanged.connect(self.on_font_update)

        self.ui.OCRModelComboBox.currentTextChanged.connect(self.on_lang_select)
        self.ui.bookComboBox.currentTextChanged.connect(self.selectBookCombo)

        # -------------------------
        # OCR Document Setup
        # -------------------------
        self.ui.OCRDocument = qtg.QTextDocument(self.ui.OCRText)

        font = self.session_manager.build_workflow_font(
            "FROMVS [MAXR]",
            20,
            os.path.dirname(os.path.realpath(__file__)),
        )

        self.ui.OCRDocument.setDefaultFont(font)
        self.ui.OCRText.setFont(font)

        self.ui.OCRBlockFormat = qtg.QTextBlockFormat()
        self.ui.OCRTextFormat = qtg.QTextFormat()
        self.ui.OCRCursor = qtg.QTextCursor(self.ui.OCRDocument)

        self.ui.OCRText.setDocument(self.ui.OCRDocument)

        self.ui.actionOCR_Preprocess.triggered.connect(self.open_preprocess_tool)

        self.imgfileList = []
        self.txtfileList = []
        self.imgdir = ""
        self.imgpath = ""
        self.txtdir = ""
        self.txtpath = ""
        self.pixler_return_path = ""
        self.pending_pixler_source_path = ""
        self._pixler_return_poll_timer = None
        self.pixler_return_prompt_dialog = None

        # -------------------------
        # Session Restore
        # -------------------------
        self.get_session_settings()
        self.OpenChrReference()

        print('current book:', self.bookabbr)

        # -------------------------
        # Final UI State
        # -------------------------
        self.show()
        qtc.QTimer.singleShot(0, self._restore_session_documents)

        self.toggleLatinToolbars()

        self.setWindowFlags(
            Qt.Window |
            Qt.WindowCloseButtonHint |
            Qt.WindowMinMaxButtonsHint        )
        # existing UI/event system
        self.event_bus = EventBus()

        # CORE ENGINE
        self.project_engine = CoreProjectCreationEngine(
            base_path=os.path.join(os.path.expanduser("~"), "Projects"),
            event_bus=self.event_bus,
            folder_list_path=os.path.join(RUNTIME_PATHS.script_dir, "ProjectFolderList.txt")
        )

        # optional: hook events
        self.event_bus.subscribe(
            "project_created",
            self.on_project_created
        )
        self._refresh_project_status()

    def _setup_developer_mode_ui(self):
        """Create hidden-by-default Developer Mode entry points.

        The Runtime Inspector is exposed through a Developer menu and remains
        inactive until the user explicitly opens it.
        """
        menu_bar = self.menuBar()
        self.developer_menu = menu_bar.addMenu("Developer")

        self.action_runtime_inspector = qtw.QAction("Runtime Inspector", self)
        self.action_runtime_inspector.setCheckable(True)
        self.action_runtime_inspector.setChecked(False)
        self.action_runtime_inspector.triggered.connect(
            self._toggle_runtime_inspector
        )
        self.developer_menu.addAction(self.action_runtime_inspector)

    def _toggle_runtime_inspector(self, checked):
        """Show or hide the Runtime Inspector dock on demand."""
        self._ensure_runtime_inspector_dock()

        if checked:
            self.runtime_inspector_dock.show()
            self.runtime_inspector_dock.raise_()
        else:
            self.runtime_inspector_dock.hide()

    def _ensure_runtime_inspector_dock(self):
        """Create the Runtime Inspector dock lazily."""
        if self.runtime_inspector_dock is not None:
            return

        self._ensure_developer_services()
        panel_module_path = os.path.join(
            RUNTIME_PATHS.developer_view_dir,
            "RuntimeInspectorPanel.py",
        )
        panel_module_spec = importlib.util.spec_from_file_location(
            "biblion_runtime_inspector_panel",
            panel_module_path,
        )
        panel_module = importlib.util.module_from_spec(panel_module_spec)
        panel_module_spec.loader.exec_module(panel_module)
        runtime_inspector_panel_class = panel_module.RuntimeInspectorPanel
        self.runtime_inspector_panel = runtime_inspector_panel_class(
            developer_services=self.developer_services,
            parent=self,
        )
        self.runtime_inspector_dock = qtw.QDockWidget(
            "Runtime Inspector",
            self,
        )
        self.runtime_inspector_dock.setObjectName("runtimeInspectorDock")
        self.runtime_inspector_dock.setWidget(self.runtime_inspector_panel)
        self.runtime_inspector_dock.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea
        )
        self.runtime_inspector_dock.visibilityChanged.connect(
            self._on_runtime_inspector_visibility_changed
        )
        self.addDockWidget(Qt.RightDockWidgetArea, self.runtime_inspector_dock)
        self.runtime_inspector_dock.hide()

    def _ensure_developer_services(self):
        """Create DeveloperServices only when a Developer panel is used."""
        if self.developer_services is not None:
            return

        self.developer_services = DeveloperServices(event_bus=self.event_bus)

    def _on_runtime_inspector_visibility_changed(self, visible):
        """Activate DeveloperServices observation only while the panel is in use."""
        if visible:
            self._activate_developer_services()
            if self.runtime_inspector_panel is not None:
                self.runtime_inspector_panel.refresh()
        else:
            self._deactivate_developer_services()

        if hasattr(self, "action_runtime_inspector"):
            self.action_runtime_inspector.blockSignals(True)
            self.action_runtime_inspector.setChecked(bool(visible))
            self.action_runtime_inspector.blockSignals(False)

    def _activate_developer_services(self):
        """Attach DeveloperServices to passive EventBus observation."""
        self._ensure_developer_services()
        if self._developer_services_active:
            return

        self.event_bus.subscribe("*", self.developer_services.observe_event)
        self._developer_services_active = True

    def _deactivate_developer_services(self):
        """Detach DeveloperServices when Developer Mode is not in use."""
        if not self._developer_services_active or self.developer_services is None:
            return

        self.event_bus.unsubscribe("*", self.developer_services.observe_event)
        self._developer_services_active = False

    def _apply_scan_icon(self):
        scan_icon = qtg.QIcon()
        for resource_path in SCAN_ICON_RESOURCES:
            scan_icon = qtg.QIcon(resource_path)
            if not scan_icon.isNull():
                break

        if scan_icon.isNull():
            for file_path in SCAN_ICON_FILES:
                if os.path.exists(file_path):
                    scan_icon = qtg.QIcon(file_path)
                    if not scan_icon.isNull():
                        break

        if scan_icon.isNull():
            return

        if hasattr(self.ui, "imageScannerbutton"):
            self.ui.imageScannerbutton.setIcon(scan_icon)
            self.ui.imageScannerbutton.setIconSize(qtc.QSize(20, 20))
            self.ui.imageScannerbutton.setToolTip("Scan image")

        if hasattr(self.ui, "actionImageScanner"):
            self.ui.actionImageScanner.setIcon(scan_icon)
            self.ui.actionImageScanner.setIconVisibleInMenu(True)

        if hasattr(self.ui, "actionImageScanner_tb"):
            self.ui.actionImageScanner_tb.setIcon(scan_icon)
            self.ui.actionImageScanner_tb.setIconVisibleInMenu(True)

    def _init_project_status_widgets(self):
        self.workflow_tracker = ProjectWorkflowTracker(workspace_root=RUNTIME_PATHS.project_root)

        self.project_name_status_label = qtw.QLabel("Project: none")
        self.project_name_status_label.setMinimumWidth(180)

        self.workflow_status_label = qtw.QLabel("MyServer 0/4 | Next: Project initialized")
        self.workflow_status_label.setMinimumWidth(360)

        self.project_overall_status_bar = qtw.QProgressBar()
        self.project_overall_status_bar.setRange(0, 100)
        self.project_overall_status_bar.setValue(0)
        self.project_overall_status_bar.setTextVisible(True)
        self.project_overall_status_bar.setFormat("Project 0%")
        self.project_overall_status_bar.setFixedWidth(140)
        self.project_overall_status_bar.setAlignment(Qt.AlignCenter)

        self.project_tracking_button = qtw.QPushButton("Milestones")
        self.project_tracking_button.setFixedHeight(24)
        self.project_tracking_button.clicked.connect(self._open_project_tracking_dialog)

        self.statusBar().addPermanentWidget(self.project_name_status_label)
        self.statusBar().addPermanentWidget(self.workflow_status_label)
        self.statusBar().addPermanentWidget(self.project_overall_status_bar)
        self.statusBar().addPermanentWidget(self.project_tracking_button)

    def _format_module_workflow_status(self, module_name, snapshot):
        module_total = int(snapshot.get("module_total_count", 0))
        module_completed = int(snapshot.get("module_completed_count", 0))
        next_label = snapshot.get("module_next_label", "")

        if module_total <= 0:
            return f"{module_name} | No milestones configured"
        if next_label == "Complete":
            return f"{module_name} {module_completed}/{module_total} | Complete"
        return f"{module_name} {module_completed}/{module_total} | Next: {next_label}"

    def _shared_active_project_root(self):
        return self.session_manager.get_active_project_root()

    def _current_model_dir(self):
        project_root_value = self.current_project_root or self._shared_active_project_root()
        if project_root_value:
            candidate = os.path.join(project_root_value, "Model")
            if os.path.isdir(candidate):
                return candidate
        return RUNTIME_PATHS.model_dir

    def _set_current_project(self, project_root):
        if not project_root:
            return None

        resolved_root = self.workflow_tracker.resolve_project_root(project_root) or os.path.abspath(os.path.normpath(project_root))
        self.current_project_root = resolved_root
        self.session_manager.set_active_project(resolved_root)
        return resolved_root

    def _refresh_project_status(self, candidate_path=None):
        snapshot = self.workflow_tracker.snapshot(
            "MyServer",
            project_root=self.current_project_root,
            candidate_paths=(
                self._shared_active_project_root(),
                candidate_path,
                self.current_project_root,
                getattr(self, "imgpath", ""),
                getattr(self, "imgdir", ""),
                getattr(self, "txtpath", ""),
                getattr(self, "txtdir", ""),
            ),
        )

        project_root_value = snapshot.get("project_root")
        if project_root_value:
            self._set_current_project(project_root_value)

        project_name = snapshot.get("project_name", "none")
        self.project_name_status_label.setText(f"Project: {project_name}")
        self.project_name_status_label.setToolTip(project_root_value or "No active project selected")

        completed_labels = snapshot.get("completed_labels", [])
        completed_text = ", ".join(completed_labels) if completed_labels else "None yet"
        overall_percent = int(snapshot.get("overall_percent", 0))
        overall_next = snapshot.get("overall_next_label", "")
        tooltip = f"Overall {overall_percent}%\nCompleted: {completed_text}\nNext: {overall_next}"

        self.workflow_status_label.setText(self._format_module_workflow_status("MyServer", snapshot))
        self.workflow_status_label.setToolTip(tooltip)
        self.project_overall_status_bar.setValue(overall_percent)
        self.project_overall_status_bar.setFormat(f"Project {overall_percent}%")
        self.project_overall_status_bar.setToolTip(tooltip)

    def _record_project_milestone(self, milestone_key, candidate_path=None, details=None):
        project_root = self.workflow_tracker.resolve_project_root(
            self._shared_active_project_root(),
            candidate_path,
            self.current_project_root,
            getattr(self, "imgpath", ""),
            getattr(self, "imgdir", ""),
        )
        if not project_root:
            return None

        self._set_current_project(project_root)
        self.workflow_tracker.record_milestone(
            project_root,
            milestone_key,
            module_name="MyServer",
            details=details,
        )
        self._refresh_project_status(project_root)
        return project_root

    def _open_project_tracking_dialog(self):
        project_root = self.workflow_tracker.resolve_project_root(
            self._shared_active_project_root(),
            self.current_project_root,
            getattr(self, "imgpath", ""),
            getattr(self, "imgdir", ""),
            getattr(self, "txtpath", ""),
            getattr(self, "txtdir", ""),
        )
        if not project_root:
            qtw.QMessageBox.information(
                self,
                "Project Milestones",
                "Open or create a project first so milestone state can be edited.",
            )
            return

        self._set_current_project(project_root)
        self.workflow_tracker.ensure_tracking_state(project_root)
        dialog = ProjectTrackingDialog(self.workflow_tracker, project_root, "MyServer", self)
        dialog.exec_()
        self._refresh_project_status(project_root)

    def on_new_project_clicked(self):
        payload = self.collect_new_project_payload()
        if payload is None:
            return None

        project_path = os.path.join(self.project_engine.base_path, payload["project_name"])
        self._pending_project_root = project_path
        if os.path.exists(project_path):
            answer = qtw.QMessageBox.question(
                self,
                "Replace Existing Project",
                f"Project {payload['project_name']} already exists. Delete it and recreate it?",
                qtw.QMessageBox.Yes | qtw.QMessageBox.No,
                qtw.QMessageBox.No,
            )
            if answer != qtw.QMessageBox.Yes:
                self._pending_project_root = None
                return None
            payload["overwrite_existing"] = True

        self._start_project_creation(
            payload,
            success_title="Project Created",
            success_message=f"Project created: {payload['project_name']}"
        )

    def on_open_project_clicked(self):
        project_path = self._choose_directory("Select project folder", self._projects_base_path())
        if not project_path:
            return None

        model_project_path = os.path.join(project_path, "Model", "Project")
        if not os.path.isdir(model_project_path):
            qtw.QMessageBox.warning(
                self,
                "Open Project",
                "Selected folder does not look like a BiblionOCR project root. Expected Model/Project under the selected folder.",
            )
            return None

        self._set_current_project(project_path)
        self.workflow_tracker.ensure_tracking_state(project_path)
        self._record_project_milestone("project_ready", project_path)
        self._refresh_project_status(project_path)
        self.statusBar().showMessage(f"Project selected: {project_path}", 5000)
        self.run_child_module('MyExplorer.py', model_project_path)
        return project_path
        return payload

    def _start_project_creation(self, payload, success_title, success_message):
        if self._project_thread is not None:
            qtw.QMessageBox.information(
                self,
                "Project Creation In Progress",
                "Wait for the current project creation task to finish."
            )
            return None

        self._project_success_title = success_title
        self._project_success_message = success_message

        self._project_thread = qtc.QThread()
        self._project_worker = ProjectCreationWorker(self.project_engine, payload)
        self._project_worker.moveToThread(self._project_thread)

        self._project_thread.started.connect(self._project_worker.run)
        self._project_worker.progress.connect(self.on_project_progress)
        self._project_worker.finished.connect(self.on_project_created_result)
        self._project_worker.error.connect(self.on_project_creation_error)

        self._project_worker.finished.connect(self._project_thread.quit)
        self._project_worker.finished.connect(self._project_worker.deleteLater)
        self._project_worker.error.connect(self._project_thread.quit)
        self._project_worker.error.connect(self._project_worker.deleteLater)
        self._project_thread.finished.connect(self._project_thread.deleteLater)
        self._project_thread.finished.connect(self._on_project_thread_finished)

        self._project_thread.start()

        self._show_progress(0)

        return payload

    def on_project_progress(self, value):
        self._set_progress_percent(value)

    def on_project_created_result(self, result):
        self._hide_progress(100)

        if result.get("status") in {"success", "ok"}:
            if self._pending_project_root:
                self._set_current_project(self._pending_project_root)
                self.workflow_tracker.ensure_tracking_state(self._pending_project_root)
                self._record_project_milestone(
                    "project_ready",
                    self._pending_project_root,
                    details={"source": "project_creation"},
                )
                self._refresh_project_status(self._pending_project_root)
            qtw.QMessageBox.information(
                self,
                self._project_success_title,
                self._project_success_message,
            )
        else:
            qtw.QMessageBox.warning(
                self,
                "Project Creation Failed",
                result.get("error", "Unknown error")
            )
        self._pending_project_root = None

    def on_project_creation_error(self, msg):
        self._hide_progress()
        self._pending_project_root = None

        qtw.QMessageBox.warning(
            self,
            "Project Creation Failed",
            msg,
        )

    def _on_project_thread_finished(self):
        self._project_thread = None
        self._project_worker = None

    def _set_progress_percent(self, value):
        if not hasattr(self, "progress_bar"):
            return

        bounded = max(0, min(100, int(value)))
        self.progress_bar.setValue(bounded * self._progress_bar_scale)

    def _show_progress(self, value=0):
        if not hasattr(self, "progress_bar"):
            return

        self._set_progress_percent(value)
        self.progress_bar.setVisible(True)

    def _hide_progress(self, value=None):
        if not hasattr(self, "progress_bar"):
            return

        if value is not None:
            self._set_progress_percent(value)
        self.progress_bar.setVisible(False)

    def open_project_settings_dialog(self):
        dialog = ProjectSettingsDialog(RUNTIME_PATHS.project_root, self.session_manager, self)
        dialog.exec_()

    def collect_new_project_payload(self):
        dialog = ProjectCreationWizardDialog(self._projects_base_path(), self)
        if dialog.exec_() != qtw.QDialog.Accepted:
            return None

        payload = dialog.get_payload()
        project_name = self._normalize_project_name(payload.get("project_name", ""))
        if project_name is None:
            qtw.QMessageBox.warning(self, "New Project", "Project name is required.")
            return None

        payload["project_name"] = project_name
        if not payload.get("project_purpose"):
            qtw.QMessageBox.warning(self, "New Project", "Project purpose is required.")
            return None
        if not payload.get("user_intent_summary"):
            qtw.QMessageBox.warning(self, "New Project", "User intent summary is required.")
            return None
        return payload

    def _normalize_project_name(self, name):
        name = name.strip()
        if not name:
            return None

        safe_name = re.sub(r"[^A-Za-z0-9_. -]+", "_", name).strip(" .")
        if not safe_name:
            qtw.QMessageBox.warning(self, "New Project", "Project name is invalid.")
            return None
        if safe_name != name:
            qtw.QMessageBox.information(
                self,
                "New Project",
                f"Project name was normalized to: {safe_name}"
            )
        return safe_name

    def on_project_created(self, event):
        print("UI: Project created!", event["project_name"])

    # def actionScanNetwork(self):
    #     self.ui.imageScannerbutton.setEnabled(False)
    #     self.networkScanner = NetworkScanner()
    #     self.networkScanner.deviceFound.connect(self.onDeviceFound)
    #     self.networkScanner.progress.connect(self.onScanProgress)
    #     self.networkScanner.finished.connect(self.onScanFinished)
    #     self.networkScanner.start()
    def actionScanNetwork(self):
        dialog = SharedScanWizardDialog(
            self.scannerManager,
            SCANNED_FOLDER,
            self,
            initial_request=self._default_scan_request(),
        )
        if dialog.exec_() != qtw.QDialog.Accepted:
            return None

        request = dialog.get_request()
        if request.get("source_type") == "adf":
            self._redirect_scan_to_myscanner(request)
            return request
        self._persist_scan_request(request)
        return self._start_scan_workflow(request)

        # self.netDialog = NetworkScanDialog(self)
        # self.netDialog.show()

    def _start_scan_workflow(self, request):
        return start_scan_workflow(
            self,
            self.scannerManager,
            request,
            self.on_scan_progress,
            self.on_scan_result,
            self.on_scan_error,
            self._on_scan_thread_finished,
            before_start=lambda: self._show_progress(0),
        )

    def on_scan_progress(self, value):
        self._set_progress_percent(value)

    def on_scan_result(self, result):
        self._hide_progress(100)

        if result.get("status") not in {"success", "ok"}:
            qtw.QMessageBox.warning(
                self,
                "Scan Failed",
                result.get("error", "Unknown scan error")
            )
            return

        self.showImage(result["path"])
        self._record_project_milestone(
            "source_acquired",
            result["path"],
            details={"backend": result.get("backend", "scanner backend")},
        )
        self.statusBar().showMessage(
            f"Scanned via {result.get('backend', 'scanner backend')}: {result['path']}",
            5000,
        )

    def on_scan_error(self, msg):
        self._hide_progress()
        qtw.QMessageBox.warning(self, "Scan Failed", msg)

    def _on_scan_thread_finished(self):
        self._scan_thread = None
        self._scan_worker = None

    def _default_scan_request(self):
        return self.scannerManager.request_from_state(self, SCANNED_FOLDER)

    def _persist_scan_request(self, request):
        normalized_request = self.scannerManager.apply_request_state(self, request, SCANNED_FOLDER)

        self.session_manager.update(
            'Session.json',
            self.scannerManager.session_payload(normalized_request),
        )

    def _redirect_scan_to_myscanner(self, request):
        normalized_request = self.scannerManager.normalize_request(request, SCANNED_FOLDER)

        self.session_manager.update(
            'ScannerSession.json',
            self.scannerManager.session_payload(
                normalized_request,
                pending_scan_handoff=True,
            ),
        )
        self.run_child_module('MyScanner.py')
        qtw.QMessageBox.information(
            self,
            'Continue In MyScanner',
            'ADF workflows are routed through MyScanner. It has been opened with this scan request so you can continue there.'
        )

    # def onDeviceFound(self, device):
    #     row = self.ui.NetworkTable.rowCount()
    #     self.ui.NetworkTable.insertRow(row)

    #     self.ui.NetworkTable.setItem(row, 0,
    #         qtw.QTableWidgetItem(device["ip"]))

    #     self.ui.NetworkTable.setItem(row, 1,
    #         qtw.QTableWidgetItem(device["mac"]))

    # # def onDeviceFound(self, device):
    # #     print(f"[FOUND] {device['ip']}   {device['mac']}")

    # def onScanProgress(self, value):
    #     print(f"[SCAN] {value}%")

    #     if hasattr(self.ui, "progressBar"):
    #         self.ui.progressBar.setValue(value)

    # def onScanFinished(self):
    #     print("[NETWORK] Scan complete.")
    #     self.ui.imageScannerbutton.setEnabled(True)

    @qtc.pyqtSlot(str)
    def on_zoom_combobox(self, text=None):
        if text is None:
            text = self.ui.ZoomComboBox.currentText()

        print("[ZOOM HANDLER HIT] ComboBox")

        try:
            value = int(text.replace("%", ""))
        except:
            print("[ZOOM ERROR] Invalid text:", text)
            return

        self.ui.Zoomslider.setValue(value)  # drives everything

    # def on_zoom_combobox(self, text):
    #     print("[ZOOM HANDLER HIT] ComboBox")

    #     try:
    #         value = int(text.replace("%", ""))
    #     except:
    #         print("[ZOOM ERROR] Invalid ComboBox value:", text)
    #         return

    #     # Sync slider (this will trigger on_zoomslider)
    #     self.ui.Zoomslider.setValue(value)

    def get_session_settings(self):
        # get session settings from shared manager
        print("loading session")
        session = SessionManager().values('Session.json')

        def get_setting(name: str, default=None):
            if default is None:
                default = getattr(self, name, None)
            return session.get(f'self.{name}', default)

        self.ocrlang = get_setting('ocrlang', '')
        self.ocrmodel = get_setting('ocrmodel', '')
        self.tessdatadir = get_setting('tessdatadir', '')
        self.tesseract = get_setting('tesseract', '')
        self.tesstrain = get_setting('tesstrain', '')
        self.bookabbr = get_setting('bookabbr', '')
        self.chapter = get_setting('chapter', '1')
        self.verse = get_setting('verse', '1')
        self.word = get_setting('word', '1')
        self.chr = get_setting('chr', '1')
        self.font = get_setting('font', '')
        self.fontsize = get_setting('fontsize', '20')
        self.linespacing = get_setting('linespacing', '')
        self.sourcebookmarkdown = get_setting('sourcebookmarkdown', '')
        self.greekbookmarkdown = get_setting('greekbookmarkdown', '')
        self.latinbookmarkdown = get_setting('latinbookmarkdown', '')
        self.sourcefile = get_setting('sourcefile', '')
        self.firstpage = get_setting('firstpage', '1')
        self.lastpage = get_setting('lastpage', '1')
        self.deltapages = get_setting('deltapages', '1')
        self.imgpath = get_setting('imgpath', '')
        self.imgdir = get_setting('imgdir', '')
        self.imgfileList = get_setting('imgfileList', [])
        # self.pixmap = get_setting('pixmap', None)
        self.qimage = get_setting('qimage', None)
        self.zoom = get_setting('zoom', '')
        self.zoomslidervalue = get_setting('zoomslidervalue', 0)
        self.txtpath = get_setting('txtpath', '')
        self.txtdir = get_setting('txtdir', '')
        self.scannerManager.apply_request_state(
            self,
            {
                'destination_folder': get_setting('scan_destination_folder', SCANNED_FOLDER),
                'backend_preference': get_setting('scan_backend_preference', 'ESCLScanner'),
                'device_name': get_setting('scan_device_name', ''),
                'allow_network_fallback': get_setting('scan_allow_network_fallback', True),
                'mode': get_setting('scan_mode', 'color'),
                'dpi': get_setting('scan_dpi', 300),
                'source_type': get_setting('scan_source_type', 'flatbed'),
                'duplex': get_setting('scan_duplex', False),
                'persist_format': get_setting('scan_persist_format', 'tiff'),
            },
            SCANNED_FOLDER,
        )

        #self.origpixmap = qtg.QPixmap.fromImage(qtg.QImage())
        if hasattr(self, 'ui'):
            self.ui.OCRlangComboBox.setCurrentText(self.ocrlang)
            self.ui.OCRModelComboBox.setCurrentText(self.ocrmodel)
            self.ui.bookComboBox.setCurrentText(self.bookabbr)
            self.ui.fontComboBox.setCurrentText(self.font)
            if str(self.fontsize).isdigit():
                self.ui.fontSizeBox.setValue(int(self.fontsize))
            self.ui.LHlineEdit.setText(self.linespacing)
            self.ui.ZoomComboBox.setCurrentText(self.zoom)
            if str(self.zoomslidervalue).isdigit():
                self.ui.Zoomslider.setValue(int(self.zoomslidervalue))

    def get_workflow_settings(self):

        # Opening JSON file
        jsonfile = os.path.join(RUNTIME_PATHS.project_root, "Model", "Project", "Data", "json", "Workflow.json")
        with open(jsonfile, 'r') as f:
            data = json.load(f)

            # Iterating through the json
            # list
            for Sequence in data:
                print(Sequence['Sequence'], Sequence['DialogUi'],Sequence['DefaultSource'])

        # Closing file
        f.close()

    def _restore_session_documents(self):
        if self.imgpath and os.path.isfile(self.imgpath):
            self.showImage(self.imgpath)

        if self.txtpath and os.path.isfile(self.txtpath):
            self.showText(self.txtpath)

    def OpenChrReference(self):
        self.chrrefmain = chrref.CharacterReference()
        self.chrrefmain.show()

    def initBookCombo(self):
        # Opening JSON file
        jsonfile = os.path.join(RUNTIME_PATHS.project_root, "Model", "Project", "Data", "json", "BooksAbbrName.json")
        with open(jsonfile, 'r') as f:
            data = json.load(f)
        # Iterating through the json
        # list
            for booknumber in data:
                print(booknumber['bookabbr'])
                self.ui.bookComboBox.addItem(booknumber['bookabbr'])

        # Closing file
        f.close()

    def selectBookCombo(self):
        oldbookabbr = self.bookabbr
        self.bookabbr = self.ui.bookComboBox.currentText()

        if self.ui.bookComboBox.currentText() != oldbookabbr:

            # jsonfile = 'Model/Data/json/BooksMarkDown.json'
            jsonfile = os.path.join(RUNTIME_PATHS.project_root, "Model", "Project", "Data", "json", "BooksMarkDown.json")

            with open(jsonfile, 'r') as f:
                data = json.load(f)
                for BookAbbr in data:
                    if BookAbbr['BookAbbr'] == self.bookabbr:
                        bookmarkdown = BookAbbr['BookMarkdown']
                        self.sourcebookmarkdown = 'source' + bookmarkdown
                        self.greekbookmarkdown = 'greek' + bookmarkdown
                        self.latinbookmarkdown = 'latin' + bookmarkdown
            f.close()

            #jsonfile = 'Model/Data/json/Session.json'
            jsonfile = os.path.join(RUNTIME_PATHS.project_root, "Model", "Project", "Data", "json", "Session.json")

            with open(jsonfile, 'r') as f:
                data = json.load(f)
                bookabbr_key = r"self.bookabbr"
                source_book_markdown_key = r"self.sourcebookmarkdown"
                greek_book_markdown_key = r"self.greekbookmarkdown"
                latin_book_markdown_key = r"self.latinbookmarkdown"

                for Setting in data:
                    if Setting['Setting'] == bookabbr_key:
                        Setting['CurrentValue'] = self.bookabbr
                    elif Setting['Setting'] == source_book_markdown_key:
                        Setting['CurrentValue'] = self.sourcebookmarkdown
                    elif Setting['Setting'] == greek_book_markdown_key:
                        Setting['CurrentValue'] = self.greekbookmarkdown
                    elif Setting['Setting'] == latin_book_markdown_key:
                        Setting['CurrentValue'] = self.latinbookmarkdown
                    print(Setting['CurrentValue'])
            f.close()

            os.remove(jsonfile)
            with open(jsonfile, 'w') as f:
                json.dump(data, f, indent=4)
            f.close()

        self.ui.bookComboBox.setCurrentText(self.bookabbr)

    def toggleGreekToolbars(self):

        greekimgpagesstate = self.ui.GreekImagePagesToolBar.isVisible()
        greekimglinesstate = self.ui.GreekImageLinesToolBar.isVisible()
        greektxtlinesstate = self.ui.GreekTextLinesToolBar.isVisible()

        # Set the visibility to its inverse
        self.ui.GreekImagePagesToolBar.setVisible(not greekimgpagesstate)
        self.ui.GreekImageLinesToolBar.setVisible(not greekimglinesstate)
        self.ui.GreekTextLinesToolBar.setVisible(not greektxtlinesstate)

    def toggleLatinToolbars(self):

        latinimgpagesstate = self.ui.LatinImagePagesToolBar.isVisible()
        latinimglinesstate = self.ui.LatinImageLinesToolBar.isVisible()
        latintxtlinesstate = self.ui.LatinTextLinesToolBar.isVisible()

        # Set the visibility to its inverse
        self.ui.LatinImagePagesToolBar.setVisible(not latinimgpagesstate)
        self.ui.LatinImageLinesToolBar.setVisible(not latinimglinesstate)
        self.ui.LatinTextLinesToolBar.setVisible(not latintxtlinesstate)

    def actionextract_pdf(self):
        print("extracting pdf pages from source pdf")

        def accept():
            # Empty default Workflow folder
            print('Workflow Folder:'+ workflow_folder,'Complete Folder:'+ complete_folder)
            for filename in os.listdir(workflow_folder):
                file_path = os.path.join(workflow_folder, filename)
                #print('File Name:'+filename, 'File Path:'+file_path)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))

            self.sourcefile = self.pdfx_ui.SourceLineEdit.text()
            self.firstpage = self.pdfx_ui.FirstPageLineEdit.text()
            self.lastpage = self.pdfx_ui.LastPageLineEdit.text()

            # Extract to default Workflow folder
            print(self.pdfx_ui.SourceLineEdit.text(), self.pdfx_ui.DestinationLineEdit.text(),self.pdfx_ui.FirstPageLineEdit.text(),self.pdfx_ui.LastPageLineEdit.text())
            pp.pdfExtractPages(self.pdfx_ui.SourceLineEdit.text(), self.pdfx_ui.DestinationLineEdit.text(),self.pdfx_ui.FirstPageLineEdit.text(),self.pdfx_ui.LastPageLineEdit.text())

            if complete_folder:
                symlinks=False
                ignore=None
                for item in os.listdir(workflow_folder):
                    source = os.path.join(workflow_folder, item)
                    destination = os.path.join(complete_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)
            print("pdf page extraction complete")

            jsonfile = os.path.join(RUNTIME_PATHS.project_root, "Model", "Project", "Data", "json", "Session.json")
            with open(jsonfile, 'r') as f:
                data = json.load(f)
                sourcefile_key = r"self.sourcefile"
                firstpage_key = r"self.firstpage"
                lastpage_key = r"self.lastpage"
                for Setting in data:
                    if Setting['Setting'] == sourcefile_key:
                        Setting['CurrentValue'] = self.sourcefile
                        print(Setting['CurrentValue'])
                    elif Setting['Setting'] == firstpage_key:
                        Setting['CurrentValue'] = self.firstpage
                        print(Setting['CurrentValue'])
                    elif Setting['Setting'] == lastpage_key:
                        Setting['CurrentValue'] = self.lastpage
                        print(Setting['CurrentValue'])
            f.close()

            os.remove(jsonfile)
            with open(jsonfile, 'w') as f:
                json.dump(data, f, indent=4)
            f.close()

        def reject():
            pass

        self.pdfxDialog = qtw.QDialog()
        self.pdfx_ui = Ui_ExtractDialog()
        self.pdfx_ui.setupUi(self.pdfxDialog)
        self.pdfxDialog.show()

        seq = "SP1"

        def setdefault():
            if self.pdfx_ui.defaultsrcBox.isChecked():
                self.pdfx_ui.SourceButton.setEnabled(False)
                self.pdfx_ui.DestinationButton.setEnabled(False)
            else:
                self.pdfx_ui.SourceButton.setEnabled(True)
                self.pdfx_ui.DestinationButton.setEnabled(True)

        self.pdfx_ui.defaultsrcBox.stateChanged.connect(setdefault)
        self.pdfx_ui.SourceButton.clicked.connect(self.OpenPdfFileDialog)
        self.pdfx_ui.DestinationButton.clicked.connect(self.DestPdfFileDialog)
        self.pdfx_ui.buttonBox.accepted.connect(accept)
        self.pdfx_ui.buttonBox.rejected.connect(reject)

        if self.pdfx_ui.defaultsrcBox.isChecked():
            jsonfile = os.path.join(RUNTIME_PATHS.project_root, "Model", "Project", "Data", "json", "Workflow.json")
            with open(jsonfile, 'r') as f:
                data = json.load(f)
               # Search the key value using 'in' operator
                for Sequence in data:
                    print(Sequence['Sequence'])
                    if Sequence['Sequence'] == seq:
                        # set source line edit to default workflow folder
                        self.pdfx_ui.SourceLineEdit.setText(Sequence['DefaultSource'])
                        self.pdfx_ui.DestinationLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                        workflow_folder = Sequence['WorkflowFullPath']+r'/'
                        complete_folder = Sequence['CompleteFullPath']+r'/'

        rsp = self.pdfxDialog.exec_()

    def actionpdf_for_tiff(self):
        print("extracting pdf pages for tif")

        def accept():
            # if self.pdf4tifDialog.Accepted:
            # Empty default Workflow folder
            print('Workflow Folder:'+ workflow_folder,'Complete Folder:'+ complete_folder)
            for filename in os.listdir(workflow_folder):
                file_path = os.path.join(workflow_folder, filename)
                print('File Name:'+filename, 'File Path:'+file_path)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))

            for filename in os.listdir(source_folder):
                print(source_folder,filename)
                source_file_path = os.path.join(source_folder, filename)

            # Extract to default Workflow folder
            print(source_file_path, workflow_folder)
            pp.pdf4tif(source_file_path, workflow_folder)
            # Extract to default Complete folder
            if complete_folder:
                symlinks=False
                ignore=None
                for item in os.listdir(workflow_folder):
                    source = os.path.join(workflow_folder, item)
                    destination = os.path.join(complete_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)
            print("pdf pages for tif extraction complete")
        def reject():
            pass

        self.pdf4tifDialog = qtw.QDialog()
        self.pdf4tif_ui = Ui_pdf4tifDialog()
        self.pdf4tif_ui.setupUi(self.pdf4tifDialog)
        self.pdf4tifDialog.show()

        seq = "SP2"

        def setdefault():
            if self.pdf4tif_ui.defaultsrcBox.isChecked():
                self.pdf4tif_ui.SourceButton.setEnabled(False)
                self.pdf4tif_ui.DestinationButton.setEnabled(False)
            else:
                self.pdf4tif_ui.SourceButton.setEnabled(True)
                self.pdf4tif_ui.DestinationButton.setEnabled(True)

        self.pdf4tif_ui.defaultsrcBox.stateChanged.connect(setdefault)
        self.pdf4tif_ui.SourceButton.clicked.connect(self.PdfForTifDialog)
        self.pdf4tif_ui.DestinationButton.clicked.connect(self.DestPdfForTifDialog)
        self.pdf4tif_ui.buttonBox.accepted.connect(accept)
        self.pdf4tif_ui.buttonBox.rejected.connect(reject)


        if self.pdf4tif_ui.defaultsrcBox.isChecked():
            # get default folder
            # Define json data
            jsonfile = os.path.join(RUNTIME_PATHS.project_root, "Model", "Project", "Data", "json", "Workflow.json")
            with open(jsonfile, 'r') as f:
                data = json.load(f)
                # Search the key value using 'in' operator
                for Sequence in data:
                    print(Sequence['Sequence'])
                    if Sequence['Sequence'] == seq:
                        # set source line edit to default workflow folder
                        self.pdf4tif_ui.SourceLineEdit.setText(Sequence['DefaultSource'])
                        self.pdf4tif_ui.DestinationLineEdit.setText(Sequence['WorkflowFullPath'])
                        source_folder = Sequence['DefaultSource']+r'/'
                        workflow_folder = Sequence['WorkflowFullPath']+r'/'
                        complete_folder = Sequence['CompleteFullPath']+r'/'
                        print(source_folder,workflow_folder,complete_folder)

        rsp = self.pdf4tifDialog.exec_()

    def actionpdf_to_tiff(self):
        print("converting pdf pages to tiff")

        def accept():
        # if self.pdf2tifDialog.Accepted:
            # Empty default Workflow folder
            print('Workflow Folder:'+ workflow_folder,'Complete Folder:'+ complete_folder)
            for filename in os.listdir(workflow_folder):
                file_path = os.path.join(workflow_folder, filename)
                print('File Name:'+filename, 'File Path:'+file_path)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))

            for filename in os.listdir(source_folder):
                print(source_folder,filename)
                source_file_path = os.path.join(source_folder, filename)

            # Extract to default Workflow folder
            print(source_folder, workflow_folder)
            #pp.pdf2tif(source_folder, workflow_folder, self.pdf2tif_ui.StartPageLineEdit.text())
            pp.pdf2tif(self.pdf2tif_ui.SourceLineEdit.text(), self.pdf2tif_ui.DestinationLineEdit.text(), self.pdf2tif_ui.StartPageLineEdit.text())
            # Copy Workflow folder to default Complete folder
            if complete_folder:
                symlinks=False
                ignore=None
                for item in os.listdir(workflow_folder):
                    source = os.path.join(workflow_folder, item)
                    destination = os.path.join(complete_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)
        def reject():
            pass

        self.pdf2tifDialog = qtw.QDialog()
        self.pdf2tif_ui = Ui_pdf2tifDialog()
        self.pdf2tif_ui.setupUi(self.pdf2tifDialog)
        self.pdf2tifDialog.show()

        seq = "SP3"

        def setdefault():
            if self.pdf2tif_ui.defaultsrcBox.isChecked():
                self.pdf2tif_ui.SourceButton.setEnabled(False)
                self.pdf2tif_ui.DestinationButton.setEnabled(False)
            else:
                self.pdf2tif_ui.SourceButton.setEnabled(True)
                self.pdf2tif_ui.DestinationButton.setEnabled(True)

        self.pdf2tif_ui.defaultsrcBox.stateChanged.connect(setdefault)
        self.pdf2tif_ui.SourceButton.clicked.connect(self.PdfToTifDialog)
        self.pdf2tif_ui.DestinationButton.clicked.connect(self.DestPdfToTifDialog)
        self.pdf2tif_ui.buttonBox.accepted.connect(accept)
        self.pdf2tif_ui.buttonBox.rejected.connect(reject)

        if self.pdf2tif_ui.defaultsrcBox.isChecked():
            # get default folder
            # Define json data
            jsonfile = os.path.join(RUNTIME_PATHS.project_root, "Model", "Project", "Data", "json", "Workflow.json")
            with open(jsonfile, 'r') as f:
                data = json.load(f)
                # Search the key value using 'in' operator
                for Sequence in data:
                    print(Sequence['Sequence'])
                    if Sequence['Sequence'] == seq:
                        # set source line edit to default workflow folder
                        self.pdf2tif_ui.SourceLineEdit.setText(Sequence['DefaultSource']+r'/')
                        self.pdf2tif_ui.DestinationLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                        source_folder = Sequence['DefaultSource']+r'/'
                        workflow_folder = Sequence['WorkflowFullPath']+r'/'
                        complete_folder = Sequence['CompleteFullPath']+r'/'
                        start_page = self.firstpage
                        self.pdf2tif_ui.StartPageLineEdit.setText(start_page)
                        print(source_folder,workflow_folder,complete_folder,start_page)

            rsp = self.pdf2tifDialog.exec_()

        print("tif pages conversion complete")

    def actiontiff_to_mono(self):
        print("creating indexed(BW) tiff")

        def accept():
            # if self.tif2monoDialog.Accepted:
            # Empty default Workflow folder
            print('Workflow Folder:'+ workflow_folder,'Complete Folder:'+ complete_folder)
            for filename in os.listdir(workflow_folder):
                file_path = os.path.join(workflow_folder, filename)
                print('File Name:'+filename, 'File Path:'+file_path)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))

            for filename in os.listdir(source_folder):
                print(source_folder,filename)
                source_file_path = os.path.join(source_folder, filename)

            # Extract to default Workflow folder
            print(source_folder, workflow_folder)
            pp.tiff2tiffidx(self.tif2mono_ui.SourceLineEdit.text(), self.tif2mono_ui.DestinationLineEdit.text())
            # Copy Workflow folder to default Complete folder
            if complete_folder:
                #pp.pdf2tif(source_folder, complete_folder, self.pdf2tif_ui.StartPageLineEdit.text())
                symlinks=False
                ignore=None
                for item in os.listdir(workflow_folder):
                    source = os.path.join(workflow_folder, item)
                    destination = os.path.join(complete_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)
        def reject():
            pass

        #usage: pp.tiff2tiffidx(source, destination)

        self.tif2monoDialog = qtw.QDialog()
        self.tif2mono_ui = Ui_tif2monoDialog()
        self.tif2mono_ui.setupUi(self.tif2monoDialog)
        self.tif2monoDialog.show()

        seq = "SP4"

        def setdefault():
            if self.tif2mono_ui.defaultsrcBox.isChecked():
                self.tif2mono_ui.SourceButton.setEnabled(False)
                self.tif2mono_ui.DestinationButton.setEnabled(False)
            else:
                self.tif2mono_ui.SourceButton.setEnabled(True)
                self.tif2mono_ui.DestinationButton.setEnabled(True)

        self.tif2mono_ui.defaultsrcBox.stateChanged.connect(setdefault)
        self.tif2mono_ui.SourceButton.clicked.connect(self.TifToMonoDialog)
        self.tif2mono_ui.DestinationButton.clicked.connect(self.DestTifToMonoDialog)
        self.tif2mono_ui.buttonBox.accepted.connect(accept)
        self.tif2mono_ui.buttonBox.rejected.connect(reject)

        if self.tif2mono_ui.defaultsrcBox.isChecked():
            # disable source button (default)

            # get default folder
            # Define json data
            jsonfile = os.path.join(RUNTIME_PATHS.project_root, "Model", "Project", "Data", "json", "Workflow.json")
            with open(jsonfile, 'r') as f:
                data = json.load(f)
                # Search the key value using 'in' operator
                for Sequence in data:
                    print(Sequence['Sequence'])
                    if Sequence['Sequence'] == seq:
                        # set source line edit to default workflow folder
                        self.tif2mono_ui.SourceLineEdit.setText(Sequence['DefaultSource']+r'/')
                        self.tif2mono_ui.DestinationLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                        source_folder = Sequence['DefaultSource']+r'/'
                        workflow_folder = Sequence['WorkflowFullPath']+r'/'
                        complete_folder = Sequence['CompleteFullPath']+r'/'+self.sourcebookmarkdown+r'/'
                        print(source_folder,workflow_folder,complete_folder)

        rsp = self.tif2monoDialog.exec_()



        print("completed creating indexed(BW) tiff")

    def actionmono_to_png(self):
        print("creating indexed(BW) png")

        def accept():
            # if self.mono2pngDialog.Accepted:
            # Empty default Workflow folder
            print('Workflow Folder:'+ workflow_folder,'Complete Folder:'+ complete_folder)
            for filename in os.listdir(workflow_folder):
                file_path = os.path.join(workflow_folder, filename)
                print('File Name:'+filename, 'File Path:'+file_path)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))

            for filename in os.listdir(source_folder):
                print(source_folder,filename)
                source_file_path = os.path.join(source_folder, filename)

            # Extract to default Workflow folder
            print(source_folder, workflow_folder)
            pp.tiff2pngidx(self.mono2png_ui.SourceLineEdit.text(), self.mono2png_ui.DestinationLineEdit.text())
            # Copy Workflow folder to default Complete folder
            if complete_folder:
                symlinks=False
                ignore=None
                for item in os.listdir(workflow_folder):
                    source = os.path.join(workflow_folder, item)
                    destination = os.path.join(complete_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)
        def reject():
            pass

        #usage: pp.tiff2pngidx(source, destination)

        self.mono2pngDialog = qtw.QDialog()
        self.mono2png_ui = Ui_mono2pngDialog()
        self.mono2png_ui.setupUi(self.mono2pngDialog)
        self.mono2pngDialog.show()

        seq = "SP5"

        def setdefault():
            if self.mono2png_ui.defaultsrcBox.isChecked():
                self.mono2png_ui.SourceButton.setEnabled(False)
                self.mono2png_ui.DestinationButton.setEnabled(False)
            else:
                self.mono2png_ui.SourceButton.setEnabled(True)
                self.mono2png_ui.DestinationButton.setEnabled(True)

        if self.mono2png_ui.defaultsrcBox.isChecked():
            # disable source button (default)

            # get default folder
            # Define json data
            jsonfile = os.path.join(RUNTIME_PATHS.project_root, "Model", "Project", "Data", "json", "Workflow.json")
            with open(jsonfile, 'r') as f:
                data = json.load(f)
                # Search the key value using 'in' operator
                for Sequence in data:
                    print(Sequence['Sequence'])
                    if Sequence['Sequence'] == seq:
                        # set source line edit to default workflow folder
                        self.mono2png_ui.SourceLineEdit.setText(Sequence['DefaultSource']+r'/')
                        self.mono2png_ui.DestinationLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                        source_folder = Sequence['DefaultSource']+r'/'
                        workflow_folder = Sequence['WorkflowFullPath']+r'/'
                        complete_folder = Sequence['CompleteFullPath']+r'/'+self.sourcebookmarkdown+r'/'
                        print(source_folder,workflow_folder,complete_folder)

        self.mono2png_ui.defaultsrcBox.stateChanged.connect(setdefault)
        self.mono2png_ui.SourceButton.clicked.connect(self.MonoToPngDialog)
        self.mono2png_ui.DestinationButton.clicked.connect(self.DestMonoToPngDialog)
        self.mono2png_ui.buttonBox.accepted.connect(accept)
        self.mono2png_ui.buttonBox.rejected.connect(reject)

        rsp = self.mono2pngDialog.exec_()
        print("completed creating indexed(BW) png")

    def actiondeskew_mono(self):
        print("deskewing monochrome tiff and png files")

        def accept():
            # if self.deskew_monoDialog.Accepted:
            # Empty default Workflow folders
            print('tif Workflow Folder:'+ tif_workflow_folder,'tif Complete Folder:'+ tif_complete_folder)
            print('png Workflow Folder:'+ png_workflow_folder,'png Complete Folder:'+ png_complete_folder)
            # Empty default tif Workflow folders
            for filename in os.listdir(tif_workflow_folder):
                file_path = os.path.join(tif_workflow_folder, filename)
                print('tif File Name:'+filename, 'tif File Path:'+file_path)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))
            # Empty default png Workflow folders
            for filename in os.listdir(png_workflow_folder):
                file_path = os.path.join(png_workflow_folder, filename)
                print('png File Name:'+filename, 'png File Path:'+file_path)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))

            for filename in os.listdir(source_folder):
                print(source_folder,filename)
                source_file_path = os.path.join(source_folder, filename)

            # Extract to default Workflow folders
            print(source_folder, png_workflow_folder, tif_workflow_folder)
            pp.deskewfiles(self.deskew_mono_ui.SourceLineEdit.text(), self.deskew_mono_ui.DestPngLineEdit.text(),self.deskew_mono_ui.DestTifLineEdit.text())
            # Copy Workflow folder to default Complete folders
            if tif_complete_folder:
                symlinks=False
                ignore=None
                for item in os.listdir(tif_workflow_folder):
                    source = os.path.join(tif_workflow_folder, item)
                    destination = os.path.join(tif_complete_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)
            if png_complete_folder:
                symlinks=False
                ignore=None
                for item in os.listdir(png_workflow_folder):
                    source = os.path.join(png_workflow_folder, item)
                    destination = os.path.join(png_complete_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)
        def reject():
            pass

        #usage: dsk.deskewfiles(source, pngdest, tifdest)

        self.deskew_monoDialog = qtw.QDialog()
        self.deskew_mono_ui = Ui_deskew_monoDialog()
        self.deskew_mono_ui.setupUi(self.deskew_monoDialog)
        self.deskew_monoDialog.show()

        seq = "SP6"

        def setdefault():
            if self.deskew_mono_ui.defaultsrcBox.isChecked():
                self.deskew_mono_ui.SourceButton.setEnabled(False)
                self.deskew_mono_ui.DestTifButton.setEnabled(False)
            else:
                self.deskew_mono_ui.SourceButton.setEnabled(True)
                self.deskew_mono_ui.DestTifButton.setEnabled(True)

        if self.deskew_mono_ui.defaultsrcBox.isChecked():
            # disable source button (default)

            # get default folder
            # Define json data
            jsonfile = os.path.join(RUNTIME_PATHS.project_root, "Model", "Project", "Data", "json", "Workflow.json")
            with open(jsonfile, 'r') as f:
                data = json.load(f)
                # Search the key value using 'in' operator
                for Sequence in data:
                    print(Sequence['Sequence'])
                    if Sequence['Sequence'] == seq:
                        # set source line edit to default workflow folder
                        self.deskew_mono_ui.SourceLineEdit.setText(Sequence['DefaultSource']+r'/')
                        self.deskew_mono_ui.DestTifLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                        source_folder = Sequence['DefaultSource']+r'/'
                        tif_workflow_folder = Sequence['WorkflowFullPath']+r'/'
                        tif_complete_folder = Sequence['CompleteFullPath']+r'/'+self.sourcebookmarkdown+r'/'
                        print(source_folder,tif_workflow_folder,tif_complete_folder)

        seq = "SP7"

        def setdefault():
            if self.deskew_mono_ui.defaultsrcBox.isChecked():
                self.deskew_mono_ui.SourceButton.setEnabled(False)
                self.deskew_mono_ui.DestPngButton.setEnabled(False)
            else:
                self.deskew_mono_ui.SourceButton.setEnabled(True)
                self.deskew_mono_ui.DestPngButton.setEnabled(True)

        self.deskew_mono_ui.SourceButton.clicked.connect(self.DeskewMonoDialog)
        self.deskew_mono_ui.DestPngButton.clicked.connect(self.DestDeskewPngDialog)
        self.deskew_mono_ui.DestTifButton.clicked.connect(self.DestDeskewTifDialog)
        self.deskew_mono_ui.buttonBox.accepted.connect(accept)
        self.deskew_mono_ui.buttonBox.rejected.connect(reject)

        if self.deskew_mono_ui.defaultsrcBox.isChecked():
            # disable source button (default)

            # get default folder
            # Define json data
            jsonfile = os.path.join(RUNTIME_PATHS.project_root, "Model", "Project", "Data", "json", "Workflow.json")
            with open(jsonfile, 'r') as f:
                # returns JSON object as
                # a dictionary
                data = json.load(f)
                # Search the key value using 'in' operator
                for Sequence in data:
                    print(Sequence['Sequence'])
                    if Sequence['Sequence'] == seq:
                        # set source line edit to default workflow folder
                        self.deskew_mono_ui.SourceLineEdit.setText(Sequence['DefaultSource']+r'/')
                        self.deskew_mono_ui.DestPngLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                        #source_folder = Sequence['DefaultSource']+r'/'
                        png_workflow_folder = Sequence['WorkflowFullPath']+r'/'
                        png_complete_folder = Sequence['CompleteFullPath']+r'/'+self.sourcebookmarkdown+r'/'
                        print(png_workflow_folder,png_complete_folder)

        rsp = self.deskew_monoDialog.exec_()
        print("completed deskewing monochrome tiff and png files")

    def actionCrop_Languages(self):
        print("creating cropped language tif files")

        def accept():
        #if self.crop_languagesDialog.Accepted:
            # Empty default tif Workflow folders
            if workflow_greek_folder:
                for filename in os.listdir(workflow_greek_folder):
                    file_path = os.path.join(workflow_greek_folder, filename)
                    print('tif File Name:'+filename, 'tif File Path:'+file_path)
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        print('Failed to delete %s. Reason: %s' % (file_path, e))
                    # Empty default tif Workflow folders
            if workflow_latin_folder:
                for filename in os.listdir(workflow_latin_folder):
                    file_path = os.path.join(workflow_latin_folder, filename)
                    print('tif File Name:'+filename, 'tif File Path:'+file_path)
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        print('Failed to delete %s. Reason: %s' % (file_path, e))
            pp.croplangs(self.crop_languages_ui.SourceLineEdit.text(), self.crop_languages_ui.BoxFolderLineEdit.text(),self.crop_languages_ui.DestGreekLineEdit.text(),self.crop_languages_ui.DestLatinLineEdit.text(),self.crop_languages_ui.ElimFolderLineEdit.text())
            print("completed creating cropped language tif files")
            # copy workflow images to complete images
            if workflow_box_folder:
                symlinks=False
                ignore=None
                for item in os.listdir(workflow_box_folder):
                    source = os.path.join(workflow_box_folder, item)
                    destination = os.path.join(complete_box_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)
            if workflow_elim_folder:
                symlinks=False
                ignore=None
                for item in os.listdir(workflow_elim_folder):
                    source = os.path.join(workflow_elim_folder, item)
                    destination = os.path.join(complete_elim_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)

            if workflow_greek_folder:
                symlinks=False
                ignore=None
                for item in os.listdir(workflow_greek_folder):
                    source = os.path.join(workflow_greek_folder, item)
                    destination = os.path.join(complete_greek_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)

            if workflow_latin_folder:
                symlinks=False
                ignore=None
                for item in os.listdir(workflow_latin_folder):
                    source = os.path.join(workflow_latin_folder, item)
                    destination = os.path.join(complete_latin_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)

        def reject():
            pass

        #usage: pp.croplangs(source, boxdir, greekdir, latindir, elimdir)
        self.crop_languagesDialog = qtw.QDialog()
        self.crop_languages_ui = Ui_crop_languagesDialog()
        self.crop_languages_ui.setupUi(self.crop_languagesDialog)
        self.crop_languagesDialog.show()


        self.crop_languages_ui.SourceButton.clicked.connect(self.CropLanguagesDialog)
        self.crop_languages_ui.BoxFolderButton.clicked.connect(self.BoxFolderDialog)
        self.crop_languages_ui.ElimFolderButton.clicked.connect(self.ElimFolderDialog)
        self.crop_languages_ui.DestGreekButton.clicked.connect(self.DestGreekDialog)
        self.crop_languages_ui.DestLatinButton.clicked.connect(self.DestLatinDialog)
        self.crop_languages_ui.buttonBox.accepted.connect(accept)
        self.crop_languages_ui.buttonBox.rejected.connect(reject)

        seq = ["SP10","SP11","GP1","GP2","LP1","LP2"]

        if self.crop_languages_ui.defaultsrcBox.isChecked():
            # disable source button (default)

            for step in seq:
                jsonfile = os.path.join(RUNTIME_PATHS.project_root, "Model", "Project", "Data", "json", "Workflow.json")
                with open(jsonfile, 'r') as f:
                    data = json.load(f)

                    # Search the key value using 'in' operator
                    for Sequence in data:
                        print(Sequence['Sequence'])
                        if Sequence['Sequence'] == step:
                            # set line edits to their default workflow folders
                            if step == "SP10":
                                self.crop_languages_ui.SourceLineEdit.setText(Sequence['DefaultSource']+r'/')
                                source_folder = Sequence['DefaultSource']+r'/'
                                self.crop_languages_ui.BoxFolderLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                                workflow_box_folder = Sequence['WorkflowFullPath']+r'/'
                                complete_box_folder = Sequence['CompleteFullPath']+r'/'+self.sourcebookmarkdown+r'/'
                            elif step == "SP11":
                                self.crop_languages_ui.ElimFolderLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                                workflow_elim_folder = Sequence['WorkflowFullPath']+r'/'
                                complete_elim_folder = Sequence['CompleteFullPath']+r'/'+self.sourcebookmarkdown+r'/'
                            elif step == "GP1":
                                self.crop_languages_ui.DestGreekLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                                workflow_greek_folder = Sequence['WorkflowFullPath']+r'/'
                                complete_greek_folder = Sequence['CompleteFullPath']+r'/'+self.greekbookmarkdown+r'/'
                            elif step == "GP2":
                                #self.crop_languages_ui.DestGreekLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                                workflow_dup_greek_folder = Sequence['WorkflowFullPath']+r'/'
                                #complete_greek_folder = Sequence['CompleteFullPath']+r'/'+self.greekbookmarkdown+r'/'
                            elif step == "LP1":
                                self.crop_languages_ui.DestLatinLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                                workflow_latin_folder = Sequence['WorkflowFullPath']+r'/'
                                complete_latin_folder = Sequence['CompleteFullPath']+r'/'+self.latinbookmarkdown+r'/'
                            elif step == "LP2":
                                #self.crop_languages_ui.DestLatinLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                                workflow_dup_latin_folder = Sequence['WorkflowFullPath']+r'/'
                                #complete_latin_folder = Sequence['CompleteFullPath']+r'/'+self.latinbookmarkdown+r'/'

                f.close()
        print(source_folder,workflow_box_folder,workflow_elim_folder,workflow_greek_folder,workflow_latin_folder)
        rsp = self.crop_languagesDialog.exec_()

    def actionConvert_Greek_tiff_To_png(self):
        print("creating indexed(BW) Greek png files")
        #usage: pp.tiff2pngidx(source, destination)
        def accept():
            # Empty default Workflow folder
            print('Workflow Folder:'+ workflow_folder,'Complete Folder:'+ complete_folder)
            for filename in os.listdir(workflow_folder):
                file_path = os.path.join(workflow_folder, filename)
                print('File Name:'+filename, 'File Path:'+file_path)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))

            for filename in os.listdir(source_folder):
                print(source_folder,filename)
                source_file_path = os.path.join(source_folder, filename)

            # Extract to default Workflow folder
            print(source_folder, workflow_folder)
            pp.tiff2pngidx(self.greekmono2png_ui.SourceLineEdit.text(), self.greekmono2png_ui.DestinationLineEdit.text())
            # Copy Workflow folder to default Complete folder
            if complete_folder:
                #pp.pdf2tif(source_folder, complete_folder, self.pdf2tif_ui.StartPageLineEdit.text())
                symlinks=False
                ignore=None
                for item in os.listdir(workflow_folder):
                    source = os.path.join(workflow_folder, item)
                    destination = os.path.join(complete_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)
        def reject():
            pass

        #usage: pp.tiff2pngidx(source, destination)

        self.greekmono2pngDialog = qtw.QDialog()
        self.greekmono2png_ui = Ui_greekmono2pngDialog()
        self.greekmono2png_ui.setupUi(self.greekmono2pngDialog)
        self.greekmono2pngDialog.show()

        seq = "GP5"

        def setdefault():
            if self.greekmono2png_ui.defaultsrcBox.isChecked():
                self.greekmono2png_ui.SourceButton.setEnabled(False)
                self.greekmono2png_ui.DestinationButton.setEnabled(False)
            else:
                self.greekmono2png_ui.SourceButton.setEnabled(True)
                self.greekmono2png_ui.DestinationButton.setEnabled(True)

        self.greekmono2png_ui.defaultsrcBox.stateChanged.connect(setdefault)
        self.greekmono2png_ui.SourceButton.clicked.connect(self.GreekMonoToPngDialog)
        self.greekmono2png_ui.DestinationButton.clicked.connect(self.GreekDestMonoToPngDialog)
        self.greekmono2png_ui.buttonBox.accepted.connect(accept)
        self.greekmono2png_ui.buttonBox.rejected.connect(reject)


        if self.greekmono2png_ui.defaultsrcBox.isChecked():
            # disable source button (default)

            # get default folder
            # Define json data

            jsonfile = os.path.join(RUNTIME_PATHS.project_root, "Model", "Project", "Data", "json", "Workflow.json")
            with open(jsonfile, 'r') as f:
                data = json.load(f)

                # Search the key value using 'in' operator
                for Sequence in data:
                    print(Sequence['Sequence'])
                    if Sequence['Sequence'] == seq:
                        # set source line edit to default workflow folder
                        self.greekmono2png_ui.SourceLineEdit.setText(Sequence['DefaultSource']+r'/')
                        self.greekmono2png_ui.DestinationLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                        source_folder = Sequence['DefaultSource']+r'/'
                        workflow_folder = Sequence['WorkflowFullPath']+r'/'
                        complete_folder = Sequence['CompleteFullPath']+r'/'+self.greekbookmarkdown+r'/'
                        print(source_folder,workflow_folder,complete_folder)

        rsp = self.greekmono2pngDialog.exec_()
        print("completed creating indexed(BW) png")

    def actionDeskewGreek_tiff(self):
        print("deskewing Greek tiff files")
        #usage: dsk.deskewfiles(source, pngdest, tifdest)

        def accept():
            # if self.deskew_greekmonoDialog.Accepted:
            # Empty default Workflow folders
            print('tif Workflow Folder:'+ tif_workflow_folder,'tif Complete Folder:'+ tif_complete_folder)
            print('png Workflow Folder:'+ png_workflow_folder,'png Complete Folder:'+ png_complete_folder)
            # Empty default tif Workflow folders
            for filename in os.listdir(tif_workflow_folder):
                file_path = os.path.join(tif_workflow_folder, filename)
                print('tif File Name:'+filename, 'tif File Path:'+file_path)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))
            # Empty default png Workflow folders
            for filename in os.listdir(png_workflow_folder):
                file_path = os.path.join(png_workflow_folder, filename)
                print('png File Name:'+filename, 'png File Path:'+file_path)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))

            for filename in os.listdir(source_folder):
                print(source_folder,filename)
                source_file_path = os.path.join(source_folder, filename)

            # Extract to default Workflow folders
            print(source_folder, png_workflow_folder, tif_workflow_folder)
            pp.deskewfiles(self.deskew_greekmono_ui.SourceLineEdit.text(), self.deskew_greekmono_ui.DestPngLineEdit.text(),self.deskew_greekmono_ui.DestTifLineEdit.text())
            # Copy Workflow folder to default Complete folders
            if tif_complete_folder:
                symlinks=False
                ignore=None
                for item in os.listdir(tif_workflow_folder):
                    source = os.path.join(tif_workflow_folder, item)
                    destination = os.path.join(tif_complete_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)
            if png_complete_folder:
                symlinks=False
                ignore=None
                for item in os.listdir(png_workflow_folder):
                    source = os.path.join(png_workflow_folder, item)
                    destination = os.path.join(png_complete_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)
        def reject():
            pass

        #usage: dsk.deskewfiles(source, pngdest, tifdest)

        self.deskew_greekmonoDialog = qtw.QDialog()
        self.deskew_greekmono_ui = Ui_deskew_greekmonoDialog()
        self.deskew_greekmono_ui.setupUi(self.deskew_greekmonoDialog)
        self.deskew_greekmonoDialog.show()

        seq = "GP6"

        def setdefault():
            if self.deskew_greekmono_ui.defaultsrcBox.isChecked():
                self.deskew_greekmono_ui.SourceButton.setEnabled(False)
                self.deskew_greekmono_ui.DestTifButton.setEnabled(False)
            else:
                self.deskew_greekmono_ui.SourceButton.setEnabled(True)
                self.deskew_greekmono_ui.DestTifButton.setEnabled(True)

        if self.deskew_greekmono_ui.defaultsrcBox.isChecked():
            # disable source button (default)

            # get default folder
            # Define json data
            jsonfile = os.path.join(RUNTIME_PATHS.project_root, "Model", "Project", "Data", "json", "Workflow.json")
            with open(jsonfile, 'r') as f:
                data = json.load(f)
                # Search the key value using 'in' operator
                for Sequence in data:
                    print(Sequence['Sequence'])
                    if Sequence['Sequence'] == seq:
                        # set source line edit to default workflow folder
                        self.deskew_greekmono_ui.SourceLineEdit.setText(Sequence['DefaultSource']+r'/')
                        self.deskew_greekmono_ui.DestTifLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                        source_folder = Sequence['DefaultSource']+r'/'
                        tif_workflow_folder = Sequence['WorkflowFullPath']+r'/'
                        tif_complete_folder = Sequence['CompleteFullPath']+r'/'+self.greekbookmarkdown+r'/'
                        print(source_folder,tif_workflow_folder,tif_complete_folder)

        seq = "GP7"

        def setdefault():
            if self.deskew_greekmono_ui.defaultsrcBox.isChecked():
                self.deskew_greekmono_ui.SourceButton.setEnabled(False)
                self.deskew_greekmono_ui.DestPngButton.setEnabled(False)
            else:
                self.deskew_greekmono_ui.SourceButton.setEnabled(True)
                self.deskew_greekmono_ui.DestPngButton.setEnabled(True)

        self.deskew_greekmono_ui.SourceButton.clicked.connect(self.DeskewGreekMonoDialog)
        self.deskew_greekmono_ui.DestPngButton.clicked.connect(self.DestDeskewGreekPngDialog)
        self.deskew_greekmono_ui.DestTifButton.clicked.connect(self.DestDeskewGreekTifDialog)
        self.deskew_greekmono_ui.buttonBox.accepted.connect(accept)
        self.deskew_greekmono_ui.buttonBox.rejected.connect(reject)

        if self.deskew_greekmono_ui.defaultsrcBox.isChecked():
            # disable source button (default)

            # get default folder
            # Define json data
            jsonfile = os.path.join(RUNTIME_PATHS.project_root, "Model", "Project", "Data", "json", "Workflow.json")
            with open(jsonfile, 'r') as f:
                data = json.load(f)
                # Search the key value using 'in' operator
                for Sequence in data:
                    print(Sequence['Sequence'])
                    if Sequence['Sequence'] == seq:
                        # set source line edit to default workflow folder
                        self.deskew_greekmono_ui.SourceLineEdit.setText(Sequence['DefaultSource']+r'/')
                        self.deskew_greekmono_ui.DestPngLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                        source_folder = Sequence['DefaultSource']+r'/'
                        png_workflow_folder = Sequence['WorkflowFullPath']+r'/'
                        png_complete_folder = Sequence['CompleteFullPath']+r'/'+self.greekbookmarkdown+r'/'
                        print(source_folder,png_workflow_folder,png_complete_folder)
            with open(jsonfile, 'r') as f:
                # returns JSON object as
                # a dictionary
                data = json.load(f)
                # Search the key value using 'in' operator
                for Sequence in data:
                    print(Sequence['Sequence'])
                    if Sequence['Sequence'] == seq:
                        # set source line edit to default workflow folder
                        #self.deskew_greekmono_ui.SourceLineEdit.setText(Sequence['DefaultSource']+r'/')
                        self.deskew_greekmono_ui.DestPngLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                        #source_folder = Sequence['DefaultSource']+r'/'
                        png_workflow_folder = Sequence['WorkflowFullPath']+r'/'
                        png_complete_folder = Sequence['CompleteFullPath']+r'/'+self.greekbookmarkdown+r'/'
                        print(source_folder,png_workflow_folder,png_complete_folder)

        rsp = self.deskew_greekmonoDialog.exec_()


        #dsk.deskewfiles("/home/jetson/Projects/Python/Images/Greek/png_greek/greek_book_40_Matthew/", "/home/jetson/Projects/Python/Images/Greek/png_greek_deskew/greek_book_40_Matthew/","/home/jetson/Projects/Python/Images/Greek/tif_greek_deskew/greek_book_40_Matthew/")
        #pp.deskewfiles("/home/jetson/Projects/Python/Images/Greek/png_greek/greek_book_41_Mark/", "/home/jetson/Projects/Python/Images/Greek/png_greek_deskew/greek_book_41_Mark/","/home/jetson/Projects/Python/Images/Greek/tif_greek_deskew/greek_book_41_Mark/")

    def actionResizeGreek_png(self):
        print("resizing Greek png files")
        #usage: pp.resizepngs(source, destination)
        def accept():
            # if self.mono2pngDialog.Accepted:
            # Empty default Workflow folder
            print('Workflow Folder:'+ workflow_folder,'Complete Folder:'+ complete_folder)
            for filename in os.listdir(workflow_folder):
                file_path = os.path.join(workflow_folder, filename)
                print('File Name:'+filename, 'File Path:'+file_path)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))

            for filename in os.listdir(source_folder):
                print(source_folder,filename)
                source_file_path = os.path.join(source_folder, filename)

            # Extract to default Workflow folder
            print(source_folder, workflow_folder)
            pp.resizepngs(self.greekresizepng_ui.SourceLineEdit.text(), self.greekresizepng_ui.DestinationLineEdit.text())

            # Copy Workflow folder to default Complete folder
            if complete_folder:
                #pp.pdf2tif(source_folder, complete_folder, self.pdf2tif_ui.StartPageLineEdit.text())
                symlinks=False
                ignore=None
                for item in os.listdir(workflow_folder):
                    source = os.path.join(workflow_folder, item)
                    destination = os.path.join(complete_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)
        def reject():
            pass

        #usage: pp.tiff2pngidx(source, destination)

        self.greekresizepngDialog = qtw.QDialog()
        self.greekresizepng_ui = Ui_greekresizepngDialog()
        self.greekresizepng_ui.setupUi(self.greekresizepngDialog)
        self.greekresizepngDialog.show()

        seq = "GP10"

        def setdefault():
            if self.greekresizepng_ui.defaultsrcBox.isChecked():
                self.greekresizepng_ui.SourceButton.setEnabled(False)
                self.greekresizepng_ui.DestinationButton.setEnabled(False)
            else:
                self.greekresizepng_ui.SourceButton.setEnabled(True)
                self.greekresizepng_ui.DestinationButton.setEnabled(True)

        self.greekresizepng_ui.defaultsrcBox.stateChanged.connect(setdefault)
        self.greekresizepng_ui.SourceButton.clicked.connect(self.GreekResizePngDialog)
        self.greekresizepng_ui.DestinationButton.clicked.connect(self.DestGreekResizePngDialog)
        self.greekresizepng_ui.buttonBox.accepted.connect(accept)
        self.greekresizepng_ui.buttonBox.rejected.connect(reject)


        if self.greekresizepng_ui.defaultsrcBox.isChecked():
            # disable source button (default)

            # get default folder
            # Define json data
            jsonfile = os.path.join(RUNTIME_PATHS.project_root, "Model", "Project", "Data", "json", "Workflow.json")
            with open(jsonfile, 'r') as f:
                data = json.load(f)
                # Search the key value using 'in' operator
                for Sequence in data:
                    print(Sequence['Sequence'])
                    if Sequence['Sequence'] == seq:
                        # set source line edit to default workflow folder
                        self.greekresizepng_ui.SourceLineEdit.setText(Sequence['DefaultSource']+r'/')
                        self.greekresizepng_ui.DestinationLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                        source_folder = Sequence['DefaultSource']+r'/'
                        workflow_folder = Sequence['WorkflowFullPath']+r'/'
                        complete_folder = Sequence['CompleteFullPath']+r'/'+self.greekbookmarkdown+r'/'
                        print(source_folder,workflow_folder,complete_folder)
            with open(jsonfile, 'r') as f:
                # returns JSON object as
                # a dictionary
                data = json.load(f)
                # Search the key value using 'in' operator
                for Sequence in data:
                    print(Sequence['Sequence'])
                    if Sequence['Sequence'] == seq:
                        # set source line edit to default workflow folder
                        self.greekresizepng_ui.SourceLineEdit.setText(Sequence['DefaultSource']+r'/')
                        self.greekresizepng_ui.DestinationLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                        source_folder = Sequence['DefaultSource']+r'/'
                        workflow_folder = Sequence['WorkflowFullPath']+r'/'
                        complete_folder = Sequence['CompleteFullPath']+r'/'+self.greekbookmarkdown+r'/'
                        print(source_folder,workflow_folder,complete_folder)

        rsp = self.greekresizepngDialog.exec_()
        print("completed resizing indexed(BW) png")

    def actionConvert_Latin_tiff_To_png(self):
        print("creating indexed(BW) Latin png files")
        #usage: pp.tiff2pngidx(source, destination)
        self.latinmono2pngDialog = qtw.QDialog()
        self.latinmono2png_ui = Ui_latinmono2pngDialog()
        self.latinmono2png_ui.setupUi(self.latinmono2pngDialog)
        self.latinmono2pngDialog.show()

        self.latinmono2png_ui.SourceButton.clicked.connect(self.LatinMonoToPngDialog)
        self.latinmono2png_ui.DestinationButton.clicked.connect(self.LatinDestMonoToPngDialog)

        rsp = self.latinmono2pngDialog.exec_()

        if self.latinmono2pngDialog.Accepted:
            pp.tiff2pngidx(self.latinmono2png_ui.SourceLineEdit.text(), self.latinmono2png_ui.DestinationLineEdit.text())
            print("completed creating indexed(BW) png")
        #pp.tiff2pngidx(r"/home/jetson/Projects/Python/Images/Source/tif_black_white/source_book_40_Matthew/", "/home/jetson/Projects/Python/Images/Source/tif_black_white_2png/source_book_40_Matthew/")
        #pp.tiff2pngidx(r"/home/jetson/Projects/Python/Images/Latin/tif_latin/latin_book_41_Mark/", "/home/jetson/Projects/Python/Images/Latin/png_latin/latin_book_41_Mark/")

    def actionDeskewLatin_tiff(self):
        print("deskewing Latin tiff files")
        #usage: dsk.deskewfiles(source, pngdest, tifdest)
        self.deskew_latinmonoDialog = qtw.QDialog()
        self.deskew_latinmono_ui = Ui_deskew_latinmonoDialog()
        self.deskew_latinmono_ui.setupUi(self.deskew_latinmonoDialog)
        self.deskew_latinmonoDialog.show()

        self.deskew_latinmono_ui.SourceButton.clicked.connect(self.DeskewLatinMonoDialog)
        self.deskew_latinmono_ui.DestPngButton.clicked.connect(self.DestDeskewLatinPngDialog)
        self.deskew_latinmono_ui.DestTifButton.clicked.connect(self.DestDeskewLatinTifDialog)

        rsp = self.deskew_latinmonoDialog.exec_()

        if self.deskew_latinmonoDialog.Accepted:
            pp.deskewfiles(self.deskew_latinmono_ui.SourceLineEdit.text(), self.deskew_latinmono_ui.DestPngLineEdit.text(),self.deskew_latinmono_ui.DestTifLineEdit.text())
            print("completed deskewing monochrome tiff and png files")
    def actionResizeLatin_png(self):
        print("resizing Latin png files")
        #usage: pp.resizepngs(source, destination)
        self.latinresizepngDialog = qtw.QDialog()
        self.latinresizepng_ui = Ui_latinresizepngDialog()
        self.latinresizepng_ui.setupUi(self.latinresizepngDialog)
        self.latinresizepngDialog.show()

        self.latinresizepng_ui.SourceButton.clicked.connect(self.LatinResizePngDialog)
        self.latinresizepng_ui.DestinationButton.clicked.connect(self.DestLatinResizePngDialog)

        rsp = self.latinresizepngDialog.exec_()

        if self.latinresizepngDialog.Accepted:
            pp.resizepngs(self.latinresizepng_ui.SourceLineEdit.text(), self.latinresizepng_ui.DestinationLineEdit.text())
            print("completed creating indexed(BW) png")

    def crop_processor(self, qimage, params):
        if not params:
            return qimage

        x = params.get("x", 0)
        y = params.get("y", 0)
        w = params.get("w", qimage.width())
        h = params.get("h", qimage.height())

        return qimage.copy(x, y, w, h)

    def actionCrop_Greek_To_tiff_Lines(self):
        print("cropping and sorting Greek tiff lines")
        #usage: tr.sortcroplines(source, splitdir, linebox)
        self.crop_greeklinesDialog = qtw.QDialog()
        self.crop_greeklines_ui = Ui_crop_greek_linesDialog()
        self.crop_greeklines_ui.setupUi(self.crop_greeklinesDialog)
        self.crop_greeklinesDialog.show()

        def setdefault():
            if self.crop_greeklines_ui.defaultsrcBox.isChecked():
                self.crop_greeklines_ui.SourceButton.setEnabled(False)
                self.crop_greeklines_ui.DestGreekButton.setEnabled(False)
                self.crop_greeklines_ui.GreekBoxFolderButton.setEnabled(False)
            else:
                self.crop_greeklines_ui.SourceButton.setEnabled(True)
                self.crop_greeklines_ui.DestGreekButton.setEnabled(True)
                self.crop_greeklines_ui.GreekBoxFolderButton.setEnabled(True)

        def accept():
            # Empty default Workflow folder
            print('Workflow Folder:'+ workflow_dest_folder,'Complete Folder:'+ complete_dest_folder)
            for filename in os.listdir(workflow_dest_folder):
                file_path = os.path.join(workflow_dest_folder, filename)
                print('File Name:'+filename, 'File Path:'+file_path)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))

            for filename in os.listdir(source_folder):
                #print(source_folder,filename)
                #source_file_path = os.path.join(source_folder, filename)

                # Extract to default Workflow folder
                print(source_folder, workflow_dest_folder, workflow_box_folder)
                tr.sortcroplines(self.crop_greeklines_ui.SourceLineEdit.text(),self.crop_greeklines_ui.GreekBoxFolderLineEdit.text(),self.crop_greeklines_ui.DestGreekLineEdit.text())

            # Copy Workflow folder to default Complete folder
            if complete_dest_folder:
                symlinks=False
                ignore=None
                for item in os.listdir(workflow_dest_folder):
                    source = os.path.join(workflow_dest_folder, item)
                    destination = os.path.join(complete_dest_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)

            # Copy Workflow line box folder to default Complete line box folder
            if complete_box_folder:
                symlinks=False
                ignore=None
                for item in os.listdir(workflow_box_folder):
                    source = os.path.join(workflow_box_folder, item)
                    destination = os.path.join(complete_box_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)

        def reject():
            pass

        self.crop_greeklines_ui.defaultsrcBox.stateChanged.connect(setdefault)
        self.crop_greeklines_ui.SourceButton.clicked.connect(self.CropGreekLinesDialog)
        self.crop_greeklines_ui.GreekBoxFolderButton.clicked.connect(self.GreekLineBoxFolderDialog)
        self.crop_greeklines_ui.DestGreekButton.clicked.connect(self.DestGreekLinesDialog)
        self.crop_greeklines_ui.buttonBox.accepted.connect(accept)
        self.crop_greeklines_ui.buttonBox.rejected.connect(reject)

        seq = ["GL1","GL2"]

        if self.crop_greeklines_ui.defaultsrcBox.isChecked():
        # disable source button (default)

            for step in seq:

                # Define json data

                jsonfile = os.path.join(RUNTIME_PATHS.project_root, "Model", "Project", "Data", "json", "Workflow.json")
                with open(jsonfile, 'r') as f:
                    # returns JSON object as
                    # a dictionary
                    data = json.load(f)

                    # Search the key value using 'in' operator
                    for Sequence in data:
                        # print(Sequence['Sequence'])
                        if Sequence['Sequence'] == step:
                            # set line edits to their default workflow folders
                            if step == "GL1":
                                self.crop_greeklines_ui.SourceLineEdit.setText(Sequence['DefaultSource']+r'/')
                                source_folder = Sequence['DefaultSource']+r'/'
                                self.crop_greeklines_ui.DestGreekLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                                workflow_dest_folder = Sequence['WorkflowFullPath']+r'/'
                                complete_dest_folder = Sequence['CompleteFullPath']+r'/'+self.sourcebookmarkdown+r'/'
                            elif step == "GL2":
                                self.crop_greeklines_ui.GreekBoxFolderLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                                workflow_box_folder = Sequence['WorkflowFullPath']+r'/'
                                complete_box_folder = Sequence['CompleteFullPath']+r'/'+self.sourcebookmarkdown+r'/'
                with open(jsonfile, 'r') as f:
                    # returns JSON object as
                    # a dictionary
                    data = json.load(f)

                    # Search the key value using 'in' operator
                    for Sequence in data:
                        # print(Sequence['Sequence'])
                        if Sequence['Sequence'] == step:
                            # set line edits to their default workflow folders
                            if step == "GL1":
                                self.crop_greeklines_ui.SourceLineEdit.setText(Sequence['DefaultSource']+r'/')
                                source_folder = Sequence['DefaultSource']+r'/'
                                self.crop_greeklines_ui.DestGreekLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                                workflow_dest_folder = Sequence['WorkflowFullPath']+r'/'
                                complete_dest_folder = Sequence['CompleteFullPath']+r'/'+self.sourcebookmarkdown+r'/'
                            elif step == "GL2":
                                self.crop_greeklines_ui.GreekBoxFolderLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                                workflow_box_folder = Sequence['WorkflowFullPath']+r'/'
                                complete_box_folder = Sequence['CompleteFullPath']+r'/'+self.sourcebookmarkdown+r'/'

                f.close()

        rsp = self.crop_greeklinesDialog.exec_()
        print("completed creating cropped language tif files")
    def actionRename_Greek_tiff_Lines(self):
        print("renaming Greek tif lines for ground truth")
        # usage: tr.renameimages(source, destination)
        self.greekrenamelinesDialog = qtw.QDialog()
        self.greekrenamelines_ui = Ui_tifgreekrenamelinesDialog()
        self.greekrenamelines_ui.setupUi(self.greekrenamelinesDialog)
        self.greekrenamelinesDialog.show()
        self.greekrenamelines_ui.SourceButton.clicked.connect(self.GreekRenameLinesDialog)
        self.greekrenamelines_ui.DestinationButton.clicked.connect(self.DestGreekRenameLinesDialog)

        rsp = self.greekrenamelinesDialog.exec_()

        if self.greekrenamelinesDialog.Accepted:
            tr.renameimages(self.greekrenamelines_ui.SourceLineEdit.text(), self.greekrenamelines_ui.DestinationLineEdit.text())

            print("completed renaming Greek tif lines for ground truth")
    def actionMove_Greek_tiff_Lines(self):
        print("moving Greek tif lines for ground truth")
        # usage: tr.renameimages(source, destination)
        self.greekmovelinesDialog = qtw.QDialog()
        self.greekmovelines_ui = Ui_tifgreekmovelinesDialog()
        self.greekmovelines_ui.setupUi(self.greekmovelinesDialog)
        self.greekmovelinesDialog.show()

        self.greekmovelines_ui.SourceButton.clicked.connect(self.GreekMovelinesDialog)
        self.greekmovelines_ui.DestinationButton.clicked.connect(self.DestGreekMovelinesDialog)

        rsp = self.greekmovelinesDialog.exec_()

        if self.greekmovelinesDialog.Accepted:
            tr.renameimages(self.greekmovelines_ui.SourceLineEdit.text(), self.greekmovelines_ui.DestinationLineEdit.text())
            print("completed moving Greek tif lines for ground truth")

    def actionCrop_Latin_To_tiff_Lines(self):
        print("cropping and sorting Latin tiff lines")
        #usage: tr.sortcroplines(source, splitdir, linebox)
        self.crop_latinlinesDialog = qtw.QDialog()
        self.crop_latinlines_ui = Ui_crop_latin_linesDialog()
        self.crop_latinlines_ui.setupUi(self.crop_latinlinesDialog)
        self.crop_latinlinesDialog.show()

        self.crop_latinlines_ui.SourceButton.clicked.connect(self.CroplatinLinesDialog)
        self.crop_latinlines_ui.BoxFolderButton.clicked.connect(self.LatinLineBoxFolderDialog)
        self.crop_latinlines_ui.DestlatinButton.clicked.connect(self.DestlatinLinesDialog)

        rsp = self.crop_latinlinesDialog.exec_()

        if self.crop_latinlinesDialog.Accepted:
            tr.sortcroplines(self.crop_latinlines_ui.SourceLineEdit.text(),self.crop_latinlines_ui.BoxFolderLineEdit.text(),self.crop_latinlines_ui.DestlatinLineEdit.text())
            print("completed creating cropped Latin tif lines")
        tr.sortcroplines(r"/home/jetson/Projects/Python/Images/Latin/png_latin_deskew/latin_book_41_Mark/","/home/jetson/Projects/Python/Images/Latin/tif_latin_autosplit/latin_book_41_Mark/","/home/jetson/Projects/Python/Images/Latin/tif_latin_linebox/latin_book_41_Mark/")

    def actionRename_Latin_tiff_Lines(self):
        print("renaming Latin tiff lines for ground truth")
        # usage: tr.renameimages(source, destination)
        self.latinrenamelinesDialog = qtw.QDialog()
        self.latinrenamelines_ui = Ui_tiflatinrenamelinesDialog()
        self.latinrenamelines_ui.setupUi(self.latinrenamelinesDialog)
        self.latinrenamelinesDialog.show()
        self.latinrenamelines_ui.SourceButton.clicked.connect(self.LatinRenameLinesDialog)
        self.latinrenamelines_ui.DestinationButton.clicked.connect(self.DestLatinRenameLinesDialog)

        rsp = self.latinrenamelinesDialog.exec_()

        if self.latinrenamelinesDialog.Accepted:
            tr.renameimages(self.latinrenamelines_ui.SourceLineEdit.text(), self.latinrenamelines_ui.DestinationLineEdit.text())

            print("completed renaming Greek tif lines for ground truth")

    def actionMove_Latin_tiff_Lines(self):
        print("moving Latin tif lines for ground truth")
        # usage: tr.renameimages(source, destination)
        self.latinmovelinesDialog = qtw.QDialog()
        self.latinmovelines_ui = Ui_tiflatinmovelinesDialog()
        self.latinmovelines_ui.setupUi(self.latinmovelinesDialog)
        self.latinmovelinesDialog.show()
        self.latinmovelines_ui.SourceButton.clicked.connect(self.LatinMovelinesDialog)
        self.latinmovelines_ui.DestinationButton.clicked.connect(self.DestLatinMovelinesDialog)

        rsp = self.latinmovelinesDialog.exec_()

        if self.latinmovelinesDialog.Accepted:
            tr.renameimages(self.latinmovelines_ui.SourceLineEdit.text(), self.latinmovelines_ui.DestinationLineEdit.text())
            print("completed moving Latin tif lines for ground truth")

    def actionSplitGreek_text_lines(self):
        print("splitting Greek textlines for ground truth")
        # usage: tr.splittextlines(source, destination)
        tr.splittextlines("/home/jetson/Projects/Python/EstablishTruth/Greek txt4linesplit/", "/home/jetson/Projects/Python/EstablishTruth/Greek lines4groundtruth/")

    def actionRenameGreek_text_lines(self):
        print("renaming Greek textlines for ground truth")
        # usage: tr.text2groundtruth(source, destination)
        tr.text2groundtruth(r"/home/jetson/Projects/Python/EstablishTruth/Greek lines4groundtruth/", "/home/jetson/Projects/Python/EstablishTruth/Greek lines2groundtruth/")

    def actionSplit_Latin_Text_Lines(self):
        print("splitting Latin textlines for ground truth")
        # usage: tr.splittextlines(source, destination)
        tr.splittextlines("/home/jetson/Projects/Python/EstablishTruth/Latin txt4linesplit/", "/home/jetson/Projects/Python/EstablishTruth/Latin lines4groundtruth/")

    def actionRename_Latin_Text_Lines(self):
        print("renaming Latin textlines for ground truth")
        # usage: tr.text2groundtruth(source, destination)
        tr.text2groundtruth(r"/home/jetson/Projects/Python/EstablishTruth/Latin lines4groundtruth/", "/home/jetson/Projects/Python/EstablishTruth/Latin lines2groundtruth/")

    def actionReview_Ground_Truth(self):
        gtr.MainWindow = qtw.QMainWindow()
        gtr.ui = gtr.Ui_MainWindow()
        gtr.ui.setupUi(gtr.MainWindow)
        gtr.MainWindow.show()

    def actionVerse_Correction(self):
        versify.MainWindow = qtw.QMainWindow()
        versify.ui = versify.Ui_MainWindow()
        versify.ui.setupUi(versify.MainWindow)
        versify.MainWindow.show()

    def actionUpdate_Wordlist(self):
        pass

    def actionTrain_Tesseract(self):
        pass

    def actionCorrect_OCR(self):
        print("performing OCR on current image")
        self.GetRawOCRtext()


    def start_image_load(self, path, target="ref"):
        print(f"[THREAD] Start load Ã¢â€ â€™ {path} ({target})")

        # store target so handler knows where to route image
        self._load_target = target

        self._thread = qtc.QThread()
        self._worker = ImageLoadWorker(self.image_load_path)

        self._worker.moveToThread(self._thread)

        # --- signals
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self.on_load_progress)
        self._worker.finished.connect(self.on_image_loaded)
        self._worker.error.connect(self.on_load_error)

        # --- cleanup
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        # --- start
        self._thread.start()

        # show progress immediately
        self._show_progress(0)


    def on_image_loaded(self, qimage):
        print("[LOAD] Complete")

        self._hide_progress(100)

        # -------------------------
        # STORE BOTH VERSIONS
        # -------------------------
        self.imgqimage = qimage
        self.imagepixmap = qtg.QPixmap.fromImage(qimage)   # Ã°Å¸â€Â¥ for zoom/display
        self.origpixmap  = qtg.QPixmap.fromImage(qimage)   # Ã°Å¸â€Â§ for preprocess tool

        if getattr(self, "_stack_path", ""):
            self.imgpath = self._stack_path
            print(f"[DEBUG] imgpath synced to loaded stack: {self.imgpath}")

        print("[DEBUG] imagepixmap isNull?", self.imagepixmap.isNull())

        # -------------------------
        # DISPLAY (no scaling here)
        # -------------------------
        self.ui.Image.setPixmap(self.imagepixmap)

    def on_load_progress(self, value):
         print(f"[LOAD] {value}%")
         self._set_progress_percent(value)

    def on_load_error(self, msg):
        print(f"[LOAD ERROR] {msg}")

        self._hide_progress()

        # Ã°Å¸â€Â´ invalidate image state
        self.imagepixmap = qtg.QPixmap()
        self.origpixmap  = qtg.QPixmap()

    def loadImage(self):
        def selected(fileName):
            filestr = os.path.basename(fileName)
            self.ui.ImageLE.setText(filestr)
            self.loadImageStackFromFile(fileName)

        self.open_non_modal_image_picker(
            "Open Image",
            self.imgdir if hasattr(self, 'imgdir') and self.imgdir else self._projects_base_path(),
            selected,
            '_image_open_dialog',
        )

    def loadImageStackFromFile(self, fileName=''):
        fileName = str(fileName)

        if not fileName or not os.path.isfile(fileName):
            print("[STACK LOAD] Invalid file")
            return

        print(f"[STACK LOAD] Requested: {fileName}")

        self._tiffCaptureHandle = tiffcapture.opentiff(fileName)
        if self._tiffCaptureHandle is None:
            print(f"[STACK LOAD] Failed to open TIFF stack: {fileName}")
            return

        self._stack_path = fileName
        self._load_target = "main"  # or "ref" if needed

        # -------------------------
        # Thread setup
        # -------------------------
        self._thread = qtc.QThread()
        self._worker = TiffStackWorker(fileName)

        self._worker.moveToThread(self._thread)

        # --- execution
        self._thread.started.connect(self._worker.run)

        # --- signals (ONLY ONCE)
        self._worker.progress.connect(self.on_load_progress)
        self._worker.finished.connect(self.on_image_loaded)
        self._worker.error.connect(self.on_load_error)

        # --- cleanup (CRITICAL)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        # -------------------------
        # Start thread
        # -------------------------
        self._thread.start()

        # -------------------------
        # Progress bar
        # -------------------------
        if hasattr(self, "progress_bar"):
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(True)

    def numFrames(self):
        """ Return the number of image frames in the stack.
        """
        if self._tiffCaptureHandle is not None:
            # !!! tiffcapture has length=0 for a single page TIFF.
            # If our handle is valid, we'll assume we have at least one image.
            return max([1, self._tiffCaptureHandle.length])
        return 0

    def getFrame(self, i=None):
        """ Return the i^th image frame as a NumPy ndarray.
        If i is None, return the current image frame.
        """
        if self._tiffCaptureHandle is None:
            return None
        if i is None:
            i = self.currentFrameIndex
        if (i is None) or (i < 0) or (i >= self.numFrames()):
            return None
        return self._tiffCaptureHandle.find_and_read(i)

    def showFrame(self, i=None):
        """ Display the i^th frame in the viewer.
        Also update the frame slider position and current frame text.
        """
        self.frame = self.getFrame(i)
        if self.frame is None:
            return
        # Convert frame ndarray to a QImage.
        self.qimage = qimage2ndarray.array2qimage(self.frame, normalize=True)

    #def open_preprocess_tool(self, checked=False):
    def open_preprocess_tool(self, checked=False):
        initial_pixmap = getattr(self, "origpixmap", None)
        if initial_pixmap is None or initial_pixmap.isNull():
            initial_pixmap = getattr(self, "imagepixmap", None)

        self.preprocess_window = OCRPreprocessTool(self, initial_pixmap=initial_pixmap)
        self.preprocess_window.exec_()


    from PyQt5.QtGui import QPixmap, QImage
    from PyQt5.QtCore import QFileInfo
    import tifffile
    import numpy as np

    def showImage(self,imgfilename):
        self.imgpath = imgfilename
        print(f"[MyServer DEBUG] self.imgpath set to: {self.imgpath}")
        self.imgfilename = self.imgpath
        self.imgdir = os.path.dirname(imgfilename)
        file = qtc.QFile(imgfilename)
        filestr = os.path.basename(imgfilename)
        filesplit = os.path.splitext(filestr)
        filename = filesplit[0]
        fileext = filesplit[1]

        if hasattr(self.ui, "ImageLE"):
            self.ui.ImageLE.setText(filestr)

        if file.open(qtc.QIODevice.ReadOnly):
            info = qtc.QFileInfo(imgfilename)

            if fileext.lower() in ('.tif', '.tiff'):
                self.loadImageStackFromFile(imgfilename)
                self.imgdir = os.path.dirname(imgfilename)
                print("[DEBUG] imagepixmap will be populated by on_image_loaded")

            else:
                self.imagepixmap = qtg.QPixmap(self.imgpath)
                self.origpixmap  = self.imagepixmap
                self.ui.Image.setPixmap(self.imagepixmap)

        file.close()

        self.on_zoom_combobox()
        self.session_manager.update('Session.json', {
            'self.imgpath': self.imgpath if self.imgpath is not None else '',
            'self.imgdir': self.imgdir if self.imgdir is not None else '',
        })
        self._record_project_milestone(
            "source_acquired",
            self.imgpath,
            details={"source": "showImage"},
        )
        self._refresh_project_status(self.imgpath)

        self.imgfileList = []
        for i in sorted(os.listdir(self.imgdir)):
            ipath = os.path.join(self.imgdir, i)
            if os.path.isfile(ipath) and i.endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff')):
                self.imgfileList.append(ipath)
        self.sortImgFiles()



#     def showImage(self, img):

#         # -------------------------------------------------
#         # DEBUG (only safe for file-based paths)
#         # -------------------------------------------------

# # ---- SAFE METADATA HANDLING ----
#         if isinstance(img, str):
#             self.imgpath = img
#             self.imgdir = QFileInfo(img).absolutePath()
#         else:
#             # QImage case (scanner)
#             self.imgpath = None
#             self.imgdir = None

#         print(f"[showImage DEBUG] self.imgpath set to: {self.imgpath}")

#         if isinstance(img, str):
#             print(f"[showImage DEBUG] self.imgdir set to: {self.imgdir}")
#         else:
#             print(f"[showImage DEBUG] self.imgdir set to: <scanner image - no filesystem>")

#         pixmap = None

#         # -------------------------------------------------
#         # CASE 1: QImage (WIA scanner path)
#         # -------------------------------------------------
#         if isinstance(img, QImage):
#             pixmap = QPixmap.fromImage(img)

#         # -------------------------------------------------
#         # CASE 2: file path (PNG/JPG/TIFF/etc.)
#         # -------------------------------------------------
#         elif isinstance(img, str):

#             suffix = QFileInfo(img).suffix().lower()

#             # ---- TIFF stack handling (your existing feature) ----
#             if suffix in ["tif", "tiff"]:
#                 try:
#                     pages = tifffile.imread(img)

#                     # If multi-page TIFF, take first page for preview
#                     if pages.ndim == 3:
#                         frame = pages[0]
#                     else:
#                         frame = pages

#                     if frame.dtype != np.uint8:
#                         frame = (255 * (frame / frame.max())).astype(np.uint8)

#                     h, w = frame.shape[:2]

#                     if len(frame.shape) == 2:
#                         qimg = QImage(frame.data, w, h, w, QImage.Format_Grayscale8)
#                     else:
#                         qimg = QImage(frame.data, w, h, w * 3, QImage.Format_RGB888)

#                     pixmap = QPixmap.fromImage(qimg)

#                 except Exception as e:
#                     print("[TIFF ERROR]", e)
#                     pixmap = QPixmap(img)

#             # ---- normal image files ----
#             else:
#                 pixmap = QPixmap(img)

#         # -------------------------------------------------
#         # CASE 3: fallback / error
#         # -------------------------------------------------
#         else:
#             print("[showImage ERROR] Unsupported type:", type(img))
#             return

#         # -------------------------------------------------
#         # DISPLAY
#         # -------------------------------------------------
#         if hasattr(self.ui, "Image"):
#             self.ui.Image.setPixmap(pixmap)
#             self.ui.Image.setScaledContents(True)
#         else:
#             print("[showImage ERROR] Image not found")

    # def showImage(self, img):

    #     # -----------------------------
    #     # CASE 1: already a QImage (NEW WIA pipeline)
    #     # -----------------------------
    #     if isinstance(img, QImage):
    #         pixmap = QPixmap.fromImage(img)

    #     # -----------------------------
    #     # CASE 2: file path (OLD pipeline still supported)
    #     # -----------------------------

    #     elif isinstance(img, str):
    #         pixmap = QPixmap(img)

    #     # -----------------------------
    #     # CASE 3: invalid input
    #     # -----------------------------
    #     else:
    #         print("[showImage ERROR] Unsupported type:", type(img))
    #         return

    #     # -----------------------------
    #     # DISPLAY (adjust label name if needed)
    #     # -----------------------------
    #     if hasattr(self.ui, "imageLabel"):
    #         self.ui.imageLabel.setPixmap(pixmap)
    #         self.ui.imageLabel.setScaledContents(True)
    #     else:
    #         print("[showImage ERROR] imageLabel not found in UI")

    # def showImage(self,imgfilename):
    #     self.imgpath = imgfilename
    #     print(f"[MyServer DEBUG] self.imgpath set to: {self.imgpath}")
    #     self.imgfilename = self.imgpath
    #     file = qtc.QFile(imgfilename)
    #     filestr = os.path.basename(imgfilename)
    #     filesplit = os.path.splitext(filestr)
    #     filename = filesplit[0]
    #     fileext = filesplit[1]

    #     if file.open(qtc.QIODevice.ReadOnly):
    #         info = qtc.QFileInfo(imgfilename)

    #         if fileext == '.tif':
    #             self.loadImageStackFromFile(imgfilename)
    #             self.imgdir = os.path.dirname(imgfilename)
    #             print("[DEBUG] imagepixmap will be populated by on_image_loaded")

    #         else:
    #             self.imagepixmap = qtg.QPixmap(self.imgpath)
    #             self.origpixmap  = self.imagepixmap
    #             self.ui.Image.setPixmap(self.imagepixmap)

    #     file.close()

        self.on_zoom_combobox()


        # jsonfile = 'Model/Project/Data/json/Session.json'
        jsonfile = os.path.join(RUNTIME_PATHS.project_root, "Model", "Project", "Data", "json", "Session.json")
        with open(jsonfile, 'r') as f:
            # data = json.load(f)
            # imgpath_key = r"self.imgpath"
            # imgdir_key = r"self.imgdir"
            data = {
            "path": self.imgpath if isinstance(self.imgpath, str) else str(self.imgpath),
            "dir": self.imgdir if isinstance(self.imgdir, str) else str(self.imgdir)
}


            for Setting in data:
                # -------------------------------------------------
                # SAFE SESSION CHECK (NO CRASH VERSION)
                # -------------------------------------------------
                Setting = locals().get("Setting", None)

                if isinstance(Setting, dict):
                    setting_value = Setting.get("Setting")
                else:
                    setting_value = None

                imgpath_key = getattr(self, "imgpath", None)
                imgdir_key = getattr(self, "imgdir", None)

                # SAFE COMPARE ONLY IF VALID
                if setting_value == imgpath_key:
                    pass
                                #if Setting['Setting'] == imgpath_key:

                f.close()

        os.remove(jsonfile)
        with open(jsonfile, 'w') as f:
            json.dump(data, f, indent=4)
        f.close()

        self.imgfileList = []

        for i in sorted(os.listdir(self.imgdir)):
            ipath = os.path.join(self.imgdir, i)
            if os.path.isfile(ipath) and i.endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff')):
                self.imgfileList.append(ipath)
        self.sortImgFiles()

    def sortImgFiles(self):
        import re

        def convert(text):
            return int(text) if text.isdigit() else text.lower()

        def alphanum_key(key):
            return [convert(c) for c in re.split('([0-9]+)', key)]

        self.sorted_imgfilelist = sorted(self.imgfileList, key=alphanum_key)

        # Set current index safely
        if self.imgpath in self.sorted_imgfilelist:
            self.current_img_index = self.sorted_imgfilelist.index(self.imgpath)
        else:
            self.current_img_index = 0

    def nextImage(self):
        if not self.sorted_imgfilelist:
            return

        self.current_img_index = (self.current_img_index + 1) % len(self.sorted_imgfilelist)
        nextimg = self.sorted_imgfilelist[self.current_img_index]

        self.imgpath = nextimg
        self.showImage(nextimg)

    def prevImage(self):
        if not self.sorted_imgfilelist:
            return

        self.current_img_index = (self.current_img_index - 1) % len(self.sorted_imgfilelist)
        previmg = self.sorted_imgfilelist[self.current_img_index]

        self.imgpath = previmg
        self.showImage(previmg)

    def ReloadImage(self):
        if self.imgpath:
            self.ui.ImageLE.setText(os.path.basename(self.imgpath))
            self.showImage(self.imgpath)
            self.sortImgFiles()

    def _projects_base_path(self):
        base_path = getattr(getattr(self, 'project_engine', None), 'base_path', '')
        if isinstance(base_path, str) and base_path and os.path.isdir(base_path):
            return base_path
        fallback = os.path.join(os.path.expanduser("~"), "Projects")
        return fallback if os.path.isdir(fallback) else qtc.QDir.homePath()

    def _dialog_start_directory(self, path_hint=''):
        if isinstance(path_hint, str) and path_hint:
            normalized = os.path.abspath(os.path.normpath(path_hint))
            if os.path.isfile(normalized):
                normalized = os.path.dirname(normalized)
            if os.path.isdir(normalized):
                return normalized
        return self._projects_base_path()

    def _choose_directory(self, title, start_dir=''):
        return str(
            qtw.QFileDialog.getExistingDirectory(
                self.ui.centralwidget,
                title,
                self._dialog_start_directory(start_dir),
            )
        )

    def _choose_file(self, title, name_filter='All Files (*.*)', start_dir=''):
        return qtw.QFileDialog.getOpenFileName(
            self.ui.centralwidget,
            title,
            self._dialog_start_directory(start_dir),
            name_filter,
        )[0]

    def loadText(self):
        self.open_non_modal_text_picker(
            'Open text file',
            self.txtdir if hasattr(self, 'txtdir') and self.txtdir else self._projects_base_path(),
            self.showText,
            '_text_open_dialog',
        )

    def OpenTextFileDialog(self, MainWindow):
        self.loadText()
        return

        txtpath = qtw.QFileDialog.getOpenFileName(
            self.ui.centralwidget,
            'Open text file',
            self.txtdir if hasattr(self, 'txtdir') else '',
            'Text files (*.txt *.csv)'
        )[0]

        if not txtpath:
            return
        else:
            # Ã¢Å“â€¦ Delegate everything to showText (single source of truth)
            self.showText(txtpath)

    def showText(self, txtfilename):
        if not txtfilename:
            return

        import os
        import json
        from PyQt5 import QtCore as qtc

        # Ã¢Å“â€¦ Always sync internal state
        self.txtpath = txtfilename
        filename = os.path.basename(self.txtpath)
        self.txtdir = os.path.dirname(self.txtpath)

        self.ui.TextLE.setText(filename)

        file = qtc.QFile(self.txtpath)

        if file.open(qtc.QIODevice.ReadOnly):
            stream = qtc.QTextStream(file)

            # Ã¢Å“â€¦ Force UTF-8 (cross-platform safe)
            stream.setCodec("UTF-8")

            text = stream.readAll()
            info = qtc.QFileInfo(self.txtpath)

            self.ui.OCRText.clear()

            if info.completeSuffix().lower() == 'txt':
                self.ui.OCRText.insertPlainText(text)
            else:
                self.ui.OCRText.setPlainText(text)

            # Ã¢Å“â€¦ formatting updates
            self.on_font_update()
            self.SetLineSpacing()

            file.close()

        # Ã¢Å“â€¦ Update session JSON safely
        jsonfile = os.path.join(RUNTIME_PATHS.project_root, "Model", "Project", "Data", "json", "Session.json")
        if os.path.exists(jsonfile):
            with open(jsonfile, 'r') as f:
                data = json.load(f)

            for Setting in data:
                if Setting['Setting'] == r"self.txtpath":
                    Setting['CurrentValue'] = self.txtpath
                elif Setting['Setting'] == r"self.txtdir":
                    Setting['CurrentValue'] = self.txtdir

            with open(jsonfile, 'w') as f:
                json.dump(data, f, indent=4)

        # Ã¢Å“â€¦ Build file list (FIXED for Windows + CSV)
        self.txtfileList = []
        for t in os.listdir(self.txtdir):
            tpath = os.path.join(self.txtdir, t)
            if os.path.isfile(tpath) and t.lower().endswith(('.txt', '.csv')):
                self.txtfileList.append(tpath)

        # Ã¢Å“â€¦ Sort + set index
        self.sortTextFiles()

    def sortTextFiles(self):
        import re

        def convert(text):
            return int(text) if text.isdigit() else text.lower()

        def alphanum_key(key):
            return [convert(c) for c in re.split('([0-9]+)', key)]

        self.sorted_txtfilelist = sorted(self.txtfileList, key=alphanum_key)

        try:
            self.txt_index = self.sorted_txtfilelist.index(self.txtpath)
        except ValueError:
            self.txt_index = 0
    def nextText(self):
        if not self.sorted_txtfilelist:
            self.loadText()
            return

        self.txt_index = (self.txt_index + 1) % len(self.sorted_txtfilelist)

        txtfile = self.sorted_txtfilelist[self.txt_index]

        self.txtpath = txtfile
        self.showText(txtfile)

    def prevText(self):
        if not self.sorted_txtfilelist:
            self.loadText()
            return

        self.txt_index = (self.txt_index - 1) % len(self.sorted_txtfilelist)

        txtfile = self.sorted_txtfilelist[self.txt_index]

        self.txtpath = txtfile
        self.showText(txtfile)

    def ReloadText(self):
        if self.txtpath:
            print("Reloading "+ self.txtpath)
            file = qtc.QFile(self.txtpath)
            filename = os.path.basename(self.txtpath)
            self.ui.TextLE.setText(filename)
            if file.open(qtc.QIODevice.ReadOnly):
                stream = qtc.QTextStream(file)
                text = stream.readAll()
                info = qtc.QFileInfo(self.txtpath)
                self.ui.OCRText.clear()
                if info.completeSuffix() == 'txt':
                    #self.ui.editor_text.setHtml(text
                    self.ui.OCRText.insertPlainText(text)
                else:
                    self.ui.OCRText.setPlainText(text)

                # update font to selection and size
                self.on_font_update()

                # update line spacing
                self.SetLineSpacing()

    def bothLoad(self):
        ''' load the matching file for either the current image or the current text '''
        def accept():
            import os

            def parse_filename(path):
                filename = os.path.splitext(os.path.basename(path))[0]
                parts = filename.split("_")

                if len(parts) < 3:
                    return None, None

                return parts[0], parts[2]  # versionref, pagestr

            # -------------------------------
            # TEXT Ã¢â€ Â IMAGE
            # -------------------------------
            if self.ImageTextPairDialog_ui.MatchTxt2Imgbutton.isChecked():

                if not self.imgpath:
                    print("No image loaded")
                    return

                versionref, pagestr = parse_filename(self.imgpath)

                if not versionref:
                    print("Filename format invalid")
                    return

                txt_path = os.path.join(
                    self.txtdir,
                    f"{versionref}_Page_{pagestr}.txt"
                )

                if os.path.exists(txt_path):
                    print("Opening:", txt_path)
                    self.txtpath = txt_path
                    self.showText(txt_path)

                    # Ã¢Å“â€¦ Sync index
                    if hasattr(self, "sorted_txtfilelist"):
                        try:
                            self.txt_index = self.sorted_txtfilelist.index(txt_path)
                        except ValueError:
                            pass
                else:
                    print("File does not exist:", txt_path)

            # -------------------------------
            # IMAGE Ã¢â€ Â TEXT
            # -------------------------------
            elif self.ImageTextPairDialog_ui.MatchImg2Txtbutton.isChecked():

                if not self.txtpath:
                    print("No text loaded")
                    return

                versionref, pagestr = parse_filename(self.txtpath)

                if not versionref:
                    print("Filename format invalid")
                    return

                imgpath = os.path.join(
                    self.imgdir,
                    f"{versionref}_Page_{pagestr}.tif"
                )

                if os.path.exists(imgpath):
                    print("Opening:", imgpath)
                    self.imgpath = imgpath
                    self.showImage(imgpath)

                    # Ã¢Å“â€¦ Sync index
                    if hasattr(self, "sorted_imgfilelist"):
                        try:
                            self.current_index = self.sorted_imgfilelist.index(imgpath)
                        except ValueError:
                            pass
                else:
                    print("File does not exist:", imgpath)


        def reject():
            pass

        self.ImageTextPairDialog = qtw.QDialog()
        self.ImageTextPairDialog_ui = Ui_ImageTextPairDialog()
        self.ImageTextPairDialog_ui.setupUi(self.ImageTextPairDialog)
        self.ImageTextPairDialog.exec_()

        self.ImageTextPairDialog_ui.buttonBox.accepted.connect(accept)
        self.ImageTextPairDialog_ui.buttonBox.rejected.connect(reject)

    def OpenPdfFileDialog(self):
        self.path = self._choose_file('Select pdf source file', '*.pdf', getattr(self, 'path', ''))

        if self.path:
            self.pdfx_ui.SourceLineEdit.setText(self.path)

    def DestPdfFileDialog(self):
        self.directory = self._choose_directory("Select destination folder", self.pdfx_ui.DestinationLineEdit.text())

        if self.directory:
            self.pdfx_ui.DestinationLineEdit.setText(self.directory+r'/')

    def PdfForTifDialog(self):
        self.path = self._choose_file('Select pdf pages source file', '*.pdf', getattr(self, 'path', ''))

        if self.path:
            self.pdf4tif_ui.SourceLineEdit.setText(self.path)

    def DestPdfForTifDialog(self):
        self.directory = self._choose_directory("Select destination folder", self.pdf4tif_ui.DestinationLineEdit.text())

        if self.directory:
            self.pdf4tif_ui.DestinationLineEdit.setText(self.directory+r'/')

    def PdfToTifDialog(self):
        self.directory = self._choose_directory("Select pdf pages source folder", self.pdf2tif_ui.SourceLineEdit.text())

        if self.directory:
            self.pdf2tif_ui.SourceLineEdit.setText(self.directory+r'/')

    def DestPdfToTifDialog(self):
        self.directory = self._choose_directory("Select destination folder", self.pdf2tif_ui.DestinationLineEdit.text())

        if self.directory:
            self.pdf2tif_ui.DestinationLineEdit.setText(self.directory+r'/')

    def TifToMonoDialog(self):
        self.directory = self._choose_directory("Select pdf pages source folder", self.tif2mono_ui.SourceLineEdit.text())

        if self.directory:
            self.tif2mono_ui.SourceLineEdit.setText(self.directory+r'/')

    def DestTifToMonoDialog(self):
        self.directory = self._choose_directory("Select destination folder", self.tif2mono_ui.DestinationLineEdit.text())

        if self.directory:
            self.tif2mono_ui.DestinationLineEdit.setText(self.directory+r'/')

    def MonoToPngDialog(self):
        self.directory = self._choose_directory("Select mono tif pages source folder", self.mono2png_ui.SourceLineEdit.text())

        if self.directory:
            self.mono2png_ui.SourceLineEdit.setText(self.directory+r'/')

    def DestMonoToPngDialog(self):
        self.directory = self._choose_directory("Select destination folder", self.mono2png_ui.DestinationLineEdit.text())

        if self.directory:
            self.mono2png_ui.DestinationLineEdit.setText(self.directory+r'/')

    def GreekMonoToPngDialog(self):
        self.directory = self._choose_directory("Select greek mono tif pages source folder", self.greekmono2png_ui.SourceLineEdit.text())

        if self.directory:
            self.greekmono2png_ui.SourceLineEdit.setText(self.directory+r'/')

    def GreekDestMonoToPngDialog(self):
        self.directory = self._choose_directory("Select destination folder", self.greekmono2png_ui.DestinationLineEdit.text())

        if self.directory:
            self.greekmono2png_ui.DestinationLineEdit.setText(self.directory+r'/')

    def DeskewMonoDialog(self):
        self.directory = self._choose_directory("Select pdf pages source folder", self.deskew_mono_ui.SourceLineEdit.text())

        if self.directory:
            self.deskew_mono_ui.SourceLineEdit.setText(self.directory+r'/')

    def DestDeskewPngDialog(self):
        self.directory = self._choose_directory("Select destination folder", self.deskew_mono_ui.DestPngLineEdit.text())

        if self.directory:
            self.deskew_mono_ui.DestPngLineEdit.setText(self.directory+r'/')

    def DestDeskewTifDialog(self):
        self.directory = self._choose_directory("Select destination folder", self.deskew_mono_ui.DestTifLineEdit.text())

        if self.directory:
            self.deskew_mono_ui.DestTifLineEdit.setText(self.directory+r'/')

    def DeskewGreekMonoDialog(self):
        self.directory = self._choose_directory("Select greek pages source folder", self.deskew_greekmono_ui.SourceLineEdit.text())

        if self.directory:
            self.deskew_greekmono_ui.SourceLineEdit.setText(self.directory+r'/')

    def DestDeskewGreekPngDialog(self):
        self.directory = self._choose_directory("Select greek png pages destination folder", self.deskew_greekmono_ui.DestPngLineEdit.text())

        if self.directory:
            self.deskew_greekmono_ui.DestPngLineEdit.setText(self.directory+r'/')

    def DestDeskewGreekTifDialog(self):
        self.directory = self._choose_directory("Select greek tif pages destination folder", self.deskew_greekmono_ui.DestTifLineEdit.text())

        if self.directory:
            self.deskew_greekmono_ui.DestTifLineEdit.setText(self.directory+r'/')

    def GreekResizePngDialog(self):
        self.directory = self._choose_directory("Select greek pages source folder", self.greekresizepng_ui.SourceLineEdit.text())

        if self.directory:
            self.greekresizepng_ui.SourceLineEdit.setText(self.directory+r'/')

    def DestGreekResizePngDialog(self):
        self.directory = self._choose_directory("Select greek png pages destination folder", self.greekresizepng_ui.DestinationLineEdit.text())

        if self.directory:
            self.greekresizepng_ui.DestinationLineEdit.setText(self.directory+r'/')

    def DeskewLatinMonoDialog(self):
        self.directory = self._choose_directory("Select latin pages source folder", self.deskew_latinmono_ui.SourceLineEdit.text())

        if self.directory:
            self.deskew_latinmono_ui.SourceLineEdit.setText(self.directory+r'/')

    def LatinMonoToPngDialog(self):
        self.directory = self._choose_directory("Select latin mono tif pages source folder", self.latinmono2png_ui.SourceLineEdit.text())

        if self.directory:
            self.latinmono2png_ui.SourceLineEdit.setText(self.directory+r'/')

    def LatinDestMonoToPngDialog(self):
        self.directory = self._choose_directory("Select destination folder", self.latinmono2png_ui.DestinationLineEdit.text())

        if self.directory:
            self.latinmono2png_ui.DestinationLineEdit.setText(self.directory+r'/')

    def DestMonoToPngDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select destination folder"))

        if self.directory:
            self.mono2png_ui.DestinationLineEdit.setText(self.directory+r'/')

    def DeskewMonoDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select pdf pages source folder"))

        if self.directory:
            self.deskew_mono_ui.SourceLineEdit.setText(self.directory+r'/')

    def DestDeskewPngDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select destination folder"))

        if self.directory:
            self.deskew_mono_ui.DestPngLineEdit.setText(self.directory+r'/')

    def DestDeskewTifDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select destination folder"))

        if self.directory:
            self.deskew_mono_ui.DestTifLineEdit.setText(self.directory+r'/')

    def DestDeskewLatinPngDialog(self):
        self.directory = self._choose_directory("Select latin png pages destination folder", self.deskew_latinmono_ui.DestPngLineEdit.text())

        if self.directory:
            self.deskew_latinmono_ui.DestPngLineEdit.setText(self.directory+r'/')

    def DestDeskewLatinTifDialog(self):
        self.directory = self._choose_directory("Select latin tif pages destination folder", self.deskew_latinmono_ui.DestTifLineEdit.text())

        if self.directory:
            self.deskew_latinmono_ui.DestTifLineEdit.setText(self.directory+r'/')

    def LatinResizePngDialog(self):
        self.directory = self._choose_directory("Select latin pages source folder", self.latinresizepng_ui.SourceLineEdit.text())

        if self.directory:
            self.latinresizepng_ui.SourceLineEdit.setText(self.directory+r'/')

    def DestLatinResizePngDialog(self):
        self.directory = self._choose_directory("Select latin png pages destination folder", self.latinresizepng_ui.DestinationLineEdit.text())

        if self.directory:
            self.latinresizepng_ui.DestinationLineEdit.setText(self.directory+r'/')

    def CropLanguagesDialog(self):
        self.directory = self._choose_directory("Select pdf pages source folder", self.crop_languages_ui.SourceLineEdit.text())

        if self.directory:
            self.crop_languages_ui.SourceLineEdit.setText(self.directory+r'/')

    def BoxFolderDialog(self):
        self.directory = self._choose_directory("Select destination folder", self.crop_languages_ui.BoxFolderLineEdit.text())

        if self.directory:
            self.crop_languages_ui.BoxFolderLineEdit.setText(self.directory+r'/')

    def ElimFolderDialog(self):
        self.directory = self._choose_directory("Select destination folder", self.crop_languages_ui.ElimFolderLineEdit.text())

        if self.directory:
            self.crop_languages_ui.ElimFolderLineEdit.setText(self.directory+r'/')

    def DestGreekDialog(self):
        self.directory = self._choose_directory("Select destination folder", self.crop_languages_ui.DestGreekLineEdit.text())

        if self.directory:
            self.crop_languages_ui.DestGreekLineEdit.setText(self.directory+r'/')

    def DestLatinDialog(self):
        self.directory = self._choose_directory("Select destination folder", self.crop_languages_ui.DestLatinLineEdit.text())

        if self.directory:
            self.crop_languages_ui.DestLatinLineEdit.setText(self.directory+r'/')

    def CropGreekLinesDialog(self):
        self.directory = self._choose_directory("Select tif pages source folder", self.crop_greeklines_ui.SourceLineEdit.text())

        if self.directory:
            self.crop_greeklines_ui.SourceLineEdit.setText(self.directory+r'/')

    def GreekLineBoxFolderDialog(self):
        self.directory = self._choose_directory("Select linebox destination folder", self.crop_greeklines_ui.GreekBoxFolderLineEdit.text())

        if self.directory:
            self.crop_greeklines_ui.GreekBoxFolderLineEdit.setText(self.directory+r'/')

    def DestGreekLinesDialog(self):
        self.directory = self._choose_directory("Select Greek lines destination folder", self.crop_greeklines_ui.DestGreekLineEdit.text())

        if self.directory:
            self.crop_greeklines_ui.DestGreekLineEdit.setText(self.directory+r'/')

    def CropLatinLinesDialog(self):
        self.directory = self._choose_directory("Select tif pages source folder", self.crop_greeklines_ui.SourceLineEdit.text())

        if self.directory:
            self.crop_greeklines_ui.SourceLineEdit.setText(self.directory+r'/')

    def LatinLineBoxFolderDialog(self):
        self.directory = self._choose_directory("Select linebox destination folder", self.crop_greeklines_ui.LatinBoxFolderLineEdit.text())

        if self.directory:
            self.crop_greeklines_ui.LatinBoxFolderLineEdit.setText(self.directory+r'/')

    def DestLatinLinesDialog(self):
        self.directory = self._choose_directory("Select Greek lines destination folder", self.crop_greeklines_ui.DestGreekLineEdit.text())

        if self.directory:
            self.crop_greeklines_ui.DestGreekLineEdit.setText(self.directory+r'/')

    def GetRawOCRtext(self):
        self.ui.OCRText.clear()
        my_OCR_rawtext = pytesseract.image_to_string(self.imgpath,lang="feg")
        self.ui.OCRText.insertPlainText(my_OCR_rawtext)
        imgfilename = self.ui.ImageLE.text()
        imgbasename = imgfilename.split(".")[0]
        self.ui.TextLE.setText(imgbasename + ".txt")

    def GetLineSpacing(self):
        self.ui.LHslider.setEnabled(True)
        self.ui.LHslider.show()
        self.ui.LHlineEdit.setPlaceholderText(str(self.ui.LHslider.value()))

    def DisableLHSlider(self):
        self.ui.LHslider.hide()
        self.ui.LHslider.setEnabled(False)

    def MoveLHSlider(self):
        self.ui.LHslider.setEnabled(True)
        #self.ui.LHslider.setValue(int(self.ui.LHlineEdit.text()))
        text = self.ui.LHlineEdit.text().strip()
        value = int(text) if text.isdigit() else 0
        self.ui.LHslider.setValue(value)

    def SetLineSpacing(self):
        lineSpacing = self.ui.LHslider.value()
        self.ui.LHlineEdit.setText(str(lineSpacing))

        cursor = self.ui.OCRText.textCursor()
        if not cursor.hasSelection():
            cursor.select(qtg.QTextCursor.Document)
        bf = self.ui.OCRCursor.blockFormat()
        bf.setLineHeight(lineSpacing, self.ui.OCRBlockFormat.ProportionalHeight)
        cursor.mergeBlockFormat(bf)

    def SaveRawTextFileDialog(self, MainWindow):
        path = qtw.QFileDialog.getSaveFileName(
            self.ui.centralwidget, 'Save Raw text file', self._dialog_start_directory(getattr(self, 'txtdir', '')),
            'Text files (*.txt)')[0]
        if not path:
            return
        with open(path, 'w') as file:
            my_RawText = self.ui.OCRDocument.toPlainText()
            file.write(my_RawText)
        filename = os.path.basename(path)
        self.ui.TextLE.setText(filename)
        file.close()

    def SaveAsCorrectedTextFileDialog(self, MainWindow):
        path = qtw.QFileDialog.getSaveFileName(
            self.ui.centralwidget, 'Save Corrected text file', self._dialog_start_directory(getattr(self, 'txtdir', '')),
            'Text files (*.txt)')[0]
        if not path:
            return
        with open(path, 'w') as file:
            my_CorrectedText = self.ui.OCRDocument.toPlainText()
            file.write(my_CorrectedText)
        filename = os.path.basename(path)
        self.ui.TextLE.setText(filename)
        file.close()

    def SaveCorrectedTextFileDialog(self, MainWindow):

        defaultdir = self._dialog_start_directory(getattr(self, 'txtdir', '')) + r"/"
        defaultfile = self.ui.TextLE.displayText()

        if defaultfile:
            path = defaultdir + defaultfile
            print(path)
            filename = defaultfile
        else:
            path = qtw.QFileDialog.getSaveFileName(
                self.ui.centralwidget, 'Save Corrected text file', self._dialog_start_directory(getattr(self, 'txtdir', '')),
                'Text files (*.txt)')[0]
            if not path:
                return
            filename = os.path.basename(path)
        with open(path, 'w') as file:
            my_CorrectedText = self.ui.OCRDocument.toPlainText()
            file.write(my_CorrectedText)

        self.ui.TextLE.setText(filename)
        file.close()

    def get_zoom(self):
        self.ui.Zoomslider.setEnabled(True)
        self.ui.Zoomslider.show()
        zoomValue = self.ui.Zoomslider.value()

    def DisableZoomSlider(self):
        self.ui.Zoomslider.hide()
        self.ui.Zoomslider.setEnabled(False)

    def MoveZoomSlider(self):
        self.ui.Zoomslider.setEnabled(True)
        try:
            value = int(self.ui.ZoomComboBox.currentText().replace('%', '').strip())
        except ValueError:
            return

        self.ui.Zoomslider.setValue(value)

    def show_combo(self):
        self.ui.ZoomComboBox.show()

    def on_zoom(self, text):
        try:
            value = int(text.replace('%', '').strip())
        except:
            return

        self.ui.Zoomslider.setValue(value)

    def on_zoomslider(self, value):
        print("[ZOOM HANDLER HIT]")  # confirm it fires

        combo_text = f"{value} %"
        if self.ui.ZoomComboBox.currentText() != combo_text:
            self.ui.ZoomComboBox.blockSignals(True)
            self.ui.ZoomComboBox.setCurrentText(combo_text)
            self.ui.ZoomComboBox.blockSignals(False)

        scale = value / 100.0
        print(value)
        print(scale)

        if not hasattr(self, "imagepixmap") or self.imagepixmap.isNull():
            print("[ZOOM ERROR] No valid pixmap")
            return

        scaled = self.imagepixmap.scaled(
            self.imagepixmap.size() * scale,
            qtc.Qt.KeepAspectRatio,
            qtc.Qt.SmoothTransformation
        )

        self.ui.Image.setPixmap(scaled)


    def run_child_module(self, filename, *args):
        module_path = os.path.abspath(os.path.join(RUNTIME_PATHS.script_dir, filename))
        cmd = [sys.executable, module_path]

        if args and args[0]:
            image_path = os.path.abspath(os.path.normpath(args[0]))
            cmd.append(image_path)

        print(f"[CMD] {cmd}")
        if not os.path.exists(module_path):
            print(f"[ERROR] File not found: {module_path}")
            return

        try:
            process = subprocess.Popen(cmd, env=_sanitized_child_process_env())
            print(f"[LAUNCH] {filename} (PID: {process.pid})")
        except Exception as e:
            print(f"[Subprocess Error] {e}")

    def _create_pixler_return_path(self):
        temp_dir = tempfile.mkdtemp(prefix="biblion_pixler_return_")
        return os.path.join(temp_dir, "pixler_return.tif")

    def _start_pixler_return_monitor(self):
        if not self.pixler_return_path:
            return

        if self._pixler_return_poll_timer is None:
            self._pixler_return_poll_timer = qtc.QTimer(self)
            self._pixler_return_poll_timer.timeout.connect(self._poll_pixler_return)

        self._pixler_return_poll_timer.start(250)

    def _stop_pixler_return_monitor(self):
        if self._pixler_return_poll_timer is not None:
            self._pixler_return_poll_timer.stop()

    def _poll_pixler_return(self):
        if not self.pixler_return_path:
            self._stop_pixler_return_monitor()
            return

        if not os.path.exists(self.pixler_return_path):
            return

        if os.path.getsize(self.pixler_return_path) <= 0:
            return

        if self.consume_pixler_return(
            self.pixler_return_path,
            source_path=self.pending_pixler_source_path,
            overwrite=False,
        ):
            self._stop_pixler_return_monitor()

    def preview_pixler_return(self, return_path):
        if not return_path or not os.path.exists(return_path):
            return False

        pixmap = qtg.QPixmap(return_path)
        if pixmap.isNull():
            image = qtg.QImage(return_path)
            if image.isNull():
                print(f"[MyServer RETURN] Could not preview returned crop: {return_path}")
                return False
            pixmap = qtg.QPixmap.fromImage(image)

        self.imagepixmap = pixmap
        self.origpixmap = pixmap
        ui = None
        try:
            ui = self.ui
        except Exception:
            ui = None

        if ui is not None and hasattr(ui, "Image"):
            ui.Image.setPixmap(self.imagepixmap)
            ui.ImageLE.setText(os.path.basename(return_path))
        print(f"[MyServer RETURN] Previewed returned crop in MyServer: {return_path}")
        return True

    def _ensure_pixler_return_prompt(self):
        if self.pixler_return_prompt_dialog is not None:
            return self.pixler_return_prompt_dialog

        dialog = qtw.QDialog(self)
        dialog.setWindowTitle("Return Crop")
        dialog.setWindowFlags(dialog.windowFlags() | qtc.Qt.Tool | qtc.Qt.WindowStaysOnTopHint)
        dialog.setModal(False)
        dialog.setAttribute(qtc.Qt.WA_ShowWithoutActivating, True)
        dialog.setFocusPolicy(qtc.Qt.NoFocus)

        layout = qtw.QVBoxLayout(dialog)
        message = qtw.QLabel(
            "MyPixler returned a crop. Inspect the preview, then decide whether to overwrite the source image."
        )
        message.setWordWrap(True)
        layout.addWidget(message)

        button_row = qtw.QHBoxLayout()
        overwrite_button = qtw.QPushButton("Overwrite Source")
        keep_button = qtw.QPushButton("Keep Preview")
        close_button = qtw.QPushButton("Close")
        button_row.addWidget(overwrite_button)
        button_row.addWidget(keep_button)
        button_row.addWidget(close_button)
        layout.addLayout(button_row)

        def do_overwrite():
            if self.pixler_return_path and self.pending_pixler_source_path:
                self.consume_pixler_return(
                    self.pixler_return_path,
                    source_path=self.pending_pixler_source_path,
                    overwrite=True,
                )

        def do_keep_preview():
            dialog.setWindowTitle("Return Crop - Preview Kept")
            self.statusBar().showMessage("Returned crop preview kept. Close this dialog when finished.")

        overwrite_button.clicked.connect(do_overwrite)
        keep_button.clicked.connect(do_keep_preview)
        close_button.clicked.connect(dialog.close)

        dialog.adjustSize()
        self.pixler_return_prompt_dialog = dialog
        return dialog

    def prompt_pixler_return_action(self):
        ui = None
        try:
            ui = self.ui
        except Exception:
            ui = None

        if ui is None:
            return False

        dialog = self._ensure_pixler_return_prompt()
        dialog.show()
        dialog.raise_()
        self.statusBar().showMessage("Returned crop preview ready. Inspect and close the floating prompt when done.")
        return True

    def consume_pixler_return(self, return_path, source_path=None, overwrite=False):
        if not return_path or not os.path.exists(return_path):
            print(f"[MyServer RETURN] Missing returned file: {return_path}")
            return False

        self.pixler_return_path = os.path.normpath(return_path)
        if source_path:
            self.pending_pixler_source_path = os.path.normpath(source_path)

        print(f"[MyServer RETURN] Received from MyPixler: {self.pixler_return_path}")

        if not overwrite:
            if not self.preview_pixler_return(self.pixler_return_path):
                return False

            self.prompt_pixler_return_action()
            return True

        if overwrite and self.pending_pixler_source_path:
            shutil.copy2(self.pixler_return_path, self.pending_pixler_source_path)
            self.imgpath = self.pending_pixler_source_path
            self.showImage(self.imgpath)
            print(f"[MyServer RETURN] Overwrote source with returned crop: {self.imgpath}")
        return True

    def OpenWithMyReader(self):
        self.run_child_module('MyReader.py')

    def OpenWithMyScanner(self):
        self.run_child_module('MyScanner.py')

    def OpenWithMyGlypher(self):
        self.run_child_module('MyGlypher.py')

    def OpenWithMyBoxer(self):
        self.run_child_module('MyBoxer.py')

    def OpenWithMyPixler(self):
        source_path = getattr(self, "imgpath", "") or getattr(self, "_stack_path", "")

        if not source_path:
            self.run_child_module('MyPixler.py')
            return

        source_path = os.path.abspath(os.path.normpath(source_path))
        self.pending_pixler_source_path = source_path
        create_return_path = getattr(self, '_create_pixler_return_path', None)
        if callable(create_return_path):
            self.pixler_return_path = create_return_path()
        else:
            temp_dir = tempfile.mkdtemp(prefix="biblion_pixler_return_")
            self.pixler_return_path = os.path.join(temp_dir, "pixler_return.tif")
        module_path = os.path.abspath(os.path.join(RUNTIME_PATHS.script_dir, 'MyPixler.py'))
        cmd = [
            sys.executable,
            module_path,
            source_path,
            '--subprocess-mode',
            '--return-path',
            self.pixler_return_path,
        ]

        print(f"[CMD] {cmd}")
        if not os.path.exists(module_path):
            print(f"[ERROR] File not found: {module_path}")
            return

        try:
            process = subprocess.Popen(cmd, env=_sanitized_child_process_env())
            print(f"[LAUNCH] MyPixler.py (PID: {process.pid})")
            self._start_pixler_return_monitor()
        except Exception as e:
            print(f"[Subprocess Error] {e}")

    def OpenWithMyVersifier(self):
        self.run_child_module('MyVersifier.py')

    def OpenWithMyResolver(self):
        self.run_child_module('MyResolver.py')

    def OpenWithMyLexer(self):
        self.run_child_module('MyLexer.py')

    def OpenWithMyGrounder(self):
        self.run_child_module('MyGrounder.py')

    def OpenWithMyTrainer(self):
        self.run_child_module('MyTrainer.py')

    def OpenWithMyWriter(self):
        self.run_child_module('MyWriter.py')

    def OpenWithMyExplorer(self):
        self.run_child_module('MyExplorer.py', self._current_model_dir())

    def OpenWithCalc(self):
        lo_cmd = 'libreoffice --calc ' + self.txtpath
        print(lo_cmd)
        os.system(lo_cmd)

    def on_font_update(self):
        # update font to selection and size
        font = qtg.QFont(self.ui.fontComboBox.currentFont())
        font.setPointSize(self.ui.fontSizeBox.value())

        self.ui.OCRText.setFont(font)

    def on_lang_select(self):
        pass



# ================================
# PROJECT CREATION STATE MACHINE
# MyServer.py - Core Implementation
# ================================

# -------------------------------
# STATE DEFINITIONS
# -------------------------------

class ProjectState(Enum):
    INIT = "INIT"
    VALIDATE_INPUT = "VALIDATE_INPUT"
    PROVENANCE_REQUIRED = "PROVENANCE_REQUIRED"
    PROVENANCE_CAPTURED = "PROVENANCE_CAPTURED"
    RIS_GENERATION = "RIS_GENERATION"
    FILESYSTEM_WRITE = "FILESYSTEM_WRITE"
    REGISTRATION = "REGISTRATION"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"

# -------------------------------
# CORE ENGINE
# -------------------------------

class ProjectCreationEngine:
    def __init__(self, base_path=None, event_bus=None):
        self.base_path = base_path or os.path.join(os.path.expanduser("~"), "Projects")
        self.state = ProjectState.INIT
        self.context = {}
        self.ris = None
        self.events = []

        # NEW: shared event bus (or create default one)
        self.event_bus = event_bus if event_bus else EventBus()

    # ---------------------------
    # EVENT EMITTER
    # ---------------------------

    def emit_event(self, event_name, metadata=None):
        event = {
            "event": event_name,
            "timestamp": time.time(),
            "state": self.state.value,
            "project_name": self.context.get("project_name"),
            "metadata": metadata or {}
        }

        # store locally (for replay/debug)
        self.events.append(event)

        # console debug
        print(f"[EVENT] {event_name}")

        # NEW: broadcast globally
        if self.event_bus:
            self.event_bus.emit(event)

        return event

    # ---------------------------
    # STATE TRANSITION CORE
    # ---------------------------

    def transition(self, next_state):
        self.state = next_state
        self.emit_event(f"state_{next_state.value.lower()}")

    # ---------------------------
    # ENTRY POINT
    # ---------------------------

    def create_project(self, payload):
        try:
            self.context = payload
            self.transition(ProjectState.INIT)

            self.validate_input()
            self.capture_provenance()
            self.generate_ris()
            self.write_filesystem()
            self.register_project()

            self.transition(ProjectState.COMPLETE)
            self.emit_event("project_created")

            return {
                "status": "success",
                "project": self.context.get("project_name")
            }

        except Exception as e:
            self.rollback()
            self.state = ProjectState.FAILED
            self.emit_event("project_failed", {"error": str(e)})
            return {"status": "failed", "error": str(e)}

    # ---------------------------
    # VALIDATION
    # ---------------------------

    def validate_input(self):
        self.transition(ProjectState.VALIDATE_INPUT)

        name = self.context.get("project_name")

        if not name or not isinstance(name, str):
            raise ValueError("Invalid project name")

        project_path = os.path.join(self.base_path, name)

        if os.path.exists(project_path):
            raise ValueError("Project already exists")

        self.emit_event("validation_passed")

    # ---------------------------
    # PROVENANCE CAPTURE
    # ---------------------------

    def capture_provenance(self):
        self.transition(ProjectState.PROVENANCE_REQUIRED)

        required_fields = [
            "project_name",
            "project_purpose",
            "creation_trigger",
            "source_context",
            "user_intent_summary"
        ]

        for field in required_fields:
            if field not in self.context:
                raise ValueError(f"Missing RIS field: {field}")

        self.ris = self.context.copy()

        self.transition(ProjectState.PROVENANCE_CAPTURED)

        # lock step (immutability simulation)
        self.ris["_locked"] = True
        self.ris["_hash"] = self._hash_ris(self.ris)

        self.emit_event("provenance_captured")

    # ---------------------------
    # RIS GENERATION
    # ---------------------------

    def generate_ris(self):
        self.transition(ProjectState.RIS_GENERATION)

        self.ris.update({
            "ris_version": "1.1",
            "timestamp_created": time.time(),
            "creator": "Max",
            "environment": {
                "platform": "MyPixler",
                "server": "MyServer"
            }
        })

        self.emit_event("ris_generated")

    # ---------------------------
    # FILESYSTEM WRITE (ATOMIC)
    # ---------------------------

    def write_filesystem(self):
        self.transition(ProjectState.FILESYSTEM_WRITE)

        project_name = self.context["project_name"]
        final_path = os.path.join(self.base_path, project_name)
        temp_path = final_path + "_tmp"

        os.makedirs(self.base_path, exist_ok=True)

        # clean temp
        if os.path.exists(temp_path):
            shutil.rmtree(temp_path)

        os.makedirs(temp_path)

                # write RIS
        with open(os.path.join(temp_path, "project.ris.json"), "w") as f:
            json.dump(self.ris, f, indent=2)

        # create structure
        os.makedirs(os.path.join(temp_path, "src"))
        os.makedirs(os.path.join(temp_path, "assets"))
        os.makedirs(os.path.join(temp_path, "logs"))
        os.makedirs(os.path.join(temp_path, "output"))
        self._write_git_support_files(temp_path)

        # atomic commit
        if os.path.exists(final_path):
            raise ValueError("Final path collision")

        os.rename(temp_path, final_path)
        self._initialize_git_repository(final_path)

        self.emit_event("filesystem_written")

    # ---------------------------
    # GIT REPOSITORY INITIALIZATION
    # ---------------------------

    def _write_git_support_files(self, project_path):
        readme_path = os.path.join(project_path, "README.md")
        gitignore_path = os.path.join(project_path, ".gitignore")

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(f"# {self.context['project_name']}\n\n")
            f.write("Local BiblionOCR project repository.\n")

        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write("__pycache__/\n")
            f.write("*.pyc\n")
            f.write("*.tmp\n")
            f.write("*.log\n")
            f.write(".DS_Store\n")
            f.write("Thumbs.db\n")

    def _initialize_git_repository(self, project_path):
        git_executable = shutil.which("git")
        if not git_executable:
            raise RuntimeError("Git executable not found; cannot initialize local repository.")

        result = subprocess.run(
            [git_executable, "init"],
            cwd=project_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Git repository initialization failed: {result.stderr.strip()}")

        branch_result = subprocess.run(
            [git_executable, "symbolic-ref", "HEAD", "refs/heads/main"],
            cwd=project_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if branch_result.returncode != 0:
            raise RuntimeError(f"Git default branch setup failed: {branch_result.stderr.strip()}")

        self.emit_event("git_repository_initialized", {"path": project_path})

    # ---------------------------
    # REGISTRATION
    # ---------------------------

    def register_project(self):
        self.transition(ProjectState.REGISTRATION)

        registry_path = os.path.join(self.base_path, "_registry.json")

        registry = []

        if os.path.exists(registry_path):
            with open(registry_path, "r") as f:
                registry = json.load(f)
            if isinstance(registry, dict):
                registry = [registry]
            elif not isinstance(registry, list):
                registry = []

        registry = [item for item in registry if item.get("project_name") != self.context["project_name"]]
        registry.append({"project_name": self.context["project_name"],"timestamp": time.time(),"path": os.path.join(self.base_path, self.context["project_name"]),"git_repository": True})
        with open(registry_path, "w") as f:
            json.dump(registry, f, indent=2)

        self.emit_event("project_registered")

    # ---------------------------
    # ROLLBACK
    # ---------------------------

    def rollback(self):
        project_name = self.context.get("project_name")
        if not project_name:
            return

        path = os.path.join(self.base_path, project_name)
        tmp_path = path + "_tmp"

        for p in [path, tmp_path]:
            if os.path.exists(p):
                shutil.rmtree(p)

        self.emit_event("rollback_complete")

    # ---------------------------
    # HASH FUNCTION
    # ---------------------------

    def _hash_ris(self, ris):
        raw = json.dumps(ris, sort_keys=True).encode()
        return hashlib.sha256(raw).hexdigest()

# ================================
# 0-MainUI - RIS Dialog Controller
# ================================

class RISDialogController:

    def __init__(self, engine):
        self.engine = engine

    def launch_dialog(self):
        """
        UI must BLOCK until RIS payload is complete
        """

        self.engine.emit_event("provenance_required")

        ris_payload = self.collect_user_input()

        self.engine.context.update(ris_payload)

        return ris_payload

    def collect_user_input(self):
        """
        Replace with real UI bindings.
        This is the contract layer.
        """

        return {
            "project_name": input("Project Name: "),
            "project_purpose": input("Purpose: "),
            "creation_trigger": "manual",
            "source_context": "0-MainUI",
            "user_intent_summary": input("Intent Summary: ")
        }
# ================================
# EVENT BUS
# ================================

class EventBus:

    def __init__(self):
        self.listeners = {}

    def subscribe(self, event_name, callback):
        if event_name not in self.listeners:
            self.listeners[event_name] = []
        self.listeners[event_name].append(callback)

    def unsubscribe(self, event_name, callback):
        callbacks = self.listeners.get(event_name)
        if not callbacks:
            return

        self.listeners[event_name] = [cb for cb in callbacks if cb != callback]
        if not self.listeners[event_name]:
            del self.listeners[event_name]

    def emit(self, event):
        name = event["event"]

        if name in self.listeners:
            for cb in list(self.listeners[name]):
                cb(event)

        if "*" in self.listeners:
            for cb in list(self.listeners["*"]):
                cb(event)

# ================================
# PROJECT REPLAY ENGINE
# ================================

class ProjectReplayEngine:

    def __init__(self, event_log):
        self.events = event_log

    def replay(self):
        state = {}

        for e in self.events:
            print(f"Replaying: {e['event']}")

            if e["event"] == "validation_passed":
                state["validated"] = True

            if e["event"] == "provenance_captured":
                state["ris_locked"] = True

            if e["event"] == "filesystem_written":
                state["written"] = True

            if e["event"] == "project_created":
                state["complete"] = True

        return state

    def reconstruct_timeline(self):
        return [
            (e["timestamp"], e["event"], e["state"])
            for e in self.events
        ]


# Only run this code if I am actually running this script
if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec()
