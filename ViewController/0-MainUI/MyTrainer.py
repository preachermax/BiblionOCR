# Python imports
import sys
import os
import re
import shutil
import json
import csv
import time

# PyQt5 imports
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc

from ext import *
from ext import versifiercount, versefind, reffind
# Custom imports
from MyTrainerUI import Ui_Trainer
from Dialogs.VariantRecorderDialog import Ui_RecorderDialog
from SqliteHelper import *
#import pytesseract

class Ui_MainWindow(qtw.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # pre-compiled QtDesigner Ui_MainUI and extended slots code starts here:        
        # load the pre-compiled QtDesigner Ui_MainUI user interface
        self.ui = Ui_Trainer()
        self.ui.setupUi(self)
        
        ChrRefText = open('c:/users/max/Projects/BiblionOCR/ViewController/Application/3-ConductOCR/FROMVS ChrReference.txt').read()
        self.ui.ChrRefplainTextEdit.setPlainText(ChrRefText)
        
        # Restore Session settings
        self.get_session_settings()

        
        self.show()

    def get_session_settings(self):
        # get session settings
        # Define json data        
        print("loading session")
        with open('c:/users/max/Projects/BiblionOCR/Model/Data/json/VersifierSession.json') as f:
            # returns JSON object as a dictionary
            data = json.load(f)
            
            f.close()

    def get_workflow_settings(self):

        # Opening JSON file
        with open('c:/users/max/Projects/BiblionOCR/Model/SQLite/json/Workflow.json') as f:
            # returns JSON object as
            # a dictionary
            data = json.load(f)
        
        # Iterating through the json
        # list
        for Sequence in data:
            print(Sequence['Sequence'], Sequence['DialogUi'],Sequence['DefaultSource'])
        
        # Closing file
        f.close()

    def save_session_settings(self):
        print("Saving Trainer session settings")  

    def OpenWithMyWriter(self):
        mw_cmd = "python3 c:/users/max/Projects/BiblionOCR/ViewController/Application/0-MainUI/MyWriter.py"
        print(mw_cmd)
        os.system(mw_cmd)


if __name__ == "__main__":
    app = qtw.QApplication(sys.argv)
    w = Ui_MainWindow()
    w.show()
    app.exec()

