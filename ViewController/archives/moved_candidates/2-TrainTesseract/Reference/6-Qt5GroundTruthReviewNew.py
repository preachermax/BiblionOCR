# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'QT5GroundTruthReview.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
import os
import re
import pytesseract
import numpy as np
import tiffcapture
import qimage2ndarray

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
              
        self.ImageButton = QtWidgets.QPushButton(self.centralwidget)
        self.ImageButton.setGeometry(QtCore.QRect(80, 40, 100, 25))
        self.ImageButton.setObjectName("ImageButton")
        self.ImageButton.setFont(QtGui.QFont('FROMVS', 8))
        self.ImageButton.setIcon(QtGui.QIcon.fromTheme("gtk-open"))
        #self.ImageButton.clicked.connect(tifView.loadImageStackFromFile())
        self.ImageButton.clicked.connect(self.loadImage)
                
        self.TextButton = QtWidgets.QPushButton(self.centralwidget)
        self.TextButton.setGeometry(QtCore.QRect(250, 40, 100, 25))
        self.TextButton.setObjectName("TextButton")
        self.TextButton.setFont(QtGui.QFont('FROMVS', 8))
        self.TextButton.setIcon(QtGui.QIcon.fromTheme("gtk-open"))
        self.TextButton.clicked.connect(self.loadText)
        
        self.SaveAsButton = QtWidgets.QPushButton(self.centralwidget)
        self.SaveAsButton.setGeometry(QtCore.QRect(420, 40, 100, 25))
        self.SaveAsButton.setObjectName("SaveAsButton")
        self.SaveAsButton.setFont(QtGui.QFont('FROMVS', 8))
        self.SaveAsButton.setIcon(QtGui.QIcon.fromTheme("gtk-save-as"))
        self.SaveAsButton.clicked.connect(self.SaveAsCorrectedTextFileDialog)
        
        self.BothNextButton = QtWidgets.QPushButton(self.centralwidget)
        self.BothNextButton.setGeometry(QtCore.QRect(590, 40, 100, 25))
        self.BothNextButton.setObjectName("BothNextButton")
        self.BothNextButton.setFont(QtGui.QFont('FROMVS', 8))
        self.BothNextButton.setIcon(QtGui.QIcon.fromTheme("gtk-go-back-rtl"))
        self.BothNextButton.clicked.connect(self.nextImage)
        self.BothNextButton.clicked.connect(self.nextText)
        
        self.Imagelabel = QtWidgets.QLabel(self.centralwidget)
        self.Imagelabel.setGeometry(QtCore.QRect(40, 110, 64, 17))
        self.Imagelabel.setObjectName("Imagelabel")
        
        self.ImageFileName = QtWidgets.QLineEdit(self.centralwidget)
        self.ImageFileName.setGeometry(QtCore.QRect(110, 100, 431, 31))
        self.ImageFileName.setObjectName("ImageFile")
        
        self.ImageView = QtWidgets.QLabel(self.centralwidget)
        self.ImageView.setGeometry(QtCore.QRect(40, 140, 701, 51))
        self.ImageView.setMinimumSize(700, 50)
        self.ImageView.setAlignment(QtCore.Qt.AlignCenter)
        self.ImageView.setPixmap(QtGui.QPixmap(""))
        self.ImageView.setObjectName("ImageView")
        
        self.NextImgButton = QtWidgets.QPushButton(self.centralwidget)
        self.NextImgButton.setGeometry(QtCore.QRect(560, 105, 83, 25))
        self.NextImgButton.setObjectName("NextImgButton")
        self.NextImgButton.setFont(QtGui.QFont('FROMVS', 8))
        self.NextImgButton.setIcon(QtGui.QIcon.fromTheme("gtk-go-back-rtl"))
        #self.NextImgButton.clicked.connect(self.loadImage("prev"))
        self.NextImgButton.clicked.connect(self.nextImage(MainWindow,getimg="prev"))
        
        self.Textlabel = QtWidgets.QLabel(self.centralwidget)
        self.Textlabel.setGeometry(QtCore.QRect(40, 220, 64, 17))
        self.Textlabel.setObjectName("Textlabel")
        
        self.TextFileName = QtWidgets.QLineEdit(self.centralwidget)
        self.TextFileName.setGeometry(QtCore.QRect(110, 204, 431, 31))
        self.TextFileName.setObjectName("TextFileName")
        
        self.TextFileEdit = QtWidgets.QTextEdit(self.centralwidget)
        self.TextFileEdit.setGeometry(QtCore.QRect(40, 250, 701, 51))
        self.TextFileEdit.setObjectName("TextFileEdit")
        
        self.TextDocument = QtGui.QTextDocument(self.TextFileEdit)
        font = QtGui.QFont()
        font.setFamily("FROMVS")
        font.setPointSize(20)
        self.TextDocument.setDefaultFont(font)
        self.TextFileEdit.setDocument(self.TextDocument)
        
        self.NextTxtButton = QtWidgets.QPushButton(self.centralwidget)
        self.NextTxtButton.setGeometry(QtCore.QRect(560, 210, 83, 25))
        self.NextTxtButton.setObjectName("NextTxtButton")
        self.NextTxtButton.setFont(QtGui.QFont('FROMVS', 8))
        self.NextTxtButton.setIcon(QtGui.QIcon.fromTheme("gtk-go-back-rtl"))
        self.NextTxtButton.clicked.connect(self.nextText)
          
        self.SaveButton = QtWidgets.QPushButton(self.centralwidget)
        self.SaveButton.setGeometry(QtCore.QRect(645, 210, 80, 25))
        self.SaveButton.setObjectName("SaveButton")
        self.SaveButton.setFont(QtGui.QFont('FROMVS', 8))
        self.SaveButton.setIcon(QtGui.QIcon.fromTheme("gtk-save"))
        self.SaveButton.clicked.connect(self.SaveCorrectedTextFileDialog)
        
        self.OCRButton = QtWidgets.QPushButton(self.centralwidget)
        self.OCRButton.setGeometry(QtCore.QRect(40, 320, 141, 25))
        self.OCRButton.setObjectName("OCRButton")
        self.OCRButton.setFont(QtGui.QFont('FROMVS', 8))
        self.OCRButton.setIcon(QtGui.QIcon.fromTheme("gtk-execute"))
        self.OCRButton.clicked.connect(self.GetRawOCRtext)
        
        self.OCRTextEdit = QtWidgets.QTextEdit(self.centralwidget)
        self.OCRTextEdit.setGeometry(QtCore.QRect(40, 350, 701, 51))
        self.OCRTextEdit.setObjectName("OCRTextEdit")
        
        self.OCRDocument = QtGui.QTextDocument(self.OCRTextEdit)
        font = QtGui.QFont()
        font.setFamily("FROMVS")
        font.setPointSize(20)
        self.OCRDocument.setDefaultFont(font)
        self.OCRTextEdit.setDocument(self.OCRDocument)
        
        self.ChrRefplainTextEdit = QtWidgets.QPlainTextEdit(self.centralwidget)
        self.ChrRefplainTextEdit.setGeometry(QtCore.QRect(40, 420, 701, 151))
        font = QtGui.QFont()
        font.setFamily("FROMVS")
        font.setPointSize(18)
        self.ChrRefplainTextEdit.setFont(font)
        self.ChrRefplainTextEdit.setMinimumSize(QtCore.QSize(700, 150))
        self.ChrRefplainTextEdit.setObjectName("ChrRefplainTextEdit")
        ChrRefText = open('/home/max/Projects/Python/Workflow/3-ConductOCR/FROMVS ChrReference.txt').read()
        self.ChrRefplainTextEdit.setPlainText(ChrRefText)
        
        
        
        MainWindow.setCentralWidget(self.centralwidget)
        
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.dirIterator = None
        self.imgfileList = []
        self.txtfileList = []
        
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
    
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
                fileName = QFileDialog.getOpenFileName(self, "Open TIFF stack file.")
            elif QT_VERSION_STR[0] == '5':
                fileName, dummy = QFileDialog.getOpenFileName(self, "Open TIFF stack file.")
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
    
    def loadImage(self, MainWindow, getimg = ""):
        
        imgfilename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.centralwidget, 'Select Image', '', 'Image Files (*.png *.jpg *.jpeg *.tif)')
        
        if imgfilename:
            self.ImageFileName.setText(os.path.basename(imgfilename))       
            self.imgfilename = imgfilename
            if imgfilename.endswith('.tif'):
                self.loadImageStackFromFile(imgfilename)
                self.showFrame(0)
                pixmap = QtGui.QPixmap.fromImage(self.qimage).scaled(self.ImageView.size(), 
                    QtCore.Qt.KeepAspectRatio)

            else:
                pixmap = QtGui.QPixmap(imgfilename).scaled(self.ImageView.size(), 
                    QtCore.Qt.KeepAspectRatio)
                        
            if pixmap.isNull():
                return
            self.ImageView.setPixmap(pixmap)
            imgdirpath = os.path.dirname(imgfilename)
            self.imgfileList = []
            for i in os.listdir(imgdirpath):
                ipath = os.path.join(imgdirpath, i)
                if os.path.isfile(ipath) and i.endswith(('.png', '.jpg', '.jpeg', '.tif')):
                    self.imgfileList.append(ipath)
            convert = lambda text: int(text) if text.isdigit() else text.lower()
            alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
            sorted_imgfilelist = sorted(self.imgfileList, key=alphanum_key)
            #self.fileList.sort()
            print(sorted_imgfilelist)
            self.imgdirIterator = iter(sorted_imgfilelist)
            while True:
                # cycle through the iterator until the current file is found
                if next(self.imgdirIterator) == imgfilename:
                    break

    def nextImage(self,MainWindow,getimg):
        if getimg == "prev":
            self.imgdirIterator = reversed(self.sorted_imgfilelist)
        else:
            self.imgdirIterator = iter(self.sorted_imgfilelist)
        
        # ensure that the file list has not been cleared due to missing files     
        if self.imgfileList:
            try:
                imgfilename = next(self.imgdirIterator)
                self.ImageFileName.setText(os.path.basename(imgfilename))
                if imgfilename.endswith('.tif'):
                    self.loadImageStackFromFile(imgfilename)
                    self.showFrame(0)
                    pixmap = QtGui.QPixmap.fromImage(self.qimage).scaled(self.ImageView.size(), 
                        QtCore.Qt.KeepAspectRatio)
                else:
                    pixmap = QtGui.QPixmap(imgfilename).scaled(self.ImageView.size(), 
                        QtCore.Qt.KeepAspectRatio)
                    '''pixmap = QtGui.QPixmap(imgfilename).scaled(self.ImageView.size(), 
                            QtCore.Qt.KeepAspectRatio)'''
                if pixmap.isNull():
                    # the file is not a valid image, remove it from the list
                    # and try to load the next one
                    self.imgfileList.remove(imgfilename)
                    self.prevImage()
                else:
                    self.ImageView.setPixmap(pixmap)
            except:
                # the iterator has finished, restart it
                self.imgdirIterator = iter(self.imgfileList)
                self.nextImage()
        else:
            # no file list found, load an image
            self.loadImage()

    def prevImage(self,MainWindow):
        

        #self.nextImage(MainWindow)

        # ensure that the file list has not been cleared due to missing files
        if self.imgfileList:
            try:
                convert = lambda text: int(text) if text.isdigit() else text.lower()
                alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
                sorted_imgfilelist = sorted(self.imgfileList, key=alphanum_key)
                self.imgdirIterator = reversed(sorted_imgfilelist)
                while True:
                    # cycle through the iterator until the current file is found
                    if next(self.imgdirIterator) == self.imgfilename:
                        break

                imgfilename = next(self.imgdirIterator)
                self.ImageFileName.setText(os.path.basename(imgfilename))
                if imgfilename.endswith('.tif'):
                    self.loadImageStackFromFile(imgfilename)
                    self.showFrame(0)
                    pixmap = QtGui.QPixmap.fromImage(self.qimage).scaled(self.ImageView.size(), 
                        QtCore.Qt.KeepAspectRatio)
                else:
                    pixmap = QtGui.QPixmap(imgfilename).scaled(self.ImageView.size(), 
                        QtCore.Qt.KeepAspectRatio)
                    pixmap = QtGui.QPixmap(imgfilename).scaled(self.ImageView.size(), 
                            QtCore.Qt.KeepAspectRatio)
                if pixmap.isNull():
                    # the file is not a valid image, remove it from the list
                    # and try to load the next one
                    self.imgfileList.remove(imgfilename)
                    self.nextImage()
                else:
                    self.ImageView.setPixmap(pixmap)
            except:
                # the iterator has finished, restart it
                sorted_imgfilelist = sorted(self.imgfileList, key=alphanum_key)
                self.imgdirIterator = reversed(sorted_imgfilelist)
        else:
            # no file list found, load an image
            self.loadImage()    
    
    
    
    def loadText(self, MainWindow):
        textpath = QtWidgets.QFileDialog.getOpenFileName(
            self.centralwidget, 'Open text file', '',
            'Text files (*.txt)')[0]
        if textpath:
            textfile = QtCore.QFile(textpath)
            txtfilename = os.path.basename(textpath)
            self.TextFileName.setText(txtfilename)
            if textfile.open(QtCore.QIODevice.ReadOnly):
                stream = QtCore.QTextStream(textfile)
                text = stream.readAll()
                info = QtCore.QFileInfo(textpath)
                if info.completeSuffix() == '.gt.txt':
                    #self.editor_text.setHtml(text)
                    self.TextFileEdit.insertPlainText(text)
                else:
                    self.TextFileEdit.setPlainText(text)
                #textfile.close()
                txtdirpath = os.path.dirname(textpath)
                self.txtfileList = []
            for t in os.listdir(txtdirpath):
                tpath = os.path.join(txtdirpath, t)
                if os.path.isfile(tpath) and t.endswith(('.gt.txt')):
                    self.txtfileList.append(tpath)
            convert = lambda text: int(text) if text.isdigit() else text.lower()
            alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
            sorted_txtfilelist = sorted(self.txtfileList, key=alphanum_key)
            #self.fileList.sort()
            print(sorted_txtfilelist)
            self.txtdirIterator = iter(sorted_txtfilelist)
            while True:
                # cycle through the iterator until the current file is found
                if next(self.txtdirIterator) == textpath:
                    break
    
    def nextText(self,MainWindow):
    # ensure that the file list has not been cleared due to missing files
        if self.txtfileList:
            try:
                txtfile = next(self.txtdirIterator)
                self.TextFileName.setText(os.path.basename(txtfile))
                #pixmap = QtGui.QPixmap(textfile).scaled(self.ImageView.size(), 
                    #QtCore.Qt.KeepAspectRatio)
                textfile = QtCore.QFile(txtfile)
                if textfile.open(QtCore.QIODevice.ReadOnly):
                    stream = QtCore.QTextStream(textfile)
                    text = stream.readAll()
                    info = QtCore.QFileInfo(textfile)
                    if info.completeSuffix() == '.gt.txt':
                    #self.editor_text.setHtml(text)
                        self.TextFileEdit.insertPlainText(text)
                    else:
                        self.TextFileEdit.setPlainText(text)
                else:
                    # the file is not a valid image, remove it from the list
                    # and try to load the next one
                    self.txtfileList.remove(textfile)
                    self.nextText()
            except:
                # the iterator has finished, restart it
                self.txtdirIterator = iter(sorted_txtfilelist)
                self.nextText()
        else:
            # no file list found, load an image
            self.loadText()
        
    def SaveAsCorrectedTextFileDialog(self, MainWindow):
        path = QtWidgets.QFileDialog.getSaveFileName(
            self.centralwidget, 'Save Corrected text file', '',
            'Text files (*.txt)')[0]
        with open(path, 'w') as file:
            my_CorrectedText = self.TextDocument.toPlainText()
            file.write(my_CorrectedText)
        file.close()

    def SaveCorrectedTextFileDialog(self, MainWindow):
        defaultdir = r"/home/max/Projects/Python/EstablishTruth/Greek lines4groundtruth/"
        defaultfile = self.TextFileName.displayText()

        if defaultfile:
            path = defaultdir + defaultfile
            filename = defaultfile
        else:
            path = QtWidgets.QFileDialog.getSaveFileName(
                self.centralwidget, 'Save Corrected text file', '',
                'Text files (*.txt)')[0]
        with open(path, 'w') as file:
            my_CorrectedText = self.TextDocument.toPlainText()
            file.write(my_CorrectedText)
        file.close()
        
    def GetRawOCRtext(self):
        path = QtWidgets.QFileDialog.getOpenFileName(
            self.centralwidget, 'Open image file', '',
            'Images (*.tif *.png)')[0]
        if path:
            file = QtCore.QFile(path)
            if file.open(QtCore.QIODevice.ReadOnly):
                info = QtCore.QFileInfo(path)
                my_OCR_rawtext = pytesseract.image_to_string(path,lang="feg")
                #self.OCRDocument.insertPlainText(my_OCR_rawtext)
                self.OCRTextEdit.insertPlainText(my_OCR_rawtext)
                file.close()

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Ground Truth Review"))
        
        self.ImageButton.setText(_translate("MainWindow", "Open Image File"))
        self.Imagelabel.setText(_translate("MainWindow", "Image:"))
        self.NextImgButton.setText(_translate("MainWindow", "Next "))
        #self.pushButton_5.setText(_translate("MainWindow", "Previous"))
        self.BothNextButton.setText(_translate("MainWindow", "Both Next "))
        self.TextButton.setText(_translate("MainWindow", "Open Text File"))
        self.Textlabel.setText(_translate("MainWindow", "Text File:"))
        self.NextTxtButton.setText(_translate("MainWindow", "Next "))
        self.SaveAsButton.setText(_translate("MainWindow", "Save As"))
        self.SaveButton.setText(_translate("MainWindow", "Save"))
        
        self.OCRButton.setText(_translate("MainWindow", "OCR Image File"))
        
        
        
        


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

