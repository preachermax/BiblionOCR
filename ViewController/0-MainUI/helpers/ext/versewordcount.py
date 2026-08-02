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

        currentVerseWordsLabel = QtWidgets.QLabel("Verse Words: ", self)
        currentVerseSymbolsLabel = QtWidgets.QLabel("Verse Symbols: ",self)
        
        self.currentVerseWords = QtWidgets.QLabel(self)
        self.currentVerseSymbols = QtWidgets.QLabel(self)

        # Total word/symbol count
        totalLabel = QtWidgets.QLabel("Total",self)
        totalLabel.setStyleSheet("font-weight:bold; font-size: 15px;")

        totalVerseWordsLabel = QtWidgets.QLabel("Verse Words: ", self)
        totalVerseSymbolsLabel = QtWidgets.QLabel("Verse Symbols: ",self)

        self.totalVerseWords = QtWidgets.QLabel(self)
        self.totalVerseSymbols = QtWidgets.QLabel(self)


        # Layout
        
        layout = QtWidgets.QGridLayout(self)

        layout.addWidget(currentLabel,0,0)
        
        layout.addWidget(currentVerseWordsLabel,1,0)
        layout.addWidget(self.currentVerseWords,1,1)

        layout.addWidget(currentVerseSymbolsLabel,2,0)
        layout.addWidget(self.currentVerseSymbols,2,1)


        spacer = QtWidgets.QWidget()
        spacer.setFixedSize(0,5)

        layout.addWidget(spacer,5,0)

        layout.addWidget(totalLabel,6,0)

        layout.addWidget(totalVerseWordsLabel,7,0)
        layout.addWidget(self.totalVerseWords,7,1)

        layout.addWidget(totalVerseSymbolsLabel,8,0)
        layout.addWidget(self.totalVerseSymbols,8,1)

        self.setWindowTitle("Word count")
        self.setGeometry(600,600,200,200)
        self.setLayout(layout)

    def getText(self):

        # Get the text currently in selection 
        Versetext = self.parent.ui.VerseText.textCursor().selectedText()

        # Split the text to get the word count
        Versewords = str(len(Versetext.split()))

        # And just get the length of the text for the symbols
        # count
        Versesymbols = str(len(Versetext))
        self.currentVerseWords.setText(Versewords)
        self.currentVerseSymbols.setText(Versesymbols)

        # For the total count, same thing as above but for the
        # total text
        Versetext = self.parent.ui.VerseText.toPlainText()

        Versewords = str(len(Versetext.split()))

        self.totalVerseWords.setText(Versewords)

        Versesymbols = str(len(Versetext))

        self.totalVerseSymbols.setText(Versesymbols)

