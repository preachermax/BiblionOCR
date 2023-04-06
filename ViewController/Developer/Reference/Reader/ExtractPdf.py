# Python imports
import sys
import os
# PyQt5 imports
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc
# Custom imports
from ExtractDialog import Ui_Dialog

class pdfxWindow(qtw.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.pdfxDialog = qtw.QDialog()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self.pdfxDialog)
        self.pdfxDialog.show()
        self.pdfxDialog.exec_()
        #rsp = self.pdfxDialog.exec_()
        
        # extended slots code
        self.ui.SourceButton.clicked.connect(self.OpenPdfFileDialog)
        self.ui.DestinationButton.clicked.connect(self.DestinationDialog)
        
        #if self.pdfxDialog.Accepted:
           # MainWindow.pp.pdf4tiff(pdfxDialog.SourceLineEdit.text(), pdfxDialog.DestinationLineEdit.text(),pdfxDialog.FirstPageLineEdit.text(),pdfxDialog.LastPageLineEdit.text())

        #rsp.close()
    
    def OpenPdfFileDialog(self):
        self.path = qtw.QFileDialog.getOpenFileName(
            self, 'Open image file', '',
            'pdf Images (*.pdf)')[0]
                
        if self.path:
            filestr = os.path.basename(self.path)
            self.pdfxDialog.SourceLineEdit(filestr)

    def DestinationDialog(self):
        file = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.destpath = qtw.QFileDialog.getExistingDirectory(self.pdfxDialog, 'Select destination path')

        if self.destpath:
            filestr = os.path.dirname(self.destpath)
            self.pdfxDialog.DestinationLineEdit(filestr)

# Only run this code if I am actually running this script
if __name__ == '__main__': 
    app = qtw.QApplication(sys.argv)
    w = pdfxWindow()
    w.show()
    app.exec()