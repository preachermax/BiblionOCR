# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'QT5GroundTruthReview.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

# PyQt5 imports
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc

# Python imports
import os
import sys
import re
import pytesseract
import numpy as np
import tiffcapture
import qimage2ndarray

# Custom imports
from MyGrounderUI import Ui_Grounder

class Ui_MainWindow(qtw.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # pre-compiled QtDesigner Ui_MainUI and extended slots code starts here:        
        # load the pre-compiled QtDesigner Ui_MainUI user interface
        self.ui = Ui_Grounder()
        self.ui.setupUi(self)           

        self.ui.ImageButton.clicked.connect(self.loadImage)       
        self.ui.TextButton.clicked.connect(self.loadText)
        self.ui.SaveImgButton.clicked.connect(self.SaveImgFileDialog)
        self.ui.BothPrevButton.clicked.connect(self.prevImage)
        self.ui.BothPrevButton.clicked.connect(self.prevText)
        self.ui.BothNextButton.clicked.connect(self.nextImage)
        self.ui.BothNextButton.clicked.connect(self.nextText)
        self.ui.PrevImgButton.clicked.connect(self.prevImage)
        self.ui.NextImgButton.clicked.connect(self.nextImage)
        
        '''self.TextDocument = qtg.QTextDocument(self.TextFileEdit)
        font = qtg.QFont()
        font.setFamily("FROMVS")
        font.setPointSize(20)
        self.TextDocument.setDefaultFont(font)
        self.TextFileEdit.setDocument(self.TextDocument)'''
        
        self.ui.PrevTxtButton.clicked.connect(self.prevText)
        self.ui.NextTxtButton.clicked.connect(self.nextText)
        self.ui.SaveButton.clicked.connect(self.SaveCorrectedTextFileDialog)
        self.ui.SaveAsButton.clicked.connect(self.SaveAsCorrectedTextFileDialog)
        self.ui.OCRButton.clicked.connect(self.GetRawOCRtext)
        
        '''self.OCRDocument = qtg.QTextDocument(self.OCRTextEdit)
        font = qtg.QFont()
        font.setFamily("FROMVS")
        font.setPointSize(20)
        self.OCRDocument.setDefaultFont(font)
        self.OCRTextEdit.setDocument(self.OCRDocument)'''
        
        ChrRefText = open('/home/max/Projects/BiblionOCR/ViewController/Application/3-ConductOCR/FROMVS ChrReference.txt').read()
        self.ui.ChrRefplainTextEdit.setPlainText(ChrRefText)


        self.dirIterator = None
        self.imgfileList = []
        self.txtfileList = []
        
        #self.retranslateUi(MainWindow)
        #qtc.QMetaObject.connectSlotsByName(MainWindow)
    
    def setImageStack(self, tiffCaptureHandle):
        """ Set the scene's current TIFF image stack to the input TiffCapture object.
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
        if len(fileName) == 0:
            if QT_VERSION_STR[0] == '4':
                fileName = qtw.QFileDialog.getOpenFileName(self, "Open TIFF stack file.")
            elif QT_VERSION_STR[0] == '5':
                fileName, dummy = qtw.QFileDialog.getOpenFileName(self, "Open TIFF stack file.")
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
    
    def loadImage(self):
        
        imgfilename, _ = qtw.QFileDialog.getOpenFileName(
            self.ui.centralwidget, 'Select Image', '', 'Image Files (*.png *.jpg *.jpeg *.tif)')
        
        if imgfilename:
            self.ui.ImageFileName.setText(os.path.basename(imgfilename))       
            self.imgfilename = imgfilename
            self.showImage(self.imgfilename)
            self.sortImgFiles()
            
    def showImage(self,imgfilename):
        self.imgfilename = imgfilename
        if self.imgfilename.endswith('.tif'):
            self.loadImageStackFromFile(self.imgfilename)
            self.showFrame(0)
            self.pixmap = qtg.QPixmap.fromImage(self.qimage).scaled(self.ui.ImageView.size(), 
                qtc.Qt.KeepAspectRatio)
        else:
            self.pixmap = qtg.QPixmap(imgfilename).scaled(self.ui.ImageView.size(), 
                qtc.Qt.KeepAspectRatio)

        if self.pixmap.isNull():
            return
        self.ui.ImageView.setPixmap(self.pixmap)
        imgdirpath = os.path.dirname(self.imgfilename)
        self.imgfileList = []
        for i in os.listdir(imgdirpath):
            ipath = os.path.join(imgdirpath, i)
            if os.path.isfile(ipath) and i.endswith(('.png', '.jpg', '.jpeg', '.tif')):
                self.imgfileList.append(ipath)
        self.sortImgFiles()

    def sortImgFiles(self):
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
        self.sorted_imgfilelist = sorted(self.imgfileList, key=alphanum_key)
        #self.fileList.sort()
        #print(self.sorted_imgfilelist)
        self.imgdirIterator = iter(self.sorted_imgfilelist)
        self.nextimage = next(self.imgdirIterator)
        self.imgdirRevIterator = reversed(self.sorted_imgfilelist)
        self.previmage = next(self.imgdirRevIterator)
        while True:
            # cycle through the iterator until the current file is found
            if next(self.imgdirIterator) == self.imgfilename:
                break
        while True:
            # cycle through the reverse iterator until the current file is found
            if next(self.imgdirRevIterator) == self.imgfilename:
                break
    
    def nextImage(self):      
        #self.sortImgFiles(MainWindow,iterdir="")
        # ensure that the file list has not been cleared due to missing files     
        if self.imgfileList:
            try:
                imgfilename = self.imgfilename
                nextimgfilename = next(self.imgdirIterator)
                self.ui.ImageFileName.setText(os.path.basename(nextimgfilename))
                if nextimgfilename.endswith('.tif'):
                    self.loadImageStackFromFile(nextimgfilename)
                    self.showFrame(0)
                    pixmap = qtg.QPixmap.fromImage(self.qimage).scaled(self.ui.ImageView.size(), 
                        qtc.Qt.KeepAspectRatio)
                else:
                    pixmap = qtg.QPixmap(nextimgfilename).scaled(self.ui.ImageView.size(), 
                        qtc.Qt.KeepAspectRatio)
                    '''pixmap = qtg.QPixmap(imgfilename).scaled(self.ImageView.size(), 
                            qtc.Qt.KeepAspectRatio)'''
                '''if pixmap.isNull():
                    # the file is not a valid image, remove it from the list
                    # and try to load the next one
                    self.imgfileList.remove(nextimgfilename)
                    self.nextImage()
                else:'''
                self.showImage(nextimgfilename)
            except:
                # the iterator has finished, restart it
                self.imgdirIterator = iter(self.imgfileList)
                self.nextImage()
        else:
            # no file list found, load an image
            self.loadImage()
        
    def prevImage(self):      
        # ensure that the file list has not been cleared due to missing files     
        if self.imgfileList:
            try:
                imgfilename = self.imgfilename
                prevfilename = next(self.imgdirRevIterator)
                self.ui.ImageFileName.setText(os.path.basename(prevfilename))
                if prevfilename.endswith('.tif'):
                    self.loadImageStackFromFile(prevfilename)
                    self.showFrame(0)
                    pixmap = qtg.QPixmap.fromImage(self.qimage).scaled(self.ui.ImageView.size(), 
                        qtc.Qt.KeepAspectRatio)
                else:
                    pixmap = qtg.QPixmap(prevfilename).scaled(self.ui.ImageView.size(), 
                        qtc.Qt.KeepAspectRatio)
                '''if pixmap.isNull():
                    # the file is not a valid image, remove it from the list
                    # and try to load the next one
                    self.imgfileList.remove(prevfilename)
                    self.prevImage()
                else:'''
                self.showImage(prevfilename)
            except:
                # the iterator has finished, restart it
                self.imgdirRevIterator = reversed(self.imgfileList)
                self.imgdirIterator = iter(self.imgfileList)
                self.prevImage()
        else:
            # no file list found, load an image
            self.loadImage()
  
    def loadText(self):
        self.textpath = qtw.QFileDialog.getOpenFileName(
            self.ui.centralwidget, 'Open text file', '',
            'Text files (*.txt)')[0]
        if self.textpath:
            self.textfile = qtc.QFile(self.textpath)
            self.txtfilename = os.path.basename(self.textpath)
            self.showText(self.txtfilename)
            #print(self.textpath,"\t",self.textfile,"\t",self.txtfilename)

            #self.sortTextFiles(MainWindow)
            
    def showText(self,txtfilename):        
        #self.textfile = txtfilename
        if self.textfile.open(qtc.QIODevice.ReadOnly):
            stream = qtc.QTextStream(self.textfile)
            text = stream.readAll()
            info = qtc.QFileInfo(self.textpath)
            if info.completeSuffix() == '.gt.txt':
                #self.editor_text.setHtml(text)
                self.ui.TextFileEdit.insertPlainText(text)
            else:
                self.ui.TextFileEdit.setPlainText(text)
            #textfile.close()
            self.ui.TextFileName.setText(self.txtfilename)
            txtdirpath = os.path.dirname(self.textpath)
            self.txtfileList = []
        for t in os.listdir(txtdirpath):
            tpath = os.path.join(txtdirpath, t)
            if os.path.isfile(tpath) and t.endswith(('.gt.txt')):
                self.txtfileList.append(tpath)
        self.sortTextFiles()

    def sortTextFiles(self):
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
        self.sorted_txtfilelist = sorted(self.txtfileList, key=alphanum_key)
        #self.fileList.sort()
        #print(self.sorted_txtfilelist)
        self.txtdirIterator = iter(self.sorted_txtfilelist)
        self.txtdirRevIterator = reversed(self.sorted_txtfilelist)
        while True:
            # cycle through the iterator until the current file is found
            if next(self.txtdirIterator) == self.textpath:
                break
        while True:
            # cycle through the reverse iterator until the current file is found
            if next(self.txtdirRevIterator) == self.textpath:
                break

    def nextText(self):
        # ensure that the file list has not been cleared due to missing files
        if self.txtfileList:
            try:
                txtfile = next(self.txtdirIterator)
                self.ui.TextFileName.setText(os.path.basename(txtfile))
                #pixmap = qtg.QPixmap(textfile).scaled(self.ImageView.size(), 
                    #qtc.Qt.KeepAspectRatio)
                self.textfile = qtc.QFile(txtfile)
                self.txtfilename = os.path.basename(txtfile)
                self.dirname = os.path.dirname(self.textpath)
                #self.textpath = os.path.join(self.dirname, "/",self.txtfilename)
                self.textpath = txtfile
                print(txtfile,"\t",self.textpath,"\t",self.textfile,"\t",self.txtfilename)
                #print(self.txtfilename)
                self.showText(self.txtfilename)
            except:
                # the iterator has finished, restart it
                self.txtdirIterator = iter(self.sorted_txtfilelist)
                self.txtdirRevIterator = reversed(self.sorted_txtfilelist)
                self.nextText()
        else:
            # no file list found, load an image
            self.loadText()
    
    def prevText(self):
        # ensure that the file list has not been cleared due to missing files
        if self.txtfileList:
            try:
                #txtfile = self.textfile
                txtfile = next(self.txtdirRevIterator)
                self.ui.TextFileName.setText(os.path.basename(txtfile))
                #pixmap = qtg.QPixmap(textfile).scaled(self.ImageView.size(), 
                    #qtc.Qt.KeepAspectRatio)
                self.textfile = qtc.QFile(txtfile)
                self.txtfilename = os.path.basename(txtfile)
                self.dirname = os.path.dirname(self.textpath)
                #self.textpath = os.path.join(self.dirname, "/",self.txtfilename)
                self.textpath = txtfile
                print(txtfile,"\t",self.textpath,"\t",self.textfile,"\t",self.txtfilename)
                #print(self.txtfilename)
                self.showText(self.txtfilename)
            except:
                # the iterator has finished, restart it
                self.txtdirRevIterator = reversed(self.sorted_txtfilelist)
                self.txtdirIterator = iter(self.sorted_txtfilelist)
                self.prevText()
        else:
            # no file list found, load an image
            self.loadText()
    
    def SaveImgFileDialog(self):
        dirpath = "/home/max/Projects/Python/Images/Greek/tif_greek_tif4groundtruth"
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
        path = qtw.QFileDialog.getSaveFileName(
            self.ui.centralwidget, 'Save Corrected text file', '',
            'Text files (*.txt)')[0]
        with open(path, 'w') as file:
            my_CorrectedText = self.ui.TextDocument.toPlainText()
            file.write(my_CorrectedText)
        file.close()

    def SaveCorrectedTextFileDialog(self, MainWindow):
        defaultdir = r"/home/max/Projects/Python/EstablishTruth/Greek lines4groundtruth/"
        defaultfile = self.ui.TextFileName.displayText()

        if defaultfile:
            path = defaultdir + defaultfile
            filename = defaultfile
        else:
            path = qtw.QFileDialog.getSaveFileName(
                self.ui.centralwidget, 'Save Corrected text file', '',
                'Text files (*.txt)')[0]
        with open(path, 'w') as file:
            my_CorrectedText = self.ui.TextDocument.toPlainText()
            file.write(my_CorrectedText)
        file.close()
        
    def GetRawOCRtext(self):
        '''path = qtw.QFileDialog.getOpenFileName(
            self.centralwidget, 'Open image file', '',
            'Images (*.tif *.png)')[0]
        
        if path:
            file = qtc.QFile(path)
            if file.open(qtc.QIODevice.ReadOnly):
                info = qtc.QFileInfo(path)
                my_OCR_rawtext = pytesseract.image_to_string(path,lang="feg")
                #self.OCRDocument.insertPlainText(my_OCR_rawtext)
                self.OCRTextEdit.insertPlainText(my_OCR_rawtext)
                file.close()'''
        file = qtc.QFile(self.imgfilename)
        if file.open(qtc.QIODevice.ReadOnly):
            #info = qtc.QFileInfo(path)
            my_OCR_rawtext = pytesseract.image_to_string(self.imgfilename,lang="feg")
            #self.OCRDocument.insertPlainText(my_OCR_rawtext)
            self.ui.OCRTextEdit.insertPlainText(my_OCR_rawtext)
            file.close()

    '''def retranslateUi(self, MainWindow):
        _translate = qtc.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Ground Truth Review"))
        
        self.ImageButton.setText(_translate("MainWindow", "Open Image File"))
        self.Imagelabel.setText(_translate("MainWindow", "Image:"))
        self.PrevImgButton.setText(_translate("MainWindow", "Prev "))
        self.NextImgButton.setText(_translate("MainWindow", "Next "))
        #self.pushButton_5.setText(_translate("MainWindow", "Previous"))
        self.BothPrevButton.setText(_translate("MainWindow", "Both Prev "))
        self.BothNextButton.setText(_translate("MainWindow", "Both Next "))
        self.TextButton.setText(_translate("MainWindow", "Open Text File"))
        self.Textlabel.setText(_translate("MainWindow", "Text File:"))
        self.PrevTxtButton.setText(_translate("MainWindow", "Prev "))
        self.NextTxtButton.setText(_translate("MainWindow", "Next "))
        self.SaveImgButton.setText(_translate("MainWindow", "Save Img As"))
        self.SaveAsButton.setText(_translate("MainWindow", "Save As"))
        self.SaveButton.setText(_translate("MainWindow", "Save"))
        
        self.OCRButton.setText(_translate("MainWindow", "OCR Image File"))'''      

# Only run this code if I am actually running this script       
if __name__ == '__main__': 
    app = qtw.QApplication(sys.argv)
    w = Ui_MainWindow()
    w.show()
    app.exec()