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

class Ui_MainWindow(QtWidgets.QWidget):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
              
        self.ImageButton = QtWidgets.QPushButton(self.centralwidget)
        self.ImageButton.setGeometry(QtCore.QRect(40, 40, 100, 25))
        self.ImageButton.setObjectName("ImageButton")
        self.ImageButton.setFont(QtGui.QFont('FROMVS', 8))
        self.ImageButton.setIcon(QtGui.QIcon.fromTheme("gtk-open"))
        #self.ImageButton.clicked.connect(tifView.loadImageStackFromFile())
        self.ImageButton.clicked.connect(self.loadImage)
                
        self.TextButton = QtWidgets.QPushButton(self.centralwidget)
        self.TextButton.setGeometry(QtCore.QRect(190, 40, 100, 25))
        self.TextButton.setObjectName("TextButton")
        self.TextButton.setFont(QtGui.QFont('FROMVS', 8))
        self.TextButton.setIcon(QtGui.QIcon.fromTheme("gtk-open"))
        self.TextButton.clicked.connect(self.loadText)
        
        self.SaveImgButton = QtWidgets.QPushButton(self.centralwidget)
        self.SaveImgButton.setGeometry(QtCore.QRect(340, 40, 100, 25))
        self.SaveImgButton.setObjectName("SaveAsButton")
        self.SaveImgButton.setFont(QtGui.QFont('FROMVS', 8))
        self.SaveImgButton.setIcon(QtGui.QIcon.fromTheme("gtk-save"))
        self.SaveImgButton.clicked.connect(self.SaveImgFileDialog)
        
        self.BothPrevButton = QtWidgets.QPushButton(self.centralwidget)
        self.BothPrevButton.setGeometry(QtCore.QRect(490, 40, 100, 25))
        self.BothPrevButton.setObjectName("BothNextButton")
        self.BothPrevButton.setFont(QtGui.QFont('FROMVS', 8))
        self.BothPrevButton.setIcon(QtGui.QIcon.fromTheme("gtk-go-forward-rtl"))
        self.BothPrevButton.clicked.connect(self.prevImage)
        self.BothPrevButton.clicked.connect(self.prevText)
        
        self.BothNextButton = QtWidgets.QPushButton(self.centralwidget)
        self.BothNextButton.setGeometry(QtCore.QRect(640, 40, 100, 25))
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
        
        self.PrevImgButton = QtWidgets.QPushButton(self.centralwidget)
        self.PrevImgButton.setGeometry(QtCore.QRect(555, 105, 83, 25))
        self.PrevImgButton.setObjectName("NextImgButton")
        self.PrevImgButton.setFont(QtGui.QFont('FROMVS', 8))
        self.PrevImgButton.setIcon(QtGui.QIcon.fromTheme("gtk-go-forward-rtl"))
        self.PrevImgButton.clicked.connect(self.prevImage)
        
        self.NextImgButton = QtWidgets.QPushButton(self.centralwidget)
        self.NextImgButton.setGeometry(QtCore.QRect(658, 105, 83, 25))
        self.NextImgButton.setObjectName("NextImgButton")
        self.NextImgButton.setFont(QtGui.QFont('FROMVS', 8))
        self.NextImgButton.setIcon(QtGui.QIcon.fromTheme("gtk-go-back-rtl"))
        self.NextImgButton.clicked.connect(self.nextImage)
        
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
        
        self.PrevTxtButton = QtWidgets.QPushButton(self.centralwidget)
        self.PrevTxtButton.setGeometry(QtCore.QRect(555, 210, 83, 25))
        self.PrevTxtButton.setObjectName("NextTxtButton")
        self.PrevTxtButton.setFont(QtGui.QFont('FROMVS', 8))
        self.PrevTxtButton.setIcon(QtGui.QIcon.fromTheme("gtk-go-forward-rtl"))
        self.PrevTxtButton.clicked.connect(self.prevText)
        
        self.NextTxtButton = QtWidgets.QPushButton(self.centralwidget)
        self.NextTxtButton.setGeometry(QtCore.QRect(658, 210, 83, 25))
        self.NextTxtButton.setObjectName("NextTxtButton")
        self.NextTxtButton.setFont(QtGui.QFont('FROMVS', 8))
        self.NextTxtButton.setIcon(QtGui.QIcon.fromTheme("gtk-go-back-rtl"))
        self.NextTxtButton.clicked.connect(self.nextText)
          
        self.SaveButton = QtWidgets.QPushButton(self.centralwidget)
        self.SaveButton.setGeometry(QtCore.QRect(663, 310, 80, 25))
        self.SaveButton.setObjectName("SaveButton")
        self.SaveButton.setFont(QtGui.QFont('FROMVS', 8))
        self.SaveButton.setIcon(QtGui.QIcon.fromTheme("gtk-save"))
        self.SaveButton.clicked.connect(self.SaveCorrectedTextFileDialog)

        self.SaveAsButton = QtWidgets.QPushButton(self.centralwidget)
        self.SaveAsButton.setGeometry(QtCore.QRect(555, 310, 100, 25))
        self.SaveAsButton.setObjectName("SaveAsButton")
        self.SaveAsButton.setFont(QtGui.QFont('FROMVS', 8))
        self.SaveAsButton.setIcon(QtGui.QIcon.fromTheme("gtk-save-as"))
        self.SaveAsButton.clicked.connect(self.SaveAsCorrectedTextFileDialog)

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
        ChrRefText = open('/home/max/Projects/BiblionOCR/ViewController/Application/3-ConductOCR/FROMVS ChrReference.txt').read()
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
    
    def loadImage(self, MainWindow):
        
        imgfilename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.centralwidget, 'Select Image', '', 'Image Files (*.png *.jpg *.jpeg *.tif)')
        
        if imgfilename:
            self.ImageFileName.setText(os.path.basename(imgfilename))       
            self.imgfilename = imgfilename
            self.showImage(MainWindow,self.imgfilename)
            self.sortImgFiles(MainWindow)
            
    def showImage(self, MainWindow,imgfilename):
        self.imgfilename = imgfilename
        if self.imgfilename.endswith('.tif'):
            self.loadImageStackFromFile(self.imgfilename)
            self.showFrame(0)
            self.pixmap = QtGui.QPixmap.fromImage(self.qimage).scaled(self.ImageView.size(), 
                QtCore.Qt.KeepAspectRatio)
        else:
            self.pixmap = QtGui.QPixmap(imgfilename).scaled(self.ImageView.size(), 
                QtCore.Qt.KeepAspectRatio)

        if self.pixmap.isNull():
            return
        self.ImageView.setPixmap(self.pixmap)
        imgdirpath = os.path.normpath(os.path.dirname(self.imgfilename))
        self.imgfileList = []
        for i in os.listdir(imgdirpath):
            ipath = os.path.normpath(os.path.join(imgdirpath, i))
            if os.path.isfile(ipath) and i.lower().endswith(('.png', '.jpg', '.jpeg', '.tif')):
                self.imgfileList.append(ipath)
        self.sortImgFiles(MainWindow)

    def sortImgFiles(self, MainWindow):
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
        self.sorted_imgfilelist = sorted(self.imgfileList, key=lambda p: alphanum_key(os.path.basename(p)))
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
    
    def nextImage(self,MainWindow):      
        #self.sortImgFiles(MainWindow,iterdir="")
        # ensure that the file list has not been cleared due to missing files     
        if self.imgfileList:
            try:
                imgfilename = self.imgfilename
                nextimgfilename = next(self.imgdirIterator)
                self.ImageFileName.setText(os.path.basename(nextimgfilename))
                if nextimgfilename.endswith('.tif'):
                    self.loadImageStackFromFile(nextimgfilename)
                    self.showFrame(0)
                    pixmap = QtGui.QPixmap.fromImage(self.qimage).scaled(self.ImageView.size(), 
                        QtCore.Qt.KeepAspectRatio)
                else:
                    pixmap = QtGui.QPixmap(nextimgfilename).scaled(self.ImageView.size(), 
                        QtCore.Qt.KeepAspectRatio)
                    '''pixmap = QtGui.QPixmap(imgfilename).scaled(self.ImageView.size(), 
                            QtCore.Qt.KeepAspectRatio)'''
                '''if pixmap.isNull():
                    # the file is not a valid image, remove it from the list
                    # and try to load the next one
                    self.imgfileList.remove(nextimgfilename)
                    self.nextImage()
                else:'''
                self.showImage(MainWindow,nextimgfilename)
            except:
                # the iterator has finished, restart it
                self.imgdirIterator = iter(self.imgfileList)
                self.nextImage(MainWindow)
        else:
            # no file list found, load an image
            self.loadImage()
        
    def prevImage(self,MainWindow):      
        # ensure that the file list has not been cleared due to missing files     
        if self.imgfileList:
            try:
                imgfilename = self.imgfilename
                prevfilename = next(self.imgdirRevIterator)
                self.ImageFileName.setText(os.path.basename(prevfilename))
                if prevfilename.endswith('.tif'):
                    self.loadImageStackFromFile(prevfilename)
                    self.showFrame(0)
                    pixmap = QtGui.QPixmap.fromImage(self.qimage).scaled(self.ImageView.size(), 
                        QtCore.Qt.KeepAspectRatio)
                else:
                    pixmap = QtGui.QPixmap(prevfilename).scaled(self.ImageView.size(), 
                        QtCore.Qt.KeepAspectRatio)
                '''if pixmap.isNull():
                    # the file is not a valid image, remove it from the list
                    # and try to load the next one
                    self.imgfileList.remove(prevfilename)
                    self.prevImage()
                else:'''
                self.showImage(MainWindow,prevfilename)
            except:
                # the iterator has finished, restart it
                self.imgdirRevIterator = reversed(self.imgfileList)
                self.imgdirIterator = iter(self.imgfileList)
                self.prevImage(MainWindow)
        else:
            # no file list found, load an image
            self.loadImage()
  
    def loadText(self, MainWindow):
        self.textpath = QtWidgets.QFileDialog.getOpenFileName(
            self.centralwidget, 'Open text file', '',
            'Text files (*.txt)')[0]
        if self.textpath:
            self.textfile = QtCore.QFile(self.textpath)
            self.txtfilename = os.path.basename(self.textpath)
            self.showText(MainWindow,self.txtfilename)
            #print(self.textpath,"\t",self.textfile,"\t",self.txtfilename)

            #self.sortTextFiles(MainWindow)
            
    def showText(self, MainWindow, txtfilename):        
        #self.textfile = txtfilename
        if self.textfile.open(QtCore.QIODevice.ReadOnly):
            stream = QtCore.QTextStream(self.textfile)
            text = stream.readAll()
            info = QtCore.QFileInfo(self.textpath)
            if info.completeSuffix() == '.gt.txt':
                #self.editor_text.setHtml(text)
                self.TextFileEdit.insertPlainText(text)
            else:
                self.TextFileEdit.setPlainText(text)
            #textfile.close()
            self.TextFileName.setText(self.txtfilename)
            txtdirpath = os.path.dirname(self.textpath)
            self.txtfileList = []
        for t in os.listdir(txtdirpath):
            tpath = os.path.join(txtdirpath, t)
            if os.path.isfile(tpath) and t.endswith(('.gt.txt')):
                self.txtfileList.append(tpath)
        self.sortTextFiles(MainWindow)

    def sortTextFiles(self,Mainwindow):
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

    def nextText(self,MainWindow):
        # ensure that the file list has not been cleared due to missing files
        if self.txtfileList:
            try:
                txtfile = next(self.txtdirIterator)
                self.TextFileName.setText(os.path.basename(txtfile))
                #pixmap = QtGui.QPixmap(textfile).scaled(self.ImageView.size(), 
                    #QtCore.Qt.KeepAspectRatio)
                self.textfile = QtCore.QFile(txtfile)
                self.txtfilename = os.path.basename(txtfile)
                self.dirname = os.path.dirname(self.textpath)
                #self.textpath = os.path.join(self.dirname, "/",self.txtfilename)
                self.textpath = txtfile
                print(txtfile,"\t",self.textpath,"\t",self.textfile,"\t",self.txtfilename)
                #print(self.txtfilename)
                self.showText(MainWindow,self.txtfilename)
            except:
                # the iterator has finished, restart it
                self.txtdirIterator = iter(self.sorted_txtfilelist)
                self.txtdirRevIterator = reversed(self.sorted_txtfilelist)
                self.nextText(MainWindow)
        else:
            # no file list found, load an image
            self.loadText()
    
    def prevText(self,MainWindow):
        # ensure that the file list has not been cleared due to missing files
        if self.txtfileList:
            try:
                #txtfile = self.textfile
                txtfile = next(self.txtdirRevIterator)
                self.TextFileName.setText(os.path.basename(txtfile))
                #pixmap = QtGui.QPixmap(textfile).scaled(self.ImageView.size(), 
                    #QtCore.Qt.KeepAspectRatio)
                self.textfile = QtCore.QFile(txtfile)
                self.txtfilename = os.path.basename(txtfile)
                self.dirname = os.path.dirname(self.textpath)
                #self.textpath = os.path.join(self.dirname, "/",self.txtfilename)
                self.textpath = txtfile
                print(txtfile,"\t",self.textpath,"\t",self.textfile,"\t",self.txtfilename)
                #print(self.txtfilename)
                self.showText(MainWindow,self.txtfilename)
            except:
                # the iterator has finished, restart it
                self.txtdirRevIterator = reversed(sorted_txtfilelist)
                self.txtdirIterator = iter(sorted_txtfilelist)
                self.prevText(MainWindow)
        else:
            # no file list found, load an image
            self.loadText()
    
    def SaveImgFileDialog(self, MainWindow):
        dirpath = "/home/max/Projects/Python/Images/Greek/tif_greek_tif4groundtruth"
        imgname = os.path.basename(self.imgfilename)
        imgfilepath = os.path.join(dirpath,imgname)
        print(imgname,"\t",imgfilepath)
        #self.qimage.save(imgfilepath,"PNG")        
        image = self.pixmap
        image.save(QtWidgets.QFileDialog.getSaveFileName(self.centralwidget, 'Save Image As', dirpath,
                                            'Name (*.jpg *.jpeg *.png *.tiff *.tif)'))
        
        '''FontChange/path = QtWidgets.QFileDialog.getSaveFileName(
            self.centralwidget, 'Save Image As', '', 'Image Files (*.png *.jpg *.jpeg *.tif)')[0]
        with open(path, 'w') as file:
            #my_Img = self.qimage
            file.write(self.imgfilename)
        file.close()'''

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
        '''path = QtWidgets.QFileDialog.getOpenFileName(
            self.centralwidget, 'Open image file', '',
            'Images (*.tif *.png)')[0]
        
        if path:
            file = QtCore.QFile(path)
            if file.open(QtCore.QIODevice.ReadOnly):
                info = QtCore.QFileInfo(path)
                my_OCR_rawtext = pytesseract.image_to_string(path,lang="feg")
                #self.OCRDocument.insertPlainText(my_OCR_rawtext)
                self.OCRTextEdit.insertPlainText(my_OCR_rawtext)
                file.close()'''
        file = QtCore.QFile(self.imgfilename)
        if file.open(QtCore.QIODevice.ReadOnly):
            #info = QtCore.QFileInfo(path)
            my_OCR_rawtext = pytesseract.image_to_string(self.imgfilename,lang="feg")
            #self.OCRDocument.insertPlainText(my_OCR_rawtext)
            self.OCRTextEdit.insertPlainText(my_OCR_rawtext)
            file.close()

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
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
        
        self.OCRButton.setText(_translate("MainWindow", "OCR Image File"))      
        
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

