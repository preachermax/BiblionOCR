import sys
import sys, os
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from VersifyTextUI import Ui_VersifyText
#import pytesseract

app = QtWidgets.QApplication([])
varui = uic.loadUi("/home/max/Projects/BiblicalOCR/ViewController/Application/0-MainUI/QtDesignerUI/VersifyTextUI.ui")

def main():
    print("working")

if __name__ == "__main__":
    main()


varui.show()
app.exec()