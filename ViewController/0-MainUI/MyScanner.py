#print(len(locals()))

# Python imports
import sys
import os
import re
#import glob
import shutil
import json
#from subprocess import Popen, PIPE, CalledProcessError
import pytesseract
import tiffcapture
import qimage2ndarray
from queue import Queue
from ext import mainfind
from HelpSystem import add_help_menu
# PyQt5 imports
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc
from PyQt5.QtCore import  Qt, QObject, QThread, pyqtSignal
# Custom imports
#from MainUI import Ui_MainUI
from MyScannerUI import Ui_Scanner
from PreProcess import PreProcess as pp

import CropTif as croptif
import QtCropImage as cropimg
import Qt5SelectRegion
#from MultiPreProcess import MultiPreProcess as mpp
from Training import Train as tr
from SessionManager import SessionManager

import MyVersifier as versifier
import MyWriter as writer
import MyBoxer as boxer
import MyPixler as pixler
import MyExplorer as explorer
import ChrReference as chrref
from SessionManager import SessionManager
#import MyResolver as resolver
#import MyGrounder as grounder

# Dialog Imports
from Dialogs.ImageTextPairDialog import Ui_ImageTextPairDialog

#print(len(locals()))

# Define a stream, custom class, that reports data written to it, with a Qt signal
'''Deprecated => class Streamer(qtc.QObject):

    textWritten = qtc.pyqtSignal(str)

    def write(self, text):
        self.textWritten.emit(str(text))'''

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

# Menu and Toolbar Action Methods 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        # pre-compiled QtDesigner Ui_MainUI and extended slots code starts here:        
        # load the pre-compiled QtDesigner Ui_MainUI user interface
        self.ui = Ui_Scanner()
        self.ui.setupUi(self)
        self.session_manager = SessionManager()
        #Implement Co-pilot Help system
        add_help_menu(self, 'MyScanner')
        self.ui.actionOpen_Image.triggered.connect(self.loadImage)
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
        
        self.ui.actionPixler_Image_Editor.triggered.connect(self.OpenWithMyPixler)
        self.ui.actionVersifier.triggered.connect(self.OpenWithMyVersifier)
        self.ui.actionBoxer.triggered.connect(self.OpenWithMyBoxer)
        self.ui.actionWriter.triggered.connect(self.OpenWithMyWriter)
        self.ui.actionProject_Browser.triggered.connect(self.OpenMyBrowser)

        self.ui.actionUpdate_Wordlist_tb.triggered.connect(self.actionUpdate_Wordlist)
        self.ui.actionTrain_Tesseract_tb.triggered.connect(self.actionTrain_Tesseract)
        self.ui.actionCorrect_OCR_tb.triggered.connect(self.actionCorrect_OCR)
        self.ui.actionFind_and_Replace.triggered.connect(mainfind.Find(self).show)
        #self.ui.actionToggle_Greek_Toolbars.triggered.connect(self.toggleGreekToolbars)
        #self.ui.actionToggle_Latin_Toolbars.triggered.connect(self.toggleLatinToolbars)

        #self.ui.OpenImageFilebutton.clicked.connect(self.OpenImageFileDialog)
        self.ui.OpenImageFilebutton.clicked.connect(self.loadImage)
        self.ui.actionEdit_Image_tb.triggered.connect(self.actionGimpEdit)
        self.ui.MyPixlerbutton.clicked.connect(self.OpenWithMyPixler)
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
        
        #self.ui.Cropbutton.clicked.connect(self.actionCropImage)
        self.ui.Deskewbutton.clicked.connect(self.actionDeskewImage)

        self.ui.OCRbutton.clicked.connect(self.GetRawOCRtext)       
        self.ui.LHDialogtbutton.clicked.connect(self.GetLineSpacing)
        self.ui.LHslider.valueChanged.connect(self.SetLineSpacing)
        self.ui.LHslider.sliderReleased.connect(self.DisableLHSlider)
        self.ui.LHlineEdit.textChanged.connect(self.MoveLHSlider)
        self.ui.LHslider.hide()
        #self.ui.EditCorrectedTextbutton.clicked.connect(self.OpenTextFileDialog)
        self.ui.EditCorrectedTextbutton.clicked.connect(self.loadText)
        self.ui.SaveAsOCRCorrTextbutton.clicked.connect(self.SaveAsCorrectedTextFileDialog)
        self.ui.SaveOCRCorrTextbutton.clicked.connect(self.SaveCorrectedTextFileDialog)         
        
        self.ui.Writerbutton.clicked.connect(self.OpenWithWriter)
        self.ui.MyWriterbutton.clicked.connect(self.OpenWithMyWriter)
        self.ui.reloadImagebutton.clicked.connect(self.ReloadImage)
        self.ui.reloadTextbutton.clicked.connect(self.ReloadText)
        self.ui.fontComboBox.currentFontChanged.connect(self.on_font_update)
        self.ui.fontSizeBox.valueChanged.connect(self.on_font_update)
        self.ui.OCRModelComboBox.currentTextChanged.connect(self.on_lang_select)

        self.ui.bookComboBox.currentTextChanged.connect(self.selectBookCombo)

        # UI and slots code ends here.
        
        # Show the Main user interface
        self.ui.OCRDocument = qtg.QTextDocument(self.ui.OCRText)
        font = qtg.QFont()
        font.setFamily("FROMVS [MAXR]")
        font.setPointSize(20)
        self.ui.OCRDocument.setDefaultFont(font)
        
        self.ui.OCRDocument.setDefaultFont(font)
        self.ui.OCRBlockFormat = qtg.QTextBlockFormat()
        self.ui.OCRTextFormat = qtg.QTextFormat()
        self.ui.OCRCursor = qtg.QTextCursor(self.ui.OCRDocument)
        
        self.ui.OCRText.setDocument(self.ui.OCRDocument)
            
        self.ui.actionCharacter_Reference.triggered.connect(self.OpenChrReference)


        #ChrRefText = open('ViewController/3-ConductOCR/FROMVS ChrReference.txt', encoding='UTF-8').read()
        #self.ui.ChrRefplainTextEdit.setPlainText(ChrRefText)
        
        #self.initBookCombo()
        #self.selectBookCombo()
        
        # Restore Session settings
        self.get_session_settings()

        self.dirIterator = None
        self.imgfileList = []
        self.txtfileList = []
        self.imgdir = ""
        self.imgpath = ""
        #self.ui.bookComboBox.setCurrentText(self.bookabbr)
        print('current book:',self.bookabbr)


        '''#
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
        #
                
        
        # Install a custom output stream by connecting sys.stdout to instance of Streamer.
        #sys.stdout = Streamer(textWritten=self.output_terminal_written)'''
        
        self.show()
        #self.toggleLatinToolbars()

    def dragEnterEvent(self, event):
        m = event.mimeData()
        if m.hasUrls():
            for url in m.urls():
                if url.isLocalFile():
                    event.accept()
                    return
        event.ignore()
              
    def dropEvent(self, event):
        if event.mimeData().hasImage:
            event.setDropAction(Qt.CopyAction)
            file_path = event.mimeData().urls()[0].toLocalFile()
            print(f'image file path: {file_path}')
            self.showImage(file_path)
            event.accept()
        if event.mimeData().hasText:
            file_path = event.mimeData().urls()[0].toLocalFile()
            print(f'text file path: {file_path}')
            self.loadDropTextEvent(file_path)
            #self.ui.OCRText.insertPlainText(self.text())
            event.accept()
        else:
            file_path = event.mimeData().urls()[0].toLocalFile()
            print(f'text file path ignored: {file_path}')
            event.ignore()

    '''@qtc.pyqtSlot(str)
    def append_text(self,text):
        #self.ui.OutputText.moveCursor(QTextCursor.End)
        #self.ui.OutputText.insertPlainText(text)
        self.ui.OutputText.append(text)
      
    #custom method to write anything printed out to console/terminal to my QTextEdit widget via append function.
    def output_terminal_written(self, text):
        self.ui.OutputText.append(text)'''
  
    def get_session_settings(self):
        # get session settings from shared manager
        print("loading session")
        session = self.session_manager.values('ScannerSession.json')

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
        self.dirIterator = get_setting('dirIterator', None)
        self.imgfileList = get_setting('imgfileList', [])
        self.pixmap = get_setting('pixmap', None)
        self.qimage = get_setting('qimage', None)
        self.zoom = get_setting('zoom', '')
        self.zoomslidervalue = get_setting('zoomslidervalue', 0)
        self.txtpath = get_setting('txtpath', '')
        self.txtdir = get_setting('txtdir', '')
        self.txtfileList = get_setting('txtfileList', [])
        self.glyph = get_setting('glyph', '')
        self.glyphname = get_setting('glyphname', '')
        self.glyphencode = get_setting('glyphencode', '')

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
        with open('Model/Project/Data/json/Workflow.json') as f:
            # returns JSON object as
            # a dictionary
            data = json.load(f)
        
        # Iterating through the json
        # list
        for Sequence in data:
            print(Sequence['Sequence'], Sequence['DialogUi'],Sequence['DefaultSource'])
        
        # Closing file
        f.close()
       
    def initBookCombo(self):

        # Opening JSON file
        with open('Model/Project/Data/json/BooksAbbrName.json') as f:
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
                  
            jsonfile = 'Model/Project/Data/json/BooksMarkDown.json'
            
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
            
            SessionManager().update('Session.json', {
                'self.bookabbr': self.bookabbr,
                'self.sourcebookmarkdown': self.sourcebookmarkdown,
                'self.greekbookmarkdown': self.greekbookmarkdown,
                'self.latinbookmarkdown': self.latinbookmarkdown,
            })

            # Opening JSON file
            '''with open('Model/Project/Data/json/BooksAbbrName.json') as f:
                # returns JSON object as
                    # a dictionary
                data = json.load(f)'''
            
            #self.ui.bookComboBox.clear()
            
            # Iterating through the json
            # list          
            '''for booknumber in data:
                print(booknumber['bookabbr'])
                self.ui.bookComboBox.addItem(booknumber['bookabbr'])
            
            # Closing file
            f.close()'''
            
        self.ui.bookComboBox.setCurrentText(self.bookabbr)

    '''def toggleGreekToolbars(self):

        greekimgpagesstate = self.ui.GreekImagePagesToolBar.isVisible()
        greekimglinesstate = self.ui.GreekImageLinesToolBar.isVisible()
        greektxtlinesstate = self.ui.GreekTextLinesToolBar.isVisible()        
        
        # Set the visibility to its inverse
        self.ui.GreekImagePagesToolBar.setVisible(not greekimgpagesstate)
        self.ui.GreekImageLinesToolBar.setVisible(not greekimglinesstate)
        self.ui.GreekTextLinesToolBar.setVisible(not greektxtlinesstate)

    def toggleLatinToolbars(self):

        #latinimgpagesstate = self.ui.LatinImagePagesToolBar.isVisible()
        latinimglinesstate = self.ui.LatinImageLinesToolBar.isVisible()
        latintxtlinesstate = self.ui.LatinTextLinesToolBar.isVisible()        
        
        # Set the visibility to its inverse
        #self.ui.LatinImagePagesToolBar.setVisible(not latinimgpagesstate)
        self.ui.LatinImageLinesToolBar.setVisible(not latinimglinesstate)
        self.ui.LatinTextLinesToolBar.setVisible(not latintxtlinesstate)'''
  
    def actionPixler(self):
        print("Opening image in Pixler")
        self.PixlerMain = qtw.QMainWindow()
        self.pixlerui = pixler.Ui_Pixler()
        self.pixlerui.setupUi(self.PixlerMain)
        
        #cropimg.w = cropimg.MainWindow()
        if self.imgpath != "":
            self.pixlerui.imgpath = self.imgpath
            self.pixlerui.origpixmap = self.origpixmap
            self.pixlerui.scale = 0.1
            self.pixlerui.RefImg.setPixmap(self.origpixmap)
            self.pixlerui.RefImgLE.setText(self.imgpath)
        #self.pixlerui.show()
        self.PixlerMain.show()
        #rsp = self.PixlerWindow.main.show()
        print("Return from Pixler")
    
    def actionDeskewImage(self):
        print("Deskewing current image")
        if self.imgpath != "":
            pp.deskewimage(self.imgpath)
            print("Reloading deskewed image")
            self.ReloadImage()
        print("Deskew current image complete")

    def actionGimpEdit(self):
        #gimp_cmd = "/usr/bin/flatpak run --branch=stable --arch=aarch64 --command=gimp-2.10 --file-forwarding org.gimp.GIMP"
        gimp_cmd = "/usr/bin/flatpak run --branch=stable --arch=aarch64 --command=gimp-2.10 --file-forwarding org.gimp.GIMP @@ " + self.imgpath + " @@"
        
        '''if 'self.imgpath' in locals():
            gimp_cmd = "/usr/bin/flatpak run --branch=stable --arch=aarch64 --command=gimp-2.10 --file-forwarding org.gimp.GIMP @@ " + self.imgpath + " @@"
            print(self.imgpath)
        else:
            gimp_cmd = "/usr/bin/flatpak run --branch=stable --arch=aarch64 --command=gimp-2.10 --file-forwarding org.gimp.GIMP"'''
        
        os.system(gimp_cmd)

    def OpenChrReference(self):
        self.chrrefmain = chrref.CharacterReference()
        self.chrrefmain.show()

    def actionCrop_Greek_To_tiff_Lines(self):
        print("cropping and sorting Greek tiff lines")
        #usage: tr.sortcroplines(source, splitdir, linebox)
        self.crop_greeklinesDialog = qtw.QDialog()
        self.crop_greeklines_ui = Ui_crop_greek_linesDialog()
        self.crop_greeklines_ui.setupUi(self.crop_greeklinesDialog)
        self.crop_greeklinesDialog.show()

        self.crop_greeklines_ui.SourceButton.clicked.connect(self.CropGreekLinesDialog)
        self.crop_greeklines_ui.BoxFolderButton.clicked.connect(self.LineBoxFolderDialog)
        self.crop_greeklines_ui.DestGreekButton.clicked.connect(self.DestGreekLinesDialog)

        rsp = self.crop_greeklinesDialog.exec_()
        
        if self.crop_greeklinesDialog.Accepted:
            tr.sortcroplines(self.crop_greeklines_ui.SourceLineEdit.text(),self.crop_greeklines_ui.BoxFolderLineEdit.text(),self.crop_greeklines_ui.DestGreekLineEdit.text())
            print("completed creating cropped language tif files")
        #tr.sortcroplines(r"c:/users/max/Projects/Python/Images/Greek/png_greek_deskew/greek_book_40_Matthew/","c:/users/max/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_40_Matthew/","c:/users/max/Projects/Python/Images/Greek/tif_greek_linebox/greek_book_40_Matthew/")
        #tr.sortcroplines(r"c:/users/max/Projects/Python/Images/Greek/png_greek_deskew/greek_book_41_Mark/","c:/users/max/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_41_Mark/","c:/users/max/Projects/Python/Images/Greek/tif_greek_linebox/greek_book_41_Mark/")
        
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
        # tr.renameimages(r"c:/users/max/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_40_Matthew/", "c:/users/max/Projects/Python/Images/Greek/tif_greek_tif4groundtruth/")
        # tr.renameimages(r"c:/users/max/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_41_Mark/", "c:/users/max/Projects/Python/Images/Greek/tif_greek_tif4groundtruth/")    
       
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
        
        # tr.renameimages(r"c:/users/max/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_40_Matthew/", "c:/users/max/Projects/Python/Images/Greek/tif_greek_tif4groundtruth/")
        #tr.renameimages("c:/users/max/Projects/Python/Images/Greek/tif_greek_tif4groundtruth/", "c:/users/max/Projects/Python/Images/Greek/tif_greek_tif2groundtruth/")
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
        #tr.sortcroplines(r"c:/users/max/Projects/Python/Images/Latin/png_latin_deskew/latin_book_40_Matthew/","c:/users/max/Projects/Python/Images/Latin/tif_latin_autosplit/latin_book_40_Matthew/","c:/users/max/Projects/Python/Images/Latin/tif_latin_linebox/latin_book_40_Matthew/")
        tr.sortcroplines(r"c:/users/max/Projects/Python/Images/Latin/png_latin_deskew/latin_book_41_Mark/","c:/users/max/Projects/Python/Images/Latin/tif_latin_autosplit/latin_book_41_Mark/","c:/users/max/Projects/Python/Images/Latin/tif_latin_linebox/latin_book_41_Mark/")

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
        
        # tr.renameimages(r"c:/users/max/Projects/Python/Images/Latin/tif_latin_autosplit/latin_book_40_Matthew/", "c:/users/max/Projects/Python/Images/Latin/tif_latin_tif4groundtruth/")
        #tr.renameimages(r"c:/users/max/Projects/Python/Images/Latin/tif_latin_autosplit/latin_book_41_Mark/", "c:/users/max/Projects/Python/Images/Latin/tif_latin_tif4groundtruth/")

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
        # tr.splittextlines(r"c:/users/max/Projects/Python/EstablishTruth/Greek txt4linesplit/", "c:/users/max/Projects/Python/EstablishTruth/Greek lines4groundtruth/")
        tr.splittextlines("c:/users/max/Projects/Python/EstablishTruth/Greek txt4linesplit/", "c:/users/max/Projects/Python/EstablishTruth/Greek lines4groundtruth/")
        
    def actionRenameGreek_text_lines(self):
        print("renaming Greek textlines for ground truth")
        # usage: tr.text2groundtruth(source, destination)
        #tr.text2groundtruth(r"c:/users/max/Projects/Python/EstablishTruth/Greek lines4groundtruth/", "c:/users/max/Projects/Python/EstablishTruth/Greek lines2groundtruth/")
        tr.text2groundtruth(r"c:/users/max/Projects/Python/EstablishTruth/Greek lines4groundtruth/", "c:/users/max/Projects/Python/EstablishTruth/Greek lines2groundtruth/")
    
    def actionSplit_Latin_Text_Lines(self):
        print("splitting Latin textlines for ground truth")
        # usage: tr.splittextlines(source, destination)
        # tr.splittextlines(r"c:/users/max/Projects/Python/EstablishTruth/Latin txt4linesplit/", "c:/users/max/Projects/Python/EstablishTruth/Latin lines4groundtruth/")
        tr.splittextlines("c:/users/max/Projects/Python/EstablishTruth/Latin txt4linesplit/", "c:/users/max/Projects/Python/EstablishTruth/Latin lines4groundtruth/")

    def actionRename_Latin_Text_Lines(self):
        print("renaming Latin textlines for ground truth")
        # usage: tr.text2groundtruth(source, destination)
        #tr.text2groundtruth(r"c:/users/max/Projects/Python/EstablishTruth/Latin lines4groundtruth/", "c:/users/max/Projects/Python/EstablishTruth/Latin lines2groundtruth/")
        tr.text2groundtruth(r"c:/users/max/Projects/Python/EstablishTruth/Latin lines4groundtruth/", "c:/users/max/Projects/Python/EstablishTruth/Latin lines2groundtruth/")
    
    '''def actionReview_Ground_Truth(self):
        gtr.MainWindow = qtw.QMainWindow()
        gtr.ui = gtr.Ui_MainWindow()
        gtr.ui.setupUi(gtr.MainWindow)
        gtr.MainWindow.show()'''


    
    def actionUpdate_Wordlist(self):
        pass
    
    def actionTrain_Tesseract(self):
        pass
    
    def actionCorrect_OCR(self):
        print("performing OCR on current image")
        self.GetRawOCRtext()

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
        """
        if len(fileName) == 0:
            if QT_VERSION_STR[0] == '4':
                fileName = QFileDialog.getOpenFileName(self, "Open TIFF stack file.")
            elif QT_VERSION_STR[0] == '5':
                fileName, dummy = QFileDialog.getOpenFileName(self, "Open TIFF stack file.")
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
        self.imgpath = qtw.QFileDialog.getOpenFileName(self.ui.centralwidget, 'Open image file',self.imgdir,'Images (*.png *.xpm *.jpg *.bmp *.gif *.tif)')[0]
        if self.imgpath:
            self.ui.ImageLe.setText(os.path.basename(self.imgpath))
            self.showImage(self.imgpath)
            self.sortImgFiles()       
        '''imgfilename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.ui.centralwidget, 'Select Image', '', 'Image Files (*.png *.jpg *.jpeg *.bmp *.tif)')
        
        if imgfilename:
            self.ui.ImageLe.setText(os.path.basename(imgfilename))       
            self.imgfilename = imgfilename'''

    def OpenImageFileDialog(self):
        self.imgpath = qtw.QFileDialog.getOpenFileName(
            self.ui.centralwidget, 'Open image file', self.imgdir,
            'Images (*.png *.xpm *.jpg *.bmp *.gif *.tif)')[0]
                
        if self.imgpath:
            self.imgdir = os.path.dirname(self.imgpath)
            self.ui.ImageLe.setText(os.path.basename(self.imgpath))
           
            #self.showImage(self.imgpath)
            #self.sortImgFiles() 

            file = qtc.QFile(self.imgpath)
            filestr = os.path.basename(self.imgpath)           
            filesplit = os.path.splitext(filestr)
            filename = filesplit[0]
            fileext = filesplit[1]          
            
            if file.open(qtc.QIODevice.ReadOnly):
                info = qtc.QFileInfo(self.imgpath)
                #print(qtg.QImage.size(self.qimage))
                #print(self.qimage.size())
                #pmsize = qtg.QPixmap.fromImage(self.qimage).size()
                #print(pmsize)

                if fileext == '.tif':
                    self.loadImageStackFromFile(str(self.imgpath))
                    self.showFrame(0)
                    
                    #w,h = qtg.QImage.size(self.qimage)
                    #print(qtg.QImage.size(self.qimage))
                    '''pmsize = qtg.QPixmap.fromImage(self.qimage).size()
                    print(pmsize)'''
                    self.origpixmap = qtg.QPixmap.fromImage(self.qimage)
                    pixmap = qtg.QPixmap.fromImage(self.qimage).scaled(self.ui.Image.size(), qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)
                    #pixmap = qtg.QPixmap.fromImage(self.qimage)   
                    self.ui.Image.setPixmap(qtg.QPixmap(pixmap))
                else:
                    
                    self.ui.Image.setPixmap(qtg.QPixmap(self.imgpath))
                
                file.close()
                
                #self.get_session_settings()
                
                #with open('Model/Data/json/Session.json', 'w') as f:
                    #json.dump(data, f, indent=2)
                

                SessionManager().update('Session.json', {
                    'self.imgpath': self.imgpath,
                    'self.imgdir': self.imgdir,
                })

        self.imgfileList = []
        for i in os.listdir(self.imgdir):
            ipath = os.path.join(self.imgdir, i)
            if os.path.isfile(ipath) and i.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tif')):
                self.imgfileList.append(ipath)
        print(self.imgfileList)
        self.sortImgFiles()

    def showImage(self,imgfilename):
        #self.imgfilename = self.imgpath
        file = qtc.QFile(imgfilename)
        filestr = os.path.basename(imgfilename)           
        filesplit = os.path.splitext(filestr)
        filename = filesplit[0]
        fileext = filesplit[1]
        
        if file.open(qtc.QIODevice.ReadOnly):
            info = qtc.QFileInfo(imgfilename)
        
            '''if self.imgpath.endswith('.tif'):
                self.loadImageStackFromFile(imgfilename)
                self.showFrame(0)
                self.pixmap = qtg.QPixmap.fromImage(self.qimage).scaled(self.ui.Image.size(), qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation) 
            else:
                self.pixmap = qtg.QPixmap(imgfilename).scaled(self.ui.Image.size(), 
                    qtc.Qt.KeepAspectRatio)'''       

            if fileext == '.tif':
                self.loadImageStackFromFile(imgfilename)
                self.showFrame(0)
                self.origpixmap = qtg.QPixmap.fromImage(self.qimage)
                '''self.origsize = self.origpixmap.size()       
                self.origheight = self.origpixmap.height
                self.origwidth = self.origpixmap.width
                self.pixmap = self.origpixmap.scaled(self.scale * self.origsize, qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)'''
                
                self.pixmap = qtg.QPixmap.fromImage(self.qimage).scaled(self.ui.Image.size(), qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)  
                #self.ui.Image.setPixmap(self.pixmap) -- moved out below
            else:
                self.pixmap = qtg.QPixmap(self.imgpath)
                #self.ui.Image.setPixmap(self.pixmap) -- moved out below
        
        file.close()
        
        if self.pixmap.isNull():
            return
        
        self.on_zoom()
        #self.ui.Image.setPixmap(self.pixmap)
        
        self.imgdir = os.path.dirname(imgfilename)
        self.ui.ImageLe.setText(filestr)
        SessionManager().update('Session.json', {
            'self.imgpath': self.imgpath,
            'self.imgdir': self.imgdir,
        })
        
        self.imgfileList = []
        for i in os.listdir(self.imgdir):
            ipath = os.path.join(self.imgdir, i)
            if os.path.isfile(ipath) and i.endswith(('.png', '.jpg', '.jpeg', '.tif')):
                self.imgfileList.append(ipath)        
        '''self.imgfileList = []
        for i in os.listdir(self.imgdir):
            ipath = os.path.join(self.imgdir, i)
            if os.path.isfile(ipath) and i.endswith(('.png', '.jpg', '.jpeg', '.tif')):
                self.imgfileList.append(ipath)'''

        self.sortImgFiles()

    def sortImgFiles(self):
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
        self.sorted_imgfilelist = sorted(self.imgfileList, key=alphanum_key)
        #self.fileList.sort()
        #print(self.sorted_imgfilelist)
        self.imgdirIterator = iter(self.sorted_imgfilelist)
        self.nextimage = next(self.imgdirIterator)
        self.imgdirRevIterator = reversed(self.sorted_imgfilelist)
        self.previmage = next(self.imgdirRevIterator)
        while True:
            # cycle through the iterator until the current file is found
            if next(self.imgdirIterator) == self.imgpath:
                break
        while True:
            # cycle through the reverse iterator until the current file is found
            if next(self.imgdirRevIterator) == self.imgpath:
                break
    
    def nextImage(self):      
        # ensure that the file list has not been cleared due to missing files     
        filestr = os.path.basename(self.imgpath)           
        filesplit = os.path.splitext(filestr)
        filename = filesplit[0]
        fileext = filesplit[1]
        
        if self.imgfileList:
            try:
                imgfilename = self.imgpath
                nextimgfilename = next(self.imgdirIterator)
                self.ui.ImageLe.setText(os.path.basename(nextimgfilename))
                if fileext == '.tif':
                    print(nextimgfilename)
                    self.loadImageStackFromFile(nextimgfilename)
                    self.showFrame(0)
                    pixmap = qtg.QPixmap.fromImage(self.qimage).scaled(self.ui.Image.size(), 
                        qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)
                else:
                    pixmap = qtg.QPixmap(nextimgfilename).scaled(self.ui.Image.size(), 
                        qtc.Qt.KeepAspectRatio)

            except:
                # the iterator has finished, restart it
                self.imgdirIterator = iter(self.imgfileList)
                #self.imgdirRevIterator = reversed(self.imgfileList)
                #print(self.imgfileList)
                self.prevImage()
            
            self.imgpath = nextimgfilename
            self.showImage(nextimgfilename)            

        else:
            # no file list found, load an image
            # self.OpenImageFileDialog()
            self.loadImage()

    def prevImage(self):
        # ensure that the file list has not been cleared due to missing files     
        filestr = os.path.basename(self.imgpath)           
        filesplit = os.path.splitext(filestr)
        filename = filesplit[0]
        fileext = filesplit[1]
        
        if self.imgfileList:
            try:
                imgfilename = self.imgpath
                previmgfilename = next(self.imgdirRevIterator)
                self.ui.ImageLe.setText(os.path.basename(previmgfilename))
                if fileext == '.tif':
                    print(previmgfilename)
                    self.loadImageStackFromFile(previmgfilename)
                    self.showFrame(0)
                    pixmap = qtg.QPixmap.fromImage(self.qimage).scaled(self.ui.Image.size(), 
                        qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)
                else:
                    pixmap = qtg.QPixmap(previmgfilename).scaled(self.ui.Image.size(), 
                        qtc.Qt.KeepAspectRatio)

            except:
                # the iterator has finished, restart it
                self.imgdirRevIterator = reversed(self.imgfileList)
                #self.imgdirIterator = iter(self.imgfileList)
                #self.nextImage()
            
            self.imgpath = previmgfilename
            self.showImage(previmgfilename)
            

        else:
            # no file list found, load an image
            # self.OpenImageFileDialog()
            self.loadImage()

    def ReloadImage(self):
        if self.imgpath:
            self.ui.ImageLe.setText(os.path.basename(self.imgpath))
            self.showImage(self.imgpath)
            self.sortImgFiles()  
        '''if self.imgpath:
            file = qtc.QFile(self.imgpath)
            filestr = os.path.basename(self.imgpath)
            self.imgdir = os.path.dirname(self.imgpath)
            self.ui.ImageLe.setText(filestr)
            filesplit = os.path.splitext(filestr)
            filename = filesplit[0]
            fileext = filesplit[1]
                        
           if file.open(qtc.QIODevice.ReadOnly):
                info = qtc.QFileInfo(self.imgpath)
                #print(qtg.QImage.size(self.qimage))
                #print(self.qimage.size())
                #pmsize = qtg.QPixmap.fromImage(self.qimage).size()
                #print(pmsize)

                if fileext == '.tif':
                    self.loadImageStackFromFile(str(self.imgpath))
                    self.showFrame(0)
                    
                    #w,h = qtg.QImage.size(self.qimage)
                    #print(qtg.QImage.size(self.qimage))
                    #pmsize = qtg.QPixmap.fromImage(self.qimage).size()
                    #print(pmsize)
                    self.origpixmap = qtg.QPixmap.fromImage(self.qimage)
                    pixmap = qtg.QPixmap.fromImage(self.qimage).scaled(self.ui.Image.size(), qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)
                    #pixmap = qtg.QPixmap.fromImage(self.qimage)   
                    self.ui.Image.setPixmap(qtg.QPixmap(pixmap))
                else:
                    
                    self.ui.Image.setPixmap(qtg.QPixmap(self.imgpath))
        
                self.imgfileList = []
                for i in os.listdir(self.imgdir):
                    ipath = os.path.join(self.imgdir, i)
                    if os.path.isfile(ipath) and i.endswith(('.png', '.jpg', '.jpeg', '.tif')):
                        self.imgfileList.append(ipath)

                self.sortImgFiles(MainWindow)'''
  
    
    def loadDropTextEvent(self,file_path):
        self.txtpath = file_path
        
        if self.txtpath:
            file = qtc.QFile(self.txtpath)
            filename = os.path.basename(self.txtpath)
            self.txtdir = os.path.dirname(self.txtpath)
            self.ui.TextLE.setText(filename)
            #self.sortTextFiles(MainWindow)
            self.showText(self.txtpath)
            self.sortTextFiles()

    def loadText(self):
        '''self.textpath = QtWidgets.QFileDialog.getOpenFileName(
            self.centralwidget, 'Open text file', '',
            'Text files (*.txt)')[0]
        if self.textpath:
            self.textfile = QtCore.QFile(self.textpath)
            self.txtfilename = os.path.basename(self.textpath)
            self.showText(MainWindow,self.txtfilename)'''
        
        self.txtpath = qtw.QFileDialog.getOpenFileName(
        self.ui.centralwidget, 'Open text file',self.txtdir,
        'Text files (*.txt *.csv)')[0]
        
        if self.txtpath:
            file = qtc.QFile(self.txtpath)
            filename = os.path.basename(self.txtpath)
            self.txtdir = os.path.dirname(self.txtpath)
            self.ui.TextLE.setText(filename)
            #self.sortTextFiles(MainWindow)
            self.showText(self.txtpath)
            self.sortTextFiles()

    def OpenTextFileDialog(self, MainWindow):
        self.txtpath = qtw.QFileDialog.getOpenFileName(
            self.ui.centralwidget, 'Open text file',self.txtdir,
            'Text files (*.txt *.csv)')[0]
        
        if self.txtpath:
            file = qtc.QFile(self.txtpath)
            filename = os.path.basename(self.txtpath)
            self.txtdir = os.path.dirname(self.txtpath)
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
                
                file.close()
        
        SessionManager().update('Session.json', {
            'self.txtpath': self.txtpath,
            'self.txtdir': self.txtdir,
        })

        #txtdirpath = self.txtdir
        SessionManager().update('Session.json', {
            'self.txtpath': self.txtpath,
            'self.txtdir': self.txtdir,
        })
        for t in os.listdir(self.txtdir):
            tpath = os.path.join(self.txtdir, t)
            if os.path.isfile(tpath) and t.endswith(('.txt')):
                self.txtfileList.append(tpath)
        self.sortTextFiles()

    def showText(self, txtfilename):        
        #self.textfile = txtfilename
        if self.txtpath:
            file = qtc.QFile(self.txtpath)
            filename = os.path.basename(self.txtpath)
            self.txtdir = os.path.dirname(self.txtpath)
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
            #textfile.close()
            #txtdirpath = os.path.dirname(self.textpath)

            # update font to selection and size       
            self.on_font_update()
            
            # update line spacing
            self.SetLineSpacing()
            file.close()
       
        SessionManager().update('Session.json', {
            'self.txtpath': self.txtpath,
            'self.txtdir': self.txtdir,
        })
        self.sortTextFiles()

    def sortTextFiles(self):
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
        self.sorted_txtfilelist = sorted(self.txtfileList, key=alphanum_key)
        #self.fileList.sort()
        #print(self.sorted_txtfilelist)
        self.txtdirIterator = iter(self.sorted_txtfilelist)
        self.txtdirRevIterator = reversed(self.sorted_txtfilelist)
        while True:
            # cycle through the iterator until the current file is found
            if next(self.txtdirIterator) == self.txtpath:
                break
        while True:
            # cycle through the reverse iterator until the current file is found
            if next(self.txtdirRevIterator) == self.txtpath:
                break

    def nextText(self):
        # ensure that the file list has not been cleared due to missing files
        filestr = os.path.basename(self.txtpath)           
        filesplit = os.path.splitext(filestr)
        filename = filesplit[0]
        fileext = filesplit[1]
        
        if self.txtfileList:
            try:
                txtfile = next(self.txtdirIterator)
                self.ui.TextLE.setText(os.path.basename(txtfile))
                #pixmap = QtGui.QPixmap(textfile).scaled(self.ImageView.size(), 
                    #QtCore.Qt.KeepAspectRatio)
                self.txtfile = qtc.QFile(txtfile)
                self.txtfilename = os.path.basename(txtfile)
                self.dirname = os.path.dirname(self.txtpath)
                #self.textpath = os.path.join(self.dirname, "/",self.txtfilename)
                self.txtpath = txtfile
                print(txtfile,"\t",self.txtpath,"\t",self.txtfile,"\t",self.txtfilename)
                #print(self.txtfilename)
                self.showText(self.txtfilename)
            except:
                # the iterator has finished, restart it
                self.txtdirIterator = iter(self.sorted_txtfilelist)
                self.txtdirRevIterator = reversed(self.sorted_txtfilelist)
                self.prevText()
            self.txtpath = txtfile
            self.showText(txtfile)
        else:
            # no file list found, load an image
            self.loadText()
    
    def prevText(self):
        # ensure that the file list has not been cleared due to missing files
        filestr = os.path.basename(self.txtpath)           
        filesplit = os.path.splitext(filestr)
        filename = filesplit[0]
        fileext = filesplit[1]
        
        if self.txtfileList:
            try:
                #txtfile = self.textfile
                txtfile = next(self.txtdirRevIterator)
                self.ui.TextLE.setText(os.path.basename(txtfile))
                #pixmap = QtGui.QPixmap(textfile).scaled(self.ImageView.size(), 
                    #QtCore.Qt.KeepAspectRatio)
                self.txtfile = qtc.QFile(txtfile)
                self.txtfilename = os.path.basename(txtfile)
                self.dirname = os.path.dirname(self.txtpath)
                #self.textpath = os.path.join(self.dirname, "/",self.txtfilename)
                self.txtpath = txtfile
                print(txtfile,"\t",self.txtpath,"\t",self.txtfile,"\t",self.txtfilename)
                #print(self.txtfilename)
                self.showText(self.txtfilename)
            except:
                # the iterator has finished, restart it
                self.txtdirRevIterator = reversed(sorted_txtfilelist)
                self.txtdirIterator = iter(sorted_txtfilelist)
                self.nextText()
            self.txtpath = txtfile
            self.showText(txtfile)    
        else:
            # no file list found, load an image
            self.loadText()      

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
                    self.showText(self.txtpath)
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

    def GetRawOCRtext(self):
        self.ui.OCRText.clear()
        my_OCR_rawtext = pytesseract.image_to_string(self.imgpath,lang="feg")
        #my_OCR_cleantext = " ".join(my_OCR_rawtext.split())
        #self.OCRDocument.insertPlainText(my_OCR_rawtext)
        #self.ui.OCRText.insertPlainText(my_OCR_cleantext)
        my_OCR_rawtext = my_OCR_rawtext.replace('\x0c', '')
        self.ui.OCRText.insertPlainText(my_OCR_rawtext)
        imgfilename = self.ui.ImageLe.text()
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
        self.ui.LHslider.setValue(int(self.ui.LHlineEdit.text()))
    
    def SetLineSpacing(self):
                
        '''num,ok = qtw.QInputDialog.getInt(self.ui.centralwidget,"Proportional Line Spacing","Enter a percent value from 0-200")  
        
        if ok:
            lineSpacing = num
        else:
            lineSpacing = 145'''

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
            self.ui.centralwidget, 'Save Raw text file',self.txtdir,
            'Text files (*.txt)')[0]
        with open(path, 'w') as file:
            my_RawText = self.ui.OCRDocument.toPlainText()
            file.write(my_RawText)
        filename = os.path.basename(path)
        self.ui.TextLE.setText(filename)
        file.close()
        
    def SaveAsCorrectedTextFileDialog(self, MainWindow):
        path = qtw.QFileDialog.getSaveFileName(
            self.ui.centralwidget, 'Save Corrected text file', self.txtdir,
            'Text files (*.txt)')[0]
        with open(path, 'w') as file:
            my_CorrectedText = self.ui.OCRDocument.toPlainText()
            file.write(my_CorrectedText)
        filename = os.path.basename(path)
        self.ui.TextLE.setText(filename)
        file.close()

    def SaveCorrectedTextFileDialog(self, MainWindow):
        
        #if self.txtdir:
            #defaultdir = self.txtdir
        #else:
            #defaultdir = r"c:/users/max/Projects/Python/EstablishTruth/Greek_txt_pages/"
        
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

        '''if self.ui.ZoomComboBox.currentText(): == "Best_Fit": 
            print("Best fit selected")
            
            self.ui.Zoomslider.setEnabled(False)
            self.origpixmap = qtg.QPixmap.fromImage(self.qimage)
            self.origsize = self.origpixmap.size()       
            self.origheight = self.origpixmap.height
            self.origwidth = self.origpixmap.width           
            
            bestheight = self.origheight
            bestwidth = self.ui.ImagescrollArea.width
            bestfit = qtc.QSize(self.origpixmap.height(),self.ui.ImagescrollArea.width())
            
            scaled_pixmap = qtg.QPixmap.fromImage(self.qimage).scaled(self.ui.ImagescrollArea.size(), qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)   
            self.ui.Image.setPixmap(qtg.QPixmap(scaled_pixmap))
        else:'''
        if self.qimage:
            self.origsize = self.origpixmap.size()       
            self.origheight = self.origpixmap.height
            self.origwidth = self.origpixmap.width
            scaled_pixmap = self.origpixmap.scaled(self.scale * self.origsize, qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)
            self.ui.Image.setPixmap(scaled_pixmap)
        
        #self.ui.ImagescrollArea.adjustsize()

    def OpenWithCalc(self):
        lo_cmd = 'libreoffice --calc ' + self.txtpath
        print(lo_cmd)
        os.system(lo_cmd)

    def OpenWithWriter(self):
        lo_cmd = 'libreoffice --writer ' + self.txtpath
        print(lo_cmd)
        os.system(lo_cmd)

    def OpenMyBrowser(self):
        
        self.browsermain = explorer.MyFileBrowser()
        self.browsermain.show()
        

    def OpenWithMyPixler(self):
        
        # Uncomment below to open My Pixler in a dependent window => disables MyScanner until closed
        
        #mw_cmd = "python3 ViewController/0-MainUI/MyPixler.py"
        #print(mw_cmd)
        #os.system(mw_cmd)

        # Open MyPixler in an independent window => allows both windows remain open and to function independently
        self.pixlermain = pixler.PixlerMain()
        self.pixlermain.show()
    
    def OpenWithMyVersifier(self):
        self.versifiermain = versifier.Ui_MainWindow()
        self.versifiermain .show()

    def OpenWithMyWriter(self):
        # Uncomment below to open My Writer in a dependent window => disables MyScanner until closed
        #mw_cmd = "python3 ViewController/0-MainUI/MyWriter.py"
        #print(mw_cmd)
        #os.system(mw_cmd)

        # Open MyWriter in an independent window => allows both windows remain open and to function independently
        self.writermain = writer.Main()
        self.writermain.show()

    def OpenWithMyBoxer(self):
        self.boxermain = boxer.MainWindow()
        self.boxermain.show()

    
    def on_font_update(self):
        # update font to selection and size       
        #font = qtg.QFont()
        #font.setFamily(self.ui.fontComboBox.currentFont())
        #print(self.ui.fontComboBox.currentFont())
        font = qtg.QFont(self.ui.fontComboBox.currentFont())
        font.setPointSize(self.ui.fontSizeBox.value())
        #font = qtg.QFont(self.font)
        #font.setPointSize(int(self.fontsize))
        
        self.ui.OCRText.setFont(font)

    def on_lang_select(self):
        pass

# Only run this code if I am actually running this script
if __name__ == '__main__': 
    app = qtw.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec()