import sys, os
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import Qt, QSortFilterProxyModel
from PyQt5.QtWidgets import QCompleter, QComboBox
from PyQt5.QtGui import QFont

#from WordListComboFilter import ExtendedComboBox

class Window(QtWidgets.QWidget):
    def __init__(self):
        super(Window, self).__init__()
        self.setWindowTitle('Text document')
        self.OCRText = QtWidgets.QTextEdit(self)
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
        
        #self.WordList = ExtendedComboBox(self)
        
        
        self.button_OpenDialog = QtWidgets.QPushButton('Open', self)
        self.button_OpenDialog.clicked.connect(self.my_OpenDialog)
        
        self.button_Format = QtWidgets.QPushButton('Format', self)
        self.button_Format.clicked.connect(self.my_Format)
        
        self.button_WordSelect = QtWidgets.QPushButton('Select', self)
        self.button_WordSelect.clicked.connect(self.toggle_window)

        v_layout = QtWidgets.QVBoxLayout(self)
        h_layout = QtWidgets.QHBoxLayout(self)
        
        h_layout.addWidget(self.button_OpenDialog)
        h_layout.addWidget(self.button_Format)
        h_layout.addWidget(self.button_WordSelect)
       
        v_layout.addWidget(self.OCRText)
        v_layout.addLayout(h_layout)
 
        #self.ToggleComboWindow = ExtendedComboBox()
        
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
        
    def toggle_window(self, checked):
        pass       
        #self.ToggleComboWindow = ExtendedComboBox()
        #if self.ToggleComboWindow.isVisible():
            #self.ToggleComboWindow.hide()
        #else:
            #self.ToggleComboWindow.show()

class ExtendedComboBox(QComboBox):
    def __init__(self, parent=None):
        super(ExtendedComboBox, self).__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setEditable(True)
        self.setStyleSheet("""
            QWidget {
                font-family: 'FROMVS';
                font-size: 20px;
                }
            """)
                 
        # add a filter model to filter matching items
        self.pFilterModel = QSortFilterProxyModel(self)
        self.pFilterModel.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.pFilterModel.setSourceModel(self.model())
        
        # add a completer, which uses the filter model
        self.completer = QCompleter(self.pFilterModel, self)
        # always show all (filtered) completions
        self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.setCompleter(self.completer)

        # connect signals
        self.lineEdit().textEdited.connect(self.pFilterModel.setFilterFixedString)
        self.completer.activated.connect(self.on_completer_activated)
        

    # on selection of an item from the completer, select the corresponding item from combobox 
    def on_completer_activated(self, text):
        if text:
            index = self.findText(text)
            self.setCurrentIndex(index)
            self.activated[str].emit(self.itemText(index))


    # on model change, update the models of the filter and completer as well 
    def setModel(self, model):
        super(ExtendedComboBox, self).setModel(model)
        self.pFilterModel.setSourceModel(model)
        self.completer.setModel(self.pFilterModel)


    # on model column change, update the model column of the filter and completer as well
    def setModelColumn(self, column):
        self.completer.setCompletionColumn(column)
        self.pFilterModel.setFilterKeyColumn(column)
        super(ExtendedComboBox, self).setModelColumn(column)
            
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.resize(640, 480)
    window.show()
    
    WordListFile = open("/home/max/Projects/Python/Workflow/3-ConductOCR/el_GR_word_list.txt", "r").readlines()
    WordList = []
    for line in WordListFile:
        WordList.append(line)
    
    combo = ExtendedComboBox()
    
    # either fill the standard model of the combobox
    combo.addItems(WordList)
    combo.setFont(QFont('FROMVS', 12))
    combo.setStyleSheet("""
        QWidget {
            font-family: 'FROMVS';
            font-size: 20px;
            }
        """)
    # or use another model
    #combo.setModel(QStringListModel(string_list))

    combo.resize(300, 40)
    combo.show()

    sys.exit(app.exec_())