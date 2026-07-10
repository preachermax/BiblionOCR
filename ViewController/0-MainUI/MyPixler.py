# -*- coding: utf-8 -*-

# Python imports
import os
import re
import json
import io
import pathlib
from gui_runtime_env import sanitize_current_process_and_reexec


sanitize_current_process_and_reexec()

import tiffcapture
import qimage2ndarray
from PIL import Image as pilimg
import shutil
import cv2
import numpy as np
from scipy import ndimage
import math
from copy import deepcopy
from SessionManager import SessionManager, build_runtime_paths

# Path configuration and directory setup
RUNTIME_PATHS = build_runtime_paths(__file__)
script_dir = RUNTIME_PATHS.script_dir
project_root = RUNTIME_PATHS.project_root
model_dir = RUNTIME_PATHS.model_dir
data_dir = RUNTIME_PATHS.data_dir
image_dir = RUNTIME_PATHS.image_dir
text_dir = RUNTIME_PATHS.text_dir
train_dir = RUNTIME_PATHS.train_dir
session_dir = RUNTIME_PATHS.session_dir


from HelpSystem import add_help_menu
from Core.project_tracking import ProjectWorkflowTracker
# PyQt5 imports
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QMessageBox, QFrame, QColorDialog
from PyQt5 import QtWidgets as qtw
from PyQt5.QtGui import QIcon
from PyQt5 import QtGui as qtg
from PyQt5.QtCore import QPoint, QRect, QSize, Qt
from PyQt5 import QtCore as qtc
from ImageLoadWorker import ImageLoadWorker
from TiffStackWorker import TiffStackWorker
# Custom imports
from PreProcess import PreProcess as pp
#from MyScanner import Ui_Scanner
from MyPixlerUI import Ui_Pixler
from Adjust import crop_processor
from ImagePreviewDialog import ImagePreviewDialog
from MorphologyDialog import MorphologyDialog
from LocalFileDrop import LocalFileDropMixin
from ProjectTrackingDialog import ProjectTrackingDialog
from print_menu_support import install_print_menu_support, image_target


# Dialog Imports
from Dialogs.ExtractDialog import Ui_ExtractDialog
from Dialogs.pdf4tifDialog import Ui_pdf4tifDialog
from Dialogs.pdf2tifDialog import Ui_pdf2tifDialog
from Dialogs.tif2monoDialog import Ui_tif2monoDialog
from Dialogs.pdf2tifDialog import Ui_pdf2tifDialog
from Dialogs.mono2pngDialog import Ui_mono2pngDialog
from Dialogs.deskew_monoDialog import Ui_deskew_monoDialog
from Dialogs.crop_languagesDialog import Ui_crop_languagesDialog
from Dialogs.greekmono2pngDialog import Ui_greekmono2pngDialog
from Dialogs.deskew_greekmonoDialog import Ui_deskew_greekmonoDialog
from Dialogs.greekresizepngDialog import Ui_greekresizepngDialog
from Dialogs.latinmono2pngDialog import Ui_latinmono2pngDialog
from Dialogs.deskew_latinmonoDialog import Ui_deskew_latinmonoDialog
from Dialogs.latinresizepngDialog import Ui_latinresizepngDialog

# The new Stream Object which replaces the default stream associated with sys.stdout
# This object just puts data in a queue!
# class WriteStream(object):
#     def __init__(self,queue):
#         self.queue = queue

#     def write(self, text):
#         self.queue.put(text)

#     def flush(self):
#         """
#         Stream flush implementation
#         """
#         pass

# A QObject (to be run in a QThread) which sits waiting for data to come through a Queue.Queue().
# It blocks until data is available, and once it has got something from the queue, it sends
# it to the "MainThread" by emitting a Qt Signal
# class ThreadConsoleTextQueueReceiver(qtc.QObject):

#     queue_element_received_signal = qtc.pyqtSignal(str)

#     def __init__(self, q: Queue, *args, **kwargs):
#         qtc.QObject.__init__(self, *args, **kwargs)
#         self.queue = q

#     @qtc.pyqtSlot()
#     def run(self):
#         self.queue_element_received_signal.emit('---> Console text queue reception Started <---\n')
#         while True:
#             text = self.queue.get()
#             self.queue_element_received_signal.emit(text)

#     @qtc.pyqtSlot()
#     def finished(self):
#         self.queue_element_received_signal.emit('---> Console text queue reception Stopped <---\n')


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
        self.eraser_tip_size = 24
        self.rubberBand = None
        self.return_to_server_button = None
        self.crop_prompt_dialog = None
        self.crop_selection_ready = False
        self.crop_drawing_active = False
        self.shared_session_manager = SessionManager()
        self.current_project_root = self.shared_session_manager.get_active_project_root() or None
        self._active_project_sync_timer = None

        # -------------------------
        # Phase 2 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â ARGUMENT HANDLING (MyServer ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ MyPixler)
        # -------------------------
        import sys

        if launch_args is not None:
            parsed_imgpath, subprocess_mode, return_path = self._parse_launch_arguments(launch_args)
            self.subprocess_mode = subprocess_mode
            self.subprocess_return_path = return_path
            if parsed_imgpath:
                imgpath = parsed_imgpath
        elif imgpath is None and len(sys.argv) > 1:
            imgpath, subprocess_mode, return_path = self._parse_launch_arguments(sys.argv[1:])
            self.subprocess_mode = subprocess_mode
            self.subprocess_return_path = return_path

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
        install_print_menu_support(
            self,
            {
                "actionPrint_Ref_Image": image_target(
                    lambda: self.refimgqimage,
                    "There is currently no active reference image loaded to print.",
                ),
                "actionPrint_Image": image_target(
                    lambda: self.imageqimage,
                    "There is currently no active edited image loaded to print.",
                ),
            },
            default_target="actionPrint_Image",
        )

        # Progress bar (safe)
        if not hasattr(self, "progress_bar"):
            self.progress_bar = qtw.QProgressBar()

        self.progress_bar.setRange(0, 100 * self._progress_bar_scale)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self._init_project_status_widgets()
        self.statusBar().addPermanentWidget(self.progress_bar)
        self._start_active_project_sync()

        add_help_menu(self, 'MyPixler')

        self.initUI()

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
            parsed_imgpath, subprocess_mode, return_path = self._parse_launch_arguments(launch_args)
        # -------------------------
        # Phase 7 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â DEFERRED STARTUP (CRITICAL)
            if parsed_imgpath:
                imgpath = parsed_imgpath
        elif imgpath is None and len(sys.argv) > 1:
            imgpath, subprocess_mode, return_path = self._parse_launch_arguments(sys.argv[1:])
            self.subprocess_mode = subprocess_mode
            self.subprocess_return_path = return_path
        # -------------------------
        if self._startup_load:
            def _startup():
                print("[INIT] Deferred startup executing")

                # index only (no rendering)
                self.setupRefImages()

                # ÃƒÂ°Ã…Â¸Ã¢â‚¬ÂÃ‚Â¥ CRITICAL: route TIFFs through the TIFF loader
                self.load_ref_image(self.refimgpath)

            qtc.QTimer.singleShot(0, _startup)
        else:
            print("[INIT] No valid image to load")

        self._refresh_project_status(self.refimgpath or self.imgpath)
        print("=== INIT COMPLETE ===")

    def _parse_launch_arguments(self, argv):
        imgpath = None
        subprocess_mode = False
        return_path = ""

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
            if token.startswith("--"):
                index += 1
                continue
            if imgpath is None:
                imgpath = token
            index += 1

        return imgpath, subprocess_mode, return_path



    # def __init__(self, imgpath=None, parent=None):
    #     super().__init__(parent)

    #     print("=== INIT START ===")
    #     # -------------------------
    #     # Phase 1 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â CORE STATE
    #     # -------------------------
    #     self.imgpath = None
    #     self.refimgpath = None

    #     if imgpath is None and len(sys.argv) > 1:
    #         imgpath = sys.argv[1]

    #     if imgpath:
    #         imgpath = os.path.abspath(os.path.normpath(imgpath))
    #         self.imgpath = imgpath
    #         self.refimgpath = imgpath

    #     self.refimgdir = os.path.dirname(self.refimgpath) if self.refimgpath else ""
    #     self.imagedir = ""

    #     self.refimgfiles = []
    #     self.refimgindex = -1
    #     self.imagefiles = []
    #     self.imageindex = -1

    #     self.RefImgchangesSaved = True

    #     # ÃƒÂ°Ã…Â¸Ã¢â‚¬ÂÃ‚Â¥ THREADING STATE (NEW ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â REQUIRED)
    #     self._thread = None
    #     self._worker = None

    #     print(f"[INIT] imgpath: {self.imgpath}")
    #     print(f"[INIT] refimgpath: {self.refimgpath}")

    #     # -------------------------
    #     # Phase 2 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â PATH SYSTEM
    #     # -------------------------
    #     self.mod_dirname = os.path.dirname(__file__)
    #     self.mod_rootdir = os.path.join(self.mod_dirname, "..", "..")
    #     self.mod_realpath = os.path.realpath(self.mod_rootdir)
    #     self.mod_abspath = os.path.abspath(self.mod_realpath)
    #     self.projecthome = os.path.normpath(self.mod_abspath)

    #     print(f"[PATH] Project Home: {self.projecthome}")

    #     # -------------------------
    #     # Phase 2.5 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â PATH SANITY
    #     # -------------------------
    #     def _assert_clean_path(label, path):
    #         if path and os.path.isabs(path):
    #             tail = path[len(self.projecthome):] if path.startswith(self.projecthome) else ""
    #             if ":" in tail:
    #                 print(f"[PATH ERROR] {label} appears double-prefixed: {path}")

    #     _assert_clean_path("refimgpath", self.refimgpath)

    #     # -------------------------
    #     # Phase 3 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â UI SETUP
    #     # -------------------------
    #     self.ui = Ui_Pixler()
    #     self.ui.setupUi(self)

    #     # ÃƒÂ°Ã…Â¸Ã¢â‚¬ÂÃ‚Â¥ FIXED Progress Bar (was broken before)
    #     self.progress_bar = qtw.QProgressBar()
    #     self.progress_bar.setRange(0, 100)
    #     self.progress_bar.setValue(0)
    #     self.progress_bar.setVisible(False)
    #     self.statusBar().addPermanentWidget(self.progress_bar)

    #     add_help_menu(self, 'MyPixler')

    #     # ÃƒÂ°Ã…Â¸Ã¢â‚¬ÂÃ‚Â¥ KEEP THIS (your extended UI wiring lives here)
    #     self.initUI()

    #     print("[INIT] UI READY")

    #     # -------------------------
    #     # Phase 4 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â IMAGE STATE
    #     # -------------------------
    #     self.origin = QPoint()

    #     self.refimgscale = 1
    #     self.imagescale = 1

    #     self.refimgpixmap = qtg.QPixmap()
    #     self.refimgqimage = qtg.QImage()

    #     self.imagepixmap = qtg.QPixmap()
    #     self.imageqimage = qtg.QImage()

    #     # -------------------------
    #     # Phase 5 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â SIGNALS
    #     # -------------------------
    #     self.ui.actionExtract_pdf.triggered.connect(self.actionextract_pdf)
    #     self.ui.actionpdf_For_tiff.triggered.connect(self.actionpdf_for_tiff)
    #     self.ui.actionpdf_To_tiff.triggered.connect(self.actionpdf_to_tiff)
    #     self.ui.actiontiff_indexed.triggered.connect(self.actiontiff_to_mono)
    #     self.ui.actionpng_indexed.triggered.connect(self.actionmono_to_png)

    #     self.ui.actionAuto_Crop_Languages.triggered.connect(self.actionCrop_Languages)
    #     self.ui.actionManually_Crop_Language_Pages.triggered.connect(self.actionCropPreview)

    #     self.ui.actionConvert_Greek_tiff_To_png.triggered.connect(self.actionConvert_Greek_tiff_To_png)
    #     self.ui.actionDeskew_Greek_tiff.triggered.connect(self.actionDeskew_Greek_tiff)
    #     self.ui.actionResize_Greek_png_pages.triggered.connect(self.actionResize_Greek_png)

    #     self.ui.actionConvert_Latin_tiff_To_png.triggered.connect(self.actionConvert_Latin_tiff_To_png)
    #     self.ui.actionDeskew_Latin_tiff.triggered.connect(self.actionDeskew_Latin_tiff)
    #     self.ui.actionResize_Latin_png_pages.triggered.connect(self.actionResize_Latin_png)

    #     # -------------------------
    #     # Phase 5.5 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â FOCUS SYSTEM
    #     # -------------------------
    #     self.ui.RefImg.setFocusPolicy(qtc.Qt.StrongFocus)
    #     self.ui.Image.setFocusPolicy(qtc.Qt.StrongFocus)

    #     self.ui.RefImgLE.setFocusPolicy(qtc.Qt.ClickFocus)
    #     self.ui.ImageLE.setFocusPolicy(qtc.Qt.ClickFocus)

    #     # -------------------------
    #     # Phase 6 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â RUBBER BAND
    #     # -------------------------
    #     self.rubberBand = ResizableRubberBand(self)
    #     self.rubberBand.hide()

    #     # -------------------------
    #     # Phase 7 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â STARTUP LOGIC
    #     # -------------------------
    #     exists = os.path.exists(self.refimgpath) if self.refimgpath else None
    #     print(f"[INIT CHECK] refimgpath exists? {self.refimgpath} -> {exists}")

    #     self._startup_load = bool(self.refimgpath and os.path.isfile(self.refimgpath))

    #     if self._startup_load:
    #         print("[INIT] Valid startup image detected")
    #     else:
    #         print("[INIT] No valid startup image")

    #     # -------------------------
    #     # Phase 8 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â DEFERRED LOAD (SAFE)
    #     # -------------------------
    #     if self._startup_load:
    #         def _startup():
    #             print("[INIT] Deferred startup executing")

    #             self.setupRefImages()  # index only

    #             # ÃƒÂ°Ã…Â¸Ã¢â‚¬ÂÃ‚Â¥ delay thread start slightly
    #             qtc.QTimer.singleShot(100, lambda: self.start_image_load(self.refimgpath, target="ref"))

    #         # def _startup():
    #         #     print("[INIT] Deferred startup executing")
    #         #     self.setupRefImages()  # index only
    #         #     self.start_image_load(self.refimgpath, target="ref")
    #         # qtc.QTimer.singleShot(0, _startup)

    #     print("=== INIT COMPLETE ===")

    # def __init__(self, imgpath=None, parent=None):
    #     super().__init__(parent)

    #     print("=== INIT START ===")

    #     # -------------------------
    #     # Phase 1 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â STATE ONLY (ALWAYS DEFINE)
    #     # -------------------------
    #     self.imgpath = None
    #     self.refimgpath = None

    #     if imgpath:
    #         imgpath = os.path.abspath(os.path.normpath(imgpath))
    #         self.imgpath = imgpath
    #         self.refimgpath = imgpath

    #     self.refimgdir = os.path.dirname(self.refimgpath) if self.refimgpath else ""
    #     self.imagedir = ""

    #     self.refimgfiles = []
    #     self.refimgindex = -1
    #     self.imagefiles = []
    #     self.imageindex = -1

    #     self.RefImgchangesSaved = True
    #     self.image_load_path = os.path.join(script_dir, "ImageLoadWorker.py")

    #     print(f"[INIT] imgpath: {self.imgpath}")
    #     print(f"[INIT] refimgpath: {self.refimgpath}")

    #     # -------------------------
    #     # Phase 2 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â PATH SYSTEM
    #     # -------------------------
    #     self.mod_dirname = os.path.dirname(__file__)
    #     self.mod_rootdir = os.path.join(self.mod_dirname, "..", "..")
    #     self.mod_realpath = os.path.realpath(self.mod_rootdir)
    #     self.mod_abspath = os.path.abspath(self.mod_realpath)
    #     self.projecthome = os.path.normpath(self.mod_abspath)

    #     print(f"[PATH] Project Home: {self.projecthome}")

    #     # -------------------------
    #     # Phase 2.5 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â PATH SANITY GUARD
    #     # -------------------------
    #     def _assert_clean_path(label, path):
    #         if path and os.path.isabs(path):
    #             tail = path[len(self.projecthome):] if path.startswith(self.projecthome) else ""
    #             if ":" in tail:
    #                 print(f"[PATH ERROR] {label} appears double-prefixed: {path}")

    #     _assert_clean_path("refimgpath", self.refimgpath)

    #     # -------------------------
    #     # Phase 3 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â UI SETUP
    #     # -------------------------
    #     self.ui = Ui_Pixler()
    #     self.ui.setupUi(self)
    #     #implement self.progress_bar = qtw.QProgressBar()
    #     self.progress_bar.setRange(0, 100)
    #     self.progress_bar.setValue(0)
    #     self.progress_bar.setVisible(False)
    #     self.statusBar().addPermanentWidget(self.progress_bar)
    #     add_help_menu(self, 'MyPixler')

    #     self.initUI()

    #     print("[INIT] UI READY")

    #     # -------------------------
    #     # Phase 4 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â IMAGE STATE INIT
    #     # -------------------------
    #     self.origin = QPoint()
    #     self.refimgscale = 1
    #     self.imagescale = 1

    #     self.refimgpixmap = qtg.QPixmap()
    #     self.refimgqimage = qtg.QImage()
    #     self.imagepixmap = qtg.QPixmap()
    #     self.imageqimage = qtg.QImage()

    #     # -------------------------
    #     # Phase 5 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â SIGNALS
    #     # -------------------------
    #     self.ui.actionExtract_pdf.triggered.connect(self.actionextract_pdf)
    #     self.ui.actionpdf_For_tiff.triggered.connect(self.actionpdf_for_tiff)
    #     self.ui.actionpdf_To_tiff.triggered.connect(self.actionpdf_to_tiff)
    #     self.ui.actiontiff_indexed.triggered.connect(self.actiontiff_to_mono)
    #     self.ui.actionpng_indexed.triggered.connect(self.actionmono_to_png)
    #     self.ui.actionAuto_Crop_Languages.triggered.connect(self.actionCrop_Languages)
    #     self.ui.actionManually_Crop_Language_Pages.triggered.connect(self.actionCropPreview)
    #     self.ui.actionConvert_Greek_tiff_To_png.triggered.connect(self.actionConvert_Greek_tiff_To_png)
    #     self.ui.actionDeskew_Greek_tiff.triggered.connect(self.actionDeskew_Greek_tiff)
    #     self.ui.actionResize_Greek_png_pages.triggered.connect(self.actionResize_Greek_png)
    #     self.ui.actionConvert_Latin_tiff_To_png.triggered.connect(self.actionConvert_Latin_tiff_To_png)
    #     self.ui.actionDeskew_Latin_tiff.triggered.connect(self.actionDeskew_Latin_tiff)
    #     self.ui.actionResize_Latin_png_pages.triggered.connect(self.actionResize_Latin_png)

    #     # Establish Panel focus policy for keypress events (arrows for next/prev)
    #     self.ui.RefImg.setFocusPolicy(qtc.Qt.StrongFocus)
    #     self.ui.Image.setFocusPolicy(qtc.Qt.StrongFocus)
    #     self.ui.RefImgLE.setFocusPolicy(qtc.Qt.ClickFocus)
    #     self.ui.ImageLE.setFocusPolicy(qtc.Qt.ClickFocus)

    #     self.rubberBand = ResizableRubberBand(self)
    #     self.rubberBand.hide()

    #     # -------------------------
    #     # Phase 6 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â STARTUP FLAG
    #     # -------------------------
    #     print(f"[INIT CHECK] refimgpath exists? {self.refimgpath} -> {os.path.exists(self.refimgpath) if self.refimgpath else 'None'}")

    #     self._startup_load = bool(self.refimgpath and os.path.isfile(self.refimgpath))

    #     if self._startup_load:
    #         print("[INIT] Valid startup image detected")
    #     else:
    #         print("[INIT] No valid startup image")

    #     # -------------------------
    #     # Phase 7 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â SINGLE DEFERRED LOAD (ONLY ONE)
    #     # -------------------------
    #     # if self._startup_load:
    #     #     def _startup():
    #     #         print("[INIT] Deferred startup executing")
    #     #         self.setupRefImages()              # index only
    #     #         self.start_image_load(path, target="ref")   # render once

    #     #     qtc.QTimer.singleShot(0, _startup)

    #     print("=== INIT COMPLETE ===")
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

        jsonfile = os.path.join(self.project_root, "Model", "Project", "Data", "json", "Workflow.json")
        with open(jsonfile, 'r') as f:
            data = json.load(f)
        # Opening JSON file
        # Iterating through the json
        # list
            for Sequence in data:
                print(Sequence['Sequence'], Sequence['DialogUi'],Sequence['DefaultSource'])

        # Closing file
        f.close()

    def initToolbar(self):
        # Signals(Slots)
        self.ui.actionCropRefImg.triggered.connect(self.actionCropImage)
        self.ui.actionDeskewRefImg.triggered.connect(self.deskewRefImg)
        self.ui.actionRotateRefImg_360_deg.triggered.connect(self.rotateRefImg)
        self.ui.actionDenoise.triggered.connect(self.openDenoiseDialog)
        self.ui.actionClipRefImg.triggered.connect(self.clip)
        self.ui.actionErase.triggered.connect(self.eraser)
        #self.ui.actionFlipRefImg.triggered.connect()
        self.ui.actionRotateRefImg_90_CW.triggered.connect(self.rotateRefImg90CW)
        self.ui.actionRotateRefImg_90_CCW.triggered.connect(self.rotateRefImg90CCW)
        self.ui.actionRotateRefImg_180_deg_CW.triggered.connect(self.rotateRefImg180CW)
        #self.ui.actionFillTransparent.triggered.connect()

    def initMenubar(self):

        # File menu Signals(Slots)
        self.ui.actionOpen_Reference_Image.triggered.connect(self.loadRefImg)
        self.ui.actionSave_Image.triggered.connect(self.SaveImage)
        self.ui.actionSave_As_Image.triggered.connect(self.SaveImageAs)
        self.ui.actionOverwrite_Reference_Image.triggered.connect(self.OverwriteRefImg)
        self.ui.actionImport_Current_Image.triggered.connect(self.importRefImg)
        self.ui.actionLanguage_Morphology.triggered.connect(self.openMorphologyDialog)
        #self.ui.actionExport_Image.triggered.connect()

        # Edit Menu Signals(Slots)

        self.ui.actionFillBackground.triggered.connect(self.choose_fill_background_color)
        self.ui.actionFillForeground.triggered.connect(self.choose_fill_foreground_color)



    def initUI(self):

        self.get_session_settings()

        self.initMenubar()
        self.initToolbar()

        # -------------------------
        # Ref Image
        # -------------------------
        self.ui.OpenRefImgbutton.clicked.connect(self.loadRefImg)
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

        #self.ui.PrevImagebutton.clicked.connect(self.prevImage)
        #elf.ui.NextImagebutton.clicked.connect(self.nextImage)

        self.ui.Imagezoomslider.valueChanged.connect(self.on_Imagezoomslider)
        self.ui.ImageZoomComboBox.currentTextChanged.connect(self.on_Imagezoom)
        self.ui.ImageZoombutton.clicked.connect(self.get_Imagezoom)
        self.ui.Imagezoomslider.sliderReleased.connect(self.disable_Imagezoomslider)

        self.ui.ExportRefImgFilebutton.clicked.connect(self.ExportImage)
        self.ui.SaveImagebutton.clicked.connect(self.SaveImage)
        self.ui.SaveAsImagebutton.clicked.connect(self.SaveImageAs)

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

        self.project_tracking_button = qtw.QPushButton("Milestones")
        self.project_tracking_button.setFixedHeight(24)
        self.project_tracking_button.clicked.connect(self._open_project_tracking_dialog)

        self.statusBar().addPermanentWidget(self.project_name_status_label)
        self.statusBar().addPermanentWidget(self.workflow_status_label)
        self.statusBar().addPermanentWidget(self.project_overall_status_bar)
        self.statusBar().addPermanentWidget(self.project_tracking_button)

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

        self.current_project_root = shared_root
        self._refresh_project_status(shared_root)

    def _format_module_workflow_status(self, module_name, snapshot):
        module_total = int(snapshot.get("module_total_count", 0))
        module_completed = int(snapshot.get("module_completed_count", 0))
        next_label = snapshot.get("module_next_label", "")

        if module_total <= 0:
            return f"{module_name} | No milestones configured"
        if next_label == "Complete":
            return f"{module_name} {module_completed}/{module_total} | Complete"
        return f"{module_name} {module_completed}/{module_total} | Next: {next_label}"

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
        overall_percent = int(snapshot.get("overall_percent", 0))
        overall_next = snapshot.get("overall_next_label", "")
        tooltip = f"Overall {overall_percent}%\nCompleted: {completed_text}\nNext: {overall_next}"

        self.workflow_status_label.setText(self._format_module_workflow_status("MyPixler", snapshot))
        self.workflow_status_label.setToolTip(tooltip)
        self.project_overall_status_bar.setValue(overall_percent)
        self.project_overall_status_bar.setFormat(f"Project {overall_percent}%")
        self.project_overall_status_bar.setToolTip(tooltip)

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
        self._refresh_project_status(project_root)
        return project_root

    def _open_project_tracking_dialog(self):
        project_root = self.workflow_tracker.resolve_project_root(
            self._shared_active_project_root(),
            self.current_project_root,
            getattr(self, "refimgpath", ""),
            getattr(self, "imgpath", ""),
            getattr(self, "refimgdir", ""),
            getattr(self, "imagedir", ""),
            getattr(self, "workflow", ""),
            getattr(self, "session", ""),
        )
        if not project_root:
            qtw.QMessageBox.information(
                self,
                "Project Milestones",
                "Select or create a project in MyServer first so milestone state can be edited.",
            )
            return

        self.current_project_root = project_root
        self.workflow_tracker.ensure_tracking_state(project_root)
        dialog = ProjectTrackingDialog(self.workflow_tracker, project_root, "MyPixler", self)
        dialog.exec_()
        self._refresh_project_status(project_root)

    def _init_subprocess_return_controls(self):
        if not self.subprocess_mode or not self.subprocess_return_path:
            return

        self.return_to_server_button = qtw.QPushButton("Return Crop to MyServer")
        self.return_to_server_button.setEnabled(False)
        self.return_to_server_button.setFixedHeight(24)
        self.return_to_server_button.setStyleSheet(
            "QPushButton { background-color: #4a4a4a; color: white; border: 1px solid #2d2d2d; padding: 2px 8px; }"
            "QPushButton:hover { background-color: #5a5a5a; }"
            "QPushButton:pressed { background-color: #3b3b3b; }"
        )
        self.return_to_server_button.setToolTip(self.subprocess_return_path)
        self.return_to_server_button.clicked.connect(self.returnCropToMyServer)
        self.statusBar().addPermanentWidget(self.return_to_server_button)

        self.statusBar().showMessage(
            f"Subprocess return ready: {self.subprocess_return_path}"
        )
    # def initUI(self):

    #     self.get_session_settings()
    #     '''if self.imgpath != "":
    #         self.refimgpath = self.imgpath
    #         self.importRefImg()'''

    #     self.initMenubar()
    #     self.initToolbar()

    #     # Button Row Signals(Slots)

    #     # Ref Image

    #     self.ui.OpenRefImgbutton.clicked.connect(self.loadRefImg)
    #     self.ui.ImportRefImgFilebutton.clicked.connect(self.importRefImg)
    #     self.ui.Deskewbutton.clicked.connect(self.deskewRefImg)

    #     self.ui.OverwriteRefImgbutton.clicked.connect(self.OverwriteRefImg)

    #     self.ui.RefImgZoombutton.clicked.connect(self.get_RefImgzoom)
    #     self.ui.RefImgZoomComboBox.currentTextChanged.connect(self.on_RefImgzoom)
    #     self.ui.RefImgzoomslider.valueChanged.connect(self.on_RefImgzoomslider)
    #     self.ui.RefImgzoomslider.sliderReleased.connect(self.disable_RefImgzoomslider)
    #     self.ui.RefImgzoomslider.hide()

    #     self.ui.NextRefImgbutton.clicked.connect(self.nextRefImage)
    #     self.ui.PrevRefImgbutton.clicked.connect(self.prevRefImage)

    #     # Both
    #     '''
    #     self.ui.BothLoadButton.clicked.connect(self.bothLoad)
    #     self.ui.BothNextImageButton.clicked.connect(nextRefImage)
    #     self.ui.BothNextImageButton.clicked.connect(nextImage)
    #     self.ui.BothPrevImageButton.clicked.connect(prevRefImage)
    #     self.ui.BothPrevImageButton.clicked.connect(prevImage)'''

    #     self.ui.reloadImagebutton.clicked.connect(self.reloadImage)
    #     self.ui.reloadRefImgbutton.clicked.connect(self.reloadRefImg)

    #     # Image
    #     self.ui.ImageLE.textChanged.connect(self.changed_RefImg)

    #     self.ui.PrevImagebutton.clicked.connect(self.prevImage)
    #     self.ui.NextImagebutton.clicked.connect(self.nextImage)

    #     self.ui.Imagezoomslider.valueChanged.connect(self.on_Imagezoomslider)
    #     self.ui.ImageZoomComboBox.currentTextChanged.connect(self.on_Imagezoom)
    #     self.ui.ImageZoombutton.clicked.connect(self.get_Imagezoom)
    #     self.ui.Imagezoomslider.sliderReleased.connect(self.disable_Imagezoomslider)

    #     self.ui.ExportRefImgFilebutton.clicked.connect(self.ExportImage)
    #     self.ui.SaveImagebutton.clicked.connect(self.SaveImage)
    #     self.ui.SaveAsImagebutton.clicked.connect(self.SaveImageAs)

    #     self.ui.RefImgzoomslider.hide()
    #     self.ui.Imagezoomslider.hide()

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

    # def loadStackFromFile(self,fileName=''):
    #     fileName = str(fileName)
    #     if len(fileName) and os.path.isfile(fileName):
    #         self._tiffCaptureHandle = tiffcapture.opentiff(fileName)

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

    # def showRefImg(self, imgpath):
    #     print(f"[SHOW] Display only: {imgpath}")

    #     if not hasattr(self, "refimgqimage") or self.refimgqimage.isNull():
    #         print("[SHOW] No image loaded yet")
    #         return

    #     pix = qtg.QPixmap.fromImage(self.refimgqimage)

    #     self.ui.RefImg.setPixmap(pix.scaled(self.ui.RefImg.size(),qtc.Qt.KeepAspectRatio,transformMode=qtc.Qt.SmoothTransformation))

    # def showRefImg(self, imgpath):
    #     print(f"[SHOW] Called with: {imgpath}")

    #     if not imgpath:
    #         print("[SHOW] No path provided")
    #         return

    #     imgpath = os.path.normpath(imgpath)

    #     if not os.path.isfile(imgpath):
    #         print(f"[SHOW] Invalid file: {imgpath}")
    #         return

    #     self.refimgpath = imgpath  # ÃƒÂ¢Ã…â€œÃ¢â‚¬Â¦ sync state

    #     print(f"[SHOW] Rendering: {imgpath}")

    #     if imgpath.lower().endswith('.tif'):
    #         print("[SHOW] TIFF detected")

    #         # ÃƒÂ°Ã…Â¸Ã¢â‚¬ÂÃ‚Â¥ async load handles everything now
    #         self.loadStackFromFile(imgpath)

    #         return   # ÃƒÂ¢Ã…â€œÃ¢â‚¬Â¦ CRITICAL: stop here (thread will finish rendering)

    #     # if imgpath.lower().endswith('.tif'):
    #     #     print("[SHOW] TIFF detected")

    #     #     self.loadStackFromFile(imgpath)
    #     #     self.showFrame(0)

    #     #     # ÃƒÂ¢Ã…â€œÃ¢â‚¬Â¦ CRITICAL: persist qimage
    #     #     self.refimgqimage = self.qimage

    #     #     self.refimgpixmap = qtg.QPixmap.fromImage(self.refimgqimage)

    #     else:
    #         print("[SHOW] Standard image")

    #         self.refimgpixmap = qtg.QPixmap(imgpath)

    #         # ÃƒÂ¢Ã…â€œÃ¢â‚¬Â¦ CRITICAL: create qimage from pixmap
    #         self.refimgqimage = self.refimgpixmap.toImage()

    #     # ÃƒÂ¢Ã…â€œÃ¢â‚¬Â¦ display
    #     self.ui.RefImg.setPixmap(
    #         self.refimgpixmap.scaled(
    #             self.ui.RefImg.size(),
    #             qtc.Qt.KeepAspectRatio,
    #             transformMode=qtc.Qt.SmoothTransformation
    #         )
    #     )

    #     print("[SHOW] Render complete")

    def showImage(self,imgfilename):
        #self.imgfilename = self.imgpath
        file = qtc.QFile(imgfilename)
        filestr = os.path.basename(imgfilename)
        filesplit = os.path.splitext(filestr)
        filename = filesplit[0]
        fileext = filesplit[1]

        if file.open(qtc.QIODevice.ReadOnly):
            info = qtc.QFileInfo(imgfilename)

            if fileext.lower() in ('.tif', '.tiff'):
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

        self.imagefileList = []
        for i in os.listdir(self.imagedir):
            ipath = os.path.normpath(os.path.join(self.imagedir, i))
            if os.path.isfile(ipath) and i.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff')):
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

# Application Controllers

    # Workflow Controllers
    def actionextract_pdf(self):
        print("extracting pdf pages from source pdf")

        def accept():
        #if self.pdfxDialog.Accepted:
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
            print("pdf page extraction complete")

            base = os.path.join(self.projecthome, 'Model', 'Project', 'Data', 'json')

            source = self.sourcefile

            if source:
                source = os.path.normpath(source)

            SessionManager(base).update('Session.json', {
                'self.sourcefile': source or "",
                'self.firstpage': self.firstpage,
                'self.lastpage': self.lastpage,
            })
            self._record_project_milestone(
                "source_acquired",
                workflow_folder,
                details={"source": "actionextract_pdf"},
            )

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
            # get default folder
            # Define json data

            jsonfile = os.path.join(project_root, "Model", "Project", "Data", "json", "Workflow.json")
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
            self._record_project_milestone(
                "source_converted",
                workflow_folder,
                details={"source": "actionpdf_for_tiff"},
            )
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
            # disable source button (default)

            # get default folder
            # Define json data

            jsonfile = os.path.join(project_root, "Model", "Project", "Data", "json", "Workflow.json")
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
            self._record_project_milestone(
                "source_converted",
                workflow_folder,
                details={"source": "actiontiff_to_mono"},
            )
            self._record_project_milestone(
                "source_converted",
                workflow_folder,
                details={"source": "actionpdf_to_tiff"},
            )
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
            # disable source button (default)

            # get default folder
            # Define json data

            jsonfile = os.path.join(project_root, "Model", "Project", "Data", "json", "Workflow.json")
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
            self._record_project_milestone(
                "source_converted",
                workflow_folder,
                details={"source": "actionmono_to_png"},
            )
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

            jsonfile = os.path.join(project_root, "Model", "Project", "Data", "json", "Workflow.json")
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

        self.mono2png_ui.defaultsrcBox.stateChanged.connect(setdefault)
        self.mono2png_ui.SourceButton.clicked.connect(self.MonoToPngDialog)
        self.mono2png_ui.DestinationButton.clicked.connect(self.DestMonoToPngDialog)
        self.mono2png_ui.buttonBox.accepted.connect(accept)
        self.mono2png_ui.buttonBox.rejected.connect(reject)


        if self.mono2png_ui.defaultsrcBox.isChecked():
            # disable source button (default)

            # get default folder
            # Define json data

            jsonfile = os.path.join(project_root, "Model", "Project", "Data", "json", "Workflow.json")
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
            self._record_project_milestone(
                "source_converted",
                tif_workflow_folder,
                details={"source": "actiondeskew_mono"},
            )
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

            jsonfile = os.path.join(project_root, "Model", "Project", "Data", "json", "Workflow.json")
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

            jsonfile = os.path.join(project_root, "Model", "Project", "Data", "json", "Workflow.json")
            with open(jsonfile, 'r') as f:
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

            '''if workflow_dup_greek_folder:
                symlinks=False
                ignore=None
                for item in os.listdir(workflow_greek_folder):
                    source = os.path.join(workflow_greek_folder, item)
                    destination = os.path.join(workflow_dup_greek_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)
                    # enable section below to remove files from workflow_greek_folder
                    file_path = os.path.join(workflow_greek_folder, filename)
                    print('File Name:'+filename, 'File Path:'+file_path)
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        print('Failed to delete %s. Reason: %s' % (file_path, e))'''

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
            self._record_project_milestone(
                "pages_prepared",
                workflow_greek_folder or workflow_latin_folder,
                details={"source": "actionCrop_Languages"},
            )
            '''if workflow_dup_latin_folder:
                #symlinks=False
                #ignore=None
                for item in os.listdir(workflow_latin_folder):
                    source = os.path.join(workflow_latin_folder, item)
                    destination = os.path.join(workflow_dup_latin_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)
                    file_path = os.path.join(workflow_latin_folder, filename)
                    print('File Name:'+filename, 'File Path:'+file_path)
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        print('Failed to delete %s. Reason: %s' % (file_path, e))'''

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

                # Define json data

                jsonfile = os.path.join(project_root, "Model", "Project", "Data", "json", "Workflow.json")
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

            jsonfile = os.path.join(project_root, "Model", "Project", "Data", "json", "Workflow.json")
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
    def actionDeskew_Greek_tiff(self):
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

            jsonfile = os.path.join(project_root, "Model", "Project", "Data", "json", "Workflow.json")
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

            jsonfile = os.path.join(project_root, "Model", "Project", "Data", "json", "Workflow.json")
            with open(jsonfile, 'r') as f:
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

    def actionResize_Greek_png(self):
        print("resizing Greek png files")
        #usage: pp.resizepngs(source, destination)
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

            jsonfile = os.path.join(project_root, "Model", "Project", "Data", "json", "Workflow.json")
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
        #pp.tiff2pngidx(r"~/Projects/Python/Images/Source/tif_black_white/source_book_40_Matthew/", "~/Projects/Python/Images/Source/tif_black_white_2png/source_book_40_Matthew/")
        #pp.tiff2pngidx(r"~/Projects/Python/Images/Latin/tif_latin/latin_book_41_Mark/", "~/Projects/Python/Images/Latin/png_latin/latin_book_41_Mark/")

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

    def actionResize_Latin_png(self):
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
        #pp.resizepngs(r"~/Projects/Python/Images/Greek/png_latin_deskew/latin_book_40_Matthew/","~/Projects/Python/Images/Greek/png_latin_resize/latin_book_40_Matthew/")
        #pp.resizepngs(r"~/Projects/Python/Images/Latin/png_latin_deskew/latin_book_41_Mark/","~/Projects/Python/Images/Latin/png_latin_resize/latin_book_41_Mark/")

    # Dialog Controllers

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

    def MonoToPngDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select mono tif pages source folder"))

        if self.directory:
            self.mono2png_ui.SourceLineEdit.setText(self.directory+r'/')

    def DestMonoToPngDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select destination folder"))

        if self.directory:
            self.mono2png_ui.DestinationLineEdit.setText(self.directory+r'/')

    def GreekMonoToPngDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select greek mono tif pages source folder"))

        if self.directory:
            self.greekmono2png_ui.SourceLineEdit.setText(self.directory+r'/')

    def GreekDestMonoToPngDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select destination folder"))

        if self.directory:
            self.greekmono2png_ui.DestinationLineEdit.setText(self.directory+r'/')

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

    def GreekResizePngDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select greek pages source folder"))

        if self.directory:
            self.greekresizepng_ui.SourceLineEdit.setText(self.directory+r'/')

    def DestGreekResizePngDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select greek png pages destination folder"))

        if self.directory:
            self.greekresizepng_ui.DestinationLineEdit.setText(self.directory+r'/')

    def DeskewLatinMonoDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select latin pages source folder"))

        if self.directory:
            self.deskew_latinmono_ui.SourceLineEdit.setText(self.directory+r'/')

    def LatinMonoToPngDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select latin mono tif pages source folder"))

        if self.directory:
            self.latinmono2png_ui.SourceLineEdit.setText(self.directory+r'/')

    def LatinDestMonoToPngDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select destination folder"))

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
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select latin png pages destination folder"))

        if self.directory:
            self.deskew_latinmono_ui.DestPngLineEdit.setText(self.directory+r'/')

    def DestDeskewLatinTifDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select latin tif pages destination folder"))

        if self.directory:
            self.deskew_latinmono_ui.DestTifLineEdit.setText(self.directory+r'/')

    def LatinResizePngDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select latin pages source folder"))

        if self.directory:
            self.latinresizepng_ui.SourceLineEdit.setText(self.directory+r'/')

    def DestLatinResizePngDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select latin png pages destination folder"))

        if self.directory:
            self.latinresizepng_ui.DestinationLineEdit.setText(self.directory+r'/')

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

    def load_ref_image(self, path):
        fileext = os.path.splitext(str(path))[1].lower()
        if fileext in ('.tif', '.tiff'):
            self.loadStackFromFile(path)
            return
        self.start_image_load(path, target="ref")

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

    # def on_image_loaded(self, qimage):
    #     # ÃƒÂ¢Ã…â€œÃ¢â‚¬Â¦ STORE BOTH (CRITICAL)
    #     self.refimgqimage = qimage
    #     self.refimgpixmap = qtg.QPixmap.fromImage(qimage)

    #     if hasattr(self, "progress_bar"):
    #         self.progress_bar.setValue(100)
    #         self.progress_bar.setVisible(False)

    #     # ÃƒÂ¢Ã…â€œÃ¢â‚¬Â¦ USE STORED PIXMAP (not a temporary one)
    #     self.ui.RefImg.setPixmap(
    #         self.refimgpixmap.scaled(self.ui.RefImg.size(),qtc.Qt.KeepAspectRatio,transformMode=qtc.Qt.SmoothTransformation))


    # def on_image_loaded(self, qimage):
    #     self.refimgqimage = qimage

    #     if hasattr(self, "progress_bar"):
    #         self.progress_bar.setValue(100)
    #         self.progress_bar.setVisible(False)

    #     pix = qtg.QPixmap.fromImage(qimage)

    #     self.ui.RefImg.setPixmap(pix.scaled(self.ui.RefImg.size(), qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation))

    # def on_image_loaded(self, qimage):
    #     print("[LOAD] Complete")

    #     self.refimgqimage = qimage

    #     if hasattr(self, "progress_bar"):
    #         self.progress_bar.setValue(100)
    #         self.progress_bar.setVisible(False)

    #     # ÃƒÂ¢Ã…â€œÃ¢â‚¬Â¦ now display
    #     self.showRefImg(self.refimgpath)

    # def on_image_loaded(self, qimage):
    #     print("[LOAD] Complete")

    #     if hasattr(self, "progress_bar"):
    #         self.progress_bar.setValue(100)
    #         self.progress_bar.setVisible(False)

    #     if self._load_target == "ref":
    #         self.refimgqimage = qimage
    #         self.refimgpixmap = QPixmap.fromImage(qimage)  # must exist

    #         # ÃƒÂ°Ã…Â¸Ã¢â‚¬ÂÃ‚Â¥ route back into your rendering pipeline
    #         # self.showRefImg(self.refimgpath)

    #     elif self._load_target == "main":
    #         self.imgqimage = qimage
    #         self.showImg(self.imgpath)



    # def on_image_loaded(self, qimage):
    #     print("[LOAD] Complete")

    #     if hasattr(self, "progress_bar"):
    #         self.progress_bar.setValue(100)
    #         self.progress_bar.setVisible(False)

    #     # -------------------------
    #     # ROUTING (THIS is critical)
    #     # -------------------------
    #     if self._load_target == "ref":
    #         self.refimgqimage = qimage
    #         pix = qtg.QPixmap.fromImage(qimage)
    #         self.ui.RefImg.setPixmap(pix)

    #     elif self._load_target == "main":
    #         self.imgqimage = qimage
    #         pix = qtg.QPixmap.fromImage(qimage)
    #         self.ui.Image.setPixmap(pix)


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


    # def loadRefImg(self, path):
    #     print(f"[LOAD REF] Requested: {path}")

    #     if not path:
    #         print("[LOAD REF] Invalid path")
    #         return
    #     else:
    #         # store path like before (keep your logic intact)
    #         self.refimgpath = path
    #         filestr = os.path.basename(path)
    #         self.ui.ImageLE.setText(filestr)
    #         # ÃƒÂ°Ã…Â¸Ã¢â‚¬ÂÃ‚Â¥ NEW: async load instead of direct render
    #         self.start_image_load(path, target="ref")



    # def loadRefImg(self):
    #     print("Loading current reference image path provided by open file dialog")
    #     self.refimgpath = qtw.QFileDialog.getOpenFileName(self.ui.centralwidget, 'Open image file',self.refimgdir,'Images (*.png *.jpeg *.jpg *.bmp *.gif *.tif)')[0]
    #     if self.refimgpath:
    #         self.ui.RefImgLE.setText(os.path.basename(self.refimgpath))
    #         print("[Pixler] Ref image indexed")

    #     #self.image_load_path = os.path.join(script_dir, "ImageLoadWorker.py")
    #     #self.start_image_load(self.image_load_path, target="ref")
    #     #self.refimgpath =

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
        self.load_ref_image(self.refimgpath)
    def prevRefImage(self):
        if not self.refimgfiles:
            return

        self.refimgindex = (self.refimgindex - 1) % len(self.refimgfiles)
        self.refimgpath = self.refimgfiles[self.refimgindex]

        print(f"[NAV] Prev ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ {self.refimgpath}")
        self.load_ref_image(self.refimgpath)

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

    # def on_RefImgzoomslider(self):
    #     #if self.ui.Zoomslider.isEnabled():
    #     RefImgzoomValue = self.ui.RefImgzoomslider.value()
    #     self.ui.RefImgZoomComboBox.setCurrentText(str(RefImgzoomValue) + " %")
    #     print(RefImgzoomValue)
    #     self.refimgscale = RefImgzoomValue/100
    #     print(self.refimgscale)

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

            self.load_ref_image(self.refimgpath)
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
        dpi_x = 300
        dpi_y = 300
        if qimage.dotsPerMeterX() > 0:
            dpi_x = qimage.dotsPerMeterX() * 0.0254
        if qimage.dotsPerMeterY() > 0:
            dpi_y = qimage.dotsPerMeterY() * 0.0254
        print("Generating: " + outfile)
        if self._source_prefers_bilevel_output():
            PILimage = PILimage.convert("1")
        PILimage.save(outfile, "TIFF", dpi=(dpi_x, dpi_y), compression="tiff_lzw")

    def returnCropToMyServer(self):
        if not self.subprocess_mode or not self.subprocess_return_path:
            print("[CROP] No subprocess return path available")
            return

        payload = getattr(self, "cropped_qimage", None)
        if payload is None or payload.isNull():
            payload = getattr(self, "imageqimage", None)

        if payload is None or payload.isNull():
            print("[CROP] No crop result available to return")
            return

        self._save_qimage_as_tiff(payload, self.subprocess_return_path)
        print(f"[CROP] Returned cropped result to MyServer: {self.subprocess_return_path}")

        if self.return_to_server_button is not None:
            self.return_to_server_button.setEnabled(False)

        qtc.QTimer.singleShot(100, self.close)

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

    def clip(self):
        print("[CLIP] Opening inverse-selection preview")
        return self._launch_preview_tool(
            self.clip_processor,
            title="Clip Preview",
            params={"background_color": self._background_fill_color_name(self.refimgqimage)},
            enable_crop=True,
        )

    def eraser(self):
        print("[ERASE] Opening preview")
        if not hasattr(self, "refimgqimage") or self.refimgqimage.isNull():
            print("[ERASE] No image loaded")
            return False

        dialog = ImagePreviewDialog(
            self.refimgqimage,
            self.erase_processor,
            {
                "brush_radius": int(self.eraser_tip_size),
                "background_color": self._background_fill_color_name(self.refimgqimage),
                "erase_points": [],
            },
            self,
            enable_crop=False,
            interaction_mode="paint",
            preview_max_dimension=1600,
        )
        dialog.setWindowTitle("Erase Preview")
        dialog.add_slider("brush_radius", 1, 200, int(self.eraser_tip_size))

        if dialog.exec_() != qtw.QDialog.Accepted:
            print("[ERASE] Cancelled")
            return False

        self.eraser_tip_size = int(dialog.params.get("brush_radius", self.eraser_tip_size))
        return self._apply_preview_result(dialog.get_result())

    def crop_processor(self, qimage, params):
        if not params:
            return qimage

        x = params.get("x", 0)
        y = params.get("y", 0)
        w = params.get("w", qimage.width())
        h = params.get("h", qimage.height())

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
        radius = max(1, int(params.get("brush_radius", self.eraser_tip_size)))
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

        if self.subprocess_mode and self.subprocess_return_path and self.return_to_server_button is not None:
            self.return_to_server_button.setEnabled(True)
            self.statusBar().showMessage("Result ready. Press Return Crop to MyServer.")

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


    # def crop_processor(self, qimage, params):
    #     # TEMP: pass-through (no actual cropping yet)
    #     return qimage

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


    # def applyProcessedImage(self, qimage):
    #     if qimage is None or qimage.isNull():
    #         print("[APPLY] Invalid processed image")
    #         return

    #     print("[APPLY] Applying processed image")

    #     # Update internal state
    #     self.refimgqimage = qimage
    #     self.refimgpixmap = qtg.QPixmap.fromImage(qimage)

    #     # Render to UI
    #     self.ui.RefImg.setPixmap(
    #         self.refimgpixmap.scaled(
    #             self.ui.RefImg.size(),
    #             qtc.Qt.KeepAspectRatio,
    #             transformMode=qtc.Qt.SmoothTransformation
    #         )
    #     )

    # def actionCropPreview(self, checked=False):

    #     print("[ACTION] Crop Preview triggered")

    #     if not self.refimgqimage or self.refimgqimage.isNull():
    #         print("[ACTION] No image loaded")
    #         return

    #     dialog = ImagePreviewDialog(
    #         self.refimgqimage,
    #         crop_processor,
    #         {},        # params (placeholder for now)
    #         self       # parent
    #     )

    #     if dialog.exec_():
    #         result = dialog.get_result()
    #         self.actionCropImage(result)


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

    # def start_image_load(self, path, target="ref"):
    #     print(f"[THREAD] Start load ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ {path} ({target})")

    #     # store target so handler knows where to route image
    #     self._load_target = target

    #     self._thread = qtc.QThread()
    #     self._worker = ImageLoadWorker(self.image_load_path)

    #     self._worker.moveToThread(self._thread)

    #     # --- signals
    #     self._thread.started.connect(self._worker.run)
    #     self._worker.progress.connect(self.on_load_progress)
    #     self._worker.finished.connect(self.on_image_loaded)
    #     self._worker.error.connect(self.on_load_error)

    #     # --- cleanup
    #     self._worker.finished.connect(self._thread.quit)
    #     self._worker.finished.connect(self._worker.deleteLater)
    #     self._thread.finished.connect(self._thread.deleteLater)

    #     # --- start
    #     self._thread.start()

    #     # show progress immediately
    #     if hasattr(self, "progress_bar"):
    #         self.progress_bar.setValue(0)
    #         self.progress_bar.setVisible(True)
# Legacy in-file ImagePreviewDialog implementation removed; use ImagePreviewDialog.py.
# class ImagePreviewDialog(qtw.QDialog):
#     def __init__(self, original_qimage, processor, params=None, parent=None):
#         super().__init__(parent)

#         screen = qtw.QApplication.primaryScreen().availableGeometry()

#         # Use ~80% of screen size
#         self.resize(int(screen.width() * 0.8), int(screen.height() * 0.8))

#         self.setWindowTitle("Preview")

#         # -------------------------
#         # Phase 1 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Store data ONLY
#         # -------------------------
#         self.original = original_qimage
#         self.processor = processor
#         self.params = params or {}

#         # -------------------------
#         # Phase 2 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Build UI FIRST
#         # -------------------------
#         layout = qtw.QVBoxLayout(self)

#         # Create labels
#         self.left_label = qtw.QLabel()
#         self.right_label = qtw.QLabel()

#         self.left_label.setAlignment(qtc.Qt.AlignCenter)
#         self.right_label.setAlignment(qtc.Qt.AlignCenter)

#         # Wrap in scroll areas
#         self.left_scroll = qtw.QScrollArea()
#         self.right_scroll = qtw.QScrollArea()

#         self.left_scroll.setWidget(self.left_label)
#         self.right_scroll.setWidget(self.right_label)

#         self.left_scroll.setWidgetResizable(True)
#         self.right_scroll.setWidgetResizable(True)

#         # ÃƒÂ¢Ã…â€œÃ¢â‚¬Â¦ NOW it exists ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ install filter
#         self.left_scroll.viewport().installEventFilter(self)

#         # Add to layout (side-by-side)
#         image_layout = qtw.QHBoxLayout()
#         image_layout.addWidget(self.left_scroll)
#         image_layout.addWidget(self.right_scroll)

#         # Then add this layout into your main dialog layout
#         layout.addLayout(image_layout, stretch=1)

#         # Buttons
#         btn_layout = qtw.QHBoxLayout()
#         self.apply_btn = qtw.QPushButton("Apply")
#         self.cancel_btn = qtw.QPushButton("Cancel")

#         btn_layout.addWidget(self.apply_btn)
#         btn_layout.addWidget(self.cancel_btn)

#         layout.addLayout(btn_layout)
#         # zoom state

#         # slider creation
#         # -------------------------
#         # Zoom Slider
#         # -------------------------
#         zoom_layout = qtw.QHBoxLayout()

#         zoom_label = qtw.QLabel("Zoom:")
#         self.zoom_slider = qtw.QSlider(qtc.Qt.Horizontal)

#         self.zoom_slider.setMinimum(1)    # 10%
#         self.zoom_slider.setMaximum(125)   # 125%
#         self.zoom_slider.setSingleStep(1)  # 1% increments

#         # self.zoom_slider.setMinimum(25)    # 0.25x
#         # self.zoom_slider.setMaximum(200)   # 2.0x

#         default_zoom = 11  # your preferred baseline

#         self.zoom_slider.setValue(default_zoom)
#         self.zoom_factor = default_zoom / 100.0

#         # connect signal
#         self.zoom_slider.valueChanged.connect(self.on_zoom_changed)

#         zoom_layout.addWidget(zoom_label)
#         zoom_layout.addWidget(self.zoom_slider)

#         layout.addLayout(zoom_layout)

#         layout.setStretchFactor(image_layout, 1)
#         layout.setStretchFactor(btn_layout, 0)
#         layout.setStretchFactor(zoom_layout, 0)

#         # -------------------------
#         # Phase 3 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Signals
#         # -------------------------

#         self.apply_btn.setMinimumHeight(30)
#         self.cancel_btn.setMinimumHeight(30)
#         self.zoom_slider.setMinimumHeight(25)

#         self.apply_btn.clicked.connect(self.accept)
#         self.cancel_btn.clicked.connect(self.reject)

#         self.rubberBand = qtw.QRubberBand(qtw.QRubberBand.Rectangle, self.left_label)
#         self.origin = qtc.QPoint()

#         self.left_label.setMouseTracking(True)

# class ImagePreviewDialog(qtw.QDialog):
#     def __init__(self, original_qimage, processor, params=None, parent=None):
#         super().__init__(parent)

#         # -------------------------
#         # Phase 1 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â CORE STATE (ALWAYS FIRST)
#         # -------------------------
#         self.original = original_qimage
#         self.processor = processor
#         self.params = params or {}

#         # ÃƒÂ¢Ã…â€œÃ¢â‚¬Â¦ MUST exist before ANY preview call
#         self.zoom_factor = 0.11   # 11% default (your preferred baseline)

#         # -------------------------
#         # Phase 2 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â WINDOW SETUP
#         # -------------------------
#         screen = qtw.QApplication.primaryScreen().availableGeometry()
#         self.resize(int(screen.width() * 0.8), int(screen.height() * 0.8))
#         self.setWindowTitle("Preview")
#         self.update_preview()

#     # ÃƒÂ¢Ã…â€œÃ¢â‚¬Â¦ THIS MUST BE AT CLASS LEVEL (not inside __init__)
#     def eventFilter(self, obj, event):
#         if obj == self.left_scroll.viewport():

#             if event.type() == qtc.QEvent.MouseButtonPress:
#                 self.origin = self.left_label.mapFrom(
#                     self.left_scroll.viewport(), event.pos()
#                 )
#                 self.rubberBand.setGeometry(qtc.QRect(self.origin, qtc.QSize()))
#                 self.rubberBand.show()

#             elif event.type() == qtc.QEvent.MouseMove:
#                 if self.rubberBand.isVisible():
#                     current_pos = self.left_label.mapFrom(
#                         self.left_scroll.viewport(), event.pos()
#                     )
#                     rect = qtc.QRect(self.origin, current_pos).normalized()
#                     self.rubberBand.setGeometry(rect)

#             elif event.type() == qtc.QEvent.MouseButtonRelease:
#                 self.rubberBand.hide()

#                 current_pos = self.left_label.mapFrom(
#                     self.left_scroll.viewport(), event.pos()
#                 )
#                 rect = qtc.QRect(self.origin, current_pos).normalized()

#                 scale = self.zoom_factor

#                 x = int(rect.x() / scale)
#                 y = int(rect.y() / scale)
#                 w = int(rect.width() / scale)
#                 h = int(rect.height() / scale)

#                 self.params.update({
#                     "x": x,
#                     "y": y,
#                     "w": max(1, w),
#                     "h": max(1, h)
#                 })

#                 print(f"[CROP] x={x}, y={y}, w={w}, h={h}")

#                 self.update_preview()

#         return super().eventFilter(obj, event)

#         # -------------------------
#         # Phase 4 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â NOW safe to process
#         # -------------------------
#         self.update_preview()

#     def on_zoom_changed(self, value):
#         print(f"[ZOOM] Slider value: {value}")  # debug
#         self.zoom_factor = value / 100.0
#         self.update_preview()

#     def update_preview(self):
#         if not self.original or self.original.isNull():
#             return

#         # Process image
#         processed = self.processor(self.original, self.params)

#         # Convert to pixmaps
#         orig_pix = qtg.QPixmap.fromImage(self.original)
#         proc_pix = qtg.QPixmap.fromImage(processed)

#         # Apply zoom scaling ONLY HERE
#         scale = self.zoom_factor

#         new_size = orig_pix.size() * scale

#         orig_scaled = orig_pix.scaled(
#             new_size,
#             qtc.Qt.KeepAspectRatio,
#             qtc.Qt.SmoothTransformation
#         )

#         proc_scaled = proc_pix.scaled(
#             new_size,
#             qtc.Qt.KeepAspectRatio,
#             qtc.Qt.SmoothTransformation
#         )

#         self.left_label.setPixmap(orig_scaled)
#         self.right_label.setPixmap(proc_scaled)

#     def get_result(self):
#         return self.processor(self.original, self.params)

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
