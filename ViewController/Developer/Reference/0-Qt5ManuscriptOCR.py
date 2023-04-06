from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QThread, pyqtSignal
import json
from SqliteHelper import *
import time
import UI_Icons
import MainUI
#import PdfExtract

app = QtWidgets.QApplication([])
#varui = uic.loadUi("/home/max/Projects/Python/Workflow/0-MainUI/MainUI.ui")

class Ui_MainWindow(object):
        
        def __init__(self):
            
            super().__init__()
            self.initUI()

        def initUI(self):
            self.varui = uic.loadUi("/home/max/Projects/Python/Workflow/0-MainUI/MainUI.ui")
            print("UI working")
            # put menu s here. Ex:
            #self.actionmove_pdf_for_tiff.triggered.connect()
            self.actionextract_pdf_tb.triggered.connect(self.extract_pdf)
            self.actionpdf_for_tiff_tb.triggered.connect(self.pdf_for_tiff)
            self.actionpdf_to_tiff__tb.triggered.connect(self.pdf_to_tiff)
            self.actiontiff_to_mono_tb.triggered.connect(self.tiff_to_mono)
            self.actionmono_to_png_tb.triggered.connect(self.mono_to_png)
            
            self.actionCrop_Languages_tb.triggered.connect(self.Crop_Languages)
            self.actionDeskewGreek_tiff_tb.triggered.connect(self.DeskewGreek_tiff)
            self.actionResizeGreek_png_tb.triggered.connect(self.ResizeGreek_png)
            self.actionDeskewLatin_tiff_tb.triggered.connect(self.DeskewLatin_tiff)
            self.actionResizeLastin_png_tb.triggered.connect(self.ResizeLastin_png)
            
            self.actionCrop_Greek_To_tiff_Lines_tb.triggered.connect(self.Crop_Greek_To_tiff_Lines)
            self.actionRename_Greek_tiff_Lines_tb.triggered.connect(self.Rename_Greek_tiff_Lines)
            self.actionMove_Greek_tiff_Lines_tb.triggered.connect(self.Move_Greek_tiff_Lines)
            
            self.actionCrop_Latin_To_tiff_Lines_tb.triggered.connect(self.Crop_Latin_To_tiff_Lines)
            self.actionRename_Latin_tiff_Lines_tb.triggered.connect(self.Rename_Latin_tiff_Lines)
            self.actionMove_Latin_tiff_Lines_tb.triggered.connect(self.Move_Latin_tiff_Lines)
            
            self.actionSplitGreek_text_lines_tb.triggered.connect(self.SplitGreek_text_lines)
            self.actionRenameGreek_text_lines_tb.triggered.connect(self.RenameGreek_text_lines)
            
            self.actionSplit_Latin_Text_Lines_tb.triggered.connect(self.Split_Latin_Text_Lines)
            self.actionRename_Latin_Text_Lines_tb.triggered.connect(self.Rename_Latin_Text_Lines)
            
            self.actionReview_Ground_Truth_tb.triggered.connect(self.Review_Ground_Truth)
            self.actionUpdate_Wordlist_tb.triggered.connect(self.Update_Wordlist)
            self.actionTrain_Tesseract_tb.triggered.connect(self.Train_Tesseract)
            self.actionCorrect_OCR_tb.triggered.connect(self.Correct_OCR)
            
            self.varui.show()

            def extract_pdf(self):
                print("extracting")
            def pdf_for_tiff(self):
                pass
            def pdf_to_tiff_(self):
                pass
            def iff_to_mono(self):
                pass
            def mono_to_png(self):
                pass
            def Crop_Languages(self):
                pass
            def DeskewGreek_tiff(self):
                pass
            def ResizeGreek_png(self):
                pass
            def DeskewLatin_tiff(self):
                pass
            def ResizeLastin_png(self):
                pass
            def Crop_Greek_To_tiff_Lines(self):
                pass
            def Rename_Greek_tiff_Lines(self):
                pass
            def Move_Greek_tiff_Lines(self):
                pass
            def Crop_Latin_To_tiff_Lines(self):
                pass
            def Rename_Latin_tiff_Lines(self):
                pass
            def Move_Latin_tiff_Lines(self):
                pass
            def SplitGreek_text_lines(self):
                pass
            def RenameGreek_text_lines(self):
                pass
            
            def Split_Latin_Text_Lines(self):
                pass
            def Rename_Latin_Text_Lines(self):
                pass
            
            def Review_Ground_Truth(self):
                pass
            def Update_Wordlist(self):
                pass
            def Train_Tesseract(self):
                pass
            def Correct_OCR(self):
                pass   


app.exec()