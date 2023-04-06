import sys
import sys, os
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from VersifyTextUI import Ui_VersifyText
#import pytesseract

class Ui_MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #self = uic.loadUi("/home/max/Projects/BiblicalOCR/ViewController/Application/0-MainUI/QtDesignerUI/VersifyTextUI.ui")
        self.ui = Ui_VersifyText()
        self.ui.setupUi(self)
        self.show()
        #self.Versify_ui.show()

if __name__ == "__main__":
    #main()
    app = QtWidgets.QApplication(sys.argv)
    w = Ui_MainWindow()
    w.show()  
    #Versify_ui = uic.loadUi("/home/max/Projects/BiblicalOCR/ViewController/Application/0-MainUI/QtDesignerUI/VersifyTextUI.ui")
    #Versify_ui.show()
    app.exec()