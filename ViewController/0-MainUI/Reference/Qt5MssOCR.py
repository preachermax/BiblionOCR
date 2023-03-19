#print(len(locals()))

# Python imports
import sys
import os
import pytesseract
import tiffcapture
import qimage2ndarray
# PyQt5 imports
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc
# Custom imports
from MainUI import Ui_MainUI
from PreProcess import PreProcess as pp
from Training import Train as tr
#from DeskewFiles import DeskewFileList as dsk

#print(len(locals()))

class MainWindow(qtw.QMainWindow):

# Menu and Toolbar Action Methods 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # pre-compiled QtDesigner Ui_MainUI and extended slots code starts here:
        
        # load the pre-compiled QtDesigner Ui_MainUI user interface
        self.ui = Ui_MainUI()
        self.ui.setupUi(self)

        # extended slots code
        self.ui.actionextract_pdf_tb.triggered.connect(self.actionextract_pdf)      
        self.ui.actionpdf_for_tiff_tb.triggered.connect(self.actionpdf_for_tiff)
        self.ui.actionpdf_to_tiff_tb.triggered.connect(self.actionpdf_to_tiff)
        self.ui.actiontiff_to_mono_tb.triggered.connect(self.actiontiff_to_mono)
        self.ui.actiondeskew_mono.triggered.connect(self.actiondeskew_mono)
        self.ui.actionmono_to_png_tb.triggered.connect(self.actionmono_to_png)
        self.ui.actionCrop_Languages_tb.triggered.connect(self.actionCrop_Languages)
        self.ui.actionDeskewGreek_tiff_tb.triggered.connect(self.actionDeskewGreek_tiff)
        self.ui.actionResizeGreek_png_tb.triggered.connect(self.actionResizeGreek_png)
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
        
        # UI and slots code ends here.
        
        # Show the Main user interface

        self.show()
    
    def actionextract_pdf(self):
        print("extracting")
        #usage: pdf4tiff(source, destination,firstpage,lastpage)
        #pp.pdf4tiff('./Images/Source/pdf_source/1516.pdf', './Images/Source/pdf_source/','51','60')
        pp.pdf4tiff('./Images/Source/pdf_source/1516.pdf', './Images/Source/pdf_source/','51','60')

    def actionpdf_for_tiff(self):
        print("creating pdf for tiff")
        #usage: pdf2tiff(source, destination)
        #pp.pdf2tiff('./Images/Source/pdf_source/1516_Page_51-60.pdf', './Images/Source/pdf4tif/')
        pp.pdf2tiff('./Images/Source/pdf_source/1516_Page_51-60.pdf', './Images/Source/pdf4tif/')
    
    def actionpdf_to_tiff(self):
        print("creating pdf to tiff")
        #usage: pdf2tif(source, destination, startpagenum)
        #pp.pdf2tif(r"/home/max/Projects/Python/Images/Source/pdf4tif/", "/home/max/Projects/Python/Images/Source/pdf2tif/","51")
        pp.pdf2tif(r"/home/max/Projects/Python/Images/Source/pdf4tif/", "/home/max/Projects/Python/Images/Source/pdf2tif/","51")

    def actiontiff_to_mono(self):
        print("creating indexed(BW) tiff")
        #usage: pp.tiff2tiffidx(source, destination)
        #pp.tiff2tiffidx("/home/max/Projects/Python/Images/Source/pdf2tif/", "/home/max/Projects/Python/Images/Source/tif_black_white/source_book_40_Matthew/")
        pp.tiff2tiffidx("/home/max/Projects/Python/Images/Source/pdf2tif/", "/home/max/Projects/Python/Images/Source/tif_black_white/source_book_40_Matthew/")

    def actiondeskew_mono(self):
        print("deskewing monochrome tiff files")
        #usage: dsk.deskewfiles(source, pngdest, tifdest)
        #dsk.deskewfiles("/home/max/Projects/Python/Images/Source/tif_black_white/source_book_40_Matthew/", "/home/max/Projects/Python/Images/Source/png_black_white_deskew/","/home/max/Projects/Python/Images/Source/tiff_black_white_deskew/")
        pp.deskewfiles("/home/max/Projects/Python/Images/Source/tif_black_white/source_book_40_Matthew/", "/home/max/Projects/Python/Images/Source/png_black_white_deskew/","/home/max/Projects/Python/Images/Source/tiff_black_white_deskew/")

    def actionmono_to_png(self):
        print("creating indexed(BW) png")
        #usage: pp.tiff2pngidx(source, destination)
        #pp.tiff2pngidx(r"/home/max/Projects/Python/Images/Source/tif_black_white/source_book_40_Matthew/", "/home/max/Projects/Python/Images/Source/tif_black_white_2png/source_book_40_Matthew/")
        pp.tiff2pngidx(r"/home/max/Projects/Python/Images/Source/tiff_black_white_deskew/", "/home/max/Projects/Python/Images/Source/tif_black_white_2png/source_book_40_Matthew/")
        
    def actionCrop_Languages(self):
        print("creating indexed(BW) png")
        #usage: pp.croplangs(source, boxdir, greekdir, latindir, elimdir)
        #pp.croplangs(r"/home/max/Projects/Python/Images/Source/tif_black_white_2png/source_book_40_Matthew/", "/home/max/Projects/Python/Images/Source/tif_box/lang_box/source_book_40_Matthew/","/home/max/Projects/Python/Images/Greek/tif_greek/greek_book_40_Matthew/","/home/max/Projects/Python/Images/Latin/tif_latin/latin_book_40_Matthew/","/home/max/Projects/Python/Images/Source/tif_eliminated/source_book_40_Matthew/")
        pp.croplangs(r"/home/max/Projects/Python/Images/Source/tif_black_white_2png/source_book_40_Matthew/", "/home/max/Projects/Python/Images/Source/tif_box/lang_box/source_book_40_Matthew/","/home/max/Projects/Python/Images/Greek/tif_greek/greek_book_40_Matthew/","/home/max/Projects/Python/Images/Latin/tif_latin/latin_book_40_Matthew/","/home/max/Projects/Python/Images/Source/tif_eliminated/source_book_40_Matthew/")
    
    def actionDeskewGreek_tiff(self):
        print("deskewing Greek tiff files")
        #usage: dsk.deskewfiles(source, pngdest, tifdest)
        #dsk.deskewfiles("/home/max/Projects/Python/Images/Greek/png_greek/greek_book_40_Matthew/", "/home/max/Projects/Python/Images/Greek/png_greek_deskew/greek_book_40_Matthew/","/home/max/Projects/Python/Images/Greek/tif_greek_deskew/greek_book_40_Matthew/")
        pp.deskewfiles("/home/max/Projects/Python/Images/Greek/png_greek/greek_book_40_Matthew/", "/home/max/Projects/Python/Images/Greek/png_greek_deskew/greek_book_40_Matthew/","/home/max/Projects/Python/Images/Greek/tif_greek_deskew/greek_book_40_Matthew/")
    
    def actionResizeGreek_png(self):
        print("resizing Greek png files")
        #usage: pp.resizepngs(source, destination)
        #pp.resizepngs(r"/home/max/Projects/Python/Images/Greek/png_greek_deskew/greek_book_40_Matthew/","/home/max/Projects/Python/Images/Greek/png_greek_resize/greek_book_40_Matthew/")
        pp.resizepngs(r"/home/max/Projects/Python/Images/Greek/png_greek_deskew/greek_book_40_Matthew/","/home/max/Projects/Python/Images/Greek/png_greek_resize/greek_book_40_Matthew/")
    
    def actionDeskewLatin_tiff(self):
        print("deskewing Latin tiff files")
        #usage: dsk.deskewfiles(source, pngdest, tifdest)
        #dsk.deskewfiles("/home/max/Projects/Python/Images/Latin/png_latin/latin_book_40_Matthew/", "/home/max/Projects/Python/Images/Latin/png_latin_deskew/latin_book_40_Matthew/","/home/max/Projects/Python/Images/Latin/tif_latin_deskew/latin_book_40_Matthew/")
        pp.deskewfiles("/home/max/Projects/Python/Images/Latin/png_latin/latin_book_40_Matthew/", "/home/max/Projects/Python/Images/Latin/png_latin_deskew/latin_book_40_Matthew/","/home/max/Projects/Python/Images/Latin/tif_latin_deskew/latin_book_40_Matthew/")
    
    def actionResizeLatin_png(self):
        print("resizing Latin png files")
        #usage: pp.resizepngs(source, destination)
        #pp.resizepngs(r"/home/max/Projects/Python/Images/Greek/png_greek_deskew/greek_book_40_Matthew/","/home/max/Projects/Python/Images/Greek/png_greek_resize/greek_book_40_Matthew/")
        pp.resizepngs(r"/home/max/Projects/Python/Images/Greek/png_greek_deskew/greek_book_40_Matthew/","/home/max/Projects/Python/Images/Greek/png_greek_resize/greek_book_40_Matthew/")
    
    def actionCrop_Greek_To_tiff_Lines(self):
        print("cropping and sorting Greek tiff lines")
        #usage: tr.sortcroplines(source, splitdir, linebox)
        #tr.sortcroplines(r"/home/max/Projects/Python/Images/Greek/png_greek_deskew/greek_book_40_Matthew/","/home/max/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_40_Matthew/","/home/max/Projects/Python/Images/Greek/tif_greek_linebox/greek_book_40_Matthew/")
        tr.sortcroplines(r"/home/max/Projects/Python/Images/Greek/png_greek_deskew/greek_book_40_Matthew/","/home/max/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_40_Matthew/","/home/max/Projects/Python/Images/Greek/tif_greek_linebox/greek_book_40_Matthew/")
        
    def actionRename_Greek_tiff_Lines(self):
        print("renaming Greek tiff lines for ground truth")
        # usage: tr.renameimages(source, destination)
        # tr.renameimages(r"/home/max/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_40_Matthew/", "/home/max/Projects/Python/Images/Greek/tif_greek_tif4groundtruth/")
        tr.renameimages(r"/home/max/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_40_Matthew/", "/home/max/Projects/Python/Images/Greek/tif_greek_tif4groundtruth/")
       
    def actionMove_Greek_tiff_Lines(self):
        pass

    def actionCrop_Latin_To_tiff_Lines(self):
        print("cropping and sorting Latin tiff lines")
        #usage: tr.sortcroplines(source, splitdir, linebox)
        #tr.sortcroplines(r"/home/max/Projects/Python/Images/Latin/png_latin_deskew/latin_book_40_Matthew/","/home/max/Projects/Python/Images/Latin/tif_latin_autosplit/latin_book_40_Matthew/","/home/max/Projects/Python/Images/Latin/tif_latin_linebox/latin_book_40_Matthew/")
        tr.sortcroplines(r"/home/max/Projects/Python/Images/Latin/png_latin_deskew/latin_book_40_Matthew/","/home/max/Projects/Python/Images/Latin/tif_latin_autosplit/latin_book_40_Matthew/","/home/max/Projects/Python/Images/Latin/tif_latin_linebox/latin_book_40_Matthew/")

    def actionRename_Latin_tiff_Lines(self):
        print("renaming Latin tiff lines for ground truth")
        # usage: tr.renameimages(source, destination)
        # tr.renameimages(r"/home/max/Projects/Python/Images/Latin/tif_latin_autosplit/latin_book_40_Matthew/", "/home/max/Projects/Python/Images/Latin/tif_latin_tif4groundtruth/")
        tr.renameimages(r"/home/max/Projects/Python/Images/Latin/tif_latin_autosplit/latin_book_40_Matthew/", "/home/max/Projects/Python/Images/Latin/tif_latin_tif4groundtruth/")

    def actionMove_Latin_tiff_Lines(self):
        pass

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
        pass
    def actionUpdate_Wordlist(self):
        pass
    def actionTrain_Tesseract(self):
        pass
    def actionCorrect_OCR(self):
        pass
    
# Only run this code if I am actually running this script
if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec()
