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
        self.ChrRefTitlelabel.setGeometry(QtCore.QRect(560, 260, 141, 20))
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
        self.ChrRefscrollArea.setGeometry(QtCore.QRect(530, 280, 220, 500))
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
            
        self.OCRDocument = QtGui.QTextDocument(self.OCRText)
        font = QtGui.QFont()
        font.setFamily("FROMVS")
        font.setPointSize(20)
        
        self.OCRDocument.setDefaultFont(font)
        self.OCRBlockFormat = QtGui.QTextBlockFormat()
        
        lineHeight = 200
        lineHeightType = self.OCRBlockFormat.ProportionalHeight
        bf = self.OCRBlockFormat
        #my_text_block = self.OCRText.textCursor().setBlockFormat(bf)
        #self.OCRText.insertPlainText(my_text_block)
        #lineCount = 0
        block = self.OCRDocument.begin()
        while block != self.OCRDocument.end(): 
            #block.isValid()
            #tc = self.QTextCursor(block)
            fmt = bf.setLineHeight(lineHeight, lineHeightType)
            cursor = QtGui.QTextCursor.StartOfBlock
            cursor = QtGui.QTextCursor.movePosition(QtGui.QTextCursor.EndOfBlock, QtGui.QTextCursor.KeepAnchor)
               #if (fmt.topMargin() != lineSpacing or fmt.bottomMargin() != lineSpacing):
                #fmt.setTopMargin(lineSpacing)
                #fmt.setBottomMargin(lineSpacing)
            self.OCRText.insertPlainText(cursor.setBlockFormat(fmt))
            block = block.next()
            #lineCount += 1 
        
        #self.OCRBlockFormat = QtGui.QTextBlockFormat()
        #self.OCRCursor = QtGui.QTextCursor(self.OCRDocument)
        #self.OCRTextSelection = self.OCRCursor.select(QtGui.QTextCursor.Document)
        #self.OCRTextSelection.setBlockFormat(self.OCRBlockFormat.setLineHeight(200,QtGui.QTextBlockFormat.ProportionalHeight))
        
               
        self.OCRText.setDocument(self.OCRDocument)
    
        #PySide.QtGui.QTextBlockFormat.setLineHeight(height, heightType)
        #Parameters:	
        #height – PySide.QtCore.qreal
        #heightType – PySide.QtCore.int
        #Sets the line height for the paragraph to the value given by height which is dependent on heightType in the way described by the QTextBlockFormat.LineHeightTypes enum.
        #PySide.QtGui.QTextBlockFormat.LineHeightTypes
        #This enum describes the various types of line spacing support paragraphs can have.
        #Constant	                            Description
        #QTextBlockFormat.SingleHeight	        This is the default line height: single spacing.
        #QTextBlockFormat.ProportionalHeight	This sets the spacing proportional to the line (in percentage). For example, set to 200 for double spacing.
        #QTextBlockFormat.FixedHeight	        This sets the line height to a fixed line height (in pixels).
        #QTextBlockFormat.MinimumHeight	        This sets the minimum line height (in pixels).
        #QTextBlockFormat.LineDistanceHeight	This adds the specified height between lines (in pixels).
        self.OCRTextFormat = QtGui.QTextFormat()
        #PySide.QtGui.QTextCursor.setBlockFormat(format)
        #Parameters:	format – PySide.QtGui.QTextBlockFormat
        #Sets the block format of the current block (or all blocks that are contained in the selection) to format .
        
        
        self.OCRTextscrollArea.setWidget(self.OCRTextscrollAreaWidgetContents)
        
        self.SetLineSpacingbutton = QtWidgets.QPushButton(self.centralwidget)
        self.SetLineSpacingbutton.setEnabled(True)
        self.SetLineSpacingbutton.setGeometry(QtCore.QRect(540, 140, 201, 25))
        self.SetLineSpacingbutton.setObjectName("SetLineSpacingbutton")
        self.SetLineSpacingbutton.clicked.connect(lambda *args:self.SetLineSpacing)
        
        self.EditCorrectedTextbutton = QtWidgets.QPushButton(self.centralwidget)
        self.EditCorrectedTextbutton.setGeometry(QtCore.QRect(540, 180, 201, 25))
        self.EditCorrectedTextbutton.setObjectName("EditCorrectedTextbutton")
        self.EditCorrectedTextbutton.clicked.connect(self.OpenTextFileDialog)
        
        self.SaveOCRCorrTextbutton = QtWidgets.QPushButton(self.centralwidget)
        self.SaveOCRCorrTextbutton.setEnabled(True)
        self.SaveOCRCorrTextbutton.setGeometry(QtCore.QRect(540, 220, 201, 25))
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
                #self.OCRDocument.insertPlainText(my_OCR_rawtext)
                self.OCRText.insertPlainText(my_OCR_rawtext)
                file.close()
    
    def SetLineSpacing(self, MainWindow):
        lineHeight = 200
        lineHeightType = self.OCRBlockFormat.ProportionalHeight
        bf = self.OCRBlockFormat
        #my_text_block = self.OCRText.textCursor().setBlockFormat(bf)
        #self.OCRText.insertPlainText(my_text_block)
        #lineCount = 0
        block = self.OCRDocument.begin()
        while block != self.OCRDocument.end(): 
            #block.isValid()
            #tc = self.QTextCursor(block)
            fmt = bf.setLineHeight(lineHeight, lineHeightType)
            cursor = QtGui.QTextCursor.StartOfBlock
            cursor = QtGui.QTextCursor.moveposition(QtGui.QTextCursor.EndOfBlock, QtGui.QTextCursor.KeepAnchor)
               #if (fmt.topMargin() != lineSpacing or fmt.bottomMargin() != lineSpacing):
                #fmt.setTopMargin(lineSpacing)
                #fmt.setBottomMargin(lineSpacing)
            self.OCRText.insertPlainText(cursor.setBlockFormat(fmt))
            block = block.next()
            #lineCount += 1 
    
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
        self.OpenImageFilebutton.setText(_translate("MainWindow", "Open Image File"))
        self.OCRbutton.setText(_translate("MainWindow", "Generate OCR Raw Text"))
        self.SaveOCRRawTextbutton.setText(_translate("MainWindow", "Save Raw Text File"))
        self.SetLineSpacingbutton.setText(_translate("MainWindow", "Set Line Spacing"))
        self.EditCorrectedTextbutton.setText(_translate("MainWindow", "Edit Corrected Text"))
        self.SaveOCRCorrTextbutton.setText(_translate("MainWindow", "Save Corrected Text File"))
        self.ImageAreaTitlelabel.setText(_translate("MainWindow", "Image to Recognize OCR"))
        self.OCRTextAreaTitlelabel.setText(_translate("MainWindow", "OCR Text File to Edit"))
        self.ChrRefTitlelabel.setText(_translate("MainWindow", "Character Reference"))
        
        

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

