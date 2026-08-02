import sys, os
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtGui import QSyntaxHighlighter
from MySpellTextEdit import SpellTextEdit, EnchantHighlighter


class Window(QtWidgets.QWidget):
    def __init__(self):
        super(Window, self).__init__()
        self.setWindowTitle('Text document')
        #self.OCRText = SpellTextEdit(self)
        self.OCRText = QtWidgets.QTextEdit.SpellTextEdit(self)
        self.OCRText.setGeometry(QtCore.QRect(0, 0, 540, 600))
        self.OCRText.setMinimumSize(QtCore.QSize(540, 600))
        self.OCRText.setAutoFillBackground(False)
        self.OCRText.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.OCRText.setObjectName("OCRText")
        
        self.OCRDocument = QtGui.QTextDocument(self.OCRText)
        font = QtGui.QFont()
        font.setFamily("FROMVS")
        font.setPointSize(20)
        self.OCRDocument.setDefaultFont(font)
        self.OCRBlockFormat = QtGui.QTextBlockFormat()
        self.OCRTextFormat = QtGui.QTextFormat()
        self.OCRCursor = QtGui.QTextCursor(self.OCRDocument)
        
        self.OCRText.setDocument(self.OCRDocument)
        
        
        self.button_OpenDialog = QtWidgets.QPushButton('Open', self)
        self.button_OpenDialog.clicked.connect(self.my_OpenDialog)
        
        self.button_Format = QtWidgets.QPushButton('Format', self)
        self.button_Format.clicked.connect(self.my_Format)

        v_layout = QtWidgets.QVBoxLayout(self)
        h_layout = QtWidgets.QHBoxLayout(self)
        
        h_layout.addWidget(self.button_OpenDialog)
        h_layout.addWidget(self.button_Format)
       
        v_layout.addWidget(self.OCRText)
        v_layout.addLayout(h_layout)
 
        #self.handleTextChanged()

    def my_OpenDialog(self):
        path = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Open file', '',
            'Text files (*.txt);;HTML files (*.html)')[0]
        if path:
            file = QtCore.QFile(path)
            if file.open(QtCore.QIODevice.ReadOnly):
                stream = QtCore.QTextStream(file)
                text = stream.readAll()
                info = QtCore.QFileInfo(path)
                if info.completeSuffix() == 'html':
                    self.OCRDocument.setHtml(text)
                else:
                    self.OCRDocument.setPlainText(text)
                file.close()
    
    def my_Format(self):
        lineSpacing = 150
        cursor = self.OCRText.textCursor()
        if not cursor.hasSelection():
            cursor.select(QtGui.QTextCursor.Document)
        bf = self.OCRCursor.blockFormat()
        bf.setLineHeight(lineSpacing, self.OCRBlockFormat.ProportionalHeight) 
        cursor.mergeBlockFormat(bf)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.resize(640, 480)
    window.show()
    sys.exit(app.exec_())