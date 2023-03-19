# Python imports
import csv
import json
import os
import re
#import glob
import shutil
import sys
#import pyautogui
#from tempfile import NamedTemporaryFile
import pandas as pd
import json

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
from PyQt5.QtWidgets import  QSpinBox, QRubberBand, QWidget, QHBoxLayout, QSizeGrip, QMenu
from PyQt5.QtCore import QPoint, QRect, QSize, Qt
from PyQt5.QtGui import QPainter, QPen, QBrush


from queue import Queue
from ext import mainfind
from MyBoxerUI import Ui_Boxer
from Training import Train as tr
#from ProjectBrowserUI import Ui_Explorer
#from ProjectBrowser import MyFileBrowser
#from PyQt5.QtCore import QObject, QThread, pyqtSignal 
# Dialog Imports

from Dialogs.crop_greek_linesDialog import Ui_crop_greek_linesDialog
from Dialogs.crop_latin_linesDialog import Ui_crop_latin_linesDialog
from Dialogs.tif_greek_lines_renameDialog import Ui_tifgreekrenamelinesDialog
from Dialogs.tif_greek_lines_moveDialog import Ui_tifgreekmovelinesDialog
from Dialogs.tif_latin_lines_renameDialog import Ui_tiflatinrenamelinesDialog
from Dialogs.tif_latin_lines_moveDialog import Ui_tiflatinmovelinesDialog
from Dialogs.ImageTextPairDialog import Ui_ImageTextPairDialog
from Dialogs.split_greek_text_linesDialog import Ui_splitgreektextlinesDialog
from Dialogs.rename_greek_text_linesDialog import Ui_renamegreektextlinesDialog

# The new Stream Object which replaces the default stream associated with sys.stdout
# This object just puts data in a queue!
class WriteStream(object):
    def __init__(self,queue):
        self.queue = queue

    def write(self, text):
        self.queue.put(text)

    def flush(self):
        """
        Stream flush implementation
        """
        pass
    
# A QObject (to be run in a QThread) which sits waiting for data to come through a Queue.Queue().
# It blocks until data is available, and once it has got something from the queue, it sends
# it to the "MainThread" by emitting a Qt Signal

class ThreadConsoleTextQueueReceiver(qtc.QObject):
    
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
        self.queue_element_received_signal.emit('---> Console text queue reception Stopped <---\n')

'''
class Logging(qtc.QObject):
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

class MainWindow(qtw.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # pre-compiled QtDesigner Ui_MainUI and extended slots code starts here:        
        # load the pre-compiled QtDesigner Ui_MainUI user interface
        self.ui = Ui_Boxer()
        self.ui.setupUi(self)
        
        self.ui.actionBatchCrop_Greek_to_tif_Lines_tb.triggered.connect(self.actionCrop_Greek_To_tiff_Lines)
        self.ui.actionRename_Greek_tif_Lines_tb.triggered.connect(self.actionRename_Greek_tiff_Lines)
        self.ui.actionMove_Greek_tif_Lines_tb.triggered.connect(self.actionMove_Greek_tiff_Lines)
        
        self.ui.actionAutoCrop_Latin_To_tif_Lines_tb.triggered.connect(self.actionCrop_Latin_To_tiff_Lines)
        self.ui.actionRename_Latin_tif_Lines_tb.triggered.connect(self.actionRename_Latin_tiff_Lines)
        self.ui.actionMove_Latin_tif_Lines_tb.triggered.connect(self.actionMove_Latin_tiff_Lines)
        
        self.ui.actionSplitGreek_text_lines_tb.triggered.connect(self.actionSplitGreek_text_lines)
        self.ui.actionRenameGreek_text_lines_tb.triggered.connect(self.actionRenameGreek_text_lines)
        
        self.ui.actionSplit_Latin_Text_Lines_tb.triggered.connect(self.actionSplit_Latin_Text_Lines)
        self.ui.actionRename_Latin_Text_Lines_tb.triggered.connect(self.actionRename_Latin_Text_Lines)
        
        self.ui.actionFind_and_Replace.triggered.connect(mainfind.Find(self).show)
        self.ui.actionToggle_Greek_Toolbars.triggered.connect(self.toggleGreekToolbars)
        self.ui.actionToggle_Latin_Toolbars.triggered.connect(self.toggleLatinToolbars)

        self.ui.actionProject_Explorer.triggered.connect(self.OpenProjectExplorer)
        
        self.ui.actionMake_Greek_LineBox_File_Pair.triggered.connect(self.linebox_make_split)
        self.ui.actionEdit_Greek_LineBox_Pair.triggered.connect(self.linebox_edit_split)
        self.ui.actionDraw_Table_LineBox_tb.triggered.connect(self.putSbLineBox)
        self.ui.actionDraw_Selected_LineBox_tb.triggered.connect(self.getRbLineBox)
        #self.ui.actionEdit_Latin_LineBox_Pair.triggered.connect(self.linebox_edit_split)

        self.ui.OpenImageFilebutton.clicked.connect(self.loadImage)
        self.ui.MyPixlerbutton.clicked.connect(self.OpenWithMyPixler)
        #self.ui.CharBoxImagebutton.clicked.connect(self.loadcharboximage)
        #self.ui.WordBoxImagebutton.clicked.connect(self.loadwordboximage)        
    
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
        self.ui.textButton.clicked.connect(self.editText)
        self.ui.tableButton.clicked.connect(self.editTable)
        self.ui.reloadImagebutton.clicked.connect(self.ReloadImage)
        self.ui.BoxTable.customContextMenuRequested.connect(self.openTableMenu)
        self.ui.reloadTextbutton.clicked.connect(self.ReloadText)
        self.ui.fontComboBox.currentFontChanged.connect(self.on_font_update)
        self.ui.fontSizeBox.valueChanged.connect(self.on_font_update)
        self.ui.OCRModelComboBox.currentTextChanged.connect(self.on_lang_select)

        self.ui.bookComboBox.currentTextChanged.connect(self.selectBookCombo)

        # UI and slots code ends here.
        
        # Show the Main user interface
        self.ui.BoxDocument = qtg.QTextDocument(self.ui.BoxText)
        font = qtg.QFont()
        font.setFamily("FROMVS [MAXR]")
        font.setPointSize(20)
        self.ui.BoxDocument.setDefaultFont(font)
        
        self.ui.BoxDocument.setDefaultFont(font)
        self.ui.BoxBlockFormat = qtg.QTextBlockFormat()
        self.ui.BoxTextFormat = qtg.QTextFormat()
        self.ui.BoxCursor = qtg.QTextCursor(self.ui.BoxDocument)
        
        self.ui.BoxText.setDocument(self.ui.BoxDocument)

        #ChrRefText = open('/home/jetson/Projects/BiblionOCR/ViewController/Application/3-ConductOCR/FROMVS ChrReference.txt').read()
        #self.ui.ChrRefplainTextEdit.setPlainText(ChrRefText)

        #self.imgdir = r"/home/jetson/Projects/BiblionOCR/Model/Images/Complete/Greek/tif_greek_pages/greek_book_41_Mark/"

        # Restore BoxerSession settings
        self.get_session_settings()

        self.origpixmap = None
        self.dirIterator = None
        self.imgfileList = []
        self.txtfileList = []
        self.imgdir = ""
        self.imgpath = ""
        #self.ui.bookComboBox.setCurrentText(self.bookabbr)
        print('current book:',self.bookabbr)

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
        self.toggleLatinToolbars()
 
 
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
    
    #custom method to write anything printed out to console/terminal to my QTextEdit widget via append function.
    def output_terminal_written(self, text):
        self.ui.OutputText.append(text)

    def get_session_settings(self):
        # get session settings
        # Define json data        
        print("loading session")
        with open('/home/jetson/Projects/BiblionOCR/Model/Project/Data/json/BoxerSession.json') as f:
            # returns JSON object as a dictionary
            data = json.load(f)
            
            # Set json key values
            ocrlang_key = r"self.ocrlang"
            ocrmodel_key = r"self.ocrmodel"
            tessdatadir_key = r"self.tessdatadir"
            tesseract_key = r"self.tesserac"
            tesstrain_key = r"self.tesstrain"
            bookabbr_key = r"self.bookabbr"
            chapter_key = r"self.chapter"
            verse_key = r"self.verse"
            word_key = r"self.word"
            chr_key = r"self.chr"
            font_key = r"self.font"
            fontsize_key = r"self.fontsize"
            linespacing_key = r"self.linespacing"
            source_book_markdown_key = r"self.sourcebookmarkdown"
            greek_book_markdown_key = r"self.greekbookmarkdown"
            latin_book_markdown_key = r"self.latinbookmarkdown"
            sourcefile_key = r"self.sourcefile"
            firstpage_key = r"self.firstpage"
            lastpage_key = r"self.lastpage"            
            deltapages_key = r"self.deltapages"
            imgpath_key = r"self.imgpath"
            imgdir_key = r"self.imgdir"
            dirIterator_key = r"self.dirIterator"
            imgfileList_key = r"self.imgfileList"
            pixmap_key = r"self.pixmap"
            qimage_key = r"self.qimage"
            zoom_key = r"self.zoom"
            zoomslidervalue_key = r"self.zoomslidervalue"
            img_xoffset_key = r"self.img_xoffset"
            img_yoffset_key = r"self.img_yoffset"
            txtpath_key = r"self.txtpath"
            txtdir_key = r"self.txtdir"
            txtfileList_key = r"self.txtfileList"
            txtgreeklinebox_key = r"self.txtgreeklinebox"
            jsongreeklinebox_key = r"self.jsongreeklinebox"
            txtlatinlinebox_key = r"self.txtlatinlinebox"
            glyph_key = r"self.glyph"
            glyphname_key = r"self.glyphname"
            glyphencode_key = r"self.glyphencode"
            greekpages_key = r"self.greekpages"
            greeklinesbox_key = r"self.greeklinesbox"
            greeklinesautosplit_key = r"self.greeklinesautosplit"
            latinpages_key = r"self.latinpages"
            latinlinesbox_key = r"self.latinlinesbox"
            latinlinesautosplit_key = r"self.latinlinesautosplit"

            print(bookabbr_key,chapter_key)
            # Find the json key values using 'in' operator
            # Define session variables from json key values
            for Setting in data:
                print('Setting: ',Setting['Setting'],Setting['CurrentValue'])
                
                if Setting['Setting'] == ocrlang_key:
                    self.ocrlang = Setting['CurrentValue']
                    self.ui.OCRlangComboBox.setCurrentText(self.ocrlang)
                elif Setting['Setting'] == ocrmodel_key:
                    self.ocrmodel = Setting['CurrentValue']
                    self.ui.OCRModelComboBox.setCurrentText(self.ocrmodel)              
                elif Setting['Setting'] == tessdatadir_key:
                    self.tessdatadir = Setting['CurrentValue']
                elif Setting['Setting'] == tesseract_key:
                    self.tesseract = Setting['CurrentValue']
                elif Setting['Setting'] == tesstrain_key:
                    self.tesstrain = Setting['CurrentValue']
                elif Setting['Setting'] == bookabbr_key:  
                    self.bookabbr = Setting['CurrentValue']
                    self.ui.bookComboBox.setCurrentText(self.bookabbr)            
                elif Setting['Setting'] == chapter_key:  
                    self.chapter = Setting['CurrentValue']          
                elif Setting['Setting'] == verse_key:
                    self.verse = Setting['CurrentValue']
                elif Setting['Setting'] == word_key:
                    self.word = Setting['CurrentValue'] 
                elif Setting['Setting'] == chr_key:
                    self.chr = Setting['CurrentValue']
                elif Setting['Setting'] == font_key:
                    self.font = Setting['CurrentValue']
                    self.ui.fontComboBox.setCurrentText(self.font)
                elif Setting['Setting'] == fontsize_key:
                    self.fontsize = Setting['CurrentValue']
                    self.ui.fontSizeBox.setValue(int(self.fontsize))           
                elif Setting['Setting'] == linespacing_key:
                    self.linespacing = Setting['CurrentValue']
                    self.ui.LHlineEdit.setText(self.linespacing)
                elif Setting['Setting'] == source_book_markdown_key:  
                    self.sourcebookmarkdown = Setting['CurrentValue']
                elif Setting['Setting'] == greek_book_markdown_key:  
                    self.greekbookmarkdown = Setting['CurrentValue']
                elif Setting['Setting'] == latin_book_markdown_key:  
                    self.latinbookmarkdown = Setting['CurrentValue']
                elif Setting['Setting'] == sourcefile_key:   
                    self.sourcefile = Setting['CurrentValue']
                elif Setting['Setting'] == firstpage_key:  
                    self.firstpage = Setting['CurrentValue']
                elif Setting['Setting'] == lastpage_key:  
                    self.lastpage = Setting['CurrentValue']
                elif Setting['Setting'] == deltapages_key:
                    self.deltapages = Setting['CurrentValue']
                elif Setting['Setting'] == imgpath_key:
                    self.imgpath = Setting['CurrentValue']
                elif Setting['Setting'] == imgdir_key:  
                    self.imgdir = Setting['CurrentValue']
                elif Setting['Setting'] == dirIterator_key:  
                    self.dirIterator = Setting['CurrentValue']
                elif Setting['Setting'] == imgfileList_key:  
                    self.imgfileList = Setting['CurrentValue']
                elif Setting['Setting'] == pixmap_key:  
                    self.pixmap = Setting['CurrentValue']
                elif Setting['Setting'] == qimage_key:  
                    self.qimage = Setting['CurrentValue']
                elif Setting['Setting'] == zoom_key:  
                    self.zoom = Setting['CurrentValue']
                    self.ui.ZoomComboBox.setCurrentText(self.zoom)
                elif Setting['Setting'] == zoomslidervalue_key:
                    self.zoomslidervalue = Setting['CurrentValue']
                    self.ui.Zoomslider.setValue(int(self.zoomslidervalue))
                elif Setting['Setting'] == img_xoffset_key:
                    self.img_xoffset = Setting['CurrentValue']
                elif Setting['Setting'] == img_yoffset_key:
                    self.img_yoffset = Setting['CurrentValue']
                elif Setting['Setting'] == txtpath_key:  
                    self.txtpath = Setting['CurrentValue'] 
                elif Setting['Setting'] == txtgreeklinebox_key:  
                    self.txtgreeklinebox = Setting['CurrentValue']
                elif Setting['Setting'] == jsongreeklinebox_key:  
                    self.jsongreeklinebox = Setting['CurrentValue']
                elif Setting['Setting'] == txtlatinlinebox_key:  
                    self.txtlatinlinebox = Setting['CurrentValue']
                elif Setting['Setting'] == txtdir_key:  
                    self.txtdir = Setting['CurrentValue']
                elif Setting['Setting'] == greekpages_key:  
                    self.greekpages = Setting['CurrentValue']
                elif Setting['Setting'] == greeklinesbox_key:  
                    self.greeklinesbox = Setting['CurrentValue']
                elif Setting['Setting'] == greeklinesautosplit_key:  
                    self.greeklinesautosplit = Setting['CurrentValue']
                elif Setting['Setting'] == latinpages_key:  
                    self.latinpages = Setting['CurrentValue']
                elif Setting['Setting'] == latinlinesbox_key:  
                    self.latinlinesbox = Setting['CurrentValue']
                elif Setting['Setting'] == latinlinesautosplit_key:  
                    self.latinlinesautosplit = Setting['CurrentValue']
                
                print('New Setting: ',Setting['Setting'],Setting['CurrentValue'])
            f.close()

    def get_workflow_settings(self):

        # Opening JSON file
        with open('/home/jetson/Projects/BiblionOCR/Model/SQLite/json/Workflow.json') as f:
            # returns JSON object as
            # a dictionary
            data = json.load(f)
        
        # Iterating through the json
        # list
        for Sequence in data:
            print(Sequence['Sequence'], Sequence['DialogUi'],Sequence['DefaultSource'])
        
        # Closing file
        f.close()
    
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
                with open('/home/jetson/Projects/BiblionOCR/Model/Project/Data/json/Workflow.json') as f:
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
                                workflow_box_folder = Sequence['WorkflowFullPath']+r'/'
                                complete_box_folder = Sequence['CompleteFullPath']+r'/'+self.sourcebookmarkdown+r'/'
                            elif step == "GL2":
                                self.crop_greeklines_ui.SourceLineEdit.setText(Sequence['DefaultSource']+r'/')
                                source_folder = Sequence['DefaultSource']+r'/'
                                self.crop_greeklines_ui.DestGreekLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                                workflow_dest_folder = Sequence['WorkflowFullPath']+r'/'
                                complete_dest_folder = Sequence['CompleteFullPath']+r'/'+self.sourcebookmarkdown+r'/'                                
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
            with open('/home/jetson/Projects/BiblionOCR/Model/Project/Data/json/Workflow.json') as f:
                # returns JSON object as
                # a dictionary
                data = json.load(f)
                # Search the key value using 'in' operator
                for Sequence in data:
                    print(Sequence['Sequence'])
                    if Sequence['Sequence'] == seq:
                        # set source line edit to default workflow folder
                        source_folder = Sequence['DefaultSource']+r'/'
                        workflow_folder = Sequence['WorkflowFullPath']+r'/'
                        complete_folder = Sequence['CompleteFullPath']+r'/'
                        self.greekrenamelines_ui.SourceLineEdit.setText(source_folder)
                        self.greekrenamelines_ui.DestinationLineEdit.setText(workflow_folder)
                        print(source_folder,workflow_folder,complete_folder)


        rsp = self.tifgreekrenamelinesDialog.exec_()
        

            
        print("completed renaming Greek tif lines for ground truth")
        # tr.renameimages(r"/home/jetson/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_40_Matthew/", "/home/jetson/Projects/Python/Images/Greek/tif_greek_tif4groundtruth/")
        # tr.renameimages(r"/home/jetson/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_41_Mark/", "/home/jetson/Projects/Python/Images/Greek/tif_greek_tif4groundtruth/")    

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
        
        # tr.renameimages(r"/home/jetson/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_40_Matthew/", "/home/jetson/Projects/Python/Images/Greek/tif_greek_tif4groundtruth/")
        #tr.renameimages("/home/jetson/Projects/Python/Images/Greek/tif_greek_tif4groundtruth/", "/home/jetson/Projects/Python/Images/Greek/tif_greek_tif2groundtruth/")
        #pass

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
                with open('/home/jetson/Projects/BiblionOCR/Model/Project/Data/json/Workflow.json') as f:
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
                                source_folder = Sequence['DefaultSource']+r'/'+self.greekbookmarkdown+r'/'
                                self.split_greeklines_ui.DestinationLineEdit.setText(Sequence['WorkflowFullPath']+r'/'+self.greekbookmarkdown+r'/')
                                workflow_dest_folder = Sequence['WorkflowFullPath']+r'/'+self.greekbookmarkdown+r'/'
                                complete_dest_folder = Sequence['CompleteFullPath']+r'/'+self.greekbookmarkdown+r'/'                                
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
                with open('/home/jetson/Projects/BiblionOCR/Model/Project/Data/json/Workflow.json') as f:
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
                                source_folder = Sequence['DefaultSource']+r'/'+self.greekbookmarkdown+r'/'
                                self.rename_greeklines_ui.DestinationLineEdit.setText(Sequence['WorkflowFullPath']+r'/'+self.greekbookmarkdown+r'/')
                                workflow_dest_folder = Sequence['WorkflowFullPath']+r'/'+self.greekbookmarkdown+r'/'
                                complete_dest_folder = Sequence['CompleteFullPath']+r'/'+self.greekbookmarkdown+r'/'                                
                f.close()
            
        rsp = self.rename_greek_text_linesDialog.exec_()
        print("completed renaming Greek textlines for ground truth review")
        #tr.sortcroplines(r"/home/jetson/Projects/Python/Images/Greek/png_greek_deskew/greek_book_41_Mark/","/home/jetson/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_41_Mark/","/home/jetson/Projects/Python/Images/Greek/tif_greek_linebox/greek_book_41_Mark/")

    # Mouse Controllers
    def mousePressEvent(self, event):
    
        #if event.button() == Qt.LeftButton and self.mode == "RbEdit":
        if event.button() == Qt.LeftButton:
            print(f'Mouse Press Position:{event.pos()}')
            event_pos_str = str(event.pos())
            print(f'Mouse Press Position Str:{event_pos_str}')
            event_pos_str = event_pos_str.split("(")
            print(f'Mouse Press Position Splitstr:{event_pos_str}')
            event_pos_repstr = event_pos_str[1].replace(")","")
            event_pos_repstr = event_pos_str[1].replace(",","")
            print(f'Mouse Press Position Replacestr:{event_pos_repstr}')  
            event_xy_str_split = event_pos_repstr.split()
            print(f'Mouse Press Position Splitstr:{event_xy_str_split}')
            event_xstr = event_xy_str_split[0]
            event_ystr = event_xy_str_split[1].replace(")","")
            print(f'Event X Str: {event_xstr}  Event Y Str: {event_ystr}')

            #self.origin_x = int(self.img_xoffset)
            #self.origin_y = int(self.img_yoffset)
            self.event_x = int(event_xstr)
            self.event_y = int(event_ystr)
            if self.event_x <= int(self.img_xoffset)-1:
                self.event_x = int(self.img_xoffset)
            if self.event_y <= int(self.img_yoffset)-1:
                self.event_y = int(self.img_yoffset)
            
            self.rubberBand = ResizableRubberBand(self)
            self.start_pos = QPoint(self.event_x, self.event_y)
            self.rubberBand.setGeometry(QRect(self.start_pos, QSize()).normalized())
            self.rubberBand.show()

    def mouseMoveEvent(self, event):
        #self.start_pos = QPoint(self.origin_x + self.event_x, self.origin_y + self.event_y)
        #if self.mode == "RbEdit":
        self.end_pos = event.pos()
        self.rubberBand.setGeometry(QRect(self.start_pos, self.end_pos).normalized())

    def mouseReleaseEvent(self, event):
    
        #if event.button() == Qt.LeftButton and self.mode == "RbEdit":
        if event.button() == Qt.LeftButton:
            geo = self.rubberBand.geometry()
            self.x_rb = self.rubberBand.x()
            self.y_rb = self.rubberBand.y()
            self.w_rb = self.rubberBand.width()
            self.h_rb = self.rubberBand.height()
            print("selection x = " + str(self.x_rb))
            print("selection w = " + str(self.w_rb))
            print("selection y = " + str(self.y_rb))
            print("selection h = " + str(self.h_rb))
            print("selection x+w = " + str(self.x_rb+self.w_rb))
            print("selection y+h = " + str(self.y_rb+self.h_rb))
            print(self.x_rb,":",self.x_rb+self.w_rb,",",self.y_rb,":",self.y_rb+self.h_rb)

            self.currentQRect = self.rubberBand.geometry()

    # Page Toolbar Actions

    def actionRenameGreek_text_lines_old(self):
        print("renaming Greek textlines for ground truth")
        # usage: tr.text2groundtruth(source, destination)
        #tr.text2groundtruth(r"/home/jetson/Projects/Python/EstablishTruth/Greek lines4groundtruth/", "/home/jetson/Projects/Python/EstablishTruth/Greek lines2groundtruth/")
        tr.text2groundtruth(r"/home/jetson/Projects/BiblionOCR/Model/Text/EstablishTruth/Greek/txt_greek_lines_autosplit/greek_book_40_Matthew/", "/home/jetson/Projects/BiblionOCR/Model/Text/EstablishTruth/Greek/txt_greek_lines_autosplit/greek_book_40_Matthew/")
    
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
    
    def initBookCombo(self):

        # Opening JSON file
        with open('/home/jetson/Projects/BiblionOCR/Model/Project/Data/json/BooksAbbrName.json') as f:
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

    def toggleGreekToolbars(self):

        greekimgpagesstate = self.ui.GreekImagePagesToolBar.isVisible()
        greekimglinesstate = self.ui.GreekImageLinesBatchToolBar.isVisible()
        greektxtlinesstate = self.ui.GreekTextLinesBatchToolBar.isVisible()        
        
        # Set the visibility to its inverse
        self.ui.GreekImagePagesToolBar.setVisible(not greekimgpagesstate)
        self.ui.GreekImageLinesBatchToolBar.setVisible(not greekimglinesstate)
        self.ui.GreekTextLinesBatchToolBar.setVisible(not greektxtlinesstate)

    def toggleLatinToolbars(self):

        #latinimgpagesstate = self.ui.LatinImagePagesToolBar.isVisible()
        latinimglinesstate = self.ui.LatinImageLinesBatchToolBar.isVisible()
        latintxtlinesstate = self.ui.LatinTextLinesBatchToolBar.isVisible()        
        
        # Set the visibility to its inverse
        #self.ui.LatinImagePagesToolBar.setVisible(not latinimgpagesstate)
        self.ui.LatinImageLinesBatchToolBar.setVisible(not latinimglinesstate)
        self.ui.LatinTextLinesBatchToolBar.setVisible(not latintxtlinesstate)

    def selectBookCombo(self):
        oldbookabbr = self.bookabbr
        self.bookabbr = self.ui.bookComboBox.currentText()
        
        if self.ui.bookComboBox.currentText() != oldbookabbr:
                  
            jsonfile = '/home/jetson/Projects/BiblionOCR/Model/Project/Data/json/BooksMarkDown.json'
            
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
            
            jsonfile = '/home/jetson/Projects/BiblionOCR/Model/Project/Data/json/BoxerSession.json'
            
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
        # Convert frame ndarray to a QImage.
        self.qimage = qimage2ndarray.array2qimage(self.frame, normalize=True)
    
    def loadImage(self):
        imgdir = "/home/jetson/Projects/BiblionOCR/Model/Project/Images/Workflow"     
        self.imgpath = qtw.QFileDialog.getOpenFileName(self.ui.centralwidget, 'Open image file',imgdir,'Images (*.png *.xpm *.jpg *.bmp *.gif *.tif)')[0]
        self.getImage(self.imgpath)
    
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
            ipath = self.imgdir + "/" + i
            #ipath = os.path.join(self.imgdir, i)
            #ipath = ipath.replace(r'\\', '/')
            if os.path.isfile(ipath) and i.endswith(('.png', '.jpg', '.jpeg', '.tif')):
                self.imgfileList.append(ipath)
        self.sortImgFiles()
        self.showImage(self.imgpath)

    def showImage(self,imgpath):
        self.imgpath = imgpath
        if self.imgpath.endswith('.tif'):
            self.loadImageStackFromFile(self.imgpath)
            self.showFrame(0)
            self.origpixmap = qtg.QPixmap.fromImage(self.qimage)
            self.pixmap = qtg.QPixmap.fromImage(self.qimage).scaled(self.ui.Image.size(), 
                qtc.Qt.KeepAspectRatio)
        else:
            self.pixmap = qtg.QPixmap(self.imgpath).scaled(self.ui.Image.size(), 
                qtc.Qt.KeepAspectRatio)

        if self.pixmap.isNull():
            return
        
        self.on_zoom()

        #self.ui.Image.setPixmap(self.pixmap) -- moved out to resize_image

        self.imgdir = os.path.dirname(self.imgpath)

        jsonfile = '/home/jetson/Projects/BiblionOCR/Model/Project/Data/json/BoxerSession.json'
                
        with open(jsonfile, 'r') as f:
            data = json.load(f)
            imgpath_key = r"self.imgpath"
            imgdir_key = r"self.imgdir"
            for Setting in data:
                if Setting['Setting'] == imgpath_key:
                    Setting['CurrentValue'] = self.imgpath
                    print(Setting['CurrentValue'])
                elif Setting['Setting'] == imgdir_key:  
                    Setting['CurrentValue'] = self.imgdir
                    print(Setting['CurrentValue'])
        f.close()

        os.remove(jsonfile)
        with open(jsonfile, 'w') as f:
            json.dump(data, f, indent=4)
        f.close()

    def sortImgFiles(self):
        #print(f'Image File List: {self.imgfileList}')
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
        self.sorted_imgfilelist = sorted(self.imgfileList, key=alphanum_key)
        print(f'Sorted Image File List: {self.sorted_imgfilelist}')

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
        zoomValue = self.ui.Zoomslider.value()
        
    def DisableZoomSlider(self):
        self.ui.Zoomslider.hide()
        self.ui.Zoomslider.setEnabled(False)

    def MoveZoomSlider(self):
        self.ui.Zoomslider.setEnabled(True)
        self.ui.Zoomslider.setValue(int(self.ui.ZoomComboBox.currentText()[0]))

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
        seltext = self.ui.ZoomComboBox.currentText()
        if self.ui.Zoomslider.isEnabled():
            self.on_zoomslider()
        #elif seltext != "Best_Fit":
            #print("Best fit not selected")
        selnumtext = seltext.split(" ")
        print(selnumtext[0])
        self.scale = float(selnumtext[0])/100
        print(self.scale)
        
        self.resize_image()

    def resize_image(self):
        if self.qimage:
            self.origsize = self.origpixmap.size()       
            self.origheight = self.origpixmap.height
            self.origwidth = self.origpixmap.width
            scaled_pixmap = self.origpixmap.scaled(self.scale * self.origsize, qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)
            self.ui.Image.setPixmap(scaled_pixmap)

    def GetOCRText(self):
        my_OCR_rawtext = pytesseract.image_to_string(self.imgpath,lang="feg")
        self.ui.OCRText.insertPlainText(my_OCR_rawtext)

    def CropGreekLinesDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select tif pages source folder"))

        if self.directory:
            self.crop_greeklines_ui.SourceLineEdit.setText(self.directory+r'/')

    def GreekLineBoxFolderDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select linebox destination folder"))
        
        if self.directory:
            self.crop_greeklines_ui.GreekBoxFolderLineEdit.setText(self.directory+r'/')

    def DestGreekLinesDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select Greek lines destination folder"))
        
        if self.directory:
            self.crop_greeklines_ui.DestGreekLineEdit.setText(self.directory+r'/')

    def CropLatinLinesDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select tif pages source folder"))

        if self.directory:
            self.crop_greeklines_ui.SourceLineEdit.setText(self.directory+r'/')

    def LatinLineBoxFolderDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select linebox destination folder"))
        
        if self.directory:
            self.crop_greeklines_ui.LatinBoxFolderLineEdit.setText(self.directory+r'/')

    def DestLatinLinesDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select Greek lines destination folder"))
        
        if self.directory:
            self.crop_greeklines_ui.DestGreekLineEdit.setText(self.directory+r'/')            

    def GreekRenameLinesDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select rename tif Greek lines source folder"))

        if self.directory:
            self.greekrenamelines_ui.SourceLineEdit.setText(self.directory+r'/')

    def DestGreekRenameLinesDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select rename Greek lines destination folder"))
        
        if self.directory:
            self.greekrenamelines_ui.DestinationLineEdit.setText(self.directory+r'/')

    def SplitGreekTextLinesDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select Greek text pages source folder"))

        if self.directory:
            self.split_greeklines_ui.SourceLineEdit.setText(self.directory+r'/')

    def DestGreekTextLinesDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select Greek text lines destination folder"))
        
        if self.directory:
            self.split_greeklines_ui.DestinationLineEdit.setText(self.directory+r'/')  

    def RenameGreekTextLinesDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select Greek text pages source folder"))

        if self.directory:
            self.rename_greeklines_ui.SourceLineEdit.setText(self.directory+r'/')

    def DestRenameGreekTextLinesDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select Greek text lines destination folder"))
        
        if self.directory:
            self.rename_greeklines_ui.DestinationLineEdit.setText(self.directory+r'/')  
    
    def editText(self):
        if self.ui.textButton.isChecked():
            self.ui.stackedWidget.setCurrentIndex(0)

    def editTable(self):
        if self.ui.tableButton.isChecked():
            self.ui.stackedWidget.setCurrentIndex(1)   
    
    def loadText(self):

        self.txtpath = qtw.QFileDialog.getOpenFileName(
            self.ui.centralwidget, 'Open text file', '/home/jetson/Projects/BiblionOCR/Model/Project/Text/EstablishTruth/Greek/txt_greek_lines_autosplit/','Text files (*.txt)')[0]
    
        self.getText(self.txtpath)

    def getText(self,textpath):
            self.txtpath = textpath
            self.txtdirname = os.path.dirname(self.txtpath)
            #create file list 
            if self.txtpath:
                #self.ui.BoxText.setText(os.path.basename(self.txtpath))       
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
                self.ui.BoxText.clear()
                if info.completeSuffix() == 'txt':
                    #self.ui.editor_text.setHtml(text
                    self.ui.BoxText.insertPlainText(text)
                else:
                    self.ui.BoxText.setPlainText(text)
            #textfile.close()
            #txtdirpath = os.path.dirname(self.txtpath)

            # update font to selection and size       
            self.on_font_update()
            
            # update line spacing
            self.SetLineSpacing()
            file.close()
       
        jsonfile = '/home/jetson/Projects/BiblionOCR/Model/Project/Data/json/BoxerSession.json'
        
        with open(jsonfile, 'r') as f:
            data = json.load(f)
            txtpath_key = r"self.txtpath"
            txtdir_key = r"self.txtdir"
            for Setting in data:
                if Setting['Setting'] == txtpath_key:
                    Setting['CurrentValue'] = self.txtpath
                    print(Setting['CurrentValue'])
                elif Setting['Setting'] == txtdir_key:  
                    Setting['CurrentValue'] = self.txtdir
                    print(Setting['CurrentValue'])
        f.close()

        os.remove(jsonfile)
        with open(jsonfile, 'w') as f:
            json.dump(data, f, indent=4)
        f.close()

    def sortTextFiles(self):
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
        self.sorted_txtfilelist = sorted(self.txtfileList, key=alphanum_key)     

    def nextText(self):
        if self.textpath:
            self.textpath = self.sorted_txtfilelist[(self.sorted_txtfilelist.index(self.textpath) + 1) % len(self.sorted_txtfilelist)]
            self.ui.TextFileName.setText(os.path.basename(self.textpath))
            self.getText(self.textpath)

    def prevText(self):
        if self.textpath:
            self.textpath = self.sorted_txtfilelist[(self.sorted_txtfilelist.index(self.textpath) - 1) % len(self.sorted_txtfilelist)]
            self.ui.TextFileName.setText(os.path.basename(self.textpath))
            self.getText(self.textpath)

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
                self.ui.BoxText.clear()
                if info.completeSuffix() == 'txt':
                    #self.ui.editor_text.setHtml(text
                    self.ui.BoxText.insertPlainText(text)
                else:
                    self.ui.BoxText.setPlainText(text)
                
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
                
        '''num,ok = qtw.QInputDialog.getInt(self.ui.centralwidget,"Proportional Line Spacing","Enter a percent value from 0-200")  
        
        if ok:
            lineSpacing = num
        else:
            lineSpacing = 145'''

        lineSpacing = self.ui.LHslider.value()
        self.ui.LHlineEdit.setText(str(lineSpacing))
            
        cursor = self.ui.BoxText.textCursor()
        if not cursor.hasSelection():
            cursor.select(qtg.QTextCursor.Document)
        bf = self.ui.BoxCursor.blockFormat()
        bf.setLineHeight(lineSpacing, self.ui.BoxBlockFormat.ProportionalHeight) 
        cursor.mergeBlockFormat(bf)
    
    def SaveRawTextFileDialog(self, MainWindow):
        path = qtw.QFileDialog.getSaveFileName(
            self.ui.centralwidget, 'Save Raw text file',self.txtdir,
            'Text files (*.txt)')[0]
        with open(path, 'w') as file:
            my_RawText = self.ui.BoxDocument.toPlainText()
            file.write(my_RawText)
        filename = os.path.basename(path)
        self.ui.TextLE.setText(filename)
        file.close()
        
    def SaveAsCorrectedTextFileDialog(self, MainWindow):
        path = qtw.QFileDialog.getSaveFileName(
            self.ui.centralwidget, 'Save Corrected text file', self.txtdir,
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
                self.ui.centralwidget, 'Save Corrected text file', '',
                'Text files (*.txt)')[0]
            filename = os.path.basename(path)
        with open(path, 'w') as file:
            my_CorrectedText = self.ui.BoxDocument.toPlainText()
            file.write(my_CorrectedText)
        
        self.ui.TextLE.setText(filename)
        file.close()

    def OpenProjectExplorer(self):
        mw_cmd = "python3 /home/jetson/Projects/BiblionOCR/ViewController/Application/0-MainUI/ProjectBrowser.py"
        print(mw_cmd)
        os.system(mw_cmd)
        '''newapp = qtw.QApplication([])
        dirPath = r'/home/jetson/Projects/BiblionOCR/'
        self.explorer = qtw.QMainWindow()
        self.ui = Ui_Explorer()
        self.ui.setupUi(self.explorer)
        fb = MyFileBrowser()
        fb.show()
        #self.explorer.show()
        newapp.exec_()'''
    
    def OpenWithMyPixler(self):
        mw_cmd = "python3 /home/jetson/Projects/BiblionOCR/ViewController/Application/0-MainUI/MyPixler.py"
        print(mw_cmd)
        os.system(mw_cmd)

    def OpenWithMyWriter(self):
        
        mw_cmd = "python3 /home/jetson/Projects/BiblionOCR/ViewController/Application/0-MainUI/MyWriter.py"
        print(mw_cmd)
        os.system(mw_cmd)
        '''
        writer.MainWindow = qtw.QMainWindow()
        writer.ui = writer.Ui_MyWriterUI()
        writer.ui.setupUi(writer.MainWindow)
        writer.MainWindow.show()'''

    def on_font_update(self):
        # update font to selection and size       
        #font = qtg.QFont()
        #font.setFamily(self.ui.fontComboBox.currentFont())
        #print(self.ui.fontComboBox.currentFont())
        font = qtg.QFont(self.ui.fontComboBox.currentFont())
        font.setPointSize(self.ui.fontSizeBox.value())
        #font = qtg.QFont(self.font)
        #font.setPointSize(int(self.fontsize))
        
        self.ui.BoxText.setFont(font)

    def on_lang_select(self):
        pass

    def loadcharboximage(self):
        '''Load Character Box Image'''
        img = cv2.imread(self.imgpath)
        self.imgdir = os.path.dirname(self.imgpath)
        filestr = os.path.basename(self.imgpath)
        os.path.splitext(filestr)            
        filesplit = os.path.splitext(filestr)
        filename = filesplit[0]
        fileext = filesplit[1]

        self.charboxcsvdir = "/home/jetson/Projects/BiblionOCR/Model/Project/Data/csv/"
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
        font = ImageFont.truetype("/home/jetson/Projects/BiblionOCR/ViewController/Application/0-MainUI/fonts/FROMVS.ttf", 8) 
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
            self.ui.BoxText.clear()
            self.ui.BoxText.insertPlainText(file_.read())
            self.ui.TextLE.setText(f"{filename}_charbox.txt")
        self.charboximagepath = f"/home/jetson/Projects/BiblionOCR/Model/Images/Complete/Greek/tif_greek_box/{filename}_charbox.tif"
        self.charboximage = pil_im.save(self.charboximagepath) 
        self.ui.ImageLe.setText(f"{filename}_charbox.tif")
        self.showImage(self.charboximagepath)
        #image = ImageQt.ImageQt(pil_im)
        #self.pixmap = qtg.QPixmap(image)

        #self.ui.Image.setPixmap(pixmap)
        #print(pytesseract.image_to_boxes(img,lang="feg"))'''

        #cv2.imshow("CV Image", img)
        #cv2.waitKey(0)

    def loadwordboximage(self):
        '''Load Word Box Image'''
        img = cv2.imread(self.imgpath)
        self.imgdir = os.path.dirname(self.imgpath)
        filestr = os.path.basename(self.imgpath)
        os.path.splitext(filestr)            
        filesplit = os.path.splitext(filestr)
        filename = filesplit[0]
        fileext = filesplit[1]

        self.wordboxcsvdir = "/home/jetson/Projects/BiblionOCR/Model/Project/Data/csv/"
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
        #self.ui.BoxText.insertPlainText(wordboxes)
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
            self.ui.BoxText.clear()
            self.ui.BoxText.insertPlainText(file_.read())
            self.ui.TextLE.setText(f"{filename}_wordbox.txt")
        self.wordboximagepath = f"/home/jetson/Projects/BiblionOCR/Model/Images/Complete/Greek/tif_greek_box/{filename}_wordbox.tif"
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
        self.wordboxcsvdir = "/home/jetson/Projects/BiblionOCR/Model/Project/Data/csv/"
        wordboxcsvpath = self.wordboxcsvdir + filename + r"_wordbox.csv"
        with open(wordboxcsvpath, mode='r') as file_:
            self.ui.BoxText.clear()
            wordboxes = file_.read()
            self.ui.BoxText.insertPlainText(wordboxes)
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
    
    # Initialize LineBox Methods
    
    def on_rowSelection(self):
        self.ui.BoxTable.selectionModel().selectionChanged.disconnect(self.on_rowSelectionChanged)
        def do_Rb():
            self.mode = "RbEdit"
            self.ui.actionDraw_Selected_LineBox_tb.setEnabled(True)
            self.ui.actionDraw_Table_LineBox_tb.setEnabled(False)
            #self.resetLineBox()
            self.drawWhiteLineBox()
            self.on_deselection()
            print('Editing LineBox image using mouse')
        def do_Sb():
            self.mode = "SbEdit"
            print('Editing LineBox image using spinboxes')
            self.ui.actionDraw_Table_LineBox_tb.setEnabled(True)
            self.ui.actionDraw_Selected_LineBox_tb.setEnabled(False)
            self.spinbox = QSpinBox(None) #changed parent from None to self.ui.BoxTable - could also be just self
            self.spinbox.setMaximum(6000)
            self.spinbox.valueChanged.connect(self.onValueChanged)
            self.getSbLineBox()
        def do_Pass():
            #self.mode = "Select"
            pass
        
        popup = qtw.QMessageBox(self)
        popup.setIcon(qtw.QMessageBox.Information)
        popup.setWindowTitle("Edit Mode")
        popup.setText("Select a linebox editing function")
        #popup.setInformativeText("Select a method for modifying the selected linebox")
        
        mouseButton = popup.addButton('Mouse Edit', qtw.QMessageBox.YesRole)
        mouseIcon = qtg.QIcon()
        mouseIcon.addPixmap(qtg.QPixmap(":/Icons/Icons//draw-rectangle-diagonally-16.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        mouseButton.setIcon(mouseIcon)
        tableButton = popup.addButton('Table Edit', qtw.QMessageBox.YesRole)
        tableIcon = qtg.QIcon()
        tableIcon.addPixmap(qtg.QPixmap(":/Icons/Icons/table-small.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        tableButton.setIcon(tableIcon)
        #popup.addButton(qtw.QPushButton('Cancel'), qtw.QMessageBox.ActionRole)
        insertAButton = popup.addButton('Insert Above', qtw.QMessageBox.YesRole)
        insertAIcon = qtg.QIcon()
        insertAIcon.addPixmap(qtg.QPixmap(":/Icons/Icons/insertabove.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        insertAButton.setIcon(insertAIcon)
        insertBButton = popup.addButton('Insert Below', qtw.QMessageBox.YesRole)
        insertBIcon = qtg.QIcon()
        insertBIcon.addPixmap(qtg.QPixmap(":/Icons/Icons/insertbelow.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        insertBButton.setIcon(insertBIcon)
        deleteButton = popup.addButton('Delete Row', qtw.QMessageBox.RejectRole)
        deleteIcon = qtg.QIcon()
        deleteIcon.addPixmap(qtg.QPixmap("/home/jetson/Projects/BiblionOCR/ViewController/Application/0-MainUI/Icons/cross-small.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        deleteButton.setIcon(deleteIcon)
        cancelButton = popup.addButton('Cancel', qtw.QMessageBox.RejectRole)
        #cancelIcon = qtg.QIcon()
        #cancelIcon.addPixmap(qtg.QPixmap("/home/jetson/Projects/BiblionOCR/ViewController/Application/0-MainUI/Icons/cross-small.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        #cancelButton.setIcon(cancelIcon)
        popup.exec()
        if popup.clickedButton() == mouseButton:
            do_Rb()
        elif popup.clickedButton() == tableButton:
            do_Sb()
        elif popup.clickedButton() == insertAButton:
            #
            location = "above"
            self.insertRow(location)
            #self.insertRowAbove()
            self.renumberRows()
            self.BoxTable2csv()
            #
            #
        elif popup.clickedButton() == insertBButton:
            #
            location = "below"
            self.insertRow(location)
            #self.insertRowBelow()
            self.renumberRows()
            self.BoxTable2csv()
            #
            #
        elif popup.clickedButton() == deleteButton:
            #
            self.deleteRow()
            self.renumberRows()
            self.BoxTable2csv()
            #
            #
        elif popup.clickedButton() == cancelButton:
            do_Pass()
        else:
            pass

    def on_rowSelectionChanged(self):
        self.mode = "edit"
        self.ui.BoxTable.setSortingEnabled(False)
        self.row_selected = self.ui.BoxTable.currentRow()        
        print("Editing BoxTable selection")
        self.ui.ZoomComboBox.setCurrentText('11 %')        
        self.ui.BoxTable.setSortingEnabled(True)
        self.on_rowSelection()

    def BoxTable2csv(self):
        self.txtpath = self.path_of_txtlinebox + self.imgfilename + "_linebox.txt"
        print(f'Path of linebox.txt: {self.txtpath}')
        if os.path.exists(self.txtpath):
            print(f'Removing: {self.txtpath}')
            os.remove(self.txtpath)
            self.ui.BoxText.clear()
        columns = range(self.ui.BoxTable.columnCount())
        header = [self.ui.BoxTable.horizontalHeaderItem(column).text() for column in columns]
        with open(self.txtpath, 'w') as csvfile:
            #writer = csv.writer(csvfile, dialect='excel', lineterminator='\n')
            writer = csv.writer(csvfile, dialect='excel', delimiter='\t', lineterminator='\n')
            writer.writerow(header)
            for row in range(self.ui.BoxTable.rowCount()):
                writer.writerow(self.ui.BoxTable.item(row, column).text() for column in columns)
        self.getText(self.txtpath)
   
    def renumberRows(self):
        print('Renumbering rows')
        rowcount = self.ui.BoxTable.rowCount()
        for row in range(rowcount):
            item = self.ui.BoxTable.item(row, 0)
            if not item:
                self.newrow = row
                print(f'Inserted row number: {row}')
                for column in range(0,7):
                    itemwidget = qtw.QTableWidgetItem()
                    self.ui.BoxTable.setItem(row, column,itemwidget)
                    item = self.ui.BoxTable.item(row, column)
                    if column == 0:
                        item.setText(str(row+1))
                    else:
                        item.setText(str(0))
            else:
                item.setText(str(row+1))
            self.ui.BoxTable.setEditTriggers(qtw.QAbstractItemView.NoEditTriggers)

    def insertRow(self, location):
        row = self.ui.BoxTable.currentRow()
        if row:
            if location == "above":
                self.ui.BoxTable.insertRow(row)
            elif location == "below":
                self.ui.BoxTable.insertRow(row+1) 
        else:
            popup = qtw.QMessageBox(self)
            popup.setIcon(qtw.QMessageBox.Information)
            popup.setWindowTitle("Select Row")
            popup.setText("You must select a row before inserting one")
            popup.setStandardButtons(qtw.QMessageBox.Ok)
            popup.exec()
            if popup.clickedButton() == qtw.QMessageBox.Ok:
                pass
    '''
    def insertRowAbove(self):
        row = self.ui.BoxTable.currentRow()
        if row:
            self.ui.BoxTable.insertRow(row) 
        else:
            popup = qtw.QMessageBox(self)
            popup.setIcon(qtw.QMessageBox.Information)
            popup.setWindowTitle("Select Row")
            popup.setText("You must select a row before inserting one")
            popup.setStandardButtons(qtw.QMessageBox.Ok)
            popup.exec()
            if popup.clickedButton() == qtw.QMessageBox.Ok:
                pass

    def insertRowBelow(self):
        row = self.ui.BoxTable.currentRow()
        if row:
            self.ui.BoxTable.insertRow(row+1)
        else:
            popup = qtw.QMessageBox(self)
            popup.setIcon(qtw.QMessageBox.Information)
            popup.setWindowTitle("Select Row")
            popup.setText("You must select a row before inserting one")
            popup.setStandardButtons(qtw.QMessageBox.Ok)
            popup.exec()
            if popup.clickedButton() == qtw.QMessageBox.Ok:
                pass
    '''

    def editRow(self):
        row = self.ui.BoxTable.currentRow()
        if not row:
            popup = qtw.QMessageBox(self)
            popup.setIcon(qtw.QMessageBox.Information)
            popup.setWindowTitle("Select Row")
            popup.setText("You must select a row before editing one")
            popup.setStandardButtons(qtw.QMessageBox.Ok)
            popup.exec()
            if popup.clickedButton() == qtw.QMessageBox.Ok:
                pass
        else:
            self.on_rowSelectionChanged
        
    def deleteRow(self):
        row = self.ui.BoxTable.currentRow()
        if row:
            self.resetLineBox()
            #self.drawWhiteLineBox()
            self.ui.BoxTable.removeRow(row)
            #self.newrow = row-1
        else:
            popup = qtw.QMessageBox(self)
            popup.setIcon(qtw.QMessageBox.Information)
            popup.setWindowTitle("Select Row")
            popup.setText("You must select a row before removing one")
            popup.setStandardButtons(qtw.QMessageBox.Ok)
            popup.exec()
            if popup.clickedButton() == qtw.QMessageBox.Ok:
                pass            

    def openTableMenu(self, position):
        tableMenu = QMenu()
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

        action = tableMenu.exec_(self.ui.BoxTable.mapToGlobal(position))
        if action == insertAboveAction:
            #
            location = "above"
            self.insertRow(location)
            #self.insertRowAbove()
            self.renumberRows()
            self.BoxTable2csv()
            #
            #
        elif action == insertBelowAction:
            #
            location = "below"
            self.insertRow(location)
            #self.insertRowBelow()
            self.renumberRows()
            self.BoxTable2csv()
            #
            #
        elif action == deleteRowAction:
            #
            self.deleteRow()
            self.renumberRows()
            self.BoxTable2csv()
            #
            #

    def setBoxPaths(self):
        
        # Greek Box Paths
        self.path_of_image_page = self.greekpages
        self.path_of_imgautosplit = self.greeklinesautosplit + r"/"
        self.path_of_imglinebox = self.greeklinesbox + r"/" + self.greekbookmarkdown + r"/"
        self.path_of_txtlinebox = self.txtgreeklinebox + r"/" + self.greekbookmarkdown + r"/"
        self.path_of_jsonlinebox = self.jsongreeklinebox + r"/" + self.greekbookmarkdown + r"/"

        # Latin Box Paths - to be added

        self.imgfilestr = os.path.basename(self.imgpath)
        self.imgfilesplit = os.path.splitext(self.imgfilestr)
        self.imgfilename = self.imgfilesplit[0]
        self.imgfileext = self.imgfilesplit[1]
        
        self.imglineboxfile = self.imgfilename + "_linebox" + self.imgfileext
        self.boximgpath = self.path_of_imglinebox + self.imglineboxfile

        self.txtpath = self.path_of_txtlinebox + self.imgfilename + "_linebox.txt"
        self.txtfilestr = os.path.basename(self.txtpath)
        self.txtfilesplit = os.path.splitext(self.txtfilestr)
        self.txtfilename = self.txtfilesplit[0]
        self.txtfilename = self.txtfilename.replace("_linebox","")
        self.txtfileext = self.txtfilesplit[1]

    def normImage(self):
        img = cv2.imread(self.imgpath)
        # convert image to grayscale and normalized rgb
        self.gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

        #normalize
        norm = cv2.normalize(self.gray, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        #print(norm.shape, norm.dtype)

        # convert to 3 channel
        self.norm = cv2.cvtColor(norm, cv2.COLOR_GRAY2BGR)
        #print(self.norm.shape, self.norm.dtype)
        #print(np.amin(self.norm),np.amax(self.norm))

    # Finalize LineBox Methods
    def saveimgline(self,roi,bnum):
        PILimage = Image.fromarray(roi)
        thresh = 127
        fn = lambda x : 255 if x > thresh else 0
        PIL_BWimage = PILimage.convert('L').point(fn, mode='1')
        tif_outfile = self.path_of_imgautosplit + self.imgfilename + "_Line" + str(bnum) + ".tif"
        print("Generating: " + tif_outfile)
        PIL_BWimage.save(tif_outfile, "TIFF", dpi=(300,300))    

    def saveLineBoxImage(self):
        imgboxfile = self.path_of_imglinebox + self.imgfilename + "_linebox" + self.imgfileext
        cv2.imwrite(imgboxfile,self.norm)
        self.boximgpath = imgboxfile
        self.showImage(self.boximgpath) 
  
    def BoxText2BoxTable(self):
        self.ui.BoxTable.clearContents()
        boxes = []
        reader = csv.reader(open(self.txtpath), delimiter = '\t')
        
        for row in reader:
            boxes.append(row)
        
        if self.mode == "make":
            boxes = boxes[0:]
        else:
            boxes = boxes[1:]

        rowCount = len(boxes)
        self.ui.BoxTable.setRowCount(rowCount)                
        self.ui.BoxTable.setSortingEnabled(False)
        for row, boxes in enumerate(boxes):
            for column, value in enumerate(boxes):
                newItem = qtw.QTableWidgetItem(value)
                self.ui.BoxTable.setItem(row, column, newItem)
        self.ui.BoxTable.resizeColumnsToContents()
        self.ui.BoxTable.setSortingEnabled(True)
  
    # Make LineBox Method
    def linebox_make_split(self):
            self.mode = 'make'
            
            self.setBoxPaths()

            dosplit = True

            self.normImage()
            
            # convert image to binary for finding contours
            ret,binary = cv2.threshold(self.gray,127,255,cv2.THRESH_BINARY)

            # binary inversion
            ret,thresh = cv2.threshold(self.gray,127,255,cv2.THRESH_BINARY_INV)

            #dilation
            kernel = np.ones((5,195), np.uint8)
            img_dilation = cv2.dilate(thresh, kernel, iterations=1)

            #medianblur
            median = cv2.medianBlur(img_dilation, 13)

            #find line contours
            ctrs, hier = cv2.findContours(median, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            #set flags for sorting contours top to bottom
            reverse = False
            i = 1

            # construct the list of bounding boxes and sort them from top to bottom
            boundingBoxes = [cv2.boundingRect(c) for c in ctrs]
            (ctrs, boundingBoxes) = zip(*sorted(zip(ctrs, boundingBoxes),key=lambda b:b[1][i], reverse=reverse))
            
            # Set initial box count
            bnum = 1

            self.ui.BoxText.clear()
            self.txtpath = self.path_of_txtlinebox + self.imgfilename + "_linebox.txt"
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
                                                               
                                # Append to BoxText
                                #boxlinestr = str(bnum) + ',' + str(x) + ',' + str(y) + ',' + str(w) + ',' + str(h) + ',' + str(x+w) + ',' + str(y+h) + '\n'
                                boxlinestr = str(bnum) + '\t' + str(x) + '\t' + str(y) + '\t' + str(w) + '\t' + str(h) + '\t' + str(x+w) + '\t' + str(y+h) + '\n'
                                txtboxfile.write(boxlinestr)
                                self.saveimgline(roi,bnum)
                                bnum += 1
                                
                        # Set height of multi-line contours and subdivide proportionally
                        elif h > 200:
                                h = int(round(h/dividers))
                                for subdiv in range(0,dividers):
                                    print('subloopcount =' + str(subdiv))
                                    roi = binary[y:y+h, x:x+w]
                                    cv2.rectangle(self.norm,(x,y),( x + w, y + h ),(0,0,255),2)
                                    
                                    # Append to BoxText
                                    #boxlinestr = str(bnum) + ',' + str(x) + ',' + str(y) + ',' + str(w) + ',' + str(h) + ',' + str(x+w) + ',' + str(y+h) + '\n'
                                    boxlinestr = str(bnum) + '\t' + str(x) + '\t' + str(y) + '\t' + str(w) + '\t' + str(h) + '\t' + str(x+w) + '\t' + str(y+h) + '\n'
                                    txtboxfile.write(boxlinestr)
                                    y = y + h
                                    if dosplit:
                                        self.saveimgline(roi,bnum)
                                    bnum += 1
                                               
            txtboxfile.close()
            
            # Write Text Box File to BoxTable TableWidget
            self.BoxText2BoxTable()

            # Overwrite Text Box File from BoxTable TableWidget
            self.BoxTable2csv()

            # Write linebox image to file
            self.saveLineBoxImage()
            self.ui.ImageLe.clear()
            self.ui.ImageLe.setText(os.path.basename(self.boximgpath))

    # Editing LineBox Methods
    def drawLineBoxImage(self):

        print(f'Drawing Linebox Image from BoxText: \n {self.txtpath}')
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
                cv2.rectangle(self.norm,(x,y),(x+w, y+h),(0,0,255),2)
                # Save Line Image
                self.saveimgline(roi,bnum)
                bnum += 1
        txtboxfile.close()

    def on_deselection(self):
        #if not self.row_selected.isNull():
        #self.ui.BoxTable.selectionModel().selectionChanged.disconnect()
        row = self.row_selected
        for column in range(1,5):
            self.ui.BoxTable.removeCellWidget(row,column)
            #cellvalue = self.ui.BoxTable.cellWidget(row, column).value()
            #print(f'Cell SpinBox Widget Value: {cellvalue}')
            #cellvalue = self.ui.BoxTable.spinbox.value

    def json2csv(self, csvFilePath, jsonFilePath):
        columns = ['Line','X','Y','W','H','X+W','Y+H']
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

    def update_BoxText(self,line,x,y,w,h):
        print(f'From getRbLineBox method - Line: {line}  X: {x}  Y: {y}  W: {w} H: {h}')
        self.jsonpath = self.path_of_jsonlinebox + self.imgfilename + "_linebox.json"
        jsonfilepath = self.jsonpath
        self.txtpath = self.path_of_txtlinebox + self.imgfilename + "_linebox.txt"
        csvfilepath = self.txtpath
        self.csv2json(csvfilepath,jsonfilepath)
        with open(jsonfilepath, 'r') as f:
            data = json.load(f)
            # Iterating through the json
            for Line in data:
                if Line['Line'] == line:
                    Line['X'] = x
                    Line['Y'] = y
                    Line['W'] = w
                    Line['H'] = h
                    Line['X+W'] = str(int(x)+int(w))
                    Line['Y+H'] = str(int(y)+int(h))
                    print(f'Updating Line: {line} found in JSON file. Dimensions :  X: {x}  Y: {y}  W: {w}  H: {h}')
                else:
                    print(f'Line: {line} not found in JSON file.')
                    break
            # Closing file
            f.close()
            os.remove(jsonfilepath)
            with open(jsonfilepath, 'w') as f:
                json.dump(data, f, indent=4)
            f.close()
        self.json2csv(csvfilepath,jsonfilepath)
        self.showText(csvfilepath)

    '''
    def update_BoxTable(self):
        # Update selected row in BoxTable from updated BoxText
        self.ui.BoxTable.setSortingEnabled(False)
        reader = list(csv.reader(open(self.txtpath), delimiter="\t"))
        # Remove column header from list of rows
        lineboxes = reader[1:]
        row = self.row_selected+1
        print(f'Selected Row: {row}')

        #self.rowCount = len(lineboxes)
        #col_list = []
        for linebox in lineboxes:
            line = linebox[0]
            if line == str(row):
                print(f'Line: {line}')
                # Extract x,y,w,h from matched row
                x = linebox[1]
                y = linebox[2]
                w = linebox[3]
                h = linebox[4]
                xw = str(int(linebox[1]) + int(linebox[3]))
                yh = str(int(linebox[2]) + int(linebox[4]))
                col_list = [x,y,w,h]
                column = 1
                for value_str in col_list:
                    self.tableitem = self.ui.BoxTable.item(self.row_selected, column)
                    cellwidget = self.ui.BoxTable.cellWidget(self.row_selected, column)
                    print(f'Selected Cell Location:  Row: {self.row_selected} Column: {column}')
                    print(f'Current Cell Widget: {cellwidget}')
                    print(f'New Cell Value: {value_str}')
                    self.ui.BoxTable.openPersistentEditor(self.tableitem)
                    self.spinbox = QSpinBox(None) #changed parent from None to self.ui.BoxTable - could also be just self
                    self.spinbox.setMaximum(6000)
                    self.spinbox.setValue(int(value_str))
                    column += 1
                xwItem = qtw.QTableWidgetItem(xw)
                self.ui.BoxTable.setItem(row, column, xwItem)
                yhItem = qtw.QTableWidgetItem(yh)
                self.ui.BoxTable.setItem(row, column, yhItem)
                
        self.ui.BoxTable.setSortingEnabled(True)
    '''
    '''
    def drawlineEvent(self):
        popup = qtw.QMessageBox(self)
        popup.setIcon(qtw.QMessageBox.Question)
        popup.setText("The linebox has been drawn/redrawn")
        popup.setInformativeText("Click Save to draw the linebox.")
        popup.setStandardButtons(qtw.QMessageBox.Save)
        popup.setDefaultButton(qtw.QMessageBox.Save)
        answer = popup.exec_()
        if answer == qtw.QMessageBox.Save:
            self.getRbLineBox()''' 

    # Rb LineBox Drawing Methods
    def putRbLineBox(self,x,y,w,h):
        self.line = int(self.ui.BoxTable.item(self.row_selected,0).text())
        print(f'Updating BoxText JSON and CSV files for line:{str(self.line)} with str values: x:{str(x)}, y:{str(y)}, w:{str(w)}, h:{str(h)}')
        self.update_BoxText(str(self.line),str(x),str(y),str(w),str(h)) 
        self.on_deselection()
        self.BoxText2BoxTable()
        # Save Line Image
        roi = self.norm[y:y+h, x:x+w]
        self.saveimgline(roi,self.line)
        self.ui.BoxTable.selectionModel().selectionChanged.connect(self.on_rowSelectionChanged)

    def drawRbLineBox(self,x,y,w,h):    
        if self.mode == "RbEdit":
            self.rubberBand.hide()
        # Draw/Redraw red LineBox
        cv2.rectangle(self.norm,(x,y),(x+w, y+h),(0,0,255),2)
        self.saveLineBoxImage()
        self.showImage(self.boximgpath)
        self.putRbLineBox(x,y,w,h)

    def getRbLineBox(self):
        #self.rubberBand.hide()        
        if self.mode == "RbEdit":
            # At scale DrawLineBox QRect at LineBox Image offset from MainWindow origin(0,0)
            DrawImg_xs = self.x_rb - int(self.img_xoffset)
            DrawImg_ys = self.y_rb - int(self.img_yoffset)
            DrawImg_ws = self.w_rb
            DrawImg_hs = self.h_rb
            DrawImg_sqrect = QRect(DrawImg_xs,DrawImg_ys,DrawImg_ws,DrawImg_hs)
            print("Offset Scaled QRect = " + str(DrawImg_sqrect))
            
            # Up scale DrawLineBox QRect at LineBox Image previously offset from MainWindow origin(0,0)
            DrawImg_xu = DrawImg_xs / self.scale
            DrawImg_yu = DrawImg_ys / self.scale
            DrawImg_wu = DrawImg_ws / self.scale
            DrawImg_hu = DrawImg_hs / self.scale
            DrawImg_uqrect = QRect(DrawImg_xu,DrawImg_yu,DrawImg_wu,DrawImg_hu)
            print("Offset Upscaled QRect = " + str(DrawImg_uqrect))

            # Set LineBox values
            x = int(DrawImg_xu)
            y = int(DrawImg_yu)
            w = int(DrawImg_wu)
            h = int(DrawImg_hu)
            
            # Disconnect put signal until RbLineBox is drawn
            # self.ui.actionDraw_Selected_LineBox_tb.triggered.disconnect(self.putRbLineBox(x,y,w,h))
            
            # Disconnect selection signal until RbLineBox is put
            self.ui.BoxTable.selectionModel().selectionChanged.disconnect(self.on_rowSelectionChanged)
            self.drawRbLineBox(x,y,w,h)
            # Reconnect put signal until RbLineBox is put
            #self.ui.actionDraw_Selected_LineBox_tb.triggered.connect(self.putRbLineBox(x,y,w,h)) 
    
    # Sb LineBox Drawing Methods
    def putSbLineBox(self):
        #self.ui.actionDraw_Table_LineBox_tb.setEnabled(False)
        self.mode = "edit"
        print('Line Box Mode: edit')
        row = self.ui.BoxTable.currentRow()
        # Update BoxText and BoxTable 
        self.line = int(self.ui.BoxTable.item(row,0).text())
        print(f'Updating BoxText JSON and CSV files for line:{str(self.line)} with str values: x:{str(self.xval)}, y:{str(self.yval)}, w:{str(self.wval)}, h:{str(self.hval)}')
        self.update_BoxText(str(self.line),str(self.xval),str(self.yval),str(self.wval),str(self.hval)) 
        self.on_deselection()
        self.BoxText2BoxTable()
        # Save Line Image
        roi = self.norm[self.yval:self.yval+self.hval, self.xval:self.xval+self.wval]
        self.saveimgline(roi,self.line)
        self.ui.BoxTable.setSortingEnabled(True)
        self.ui.actionDraw_Table_LineBox_tb.triggered.disconnect(self.putSbLineBox())    

    def resetLineBox(self):
        # Draw/Redraw white LineBox
        print('Resetting previous linebox to white')
        x = self.prevx
        y = self.prevy
        w = self.prevw
        h = self.prevh
        cv2.rectangle(self.norm,(x,y),(x+w, y+h),(255,255,255),2)
        pil_img = Image.fromarray(self.norm)
        qimage = ImageQt.ImageQt(pil_img)
        self.pixmap = qtg.QPixmap.fromImage(qimage).scaled(self.ui.Image.size(), qtc.Qt.KeepAspectRatio)         
        self.on_zoom()
        #self.saveLineBoxImage()
        #self.showImage(self.boximgpath)
    
    def drawWhiteLineBox(self):
        self.ui.BoxTable.setSortingEnabled(False)
        self.row_selected = self.ui.BoxTable.currentRow()
        line = int(self.ui.BoxTable.item(self.row_selected,0).text())
        # get dimensions of selected row/linebox
        with open(self.txtpath,'r') as csvfile:
            lines = csv.reader(csvfile, delimiter = '\t')
            for csvline in lines:
                if csvline[0] == str(line):
                    x = int(csvline[1])
                    y = int(csvline[2])
                    w = int(csvline[3])
                    h = int(csvline[4])
                    print('Drawing white linebox')
                    cv2.rectangle(self.norm,(x,y),(x+w, y+h),(255,255,255),2)
                    self.prevx = x
                    self.prevy = y
                    self.prevw = w
                    self.prevh = h
                    pil_img = Image.fromarray(self.norm)
                    qimage = ImageQt.ImageQt(pil_img)
                    self.pixmap = qtg.QPixmap.fromImage(qimage).scaled(self.ui.Image.size(), qtc.Qt.KeepAspectRatio)       
                    self.on_zoom()
                    #self.saveLineBoxImage()       
                    #self.showImage(self.boximgpath)
        csvfile.close()  
    
    def drawSbLineBox(self,x,y,w,h):
        #self.spinbox.valueChanged.disconnect()
        # Draw/Redraw white LineBox
        self.resetLineBox()
        # Draw/Redraw red LineBox
        cv2.rectangle(self.norm,(x,y),(x+w, y+h),(0,0,255),2)
        self.prevx = x
        self.prevy = y
        self.prevw = w
        self.prevh = h
        pil_img = Image.fromarray(self.norm)
        qimage = ImageQt.ImageQt(pil_img)
        self.pixmap = qtg.QPixmap.fromImage(qimage).scaled(self.ui.Image.size(), qtc.Qt.KeepAspectRatio)         
        self.on_zoom()
        self.ui.actionDraw_Table_LineBox_tb.triggered.connect(self.putSbLineBox())
        #self.saveLineBoxImage()
        #self.showImage(self.boximgpath)
        #self.spinbox.valueChanged.connect(self.onValueChanged)

    def onValueChanged(self):
        print('This is the handler for the selected spinbox value that is changed')
        #self.spinbox.valueChanged.disconnect(self.onValueChanged)
        row = self.ui.BoxTable.currentRow()
        col = self.ui.BoxTable.currentColumn()
        if col == 1:
            self.xval = self.ui.BoxTable.cellWidget(row, 1).value()
            self.yval = int(self.ui.BoxTable.item(row,2).text())
            self.wval = int(self.ui.BoxTable.item(row,3).text())
            self.hval = int(self.ui.BoxTable.item(row,4).text())
        elif col == 2:
            self.yval = self.ui.BoxTable.cellWidget(row, 2).value()
            self.xval = int(self.ui.BoxTable.item(row,1).text())
            self.wval = int(self.ui.BoxTable.item(row,3).text())
            self.hval = int(self.ui.BoxTable.item(row,4).text())
        elif col == 3:
            self.wval = self.ui.BoxTable.cellWidget(row, 3).value()
            self.xval = int(self.ui.BoxTable.item(row,1).text())
            self.yval = int(self.ui.BoxTable.item(row,2).text())
            self.hval = int(self.ui.BoxTable.item(row,4).text())
        elif col == 4:
            self.hval = self.ui.BoxTable.cellWidget(row, 4).value()
            self.xval = int(self.ui.BoxTable.item(row,1).text())
            self.yval = int(self.ui.BoxTable.item(row,2).text())
            self.wval = int(self.ui.BoxTable.item(row,3).text())  
        #For printing purposes
        line = int(self.ui.BoxTable.item(row,0).text())
        print(f'Line: {str(line)} X:{str(self.xval)} Y:{str(self.yval)} W:{str(self.wval)} H:{str(self.hval)}')
        #self.resetLineBox()
        self.drawSbLineBox(self.xval,self.yval,self.wval,self.hval)

    def getSpinBox(self):
        self.row_selected = self.ui.BoxTable.currentRow()
        self.col_selected = self.ui.BoxTable.currentColumn() 
        self.tableitem = self.ui.BoxTable.item(self.row_selected, self.col_selected)
        cellwidget = self.ui.BoxTable.cellWidget(self.row_selected, self.col_selected)
        cellvalue = self.ui.BoxTable.item(self.row_selected,self.col_selected).text()
        print(f'Selected Cell Location:  Row: {self.row_selected} Column: {self.col_selected}')
        print(f'Current Cell Widget: {cellwidget}')
        print(f'Current Cell Value: {cellvalue}')
        #self.ui.BoxTable.openPersistentEditor(self.tableitem)
        #self.spinbox = QSpinBox(None) #changed parent from None to self.ui.BoxTable - could also be just self
        #self.spinbox.setMaximum(6000)
        self.spinbox.setValue(int(cellvalue))
        self.ui.BoxTable.setCellWidget(self.row_selected,self.col_selected,self.spinbox)
        self.spinbox.valueChanged.connect(self.onValueChanged)
        self.ui.BoxTable.setSortingEnabled(True)

    def getSbLineBox(self):
        self.ui.BoxTable.selectionModel().selectionChanged.disconnect(self.on_rowSelectionChanged)
        self.ui.BoxTable.setSelectionBehavior(qtw.QAbstractItemView.SelectItems)
        print(f'Selection Mode: Select Items')
        #self.ui.actionDraw_Table_LineBox_tb.triggered.connect(self.putSbLineBox(x,y,w,h))
        #self.spinbox = QSpinBox(None) #changed parent from None to self.ui.BoxTable - could also be just self
        #self.spinbox.setMaximum(6000)
        #self.spinbox.valueChanged.connect(self.onValueChanged)
        self.ui.BoxTable.setSortingEnabled(False)
        if self.mode == "SbEdit":
            print('Line Box Mode: SbEdit')
            for column in range(0,7):
                self.tableitem = self.ui.BoxTable.item(self.row_selected, column)
                if column == 0 or column == 5 or column == 6:
                    self.tableitem.setFlags(qtc.Qt.ItemIsEditable)
                cellwidget = self.ui.BoxTable.cellWidget(self.row_selected, column)
                cellvalue = self.ui.BoxTable.item(self.row_selected,column).text()
                print(f'Selected Cell Location:  Row: {self.row_selected} Column: {column}')
                print(f'Current Cell Widget: {cellwidget}')
                print(f'Current Cell Value: {cellvalue}')
                if column == 1:                   
                    self.prevx = int(cellvalue)
                    self.currx = int(cellvalue)
                elif column == 2:
                    self.prevy = int(cellvalue)
                    self.curry = int(cellvalue)
                elif column == 3:
                    self.prevw = int(cellvalue)
                    self.currw = int(cellvalue)
                elif column == 4:
                    self.prevh = int(cellvalue)
                    self.currh = int(cellvalue)
            print(f'Prev X: {self.prevx} Prev Y: {self.prevy} Prev W: {self.prevw} Prev H: {self.prevh}')
            print(f'Curr X: {self.currx} Curr Y: {self.curry} Curr W: {self.currw} Curr H: {self.currh}')
            self.ui.BoxTable.selectionModel().selectionChanged.connect(self.getSpinBox)
            
    # Edit LineBox Method
    def linebox_edit_split(self):
        self.mode = "edit"
        print ('Line Box Mode: edit')
        self.ui.BoxTable.setSelectionBehavior(qtw.QAbstractItemView.SelectRows)
        print('Box Table Selection Mode: Single Selection (default)')
        print('Box Table Selection Behavior: Select Rows (default)')
        if self.ui.ImageLe.displayText() != "":
            popup = qtw.QMessageBox(self)
            popup.setIcon(qtw.QMessageBox.Information)
            popup.setWindowTitle("Edit Mode")
            popup.setText("'Edit Current' linebox pair or load and 'Edit Other'")
            currentButton = popup.addButton('Edit Current', qtw.QMessageBox.YesRole)
            otherButton = popup.addButton('Edit Other', qtw.QMessageBox.YesRole)
            popup.exec()
            if popup.clickedButton() == currentButton:
                pass
            elif popup.clickedButton() == otherButton:
                self.ui.ImageLe.clear()
                self.ui.Image.clear()
        
        if self.ui.ImageLe.displayText() == "":
            # Get imglinebox source file
            self.loadImage()
            self.setBoxPaths()
            self.ui.ImageLe.clear()
            self.ui.ImageLe.setText(self.imgfilename + "_linebox.tif")
            # Normalize indexed tif source file to RGB image
            self.normImage()
        else: 
            self.showImage(self.imgpath)       
            #self.ui.ImageLe.clear()
            #self.ui.ImageLe.setText(self.imgfilename)
            self.ui.ImageLe.setText(self.imgfilename + "_linebox.tif")
        
        self.ui.TextLE.clear()
        self.ui.TextLE.setText(self.txtfilestr)
        imgfilename = self.ui.ImageLe.displayText().split(r".")[0]
        txtfilename = self.ui.TextLE.displayText().split(r".")[0]
        # Get matching BoxText file
        print(f'Text File Name: {txtfilename}  Image File Name: {imgfilename}')
        if txtfilename == imgfilename:
            self.getText(self.txtpath)
            #BoxText2BoxTable()
            self.drawLineBoxImage()
            self.saveLineBoxImage()
            self.BoxText2BoxTable()
            #imglineboxfile = imgfilename + "_linebox" + imgfileext
            #boximgpath = dest_of_imglinebox + imglineboxfile
            #self.ui.ImageLe.setText(imglineboxfile)
            print("Waiting on BoxTable selection")
            #self.showImage(boximgpath)
            
            #while True:
            self.row_current = self.ui.BoxTable.currentRow()
            self.ui.BoxTable.selectionModel().selectionChanged.connect(self.on_rowSelectionChanged)

        else:
        #if txtfilename != imgfilename:
            # change this to message box    
            print(f'The linebox text: {txtfilename} does not match the linebox image: {imgfilename} -- Please try again!')
            #self.linebox_edit_split

    def renameimages(source, destination):
            def sorted_alphanumeric(data):
                    convert = lambda text: int(text) if text.isdigit() else text.lower()
                    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
                    return sorted(data, key=alphanum_key)
                    #usage:dirlist = sorted_alphanumeric(os.listdir(...)) - works great!

            path_of_images = source
            dest_of_images = destination
            #sorted(os.listdir(os.getcwd()), key=len) does not work

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

class ResizableRubberBand(QWidget):
    """Wrapper to make QRubberBand mouse-resizable using QSizeGrip

    Source: http://stackoverflow.com/a/19067132/435253
    """
    def __init__(self, parent = None):
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
        self.show()

    def resizeEvent(self, event):
        self.rubberband.resize(self.size())

# Only run this code if I am actually running this script
if __name__ == '__main__': 
    app = qtw.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec()
