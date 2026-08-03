# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'OCRCorrection.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

import sys
import sys, os
from PyQt5 import QtCore, QtGui, QtWidgets
import pytesseract

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1300, 720)
        
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
                
        self.OCRbutton = QtWidgets.QPushButton(self.centralwidget)
        self.OCRbutton.setEnabled(True)
        self.OCRbutton.setGeometry(QtCore.QRect(530, 0, 100, 25))
        self.OCRbutton.setObjectName("OCRbutton")
        self.OCRbutton.setFont(QtGui.QFont('FROMVS', 8))
        self.OCRbutton.setIcon(QtGui.QIcon.fromTheme("gtk-execute"))
        self.OCRbutton.clicked.connect(self.GetRawOCRtext)
                
        '''self.SaveOCRRawTextbutton = QtWidgets.QPushButton(self.centralwidget)
        self.SaveOCRRawTextbutton.setEnabled(True)
        self.SaveOCRRawTextbutton.setGeometry(QtCore.QRect(650, 0, 100, 25))
        self.SaveOCRRawTextbutton.setObjectName("SaveOCRRawTextbutton")
        self.SaveOCRRawTextbutton.clicked.connect(self.SaveRawTextFileDialog)'''
            
        self.ImageLe = QtWidgets.QLineEdit(self.centralwidget)
        self.ImageLe.setGeometry(QtCore.QRect(299, 0, 201, 25))
        
        self.TextLe = QtWidgets.QLineEdit(self.centralwidget)
        self.TextLe.setGeometry(QtCore.QRect(759, 0, 201, 25))
        
        self.ImagescrollArea = QtWidgets.QScrollArea(self.centralwidget)
        self.ImagescrollArea.setGeometry(QtCore.QRect(0, 26, 520, 600))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ImagescrollArea.sizePolicy().hasHeightForWidth())
        self.ImagescrollArea.setSizePolicy(sizePolicy)
        self.ImagescrollArea.setMinimumSize(QtCore.QSize(501, 600))
        self.ImagescrollArea.setWidgetResizable(True)
        self.ImagescrollArea.setObjectName("ImagescrollArea")
        
        self.ImagescrollAreaWidgetContents = QtWidgets.QWidget()
        #self.ImagescrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 501, 1800))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ImagescrollAreaWidgetContents.sizePolicy().hasHeightForWidth())
        self.ImagescrollAreaWidgetContents.setSizePolicy(sizePolicy)
        self.ImagescrollAreaWidgetContents.setMinimumSize(QtCore.QSize(501, 1800))
        self.ImagescrollAreaWidgetContents.setObjectName("ImagescrollAreaWidgetContents")
        
        self.Image = QtWidgets.QLabel(self.ImagescrollAreaWidgetContents)
        self.Image.setGeometry(QtCore.QRect(0, 0, 521, 1680))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Image.sizePolicy().hasHeightForWidth())
        self.Image.setSizePolicy(sizePolicy)
        self.Image.setMinimumSize(QtCore.QSize(500, 1680))
        self.Image.setText("Image File")
        self.Image.setPixmap(QtGui.QPixmap("../../Images/Greek/jpg_desk_greek/greek_book_40_Matthew/greek1516_Page_011.jpg"))
        self.Image.setObjectName("Image")
        
        self.ImagescrollArea.setWidget(self.ImagescrollAreaWidgetContents)

        self.ChrRefplainTextEdit = QtWidgets.QPlainTextEdit(self.centralwidget)
        self.ChrRefplainTextEdit.setGeometry(QtCore.QRect(530, 26, 220, 600))
        font = QtGui.QFont()
        font.setFamily("FROMVS")
        font.setPointSize(18)
        self.ChrRefplainTextEdit.setFont(font)
        self.ChrRefplainTextEdit.setMinimumSize(QtCore.QSize(200, 600))
        self.ChrRefplainTextEdit.setObjectName("ChrRefplainTextEdit")
        ChrRefText = open('/home/max/Projects/Python/Workflow/3-ConductOCR/FROMVS ChrReference.txt').read()
        self.ChrRefplainTextEdit.setPlainText(ChrRefText)
        
        self.OCRText = QtWidgets.QTextEdit(self.centralwidget)
        self.OCRText.setGeometry(QtCore.QRect(760, 26, 540, 600))
        self.OCRText.setMinimumSize(QtCore.QSize(540, 600))
        self.OCRText.setAutoFillBackground(False)
        self.OCRText.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.OCRText.setObjectName("OCRText")
            
        self.OCRDocument = QtGui.QTextDocument(self.OCRText)
        font = QtGui.QFont()
        font.setFamily("FROMVS")
        font.setPointSize(20)
        self.OCRDocument.setDefaultFont(font)
        
        self.OCRDocument.setDefaultFont(font)
        self.OCRBlockFormat = QtGui.QTextBlockFormat()
        self.OCRTextFormat = QtGui.QTextFormat()
        self.OCRCursor = QtGui.QTextCursor(self.OCRDocument)
        
        self.OCRText.setDocument(self.OCRDocument)
        
        self.SetLineSpacingbutton = QtWidgets.QPushButton(self.centralwidget)
        self.SetLineSpacingbutton.setEnabled(True)
        self.SetLineSpacingbutton.setGeometry(QtCore.QRect(650, 0, 100, 25))
        self.SetLineSpacingbutton.setObjectName("SetLineSpacingbutton")
        self.SetLineSpacingbutton.setFont(QtGui.QFont('FROMVS', 8))
        self.SetLineSpacingbutton.setIcon(QtGui.QIcon.fromTheme("gtk-goto-top"))
        self.SetLineSpacingbutton.clicked.connect(self.SetLineSpacing)
        
        self.EditCorrectedTextbutton = QtWidgets.QPushButton(self.centralwidget)
        self.EditCorrectedTextbutton.setGeometry(QtCore.QRect(1040, 0, 60, 25))
        self.EditCorrectedTextbutton.setObjectName("EditCorrectedTextbutton")
        self.EditCorrectedTextbutton.setFont(QtGui.QFont('FROMVS', 8))
        self.EditCorrectedTextbutton.setIcon(QtGui.QIcon.fromTheme("gtk-open")) 
        self.EditCorrectedTextbutton.clicked.connect(self.OpenTextFileDialog)
        
        self.SaveAsOCRCorrTextbutton = QtWidgets.QPushButton(self.centralwidget)
        self.SaveAsOCRCorrTextbutton.setEnabled(True)
        self.SaveAsOCRCorrTextbutton.setGeometry(QtCore.QRect(1110, 0, 80, 25))
        self.SaveAsOCRCorrTextbutton.setObjectName("SaveAsOCRCorrTextbutton")
        self.SaveAsOCRCorrTextbutton.setFont(QtGui.QFont('FROMVS', 8))
        self.SaveAsOCRCorrTextbutton.setIcon(QtGui.QIcon.fromTheme("gtk-save-as"))
        self.SaveAsOCRCorrTextbutton.clicked.connect(self.SaveAsCorrectedTextFileDialog)

        self.SaveOCRCorrTextbutton = QtWidgets.QPushButton(self.centralwidget)
        self.SaveOCRCorrTextbutton.setEnabled(True)
        self.SaveOCRCorrTextbutton.setGeometry(QtCore.QRect(1200, 0, 80, 25))
        self.SaveOCRCorrTextbutton.setObjectName("SaveOCRCorrTextbutton")
        self.SaveOCRCorrTextbutton.setFont(QtGui.QFont('FROMVS', 8))
        self.SaveOCRCorrTextbutton.setIcon(QtGui.QIcon.fromTheme("gtk-save"))
        self.SaveOCRCorrTextbutton.clicked.connect(self.SaveCorrectedTextFileDialog)
                
        self.OpenImageFilebutton = QtWidgets.QPushButton(self.centralwidget)
        self.OpenImageFilebutton.setGeometry(QtCore.QRect(10, 0, 150, 25))
        self.OpenImageFilebutton.setObjectName("OpenImageFilebutton")
        self.OpenImageFilebutton.setFont(QtGui.QFont('FROMVS', 8))
        self.OpenImageFilebutton.setIcon(QtGui.QIcon.fromTheme("gtk-open"))
        self.OpenImageFilebutton.clicked.connect(self.OpenImageFileDialog)
        
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1300, 22))
        self.menubar.setObjectName("menubar")
        
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def OpenImageFileDialog(self, MainWindow):
        path = QtWidgets.QFileDialog.getOpenFileName(
            self.centralwidget, 'Open image file', '',
            'Images (*.png *.xpm *.jpg *.bmp *.gif)')[0]
                
        if path:
            file = QtCore.QFile(path)
            filestr = os.path.basename(path)
            self.ImageLe.setText(filestr)
            filesplit = os.path.splitext(filestr)
            filename = filesplit[0]
            fileext = filesplit[1]
                        
            if file.open(QtCore.QIODevice.ReadOnly):
                info = QtCore.QFileInfo(path)
                self.Image.setPixmap(QtGui.QPixmap(path))
                file.close()
    
    def GetRawOCRtext(self):
        path = QtWidgets.QFileDialog.getOpenFileName(
            self.centralwidget, 'Open tif image file', '',
            'Images (*.tif)')[0]
        if path:
            file = QtCore.QFile(path)
            if file.open(QtCore.QIODevice.ReadOnly):
                info = QtCore.QFileInfo(path)
                my_OCR_rawtext = pytesseract.image_to_string(path,lang="feg")
                #self.OCRDocument.insertPlainText(my_OCR_rawtext)
                self.OCRText.insertPlainText(my_OCR_rawtext)
                file.close()
    
    def SetLineSpacing(self, MainWindow):
        num,ok = QtWidgets.QInputDialog.getInt(self.centralwidget,"Proportional Line Spacing","Enter a percent value from 0-200")
        if ok:
            lineSpacing = num
        else:
            lineSpacing = 145
            
        cursor = self.OCRText.textCursor()
        if not cursor.hasSelection():
            cursor.select(QtGui.QTextCursor.Document)
        bf = self.OCRCursor.blockFormat()
        bf.setLineHeight(lineSpacing, self.OCRBlockFormat.ProportionalHeight) 
        cursor.mergeBlockFormat(bf)
    
    def OpenTextFileDialog(self, MainWindow):
        path = QtWidgets.QFileDialog.getOpenFileName(
            self.centralwidget, 'Open text file', '',
            'Text files (*.txt)')[0]
        if path:
            file = QtCore.QFile(path)
            filename = os.path.basename(path)
            self.TextLe.setText(filename)
            if file.open(QtCore.QIODevice.ReadOnly):
                stream = QtCore.QTextStream(file)
                text = stream.readAll()
                info = QtCore.QFileInfo(path)
                if info.completeSuffix() == 'txt':
                    #self.editor_text.setHtml(text)
                    self.OCRText.insertPlainText(text)
                else:
                    self.OCRText.setPlainText(text)
                file.close()
        
    def SaveRawTextFileDialog(self, MainWindow):
        path = QtWidgets.QFileDialog.getSaveFileName(
            self.centralwidget, 'Save Raw text file', '',
            'Text files (*.txt)')[0]
        with open(path, 'w') as file:
            my_RawText = self.OCRDocument.toPlainText()
            file.write(my_RawText)
        filename = os.path.basename(path)
        self.TextLe.setText(filename)
        file.close()
        
    def SaveAsCorrectedTextFileDialog(self, MainWindow):
        path = QtWidgets.QFileDialog.getSaveFileName(
            self.centralwidget, 'Save Corrected text file', '',
            'Text files (*.txt)')[0]
        with open(path, 'w') as file:
            my_CorrectedText = self.OCRDocument.toPlainText()
            file.write(my_CorrectedText)
        filename = os.path.basename(path)
        self.TextLe.setText(filename)
        file.close()

    def SaveCorrectedTextFileDialog(self, MainWindow):
        
        defaultdir = r"/home/max/Projects/Python/EstablishTruth/Greek txt pages/greek_book_40_Matthew/"
        defaultfile = self.TextLe.displayText()

        if defaultfile:
            path = defaultdir + defaultfile
            filename = defaultfile
        else:
            path = QtWidgets.QFileDialog.getSaveFileName(
                self.centralwidget, 'Save Corrected text file', '',
                'Text files (*.txt)')[0]
            filename = os.path.basename(path)
        with open(path, 'w') as file:
            my_CorrectedText = self.OCRDocument.toPlainText()
            file.write(my_CorrectedText)
        
        self.TextLe.setText(filename)
        file.close()
    
    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "OCR Correction"))
        self.OpenImageFilebutton.setText(_translate("MainWindow", "Open Image"))
        self.OCRbutton.setText(_translate("MainWindow", "OCR Raw"))
        #self.SaveOCRRawTextbutton.setText(_translate("MainWindow", "Save Raw"))
        self.SetLineSpacingbutton.setText(_translate("MainWindow", "Line Height"))
        self.EditCorrectedTextbutton.setText(_translate("MainWindow", "Open"))
        self.SaveAsOCRCorrTextbutton.setText(_translate("MainWindow", "Save As"))
        self.SaveOCRCorrTextbutton.setText(_translate("MainWindow", "Save"))

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

