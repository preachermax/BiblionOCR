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
        self.OCRbutton.setGeometry(QtCore.QRect(540, 60, 201, 25))
        self.OCRbutton.setObjectName("OCRbutton")
        self.OCRbutton.clicked.connect(self.GetRawOCRtext)
                
        self.SaveOCRRawTextbutton = QtWidgets.QPushButton(self.centralwidget)
        self.SaveOCRRawTextbutton.setEnabled(True)
        self.SaveOCRRawTextbutton.setGeometry(QtCore.QRect(540, 100, 201, 25))
        self.SaveOCRRawTextbutton.setObjectName("SaveOCRRawTextbutton")
        self.SaveOCRRawTextbutton.clicked.connect(self.SaveRawTextFileDialog)
        
        self.ImageAreaTitlelabel = QtWidgets.QLabel(self.centralwidget)
        self.ImageAreaTitlelabel.setGeometry(QtCore.QRect(10, 0, 171, 20))
        self.ImageAreaTitlelabel.setObjectName("ImageAreaTitlelabel")
        
        self.OCRTextAreaTitlelabel = QtWidgets.QLabel(self.centralwidget)
        self.OCRTextAreaTitlelabel.setGeometry(QtCore.QRect(960, 0, 141, 20))
        self.OCRTextAreaTitlelabel.setObjectName("OCRTextAreaTitlelabel")
        
        self.ChrRefTitlelabel = QtWidgets.QLabel(self.centralwidget)
        self.ChrRefTitlelabel.setGeometry(QtCore.QRect(560, 230, 141, 20))
        self.ChrRefTitlelabel.setObjectName("ChrRefTitlelabel")
        
        self.ImagescrollArea = QtWidgets.QScrollArea(self.centralwidget)
        self.ImagescrollArea.setGeometry(QtCore.QRect(0, 20, 520, 700))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ImagescrollArea.sizePolicy().hasHeightForWidth())
        self.ImagescrollArea.setSizePolicy(sizePolicy)
        self.ImagescrollArea.setMinimumSize(QtCore.QSize(501, 700))
        self.ImagescrollArea.setWidgetResizable(True)
        self.ImagescrollArea.setObjectName("ImagescrollArea")
        
        self.ImagescrollAreaWidgetContents = QtWidgets.QWidget()
        self.ImagescrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 501, 1800))
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
        #self.Image.setPixmap(QtGui.QPixmap("../../Images/Greek/jpg_desk_greek/greek_book_40_Matthew/greek1516_Page_011.jpg"))
        self.Image.setObjectName("Image")
        
        self.ImagescrollArea.setWidget(self.ImagescrollAreaWidgetContents)
        
        self.ChrRefscrollArea = QtWidgets.QScrollArea(self.centralwidget)
        self.ChrRefscrollArea.setGeometry(QtCore.QRect(530, 250, 220, 500))
        self.ChrRefscrollArea.setWidgetResizable(True)
        self.ChrRefscrollArea.setObjectName("ChrRefscrollArea")
        
        self.ChrRefcrollAreaWidgetContents = QtWidgets.QWidget()
        self.ChrRefcrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 220, 500))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ChrRefcrollAreaWidgetContents.sizePolicy().hasHeightForWidth())
        self.ChrRefcrollAreaWidgetContents.setSizePolicy(sizePolicy)
        self.ChrRefcrollAreaWidgetContents.setMinimumSize(QtCore.QSize(201, 2000))
        self.ChrRefcrollAreaWidgetContents.setObjectName("ChrRefcrollAreaWidgetContents")
        
        self.ChrRefplainTextEdit = QtWidgets.QPlainTextEdit(self.ChrRefcrollAreaWidgetContents)
        self.ChrRefplainTextEdit.setGeometry(QtCore.QRect(0, 0, 220, 1680))
        font = QtGui.QFont()
        font.setFamily("FROMVS")
        font.setPointSize(18)
        self.ChrRefplainTextEdit.setFont(font)
        self.ChrRefplainTextEdit.setMinimumSize(QtCore.QSize(200, 1680))
        self.ChrRefplainTextEdit.setObjectName("ChrRefplainTextEdit")
        ChrRefText = open('/home/max/Projects/Python/Workflow/3-ConductOCR/FROMVS ChrReference.txt').read()
        self.ChrRefplainTextEdit.setPlainText(ChrRefText)
        
        self.ChrRefscrollArea.setWidget(self.ChrRefcrollAreaWidgetContents)
        
        self.OCRTextscrollArea = QtWidgets.QScrollArea(self.centralwidget)
        self.OCRTextscrollArea.setGeometry(QtCore.QRect(760, 20, 540, 700))
        self.OCRTextscrollArea.setAcceptDrops(False)
        self.OCRTextscrollArea.setWidgetResizable(True)
        self.OCRTextscrollArea.setObjectName("OCRTextscrollArea")
        
        self.OCRTextscrollAreaWidgetContents = QtWidgets.QWidget()
        self.OCRTextscrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 540, 1700))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.OCRTextscrollAreaWidgetContents.sizePolicy().hasHeightForWidth())
        self.OCRTextscrollAreaWidgetContents.setSizePolicy(sizePolicy)
        self.OCRTextscrollAreaWidgetContents.setMinimumSize(QtCore.QSize(540, 1700))
        self.OCRTextscrollAreaWidgetContents.setObjectName("OCRTextscrollAreaWidgetContents")
        
        self.OCRText = QtWidgets.QTextEdit(self.OCRTextscrollAreaWidgetContents)
        self.OCRText.setGeometry(QtCore.QRect(0, 0, 540, 1702))
        self.OCRText.setMinimumSize(QtCore.QSize(540, 1702))
        font = QtGui.QFont()
        font.setFamily("FROMVS")
        font.setPointSize(20)
        self.OCRText.setFont(font)
        self.OCRText.setAutoFillBackground(False)
        self.OCRText.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.OCRText.setObjectName("OCRText")
        
        self.OCRTextscrollArea.setWidget(self.OCRTextscrollAreaWidgetContents)
        
        self.EditCorrectedTextbutton = QtWidgets.QPushButton(self.centralwidget)
        self.EditCorrectedTextbutton.setGeometry(QtCore.QRect(540, 150, 201, 25))
        self.EditCorrectedTextbutton.setObjectName("EditCorrectedTextbutton")
        self.EditCorrectedTextbutton.clicked.connect(self.OpenTextFileDialog)
        
        self.SaveOCRCorrTextbutton = QtWidgets.QPushButton(self.centralwidget)
        self.SaveOCRCorrTextbutton.setEnabled(True)
        self.SaveOCRCorrTextbutton.setGeometry(QtCore.QRect(540, 190, 201, 25))
        self.SaveOCRCorrTextbutton.setObjectName("SaveOCRCorrTextbutton")
        self.SaveOCRCorrTextbutton.clicked.connect(self.SaveCorrectedTextFileDialog)
        
        self.OpenImageFilebutton = QtWidgets.QPushButton(self.centralwidget)
        self.OpenImageFilebutton.setGeometry(QtCore.QRect(542, 20, 201, 25))
        self.OpenImageFilebutton.setObjectName("OpenImageFilebutton")
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
            if file.open(QtCore.QIODevice.ReadOnly):
                info = QtCore.QFileInfo(path)
                self.Image.setPixmap(QtGui.QPixmap(path))
                file.close()
    
    def GetRawOCRtext(self):
        #ImageFileName = os.path.filename(self.Image.QPixmap)
        path = QtWidgets.QFileDialog.getOpenFileName(
            self.centralwidget, 'Open tif image file', '',
            'Images (*.tif)')[0]
        if path:
            file = QtCore.QFile(path)
            if file.open(QtCore.QIODevice.ReadOnly):
                info = QtCore.QFileInfo(path)
                my_OCR_rawtext = pytesseract.image_to_string(path,lang="feg")
                self.OCRText.insertPlainText(my_OCR_rawtext)
                file.close()
    
    def OpenTextFileDialog(self, MainWindow):
        path = QtWidgets.QFileDialog.getOpenFileName(
            self.centralwidget, 'Open text file', '',
            'Text files (*.txt)')[0]
        if path:
            file = QtCore.QFile(path)
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
            my_RawText = self.OCRText.toPlainText()
            file.write(my_RawText)
        file.close()
        
    def SaveCorrectedTextFileDialog(self, MainWindow):
        path = QtWidgets.QFileDialog.getSaveFileName(
            self.centralwidget, 'Save Corrected text file', '',
            'Text files (*.txt)')[0]
        with open(path, 'w') as file:
            my_CorrectedText = self.OCRText.toPlainText()
            file.write(my_CorrectedText)
        file.close()
    
    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "OCR Correction"))
        self.OCRbutton.setText(_translate("MainWindow", "Generate OCR Raw Text"))
        self.SaveOCRRawTextbutton.setText(_translate("MainWindow", "Save Raw Text File"))
        self.ImageAreaTitlelabel.setText(_translate("MainWindow", "Image to Recognize OCR"))
        self.OCRTextAreaTitlelabel.setText(_translate("MainWindow", "OCR Text File to Edit"))
        self.ChrRefTitlelabel.setText(_translate("MainWindow", "Character Reference"))
        self.EditCorrectedTextbutton.setText(_translate("MainWindow", "Edit Corrected Text"))
        self.SaveOCRCorrTextbutton.setText(_translate("MainWindow", "Save Corrected Text File"))
        self.OpenImageFilebutton.setText(_translate("MainWindow", "Open Image File"))

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

