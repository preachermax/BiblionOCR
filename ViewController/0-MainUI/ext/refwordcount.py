#PYQT5 PyQt4’s QtGui module has been split into PyQt5’s QtGui, QtPrintSupport and QtWidgets modules

from PyQt5 import QtWidgets
#PYQT5 QDialog, QGridLayout, QLabel, QWidget

from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import Qt

class WordCount(QtWidgets.QDialog):
    def __init__(self,parent = None):
        QtWidgets.QDialog.__init__(self, parent)

        self.parent = parent
         
        self.initUI()
 
    def initUI(self):

        # Word count in selection
        currentLabel = QtWidgets.QLabel("Current selection",self)
        currentLabel.setStyleSheet("font-weight:bold; font-size: 15px;")

        currentRefWordsLabel = QtWidgets.QLabel("Reference Words: ", self)
        currentRefSymbolsLabel = QtWidgets.QLabel("Reference Symbols: ",self)
        
        self.currentRefWords = QtWidgets.QLabel(self)
        self.currentRefSymbols = QtWidgets.QLabel(self)

        # Total word/symbol count
        totalLabel = QtWidgets.QLabel("Total",self)
        totalLabel.setStyleSheet("font-weight:bold; font-size: 15px;")


        totalRefWordsLabel = QtWidgets.QLabel("Reference Words: ", self)
        totalRefSymbolsLabel = QtWidgets.QLabel("Reference Symbols: ",self)

        self.totalRefWords = QtWidgets.QLabel(self)
        self.totalRefSymbols = QtWidgets.QLabel(self)

        # Layout
        
        layout = QtWidgets.QGridLayout(self)

        layout.addWidget(currentLabel,0,0)
        
        layout.addWidget(currentRefWordsLabel,1,0)
        layout.addWidget(self.currentRefWords,1,1)

        layout.addWidget(currentRefSymbolsLabel,2,0)
        layout.addWidget(self.currentRefSymbols,2,1)


        spacer = QtWidgets.QWidget()
        spacer.setFixedSize(0,5)

        layout.addWidget(spacer,5,0)

        layout.addWidget(totalLabel,6,0)

        layout.addWidget(totalRefWordsLabel,7,0)
        layout.addWidget(self.totalRefWords,7,1)

        layout.addWidget(totalRefSymbolsLabel,8,0)
        layout.addWidget(self.totalRefSymbols,8,1)


        self.setWindowTitle("Word count")
        self.setGeometry(600,600,200,200)
        self.setLayout(layout)

    def getText(self):

        # Get the text currently in selection
        Reftext = self.parent.ui.RefText.textCursor().selectedText()

        # Split the text to get the word count
        Refwords = str(len(Reftext.split()))

        # And just get the length of the text for the symbols
        # count
        Refsymbols = str(len(Reftext))

        self.currentRefWords.setText(Refwords)
        self.currentRefSymbols.setText(Refsymbols)

        # For the total count, same thing as above but for the
        # total text
        
        Reftext = self.parent.ui.RefText.toPlainText()

        Refwords = str(len(Reftext.split()))

        self.totalRefWords.setText(Refwords)

        Refsymbols = str(len(Reftext))

        self.totalRefSymbols.setText(Refsymbols)
