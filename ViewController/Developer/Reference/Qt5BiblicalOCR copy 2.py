#print(len(locals()))

# Python imports
import sys
import os
import json
#from subprocess import Popen, PIPE, CalledProcessError
import pytesseract
import tiffcapture
import qimage2ndarray
from queue import Queue
# PyQt5 imports
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc
from PyQt5.QtCore import QObject, QThread, pyqtSignal
# Custom imports
from MainUI import Ui_MainUI
from PreProcess import PreProcess as pp
from ExtractDialog import Ui_ExtractDialog
from pdf4tifDialog import Ui_pdf4tifDialog
from pdf2tifDialog import Ui_pdf2tifDialog
from tif2monoDialog import Ui_tif2monoDialog
from mono2pngDialog import Ui_mono2pngDialog
from deskew_monoDialog import Ui_deskew_monoDialog
from crop_languagesDialog import Ui_crop_languagesDialog
from greekmono2pngDialog import Ui_greekmono2pngDialog
from deskew_greekmonoDialog import Ui_deskew_greekmonoDialog
from greekresizepngDialog import Ui_greekresizepngDialog
from latinmono2pngDialog import Ui_latinmono2pngDialog
from deskew_latinmonoDialog import Ui_deskew_latinmonoDialog
from latinresizepngDialog import Ui_latinresizepngDialog
from crop_greek_linesDialog import Ui_crop_greek_linesDialog
from crop_latin_linesDialog import Ui_crop_latin_linesDialog
from tif_greek_lines_renameDialog import Ui_tifgreekrenamelinesDialog
from tif_greek_lines_moveDialog import Ui_tifgreekmovelinesDialog
from tif_latin_lines_renameDialog import Ui_tiflatinrenamelinesDialog
from tif_latin_lines_moveDialog import Ui_tiflatinmovelinesDialog



import CropTif as croptif
import QtCropImage as cropimg
import Qt5SelectRegion
#from MultiPreProcess import MultiPreProcess as mpp
from Training import Train as tr
import Qt5GroundTruthReview as gtr
import Qt5Versify as versify

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
        # pre-compiled QtDesigner Ui_MainUI and extended slots code starts here:        
        # load the pre-compiled QtDesigner Ui_MainUI user interface
        self.ui = Ui_MainUI()
        self.ui.setupUi(self)

        # extended slots code
        self.ui.actionOpen_Image.triggered.connect(self.OpenImageFileDialog)
        self.ui.actionVerse_Correction.triggered.connect(self.actionVerse_Correction)
        
        self.ui.actionextract_pdf_tb.triggered.connect(self.actionextract_pdf)      
        self.ui.actionpdf_for_tiff_tb.triggered.connect(self.actionpdf_for_tiff)
        self.ui.actionpdf_to_tiff_tb.triggered.connect(self.actionpdf_to_tiff)
        self.ui.actiontiff_to_mono_tb.triggered.connect(self.actiontiff_to_mono)
        self.ui.actiondeskew_mono.triggered.connect(self.actiondeskew_mono)
        self.ui.actionmono_to_png_tb.triggered.connect(self.actionmono_to_png)
        self.ui.actionCrop_Languages_tb.triggered.connect(self.actionCrop_Languages)
        
        self.ui.actionManual_Crop_Image_tb.triggered.connect(self.actionCropImage)
        
        self.ui.actionEdit_Image_tb.triggered.connect(self.actionGimpEdit) 
        
        self.ui.actionConvert_Greek_tiff_To_png.triggered.connect(self.actionConvert_Greek_tiff_To_png)
        self.ui.actionDeskewGreek_tiff_tb.triggered.connect(self.actionDeskewGreek_tiff)
        self.ui.actionResizeGreek_png_tb.triggered.connect(self.actionResizeGreek_png)
        self.ui.actionConvert_Latin_tiff_To_png.triggered.connect(self.actionConvert_Latin_tiff_To_png)
        self.ui.actionDeskewLatin_tiff_tb.triggered.connect(self.actionDeskewLatin_tiff)
        self.ui.actionResizeLatin_png_tb.triggered.connect(self.actionResizeLatin_png)
        
        self.ui.actionCrop_Greek_to_tiff_Lines_tb.triggered.connect(self.actionCrop_Greek_To_tiff_Lines)
        self.ui.actionRename_Greek_tiff_Lines_tb.triggered.connect(self.actionRename_Greek_tiff_Lines)
        self.ui.actionMove_Greek_tiff_Lines_tb.triggered.connect(self.actionMove_Greek_tiff_Lines)
        
        self.ui.actionCrop_Latin_To_tiff_Lines_tb.triggered.connect(self.actionCrop_Latin_To_tiff_Lines)
        self.ui.actionRename_Latin_tiff_Lines_tb.triggered.connect(self.actionRename_Latin_tiff_Lines)
        self.ui.actionMove_Latin_tiff_Lines_tb.triggered.connect(self.actionMove_Latin_tiff_Lines)
        
        self.ui.actionSplitGreek_text_lines_tb.triggered.connect(self.actionSplitGreek_text_lines)
        self.ui.actionRenameGreek_text_lines_tb.triggered.connect(self.actionRenameGreek_text_lines)
        
        self.ui.actionSplit_Latin_Text_Lines_tb.triggered.connect(self.actionSplit_Latin_Text_Lines)
        self.ui.actionRename_Latin_Text_Lines_tb.triggered.connect(self.actionRename_Latin_Text_Lines)
        
        self.ui.actionReview_Ground_Truth_tb.triggered.connect(self.actionReview_Ground_Truth)
        self.ui.actionUpdate_Wordlist_tb.triggered.connect(self.actionUpdate_Wordlist)
        self.ui.actionTrain_Tesseract_tb.triggered.connect(self.actionTrain_Tesseract)
        self.ui.actionCorrect_OCR_tb.triggered.connect(self.actionCorrect_OCR)

        self.ui.Cropbutton.clicked.connect(self.actionCropImage)
        #self.ui.EditImageFilebutton.clicked.connect(self.actionGimpEdit) 
        self.ui.OCRbutton.clicked.connect(self.GetRawOCRtext)       
        self.ui.LHDialogtbutton.clicked.connect(self.GetLineSpacing)
        self.ui.LHslider.valueChanged.connect(self.SetLineSpacing)
        self.ui.LHslider.sliderReleased.connect(self.DisableSlider)
        self.ui.LHlineEdit.textChanged.connect(self.MoveSlider)
        self.ui.EditCorrectedTextbutton.clicked.connect(self.OpenTextFileDialog)
        self.ui.SaveAsOCRCorrTextbutton.clicked.connect(self.SaveAsCorrectedTextFileDialog)
        self.ui.SaveOCRCorrTextbutton.clicked.connect(self.SaveCorrectedTextFileDialog)         
        self.ui.OpenImageFilebutton.clicked.connect(self.OpenImageFileDialog)
        self.ui.Calcbutton.clicked.connect(self.OpenWithCalc)
        self.ui.Writerbutton.clicked.connect(self.OpenWithWriter)
        self.ui.reloadImagebutton.clicked.connect(self.ReloadImage)
        self.ui.reloadTextbutton.clicked.connect(self.ReloadText)
        self.ui.fontComboBox.currentFontChanged.connect(self.on_font_update)
        self.ui.fontSizeBox.valueChanged.connect(self.on_font_update)
        self.ui.langComboBox.currentTextChanged.connect(self.on_lang_select)
        self.ui.Zoombutton.clicked.connect(self.show_combo)
        self.ui.ZoomComboBox.currentTextChanged.connect(self.on_zoom)

        self.ui.ZoomComboBox.hide()


        
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

        ChrRefText = open('/home/max/Projects/BiblicalOCR/ViewController/Application/3-ConductOCR/FROMVS ChrReference.txt').read()
        self.ui.ChrRefplainTextEdit.setPlainText(ChrRefText)
        
        self.imgpath = ""
        self.imgdir = ""
        self.txtpath = ""
        self.txtdir = ""
        #'''      
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
        #'''
                
        
        # Install a custom output stream by connecting sys.stdout to instance of Streamer.
        #sys.stdout = Streamer(textWritten=self.output_terminal_written)
        
        self.show()

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

    def get_workflow_settings(self):

        # Opening JSON file
        with open('/home/max/Projects/BiblicalOCR/Model/SQLite/json/Workflow.json') as f:
            # returns JSON object as
            # a dictionary
            data = json.load(f)
        
        # Iterating through the json
        # list
        for Sequence in data:
            print(Sequence['Sequence'], Sequence['DialogUi'],Sequence['DefaultSource'])
        
        # Closing file
        f.close()

    def actionextract_pdf(self):
        print("extracting pdf pages from source pdf")
        '''app = qtw.QApplication(sys.argv)
        w = pdfxWindow()
        w.show()
        app.exec()'''
        
        self.pdfxDialog = qtw.QDialog()
        self.pdfx_ui = Ui_ExtractDialog()
        self.pdfx_ui.setupUi(self.pdfxDialog)
        self.pdfxDialog.show()
        #self.pdfxDialog.exec_()
        
        self.pdfx_ui.SourceButton.clicked.connect(self.OpenPdfFileDialog)
        self.pdfx_ui.DestinationButton.clicked.connect(self.DestPdfFileDialog)

        rsp = self.pdfxDialog.exec_()
        
        if self.pdfxDialog.Accepted:
            pp.pdfExtractPages(self.pdfx_ui.SourceLineEdit.text(), self.pdfx_ui.DestinationLineEdit.text(),self.pdfx_ui.FirstPageLineEdit.text(),self.pdfx_ui.LastPageLineEdit.text())
            print("pdf page extraction complete")
            ''' #usage: pdf4tiff(source, destination,firstpage,lastpage)    
            #pp.pdf4tiff('./Images/Source/pdf_source/1516.pdf', './Images/Source/pdf_source/','73','80') 
            
            #mpp.pdf4tiff('./Images/Source/pdf_source/1516.pdf', './Images/Source/pdf_source/','51','60')
            print("pdf page extraction complete")
            with Popen(pp.pdf4tiff('./Images/Source/pdf_source/1516.pdf', './Images/Source/pdf_source/','51','60'), stdout=PIPE, bufsize=1, universal_newlines=True) as p:
                for b in p.stdout:
                    print(b, end='') # b is the byte from stdout

            if p.returncode != 0:
                raise CalledProcessError(p.returncode, p.args)'''
        
    def actionpdf_for_tiff(self):
        print("extracting pdf pages for tif")
        
        self.pdf4tifDialog = qtw.QDialog()
        self.pdf4tif_ui = Ui_pdf4tifDialog()
        self.pdf4tif_ui.setupUi(self.pdf4tifDialog)
        self.pdf4tifDialog.show()

        self.pdf4tif_ui.SourceButton.clicked.connect(self.PdfForTifDialog)
        self.pdf4tif_ui.DestinationButton.clicked.connect(self.DestPdfForTifDialog)

        rsp = self.pdf4tifDialog.exec_()
        
        if self.pdf4tifDialog.Accepted:
            pp.pdf4tif(self.pdf4tif_ui.SourceLineEdit.text(), self.pdf4tif_ui.DestinationLineEdit.text())
            print("pdf pages for tif extraction complete")

    def actionpdf_to_tiff(self):
        print("converting pdf pages to tiff")

        self.pdf2tifDialog = qtw.QDialog()
        self.pdf2tif_ui = Ui_pdf2tifDialog()
        self.pdf2tif_ui.setupUi(self.pdf2tifDialog)
        self.pdf2tifDialog.show()

        self.pdf2tif_ui.SourceButton.clicked.connect(self.PdfToTifDialog)
        self.pdf2tif_ui.DestinationButton.clicked.connect(self.DestPdfToTifDialog)

        rsp = self.pdf2tifDialog.exec_()
        
        if self.pdf2tifDialog.Accepted:
            pp.pdf2tif(self.pdf2tif_ui.SourceLineEdit.text(), self.pdf2tif_ui.DestinationLineEdit.text(), self.pdf2tif_ui.StartPageLineEdit.text())
            print("pdf pages to tiff conversion complete")
        #pp.pdf2tif(r"/home/max/Projects/Python/Images/Source/pdf4tif/", "/home/max/Projects/Python/Images/Source/pdf2tif/","51")
        #pp.pdf2tif(r"/home/max/Projects/Python/Images/Source/pdf4tif/", "/home/max/Projects/Python/Images/Source/pdf2tif/","73")
        #print("pdf to tiff conversion complete")

        #self.Dui = None

    def actiontiff_to_mono(self):
        print("creating indexed(BW) tiff")
        #usage: pp.tiff2tiffidx(source, destination)
        self.tif2monoDialog = qtw.QDialog()
        self.tif2mono_ui = Ui_tif2monoDialog()
        self.tif2mono_ui.setupUi(self.tif2monoDialog)
        self.tif2monoDialog.show()

        self.tif2mono_ui.SourceButton.clicked.connect(self.TifToMonoDialog)
        self.tif2mono_ui.DestinationButton.clicked.connect(self.DestTifToMonoDialog)

        rsp = self.tif2monoDialog.exec_()
        
        if self.tif2monoDialog.Accepted:
            pp.tiff2tiffidx(self.tif2mono_ui.SourceLineEdit.text(), self.tif2mono_ui.DestinationLineEdit.text())
            print("completed creating indexed(BW) tiff")
            #pp.tiff2tiffidx("/home/max/Projects/Python/Images/Source/pdf2tif/", "/home/max/Projects/Python/Images/Source/tif_black_white/source_book_41_Mark/")
            #mpp.tiff2tiffidx("/home/max/Projects/Python/Images/Source/pdf2tif/", "/home/max/Projects/Python/Images/Source/tif_black_white/source_book_40_Matthew/")

    def actionmono_to_png(self):
        print("creating indexed(BW) png")
        #usage: pp.tiff2pngidx(source, destination)
        self.mono2pngDialog = qtw.QDialog()
        self.mono2png_ui = Ui_mono2pngDialog()
        self.mono2png_ui.setupUi(self.mono2pngDialog)
        self.mono2pngDialog.show()

        self.mono2png_ui.SourceButton.clicked.connect(self.MonoToPngDialog)
        self.mono2png_ui.DestinationButton.clicked.connect(self.DestMonoToPngDialog)

        rsp = self.mono2pngDialog.exec_()
        
        if self.mono2pngDialog.Accepted:
            pp.tiff2pngidx(self.mono2png_ui.SourceLineEdit.text(), self.mono2png_ui.DestinationLineEdit.text())
            print("completed creating indexed(BW) png")
        #pp.tiff2pngidx(r"/home/max/Projects/Python/Images/Source/tif_black_white/source_book_40_Matthew/", "/home/max/Projects/Python/Images/Source/tif_black_white_2png/source_book_40_Matthew/")
        #pp.tiff2pngidx(r"/home/max/Projects/Python/Images/Source/tiff_black_white_deskew/", "/home/max/Projects/Python/Images/Source/tif_black_white_2png/source_book_41_Mark/")
    
    def actiondeskew_mono(self):
        print("deskewing monochrome tiff and png files")
        #usage: dsk.deskewfiles(source, pngdest, tifdest)
        self.deskew_monoDialog = qtw.QDialog()
        self.deskew_mono_ui = Ui_deskew_monoDialog()
        self.deskew_mono_ui.setupUi(self.deskew_monoDialog)
        self.deskew_monoDialog.show()

        self.deskew_mono_ui.SourceButton.clicked.connect(self.DeskewMonoDialog)
        self.deskew_mono_ui.DestPngButton.clicked.connect(self.DestDeskewPngDialog)
        self.deskew_mono_ui.DestTifButton.clicked.connect(self.DestDeskewTifDialog)

        rsp = self.deskew_monoDialog.exec_()
        
        if self.deskew_monoDialog.Accepted:
            pp.deskewfiles(self.deskew_mono_ui.SourceLineEdit.text(), self.deskew_mono_ui.DestPngLineEdit.text(),self.deskew_mono_ui.DestTifLineEdit.text())
            print("completed deskewing monochrome tiff and png files")
        #dsk.deskewfiles("/home/max/Projects/Python/Images/Source/tif_black_white/source_book_40_Matthew/", "/home/max/Projects/Python/Images/Source/png_black_white_deskew/","/home/max/Projects/Python/Images/Source/tiff_black_white_deskew/")
        #pp.deskewfiles("/home/max/Projects/Python/Images/Source/tif_black_white/source_book_41_Mark/", "/home/max/Projects/Python/Images/Source/png_black_white_deskew/","/home/max/Projects/Python/Images/Source/tiff_black_white_deskew/")  
        
    def actionCrop_Languages(self):
        print("creating cropped language tif files")
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

        rsp = self.crop_languagesDialog.exec_()
        
        if self.crop_languagesDialog.Accepted:
            pp.croplangs(self.crop_languages_ui.SourceLineEdit.text(), self.crop_languages_ui.BoxFolderLineEdit.text(),self.crop_languages_ui.DestGreekLineEdit.text(),self.crop_languages_ui.DestLatinLineEdit.text(),self.crop_languages_ui.ElimFolderLineEdit.text())
            print("completed creating cropped language tif files")
        #pp.croplangs(r"/home/max/Projects/Python/Images/Source/tif_black_white_2png/source_book_40_Matthew/", "/home/max/Projects/Python/Images/Source/tif_box/lang_box/source_book_40_Matthew/","/home/max/Projects/Python/Images/Greek/tif_greek/greek_book_40_Matthew/","/home/max/Projects/Python/Images/Latin/tif_latin/latin_book_40_Matthew/","/home/max/Projects/Python/Images/Source/tif_eliminated/source_book_40_Matthew/")
        #pp.croplangs(r"/home/max/Projects/Python/Images/Source/tif_black_white_2png/source_book_41_Mark/", "/home/max/Projects/Python/Images/Source/tif_box/lang_box/source_book_41_Mark/","/home/max/Projects/Python/Images/Greek/tif_greek/greek_book_41_Mark/","/home/max/Projects/Python/Images/Latin/tif_latin/latin_book_41_Mark/","/home/max/Projects/Python/Images/Source/tif_eliminated/source_book_41_Mark/")
        

        '''self.crop_languagesDialog = qtw.QDialog()
        self.crop_languages_ui = Ui_crop_languagesDialog()
        self.crop_languages_ui.setupUi(self.crop_languagesDialog)
        self.crop_languagesDialog.show()'''

        self.CropWindow = qtw.QMainWindow()
        self.cropui = croptif.Ui_MainWindow()
        self.cropui.setupUi(self.CropWindow)
        self.CropWindow.show()

        self.cropui.OpenImageFilebutton.clicked.connect(self.OpenCropFileDialog)
        self.cropui.CropButton.clicked.connect(self.CropTif(self.cropui.Image))
        self.cropui.SaveCroppedImgAsbutton.clicked.connect(self.DestLatinDialog)
        self.cropui.SaveCroppedImgbutton.clicked.connect(self.DestLatinDialog)

        rsp = self.CropWindow.exec_()    

    def actionConvert_Greek_tiff_To_png(self):
        print("creating indexed(BW) Greek png files")
        #usage: pp.tiff2pngidx(source, destination)
        self.greekmono2pngDialog = qtw.QDialog()
        self.greekmono2png_ui = Ui_greekmono2pngDialog()
        self.greekmono2png_ui.setupUi(self.greekmono2pngDialog)
        self.greekmono2pngDialog.show()

        self.greekmono2png_ui.SourceButton.clicked.connect(self.GreekMonoToPngDialog)
        self.greekmono2png_ui.DestinationButton.clicked.connect(self.GreekDestMonoToPngDialog)

        rsp = self.greekmono2pngDialog.exec_()
        
        if self.greekmono2pngDialog.Accepted:
            pp.tiff2pngidx(self.greekmono2png_ui.SourceLineEdit.text(), self.greekmono2png_ui.DestinationLineEdit.text())
            print("completed creating indexed(BW) png")
        #pp.tiff2pngidx(r"/home/max/Projects/Python/Images/Source/tif_black_white/source_book_40_Matthew/", "/home/max/Projects/Python/Images/Source/tif_black_white_2png/source_book_40_Matthew/")
        #pp.tiff2pngidx(r"/home/max/Projects/Python/Images/Greek/tif_greek/greek_book_41_Mark/", "/home/max/Projects/Python/Images/Greek/png_greek/greek_book_41_Mark/")

    def actionDeskewGreek_tiff(self):
        print("deskewing Greek tiff files")
        #usage: dsk.deskewfiles(source, pngdest, tifdest)
        self.deskew_greekmonoDialog = qtw.QDialog()
        self.deskew_greekmono_ui = Ui_deskew_greekmonoDialog()
        self.deskew_greekmono_ui.setupUi(self.deskew_greekmonoDialog)
        self.deskew_greekmonoDialog.show()

        self.deskew_greekmono_ui.SourceButton.clicked.connect(self.DeskewGreekMonoDialog)
        self.deskew_greekmono_ui.DestPngButton.clicked.connect(self.DestDeskewGreekPngDialog)
        self.deskew_greekmono_ui.DestTifButton.clicked.connect(self.DestDeskewGreekTifDialog)

        rsp = self.deskew_greekmonoDialog.exec_()
        
        if self.deskew_greekmonoDialog.Accepted:
            pp.deskewfiles(self.deskew_greekmono_ui.SourceLineEdit.text(), self.deskew_greekmono_ui.DestPngLineEdit.text(),self.deskew_greekmono_ui.DestTifLineEdit.text())
            print("completed deskewing monochrome tiff and png files")
        
        #dsk.deskewfiles("/home/max/Projects/Python/Images/Greek/png_greek/greek_book_40_Matthew/", "/home/max/Projects/Python/Images/Greek/png_greek_deskew/greek_book_40_Matthew/","/home/max/Projects/Python/Images/Greek/tif_greek_deskew/greek_book_40_Matthew/")
        #pp.deskewfiles("/home/max/Projects/Python/Images/Greek/png_greek/greek_book_41_Mark/", "/home/max/Projects/Python/Images/Greek/png_greek_deskew/greek_book_41_Mark/","/home/max/Projects/Python/Images/Greek/tif_greek_deskew/greek_book_41_Mark/")
    
    def actionResizeGreek_png(self):
        print("resizing Greek png files")
        #usage: pp.resizepngs(source, destination)
        self.greekresizepngDialog = qtw.QDialog()
        self.greekresizepng_ui = Ui_greekresizepngDialog()
        self.greekresizepng_ui.setupUi(self.greekresizepngDialog)
        self.greekresizepngDialog.show()

        self.greekresizepng_ui.SourceButton.clicked.connect(self.GreekResizePngDialog)
        self.greekresizepng_ui.DestinationButton.clicked.connect(self.DestGreekResizePngDialog)

        rsp = self.greekresizepngDialog.exec_()
        
        if self.greekresizepngDialog.Accepted:
            pp.resizepngs(self.greekresizepng_ui.SourceLineEdit.text(), self.greekresizepng_ui.DestinationLineEdit.text())
            print("completed creating indexed(BW) png")
        
        
        #pp.resizepngs(r"/home/max/Projects/Python/Images/Greek/png_greek_deskew/greek_book_40_Matthew/","/home/max/Projects/Python/Images/Greek/png_greek_resize/greek_book_40_Matthew/")
        #pp.resizepngs(r"/home/max/Projects/Python/Images/Greek/png_greek_deskew/greek_book_41_Mark/","/home/max/Projects/Python/Images/Greek/png_greek_resize/greek_book_41_Mark/")

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
        #pp.tiff2pngidx(r"/home/max/Projects/Python/Images/Source/tif_black_white/source_book_40_Matthew/", "/home/max/Projects/Python/Images/Source/tif_black_white_2png/source_book_40_Matthew/")
        #pp.tiff2pngidx(r"/home/max/Projects/Python/Images/Latin/tif_latin/latin_book_41_Mark/", "/home/max/Projects/Python/Images/Latin/png_latin/latin_book_41_Mark/")

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
        #dsk.deskewfiles("/home/max/Projects/Python/Images/Latin/png_latin/latin_book_40_Matthew/", "/home/max/Projects/Python/Images/Latin/png_latin_deskew/latin_book_40_Matthew/","/home/max/Projects/Python/Images/Latin/tif_latin_deskew/latin_book_40_Matthew/")
        #pp.deskewfiles("/home/max/Projects/Python/Images/Latin/png_latin/latin_book_41_Mark/", "/home/max/Projects/Python/Images/Latin/png_latin_deskew/latin_book_41_Mark/","/home/max/Projects/Python/Images/Latin/tif_latin_deskew/latin_book_41_Mark/")
    
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
        #pp.resizepngs(r"/home/max/Projects/Python/Images/Greek/png_latin_deskew/latin_book_40_Matthew/","/home/max/Projects/Python/Images/Greek/png_latin_resize/latin_book_40_Matthew/")
        #pp.resizepngs(r"/home/max/Projects/Python/Images/Latin/png_latin_deskew/latin_book_41_Mark/","/home/max/Projects/Python/Images/Latin/png_latin_resize/latin_book_41_Mark/")

    def actionCropImage(self):
        
        cropimg.w = cropimg.MainWindow()
        if self.imgpath != "":
            cropimg.w.imgpath = self.imgpath
            cropimg.w.origpixmap = self.origpixmap
            cropimg.w.scale = 0.1
            cropimg.w.ui.Image.setPixmap(self.origpixmap)
            cropimg.w.ui.ImageLe.setText(self.imgpath)
        cropimg.w.show()
          
    def actionGimpEdit(self):
        gimp_cmd = "/usr/bin/flatpak run --branch=stable --arch=aarch64 --command=gimp-2.10 --file-forwarding org.gimp.GIMP"
        '''if 'self.imgpath' in locals():
            gimp_cmd = "/usr/bin/flatpak run --branch=stable --arch=aarch64 --document-export =" + self.imgpath + "--command=gimp-2.10" + self.imgpath + "--file-forwarding org.gimp.GIMP"
            print(self.imgpath)
        else:
            gimp_cmd = "/usr/bin/flatpak run --branch=stable --arch=aarch64 --command=gimp-2.10 --file-forwarding org.gimp.GIMP"'''         
        
        os.system(gimp_cmd)

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
        #tr.sortcroplines(r"/home/max/Projects/Python/Images/Greek/png_greek_deskew/greek_book_40_Matthew/","/home/max/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_40_Matthew/","/home/max/Projects/Python/Images/Greek/tif_greek_linebox/greek_book_40_Matthew/")
        #tr.sortcroplines(r"/home/max/Projects/Python/Images/Greek/png_greek_deskew/greek_book_41_Mark/","/home/max/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_41_Mark/","/home/max/Projects/Python/Images/Greek/tif_greek_linebox/greek_book_41_Mark/")
        
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
        # tr.renameimages(r"/home/max/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_40_Matthew/", "/home/max/Projects/Python/Images/Greek/tif_greek_tif4groundtruth/")
        # tr.renameimages(r"/home/max/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_41_Mark/", "/home/max/Projects/Python/Images/Greek/tif_greek_tif4groundtruth/")    
       
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
        
        # tr.renameimages(r"/home/max/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_40_Matthew/", "/home/max/Projects/Python/Images/Greek/tif_greek_tif4groundtruth/")
        #tr.renameimages("/home/max/Projects/Python/Images/Greek/tif_greek_tif4groundtruth/", "/home/max/Projects/Python/Images/Greek/tif_greek_tif2groundtruth/")
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
        #tr.sortcroplines(r"/home/max/Projects/Python/Images/Latin/png_latin_deskew/latin_book_40_Matthew/","/home/max/Projects/Python/Images/Latin/tif_latin_autosplit/latin_book_40_Matthew/","/home/max/Projects/Python/Images/Latin/tif_latin_linebox/latin_book_40_Matthew/")
        tr.sortcroplines(r"/home/max/Projects/Python/Images/Latin/png_latin_deskew/latin_book_41_Mark/","/home/max/Projects/Python/Images/Latin/tif_latin_autosplit/latin_book_41_Mark/","/home/max/Projects/Python/Images/Latin/tif_latin_linebox/latin_book_41_Mark/")

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
        
        # tr.renameimages(r"/home/max/Projects/Python/Images/Latin/tif_latin_autosplit/latin_book_40_Matthew/", "/home/max/Projects/Python/Images/Latin/tif_latin_tif4groundtruth/")
        #tr.renameimages(r"/home/max/Projects/Python/Images/Latin/tif_latin_autosplit/latin_book_41_Mark/", "/home/max/Projects/Python/Images/Latin/tif_latin_tif4groundtruth/")

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
        # tr.splittextlines(r"/home/max/Projects/Python/EstablishTruth/Greek txt4linesplit/", "/home/max/Projects/Python/EstablishTruth/Greek lines4groundtruth/")
        tr.splittextlines("/home/max/Projects/Python/EstablishTruth/Greek txt4linesplit/", "/home/max/Projects/Python/EstablishTruth/Greek lines4groundtruth/")
        
    def actionRenameGreek_text_lines(self):
        print("renaming Greek textlines for ground truth")
        # usage: tr.text2groundtruth(source, destination)
        #tr.text2groundtruth(r"/home/max/Projects/Python/EstablishTruth/Greek lines4groundtruth/", "/home/max/Projects/Python/EstablishTruth/Greek lines2groundtruth/")
        tr.text2groundtruth(r"/home/max/Projects/Python/EstablishTruth/Greek lines4groundtruth/", "/home/max/Projects/Python/EstablishTruth/Greek lines2groundtruth/")
    
    def actionSplit_Latin_Text_Lines(self):
        print("splitting Latin textlines for ground truth")
        # usage: tr.splittextlines(source, destination)
        # tr.splittextlines(r"/home/max/Projects/Python/EstablishTruth/Latin txt4linesplit/", "/home/max/Projects/Python/EstablishTruth/Latin lines4groundtruth/")
        tr.splittextlines("/home/max/Projects/Python/EstablishTruth/Latin txt4linesplit/", "/home/max/Projects/Python/EstablishTruth/Latin lines4groundtruth/")

    def actionRename_Latin_Text_Lines(self):
        print("renaming Latin textlines for ground truth")
        # usage: tr.text2groundtruth(source, destination)
        #tr.text2groundtruth(r"/home/max/Projects/Python/EstablishTruth/Latin lines4groundtruth/", "/home/max/Projects/Python/EstablishTruth/Latin lines2groundtruth/")
        tr.text2groundtruth(r"/home/max/Projects/Python/EstablishTruth/Latin lines4groundtruth/", "/home/max/Projects/Python/EstablishTruth/Latin lines2groundtruth/")
    
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

    def GreekMonoToPngDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select greek mono tif pages source folder"))
        
        if self.directory:
            self.greekmono2png_ui.SourceLineEdit.setText(self.directory+r'/')

    def DestMonoToPngDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select destination folder"))
        
        if self.directory:
            self.mono2png_ui.DestinationLineEdit.setText(self.directory+r'/')

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

    def DeskewGreekMonoDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select greek pages source folder"))
        
        if self.directory:
            self.deskew_greekmono_ui.SourceLineEdit.setText(self.directory+r'/')

    def LatinMonoToPngDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select latin mono tif pages source folder"))
        
        if self.directory:
            self.latinmono2png_ui.SourceLineEdit.setText(self.directory+r'/')

    def DestMonoToPngDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select destination folder"))
        
        if self.directory:
            self.mono2png_ui.DestinationLineEdit.setText(self.directory+r'/')

    def LatinDestMonoToPngDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select destination folder"))
        
        if self.directory:
            self.latinmono2png_ui.DestinationLineEdit.setText(self.directory+r'/')

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

    def DeskewLatinMonoDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select mono tif pages source folder"))
        
        if self.directory:
            self.mono2png_ui.SourceLineEdit.setText(self.directory+r'/')

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
                
    def OpenImageFileDialog(self):
        self.imgpath = qtw.QFileDialog.getOpenFileName(
            self.ui.centralwidget, 'Open image file', self.imgdir,
            'Images (*.png *.xpm *.jpg *.bmp *.gif *.tif)')[0]
                
        if self.imgpath:
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
                    '''pmsize = qtg.QPixmap.fromImage(self.qimage).size()
                    print(pmsize)'''
                    self.origpixmap = qtg.QPixmap.fromImage(self.qimage)
                    pixmap = qtg.QPixmap.fromImage(self.qimage).scaled(self.ui.Image.size(), qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)
                    #pixmap = qtg.QPixmap.fromImage(self.qimage)   
                    self.ui.Image.setPixmap(qtg.QPixmap(pixmap))
                else:
                    
                    self.ui.Image.setPixmap(qtg.QPixmap(self.imgpath))
                
                file.close()

    def GetRawOCRtext(self):
        my_OCR_rawtext = pytesseract.image_to_string(self.imgpath,lang="feg")
        self.ui.OCRText.insertPlainText(my_OCR_rawtext)
        '''path = qtw.QFileDialog.getOpenFileName(
            self.ui.centralwidget, 'Open tif image file', '',
            'Images (*.tif)')[0]
        if path:
            file = qtc.QFile(path)
            if file.open(qtc.QIODevice.ReadOnly):
                info = qtc.QFileInfo(path)
                my_OCR_rawtext = pytesseract.image_to_string(path,lang="feg")
                #self.ui.OCRDocument.insertPlainText(my_OCR_rawtext)
                self.ui.OCRText.insertPlainText(my_OCR_rawtext)
                file.close()'''
    
    def GetLineSpacing(self, MainWindow):
        self.ui.LHslider.setEnabled(True)
        self.ui.LHlineEdit.setPlaceholderText(str(self.ui.LHslider.value()))

    def DisableSlider(self):
        self.ui.LHslider.setEnabled(False)

    def MoveSlider(self):
        self.ui.LHslider.setEnabled(True)
        self.ui.LHslider.setValue(int(self.ui.LHlineEdit.text()))
    
    def SetLineSpacing(self, MainWindow):
                
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
        
        if self.txtdir:
            defaultdir = self.txtdir
        else:
            defaultdir = r"/home/max/Projects/Python/EstablishTruth/Greek_txt_pages/"
        
        defaultfile = self.ui.TextLE.displayText()

        if defaultfile:
            path = defaultdir + defaultfile
            filename = defaultfile
        else:
            path = qtw.QFileDialog.getSaveFileName(
                self.centralwidget, 'Save Corrected text file', '',
                'Text files (*.txt)')[0]
            filename = os.path.basename(path)
        with open(path, 'w') as file:
            my_CorrectedText = self.ui.OCRDocument.toPlainText()
            file.write(my_CorrectedText)
        
        self.ui.TextLE.setText(filename)
        file.close()
    
    def show_combo(self):
        self.ui.ZoomComboBox.show()

    def on_zoom(self):
        seltext = self.ui.ZoomComboBox.currentText()
        if seltext != "Best_Fit":
            selnumtext = seltext.split(" ")
            print(selnumtext[0])
            self.scale = float(selnumtext[0])/100
            
            #self.scale *= 2
            print(self.scale)
            self.ui.ZoomComboBox.hide()
        self.resize_image()

    def resize_image(self):
        self.origsize = self.origpixmap.size()       
        if self.ui.ZoomComboBox.currentText() == "Best_Fit":
            self.origpixmap = qtg.QPixmap.fromImage(self.qimage)
            pixmap = qtg.QPixmap.fromImage(self.qimage).scaled(self.ui.Image.size(), qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)   
            self.ui.Image.setPixmap(qtg.QPixmap(pixmap))
        else:
            scaled_pixmap = self.origpixmap.scaled(self.scale * self.origsize, qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)
            self.ui.Image.setPixmap(scaled_pixmap)

    def OpenWithCalc(self):
        lo_cmd = 'libreoffice --calc ' + self.txtpath
        print(lo_cmd)
        os.system(lo_cmd)

    def OpenWithWriter(self):
        lo_cmd = 'libreoffice --writer ' + self.txtpath
        print(lo_cmd)
        os.system(lo_cmd)

    def ReloadImage(self):
        if self.imgpath:
            file = qtc.QFile(self.imgpath)
            filestr = os.path.basename(self.imgpath)
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
                    '''pmsize = qtg.QPixmap.fromImage(self.qimage).size()
                    print(pmsize)'''
                    self.origpixmap = qtg.QPixmap.fromImage(self.qimage)
                    pixmap = qtg.QPixmap.fromImage(self.qimage).scaled(self.ui.Image.size(), qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)
                    #pixmap = qtg.QPixmap.fromImage(self.qimage)   
                    self.ui.Image.setPixmap(qtg.QPixmap(pixmap))
                else:
                    
                    self.ui.Image.setPixmap(qtg.QPixmap(self.imgpath))

    def ReloadText(self):
        if self.txtpath:
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

    def on_font_update(self):
        # update font to selection and size       
        #font = qtg.QFont()
        #font.setFamily(self.ui.fontComboBox.currentFont())
        #print(self.ui.fontComboBox.currentFont())
        font = qtg.QFont(self.ui.fontComboBox.currentFont())
        font.setPointSize(self.ui.fontSizeBox.value())
        self.ui.OCRText.setFont(font)

    def on_lang_select(self):
        pass

# Only run this code if I am actually running this script
if __name__ == '__main__': 
    app = qtw.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec()