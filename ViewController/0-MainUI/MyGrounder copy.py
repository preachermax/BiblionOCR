# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'QT5GroundTruthReview.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

# PyQt5 imports
from pickle import FALSE
from string import punctuation
#from termios import OCRNL
from turtle import clear
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc
from PyQt5.QtCore import QAbstractTableModel, Qt
from PyQt5.QtWidgets import QTableView

# Python imports
import os
import sys
import re
import pytesseract
#import numpy as np
import pandas as pd
from sqlalchemy import false
import tiffcapture
import qimage2ndarray
import csv
import json
import shutil
from decimal import Decimal
from tempfile import NamedTemporaryFile
import platform

# Dialog Imports
from Dialogs.ImageTextPairDialog import Ui_ImageTextPairDialog
from Dialogs.tif_greek_lines_renameDialog import Ui_tifgreekrenamelinesDialog
from Dialogs.renumber_greek_text_linesDialog import Ui_renumbergreektextlinesDialog
from Dialogs.tif_greek_lines_renumberDialog import Ui_tifgreekrenumberlinesDialog
from Dialogs.tif_latin_lines_moveDialog import Ui_tiflatinmovelinesDialog
from Dialogs.tif_greek_lines_stageDialog import Ui_tifgreekstagelinesDialog
from Dialogs.PageVerseXrefDialog import Ui_PageVerseXrefDialog

# Custom imports
from ext import *
from ext import versefind, scanfind
from Training import Train as tr
from MyGrounderUI import Ui_Grounder
import MyVersifier as versifier
import MyBoxer as boxer
import MyScanner as scanner
import MyExplorer as explorer
#import PageVerseCrossReference as xref

# Custom Exception class heirarchy
class Error(Exception):
    pass

class TextError(Error):
    pass

class PageTextError(TextError):
    pass

class VerseTextError(TextError):
    pass

class ImageError(Error):
    pass

class DataError(Error):
    pass

class VerseTextError(Exception):
    pass

class DateTimeDelegate(qtw.QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super(DateTimeDelegate, self).initStyleOption(option, index)
        value = index.data()
        option.text = qtc.QDateTime.fromMSecsSinceEpoch(value).toString("dd.MM.yyyy")

class pandasModel(QAbstractTableModel):

    def __init__(self, data):
        QAbstractTableModel.__init__(self)
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parnet=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[col]
        return None

class Ui_MainWindow(qtw.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Drops
        self.setAcceptDrops(True)

        #UI
        # pre-compiled QtDesigner Ui_MainUI and extended slots code starts here:        
        # load the pre-compiled QtDesigner Ui_MainUI user interface
        self.ui = Ui_Grounder()
        self.ui.setupUi(self)           

        # Applications
        self.ui.actionScanner.triggered.connect(self.OpenWithMyScanner)
        self.ui.actionVersifier.triggered.connect(self.OpenWithMyVersifier)
        self.ui.actionBoxer.triggered.connect(self.OpenWithMyBoxer)
        self.ui.actionProject_Browser.triggered.connect(self.OpenMyBrowser)
        #self.ui.actionPage_Verse_Cross_Reference.triggered.connect(self.OpenPageVerseXref)
        #self.ui.actionPage_Verse_Cross_Reference.triggered.connect(self.PageVerseXref)

        # Synchronize
        self.ui.BothPrevButton.clicked.connect(self.prevImage)
        self.ui.BothPrevButton.clicked.connect(self.prevText)
        self.ui.BothNextButton.clicked.connect(self.nextImage)
        self.ui.BothNextButton.clicked.connect(self.nextText)
        self.ui.BothLoadButton.clicked.connect(self.bothLoad)
        self.ui.BothDiscardButton.clicked.connect(self.discardImage)
        self.ui.BothDiscardButton.clicked.connect(self.discardText)
        self.ui.bookComboBox.currentTextChanged.connect(self.selectBookCombo)

        # Line Image controls
        #self.ui.StageButton.clicked.connect(self.Stage_Greek_tiff_Lines)
        self.ui.actionStage_Ground_Truth.triggered.connect(self.Stage_Greek_tiff_Lines)
        self.ui.ImageButton.clicked.connect(self.loadImage)       
        self.ui.PrevImgButton.clicked.connect(self.prevImage)
        self.ui.NextImgButton.clicked.connect(self.nextImage)
        self.ui.SaveImgAsButton.clicked.connect(self.SaveImgFileDialog)
        self.ui.DiscardImageButton.clicked.connect(self.discardImage)
        #self.ui.RenumberImagesButton.clicked.connect(self.Renumber_Greek_tiff_Lines)
        self.ui.actionRenumber_Images.triggered.connect(self.Renumber_Greek_tiff_Lines)

        # Line text controls
        self.ui.TextButton.clicked.connect(self.loadText)
        self.ui.fontComboBox.currentFontChanged.connect(self.on_font_update)
        self.ui.fontSizeBox.valueChanged.connect(self.on_font_update)
        self.ui.PrevTxtButton.clicked.connect(self.prevText)
        self.ui.NextTxtButton.clicked.connect(self.nextText)
        self.ui.SaveButton.clicked.connect(self.SaveCorrectedTextFileDialog)
        self.ui.SaveAsButton.clicked.connect(self.SaveAsCorrectedTextFileDialog)
        self.ui.DiscardTextButton.clicked.connect(self.discardText)
        #self.ui.RenumberTextButton.clicked.connect(self.Renumber_Greek_text_Lines)
        self.ui.actionRenumber_Text.triggered.connect(self.Renumber_Greek_text_Lines)

        # Line text changes
        #self.ui.TextFileEdit.textChanged.connect(self.verseAutoSeek)
        #self.ui.TextFileEdit.textChanged.connect(self.pageAutoSeek)
        #self.ui.TextFileName.textChanged.connect(self.verseAutoSeek)
        #self.ui.TextFileName.textChanged.connect(self.pageAutoSeek)

        # OCR
        self.ui.OCRButton.clicked.connect(self.GetRawOCRtext)
        self.ui.OCRlangComboBox.currentTextChanged.connect(self.on_lang_select)
        self.ui.AutoScancheckBox.stateChanged.connect(self.autoScan)
        self.ui.AutoScancheckBox.setCheckState(False)
        #self.ui.OCRAccuracyLineEdit.textChanged.connect(self.OCRAccuracy)

        # Page
        self.ui.PagefontComboBox.currentFontChanged.connect(self.on_page_font_update)
        self.ui.PagefontSizeBox.valueChanged.connect(self.on_page_font_update)
        self.ui.PageAutoSeekcheckBox.stateChanged.connect(self.pageAutoSeek)
        self.ui.SavePageTextButton.clicked.connect(self.SavePageTextDialog)


        # Verse 
        self.ui.VerseFindButton.clicked.connect(versefind.Find(self).show)
        self.ui.PageFindButton.clicked.connect(scanfind.Find(self).show)
        self.ui.StartbookComboBox.currentTextChanged.connect(self.selectBookCombo)
        self.ui.StartbookComboBox.currentTextChanged.connect(self.loadChapterCombo)
        self.ui.StartchapterComboBox.currentTextChanged.connect(self.loadVerseCombo)
        self.ui.StartverseComboBox.currentTextChanged.connect(self.updateXRef_json)
        self.ui.VerseAutoSeekcheckBox.stateChanged.connect(self.verseAutoSeek)
        self.ui.VersefontComboBox.currentFontChanged.connect(self.on_verse_font_update)
        self.ui.VersefontSizeBox.valueChanged.connect(self.on_verse_font_update)
        self.ui.SaveVerseTextButton.clicked.connect(self.SaveVerseTextDialog)
        
        # Final
        #self.ui.ReviewCompletecheckBox.stateChanged.connect(self.updateXRef)
        #self.ui.RenameButton.clicked.connect(self.buildXRef)
        #self.ui.StageButton.clicked.connect()

        # Restore Session settings
        self.get_session_settings()
        self.bookmarkdown = self.greekbookmarkdown
        self.get_xref_last_image()
        #self.get_xref_settings()
        self.dirIterator = None
        self.findirection = None
        self.lastverse = None
        self.imgfileList = []
        self.txtfileList = []
        
        self.VerseLastEnd = 0

        # Reference
        ChrRefText = open(self.projecthome + 'ViewController/3-ConductOCR/FROMVS ChrReference.txt', encoding='UTF-8').read()
        self.ui.ChrRefplainTextEdit.setPlainText(ChrRefText)
        
        #self.loadChapterCombo()

        #self.loadVerseText()

# Drop Functons
    def dragEnterEvent(self, event):
        m = event.mimeData()
        if m.hasUrls():
            for url in m.urls():
                if url.isLocalFile():
                    event.accept()
                    return
        event.ignore()
              
    def dropEvent(self, event):
        if event.mimeData().hasText:
            file_path = event.mimeData().urls()[0].toLocalFile()
            print(f'text file path: {file_path}')
            self.loadDropTextEvent(file_path)
            event.accept()
        if event.mimeData().hasImage:
            event.setDropAction(Qt.CopyAction)
            file_path = event.mimeData().urls()[0].toLocalFile()
            print(f'image file path: {file_path}')
            self.loadDropImageEvent(file_path)
            event.accept()        

        else:
            file_path = event.mimeData().urls()[0].toLocalFile()
            print(f'drop file ignored: {file_path}')
            event.ignore()

# Session functions
    def get_session_settings(self):
        # get session settings
        self.homedir = os.path.expanduser('~')
        self.user = os.path.basename(self.homedir)
        self.userdir = os.path.expanduser('~')
        self.projectsdir = 'Projects'
        self.projectname = 'BiblionOCR'
        self.projecthome = os.path.join(self.userdir, self.projectsdir, self.projectname) + os.sep
        
        # Define json data        
        print("loading session")
        with open(self.projecthome + 'Model/Project/Data/json/GrounderSession.json') as f:
            # returns JSON object as a dictionary
            data = json.load(f)
            
            # Set json key values
            linuxhomedir_key = r'self.linuxhomedir'
            linuxuser_key = r'self.linuxuser'
            linuxuserdir_key = r'self.linuxuserdir'
            windowshomedir_key = r'self.windowshomedir'
            windowsuser_key = r'self.windowsuser'
            windowsuserdir_key = r'self.windowsuserdir'
            macoshomedir_key = r'self.macoshomedir'
            macosuser_key = r'self.macosuser'
            macosuserdir_key = r'self.macosuserdir'
            projectsdir_key = r'self.projectsdir'
            projectname_key = r'self.projectname'  
            ocrlang_key = r"self.ocrlang"
            ocrmodel_key = r"self.ocrmodel"
            linuxtessdatadir_key = r"self.linuxtessdatadir"
            linuxtesseract_key = r"self.linuxtesseract"
            linuxtesstrain_key = r"self.linuxtesstrain"
            windowstessdatadir_key = r"self.windowstessdatadir"
            windowstesseract_key = r"self.windowstesseract"
            windowstesstrain_key = r"self.windowstesstrain"
            bookabbr_key = r"self.bookabbr"
            font_key = r"self.font"
            fontsize_key = r"self.fontsize"
            source_book_markdown_key = r"self.sourcebookmarkdown"
            greek_book_markdown_key = r"self.greekbookmarkdown"
            latin_book_markdown_key = r"self.latinbookmarkdown"
            sourcefile_key = r"self.sourcefile"
            firstpage_key = r"self.firstpage"
            lastpage_key = r"self.lastpage"            
            imagepath_key = r"self.imagepath"
            imagedir_key = r"self.imagedir"
            imagepage_key = r"self.imagepage"
            imageline_key = r"self.imageline"
            imagefileList_key = r"self.imagefileList"
            imagezoom_key = r"self.imagezoom"
            imagezoomslidervalue_key = r"self.imagezoomslidervalue"
            dirIterator_key = r"self.dirIterator"
            pixmap_key = r"self.pixmap"
            qimage_key = r"self.qimage"
            textpath_key = r"self.textpath"
            textdir_key = r"self.textdir"
            textfileList_key = r"self.textfileList"
            PagelastStart_key = r"self.PagelastStart"       
            pagetextpath_key = r"self.pagetextpath"
            pagetextdir_key = r"self.pagetextdir"
            pagetextfileList_key = r"self.pagetextfileList"
            pagetextpage_key = r"self.pagetextpage"
            VerseStart_key = r"self.VerseStart"
            VerseLastEnd_key = r"self.VerseLastEnd"
            versetextpath_key = r"self.versetextpath"
            versetextdir_key = r"self.versetextdir"
            startbookabbr_key = r"self.startbookabbr"
            startchapter_key = r"self.startchapter"
            startverse_key = r"self.startverse"
            startverseline_key = r"self.startverseline"
            ocraccuracy_key = r"self.ocraccuracy"
            gtvalid_key = r"self.gtvalid"
            gtreview_key = r"self.gtreview"

            # Find the json key values using 'in' operator
            # Define session variables from json key values
            for Setting in data:
                print('Setting: ',Setting['Setting'],Setting['CurrentValue'])
                
                if Setting['Setting'] == linuxhomedir_key:
                    self.linuxhomedir = Setting['CurrentValue']
                elif Setting['Setting'] == linuxuser_key:
                    self.linuxuser = Setting['CurrentValue']
                elif Setting['Setting'] == linuxuserdir_key:
                    self.linuxuserdir = Setting['CurrentValue']                
                elif Setting['Setting'] == windowshomedir_key:
                    self.windowshomedir = Setting['CurrentValue']
                elif Setting['Setting'] == windowsuser_key:
                    self.windowsuser = Setting['CurrentValue']
                elif Setting['Setting'] == windowsuserdir_key:
                    self.windowsuserdir = Setting['CurrentValue']
                elif Setting['Setting'] == projectsdir_key:
                    self.projectsdir = Setting['CurrentValue']
                elif Setting['Setting'] == projectname_key:
                    self.projectname = Setting['CurrentValue']
                if Setting['Setting'] == ocrlang_key:
                    self.ocrlang = Setting['CurrentValue']
                    self.ui.OCRlangComboBox.setCurrentText(self.ocrlang)
                elif Setting['Setting'] == ocrmodel_key:
                    self.ocrmodel = Setting['CurrentValue']
                    self.ui.OCRModelComboBox.setCurrentText(self.ocrmodel)              
                elif Setting['Setting'] == linuxtessdatadir_key:
                    self.linuxtessdatadir = Setting['CurrentValue']
                elif Setting['Setting'] == linuxtesseract_key:
                    self.linuxtesseract = Setting['CurrentValue']
                elif Setting['Setting'] == linuxtesstrain_key:
                    self.linuxtesstrain = Setting['CurrentValue']
                elif Setting['Setting'] == windowstessdatadir_key:
                    self.windowstessdatadir = Setting['CurrentValue']
                elif Setting['Setting'] == windowstesseract_key:
                    self.windowstesseract = Setting['CurrentValue']
                elif Setting['Setting'] == windowstesstrain_key:
                    self.windowstesstrain = Setting['CurrentValue']
                elif Setting['Setting'] == bookabbr_key:  
                    self.bookabbr = Setting['CurrentValue']
                elif Setting['Setting'] == font_key:
                    self.font = Setting['CurrentValue']
                    self.ui.fontComboBox.setCurrentText(self.font)
                elif Setting['Setting'] == fontsize_key:
                    self.fontsize = Setting['CurrentValue']
                    self.ui.fontSizeBox.setValue(int(self.fontsize))           
                elif Setting['Setting'] == source_book_markdown_key:  
                    self.sourcebookmarkdown = Setting['CurrentValue']
                elif Setting['Setting'] == greek_book_markdown_key:  
                    self.greekbookmarkdown = Setting['CurrentValue']
                    if self.ocrlang == "Ancient Greek" or self.ocrlang == "Middle Greek" or self.ocrlang == "Modern Greek":
                        self.language = "greek"
                elif Setting['Setting'] == latin_book_markdown_key:  
                    self.latinbookmarkdown = Setting['CurrentValue']
                    if self.ocrlang == "Latin":
                        self.language = "latin"
                elif Setting['Setting'] == sourcefile_key:   
                    self.sourcefile = Setting['CurrentValue']
                elif Setting['Setting'] == firstpage_key:  
                    self.firstpage = Setting['CurrentValue']
                elif Setting['Setting'] == lastpage_key:  
                    self.lastpage = Setting['CurrentValue']
                elif Setting['Setting'] == imagepath_key:
                    self.imagepath = Setting['CurrentValue']
                elif Setting['Setting'] == imagedir_key:
                    self.imagedir = Setting['CurrentValue']
                elif Setting['Setting'] == imagepage_key:
                    self.imagepage = Setting['CurrentValue']
                elif Setting['Setting'] == imageline_key:
                    self.imageline = Setting['CurrentValue'] 
                elif Setting['Setting'] == imagefileList_key:
                    self.imagefileList = Setting['CurrentValue']
                elif Setting['Setting'] == imagezoom_key:
                    self.imagezoom = Setting['CurrentValue']
                elif Setting['Setting'] == imagezoomslidervalue_key:
                    self.imagezoomslidervalue = Setting['CurrentValue']
                elif Setting['Setting'] == dirIterator_key:  
                    self.dirIterator = Setting['CurrentValue']
                elif Setting['Setting'] == pixmap_key:  
                    self.pixmap = Setting['CurrentValue']
                elif Setting['Setting'] == qimage_key:  
                    self.qimage = Setting['CurrentValue']
                elif Setting['Setting'] == textpath_key:  
                    self.textpath = Setting['CurrentValue'] 
                elif Setting['Setting'] == textdir_key:  
                    self.textdir = Setting['CurrentValue']
                elif Setting['Setting'] == textfileList_key:
                    self.textfileList = Setting['CurrentValue']
                elif Setting['Setting'] == PagelastStart_key:
                    self.PagelastStart = Setting['CurrentValue']
                elif Setting['Setting'] == pagetextpath_key:
                    self.pagetextpath = Setting['CurrentValue']
                elif Setting['Setting'] == pagetextdir_key:
                    self.pagetextdir = Setting['CurrentValue']
                elif Setting['Setting'] == pagetextfileList_key:
                    self.pagetextfileList = Setting['CurrentValue']
                elif Setting['Setting'] == pagetextpage_key:
                    self.pagetextpage = Setting['CurrentValue']
                elif Setting['Setting'] == VerseStart_key:
                    self.VerseStart = int(Setting['CurrentValue'])
                elif Setting['Setting'] == VerseLastEnd_key:
                    self.VerseLastEnd = int(Setting['CurrentValue'])
                elif Setting['Setting'] == versetextpath_key:
                    self.versetextpath = Setting['CurrentValue']
                elif Setting['Setting'] == versetextdir_key:
                    self.versetextdir = Setting['CurrentValue']
                elif Setting['Setting'] == startbookabbr_key:
                    self.startbookabbr = Setting['CurrentValue']
                elif Setting['Setting'] == startchapter_key:
                    self.startchapter = Setting['CurrentValue']
                elif Setting['Setting'] == startverse_key:
                    self.startverse = Setting['CurrentValue']
                elif Setting['Setting'] == startverseline_key:
                    self.startverseline = Setting['CurrentValue']
                elif Setting['Setting'] == ocraccuracy_key:
                    self.ocraccuracy = Setting['CurrentValue']
                elif Setting['Setting'] == gtvalid_key:
                    self.gtvalid = Setting['CurrentValue']
                elif Setting['Setting'] == gtreview_key:
                    self.gtreview = Setting['CurrentValue']
                print('New Setting: ',Setting['Setting'],Setting['CurrentValue'])
            f.close()
            
            if platform.system() == 'Linux':
                self.homedir = self.linuxhomedir
                self.user = self.linuxuser
                self.userdir = self.linuxuserdir
                self.tessdatadir = self.linuxtessdatadir
                self.tesseract = self.linuxtesseract
                self.tesstrain = self.linuxtesstrain
            elif platform.system() == 'Windows':
                self.homedir = self.windowshomedir
                self.user = self.windowsuser
                self.userdir = self.windowsuserdir
                self.tessdatadir = self.windowstessdatadir
                self.tesseract = self.windowstesseract
                self.tesstrain = self.windowstesstrain
            elif platform.system() == 'MacOS':
                self.homedir = self.macoshomedir
                self.user = self.macosuser
                self.userdir = self.macosuserdir
            else:
                self.homedir = r'.'
                self.user = r'/'
                self.userdir = r'./'
            
            self.projecthome = self.userdir + self.projectsdir + self.projectname + '/'
            print(f'Absolute Path to User Directory: {self.userdir}')

            # Update Project paths
            self.textdir = self.projecthome + self.textdir
            self.textpath = self.projecthome + self.textpath
            self.imagedir = self.projecthome + self.imagedir
            self.imagepath = self.projecthome + self.imagepath
            self.sourcefile = self.projecthome + self.sourcefile
            self.pagetextdir = self.projecthome + self.pagetextdir
            self.pagetextpath = self.projecthome + self.pagetextpath
            self.versetextpath = self.projecthome + self.versetextpath
            self.versetextdir = self.projecthome + self.versetextdir
 
    def get_workflow_settings(self):

        # Opening JSON file
        with open(self.projecthome + 'Model/Project/SQLite/json/Workflow.json') as f:
            # returns JSON object as
            # a dictionary
            data = json.load(f)
        
        # Iterating through the json
        # list
        for Sequence in data:
            print(Sequence['Sequence'], Sequence['DialogUi'],Sequence['DefaultSource'])
        
        # Closing file
        f.close()

    def get_xref_last_image(self):
        imgdir = self.projecthome + "Model/Project/Images/Workflow/Greek/tif_greek_lines_4groundtruth/"
        xrefjsonfile = self.projecthome + 'Model/Project/Data/json/PageVerseCrossReference.json'
        markdownjsonfile = self.projecthome + 'Model/Project/Data/json/BooksMarkDown.json'
        with open(xrefjsonfile, 'r') as f:
            data = json.load(f)
            # Iterating through the json LineImageFiles
            for PageLineImageFile in data:
                if PageLineImageFile['PageLineTextFile'] == '':
                    self.imgfile = PageLineImageFile['PageLineImageFile']
                    print(f'Next image file: {self.imgfile}')
                    self.imgpath = imgdir + self.imgfile
                    f.close()
                    break
        print(f'Next image for review: {self.imgpath}')
        self.getImage(self.imgpath)
        self.prevImage()
        self.syncText2Image()   
        
# Application callers
    def OpenWithMyScanner(self):
        self.scannermain = scanner.MainWindow()
        self.scannermain.show()

    def OpenWithMyVersifier(self):
        self.versifiermain = versifier.Ui_MainWindow()
        self.versifiermain .show()

    def OpenWithMyBoxer(self):
        self.boxermain = boxer.MainWindow()
        self.boxermain.show()

    def OpenMyBrowser(self):
        
        self.browsermain = explorer.MyFileBrowser()
        self.browsermain.show()

    
# Line image functions
    def setImageStack(self, tiffCaptureHandle):
        """ Set the scene'Model/Project/Data/json/PageVerseCrossReference.json current TIFF image stack to the input TiffCapture object.
        Raises a RuntimeError if the input tiffCaptureHandle has type other than TiffCapture.
        :type tiffCaptureHandle: TiffCapture
        """
        if type(tiffCaptureHandle) is not tiffcapture.TiffCapture:
            raise RuntimeError("MultiPageTIFFViewerQt.setImageStack: Argument must be a TiffCapture object.")
        self._tiffCaptureHandle = tiffCaptureHandle
        self.showFrame(0)

    def loadImageStackFromFile(self, fileName=''):
        """ Load an image stack from file.
        Without any arguments, loadImageStackFromFile() will popup a file dialog to choose the image file.
        With a fileName argument, loadImageStackFromFile(fileName) will attempt to load the specified file directly.
        """
        '''
        if len(fileName) == 0:
            if QT_VERSION_STR[0] == '4':
                fileName = qtw.QFileDialog.getOpenFileName(self, "Open TIFF stack file.")
            elif QT_VERSION_STR[0] == '5':
                fileName, dummy = qtw.QFileDialog.getOpenFileName(self, "Open TIFF stack file.")'''
        fileName = str(fileName)
        if len(fileName) and os.path.isfile(fileName):
            self._tiffCaptureHandle = tiffcapture.opentiff(fileName)
            
    def numFrames(self):
        """ Return the number of image frames in the stack.
        """
        if self._tiffCaptureHandle is not None:
            # !!! tiffcapture has length=0 for a single page TIFF.
            # If our handle is valid, we'll assume we have at least one image.
            return max([1, self._tiffCaptureHandle.length])
        return 0

    def getFrame(self, i=None):
        """ Return the i^th image frame as a NumPy ndarray.
        If i is None, return the current image frame.
        """
        if self._tiffCaptureHandle is None:
            return None
        if i is None:
            i = self.currentFrameIndex
        if (i is None) or (i < 0) or (i >= self.numFrames()):
            return None
        return self._tiffCaptureHandle.find_and_read(i)

    def showFrame(self, i=None):
        """ Display the i^th frame in the viewer.
        Also update the frame slider position and current frame text.
        """
        self.frame = self.getFrame(i)
        if self.frame is None:
            return
        # Convert frame ndarray to a QImage.
        self.qimage = qimage2ndarray.array2qimage(self.frame, normalize=True)
    
    def loadDropImageEvent(self,file_path):
        self.imgpath = file_path
        if self.imgpath:
            self.ui.ImageFileName.setText(os.path.basename(self.imgpath))       
            self.imgfilename = os.path.basename(self.imgpath)
            self.imgdir = os.path.dirname(self.imgpath)
            self.showImage(self.imgpath)
            #self.sortImgFiles()
    
    def loadImage(self):
        self.imgpath = qtw.QFileDialog.getOpenFileName(
            self.ui.centralwidget, 'Select Image', "Model/Project/Images/Workflow/Greek/tif_greek_lines_4groundtruth/", 'Image Files (*.png *.jpg *.jpeg *.tif *.bmp)')[0]
        self.getImage(self.imgpath)   
            
        #moved to getImage()
        '''self.ui.ImageFileName.setText(os.path.basename(self.imgpath))       
        self.imgfile = qtc.QFile(self.imgpath)
        self.imgfilename = os.path.basename(self.imgpath)
        self.showImage(self.imgpath)'''
    
    def getImage(self, imgpath):
            self.imgpath = imgpath
            #create file list 
            if self.imgpath:
                self.ui.ImageFileName.setText(os.path.basename(self.imgpath))       
                self.imgfile = qtc.QFile(self.imgpath)
                self.imgfilename = os.path.basename(self.imgpath)
                self.imgdirname = os.path.dirname(self.imgpath)
                self.imgfileList = []
            for i in os.listdir(self.imgdirname):
                ipath = os.path.join(self.imgdirname, i)
                if os.path.isfile(ipath) and i.endswith(('.png', '.jpg', '.jpeg', '.tif')):
                    self.imgfileList.append(ipath)
            self.sortImgFiles()
            self.showImage(self.imgpath)
         
    def showImage(self,imgpath):
        self.imgpath = imgpath
        if self.imgpath.endswith('.tif'):
            self.loadImageStackFromFile(self.imgpath)
            self.showFrame(0)
            self.pixmap = qtg.QPixmap.fromImage(self.qimage).scaled(self.ui.ImageView.size(), 
                qtc.Qt.KeepAspectRatio)
        else:
            self.pixmap = qtg.QPixmap(self.imgpath).scaled(self.ui.ImageView.size(), 
                qtc.Qt.KeepAspectRatio)

        if self.pixmap.isNull():
            return
        self.ui.ImageView.setPixmap(self.pixmap)
        self.imgdirname = os.path.dirname(self.imgpath)
        self.imgfileList = []
        for i in os.listdir(self.imgdirname):
            ipath = os.path.join(self.imgdirname, i)
            if os.path.isfile(ipath) and i.endswith(('.png', '.jpg', '.jpeg', '.tif')):
                self.imgfileList.append(ipath)
        #print(list(self.imgfileList))
        #self.sortImgFiles()
        self.autoScan()

    '''
    def setFwdImgDirIterator(self):
        self.imgdirIterator = iter(self.sorted_imgfilelist)
        #print(f'Image Directory Iterator: {list(self.imgdirIterator)}')
        for it in self.imgdirIterator:
            # cycle through the iterator until the current file is found
            if it == self.imgpath:
                break
    
    def setRevImgDirIterator(self):
        self.imgdirRevIterator = reversed(self.sorted_imgfilelist)
        #print(f'Image Directory Reverse Iterator: {list(self.imgdirRevIterator)}')
        for it in self.imgdirRevIterator:
            # cycle through the reverse iterator until the current file is found
            if it == self.imgpath:
                break
    '''

    def sortImgFiles(self):
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
        self.sorted_imgfilelist = sorted(self.imgfileList, key=alphanum_key)
        
        #self.setFwdImgDirIterator()
        #self.setRevImgDirIterator()

    
    def nextImage(self):
        if self.imgpath:
            self.imgpath = self.sorted_imgfilelist[(self.sorted_imgfilelist.index(self.imgpath) + 1) % len(self.sorted_imgfilelist)]
            self.ui.ImageFileName.setText(os.path.basename(self.imgpath))
            self.getImage(self.imgpath)
    
    def prevImage(self):
        if self.imgpath:
            self.imgpath = self.sorted_imgfilelist[(self.sorted_imgfilelist.index(self.imgpath) - 1) % len(self.sorted_imgfilelist)]
            self.ui.ImageFileName.setText(os.path.basename(self.imgpath))
            self.getImage(self.imgpath)
       
    '''
    def nextImage(self):
        if self.imgpath:    
            for it in self.imgdirIterator:
            # cycle through the iterator until the current file is found
                if it == self.imgpath:
                    self.ui.ImageFileName.setText(os.path.basename(self.imgpath))
                    self.getImage(self.imgpath)
                else:
                    self.loadImage()
        else:
            self.loadImage()

    def prevImage(self):
        if self.imgpath:    
            for it in self.imgdirRevIterator:
            # cycle through the iterator until the current file is found
                if it == self.imgpath:
                    self.ui.ImageFileName.setText(os.path.basename(self.imgpath))
                    self.getImage(self.imgpath)
                else:
                    self.loadImage()
        else:
            self.loadImage()

        if self.imgpath:
            try:
                self.imgpath = next(self.imgdirRevIterator)
                self.ui.ImageFileName.setText(os.path.basename(self.imgpath))
                self.getImage(self.imgpath)
            except:
                # the iterator has finished, restart it
                #self.setFwdImgDirIterator()
                self.setRevImgDirIterator()
                self.nextImage()
        else:
            self.loadImage()
        '''
# Line text Functions
    def loadDropTextEvent(self,file_path):
        self.textpath = file_path
        if self.textpath:
            self.ui.TextFileName.setText(os.path.basename(self.textpath))
            self.textfile = qtc.QFile(self.textpath)
            self.txtfilename = os.path.basename(self.textpath)
            self.showText(self.textpath)
    
    def loadText(self):

        self.textpath = qtw.QFileDialog.getOpenFileName(
            self.ui.centralwidget, 'Open text file', self.projecthome + 'Model/Project/Text/EstablishTruth/Greek/txt_greek_lines_autosplit/','Text files (*.txt)')[0]
    
        self.getText(self.textpath)

    def getText(self,textpath):
            self.textpath = textpath
            self.txtdirname = os.path.dirname(self.textpath)
            #create file list 
            if self.textpath:
                self.ui.TextFileName.setText(os.path.basename(self.textpath))       
                self.txtfile = qtc.QFile(self.textpath)
                self.txtfilename = os.path.basename(self.textpath)
                self.txtdirname = os.path.dirname(self.textpath)
                self.txtfileList = []
            for t in os.listdir(self.txtdirname):
                tpath = os.path.join(self.txtdirname, t)
                if os.path.isfile(tpath) and t.endswith(('.txt')):
                    self.txtfileList.append(tpath)
            self.sortTextFiles()
            self.showText(self.textpath)
            
    def showText(self,txtpath):        
        self.textpath = txtpath
        #self.ui.TextFileEdit.clear()
        self.txtdirname = os.path.dirname(self.textpath)
        print(f'first txtdirname: {self.txtdirname}')
        #self.textfile = txtfilename
        if self.txtfile.open(qtc.QIODevice.ReadOnly):
            stream = qtc.QTextStream(self.txtfile)
            stream.setCodec("UTF-8")
            text = stream.readAll()
            info = qtc.QFileInfo(self.textpath)
            if info.completeSuffix() == 'txt':
                #self.ui.editor_text.setHtml(text
                self.ui.TextFileEdit.insertPlainText(text)
            else:
                self.ui.TextFileEdit.setPlainText(text)
            self.ui.TextFileName.setText(self.txtfilename)
            self.txtdirname = os.path.dirname(self.textpath)
            print(f'second txtdirname: {self.txtdirname}')
            self.txtfileList = []
        for t in os.listdir(self.txtdirname):
            tpath = os.path.join(self.txtdirname, t)
            if os.path.isfile(tpath) and t.endswith(('.txt')):
                self.txtfileList.append(tpath)
        #self.sortTextFiles()
        self.on_font_update()

        # Update Line comboBox
        txtfilnamesplit = self.txtfilename.split("_")
        print(f'Text file name split: {txtfilnamesplit}')
        linenumstr = txtfilnamesplit[3]
        print(f'Line number string: {linenumstr}')
        linenum = linenumstr[4:6]
        linenum = linenum.replace(".","")
        print(f'Line number: {linenum}')
        self.ui.LinecomboBox.setCurrentText(linenum)

        # Update Book comboBox
        bookdirsplit = self.txtdirname.split("/")
        print(f'book directory split: {bookdirsplit}')
        bookdir = bookdirsplit[11]
        print(f'Text directory path: {self.txtdirname}  book directory: {bookdir}')
        dirsplit = bookdir.split("_")
        
        lang =  dirsplit[0]
        booknum = dirsplit[2]
        bookstr = dirsplit[3]
        bookabbr = bookstr[:3]
        print(f'Book abbreviation: {bookabbr}')
        self.ui.bookComboBox.setCurrentText(bookabbr)

        self.loadPageText()        

        #if self.ui.Imagelabel.pixmap():
        if self.ui.OCRTextEdit.text():
            self.OCRAccuracy()

        self.loadVerseText()
        try:
            self.verseAutoSeek()
        except:
            print("verseAutoSeek out of range error")
    '''
    def setFwdTxtDirIterator(self):
        self.txtdirIterator = iter(self.sorted_txtfilelist)
        #print(f'Text Directory Iterator: {list(self.txtdirIterator)}')
        for it in self.txtdirIterator:
            # cycle through the iterator until the current file is found
            #print(f'Text Directory Iterator: {list(self.txtdirIterator)}')
            if next(self.txtdirIterator) == self.textpath:
                break
     
    def setRevTxtDirIterator(self):
        self.txtdirRevIterator = reversed(self.sorted_txtfilelist)
        #print(f'Text Directory Reverse Iterator: {list(self.txtdirRevIterator)}')
        for it in self.txtdirRevIterator:
            # cycle through the reverse iterator until the current file is found
            #print(f'Image Directory Reverse Iterator: {list(self.txtdirRevIterator)}')
            if it == self.textpath:
                break'''

    def sortTextFiles(self):
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
        self.sorted_txtfilelist = sorted(self.txtfileList, key=alphanum_key)     
        
        #self.setFwdTxtDirIterator()
        #self.setRevTxtDirIterator()

    def nextText(self):
        if self.textpath:
            self.textpath = self.sorted_txtfilelist[(self.sorted_txtfilelist.index(self.textpath) + 1) % len(self.sorted_txtfilelist)]
            self.ui.TextFileName.setText(os.path.basename(self.textpath))
            self.getText(self.textpath)

    def prevText(self):
        if self.textpath:
            self.textpath = self.sorted_txtfilelist[(self.sorted_txtfilelist.index(self.textpath) - 1) % len(self.sorted_txtfilelist)]
            self.ui.TextFileName.setText(os.path.basename(self.textpath))
            self.getText(self.textpath)
    
    '''
    def nextText(self):
        if self.textpath:
            for it in self.txtdirIterator:
            # cycle through the iterator until the current file is found
                if it == self.textpath:
                    self.ui.TextFileName.setText(os.path.basename(self.textpath))
                    self.getText(self.textpath)
                else:
                    self.loadText()
    
    def prevText(self):
        if self.textpath:
            for it in self.txtdirRevIterator:
            # cycle through the iterator until the current file is found
                if it == self.textpath:
                    self.ui.TextFileName.setText(os.path.basename(self.textpath))
                    self.getText(self.textpath)
                else:
                    self.loadText()'''
   
    def syncText2Image(self):
        imgdir = self.projecthome + "Model/Project/Images/Workflow/Greek/tif_greek_lines_4groundtruth/"
        xrefjsonfile = self.projecthome + 'Model/Project/Data/json/PageVerseCrossReference.json'
        markdownjsonfile = self.projecthome + 'Model/Project/Data/json/BooksMarkDown.json'
        bookAbbr = self.bookabbr
        if self.imgpath:
            filestr = os.path.basename(self.imgpath)
            print(f'Finding text file matching: {self.ui.ImageFileName.displayText()}')
            with open(xrefjsonfile, 'r') as f:
                data = json.load(f)
                # Iterating through the json LineImageFiles
                for PageLineImageFile in data:
                    if PageLineImageFile['PageLineImageFile'] == filestr:
                        bookAbbr = PageLineImageFile['StartBook']
                        #self.ui.bookComboBox.setCurrentText('bookAbbr')
                        f.close()
            
            with open(markdownjsonfile, 'r') as f:
                data = json.load(f)
                # Iterating through the json BooksMarkDown
                for BookAbbr in data:
                    if BookAbbr['BookAbbr'] == bookAbbr:
                        self.bookmarkdown = self.language + BookAbbr['BookMarkdown']
                        f.close()

            filedir = os.path.dirname(self.imgpath)
            filesplit = os.path.splitext(filestr)
            filename = filesplit[0]
            fileext = filesplit[1]                    
            namesplit = filename.split("_")                    
            versionref = namesplit[0]
            pagestr = namesplit[2]
            linestr = namesplit[3]
            pagenum = int(pagestr)
            self.textpath = self.textdir +r"/"+ self.bookmarkdown +r"/"+ versionref + "_Page_" + pagestr + "_" + linestr +r".txt"
            print(self.textpath)
            self.getText(self.textpath)
        else:
            print(self.imagepath + " does not exist")
            self.loadImage()
        
    def bothLoad(self):
        ''' load the matching file for either the current image or the current text '''
        def accept():
            versionref = ''
            pagestr = ''
            #if self.ImageTextPairDialog.Accepted:
            if self.ImageTextPairDialog_ui.MatchTxt2Imgbutton.isChecked():
                self.syncText2Image()
            elif self.ImageTextPairDialog_ui.MatchImg2Txtbutton.isChecked():
                print("matching image file to current text file")
                print(self.textpath)
                if self.textpath:
                    print("finding matched image file for " + self.textpath)
                    txtfilename = self.textpath
                    file = qtc.QFile(txtfilename)
                    filestr = os.path.basename(txtfilename)           
                    filedir = os.path.dirname(txtfilename)
                    filesplit = os.path.splitext(filestr)
                    filename = filesplit[0]
                    fileext = filesplit[1]                    
                    namesplit = filename.split("_")                    
                    versionref = namesplit[0]
                    pagestr = namesplit[2]
                    pagenum = int(pagestr)
                    print(self.imagedir +r"/"+ versionref + "_Page_" + pagestr + r".tif")    
                else:
                    print(self.textpath + " does not exist")
                
                self.tryimgpath = self.imagedir +r"/"+ versionref + "_Page_" + pagestr + r".tif"
                if self.tryimgpath:
                    print("opening " + self.tryimgpath)
                    self.imagepath = self.tryimgpath
                    self.showImage(self.imagepath)
                else:
                    print(self.tryimgpath + " does not exist")


        def reject():
            pass        
        
        self.ImageTextPairDialog = qtw.QDialog()
        self.ImageTextPairDialog_ui = Ui_ImageTextPairDialog()
        self.ImageTextPairDialog_ui.setupUi(self.ImageTextPairDialog)
        self.ImageTextPairDialog.show()

        self.ImageTextPairDialog_ui.buttonBox.accepted.connect(accept)
        self.ImageTextPairDialog_ui.buttonBox.rejected.connect(reject)

    def discardImage(self):
        print('Discard Line Image File')
        discarddir = self.projecthome + "Model/Project/Images/Workflow/Greek/tif_greek_lines_discard/"
        imgfile = self.ui.ImageFileName.displayText()
        shutil.move(os.path.join(self.imgdirname, imgfile), discarddir)
        self.gtvalid = False
        imagefile = self.ui.ImageFileName.displayText()
        ######################## Remove json entry
        jsonfile = self.projecthome + 'Model/Project/Data/json/PageVerseCrossReference.json'

        with open(jsonfile, 'r') as f:
            data = json.load(f)
        

        # Iterate through the data in the JSON and pop (remove)                      
        # the obj once we find it.                                                      
        for i in range(len(data)):
            if data[i]["PageLineImageFile"] == imagefile:
                data.pop(i)
                break

        # Output the updated file with pretty JSON                                      
        # Closing file
        f.close()
        
        os.remove(jsonfile)
        with open(jsonfile, 'w') as f:
            json.dump(data, f, indent=4)
        f.close()

    def Renumber_Greek_tiff_Lines(self):
        print("renumbering Greek tif lines for ground truth")
        # usage: tr.renumberimages(source, destination)
        self.tifgreekrenumberlinesDialog = qtw.QDialog()
        self.greekrenumberlines_ui = Ui_tifgreekrenumberlinesDialog()
        self.greekrenumberlines_ui.setupUi(self.tifgreekrenumberlinesDialog)
        self.tifgreekrenumberlinesDialog.show()
        
        def accept():
            # if self.pdf4tifDialog.Accepted:
            # Empty default Workflow folder
            start_page = self.greekrenumberlines_ui.StartPageLineEdit.displayText()
            end_page = self.greekrenumberlines_ui.EndPageLineEdit.displayText()
            print(f'source_folder: {source_folder},workflow_folder: {workflow_folder},complete_folder: {complete_folder}, start_page: {start_page}, end_page: {end_page}')
            #print('Workflow Folder:'+ workflow_folder,'Complete Folder:'+ complete_folder)
            for filename in os.listdir(workflow_folder):
                file_path = os.path.join(workflow_folder, filename)
                print('File Name:'+filename, 'File Path:'+file_path)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %Model/Project/Data/json/PageVerseCrossReference.json. Reason: %Model/Project/Data/json/PageVerseCrossReference.json' % (file_path, e))
            
            for filename in os.listdir(source_folder):
                print(source_folder,filename)
                source_file_path = os.path.join(source_folder, filename)

            # Extract to default Workflow folder
            print(source_file_path, workflow_folder, start_page, end_page)
            #tr.renumberimages(self.greekrenumberlines_ui.SourceLineEdit.text(), self.greekrenumberlines_ui.DestinationLineEdit.text(), self.greekrenumberlines_ui.StartPageLineEdit.displayText(), self.greekrenumberlines_ui.EndPageLineEdit.displayText())
            tr.renumberimages(source_folder, workflow_folder, start_page, end_page)
            # Extract to default Complete folder
            #if complete_folder:
                #pp.pdf4tif(source_file_path, complete_folder)
            if complete_folder:
                symlinks=False
                ignore=None
                for item in os.listdir(workflow_folder):
                    source = os.path.join(workflow_folder, item)
                    destination = os.path.join(complete_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)
            print("completed renumbering Greek tif lines for ground truth")
        def reject():
            pass

        seq = "GL4"
        
        def setdefault():
            if self.greekrenumberlines_ui.defaultsrcBox.isChecked():
                self.greekrenumberlines_ui.SourceButton.setEnabled(False)
                self.greekrenumberlines_ui.DestinationButton.setEnabled(False)
            else:
                self.greekrenumberlines_ui.SourceButton.setEnabled(True)
                self.greekrenumberlines_ui.DestinationButton.setEnabled(True)

        self.greekrenumberlines_ui.defaultsrcBox.stateChanged.connect(setdefault)
        self.greekrenumberlines_ui.SourceButton.clicked.connect(self.GreekRenumberLinesDialog)
        self.greekrenumberlines_ui.DestinationButton.clicked.connect(self.DestGreekRenumberLinesDialog)
        self.greekrenumberlines_ui.buttonBox.accepted.connect(accept)
        self.greekrenumberlines_ui.buttonBox.rejected.connect(reject)

        if self.greekrenumberlines_ui.defaultsrcBox.isChecked(): 
            
            
            # disable source button (default)
            
            # get default folder
            # Define json data        
            with open(self.projecthome + 'Model/Project/Data/json/Workflow.json') as f:
                # returns JSON object as
                # a dictionary
                data = json.load(f)
                # Search the key value using 'in' operator
                for Sequence in data:
                    
                    if Sequence['Sequence'] == seq:
                        print(Sequence['Sequence'])
                        # set source line edit to default workflow folder
                        source_folder = Sequence['DefaultSource']+r'/'
                        workflow_folder = Sequence['WorkflowFullPath']+r'/'
                        complete_folder = Sequence['CompleteFullPath']+r'/'
                        self.greekrenumberlines_ui.SourceLineEdit.setText(source_folder)
                        self.greekrenumberlines_ui.DestinationLineEdit.setText(workflow_folder)
                        self.greekrenumberlines_ui.StartPageLineEdit.setText("1")
                        #print(f'source_folder: {source_folder},workflow_folder: {workflow_folder},complete_folder: {complete_folder}')


        rsp = self.tifgreekrenumberlinesDialog.exec_()
        
            
        print("completed renumbering Greek tif lines for ground truth")
        # tr.renumberimages(r"~/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_40_Matthew/", "~/Projects/Python/Images/Greek/tif_greek_tif4groundtruth/")
        # tr.renumberimages(r"~/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_41_Mark/", "~/Projects/Python/Images/Greek/tif_greek_tif4groundtruth/")    

    def GreekRenumberLinesDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select rename tif Greek lines source folder"))

        if self.directory:
            self.greekrenumberlines_ui.SourceLineEdit.setText(self.directory+r'/')

    def DestGreekRenumberLinesDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select rename Greek lines destination folder"))
        
        if self.directory:
            self.greekrenumberlines_ui.DestinationLineEdit.setText(self.directory+r'/')

    '''def Stage_Greek_RenamedLinesDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select rename tif Greek lines source folder"))

        if self.directory:
            self.stagegreeklines_ui.SourceLineEdit.setText(self.directory+r'/')'''

    '''def Stage_Greek_RenumberedLinesDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select rename tif Greek lines source folder"))

        if self.directory:
            self.stagegreeklines_ui.SourceLineEdit.setText(self.directory+r'/')'''
    
    def Stage_Greek_tiff_Lines(self):
        print("staging Greek tif lines for ground truth")
        # usage: tr.stageimages(source, destination, startpage, endpage)
        self.tifgreekstagelinesDialog = qtw.QDialog()
        self.greekstagelines_ui = Ui_tifgreekstagelinesDialog()
        self.greekstagelines_ui.setupUi(self.tifgreekstagelinesDialog)
        self.tifgreekstagelinesDialog.show()
        
        def accept():
            # if self.pdf4tifDialog.Accepted:
            # Empty default Workflow folder
            start_page = self.greekstagelines_ui.StartPageLineEdit.displayText()
            end_page = self.greekstagelines_ui.EndPageLineEdit.displayText()
            print(f'source_folder: {source_folder},workflow_folder: {workflow_folder},complete_folder: {complete_folder}, start_page: {start_page}, end_page: {end_page}')
            #print('Workflow Folder:'+ workflow_folder,'Complete Folder:'+ complete_folder)
            '''for filename in os.listdir(workflow_folder):
                file_path = os.path.join(workflow_folder, filename)
                print('File Name:'+filename, 'File Path:'+file_path)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %Model/Project/Data/json/PageVerseCrossReference.json. Reason: %Model/Project/Data/json/PageVerseCrossReference.json' % (file_path, e))'''
            
            for filename in os.listdir(source_folder):
                print(source_folder,filename)
                source_file_path = os.path.join(source_folder, filename)

            # Extract to default Workflow folder
            print(source_file_path, workflow_folder, start_page, end_page)
            #tr.stageimages(self.greekstagelines_ui.SourceLineEdit.text(), self.greekstagelines_ui.DestinationLineEdit.text(), self.greekstagelines_ui.StartPageLineEdit.displayText(), self.greekstagelines_ui.EndPageLineEdit.displayText())
            tr.stageimages(source_folder, workflow_folder, start_page, end_page)
            # Extract to default Complete folder
            #if complete_folder:
                #pp.pdf4tif(source_file_path, complete_folder)
            if complete_folder:
                symlinks=False
                ignore=None
                for item in os.listdir(workflow_folder):
                    source = os.path.join(workflow_folder, item)
                    destination = os.path.join(complete_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)
            print("completed staging Greek tif lines for ground truth")
        def reject():
            pass

        seq = "GT4"
        
        def setdefault():
            if self.greekstagelines_ui.defaultsrcBox.isChecked():
                self.greekstagelines_ui.SourceButton.setEnabled(False)
                self.greekstagelines_ui.DestinationButton.setEnabled(False)
            else:
                self.greekstagelines_ui.SourceButton.setEnabled(True)
                self.greekstagelines_ui.DestinationButton.setEnabled(True)

        self.greekstagelines_ui.defaultsrcBox.stateChanged.connect(setdefault)
        self.greekstagelines_ui.SourceButton.clicked.connect(self.GreekStageLinesDialog)
        self.greekstagelines_ui.DestinationButton.clicked.connect(self.DestGreekStageLinesDialog)
        self.greekstagelines_ui.buttonBox.accepted.connect(accept)
        self.greekstagelines_ui.buttonBox.rejected.connect(reject)

        if self.greekstagelines_ui.defaultsrcBox.isChecked(): 
            
            
            # disable source button (default)
            
            # get default folder
            # Define json data        
            with open(self.projecthome + 'Model/Project/Data/json/Workflow.json') as f:
                # returns JSON object as
                # a dictionary
                data = json.load(f)
                # Search the key value using 'in' operator
                for Sequence in data:
                    
                    if Sequence['Sequence'] == seq:
                        print(Sequence['Sequence'])
                        # set source line edit to default workflow folder
                        source_folder = self.projecthome + Sequence['DefaultSource']+r'/'
                        workflow_folder = self.projecthome + Sequence['WorkflowFullPath']+r'/'
                        complete_folder = self.projecthome + Sequence['CompleteFullPath']+r'/'
                        self.greekstagelines_ui.SourceLineEdit.setText(source_folder)
                        self.greekstagelines_ui.DestinationLineEdit.setText(workflow_folder)
                        self.greekstagelines_ui.StartPageLineEdit.setText("1")
                        #print(f'source_folder: {source_folder},workflow_folder: {workflow_folder},complete_folder: {complete_folder}')


        rsp = self.tifgreekstagelinesDialog.exec_()
        
            
        print("completed staging Greek tif lines for ground truth")
        # tr.stageimages(r"c:/users/max/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_40_Matthew/", "c:/users/max/Projects/Python/Images/Greek/tif_greek_tif4groundtruth/")
        # tr.stageimages(r"c:/users/max/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_41_Mark/", "c:/users/max/Projects/Python/Images/Greek/tif_greek_tif4groundtruth/")    
    
    '''def Stage_Greek_tiff_Lines(self):
        print("renumbering Greek tif lines for ground truth")
        # usage: tr.renumberimages(source, destination)
        self.stagegreeklinesDialog = qtw.QDialog()
        self.stagegreeklines_ui = Ui_tifgreekstagelinesDialog()
        self.stagegreeklines_ui.setupUi(self.stagegreeklinesDialog)
        self.stagegreeklinesDialog.show()
        
        def accept():
            # if self.pdf4tifDialog.Accepted:
            # Empty default Workflow folder
            print(f'source_renamed_folder: {source_renamed_folder},source_renumbered_folder: {source_renumbered_folder},workflow_folder: {workflow_folder},complete_folder: {complete_folder}')
            #print('Workflow Folder:'+ workflow_folder,'Complete Folder:'+ complete_folder)
            for filename in os.listdir(workflow_folder):
                file_path = os.path.join(workflow_folder, filename)
                print('File Name:'+filename, 'File Path:'+file_path)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %Model/Project/Data/json/PageVerseCrossReference.json. Reason: %Model/Project/Data/json/PageVerseCrossReference.json' % (file_path, e))
            

            # Stage Renamed Files
            for filename in os.listdir(source_renamed_folder):
                print(source_renamed_folder,filename)
                source_file_path = os.path.join(source_renamed_folder, filename)

            # Extract to default Workflow folder
            print(source_file_path, workflow_folder,)
            #tr.renumberimages(self.stagegreeklines_ui.SourceLineEdit.text(), self.stagegreeklines_ui.DestinationLineEdit.text(), self.stagegreeklines_ui.StartPageLineEdit.displayText(), self.stagegreeklines_ui.EndPageLineEdit.displayText())
            
            tr.stageimages(source_renamed_folder, workflow_folder)
            
            # Extract to default Complete folder
            #if complete_folder:
                #pp.pdf4tif(source_file_path, complete_folder)
            if complete_folder:
                symlinks=False
                ignore=None
                for item in os.listdir(workflow_folder):
                    source = os.path.join(workflow_folder, item)
                    destination = os.path.join(complete_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)

            # Stage Renumbered Files
            for filename in os.listdir(source_renumbered_folder):
                print(source_renumbered_folder,filename)
                source_file_path = os.path.join(source_renumbered_folder, filename)

            # Extract to default Workflow folder
            print(source_file_path, workflow_folder,)
            #tr.renumberimages(self.stagegreeklines_ui.SourceLineEdit.text(), self.stagegreeklines_ui.DestinationLineEdit.text(), self.stagegreeklines_ui.StartPageLineEdit.displayText(), self.stagegreeklines_ui.EndPageLineEdit.displayText())
            
            tr.stageimages(source_renumbered_folder, workflow_folder)
            
            # Extract to default Complete folder
            #if complete_folder:
                #pp.pdf4tif(source_file_path, complete_folder)
            if complete_folder:
                symlinks=False
                ignore=None
                for item in os.listdir(workflow_folder):
                    source = os.path.join(workflow_folder, item)
                    destination = os.path.join(complete_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)

            print("completed staging Greek tif lines for ground truth")

        def reject():
            pass

        seq = "GL5"
        
        def setdefault():
            if self.stagegreeklines_ui.defaultsrcBox.isChecked():
                self.stagegreeklines_ui.SourceRenamedButton.setEnabled(False)
                self.stagegreeklines_ui.DestinationButton.setEnabled(False)
            else:
                self.stagegreeklines_ui.SourceRenamedButton.setEnabled(True)
                self.stagegreeklines_ui.DestinationButton.setEnabled(True)

        self.stagegreeklines_ui.defaultsrcBox.stateChanged.connect(setdefault)
        self.stagegreeklines_ui.SourceRenamedButton.clicked.connect(self.GreekRenumberLinesDialog)
        self.stagegreeklines_ui.DestinationButton.clicked.connect(self.DestGreekRenumberLinesDialog)
        self.stagegreeklines_ui.buttonBox.accepted.connect(accept)
        self.stagegreeklines_ui.buttonBox.rejected.connect(reject)

        if self.stagegreeklines_ui.defaultsrcBox.isChecked(): 
               
            # disable source button (default)
            
            # get default folder
            # Define json data        
            with open(self.projecthome + 'Model/Project/Data/json/Workflow.json') as f:
                # returns JSON object as
                # a dictionary
                data = json.load(f)
                # Search the key value using 'in' operator
                for Sequence in data:
                    
                    if Sequence['Sequence'] == seq:
                        print(Sequence['Sequence'])
                        # set source line edit to default workflow folder
                        source_renamed_folder = Sequence['DefaultSource']+r'/'
                        workflow_folder = Sequence['WorkflowFullPath']+r'/'
                        complete_folder = Sequence['CompleteFullPath']+r'/'
                        self.stagegreeklines_ui.SourceRenamedLineEdit.setText(source_renamed_folder)
                        self.stagegreeklines_ui.DestinationLineEdit.setText(workflow_folder)
                        #print(f'source_folder: {source_folder},workflow_folder: {workflow_folder},complete_folder: {complete_folder}')
        
        seq = "GL6"
        
        def setdefault():
            if self.stagegreeklines_ui.defaultsrcBox.isChecked():
                self.stagegreeklines_ui.SourceRenumberedButton.setEnabled(False)
            else:
                self.stagegreeklines_ui.SourceRenumberedButton.setEnabled(True)

        self.stagegreeklines_ui.SourceRenumberedButton.clicked.connect(self.GreekRenumberLinesDialog)

        if self.stagegreeklines_ui.defaultsrcBox.isChecked(): 
            
            
            # disable source button (default)
            
            # get default folder
            # Define json data        
            with open(self.projecthome + 'Model/Project/Data/json/Workflow.json') as f:
                # returns JSON object as
                # a dictionary
                data = json.load(f)
                # Search the key value using 'in' operator
                for Sequence in data:
                    
                    if Sequence['Sequence'] == seq:
                        print(Sequence['Sequence'])
                        # set source line edit to default workflow folder
                        source_renumbered_folder = Sequence['DefaultSource']+r'/'
                        self.stagegreeklines_ui.SourceRenumberedLineEdit.setText(source_renumbered_folder)
                        #print(f'source_folder: {source_folder},workflow_folder: {workflow_folder},complete_folder: {complete_folder}')


        #rsp = self.tifstagegreeklines_uiDialog.exec_()'''
  
    def GreekStageLinesDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select rename tif Greek lines source folder"))

        if self.directory:
            self.greekstagelines_ui.SourceLineEdit.setText(self.directory+r'/')

    def DestGreekStageLinesDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select rename Greek lines destination folder"))
        
        if self.directory:
            self.greekstagelines_ui.DestinationLineEdit.setText(self.directory+r'/')

    '''def DestGreekStageLinesDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select rename Greek lines destination folder"))
        
        if self.directory:
            self.stagegreeklines_ui.DestinationLineEdit.setText(self.directory+r'/')'''

    def SaveImgFileDialog(self):
        dirpath = "Model/Project/Images/Workflow/Greek/tif_greek_lines_4groundtruth/"
        imgname = os.path.basename(self.imgfilename)
        imgfilepath = os.path.join(dirpath,imgname)
        print(imgname,"\t",imgfilepath)
        #self.qimage.save(imgfilepath,"PNG")        
        image = self.pixmap
        image.save(qtw.QFileDialog.getSaveFileName(self.ui.centralwidget, 'Save Image As', dirpath,
                                            'Name (*.jpg *.jpeg *.png *.tiff *.tif)'))
        
        '''FontChange/path = qtw.QFileDialog.getSaveFileName(
            self.centralwidget, 'Save Image As', '', 'Image Files (*.png *.jpg *.jpeg *.tif)')[0]
        with open(path, 'w') as file:
            #my_Img = self.qimage
            file.write(self.imgfilename)
        file.close()'''

    def SaveAsCorrectedTextFileDialog(self):
        self.path = qtw.QFileDialog.getSaveFileName(
            self.ui.centralwidget, 'Save Corrected text file', '',
            'Text files (*.txt)')[0]
        with open(self.path, 'w') as file:
            my_CorrectedText = self.ui.TextFileEdit.toPlainText()
            file.write(my_CorrectedText)
        file.close()

    def SaveCorrectedTextFileDialog(self, MainWindow):
        #defaultdir = r"c:/users/max/Projects/Python/EstablishTruth/Greek lines4groundtruth/"
        defaultdir = r"Model/Project/Text/EstablishTruth/Greek/txt_greek_lines_autosplit/" + self.greekbookmarkdown + "/"
       
        
        defaultfile = self.ui.TextFileName.displayText()
        path = self.projecthome + defaultdir + defaultfile

        if defaultfile == "":
            path = qtw.QFileDialog.getSaveFileName(
                self.ui.centralwidget, 'Save Corrected text file', '',
                'Text files (*.txt)')[0]
        with open(path, 'w') as file:
            my_CorrectedText = self.ui.TextFileEdit.toPlainText()
            file.write(my_CorrectedText)
        file.close()

    def discardText(self):        
        print('Discard Line Text File')
        discarddir = self.projecthome + "Model/Project/Text/EstablishTruth/Greek/txt_greek_lines_discard"
        txtfile = self.ui.TextFileName.displayText()
        shutil.move(os.path.join(self.txtdirname, txtfile), discarddir)
        self.gtvalid = False

    def Renumber_Greek_text_Lines(self):
        print("renaming Greek textlines for ground truth review")
        #usage: tr.sortcroplines(source, splitdir, linebox)
        self.renumber_greek_text_linesDialog = qtw.QDialog()
        self.renumber_greeklines_ui = Ui_renumbergreektextlinesDialog()
        self.renumber_greeklines_ui.setupUi(self.renumber_greek_text_linesDialog)
        self.renumber_greek_text_linesDialog.show()
        #tr.sortcroplines(r"c:/users/max/Projects/Python/Images/Greek/png_greek_deskew/greek_book_40_Matthew/","c:/users/max/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_40_Matthew/","c:/users/max/Projects/Python/Images/Greek/tif_greek_linebox/greek_book_40_Matthew/")

        def setdefault():
            if self.renumber_greeklines_ui.defaultsrcBox.isChecked():
                self.renumber_greeklines_ui.SourceButton.setEnabled(False)
                self.renumber_greeklines_ui.DestinationButton.setEnabled(False)

            else:
                self.renumber_greeklines_ui.SourceButton.setEnabled(True)
                self.renumber_greeklines_ui.DestinationButton.setEnabled(True)

        def accept():
            # if self.crop_greeklinesDialog.Accepted:
            # Empty default Workflow folder
            print('Workflow Folder:'+ workflow_dest_folder,'Complete Folder:'+ complete_dest_folder)
            for filename in os.listdir(workflow_dest_folder):
                file_path = os.path.join(workflow_dest_folder, filename)
                #print('File Name:'+filename, 'File Path:'+file_path)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %Model/Project/Data/json/PageVerseCrossReference.json. Reason: %Model/Project/Data/json/PageVerseCrossReference.json' % (file_path, e))
            
            for filename in os.listdir(source_folder):
                print(source_folder,filename)
                #source_file_path = os.path.join(source_folder, filename)
            
            # Extract to default Workflow folder
            print(source_folder, workflow_dest_folder)
            #self.splittextlines(self.split_greeklines_ui.SourceLineEdit.text(),self.split_greeklines_ui.DestinationLineEdit.text())
            #self.splittextlines(source_folder,source_folder)
            tr.text2groundtruth(self.renumber_greeklines_ui.SourceLineEdit.text(),self.renumber_greeklines_ui.DestinationLineEdit.text())
            '''
            # Copy Workflow folder to default Complete folder
            if complete_dest_folder:
                symlinks=False
                ignore=None
                for item in os.listdir(workflow_dest_folder):
                    source = os.path.join(workflow_dest_folder, item)
                    destination = os.path.join(complete_dest_folder, item)
                    if os.path.isdir(workflow_dest_folder):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)

            # Copy Workflow line box folder to default Complete line box folder
            if complete_box_folder:
                symlinks=False
                ignore=None
                for item in os.listdir(workflow_box_folder):
                    source = os.path.join(workflow_box_folder, item)
                    destination = os.path.join(complete_box_folder, item)
                    if os.path.isdir(workflow_box_folder):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy(source, destination)'''

        def reject():
            pass

        self.renumber_greeklines_ui.defaultsrcBox.stateChanged.connect(setdefault)
        self.renumber_greeklines_ui.SourceButton.clicked.connect(self.RenumberGreekTextLinesDialog)
        self.renumber_greeklines_ui.DestinationButton.clicked.connect(self.DestRenumberGreekTextLinesDialog)
        self.renumber_greeklines_ui.buttonBox.accepted.connect(accept)
        self.renumber_greeklines_ui.buttonBox.rejected.connect(reject)

        seq = ["GL7","AddStep"]
        
        if self.renumber_greeklines_ui.defaultsrcBox.isChecked(): 
        # disable source button (default)
            
            for step in seq:

                # Define json data        
                with open(self.projecthome + 'Model/Project/Data/json/Workflow.json') as f:
                    # returns JSON object as
                    # a dictionary
                    data = json.load(f)

                    # Search the key value using 'in' operator
                    for Sequence in data:
                        # print(Sequence['Sequence'])
                        if Sequence['Sequence'] == step:
                            # set line edits to their default workflow folders
                            if step == "GL7":
                                self.renumber_greeklines_ui.SourceLineEdit.setText(Sequence['DefaultSource']+r'/'+self.greekbookmarkdown+r'/')
                                source_folder = Sequence['DefaultSource']+r'/'+self.greekbookmarkdown+r'/'
                                self.renumber_greeklines_ui.DestinationLineEdit.setText(Sequence['WorkflowFullPath']+r'/'+self.greekbookmarkdown+r'/')
                                workflow_dest_folder = Sequence['WorkflowFullPath']+r'/'+self.greekbookmarkdown+r'/'
                                complete_dest_folder = Sequence['CompleteFullPath']+r'/'+self.greekbookmarkdown+r'/'                                
                f.close()
            
        rsp = self.renumber_greek_text_linesDialog.exec_()
        print("completed renaming Greek textlines for ground truth review")
        #tr.sortcroplines(r"c:/users/max/Projects/Python/Images/Greek/png_greek_deskew/greek_book_41_Mark/","c:/users/max/Projects/Python/Images/Greek/tif_greek_autosplit/greek_book_41_Mark/","c:/users/max/Projects/Python/Images/Greek/tif_greek_linebox/greek_book_41_Mark/")

    def RenumberGreekTextLinesDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select Greek text pages source folder"))

        if self.directory:
            self.renumber_greeklines_ui.SourceLineEdit.setText(self.directory+r'/')

    def DestRenumberGreekTextLinesDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select Greek text lines destination folder"))
        
        if self.directory:
            self.renumber_greeklines_ui.DestinationLineEdit.setText(self.directory+r'/')  

    def on_font_update(self):
        # update font to selection and size       
        #font = qtg.QFont()
        #font.setFamily(self.ui.fontComboBox.currentFont())
        #print(self.ui.fontComboBox.currentFont())
        font = qtg.QFont(self.ui.fontComboBox.currentFont())
        font.setPointSize(self.ui.fontSizeBox.value())
        #font = qtg.QFont(self.font)
        #font.setPointSize(int(self.fontsize))
        self.ui.TextFileEdit.setFont(font)
        self.ui.OCRTextEdit.setFont(font)

# OCR Functions
    def GetRawOCRtext(self):
        file = qtc.QFile(self.imgpath)
        if file.open(qtc.QIODevice.ReadOnly):
            #info = qtc.QFileInfo(path)
            self.ui.OCRTextEdit.clear()
            my_OCR_rawtext = pytesseract.image_to_string(self.imgpath,lang="feg")
            my_OCR_cleantext = " ".join(my_OCR_rawtext.split())
            #self.OCRDocument.insertPlainText(my_OCR_rawtext)
            self.ui.OCRTextEdit.setText(my_OCR_cleantext)
            file.close()
        
        # update font to selection and size  
        self.on_font_update()

    def autoScan(self):
        
        self.ui.OCRAccuracyLineEdit.clear()
        self.ui.OCRAccuracyLineEdit.setText('0.00')
        if self.ui.AutoScancheckBox.isChecked():
            print('conducting OCR autoscan')
            self.GetRawOCRtext()
        else:
            self.ui.OCRTextEdit.clear()

    def OCRAccuracy(self):
        print(f'calculating OCR accuracy result for: {self.ui.OCRTextEdit.displayText()}') 
        
        if self.ui.OCRTextEdit.displayText() != None:

            OCRtext = self.ui.OCRTextEdit.text()
            OCRsplit = OCRtext.split()
            print(f'OCRsplit: {OCRsplit}')

            Linetext = self.ui.TextFileEdit.toPlainText()
            Linesplit = Linetext.split()
            print(f'Linesplit: {Linesplit}')
            
            OCRwords = len(OCRsplit)
            print('OCR wordcount:' + str(OCRwords))
            Linewords = len(Linesplit)
            print('Line wordcount:' + str(Linewords))

            matchTotal = 0
            patternlist = []
            wordlist = []

            for ocrword in OCRsplit:
                #pattern = re.compile(re.escape(ocrword))
                #pattern = r'\b' + r'\w+'
                print(f'ocrword: {ocrword}')
                pattern = re.compile(re.escape(ocrword))
                for lineword in Linesplit:            
                    print(f'lineword: {lineword}')
                    if re.search(pattern, lineword):
                        matchTotal += 1
                
            if matchTotal > 0:
                print(f'matchTotal: {matchTotal}')

                OCRsymbols = len(OCRtext)
                print('OCR symbolcount:' + str(OCRsymbols))

                Linesymbols = len(Linetext)
                print('Line symbolcount:' + str(Linesymbols))
                
                OCRFraction =  matchTotal / Linewords
                
                #OCRFraction = matchTotal/Linewords 
                OCRDecimal = Decimal(str(OCRFraction))
                OCRPercent = OCRDecimal * 100
                if OCRPercent > 100:
                    OCRPercent = 100.000
                OCRAccuracy = round(OCRPercent, 2)

                print('OCR Accuracy = ' + str(OCRAccuracy))
                #self.ui.OCRAccuracyLineEdit.clear()
                self.ui.OCRAccuracyLineEdit.setText(str(OCRAccuracy))
        else:
            self.ui.OCRAccuracyLineEdit.clear()
            self.ui.OCRAccuracyLineEdit.setText('0.00')

        '''jsonfile = self.projecthome + 'Model/Project/Data/json/GrounderSession.json'
        
        with open(jsonfile, 'r') as f:
            data = json.load(f)
            
            ocraccuracy_key = r"self.ocraccuracy"       

            for Setting in data:
                if Setting['Setting'] == self.ocraccuracy_key:
                    Setting['CurrentValue'] = self.ocraccuracy
                    print(Setting['CurrentValue'])
        f.close()

        os.remove(jsonfile)
        with open(jsonfile, 'w') as f:
            json.dump(data, f, indent=4)
        f.close()'''    

# Book Chapter:Verse Combo Box fuctions
    def selectBookCombo(self):
        oldbookabbr = self.bookabbr
        self.bookabbr = self.ui.bookComboBox.currentText()
        
        if self.ui.bookComboBox.currentText() != oldbookabbr:
                  
            jsonfile = self.projecthome + 'Model/Project/Data/json/BooksMarkDown.json'
            
            with open(jsonfile, 'r') as f:
                data = json.load(f)
                for BookAbbr in data:
                    if BookAbbr['BookAbbr'] == self.bookabbr:
                        self.bookmarkdown = BookAbbr['BookMarkdown']
                        self.sourcebookmarkdown = 'source'+self.bookmarkdown
                        self.greekbookmarkdown = 'greek'+self.bookmarkdown
                        self.latinbookmarkdown = 'latin'+self.bookmarkdown
                        print(self.bookmarkdown,self.sourcebookmarkdown,self.greekbookmarkdown,self.latinbookmarkdown)
            f.close()
            
            jsonfile = self.projecthome + 'Model/Project/Data/json/GrounderSession.json'
            
            with open(jsonfile, 'r') as f:
                data = json.load(f)
                bookabbr_key = r"self.bookabbr"
                
                source_book_markdown_key = r"self.sourcebookmarkdown"
                greek_book_markdown_key = r"self.greekbookmarkdown"
                latin_book_markdown_key = r"self.latinbookmarkdown"

                for Setting in data:
                    if Setting['Setting'] == bookabbr_key:
                        Setting['CurrentValue'] = self.bookabbr
                    elif Setting['Setting'] == source_book_markdown_key:
                        Setting['CurrentValue'] = self.sourcebookmarkdown
                    elif Setting['Setting'] == greek_book_markdown_key:
                        Setting['CurrentValue'] = self.greekbookmarkdown
                    elif Setting['Setting'] == latin_book_markdown_key:
                        Setting['CurrentValue'] = self.latinbookmarkdown
                    print(Setting['CurrentValue'])
            f.close()
            
            os.remove(jsonfile)
            with open(jsonfile, 'w') as f:
                json.dump(data, f, indent=4)
            f.close()

            # Opening JSON file
            '''with open(self.projecthome + 'Model/Project/Data/json/BooksAbbrName.json') as f:
                # returns JSON object as
                    # a dictionary
                data = json.load(f)'''
            
            #self.ui.bookComboBox.clear()
            
            # Iterating through the json
            # list          
            '''for booknumber in data:
                print(booknumber['bookabbr'])
                self.ui.bookComboBox.addItem(booknumber['bookabbr'])
            
            # Closing file
            f.close()'''
            
        self.ui.bookComboBox.setCurrentText(self.bookabbr)
        self.ui.StartbookComboBox.setCurrentText(self.bookabbr)

    def loadChapterCombo(self):
        self.ui.StartchapterComboBox.clear()
        # Opening JSON file
        with open(self.projecthome + 'Model/Project/Data/json/BookChapter.json') as f:
            # returns JSON object as
            # a dictionary
            data = json.load(f)
        # Iterating through the json
        # list
        for Chapter in data:
            if Chapter['Book'] == self.ui.StartbookComboBox.currentText():
                self.ui.StartchapterComboBox.addItem(str(Chapter['Chapter']))
        # Closing file
        f.close()

        self.startchapter = self.ui.StartchapterComboBox.currentText()
        self.startchapternum = int(self.startchapter)
        self.startchaptercount = self.ui.StartchapterComboBox.count()

    def loadVerseCombo(self):
        self.ui.StartverseComboBox.clear()

        # Opening JSON file
        with open(self.projecthome + 'Model/Project/Data/json/BookChapterVerse.json') as f:
            # returns JSON object as
            # a dictionary
            data = json.load(f)
            
        # Iterating through the json
        # list
        for Verse in data:
            if Verse['Book'] == self.ui.StartbookComboBox.currentText() and str(Verse['Chapter']) == self.ui.StartchapterComboBox.currentText():
                self.ui.StartverseComboBox.addItem(str(Verse["Verse"]))
        # Closing file
        f.close()

# Page fuctions
    def loadPageText(self):
        self.getPage()
        if self.pagetextpath:
            self.pagetextfile = qtc.QFile(self.pagetextpath)
            self.pagetextfilename = os.path.basename(self.pagetextpath)
            self.showPageText(self.pagetextpath) 
    
    def sortPageFiles(self):
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
        self.sorted_pagefilelist = sorted(self.pagetextfileList, key=alphanum_key)
        #self.fileList.sort()
        #print(self.sorted_txtfilelist)
        self.pagedirIterator = iter(self.pagetextfileList)
        self.pagedirRevIterator = reversed(self.sorted_pagefilelist)
        while True:
            # cycle through the iterator until the current file is found
            if next(self.pagedirIterator) == self.pagetextpath:
                break
        while True:
            # cycle through the reverse iterator until the current file is found
            if next(self.pagedirRevIterator) == self.pagetextpath:
                break
        jsonfile = self.projecthome + 'Model/Project/Data/json/GrounderSession.json'
        
        with open(jsonfile, 'r') as f:
            data = json.load(f)
            pagetextfileList_key = r"self.pagetextfileList"
            for Setting in data:
                if Setting['Setting'] == pagetextfileList_key:
                    Setting['CurrentValue'] = self.pagetextfileList
                    print(Setting['CurrentValue'])
        f.close()

        os.remove(jsonfile)
        with open(jsonfile, 'w') as f:
            json.dump(data, f, indent=4)
        f.close()
    
    def showPageText(self,txtfilename):       
        #self.pagetextfile = txtfilename
        if self.pagetextfile.open(qtc.QIODevice.ReadOnly):
            stream = qtc.QTextStream(self.pagetextfile)
            stream.setCodec("UTF-8")
            pagetext = stream.readAll()
            info = qtc.QFileInfo(self.pagetextpath)
            if info.completeSuffix() == 'txt':
                #self.ui.editor_pagetext.setHtml(pagetext
                self.ui.PageText.insertPlainText(pagetext)
            else:
                self.ui.PageText.setPlainText(pagetext)
            self.pagetext = self.ui.PageText.toPlainText()
            self.on_page_font_update()

            self.pageAutoSeek()
    
    def pageAutoSeek(self):

        if self.ui.PageAutoSeekcheckBox.isChecked():
            cursor = self.ui.PageText.textCursor()
            cursor.setPosition(0)
            for i in range(self.linenum):
                if i == 0:
                    cursor.movePosition(qtg.QTextCursor.StartOfLine,qtg.QTextCursor.MoveAnchor)       
                else:
                    cursor.movePosition(qtg.QTextCursor.NextBlock,qtg.QTextCursor.MoveAnchor)
            cursor.movePosition(qtg.QTextCursor.EndOfLine,qtg.QTextCursor.KeepAnchor)
            self.ui.PageText.setTextCursor(cursor)
            self.ui.PageText.ensureCursorVisible()
            try:
                if cursor.selectedText() != self.ui.TextFileEdit.toPlainText():
                    raise PageTextError
            except PageTextError:
                msg = qtw.QMessageBox()
                msg.setIcon(qtw.QMessageBox.Warning)
                # setting message for Message Box
                msg.setText("The selected page text does not match the current line text.  Please check spelling and spacing.")
                # setting Message box window title
                msg.setWindowTitle("Page Text Warning")
                # declaring buttons on Message Box
                msg.setStandardButtons(qtw.QMessageBox.Ok)
                # start the app
                retval = msg.exec_()
        
        else:
            print("Page text auto seek disabled")
 
    def getPage(self):  
        self.ui.PageText.clear()
        textfilestr = self.ui.TextFileName.displayText()    
        filesplit = os.path.splitext(textfilestr)  
        filename = filesplit[0]
        fileext = filesplit[1]
        namesplit = filename.split("_")        
        versionref = namesplit[0]
        self.pagenumstr = namesplit[2]
        pagenum = int(self.pagenumstr)
        linestr = namesplit[3]
        linenumstr = linestr.split(r'.')
        linenumstr = linenumstr[0]
        linenumstr = linenumstr.replace('Line','')
        self.linenum = int(linenumstr)
        self.ui.PagelineEdit.setText(self.pagenumstr)
        self.pagetextpath = self.pagetextdir + "/" + self.greekbookmarkdown + "/" + versionref + "_" + "Page" + "_" + self.pagenumstr + fileext
        print(f'Page text file path: {self.pagetextpath}')
        
        jsonfile = self.projecthome + 'Model/Project/Data/json/GrounderSession.json'
        
        with open(jsonfile, 'r') as f:
            data = json.load(f)
            pagetextpath_key = r"self.pagetextpath"
            pagetextdir_key = r"self.pagetextdir"
            pagetextpage_key = r"self.pagetextpage"
            pagetextpath = self.pagetextpath
            pagetextpath = pagetextpath.replace(self.projecthome,"")
            pagetextdir = self.pagetextdir
            pagetextdir = pagetextdir.replace(self.projecthome,"")
            for Setting in data:
                if Setting['Setting'] == pagetextpath_key:
                    Setting['CurrentValue'] = pagetextpath
                    print(Setting['CurrentValue'])
                elif Setting['Setting'] == pagetextdir_key:  
                    Setting['CurrentValue'] = pagetextdir
                elif Setting['Setting'] == pagetextpage_key:  
                    Setting['CurrentValue'] = self.pagenumstr
                    print(Setting['CurrentValue'])
        f.close()

        os.remove(jsonfile)
        with open(jsonfile, 'w') as f:
            json.dump(data, f, indent=4)
        f.close()

    def SavePageTextDialog(self):
        
        defaultfile =  os.path.basename(self.pagetextpath)
        defaultpath = self.pagetextpath

        print(f'Page textpath: {defaultpath}')
        
        if defaultpath:
            path = defaultpath
            filename = defaultfile
        else:
            path = qtw.QFileDialog.getSaveFileName(
                self.ui.centralwidget, 'Save Corrected text file', '',
                'Text files (*.txt)')[0]
            filename = os.path.basename(path)        

        print(f'Saving Page Text: {path}')
        with open(path, 'w') as file:
            my_CorrectedText = self.ui.PageText.toPlainText()
            file.write(my_CorrectedText)
        
        file.close()
    
    def on_page_font_update(self):
        # update Verse font to selection and size       
        font = qtg.QFont(self.ui.PagefontComboBox.currentFont())
        font.setPointSize(self.ui.PagefontSizeBox.value())
        self.ui.PageText.setFont(font)

    def on_lang_select(self):
        pass

# Verse fuctions
    def loadVerseText(self):
         if self.versetextpath:
            self.versetextfile = qtc.QFile(self.versetextpath)
            self.versetxtfilename = os.path.basename(self.versetextpath)
            self.showVerseText(self.versetextpath)       

    def showVerseText(self,txtfilename):       
        #self.versetextfile = txtfilename
        self.ui.VerseText.clear()
        if self.versetextfile.open(qtc.QIODevice.ReadOnly):
            stream = qtc.QTextStream(self.versetextfile)
            stream.setCodec("UTF-8")
            versetext = stream.readAll()
            info = qtc.QFileInfo(self.versetextpath)
            if info.completeSuffix() == 'txt':
                #self.ui.editor_versetext.setHtml(versetext
                self.ui.VerseText.insertPlainText(versetext)
            else:
                self.ui.VerseText.setPlainText(versetext)          

            self.on_verse_font_update()
        
    def getVerse(self,find_end):
        print('Getting the book, chapter, and verse cross references ')
        cursor = self.ui.VerseText.textCursor()
        cursor.setPosition(find_end)
        
        fullverse = cursor.block().text()
        print(f'full verse text: {fullverse}')
        lenverse = len(fullverse)
        print(f'full verse length: {lenverse}') 
        
        cursor.movePosition(qtg.QTextCursor.EndOfBlock,qtg.QTextCursor.MoveAnchor)
        self.blockend = cursor.position()
        print(f'block end postion = {cursor.position()}')
        cursor.movePosition(qtg.QTextCursor.StartOfBlock,qtg.QTextCursor.MoveAnchor)
        print(f'start line postion = {cursor.position()}')
        
        cursor.movePosition(qtg.QTextCursor.Right, qtg.QTextCursor.KeepAnchor,3)
        print(f'endbook postion = {cursor.position()}')
        #self.ui.VerseText.moveCursor(qtg.QTextCursor.EndOfWord,qtg.QTextCursor.KeepAnchor)
        self.book = cursor.selection().toPlainText()
        print(f'book: {self.book}')
        self.ui.StartbookComboBox.currentTextChanged.disconnect(self.loadChapterCombo)
        self.ui.StartbookComboBox.setCurrentText(self.book)
        self.ui.StartbookComboBox.currentTextChanged.connect(self.loadChapterCombo)
        
        cursor.movePosition(qtg.QTextCursor.NextWord, qtg.QTextCursor.MoveAnchor)
        print(f'NextWord Position: {cursor.position()}')
        cursor.movePosition(qtg.QTextCursor.EndOfWord, qtg.QTextCursor.KeepAnchor)
        self.chapter = cursor.selection().toPlainText()
        print(f'chapter: {self.chapter}')
        self.ui.StartchapterComboBox.currentTextChanged.disconnect(self.loadVerseCombo)
        self.ui.StartchapterComboBox.setCurrentText(self.chapter)
        self.ui.StartchapterComboBox.currentTextChanged.connect(self.loadVerseCombo)

        cursor.movePosition(qtg.QTextCursor.NextWord, qtg.QTextCursor.MoveAnchor)
        print(f'NextWord Position: {cursor.position()}')
        cursor.movePosition(qtg.QTextCursor.EndOfWord, qtg.QTextCursor.KeepAnchor)
        self.verse = cursor.selection().toPlainText()
        print(f'verse: {self.verse}')
        self.ui.StartverseComboBox.currentTextChanged.disconnect(self.updateXRef_json)
        self.ui.StartverseComboBox.setCurrentText(self.verse)
        self.ui.StartverseComboBox.currentTextChanged.connect(self.updateXRef_json)

        self.bcvstr = self.book + " " + self.chapter + ":" + self.verse
        print(f'book chapter:verse - {self.bcvstr}')
        self.lenbcv = len(self.bcvstr)
        print(f'length of bcv string: {self.lenbcv}')
        # may want to create auto enable radio button in gui.

        #self.updatesession()
    
    def updatesession(self):

        jsonfile = self.projecthome + 'Model/Project/Data/json/GrounderSession.json'
        
        with open(jsonfile, 'r') as f:
            data = json.load(f)
            versetextpath_key = r"self.versetextpath"
            versetextdir_key = r"self.versetextdir"
            startbookabbr_key = r"self.startbookabbr"
            startchapter_key = r"self.startchapter"
            startverse_key = r"startverse_key "
            for Setting in data:
                if Setting['Setting'] == versetextpath_key:
                    Setting['CurrentValue'] = self.versetextpath
                    print(Setting['CurrentValue'])
                elif Setting['Setting'] == versetextdir_key:  
                    Setting['CurrentValue'] = self.versetextdir
                elif Setting['Setting'] == startbookabbr_key:
                    Setting['CurrentValue'] = self.book
                elif Setting['Setting'] == startchapter_key:
                    Setting['CurrentValue'] = self.chapter
                elif Setting['Setting'] == startverse_key:
                    Setting['CurrentValue'] = self.verse
                    print(Setting['CurrentValue'])

        f.close()

        os.remove(jsonfile)
        with open(jsonfile, 'w') as f:
            json.dump(data, f, indent=4)
        f.close()

    def reconnectStartComboBoxes(self):
        self.ui.StartbookComboBox.currentTextChanged.connect(self.selectBookCombo)
        self.ui.StartbookComboBox.currentTextChanged.connect(self.loadChapterCombo)
        self.ui.StartchapterComboBox.currentTextChanged.connect(self.loadVerseCombo)
        self.ui.StartverseComboBox.currentTextChanged.connect(self.updateXRef_json)
    
    def verseAutoSeek(self):
        self.verselength = 0
        if self.ui.VerseAutoSeekcheckBox.isChecked():
            # Get line text
            text = self.ui.TextFileEdit.toPlainText()
            print(f'Current line text: {text}')
            # Get verse text
            versetext = self.ui.VerseText.toPlainText()
            #print(f'Current line versetext: {versetext}')

            cursor = self.ui.VerseText.textCursor()
            print(f'Verse last ending cursor position: {self.VerseLastEnd}')
            ''' 
            if self.VerseLastEnd > 0:
                self.VerseStart = self.VerseLastEnd
            else:
                self.VerseStart = 0

            cursor.setPosition(self.VerseStart)
            print(f'Beginning cursor position: {cursor.position()}')
            '''
            cursor.setPosition(0)
            # Check if line text has hyphenations
            linestr = re.sub(r'[]','',text)
            lenstr = len(linestr)
            print(f'Line string to find in Verse text: {linestr}')
            print(f'Length of Line string to find in Verse text: {lenstr}')
            #print(f'Find direction = {self.findirection}')
            # Save this self.projecthome + 'Model/Project/Data/json/PageVerseCrossReference.json' string for troubleshooting:
            # Model/Project/Data/json/PageVerseCrossReference.json = "ΙΒΛΟΣ γενέ"

            ### FIND ENTIRE LINE
            start = versetext.find(linestr)
            end = start + len(linestr)
            print(f'start: {start} end: {end}')

            
            if start > 0:

                cursor.movePosition(qtg.QTextCursor.Right, qtg.QTextCursor.MoveAnchor, start)
                cursor.movePosition(qtg.QTextCursor.Right,qtg.QTextCursor.KeepAnchor, end-start)
                selversetext = cursor.selectedText()
                print(f'selected verse text: {selversetext}')
                           
                self.ui.VerseText.setTextCursor(cursor)
                self.ui.VerseText.ensureCursorVisible()

                try:
                    if cursor.selectedText() != linestr:
                        raise VerseTextError
                except VerseTextError:
                    msg = qtw.QMessageBox()
                    msg.setIcon(qtw.QMessageBox.Warning)
                    # setting message for Message Box
                    msg.setText("The selected verse text does not match the current line text.  Please check spelling, spacing and use of combining diacriticals.")
                    # setting Message box window title
                    msg.setWindowTitle("Verse Text Warning")
                    # declaring buttons on Message Box
                    msg.setStandardButtons(qtw.QMessageBox.Ok)
                    # start the app
                    retval = msg.exec_()

                self.VerseStart = start
                print(f'verse cursor start: {self.VerseStart}')
                self.VerseLastEnd = end 
                print(f'verse cursor last found end position: {self.VerseLastEnd}')
                self.getVerse(start)

                #self.updatesession()
                
                self.updateXRef_json()

            #if start == -1 and self.findirection == 'next':
            if start == -1:
                print(f'complete text line not found')
                #start = 0

                self.getVerse(self.VerseLastEnd)
                print(f'Getting current verse position at {self.VerseLastEnd}')                
                print(f'End of block position: {self.blockend}')
                print(f'verse last end position: {self.VerseLastEnd}')
                cursor.movePosition(qtg.QTextCursor.Right, qtg.QTextCursor.MoveAnchor, self.VerseLastEnd)
                print(f'Anchor position: {cursor.position()}')
                cursor.movePosition(qtg.QTextCursor.Right, qtg.QTextCursor.KeepAnchor, self.blockend - self.VerseLastEnd)
                #cursor.movePosition(qtg.QTextCursor.Right, qtg.QTextCursor.KeepAnchor, qtg.QTextCursor.EndOfBlock - self.VerseLastEnd)
                print(f'End of block position: {cursor.position()}')
                self.ui.VerseText.setTextCursor(cursor)
                self.ui.VerseText.ensureCursorVisible()

                self.updateXRef_json()
                
                remversetext = cursor.selectedText()
                if remversetext[0] == " ":
                    remversetext = remversetext[1:]
                remverselen = len(remversetext)
                print(f'remaining verse text: {remversetext} remaining verse length: {remverselen}')
                linestart = linestr.find(remversetext)

                try:                      
                    if linestart == -1 and self.findirection == 'next':
                        raise VerseTextError
                except VerseTextError:
                    msg = qtw.QMessageBox()
                    msg.setIcon(qtw.QMessageBox.Warning)
                    # setting message for Message Box
                    msg.setText("The selected part 1 starting verse text does not match the current part 1 line text.  Please check spelling, spacing and use of combining diacriticals..")
                    # setting Message box window title
                    msg.setWindowTitle("Verse Text Warning")
                    # declaring buttons on Message Box
                    msg.setStandardButtons(qtw.QMessageBox.Ok)
                    # start the app
                    retval = msg.exec_()

                lineparttwo = linestr[remverselen:]
                lenparttwo = len(lineparttwo)
                print(f'line part two: {lineparttwo} length part two: {lenparttwo}')
                
                parttwostart = versetext.find(lineparttwo)
                print(f'line part two start: {parttwostart}')
                parttwoend = parttwostart + lenparttwo
                print(f'line part two end: {parttwoend}')
                print(f'block end: {self.blockend}')

                try:                      
                    if parttwostart == -1 and self.findirection == 'next':
                        raise VerseTextError
                except VerseTextError:
                    msg = qtw.QMessageBox()
                    msg.setIcon(qtw.QMessageBox.Warning)
                    # setting message for Message Box
                    msg.setText("The part 2 ending verse text does not match the line part 2 text.  Please check spelling, spacing and use of combining diacriticals.")
                    # setting Message box window title
                    msg.setWindowTitle("Verse Text Warning")
                    # declaring buttons on Message Box
                    msg.setStandardButtons(qtw.QMessageBox.Ok)
                    # start the app
                    retval = msg.exec_()
                if parttwostart > 0:                   
                    print(f'current cursor before position: {cursor.position()}')
                    cursor.movePosition(qtg.QTextCursor.Right, qtg.QTextCursor.KeepAnchor, parttwoend - self.blockend)
                    print(f'current cursor after position: {cursor.position()}')
                    print(f'part two selected text: {cursor.selectedText()}')
                    self.ui.VerseText.setTextCursor(cursor)
                    self.ui.VerseText.ensureCursorVisible()

                    #self.VerseStart = self.VerseLastEnd
                    self.VerseStart = self.VerseLastEnd-1
                    print(f'verse cursor start: {self.VerseStart}')
                    self.VerseLastEnd = parttwoend
                    print(f'verse cursor last found end position: {self.VerseLastEnd}')

            if start == -1 and self.findirection == 'prev':
                print(f'complete previous text line not found')
                self.prevImage()
                self.prevText()
   
        else:
            print("Verse text auto seek disabled")    
            self.reconnectStartComboBoxes()
            return
        
        jsonfile = self.projecthome + 'Model/Project/Data/json/GrounderSession.json'
        
        with open(jsonfile, 'r') as f:
            data = json.load(f)
            
            VerseStart_key = r"self.VerseStart"
            VerseLastEnd_key = r"self.VerseLastEnd"       

            for Setting in data:
                if Setting['Setting'] == VerseStart_key:
                    Setting['CurrentValue'] = self.VerseStart   
                elif Setting['Setting'] == VerseLastEnd_key:
                    Setting['CurrentValue'] = self.VerseLastEnd
                    print(f'Final cursor end position: {self.VerseLastEnd}')
        f.close()

        os.remove(jsonfile)
        with open(jsonfile, 'w') as f:
            json.dump(data, f, indent=4)
        f.close()

    def SaveVerseTextDialog(self):
        
        defaultfile =  os.path.basename(self.versetextpath)
        defaultpath = self.versetextpath
        
        if defaultpath:
            path = defaultpath
            filename = defaultfile
        else:
            path = qtw.QFileDialog.getSaveFileName(
                self.ui.centralwidget, 'Save Corrected text file', '',
                'Text files (*.txt)')[0]
            filename = os.path.basename(path)        

        print(f'Saving Verse Text: {path}')
        with open(path, 'w') as file:
            my_CorrectedText = self.ui.VerseText.toPlainText()
            file.write(my_CorrectedText)
        
        file.close()

    def on_verse_font_update(self):
        # update Verse font to selection and size       
        font = qtg.QFont(self.ui.VersefontComboBox.currentFont())
        font.setPointSize(self.ui.VersefontSizeBox.value())
        self.ui.VerseText.setFont(font)

# Ground Truth Cross References
    def buildXRef(self):
        'building the PageLineCrossReference.csv from renamed linefiles'
        def sorted_alphanumeric(data):
            convert = lambda text: int(text) if text.isdigit() else text.lower()
            alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
            return sorted(data, key=alphanum_key)
            #usage:dirlist = sorted_alphanumeric(os.listdir(...)) - works great!

        path_of_images = self.projecthome + r'Model/Project/Images/Complete/Greek/tif_greek_lines_renamed/'

        list_of_images = sorted_alphanumeric(os.listdir(path_of_images))

        print(list_of_images)

        for image in list_of_images:
                
                filestr = os.path.basename(os.path.join(path_of_images, image))
                
                filestr = filestr.replace(r'.gt','')

                filesplit = os.path.splitext(filestr)
                
                filename = filesplit[0]
                
                fileext = filesplit[1]
                
                namesplit = filename.split("_")
                
                
                versionref = namesplit[0]
                
                pagestr = namesplit[2]
                
                pagenum = int(pagestr)
                
                linestr = namesplit[3].replace('Line','')

                linenum = int(linestr)

                #print(versionref,pagenum,linestr)
                print(f"namesplit: {namesplit} versionref: {versionref} pagestr: {pagestr} pagenum: {pagenum} linenum: {linenum}")

                with open(self.projecthome + r'Model/Project/Data/csv/PageVerseCrossReference.csv', 'a', newline='') as csvfile:
                    fieldnames = ['LineImageFile','ImgPageNum','ImgPageLineNum','LineTextFile','LineText','Valid','ReviewComplete','StartBook','StartChapter','StartVerse','OCRAccuracy']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writerow({'LineImageFile':filestr,'ImgPageNum':pagenum,'ImgPageLineNum':linenum,'LineTextFile':'','LineText':'','Valid':'False','ReviewComplete':'False','StartBook':'','StartChapter':'','StartVerse':'','OCRAccuracy':'0'})

    def loadPageLineCombos(self):
        'loading the Page and Line combo boxes.'
        def sorted_alphanumeric(data):
            convert = lambda text: int(text) if text.isdigit() else text.lower()
            alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
            return sorted(data, key=alphanum_key)
            #usage:dirlist = sorted_alphanumeric(os.listdir(...)) - works great!

        path_of_images = self.projecthome + r'Model/Project/Images/Workflow/Greek/tif_greek_lines_4groundtruth/'

        list_of_images = sorted_alphanumeric(os.listdir(path_of_images))

        print(list_of_images)

        for image in list_of_images:
                
                filestr = os.path.basename(os.path.join(path_of_images, image))
                
                filestr = filestr.replace(r'.gt','')

                filesplit = os.path.splitext(filestr)
                
                filename = filesplit[0]
                
                fileext = filesplit[1]
                
                namesplit = filename.split("_")
                
                
                versionref = namesplit[0]
                
                pagestr = namesplit[2]
                
                self.PVXrefDialog_ui.PagecomboBox.addItem(pagestr)

                pagenum = int(pagestr)
                
                linestr = namesplit[3].replace('Line','')
                self.PVXrefDialog_ui.LinecomboBox.addItem(linestr)

                linenum = int(linestr)

                #print(versionref,pagenum,linestr)

    def updateXRef_json(self):
        # Update Page Verse Cross Reference

        # Opening JSON file
        imagefile = self.ui.ImageFileName.displayText()
        #imagefile = imagefile.replace(r'.gt','')
        #filestr = os.path.basename(imagefile)
        filesplit = os.path.splitext(imagefile)  
        filename = filesplit[0]
        fileext = filesplit[1]
        namesplit = filename.split("_")        
        versionref = namesplit[0]
        pagestr = namesplit[2]
        pagenum = int(pagestr)
        linestr = namesplit[3].replace('Line','')
        linestr = linestr.replace('.gt',"")
        linenum = int(linestr)

        print('updating page verse cross reference')
        jsonfile = self.projecthome + 'Model/Project/Data/json/PageVerseCrossReference.json'

        with open(jsonfile, 'r') as f:
            data = json.load(f)
        
            # Iterating through the json
            # list
            for PageLineImageFile in data:
                
                if PageLineImageFile['PageLineImageFile'] == imagefile:

                    PageLineImageFile['Page'] = str(pagenum)
                    PageLineImageFile['PageLine'] = str(linenum)
                    PageLineImageFile['PageLineTextFile'] = self.ui.TextFileName.displayText()
                    PageLineImageFile['StartBook'] = self.ui.StartbookComboBox.currentText()
                    PageLineImageFile['StartChapter'] = self.ui.StartchapterComboBox.currentText()
                    PageLineImageFile['StartVerse'] = self.ui.StartverseComboBox.currentText()
        # Closing file
        f.close()
        
        os.remove(jsonfile)
        with open(jsonfile, 'w') as f:
            json.dump(data, f, indent=4)
        f.close()

    def updateXRef_csv(self):
        if self.ui.ReviewCompletecheckBox.isChecked():
        
            'update the PageLineCrossReference.csv'
            imagefile = self.ui.ImageFileName.displayText()
            textfile = self.ui.TextFileName.displayText()
            linetext = self.ui.TextFileEdit.toPlainText()
            if self.ui.ReviewCompletecheckBox.isChecked():
                self.gtreview = True
            startbook = self.ui.StartbookComboBox.currentText()
            startchapter = self.ui.StartchapterComboBox.currentText()
            startverse =  self.ui.StartverseComboBox.currentText()
            self.ocraccuracy = self.ui.OCRAccuracyLineEdit.displayText()

            filestr = os.path.basename(imagefile)    
            filesplit = os.path.splitext(filestr)  
            filename = filesplit[0]
            fileext = filesplit[1]
            namesplit = filename.split("_")        
            versionref = namesplit[0]
            pagestr = namesplit[2]
            pagenum = int(pagestr)
            linestr = namesplit[3].replace('Line','')
            linenum = int(linestr)
            
            XReffile = self.projecthome + r'Model/Project/Data/csv/PageVerseCrossReference.csv'
            tempfile = NamedTemporaryFile(mode='w', delete=False)
            
            fields = ['LineImageFile','ImgPageNum','ImgPageLineNum','LineTextFile','LineText','Valid','ReviewComplete','StartBook','StartChapter','StartVerse','OCRAccuracy']

            with open(XReffile, 'r', encoding='UTF-8') as csvfile, tempfile:
                reader = csv.DictReader(csvfile, fieldnames=fields)
                writer = csv.DictWriter(tempfile, fieldnames=fields)
                for row in reader:
                    if row['LineImageFile'] == imagefile:
                        print('updating cross reference for ',row['LineImageFile'])
                        row['ImgPageNum'],row['ImgPageLineNum'],row['LineTextFile'],row['LineText'],row['Valid'],row['ReviewComplete'],row['StartBook'],row['StartChapter'],row['StartVerse'],row['OCRAccuracy'] = pagenum, linenum, textfile, linetext, self.gtvalid, self.gtreview, startbook, startchapter, startverse, self.ocraccuracy

                    row = {'LineImageFile': row['LineImageFile'], 'ImgPageNum': row['ImgPageNum'], 'ImgPageLineNum': row['ImgPageLineNum'], 'LineTextFile': row['LineTextFile'],row['LineText']:'LineText',row['Valid']:'Valid',row['ReviewComplete']:'ReviewComplete',row['StartBook']:'StartBook',row['StartChapter']:'StartChapter',row['StartVerse']:'StartVerse',row['OCRAccuracy']:'OCRAccuracy'}
                    writer.writerow(row)

            shutil.move(tempfile.name, filename)  

    def PageVerseXref(self):
        
        
        print("Page Verse Cross Reference Dialog")
        # usage: tr.renumberimages(source, destination)

        self.PageVerseXrefDialog = qtw.QDialog()
        self.PVXrefDialog_ui = Ui_PageVerseXrefDialog()
        self.PVXrefDialog_ui.setupUi(self.PageVerseXrefDialog)
        self.PageVerseXrefDialog.show()
        
        # Initialize XRef Dialog
        def InitDialog():            
            
            lineimgfile = self.ui.ImageFileName.displayText()
            linetxtfile =  self.ui.TextFileName.displayText()
            imagefile = lineimgfile
            imagefile = imagefile.replace(r'.gt','')
            filestr = os.path.basename(imagefile)
            filesplit = os.path.splitext(filestr)  
            filename = filesplit[0]
            fileext = filesplit[1]
            namesplit = filename.split("_")        
            versionref = namesplit[0]
            pagestr = namesplit[2]
            #pagenum = int(pagestr)
            #page = pagestr
            page = self.ui.PagelineEdit.displayText()
            pagenum = int(page)
            
            linestr = namesplit[3].replace('Line','')
            linenum = int(linestr)
            line = linenum
            
            # Initialize Filenames

            pageimgfile = versionref + "_" + "Page" + "_" + page + fileext 
            self.PVXrefDialog_ui.PageImageFileName.setText(pageimgfile)
            
            self.PVXrefDialog_ui.LineImageFileName.setText(lineimgfile)
            
            pagetextfile = os.path.basename(self.pagetextpath)
            self.PVXrefDialog_ui.PageTextFileName.setText(pagetextfile)
            
            self.PVXrefDialog_ui.LineTextFileName.setText(linetxtfile)

            book = self.ui.StartbookComboBox.currentText()
            chapter = self.ui.StartchapterComboBox.currentText()
            verse = self.ui.StartverseComboBox.currentText()
            
            self.xref_df = pd.read_json(self.projecthome + 'Model/Project/Data/json/PageVerseCrossReference.json')
            self.xref_table_df = self.xref_df[["Page","PageLine","StartBook","StartChapter","StartVerse"]]
            
            # Initialize comboBoxes
            page_col = self.xref_df["Page"]
            page_nums = page_col.unique()
            pages = [str(x) for x in page_nums]
            self.PVXrefDialog_ui.PagecomboBox.clear()
            self.PVXrefDialog_ui.PagecomboBox.addItems(pages)
            self.PVXrefDialog_ui.PagecomboBox.setCurrentText(page)
            self.PVXrefDialog_ui.PagecomboBox.currentTextChanged.connect(set_pageframe)
            

            self.PVXrefDialog_ui.LinecomboBox.setCurrentText(str(line))
            self.PVXrefDialog_ui.LinefindPushButton.clicked.connect(set_pagelineframe)
            #self.PVXrefDialog_ui.LinecomboBox.currentTextChanged.connect()
            
            self.PVXrefDialog_ui.StartbookComboBox.setCurrentText(book)
            #self.ui.bookComboBox.currentTextChanged.connect(self.selectBookCombo)
            self.PVXrefDialog_ui.StartchapterComboBox.setCurrentText(chapter)
            self.PVXrefDialog_ui.StartverseComboBox.setCurrentText(verse)

            '''page = self.PVXrefDialog_ui.PagecomboBox.currentText()
            line = self.PVXrefDialog_ui.LinecomboBox.currentText()
            book = self.PVXrefDialog_ui.StartbookComboBox.currentText()
            chapter = self.PVXrefDialog_ui.StartchapterComboBox.currentText()
            verse = self.PVXrefDialog_ui.StartverseComboBox.currentText()'''
        
            #df = pd.read_json(self.projecthome + 'Model/Project/Data/json/PageVerseCrossReference.json')
            #table_df = df[["Page","PageLine","StartBook","StartChapter","StartVerse"]]
            
            #self.PVXrefDialog_ui.LinefindPushButton.clicked.connect(pagefilter(page))
            #self.PVXrefDialog_ui.LinefindPushButton.clicked.connect(linefilter(page, line))
            #self.PVXrefDialog_ui.VersefindPushButton.clicked.connect(versefind(book, chapter, verse))
        
            model = pandasModel(self.xref_table_df)
            self.PVXrefDialog_ui.XrefTableView.setModel(model)
        
        def set_pageframe():
            page = self.PVXrefDialog_ui.PagecomboBox.currentText()
            page_filter = (self.xref_df["Page"] == int(page))
            self.xref_table_df = self.xref_df.loc[page_filter,["Page","PageLine","StartBook","StartChapter","StartVerse"]]
            
            #set linecombo
            line_col = self.xref_table_df["PageLine"]
            print(line_col)
            #line_col = self.xref_df["PageLine"]
            #line_nums = line_col.unique()
            lines = [str(x) for x in line_col]
            self.PVXrefDialog_ui.LinecomboBox.clear()
            self.PVXrefDialog_ui.LinecomboBox.addItems(lines)
            
        def set_pagelineframe():
            page = int(self.PVXrefDialog_ui.PagecomboBox.currentText())
            line = int(self.PVXrefDialog_ui.LinecomboBox.currentText())
            page_filter = (self.xref_table_df["Page"] == page)
            page_df = self.xref_table_df[page_filter]
            page_line_filter = page_filter & (self.xref_table_df["PageLine"] == line)
            row_df = self.xref_table_df[page_line_filter]
            row_index = row_df.index[0]
            print(f'row index: {row_index}')
            #table_df = row_df[["Page","PageLine","StartBook","StartChapter","StartVerse"]]
            #table_df = row_df[["Page","PageLine","StartBook","StartChapter","StartVerse"]]
            model = pandasModel(page_df)
            self.PVXrefDialog_ui.XrefTableView.setModel(model)
            
            self.PVXrefDialog_ui.XrefTableView.selectRow(line - 1)
            idx_row = self.PVXrefDialog_ui.XrefTableView.currentIndex()
            print(f'idx_row: {idx_row}')
            #sel_row = self.PVXrefDialog_ui.XrefTableView.model().index(self.PVXrefDialog_ui.XrefTableView.currentIndex().row())
            mod_row = self.PVXrefDialog_ui.XrefTableView.model().index()
            print(f'mod_row: {mod_row}')
            #self.PVXrefDialog_ui.StartbookComboBox.setCurrentText(sel_row,2).text()
            #self.PVXrefDialog_ui.StartchapterComboBox.setCurrentText(sel_row,3).text()
            #self.PVXrefDialog_ui.StartverseComboBox.setCurrentText(sel_row,4).text()

        def rowSelectionChanged():
            print("row select")
            #loadFormView()
            #print(getSelectedBook())

        def getSelectedRowId():
            #return varui.VarianceTable.selectedItems()
            return self.PVXrefDialog_ui.XrefTableView.currentRow()

        def getSelectedBook():
            return self.PVXrefDialog_ui.XrefTableView.item(getSelectedRowId(),2).text()
        
        def versefind(book, chapter, verse):
            print("Page Verse Cross Reference Verse Find")

        InitDialog()

# Only run this code if I am actually running this script       
if __name__ == '__main__': 
    app = qtw.QApplication(sys.argv)
    w = Ui_MainWindow()
    w.show()
    #app.exec()

    # view.show()
    sys.exit(app.exec_())
