# pyright: reportGeneralTypeIssues=false, reportOptionalMemberAccess=false, reportAssignmentType=false, reportArgumentType=false, reportAttributeAccessIssue=false, reportCallIssue=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportPossiblyUnboundVariable=false, reportIncompatibleMethodOverride=false, reportRedeclaration=false, reportOperatorIssue=false
# -*- coding: utf-8 -*-

# Python imports
import importlib.util
import sys
import os
import subprocess
import tempfile
from dataclasses import replace

_LOCAL_MODULE_DIR = os.path.abspath(os.path.dirname(__file__))
_LEGACY_MAINUI_DIR = os.path.abspath(os.path.join(_LOCAL_MODULE_DIR, "..", "0-MainUI"))
_LEGACY_MAINUI_HELPERS_DIR = os.path.abspath(os.path.join(_LEGACY_MAINUI_DIR, "helpers"))
_LOCAL_HELPERS_DIR = os.path.abspath(os.path.join(_LOCAL_MODULE_DIR, "helpers"))
if _LOCAL_MODULE_DIR not in sys.path:
    sys.path.insert(0, _LOCAL_MODULE_DIR)
if _LEGACY_MAINUI_DIR not in sys.path:
    sys.path.insert(0, _LEGACY_MAINUI_DIR)
if _LEGACY_MAINUI_HELPERS_DIR not in sys.path:
    sys.path.insert(0, _LEGACY_MAINUI_HELPERS_DIR)
if _LOCAL_HELPERS_DIR not in sys.path:
    sys.path.insert(0, _LOCAL_HELPERS_DIR)

from gui_runtime_env import sanitize_current_process_and_reexec

sanitize_current_process_and_reexec()

import re
import io
import pathlib
import tiffcapture
import qimage2ndarray
from queue import Queue
from PIL import Image as pilimg
from PIL import ImageQt as pilqimg
import shutil
import cv2
import numpy as np
from scipy import ndimage
import math
from copy import deepcopy
# Path configuration and directory setup
script_dir = os.path.dirname(os.path.realpath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))

# Define directories
model_dir = os.path.join(project_root, "Model")
data_dir = os.path.join(model_dir, "Data")
image_dir = os.path.join(model_dir, "Images")
text_dir = os.path.join(model_dir, "Text")
train_dir = os.path.join(model_dir, "Training")
session_dir = os.path.join(data_dir, "json")

# Add project root to path
if project_root not in sys.path:
    sys.path.insert(0, project_root)


from HelpSystem import add_help_menu, show_help
from source_reader import SourceReaderDock
from Core.book_metadata import (
    book_session_values,
    find_book_reference,
    load_book_references,
    normalize_book_folder,
)
from Core.page_workflow import (
    PAGE_WORKFLOW_FILENAME,
    WORKFLOW_DIRECTORY,
    advance_page_workflow_files,
    load_page_workflow,
    resolve_page_workflow_path,
    select_page_workflow_step,
)
from Core.project_tracking import ProjectWorkflowTracker
from Core.source_documents import (
    SUPPORTED_SOURCE_EXTENSIONS,
    complete_project_staged_pdf_handoff,
    convert_pdf_pages_to_tiff,
    extract_pdf_page_range,
    extract_pdf_pages,
    extract_pdf_source_pages,
    find_project_pdf_source,
    project_staged_pdf_complete_directory,
    project_staged_pdf_workflow_directory,
)
from Core.workflow_wizard_actions import (
    install_workflow_wizard_menu_actions,
)
from SessionManager import SessionManager
# PyQt5 imports
from PyQt5 import uic
from PyQt5.QtWidgets import QRubberBand, QWidget, QVBoxLayout, QHBoxLayout, QSizeGrip, QPushButton, QMessageBox, QFrame, QLabel, QColorDialog
from PyQt5 import QtWidgets as qtw
from PyQt5.QtGui import QPainter, QPen, QIcon, QPixmap, QColor, QBrush
from PyQt5 import QtGui as qtg
from PyQt5.QtCore import QPoint, QRect, QSize, Qt, QUrl
from PyQt5 import QtCore as qtc
from ImageLoadWorker import ImageLoadWorker
from TiffStackWorker import TiffStackWorker
# Custom imports
from PreProcess import PreProcess as pp
#from MyScanner import Ui_Scanner
_UI_MODULE_PATH = os.path.join(_LOCAL_MODULE_DIR, "MyPixlerUI.py")
_UI_SPEC = importlib.util.spec_from_file_location("biblion_mypixler_ui", _UI_MODULE_PATH)
if _UI_SPEC is None or _UI_SPEC.loader is None:
    raise ImportError(f"Unable to load MyPixler UI module from {_UI_MODULE_PATH}")
_UI_MODULE = importlib.util.module_from_spec(_UI_SPEC)
_UI_SPEC.loader.exec_module(_UI_MODULE)
Ui_Pixler = _UI_MODULE.Ui_Pixler
from Adjust import crop_processor, get_processor, rotate_processor, threshold_processor, PROCESSORS
from ImagePreviewDialog import ImagePreviewDialog
from MorphologyDialog import MorphologyDialog
from LocalFileDrop import LocalFileDropMixin
from MyPixlerPageWorkflowWizard import MyPixlerPageWorkflowWizardDialog


# Dialog Imports
from Dialogs.ExtractDialog import Ui_ExtractDialog
from Dialogs.StageDialog import Ui_StageDialog
from Dialogs.pdf4tifDialog import Ui_pdf4tifDialog
from Dialogs.pdf2tifDialog import Ui_pdf2tifDialog
from Dialogs.tif2monoDialog import Ui_tif2monoDialog
from Dialogs.deskew_monoDialog import Ui_deskew_monoDialog
from Dialogs.crop_languagesDialog import Ui_crop_languagesDialog
from Dialogs.deskew_greekmonoDialog import Ui_deskew_greekmonoDialog
from Dialogs.deskew_latinmonoDialog import Ui_deskew_latinmonoDialog

def _copy_qimage_resolution_metadata(source, target):
    if source is None or target is None or source.isNull() or target.isNull():
        return

    target.setDotsPerMeterX(source.dotsPerMeterX())
    target.setDotsPerMeterY(source.dotsPerMeterY())
    target.setDevicePixelRatio(source.devicePixelRatio())

    if hasattr(source, "colorSpace") and hasattr(target, "setColorSpace"):
        try:
            color_space = source.colorSpace()
            if color_space.isValid():
                target.setColorSpace(color_space)
        except Exception:
            pass

def _qimage_to_cv_bgr_image(qimage):
    if qimage is None or qimage.isNull():
        return None

    buffer = qtc.QBuffer()
    buffer.open(qtc.QBuffer.ReadWrite)
    qimage.save(buffer, "PNG")
    pil_image = pilimg.open(io.BytesIO(buffer.data())).convert("RGB")
    return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

def _morphology_shape_constant(shape_name):
    shape_map = {
        "rect": cv2.MORPH_RECT,
        "ellipse": cv2.MORPH_ELLIPSE,
        "cross": cv2.MORPH_CROSS,
    }
    return shape_map.get(shape_name, cv2.MORPH_RECT)

def process_morphology_qimage(qimage, params, progress_callback=None, status_callback=None):
    def report_progress(value):
        if progress_callback is not None:
            progress_callback(int(value))

    def report_status(message):
        if status_callback is not None:
            status_callback(message)

    if qimage is None or qimage.isNull():
        return qtg.QImage()

    report_status("Preparing morphology input...")
    report_progress(5)

    cv_image = _qimage_to_cv_bgr_image(qimage)
    if cv_image is None:
        return qtg.QImage()

    report_status("Converting reference image to grayscale...")
    report_progress(20)
    if len(cv_image.shape) == 2:
        gray = cv_image
    else:
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

    threshold_value = max(0, min(255, int(params.get("threshold", 0))))
    report_status("Thresholding reference image...")
    report_progress(40)
    if threshold_value == 0:
        _threshold, binary = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
    else:
        _threshold, binary = cv2.threshold(
            gray, threshold_value, 255, cv2.THRESH_BINARY
        )

    operation = params.get("operator", "threshold")
    kernel_x = max(1, int(params.get("kernel_x", 3)))
    kernel_y = max(1, int(params.get("kernel_y", 3)))
    kernel_x = kernel_x if kernel_x % 2 == 1 else kernel_x + 1
    kernel_y = kernel_y if kernel_y % 2 == 1 else kernel_y + 1
    iterations = max(0, int(params.get("iterations", 1)))

    processed_mask = cv2.bitwise_not(binary)
    if operation != "threshold" and iterations > 0:
        report_status("Applying morphology operator...")
        report_progress(65)
        kernel = cv2.getStructuringElement(
            _morphology_shape_constant(params.get("shape", "rect")),
            (kernel_x, kernel_y),
        )

        if operation == "erode":
            processed_mask = cv2.erode(processed_mask, kernel, iterations=iterations)
        elif operation == "dilate":
            processed_mask = cv2.dilate(processed_mask, kernel, iterations=iterations)
        elif operation == "open":
            processed_mask = cv2.morphologyEx(
                processed_mask, cv2.MORPH_OPEN, kernel, iterations=iterations
            )
        elif operation == "close":
            processed_mask = cv2.morphologyEx(
                processed_mask, cv2.MORPH_CLOSE, kernel, iterations=iterations
            )
    else:
        report_status("Threshold preview selected. Skipping morphology operator...")
        report_progress(65)

    report_status("Finalizing processed image...")
    report_progress(85)
    result = cv2.bitwise_not(processed_mask)
    result_qimage = qimage2ndarray.array2qimage(result, normalize=False)
    _copy_qimage_resolution_metadata(qimage, result_qimage)
    report_progress(100)
    return result_qimage

class MorphologyApplyWorker(qtc.QObject):
    progress = qtc.pyqtSignal(int)
    status = qtc.pyqtSignal(str)
    finished = qtc.pyqtSignal(object)
    error = qtc.pyqtSignal(str)

    def __init__(self, qimage, params, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.qimage = qtg.QImage(qimage)
        self.params = dict(params or {})

    @qtc.pyqtSlot()
    def run(self):
        try:
            result = process_morphology_qimage(
                self.qimage,
                self.params,
                progress_callback=self.progress.emit,
                status_callback=self.status.emit,
            )
            self.finished.emit(result)
        except Exception as exc:
            self.error.emit(str(exc))

class PixlerMain(LocalFileDropMixin, qtw.QMainWindow):

    def __init__(self, imgpath=None, parent=None, launch_args=None):
        super().__init__(parent)

        print("=== INIT START ===")

        # -------------------------
        # Phase 1 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â HARD STATE INIT (CRITICAL)
        # -------------------------
        self.imgpath = None
        self.refimgpath = None
        self.subprocess_mode = False
        self.subprocess_return_path = ""
        self.subprocess_caller = ""

        self.refimgdir = ""
        self.imagedir = ""

        self.refimgfiles = []
        self.refimgindex = -1
        self.imagefiles = []
        self.imageindex = -1

        self.RefImgchangesSaved = True

        self.origin = QPoint()
        self.refimgscale = 1
        self.imagescale = 1

        self.refimgpixmap = qtg.QPixmap()
        self.refimgqimage = qtg.QImage()
        self.imagepixmap = qtg.QPixmap()
        self.imageqimage = qtg.QImage()
        self._progress_bar_scale = 10
        self._stack_thread = None
        self._stack_worker = None
        self._load_thread = None
        self._load_worker = None
        self._processing_thread = None
        self._processing_worker = None
        self._pending_morphology_params = None
        self.morphology_params = {
            "threshold": 0,
            "operator": "threshold",
            "shape": "rect",
            "kernel_x": 3,
            "kernel_y": 3,
            "iterations": 1,
        }
        self.fill_background_color = qtg.QColor("white")
        self.fill_foreground_color = qtg.QColor("black")
        self.eraser_tip_diameter = 24
        self.eraser_tip_shape = "circle"
        self._last_crop_origin = qtc.QPoint(0, 0)
        self.rubberBand = None
        self.return_button = None
        self.crop_prompt_dialog = None
        self.crop_selection_ready = False
        self.crop_drawing_active = False
        self.shared_session_manager = SessionManager()
        self.current_project_root = self.shared_session_manager.get_active_project_root() or None
        self.current_project_page = 1
        self.current_project_milestone = ""
        self.current_page_milestone = ""
        self._active_project_sync_timer = None
        self.pdf_source_path = ""
        self.pdf_page_count = 0
        self.source_reader = None

        # -------------------------
        # Phase 2 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â ARGUMENT HANDLING (calling module ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ MyPixler)
        # -------------------------
        import sys

        if launch_args is not None:
            parsed_imgpath, subprocess_mode, return_path, caller = self._parse_launch_arguments(launch_args)
            self.subprocess_mode = subprocess_mode
            self.subprocess_return_path = return_path
            self.subprocess_caller = caller
            if parsed_imgpath:
                imgpath = parsed_imgpath
        elif imgpath is None and len(sys.argv) > 1:
            imgpath, subprocess_mode, return_path, caller = self._parse_launch_arguments(sys.argv[1:])
            self.subprocess_mode = subprocess_mode
            self.subprocess_return_path = return_path
            self.subprocess_caller = caller

        if not imgpath:
            shared_page = self.shared_session_manager.get_active_project_page_state()
            shared_page_path = str(shared_page.get("page_path", "") or "")
            if os.path.isfile(shared_page_path) and self.is_image_file(shared_page_path):
                imgpath = shared_page_path

        if imgpath:
            imgpath = os.path.abspath(os.path.normpath(imgpath))
            self.imgpath = imgpath
            self.refimgpath = imgpath

        print(f"[INIT] argv imgpath: {imgpath}")
        print(f"[INIT] refimgpath (pre-session): {self.refimgpath}")

        # -------------------------
        # Phase 3 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â PATH SYSTEM
        # -------------------------
        self.mod_dirname = os.path.dirname(__file__)
        self.mod_rootdir = os.path.join(self.mod_dirname, "..", "..")
        self.projecthome = os.path.abspath(os.path.realpath(self.mod_rootdir))

        print(f"[PATH] Project Home: {self.projecthome}")

        # -------------------------
        # Phase 4 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â UI SETUP
        # -------------------------
        self.ui = Ui_Pixler()
        self.ui.setupUi(self)
        install_workflow_wizard_menu_actions(
            self,
            'MyPixler',
            include_project_wizard=False,
            include_page_wizard=True,
        )
        self.open_page_workflow_wizard = self._open_page_workflow_wizard

        # Progress bar (safe)
        if not hasattr(self, "progress_bar"):
            self.progress_bar = qtw.QProgressBar()

        self.progress_bar.setRange(0, 100 * self._progress_bar_scale)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self._init_project_status_widgets()
        self.statusBar().addPermanentWidget(self.progress_bar)

        add_help_menu(self, 'MyPixler')

        self.initUI()
        self._start_active_project_sync()
        qtc.QTimer.singleShot(250, self._open_project_source_pdf_on_startup)

        print("[INIT] UI READY")

        # -------------------------
        # Phase 5 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â SESSION FALLBACK (ONLY IF NO ARG)
        # -------------------------
        if not self.refimgpath:
            print("[INIT] Loading from session")
            self.get_session_settings()

        print(f"[INIT] refimgpath (final): {self.refimgpath}")

        # -------------------------
        # Phase 6 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â VALIDATION
        # -------------------------
        self._startup_load = bool(
            self.refimgpath and os.path.isfile(self.refimgpath)
        )

        if launch_args is not None:
            parsed_imgpath, subprocess_mode, return_path, caller = self._parse_launch_arguments(launch_args)
            self.subprocess_caller = caller
        # -------------------------
        # Phase 7 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â DEFERRED STARTUP (CRITICAL)
            if parsed_imgpath:
                imgpath = parsed_imgpath
        elif imgpath is None and len(sys.argv) > 1:
            imgpath, subprocess_mode, return_path, caller = self._parse_launch_arguments(sys.argv[1:])
            self.subprocess_mode = subprocess_mode
            self.subprocess_return_path = return_path
            self.subprocess_caller = caller
        # -------------------------
        if self._startup_load:
            def _startup():
                print("[INIT] Deferred startup executing")

                # index only (no rendering)
                self.setupRefImages()

                # ÃƒÂ°Ã…Â¸Ã¢â‚¬ÂÃ‚Â¥ CRITICAL: start async load
                self.start_image_load(self.refimgpath, target="ref")

            qtc.QTimer.singleShot(0, _startup)
        else:
            print("[INIT] No valid image to load")

        self._refresh_project_status(self.refimgpath or self.imgpath)
        print("=== INIT COMPLETE ===")

    def _open_page_workflow_wizard(self, _requested_module=None):
        dialog = MyPixlerPageWorkflowWizardDialog(self, self)
        dialog.exec_()

    def _parse_launch_arguments(self, argv):
        imgpath = None
        subprocess_mode = False
        return_path = ""
        caller = ""

        index = 0
        while index < len(argv):
            token = argv[index]
            if token == "--subprocess-mode":
                subprocess_mode = True
                index += 1
                continue
            if token == "--return-path" and index + 1 < len(argv):
                return_path = os.path.abspath(os.path.normpath(argv[index + 1]))
                subprocess_mode = True
                index += 2
                continue
            if token == "--caller" and index + 1 < len(argv):
                caller = str(argv[index + 1]).strip()
                index += 2
                continue
            if token.startswith("--"):
                index += 1
                continue
            if imgpath is None:
                imgpath = token
            index += 1

        return imgpath, subprocess_mode, return_path, caller

    @qtc.pyqtSlot(str)
    def append_text(self,text):
        self.ui.OutputText.append(text)

    #custom method to write anything printed out to console/terminal to my QTextEdit widget via append function.
    def output_terminal_written(self, text):
        self.ui.OutputText.append(text)

    # Session View

    def get_session_settings(self):
        base = os.path.join(self.projecthome, 'Model', 'Project', 'Data', 'json')
        sm = SessionManager(base)

        print("loading scanner session")
        scanner_session = sm.values('ScannerSession.json')

        # -------------------------
        # Preserve runtime values FIRST
        # -------------------------
        runtime_imgpath = getattr(self, 'imgpath', '')
        runtime_refimgpath = getattr(self, 'refimgpath', '')

        # -------------------------
        # Scanner session (fallback only)
        # -------------------------
        session_imgpath = scanner_session.get('self.imgpath', '')
        session_imgdir = scanner_session.get('self.imgdir', '')

        if not runtime_imgpath and session_imgpath:
            self.imgpath = os.path.normpath(session_imgpath)
        else:
            self.imgpath = os.path.normpath(runtime_imgpath) if runtime_imgpath else ""

        self.imgdir = os.path.normpath(session_imgdir) if session_imgdir else ""

        print("loading pixler session")
        session = sm.values('PixlerSession.json')

        # -------------------------
        # Helpers
        # -------------------------
        def get_setting(name: str, default=None):
            if default is None:
                default = getattr(self, name, None)
            return session.get(f'self.{name}', default)

        def abs_project_path(name: str, default=''):
            value = session.get(f'self.{name}')
            if not value:
                return getattr(self, name, default)

            value = os.path.normpath(value)

            if os.path.isabs(value):
                return value

            return os.path.normpath(os.path.join(self.projecthome, value))

        def data_path(name: str, default=''):
            value = session.get(f'self.{name}')
            if not value:
                return getattr(self, name, default)

            value = os.path.normpath(value)

            if os.path.isabs(value):
                return value

            return os.path.normpath(os.path.join(self.projecthome, self.jsondir, value))

        # -------------------------
        # Load simple settings
        # -------------------------
        self.jsondir = get_setting('jsondir', '')
        self.session = data_path('session')
        self.workflow = data_path('workflow')

        self.font = get_setting('font', '')
        self.fontsize = get_setting('fontsize', 20)
        self.ocrlang = get_setting('ocrlang', '')
        self.ocrmodel = get_setting('ocrmodel', '')
        self.bookabbr = get_setting('bookabbr', '')
        self.chr = get_setting('chr', '')

        self.sourcebookmarkdown = get_setting('sourcebookmarkdown', '')
        self.greekbookmarkdown = get_setting('greekbookmarkdown', '')
        self.latinbookmarkdown = get_setting('latinbookmarkdown', '')

        self.pixmap = get_setting('pixmap', None)
        self.qimage = get_setting('qimage', None)

        # -------------------------
        # CRITICAL: Controlled path restore
        # -------------------------

        session_ref = abs_project_path('refimgpath')
        if not runtime_refimgpath and session_ref:
            self.refimgpath = session_ref
        # else: KEEP runtime value

        self.refimgdir = abs_project_path('refimgdir')

        session_img = abs_project_path('imagepath')
        if not runtime_imgpath and session_img:
            self.imagepath = session_img
        # else: KEEP runtime

        self.imagedir = abs_project_path('imagedir')

        # -------------------------
        # Remaining settings
        # -------------------------
        self.refimg_xoffset = get_setting('refimg_xoffset', 0)
        self.refimg_yoffset = get_setting('refimg_yoffset', 0)
        self.refimgtfileList = get_setting('refimgtfileList', [])
        self.refimgzoom = get_setting('refimgzoom', '')
        self.refimgzoomslidervalue = get_setting('refimgzoomslidervalue', 0)

        self.image_xoffset = get_setting('image_xoffset', 0)
        self.image_yoffset = get_setting('image_yoffset', 0)
        self.imagefileList = get_setting('imagefileList', [])
        self.imagezoom = get_setting('imagezoom', '')
        self.imagezoomslidervalue = get_setting('imagezoomslidervalue', 0)
        self.current_project_page = get_setting('current_project_page', 1)
        self.current_project_milestone = get_setting('current_project_milestone', '')
        self.current_page_milestone = get_setting('current_page_milestone', '')

        # Bulk paths (safe now)
        self.bmpsourcedir = abs_project_path('bmpsourcedir')
        self.bmpgreekdir = abs_project_path('bmpgreekdir')

        self.pixlerpagesrotatedir = abs_project_path('pixlerpagesrotatedir')

        self.greekpages = abs_project_path('greekpages')
        self.greekpagesrotated = abs_project_path('greekpagesrotated')
        self.greekpagesdeskewed = abs_project_path('greekpagesdeskewed')
        self.greekpagescropped = abs_project_path('greekpagescropped')
        self.greekpagescleaned = abs_project_path('greekpagescleaned')
        self.greekpagesbox = abs_project_path('greekpagesbox')

        self.greeklinescropped = abs_project_path('greeklinescropped')
        self.greeklinescleaned = abs_project_path('greeklinescleaned')
        self.greeklinesbox = abs_project_path('greeklinesbox')

        self.latinpages = abs_project_path('latinpages')
        self.latinpagesrotated = abs_project_path('latinpagesrotated')
        self.latinpagesdeskewed = abs_project_path('latinpagesdeskewed')
        self.latinpagescropped = abs_project_path('latinpagescropped')
        self.latinpagescleaned = abs_project_path('latinpagescleaned')
        self.latinpagesbox = abs_project_path('latinpagesbox')

        self.latinlinescropped = abs_project_path('latinlinescropped')
        self.latinlinescleaned = abs_project_path('latinlinescleaned')
        self.latinlinesbox = abs_project_path('latinlinesbox')

        self.hebrewpagesdenoised = abs_project_path('hebrewpagesdenoised')
        self.hebrewpagesrotated = abs_project_path('hebrewpagesrotated')
        self.hebrewpagesdeskewed = abs_project_path('hebrewpagesdeskewed')
        self.hebrewpagescropped = abs_project_path('hebrewpagescropped')
        self.hebrewpagescleaned = abs_project_path('hebrewpagescleaned')
        self.hebrewpagesbox = abs_project_path('hebrewpagesbox')

        self.hebrewlinescropped = abs_project_path('hebrewlinescropped')
        self.hebrewlinescleaned = abs_project_path('hebrewlinescleaned')
        self.hebrewlinesbox = abs_project_path('hebrewlinesbox')

        print(f'Absolute Path to Project Directory: {self.projecthome}')

    def _update_pixler_session_paths(self):
        base = os.path.join(self.projecthome, 'Model', 'Project', 'Data', 'json')

        payload = {}
        if getattr(self, 'refimgpath', None):
            payload['self.refimgpath'] = os.path.normpath(self.refimgpath)
        if getattr(self, 'refimgdir', None):
            payload['self.refimgdir'] = os.path.normpath(self.refimgdir)
        if getattr(self, 'imagepath', None):
            payload['self.imagepath'] = os.path.normpath(self.imagepath)
        if getattr(self, 'imagedir', None):
            payload['self.imagedir'] = os.path.normpath(self.imagedir)

        if payload:
            SessionManager(base).update('PixlerSession.json', payload)

    def get_workflow_settings(self):
        definition_root = self._workflow_definition_root()
        steps, _notes = load_page_workflow(definition_root)
        if not steps:
            print("[WORKFLOW] No page_workflow.csv file found; continuing with manual paths.")
            return

        for step in steps:
            if step.module == "MyPixler":
                print(step.sequence, step.dialog_ui, step.workflow_source)

    def initToolbar(self):
        # Signals(Slots)
        self.ui.actionCropRefImg.triggered.connect(self.actionCropImage)
        self.ui.actionDeskewRefImg.triggered.connect(self.deskewRefImg)
        self.ui.actionRotateRefImg_360_deg.triggered.connect(self.rotateRefImg)
        self.ui.actionDenoise.triggered.connect(self.openDenoiseDialog)
        self.ui.actionClipRefImg.triggered.connect(self.clip)
        self.ui.actionErase.triggered.connect(self.eraser)
        self.ui.actionRotateRefImg_90_CW.triggered.connect(self.rotateRefImg90CW)
        self.ui.actionRotateRefImg_90_CCW.triggered.connect(self.rotateRefImg90CCW)

    def initWorkflowActions(self):
        workflow_actions = (
            ("actionStage_pdf", self.actionstage_pdf),
            ("actionExtract_pdf", self.actionextract_pdf),
            ("actionpdf_For_tiff", self.actionpdf_for_tiff),
            ("actionpdf_To_tiff", self.actionpdf_to_tiff),
            ("actiontiff_indexed", self.actiontiff_to_mono),
            ("actionDeskew_indexed", self.actiondeskew_mono),
            ("actionManually_Crop_Language_Pages", self.actionCropImage),
            ("actionAuto_Crop", self.actionCrop_Languages),
            ("actionDeskew_Greek_tiff", self.actionDeskew_Greek_tiff),
            ("actionDeskew_Latin_tiff", self.actionDeskew_Latin_tiff),
        )
        for action_name, callback in workflow_actions:
            getattr(self.ui, action_name).triggered.connect(callback)

    def initMenubar(self):

        # File menu Signals(Slots)
        self.ui.actionMyExplorer.triggered.connect(self.open_myexplorer)
        self.ui.actionOpen_Reference_Image.triggered.connect(self.loadRefImg)
        self.ui.actionSave_Image.triggered.connect(self.save_image_with_myexplorer)
        self.ui.actionSave_As_Image.triggered.connect(self.save_image_as_with_myexplorer)
        self.ui.actionOverwrite_Reference_Image.triggered.connect(self.OverwriteRefImg)
        self.ui.actionImport_Current_Image.triggered.connect(self.importRefImg)
        self.ui.actionLanguage_Morphology.triggered.connect(self.openMorphologyDialog)
        self.view_source_document_action = qtw.QAction("Open Source Reader", self)
        self.view_source_document_action.setEnabled(bool(self._project_source_pdf()))
        self.view_source_document_action.triggered.connect(self._view_source_document_triggered)
        self.ui.menuView.addAction(self.view_source_document_action)
        self.source_reader_visibility_action = qtw.QAction("Show Source Reader", self)
        self.source_reader_visibility_action.setCheckable(True)
        self.source_reader_visibility_action.setEnabled(False)
        self.source_reader_visibility_action.triggered.connect(self._set_source_reader_visibility)
        self.ui.menuView.addAction(self.source_reader_visibility_action)
        #self.ui.actionExport_Image.triggered.connect()

        # Edit Menu Signals(Slots)

        self.ui.actionFillBackground.triggered.connect(self.choose_fill_background_color)
        self.ui.actionFillForeground.triggered.connect(self.choose_fill_foreground_color)

    def open_myexplorer(self):
        explorer_path = os.path.join(
            project_root,
            "ViewController",
            "0-MainUI",
            "MyExplorer.py",
        )
        if not os.path.isfile(explorer_path):
            qtw.QMessageBox.warning(
                self,
                "Open MyExplorer",
                f"MyExplorer is not available at:\n{explorer_path}",
            )
            return None
        active_root = self.current_project_root or self._shared_active_project_root()
        command = [sys.executable, explorer_path]
        if active_root:
            command.append(active_root)
        try:
            return subprocess.Popen(command)
        except OSError as exc:
            qtw.QMessageBox.warning(
                self,
                "Open MyExplorer",
                f"MyExplorer could not be opened.\n\n{exc}",
            )
            return None

    def initUI(self):

        self.get_session_settings()

        self.initMenubar()
        self.initToolbar()
        self.initWorkflowActions()

        # -------------------------
        # Ref Image
        # -------------------------
        self.ui.OpenRefImgbutton.clicked.connect(self.open_image_with_myexplorer)
        self.ui.ImportRefImgFilebutton.clicked.connect(self.importRefImg)
        self.ui.Deskewbutton.clicked.connect(self.deskewRefImg)
        self.ui.OverwriteRefImgbutton.clicked.connect(self.OverwriteRefImg)

        self.ui.RefImgZoombutton.clicked.connect(self.get_RefImgzoom)
        self.ui.RefImgZoomComboBox.currentTextChanged.connect(self.on_RefImgzoom)
        self.ui.RefImgzoomslider.valueChanged.connect(self.on_RefImgzoomslider)
        self.ui.RefImgzoomslider.sliderReleased.connect(self.disable_RefImgzoomslider)

        self.ui.NextRefImgbutton.clicked.connect(self.nextRefImage)
        self.ui.PrevRefImgbutton.clicked.connect(self.prevRefImage)

        # -------------------------
        # Both
        # -------------------------
        self.ui.reloadImagebutton.clicked.connect(self.reloadImage)
        self.ui.reloadRefImgbutton.clicked.connect(self.reloadRefImg)

        # -------------------------
        # Image
        # -------------------------
        self.ui.ImageLE.textChanged.connect(self.changed_RefImg)
        self.ui.Imagezoomslider.valueChanged.connect(self.on_Imagezoomslider)
        self.ui.ImageZoomComboBox.currentTextChanged.connect(self.on_Imagezoom)
        self.ui.ImageZoombutton.clicked.connect(self.get_Imagezoom)
        self.ui.Imagezoomslider.sliderReleased.connect(self.disable_Imagezoomslider)

        self.ui.ExportRefImgFilebutton.clicked.connect(self.ExportImage)
        self.ui.SaveImagebutton.clicked.connect(self.save_image_with_myexplorer)
        self.ui.SaveAsImagebutton.clicked.connect(self.save_image_as_with_myexplorer)

        # -------------------------
        # UI defaults
        # -------------------------
        self.ui.RefImgzoomslider.hide()
        self.ui.Imagezoomslider.hide()

        self.rubberBand = ResizableRubberBand(self)
        self.rubberBand.hide()

        self._init_subprocess_return_controls()

        # ÃƒÂ°Ã…Â¸Ã¢â‚¬ÂÃ‚Â¥ mark UI ready
        self._ui_ready = True

    def _init_crop_prompt_dialog(self):
        self.crop_prompt_dialog = qtw.QDialog(self)
        self.crop_prompt_dialog.setWindowTitle("Finalize Crop")
        self.crop_prompt_dialog.setWindowFlags(
            self.crop_prompt_dialog.windowFlags() | qtc.Qt.Tool | qtc.Qt.WindowStaysOnTopHint
        )
        self.crop_prompt_dialog.setWindowModality(qtc.Qt.NonModal)

        layout = qtw.QVBoxLayout(self.crop_prompt_dialog)
        message = qtw.QLabel("Resize the handles as needed, then confirm the crop.")
        message.setWordWrap(True)
        layout.addWidget(message)

        button_box = qtw.QDialogButtonBox(
            qtw.QDialogButtonBox.Apply | qtw.QDialogButtonBox.Cancel
        )
        apply_button = button_box.button(qtw.QDialogButtonBox.Apply)
        cancel_button = button_box.button(qtw.QDialogButtonBox.Cancel)
        apply_button.setText("Apply Crop")
        cancel_button.setText("Keep Editing")
        apply_button.clicked.connect(self.apply_crop_selection)
        cancel_button.clicked.connect(self.crop_prompt_dialog.hide)
        layout.addWidget(button_box)

    def _show_crop_prompt_dialog(self):
        if self.crop_prompt_dialog is None:
            self._init_crop_prompt_dialog()

        self.crop_prompt_dialog.show()
        self.crop_prompt_dialog.raise_()
        self.crop_prompt_dialog.activateWindow()

    def _init_project_status_widgets(self):
        self.workflow_tracker = ProjectWorkflowTracker(workspace_root=project_root)

        self.project_name_status_label = qtw.QLabel("Project: none")
        self.project_name_status_label.setMinimumWidth(180)

        self.workflow_status_label = qtw.QLabel("MyPixler 0/5 | Next: Source images captured")
        self.workflow_status_label.setMinimumWidth(360)

        self.project_overall_status_bar = qtw.QProgressBar()
        self.project_overall_status_bar.setRange(0, 100)
        self.project_overall_status_bar.setValue(0)
        self.project_overall_status_bar.setTextVisible(True)
        self.project_overall_status_bar.setFormat("Project 0%")
        self.project_overall_status_bar.setFixedWidth(140)
        self.project_overall_status_bar.setAlignment(Qt.AlignCenter)

        self.page_status_bar = qtw.QProgressBar()
        self.page_status_bar.setRange(0, 100)
        self.page_status_bar.setValue(0)
        self.page_status_bar.setTextVisible(True)
        self.page_status_bar.setFormat("Page 0%")
        self.page_status_bar.setFixedWidth(130)
        self.page_status_bar.setAlignment(Qt.AlignCenter)

        self.statusBar().addPermanentWidget(self.project_name_status_label)
        self.statusBar().addPermanentWidget(self.workflow_status_label)
        self.statusBar().addPermanentWidget(self.project_overall_status_bar)
        self.statusBar().addPermanentWidget(self.page_status_bar)

    def _shared_active_project_root(self):
        return self.shared_session_manager.get_active_project_root()

    def _start_active_project_sync(self):
        if self._active_project_sync_timer is None:
            self._active_project_sync_timer = qtc.QTimer(self)
            self._active_project_sync_timer.timeout.connect(self._sync_active_project_from_server)
            self._active_project_sync_timer.start(1000)
        self._sync_active_project_from_server()

    def _sync_active_project_from_server(self):
        shared_root = self._shared_active_project_root()
        if not shared_root or shared_root == self.current_project_root:
            return

        viewer = self.source_reader
        if viewer is not None and not self._path_is_within(viewer.pdf_path, shared_root):
            self._close_source_reader_automatically()
        self.current_project_root = shared_root
        self.view_source_document_action.setEnabled(bool(self._project_source_pdf(shared_root)))
        self._refresh_project_status(shared_root)

    def _project_source_pdf(self, project_root=None):
        active_root = project_root or self._shared_active_project_root() or self.current_project_root
        if not active_root:
            return ""
        return find_project_pdf_source(str(active_root))

    def view_source_document(self):
        source_path = self._project_source_pdf()
        if not source_path:
            qtw.QMessageBox.information(
                self,
                "Open Source Reader",
                "The active project does not have a PDF or TIFF source document.",
            )
            return False
        return self._open_pdf_source(source_path, floating=False)

    def _open_project_source_pdf_on_startup(self):
        qtw.QApplication.processEvents(qtc.QEventLoop.AllEvents, 50)
        viewer = self.source_reader
        if viewer is not None:
            viewer.show_reader()
            return True

        source_path = self._project_source_pdf()
        if not source_path:
            return False
        return self._open_pdf_source(source_path, floating=False)

    def _view_source_document_triggered(self, _checked=False):
        self.view_source_document()

    @staticmethod
    def _path_is_within(path, directory):
        try:
            return os.path.commonpath((os.path.abspath(path), os.path.abspath(directory))) == os.path.abspath(directory)
        except ValueError:
            return False

    def _sync_source_reader_visibility_action(self, visible):
        action = getattr(self, "source_reader_visibility_action", None)
        if action is None:
            return
        try:
            action.blockSignals(True)
            action.setChecked(bool(visible))
            action.blockSignals(False)
        except RuntimeError:
            return

    def _set_source_reader_visibility(self, visible):
        viewer = self.source_reader
        if viewer is None:
            if visible:
                self.view_source_document()
            return
        viewer.set_reader_visible(bool(visible))
        if visible and viewer.is_reader_floating():
            viewer.raise_()
            viewer.activateWindow()

    def _close_source_reader_automatically(self):
        viewer = self.source_reader
        if viewer is None:
            return
        self.source_reader = None
        viewer.close_automatically()
        self._sync_source_reader_visibility_action(False)
        self.source_reader_visibility_action.setEnabled(False)

    def _on_source_reader_destroyed(self, closed_viewer):
        if self.source_reader is not closed_viewer:
            return
        self.source_reader = None
        self._sync_source_reader_visibility_action(False)
        try:
            self.source_reader_visibility_action.setEnabled(False)
        except RuntimeError:
            pass

    def _on_pdf_source_loaded(self, viewer, pdf_path, page_count):
        if self.source_reader is not viewer:
            return
        self.pdf_source_path = os.path.abspath(pdf_path)
        self.pdf_page_count = int(page_count)
        self.statusBar().showMessage(
            f"Source document ready: {page_count} page{'s' if page_count != 1 else ''}",
            5000,
        )

    def _on_pdf_source_load_failed(self, viewer, message):
        if self.source_reader is not viewer:
            return
        self.pdf_source_path = ""
        self.pdf_page_count = 0
        qtw.QMessageBox.warning(
            self,
            "Open Source Document",
            f"Could not display the source document.\n\n{message}",
        )
        self._close_source_reader_automatically()

    def _open_pdf_source(self, pdf_path, floating=True):
        try:
            viewer = SourceReaderDock(pdf_path, self)
            self._close_source_reader_automatically()
            self.source_reader = viewer
            self.pdf_source_path = os.path.abspath(pdf_path)
            self.pdf_page_count = 0
            self.addDockWidget(qtc.Qt.DockWidgetArea.LeftDockWidgetArea, viewer)
            viewer.readerVisibilityChanged.connect(self._sync_source_reader_visibility_action)
            viewer.documentLoaded.connect(
                lambda loaded_path, page_count, active_viewer=viewer: self._on_pdf_source_loaded(
                    active_viewer,
                    loaded_path,
                    page_count,
                )
            )
            viewer.loadFailed.connect(
                lambda message, active_viewer=viewer: self._on_pdf_source_load_failed(
                    active_viewer,
                    message,
                )
            )
            viewer.destroyed.connect(
                lambda _object=None, closed_viewer=viewer: self._on_source_reader_destroyed(closed_viewer)
            )
            self.source_reader_visibility_action.setEnabled(True)
            viewer.show_reader()
            self.resizeDocks([viewer], [420], qtc.Qt.Horizontal)
            if floating:
                viewer.float_reader()
        except (RuntimeError, ValueError) as exc:
            self.pdf_source_path = ""
            self.pdf_page_count = 0
            qtw.QMessageBox.warning(
                self,
                "Open Source Document",
                f"Could not display the source document.\n\n{exc}",
            )
            return False
        return True

    def _format_module_workflow_status(self, module_name, snapshot):
        module_total = int(snapshot.get("module_total_count", 0))
        module_completed = int(snapshot.get("module_completed_count", 0))
        next_label = snapshot.get("module_next_label", "")

        if module_total <= 0:
            return f"{module_name} | No milestones configured"
        if next_label == "Complete":
            return f"{module_name} {module_completed}/{module_total} | Complete"
        return f"{module_name} {module_completed}/{module_total} | Next: {next_label}"

    def _page_number_from_path(self, path, fallback=None):
        candidate = str(path or "").strip()
        if not candidate:
            return max(1, int(fallback or getattr(self, "current_project_page", 1) or 1))

        stem = os.path.splitext(os.path.basename(candidate))[0]
        for pattern in (
            r"(?:^|[_\-\s])page[_\-\s]*(\d+)",
            r"(?:^|[_\-\s])p(?:age)?[_\-\s]*(\d+)",
            r"(\d+)$",
        ):
            match = re.search(pattern, stem, re.IGNORECASE)
            if match:
                return max(1, int(match.group(1)))

        return max(1, int(fallback or getattr(self, "current_project_page", 1) or 1))

    def _sync_project_page_state(self, page_path=None, project_milestone=None, page_milestone=None):
        page_number = self._page_number_from_path(page_path)
        if page_path and os.path.isfile(page_path):
            page_state = self.shared_session_manager.set_active_project_page_state(
                page_path,
                page_number=page_number,
                module_name="MyPixler",
            )
            page_number = page_state["page_number"]
        else:
            self.shared_session_manager.set_active_project_page(page_number)
        self.current_project_page = page_number

        payload = {
            'self.current_project_page': page_number,
        }

        if project_milestone is not None:
            self.current_project_milestone = str(project_milestone or '').strip()
            payload['self.current_project_milestone'] = self.current_project_milestone

        if page_milestone is not None:
            self.current_page_milestone = str(page_milestone or '').strip()
            payload['self.current_page_milestone'] = self.current_page_milestone

        active_root = self.current_project_root or self._shared_active_project_root() or self.projecthome
        base = os.path.join(active_root, 'Model', 'Project', 'Data', 'json')
        SessionManager(base).update('Session.json', payload)
        SessionManager(base).update('PixlerSession.json', payload)
        return page_number

    def _move_workflow_entries(self, workflow_dir, complete_dir):
        if not workflow_dir or not complete_dir:
            return

        os.makedirs(workflow_dir, exist_ok=True)
        os.makedirs(complete_dir, exist_ok=True)

        self._convert_workflow_png_to_indexed_tiff(workflow_dir)

        for item in os.listdir(workflow_dir):
            source = os.path.join(workflow_dir, item)
            destination = os.path.join(complete_dir, item)
            if os.path.exists(destination):
                if os.path.isdir(destination) and not os.path.islink(destination):
                    shutil.rmtree(destination)
                else:
                    os.remove(destination)
            shutil.move(source, destination)

    def _convert_workflow_png_to_indexed_tiff(self, workflow_dir):
        if not os.path.isdir(workflow_dir):
            return

        for item in os.listdir(workflow_dir):
            source = os.path.join(workflow_dir, item)
            if not os.path.isfile(source):
                continue
            stem, ext = os.path.splitext(item)
            if ext.lower() != ".png":
                continue

            target = os.path.join(workflow_dir, stem + ".tif")
            try:
                with pilimg.open(source) as img:
                    indexed = img.convert("L").convert("P", palette=pilimg.ADAPTIVE, colors=256)
                    indexed.save(target, "TIFF", dpi=(300, 300), compression="tiff_lzw")
                os.remove(source)
            except Exception as exc:
                print(f"[PIXLER] Could not convert intermediary PNG to TIFF: {source} ({exc})")

    def _refresh_project_status(self, candidate_path=None):
        snapshot = self.workflow_tracker.snapshot(
            "MyPixler",
            project_root=self.current_project_root,
            candidate_paths=(
                self._shared_active_project_root(),
                candidate_path,
                self.current_project_root,
                getattr(self, "refimgpath", ""),
                getattr(self, "imgpath", ""),
                getattr(self, "refimgdir", ""),
                getattr(self, "imagedir", ""),
                getattr(self, "workflow", ""),
                getattr(self, "session", ""),
            ),
        )

        project_root_value = snapshot.get("project_root")
        if project_root_value:
            self.current_project_root = project_root_value

        project_name = snapshot.get("project_name", "none")
        self.project_name_status_label.setText(f"Project: {project_name}")
        self.project_name_status_label.setToolTip(project_root_value or "No active project selected")

        completed_labels = snapshot.get("completed_labels", [])
        completed_text = ", ".join(completed_labels) if completed_labels else "None yet"
        project_percent = int(snapshot.get("project_percent", snapshot.get("overall_percent", 0)))
        page_percent = int(snapshot.get("page_percent", project_percent))
        completed_pages = int(snapshot.get("completed_pages", 0))
        total_pages = int(snapshot.get("total_pages", 0))
        overall_next = snapshot.get("overall_next_label", "")
        tooltip = (
            f"Project {project_percent}%\n"
            f"Page {page_percent}% ({completed_pages}/{total_pages})\n"
            f"Completed: {completed_text}\n"
            f"Next: {overall_next}"
        )

        self.workflow_status_label.setText(self._format_module_workflow_status("MyPixler", snapshot))
        self.workflow_status_label.setToolTip(tooltip)
        self.project_overall_status_bar.setValue(project_percent)
        self.project_overall_status_bar.setFormat(f"Project {project_percent}%")
        self.project_overall_status_bar.setToolTip(tooltip)
        self.page_status_bar.setValue(page_percent)
        self.page_status_bar.setFormat(f"Page {page_percent}%")
        self.page_status_bar.setToolTip(tooltip)

    def _record_project_milestone(self, milestone_key, candidate_path=None, details=None):
        project_root = self.workflow_tracker.resolve_project_root(
            self._shared_active_project_root(),
            candidate_path,
            self.current_project_root,
            getattr(self, "refimgpath", ""),
            getattr(self, "imgpath", ""),
            getattr(self, "refimgdir", ""),
            getattr(self, "imagedir", ""),
            getattr(self, "workflow", ""),
            getattr(self, "session", ""),
        )
        if not project_root:
            return None

        self.current_project_root = project_root
        self.workflow_tracker.ensure_tracking_state(project_root)
        self.workflow_tracker.record_milestone(
            project_root,
            milestone_key,
            module_name="MyPixler",
            details=details,
        )
        self._sync_project_page_state(project_root, project_milestone=milestone_key, page_milestone=milestone_key)
        self._refresh_project_status(project_root)
        return project_root

    def _workflow_definition_root(self):
        active_root = self.current_project_root or self._shared_active_project_root()
        for candidate in (self.projecthome, project_root, active_root):
            if not candidate:
                continue
            workflow_csv = os.path.join(candidate, WORKFLOW_DIRECTORY, PAGE_WORKFLOW_FILENAME)
            if os.path.isfile(workflow_csv):
                return candidate
        return self.projecthome

    def _workflow_step_for_method(self, method_name):
        active_root = self.current_project_root or self._shared_active_project_root() or self.projecthome
        context = self.workflow_tracker._load_project_context(active_root)
        page_section = context.get("CurrentSourceSection", "Front Matter")
        completed = self._completed_page_milestones(active_root, context)
        step = select_page_workflow_step(
            self._workflow_definition_root(),
            "MyPixler",
            method_name,
            page_section,
            completed,
        )
        if step is None:
            self.statusBar().showMessage(
                f"No pending MyPixler {method_name} step for {page_section}.",
                7000,
            )
        return step

    def _completed_page_milestones(self, active_root, context=None):
        context = context or self.workflow_tracker._load_project_context(active_root)
        page_number = max(
            1,
            int(context.get("CurrentProjectPage", getattr(self, "current_project_page", 1)) or 1),
        )
        state = self.workflow_tracker.load_tracking_state(active_root)
        page_state = state.get("page_milestones", {}).get(str(page_number), {})
        return {
            key
            for key, value in page_state.items()
            if isinstance(value, dict) and value.get("complete")
        } if isinstance(page_state, dict) else set()

    def _pending_dialog_workflow_steps(self, method_name, active_root):
        completed = self._completed_page_milestones(active_root)
        return [
            step
            for step in self._workflow_steps_for_method(method_name)
            if step.milestone_name not in completed
        ]

    def _dialog_workflow_completion(self, method_name, active_root):
        steps = self._workflow_steps_for_method(method_name)
        pending_steps = self._pending_dialog_workflow_steps(method_name, active_root)
        pending_names = {step.milestone_name for step in pending_steps}
        completed_steps = [
            step for step in steps if step.milestone_name not in pending_names
        ]
        return steps, completed_steps, pending_steps

    @staticmethod
    def _completed_step_report(completed_steps):
        return "\n".join(
            f"{step.sequence} - {step.milestone_name}"
            for step in completed_steps
        )

    def _report_completed_dialog_loop(self, title, completed_steps):
        completed_report = PixlerMain._completed_step_report(completed_steps)
        message = (
            "This extraction function is complete.\n\n"
            "Completed milestones:\n"
            f"{completed_report}\n\n"
            "To re-enable a dialog, open MyServer > Project Settings > "
            "Milestone Settings and uncheck Complete for its milestone."
        )
        self.statusBar().showMessage(
            f"{title} is complete: "
            + ", ".join(step.sequence for step in completed_steps),
            10000,
        )
        PixlerMain._center_next_message_box(self)
        qtw.QMessageBox.information(self, title, message)

    @staticmethod
    def _prepare_extract_dialog(dialog, ui):
        ui.MilestoneOverrideCheckBox.setChecked(False)
        ui.MilestoneOverrideCheckBox.hide()

    @staticmethod
    def _center_dialog_on_parent_screen(dialog):
        parent = dialog.parentWidget()
        screen = parent.screen() if parent is not None else qtw.QApplication.primaryScreen()
        if screen is None:
            return
        available = screen.availableGeometry()
        target = parent.frameGeometry().center() if parent is not None else available.center()
        frame = dialog.frameGeometry()
        frame.moveCenter(target)
        left = min(max(frame.left(), available.left()), available.right() - frame.width() + 1)
        top = min(max(frame.top(), available.top()), available.bottom() - frame.height() + 1)
        dialog.move(left, top)

    @staticmethod
    def _center_next_message_box(parent):
        def center_message_box():
            for widget in qtw.QApplication.topLevelWidgets():
                if isinstance(widget, qtw.QMessageBox) and widget.isVisible():
                    PixlerMain._center_dialog_on_parent_screen(widget)

        qtc.QTimer.singleShot(0, center_message_box)

    def _refresh_extract_completion_progress(self, active_root, ui=None, label="Complete"):
        refresh_status = getattr(self, "_refresh_project_status", None)
        if callable(refresh_status):
            refresh_status(active_root)
        if ui is not None:
            ui.ProgressLabel.setText(label)
        qtw.QApplication.processEvents(qtc.QEventLoop.AllEvents, 50)

    def _show_extraction_progress(self, parent, label):
        progress = qtw.QProgressDialog(label, "", 0, 0, parent)
        progress.setWindowTitle("Extracting")
        progress.setCancelButton(None)
        progress.setAutoClose(False)
        progress.setAutoReset(False)
        progress.setMinimumDuration(0)
        progress.setWindowModality(qtc.Qt.NonModal)
        progress.setAttribute(qtc.Qt.WA_DeleteOnClose, True)
        progress.show()
        qtw.QApplication.processEvents(qtc.QEventLoop.AllEvents, 50)
        return progress

    @staticmethod
    def _close_extraction_progress(progress):
        if progress is None:
            return
        progress.close()
        qtw.QApplication.processEvents(qtc.QEventLoop.AllEvents, 50)

    def _workflow_steps_for_method(self, method_name):
        steps, _notes = load_page_workflow(self._workflow_definition_root())
        section_order = {
            "FrontSection": 0,
            "MiddleSections": 1,
            "VerseSections": 2,
            "BackSection": 3,
        }
        matching_steps = [
            step
            for step in steps
            if step.module == "MyPixler" and step.method == method_name
        ]
        return sorted(
            matching_steps,
            key=lambda step: section_order.get(step.page_section, len(section_order)),
        )

    def _workflow_step_paths(self, step):
        active_root = self.current_project_root or self._shared_active_project_root() or self.projecthome
        return (
            resolve_page_workflow_path(active_root, step.workflow_source),
            resolve_page_workflow_path(active_root, step.complete_destination),
            resolve_page_workflow_path(active_root, step.workflow_handshake),
        )

    @staticmethod
    def _first_workflow_file(workflow_dir):
        if not workflow_dir or not os.path.isdir(workflow_dir):
            return ""
        for name in sorted(os.listdir(workflow_dir)):
            candidate = os.path.join(workflow_dir, name)
            if os.path.isfile(candidate):
                return candidate
        return ""

    @staticmethod
    def _first_workflow_source_document(workflow_dir):
        if not workflow_dir or not os.path.isdir(workflow_dir):
            return ""
        for name in sorted(os.listdir(workflow_dir)):
            candidate = os.path.join(workflow_dir, name)
            if (
                os.path.isfile(candidate)
                and os.path.splitext(name)[1].lower() in SUPPORTED_SOURCE_EXTENSIONS
            ):
                return candidate
        return ""

    def _finish_page_workflow_step(self, step, details=None, stage_source=False):
        active_root = self.current_project_root or self._shared_active_project_root() or self.projecthome
        advance_page_workflow_files(active_root, step, stage_source=stage_source)
        context = self.workflow_tracker._load_project_context(active_root)
        page_number = max(
            1,
            int(
                context.get(
                    "CurrentProjectPage",
                    context.get(
                        "ProjectPageNumber",
                        getattr(self, "current_project_page", 1),
                    ),
                )
                or 1
            ),
        )
        self.current_project_page = page_number
        self.workflow_tracker.record_page_milestone(
            active_root,
            page_number,
            step.milestone_name,
            module_name="MyPixler",
            details=details,
        )
        self._sync_project_page_state(
            active_root,
            project_milestone=step.milestone_name,
            page_milestone=step.milestone_name,
        )
        self._refresh_project_status(active_root)
        qtw.QApplication.processEvents(qtc.QEventLoop.AllEvents, 50)


    def _init_subprocess_return_controls(self):
        if not self.subprocess_mode or not self.subprocess_return_path:
            return

        self.return_button = qtw.QPushButton("Return")
        self.return_button.setEnabled(False)
        self.return_button.setFixedHeight(24)
        self.return_button.setStyleSheet(
            "QPushButton { background-color: #4a4a4a; color: white; border: 1px solid #2d2d2d; padding: 2px 8px; }"
            "QPushButton:hover { background-color: #5a5a5a; }"
            "QPushButton:pressed { background-color: #3b3b3b; }"
        )
        self.return_button.setToolTip(self.subprocess_return_path)
        self.return_button.clicked.connect(self.returnToCaller)
        self.statusBar().addPermanentWidget(self.return_button)

        self.statusBar().showMessage(
            f"Subprocess return ready: {self.subprocess_return_path}"
        )

    def setStack(self, tiffCaptureHandle):
            """ Set the scene's current TIFF image stack to the input TiffCapture object.
            Raises a RuntimeError if the input tiffCaptureHandle has type other than TiffCapture.
            :type tiffCaptureHandle: TiffCapture
            """
            if type(tiffCaptureHandle) is not tiffcapture.TiffCapture:
                raise RuntimeError("MultiPageTIFFViewerQt.setImageStack: Argument must be a TiffCapture object.")
            self._tiffCaptureHandle = tiffCaptureHandle
            self.showFrame(0)

    def loadStackFromFile(self, fileName=''):
        fileName = str(fileName)

        if not fileName or not os.path.isfile(fileName):
            print("[STACK LOAD] Invalid file")
            return

        print(f"[STACK LOAD] Requested: {fileName}")

        self._stack_path = fileName

        # -------------------------
        # Thread setup
        # -------------------------
        self._stack_thread = qtc.QThread(self)
        self._stack_worker = TiffStackWorker(fileName)

        self._stack_worker.moveToThread(self._stack_thread)

        self._stack_thread.started.connect(self._stack_worker.run)

        self._stack_worker.progress.connect(self.on_stack_progress)
        self._stack_worker.finished.connect(self.on_stack_loaded)
        self._stack_worker.error.connect(self.on_stack_error)

        # cleanup
        self._stack_worker.finished.connect(self._stack_thread.quit)
        self._stack_worker.finished.connect(self._stack_worker.deleteLater)
        self._stack_worker.error.connect(self._stack_thread.quit)
        self._stack_worker.error.connect(self._stack_worker.deleteLater)
        self._stack_thread.finished.connect(self._stack_thread.deleteLater)
        self._stack_thread.finished.connect(self._on_stack_thread_finished)

        self._stack_thread.start()

        self.statusBar().showMessage("Loading TIFF reference image...")
        self._show_progress(0)

    def on_stack_progress(self, value):
        print(f"[STACK] {value}%")
        self._set_progress_percent(value)
        self.statusBar().showMessage(f"Loading TIFF reference image... {int(value)}%")

    def on_stack_loaded(self, handle):
        print("[STACK] Loaded")

        self._hide_progress(100)

        # TiffStackWorker currently emits the first frame as a QImage.
        # Preserve that full-resolution frame directly instead of routing it
        # back through a second ndarray->QImage conversion step.
        self.qimage = handle
        self.refimgqimage = self.qimage
        self.refimgpixmap = qtg.QPixmap.fromImage(self.refimgqimage)
        if self.refimgpath:
            self.refimgdir = os.path.dirname(self.refimgpath)
        self._update_pixler_session_paths()
        self._sync_project_page_state(self.refimgpath)

        # display
        self.ui.RefImg.setPixmap(
            self.refimgpixmap.scaled(
                self.ui.RefImg.size(),
                qtc.Qt.KeepAspectRatio,
                transformMode=qtc.Qt.SmoothTransformation
            )
        )

        self._refresh_project_status(self.refimgpath or self.refimgdir)
        self.statusBar().showMessage("Reference TIFF loaded.")
        print("[STACK] Render complete")

    def on_stack_error(self, msg):
        print(f"[STACK ERROR] {msg}")
        self._hide_progress()
        self.statusBar().showMessage(f"TIFF load failed: {msg}", 5000)

    def _on_stack_thread_finished(self):
        self._stack_thread = None
        self._stack_worker = None

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
        self.qimage = qimage2ndarray.array2qimage(self.frame, normalize=False)

    def showImage(self,imgfilename):
        #self.imgfilename = self.imgpath
        file = qtc.QFile(imgfilename)
        filestr = os.path.basename(imgfilename)
        filesplit = os.path.splitext(filestr)
        filename = filesplit[0]
        fileext = filesplit[1]

        if file.open(qtc.QIODevice.ReadOnly):
            info = qtc.QFileInfo(imgfilename)

            if fileext == '.tif':
                self.loadStackFromFile(imgfilename)
                self.showFrame(0)
                self.imageqimage = qtg.QImage(self.qimage)
                self.imagepixmap = qtg.QPixmap.fromImage(self.imageqimage)
            # else:
            #     self.imagepixmap = qtg.QPixmap(self.imagepath)
            else:
                self.imagepixmap = qtg.QPixmap(imgfilename)
        file.close()

        if self.imagepixmap.isNull():
            return

        self.on_Imagezoom()

        base = os.path.join(self.projecthome, 'Model', 'Project', 'Data', 'json')

        self.imagedir = os.path.dirname(imgfilename)
        self.ui.ImageLE.setText(filestr)

        SessionManager(base).update('PixlerSession.json', {
            'self.imagepath': os.path.normpath(self.imagepath),
            'self.imagedir': os.path.normpath(self.imagedir),
        })
        self._sync_project_page_state(self.imagepath)

        self.imagefileList = []
        for i in os.listdir(self.imagedir):
            ipath = os.path.normpath(os.path.join(self.imagedir, i))
            if os.path.isfile(ipath) and i.lower().endswith(('.png', '.jpg', '.jpeg', '.tif')):
                self.imagefileList.append(ipath)

        self.sortImgFiles()

    def closeEvent(self,event):

        if self.RefImgchangesSaved:

            event.accept()

        else:

            popup = QMessageBox(self)

            popup.setIcon(QMessageBox.Warning)

            popup.setText("The document has been modified")

            popup.setInformativeText("Do you want to save your changes?")

            popup.setStandardButtons(QMessageBox.Save   |
                                      QMessageBox.Cancel |
                                      QMessageBox.Discard)

            popup.setDefaultButton(QMessageBox.Save)

            answer = popup.exec_()

            if answer == QMessageBox.Save:
                self.save()

            elif answer == QMessageBox.Discard:
                event.accept()

            else:
                event.ignore()

        if event.isAccepted():
            self._close_source_reader_automatically()

# Application Controllers

    # Workflow Controllers

    # Page workflow: Sequence SSHF; MilestoneName src_pages_front_matter_staged.
    # Page workflow: Sequence SSHM; MilestoneName src_pages_middle_matter_staged.
    # Page workflow: Sequence SSHV; MilestoneName src_pages_verses_staged.
    # Page workflow: Sequence SSHB; MilestoneName src_pages_back_matter_staged.
    def actionstage_pdf(self):
        active_root = self.current_project_root or self._shared_active_project_root() or self.projecthome
        workflow_step = self._workflow_step_for_method("actionstage_pdf")
        step_paths = self._workflow_step_paths(workflow_step) if workflow_step else ("", "", "")
        section_source = step_paths[0]
        stage_section = bool(self._first_workflow_source_document(section_source))
        source_dir = (
            section_source
            if stage_section
            else project_staged_pdf_workflow_directory(active_root)
        )
        destination_dir = (
            step_paths[1]
            if stage_section
            else project_staged_pdf_complete_directory(active_root)
        )
        dialog = qtw.QDialog(self if isinstance(self, qtw.QWidget) else None)
        ui = Ui_StageDialog()
        ui.setupUi(dialog)
        ui.SourceLineEdit.setText(source_dir)
        ui.DestinationLineEdit.setText(destination_dir)

        def select_directory(line_edit, title):
            selected = qtw.QFileDialog.getExistingDirectory(self, title, line_edit.text())
            if selected:
                line_edit.setText(selected)

        def set_defaults_enabled(checked):
            ui.SourceButton.setEnabled(not checked)
            ui.DestinationButton.setEnabled(not checked)
            if checked:
                ui.SourceLineEdit.setText(source_dir)
                ui.DestinationLineEdit.setText(destination_dir)

        ui.defaultsrcBox.toggled.connect(set_defaults_enabled)
        ui.SourceButton.clicked.connect(
            lambda: select_directory(ui.SourceLineEdit, "Select staged PDF source folder")
        )
        ui.DestinationButton.clicked.connect(
            lambda: select_directory(ui.DestinationLineEdit, "Select staged PDF destination folder")
        )
        dialog.adjustSize()
        PixlerMain._center_dialog_on_parent_screen(dialog)
        if dialog.exec_() != qtw.QDialog.Accepted:
            return

        try:
            if stage_section:
                source_path = self._first_workflow_source_document(ui.SourceLineEdit.text())
                if not source_path:
                    raise ValueError(f"No staged section PDF exists in: {ui.SourceLineEdit.text()}")
                destination_path = os.path.join(
                    ui.DestinationLineEdit.text(),
                    os.path.basename(source_path),
                )
                if os.path.exists(destination_path) and not ui.OverrideCheckBox.isChecked():
                    raise FileExistsError(f"Staged section PDF already exists: {destination_path}")
                if os.path.exists(destination_path) and ui.OverrideCheckBox.isChecked():
                    if not self._confirm_extract_overwrite(
                        dialog,
                        ui.DestinationLineEdit.text(),
                    ):
                        return
                if ui.defaultsrcBox.isChecked():
                    self._finish_page_workflow_step(
                        workflow_step,
                        details={"source": "actionstage_pdf"},
                        stage_source=True,
                    )
                else:
                    selected_step = replace(
                        workflow_step,
                        workflow_source=os.path.relpath(ui.SourceLineEdit.text(), active_root),
                        complete_destination=os.path.relpath(ui.DestinationLineEdit.text(), active_root),
                    )
                    self._finish_page_workflow_step(
                        selected_step,
                        details={"source": "actionstage_pdf_override"},
                        stage_source=True,
                    )
                staged_path = destination_path
            else:
                selected_destination = ui.DestinationLineEdit.text()
                destination_has_files = (
                    os.path.isdir(selected_destination)
                    and bool(os.listdir(selected_destination))
                )
                if (
                    ui.OverrideCheckBox.isChecked()
                    and destination_has_files
                    and not self._confirm_extract_overwrite(dialog, selected_destination)
                ):
                    return
                staged_path = complete_project_staged_pdf_handoff(
                    active_root,
                    source_dir=ui.SourceLineEdit.text(),
                    destination_dir=ui.DestinationLineEdit.text(),
                    override=ui.OverrideCheckBox.isChecked(),
                )
        except (OSError, ValueError) as exc:
            PixlerMain._center_next_message_box(self)
            qtw.QMessageBox.warning(
                self,
                "Stage Source Document",
                f"The staged MyServer PDF could not be accepted into MyPixler.\n\n{exc}",
            )
            return
        self.statusBar().showMessage(f"Staged source PDF accepted: {staged_path}", 5000)

    # Page workflow: Sequence ES2F; MilestoneName src_pages_front_matter_extracted.
    # Page workflow: Sequence ES2M; MilestoneName src_pages_middle_matter_extracted.
    # Page workflow: Sequence EM2B; MilestoneName middle_matter_pages_extracted_to_books.
    # Page workflow: Sequence ES2V; MilestoneName src_pages_verses_extracted.
    # Page workflow: Sequence EV2B; MilestoneName verse_pages_extracted_to_books.
    # Page workflow: Sequence ES2B; MilestoneName src_pages_back_matter_extracted.
    def actionextract_pdf(self):
        workflow_step = self._workflow_step_for_method("actionextract_pdf")
        if workflow_step:
            workflow_source, _complete_folder, _workflow_handshake = self._workflow_step_paths(workflow_step)
            if workflow_step.sequence in {"EM2B", "EV2B"}:
                return self.actionextract_book_pages(workflow_step)
            if self._first_workflow_source_document(workflow_source):
                return self.actionextract_staged_pdf_pages(workflow_step)
        return self._extract_source_pdf_sections()

    @staticmethod
    def _run_non_modal_dialog(dialog):
        dialog.setWindowModality(qtc.Qt.NonModal)
        dialog.setModal(False)
        event_loop = qtc.QEventLoop(dialog)
        dialog.finished.connect(event_loop.quit)
        dialog.show()
        PixlerMain._center_dialog_on_parent_screen(dialog)
        dialog.raise_()
        dialog.activateWindow()
        event_loop.exec_()
        return dialog.result()

    @staticmethod
    def _extract_dialog_state_manager(active_root):
        return SessionManager(
            os.path.join(active_root, "Model", "Project", "Data", "json")
        )

    def _load_extract_dialog_state(self, active_root):
        value = self._extract_dialog_state_manager(active_root).values(
            "PixlerSession.json",
            ["self.pdf_extraction_state"],
        ).get("self.pdf_extraction_state")
        return value if isinstance(value, dict) else {}

    def _save_extract_dialog_state(self, active_root, state):
        self._extract_dialog_state_manager(active_root).update(
            "PixlerSession.json",
            {"self.pdf_extraction_state": state},
        )

    @staticmethod
    def _confirm_extract_overwrite(parent, destination, preserved_paths=()):
        preserved = {
            os.path.normcase(os.path.abspath(path)) for path in preserved_paths
        }
        existing = [
            os.path.join(destination, name)
            for name in os.listdir(destination)
        ] if os.path.isdir(destination) else []
        replaceable = [
            path for path in existing
            if os.path.normcase(os.path.abspath(path)) not in preserved
        ]
        if not replaceable:
            return True
        PixlerMain._center_next_message_box(parent)
        response = qtw.QMessageBox.warning(
            parent,
            "Overwrite Existing Extraction",
            f"{len(replaceable)} existing item(s) in the destination will be replaced. Continue?",
            qtw.QMessageBox.Yes | qtw.QMessageBox.No,
            qtw.QMessageBox.No,
        )
        return response == qtw.QMessageBox.Yes

    def _install_extract_context_menu(self, dialog, ui, skip_result, skip_callback=None):
        def show_context_menu(position):
            menu = qtw.QMenu(dialog)
            focused = qtw.QApplication.focusWidget()
            undo_action = menu.addAction("Undo")
            redo_action = menu.addAction("Redo")
            undo_action.setEnabled(isinstance(focused, qtw.QLineEdit) and focused.isUndoAvailable())
            redo_action.setEnabled(isinstance(focused, qtw.QLineEdit) and focused.isRedoAvailable())
            menu.addSeparator()
            skip_action = menu.addAction("Skip")
            selected = menu.exec_(dialog.mapToGlobal(position))
            if selected == undo_action and isinstance(focused, qtw.QLineEdit):
                focused.undo()
            elif selected == redo_action and isinstance(focused, qtw.QLineEdit):
                focused.redo()
            elif selected == skip_action:
                if skip_callback is None:
                    dialog.done(skip_result)
                else:
                    skip_callback()

        dialog.customContextMenuRequested.connect(show_context_menu)

    @staticmethod
    def _book_stage_root(path):
        normalized_path = os.path.abspath(path)
        if os.path.basename(normalized_path).lstrip("_").startswith("book_"):
            return os.path.dirname(normalized_path)
        return normalized_path

    @classmethod
    def _book_stage_directories(cls, configured_path, reference_root=None):
        stage_root = cls._book_stage_root(configured_path)
        if not os.path.isdir(stage_root):
            return []
        directories = [
            os.path.join(stage_root, name)
            for name in os.listdir(stage_root)
            if name.startswith("book_")
            and os.path.isdir(os.path.join(stage_root, name))
        ]
        if not reference_root:
            return sorted(directories)
        reference_order = {
            normalize_book_folder(item.get("BookMarkdown")): index
            for index, item in enumerate(load_book_references(reference_root))
        }
        return sorted(
            directories,
            key=lambda path: (
                reference_order.get(os.path.basename(path), len(reference_order)),
                os.path.basename(path),
            ),
        )

    def _sync_extraction_book_session(self, active_root, book_folder):
        reference = find_book_reference(active_root, book_folder)
        if reference is None:
            reference = find_book_reference(self.projecthome, book_folder)
        if reference is None:
            return {}
        values = book_session_values(reference)
        PixlerMain._extract_dialog_state_manager(active_root).update("Session.json", values)
        return values

    def _book_extraction_source(self, active_root, workflow_step, workflow_source):
        if PixlerMain._first_workflow_source_document(workflow_source):
            return workflow_source
        source_root = self._book_stage_root(workflow_source)
        for candidate in self._workflow_steps_for_method("actionextract_pdf"):
            if candidate.sequence == workflow_step.sequence:
                continue
            candidate_handshake = resolve_page_workflow_path(
                active_root,
                candidate.workflow_handshake,
            )
            if os.path.normcase(self._book_stage_root(candidate_handshake)) != os.path.normcase(source_root):
                continue
            candidate_complete = resolve_page_workflow_path(
                active_root,
                candidate.complete_destination,
            )
            if PixlerMain._first_workflow_source_document(candidate_complete):
                return candidate_complete
        return workflow_source

    @staticmethod
    def _last_extracted_book_page(book_destinations, book_states, current_index):
        for previous_index in range(current_index - 1, -1, -1):
            previous_name = os.path.basename(book_destinations[previous_index])
            previous_state = book_states.get(previous_name, {})
            if previous_state.get("completion_source") != "extraction":
                continue
            try:
                return max(int(previous_state.get("last_page", 0) or 0), 0)
            except (TypeError, ValueError):
                return 0
        return 0

    @staticmethod
    def _normalize_extract_status(saved):
        status = str(saved.get("status", "pending") or "pending").lower()
        if status == "extracted":
            saved["status"] = "complete"
            saved.setdefault("completion_source", "extraction")
        elif status == "skipped":
            saved["status"] = "complete"
            saved.setdefault("completion_source", "skip")
        elif status != "complete":
            saved["status"] = "pending"
            saved.pop("completion_source", None)
        return saved["status"]

    def actionextract_book_pages(self, workflow_step):
        active_root = self.current_project_root or self._shared_active_project_root() or self.projecthome
        completed_milestones = (
            self._completed_page_milestones(active_root)
            if hasattr(self, "_completed_page_milestones")
            else set()
        )
        if workflow_step.milestone_name in completed_milestones:
            PixlerMain._report_completed_dialog_loop(
                self,
                f"{workflow_step.page_section} Book Extraction",
                [workflow_step],
            )
            return []
        workflow_source, complete_folder, workflow_handshake = self._workflow_step_paths(workflow_step)
        extraction_source = PixlerMain._book_extraction_source(
            self,
            active_root,
            workflow_step,
            workflow_source,
        )
        if not PixlerMain._first_workflow_source_document(extraction_source):
            PixlerMain._center_next_message_box(self)
            qtw.QMessageBox.warning(
                self,
                "Extract Book Pages",
                "No PDF source is available for this book-extraction step or its predecessor.",
            )
            return []
        book_destinations = self._book_stage_directories(
            complete_folder,
            reference_root=active_root,
        )
        if not book_destinations:
            book_destinations = self._book_stage_directories(
                complete_folder,
                reference_root=self.projecthome,
            )
        if not book_destinations:
            PixlerMain._center_next_message_box(self)
            qtw.QMessageBox.warning(
                self,
                "Extract Book Pages",
                f"No generated book folders are available in:\n{self._book_stage_root(complete_folder)}",
            )
            return []

        state = self._load_extract_dialog_state(active_root)
        workflow_states = state.setdefault("book_extractions", {})
        workflow_state = workflow_states.setdefault(workflow_step.sequence, {})
        book_states = workflow_state.setdefault("books", {})
        for saved_state in book_states.values():
            if isinstance(saved_state, dict):
                PixlerMain._normalize_extract_status(saved_state)
        all_books_were_complete = bool(book_destinations) and all(
            book_states.get(os.path.basename(path), {}).get("status") == "complete"
            for path in book_destinations
        )
        if workflow_state.get("milestone_complete") or all_books_were_complete:
            for saved_state in book_states.values():
                if isinstance(saved_state, dict):
                    saved_state["status"] = "pending"
                    saved_state.pop("completion_source", None)
            workflow_state["milestone_complete"] = False

        pending_indices = [
            index
            for index, path in enumerate(book_destinations)
            if book_states.get(os.path.basename(path), {}).get("status") != "complete"
        ]
        if not pending_indices:
            return []
        requested_index = min(
            max(int(workflow_state.get("book_index", 0) or 0), 0),
            len(book_destinations) - 1,
        )
        current_position = next(
            (
                position
                for position, book_index in enumerate(pending_indices)
                if book_index >= requested_index
            ),
            0,
        )
        previous_result = qtw.QDialog.Accepted + 1
        next_result = previous_result + 1
        skip_result = next_result + 1
        dialog = qtw.QDialog(self if isinstance(self, qtw.QWidget) else None)
        ui = Ui_ExtractDialog()
        ui.setupUi(dialog)
        PixlerMain._prepare_extract_dialog(dialog, ui)
        self._install_extract_context_menu(dialog, ui, skip_result)
        ui.HelpButton.clicked.connect(lambda: show_help(dialog, "MyPixler"))
        ui.PreviousButton.clicked.connect(lambda: dialog.done(previous_result))
        ui.NextButton.clicked.connect(lambda: dialog.done(next_result))
        ui.SkipButton.clicked.connect(lambda: dialog.done(skip_result))
        ui.buttonBox.button(qtw.QDialogButtonBox.Ok).setText("Extract Book")
        ui.SourceLineEdit.setText(extraction_source)
        ui.SourceButton.setEnabled(False)
        ui.defaultsrcBox.hide()
        ui.MakeDefaultCheckBox.hide()
        extracted_paths = []

        while True:
            current_index = pending_indices[current_position]
            destination = book_destinations[current_index]
            book_name = os.path.basename(destination)
            book_reference = find_book_reference(active_root, book_name)
            if book_reference is None:
                book_reference = find_book_reference(self.projecthome, book_name)
            book_markdown = (
                str(book_reference.get("BookMarkdown", ""))
                if book_reference is not None
                else f"_{book_name}"
            )
            PixlerMain._sync_extraction_book_session(self, active_root, book_name)
            saved = book_states.setdefault(book_name, {})
            prior_end = PixlerMain._last_extracted_book_page(
                book_destinations,
                book_states,
                current_index,
            )
            dialog.setWindowTitle(f"Extract {workflow_step.page_section}: {book_name}")
            saved_source = str(saved.get("source", extraction_source))
            if not PixlerMain._first_workflow_source_document(saved_source):
                saved_source = extraction_source
            ui.SourceLineEdit.setText(saved_source)
            ui.DestinationLineEdit.setText(str(saved.get("destination", destination)))
            ui.FirstPageLineEdit.setText(str(saved.get("first_page", prior_end + 1)))
            ui.LastPageLineEdit.setText(str(saved.get("last_page", prior_end + 1)))
            ui.ProgressLabel.setText(
                f"Book {current_index + 1} of {len(book_destinations)}: {book_name}"
                f" ({book_markdown})"
                f" | {saved.get('status', 'pending')}"
            )
            ui.PreviousButton.setEnabled(current_position > 0)
            ui.NextButton.setEnabled(current_position < len(pending_indices) - 1)
            result = self._run_non_modal_dialog(dialog)
            saved.update({
                "source": ui.SourceLineEdit.text(),
                "destination": ui.DestinationLineEdit.text(),
                "first_page": ui.FirstPageLineEdit.text(),
                "last_page": ui.LastPageLineEdit.text(),
            })
            workflow_state["book_index"] = current_index
            self._save_extract_dialog_state(active_root, state)

            if result == qtw.QDialog.Rejected:
                return extracted_paths
            if result == previous_result:
                current_position = max(0, current_position - 1)
                continue
            if result == next_result:
                current_position = min(len(pending_indices) - 1, current_position + 1)
                continue
            if result == skip_result:
                PixlerMain._center_next_message_box(dialog)
                response = qtw.QMessageBox.question(
                    dialog,
                    "Skip Book Extraction",
                    "Skip this book for now? It will remain pending.",
                    qtw.QMessageBox.Yes | qtw.QMessageBox.Cancel,
                    qtw.QMessageBox.Cancel,
                )
                if response == qtw.QMessageBox.Cancel:
                    continue
                saved["status"] = "pending"
                saved.pop("completion_source", None)
                self._save_extract_dialog_state(active_root, state)
            else:
                destination_path = ui.DestinationLineEdit.text()
                os.makedirs(destination_path, exist_ok=True)
                if not self._confirm_extract_overwrite(dialog, destination_path):
                    continue
                progress = PixlerMain._show_extraction_progress(
                    self,
                    dialog,
                    f"Extracting pages for {book_name}...",
                )
                try:
                    for name in os.listdir(destination_path):
                        path = os.path.join(destination_path, name)
                        if os.path.isdir(path) and not os.path.islink(path):
                            shutil.rmtree(path)
                        else:
                            os.remove(path)
                    book_paths = extract_pdf_source_pages(
                        ui.SourceLineEdit.text(),
                        destination_path,
                        ui.FirstPageLineEdit.text(),
                        ui.LastPageLineEdit.text(),
                    )
                except (OSError, ValueError) as exc:
                    PixlerMain._center_next_message_box(dialog)
                    qtw.QMessageBox.warning(
                        dialog,
                        "Extract Book Pages",
                        f"Could not extract pages for {book_name}.\n\n{exc}",
                    )
                    continue
                finally:
                    PixlerMain._close_extraction_progress(progress)
                extracted_paths.extend(book_paths)
                saved["status"] = "complete"
                saved["completion_source"] = "extraction"
                self._save_extract_dialog_state(active_root, state)

            current_position += 1
            if current_position >= len(pending_indices):
                break

        incomplete_books = [
            os.path.basename(path)
            for path in book_destinations
            for book_state in (book_states.get(os.path.basename(path), {}),)
            if book_state.get("status") != "complete"
        ]
        if incomplete_books:
            workflow_state["book_index"] = next(
                (
                    index
                    for index, path in enumerate(book_destinations)
                    if os.path.basename(path) in incomplete_books
                ),
                0,
            )
            self._save_extract_dialog_state(active_root, state)
            self.statusBar().showMessage(
                f"Book extraction paused with {len(incomplete_books)} book(s) pending.",
                7000,
            )
            return extracted_paths

        source_root = self._book_stage_root(workflow_source)
        complete_root = self._book_stage_root(complete_folder)
        handshake_root = self._book_stage_root(workflow_handshake)
        aggregate_step = replace(
            workflow_step,
            workflow_source=os.path.relpath(source_root, active_root),
            complete_destination=os.path.relpath(complete_root, active_root),
            workflow_handshake=os.path.relpath(handshake_root, active_root),
        )
        if extracted_paths:
            self._finish_page_workflow_step(
                aggregate_step,
                details={
                    "source": "actionextract_book_pages",
                    "book_count": len(book_destinations),
                    "page_count": len(extracted_paths),
                },
            )
        workflow_state["milestone_complete"] = True
        workflow_state["book_index"] = 0
        self._save_extract_dialog_state(active_root, state)
        self.statusBar().showMessage(
            f"Extracted {len(extracted_paths)} pages into {len(book_destinations)} book folders.",
            7000,
        )
        PixlerMain._report_completed_dialog_loop(
            self,
            f"{workflow_step.page_section} Book Extraction",
            [workflow_step],
        )
        return extracted_paths

    def _extract_source_pdf_sections(self):
        active_root = self.current_project_root or self._shared_active_project_root() or self.projecthome
        configured_steps, completed_steps, stage_steps = (
            PixlerMain._dialog_workflow_completion(
                self,
                "actionstage_pdf",
                active_root,
            )
        )
        if len(configured_steps) < 4:
            PixlerMain._center_next_message_box(self)
            qtw.QMessageBox.warning(
                self,
                "Extract Source PDF",
                "The page workflow does not define all four source sections.",
            )
            return []
        if not stage_steps:
            PixlerMain._report_completed_dialog_loop(
                self,
                "Source Section Extraction",
                completed_steps,
            )
            return []

        source_file = self._first_workflow_source_document(
            project_staged_pdf_complete_directory(active_root)
        )
        if not source_file:
            PixlerMain._center_next_message_box(self)
            qtw.QMessageBox.warning(
                self,
                "Extract Source PDF",
                "Stage the MyServer source PDF into MyPixler before extracting its sections.",
            )
            return []

        context = self.workflow_tracker._load_project_context(active_root)
        total_pages = max(1, int(context.get("NumberPages", 1) or 1))
        ranges = {
            str(section.get("key", "")): (
                section.get("start_page"),
                section.get("end_page"),
            )
            for section in context.get("SourcePageSections", [])
            if isinstance(section, dict)
        }
        section_range_keys = {
            "FrontSection": "front_matter",
            "MiddleSections": "scripture",
            "VerseSections": "scripture",
            "BackSection": "back_matter",
        }
        steps = stage_steps
        state = self._load_extract_dialog_state(active_root)
        section_states = state.setdefault("sections", {})
        extracted_paths = []
        configured_index = min(
            max(int(state.get("section_index", 0) or 0), 0),
            len(configured_steps) - 1,
        )
        saved_sequence = str(
            state.get("section_sequence")
            or configured_steps[configured_index].sequence
        )
        current_index = next(
            (
                index
                for index, pending_step in enumerate(steps)
                if pending_step.sequence == saved_sequence
            ),
            0,
        )
        previous_result = qtw.QDialog.Accepted + 1
        next_result = previous_result + 1
        skip_result = next_result + 1
        dialog = qtw.QDialog(self if isinstance(self, qtw.QWidget) else None)
        ui = Ui_ExtractDialog()
        ui.setupUi(dialog)
        PixlerMain._prepare_extract_dialog(dialog, ui)
        self._install_extract_context_menu(dialog, ui, skip_result)
        ui.HelpButton.clicked.connect(lambda: show_help(dialog, "MyPixler"))
        ui.PreviousButton.clicked.connect(lambda: dialog.done(previous_result))
        ui.NextButton.clicked.connect(lambda: dialog.done(next_result))
        ui.SkipButton.clicked.connect(lambda: dialog.done(skip_result))
        ok_button = ui.buttonBox.button(qtw.QDialogButtonBox.Ok)
        ok_button.setText("Extract")
        if completed_steps:
            completed_report = PixlerMain._completed_step_report(completed_steps)
            ui.ProgressLabel.setToolTip(
                "Completed dialogs omitted from this loop:\n"
                f"{completed_report}\n\n"
                "Uncheck Complete in MyServer > Project Settings > "
                "Milestone Settings to restore one."
            )
            self.statusBar().showMessage(
                "Completed extraction dialogs skipped: "
                + ", ".join(
                    f"{step.sequence} - {step.milestone_name}"
                    for step in completed_steps
                ),
                10000,
            )
        current_defaults = {}

        def set_defaults_enabled(checked):
            ui.SourceButton.setEnabled(not checked)
            ui.DestinationButton.setEnabled(not checked)
            ui.MakeDefaultCheckBox.setEnabled(not checked)
            if checked:
                ui.MakeDefaultCheckBox.setChecked(False)
                if current_defaults:
                    ui.SourceLineEdit.setText(current_defaults["source"])
                    ui.DestinationLineEdit.setText(current_defaults["destination"])
                    ui.FirstPageLineEdit.setText(current_defaults["first_page"])
                    ui.LastPageLineEdit.setText(current_defaults["last_page"])

        def select_source():
            selected = qtw.QFileDialog.getOpenFileName(
                self if isinstance(self, qtw.QWidget) else None,
                "Select PDF source file",
                ui.SourceLineEdit.text(),
                "PDF files (*.pdf)",
            )[0]
            if selected:
                ui.SourceLineEdit.setText(selected)

        def select_destination():
            selected = qtw.QFileDialog.getExistingDirectory(
                self if isinstance(self, qtw.QWidget) else None,
                "Select section staging folder",
                ui.DestinationLineEdit.text(),
            )
            if selected:
                ui.DestinationLineEdit.setText(selected)

        ui.defaultsrcBox.toggled.connect(set_defaults_enabled)
        ui.SourceButton.clicked.connect(select_source)
        ui.DestinationButton.clicked.connect(select_destination)
        def mark_custom_value(_text):
            ui.defaultsrcBox.setChecked(False)
            ui.MakeDefaultCheckBox.setEnabled(True)

        ui.SourceLineEdit.textEdited.connect(mark_custom_value)
        ui.DestinationLineEdit.textEdited.connect(mark_custom_value)
        ui.FirstPageLineEdit.textEdited.connect(mark_custom_value)
        ui.LastPageLineEdit.textEdited.connect(mark_custom_value)

        while True:
            step = steps[current_index]
            destination = resolve_page_workflow_path(active_root, step.workflow_source)
            default_first, default_last = ranges.get(
                section_range_keys.get(step.page_section, ""),
                (None, None),
            )
            saved = section_states.get(step.sequence, {})
            PixlerMain._normalize_extract_status(saved)
            saved["status"] = "pending"
            saved.pop("completion_source", None)
            defaults = saved.get("defaults", {}) if isinstance(saved, dict) else {}
            current_defaults.clear()
            current_defaults.update({
                "source": str(defaults.get("source", source_file)),
                "destination": str(defaults.get("destination", destination)),
                "first_page": str(defaults.get("first_page", default_first or 1)),
                "last_page": str(defaults.get("last_page", default_last or total_pages)),
            })
            dialog.setWindowTitle(f"Extract {step.page_section} source pages")
            ui.SourceLineEdit.setText(str(saved.get("source", current_defaults["source"])))
            ui.DestinationLineEdit.setText(str(saved.get("destination", current_defaults["destination"])))
            ui.FirstPageLineEdit.setText(str(saved.get("first_page", current_defaults["first_page"])))
            ui.LastPageLineEdit.setText(str(saved.get("last_page", current_defaults["last_page"])))
            ui.defaultsrcBox.setChecked(bool(saved.get("use_default", True)))
            ui.ProgressLabel.setText(
                f"Section {current_index + 1} of {len(steps)}: {step.page_section}"
                f" | {saved.get('status', 'pending')}"
            )
            ui.PreviousButton.setEnabled(current_index > 0)
            ui.NextButton.setEnabled(current_index < len(steps) - 1)
            result = self._run_non_modal_dialog(dialog)
            current_state = section_states.setdefault(step.sequence, {})
            current_state.update({
                "source": ui.SourceLineEdit.text(),
                "destination": ui.DestinationLineEdit.text(),
                "first_page": ui.FirstPageLineEdit.text(),
                "last_page": ui.LastPageLineEdit.text(),
                "use_default": ui.defaultsrcBox.isChecked(),
            })
            if ui.MakeDefaultCheckBox.isChecked():
                current_state["defaults"] = {
                    "source": ui.SourceLineEdit.text(),
                    "destination": ui.DestinationLineEdit.text(),
                    "first_page": ui.FirstPageLineEdit.text(),
                    "last_page": ui.LastPageLineEdit.text(),
                }
            state["section_index"] = configured_steps.index(step)
            state["section_sequence"] = step.sequence
            self._save_extract_dialog_state(active_root, state)

            if result == qtw.QDialog.Rejected:
                return extracted_paths
            if result == previous_result:
                current_index = max(0, current_index - 1)
                continue
            if result == next_result:
                current_index = min(len(steps) - 1, current_index + 1)
                continue
            if result == skip_result:
                PixlerMain._center_next_message_box(dialog)
                response = qtw.QMessageBox.question(
                    dialog,
                    "Skip Section Extraction",
                    "Skip this section for now? It will remain pending.",
                    qtw.QMessageBox.Yes | qtw.QMessageBox.Cancel,
                    qtw.QMessageBox.Cancel,
                )
                if response == qtw.QMessageBox.Cancel:
                    continue
                current_state["status"] = "pending"
                current_state.pop("completion_source", None)
                self._save_extract_dialog_state(active_root, state)
                current_index += 1
                if current_index >= len(steps):
                    break
                continue

            destination_path = ui.DestinationLineEdit.text()
            os.makedirs(destination_path, exist_ok=True)
            if not self._confirm_extract_overwrite(dialog, destination_path):
                continue
            progress = PixlerMain._show_extraction_progress(
                self,
                dialog,
                f"Extracting {step.page_section} source pages...",
            )
            try:
                for name in os.listdir(destination_path):
                    path = os.path.join(destination_path, name)
                    if os.path.isdir(path) and not os.path.islink(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                extracted_paths.append(
                    extract_pdf_page_range(
                        ui.SourceLineEdit.text(),
                        destination_path,
                        ui.FirstPageLineEdit.text(),
                        ui.LastPageLineEdit.text(),
                    )
                )
            except (OSError, ValueError) as exc:
                PixlerMain._center_next_message_box(dialog)
                qtw.QMessageBox.warning(
                    dialog,
                    "Extract PDF Pages",
                    f"Could not extract the selected {step.page_section} pages.\n\n{exc}",
                )
                return extracted_paths
            finally:
                PixlerMain._close_extraction_progress(progress)

            completion_step = replace(
                step,
                workflow_source=os.path.relpath(destination_path, active_root),
            )
            try:
                self._finish_page_workflow_step(
                    completion_step,
                    details={"source": "extract_source_pdf_section"},
                    stage_source=True,
                )
            except (OSError, ValueError) as exc:
                current_state["status"] = "pending"
                current_state.pop("completion_source", None)
                self._save_extract_dialog_state(active_root, state)
                extracted_paths.pop()
                PixlerMain._center_next_message_box(dialog)
                qtw.QMessageBox.warning(
                    dialog,
                    "Complete Section Extraction",
                    f"The section PDF was created, but its workflow handoff could not be completed.\n\n{exc}",
                )
                return extracted_paths
            current_state["status"] = "complete"
            current_state["completion_source"] = "extraction"
            self._save_extract_dialog_state(active_root, state)
            PixlerMain._refresh_extract_completion_progress(
                self,
                active_root,
                ui,
                f"{step.sequence} - {step.milestone_name} | complete",
            )
            complete_destination = resolve_page_workflow_path(
                active_root,
                step.complete_destination,
            )
            extracted_paths[-1] = os.path.join(
                complete_destination,
                os.path.basename(extracted_paths[-1]),
            )
            current_index += 1
            if current_index >= len(steps):
                break

        state["section_index"] = 0
        state["section_sequence"] = configured_steps[0].sequence
        self._save_extract_dialog_state(active_root, state)

        self.statusBar().showMessage(
            f"Extracted source PDF into {len(extracted_paths)} section staging folders.",
            5000,
        )
        if len(extracted_paths) == len(steps):
            PixlerMain._report_completed_dialog_loop(
                self,
                "Source Section Extraction",
                configured_steps,
            )
        return extracted_paths

    def actionextract_staged_pdf_pages(self, workflow_step=None):
        workflow_step = workflow_step or self._workflow_step_for_method("actionextract_pdf")
        if workflow_step is None:
            return []
        workflow_source, complete_folder, _workflow_handshake = self._workflow_step_paths(workflow_step)
        source_file = self._first_workflow_source_document(workflow_source)
        if not source_file:
            PixlerMain._center_next_message_box(self)
            qtw.QMessageBox.warning(
                self,
                "Extract Staged Section PDF",
                f"No staged section PDF is available in:\n{workflow_source}",
            )
            return []

        dialog = qtw.QDialog(self if isinstance(self, qtw.QWidget) else None)
        ui = Ui_ExtractDialog()
        ui.setupUi(dialog)
        PixlerMain._prepare_extract_dialog(dialog, ui)
        active_root = self.current_project_root or self._shared_active_project_root() or self.projecthome
        state = self._load_extract_dialog_state(active_root)
        section_states = state.setdefault("single_page_sections", {})
        saved = section_states.get(workflow_step.sequence, {})
        PixlerMain._normalize_extract_status(saved)
        saved["status"] = "pending"
        saved.pop("completion_source", None)
        defaults = saved.get("defaults", {}) if isinstance(saved, dict) else {}
        current_defaults = {
            "source": str(defaults.get("source", source_file)),
            "destination": str(defaults.get("destination", complete_folder)),
            "first_page": str(defaults.get("first_page", "1")),
            "last_page": str(defaults.get("last_page", "")),
        }
        dialog.setWindowTitle(f"Extract {workflow_step.page_section} into single-page PDFs")
        ui.SourceLineEdit.setText(str(saved.get("source", current_defaults["source"])))
        ui.DestinationLineEdit.setText(str(saved.get("destination", current_defaults["destination"])))
        ui.FirstPageLineEdit.setText(str(saved.get("first_page", current_defaults["first_page"])))
        ui.LastPageLineEdit.setText(str(saved.get("last_page", current_defaults["last_page"])))
        ui.LastPageLineEdit.setPlaceholderText("Final page")
        ui.PreviousButton.hide()
        ui.NextButton.hide()
        ui.ProgressLabel.setText(f"Extracting staged {workflow_step.page_section} PDF")
        ui.HelpButton.clicked.connect(lambda: show_help(dialog, "MyPixler"))

        def skip_extraction():
            PixlerMain._center_next_message_box(dialog)
            response = qtw.QMessageBox.question(
                dialog,
                "Skip Page Extraction",
                "Skip this extraction for now? It will remain pending.",
                qtw.QMessageBox.Yes | qtw.QMessageBox.Cancel,
                qtw.QMessageBox.Cancel,
            )
            if response == qtw.QMessageBox.Cancel:
                return
            saved["status"] = "pending"
            saved.pop("completion_source", None)
            dialog.reject()

        ui.SkipButton.clicked.connect(skip_extraction)
        self._install_extract_context_menu(
            dialog,
            ui,
            qtw.QDialog.Rejected,
            skip_callback=skip_extraction,
        )

        def set_defaults_enabled(checked):
            ui.SourceButton.setEnabled(not checked)
            ui.DestinationButton.setEnabled(not checked)
            ui.MakeDefaultCheckBox.setEnabled(not checked)
            if checked:
                ui.MakeDefaultCheckBox.setChecked(False)
                ui.SourceLineEdit.setText(current_defaults["source"])
                ui.DestinationLineEdit.setText(current_defaults["destination"])
                ui.FirstPageLineEdit.setText(current_defaults["first_page"])
                ui.LastPageLineEdit.setText(current_defaults["last_page"])

        def select_source():
            selected = qtw.QFileDialog.getOpenFileName(
                self if isinstance(self, qtw.QWidget) else None,
                "Select staged section PDF",
                ui.SourceLineEdit.text(),
                "PDF files (*.pdf)",
            )[0]
            if selected:
                ui.SourceLineEdit.setText(selected)

        def select_destination():
            selected = qtw.QFileDialog.getExistingDirectory(
                self if isinstance(self, qtw.QWidget) else None,
                "Select single-page PDF destination",
                ui.DestinationLineEdit.text(),
            )
            if selected:
                ui.DestinationLineEdit.setText(selected)

        ui.defaultsrcBox.toggled.connect(set_defaults_enabled)
        ui.SourceButton.clicked.connect(select_source)
        ui.DestinationButton.clicked.connect(select_destination)
        ui.defaultsrcBox.setChecked(bool(saved.get("use_default", True)))
        def mark_custom_value(_text):
            ui.defaultsrcBox.setChecked(False)
            ui.MakeDefaultCheckBox.setEnabled(True)

        ui.SourceLineEdit.textEdited.connect(mark_custom_value)
        ui.DestinationLineEdit.textEdited.connect(mark_custom_value)
        ui.FirstPageLineEdit.textEdited.connect(mark_custom_value)
        ui.LastPageLineEdit.textEdited.connect(mark_custom_value)
        result = self._run_non_modal_dialog(dialog)
        saved.update({
            "source": ui.SourceLineEdit.text(),
            "destination": ui.DestinationLineEdit.text(),
            "first_page": ui.FirstPageLineEdit.text(),
            "last_page": ui.LastPageLineEdit.text(),
            "use_default": ui.defaultsrcBox.isChecked(),
        })
        if ui.MakeDefaultCheckBox.isChecked():
            saved["defaults"] = {
                "source": ui.SourceLineEdit.text(),
                "destination": ui.DestinationLineEdit.text(),
                "first_page": ui.FirstPageLineEdit.text(),
                "last_page": ui.LastPageLineEdit.text(),
            }
        section_states[workflow_step.sequence] = saved
        self._save_extract_dialog_state(active_root, state)
        if result != qtw.QDialog.Accepted:
            return []

        progress = PixlerMain._show_extraction_progress(
            self,
            dialog,
            f"Extracting {workflow_step.page_section} into individual pages...",
        )
        try:
            destination_dir = os.path.abspath(ui.DestinationLineEdit.text())
            source_path = os.path.abspath(ui.SourceLineEdit.text())
            source_in_destination = os.path.dirname(source_path) == destination_dir
            extraction_dir = destination_dir
            temporary_dir = None
            if source_in_destination:
                temporary_dir = tempfile.TemporaryDirectory()
                extraction_dir = temporary_dir.name
            os.makedirs(destination_dir, exist_ok=True)
            if not self._confirm_extract_overwrite(
                dialog,
                destination_dir,
                preserved_paths=(source_path,) if source_in_destination else (),
            ):
                if temporary_dir is not None:
                    temporary_dir.cleanup()
                return []
            for name in os.listdir(destination_dir):
                path = os.path.join(destination_dir, name)
                if source_in_destination and os.path.normcase(os.path.abspath(path)) == os.path.normcase(source_path):
                    continue
                if os.path.isdir(path) and not os.path.islink(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            extracted_paths = extract_pdf_pages(
                source_path,
                extraction_dir,
                ui.FirstPageLineEdit.text() or 1,
                ui.LastPageLineEdit.text() or None,
            )
            if temporary_dir is not None:
                os.remove(source_path)
                moved_paths = []
                for extracted_path in extracted_paths:
                    destination_path = os.path.join(destination_dir, os.path.basename(extracted_path))
                    shutil.move(extracted_path, destination_path)
                    moved_paths.append(destination_path)
                extracted_paths = moved_paths
                temporary_dir.cleanup()
            self._finish_page_workflow_step(
                workflow_step,
                details={
                    "source": "actionextract_staged_pdf_pages",
                    "page_count": len(extracted_paths),
                },
            )
            saved["status"] = "complete"
            saved["completion_source"] = "extraction"
            self._save_extract_dialog_state(active_root, state)
            PixlerMain._refresh_extract_completion_progress(
                self,
                active_root,
                ui,
                f"{workflow_step.sequence} - {workflow_step.milestone_name} | complete",
            )
        except (OSError, ValueError) as exc:
            PixlerMain._center_next_message_box(dialog)
            qtw.QMessageBox.warning(
                dialog,
                "Extract Staged Section PDF",
                f"Could not extract the staged section PDF.\n\n{exc}",
            )
            return []
        finally:
            PixlerMain._close_extraction_progress(progress)

        self.statusBar().showMessage(
            f"Extracted {len(extracted_paths)} single-page PDFs for {workflow_step.page_section}.",
            5000,
        )
        PixlerMain._report_completed_dialog_loop(
            self,
            f"{workflow_step.page_section} Page Extraction",
            [workflow_step],
        )
        return extracted_paths

    # Page workflow: Sequence EF4T; MilestoneName front_matter_pages_extracted_for_tif.
    # Page workflow: Sequence EB4T; MilestoneName middle_matter_pages_extracted_for_tif.
    # Page workflow: Sequence EB4T; MilestoneName verse_books_pages_extracted_for_tif.
    # Page workflow: Sequence EB4T; MilestoneName back_matter_pages_extracted_for_tif.
    def actionpdf_for_tiff(self):
        workflow_step = self._workflow_step_for_method("actionpdf_for_tiff")
        source_folder, complete_folder, _workflow_handshake = (
            self._workflow_step_paths(workflow_step) if workflow_step else ("", "", "")
        )
        workflow_folder = complete_folder
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

            source_file_path = self.pdf4tif_ui.SourceLineEdit.text().strip()
            if os.path.isdir(source_file_path):
                source_file_path = self._first_workflow_file(source_file_path)
            progress = PixlerMain._show_extraction_progress(
                self,
                self.pdf4tifDialog,
                "Extracting PDF pages for TIFF conversion...",
            )
            try:
                extracted_paths = extract_pdf_pages(
                    source_file_path,
                    self.pdf4tif_ui.DestinationLineEdit.text(),
                    self.pdf4tif_ui.FirstPageSpinBox.value(),
                    self.pdf4tif_ui.LastPageSpinBox.value() or None,
                )
            except (OSError, ValueError) as exc:
                qtw.QMessageBox.warning(
                    self.pdf4tifDialog,
                    "Extract PDF Pages for TIFF",
                    f"Could not extract the section PDF into individual pages.\n\n{exc}",
                )
                return
            finally:
                PixlerMain._close_extraction_progress(progress)
            print(f"pdf pages for tif extraction complete: {len(extracted_paths)} pages")
            if workflow_step:
                self._finish_page_workflow_step(
                    workflow_step,
                    details={"source": "actionpdf_for_tiff"},
                )
        def reject():
            pass

        self.pdf4tifDialog = qtw.QDialog()
        self.pdf4tif_ui = Ui_pdf4tifDialog()
        self.pdf4tif_ui.setupUi(self.pdf4tifDialog)
        self.pdf4tifDialog.show()

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
            self.pdf4tif_ui.SourceLineEdit.setText(source_folder)
            self.pdf4tif_ui.DestinationLineEdit.setText(complete_folder)
            print(source_folder, workflow_folder, complete_folder)

        rsp = self.pdf4tifDialog.exec_()

    # Page workflow: Sequence 4T2T; MilestoneName front_matter_pages_converted_to_tif.
    # Page workflow: Sequence 4T2T; MilestoneName middle_matter_pages_converted_to_tif.
    # Page workflow: Sequence 4T2T; MilestoneName verse_books_pages_converted_to_tif.
    # Page workflow: Sequence 4T2T; MilestoneName back_matter_pages_converted_to_tif.
    def actionpdf_to_tiff(self):
        workflow_step = self._workflow_step_for_method("actionpdf_to_tiff")
        source_folder, complete_folder, _workflow_handshake = (
            self._workflow_step_paths(workflow_step) if workflow_step else ("", "", "")
        )
        workflow_folder = complete_folder
        print("converting pdf pages to tiff")

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
            #pp.pdf2tif(source_folder, workflow_folder, self.pdf2tif_ui.StartPageLineEdit.text())
            try:
                converted_paths = convert_pdf_pages_to_tiff(
                    self.pdf2tif_ui.SourceLineEdit.text(),
                    self.pdf2tif_ui.DestinationLineEdit.text(),
                    self.pdf2tif_ui.StartPageLineEdit.text(),
                )
            except (OSError, RuntimeError, ValueError) as exc:
                qtw.QMessageBox.warning(
                    self.pdf2tifDialog,
                    "Convert PDF Pages to TIFF",
                    f"Could not convert the individual PDF pages to TIFF.\n\n{exc}",
                )
                return
            print(f"pdf pages converted to tiff: {len(converted_paths)} pages")
            if workflow_step:
                self._finish_page_workflow_step(
                    workflow_step,
                    details={"source": "actionpdf_to_tiff"},
                )
        def reject():
            pass

        self.pdf2tifDialog = qtw.QDialog()
        self.pdf2tif_ui = Ui_pdf2tifDialog()
        self.pdf2tif_ui.setupUi(self.pdf2tifDialog)
        self.pdf2tifDialog.show()

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
            source_file = self._first_workflow_file(source_folder)
            self.pdf2tif_ui.SourceLineEdit.setText(source_file or source_folder)
            self.pdf2tif_ui.DestinationLineEdit.setText(complete_folder)
            start_page = self.firstpage
            self.pdf2tif_ui.StartPageLineEdit.setText(start_page)
            print(source_folder, workflow_folder, complete_folder, start_page)

        rsp = self.pdf2tifDialog.exec_()



        print("tif pages conversion complete")

    # Page workflow: Sequence 2T2I; MilestoneName front_matter_tif_pages_indexed.
    # Page workflow: Sequence 2T2I; MilestoneName middle_matter_tif_pages_indexed.
    # Page workflow: Sequence 2T2I; MilestoneName verse_books_tif_pages_indexed.
    # Page workflow: Sequence 2T2I; MilestoneName back_matter_tif_pages_indexed.
    def actiontiff_to_mono(self):
        workflow_step = self._workflow_step_for_method("actiontiff_to_mono")
        source_folder, complete_folder, _workflow_handshake = (
            self._workflow_step_paths(workflow_step) if workflow_step else ("", "", "")
        )
        workflow_folder = complete_folder
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
            if workflow_step:
                self._finish_page_workflow_step(
                    workflow_step,
                    details={"source": "actiontiff_to_mono"},
                )
        def reject():
            pass

        #usage: pp.tiff2tiffidx(source, destination)

        self.tif2monoDialog = qtw.QDialog()
        self.tif2mono_ui = Ui_tif2monoDialog()
        self.tif2mono_ui.setupUi(self.tif2monoDialog)
        self.tif2monoDialog.show()

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
            self.tif2mono_ui.SourceLineEdit.setText(source_folder)
            self.tif2mono_ui.DestinationLineEdit.setText(complete_folder)
            print(source_folder, workflow_folder, complete_folder)

        rsp = self.tif2monoDialog.exec_()



        print("completed creating indexed(BW) tiff")

    def actiondeskew_mono(self):
        print("deskewing monochrome tiff and png files")

        def accept():
            source_folder = self.deskew_mono_ui.SourceLineEdit.text()
            tif_workflow_folder = self.deskew_mono_ui.DestTifLineEdit.text()
            png_workflow_folder = self.deskew_mono_ui.DestPngLineEdit.text()
            tif_complete_folder = ""
            png_complete_folder = ""
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
        def reject():
            pass

        #usage: dsk.deskewfiles(source, pngdest, tifdest)

        self.deskew_monoDialog = qtw.QDialog()
        self.deskew_mono_ui = Ui_deskew_monoDialog()
        self.deskew_mono_ui.setupUi(self.deskew_monoDialog)
        self.deskew_monoDialog.show()

        def setdefault():
            if self.deskew_mono_ui.defaultsrcBox.isChecked():
                self.deskew_mono_ui.SourceButton.setEnabled(False)
                self.deskew_mono_ui.DestTifButton.setEnabled(False)
            else:
                self.deskew_mono_ui.SourceButton.setEnabled(True)
                self.deskew_mono_ui.DestTifButton.setEnabled(True)

        if self.deskew_mono_ui.defaultsrcBox.isChecked():
            self.deskew_mono_ui.defaultsrcBox.setChecked(False)

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
            self.deskew_mono_ui.defaultsrcBox.setChecked(False)
        self.deskew_mono_ui.defaultsrcBox.setEnabled(False)
        self.deskew_mono_ui.defaultsrcBox.setToolTip("This manual tool is not part of page_workflow.csv.")

        rsp = self.deskew_monoDialog.exec_()
        print("completed deskewing monochrome tiff and png files")

    def actionCrop_Languages(self):
        print("creating cropped language tif files")

        def accept():
            source_folder = self.crop_languages_ui.SourceLineEdit.text()
            workflow_box_folder = self.crop_languages_ui.BoxFolderLineEdit.text()
            workflow_elim_folder = self.crop_languages_ui.ElimFolderLineEdit.text()
            workflow_greek_folder = self.crop_languages_ui.DestGreekLineEdit.text()
            workflow_latin_folder = self.crop_languages_ui.DestLatinLineEdit.text()
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

        if self.crop_languages_ui.defaultsrcBox.isChecked():
            self.crop_languages_ui.defaultsrcBox.setChecked(False)
        self.crop_languages_ui.defaultsrcBox.setEnabled(False)
        self.crop_languages_ui.defaultsrcBox.setToolTip("Column cropping is governed by MyBoxer in page_workflow.csv.")
        rsp = self.crop_languagesDialog.exec_()

    def actionDeskew_Greek_tiff(self):
        print("deskewing Greek tiff files")
        #usage: dsk.deskewfiles(source, pngdest, tifdest)

        def accept():
            source_folder = self.deskew_greekmono_ui.SourceLineEdit.text()
            tif_workflow_folder = self.deskew_greekmono_ui.DestTifLineEdit.text()
            png_workflow_folder = self.deskew_greekmono_ui.DestPngLineEdit.text()
            tif_complete_folder = ""
            png_complete_folder = ""
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
        def reject():
            pass

        #usage: dsk.deskewfiles(source, pngdest, tifdest)

        self.deskew_greekmonoDialog = qtw.QDialog()
        self.deskew_greekmono_ui = Ui_deskew_greekmonoDialog()
        self.deskew_greekmono_ui.setupUi(self.deskew_greekmonoDialog)
        self.deskew_greekmonoDialog.show()

        def setdefault():
            if self.deskew_greekmono_ui.defaultsrcBox.isChecked():
                self.deskew_greekmono_ui.SourceButton.setEnabled(False)
                self.deskew_greekmono_ui.DestTifButton.setEnabled(False)
            else:
                self.deskew_greekmono_ui.SourceButton.setEnabled(True)
                self.deskew_greekmono_ui.DestTifButton.setEnabled(True)

        if self.deskew_greekmono_ui.defaultsrcBox.isChecked():
            self.deskew_greekmono_ui.defaultsrcBox.setChecked(False)

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
            self.deskew_greekmono_ui.defaultsrcBox.setChecked(False)
        self.deskew_greekmono_ui.defaultsrcBox.setEnabled(False)
        self.deskew_greekmono_ui.defaultsrcBox.setToolTip("This manual tool is not part of page_workflow.csv.")

        rsp = self.deskew_greekmonoDialog.exec_()

    def actionDeskew_Latin_tiff(self):
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
        #dsk.deskewfiles("~/Projects/Python/Images/Latin/png_latin/latin_book_40_Matthew/", "~/Projects/Python/Images/Latin/png_latin_deskew/latin_book_40_Matthew/","~/Projects/Python/Images/Latin/tif_latin_deskew/latin_book_40_Matthew/")
        #pp.deskewfiles("~/Projects/Python/Images/Latin/png_latin/latin_book_41_Mark/", "~/Projects/Python/Images/Latin/png_latin_deskew/latin_book_41_Mark/","~/Projects/Python/Images/Latin/tif_latin_deskew/latin_book_41_Mark/")

    def OpenPdfFileDialog(self):
        self.path = qtw.QFileDialog.getOpenFileName(self.ui.centralwidget,'Select pdf source file','','*.pdf')[0]

        if self.path:
            self.pdfx_ui.SourceLineEdit.setText(self.path)

    def DestPdfFileDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select destination folder"))

        if self.directory:
            self.pdfx_ui.DestinationLineEdit.setText(self.directory+r'/')

    def PdfForTifDialog(self):
        self.path = qtw.QFileDialog.getOpenFileName(self.ui.centralwidget,'Select pdf pages source file','','*.pdf')[0]

        if self.path:
            self.pdf4tif_ui.SourceLineEdit.setText(self.path)

    def DestPdfForTifDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select destination folder"))

        if self.directory:
            self.pdf4tif_ui.DestinationLineEdit.setText(self.directory+r'/')

    def PdfToTifDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select pdf pages source folder"))

        if self.directory:
            self.pdf2tif_ui.SourceLineEdit.setText(self.directory+r'/')

    def DestPdfToTifDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select destination folder"))

        if self.directory:
            self.pdf2tif_ui.DestinationLineEdit.setText(self.directory+r'/')

    def TifToMonoDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select pdf pages source folder"))

        if self.directory:
            self.tif2mono_ui.SourceLineEdit.setText(self.directory+r'/')

    def DestTifToMonoDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select destination folder"))

        if self.directory:
            self.tif2mono_ui.DestinationLineEdit.setText(self.directory+r'/')

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

    def DeskewGreekMonoDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select greek pages source folder"))

        if self.directory:
            self.deskew_greekmono_ui.SourceLineEdit.setText(self.directory+r'/')

    def DestDeskewGreekPngDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select greek png pages destination folder"))

        if self.directory:
            self.deskew_greekmono_ui.DestPngLineEdit.setText(self.directory+r'/')

    def DestDeskewGreekTifDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select greek tif pages destination folder"))

        if self.directory:
            self.deskew_greekmono_ui.DestTifLineEdit.setText(self.directory+r'/')

    def DeskewLatinMonoDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select latin pages source folder"))

        if self.directory:
            self.deskew_latinmono_ui.SourceLineEdit.setText(self.directory+r'/')

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
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select latin png pages destination folder"))

        if self.directory:
            self.deskew_latinmono_ui.DestPngLineEdit.setText(self.directory+r'/')

    def DestDeskewLatinTifDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select latin tif pages destination folder"))

        if self.directory:
            self.deskew_latinmono_ui.DestTifLineEdit.setText(self.directory+r'/')

    def CropLanguagesDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select pdf pages source folder"))

        if self.directory:
            self.crop_languages_ui.SourceLineEdit.setText(self.directory+r'/')

    def BoxFolderDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select destination folder"))

        if self.directory:
            self.crop_languages_ui.BoxFolderLineEdit.setText(self.directory+r'/')

    def ElimFolderDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select destination folder"))

        if self.directory:
            self.crop_languages_ui.ElimFolderLineEdit.setText(self.directory+r'/')

    def DestGreekDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select destination folder"))

        if self.directory:
            self.crop_languages_ui.DestGreekLineEdit.setText(self.directory+r'/')

    def DestLatinDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select destination folder"))

        if self.directory:
            self.crop_languages_ui.DestLatinLineEdit.setText(self.directory+r'/')

    # Mouse Controllers
    def wheelEvent(self, event):
        delta = event.angleDelta().y()

        if delta > 0:
            self.zoom_factor *= 1.1
        else:
            self.zoom_factor *= 0.9

        # Clamp zoom
        self.zoom_factor = max(0.25, min(2.0, self.zoom_factor))

        # Sync slider
        self.zoom_slider.setValue(int(self.zoom_factor * 100))

        self.update_preview()

    def mousePressEvent(self, event):

        # ---- Focus routing (GOOD as-is) ----
        if self.ui.RefImg.geometry().contains(event.pos()):
            self.ui.RefImg.setFocus()
        elif self.ui.Image.geometry().contains(event.pos()):
            self.ui.Image.setFocus()

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):

        '''if not self.origin.isNull():
            self.refimg_xoffset = self.ui.RefImg.x()
            self.refimg_yoffset = self.ui.RefImg.y()
            (x,y) = event.pos()
            x = self.refimg_xoffset + x
            y = self.refimg_yoffset + y
            pos = QPoint(x,y)
            print(str(pos))
            self.rubberBand.setGeometry(QRect(self.origin, pos).normalized())'''
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)

    # Reference Image Edit Controllers
    def start_image_load(self, path, target="ref"):
        print(f"[THREAD] Start load ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ {path} ({target})")
        # store target so handler knows where to route image
        self._load_target = target
        self._load_thread = qtc.QThread(self)
        self._load_worker = ImageLoadWorker(path)
        self._load_worker.moveToThread(self._load_thread)

        # --- signals
        self._load_thread.started.connect(self._load_worker.run)
        self._load_worker.progress.connect(self.on_load_progress)
        self._load_worker.finished.connect(self.on_image_loaded)
        self._load_worker.error.connect(self.on_load_error)

        # --- cleanup
        self._load_worker.finished.connect(self._load_thread.quit)
        self._load_worker.finished.connect(self._load_worker.deleteLater)
        self._load_worker.error.connect(self._load_thread.quit)
        self._load_worker.error.connect(self._load_worker.deleteLater)
        self._load_thread.finished.connect(self._load_thread.deleteLater)
        self._load_thread.finished.connect(self._on_load_thread_finished)

        # --- start
        self._load_thread.start()

        self.statusBar().showMessage("Loading reference image...")
        self._show_progress(0)

    def on_load_progress(self, value):
        print(f"[LOAD] {value}%")
        self._set_progress_percent(value)
        self.statusBar().showMessage(f"Loading reference image... {int(value)}%")

    def on_image_loaded(self, qimage):
        self.refimgqimage = qimage

        self._hide_progress(100)

        # store pixmap (CRITICAL for zoom, etc.)
        self.refimgpixmap = qtg.QPixmap.fromImage(qimage)
        if self.refimgpath:
            self.refimgdir = os.path.dirname(self.refimgpath)
        self._update_pixler_session_paths()
        self._sync_project_page_state(self.refimgpath)

        # display
        self.ui.RefImg.setPixmap(self.refimgpixmap.scaled(self.ui.RefImg.size(), qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation))

        # -------------------------
        # ÃƒÂ¢Ã…â€œÃ¢â‚¬Â¦ ADD THIS BLOCK
        # -------------------------
        if self.refimgpath:
            filename = os.path.basename(self.refimgpath)
            self.ui.RefImgLE.setText(filename)
            #self.ui.RefImgLE.setToolTip(self.refimgpath)  # Reuse this path forward to modify a ToolTip
            self.ui.RefImgLE.setToolTip("Reference Image Filename")

        self._refresh_project_status(self.refimgpath or self.refimgdir)
        self.statusBar().showMessage("Reference image loaded.")

    def on_load_error(self, msg):
        print(f"[LOAD ERROR] {msg}")
        self._hide_progress()
        self.statusBar().showMessage(f"Image load failed: {msg}", 5000)

    def _on_load_thread_finished(self):
        self._load_thread = None
        self._load_worker = None

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

    def importRefImg(self):
        print("Importing current reference image path provided by get_session")
        if self.imgpath:
            print(self.imgpath)
            self.refimgpath = self.imgpath
            self.refimgdir = os.path.dirname(self.refimgpath)
            self._update_pixler_session_paths()
            self.ui.RefImgLE.setText(os.path.basename(self.refimgpath))
            self._refresh_project_status(self.refimgpath)
            print("[Pixler] Ref image indexed")

    def loadRefImg(self):
        self.open_non_modal_image_picker(
            "Open Reference Image",
            self.refimgdir or self.imagedir or "",
            self._load_ref_image_from_picker,
            '_ref_image_open_dialog',
        )

    def _load_ref_image_from_picker(self, fileName):

        fileName = os.path.abspath(os.path.normpath(fileName))

        if not os.path.isfile(fileName):
            print(f"[OPEN] Invalid file: {fileName}")
            return

        print(f"[OPEN] Selected: {fileName}")

        # -------------------------
        # Update state
        # -------------------------
        self.refimgpath = fileName
        self.refimgdir = os.path.dirname(fileName)
        self._refresh_project_status(fileName)

        # -------------------------
        # Re-index folder (optional but recommended)
        # -------------------------
        self.setupRefImages()

        # -------------------------
        # ÃƒÂ°Ã…Â¸Ã¢â‚¬ÂÃ‚Â¥ CRITICAL: async load
        # -------------------------
        self.start_image_load(fileName, target="ref")

    def sortRefImgFiles(self):
        import os

        # --- Case 1: Single-image mode (from MyServer) ---
        if getattr(self, "refimgpath", None):
            if os.path.isfile(self.refimgpath):
                self.refimgfiles = [self.refimgpath]
                self.refimgindex = 0
                print("[Pixler] Single image mode")
                return

        # --- Case 2: Directory mode ---
        if not getattr(self, "refimgdir", None):
            print("[Pixler] No reference image directory set")
            self.refimgfiles = []
            self.refimgindex = -1
            return

        if not os.path.isdir(self.refimgdir):
            print(f"[Pixler] Invalid directory: {self.refimgdir}")
            self.refimgfiles = []
            self.refimgindex = -1
            return

        # --- Build file list ---
        valid_ext = ('.png', '.jpg', '.jpeg', '.tif', '.tiff')

        self.refimgfiles = sorted([
            os.path.join(self.refimgdir, f)
            for f in os.listdir(self.refimgdir)
            if f.lower().endswith(valid_ext)
        ])

        print(f"[Pixler DEBUG] imgpath: {self.imgpath}")

        # --- Find current index ---
        if self.refimgpath in self.refimgfiles:
            self.refimgindex = self.refimgfiles.index(self.refimgpath)
        else:
            self.refimgindex = 0 if self.refimgfiles else -1

        print(f"[Pixler DEBUG] imgpath: {self.imgpath}")

    def build_file_list(self, directory):
        if not os.path.isdir(directory):
            return []

        valid_ext = ('.png', '.jpg', '.jpeg', '.tif', '.tiff')

        files = [
            os.path.join(directory, f)
            for f in os.listdir(directory)
            if f.lower().endswith(valid_ext)
        ]

        # natural sort
        import re
        def convert(text):
            return int(text) if text.isdigit() else text.lower()

        def key_func(key):
            return [convert(c) for c in re.split('([0-9]+)', key)]

        return sorted(files, key=key_func)

    def setupRefImages(self):
        self.refimgpath
        if getattr(self, "_in_setup", False):
            print("[GUARD] setupRefImages re-entry blocked")
            return

        self._in_setup = True

        print("=== setupRefImages START ===")
        import traceback

        print("=== setupRefImages CALLED FROM ===")
        traceback.print_stack(limit=6)
        # --- 1. HARD GUARD: UI must exist ---
        if not hasattr(self, "ui") or self.ui is None:
            print("[Pixler ERROR] UI not initialized")
            return

        # --- 2. HARD GUARD: path must exist ---
        if not self.refimgpath:
            print("[Pixler] No input image")
            return

        # Normalize early (prevents mixed path bugs)
        self.refimgpath = os.path.normpath(self.refimgpath)

        if not os.path.isfile(self.refimgpath):
            print(f"[Pixler] Invalid file: {self.refimgpath}")
            return

        print(f"[Pixler DEBUG] Using refimgpath: {self.refimgpath}")

        # --- 3. DIRECTORY RESOLUTION (SAFE) ---
        self.refimgdir = os.path.dirname(self.refimgpath)

        if not os.path.isdir(self.refimgdir):
            print(f"[Pixler ERROR] Directory does not exist: {self.refimgdir}")
            return

        # --- 4. BUILD FILE LIST SAFELY ---
        valid_ext = ('.png', '.jpg', '.jpeg', '.tif', '.tiff')

        try:
            files = os.listdir(self.refimgdir)
        except Exception as e:
            print(f"[Pixler ERROR] Failed to list directory: {e}")
            return

        self.refimgfiles = sorted([
            os.path.normpath(os.path.join(self.refimgdir, f))
            for f in files
            if f.lower().endswith(valid_ext)
        ])

        if not self.refimgfiles:
            print("[Pixler WARNING] No valid images found in directory")
            return

        # --- 5. INDEX RESOLUTION (SAFE) ---
        try:
            self.refimgindex = self.refimgfiles.index(self.refimgpath)
        except ValueError:
            print("[Pixler WARNING] Current image not in list, defaulting to first")
            self.refimgindex = 0
            self.refimgpath = self.refimgfiles[0]

        print(f"[Pixler] Loaded {len(self.refimgfiles)} images")
        print(f"[Pixler DEBUG] Index: {self.refimgindex}")

        # --- 6. FINAL RENDER (UI SAFE POINT) ---
        #self.showRefImg(self.refimgpath)
        #self.image_load_path = os.path.join(script_dir, "ImageLoadWorker.py")
        #self.start_image_load(self.refimgpath, target="ref")
        print("[Pixler] Ref image indexed")

        print("=== setupRefImages END ===")

    def nextRefImage(self):
        if not self.refimgfiles:
            return

        self.refimgindex = (self.refimgindex + 1) % len(self.refimgfiles)
        self.refimgpath = self.refimgfiles[self.refimgindex]

        print(f"[NAV] Next ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ {self.refimgpath}")
        self.start_image_load(self.refimgpath, target="ref")

    def prevRefImage(self):
        if not self.refimgfiles:
            return

        self.refimgindex = (self.refimgindex - 1) % len(self.refimgfiles)
        self.refimgpath = self.refimgfiles[self.refimgindex]

        print(f"[NAV] Prev ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ {self.refimgpath}")
        self.start_image_load(self.refimgpath, target="ref")

    def keyPressEvent(self, event):
        key = event.key()

        focus_widget = self.focusWidget()

        # --- LEFT PANEL (Reference Image) ---
        if focus_widget in (self.ui.RefImg, self.ui.RefImgLE):
            if key == qtc.Qt.Key_Right:
                self.nextRefImage()
                return
            elif key == qtc.Qt.Key_Left:
                self.prevRefImage()
                return

        # --- RIGHT PANEL (Working Image) ---
        elif focus_widget in (self.ui.Image, self.ui.ImageLE):
            if key == qtc.Qt.Key_Right:
                self.nextImg()
                return
            elif key == qtc.Qt.Key_Left:
                self.prevImg()
                return

        # --- FALLBACK (optional) ---
        # If nothing focused, default to ref panel (or do nothing)
        if key == qtc.Qt.Key_Right:
            self.nextRefImage()
        elif key == qtc.Qt.Key_Left:
            self.prevRefImage()

    def reloadRefImg(self):
        if self.refimgpath:
            self.refimgdir = os.path.dirname(self.refimgpath)
            self.ui.RefImgLE.setText(os.path.basename(self.refimgpath))

            print("[Pixler] Ref image indexed")

    def show_RefImgzoomslider(self):
        self.ui.RefImgzoomslider.show()

    def get_RefImgzoom(self):
        self.ui.RefImgzoomslider.setEnabled(True)
        self.ui.RefImgzoomslider.show()
        RefImgzoomValue = self.ui.RefImgzoomslider.value()

    def disable_RefImgzoomslider(self):
        self.ui.RefImgzoomslider.hide()
        self.ui.RefImgzoomslider.setEnabled(False)

    def move_RefImgzoomslider(self):
        self.ui.RefImgzoomslider.setEnabled(True)
        self.ui.RefImgzoomslider.setValue(int(self.ui.RefImgZoomComboBox.currentText()[0]))

    def on_RefImgzoomslider(self):
        zoomValue = self.ui.RefImgzoomslider.value()
        self.ui.RefImgZoomComboBox.blockSignals(True)
        self.ui.RefImgZoomComboBox.setCurrentText(str(zoomValue) + " %")
        self.ui.RefImgZoomComboBox.blockSignals(False)
        print(zoomValue)
        self.refimgscale = zoomValue / 100
        print(self.refimgscale)
        self.resize_RefImg()

    def on_RefImgzoom(self):
        seltext = self.ui.RefImgZoomComboBox.currentText()
        if self.ui.RefImgzoomslider.isEnabled():
            self.on_RefImgzoomslider()
        #elif seltext != "Best_Fit":
            #print("Best fit not selected")
        selnumtext = seltext.split(" ")
        print(selnumtext[0])
        self.refimgscale = float(selnumtext[0])/100
        print(self.refimgscale)

        self.resize_RefImg()

    def resize_RefImg(self):

        self.refimgsize = self.refimgpixmap.size()
        print(self.refimgsize)
        self.origheight = self.refimgpixmap.height
        self.origwidth = self.refimgpixmap.width
        scaled_pixmap = self.refimgpixmap.scaled(self.refimgscale * self.refimgsize, qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)
        self.ui.RefImg.setPixmap(scaled_pixmap)

    def changed_RefImg(self):
        self.RefImgchangesSaved = False

    # Image Controllers

    def setupImages(self):
        if not self.imagepath or not os.path.isfile(self.imagepath):
            return

        self.imagedir = os.path.dirname(self.imagepath)

        valid_ext = ('.png', '.jpg', '.jpeg', '.tif', '.tiff')

        self.imagefileList = sorted([
            os.path.join(self.imagedir, f)
            for f in os.listdir(self.imagedir)
            if f.lower().endswith(valid_ext)
        ])

        self.imageindex = self.imagefileList.index(self.imagepath)

        print(f"[Pixler] Loaded {len(self.imagefileList)} working images")

    def sortImageFiles(self):
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
        self.sorted_imagefilelist = sorted(self.imagefileList, key=alphanum_key)

    def get_Imagezoom(self):
        self.ui.Imagezoomslider.setEnabled(True)
        self.ui.Imagezoomslider.show()
        zoomValue = self.ui.Imagezoomslider.value()

    def disable_Imagezoomslider(self):
        self.ui.Imagezoomslider.hide()
        self.ui.Imagezoomslider.setEnabled(False)

    def move_Imagezoomslider(self):
        self.ui.Imagezoomslider.setEnabled(True)
        self.ui.Imagezoomslider.setValue(int(self.ui.ImageZoomComboBox.currentText()[0]))

    def on_Imagezoomslider(self):
        zoomValue = self.ui.Imagezoomslider.value()
        self.ui.ImageZoomComboBox.blockSignals(True)
        self.ui.ImageZoomComboBox.setCurrentText(str(zoomValue) + " %")
        self.ui.ImageZoomComboBox.blockSignals(False)
        print(zoomValue)
        self.imagescale = zoomValue / 100
        print(self.imagescale)
        self.resize_Image()

    def on_Imagezoom(self):
        seltext = self.ui.ImageZoomComboBox.currentText()
        if self.ui.Imagezoomslider.isEnabled():
            self.on_Imagezoomslider()
        selnumtext = seltext.split(" ")
        print(selnumtext[0])
        self.imagescale = float(selnumtext[0])/100
        print(self.imagescale)

        self.resize_Image()

    def setupImageList(self):
        if not self.imagepath:
            return

        self.imagedir = os.path.dirname(self.imagepath)
        self.imagefiles = self.build_file_list(self.imagedir)

        if self.imagepath in self.imagefiles:
            self.imageindex = self.imagefiles.index(self.imagepath)
        else:
            self.imageindex = 0

    def nextImage(self):
        if not self.imagefileList:
            print("[NAV] No images loaded")
            return

        self.imageindex = (self.imageindex + 1) % len(self.imagefileList)
        self.imagepath = self.imagefileList[self.imageindex]

        print(f"[NAV] Next (right) ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ {self.imagepath}")
        self.showImage(self.imagepath)

    def prevImage(self):
        if not self.imagefileList:
            print("[NAV] No images loaded")
            return

        self.imageindex = (self.imageindex - 1) % len(self.imagefileList)
        self.imagepath = self.imagefileList[self.imageindex]

        print(f"[NAV] Prev (right) ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ {self.imagepath}")
        self.showImage(self.imagepath)

    def reloadImage(self):
        if self.imgpath:
            self.ui.ImageLe.setText(os.path.basename(self.imgpath))

            self.start_image_load(self.refimgpath, target="ref")
            print("[Pixler] Ref image indexed")

            self.sortImgFiles()

    def resize_Image(self):
        if not hasattr(self, "imagepixmap") or self.imagepixmap.isNull():
            print("[ZOOM] No right-panel pixmap available")
            return

        self.imagesize = self.imagepixmap.size()
        self.origheight = self.imagepixmap.height()
        self.origwidth = self.imagepixmap.width()
        print("resizing " + str(self.imagesize))

        target_size = qtc.QSize(
            max(1, int(self.origwidth * self.imagescale)),
            max(1, int(self.origheight * self.imagescale))
        )
        scaled_pixmap = self.imagepixmap.scaled(
            target_size,
            qtc.Qt.KeepAspectRatio,
            transformMode=qtc.Qt.FastTransformation
        )
        self.ui.Image.setPixmap(scaled_pixmap)

    def ExportImage(self):
        pass

    def SaveImageAs(self):
        path = qtw.QFileDialog.getSaveFileName(
            self.ui.centralwidget, 'Save cropped tiff file', '',
            'Tiff files (*.tif)')[0]
        if not path:
            return

        my_image = self.imageqimage if not self.imageqimage.isNull() else self.imagepixmap.toImage()
        self._save_qimage_as_tiff(my_image, path)
        filename = os.path.basename(path)
        self.ui.ImageLE.setText(filename)

        RefImgchangesSaved = True

    def SaveImage(self):

        filename = self.ui.ImageLE.displayText()

        if self.workflowdir:
            path = self.workflowdir + "/" + filename

        else:
            path = qtw.QFileDialog.getSaveFileName(
                self.centralwidget, 'Save modified tif file', '',
                'Tif files (*.tif)')[0]

        if not path:
            return

        my_image = self.imageqimage if not self.imageqimage.isNull() else self.imagepixmap.toImage()
        self._save_qimage_as_tiff(my_image, path)
        filename = os.path.basename(path)
        self.ui.ImageLE.setText(filename)
        #file.close()

        RefImgchangesSaved = True

    def OverwriteRefImg(self):
        path = self.refimgpath
        if not path:
            return

        my_image = self.imageqimage if not self.imageqimage.isNull() else self.imagepixmap.toImage()
        self._save_qimage_as_tiff(my_image, path)
        filename = os.path.basename(path)
        self.ui.RefImgLE.setText(filename)
        #file.close()

        RefImgchangesSaved = True

    def _save_qimage_as_tiff(self, qimage, outfile):
        qimage = self._prepare_output_qimage(qimage)
        buffer = qtc.QBuffer()
        buffer.open(qtc.QBuffer.ReadWrite)
        qimage.save(buffer, "PNG")
        PILimage = pilimg.open(io.BytesIO(buffer.data()))

        # Workflow handoffs standardize on 300-DPI indexed TIFF outputs.
        dpi_x = 300
        dpi_y = 300
        print("Generating: " + outfile)
        if self._source_prefers_bilevel_output():
            PILimage = PILimage.convert("1")
        else:
            PILimage = PILimage.convert("L").convert("P", palette=pilimg.ADAPTIVE, colors=256)
        PILimage.save(outfile, "TIFF", dpi=(dpi_x, dpi_y), compression="tiff_lzw")

    def _normalize_return_geometry(self, qimage):
        if qimage is None or qimage.isNull():
            return qtg.QImage()

        if not hasattr(self, "refimgqimage") or self.refimgqimage.isNull():
            return qimage

        source = self.refimgqimage
        if qimage.width() == source.width() and qimage.height() == source.height():
            return qimage

        canvas = qtg.QImage(source)
        painter = qtg.QPainter(canvas)
        fill_color = self._coerce_fill_color(None, source)
        painter.fillRect(canvas.rect(), fill_color)

        origin = getattr(self, "_last_crop_origin", qtc.QPoint(0, 0)) or qtc.QPoint(0, 0)
        draw_x = max(0, min(int(origin.x()), max(0, canvas.width() - qimage.width())))
        draw_y = max(0, min(int(origin.y()), max(0, canvas.height() - qimage.height())))
        painter.drawImage(draw_x, draw_y, qimage)
        painter.end()

        self._copy_qimage_resolution(source, canvas)
        return canvas

    def returnToCaller(self):
        if not self.subprocess_mode or not self.subprocess_return_path:
            print("[CROP] No subprocess return path available")
            return

        payload = getattr(self, "cropped_qimage", None)
        if payload is None or payload.isNull():
            payload = getattr(self, "imageqimage", None)

        if payload is None or payload.isNull():
            print("[CROP] No crop result available to return")
            return

        payload = self._normalize_return_geometry(payload)
        self._save_qimage_as_tiff(payload, self.subprocess_return_path)
        caller = self.subprocess_caller or "calling module"
        print(f"[CROP] Returned edited result to {caller}: {self.subprocess_return_path}")

        if self.return_button is not None:
            self.return_button.setEnabled(False)

        qtc.QTimer.singleShot(100, self.close)

    def returnCropToMyServer(self):
        self.returnToCaller()

    def changed_Image(self):
        self.ImagechangesSaved = False

    def _crop_rect_from_rubberband(self):
        if self.rubberBand is None or self.rubberBand.width() <= 0 or self.rubberBand.height() <= 0:
            return QRect()

        clip_x = self.rubberBand.x() - int(self.refimg_xoffset)
        clip_y = self.rubberBand.y() - int(self.refimg_yoffset)
        clip_w = self.rubberBand.width()
        clip_h = self.rubberBand.height()

        if self.refimgscale:
            clip_x = int(round(clip_x / self.refimgscale))
            clip_y = int(round(clip_y / self.refimgscale))
            clip_w = int(round(clip_w / self.refimgscale))
            clip_h = int(round(clip_h / self.refimgscale))

        clip_x = max(0, clip_x)
        clip_y = max(0, clip_y)
        clip_w = max(1, clip_w)
        clip_h = max(1, clip_h)

        if not self.refimgpixmap.isNull():
            clip_w = min(clip_w, self.refimgpixmap.width() - clip_x)
            clip_h = min(clip_h, self.refimgpixmap.height() - clip_y)

        return QRect(clip_x, clip_y, clip_w, clip_h)

    def preview_crop_selection(self):
        if self.rubberBand is None or not self.rubberBand.isVisible():
            return

        crop_rect = self._crop_rect_from_rubberband()
        if crop_rect.isNull() or crop_rect.width() <= 0 or crop_rect.height() <= 0:
            return

        self.currentQRect = self.rubberBand.geometry()
        self.clippixmap = self.refimgpixmap.copy(crop_rect)
        if self.clippixmap.isNull():
            print("[CROP] Preview crop pixmap is null")
            return

        print("[CROP] Preview QRect = " + str(crop_rect))
        self.imagepixmap = self.clippixmap
        self.imageqimage = self.clippixmap.toImage()
        self.ui.Image.setAlignment(qtc.Qt.AlignLeft | qtc.Qt.AlignTop)
        self.ui.Image.setPixmap(self.imagepixmap)
        self.resize_Image()

    def _on_crop_overlay_changed(self):
        self.crop_selection_ready = True
        self.preview_crop_selection()

    def apply_crop_selection(self):
        self.preview_crop_selection()
        if self.rubberBand is not None:
            self.rubberBand.hide()
        if self.crop_prompt_dialog is not None:
            self.crop_prompt_dialog.hide()
        self.crop_selection_ready = False
        self.crop_drawing_active = False

    # Page workflow: Sequence MI2C; MilestoneName front_matter_tif_pages_clipped.
    # Page workflow: Sequence MI2C; MilestoneName middle_matter_tif_pages_clipped.
    # Page workflow: Sequence MI2C; MilestoneName back_matter_tif_pages_clipped (VerseSections row).
    # Page workflow: Sequence MI2C; MilestoneName back_matter_tif_pages_clipped.
    def clip(self):
        print("[CUT] Opening cut preview")
        return self._launch_preview_tool(
            self.clip_processor,
            title="Cut Preview",
            params={"background_color": self._background_fill_color_name(self.refimgqimage)},
            enable_crop=True,
        )

    # Page workflow Method "eraser": Sequence MC2E; MilestoneName front_matter_tif_pages_erased.
    # Page workflow Method "eraser": Sequence MC2E; MilestoneName middle_matter_tif_pages_erased.
    # Page workflow Method "eraser": Sequence MC2E; MilestoneName verse_books_tif_pages_erased.
    # Page workflow Method "eraser": Sequence MC2E; MilestoneName back_matter_tif_pages_erased.
    def eraser(self):
        print("[ERASE] Opening preview")
        if not hasattr(self, "refimgqimage") or self.refimgqimage.isNull():
            print("[ERASE] No image loaded")
            return False

        dialog = ImagePreviewDialog(
            self.refimgqimage,
            self.erase_processor,
            {
                "tip_diameter_px": int(self.eraser_tip_diameter),
                "tip_shape": str(self.eraser_tip_shape or "circle"),
                "background_color": self._background_fill_color_name(self.refimgqimage),
                "erase_points": [],
            },
            self,
            enable_crop=False,
            interaction_mode="paint",
            preview_max_dimension=1600,
        )
        dialog.setWindowTitle("Erase Preview")
        max_tip = self._max_eraser_tip_diameter()
        dialog.add_slider("tip_diameter_px", 1, max_tip, min(int(self.eraser_tip_diameter), max_tip))
        dialog.add_choice("tip_shape", ["circle", "square", "diamond"], str(self.eraser_tip_shape or "circle"))

        if dialog.exec_() != qtw.QDialog.Accepted:
            print("[ERASE] Cancelled")
            return False

        self.eraser_tip_diameter = max(1, int(dialog.params.get("tip_diameter_px", self.eraser_tip_diameter)))
        self.eraser_tip_shape = str(dialog.params.get("tip_shape", self.eraser_tip_shape or "circle")).strip().lower() or "circle"
        return self._apply_preview_result(dialog.get_result())

    def _max_eraser_tip_diameter(self):
        if hasattr(self, "ui") and hasattr(self.ui, "LHlineEdit"):
            raw = str(self.ui.LHlineEdit.text() or "").strip()
            if raw.isdigit():
                return max(1, min(1024, int(raw)))

        source = getattr(self, "refimgqimage", None)
        if source is not None and not source.isNull():
            estimated = max(1, int(source.height() / 35))
            return max(1, min(1024, estimated))

        return 128

    def crop_processor(self, qimage, params):
        if not params:
            return qimage

        x = params.get("x", 0)
        y = params.get("y", 0)
        w = params.get("w", qimage.width())
        h = params.get("h", qimage.height())

        self._last_crop_origin = qtc.QPoint(int(x), int(y))

        # safety clamp
        x = max(0, x)
        y = max(0, y)
        w = max(1, w)
        h = max(1, h)

        result = qimage.copy(x, y, w, h)
        self._copy_qimage_resolution(qimage, result)
        return result

    def clip_processor(self, qimage, params):
        if qimage is None or qimage.isNull() or not params:
            return qimage

        x = int(params.get("x", 0))
        y = int(params.get("y", 0))
        w = int(params.get("w", 0))
        h = int(params.get("h", 0))
        if w <= 0 or h <= 0:
            return qimage

        result = qtg.QImage(qimage)
        painter = qtg.QPainter(result)
        painter.fillRect(
            qtc.QRect(x, y, w, h),
            self._coerce_fill_color(params.get("background_color"), qimage),
        )
        painter.end()
        self._copy_qimage_resolution(qimage, result)
        return result

    def erase_processor(self, qimage, params):
        if qimage is None or qimage.isNull() or not params:
            return qimage

        erase_points = params.get("erase_points", [])
        tip_diameter = max(1, int(params.get("tip_diameter_px", params.get("brush_radius", self.eraser_tip_diameter))))
        radius = max(1, int(round(tip_diameter / 2.0)))
        tip_shape = str(params.get("tip_shape", self.eraser_tip_shape or "circle")).strip().lower() or "circle"
        if not erase_points:
            return qimage

        result = qtg.QImage(qimage)
        painter = qtg.QPainter(result)
        fill_color = self._coerce_fill_color(params.get("background_color"), qimage)
        painter.setPen(qtg.QPen(fill_color, 1))
        painter.setBrush(qtg.QBrush(fill_color))
        for point in erase_points:
            x = int(point.get("x", 0))
            y = int(point.get("y", 0))
            if tip_shape == "square":
                painter.drawRect(qtc.QRect(x - radius, y - radius, radius * 2, radius * 2))
            elif tip_shape == "diamond":
                diamond = qtg.QPolygon([
                    qtc.QPoint(x, y - radius),
                    qtc.QPoint(x + radius, y),
                    qtc.QPoint(x, y + radius),
                    qtc.QPoint(x - radius, y),
                ])
                painter.drawPolygon(diamond)
            else:
                painter.drawEllipse(qtc.QPoint(x, y), radius, radius)
        painter.end()
        self._copy_qimage_resolution(qimage, result)
        return result

    def openDenoiseDialog(self):
        return self.openMorphologyDialog(window_title="Denoise Preview")

    def choose_fill_background_color(self):
        color = QColorDialog.getColor(self.fill_background_color, self, "Choose Background Fill Color")
        if not color.isValid():
            return False

        self.fill_background_color = color
        self.statusBar().showMessage("Background fill color set to {}".format(color.name()), 3000)
        return True

    def choose_fill_foreground_color(self):
        color = QColorDialog.getColor(self.fill_foreground_color, self, "Choose Foreground Fill Color")
        if not color.isValid():
            return False

        self.fill_foreground_color = color
        self.statusBar().showMessage("Foreground fill color set to {}".format(color.name()), 3000)
        return True

    def _background_fill_color_name(self, qimage):
        return self._default_background_fill_color(qimage).name()

    def _default_background_fill_color(self, qimage):
        if qimage is not None and not qimage.isNull():
            if qimage.format() in (qtg.QImage.Format_Mono, qtg.QImage.Format_MonoLSB):
                return qtg.QColor("white")
            if qimage.isGrayscale() or qimage.depth() == 8:
                return qtg.QColor("white")

        if isinstance(self.fill_background_color, qtg.QColor) and self.fill_background_color.isValid():
            return qtg.QColor(self.fill_background_color)

        return qtg.QColor("white")

    def _coerce_fill_color(self, color_value, qimage):
        if isinstance(color_value, qtg.QColor) and color_value.isValid():
            return qtg.QColor(color_value)

        if isinstance(color_value, str) and color_value:
            color = qtg.QColor(color_value)
            if color.isValid():
                return color

        return self._default_background_fill_color(qimage)

    def deskew_processor(self, qimage, params=None):
        if qimage is None or qimage.isNull():
            return qtg.QImage()

        cv_image = self._qimage_to_cv_bgr(qimage)
        if cv_image is None:
            return qtg.QImage(qimage)

        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (9, 9), 0)
        thresh = cv2.threshold(
            blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )[1]
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 5))
        dilated = cv2.dilate(thresh, kernel, iterations=5)

        contour_result = cv2.findContours(
            dilated, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
        )
        contours = contour_result[0] if len(contour_result) == 2 else contour_result[1]
        if not contours:
            return qtg.QImage(qimage)

        largest_contour = max(contours, key=cv2.contourArea)
        angle = cv2.minAreaRect(largest_contour)[-1]
        if angle < -45:
            angle = 90 + angle

        (height, width) = cv_image.shape[:2]
        center = (width // 2, height // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            cv_image,
            matrix,
            (width, height),
            flags=cv2.INTER_NEAREST if self._should_preserve_binary_output(qimage) else cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )

        result = self._cv_bgr_to_qimage(rotated)
        if self._should_preserve_binary_output(qimage):
            result = self._convert_qimage_to_bilevel(result)
        self._copy_qimage_resolution(qimage, result)
        return result

    def rotate_preview_processor(self, qimage, params):
        angle = float(params.get("angle", 0))

        if qimage is None or qimage.isNull():
            return qtg.QImage()

        transform_mode = (
            qtc.Qt.FastTransformation
            if self._should_preserve_binary_output(qimage)
            else qtc.Qt.SmoothTransformation
        )
        transform = qtg.QTransform().rotate(angle)
        result = qimage.transformed(transform, mode=transform_mode)
        if self._should_preserve_binary_output(qimage):
            result = self._convert_qimage_to_bilevel(result)
        self._copy_qimage_resolution(qimage, result)
        return result

    def _qimage_to_cv_bgr(self, qimage):
        if qimage is None or qimage.isNull():
            return None

        buffer = qtc.QBuffer()
        buffer.open(qtc.QBuffer.ReadWrite)
        qimage.save(buffer, "PNG")
        pil_image = pilimg.open(io.BytesIO(buffer.data())).convert("RGB")
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    def _cv_bgr_to_qimage(self, cv_image):
        if cv_image is None:
            return qtg.QImage()

        if len(cv_image.shape) == 2:
            rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_GRAY2RGB)
        else:
            rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        return qimage2ndarray.array2qimage(rgb_image, normalize=False)

    def _source_prefers_bilevel_output(self):
        if not self.refimgpath or not os.path.isfile(self.refimgpath):
            return False

        try:
            with pilimg.open(self.refimgpath) as source_image:
                return source_image.mode == "1"
        except Exception as exc:
            print(f"[TIFF SAVE] Could not inspect source mode: {exc}")
            return False

    @staticmethod
    def _is_bilevel_qimage(qimage):
        if qimage is None or qimage.isNull():
            return False

        if qimage.format() in (qtg.QImage.Format_Mono, qtg.QImage.Format_MonoLSB):
            return True

        if qimage.depth() == 1:
            return True

        return qimage.colorCount() == 2

    def _should_preserve_binary_output(self, qimage=None):
        return self._source_prefers_bilevel_output() or self._is_bilevel_qimage(qimage)

    def _prepare_output_qimage(self, qimage):
        if qimage is None or qimage.isNull():
            return qtg.QImage()

        prepared = qtg.QImage(qimage)
        if self._should_preserve_binary_output(qimage):
            prepared = self._convert_qimage_to_bilevel(prepared)

        self._copy_qimage_resolution(qimage, prepared)
        return prepared

    def _convert_qimage_to_bilevel(self, qimage):
        cv_image = self._qimage_to_cv_bgr(qimage)
        if cv_image is None:
            return qtg.QImage(qimage)

        if len(cv_image.shape) == 2:
            gray = cv_image
        else:
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

        _threshold, binary = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        bilevel = qimage2ndarray.array2qimage(binary, normalize=False)
        if bilevel.format() not in (qtg.QImage.Format_Mono, qtg.QImage.Format_MonoLSB):
            bilevel = bilevel.convertToFormat(qtg.QImage.Format_Mono)
        return bilevel

    def _apply_preview_result(self, result):
        if result is None or result.isNull():
            print("[PREVIEW APPLY] No result returned")
            return False

        result = self._prepare_output_qimage(result)

        result_pixmap = qtg.QPixmap.fromImage(result)
        if result_pixmap.isNull():
            print("[PREVIEW APPLY] Result pixmap is null")
            return False

        self.imageqimage = result
        self.imagepixmap = result_pixmap
        self.imagescale = 1.0

        if self.refimgpath:
            self.imagepath = self.refimgpath
            self.imagedir = os.path.dirname(self.refimgpath)
            self.ui.ImageLE.setText(os.path.basename(self.refimgpath))

        if self.subprocess_mode and self.subprocess_return_path and self.return_button is not None:
            self.return_button.setEnabled(True)
            self.statusBar().showMessage("Result ready. Press Return.")

        self.ui.Image.setAlignment(qtc.Qt.AlignLeft | qtc.Qt.AlignTop)
        self.ui.Image.setPixmap(self.imagepixmap)
        self.ui.Image.resize(self.imagepixmap.size())
        print("[PREVIEW APPLY] Result displayed on right panel")
        return True

    def _launch_preview_tool(self, processor, title="Preview", params=None,
                             sliders=None, enable_crop=False,
                             preview_max_dimension=0):
        if not hasattr(self, "refimgqimage") or self.refimgqimage.isNull():
            print("[PREVIEW] No image loaded")
            return False

        dialog = ImagePreviewDialog(
            self.refimgqimage,
            processor,
            params or {},
            self,
            enable_crop=enable_crop,
            preview_max_dimension=preview_max_dimension,
        )
        dialog.setWindowTitle(title)

        for slider in sliders or []:
            dialog.add_slider(*slider)

        if dialog.exec_() != qtw.QDialog.Accepted:
            print("[PREVIEW] Cancelled")
            return False

        return self._apply_preview_result(dialog.get_result())

    @staticmethod
    def _copy_qimage_resolution(source, target):
        if source is None or target is None or source.isNull() or target.isNull():
            return

        target.setDotsPerMeterX(source.dotsPerMeterX())
        target.setDotsPerMeterY(source.dotsPerMeterY())
        target.setDevicePixelRatio(source.devicePixelRatio())

        if hasattr(source, "colorSpace") and hasattr(target, "setColorSpace"):
            try:
                color_space = source.colorSpace()
                if color_space.isValid():
                    target.setColorSpace(color_space)
            except Exception:
                pass

    def actionCropImage(self):
        print("[NEW CROP]")

        if self._launch_preview_tool(
            self.crop_processor,
            title="Crop Preview",
            enable_crop=True,
        ):
            self.cropped_qimage = qtg.QImage(self.imageqimage)
            self.cropped_pixmap = qtg.QPixmap(self.imagepixmap)
            print("[CROP] Using full-resolution crop result: {}x{}".format(
                self.imageqimage.width(), self.imageqimage.height()
            ))

    def deskewRefImg(self):
        print("[DESKEW] Opening preview")
        self._launch_preview_tool(
            self.deskew_processor,
            title="Deskew Preview",
            enable_crop=False,
        )

    def initcvimg(self):
        print("RefImg path = " + self.refimgpath)
        self.cvimg = cv2.imread(self.refimgpath, 1)

    def rotateRefImg(self):
        self.workflowdir = self.pixlerpagesrotatedir
        self._launch_preview_tool(
            self.rotate_preview_processor,
            title="Rotate Preview",
            params={"angle": 0},
            sliders=[("angle", 0, 360, 0)],
            enable_crop=False,
            preview_max_dimension=1600,
        )

    def rotateRefImg90CW(self):
        self.workflowdir = self.pixlerpagesrotatedir
        self._launch_preview_tool(
            self.rotate_preview_processor,
            title="Rotate 90 deg CW Preview",
            params={"angle": 90},
            enable_crop=False,
            preview_max_dimension=1600,
        )

    def rotateRefImg90CCW(self):
        self.workflowdir = self.pixlerpagesrotatedir
        self._launch_preview_tool(
            self.rotate_preview_processor,
            title="Rotate 90 deg CCW Preview",
            params={"angle": -90},
            enable_crop=False,
            preview_max_dimension=1600,
        )

    def rotateRefImg180CW(self):
        self.workflowdir = self.pixlerpagesrotatedir
        self._launch_preview_tool(
            self.rotate_preview_processor,
            title="Rotate 180 deg Preview",
            params={"angle": 180},
            enable_crop=False,
            preview_max_dimension=1600,
        )

    def openMorphologyDialog(self, window_title="Reference Morphology"):
        if not hasattr(self, "refimgqimage") or self.refimgqimage.isNull():
            print("[MORPHOLOGY] No image loaded")
            return False

        dialog = MorphologyDialog(
            self.refimgqimage,
            self.morphology_preview_processor,
            params=self.morphology_params,
            parent=self,
            preview_max_dimension=1600,
        )
        dialog.setWindowTitle(window_title)

        if dialog.exec_() != qtw.QDialog.Accepted:
            print("[MORPHOLOGY] Cancelled")
            return False

        return self.start_morphology_apply(dialog.params)

    def start_morphology_apply(self, params):
        if self._processing_thread is not None:
            qtw.QMessageBox.information(
                self,
                "Morphology In Progress",
                "Wait for the current morphology task to finish.",
            )
            return False

        self._pending_morphology_params = dict(params or {})
        self._processing_thread = qtc.QThread(self)
        self._processing_worker = MorphologyApplyWorker(
            self.refimgqimage,
            self._pending_morphology_params,
        )
        self._processing_worker.moveToThread(self._processing_thread)

        self._processing_thread.started.connect(self._processing_worker.run)
        self._processing_worker.progress.connect(self.on_morphology_progress)
        self._processing_worker.status.connect(self.on_morphology_status)
        self._processing_worker.finished.connect(self.on_morphology_finished)
        self._processing_worker.error.connect(self.on_morphology_error)

        self._processing_worker.finished.connect(self._processing_thread.quit)
        self._processing_worker.finished.connect(self._processing_worker.deleteLater)
        self._processing_worker.error.connect(self._processing_thread.quit)
        self._processing_worker.error.connect(self._processing_worker.deleteLater)
        self._processing_thread.finished.connect(self._processing_thread.deleteLater)
        self._processing_thread.finished.connect(self._on_processing_thread_finished)

        self._processing_thread.start()

        self.statusBar().showMessage("Applying morphology to reference image...")
        self._show_progress(0)
        return True

    def on_morphology_progress(self, value):
        self._set_progress_percent(value)

    def on_morphology_status(self, message):
        self.statusBar().showMessage(message)

    def on_morphology_finished(self, result):
        self._hide_progress(100)
        self.statusBar().showMessage("Morphology result ready.")
        self.morphology_params = dict(self._pending_morphology_params or self.morphology_params)
        self._pending_morphology_params = None
        if not self._apply_preview_result(result):
            qtw.QMessageBox.warning(self, "Morphology Failed", "Processed morphology result could not be applied.")

    def on_morphology_error(self, message):
        self._hide_progress()
        self.statusBar().showMessage(f"Morphology failed: {message}", 5000)
        self._pending_morphology_params = None
        qtw.QMessageBox.warning(self, "Morphology Failed", message)

    def _on_processing_thread_finished(self):
        self._processing_thread = None
        self._processing_worker = None

    def morphology_preview_processor(self, qimage, params):
        return process_morphology_qimage(qimage, params)

class Images:
    def __init__(self, img):
        self.img = cv2.imread(img, 1)
        if self.img.shape[0] / self.img.shape[1] < 0.76:
            self.img_width = 1100
            self.img_height = int(self.img_width * self.img.shape[0] / self.img.shape[1])
        else:
            self.img_height = 700
            self.img_width = int(self.img_height * self.img.shape[1] / self.img.shape[0])

        self.img = cv2.resize(self.img, (self.img_width, self.img_height))
        self.img_copy = deepcopy(self.img)
        self.grand_img_copy = deepcopy(self.img)

        self.img_name = img.split('/')[-1].split(".")[0]
        self.img_format = img.split('/')[-1].split(".")[1]

        self.left, self.right, self.top, self.cvbottom = None, None, None, None

    def auto_contrast(self):
        clip_hist_percent = 20
        gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)

        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist_size = len(hist)
        accumulator = [float(hist[0])]
        for index in range(1, hist_size):
            accumulator.append(accumulator[index - 1] + float(hist[index]))
        maximum = accumulator[-1]
        clip_hist_percent *= (maximum / 100.0)
        clip_hist_percent /= 2.0
        minimum_gray = 0
        while accumulator[minimum_gray] < clip_hist_percent:
            minimum_gray += 1
        maximum_gray = hist_size - 1
        while accumulator[maximum_gray] >= (maximum - clip_hist_percent):
            maximum_gray -= 1
        alpha = 255 / (maximum_gray - minimum_gray)
        beta = -minimum_gray * alpha

        self.img = cv2.convertScaleAbs(self.img, alpha=alpha, beta=beta)

    def auto_sharpen(self):
        self.img = cv2.detailEnhance(self.img, sigma_s=10, sigma_r=0.3)

    def auto_cartoon(self, style=0):
        edges1 = cv2.bitwise_not(cv2.Canny(self.img, 100, 200))
        gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, 5)
        edges2 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 7, 7)
        dst = cv2.edgePreservingFilter(self.img, flags=2, sigma_s=64, sigma_r=0.25)

        if not style:
            # less blurry
            self.img = cv2.bitwise_and(dst, dst, mask=edges1)
        else:
            # more blurry
            self.img = cv2.bitwise_and(dst, dst, mask=edges2)

    def auto_invert(self):
        self.img = cv2.bitwise_not(self.img)

    def change_b_c(self, alpha=1, beta=0):
        # contrast from 0 to 3, brightness from -100 to 100
        self.img = cv2.convertScaleAbs(self.img, alpha=alpha, beta=beta)

    def change_saturation(self, value):
        # -300 to 300
        img_hsv = cv2.cvtColor(self.img, cv2.COLOR_BGR2HSV).astype("float32")
        (h, s, v) = cv2.split(img_hsv)
        s += value
        s = np.clip(s, 0, 255)
        img_hsv = cv2.merge([h, s, v])
        self.img = cv2.cvtColor(img_hsv.astype("uint8"), cv2.COLOR_HSV2BGR)

    def remove_color(self, color):
        h = color.lstrip('#')
        color = np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)])

        img_hsv = cv2.cvtColor(self.img, cv2.COLOR_BGR2HSV).astype("float32")
        low = np.array([color[0] - 15, 0, 20])
        high = np.array([color[0] + 15, 255, 255])
        mask = cv2.inRange(img_hsv, low, high)
        img_hsv[mask > 0] = (0, 0, 255)
        self.img = cv2.cvtColor(img_hsv.astype("uint8"), cv2.COLOR_HSV2BGR)

    def crop_img(self, left, right, top, bottom):
        self.img = self.img[left:right, top:bottom]

    def rotate_img(self, angle, crop=False, flip=[False, False]):
        self.reset(flip)
        if not crop:
            self.img = cv2.resize(self.img, (0, 0), fx=0.5, fy=0.5)
            w, h = self.img.shape[1], self.img.shape[0]
        else:
            w, h = self.img_width, self.img_height

        self.img = ndimage.rotate(self.img, angle)

        angle = math.radians(angle)
        quadrant = int(math.floor(angle / (math.pi / 2))) & 3
        sign_alpha = angle if ((quadrant & 1) == 0) else math.pi - angle
        alpha = (sign_alpha % math.pi + math.pi) % math.pi
        bb_w = w * math.cos(alpha) + h * math.sin(alpha)
        bb_h = w * math.sin(alpha) + h * math.cos(alpha)
        gamma = math.atan2(bb_w, bb_w) if (w < h) else math.atan2(bb_w, bb_w)
        delta = math.pi - alpha - gamma
        length = h if (w < h) else w
        d = length * math.cos(alpha)
        a = d * math.sin(alpha) / math.sin(delta)
        y = a * math.cos(gamma)
        x = y * math.tan(gamma)
        wr, hr = bb_w - 2 * x, bb_h - 2 * y

        midpoint = (np.array(self.img.shape[:-1]) // 2)[::-1]
        half_w, half_h = wr // 2, hr // 2
        self.left, self.right, self.top, self.bottom = int(midpoint[0] - half_w), int(midpoint[0] + half_w), \
                                                       int(midpoint[1] - half_h), int(midpoint[1] + half_h)

    def detect_face(self):
        face_cascade = cv2.CascadeClassifier('data/haarcascade_frontalface_alt2.xml')
        gray_scale_img = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
        face_coord = face_cascade.detectMultiScale(gray_scale_img)

        return face_coord

    def bypass_censorship(self):
        width = self.img.shape[1]
        height = self.img.shape[0]
        smaller_img = cv2.resize(self.img, (width // 2, height // 2))
        image = np.zeros(self.img.shape, np.uint8)

        try:
            image[:height // 2, :width // 2] = cv2.rotate(smaller_img, cv2.cv2.ROTATE_180)
            image[height // 2:, :width // 2] = smaller_img
            image[height // 2:, width // 2:] = cv2.rotate(smaller_img, cv2.cv2.ROTATE_180)
            image[:height // 2, width // 2:] = smaller_img
        except:
            try:
                image[:height // 2, :width // 2] = cv2.rotate(smaller_img, cv2.cv2.ROTATE_180)
                image[height // 2 + 1:, :width // 2] = smaller_img
                image[height // 2 + 1:, width // 2:] = cv2.rotate(smaller_img, cv2.cv2.ROTATE_180)
                image[:height // 2, width // 2:] = smaller_img
            except:
                image[:height // 2, :width // 2] = cv2.rotate(smaller_img, cv2.cv2.ROTATE_180)
                image[height // 2:, :width // 2] = smaller_img
                image[height // 2:, width // 2 + 1:] = cv2.rotate(smaller_img, cv2.cv2.ROTATE_180)
                image[:height // 2, width // 2 + 1:] = smaller_img
        self.img = image

    def save_img(self, file):
        cv2.imwrite(file, self.img)

    def reset(self, flip=None):
        if flip is None:
            flip = [False, False]
        self.img = deepcopy(self.img_copy)
        if flip[0]:
            self.img = cv2.flip(self.img, 0)
        if flip[1]:
            self.img = cv2.flip(self.img, 1)

    def grand_reset(self):
        self.img = deepcopy(self.grand_img_copy)
        self.img_copy = deepcopy(self.grand_img_copy)

class Brightness(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi(f"{pathlib.Path(__file__).parent.absolute()}/ui/brightness_btn.ui", self)

        self.frame = self.findChild(QFrame, "frame")
        self.vbox2 = self.findChild(QVBoxLayout, "vbox2")
        self.y_btn = self.findChild(QPushButton, "y_btn")
        self.y_btn.setIcon(QIcon(f"{pathlib.Path(__file__).parent.absolute()}/icon/check.png"))
        self.y_btn.setStyleSheet("QPushButton{border: 0px solid;}")
        self.y_btn.setIconSize(QSize(70, 70))
        self.n_btn = self.findChild(QPushButton, "n_btn")
        self.n_btn.setIcon(QIcon(f"{pathlib.Path(__file__).parent.absolute()}/icon/cross.png"))
        self.n_btn.setStyleSheet("QPushButton{border: 0px solid;}")
        self.n_btn.setIconSize(QSize(70, 70))

        self.pten = self.findChild(QPushButton, "pten")
        self.pten.setStyleSheet("QPushButton{border: 0px solid;}")
        self.mten = self.findChild(QPushButton, "mten")
        self.mten.setStyleSheet("QPushButton{border: 0px solid;}")

class Filter(QWidget):
    def __init__(self, main):
        super().__init__()
        uic.loadUi(f"{pathlib.Path(__file__).parent.absolute()}/ui/filter_frame.ui", self)
        self.img_class, self.update_img, self.base_frame, self.vbox = \
            main.img_class, main.update_img, main.base_frame, main.vbox

        self.frame = self.findChild(QFrame, "frame")
        self.contrast_btn = self.findChild(QPushButton, "contrast_btn")
        self.sharpen_btn = self.findChild(QPushButton, "sharpen_btn")
        self.cartoon_btn = self.findChild(QPushButton, "cartoon_btn")
        self.cartoon_btn1 = self.findChild(QPushButton, "cartoon_btn2")
        self.invert_btn = self.findChild(QPushButton, "invert_btn")
        self.bypass_btn = self.findChild(QPushButton, "bypass_btn")

        self.y_btn = self.findChild(QPushButton, "y_btn")
        self.y_btn.setIcon(QIcon(f"{pathlib.Path(__file__).parent.absolute()}/icon/check.png"))
        self.y_btn.setStyleSheet("QPushButton{border: 0px solid;}")
        self.y_btn.setIconSize(QSize(60, 60))
        self.n_btn = self.findChild(QPushButton, "n_btn")
        self.n_btn.setIcon(QIcon(f"{pathlib.Path(__file__).parent.absolute()}/icon/cross.png"))
        self.n_btn.setStyleSheet("QPushButton{border: 0px solid;}")
        self.n_btn.setIconSize(QSize(60, 60))

        self.y_btn.clicked.connect(lambda _: self.click_y())
        self.n_btn.clicked.connect(lambda _: self.click_n())
        self.contrast_btn.clicked.connect(lambda _: self.click_contrast())
        self.sharpen_btn.clicked.connect(lambda _: self.click_sharpen())
        self.cartoon_btn.clicked.connect(lambda _: self.click_cartoon())
        self.cartoon_btn1.clicked.connect(lambda _: self.click_cartoon1())
        self.invert_btn.clicked.connect(lambda _: self.click_invert())
        self.bypass_btn.clicked.connect(lambda _: self.click_bypass())

    def click_contrast(self):
        self.img_class.auto_contrast()
        self.update_img()
        self.contrast_btn.clicked.disconnect()

    def click_sharpen(self):
        self.img_class.auto_sharpen()
        self.update_img()
        self.sharpen_btn.clicked.disconnect()

    def click_cartoon(self):
        self.img_class.auto_cartoon()
        self.update_img()
        self.cartoon_btn.clicked.disconnect()

    def click_cartoon1(self):
        self.img_class.auto_cartoon(1)
        self.update_img()
        self.cartoon_btn1.clicked.disconnect()

    def click_invert(self):
        self.img_class.auto_invert()
        self.update_img()
        self.invert_btn.clicked.disconnect()

    def click_bypass(self):
        self.img_class.bypass_censorship()
        self.update_img()
        self.bypass_btn.clicked.disconnect()

    def click_y(self):
        self.frame.setParent(None)
        self.img_class.img_copy = deepcopy(self.img_class.img)
        self.img_class.grand_img_copy = deepcopy(self.img_class.img)
        self.vbox.addWidget(self.base_frame)

    def click_n(self):
        if not np.array_equal(self.img_class.grand_img_copy, self.img_class.img):
            msg = QMessageBox.question(self, "Cancel edits", "Confirm to discard all the changes?   ",
                                       QMessageBox.Yes | QMessageBox.No)
            if msg != QMessageBox.Yes:
                return False

        self.frame.setParent(None)
        self.img_class.grand_reset()
        self.update_img()
        self.vbox.addWidget(self.base_frame)

class Adjust(QWidget):
    def __init__(self, main):
        super().__init__()
        uic.loadUi(f"{pathlib.Path(__file__).parent.absolute()}/ui/adjust_frame.ui", self)
        self.get_zoom_factor = main.get_zoom_factor

        self.img_class, self.update_img, self.base_frame = main.img_class, main.update_img, main.base_frame
        self.rb, self.vbox, self.flip, self.zoom_factor = main.rb, main.vbox, main.flip, main.zoom_factor
        self.zoom_moment, self.slider, self.gv, self.vbox1 = main.zoom_moment, main.slider, main.gv, main.vbox1
        self.start_detect = False

        self.frame = self.findChild(QFrame, "frame")
        self.crop_btn = self.findChild(QPushButton, "crop_btn")
        self.rotate_btn = self.findChild(QPushButton, "rotate_btn")
        self.brightness_btn = self.findChild(QPushButton, "brightness_btn")
        self.contrast_btn = self.findChild(QPushButton, "contrast_btn")
        self.saturation_btn = self.findChild(QPushButton, "saturation_btn")
        self.mask_btn = self.findChild(QPushButton, "mask_btn")

        self.y_btn = self.findChild(QPushButton, "y_btn")
        self.y_btn.setIcon(QIcon(f"{pathlib.Path(__file__).parent.absolute()}/icon/check.png"))
        self.y_btn.setStyleSheet("QPushButton{border: 0px solid;}")
        self.y_btn.setIconSize(QSize(60, 60))
        self.n_btn = self.findChild(QPushButton, "n_btn")
        self.n_btn.setIcon(QIcon(f"{pathlib.Path(__file__).parent.absolute()}/icon/cross.png"))
        self.n_btn.setStyleSheet("QPushButton{border: 0px solid;}")
        self.n_btn.setIconSize(QSize(60, 60))

        self.y_btn.clicked.connect(lambda _: self.click_y())
        self.n_btn.clicked.connect(lambda _: self.click_n())
        #self.crop_btn.clicked.connect(lambda _: self.click_crop())
        self.rotate_btn.clicked.connect(lambda _: self.click_crop(rotate=True))
        self.brightness_btn.clicked.connect(lambda _: self.click_brightness())
        self.contrast_btn.clicked.connect(lambda _: self.click_brightness(mode=1))
        self.saturation_btn.clicked.connect(lambda _: self.click_brightness(mode=2))
        self.mask_btn.clicked.connect(lambda _: self.click_brightness(mode=3))

        dialog = ImagePreviewDialog(
        parent=self,
        original_qimage=self.refimgqimage,
        processor=crop_processor
)
        # Add controls (simple first pass)
        dialog.add_slider("x", 0, self.refimgqimage.width(), 0)
        dialog.add_slider("y", 0, self.refimgqimage.height(), 0)
        dialog.add_slider("w", 1, self.refimgqimage.width(), self.refimgqimage.width())
        dialog.add_slider("h", 1, self.refimgqimage.height(), self.refimgqimage.height())

        if dialog.exec_() == qtw.QDialog.Accepted:
            result = dialog.get_result()

            if result:
                print("[Crop] Applying result")

                # ÃƒÂ°Ã…Â¸Ã¢â‚¬ÂÃ‚Â¥ IMPORTANT: integrate with your pipeline
                self.refimgqimage = result
                self.refimgpixmap = qtg.QPixmap.fromImage(result)

                self.ui.RefImg.setPixmap(self.refimgpixmap)

    def click_crop(self, rotate=False):
        def click_y1():
            if rotate:
                self.img_class.rotate_img(self.rotate_value, crop=True, flip=self.flip)
                self.img_class.crop_img(int(self.rb.top * 2 / self.zoom_factor),
                                        int(self.rb.bottom * 2 / self.zoom_factor),
                                        int(self.rb.left * 2 / self.zoom_factor),
                                        int(self.rb.right * 2 / self.zoom_factor))
            else:
                self.img_class.reset(self.flip)
                self.img_class.crop_img(int(self.rb.top / self.zoom_factor), int(self.rb.bottom / self.zoom_factor),
                                        int(self.rb.left // self.zoom_factor), int(self.rb.right // self.zoom_factor))

            self.update_img()
            self.zoom_moment = False

            self.img_class.img_copy = deepcopy(self.img_class.img)
            self.slider.setParent(None)
            self.slider.valueChanged.disconnect()
            #crop_frame.frame.setParent(None)
            self.vbox.addWidget(self.frame)
            self.rb.close()

        def click_n1():
            if not np.array_equal(img_copy, self.img_class.img):
                msg = QMessageBox.question(self, "Cancel edits", "Confirm to discard all the changes?   ",
                                           QMessageBox.Yes | QMessageBox.No)
                if msg != qtw.MessageBox.Yes:
                    return False

            self.img_class.reset()
            self.update_img()
            self.zoom_moment = False

            self.slider.setParent(None)
            self.slider.valueChanged.disconnect()
            #crop_frame.frame.setParent(None)
            self.vbox.addWidget(self.frame)
            self.rb.close()

        def change_slide():
            self.rotate_value = self.slider.value()
            self.slider.setValue(self.rotate_value)

            self.img_class.rotate_img(self.rotate_value)

            self.rb.setGeometry(int(self.img_class.left * self.zoom_factor), int(self.img_class.top * self.zoom_factor),
                                int((self.img_class.right - self.img_class.left) * self.zoom_factor),
                                int((self.img_class.bottom - self.img_class.top) * self.zoom_factor))

            self.rb.show()
            self.rb.raise_()
            self.update_img(True)

        def add_90():
            if self.rotate_value <= 270:
                self.rotate_value += 90
            else:
                self.rotate_value = 360
            self.slider.setValue(self.rotate_value)
            change_slide()

        def subtract_90():
            if self.rotate_value >= 90:
                self.rotate_value -= 90
            else:
                self.rotate_value = 0
            self.slider.setValue(self.rotate_value)
            change_slide()

        def vertical_flip():
            nonlocal vflip_ct
            self.img_class.img = cv2.flip(self.img_class.img, 0)
            if rotate:
                self.update_img(True)
            else:
                self.update_img()
            vflip_ct += 1
            self.flip[0] = vflip_ct % 2 == 1

        def horizontal_flip():
            nonlocal hflip_ct
            self.img_class.img = cv2.flip(self.img_class.img, 1)
            if rotate:
                self.update_img(True)
            else:
                self.update_img()
            hflip_ct += 1
            self.flip[1] = hflip_ct % 2 == 1

        crop_frame = self.click_crop()
        crop_frame.n_btn.clicked.connect(click_n1)
        crop_frame.y_btn.clicked.connect(click_y1)
        crop_frame.rotate.clicked.connect(add_90)
        crop_frame.rotatect.clicked.connect(subtract_90)
        crop_frame.vflip.clicked.connect(vertical_flip)
        crop_frame.hflip.clicked.connect(horizontal_flip)
        self.flip = [False, False]
        vflip_ct = 2
        hflip_ct = 2

        self.frame.setParent(None)

        self.zoom_factor = self.get_zoom_factor()

        self.rb = ResizableRubberBand(self)
        self.rb.setGeometry(0, 0, int(self.img_class.img.shape[1] * self.zoom_factor),
                    int(self.img_class.img.shape[0] * self.zoom_factor))
        self.rb.show()
        self.rb.raise_()
        self.img_class.change_b_c(beta=-40)
        self.slider.valueChanged.connect(change_slide)


        if not rotate:
            self.update_img()
        else:
            self.vbox1.insertWidget(1, self.slider)
            self.slider.setRange(0, 360)
            self.slider.setValue(0)
            self.zoom_moment = True
            self.img_class.rotate_img(0)
            self.rb.setGeometry(0, 0, int(self.img_class.img.shape[1] * self.zoom_factor),
                                int(self.img_class.img.shape[0] * self.zoom_factor))
            self.rb.show()
            self.rb.raise_()
            self.update_img(True)

        img_copy = deepcopy(self.img_class.img)

    def click_brightness(self, mode=0):
        def click_y1():
            self.img_class.img_copy = deepcopy(self.img_class.img)
            if mode != 3:
                self.slider.setParent(None)
                self.slider.valueChanged.disconnect()
            brightness_frame.frame.setParent(None)
            self.vbox.addWidget(self.frame)

        def click_n1():
            if not np.array_equal(self.img_class.img_copy, self.img_class.img):
                msg = QMessageBox.question(self, "Cancel edits", "Confirm to discard all the changes?   ",
                                           QMessageBox.Yes | QMessageBox.No)
                if msg != QMessageBox.Yes:
                    return False
            self.img_class.reset()
            self.update_img()

            if mode != 3:
                self.slider.setParent(None)
                self.slider.valueChanged.disconnect()
            brightness_frame.frame.setParent(None)
            self.vbox.addWidget(self.frame)

        def change_slide():
            self.brightness_value = self.slider.value()
            self.img_class.reset()
            self.img_class.change_b_c(beta=self.brightness_value)
            self.update_img()

        def change_slide_contr():
            self.contrast_value = self.slider.value() / 100
            self.img_class.reset()
            self.img_class.change_b_c(alpha=self.contrast_value)
            self.update_img()

        def change_slide_sat():
            self.saturation_value = self.slider.value() / 250
            self.img_class.reset()
            self.img_class.change_b_c(alpha=self.saturation_value)
            self.update_img()

        def color_dialog():
            color = QColorDialog.getColor()
            self.img_class.remove_color(color.name())

        brightness_frame = Brightness()
        brightness_frame.y_btn.clicked.connect(click_y1)
        brightness_frame.n_btn.clicked.connect(click_n1)

        self.frame.setParent(None)
        self.vbox.addWidget(brightness_frame.frame)

        if mode == 1:
            self.vbox1.insertWidget(1, self.slider)
            self.slider.setRange(0, 300)
            self.slider.setValue(100)
            self.slider.valueChanged.connect(change_slide_contr)
        elif mode == 2:
            self.vbox1.insertWidget(1, self.slider)
            self.slider.setRange(0, 1000)
            self.slider.setValue(250)
            self.slider.valueChanged.connect(change_slide_sat)
        elif mode == 3:
            btnn = QPushButton("Select color", brightness_frame)
            #btnn.setFont(QFont("Neue Haas Grotesk Text Pro Medi", 14))
            btnn.setStyleSheet("QPushButton{border: 0px solid;}")
            btnn.setMaximumHeight(50)
            #btnn.clicked.connect(color_dialog)
            brightness_frame.vbox2.insertWidget(0, btnn)
        else:
            self.vbox1.insertWidget(1, self.slider)
            self.slider.setRange(-120, 160)
            self.slider.setValue(0)
            self.slider.valueChanged.connect(change_slide)

    def click_y(self):
        self.start_detect = False
        self.frame.setParent(None)
        self.img_class.img_copy = deepcopy(self.img_class.img)
        self.img_class.grand_img_copy = deepcopy(self.img_class.img)
        self.vbox.addWidget(self.base_frame)

    def click_n(self):
        if not np.array_equal(self.img_class.grand_img_copy, self.img_class.img):
            msg = QMessageBox.question(self, "Cancel edits", "Confirm to discard all the changes?   ",
                                       QMessageBox.Yes | QMessageBox.No)
            if msg != QMessageBox.Yes:
                return False

        self.start_detect = False
        self.frame.setParent(None)
        self.img_class.grand_reset()
        self.update_img()
        self.vbox.addWidget(self.base_frame)

class ResizableRubberBand(QWidget):
    """Crop overlay with sibling grip handles that stay visible above it.

    The previous child-handle approach could be clipped or hidden by the
    translucent overlay on some Qt/Windows combinations.  These grips are
    parented to the same MyPixler window as the overlay, so they are independent
    widgets that can always be raised above the crop rectangle.
    """

    HANDLE_SIZE = 18
    MIN_SIZE = 24

    def __init__(self, parent=None):
        super(ResizableRubberBand, self).__init__(parent)

        self.setMinimumSize(self.MIN_SIZE, self.MIN_SIZE)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(
            "border: 2px dashed #ffbf00;"
            "background-color: rgba(255, 191, 0, 35);"
        )

        self._drag_handle = None
        self._drag_start_global = QPoint()
        self._drag_start_geometry = QRect()
        self._handles = {}
        self._create_handles()
        self._set_handles_visible(False)

    def _create_handles(self):
        parent = self.parentWidget()
        cursor_map = {
            "nw": Qt.SizeFDiagCursor,
            "n": Qt.SizeVerCursor,
            "ne": Qt.SizeBDiagCursor,
            "e": Qt.SizeHorCursor,
            "se": Qt.SizeFDiagCursor,
            "s": Qt.SizeVerCursor,
            "sw": Qt.SizeBDiagCursor,
            "w": Qt.SizeHorCursor,
        }

        for name, cursor in cursor_map.items():
            handle = QFrame(parent)
            handle.setObjectName("cropGrip_{}".format(name))
            handle.setCursor(cursor)
            handle.setFixedSize(self.HANDLE_SIZE, self.HANDLE_SIZE)
            handle.setStyleSheet(
                "QFrame { background-color: #ff0000; border: 2px solid #ffffff; }"
                "QFrame:hover { background-color: #ffff00; border: 2px solid #000000; }"
            )
            handle.setToolTip("Drag to resize crop ({})".format(name))
            handle.setMouseTracking(True)
            handle.installEventFilter(self)
            self._handles[name] = handle

    def setGeometry(self, *args):
        super().setGeometry(*args)
        self._position_handles()
        self._raise_handles()

    def show(self):
        super().show()
        self._position_handles()
        self._set_handles_visible(True)
        self._raise_handles()
        print("[CROP UI] RubberBand shown with {} sibling grip handles".format(len(self._handles)))

    def hide(self):
        self._set_handles_visible(False)
        super().hide()

    def eventFilter(self, obj, event):
        handle_name = None
        for name, handle in self._handles.items():
            if obj is handle:
                handle_name = name
                break

        if handle_name is None:
            return super().eventFilter(obj, event)

        if event.type() == qtc.QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            print("[CROP UI] Grip press: {}".format(handle_name))
            self._drag_handle = handle_name
            self._drag_start_global = event.globalPos()
            self._drag_start_geometry = self.geometry()
            event.accept()
            return True

        if event.type() == qtc.QEvent.MouseMove and self._drag_handle:
            delta = event.globalPos() - self._drag_start_global
            self._resize_from_handle(self._drag_handle, delta)
            event.accept()
            return True

        if event.type() == qtc.QEvent.MouseButtonRelease and self._drag_handle:
            print("[CROP UI] Grip release: {}".format(self._drag_handle))
            self._drag_handle = None
            parent = self.parentWidget()
            if parent is not None and hasattr(parent, "_on_crop_overlay_changed"):
                parent._on_crop_overlay_changed()
            event.accept()
            return True

        return super().eventFilter(obj, event)

    def _resize_from_handle(self, handle_name, delta):
        rect = QRect(self._drag_start_geometry)

        if "n" in handle_name:
            rect.setTop(rect.top() + delta.y())
        if "s" in handle_name:
            rect.setBottom(rect.bottom() + delta.y())
        if "w" in handle_name:
            rect.setLeft(rect.left() + delta.x())
        if "e" in handle_name:
            rect.setRight(rect.right() + delta.x())

        rect = self._normalized_minimum_rect(rect)
        rect = self._clamped_to_parent(rect)
        self.setGeometry(rect)

    def _normalized_minimum_rect(self, rect):
        rect = rect.normalized()

        if rect.width() < self.MIN_SIZE:
            if self._drag_handle and "w" in self._drag_handle:
                rect.setLeft(rect.right() - self.MIN_SIZE + 1)
            else:
                rect.setRight(rect.left() + self.MIN_SIZE - 1)

        if rect.height() < self.MIN_SIZE:
            if self._drag_handle and "n" in self._drag_handle:
                rect.setTop(rect.bottom() - self.MIN_SIZE + 1)
            else:
                rect.setBottom(rect.top() + self.MIN_SIZE - 1)

        return rect

    def _clamped_to_parent(self, rect):
        parent = self.parentWidget()
        if parent is None:
            return rect

        bounds = parent.rect()
        if rect.left() < bounds.left():
            rect.setLeft(bounds.left())
        if rect.top() < bounds.top():
            rect.setTop(bounds.top())
        if rect.right() > bounds.right():
            rect.setRight(bounds.right())
        if rect.bottom() > bounds.bottom():
            rect.setBottom(bounds.bottom())
        return rect

    def _set_handles_visible(self, visible):
        for handle in self._handles.values():
            handle.setVisible(visible)

    def _raise_handles(self):
        self.raise_()
        for handle in self._handles.values():
            handle.raise_()

    def _position_handles(self):
        if not self._handles:
            return

        rect = self.geometry()
        size = self.HANDLE_SIZE
        half = size // 2
        center_x = rect.left() + rect.width() // 2
        center_y = rect.top() + rect.height() // 2

        positions = {
            "nw": (rect.left() - half, rect.top() - half),
            "n": (center_x - half, rect.top() - half),
            "ne": (rect.right() - half, rect.top() - half),
            "e": (rect.right() - half, center_y - half),
            "se": (rect.right() - half, rect.bottom() - half),
            "s": (center_x - half, rect.bottom() - half),
            "sw": (rect.left() - half, rect.bottom() - half),
            "w": (rect.left() - half, center_y - half),
        }

        parent = self.parentWidget()
        bounds = parent.rect() if parent is not None else QRect()
        for name, (x, y) in positions.items():
            if parent is not None:
                x = max(bounds.left(), min(x, bounds.right() - size + 1))
                y = max(bounds.top(), min(y, bounds.bottom() - size + 1))
            self._handles[name].move(x, y)

    def resizeEvent(self, event):
        self._position_handles()
        self._raise_handles()
        super().resizeEvent(event)

    def moveEvent(self, event):
        self._position_handles()
        self._raise_handles()
        super().moveEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        self._position_handles()
        self._set_handles_visible(True)
        self._raise_handles()

def main():
    import os
    import sys
    image_path = None   # ÃƒÂ¢Ã…â€œÃ¢â‚¬Â¦ define it

    if len(sys.argv) >= 2:
        image_path = os.path.abspath(sys.argv[1])

    app = qtw.QApplication(sys.argv)

    main = PixlerMain(image_path, launch_args=sys.argv[1:])
    main.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
