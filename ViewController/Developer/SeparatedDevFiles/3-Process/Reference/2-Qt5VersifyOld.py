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
                         
        self.VerseTextLe = QtWidgets.QLineEdit(self.centralwidget)
        self.VerseTextLe.setGeometry(QtCore.QRect(330, 0, 201, 25))
        
        self.TextLe = QtWidgets.QLineEdit(self.centralwidget)
        self.TextLe.setGeometry(QtCore.QRect(769, 0, 201, 25))
        
        self.VerseText = QtWidgets.QTextEdit(self.centralwidget)
        self.VerseText.setGeometry(QtCore.QRect(0, 26, 520, 600))
        self.VerseText.setMinimumSize(QtCore.QSize(520, 600))
        self.VerseText.setAutoFillBackground(False)
        self.VerseText.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
        self.VerseText.setObjectName("VerseText")
        
        self.VerseDocument = QtGui.QTextDocument(self.VerseText)
        font = QtGui.QFont()
        font.setFamily("FROMVS")
        font.setPointSize(20)
        self.VerseDocument.setDefaultFont(font)
        
        self.VerseDocument.setDefaultFont(font)
        self.VerseBlockFormat = QtGui.QTextBlockFormat()
        self.VerseTextFormat = QtGui.QTextFormat()
        self.VerseCursor = QtGui.QTextCursor(self.VerseDocument)
        
        self.VerseText.setDocument(self.VerseDocument)
        
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
        self.OCRText.setGeometry(QtCore.QRect(760, 26, 520, 600))
        self.OCRText.setMinimumSize(QtCore.QSize(520, 600))
        self.OCRText.setAutoFillBackground(False)
        self.OCRText.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
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
        self.SetLineSpacingbutton.setGeometry(QtCore.QRect(980, 0, 100, 25))
        self.SetLineSpacingbutton.setObjectName("SetLineSpacingbutton")
        self.SetLineSpacingbutton.clicked.connect(self.SetLineSpacing)
        
        self.EditCorrectedTextbutton = QtWidgets.QPushButton(self.centralwidget)
        self.EditCorrectedTextbutton.setGeometry(QtCore.QRect(1090, 0, 100, 25))
        self.EditCorrectedTextbutton.setObjectName("EditCorrectedTextbutton")
        self.EditCorrectedTextbutton.clicked.connect(self.OpenTextFileDialog)
        
        self.SaveOCRCorrTextbutton = QtWidgets.QPushButton(self.centralwidget)
        self.SaveOCRCorrTextbutton.setEnabled(True)
        self.SaveOCRCorrTextbutton.setGeometry(QtCore.QRect(1200, 0, 100, 25))
        self.SaveOCRCorrTextbutton.setObjectName("SaveOCRCorrTextbutton")
        self.SaveOCRCorrTextbutton.clicked.connect(self.SaveCorrectedTextFileDialog)
        
        self.OpenVerseTextbutton = QtWidgets.QPushButton(self.centralwidget)
        self.OpenVerseTextbutton.setGeometry(QtCore.QRect(10, 0, 150, 25))
        self.OpenVerseTextbutton.setObjectName("OpenVerseTextbutton")
        self.OpenVerseTextbutton.clicked.connect(self.OpenVerseTextDialog)
        
        self.SaveVerseTextbutton = QtWidgets.QPushButton(self.centralwidget)
        self.SaveVerseTextbutton.setEnabled(True)
        self.SaveVerseTextbutton.setGeometry(QtCore.QRect(170, 0, 150, 25))
        self.SaveVerseTextbutton.setObjectName("SaveVerseTextbutton")
        self.SaveVerseTextbutton.clicked.connect(self.SaveCorrectedVersesFileDialog)
        
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

    def OpenVerseTextDialog(self, MainWindow):
        path = QtWidgets.QFileDialog.getOpenFileName(
            self.centralwidget, 'Open verse text file', '',
            'Text files (*.txt)')[0]
                
        if path:
            file = QtCore.QFile(path)
            filename = os.path.basename(path)
            self.VerseTextLe.setText(filename)
            if file.open(QtCore.QIODevice.ReadOnly):
                stream = QtCore.QTextStream(file)
                text = stream.readAll()
                info = QtCore.QFileInfo(path)
                if info.completeSuffix() == 'txt':
                    #self.editor_text.setHtml(text)
                    self.VerseText.insertPlainText(text)
                else:
                    self.VerseText.setPlainText(text)
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
             
    def SaveCorrectedTextFileDialog(self, MainWindow):
        path = QtWidgets.QFileDialog.getSaveFileName(
            self.centralwidget, 'Save Corrected text file', '',
            'Text files (*.txt)')[0]
        with open(path, 'w') as file:
            my_CorrectedText = self.OCRDocument.toPlainText()
            file.write(my_CorrectedText)
        filename = os.path.basename(path)
        self.TextLe.setText(filename)
        file.close()
        
    def SaveCorrectedVersesFileDialog(self, MainWindow):
        path = QtWidgets.QFileDialog.getSaveFileName(
            self.centralwidget, 'Save Corrected text file', '',
            'Text files (*.txt)')[0]
        with open(path, 'w') as file:
            my_CorrectedText = self.VerseDocument.toPlainText()
            file.write(my_CorrectedText)
        filename = os.path.basename(path)
        self.VerseTextLe.setText(filename)
        file.close()
    
    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Verse Correction"))
        self.OpenVerseTextbutton.setText(_translate("MainWindow", "Open Verses"))
        self.SaveVerseTextbutton.setText(_translate("MainWindow", "Save Verses"))
        self.SetLineSpacingbutton.setText(_translate("MainWindow", "Line Height"))
        self.EditCorrectedTextbutton.setText(_translate("MainWindow", "Edit Text"))
        self.SaveOCRCorrTextbutton.setText(_translate("MainWindow", "Save Edit"))

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

