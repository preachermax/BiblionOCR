# Python imports
import csv
import json
import os
import re
from pathlib import Path
from HelpSystem import add_help_menu

#import glob
import shutil
import sys
import time
#import pyautogui
#from tempfile import NamedTemporaryFile
import pandas as pd
import json
import platform

#from ImageQt import ImageQt
import cv2
import numpy as np
import pytesseract
import qimage2ndarray
import tiffcapture
#from subprocess import Popen, PIPE, CalledProcessError

from PIL import Image, ImageDraw, ImageFont, ImageQt

# PyQt5 imports
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5 import QtWidgets as qtw
from PyQt5.QtWidgets import  QSpinBox, QRubberBand, QWidget, QHBoxLayout, QSizeGrip, QMenu, QFrame, QProgressBar
from PyQt5.QtCore import QPoint, QRect, QSize, Qt, QObject, QThread, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QBrush


from queue import Queue
from ext import mainfind
from MyBoxerUI import Ui_Boxer
from Training import Train as tr
from PreProcess import PreProcess as pp
from SessionManager import SessionManager
from LocalFileDrop import LocalFileDropMixin
from project_status_controller import ProjectStatusController
#from ProjectBrowserUI import Ui_Explorer
#from ProjectBrowser import MyFileBrowser
#from PyQt5.QtCore import QObject, QThread, pyqtSignal
# Dialog Imports
from MySlidersUI import Ui_SliderDialog
from Dialogs.deskew_greekmonoDialog import Ui_deskew_greekmonoDialog
from Dialogs.crop_languagesDialog import Ui_crop_languagesDialog
from Dialogs.crop_greek_linesDialog import Ui_crop_greek_linesDialog
from Dialogs.crop_latin_linesDialog import Ui_crop_latin_linesDialog
from Dialogs.tif_greek_lines_renameDialog import Ui_tifgreekrenamelinesDialog
#from Dialogs.tif_greek_lines_moveDialog import Ui_tifgreekmovelinesDialog
from Dialogs.tif_latin_lines_renameDialog import Ui_tiflatinrenamelinesDialog
from Dialogs.tif_latin_lines_moveDialog import Ui_tiflatinmovelinesDialog
from Dialogs.tif_greek_lines_stageDialog import Ui_tifgreekstagelinesDialog
from Dialogs.ImageTextPairDialog import Ui_ImageTextPairDialog
from Dialogs.split_greek_text_linesDialog import Ui_splitgreektextlinesDialog
from Dialogs.rename_greek_text_linesDialog import Ui_renamegreektextlinesDialog

###########    Unused Thread Classes   ############
'''class WriteStream(object):
    # The new Stream Object which replaces the default stream associated with sys.stdout
    # This object just puts data in a queue!
    def __init__(self,queue):
        self.queue = queue

    def write(self, text):
        self.queue.put(text)

    def flush(self):
        """
        Stream flush implementation
        """
        pass'''
'''class ThreadConsoleTextQueueReceiver(qtc.QObject):
    # A QObject (to be run in a QThread) which sits waiting for data to come through a Queue.Queue().
    # It blocks until data is available, and once it has got something from the queue, it sends
    # it to the "MainThread" by emitting a Qt Signal
    queue_element_received_signal = qtc.pyqtSignal(str)

    def __init__(self, q: Queue, *args, **kwargs):
        qtc.QObject.__init__(self, *args, **kwargs)
        self.queue = q

    @qtc.pyqtSlot()
    def run(self):
        self.queue_element_received_signal.emit('---> Console text queue reception Started <---\n')
        while True:
            text = self.queue.get()
            self.queue_element_received_signal.emit(text)

    @qtc.pyqtSlot()
    def finished(self):
        self.queue_element_received_signal.emit('---> Console text queue reception Stopped <---\n')'''
'''class Logging(qtc.QObject):
    def setup_logging(log_prefix):
        global __is_setup_done

        if __is_setup_done:
            pass
        else:
            __log_file_name = "{}-{}_log_file.txt".format(log_prefix,
                                                        datetime.datetime.utcnow().isoformat().replace(":", "-"))

            __log_format = '%(asctime)s - %(name)-30s - %(levelname)s - %(message)s'
            __console_date_format = '%Y-%m-%d %H:%M:%S'
            __file_date_format = '%Y-%m-%d %H-%M-%S'

            root = logging.getLogger()
            root.setLevel(logging.DEBUG)

            console_formatter = logging.Formatter(__log_format, __console_date_format)

            file_formatter = logging.Formatter(__log_format, __file_date_format)
            file_handler = logging.FileHandler(__log_file_name, mode='a', delay=True)

            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(file_formatter)
            root.addHandler(file_handler)

            tqdm_handler = TqdmLoggingHandler()
            tqdm_handler.setLevel(logging.DEBUG)
            tqdm_handler.setFormatter(console_formatter)
            root.addHandler(tqdm_handler)

            __is_setup_done = True

class TqdmLoggingHandler(logging.StreamHandler):

    def __init__(self, level=logging.NOTSET):
        logging.StreamHandler.__init__(self)

    def emit(self, record):
        msg = self.format(record)
        tqdm.write(msg)
        # from https://stackoverflow.com/questions/38543506/change-logging-print-function-to-tqdm-write-so-logging-doesnt-interfere-wit/38739634#38739634
        self.flush()
'''

###########    Partially Used Classes    ############
class ProgThread(QThread):
    # Create a counter thread
    change_value = pyqtSignal(int)
    def run(self):
        cnt = 0
        while cnt < 100:
            cnt+=1
            time.sleep(0.3)
            self.change_value.emit(cnt)

class VLine(QFrame):
    # a simple VLine, like the one you get from designer
    def __init__(self):
        super(VLine, self).__init__()
        self.setFrameShape(self.VLine|self.Sunken)

class changedSignalTest(QObject):
    signaltest = pyqtSignal(str,dict)

###########    Main Application Window Class    ############
class MainWindow(LocalFileDropMixin, qtw.QMainWindow):

###########    Initialize Main Application Window    ############
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #Set Project Path
        self.mod_dirname = os.path.dirname(__file__)
        up_once = os.path.join(self.mod_dirname,"..")
        up_twice = os.path.join(up_once,"..")
        self.mod_rootdir = up_twice
        self.mod_realpath = os.path.realpath(self.mod_rootdir)
        self.mod_abspath = os.path.abspath(self.mod_realpath)
        self.mod_relpath = os.path.relpath(self.mod_abspath)
        self.projecthome = self.mod_abspath + os.sep
        self.session_manager = SessionManager(os.path.join(self.projecthome, 'Model', 'Project', 'Data', 'json'))
        print(f'OS Path dirname: {self.mod_dirname}')
        print(f'OS Path rootdir: {self.mod_rootdir}')
        print(f'OS Path realpath: {self.mod_realpath}')
        print(f'OS Path abspath: {self.mod_abspath}')
        print(f'OS Path relpath: {self.mod_dirname}')
        print(f'Project Home: {self.projecthome}')

        # pre-compiled QtDesigner Ui_MainUI and extended slots code starts here:
        # load the pre-compiled QtDesigner Ui_MainUI user interface
        self.ui = Ui_Boxer()
        self.ui.setupUi(self)
        self.install_local_file_drop(
            [self, getattr(self.ui, 'BoxWidget', None)],
            image_handler=self.getImage,
            text_handler=self.getText,
        )
        #Implement Co-pilot Help system
        add_help_menu(self, 'MyBoxer')
        self.ui.ImageTab.currentChanged.connect(self.on_tabChanged)
        # Manual
        self.ui.actionManually_Crop_Page.triggered.connect(self.pagebox_make_split)
        self.ui.actionEdit_Greek_PageBox.triggered.connect(self.pagebox_edit_split)
        #self.ui.actionEdit_Latin_PageBox.triggered.connect(self.pagebox_edit_split)
        #self.ui.actionCropPage.triggered.connect(self.crop)
        self.ui.actionDeskewPage.triggered.connect(self.deskewImage)
        #self.ui.actionRotatePage.triggered.connect(self.rotateImage)
        self.currentBoxTable = self.ui.LineBoxTable
        self.currentTextTable = self.ui.LineBoxText

        # Auto
        self.ui.actionAuto_Crop_Languages.triggered.connect(self.actionCrop_Languages)
        #self.ui.actionManually_Crop_Language_Pages.triggered.connect(self.crop_Page)
        self.ui.actionDeskew_Greek_tiff.triggered.connect(self.actionDeskew_Greek_tiff)

        self.ui.actionBatchCrop_Greek_to_tif_Lines_tb.triggered.connect(self.actionCrop_Greek_To_tiff_Lines)
        self.ui.actionRename_Greek_tif_Lines_tb.triggered.connect(self.actionRename_Greek_tiff_Lines)
        self.ui.actionStage_Greek_tif_Lines_tb.triggered.connect(self.actionStage_Greek_tiff_Lines)

        self.ui.actionAutoCrop_Latin_To_tif_Lines_tb.triggered.connect(self.actionCrop_Latin_To_tiff_Lines)
        self.ui.actionRename_Latin_tif_Lines_tb.triggered.connect(self.actionRename_Latin_tiff_Lines)
        self.ui.actionStage_Latin_tif_Lines_tb.triggered.connect(self.actionStage_Latin_tiff_Lines)

        self.ui.actionSplitGreek_text_lines_tb.triggered.connect(self.actionSplitGreek_text_lines)
        self.ui.actionRenameGreek_text_lines_tb.triggered.connect(self.actionRenameGreek_text_lines)

        self.ui.actionSplit_Latin_Text_Lines_tb.triggered.connect(self.actionSplit_Latin_Text_Lines)
        self.ui.actionRename_Latin_Text_Lines_tb.triggered.connect(self.actionRename_Latin_Text_Lines)

        self.ui.actionFind_and_Replace.triggered.connect(mainfind.Find(self).show)
        self.ui.actionToggle_Greek_Toolbars.triggered.connect(self.toggleGreekToolbars)
        #self.ui.actionToggle_Latin_Toolbars.triggered.connect(self.toggleLatinToolbars)
        self.ui.actionDark_Orange.triggered.connect(self.darkOrange)
        self.ui.actionDark_Blue.triggered.connect(self.darkBlue)
        self.ui.actionClassic.triggered.connect(self.classic)
        self.ui.actionStandardUI.triggered.connect(self.standardUI)
        self.ui.actionProject_Explorer.triggered.connect(self.OpenProjectExplorer)

        self.ui.actionMake_Greek_LineBox_Files.triggered.connect(self.linebox_make_split)
        self.ui.actionEdit_Greek_LineBox_Pair.triggered.connect(self.linebox_edit_split)
        self.ui.actionDraw_Table_LineBox_tb.triggered.connect(self.putSbLineBox)
        self.ui.actionDraw_Selected_LineBox_tb.triggered.connect(self.getRbLineBox)
        #self.ui.actionEdit_Latin_LineBox_Pair.triggered.connect(self.linebox_edit_split)

        self.ui.OpenImageFilebutton.clicked.connect(self.loadImage)
        self.ui.action_Pixler.triggered.connect(self.OpenWithMyPixler)
        #self.ui.action_Grounder.triggered.connect(self.OpenWithMyGrounder)

        #self.ui.CharBoxImagebutton.clicked.connect(self.loadcharboximage)
        #self.ui.WordBoxImagebutton.clicked.connect(self.loadwordboximage)
        self.ui.actionMake_Character_Box_Files.triggered.connect(self.loadcharboximage)
        self.ui.actionMake_Word_Box_Files.triggered.connect(self.loadwordboximage)

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

        self.ui.LineCheckBox.stateChanged.connect(self.getLineBoxImageLines)

        self.ui.Zoombutton.clicked.connect(self.get_zoom)
        self.ui.ZoomComboBox.currentTextChanged.connect(self.on_zoom)
        self.ui.Zoomslider.valueChanged.connect(self.on_zoomslider)
        self.ui.Zoomslider.sliderReleased.connect(self.DisableZoomSlider)
        self.ui.Zoomslider.hide()
        self.ui.LHDialogbutton.clicked.connect(self.GetLineSpacing)
        self.ui.LHslider.valueChanged.connect(self.SetLineSpacing)
        self.ui.LHslider.sliderReleased.connect(self.DisableLHSlider)
        self.ui.LHlineEdit.textChanged.connect(self.MoveLHSlider)
        self.ui.LHslider.hide()

        self.ui.EditCorrectedTextbutton.clicked.connect(self.loadText)
        self.ui.SaveAsBoxCorrTextbutton.clicked.connect(self.SaveAsCorrectedTextFileDialog)
        self.ui.SaveBoxCorrTextbutton.clicked.connect(self.SaveCorrectedTextFileDialog)

        #self.ui.MyWriterbutton.clicked.connect(self.OpenWithMyWriter)
        #self.ui.textButton.clicked.connect(self.editText)
        #self.ui.tableButton.clicked.connect(self.editTable)
        self.ui.reloadImagebutton.clicked.connect(self.drawLineBoxImage)

        self.ui.LineBoxTable.setCornerButtonEnabled(False)
        self.ui.LineBoxTable.setContextMenuPolicy(qtc.Qt.CustomContextMenu)
        self.ui.LineBoxTable.customContextMenuRequested.connect(self.openTableMenu)

        self.ui.PageBoxTable.setCornerButtonEnabled(False)
        self.ui.PageBoxTable.setContextMenuPolicy(qtc.Qt.CustomContextMenu)
        self.ui.PageBoxTable.customContextMenuRequested.connect(self.openTableMenu)

        self.ui.reloadTextbutton.clicked.connect(self.BoxText2BoxTable)
        self.ui.fontComboBox.currentFontChanged.connect(self.on_font_update)
        self.ui.fontSizeBox.valueChanged.connect(self.on_font_update)
        self.ui.OCRModelComboBox.currentTextChanged.connect(self.on_lang_select)

        self.ui.bookComboBox.currentTextChanged.connect(self.selectBookCombo)

        # UI and slots code ends here.

        # Show the Main user interface
        self.ui.BoxDocument = qtg.QTextDocument(self.currentTextTable)
        font = self.session_manager.build_workflow_font(
            "FROMVS [MAXR]",
            20,
            os.path.dirname(os.path.realpath(__file__)),
        )
        self.ui.BoxDocument.setDefaultFont(font)
        self.currentTextTable.setFont(font)
        self.ui.BoxBlockFormat = qtg.QTextBlockFormat()
        self.currentTextTableFormat = qtg.QTextFormat()
        self.ui.BoxCursor = qtg.QTextCursor(self.ui.BoxDocument)

        self.currentTextTable.setDocument(self.ui.BoxDocument)

        #self.ui.progressBar.valueChanged.connect(self.restartProgressTimer)
        # Initialize statusProgressBar Widget -- invoke addWidget as needed
        self.statusProgressBar = qtw.QProgressBar()
        self.statusProgressBar.resize(140,22)
        self.statusProgressBar.setProperty("value", 0)
        self.statusProgressBar.setObjectName("statusProgressBar")
        # statusBoxTypeLabel and statusBoxType
        self.statusBoxTypeLabel = qtw.QLabel()
        self.statusBoxTypeLabel.setText('Box Type: ')
        self.statusBoxType = qtw.QLabel()
        self.statusBoxType.resize(50,22)
        self.statusBoxType.setStyleSheet('border: 0; color:  blue;')
        font = qtg.QFont()
        font.setFamily("FROMVS [MAXR]")
        font.setPointSize(11)
        self.statusBoxType.setFont(font)
        self.statusBoxType.setAlignment(qtc.Qt.AlignCenter)
        self.statusBoxType.setText('None')
        # statusBoxModeLabel and statusBoxMode
        self.statusBoxModeLabel = qtw.QLabel()
        self.statusBoxModeLabel.setText('Box Mode: ')
        self.statusBoxMode = qtw.QLabel()
        self.statusBoxMode.resize(50,22)
        self.statusBoxMode.setStyleSheet('border: 0; color:  blue;')
        font = qtg.QFont()
        font.setFamily("FROMVS")
        font.setPointSize(11)
        self.statusBoxMode.setFont(font)
        self.statusBoxMode.setAlignment(qtc.Qt.AlignCenter)
        self.statusBoxMode.setText('None')
        # statusDrawingModeLabel and statusDrawingMode
        self.statusDrawingModeLabel = qtw.QLabel()
        self.statusDrawingModeLabel.setText('Drawing Mode: ')
        self.statusDrawingMode = qtw.QLabel()
        self.statusDrawingMode.resize(50,22)
        self.statusDrawingMode.setStyleSheet('border: 0; color:  blue;')
        font = qtg.QFont()
        font.setFamily("FROMVS")
        font.setPointSize(11)
        self.statusDrawingMode.setFont(font)
        self.statusDrawingMode.setAlignment(qtc.Qt.AlignCenter)
        self.statusDrawingMode.setText('None')
        # statusSelectionModeLabel and statusSelectionMode
        self.statusSelectionModeLabel = qtw.QLabel()
        self.statusSelectionModeLabel.setText('Selection Mode: ')
        self.statusSelectionMode = qtw.QLabel()
        self.statusSelectionMode.resize(50,22)
        self.statusSelectionMode.setStyleSheet('border: 0; color:  blue;')
        font = qtg.QFont()
        font.setFamily("FROMVS")
        font.setPointSize(11)
        self.statusSelectionMode.setFont(font)
        self.statusSelectionMode.setAlignment(qtc.Qt.AlignCenter)
        self.statusSelectionMode.setText('None')
        # statusSpacerLabel
        self.statusSpacerLabel = qtw.QLabel()
        self.statusSpacerLabel.setText('     ')

        # Create Default Status Bar Permanent Widgets
        self.ui.statusbar.addPermanentWidget(VLine())
        self.ui.statusbar.addPermanentWidget(self.statusBoxTypeLabel)
        self.ui.statusbar.addPermanentWidget(self.statusBoxType)
        self.ui.statusbar.addPermanentWidget(VLine())
        self.ui.statusbar.addPermanentWidget(self.statusBoxModeLabel)
        self.ui.statusbar.addPermanentWidget(self.statusBoxMode)
        self.ui.statusbar.addPermanentWidget(VLine())
        self.ui.statusbar.addPermanentWidget(self.statusDrawingModeLabel)
        self.ui.statusbar.addPermanentWidget(self.statusDrawingMode)
        self.ui.statusbar.addPermanentWidget(VLine())
        self.ui.statusbar.addPermanentWidget(self.statusSelectionModeLabel)
        self.ui.statusbar.addPermanentWidget(self.statusSelectionMode)
        self.ui.statusbar.addPermanentWidget(VLine())
        self.ui.statusbar.addPermanentWidget(self.statusSpacerLabel)

        self.ui.statusbar.showMessage('Ready...')

        #ChrRefText = open(self.userdir + '/Projects/BiblionOCR/ViewController/Application/3-ConductOCR/FROMVS ChrReference.txt').read()
        #self.ui.ChrRefplainTextEdit.setPlainText(ChrRefText)

        #self.imgdir = r"Model/Images/Complete/Greek/tif_greek_pages/greek_book_41_Mark/"

        # Restore BoxerSession settings
        self.get_session_settings()
        self.project_status_controller = ProjectStatusController(
            self,
            'MyBoxer',
            session_manager=self.session_manager,
        )
        #self.ui.progressBar.setStyleSheet("QProgressBar {border: 2px solid grey;border-radius:8px;padding:1px}"
                                       #"QProgressBar::chunk {background:blue}")
        self.ui.progressBar.setStyleSheet("QProgressBar::chunk {background:blue}")


        self.ui.ImageTab.setCurrentIndex(3)
        self.currenttabindex = self.ui.ImageTab.currentIndex()
        self.currenttabtext = self.ui.ImageTab.tabText(self.currenttabindex)
        self.origpixmap = None
        self.box_color = "red"
        self.dirIterator = None
        self.imgfileList = []
        self.txtfileList = []
        self.imgpath = ""
        self.txtpath = ""
        self.imgopentitle = "Open Image"
        self.txtopentitle = "Open Text"
        #self.ui.bookComboBox.setCurrentText(self.bookabbr)
        #print('current book:',self.bookabbr)

        #self.disableMouseEvents()

        '''
        #setup_logging(self.__class__.__name__)
        #self.__logger = logging.getLogger(self.__class__.__name__)
        #self.__logger.setLevel(logging.DEBUG)

        # create console text queue
        self.queue_console_text = Queue()

        # redirect stdout to the queue
        output_stream = WriteStream(self.queue_console_text)
        sys.stdout = output_stream

        #self.thread_initialize = qtc.QThread()

        #self.init_procedure_object = InitializationProcedures(self)

        # create console text read thread + receiver object
        self.thread_queue_listener = qtc.QThread()
        self.console_text_receiver = ThreadConsoleTextQueueReceiver(self.queue_console_text)

        # connect receiver object to widget for text update
        self.console_text_receiver.queue_element_received_signal.connect(self.append_text)

        # attach console text receiver to console text thread
        self.console_text_receiver.moveToThread(self.thread_queue_listener)

        # attach to start / stop methods
        self.thread_queue_listener.started.connect(self.console_text_receiver.run)
        self.thread_queue_listener.finished.connect(self.console_text_receiver.finished)
        self.thread_queue_listener.start()
        '''


        # Install a custom output stream by connecting sys.stdout to instance of Streamer.
        #sys.stdout = Streamer(textWritten=self.output_terminal_written)

        #self.show()
        #self.toggleLatinToolbars()

        # This should work if pyqtcss can be imported
        '''styles = pyqtcss.available_styles()
        print(f'Available styles: {styles}')
        style_string = pyqtcss.get_style("dark_orange")
        self.ui.BoxWidget.setStyleSheet(style_string)'''

        #def restartProgressTimer(self):
            #self.progtimer = self.ui.progressBar.value()
            #while self.progtimer < 100:
                #self.progtimer+=1
                #time.sleep(0.3)
                #self.ui.progressBar.setValue(self.progtimer)
            #self.thread = ProgThread()
            #self.thread.change_value.connect(self.setProgressVal)
            #self.thread.start()

        #self.startProgressBar()
            # setting for loop to set value of progress bar
            #for i in range(101):

                # slowing down the loop
                #time.sleep(0.05)
        #def setProgressVal(self, val):
            #self.ui.progressBar.setValue(val)

    @qtc.pyqtSlot(str)
    def append_text(self,text):
        #self.ui.OutputText.moveCursor(QTextCursor.End)
        #self.ui.OutputText.insertPlainText(text)
        self.ui.OutputText.append(text)

    '''def onUpdateText(self, text):
        cursor = self.process.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.process.setTextCursor(cursor)
        self.process.ensureCursorVisible()'''
    '''def output_terminal_written(self, text):
        #custom method to write anything printed out to console/terminal to my QTextEdit widget via append function.
        self.ui.OutputText.append(text)'''

###########    Initialize Session    ############
    def get_session_settings(self):
        # get session settings from shared manager
        print("loading session")
        active_project = SessionManager().get_active_project('Session.json')
        self.current_project_root = active_project.get('project_root', '')
        self.current_project_name = active_project.get('project_name', '')
        session = self.session_manager.values('BoxerSession.json')

        def abs_project_path(key: str) -> str:
            value = session.get(key)
            if value:
                return self.projecthome + value
            return getattr(self, key.replace('self.', ''), '')

        def get_setting(name: str, default=None):
            if default is None:
                default = getattr(self, name, None)
            return session.get(f'self.{name}', default)

        self.jsondir = get_setting('jsondir', '')
        self.session = abs_project_path('self.session')
        self.workflow = abs_project_path('self.workflow')
        self.booksmarkdown = abs_project_path('self.booksmarkdown')
        self.booksabbr = abs_project_path('self.booksabbr')
        self.font = get_setting('font', '')
        self.fontsize = get_setting('fontsize', '20')
        self.ocrlang = get_setting('ocrlang', '')
        self.ocrmodel = get_setting('ocrmodel', '')
        self.bookabbr = get_setting('bookabbr', '')
        self.chapter = get_setting('chapter', '1')
        self.verse = get_setting('verse', '1')
        self.word = get_setting('word', '1')
        self.chr = get_setting('chr', '1')
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
        self.dirIterator = get_setting('dirIterator', None)
        self.imgfileList = get_setting('imgfileList', [])
        self.pixmap = get_setting('pixmap', '')
        self.qimage = get_setting('qimage', '')
        self.zoom = get_setting('zoom', '25 %')
        self.zoomslidervalue = get_setting('zoomslidervalue', '25')
        self.img_xoffset = get_setting('img_xoffset', 0)
        self.img_yoffset = get_setting('img_yoffset', 0)
        self.txtpath = get_setting('txtpath', '')
        self.txtdir = get_setting('txtdir', '')
        self.txtfileList = get_setting('txtfileList', [])
        self.txtpagesbox = abs_project_path('self.txtpagesbox')
        self.jsonpagebox = abs_project_path('self.jsonpagebox')
        self.txtgreeklinebox = get_setting('txtgreeklinebox', '')
        self.jsongreeklinebox = get_setting('jsongreeklinebox', '')
        self.txtlatinlinebox = get_setting('txtlatinlinebox', '')
        self.glyph = get_setting('glyph', '')
        self.glyphname = get_setting('glyphname', '')
        self.glyphencode = get_setting('glyphencode', '')
        self.pages = abs_project_path('self.pages')
        self.pagesrotated = abs_project_path('self.pagesrotated')
        self.pagesdeskewed = abs_project_path('self.pagesdeskewed')
        self.pagescropped = abs_project_path('self.pagescropped')
        self.pagescleaned = abs_project_path('self.pagescleaned')
        self.pagesbox = abs_project_path('self.pagesbox')
        self.pageseliminated = abs_project_path('self.pageseliminated')
        self.greekpagesautosplit = abs_project_path('self.greekpagesautosplit')
        self.greekpages = get_setting('greekpages', '')
        self.greekpagesbox = get_setting('greekpagesbox', '')
        self.greeklinesbox = get_setting('greeklinesbox', '')
        self.greeklinesautosplit = get_setting('greeklinesautosplit', '')
        self.latinpagesautosplit = abs_project_path('self.latinpagesautosplit')
        self.latinpages = get_setting('latinpages', '')
        self.latinpagesbox = get_setting('latinpagesbox', '')
        self.latinlinesbox = get_setting('latinlinesbox', '')
        self.latinlinesautosplit = get_setting('latinlinesautosplit', '')

        self.ui.fontComboBox.setCurrentText(self.font)
        self.ui.fontSizeBox.setValue(int(self.fontsize) if str(self.fontsize).isdigit() else self.ui.fontSizeBox.value())
        self.ui.OCRlangComboBox.setCurrentText(self.ocrlang)
        self.ui.OCRModelComboBox.setCurrentText(self.ocrmodel)
        self.ui.bookComboBox.setCurrentText(self.bookabbr)
        self.ui.LHlineEdit.setText(self.linespacing)

    def save_session_settings(self, **updates):
        self.session_manager.update('BoxerSession.json', updates)

    def get_workflow_settings(self):

        # Opening JSON file
        with open(self.workflow) as f:
            # returns JSON object as
            # a dictionary
            data = json.load(f)

        # Iterating through the json
        # list
        for Sequence in data:
            print(Sequence['Sequence'], Sequence['DialogUi'],Sequence['DefaultSource'])

        # Closing file
        f.close()

###########    Start Application    ############

    def on_tabChanged(self):
        self.currenttabindex = self.ui.ImageTab.currentIndex()
        self.currenttabtext = self.ui.ImageTab.tabText(self.currenttabindex)
        print(f'Current Tab: {self.currenttabtext}')
        #if self.imgpath:
        if self.currenttabtext == "Line Box":
            #if self.statusBoxMode.text() == 'Make':
                #self.imgdir = self.greekpages
            #elif self.statusBoxMode.text() == 'Edit':
            self.currentBoxImage = self.ui.LineBoxImage
            self.currentBoxTable = self.ui.LineBoxTable
            self.currentTextTable = self.ui.LineBoxText
            self.imgdir = self.greeklinesbox
            print(f'TabChanged Image Dir: {self.imgdir}')
            self.imgopentitle = "Open Line Box Image"
            self.txtdir = self.txtgreeklinebox
            self.txtopentitle = "Open Line Box Text"
        elif self.currenttabtext == "Page Image":
            self.pageimage = self.imgpath
            self.imgdir = self.greekpages
        elif self.currenttabtext == "Page Box":
            #self.imgstrippath = self.imgpath.split("_")
            #self.imgpath = self.imgstrippath[0] + "_pagebox.tif"
            #if self.statusBoxMode.text() == 'Make':
                #self.imgdir = self.greekpages
            #elif self.statusBoxMode.text() == 'Edit':
                #self.imgdir = self.pagesbox
            self.currentBoxImage = self.ui.PageBoxImage
            self.currentBoxTable = self.ui.PageBoxTable
            self.currentTextTable = self.ui.PageBoxText
            self.imgdir = self.greekpagesbox
            print(f'TabChanged Image Dir: {self.imgdir}')
            self.imgopentitle = "Open Page Box Image"
            self.txtdir = self.txtpagesbox
            self.txtopentitle = "Open Page Box Text"
        elif self.currenttabtext == "Source Image":
            self.imgstrippath = self.imgpath.split("_")
            self.imgpath = self.imgstrippath[0] + ".tif"
            self.imgdir = "Model/Project/Images/Complete/Source/tif_black_white"
            self.imgopentitle = "Open Source Image"
            self.txtopentitle = "Open Source Text"
            #print(f'TabChanged Image Dir: {self.imgdir}')
            #self.getImage(self.imgpath)

    def setBoxPaths(self):
        self.imgfilestr = os.path.basename(self.imgpath)
        self.imgfilesplit = os.path.splitext(self.imgfilestr)
        self.imgfilename = self.imgfilesplit[0]
        self.imgfileext = self.imgfilesplit[1]


        self.txtfilestr = os.path.basename(self.txtpath)
        self.txtfilesplit = os.path.splitext(self.txtfilestr)
        self.txtfilename = self.txtfilesplit[0]
        self.txtfileext = self.txtfilesplit[1]

        #Line Box Paths
        if self.currenttabtext == "Line Box":
            self.path_of_imgautosplit = self.projecthome + self.greeklinesautosplit + r"/"
            self.path_of_imglinebox = self.projecthome + self.greeklinesbox + r"/" + self.greekbookmarkdown + r"/"
            self.path_of_txtlinebox = self.projecthome + self.txtgreeklinebox + r"/" + self.greekbookmarkdown + r"/"
            #self.path_of_jsonlinebox = self.projecthome + self.jsongreeklinebox + r"/" + self.greekbookmarkdown + r"/"
            self.jsonpath = self.projecthome + self.jsongreeklinebox + r"/" + self.greekbookmarkdown + r"/"
            self.imglineboxfile = self.path_of_imglinebox + self.imgfilename.replace("_linebox", "") + "_linebox" + self.imgfileext
            #if self.statusBoxMode.text() == 'Make':
                #self.imglineboxfile = self.projecthome + self.imgfilename + "_linebox" + self.imgfileext
            #elif self.statusBoxMode.text() == 'Edit':
                #self.imglineboxfile = self.projecthome + self.imgfilename + self.imgfileext
            self.boximgpath = self.imglineboxfile
            self.txtpath = self.path_of_txtlinebox + self.imgfilename.replace("_linebox", "") + "_linebox.txt"
            self.txtfilestr = os.path.basename(self.txtpath)
            self.txtfilesplit = os.path.splitext(self.txtfilestr)
            self.txtfilename = self.txtfilesplit[0]
            self.txtfileext = self.txtfilesplit[1]
        #Page Image Paths
        elif self.currenttabtext == "Page Image":
            self.pageimage = self.imgpath
            self.path_of_image_page = self.projecthome + self.greekpages
        #Page Box Paths
        elif self.currenttabtext == "Page Box":
            self.pageimage = self.imgpath
            self.path_of_image_page = self.projecthome + self.greekpagesbox + r"/"
            self.imgfilestr = os.path.basename(self.imgpath)
            self.imgfilesplit = os.path.splitext(self.imgfilestr)
            self.imgfilename = self.imgfilesplit[0]
            self.imgfileext = self.imgfilesplit[1]
            self.imgpageboxfile = self.path_of_image_page + self.imgfilename.replace("_pagebox", "") + "_pagebox" + self.imgfileext
            self.boximgpath = self.imgpageboxfile
            self.path_of_txtpagebox = self.txtpagesbox + r"/"
            self.path_of_jsonpagebox = self.jsonpagebox + r"/"
            self.jsonpath = self.path_of_jsonpagebox + self.imgfilename.replace("_pagebox", "") + "_pagebox.json"
            self.txtpath = self.path_of_txtpagebox + self.imgfilename.replace("_pagebox", "") + "_pagebox.txt"
            self.txtfilestr = os.path.basename(self.txtpath)
            self.txtfilesplit = os.path.splitext(self.txtfilestr)
            self.txtfileext = self.txtfilesplit[1]

    # Combo Boxes
    def initBookCombo(self):

        # Opening JSON file
        with open(self.booksabbr) as f:
            # returns JSON object as
            # a dictionary
            data = json.load(f)

        # Iterating through the json
        # list
        for booknumber in data:
            print(booknumber['bookabbr'])
            self.ui.bookComboBox.addItem(booknumber['bookabbr'])

        # Closing file
        f.close()

        #self.ui.bookComboBox.setEditText(self.bookabbr)'''

    def selectBookCombo(self):
        oldbookabbr = self.bookabbr
        self.bookabbr = self.ui.bookComboBox.currentText()

        if self.ui.bookComboBox.currentText() != oldbookabbr:

            jsonfile = self.booksmarkdown

            with open(jsonfile, 'r') as f:
                data = json.load(f)
                for BookAbbr in data:
                    if BookAbbr['BookAbbr'] == self.bookabbr:
                        bookmarkdown = BookAbbr['BookMarkdown']
                        self.sourcebookmarkdown = 'source'+bookmarkdown
                        self.greekbookmarkdown = 'greek'+bookmarkdown
                        self.latinbookmarkdown = 'latin'+bookmarkdown
                        print(bookmarkdown,self.sourcebookmarkdown,self.greekbookmarkdown,self.latinbookmarkdown)
            f.close()

            self.session_manager.update('BoxerSession.json', {
                'self.bookabbr': self.bookabbr,
                'self.sourcebookmarkdown': self.sourcebookmarkdown,
                'self.greekbookmarkdown': self.greekbookmarkdown,
                'self.latinbookmarkdown': self.latinbookmarkdown,
            })

        self.ui.bookComboBox.setCurrentText(self.bookabbr)

    def OpenProjectExplorer(self):
        mw_cmd = f"python3 \"{os.path.join(self.projecthome, 'ViewController', '0-MainUI', 'MyExplorer.py')}\""
        print(mw_cmd)
        os.system(mw_cmd)
        '''newapp = qtw.QApplication([])
        dirPath = rself.userdir + '/Projects/BiblionOCR/'
        self.explorer = qtw.QMainWindow()
        self.ui = Ui_Explorer()
        self.ui.setupUi(self.explorer)
        fb = MyFileBrowser()
        fb.show()
        #self.explorer.show()
        newapp.exec_()'''

    def OpenWithMyPixler(self):
        mw_cmd = f"python3 \"{os.path.join(self.projecthome, 'ViewController', '0-MainUI', 'MyPixler.py')}\""
        print(mw_cmd)
        os.system(mw_cmd)

    def OpenWithMyWriter(self):

        mw_cmd = f"python3 \"{os.path.join(self.projecthome, 'ViewController', '0-MainUI', 'MyWriter.py')}\""
        print(mw_cmd)
        os.system(mw_cmd)
        '''
        writer.MainWindow = qtw.QMainWindow()
        writer.ui = writer.Ui_MyWriterUI()
        writer.ui.setupUi(writer.MainWindow)"
        writer.MainWindow.show()'''

###########    Source Shared Methods    #############
    # Start Character Box Methods - Moved to Glypher
    def loadcharboximage(self):
        '''Load Character Box Image'''
        img = cv2.imread(self.imgpath)
        self.imgdir = os.path.dirname(self.imgpath)
        filestr = os.path.basename(self.imgpath)
        os.path.splitext(filestr)
        filesplit = os.path.splitext(filestr)
        filename = filesplit[0]
        fileext = filesplit[1]

        self.charboxcsvdir = self.projecthome + "Model/Project/Data/csv/"
        charboxcsvpath = self.charboxcsvdir + filename + r"_charbox.csv"

        '''scale_percent = 25 # percent of original size
        width = int(img.shape[1] * scale_percent / 100)
        height = int(img.shape[0] * scale_percent / 100)
        dim = (width, height)
        resized = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)'''

        #############################################
        #### Detecting Characters  ######
        #############################################
        hImg, wImg,_ = img.shape
        charboxes = pytesseract.image_to_boxes(img,lang="feg")
        # Pass the image to PIL
        pil_im = Image.fromarray(img)

        draw = ImageDraw.Draw(pil_im)
        # use a truetype font
        font = ImageFont.truetype(os.path.join(self.projecthome, "ViewController", "0-MainUI", "fonts", "FROMVS.ttf"), 8)
        #font = ImageFont.truetype("FROMVS.ttf", 20)

        # Draw the text
        #draw.text((10, 700), text_to_show, font=font)

        # Get back the image to OpenCV
        #cv2_im_processed = cv2.cvtColor(np.array(pil_im), cv2.COLOR_RGB2BGR)

        for b in charboxes.splitlines():
            print(b)
            b = b.split(' ')
            print(b)
            x, y, w, h = int(b[1]), int(b[2]), int(b[3]), int(b[4])
            char = b[0]
            cv2.rectangle(img, (x,hImg- y), (w,hImg- h), (255, 50, 50), 2)
            #cv2.putText(img,b[0],(x,hImg- y+25),cv2.FONT_HERSHEY_TRIPLEX,1,(50,50,255),2)

            # Pass the image to PIL
            pil_im = Image.fromarray(img)
            #draw = ImageDraw.Draw(pil_im)
            # use a truetype font

            print(f"Drawing character: {char}")
            #draw.text((x,hImg-y), char, font=font)
            with open(charboxcsvpath, mode='a') as file_:
                file_.write(f"{char}\t{x}\t{y}\t{w}\t{h}")
                file_.write("\n")  # Next line.
        file_.close()
        with open(charboxcsvpath, mode='r') as file_:
            self.currentTextTable.clear()
            self.currentTextTable.insertPlainText(file_.read())
            self.ui.TextLE.setText(f"{filename}_charbox.txt")
        self.charboximagepath = f"Model/Images/Complete/Greek/tif_greek_box/{filename}_charbox.tif"
        self.charboximage = pil_im.save(self.charboximagepath)
        self.ui.ImageLe.setText(f"{filename}_charbox.tif")
        self.showImage(self.charboximagepath)
        #image = ImageQt.ImageQt(pil_im)
        #self.pixmap = qtg.QPixmap(image)

        #self.ui.Image.setPixmap(pixmap)
        #print(pytesseract.image_to_boxes(img,lang="feg"))'''

        #cv2.imshow("CV Image", img)
        #cv2.waitKey(0)
    #Start Word Box Methods --- Move to Lexer
    def loadwordboximage(self):
        '''Load Word Box Image'''
        img = cv2.imread(self.imgpath)
        self.imgdir = os.path.dirname(self.imgpath)
        filestr = os.path.basename(self.imgpath)
        os.path.splitext(filestr)
        filesplit = os.path.splitext(filestr)
        filename = filesplit[0]
        fileext = filesplit[1]

        self.wordboxcsvdir = self.projecthome + "Model/Project/Data/csv/"
        wordboxcsvpath = self.wordboxcsvdir + filename + r"_wordbox.csv"

        '''scale_percent = 25 # percent of original size
        width = int(img.shape[1] * scale_percent / 100)
        height = int(img.shape[0] * scale_percent / 100)
        dim = (width, height)
        resized = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)'''

        ##############################################
        ##### Detecting Words  ######
        ##############################################
        # #[   0          1           2           3           4          5         6       7       8        9        10       11 ]
        # #['level', 'page_num', 'block_num', 'par_num', 'line_num', 'word_num', 'left', 'top', 'width', 'height', 'conf', 'text']
        lines = []
        wordboxes = pytesseract.image_to_data(img,lang="feg")
        #self.currentTextTable.insertPlainText(wordboxes)
        for a,b in enumerate(wordboxes.splitlines()):
            print(b)
            if a!=0:
                b = b.split()
                if len(b)==12:
                    imglinenum, imgwordnum = int(b[4]), int(b[5])
                    x,y,w,h = int(b[6]),int(b[7]),int(b[8]),int(b[9])
                    imgword = b[11]
                    cv2.rectangle(img, (x,y), (x+w, y+h), (255, 50, 50), 2)
                    #cv2.putText(img,b[11],(x,y-5),cv2.FONT_HERSHEY_SIMPLEX,1,(50,50,255),2)
                    # Pass the image to PIL
                    pil_im = Image.fromarray(img)
                    #draw = ImageDraw.Draw(pil_im)
                    # use a truetype font
                    print(f"For Image Line #: {str(imglinenum)} and Image Word #: {str(imgwordnum)} Placing Text Word: {imgword}")
                    #draw.text((x,y-5), imgword, font=font)
                    with open(wordboxcsvpath, mode='a') as file_:
                        file_.write(f"{imglinenum}\t{imgwordnum}\t{imgword}\t{x}\t{y}\t{w}\t{h}")
                        file_.write("\n")  # Next line.
        file_.close()
        with open(wordboxcsvpath, mode='r') as file_:
            self.currentTextTable.clear()
            self.currentTextTable.insertPlainText(file_.read())
            self.ui.TextLE.setText(f"{filename}_wordbox.txt")
        self.wordboximagepath = f"Model/Images/Complete/Greek/tif_greek_box/{filename}_wordbox.tif"
        self.wordboximage = pil_im.save(self.wordboximagepath)
        self.ui.ImageLe.setText(f"{filename}_wordbox.tif")
        self.showImage(self.wordboximagepath)
        #image = ImageQt.ImageQt(pil_im)
        #self.pixmap = qtg.QPixmap(image)

        #self.ui.Image.setPixmap(pixmap)
        #print(pytesseract.image_to_boxes(img,lang="feg"))'''

        #cv2.imshow("CV Image", img)
        #cv2.waitKey(0)
    def word2linebox(self):
        filename = "greek1516_Page_082"
        self.wordboxcsvdir = self.projecthome + "Model/Project/Data/csv/"
        wordboxcsvpath = self.wordboxcsvdir + filename + r"_wordbox.csv"
        with open(wordboxcsvpath, mode='r') as file_:
            self.currentTextTable.clear()
            wordboxes = file_.read()
            self.currentTextTable.insertPlainText(wordboxes)
            self.ui.TextLE.setText(f"{filename}_wordbox.csv")
        file_.close()

        boxfile = open(wordboxcsvpath)
        with boxfile:
            csv_f = csv.reader(boxfile, delimiter = "\t")
            linecount = 1
            for row in csv_f:
                #print(f"linenum: {row[0]} wordnum: {row[1]} word: {row[2]} x: {row[3]} y: {row[4]} w: {row[5]} h: {row[6]}")
                if int(row[0]) == linecount:
                    print(f"linenum: {row[0]} wordnum: {row[1]}")
                linecount =+ 1

###########    Source Image Methods    #############
    def deskewImage(self):
        print("Deskewing current reference image")
        if self.imgpath != "":
            print(f"Source Image Path: {self.imgpath}")
            pp.deskewimage(self.imgpath)
            print("Reloading deskewed image")
            self.showImage(self.imgpath)
        print("Deskew current image complete")

    def setImageStack(self, tiffCaptureHandle):
            """ Set the scene's current TIFF image stack to the input TiffCapture object.
            Raises a RuntimeError if the input tiffCaptureHandle has type other than TiffCapture.
            :type tiffCaptureHandle: TiffCapture
            """
            if type(tiffCaptureHandle) is not tiffcapture.TiffCapture:
                raise RuntimeError("MultiPageTIFFViewerQt.setImageStack: Argument must be a TiffCapture object.")
            self._tiffCaptureHandle = tiffCaptureHandle
            self.showFrame(0)

    def loadImageStackFromFile(self,fileName=''):
        """ Load an image stack from file.
        Without any arguments, loadImageStackFromFile() will popup a file dialog to choose the image file.
        With a fileName argument, loadImageStackFromFile(fileName) will attempt to load the specified file directly.

        if len(fileName) == 0:
            if QT_VERSION_STR[0] == '4':
                fileName = QFileDialog.getOpenFileName(self, "Open TIFF stack file.")
            elif QT_VERSION_STR[0] == '5':
                fileName, dummy = QFileDialog.getOpenFileName(self, "Open TIFF stack file.")"""
        fileName = str(fileName)
        if len(fileName) and os.path.isfile(fileName):
            self._tiffCaptureHandle = tiffcapture.opentiff(fileName)

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

    def showLineFrame(self, i=None):
        self.lineframe = self.getFrame(i)
        if self.lineframe is None:
            return

    def loadImage(self):
        imgdir = self.projecthome + self.imgdir
        print(f'Current Image Folder: {imgdir}')
        self.open_non_modal_image_picker(
            self.imgopentitle or 'Open image file',
            imgdir,
            self.getImage,
            '_image_open_dialog',
        )

    def getImage(self, imgpath):
        self.imgpath = imgpath
        #create file list
        if self.imgpath:
            self.ui.ImageLe.setText(os.path.basename(self.imgpath))
            self.imgfile = qtc.QFile(self.imgpath)
            self.imgfilename = os.path.basename(self.imgpath)
            self.imgdir = os.path.dirname(self.imgpath)
            self.imgfileList = []
        for i in os.listdir(self.imgdir):
            ipath = os.path.normpath(os.path.join(self.imgdir, i))
            if os.path.isfile(ipath) and i.lower().endswith(('.png', '.jpg', '.jpeg', '.tif')):
                self.imgfileList.append(ipath)
        self.sortImgFiles()
        self.showImage(self.imgpath)

    def showImage(self,imgpath):
        self.imgpath = imgpath
        if self.imgpath.endswith('.tif'):
            self.loadImageStackFromFile(self.imgpath)
            self.showFrame(0)
            # Convert frame ndarray to a QImage.
            self.qimage = qimage2ndarray.array2qimage(self.frame, normalize=True)
            self.origpixmap = qtg.QPixmap.fromImage(self.qimage)
            # Convert self.qimage to pixmap
            self.pixmap = qtg.QPixmap.fromImage(self.qimage).scaled(self.ui.SourceImage.size(),
                qtc.Qt.KeepAspectRatio)
        else:
            self.pixmap = qtg.QPixmap(self.imgpath).scaled(self.ui.SourceImage.size(),
                qtc.Qt.KeepAspectRatio)

        if self.pixmap.isNull():
            return
        #self.get_LineImg()
        self.on_zoom()

        #self.ui.Image.setPixmap(self.pixmap) -- moved out to resize_image

        self.imgdir = os.path.dirname(self.imgpath)

        self.session_manager.update('BoxerSession.json', {
            'self.imgpath': self.imgpath,
            'self.imgdir': self.imgdir,
        })

    def sortImgFiles(self):
        #print(f'Image File List: {self.imgfileList}')
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
        self.sorted_imgfilelist = sorted(self.imgfileList, key=alphanum_key)
        #print(f'Sorted Image File List: {self.sorted_imgfilelist}')

    def nextImage(self):
        if self.imgpath:
            self.imgpath = self.sorted_imgfilelist[(self.sorted_imgfilelist.index(self.imgpath) + 1) % len(self.sorted_imgfilelist)]
            self.ui.ImageLe.setText(os.path.basename(self.imgpath))
            self.getImage(self.imgpath)

    def prevImage(self):
        if self.imgpath:
            self.imgpath = self.sorted_imgfilelist[(self.sorted_imgfilelist.index(self.imgpath) - 1) % len(self.sorted_imgfilelist)]
            self.ui.ImageLe.setText(os.path.basename(self.imgpath))
            self.getImage(self.imgpath)

    def ReloadImage(self):
        if self.imgpath:
            self.ui.ImageLe.setText(os.path.basename(self.imgpath))
            self.showImage(self.imgpath)
            self.sortImgFiles()

    def get_zoom(self):
        self.ui.Zoomslider.setEnabled(True)
        self.ui.Zoomslider.show()
        self.zoomValue = self.ui.Zoomslider.value()

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

    def on_zoomslider(self):
        #if self.ui.Zoomslider.isEnabled():
        zoomValue = self.ui.Zoomslider.value()
        self.ui.ZoomComboBox.setCurrentText(str(zoomValue) + " %")
        print(zoomValue)
        self.scale = zoomValue/100
        print(self.scale)

    def on_zoom(self):
        if self.qimage:
            self.ui.ZoomComboBox.currentTextChanged.disconnect(self.on_zoom)
            seltext = self.ui.ZoomComboBox.currentText()
            if self.ui.Zoomslider.isEnabled() == True:
                print('Zoomslider is enabled')
            else :
                print('Zoomslider is disabled')
            if seltext == "Contents":
                print("Resizing to Contents")
                #self.DisableZoomSlider()
                if self.qimage:
                    self.origsize = self.origpixmap.size()
                self.scale = float((self.ui.SourceImagescrollArea.height())/self.origpixmap.height())
                #self.ui.ImagescrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                #self.ui.ImagescrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                #scale_width = float(self.scaled_pixmap.width()/self.origpixmap.width())
                #scale_height = float(self.scaled_pixmap.height()/self.origpixmap.height())
                #image_scale = float(scale_width/scale_height)
                self.ui.ZoomComboBox.setCurrentText(str(int(self.scale*100)) + " %" )
                self.ui.Zoomslider.setValue(int(self.scale*100))
            elif self.ui.Zoomslider.isEnabled() == True:
                print("Resizing to Zoomslider value")
                #self.ui.ImagescrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
                #self.ui.ImagescrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
                self.on_zoomslider()
                selnumtext = seltext.split(" ")
                print(selnumtext[0])
                self.scale = float(selnumtext[0])/100
                print(self.scale)
                #self.resize_image()
            else:
                self.scale = float(int(seltext.split(" ")[0])/100)
                print(f'Starting scale: {self.scale*100}' + ' %')

            print(f'Final scale: {self.scale*100}' + ' %')
            self.scaled_pixmap = self.origpixmap.scaled(self.scale * self.origpixmap.size(), qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)

            print('Resizing contents')
            self.ui.SourceImagescrollAreaWidgetContents.resize(self.scale * self.ui.SourceImagescrollAreaWidgetContents.size())
            print(f'SourceImagescrollAreaWidgetContents size: {self.ui.SourceImagescrollAreaWidgetContents.size()}')
            self.resize_image()
            self.ui.ZoomComboBox.currentTextChanged.connect(self.on_zoom)

    def resize_image(self):
        if self.qimage:
            self.origsize = self.origpixmap.size()
            self.origheight = self.origpixmap.height
            self.origwidth = self.origpixmap.width
            self.scaled_pixmap = self.origpixmap.scaled(self.scale * self.origsize, qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)
            if self.currenttabtext == "Line Box":
                self.currentBoxImage.setPixmap(self.scaled_pixmap)
            elif self.currenttabtext == "Page Image":
                self.ui.PageImage.setPixmap(self.scaled_pixmap)
            elif self.currenttabtext == "Page Box":
                self.currentBoxImage.setPixmap(self.scaled_pixmap)
            elif self.currenttabtext == "Source Image":
                self.ui.SourceImage.setPixmap(self.scaled_pixmap)

###########    Source Text Methods    #############
    def GetOCRText(self):
        my_OCR_rawtext = pytesseract.image_to_string(self.imgpath,lang="feg")
        self.ui.OCRText.insertPlainText(my_OCR_rawtext)

    def editText(self):
        if self.ui.textButton.isChecked():
            self.ui.stackedWidget.setCurrentIndex(0)

    def editTable(self):
        if self.ui.tableButton.isChecked():
            self.ui.stackedWidget.setCurrentIndex(1)

    def loadText(self):
        if not self.txtopentitle:
            self.txtopentitle = "Open Text File"
        self.open_non_modal_text_picker(
            self.txtopentitle,
            f'{self.projecthome}Model/Project/Text/EstablishTruth/Greek/txt_greek_lines_autosplit/',
            self.getText,
            '_text_open_dialog',
        )

    def getText(self,textpath):
            self.txtpath = textpath
            self.txtdirname = os.path.dirname(self.txtpath)
            #create file list
            if self.txtpath:
                #self.currentTextTable.setText(os.path.basename(self.txtpath))
                self.txtfile = qtc.QFile(self.txtpath)
                self.txtfilename = os.path.basename(self.txtpath)
                self.txtdirname = os.path.dirname(self.txtpath)
                self.txtfileList = []
            for t in os.listdir(self.txtdirname):
                #tpath = os.path.join(self.txtdirname, t)
                tpath = self.txtdirname + '/' + t
                if os.path.isfile(tpath) and t.endswith(('.txt')):
                    self.txtfileList.append(tpath)
            self.sortTextFiles()
            self.showText(self.txtpath)

    def showText(self,txtpath):
        self.txtpath = txtpath
        if self.txtpath:
            file = qtc.QFile(self.txtpath)
            filename = os.path.basename(self.txtpath)
            self.txtdir = os.path.dirname(self.txtpath)
            self.ui.TextLE.setText(filename)

            if file.open(qtc.QIODevice.ReadOnly):
                stream = qtc.QTextStream(file)
                text = stream.readAll()
                info = qtc.QFileInfo(self.txtpath)
                self.currentTextTable.clear()
                if info.completeSuffix() == 'txt':
                    #self.ui.editor_text.setHtml(text
                    self.currentTextTable.insertPlainText(text)
                else:
                    self.currentTextTable.setPlainText(text)
            #textfile.close()
            #txtdirpath = os.path.dirname(self.txtpath)

            # update font to selection and size
            self.on_font_update()

            # update line spacing
            self.SetLineSpacing()
            file.close()

        self.session_manager.update('BoxerSession.json', {
            'self.txtpath': self.txtpath,
            'self.txtdir': self.txtdir,
        })

    def sortTextFiles(self):
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
        self.sorted_txtfilelist = sorted(self.txtfileList, key=alphanum_key)

    def nextText(self):
        if self.txtpath:
            self.txtpath = self.sorted_txtfilelist[(self.sorted_txtfilelist.index(self.txtpath) + 1) % len(self.sorted_txtfilelist)]
            self.ui.TextFileName.setText(os.path.basename(self.txtpath))
            self.getText(self.txtpath)

    def prevText(self):
        if self.txtpath:
            self.txtpath = self.sorted_txtfilelist[(self.sorted_txtfilelist.index(self.txtpath) - 1) % len(self.sorted_txtfilelist)]
            self.ui.TextFileName.setText(os.path.basename(self.txtpath))
            self.getText(self.txtpath)

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
                self.currentTextTable.clear()
                if info.completeSuffix() == 'txt':
                    #self.ui.editor_text.setHtml(text
                    self.currentTextTable.insertPlainText(text)
                else:
                    self.currentTextTable.setPlainText(text)

                # update font to selection and size
                self.on_font_update()

                # update line spacing
                self.SetLineSpacing()

    def bothLoad(self):
        ''' load the matching file for either the current image or the current text '''
        def accept():
            #if self.ImageTextPairDialog.Accepted:
            if self.ImageTextPairDialog_ui.MatchTxt2Imgbutton.isChecked():
                print("matching text file to current image file")
                print(self.imgpath)
                if self.imgpath:
                    print("finding matched text file for " + self.imgpath)
                    imgfilename = self.imgpath
                    file = qtc.QFile(imgfilename)
                    filestr = os.path.basename(imgfilename)
                    filedir = os.path.dirname(imgfilename)
                    filesplit = os.path.splitext(filestr)
                    filename = filesplit[0]
                    fileext = filesplit[1]
                    namesplit = filename.split("_")
                    versionref = namesplit[0]
                    pagestr = namesplit[2]
                    pagenum = int(pagestr)
                    print(self.txtdir +r"/"+ versionref + "_Page_" + pagestr + r".txt")
                else:
                    print(self.imgpath + " does not exist")

                self.trytxtpath = self.txtdir +r"/"+ versionref + "_Page_" + pagestr + r".txt"
                if self.trytxtpath:
                    print("opening " + self.trytxtpath)
                    self.txtpath = self.trytxtpath
                    self.showText()
                    #self.ReloadText()
                else:
                    print(self.trytxtpath + " does not exist")

            elif self.ImageTextPairDialog_ui.MatchImg2Txtbutton.isChecked():
                print("matching image file to current text file")
                print(self.txtpath)
                if self.txtpath:
                    print("finding matched image file for " + self.txtpath)
                    txtfilename = self.txtpath
                    file = qtc.QFile(txtfilename)
                    filestr = os.path.basename(txtfilename)
                    filedir = os.path.dirname(txtfilename)
                    filesplit = os.path.splitext(filestr)
                    filename = filesplit[0]
                    fileext = filesplit[1]
                    namesplit = filename.split("_")
                    versionref = namesplit[0]
                    pagestr = namesplit[2]
                    pagenum = int(pagestr)
                    print(self.imgdir +r"/"+ versionref + "_Page_" + pagestr + r".tif")
                else:
                    print(self.txtpath + " does not exist")

                self.tryimgpath = self.imgdir +r"/"+ versionref + "_Page_" + pagestr + r".tif"
                if self.tryimgpath:
                    print("opening " + self.tryimgpath)
                    self.imgpath = self.tryimgpath
                    self.showImage(self.imgpath)
                else:
                    print(self.tryimgpath + " does not exist")


        def reject():
            pass

        self.ImageTextPairDialog = qtw.QDialog()
        self.ImageTextPairDialog_ui = Ui_ImageTextPairDialog()
        self.ImageTextPairDialog_ui.setupUi(self.ImageTextPairDialog)
        self.ImageTextPairDialog.show()

        self.ImageTextPairDialog_ui.buttonBox.accepted.connect(accept)
        self.ImageTextPairDialog_ui.buttonBox.rejected.connect(reject)

    def GetLineSpacing(self):
        self.ui.LHslider.setEnabled(True)
        self.ui.LHslider.show()
        self.ui.LHlineEdit.setPlaceholderText(str(self.ui.LHslider.value()))

    def DisableLHSlider(self):
        self.ui.LHslider.hide()
        self.ui.LHslider.setEnabled(False)

    def MoveLHSlider(self):
        self.ui.LHslider.setEnabled(True)
        self.ui.LHslider.setValue(int(self.ui.LHlineEdit.text()))

    def SetLineSpacing(self):

        '''num,ok = qtw.QInputDialog.getInt(self.ui.BoxWidget,"Proportional Line Spacing","Enter a percent value from 0-200")

        if ok:
            lineSpacing = num
        else:
            lineSpacing = 145'''

        lineSpacing = self.ui.LHslider.value()
        self.ui.LHlineEdit.setText(str(lineSpacing))

        cursor = self.currentTextTable.textCursor()
        if not cursor.hasSelection():
            cursor.select(qtg.QTextCursor.Document)
        bf = self.ui.BoxCursor.blockFormat()
        bf.setLineHeight(lineSpacing, self.ui.BoxBlockFormat.ProportionalHeight)
        cursor.mergeBlockFormat(bf)

    def SaveRawTextFileDialog(self, MainWindow):
        path = qtw.QFileDialog.getSaveFileName(
            self.ui.BoxWidget, 'Save Raw text file',self.txtdir,
            'Text files (*.txt)')[0]
        with open(path, 'w') as file:
            my_RawText = self.ui.BoxDocument.toPlainText()
            file.write(my_RawText)
        filename = os.path.basename(path)
        self.ui.TextLE.setText(filename)
        file.close()

    def SaveAsCorrectedTextFileDialog(self, MainWindow):
        path = qtw.QFileDialog.getSaveFileName(
            self.ui.BoxWidget, 'Save Corrected text file', self.txtdir,
            'Text files (*.txt)')[0]
        with open(path, 'w') as file:
            my_CorrectedText = self.ui.BoxDocument.toPlainText()
            file.write(my_CorrectedText)
        filename = os.path.basename(path)
        self.ui.TextLE.setText(filename)
        file.close()

    def SaveCorrectedTextFileDialog(self, MainWindow):

        #if self.txtdir:
            #defaultdir = self.txtdir
        #else:
            #defaultdir = r"/home/jetson/Projects/Python/EstablishTruth/Greek_txt_pages/"

        defaultdir = self.txtdir + r"/"
        defaultfile = self.ui.TextLE.displayText()

        if defaultfile:
            path = defaultdir + defaultfile
            print(path)
            filename = defaultfile
        else:
            path = qtw.QFileDialog.getSaveFileName(
                self.ui.BoxWidget, 'Save Corrected text file', '',
                'Text files (*.txt)')[0]
            filename = os.path.basename(path)
        with open(path, 'w') as file:
            my_CorrectedText = self.ui.BoxDocument.toPlainText()
            file.write(my_CorrectedText)

        self.ui.TextLE.setText(filename)
        file.close()

    def on_font_update(self):
        # update font to selection and size
        #font = qtg.QFont()
        #font.setFamily(self.ui.fontComboBox.currentFont())
        #print(self.ui.fontComboBox.currentFont())
        font = qtg.QFont(self.ui.fontComboBox.currentFont())
        font.setPointSize(self.ui.fontSizeBox.value())
        #font = qtg.QFont(self.font)
        #font.setPointSize(int(self.fontsize))

        self.currentTextTable.setFont(font)
        self.ui.PageBoxText.setFont(font)

    def on_lang_select(self):
        pass


###########    Page Box Shared Methods    #############
    # Page Toolbar Actions

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
            with open('Model/Data/json/Workflow.json') as f:
                # returns JSON object as
                # a dictionary
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
            with open('Model/Data/json/Workflow.json') as f:
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


        #dsk.deskewfiles("~/Projects/Python/Images/Greek/png_greek/greek_book_40_Matthew/", "~/Projects/Python/Images/Greek/png_greek_deskew/greek_book_40_Matthew/","~/Projects/Python/Images/Greek/tif_greek_deskew/greek_book_40_Matthew/")
        #pp.deskewfiles("~/Projects/Python/Images/Greek/png_greek/greek_book_41_Mark/", "~/Projects/Python/Images/Greek/png_greek_deskew/greek_book_41_Mark/","~/Projects/Python/Images/Greek/tif_greek_deskew/greek_book_41_Mark/")

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
                with open('Model/Data/json/Workflow.json') as f:
                    # returns JSON object as
                    # a dictionary
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

    '''def croplangs(source, boxdir, greekdir, latindir, elimdir):

        dest_of_elimination = elimdir
        dest_of_greek = greekdir
        dest_of_latin = latindir
        dest_of_box = boxdir
        path_of_images = source

        list_of_images = os.listdir(path_of_images)
        for image in list_of_images:

                img = cv2.imread(os.path.join(path_of_images, image))

                filestr = os.path.basename(os.path.join(path_of_images, image))
                filesplit = os.path.splitext(filestr)
                filename = filesplit[0]
                fileext = filesplit[1]

                #filename = os.path.basename(os.path.join(path_of_images, image))
        #load the image
        #image = cv2.imread(args["image"])
        #image = cv2.imread("./Images/tif_newtest/1516_Page_002.tif")
        #cv2.imshow('orig',image)
        #cv2.waitKey(0)

        #grayscale
                gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        #cv2.imshow('gray',gray)
        #cv2.waitKey(0)read

        #binary
                ret,binary = cv2.threshold(gray,127,255,cv2.THRESH_BINARY)

        #binary inversion
                ret,thresh = cv2.threshold(gray,127,255,cv2.THRESH_BINARY_INV)
        #cv2.imshow('thresh',thresh)
        #cv2.waitKey(0)

        #dilation
                kernel = np.ones((70,100), np.uint8)
                img_dilation = cv2.dilate(thresh, kernel, iterations=1)
        #cv2.imshow('dilated',img_dilation)
                #cv2.imwrite((image+'dilation.tif'),img_dilation)
        #cv2.waitKey(0)

        #medianblur
                #median = cv2.medianBlur(img_dilation, 17)
        #cv2.imshow('medianblur',median)
        #cv2.imwrite('medianblur.tif',median)
        #cv2.waitKey(0)

        #find contours
                im2,ctrs, hier = cv2.findContours(img_dilation.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        #set flags for sorting contours top to bottom
                reverse = False
                i = 0

        # construct the list of bounding boxes and sort them from left to right
                boundingBoxes = [cv2.boundingRect(c) for c in ctrs]
                (ctrs, boundingBoxes) = zip(*sorted(zip(ctrs, boundingBoxes), key=lambda b:b[1][i], reverse=reverse))

        # Set initial box count
                bnum = 1
                destfolder = ""
                deststr = ""

                for i,c in enumerate(ctrs):

                        # Get bounding box
                        x, y, w, h = cv2.boundingRect(c)

                        # Get ROI
                        roi = binary[y:y+h, x:x+w]

                        # Set height validation of contour to eliminate unwanted ROI's
                        if w > 1600 and h > 4000:

                                if bnum==1:
                                        destfolder = dest_of_greek
                                        deststr = 'greek'
                                        bnum = bnum + 1
                                else:
                                        destfolder = dest_of_latin
                                        deststr = 'latin'
                                        bnum = 1

                                if destfolder!="":
                                        # Write accepted ROI to correct folder/file
                                        PILimage = Image.fromarray(roi)
                                        thresh = 127
                                        fn = lambda x : 255 if x > thresh else 0
                                        PIL_BWimage = PILimage.convert('L').point(fn, mode='1')
                                        outfile = destfolder+deststr+filename + ".tif"
                                        print("Generating: " + outfile)
                                        PIL_BWimage.save(outfile, "TIFF", dpi=(300,300))

                                        #cv2.imwrite(destfolder+deststr+filename, roi)
                                        # Draw box around accepted ROI
                                        cv2.rectangle(binary,(x,y),( x + w, y + h ),(90,0,255),2)
                                else:
                                        pass
                        else:
                                # Eliminate smaller ROI as noise but save to eliminated folder/file anyway
                                cv2.imwrite(dest_of_elimination + filename + "segment-" + str(i) + fileext, roi)

                cv2.imwrite(os.path.join(dest_of_box, filename + fileext),binary)'''

    def renameimages(source, destination):
            def sorted_alphanumeric(data):
                    convert = lambda text: int(text) if text.isdigit() else text.lower()
                    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
                    return sorted(data, key=alphanum_key)
                    #usage:dirlist = sorted_alphanumeric(os.listdir(...)) - works great!

            path_of_images = source
            dest_of_images = destination
            list_of_images = sorted_alphanumeric(os.listdir(path_of_images))

            print(list_of_images)

            newpagenum = 1
            newlinenum = 1

            for image in list_of_images:
                    img = cv2.imread(os.path.join(path_of_images, image))
                    height, width = img.shape[:2]
                    filestr = os.path.basename(os.path.join(path_of_images, image))
                    filesplit = os.path.splitext(filestr)
                    filename = filesplit[0]
                    fileext = filesplit[1]
                    namesplit = filename.split("_")
                    versionref = namesplit[0]
                    pagestr = namesplit[2]
                    pagenum = int(pagestr)
                    linestr = namesplit[3]
                    #print(versionref,pagenum,linestr)
                    print(f"namesplit: {namesplit} versionref: {versionref} pagestr: {pagestr} pagenum: {pagenum} linestr: {linestr}")
                    linenum = int(re.match('.*?([0-9]+)$', linestr).group(1))
                    #print("Last digits of "+filename+" are "+last_digits)
                    if pagenum > newpagenum:
                            newlinenum = 1
                            newpagenum = pagenum
                    print("pagenum: " + pagestr + "  newpagenum: " + str(newpagenum) + "  linenum: " + str(linenum) + "  newlinenum: " + str(newlinenum))
                    shutil.copy(path_of_images + filestr, dest_of_images + versionref + "_Page_" + pagestr + "_Line" + str(newlinenum) + fileext)
                    newlinenum += 1
                    print("linenum: " + str(linenum) + "  newlinenum: " + str(newlinenum))

    def moveimages(source, destination):
            def sorted_alphanumeric(data):
                    convert = lambda text: int(text) if text.isdigit() else text.lower()
                    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
                    return sorted(data, key=alphanum_key)
                    #usage:dirlist = sorted_alphanumeric(os.listdir(...)) - works great!

            path_of_images = source
            dest_of_groundtruth = destination
            #sorted(os.listdir(os.getcwd()), key=len) does not work

            list_of_images = sorted_alphanumeric(os.listdir(path_of_images))

            #print(list_of_images)

            newpagenum = 1
            newlinenum = 1

            for image in list_of_images:

                    img = cv2.imread(os.path.join(path_of_images, image))

                    height, width = img.shape[:2]

                    filestr = os.path.basename(os.path.join(path_of_images, image))

                    filesplit = os.path.splitext(filestr)

                    filename = filesplit[0]

                    fileext = filesplit[1]

                    namesplit = filename.split("_")

                    versionref = namesplit[0]

                    pagestr = namesplit[2]

                    pagenum = int(pagestr)

                    linestr = namesplit[3]
                    #print(versionref,pagenum,linestr)

                    linenum = int(re.match('.*?([0-9]+)$', linestr).group(1))
                    #print("Last digits of "+filename+" are "+last_digits)

                    if pagenum > newpagenum:

                            newlinenum = 1

                            newpagenum = pagenum

                    print("pagenum: " + pagestr + "  newpagenum: " + str(newpagenum) + "  linenum: " + str(linenum) + "  newlinenum: " + str(newlinenum))

                    shutil.move(path_of_images + filestr, dest_of_groundtruth + versionref + "_Page_" + pagestr + "_Line" + str(newlinenum) + fileext)

                    newlinenum += 1
                            #print("linenum: " + str(linenum) + "  newlinenum: " + str(newlinenum))

    # Page Box Dialogs
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

    # Start Page Box Methods

    # Page Box Methods
    def pagebox_make_split(self):
            path_of_images = self.pages
            dest_of_box = self.pagesbox
            dest_of_elimination = self.pageseliminated
            dest_of_greek = self.greekpagesautosplit
            dest_of_latin = self.latinpagesautosplit

            self.currentBoxTable.verticalHeader().hide()
            self.statusBoxMode.setText('Make')
            self.statusBoxType.setText('Page')
            self.statusDrawingMode.setText('Auto')
            self.editCurrent = False
            #If no page image present, then load one.
            if self.ui.SourceImage.pixmap():
                if self.ui.ImageTab.currentIndex() != 3:
                    self.ui.ImageTab.setCurrentIndex(3)
                    self.loadImage()

                print('Open Make Image message dailog')
                popup = qtw.QMessageBox(self)
                popup.setIcon(qtw.QMessageBox.Information)
                popup.setWindowTitle("Make PageBox File Pair")
                popup.setText("'Make Current' pagebox pair or load and 'Make Other'")
                currentButton = popup.addButton('Make Current', qtw.QMessageBox.YesRole)
                otherButton = popup.addButton('Make Other', qtw.QMessageBox.YesRole)
                popup.exec()
                if popup.clickedButton() == currentButton:
                    self.getImage(self.imgpath)
                elif popup.clickedButton() == otherButton:
                    self.ui.ImageLe.clear()
                    self.ui.SourceImage.clear()
                    self.currentBoxImage.clear()
                    self.ui.TextLE.clear()
                    self.currentTextTable.clear()
                    self.currentBoxTable.clear()
                    # Get imglinebox source file
                    self.loadImage()
            else:
                # Activate the Page Image Tab
                if self.ui.ImageTab.currentIndex() != 3:
                    self.ui.ImageTab.setCurrentIndex(3)
                # Get page box source file
                self.loadImage()
            print(f'from Load Source Image: self.imgpath = {self.imgpath}')
            # setting value to progress bar
            self.ui.progressBar.setValue(10)

            # Make PageBox File Pair
            self.ui.ImageLe.clear()
            self.ui.ImageLe.setText(os.path.basename(self.imgpath))
            dosplit = True
            self.normImage()
            # convert image to binary numpy array for finding contours
            ret,binary = cv2.threshold(self.gray,127,255,cv2.THRESH_BINARY)
            # binary numpy array inversion
            ret,thresh = cv2.threshold(self.gray,127,255,cv2.THRESH_BINARY_INV)
            # binary numpy array dilation
            kernel = np.ones((70,100), np.uint8)
            img_dilation = cv2.dilate(thresh, kernel, iterations=1)
            # binary numpy array medianblur
            #median = cv2.medianBlur(img_dilation, 13)
            # find binary numpy array line contours
            ctrs, hier = cv2.findContours(img_dilation, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            # set flags for sorting contours top to bottom
            reverse = False
            i = 1
            # construct the list of bounding boxes and sort them from top to bottom
            boundingBoxes = [cv2.boundingRect(c) for c in ctrs]
            (ctrs, boundingBoxes) = zip(*sorted(zip(ctrs, boundingBoxes),key=lambda b:b[1][i], reverse=reverse))

            # Activate the Page Box Tab
            if self.ui.ImageTab.currentIndex() != 2:
                self.ui.ImageTab.setCurrentIndex(2)
            else:
                self.on_tabChanged()
            print(f'after tab changed to Page Box: self.imgpath = {self.imgpath}')
            self.ui.progressBar.setValue(40)

            self.setBoxPaths()
            print(f'from setBoxPaths: imgfilename = {self.imgfilename}')
            self.imgpath = self.boximgpath

            # Set initial box count
            bnum = 0
            self.currentTextTable.clear()
            if os.path.exists(self.txtpath):
                print(f'Removing: {self.txtpath}')
                os.remove(self.txtpath)
            with open(self.txtpath, "a") as txtboxfile:
                for i,c in enumerate(ctrs):
                    # Get bounding box
                    x, y, w, h = cv2.boundingRect(c)
                    dividers = int(round(w/3400))
                    # Get ROI
                    roi = binary[y:y+h, x:x+w]
                    #if i >= 0:
                    # Set height validation of contour to eliminate unwanted ROI's
                    if w < 3600 and h > 4000:
                            bnum += 1
                            print(f'Page Box Number: {bnum}')
                            if x <= 2300:
                                    self.pagedestfolder = dest_of_greek
                                    self.pagedeststr = 'greek'
                            elif x >= 2301:
                                    self.pagedestfolder = dest_of_latin
                                    self.pagedeststr = 'latin'

                            if self.pagedestfolder != "":
                                    # Write accepted ROI to correct folder/file
                                    PILimage = Image.fromarray(roi)
                                    thresh = 127
                                    fn = lambda x : 255 if x > thresh else 0
                                    PIL_BWimage = PILimage.convert('L').point(fn, mode='1')
                                    outfile = self.pagedestfolder + r"/" + self.pagedeststr + self.imgfilename + "_pagebox.tif"
                                    print("Generating: " + outfile)
                                    PIL_BWimage.save(outfile, "TIFF", dpi=(300,300))

                                    #cv2.imwrite(destfolder+deststr+filename, roi)
                                    # Draw box around accepted ROI
                                    cv2.rectangle(self.norm,(x,y),( x + w, y + h ),(90,0,255),2)
                                    boxlinestr = str(bnum) + '\t' + str(x) + '\t' + str(y) + '\t' + str(w) + '\t' + str(h) + '\n'
                                    txtboxfile.write(boxlinestr)
                    '''elif w > 3600:
                        # Set width of multi-page contours and subdivide proportionally
                        w = int(round(w/dividers))
                        for subdiv in range(0,dividers):
                            print('subloopcount =' + str(subdiv))
                            roi = binary[y:y+h, x:x+w]
                            cv2.rectangle(self.norm,(x,y),( x + w, y + h ),(0,0,255),2)
                            # Append to LineBoxText
                            boxlinestr = str(bnum) + '\t' + str(x) + '\t' + str(y) + '\t' + str(w) + '\t' + str(h) + '\t' + '\n'
                            txtboxfile.write(boxlinestr)'''

            '''with open(self.txtpath, "a") as txtboxfile:
                for i,c in enumerate(ctrs):
                        # Get bounding box
                        x, y, w, h = cv2.boundingRect(c)
                        dividers = int(round(w/3400))
                        print("countour height = " + str(h) + "\t" + "number of boxes = " + str(dividers))
                        # Set size validation of contour to eliminate unwanted boxes
                        if w < 3600 and h > 4000:
                            #if h>120 and h<200:
                            roi = binary[y:y+h, x:x+w]
                            cv2.rectangle(self.norm,(x,y),( x + w, y + h ),(0,0,255),2)
                            # Append to LineBoxText
                            #boxlinestr = str(bnum) + ',' + str(x) + ',' + str(y) + ',' + str(w) + ',' + str(h) + ',' + str(x+w) + ',' + str(y+h) + '\n'
                            boxlinestr = str(bnum) + '\t' + str(x) + '\t' + str(y) + '\t' + str(w) + '\t' + str(h) + '\n'
                            txtboxfile.write(boxlinestr)
                            self.savePageBoxImagePage(roi,bnum)
                            bnum += 1
                        # Set height of multi-page contours and subdivide proportionally
                        elif w > 3600:
                                w = int(round(w/dividers))
                                for subdiv in range(0,dividers):
                                    print('subloopcount =' + str(subdiv))
                                    roi = binary[y:y+h, x:x+w]
                                    cv2.rectangle(self.norm,(x,y),( x + w, y + h ),(0,0,255),2)
                                    # Append to LineBoxText
                                    boxlinestr = str(bnum) + '\t' + str(x) + '\t' + str(y) + '\t' + str(w) + '\t' + str(h) + '\t' + '\n'
                                    txtboxfile.write(boxlinestr)
                                    y = y + h
                                    #if dosplit:
                                        #self.savePageBoxImagePage(roi,bnum)
                                    bnum += 1'''
                        # setting value to progress bar
                        #self.ui.progressBar.setValue(bnum)

            print(f'Created PageBox Text File: {self.txtpath}')
            #self.txtpath = self.path_of_txtlinebox + self.imgfilename + "_linebox.txt"
            txtboxfile.close()
            self.ui.progressBar.setValue(50)

            # Write Text Box File to PageBoxTable TableWidget
            self.BoxText2BoxTable()
            self.ui.progressBar.setValue(75)

            # Overwrite Text Box File from PageBoxTable TableWidget
            # Already wrote the txtboxfile, above; so,likely unecessary
            self.PageBoxTable2csv()
            self.ui.progressBar.setValue(85)

            # Write page image to file
            self.savePageBoxImage()
            self.ui.ImageLe.clear()
            self.ui.ImageLe.setText(os.path.basename(self.boximgpath))
            self.ui.progressBar.setValue(101)
            self.ui.progressBar.reset()

    # Edit PageBox Method
    def pagebox_edit_split(self):

        self.ui.statusbar.showMessage('Loading the PageBox file pair for editing')
        start = time.perf_counter()
        # Activate the Page Image Tab
        if self.ui.ImageTab.currentIndex() != 2:
            self.ui.ImageTab.setCurrentIndex(2)
        else:
            self.on_tabChanged()
        self.setBoxPaths()
        self.imgpath = self.boximgpath

        self.currentBoxTable.verticalHeader().hide()
        self.statusBoxMode.setText("Edit")
        self.statusBoxType.setText("Page")
        self.statusSelectionMode.setText("Rows")
        self.currentBoxTable.setSelectionBehavior(qtw.QAbstractItemView.SelectRows)

        def loadBoxImage():
            self.ui.ImageLe.clear()
            self.currentBoxImage.clear()
            self.loadImage()
            self.setBoxPaths()
            self.imgpath = self.boximgpath
            self.showImage(self.imgpath)

        self.editCurrent = True
        if self.currentBoxImage.pixmap():
        #if self.ui.ImageLe.displayText() != "":
            popup = qtw.QMessageBox(self)
            popup.setIcon(qtw.QMessageBox.Information)
            popup.setWindowTitle("Edit Mode")
            popup.setText("'Edit Current' pagebox pair or load and 'Edit Other'")
            currentButton = popup.addButton('Edit Current', qtw.QMessageBox.YesRole)
            otherButton = popup.addButton('Edit Other', qtw.QMessageBox.YesRole)
            popup.exec()
            if popup.clickedButton() == currentButton:
                self.getImage(self.imgpath)
                self.editCurrent = True
            elif popup.clickedButton() == otherButton:
                loadBoxImage()
                self.editCurrent = False
        else:
            loadBoxImage()
        self.normImage()
        self.ui.ImageLe.setText(os.path.basename(self.boximgpath))
        print(f"From setBoxPaths: self.txtpath = {self.txtpath}")
        # setting value to progress bar
        self.ui.progressBar.setValue(10)

        # validate image as a PageBox Image
        '''pathsplit = self.imgpath.split('_')
        tailsplit = pathsplit[1]
        if tailsplit == "pagebox.tif":
            is_pagebox = True
        else:
            is_pagebox = False
            print("This is not a valid PageBox Image! Please try again")  # need to throw error'''
        self.ui.TextLE.clear()
        self.ui.TextLE.setText(self.txtfilestr)
        imgfilename = self.ui.ImageLe.displayText().split(r".")[0]
        txtfilename = self.ui.TextLE.displayText().split(r".")[0]
        # Get matching PageBoxText file
        print(f'Text File Name: {txtfilename}  Image File Name: {imgfilename}')
        if txtfilename == imgfilename:
            self.getText(self.txtpath)
            self.ui.progressBar.setValue(25)
            #if drawbox:
                # self.drawPageBoxImage()
            self.ui.progressBar.setValue(50)
            #self.savePageBoxImage()
            self.ui.progressBar.setValue(75)
            self.BoxText2BoxTable()
            self.ui.progressBar.setValue(100)
            print("Waiting on PageBoxTable selection")
            self.row_current = self.currentBoxTable.currentRow()
            self.startEditLoop = True
            self.currentBoxTable.selectionModel().currentRowChanged.connect(self.on_currentRowChanged)
        else:
            print(f'The pagebox text: {txtfilename} does not match the pagebox image: {imgfilename} -- Please try again!')

        self.ui.progressBar.setValue(101)
        self.ui.progressBar.reset()
        finish = time.perf_counter()
        self.ui.statusbar.showMessage(f"File load completed successfully in {finish - start:0.4f} seconds")
        print(f"File load completed successfully in {finish - start:0.4f} seconds")

############    Page Box Image Methods    #############

    def getPageBoxImagePages(self):
        rowcount = self.currentBoxTable.rowCount()
        for row in range(rowcount):
            page = self.currentBoxTable.item(row,0).text()
            x = int(self.currentBoxTable.item(row,1).text())
            y = int(self.currentBoxTable.item(row,2).text())
            w = int(self.currentBoxTable.item(row,3).text())
            h = int(self.currentBoxTable.item(row,4).text())
            linex = x+w-80
            liney = y+h-4
            '''if self.ui.LineCheckBox.isChecked():
                print(f'Placing line number at : {linex},{liney}')
                cv2.putText(self.norm,line,(linex,liney),cv2.FONT_HERSHEY_SIMPLEX,2,(255,0,0),3)
            else:
                print(f'Removing line number at : {linex},{liney}')
                cv2.putText(self.norm,line,(linex,liney),cv2.FONT_HERSHEY_SIMPLEX,2,(255,255,255),3)'''
        pil_img = Image.fromarray(self.norm)
        qimage = ImageQt.ImageQt(pil_img)
        self.pixmap = qtg.QPixmap.fromImage(qimage).scaled(self.scale * self.origsize, qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)
        self.ui.PageImage.setPixmap(self.pixmap)

    def savePageBoxImagePage(self,roi,bnum):
        dest_of_greek = self.greekpagesautosplit
        dest_of_latin = self.latinpagesautosplit
        currentRow = self.ui.PageBoxTable.currentRow()
        if int(self.ui.PageBoxTable.item(currentRow,1).text()) <= 2300:
            self.pagedestfolder = dest_of_greek
            self.pagedeststr = 'greek'
        elif int(self.ui.PageBoxTable.item(currentRow,1).text()) >= 2301:
            self.pagedestfolder = dest_of_latin
            self.pagedeststr = 'latin'

        if self.pagedestfolder != "":
            PILimage = Image.fromarray(roi)
            thresh = 127
            fn = lambda x : 255 if x > thresh else 0
            PIL_BWimage = PILimage.convert('L').point(fn, mode='1')
            tif_outfile = self.pagedestfolder + self.pagedeststr + self.imgfilename.replace("_pagebox.tif","") + "_pagebox.tif"
            print("Generating: " + tif_outfile)
            PIL_BWimage.save(tif_outfile, "TIFF", dpi=(300,300))

    def savePageBoxImage(self):
        self.ui.statusbar.showMessage(f'Saving PageBox file: {self.imgpath}')
        print(f'Saving PageBox file: {self.imgpath}')
        cv2.imwrite(self.imgpath, self.norm)
        self.boximgpath = self.imgpath
        self.showImage(self.boximgpath)
        #if self.ui.LineCheckBox.isChecked():
            #self.getLineBoxImageLines()

###########    Page Box Text Methods    #############

    def BoxText2BoxTable(self):
        #self.currentBoxTable.clearContents()
        boxes = []
        reader = csv.reader(open(self.txtpath), delimiter = '\t')

        for row in reader:
            boxes.append(row)

        '''if self.statusBoxType.text() == "Page":
            if self.statusBoxMode.text() == "Make":
                boxes = boxes[0:]
            elif self.statusBoxMode.text() == "Edit":
                if self.editCurrent == True:
                    boxes = boxes[0:]
                else:
                    boxes = boxes[1:]
        if self.statusBoxType.text() == "Line":'''
        if self.statusBoxMode.text() == "Make":
            boxes = boxes[0:]
        else:
            boxes = boxes[1:]
        #boxes = boxes[1:]
        rowCount = len(boxes)
        self.currentBoxTable.setRowCount(rowCount)
        colcount = self.currentBoxTable.columnCount()
        print(f'BoxTable column count: {colcount}')
        self.currentBoxTable.setSortingEnabled(False)
        #self.currentBoxTable.clearContents()
        for row, boxes in enumerate(boxes):
            for column, value in enumerate(boxes):
                if column == 0:
                    tableitem = qtw.QTableWidgetItem()
                    tableitem.setFlags(qtc.Qt.ItemIsEditable)
                    newItem = qtw.QTableWidgetItem(value)
                    self.currentBoxTable.setItem(row, column, newItem)
                elif column >= 1 and column <= 4:
                    #print(f'Updating PageBoxTable column: {column}')
                    newItem = qtw.QTableWidgetItem(value)

                    #Scaled
                    #newVal = int(newItem.text())
                    #scaledVal = int(newVal * self.scale)
                    #newItem.setText(str(scaledVal))

                    #Not Scaled
                    newVal = int(newItem.text())
                    newItem.setText(str(newVal))
                    self.currentBoxTable.setItem(row, column, newItem)
        self.showEditButtons()
        self.currentBoxTable.resizeColumnsToContents()
        self.currentBoxTable.resizeRowsToContents()
        self.currentBoxTable.setSortingEnabled(True)

    def update_PageBoxText(self,page,x,y,w,h):
        print(f'From getRbBox method - Page: {page}  X: {x}  Y: {y}  W: {w} H: {h}')
        #self.jsonpath = self.path_of_jsonpagebox + self.imgfilename + "_pagebox.json"
        jsonfilepath = self.jsonpath
        #self.txtpath = self.path_of_txtlinebox + self.imgfilename + "_linebox.txt"
        csvfilepath = self.txtpath
        self.csv2json(csvfilepath,jsonfilepath)
        with open(jsonfilepath, 'r') as f:
            data = json.load(f)
            # Iterating through the json
            for Page in data:
                print(f'Page from json file: {Page} -- page from putRbBox: {page} ')
                if Page['Page'] == page:
                    Page['X'] = x
                    Page['Y'] = y
                    Page['W'] = w
                    Page['H'] = h
                    print(f'Updating Page: {page} found in JSON file. Dimensions :  X: {x}  Y: {y}  W: {w}  H: {h}')
                else:
                    print(f'Page: {page} not found in JSON file.')
            # Closing file
            f.close()
            os.remove(jsonfilepath)
            with open(jsonfilepath, 'w') as f:
                json.dump(data, f, indent=4)
            f.close()
        self.json2csv(csvfilepath,jsonfilepath)
        self.showText(csvfilepath)

    def PageBoxText2PageBoxTable(self):
        #self.currentBoxTable.clearContents()
        boxes = []
        reader = csv.reader(open(self.txtpath), delimiter = '\t')

        for row in reader:
            boxes.append(row)

        '''if self.statusBoxMode.text() == "Make":
            boxes = boxes[0:]
        else:
            boxes = boxes[1:]'''
        boxes = boxes[0:]
        rowCount = len(boxes)
        self.currentBoxTable.setRowCount(rowCount)
        colcount = self.currentBoxTable.columnCount()
        print(f'PageBoxTable column count: {colcount}')
        self.currentBoxTable.setSortingEnabled(False)
        #self.currentBoxTable.clearContents()
        for row, boxes in enumerate(boxes):
            for column, value in enumerate(boxes):
                if column == 0:
                    tableitem = qtw.QTableWidgetItem()
                    tableitem.setFlags(qtc.Qt.ItemIsEditable)
                    newItem = qtw.QTableWidgetItem(value)
                    self.currentBoxTable.setItem(row, column, newItem)
                elif column >= 1 and column <= 4:
                    #print(f'Updating PageBoxTable column: {column}')
                    newItem = qtw.QTableWidgetItem(value)

                    #Scaled
                    #newVal = int(newItem.text())
                    #scaledVal = int(newVal * self.scale)
                    #newItem.setText(str(scaledVal))

                    #Not Scaled
                    newVal = int(newItem.text())
                    newItem.setText(str(newVal))
                    self.currentBoxTable.setItem(row, column, newItem)
        self.showEditButtons()
        self.currentBoxTable.resizeColumnsToContents()
        self.currentBoxTable.resizeRowsToContents()
        self.currentBoxTable.setSortingEnabled(True)

    def PageBoxTable2csv(self):
        #self.txtpath = self.path_of_txtlinebox + self.imgfilename + "_linebox.txt"
        print(f'Path of pagebox.txt: {self.txtpath}')
        if os.path.exists(self.txtpath):
            print(f'Removing: {self.txtpath}')
            os.remove(self.txtpath)
            self.currentTextTable.clear()
        colCount = range(self.currentBoxTable.columnCount()- 6)
        header = [self.currentBoxTable.horizontalHeaderItem(column).text() for column in colCount]
        with open(self.txtpath, 'w') as csvfile:
            #writer = csv.writer(csvfile, dialect='excel', lineterminator='\n')
            writer = csv.writer(csvfile, dialect='excel', delimiter='\t', lineterminator='\n')
            writer.writerow(header)
            for row in range(self.currentBoxTable.rowCount()):
                writer.writerow(self.currentBoxTable.item(row, column).text() for column in colCount)
        self.getText(self.txtpath)


###########    Line Box Shared Methods    #############
    # Line Toolbar Actions

    def actionCrop_Greek_To_tiff_Lines(self):
        print("cropping and sorting Greek tiff lines")
        #usage: tr.sortcroplines(source, splitdir, linebox)
        self.crop_greeklinesDialog = qtw.QDialog()
        self.crop_greeklines_ui = Ui_crop_greek_linesDialog()
        self.crop_greeklines_ui.setupUi(self.crop_greeklinesDialog)
        self.crop_greeklinesDialog.show()
        #tr.sortcroplines(r"/home/jetson/Projects/Python/Images/Greek/png_greek_deskew/greek_book_40_Matthew/","/home/jetson/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_40_Matthew/","/home/jetson/Projects/Python/Images/Greek/tif_greek_linebox/greek_book_40_Matthew/")

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
            # if self.crop_greeklinesDialog.Accepted:
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
                print(source_folder,filename)
                #source_file_path = os.path.join(source_folder, filename)

            # Extract to default Workflow folder
            print(source_folder, workflow_dest_folder, workflow_box_folder)
            tr.sortcroplines(self.crop_greeklines_ui.SourceLineEdit.text(),self.crop_greeklines_ui.GreekBoxFolderLineEdit.text(),self.crop_greeklines_ui.DestGreekLineEdit.text())
            '''
            # Copy Workflow folder to default Complete folder
            if complete_dest_folder:
                symlinks=False
                ignore=None
                for item in os.listdir(workflow_dest_folder):
                    source = os.path.join(workflow_dest_folder, item)
                    destination = os.path.join(complete_dest_folder, item)
                    if os.path.isdir(workflow_dest_folder):
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
                    if os.path.isdir(workflow_box_folder):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy(source, destination)'''

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
                with open(self.workflow) as f:
                    # returns JSON object as
                    # a dictionary
                    data = json.load(f)

                    # Search the key value using 'in' operator
                    for Sequence in data:
                        # print(Sequence['Sequence'])
                        if Sequence['Sequence'] == step:
                            # set line edits to their default workflow folders
                            if step == "GL1":
                                self.crop_greeklines_ui.GreekBoxFolderLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                                workflow_box_folder = self.projecthome + Sequence['WorkflowFullPath']+r'/'
                                complete_box_folder = self.projecthome + Sequence['CompleteFullPath']+r'/'+self.sourcebookmarkdown+r'/'
                            elif step == "GL2":
                                self.crop_greeklines_ui.SourceLineEdit.setText(Sequence['DefaultSource']+r'/')
                                source_folder = self.projecthome + Sequence['DefaultSource']+r'/'
                                self.crop_greeklines_ui.DestGreekLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                                workflow_dest_folder = self.projecthome + Sequence['WorkflowFullPath']+r'/'
                                complete_dest_folder = self.projecthome + Sequence['CompleteFullPath']+r'/'+self.sourcebookmarkdown+r'/'
                f.close()

        rsp = self.crop_greeklinesDialog.exec_()
        print("completed creating cropped language tif files")
        #tr.sortcroplines(r"/home/jetson/Projects/Python/Images/Greek/png_greek_deskew/greek_book_41_Mark/","/home/jetson/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_41_Mark/","/home/jetson/Projects/Python/Images/Greek/tif_greek_linebox/greek_book_41_Mark/")

    def actionRename_Greek_tiff_Lines(self):
        print("renaming Greek tif lines for ground truth")
        # usage: tr.renameimages(source, destination)
        self.tifgreekrenamelinesDialog = qtw.QDialog()
        self.greekrenamelines_ui = Ui_tifgreekrenamelinesDialog()
        self.greekrenamelines_ui.setupUi(self.tifgreekrenamelinesDialog)
        self.tifgreekrenamelinesDialog.show()

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
            tr.renameimages(self.greekrenamelines_ui.SourceLineEdit.text(), self.greekrenamelines_ui.DestinationLineEdit.text())

            # Extract to default Complete folder
            #if complete_folder:
                #pp.pdf4tif(source_file_path, complete_folder)
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
            print("completed renaming Greek tif lines for ground truth")
        def reject():
            pass

        seq = "GL3"

        def setdefault():
            if self.greekrenamelines_ui.defaultsrcBox.isChecked():
                self.greekrenamelines_ui.SourceButton.setEnabled(False)
                self.greekrenamelines_ui.DestinationButton.setEnabled(False)
            else:
                self.greekrenamelines_ui.SourceButton.setEnabled(True)
                self.greekrenamelines_ui.DestinationButton.setEnabled(True)

        self.greekrenamelines_ui.defaultsrcBox.stateChanged.connect(setdefault)
        self.greekrenamelines_ui.SourceButton.clicked.connect(self.GreekRenameLinesDialog)
        self.greekrenamelines_ui.DestinationButton.clicked.connect(self.DestGreekRenameLinesDialog)
        self.greekrenamelines_ui.buttonBox.accepted.connect(accept)
        self.greekrenamelines_ui.buttonBox.rejected.connect(reject)

        if self.greekrenamelines_ui.defaultsrcBox.isChecked():
            # disable source button (default)

            # get default folder
            # Define json data
            with open(self.workflow) as f:
                # returns JSON object as
                # a dictionary
                data = json.load(f)
                # Search the key value using 'in' operator
                for Sequence in data:
                    print(Sequence['Sequence'])
                    if Sequence['Sequence'] == seq:
                        # set source line edit to default workflow folder
                        source_folder = self.projecthome + Sequence['DefaultSource']+r'/'
                        workflow_folder = self.projecthome + Sequence['WorkflowFullPath']+r'/'
                        complete_folder = self.projecthome + Sequence['CompleteFullPath']+r'/'
                        self.greekrenamelines_ui.SourceLineEdit.setText(source_folder)
                        self.greekrenamelines_ui.DestinationLineEdit.setText(workflow_folder)
                        print(source_folder,workflow_folder,complete_folder)


        rsp = self.tifgreekrenamelinesDialog.exec_()



        print("completed renaming Greek tif lines for ground truth")
        # tr.renameimages(r"/home/jetson/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_40_Matthew/", "/home/jetson/Projects/Python/Images/Greek/tif_greek_tif4groundtruth/")
        # tr.renameimages(r"/home/jetson/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_41_Mark/", "/home/jetson/Projects/Python/Images/Greek/tif_greek_tif4groundtruth/")

    def actionStage_Greek_tiff_Lines(self):
        print("staging Greek tif lines for ground truth")
        # usage: tr.stageimages(source, destination, startpage, endpage)
        self.tifgreekstagelinesDialog = qtw.QDialog()
        self.greekstagelines_ui = Ui_tifgreekstagelinesDialog()
        self.greekstagelines_ui.setupUi(self.tifgreekstagelinesDialog)
        self.tifgreekstagelinesDialog.show()

        def accept():
            # if self.pdf4tifDialog.Accepted:
            # Empty default Workflow folder
            start_page = self.greekstagelines_ui.StartPageLineEdit.displayText()
            end_page = self.greekstagelines_ui.EndPageLineEdit.displayText()
            print(f'source_folder: {source_folder},workflow_folder: {workflow_folder},complete_folder: {complete_folder}, start_page: {start_page}, end_page: {end_page}')
            #print('Workflow Folder:'+ workflow_folder,'Complete Folder:'+ complete_folder)
            '''for filename in os.listdir(workflow_folder):
                file_path = os.path.join(workflow_folder, filename)
                print('File Name:'+filename, 'File Path:'+file_path)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %Model/Project/Data/json/PageVerseCrossReference.json. Reason: %Model/Project/Data/json/PageVerseCrossReference.json' % (file_path, e))'''

            for filename in os.listdir(source_folder):
                print(source_folder,filename)
                source_file_path = os.path.join(source_folder, filename)

            # Extract to default Workflow folder
            print(source_file_path, workflow_folder, start_page, end_page)
            #tr.stageimages(self.greekstagelines_ui.SourceLineEdit.text(), self.greekstagelines_ui.DestinationLineEdit.text(), self.greekstagelines_ui.StartPageLineEdit.displayText(), self.greekstagelines_ui.EndPageLineEdit.displayText())
            tr.stageimages(source_folder, workflow_folder, start_page, end_page)
            # Extract to default Complete folder
            #if complete_folder:
                #pp.pdf4tif(source_file_path, complete_folder)
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
            print("completed staging Greek tif lines for ground truth")
        def reject():
            pass

        seq = "GT4"

        def setdefault():
            if self.greekstagelines_ui.defaultsrcBox.isChecked():
                self.greekstagelines_ui.SourceButton.setEnabled(False)
                self.greekstagelines_ui.DestinationButton.setEnabled(False)
            else:
                self.greekstagelines_ui.SourceButton.setEnabled(True)
                self.greekstagelines_ui.DestinationButton.setEnabled(True)

        self.greekstagelines_ui.defaultsrcBox.stateChanged.connect(setdefault)
        self.greekstagelines_ui.SourceButton.clicked.connect(self.GreekStageLinesDialog)
        self.greekstagelines_ui.DestinationButton.clicked.connect(self.DestGreekStageLinesDialog)
        self.greekstagelines_ui.buttonBox.accepted.connect(accept)
        self.greekstagelines_ui.buttonBox.rejected.connect(reject)

        if self.greekstagelines_ui.defaultsrcBox.isChecked():


            # disable source button (default)

            # get default folder
            # Define json data
            with open(self.workflow) as f:
                # returns JSON object as
                # a dictionary
                data = json.load(f)
                # Search the key value using 'in' operator
                for Sequence in data:

                    if Sequence['Sequence'] == seq:
                        print(Sequence['Sequence'])
                        # set source line edit to default workflow folder
                        source_folder = self.projecthome + Sequence['DefaultSource']+r'/'
                        workflow_folder = self.projecthome + Sequence['WorkflowFullPath']+r'/'
                        complete_folder = self.projecthome + Sequence['CompleteFullPath']+r'/'
                        self.greekstagelines_ui.SourceLineEdit.setText(source_folder)
                        self.greekstagelines_ui.DestinationLineEdit.setText(workflow_folder)
                        self.greekstagelines_ui.StartPageLineEdit.setText("1")
                        #print(f'source_folder: {source_folder},workflow_folder: {workflow_folder},complete_folder: {complete_folder}')


        rsp = self.tifgreekstagelinesDialog.exec_()


        print("completed staging Greek tif lines for ground truth")
        # tr.stageimages(r"c:/users/max/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_40_Matthew/", "c:/users/max/Projects/Python/Images/Greek/tif_greek_tif4groundtruth/")
        # tr.stageimages(r"c:/users/max/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_41_Mark/", "c:/users/max/Projects/Python/Images/Greek/tif_greek_tif4groundtruth/")

    '''def actionStage_Greek_tiff_Lines(self):
        print("staging Greek tif lines for ground truth")
        # usage: tr.renameimages(source, destination)
        self.greekstagelinesDialog = qtw.QDialog()
        self.greekstagelines_ui = Ui_tifgreekstagelinesDialog()
        self.greekstagelines_ui.setupUi(self.greekstagelinesDialog)
        self.greekstagelinesDialog.show()

        self.greekstagelines_ui.SourceButton.clicked.connect(self.GreekStagelinesDialog)
        self.greekstagelines_ui.DestinationButton.clicked.connect(self.DestGreekStagelinesDialog)

        rsp = self.greekstagelinesDialog.exec_()

        if self.greekstagelinesDialog.Accepted:
            tr.stageimages(self.greekstagelines_ui.SourceLineEdit.text(), self.greekstagelines_ui.DestinationLineEdit.text())
            print("completed staging Greek tif lines for ground truth")

        # tr.renameimages(r"/home/jetson/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_40_Matthew/", "/home/jetson/Projects/Python/Images/Greek/tif_greek_tif4groundtruth/")
        #tr.renameimages("/home/jetson/Projects/Python/Images/Greek/tif_greek_tif4groundtruth/", "/home/jetson/Projects/Python/Images/Greek/tif_greek_tif2groundtruth/")
        #pass'''

    def actionCrop_Latin_To_tiff_Lines(self):
        print("cropping and sorting Latin tiff lines")
        #usage: tr.sortcroplines(source, splitdir, linebox)
        self.crop_latinlinesDialog = qtw.QDialog()
        self.crop_latinlines_ui = Ui_crop_latin_linesDialog()
        self.crop_latinlines_ui.setupUi(self.crop_latinlinesDialog)
        self.crop_latinlinesDialog.show()

        self.crop_latinlines_ui.SourceButton.clicked.connect(self.CroplatinLinesDialog)
        self.crop_latinlines_ui.BoxFolderButton.clicked.connect(self.LineBoxFolderDialog)
        self.crop_latinlines_ui.DestlatinButton.clicked.connect(self.DestlatinLinesDialog)

        rsp = self.crop_latinlinesDialog.exec_()

        if self.crop_latinlinesDialog.Accepted:
            tr.sortcroplines(self.crop_latinlines_ui.SourceLineEdit.text(),self.crop_latinlines_ui.BoxFolderLineEdit.text(),self.crop_latinlines_ui.DestlatinLineEdit.text())
            print("completed creating cropped Latin tif lines")
        #tr.sortcroplines(r"/home/jetson/Projects/Python/Images/Latin/png_latin_deskew/latin_book_40_Matthew/","/home/jetson/Projects/Python/Images/Latin/tif_latin_autosplit/latin_book_40_Matthew/","/home/jetson/Projects/Python/Images/Latin/tif_latin_linebox/latin_book_40_Matthew/")
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

        # tr.renameimages(r"/home/jetson/Projects/Python/Images/Latin/tif_latin_autosplit/latin_book_40_Matthew/", "/home/jetson/Projects/Python/Images/Latin/tif_latin_tif4groundtruth/")
        #tr.renameimages(r"/home/jetson/Projects/Python/Images/Latin/tif_latin_autosplit/latin_book_41_Mark/", "/home/jetson/Projects/Python/Images/Latin/tif_latin_tif4groundtruth/")

    def actionStage_Latin_tiff_Lines(self):
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
        print("splitting Greek textlines for ground truth review")
        #usage: tr.sortcroplines(source, splitdir, linebox)
        self.split_greek_text_linesDialog = qtw.QDialog()
        self.split_greeklines_ui = Ui_splitgreektextlinesDialog()
        self.split_greeklines_ui.setupUi(self.split_greek_text_linesDialog)
        self.split_greek_text_linesDialog.show()
        #tr.sortcroplines(r"/home/jetson/Projects/Python/Images/Greek/png_greek_deskew/greek_book_40_Matthew/","/home/jetson/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_40_Matthew/","/home/jetson/Projects/Python/Images/Greek/tif_greek_linebox/greek_book_40_Matthew/")

        def setdefault():
            if self.split_greeklines_ui.defaultsrcBox.isChecked():
                self.split_greeklines_ui.SourceButton.setEnabled(False)
                self.split_greeklines_ui.DestinationButton.setEnabled(False)

            else:
                self.split_greeklines_ui.SourceButton.setEnabled(True)
                self.split_greeklines_ui.DestinationButton.setEnabled(True)

        def accept():
            # if self.crop_greeklinesDialog.Accepted:
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
                print(source_folder,filename)
                #source_file_path = os.path.join(source_folder, filename)

            # Extract to default Workflow folder
            print(source_folder, workflow_dest_folder)
            #self.splittextlines(self.split_greeklines_ui.SourceLineEdit.text(),self.split_greeklines_ui.DestinationLineEdit.text())
            #self.splittextlines(source_folder,source_folder)
            tr.splittextlines(self.split_greeklines_ui.SourceLineEdit.text(),self.split_greeklines_ui.DestinationLineEdit.text())
            '''
            # Copy Workflow folder to default Complete folder
            if complete_dest_folder:
                symlinks=False
                ignore=None
                for item in os.listdir(workflow_dest_folder):
                    source = os.path.join(workflow_dest_folder, item)
                    destination = os.path.join(complete_dest_folder, item)
                    if os.path.isdir(workflow_dest_folder):
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
                    if os.path.isdir(workflow_box_folder):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy(source, destination)'''

        def reject():
            pass

        self.split_greeklines_ui.defaultsrcBox.stateChanged.connect(setdefault)
        self.split_greeklines_ui.SourceButton.clicked.connect(self.SplitGreekTextLinesDialog)
        self.split_greeklines_ui.DestinationButton.clicked.connect(self.DestGreekTextLinesDialog)
        self.split_greeklines_ui.buttonBox.accepted.connect(accept)
        self.split_greeklines_ui.buttonBox.rejected.connect(reject)

        seq = ["GL6","AddStep"]

        if self.split_greeklines_ui.defaultsrcBox.isChecked():
        # disable source button (default)

            for step in seq:

                # Define json data
                with open(self.workflow) as f:
                    # returns JSON object as
                    # a dictionary
                    data = json.load(f)

                    # Search the key value using 'in' operator
                    for Sequence in data:
                        # print(Sequence['Sequence'])
                        if Sequence['Sequence'] == step:
                            # set line edits to their default workflow folders
                            if step == "GL6":
                                self.split_greeklines_ui.SourceLineEdit.setText(Sequence['DefaultSource']+r'/'+self.greekbookmarkdown+r'/')
                                source_folder = self.projecthome + Sequence['DefaultSource']+r'/'+self.greekbookmarkdown+r'/'
                                self.split_greeklines_ui.DestinationLineEdit.setText(Sequence['WorkflowFullPath']+r'/'+self.greekbookmarkdown+r'/')
                                workflow_dest_folder = self.projecthome + Sequence['WorkflowFullPath']+r'/'+self.greekbookmarkdown+r'/'
                                complete_dest_folder = self.projecthome + Sequence['CompleteFullPath']+r'/'+self.greekbookmarkdown+r'/'
                f.close()

        rsp = self.split_greek_text_linesDialog.exec_()
        print("completed splitting Greek textlines for ground truth review")
        #tr.sortcroplines(r"/home/jetson/Projects/Python/Images/Greek/png_greek_deskew/greek_book_41_Mark/","/home/jetson/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_41_Mark/","/home/jetson/Projects/Python/Images/Greek/tif_greek_linebox/greek_book_41_Mark/")

    def actionRenameGreek_text_lines(self):
        print("renaming Greek textlines for ground truth review")
        #usage: tr.sortcroplines(source, splitdir, linebox)
        self.rename_greek_text_linesDialog = qtw.QDialog()
        self.rename_greeklines_ui = Ui_renamegreektextlinesDialog()
        self.rename_greeklines_ui.setupUi(self.rename_greek_text_linesDialog)
        self.rename_greek_text_linesDialog.show()
        #tr.sortcroplines(r"/home/jetson/Projects/Python/Images/Greek/png_greek_deskew/greek_book_40_Matthew/","/home/jetson/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_40_Matthew/","/home/jetson/Projects/Python/Images/Greek/tif_greek_linebox/greek_book_40_Matthew/")

        def setdefault():
            if self.rename_greeklines_ui.defaultsrcBox.isChecked():
                self.rename_greeklines_ui.SourceButton.setEnabled(False)
                self.rename_greeklines_ui.DestinationButton.setEnabled(False)

            else:
                self.rename_greeklines_ui.SourceButton.setEnabled(True)
                self.rename_greeklines_ui.DestinationButton.setEnabled(True)

        def accept():
            # if self.crop_greeklinesDialog.Accepted:
            # Empty default Workflow folder
            print('Workflow Folder:'+ workflow_dest_folder,'Complete Folder:'+ complete_dest_folder)
            for filename in os.listdir(workflow_dest_folder):
                file_path = os.path.join(workflow_dest_folder, filename)
                #print('File Name:'+filename, 'File Path:'+file_path)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))

            for filename in os.listdir(source_folder):
                print(source_folder,filename)
                #source_file_path = os.path.join(source_folder, filename)

            # Extract to default Workflow folder
            print(source_folder, workflow_dest_folder)
            #self.splittextlines(self.split_greeklines_ui.SourceLineEdit.text(),self.split_greeklines_ui.DestinationLineEdit.text())
            #self.splittextlines(source_folder,source_folder)
            tr.text2groundtruth(self.rename_greeklines_ui.SourceLineEdit.text(),self.rename_greeklines_ui.DestinationLineEdit.text())
            '''
            # Copy Workflow folder to default Complete folder
            if complete_dest_folder:
                symlinks=False
                ignore=None
                for item in os.listdir(workflow_dest_folder):
                    source = os.path.join(workflow_dest_folder, item)
                    destination = os.path.join(complete_dest_folder, item)
                    if os.path.isdir(workflow_dest_folder):
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
                    if os.path.isdir(workflow_box_folder):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy(source, destination)'''

        def reject():
            pass

        self.rename_greeklines_ui.defaultsrcBox.stateChanged.connect(setdefault)
        self.rename_greeklines_ui.SourceButton.clicked.connect(self.RenameGreekTextLinesDialog)
        self.rename_greeklines_ui.DestinationButton.clicked.connect(self.DestRenameGreekTextLinesDialog)
        self.rename_greeklines_ui.buttonBox.accepted.connect(accept)
        self.rename_greeklines_ui.buttonBox.rejected.connect(reject)

        seq = ["GL7","AddStep"]

        if self.rename_greeklines_ui.defaultsrcBox.isChecked():
        # disable source button (default)

            for step in seq:

                # Define json data
                with open(self.workflow) as f:
                    # returns JSON object as
                    # a dictionary
                    data = json.load(f)

                    # Search the key value using 'in' operator
                    for Sequence in data:
                        # print(Sequence['Sequence'])
                        if Sequence['Sequence'] == step:
                            # set line edits to their default workflow folders
                            if step == "GL7":
                                self.rename_greeklines_ui.SourceLineEdit.setText(Sequence['DefaultSource']+r'/'+self.greekbookmarkdown+r'/')
                                source_folder = self.projecthome + Sequence['DefaultSource']+r'/'+self.greekbookmarkdown+r'/'
                                self.rename_greeklines_ui.DestinationLineEdit.setText(Sequence['WorkflowFullPath']+r'/'+self.greekbookmarkdown+r'/')
                                workflow_dest_folder = self.projecthome + Sequence['WorkflowFullPath']+r'/'+self.greekbookmarkdown+r'/'
                                complete_dest_folder = self.projecthome + Sequence['CompleteFullPath']+r'/'+self.greekbookmarkdown+r'/'
                f.close()

        rsp = self.rename_greek_text_linesDialog.exec_()
        print("completed renaming Greek textlines for ground truth review")
        #tr.sortcroplines(r"/home/jetson/Projects/Python/Images/Greek/png_greek_deskew/greek_book_41_Mark/","/home/jetson/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_41_Mark/","/home/jetson/Projects/Python/Images/Greek/tif_greek_linebox/greek_book_41_Mark/")

    def toggleGreekToolbars(self):

        greekimgpagesstate = self.ui.GreekImagePagesToolBar.isVisible()
        greekimglinesstate = self.ui.GreekImageLinesBatchToolBar.isVisible()
        greektxtlinesstate = self.ui.GreekTextLinesBatchToolBar.isVisible()

        # Set the visibility to its inverse
        self.ui.GreekImagePagesToolBar.setVisible(not greekimgpagesstate)
        self.ui.GreekImageLinesBatchToolBar.setVisible(not greekimglinesstate)
        self.ui.GreekTextLinesBatchToolBar.setVisible(not greektxtlinesstate)

    '''def toggleLatinToolbars(self):

        #latinimgpagesstate = self.ui.LatinImagePagesToolBar.isVisible()
        latinimglinesstate = self.ui.LatinImageLinesBatchToolBar.isVisible()
        latintxtlinesstate = self.ui.LatinTextLinesBatchToolBar.isVisible()

        # Set the visibility to its inverse
        #self.ui.LatinImagePagesToolBar.setVisible(not latinimgpagesstate)
        self.ui.LatinImageLinesBatchToolBar.setVisible(not latinimglinesstate)
        self.ui.LatinTextLinesBatchToolBar.setVisible(not latintxtlinesstate)'''

    def sortcroplines(source, linebox, splitdir):
            dest_of_autosplit = splitdir
            dest_of_linebox = linebox
            path_of_images = source

            list_of_images = os.listdir(path_of_images)

            def saveline(roi,bnum):
                    PILimage = Image.fromarray(roi)
                    thresh = 127
                    fn = lambda x : 255 if x > thresh else 0
                    PIL_BWimage = PILimage.convert('L').point(fn, mode='1')
                    tif_outfile = dest_of_autosplit + filename + "_Line" + str(bnum) + ".tif"
                    print("Generating: " + tif_outfile)
                    PIL_BWimage.save(tif_outfile, "TIFF", dpi=(300,300))

            def removeworkflow(source):
                    shutil.remove(source)

            for image in list_of_images:

                    img = cv2.imread(os.path.join(path_of_images, image))

                    filestr = os.path.basename(os.path.join(path_of_images, image))

                    filesplit = os.path.splitext(filestr)

                    filename = filesplit[0]

                    fileext = filesplit[1]

                    #grayscale
                    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
                    #cv2.imwrite(dest_of_test_images + filename + "_gray" + fileext,gray)
                    #cv2.imshow('gray',gray)
                    #cv2.waitKey(0)

                    #binary
                    ret,binary = cv2.threshold(gray,127,255,cv2.THRESH_BINARY)

                    #binary inversion
                    ret,thresh = cv2.threshold(gray,127,255,cv2.THRESH_BINARY_INV)
                    #cv2.imwrite(dest_of_test_images + filename + "_thresh" + fileext,thresh)
                    #cv2.imshow('second',thresh)
                    #cv2.waitKey(0)

                    #dilation
                    kernel = np.ones((5,195), np.uint8)
                    img_dilation = cv2.dilate(thresh, kernel, iterations=1)
                    #cv2.imwrite(dest_of_test_images + filename + "_dilation" + fileext,img_dilation)
                    #cv2.imshow('dilated',img_dilation)
                    #cv2.waitKey(0)

                    #medianblur
                    median = cv2.medianBlur(img_dilation, 13)
                    #cv2.imwrite(dest_of_test_images + filename + "_blur" + fileext,median)
                    #cv2.imshow('medianblur',median)
                    #cv2.waitKey(0)

                    #find contours
                    im2,ctrs, hier = cv2.findContours(median, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

                    #set flags for sorting contours top to bottom
                    reverse = False
                    i = 1

                    # construct the list of bounding boxes and sort them from top to bottom
                    boundingBoxes = [cv2.boundingRect(c) for c in ctrs]
                    (ctrs, boundingBoxes) = zip(*sorted(zip(ctrs, boundingBoxes),key=lambda b:b[1][i], reverse=reverse))

                    # Set initial box count
                    bnum = 1

                    for i,c in enumerate(ctrs):

                            # Get bounding box
                            x, y, w, h = cv2.boundingRect(c)
                            dividers = int(round(h/150))
                            print("countour height = " + str(h) + "\t" + "number of boxes = " + str(dividers))
                            # Set height validation of contour to eliminate unwanted boxes
                            if h>120 and h<200:
                                    roi = binary[y:y+h, x:x+w]
                                    cv2.rectangle(binary,(x,y),( x + w, y + h ),(0,0,255),2)
                                    bnum += 1
                                    saveline(roi,bnum)

                            # Set height of multi-line contours and subdivide proportionally
                            elif h > 200:
                                    h = int(round(h/dividers))
                                    for subdiv in range(0,dividers):
                                            print('subloopcount =' + str(subdiv))
                                            roi = binary[y:y+h, x:x+w]
                                            cv2.rectangle(binary,(x,y),( x + w, y + h ),(0,0,255),2)
                                            bnum += 1
                                            y = y + h
                                            saveline(roi,bnum)


                    # Write linebox image to file
                    cv2.imwrite(dest_of_linebox + filename + "_linebox" + fileext,binary)

                    #cv2.imshow("box image",image)
                    #cv2.waitKey(0)
                    #print("Writing "+filename+" Linebox Image")


    # Line Box Dialogs
    def CropGreekLinesDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.BoxWidget, "Select tif pages source folder"))

        if self.directory:
            self.crop_greeklines_ui.SourceLineEdit.setText(self.directory+r'/')

    def GreekLineBoxFolderDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.BoxWidget, "Select linebox destination folder"))

        if self.directory:
            self.crop_greeklines_ui.GreekBoxFolderLineEdit.setText(self.directory+r'/')

    def DestGreekLinesDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.BoxWidget, "Select Greek lines destination folder"))

        if self.directory:
            self.crop_greeklines_ui.DestGreekLineEdit.setText(self.directory+r'/')

    def CropLatinLinesDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.BoxWidget, "Select tif pages source folder"))

        if self.directory:
            self.crop_greeklines_ui.SourceLineEdit.setText(self.directory+r'/')

    def LatinLineBoxFolderDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.BoxWidget, "Select linebox destination folder"))

        if self.directory:
            self.crop_greeklines_ui.LatinBoxFolderLineEdit.setText(self.directory+r'/')

    def DestLatinLinesDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.BoxWidget, "Select Greek lines destination folder"))

        if self.directory:
            self.crop_greeklines_ui.DestGreekLineEdit.setText(self.directory+r'/')

    def GreekStageLinesDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select rename tif Greek lines source folder"))

        if self.directory:
            self.greekstagelines_ui.SourceLineEdit.setText(self.directory+r'/')

    def DestGreekStageLinesDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select rename Greek lines destination folder"))

        if self.directory:
            self.greekstagelines_ui.DestinationLineEdit.setText(self.directory+r'/')

    def GreekMoveLinesDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.BoxWidget, "Select rename tif Greek lines source folder"))

        if self.directory:
            self.greekrenamelines_ui.SourceLineEdit.setText(self.directory+r'/')

    def DestGreekMoveLinesDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.BoxWidget, "Select rename Greek lines destination folder"))

        if self.directory:
            self.greekrenamelines_ui.DestinationLineEdit.setText(self.directory+r'/')

    def GreekRenameLinesDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.BoxWidget, "Select rename tif Greek lines source folder"))

        if self.directory:
            self.greekrenamelines_ui.SourceLineEdit.setText(self.directory+r'/')

    def DestGreekRenameLinesDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.BoxWidget, "Select rename Greek lines destination folder"))

        if self.directory:
            self.greekrenamelines_ui.DestinationLineEdit.setText(self.directory+r'/')

    def SplitGreekTextLinesDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.BoxWidget, "Select Greek text pages source folder"))

        if self.directory:
            self.split_greeklines_ui.SourceLineEdit.setText(self.directory+r'/')

    def DestGreekTextLinesDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.BoxWidget, "Select Greek text lines destination folder"))

        if self.directory:
            self.split_greeklines_ui.DestinationLineEdit.setText(self.directory+r'/')

    def RenameGreekTextLinesDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.BoxWidget, "Select Greek text pages source folder"))

        if self.directory:
            self.rename_greeklines_ui.SourceLineEdit.setText(self.directory+r'/')

    def DestRenameGreekTextLinesDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.BoxWidget, "Select Greek text lines destination folder"))

        if self.directory:
            self.rename_greeklines_ui.DestinationLineEdit.setText(self.directory+r'/')
    # End of Dialog folders exist validations

    # Make LineBox Method
    def linebox_make_split(self):
            self.currentBoxTable.verticalHeader().hide()
            self.statusBoxMode.setText('Make')
            self.statusBoxType.setText('Line')
            self.statusDrawingMode.setText('Auto')

            #If no page image present, then load one.
            if self.ui.PageImage.pixmap():
                # Activate the Page Image Tab
                if self.ui.ImageTab.currentIndex() != 1:
                    self.ui.ImageTab.setCurrentIndex(1)
                # Get imglinebox source file
                #if self.ui.ImageLe.displayText() == "":
                print('Open Make Image message dailog')
                popup = qtw.QMessageBox(self)
                popup.setIcon(qtw.QMessageBox.Information)
                popup.setWindowTitle("Make LineBox File Pair")
                popup.setText("Make LineBox from Current Page or load a New Page")
                currentButton = popup.addButton('Use Current Page', qtw.QMessageBox.YesRole)
                newButton = popup.addButton('Load New Page', qtw.QMessageBox.YesRole)
                popup.exec()
                if popup.clickedButton() == currentButton:
                    self.getImage(self.imgpath)
                elif popup.clickedButton() == newButton:
                    self.ui.ImageLe.clear()
                    self.currentBoxImage.clear()
                    self.ui.PageImage.clear()
                    self.ui.TextLE.clear()
                    #self.currentTextTable.clear()
                    #self.currentBoxTable.clear()
                    self.loadImage()
            else:
                # Activate the Page Image Tab
                if self.ui.ImageTab.currentIndex() != 1:
                    self.ui.ImageTab.setCurrentIndex(1)
                # Get imglinebox source file
                self.loadImage()
            print(f'from Load Page Image: self.imgpath = {self.imgpath}')
            # Activate the Line Box Tab
            if self.ui.ImageTab.currentIndex() != 0:
                self.ui.ImageTab.setCurrentIndex(0)
            else:
                self.on_tabChanged()
            print(f'after tab changed to Line Box: self.imgpath = {self.imgpath}')
            # setting value to progress bar
            self.ui.progressBar.setValue(10)
            self.setBoxPaths()
            print(f'from setBoxPaths: imgfilename = {self.imgfilename}')
            # Make LineBox File Pair
            self.ui.ImageLe.clear()
            self.ui.ImageLe.setText(os.path.basename(self.imgpath))
            # validate image as a LineBox Image
            '''pathsplit = self.imgpath.split('_')
            tailsplit = pathsplit[1]
            if tailsplit == "linebox.tif":
                is_linebox = True
                print("This is not a valid Page Image! Please try again") # need to throw error
            else:
                is_linebox = False'''
            self.normImage()
            # Set normalized Page Image Path to point to Box Image Path before moving forward
            self.imgpath = self.boximgpath
            # convert image to binary numpy array for finding contours
            ret,binary = cv2.threshold(self.gray,127,255,cv2.THRESH_BINARY)
            # binary numpy array inversion
            ret,thresh = cv2.threshold(self.gray,127,255,cv2.THRESH_BINARY_INV)
            # binary numpy array dilation
            kernel = np.ones((5,195), np.uint8)
            img_dilation = cv2.dilate(thresh, kernel, iterations=1)
            # binary numpy array medianblur
            median = cv2.medianBlur(img_dilation, 13)
            # find binary numpy array line contours
            ctrs, hier = cv2.findContours(median, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            # set flags for sorting contours top to bottom
            reverse = False
            i = 1
            # construct the list of bounding boxes and sort them from top to bottom
            boundingBoxes = [cv2.boundingRect(c) for c in ctrs]
            (ctrs, boundingBoxes) = zip(*sorted(zip(ctrs, boundingBoxes),key=lambda b:b[1][i], reverse=reverse))
            # Set initial box count
            bnum = 1
            self.currentTextTable.clear()
            if os.path.exists(self.txtpath):
                print(f'Removing: {self.txtpath}')
                os.remove(self.txtpath)
            with open(self.txtpath, "a") as txtboxfile:
                for i,c in enumerate(ctrs):
                        # Get bounding box
                        x, y, w, h = cv2.boundingRect(c)
                        dividers = int(round(h/150))
                        print("countour height = " + str(h) + "\t" + "number of boxes = " + str(dividers))
                        # Set height validation of contour to eliminate unwanted boxes
                        if h>120 and h<200:
                                roi = binary[y:y+h, x:x+w]
                                cv2.rectangle(self.norm,(x,y),( x + w, y + h ),(0,0,255),2)
                                # Append to LineBoxText
                                #boxlinestr = str(bnum) + ',' + str(x) + ',' + str(y) + ',' + str(w) + ',' + str(h) + ',' + str(x+w) + ',' + str(y+h) + '\n'
                                boxlinestr = str(bnum) + '\t' + str(x) + '\t' + str(y) + '\t' + str(w) + '\t' + str(h) + '\n'
                                txtboxfile.write(boxlinestr)
                                self.saveLineBoxImageLine(roi,bnum)
                                bnum += 1
                        # Set height of multi-line contours and subdivide proportionally
                        elif h > 200:
                                h = int(round(h/dividers))
                                for subdiv in range(0,dividers):
                                    print('subloopcount =' + str(subdiv))
                                    roi = binary[y:y+h, x:x+w]
                                    cv2.rectangle(self.norm,(x,y),( x + w, y + h ),(0,0,255),2)
                                    # Append to LineBoxText
                                    boxlinestr = str(bnum) + '\t' + str(x) + '\t' + str(y) + '\t' + str(w) + '\t' + str(h) + '\t' + '\n'
                                    txtboxfile.write(boxlinestr)
                                    y = y + h
                                    #if dosplit:
                                    self.saveLineBoxImageLine(roi,bnum)
                                    bnum += 1
                        # setting value to progress bar
                        self.ui.progressBar.setValue(bnum)
            #self.txtpath = self.path_of_txtlinebox + self.imgfilename + "_linebox.txt"
            print(f'Created LineBox Text File: {self.txtpath}')
            txtboxfile.close()
            self.ui.progressBar.setValue(50)

            # Write Text Box File to LineBoxTable TableWidget
            self.BoxText2BoxTable()
            self.ui.progressBar.setValue(75)

            # Overwrite Text Box File from LineBoxTable TableWidget
            # Already wrote the txtboxfile, above; so,likely unecessary
            self.LineBoxTable2csv()
            self.ui.progressBar.setValue(85)

            # Write linebox image to file
            self.saveLineBoxImage()
            self.ui.ImageLe.clear()
            self.ui.ImageLe.setText(os.path.basename(self.boximgpath))
            self.ui.progressBar.setValue(101)
            self.ui.progressBar.reset()

    # Edit LineBox Method
    def linebox_edit_split(self):
        self.ui.statusbar.showMessage('Loading the LineBox file pair for editing')
        start = time.perf_counter()

        # Activate the Line Box Tab
        if self.ui.ImageTab.currentIndex() != 0:
            self.ui.ImageTab.setCurrentIndex(0)
        else:
            self.on_tabChanged()
        self.setBoxPaths()
        self.imgpath = self.boximgpath

        self.currentBoxTable.verticalHeader().hide()
        self.statusBoxMode.setText("Edit")
        self.statusBoxType.setText("Line")
        self.statusSelectionMode.setText("Rows")
        self.currentBoxTable.setSelectionBehavior(qtw.QAbstractItemView.SelectRows)

        def loadBoxImage():
            self.ui.ImageLe.clear()
            self.currentBoxImage.clear()
            self.loadImage()
            self.setBoxPaths()
            self.imgpath = self.boximgpath
            self.showImage(self.imgpath)

        if self.currentBoxImage.pixmap():
        #if self.ui.ImageLe.displayText() != "":
            popup = qtw.QMessageBox(self)
            popup.setIcon(qtw.QMessageBox.Information)
            popup.setWindowTitle("Edit Mode")
            popup.setText("'Edit Current' linebox pair or load and 'Edit Other'")
            currentButton = popup.addButton('Edit Current', qtw.QMessageBox.YesRole)
            otherButton = popup.addButton('Edit Other', qtw.QMessageBox.YesRole)
            popup.exec()
            if popup.clickedButton() == currentButton:
                self.getImage(self.imgpath)

            elif popup.clickedButton() == otherButton:
                loadBoxImage()
        else:
            loadBoxImage()
        self.normImage()
        self.ui.ImageLe.setText(os.path.basename(self.boximgpath))
        print(f"From setBoxPaths: self.txtpath = {self.txtpath}")
        # setting value to progress bar
        self.ui.progressBar.setValue(10)

        # validate image as a LineBox Image
        '''pathsplit = self.imgpath.split('_')
        tailsplit = pathsplit[1]
        if tailsplit == "linebox.tif":
            is_linebox = True
        else:
            is_linebox = False
            print("This is not a valid LineBox Image! Please try again")  # need to throw error'''
        self.ui.TextLE.clear()
        self.ui.TextLE.setText(self.txtfilestr)
        imgfilename = self.ui.ImageLe.displayText().split(r".")[0]
        txtfilename = self.ui.TextLE.displayText().split(r".")[0]
        # Get matching LineBoxText file
        print(f'Text File Name: {txtfilename}  Image File Name: {imgfilename}')
        if txtfilename == imgfilename:
            self.getText(self.txtpath)
            self.ui.progressBar.setValue(25)
            #if drawbox:
                # self.drawLineBoxImage()
            self.ui.progressBar.setValue(50)
            #self.saveLineBoxImage()
            self.ui.progressBar.setValue(75)
            self.BoxText2BoxTable()
            self.ui.progressBar.setValue(100)
            print("Waiting on LineBoxTable selection")
            self.row_current = self.currentBoxTable.currentRow()
            self.startEditLoop = True
            self.currentBoxTable.selectionModel().currentRowChanged.connect(self.on_currentRowChanged)
        else:
            print(f'The linebox text: {txtfilename} does not match the linebox image: {imgfilename} -- Please try again!')

        self.ui.progressBar.setValue(101)
        self.ui.progressBar.reset()
        finish = time.perf_counter()
        self.ui.statusbar.showMessage(f"File load completed successfully in {finish - start:0.4f} seconds")
        print(f"File load completed successfully in {finish - start:0.4f} seconds")


############    Line Box Image Methods    #############

    def on_acceptLineBoxEdit(self):
        if self.statusDrawingMode.text() == 'Table':
            self.putSbLineBox()
            #self.completeSbLineBox
        if self.statusDrawingMode.text() == 'Mouse':
            self.getRbLineBox()
        pass

    def on_rDrawSelection(self):
        self.rubberBand = ResizableRubberBand(self)
        self.rubberBand.hide()
        #self.on_editLineBox(self.row_selected)
        self.statusBoxMode.setText("Edit")
        #self.statusBoxType.setText("Line")
        self.statusSelectionMode.setText("Row")
        self.statusDrawingMode.setText("Mouse")

        self.currentBoxTable.setSortingEnabled(False)
        self.row_selected = self.currentBoxTable.currentRow()
        #print("Editing LineBoxTable selection")
        self.ui.ZoomComboBox.setCurrentText('Contents')
        self.setPrevLineBox()
        # self.getPrevTextLineBox()
        self.ui.statusbar.showMessage('Editing LineBox image using mouse and QRubberBand')
        self.on_resetLineBox()
        #self.currentBoxTable.clearSelection()

    def on_sDrawSelection(self):
        self.row_selected = self.currentBoxTable.currentRow()
        # self.on_editLineBox(self.row_selected)
        self.statusBoxMode.setText("Edit")
        #self.statusBoxType.setText("Line")
        self.statusSelectionMode.setText("Row")
        self.statusDrawingMode.setText("Table")

        self.currentBoxTable.setSortingEnabled(False)
        self.ui.ZoomComboBox.setCurrentText('Contents')

        self.setPrevLineBox()
        #self.on_editLineBox(self.row_selected)
        self.on_selectLineBox(self.row_selected)

        print('Edit LineBox image using LineBoxTable spinboxes')
        self.ui.statusbar.showMessage('Edit LineBox image using LineBoxTable spinboxes')
        # self.currentBoxTable.clearSelection()
        self.currentBoxTable.setSortingEnabled(False)
        colcount = self.currentBoxTable.columnCount() - 6
        for col in range(colcount):
            self.tableitem = self.currentBoxTable.item(self.row_selected, col)
            self.cellwidget = self.currentBoxTable.cellWidget(self.row_selected, col)
            self.cellvalue = self.currentBoxTable.item(self.row_selected, col).text()
            print(f'Selected Cell Location:  Row: {self.row_selected} Column: {col}')
            print(f'Current Cell Widget: {self.cellwidget}')
            print(f'Current Cell Value: {self.cellvalue}')
            if col == 0:
                self.tableitem.setFlags(qtc.Qt.ItemIsEditable)
            elif col == 1:
                self.currx = int(self.cellvalue)
            elif col == 2:
                self.curry = int(self.cellvalue)
            elif col == 3:
                self.currw = int(self.cellvalue)
            elif col == 4:
                self.currh = int(self.cellvalue)

        print(f'Prev X: {self.prevx} Prev Y: {self.prevy} Prev W: {self.prevw} Prev H: {self.prevh}')
        print(f'Curr X: {self.currx} Curr Y: {self.curry} Curr W: {self.currw} Curr H: {self.currh}')
        self.ui.statusbar.showMessage(f'Prev X: {self.prevx} Prev Y: {self.prevy} Prev W: {self.prevw} Prev H: {self.prevh} --- Curr X: {self.currx} Curr Y: {self.curry} Curr W: {self.currw} Curr H: {self.currh}')
        #self.getSpinBox()
        self.getSpinBoxes()

    def on_insertRowAbove(self):
        row = self.currentBoxTable.currentRow()
        self.on_editLineBox(row)
        if row:
            self.currentBoxTable.insertRow(row)
            self.renumberRows()
            self.LineBoxTable2csv()

    def on_insertRowBelow(self):
        row = self.currentBoxTable.currentRow()
        self.on_editLineBox(row)
        if row:
            self.currentBoxTable.insertRow(row+1)
            self.renumberRows()
            self.LineBoxTable2csv()

    def on_deleteRowSelection(self):
        row = self.currentBoxTable.currentRow()
        self.on_drawLineBox(row)
        if row:
            popup = qtw.QMessageBox(self)
            popup.setIcon(qtw.QMessageBox.Information)
            popup.setWindowTitle("Are you sure?")
            popup.setText("This will delete the current row! This cannot be undone!")
            popup.setStandardButtons(qtw.QMessageBox.Ok|qtw.QMessageBox.Cancel)
            #popup.exec()
            #if popup.buttonClicked() == qtw.QMessageBox.Ok:
            returnValue = popup.exec()
            if returnValue == qtw.QMessageBox.Ok:
                print('OK clicked')
                self.setPrevLineBox()
                self.on_resetLineBox()
                self.currentBoxTable.removeRow(row)
                self.renumberRows()
                self.LineBoxTable2csv()
                self.drawLineBoxImage
                self.saveLineBoxImage()
                self.BoxText2BoxTable()
            else:
                pass

    def on_currentRowChanged(self,current,previous):
        # Indexes Selected
        self.ix_selected = current
        self.prev_ix_selected = previous

        # Row Selected
        self.row_selected = current.row()
        # Previous Row Selected
        self.prev_row_selected = previous.row()

        self.run_event = False

        print(f'Selected Row: {self.row_selected}  Previous Row: {self.prev_row_selected}')
        self.ui.statusbar.showMessage(f'Selected Row: {self.row_selected}  Previous Row: {self.prev_row_selected}')

        # clear the CellWidgets
        rowcount = self.currentBoxTable.rowCount()
        colcount = self.currentBoxTable.columnCount()
        for row in range(rowcount):
            for col in range(colcount):
                self.currentBoxTable.removeCellWidget(row,col)

        self.showEditButtons()
        self.currentBoxTable.setSortingEnabled(False)
        self.row_selected = self.currentBoxTable.currentRow()
        print("Editing LineBoxTable selection")
        self.ui.ZoomComboBox.setCurrentText('Contents')
        self.currentBoxTable.resizeRowsToContents()
        if self.prev_row_selected >= 0:
            self.on_editLineBox(self.prev_row_selected)
        if self.ui.LineCheckBox.isChecked():
            self.getLineBoxImageLines()
        self.on_selectLineBox(self.row_selected)

    def on_boxValueChanged(self):
        print('This is the handler for the selected spinbox value that is changed')
        #self.spinbox.valueChanged.disconnect(self.on_boxValueChanged)
        self.on_resetLineBox()
        row = self.currentBoxTable.currentRow()
        col = self.currentBoxTable.currentColumn()
        xval = int(self.currentBoxTable.item(row,1).text())
        yval = int(self.currentBoxTable.item(row,2).text())
        wval = int(self.currentBoxTable.item(row,3).text())
        hval = int(self.currentBoxTable.item(row,4).text())
        if col == 1:
            xval = self.currentBoxTable.cellWidget(row, 1).value()
            self.currentBoxTable.item(row,1).setText(str(xval))
        elif col == 2:
            yval = self.currentBoxTable.cellWidget(row, 2).value()
            self.currentBoxTable.item(row,2).setText(str(yval))
        elif col == 3:
            wval = self.currentBoxTable.cellWidget(row, 3).value()
            self.currentBoxTable.item(row,3).setText(str(wval))
        elif col == 4:
            hval = self.currentBoxTable.cellWidget(row, 4).value()
            self.currentBoxTable.item(row,4).setText(str(hval))
        #self.spinbox.valueChanged.connect(self.on_boxValueChanged)
        self.setPrevLineBox()

        #For printing purposes
        line = int(self.currentBoxTable.item(row,0).text())
        print(f'Line: {str(line)} X:{str(xval)} Y:{str(yval)} W:{str(wval)} H:{str(hval)}')
        self.ui.statusbar.showMessage(f'Line: {str(line)} X:{str(xval)} Y:{str(yval)} W:{str(wval)} H:{str(hval)}')
        #Scaled
        #scaled_x,scaled_y,scaled_w,scaled_h = int(self.xval/self.scale),int(self.yval/self.scale),int(self.wval/self.scale),int(self.hval/self.scale)
        #self.drawSbLineBox(scaled_x,scaled_y,scaled_w,scaled_h)

        #Not Scaled
        self.x_sb_draw = xval
        self.y_sb_draw = yval
        self.w_sb_draw = wval
        self.h_sb_draw = hval
        self.drawSbLineBox()
        #self.drawSbLineBox(self.xval,self.yval,self.wval,self.hval)

    def on_selectLineBox(self,row):
        # Draw/Redraw green LineBox
        print('Setting selected linebox to green')
        self.ui.statusbar.showMessage('Setting selected linebox to green')
        if row:
            x = int(self.currentBoxTable.item(row,1).text())
            y = int(self.currentBoxTable.item(row,2).text())
            w = int(self.currentBoxTable.item(row,3).text())
            h = int(self.currentBoxTable.item(row,4).text())
            cv2.rectangle(self.norm,(x,y),(x+w, y+h),(0,255,0),2)
            pil_img = Image.fromarray(self.norm)
            qimage = ImageQt.ImageQt(pil_img)
            self.pixmap = qtg.QPixmap.fromImage(qimage).scaled(self.scale * self.origsize, qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)
            self.currentBoxImage.setPixmap(self.pixmap)
            print("Selected linebox should be green")
            self.ui.statusbar.showMessage("Selected linebox should be green")
            self.box_color = "green"

    def on_editLineBox(self,prevrow):
        if prevrow:
            x = int(self.currentBoxTable.item(prevrow,1).text())
            y = int(self.currentBoxTable.item(prevrow,2).text())
            w = int(self.currentBoxTable.item(prevrow,3).text())
            h = int(self.currentBoxTable.item(prevrow,4).text())
            cv2.rectangle(self.norm,(x,y),(x+w, y+h),(0,0,255),2)
            pil_img = Image.fromarray(self.norm)
            qimage = ImageQt.ImageQt(pil_img)
            self.pixmap = qtg.QPixmap.fromImage(qimage).scaled(self.scale * self.origsize, qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)
            self.currentBoxImage.setPixmap(self.pixmap)

    def on_drawLineBox(self,row):
        # Draw/Redraw red LineBox
        print('Resetting previous linebox to red')
        self.ui.statusbar.showMessage('Resetting linebox to red')
        if row:
            x = int(self.currentBoxTable.item(row,1).text())
            y = int(self.currentBoxTable.item(row,2).text())
            w = int(self.currentBoxTable.item(row,3).text())
            h = int(self.currentBoxTable.item(row,4).text())
            cv2.rectangle(self.norm,(x,y),(x+w, y+h),(0,0,255),2)
            pil_img = Image.fromarray(self.norm)
            qimage = ImageQt.ImageQt(pil_img)
            self.pixmap = qtg.QPixmap.fromImage(qimage).scaled(self.scale * self.origsize, qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)
            self.currentBoxImage.setPixmap(self.pixmap)
            self.box_color = "red"
            print('Selected linebox should be red')
            self.ui.statusbar.showMessage('Selected linebox should be red')

    def on_resetLineBox(self):
        # Draw/Redraw white LineBox
        print('Resetting previous linebox to white')
        self.ui.statusbar.showMessage('Resetting previous linebox to white')
        x = self.prevx
        y = self.prevy
        w = self.prevw
        h = self.prevh
        cv2.rectangle(self.norm,(x,y),(x+w, y+h),(255,255,255),2)
        pil_img = Image.fromarray(self.norm)
        qimage = ImageQt.ImageQt(pil_img)
        self.pixmap = qtg.QPixmap.fromImage(qimage).scaled(self.scale * self.origsize, qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)
        self.currentBoxImage.setPixmap(self.pixmap)
        self.box_color = "white"
        print('Selected linebox should be removed (i.e. white, blank or background)')
        self.ui.statusbar.showMessage('Selected linebox should be removed (i.e. white, blank or background)')

    def normImage(self):
        img = cv2.imread(self.imgpath)
        # convert image to grayscale and normalized rgb
        self.gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

        # normalize to Black and White
        norm = cv2.normalize(self.gray, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        #print(norm.shape, norm.dtype)

        # convert to 3 channel
        self.norm = cv2.cvtColor(norm, cv2.COLOR_GRAY2BGR)
        #print(self.norm.shape, self.norm.dtype)
        #print(np.amin(self.norm),np.amax(self.norm))

    def morphImage(self):
        print("Setting image morpholgy with enabled sliders")

    # LineBox Drawing Methods
    # Rubberband(Rb) LineBox Drawing Methods
    def putRbLineBox(self):
        self.run_event = False
        if self.rubberBand:
            self.rubberBand.hide()
            self.rubberBand = None
        x = str(self.x_rb_draw)
        y = str(self.y_rb_draw)
        w = str(self.w_rb_draw)
        h = str(self.h_rb_draw)

        if self.statusBoxType.text() == "Line":
            self.line = int(self.currentBoxTable.item(self.row_selected,0).text())
            print(f'Updating LineBoxText JSON and CSV files for line:{str(self.line)} with str values: x:{x}, y:{y}, w:{w}, h:{h}')
            self.update_LineBoxText(str(self.line),x,y,w,h)
        elif self.statusBoxType.text() == "Page":
            self.page = int(self.currentBoxTable.item(self.row_selected,0).text())
            print(f'Updating PageBoxText JSON and CSV files for page:{str(self.page)} with str values: x:{x}, y:{y}, w:{w}, h:{h}')
            self.update_PageBoxText(str(self.page),x,y,w,h)

        self.BoxText2BoxTable()

        self.drawLineBoxImage()

        if self.statusBoxType.text() == "Line":
            self.saveLineBoxImage()
        elif self.statusBoxType.text() == "Page":
            self.savePageBoxImage()

        self.currentBoxTable.clearSelection()
        self.startEditLoop = True
        # Save Line Image
        x = int(x)
        y = int(y)
        w = int(w)
        h = int(h)
        roi = self.norm[y:y+h, x:x+w]

        if self.statusBoxType.text() == "Line":
            self.saveLineBoxImageLine(roi,self.line)
        elif self.statusBoxType.text() == "Page":
            self.savePageBoxImagePage(roi,self.page)
        self.statusDrawingMode.setText("None")

    def drawRbLineBox(self):
        if self.statusDrawingMode.text() == "Mouse":
            x = self.x_rb_draw
            y = self.y_rb_draw
            w = self.w_rb_draw
            h = self.h_rb_draw
            # Draw/Redraw red Linebox
            cv2.rectangle(self.norm,(x,y),(x+w, y+h),(0,0,255),2)
            #self.saveLineBoxImage()
            self.showImage(self.boximgpath)
            self.putRbLineBox()

        if self.rubberBand:
            self.rubberBand.hide()
            self.rubberBand = None

    def getRbLineBox(self):
        #self.rubberBand.hide()
        self.run_event = True
        if self.statusDrawingMode.text() == "Mouse":
            # At scale DrawLineBox QRect at LineBox Image offset from MainWindow origin(0,0)
            DrawImg_xs = self.x_rb
            DrawImg_ys = self.y_rb
            #DrawImg_xs = self.x_rb
            #DrawImg_ys = self.y_rb
            DrawImg_ws = self.w_rb
            DrawImg_hs = self.h_rb
            DrawImg_sqrect = QRect(DrawImg_xs,DrawImg_ys,DrawImg_ws,DrawImg_hs)
            print("Offset Scaled QRect = " + str(DrawImg_sqrect))

            # Up scale DrawLineBox QRect at LineBox Image previously offset from MainWindow origin(0,0)
            self.x_rb_draw = int(round(DrawImg_xs / self.scale))
            self.y_rb_draw = int(round(DrawImg_ys / self.scale))
            self.w_rb_draw = int(round(DrawImg_ws / self.scale))
            self.h_rb_draw = int(round(DrawImg_hs / self.scale))
            DrawImg_uqrect = QRect(self.x_rb_draw,self.y_rb_draw,self.w_rb_draw,self.h_rb_draw)
            print("Offset Upscaled QRect = " + str(DrawImg_uqrect))

            print(f'x_rb_draw: {self.x_rb_draw} y_rb_draw: {self.y_rb_draw} w_rb_draw: {self.w_rb_draw} h_rb_draw: {self.h_rb_draw}')
            self.drawRbLineBox()

    # Spinbox(Sb) Drawing Methods
    def putSbLineBox(self):
        row = self.currentBoxTable.currentRow()
        x = self.x_sb_draw
        y = self.y_sb_draw
        w = self.w_sb_draw
        h = self.h_sb_draw

        # Update LineBoxText and LineBoxTable

        if self.statusBoxType.text() == "Line":
            self.line = int(self.currentBoxTable.item(self.row_selected,0).text())
            print(f'Updating LineBoxText JSON and CSV files for line:{str(self.line)} with str values: x:{x}, y:{y}, w:{w}, h:{h}')
            self.update_LineBoxText(str(self.line),x,y,w,h)
        elif self.statusBoxType.text() == "Page":
            self.page = int(self.currentBoxTable.item(self.row_selected,0).text())
            print(f'Updating PageBoxText JSON and CSV files for page:{str(self.page)} with str values: x:{x}, y:{y}, w:{w}, h:{h}')
            self.update_PageBoxText(str(self.page),x,y,w,h)
        #self.line = int(self.currentBoxTable.item(row,0).text())
        #print(f'Updating LineBoxText JSON and CSV files for line:{str(self.line)} with str values: x:{str(x)}, y:{str(y)}, w:{str(w)}, h:{str(h)}')
        #self.update_LineBoxText(str(self.line),str(x),str(y),str(w),str(h))
        self.BoxText2BoxTable()
        self.drawLineBoxImage()

        if self.statusBoxType.text() == "Line":
            self.saveLineBoxImage()
        elif self.statusBoxType.text() == "Page":
            self.savePageBoxImage()

        #self.saveLineBoxImage()
        self.currentBoxTable.clearSelection()
        #self.clearSpinBoxes()
        # Save Line Image
        roi = self.norm[y:y+h, x:x+w]
        if self.statusBoxType.text() == "Line":
            self.saveLineBoxImageLine(roi,self.line)
        elif self.statusBoxType.text() == "Page":
            self.savePageBoxImagePage(roi,self.page)
        self.statusDrawingMode.setText("None")
        self.currentBoxTable.setSortingEnabled(True)
        self.statusDrawingMode.setText("None")

    def completeSbLineBox(self):
        popup = qtw.QMessageBox(self)
        popup.setWindowModality(Qt.NonModal)
        popup.setIcon(qtw.QMessageBox.Information)
        popup.setWindowTitle("Edit Line Box")
        popup.setText("Press OK to keep the edited Line Box")
        popup.setStandardButtons(qtw.QMessageBox.Ok|qtw.QMessageBox.Cancel)
        popup.exec()
        if popup.clickedButton() == qtw.QMessageBox.Ok:
            self.putSbLineBox()
        #elif popup.clickedButton() == qtw.QMessageBox.Cancel:
        else:
            #self.clearSpinBoxes()
            self.BoxText2BoxTable()

    def drawSbLineBox(self):
        x = int(self.x_sb_draw)
        y = int(self.y_sb_draw)
        w = int(self.w_sb_draw)
        h = int(self.h_sb_draw)
        print(f'Spinbox values: x:{x} y:{y} w:{w} h:{h}')
        self.ui.statusbar.showMessage(f'Spinbox values: x:{x} y:{y} w:{w} h:{h}')
        cv2.rectangle(self.norm,(x,y),(x+w, y+h),(0,0,255),2)
        pil_img = Image.fromarray(self.norm)
        qimage = ImageQt.ImageQt(pil_img)
        self.pixmap = qtg.QPixmap.fromImage(qimage).scaled(self.scale * self.origsize, qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)
        self.currentBoxImage.setPixmap(self.pixmap)

    def getSpinBoxes(self):
        self.row_selected = self.currentBoxTable.currentRow()
        row = self.row_selected
        #self.col_selected = self.currentBoxTable.currentColumn()
        #print(f'Selected Cell Location:  Row: {self.row_selected} Column: {self.col_selected} Cell Value: {self.cellvalue}')
        for column in range(1,5):
            value = self.currentBoxTable.item(row,column).text()
            spinbox = QSpinBox(self.currentBoxTable) #changed parent from None to self.currentBoxTable - could also be just self
            #self.spinbox.setMaximum(6000)
            aspect = round((self.currentBoxImage.width()/self.currentBoxImage.height()),2)
            print(f'Aspect Ratio: {aspect}')
            spinbox.setMaximum(self.currentBoxImage.width())
            # setting step size to the reciprocal of the scale
            stepsize = int((1/self.scale)/2)
            # using scaled step size
            #spinbox.setAccelerated(False)
            spinbox.setSingleStep(stepsize)
            #spinbox.setStepType(qtw.QAbstractSpinBox.DefaultStepType)
            #spinbox.setStepType(qtw.QAbstractSpinBox.AdaptiveDecimalStepType)
            #spinbox.setCorrectionMode(qtw.QAbstractSpinBox.CorrectToNearestValue)

            # getting font of the spin box
            font = spinbox.font()
            # setting point size
            font.setPointSize(8)
            # reassigning this font to the spin box
            spinbox.setFont(font)

            spinbox.setFixedWidth(50)
            spinbox.setValue(int(value))
            self.currentBoxTable.setCellWidget(row,column,spinbox)
            self.currentBoxTable.resizeRowToContents(row)
            self.currentBoxTable.resizeColumnToContents(column)
            spinbox.valueChanged.connect(self.on_boxValueChanged)

    '''def getSpinBox(self):
        self.row_selected = self.currentBoxTable.currentRow()
        self.col_selected = self.currentBoxTable.currentColumn()
        print(f'Selected Cell Location:  Row: {self.row_selected} Column: {self.col_selected} Cell Value: {self.cellvalue}')
        self.spinbox = QSpinBox(self.currentBoxTable) #changed parent from None to self.currentBoxTable - could also be just self
        #self.spinbox.setMaximum(6000)
        self.spinbox.setMaximum(int(self.scale*self.ui.Image.height()))
        self.spinbox.setValue(int(self.cellvalue))
        self.currentBoxTable.setCellWidget(self.row_selected,self.col_selected,self.spinbox)
        self.spinbox.valueChanged.connect(self.on_boxValueChanged)'''

    def getLineBoxImageLines(self):
        rowcount = self.currentBoxTable.rowCount()
        for row in range(rowcount):
            line = self.currentBoxTable.item(row,0).text()
            x = int(self.currentBoxTable.item(row,1).text())
            y = int(self.currentBoxTable.item(row,2).text())
            w = int(self.currentBoxTable.item(row,3).text())
            h = int(self.currentBoxTable.item(row,4).text())
            linex = x+w-80
            liney = y+h-4
            if self.ui.LineCheckBox.isChecked():
                print(f'Placing line number at : {linex},{liney}')
                cv2.putText(self.norm,line,(linex,liney),cv2.FONT_HERSHEY_SIMPLEX,2,(255,0,0),3)
            else:
                print(f'Removing line number at : {linex},{liney}')
                cv2.putText(self.norm,line,(linex,liney),cv2.FONT_HERSHEY_SIMPLEX,2,(255,255,255),3)
        pil_img = Image.fromarray(self.norm)
        qimage = ImageQt.ImageQt(pil_img)
        self.pixmap = qtg.QPixmap.fromImage(qimage).scaled(self.scale * self.origsize, qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)
        self.currentBoxImage.setPixmap(self.pixmap)

    def saveLineBoxImageLine(self,roi,bnum):
        PILimage = Image.fromarray(roi)
        thresh = 127
        fn = lambda x : 255 if x > thresh else 0
        PIL_BWimage = PILimage.convert('L').point(fn, mode='1')
        tif_outfile = self.path_of_imgautosplit + self.imgfilename + "_Line" + str(bnum) + ".tif"
        print("Generating: " + tif_outfile)
        PIL_BWimage.save(tif_outfile, "TIFF", dpi=(300,300))

    def saveLineBoxImage(self):
        #self.imgboxfile = self.path_of_imglinebox + self.imgfilename + "_linebox" + self.imgfileext
        #self.ui.statusbar.showMessage(f'Saving LineBox file: {self.imgboxfile}')
        print(f'Saving LineBox file: {self.imgpath}')
        cv2.imwrite(self.imgpath, self.norm)
        self.boximgpath = self.imgpath
        self.showImage(self.boximgpath)
        if self.ui.LineCheckBox.isChecked():
            self.getLineBoxImageLines()

    def drawLineBoxImage(self):
        print(f'Drawing Linebox Image from LineBoxText: \n {self.txtpath}')
        # Set initial box count
        bnum = 1
        with open(self.txtpath, "r") as txtboxfile:
            reader = list(csv.reader(txtboxfile, delimiter = '\t'))
            # Remove column header from list of rows
            lineboxes = reader[1:]
            self.rowCount = len(lineboxes)
            for linebox in lineboxes:
                # Extract x,y,w,h from each row
                line = str(linebox[0])
                x = int(linebox[1])
                y = int(linebox[2])
                w = int(linebox[3])
                h = int(linebox[4])
                roi = self.norm[y:y+h, x:x+w]
                print(f'Placing line box at : {x},{y},{w},{h}')
                #self.on_drawLineBox(x,y,w,h)
                cv2.rectangle(self.norm,(x,y),(x+w, y+h),(0,0,255),2)
                if self.statusBoxType.text() == "Line":
                    # Save Line Image
                    self.saveLineBoxImageLine(roi,bnum)
                elif self.statusBoxType.text() == "Page":
                    # Save Page Image
                    self.savePageBoxImagePage(roi,bnum)
                bnum += 1
        txtboxfile.close()

###########    Line Box Text Methods    #############

    def actionRenameGreek_text_lines_old(self):
        print("renaming Greek textlines for ground truth")
        # usage: tr.text2groundtruth(source, destination)
        #tr.text2groundtruth(r"/home/jetson/Projects/Python/EstablishTruth/Greek lines4groundtruth/", "/home/jetson/Projects/Python/EstablishTruth/Greek lines2groundtruth/")
        tr.text2groundtruth(r"Model/Text/EstablishTruth/Greek/txt_greek_lines_autosplit/greek_book_40_Matthew/", "Model/Text/EstablishTruth/Greek/txt_greek_lines_autosplit/greek_book_40_Matthew/")

    def actionSplit_Latin_Text_Lines(self):
        print("splitting Latin textlines for ground truth")
        # usage: tr.splittextlines(source, destination)
        # tr.splittextlines(r"/home/jetson/Projects/Python/EstablishTruth/Latin txt4linesplit/", "/home/jetson/Projects/Python/EstablishTruth/Latin lines4groundtruth/")
        tr.splittextlines("/home/jetson/Projects/Python/EstablishTruth/Latin txt4linesplit/", "/home/jetson/Projects/Python/EstablishTruth/Latin lines4groundtruth/")

    def actionRename_Latin_Text_Lines(self):
        print("renaming Latin textlines for ground truth")
        # usage: tr.text2groundtruth(source, destination)
        #tr.text2groundtruth(r"/home/jetson/Projects/Python/EstablishTruth/Latin lines4groundtruth/", "/home/jetson/Projects/Python/EstablishTruth/Latin lines2groundtruth/")
        tr.text2groundtruth(r"/home/jetson/Projects/Python/EstablishTruth/Latin lines4groundtruth/", "/home/jetson/Projects/Python/EstablishTruth/Latin lines2groundtruth/")

    def splittextlines(self, source, destination):
                dest_of_textlinefiles = destination
                path_of_textfiles = source
                print(f'source:  {source} destination {destination}')
                list_of_textfiles = os.listdir(path_of_textfiles)

                for tfile in list_of_textfiles:

                        textfile = open(path_of_textfiles + tfile)

                        filestr = os.path.basename(path_of_textfiles + tfile)

                        filesplit = os.path.splitext(filestr)

                        filename = filesplit[0]

                        fileext = filesplit[1]

                        for cnt, line in enumerate(textfile):
                                # open file to write line
                                outF = open(dest_of_textlinefiles + filename + "_Line" + str(cnt + 1) + fileext, "w")
                                # write line to output file
                                #outF.write(line)
                                outF.write(" ".join(line.split()))
                                #outF.write("\n")
                                print("Line {}: {}".format(cnt, line))
                                outF.close()

    def text2groundtruth(source, destination):
            def sorted_alphanumeric(data):
                    convert = lambda text: int(text) if text.isdigit() else text.lower()
                    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
                    return sorted(data, key=alphanum_key)
                    #usage:dirlist = sorted_alphanumeric(os.listdir(...)) - works great!

            dest_of_groundtruth = destination
            path_of_textfiles = source
            list_of_textfiles = sorted_alphanumeric(os.listdir(path_of_textfiles))
            font_name = "FROMVS_Regular_"

            for textfile in list_of_textfiles:

                    '''filestr = os.path.basename(os.path.join(path_of_textfiles, textfile))

                    print(dest_of_groundtruth + filestr)

                    shutil.copy(path_of_textfiles + filestr, dest_of_groundtruth + filestr)'''

                    filestr = os.path.basename(os.path.join(path_of_textfiles, textfile))

                    filesplit = os.path.splitext(filestr)

                    filename = filesplit[0]

                    fileext = filesplit[1]

                    namesplit = filename.split("_")

                    versionref = namesplit[0]

                    pagestr = namesplit[2]

                    pagenum = int(pagestr)

                    linestr = namesplit[3]

                    print(font_name + versionref + "_Page_" + pagestr + "_" + linestr + fileext)

                    shutil.move(path_of_textfiles + filestr, dest_of_groundtruth + font_name + versionref + "_Page_" + pagestr + "_" + linestr + fileext)

    # Table Methods

    def LineBoxTable2csv(self):
        #self.txtpath = self.path_of_txtlinebox + self.imgfilename + "_linebox.txt"
        print(f'Path of linebox.txt: {self.txtpath}')
        if os.path.exists(self.txtpath):
            print(f'Removing: {self.txtpath}')
            os.remove(self.txtpath)
            self.currentTextTable.clear()
        colCount = range(self.currentBoxTable.columnCount()- 6)
        header = [self.currentBoxTable.horizontalHeaderItem(column).text() for column in colCount]
        with open(self.txtpath, 'w') as csvfile:
            #writer = csv.writer(csvfile, dialect='excel', lineterminator='\n')
            writer = csv.writer(csvfile, dialect='excel', delimiter='\t', lineterminator='\n')
            writer.writerow(header)
            for row in range(self.currentBoxTable.rowCount()):
                writer.writerow(self.currentBoxTable.item(row, column).text() for column in colCount)
        self.getText(self.txtpath)

    def update_LineBoxText(self,line,x,y,w,h):
        print(f'From getRbLineBox method - Line: {line}  X: {x}  Y: {y}  W: {w} H: {h}')
        self.jsonpath = self.path_of_jsonlinebox + self.imgfilename + "_linebox.json"

        jsonfilepath = self.jsonpath
        #self.txtpath = self.path_of_txtlinebox + self.imgfilename + "_linebox.txt"
        csvfilepath = self.txtpath
        self.csv2json(csvfilepath,jsonfilepath)
        with open(jsonfilepath, 'r') as f:
            data = json.load(f)
            # Iterating through the json
            for Line in data:
                print(f'Line from json file: {Line} -- line from putRbLineBox: {line} ')
                if Line['Line'] == line:
                    Line['X'] = x
                    Line['Y'] = y
                    Line['W'] = w
                    Line['H'] = h
                    print(f'Updating Line: {line} found in JSON file. Dimensions :  X: {x}  Y: {y}  W: {w}  H: {h}')
                else:
                    print(f'Line: {line} not found in JSON file.')
            # Closing file
            f.close()
            os.remove(jsonfilepath)
            with open(jsonfilepath, 'w') as f:
                json.dump(data, f, indent=4)
            f.close()
        self.json2csv(csvfilepath,jsonfilepath)
        self.showText(csvfilepath)

    def showEditButtons(self):
        if self.statusBoxMode.text() == 'Edit':
            rowcount = self.currentBoxTable.rowCount()
            selected_row = self.currentBoxTable.currentRow()
            print(f'selected_row: {selected_row}')
            colcount = self.currentBoxTable.columnCount()
            self.currentBoxTable.horizontalHeader().resizeSection(0, 25)
            insertAButton = qtw.QPushButton(self.currentBoxTable)
            insertBButton = qtw.QPushButton(self.currentBoxTable)
            deleteButton = qtw.QPushButton(self.currentBoxTable)
            rDrawButton = qtw.QPushButton(self.currentBoxTable)
            sDrawButton = qtw.QPushButton(self.currentBoxTable)
            acceptButton = qtw.QPushButton(self.currentBoxTable)

            for row in range(rowcount):
                if row == selected_row:
                    print(f'Row {row} matched!')
                    for col in range(colcount):
                        if col == 5:
                            insertAButton.setEnabled(True)
                            insertAButton.show()
                            insertAIcon = qtg.QIcon()
                            insertAIcon.addPixmap(qtg.QPixmap(":/Icons/Icons/insertabove.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
                            insertAButton.setIcon(insertAIcon)
                            insertAButton.setIconSize(QSize(12,12))
                            self.currentBoxTable.setCellWidget(row,col,insertAButton)
                            self.inslocation = "above"
                            insertAButton.clicked.connect(self.on_insertRowAbove)
                        elif col == 6:
                            insertBButton.setEnabled(True)
                            insertBButton.show()
                            insertBIcon = qtg.QIcon()
                            insertBIcon.addPixmap(qtg.QPixmap(":/Icons/Icons/insertbelow.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
                            insertBButton.setIcon(insertBIcon)
                            insertBButton.setIconSize(QSize(12,12))
                            self.currentBoxTable.setCellWidget(row,col,insertBButton)
                            self.inslocation = "below"
                            insertBButton.clicked.connect(self.on_insertRowBelow)
                        elif col == 7:
                            deleteButton.setEnabled(True)
                            deleteButton.show()
                            deleteIcon = qtg.QIcon()
                            deleteIcon.addPixmap(qtg.QPixmap(":/Icons/Icons/deleterow.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
                            deleteButton.setIcon(deleteIcon)
                            deleteButton.setIconSize(QSize(12,12))
                            self.currentBoxTable.setCellWidget(row,col,deleteButton)
                            deleteButton.clicked.connect(self.on_deleteRowSelection)
                        elif col == 8:
                            rDrawButton.setEnabled(True)
                            rDrawButton.show()
                            rDrawIcon = qtg.QIcon()
                            rDrawIcon.addPixmap(qtg.QPixmap(":/Icons/Icons/rubberband.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
                            rDrawButton.setIcon(rDrawIcon)
                            rDrawButton.setIconSize(QSize(12,12))
                            self.currentBoxTable.setCellWidget(row,col,rDrawButton)
                            rDrawButton.clicked.connect(self.on_rDrawSelection)
                        elif col == 9:
                            sDrawButton.setEnabled(True)
                            sDrawButton.show()
                            sDrawIcon = qtg.QIcon()
                            sDrawIcon.addPixmap(qtg.QPixmap(":/Icons/Icons/spinbox4.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
                            sDrawButton.setIcon(sDrawIcon)
                            sDrawButton.setIconSize(QSize(16,16))
                            self.currentBoxTable.setCellWidget(row,col,sDrawButton)
                            sDrawButton.clicked.connect(self.on_sDrawSelection)
                        elif col == 10:
                            acceptButton.setEnabled(True)
                            acceptButton.show()
                            acceptButton = qtw.QPushButton(self.currentBoxTable)
                            acceptIcon = qtg.QIcon()
                            acceptIcon.addPixmap(qtg.QPixmap(":/Icons/Icons/Valid.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
                            acceptButton.setIcon(acceptIcon)
                            acceptButton.setIconSize(QSize(12,12))
                            self.currentBoxTable.setCellWidget(row,col,acceptButton)
                            acceptButton.clicked.connect(self.on_acceptLineBoxEdit)

    def LineBoxText2LineBoxTable(self):
        #self.currentBoxTable.clearContents()
        boxes = []
        reader = csv.reader(open(self.txtpath), delimiter = '\t')

        for row in reader:
            boxes.append(row)

        if self.statusBoxMode.text() == "Make":
            boxes = boxes[0:]
        else:
            boxes = boxes[1:]

        rowCount = len(boxes)
        self.currentBoxTable.setRowCount(rowCount)
        colcount = self.currentBoxTable.columnCount()
        print(f'LineBoxTable column count: {colcount}')
        self.currentBoxTable.setSortingEnabled(False)
        #self.currentBoxTable.clearContents()
        for row, boxes in enumerate(boxes):
            for column, value in enumerate(boxes):
                if column == 0:
                    tableitem = qtw.QTableWidgetItem()
                    tableitem.setFlags(qtc.Qt.ItemIsEditable)
                    newItem = qtw.QTableWidgetItem(value)
                    self.currentBoxTable.setItem(row, column, newItem)
                elif column >= 1 and column <= 4:
                    #print(f'Updating LineBoxTable column: {column}')
                    newItem = qtw.QTableWidgetItem(value)

                    #Scaled
                    #newVal = int(newItem.text())
                    #scaledVal = int(newVal * self.scale)
                    #newItem.setText(str(scaledVal))

                    #Not Scaled
                    newVal = int(newItem.text())
                    newItem.setText(str(newVal))
                    self.currentBoxTable.setItem(row, column, newItem)
        self.showEditButtons()
        self.currentBoxTable.resizeColumnsToContents()
        self.currentBoxTable.resizeRowsToContents()
        self.currentBoxTable.setSortingEnabled(True)

    def renumberRows(self):
        print('Renumbering rows')
        rowcount = self.currentBoxTable.rowCount()
        colcount = self.currentBoxTable.columnCount() - 6
        for row in range(rowcount):
            item = self.currentBoxTable.item(row, 0)
            if not item:
                self.newrow = row
                print(f'Inserted row number: {row}')
                for column in range(colcount):
                    itemwidget = qtw.QTableWidgetItem()
                    self.currentBoxTable.setItem(row, column,itemwidget)
                    item = self.currentBoxTable.item(row, column)
                    if column == 0:
                        item.setText(str(row+1))
                    else:
                        item.setText(str(0))
            else:
                item.setText(str(row+1))
            self.currentBoxTable.setEditTriggers(qtw.QAbstractItemView.NoEditTriggers)

    def openTableMenu(self,position):
        tableMenu = QMenu()

        undoAction = tableMenu.addAction("Undo")
        iconUndo = qtg.QIcon()
        iconUndo.addPixmap(qtg.QPixmap(":/Icons/Icons/Undo-icon.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        undoAction.setIcon(iconUndo)

        redoAction = tableMenu.addAction("Redo")
        iconRedo = qtg.QIcon()
        iconRedo.addPixmap(qtg.QPixmap(":/Icons/Icons/Redo-icon.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        redoAction.setIcon(iconRedo)

        insertAboveAction = tableMenu.addAction("Insert Row Above")
        iconA = qtg.QIcon()
        iconA.addPixmap(qtg.QPixmap(":/Icons/Icons/insertabove.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        insertAboveAction.setIcon(iconA)

        insertBelowAction = tableMenu.addAction("Insert Row Below")
        iconB = qtg.QIcon()
        iconB.addPixmap(qtg.QPixmap(":/Icons/Icons/insertbelow.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        insertBelowAction.setIcon(iconB)

        deleteRowAction = tableMenu.addAction("Delete Current Row")
        iconD = qtg.QIcon()
        iconD.addPixmap(qtg.QPixmap(":/Icons/Icons/cross.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        deleteRowAction.setIcon(iconD)

        action = tableMenu.exec_(self.currentBoxTable.mapToGlobal(position))
        if action == undoAction:
            qtw.QUndoStack.undo()
        elif action == redoAction:
            qtw.QUndoStack.redo()
        elif action == insertAboveAction:
            self.on_insertRowAbove()
        elif action == insertBelowAction:
            self.on_insertRowBelow()
        elif action == deleteRowAction:
            self.on_deleteRowSelection()

    def setPrevLineBox(self):
        self.currentBoxTable.setSortingEnabled(False)
        self.row_selected = self.currentBoxTable.currentRow()
        row = self.row_selected
        #self.currentBoxTable.setCellWidget(self.row_selected,0,self.currentBoxTable)
        self.line = int(self.currentBoxTable.item(self.row_selected,0).text())
        # get dimensions of selected row/linebox
        self.prevx = int(self.currentBoxTable.item(row,1).text())
        self.prevy = int(self.currentBoxTable.item(row,2).text())
        self.prevw = int(self.currentBoxTable.item(row,3).text())
        self.prevh = int(self.currentBoxTable.item(row,4).text())

    def getPrevTextLineBox(self):
        self.currentBoxTable.setSortingEnabled(False)
        self.row_selected = self.currentBoxTable.currentRow()
        self.line = int(self.currentBoxTable.item(self.row_selected,0).text())
        # get dimensions of selected csv row/linebox
        with open(self.txtpath,'r') as csvfile:
            lines = csv.reader(csvfile, delimiter = '\t')
            for csvline in lines:
                if csvline[0] == str(self.line):
                    self.prevx = int(csvline[1])
                    self.prevy = int(csvline[2])
                    self.prevw = int(csvline[3])
                    self.prevh = int(csvline[4])

    # Text Methods

    def json2csv(self, csvFilePath, jsonFilePath):
        if self.statusBoxType.text() == "Line":
            columns = ['Line','X','Y','W','H']
        elif self.statusBoxType.text() == "Page":
            columns = ['Page','X','Y','W','H']
        df = pd.read_json (jsonFilePath)
        df = df[columns]
        df.to_csv(csvFilePath, sep='\t', header=True, index=False, encoding='utf-8')

    def csv2json(self, csvFilePath, jsonFilePath):
        jsonArray = []
        #read csv file
        with open(csvFilePath, encoding='utf-8') as csvf:
            #load csv file data using csv library's dictionary reader
            csvReader = csv.DictReader(csvf, delimiter = '\t')

            #convert each csv dictionary row into json array
            for row in csvReader:
                #add this python dict to json array
                jsonArray.append(row)

        #write jsonArray to file
        with open(jsonFilePath, 'w', encoding='utf-8') as jsonf:
            json.dump(jsonArray, jsonf, indent=4)

    # Mouse Controllers
    def mousePressEvent(self, event):
        #if self.rubberBand:
            # Limit scope of rubberband starting position
        if self.ui.ImageLe.displayText() != "":
            self.run_event = True
            x_min = int(self.img_xoffset) - 1
            #print(f'xmin: {x_min}')
            x_max = (int(self.img_xoffset) + self.scaled_pixmap.width()) + 1
            #print(f'xmax: {x_max}')
            y_min = int(self.img_yoffset) - 1
            #print(f'ymin: {y_min}')
            y_max = (int(self.img_yoffset) + self.scaled_pixmap.height()) + 1
            #print(f'ymax: {y_max}')
        else:
            self.run_event = False
            print('You cannot draw without a loaded image')
        if self.statusBoxMode.text() == "Edit":
            if self.statusDrawingMode.text() == "Mouse":
                self.event_x = event.pos().x()
                self.event_y = event.pos().y()
                self.start_pos = QPoint(self.event_x, self.event_y)
                print(f'Mouse clicked at start position: {self.start_pos}')
                if self.ui.ImageLe.displayText() != "":
                    self.run_event = True
                if event.button() == Qt.LeftButton and self.run_event == True:
                    self.rubberBand.setGeometry(QRect(self.start_pos, QSize()).normalized())
                    self.rubberBand.show()
                '''# Limit scope of rubberband starting position
                if self.ui.ImageLe.displayText() != "":
                    self.run_event = True
                    x_min = int(self.img_xoffset) - 1
                    #print(f'xmin: {x_min}')
                    x_max = (int(self.img_xoffset) + self.scaled_pixmap.width()) + 1
                    #print(f'xmax: {x_max}')
                    y_min = int(self.img_yoffset) - 1
                    #print(f'ymin: {y_min}')
                    y_max = (int(self.img_yoffset) + self.scaled_pixmap.height()) + 1
                    #print(f'ymax: {y_max}')
                else:
                    self.run_event = False
                    print('You cannot draw without a loaded image')'''

                '''if event.button() == Qt.LeftButton and self.run_event == True:
                    if self.event_x >= x_min and self.event_x <= x_max and self.event_y >= y_min and self.event_y <= y_max:
                        #if self.rubberBand.w() != 0 and self.rubberBand.h() != 0:
                        #self.rubberBand = ResizableRubberBand(self)
                        self.run_event = True
                        self.rubberBand.setGeometry(QRect(self.start_pos, QSize()).normalized())
                        self.rubberBand.show()
                    else:
                        self.run_event = False
                        print('You cannot draw outside the current image borders')'''

            else:
                # If in Edit mode, select Row from LineBox Image
                self.run_event = False
                if event.button() == Qt.LeftButton:
                    event_x = event.pos().x()
                    grid_x = event_x - int(self.img_xoffset)
                    event_y = event.pos().y()
                    grid_y = event_y - int(self.img_yoffset)
                    scaled_x = int(round(grid_x / self.scale))
                    scaled_y = int(round(grid_y / self.scale))
                    if event_x >= x_min and event_x <= x_max and event_y >= y_min and event_y <= y_max:
                        rowcount = self.currentBoxTable.rowCount()
                        for row in range(rowcount):
                            y = int(self.currentBoxTable.item(row,2).text())
                            h = int(self.currentBoxTable.item(row,4).text())
                            y_h = y + h
                            if y <= scaled_y and scaled_y <= y_h:
                                self.currentBoxTable.selectRow(row)

    def mouseMoveEvent(self, event):
        if self.statusBoxMode.text() == "Edit" and self.run_event:
            self.end_pos = event.pos()
            self.rubberBand.setGeometry(QRect(self.start_pos, self.end_pos).normalized())
            row = self.currentBoxTable.currentRow()
            geo = self.rubberBand.geometry()
            #while self.run_event:
            self.x_rb = self.rubberBand.x() - int(self.img_xoffset)
            self.y_rb = self.rubberBand.y() - int(self.img_yoffset)
            self.w_rb = self.rubberBand.width()
            self.h_rb = self.rubberBand.height()
            self.currentBoxTable.item(row,1).setText(str(int(round(self.x_rb/self.scale))))
            self.currentBoxTable.item(row,2).setText(str(int(round(self.y_rb/self.scale))))
            self.currentBoxTable.item(row,3).setText(str(int(round(self.w_rb/self.scale))))
            self.currentBoxTable.item(row,4).setText(str(int(round(self.h_rb/self.scale))))
            self.ui.statusbar.showMessage(f'x:{self.x_rb} y:{self.y_rb} w:{self.w_rb} h:{self.h_rb}')

    #def mouseReleaseEvent(self, event):

    # Utility Methods

    # Style Sheets
    def darkOrange(self):
        app.setStyleSheet(Path('ViewController/0-MainUI/Stylesheets/dark_orange.qss').read_text())

    def darkBlue(self):
        app.setStyleSheet(Path('ViewController/0-MainUI/Stylesheets/dark_blue.qss').read_text())

    def classic(self):
        app.setStyleSheet(Path('ViewController/0-MainUI/Stylesheets/classic.qss').read_text())

    def standardUI(self):
        app.setStyleSheet("")

###########    Other Classes and Subclasses    ############
class ResizableRubberBand(QWidget):
    """Wrapper to make QRubberBand mouse-resizable using QSizeGrip

    Source: http://stackoverflow.com/a/19067132/435253
    """
    def __init__(self, parent):
        super(ResizableRubberBand, self).__init__(parent)

        self.setWindowFlags(Qt.SubWindow)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.grip1 = QSizeGrip(self)
        self.grip2 = QSizeGrip(self)
        self.layout.addWidget(self.grip1, 0, Qt.AlignLeft | Qt.AlignTop)
        self.layout.addWidget(self.grip2, 0, Qt.AlignRight | Qt.AlignBottom)
        self.rubberband = QRubberBand(QRubberBand.Rectangle, self)
        self.rubberband.move(0, 0)
        self.rubberband.show()
        # self.show()

    def resizeEvent(self, event):
        self.rubberband.resize(self.size())
        row = self.parent().ui.LineBoxTable.currentRow()
        self.parent().x_rb = self.parent().rubberBand.x()
        self.parent().y_rb = self.parent().rubberBand.y()
        self.parent().w_rb = self.parent().rubberBand.width()
        self.parent().h_rb = self.parent().rubberBand.height()
        self.parent().ui.LineBoxTable.item(row,1).setText(str(int(round((self.parent().rubberBand.x() - int(self.parent().img_xoffset))/self.parent().scale))))
        self.parent().ui.LineBoxTable.item(row,2).setText(str(int(round((self.parent().rubberBand.y() - int(self.parent().img_yoffset))/self.parent().scale))))
        self.parent().ui.LineBoxTable.item(row,3).setText(str(int(round(self.parent().rubberBand.width()/self.parent().scale))))
        self.parent().ui.LineBoxTable.item(row,4).setText(str(int(round(self.parent().rubberBand.height()/self.parent().scale))))
        self.parent().ui.statusbar.showMessage(f'Resizing to x:{self.parent().x_rb} y:{self.parent().y_rb} w:{self.parent().w_rb} h:{self.parent().h_rb}')
        #super(ResizableRubberBand, self).resizeEvent(event)

########### Only run this code if actually running this application
if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec()
