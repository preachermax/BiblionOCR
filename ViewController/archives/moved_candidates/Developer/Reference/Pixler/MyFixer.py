# -*- coding: utf-8 -*-

# Python imports
import sys
import os
import json
import io
import tiffcapture
import qimage2ndarray
from PIL import Image as pilimg

# PyQt5 imports
from PyQt5.QtWidgets import QRubberBand, QWidget, QHBoxLayout, QSizeGrip
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QPoint, QRect, QSize, Qt
from PyQt5 import QtCore as qtc
#from PyQt5 import QtPrintSupport
#from PyQt5 import QPrintPreviewDialog, QPrintDialog

# Custom imports
from MyPixerUI import Ui_MyPixerUI

class Main(qtw.QMainWindow):
# Application View
    def __init__(self,parent=None):
        qtw.QMainWindow.__init__(self,parent)

        self.imgpath = ""
        self.imgdir = ""
        self.changesSaved = True

        self.ui = Ui_MyFixerUI()
        self.ui.setupUi(self)
        self.initUI()

        self.rubberBand = ResizableRubberBand(self)
        self.currentQRect = self.rubberBand.geometry()
        
        self.origin = QPoint()
        self.scale = 1
        self.refimgdir=""
        self.imagedir=""
        self.refimgpath=""
        self.imagepath=""

        self.refimgsize = 1
        self.refimgpixmap = qtg.QPixmap()
        self.imagesize = 1
        self.imagepixmap = qtg.QPixmap()

# Session View

    def get_session_settings(self):
        # get session settings
        # Define json data        
        print("loading session")
        with open('/home/max/Projects/BiblicalOCR/Model/Data/json/PixerSession.json') as f:
            # returns JSON object as a dictionary
            data = json.load(f)
            
            # Set json key values
            bookabbr_key = r"self.bookabbr"
            word_key = r"self.word"
            chr_key = r"self.chr"
            font_key = r"self.font"
            fontsize_key = r"self.fontsize"
            source_book_markdown_key = r"self.sourcebookmarkdown"
            greek_book_markdown_key = r"self.greekbookmarkdown"
            latin_book_markdown_key = r"self.latinbookmarkdown"
            pixmap_key = r"self.pixmap"
            qimage_key = r"self.qimage"
            bmpsourcedir_key = r"self.bmpsourcedir"
            bmpgreekdir_key = r"self.bmpgreekdir"
            refimgpath_key = r"self.refimgpath"
            refimgdir_key = r"self.refimgdir"
            refimgtfileList_key = r"self.refimgtfileList"
            refimgzoom_key = r"self.refimgzoom"
            refimgzoomslidervalue_key = r"self.refimgzoomslidervalue"
            imagepath_key = r"self.imagepath"
            imagedir_key = r"self.imagedir"
            imagefileList_key = r"self.imagefileList"
            imagezoom_key = r"self.imagezoom"
            imagezoomslidervalue_key = r"self.imagezoomslidervalue"
            greekpagesrotated_key = r"self.greekpagesrotated"
            greekpagesdeskewed_key = r"self.greekpagesdeskewed"
            greekpagescropped_key = r"self.greekpagescropped"
            greekpagescleaned_key = r"self.greekpagescleaned"
            greekpagesbox_key = r"self.greekpagesbox"
            greeklinescropped_key = r"self.greeklinescropped"
            greeklinescleaned_key = r"self.greeklinescleaned"
            greeklinesbox_key = r"self.greeklinesbox"
            hebrewpagesrotated_key = r"self.hebrewpagesrotated"
            hebrewpagesdeskewed_key = r"self.hebrewpagesdeskewed"
            hebrewpagescropped_key = r"self.hebrewpagescroppe"
            hebrewpagescleaned_key = r"self.hebrewpagescleaned"
            hebrewpagesbox_key = r"self.hebrewpagesbox"
            hebrewlinescropped_key = r"self.hebrewlinescropped"
            hebrewlinescleaned_key = r"self.hebrewlinescleaned"
            hebrewlinesbox_key = r"self.hebrewlinesbox"
            hebrewpagesrotated_key = r"self.hebrewpagesrotated"
            hebrewpagesdeskewed_key = r"self.hebrewpagesdeskewed"
            hebrewpagescropped_key = r"self.hebrewpagescroppe"
            hebrewpagescleaned_key = r"self.hebrewpagescleaned"
            hebrewpagesbox_key = r"self.hebrewpagesbox"
            hebrewlinescropped_key = r"self.hebrewlinescropped"
            hebrewlinescleaned_key = r"self.hebrewlinescleaned"
            hebrewlinesbox_key = r"self.hebrewlinesbox"

            # Find the json key values using 'in' operator
            # Define session variables from json key values
            for Setting in data:
                print('Setting: ',Setting['Setting'],Setting['CurrentValue'])
                
                if Setting['Setting'] == bookabbr_key:  
                    self.bookabbr = Setting['CurrentValue']
                    #self.ui.bookComboBox.setCurrentText(self.bookabbr)            
                elif Setting['Setting'] == word_key:
                    self.word = Setting['CurrentValue'] 
                elif Setting['Setting'] == chr_key:
                    self.chr = Setting['CurrentValue']
                elif Setting['Setting'] == font_key:
                    self.font = Setting['CurrentValue']
                elif Setting['Setting'] == fontsize_key:
                    self.fontsize = Setting['CurrentValue']         
                elif Setting['Setting'] == source_book_markdown_key:  
                    self.sourcebookmarkdown = Setting['CurrentValue']
                elif Setting['Setting'] == greek_book_markdown_key:  
                    self.greekbookmarkdown = Setting['CurrentValue']
                elif Setting['Setting'] == latin_book_markdown_key:  
                    self.latinbookmarkdown = Setting['CurrentValue']
                elif Setting['Setting'] == pixmap_key:
                    self.pixmap = Setting['CurrentValue']
                elif Setting['Setting'] == qimage_key:
                    self.qimage = Setting['CurrentValue']
                elif Setting['Setting'] == bmpsourcedir_key:
                    self.bmpsourcedir = Setting['CurrentValue']
                elif Setting['Setting'] == bmpgreekdir_key:
                    self.bmpgreekdir = Setting['CurrentValue']
                elif Setting['Setting'] == refimgpath_key:
                    self.refimgpath = Setting['CurrentValue']
                elif Setting['Setting'] == refimgdir_key:
                    self.refimgdir = Setting['CurrentValue']
                elif Setting['Setting'] == refimgtfileList_key:
                    self.refimgtfileList = Setting['CurrentValue']
                elif Setting['Setting'] == refimgzoom_key:
                    self.refimgzoom = Setting['CurrentValue']
                elif Setting['Setting'] == refimgzoomslidervalue_key:
                    self.refimgzoomslidervalue = Setting['CurrentValue']
                elif Setting['Setting'] == imagepath_key:
                    self.imagepath = Setting['CurrentValue']
                elif Setting['Setting'] == imagedir_key:
                    self.imagedir = Setting['CurrentValue']
                elif Setting['Setting'] == imagefileList_key:
                    self.imagefileList = Setting['CurrentValue']
                elif Setting['Setting'] == imagezoom_key:
                    self.imagezoom = Setting['CurrentValue']
                elif Setting['Setting'] == imagezoomslidervalue_key:
                    self.imagezoomslidervalue = Setting['CurrentValue']
                elif Setting['Setting'] == greekpagesrotated_key:
                    self.greekpagesrotated = Setting['CurrentValue']
                elif Setting['Setting'] == greekpagesdeskewed_key:
                    self.greekpagesdeskewed = Setting['CurrentValue']
                elif Setting['Setting'] == greekpagescropped_key:
                    self.greekpagescropped = Setting['CurrentValue']
                elif Setting['Setting'] == greekpagescleaned_key:
                    self.greekpagescleaned = Setting['CurrentValue']
                elif Setting['Setting'] == greekpagesbox_key:
                    self.greekpagesbox = Setting['CurrentValue']
                elif Setting['Setting'] == greeklinescropped_key:
                    self.greeklinescropped = Setting['CurrentValue']
                elif Setting['Setting'] == greeklinescleaned_key:
                    self.greeklinescleaned = Setting['CurrentValue']
                elif Setting['Setting'] == greeklinesbox_key:
                    self.greeklinesbox = Setting['CurrentValue']
                elif Setting['Setting'] == latinpagesrotated_key:
                    self.latinpagesrotated = Setting['CurrentValue']
                elif Setting['Setting'] == latinpagesdeskewed_key:
                    self.latinpagesdeskewed = Setting['CurrentValue']
                elif Setting['Setting'] == latinpagescropped_key:
                    self.latinpagescropped = Setting['CurrentValue']
                elif Setting['Setting'] == latinpagescleaned_key:
                    self.latinpagescleaned = Setting['CurrentValue']
                elif Setting['Setting'] == latinpagesbox_key:
                    self.latinpagesbox = Setting['CurrentValue']
                elif Setting['Setting'] == latinlinescropped_key:
                    self.latinlinescropped = Setting['CurrentValue']
                elif Setting['Setting'] == latinlinescleaned_key:
                    self.latinlinescleaned = Setting['CurrentValue']
                elif Setting['Setting'] == latinlinesbox_key:
                    self.latinlinesbox = Setting['CurrentValue']
                elif Setting['Setting'] == hebrewpagesrotated_key:
                    self.hebrewpagesrotated = Setting['CurrentValue']
                elif Setting['Setting'] == hebrewpagesdeskewed_key:
                    self.hebrewpagesdeskewed = Setting['CurrentValue']
                elif Setting['Setting'] == hebrewpagescropped_key:
                    self.hebrewpagescropped = Setting['CurrentValue']
                elif Setting['Setting'] == hebrewpagescleaned_key:
                    self.hebrewpagescleaned = Setting['CurrentValue']
                elif Setting['Setting'] == hebrewpagesbox_key:
                    self.hebrewpagesbox = Setting['CurrentValue']
                elif Setting['Setting'] == hebrewlinescropped_key:
                    self.hebrewlinescropped = Setting['CurrentValue']
                elif Setting['Setting'] == hebrewlinescleaned_key:
                    self.hebrewlinescleaned = Setting['CurrentValue']
                elif Setting['Setting'] == hebrewlinesbox_key:
                    self.hebrewlinesbox = Setting['CurrentValue']
                
                print('New Setting: ',Setting['Setting'],Setting['CurrentValue'])
            f.close()
   
    def initToolbar(self):
        # Signals(Slots)
        self.ui.actionDenoise.triggered.connect()
        self.ui.actionErase.triggered.connect()
        self.ui.actionFlipRefImg.triggered.connect()
        self.ui.actionRotateRefImg_CW.triggered.connect()
        self.ui.actionRotateRefImg_CCW.triggered.connect()
        self.ui.actionCropRefImg.triggered.connect()
        self.ui.actionFillTransparent.triggered.connect()
        self.ui.actionDeskewRefImg.triggered.connect()
  
    def initMenubar(self):
        
        # File menu Signals(Slots)
        self.ui.actionOpen_Reference_Image.triggered.connect(self.loadImage)
        #self.ui.actionOpen_Image.triggered.connect(self.x)
        self.ui.actionSave_Image.triggered.connect(self.SaveImage)
        self.ui.actionSaveAsImage.triggered.connect(self.SaveAsImage)
        self.ui.actionOverwrite_Reference_Image.triggered.connect(self.OverwriteRefImage)
        self.ui.actionImport_Current_Image.triggered.connect(self.importfile)
        self.ui.actionExport_Image.triggered.connect()
        
        # Edit Menu Signals(Slots)

        self.ui.actionFillSelection.triggered.connect()
        self.ui.actionFillBackground.triggered.connect()
        self.ui.actionFillForeground.triggered.connect()

    def initUI(self):

        self.get_session_settings()        
        self.initMenubar()
        self.initToolbar()

        # Button Row Signals(Slots)
        
        # Ref Image
        
        self.ui.OpenRefImgbutton.clicked.connect(self.loadRefImg)
        self.ui.ImportRefImgFilebutton.clicked.connect(self.importRefImg)
        self.ui.OverwriteRefImgbutton.clicked.connect(self.OverwriteRefImg)
 
        self.ui.RefImgZoombutton.clicked.connect(self.get_RefImgzoom)
        self.ui.RefImgZoomComboBox.currentTextChanged.connect(self.on_RefImgzoom)
        self.ui.RefImgzoomslider.valueChanged.connect(self.on_RefImgzoomslider)
        self.ui.RefImgzoomslider.sliderReleased.connect(self.disable_RefImgzoomslider)
        self.ui.RefImgzoomslider.hide()
        
        self.ui.NextRefImgbutton.clicked.connect(self.nextRefImg)
        self.ui.PrevRefImgbutton.clicked.connect(self.prevRefImg)
        
        # Both
        '''
        self.ui.BothLoadButton.clicked.connect(self.bothLoad)
        self.ui.BothNextImageButton.clicked.connect(nextRefImg)
        self.ui.BothNextImageButton.clicked.connect(nextImage)        
        self.ui.BothPrevImageButton.clicked.connect(prevRefImg)
        self.ui.BothPrevImageButton.clicked.connect(prevImage)'''
        
        self.ui.reloadImagebutton.clicked.connect(self.reloadImg)
        self.ui.reloadRefImagebutton.clicked.connect(self.reloadRefImg)

        # Image
        self.ui.ImageLE.textChanged.connect(self.changed_RefImg)
        
        self.ui.PrevImagebutton.clicked.connect(self.prevImage)
        self.ui.NextImagebutton.clicked.connect(self.nextImage)
        
        self.ui.Imagezoomslider.valueChanged.connect(self.on_Imagezoomslider)
        self.ui.ImageZoomComboBox.currentTextChanged.connect(self.on_Imagezoom)
        self.ui.ImageZoombutton.clicked.connect(self.get_Imagezoom)
        self.ui.Imagezoomslider.sliderReleased.connect(self.disableImagezoomslider)
        
        self.ui.ExportImageFilebutton.clicked.connect(self.ExportImage)
        self.ui.SaveImagebutton.clicked.connect(self.SaveImage)
        self.ui.SaveAsImagebutton.clicked.connect(self.SaveAsImage)
        
        self.ui.RefImgzoomslider.hide()
        self.ui.Imagezoomslider.hide()

    def setStack(self, tiffCaptureHandle):
            """ Set the scene's current TIFF image stack to the input TiffCapture object.
            Raises a RuntimeError if the input tiffCaptureHandle has type other than TiffCapture.
            :type tiffCaptureHandle: TiffCapture
            """
            if type(tiffCaptureHandle) is not tiffcapture.TiffCapture:
                raise RuntimeError("MultiPageTIFFViewerQt.setImageStack: Argument must be a TiffCapture object.")
            self._tiffCaptureHandle = tiffCaptureHandle
            self.showFrame(0)

    def loadStackFromFile(self,fileName=''):
        """ Load an image stack from file.
        Without any arguments, loadStackFromFile() will popup a file dialog to choose the image file.
        With a fileName argument, loadStackFromFile(fileName) will attempt to load the specified file directly.
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

    def showRefImg(self,imgfilename):
        #self.imgfilename = self.imgpath
        file = qtc.QFile(imgfilename)
        filestr = os.path.basename(imgfilename)           
        filesplit = os.path.splitext(filestr)
        filename = filesplit[0]
        fileext = filesplit[1]
        
        if file.open(qtc.QIODevice.ReadOnly):
            info = qtc.QFileInfo(imgfilename)
        
            '''if self.imgpath.endswith('.tif'):
                self.loadStackFromFile(imgfilename)
                self.showFrame(0)
                self.refimgpixmap = qtg.QPixmap.fromImage(self.qimage).scaled(self.ui.Image.size(), qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation) 
            else:
                self.refimgpixmap = qtg.QPixmap(imgfilename).scaled(self.ui.Image.size(), 
                    qtc.Qt.KeepAspectRatio)'''       

            if fileext == '.tif':
                self.loadStackFromFile(imgfilename)
                self.showFrame(0)
                #self.refimgpixmap = qtg.QPixmap.fromImage(self.qimage)                
                self.refimgpixmap = qtg.QPixmap.fromImage(self.qimage).scaled(self.ui.Image.size(), qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)  
            else:
                self.refimgpixmap = qtg.QPixmap(self.imgpath)
        
        file.close()
        
        if self.refimgpixmap.isNull():
            return
        
        self.on_RefImgzoom()
        
        self.refimgdir = os.path.dirname(imgfilename)
        self.ui.RefImgLe.setText(filestr)
        jsonfile = '/home/max/Projects/BiblicalOCR/Model/Data/json/PixerSession.json'
                
        with open(jsonfile, 'r') as f:
            data = json.load(f)
            refimgpath_key = r"self.refimgpath"
            refimgdir_key = r"self.refimgdir"
            for Setting in data:
                if Setting['Setting'] == refimgpath_key:
                    Setting['CurrentValue'] = self.refimgpath
                    print(Setting['CurrentValue'])
                elif Setting['Setting'] == refimgdir_key:  
                    Setting['CurrentValue'] = self.refimgdir
                    print(Setting['CurrentValue'])
        f.close()

        os.remove(jsonfile)
        with open(jsonfile, 'w') as f:
            json.dump(data, f, indent=4)
        f.close()
        
        self.refimgfileList = []
        for i in os.listdir(self.refimgdir):
            ipath = os.path.join(self.refimgdir, i)
            if os.path.isfile(ipath) and i.endswith(('.png', '.jpg', '.jpeg', '.tif')):
                self.refimgfileList.append(ipath)        
        '''self.imgfileList = []
        for i in os.listdir(self.imgdir):
            ipath = os.path.join(self.imgdir, i)
            if os.path.isfile(ipath) and i.endswith(('.png', '.jpg', '.jpeg', '.tif')):
                self.imgfileList.append(ipath)'''

        self.sortRefImgFiles()

    def showImage(self,imgfilename):
        #self.imgfilename = self.imgpath
        file = qtc.QFile(imgfilename)
        filestr = os.path.basename(imgfilename)           
        filesplit = os.path.splitext(filestr)
        filename = filesplit[0]
        fileext = filesplit[1]
        
        if file.open(qtc.QIODevice.ReadOnly):
            info = qtc.QFileInfo(imgfilename)
        
            '''if self.imgpath.endswith('.tif'):
                self.loadStackFromFile(imgfilename)
                self.showFrame(0)
                self.imgpixmap = qtg.QPixmap.fromImage(self.qimage).scaled(self.ui.Image.size(), qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation) 
            else:
                self.imgpixmap = qtg.QPixmap(imgfilename).scaled(self.ui.Image.size(), 
                    qtc.Qt.KeepAspectRatio)'''       

            if fileext == '.tif':
                self.loadStackFromFile(imgfilename)
                self.showFrame(0)
                #self.imagepixmap = qtg.QPixmap.fromImage(self.qimage)                
                self.imagepixmap = qtg.QPixmap.fromImage(self.qimage).scaled(self.ui.Image.size(), qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)  
            else:
                self.imagepixmap = qtg.QPixmap(self.imagepath)
        
        file.close()
        
        if self.imagepixmap.isNull():
            return
        
        self.on_Imagezoom()
        #self.ui.Image.setPixmap(self.refimgpixmap)
        
        self.imagedir = os.path.dirname(imgfilename)
        self.ui.ImageLE.setText(filestr)
        jsonfile = '/home/max/Projects/BiblicalOCR/Model/Data/json/PixerSession.json'
                
        with open(jsonfile, 'r') as f:
            data = json.load(f)
            imagepath_key = r"self.imagepath"
            imagedir_key = r"self.imagedir"
            for Setting in data:
                if Setting['Setting'] == imagepath_key:
                    Setting['CurrentValue'] = self.imagepath
                    print(Setting['CurrentValue'])
                elif Setting['Setting'] == imagedir_key:  
                    Setting['CurrentValue'] = self.imagedir
                    print(Setting['CurrentValue'])
        f.close()

        os.remove(jsonfile)
        with open(jsonfile, 'w') as f:
            json.dump(data, f, indent=4)
        f.close()
        
        self.imagefileList = []
        for i in os.listdir(self.imagedir):
            ipath = os.path.join(self.imagedir, i)
            if os.path.isfile(ipath) and i.endswith(('.png', '.jpg', '.jpeg', '.tif')):
                self.imagefileList.append(ipath)        
        '''self.imgfileList = []
        for i in os.listdir(self.imgdir):
            ipath = os.path.join(self.imgdir, i)
            if os.path.isfile(ipath) and i.endswith(('.png', '.jpg', '.jpeg', '.tif')):
                self.imgfileList.append(ipath)'''

        self.sortImgFiles()

    def closeEvent(self,event):

        if self.RefImgchangesSaved:

            event.accept()

        else:
        
            popup = qtw.QMessageBox(self)

            popup.setIcon(qtw.QMessageBox.Warning)
            
            popup.setText("The document has been modified")
            
            popup.setInformativeText("Do you want to save your changes?")
            
            popup.setStandardButtons(qtw.QMessageBox.Save   |
                                      qtw.QMessageBox.Cancel |
                                      qtw.QMessageBox.Discard)
            
            popup.setDefaultButton(qtw.QMessageBox.Save)

            answer = popup.exec_()

            if answer == qtw.QMessageBox.Save:
                self.save()

            elif answer == qtw.QMessageBox.Discard:
                event.accept()

            else:
                event.ignore()

# Application Controllers
    # Mouse Controllers
    def mousePressEvent(self, event):
    
        if event.button() == Qt.LeftButton:
        
            self.origin = QPoint(event.pos())
            self.rubberBand.setGeometry(QRect(self.origin, QSize()))
            self.rubberBand.show()
    
    def mouseMoveEvent(self, event):
    
        if not self.origin.isNull():
            self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())

    def mouseReleaseEvent(self, event):
    
        if event.button() == Qt.LeftButton:
            box = self.rubberBand.shape()
            geo = self.rubberBand.geometry()
            h = self.rubberBand.height()
            w = self.rubberBand.width()
            x = self.rubberBand.x()
            y = self.rubberBand.y()
            print(box)
            print(geo)
            print(x)
            print(w)
            print(x+w)
            print(y)
            print(h)
            print(y+h)
            print(x,":",x+w,",",y,":",y+h)
            #self.cropregion(x,y,w,h)'''
            self.currentQRect = self.rubberBand.geometry()
            self.imgpixmap = self.ui.Image.pixmap().copy(self.currentQRect)
            
            #self.ui.Cropped.setPixmap(self.imgpixmap)
            
            #croppedimg = self.ui.Image[x:x+w,y:y+h]
            #self.rubberBand.hide()

    # Reference Image Controllers
    def importRefImage(self):
        print("Importing current reference image from MainWindow")
        if self.refimgpath:
            print(self.refimgpath)
            self.filename = self.refimgpath

            with open(self.filename) as file:
                self.ui.REFImgLE.setText(file.read())
            
            #self.on_font_update()
            #if self.font:
                #self.ui.textEdit.setCurrentFont(qtg.QFont(self.font))

    def loadRefImg(self):     
        self.refimgpath = qtw.QFileDialog.getOpenFileName(self.ui.centralwidget, 'Open image file',self.refimgdir,'Images (*.png *.xpm *.jpg *.bmp *.gif *.tif)')[0]
        if self.refimgpath:
            self.ui.ImageLe.setText(os.path.basename(self.refimgpath))
            self.showImage(self.refimgpath)
            self.sortImgFiles()       
        '''imgfilename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.ui.centralwidget, 'Select Image', '', 'Image Files (*.png *.jpg *.jpeg *.bmp *.tif)')
        
        if imgfilename:
            self.ui.ImageLe.setText(os.path.basename(imgfilename))       
            self.imgfilename = imgfilename'''

    def sortRefImgFiles(self):
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
        self.sorted_refimgfilelist = sorted(self.refimgfileList, key=alphanum_key)
        #self.fileList.sort()
        #print(self.sorted_refimgfilelist)
        self.refimgdirIterator = iter(self.sorted_refimgfilelist)
        self.nextimage = next(self.refimgdirIterator)
        self.refimgdirRevIterator = reversed(self.sorted_refimgfilelist)
        self.previmage = next(self.refimgdirRevIterator)
        while True:
            # cycle through the iterator until the current file is found
            if next(self.refimgdirIterator) == self.refimgpath:
                break
        while True:
            # cycle through the reverse iterator until the current file is found
            if next(self.refimgdirRevIterator) == self.refimgpath:
                break
    
    def nextRefImg(self):      
        # ensure that the file list has not been cleared due to missing files     
        filestr = os.path.basename(self.refimgpath)           
        filesplit = os.path.splitext(filestr)
        filename = filesplit[0]
        fileext = filesplit[1]
        
        if self.refimgfileList:
            try:
                refimgfilename = self.refimgpath
                nextrefimgfilename = next(self.refimgdirIterator)
                self.ui.ImageLe.setText(os.path.basename(nextrefimgfilename))
                if fileext == '.tif':
                    print(nextrefimgfilename)
                    self.loadStackFromFile(nextrefimgfilename)
                    self.showFrame(0)
                    pixmap = qtg.QPixmap.fromImage(self.qimage).scaled(self.ui.Image.size(), 
                        qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)
                else:
                    pixmap = qtg.QPixmap(nextrefimgfilename).scaled(self.ui.Image.size(), 
                        qtc.Qt.KeepAspectRatio)

            except:
                # the iterator has finished, restart it
                self.refimgdirIterator = iter(self.refimgfileList)
                #self.imgdirRevIterator = reversed(self.imgfileList)
                #print(self.imgfileList)
                self.prevImage()
            
            self.refimgpath = nextrefimgfilename
            self.showImage(nextrefimgfilename)            

        else:
            # no file list found, load an image
            # self.OpenImageFileDialog()
            self.loadImage()

    def prevRefImg(self):
        # ensure that the file list has not been cleared due to missing files     
        filestr = os.path.basename(self.refimgpath)           
        filesplit = os.path.splitext(filestr)
        filename = filesplit[0]
        fileext = filesplit[1]
        
        if self.refimgfileList:
            try:
                refimgfilename = self.refimgpath
                prevrefimgfilename = next(self.refimgdirRevIterator)
                self.ui.ImageLe.setText(os.path.basename(prevrefimgfilename))
                if fileext == '.tif':
                    print(prevrefimgfilename)
                    self.loadStackFromFile(prevrefimgfilename)
                    self.showFrame(0)
                    pixmap = qtg.QPixmap.fromImage(self.qimage).scaled(self.ui.Image.size(), 
                        qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)
                else:
                    pixmap = qtg.QPixmap(prevrefimgfilename).scaled(self.ui.Image.size(), 
                        qtc.Qt.KeepAspectRatio)

            except:
                # the iterator has finished, restart it
                self.refimgdirRevIterator = reversed(self.refimgfileList)
                #self.refimgdirIterator = iter(self.imgfileList)
                #self.nextImage()
            
            self.refimgpath = prevrefimgfilename
            self.showImage(prevrefimgfilename)
            

        else:
            # no file list found, load an image
            # self.OpenImageFileDialog()
            self.loadRefImg()

    def reloadRefImg(self):
        if self.refimgpath:
            self.ui.RefImgLE.setText(os.path.basename(self.refimgpath))
            self.showRefImg(self.refimgpath)
            self.sortRefImgFiles()  

    def OverwriteRefImg(self):
    
        #defaultdir = r"/home/max/Projects/Python/EstablishTruth/Greek txt pages/greek_book_41_Mark/"
        defaultpath = self.refimgpath
        filename = os.path.basename(defaultpath)
        
        if defaultpath:
            path = defaultpath    
        else:
            path = qtw.QFileDialog.getSaveFileName(
                self.centralwidget, 'Overwrite reference image file', '',
                'Tiff files (*.tif)')[0]
        
        self.imagepixmap.save(path)
        filename = os.path.basename(path)
        self.ui.RefImgLE.setText(filename)
        self.SaveImage()
        self.reloadRefImg()
        file.close()

    def show_RefImgzoomslider(self):
        self.ui.RefImgzoomslider.show()

    def get_RefImgzoom(self):
        self.ui.RefImgzoomslider.setEnabled(True)
        self.ui.RefImgzoomslider.show()
        RefImgzoomValue = self.ui.RefImgzoomslider.value()
        
    def disable_RefImgzoomslider(self):
        self.ui.RefImgzoomslider.hide()
        self.ui.RefImgzoomslider.setEnabled(False)

    def move_RefImgzoomslider(self):
        self.ui.RefImgzoomslider.setEnabled(True)
        self.ui.RefImgzoomslider.setValue(int(self.ui.RefImgZoomComboBox.currentText()[0]))

    def on_RefImgzoomslider(self):
        #if self.ui.Zoomslider.isEnabled():
        RefImgzoomValue = self.ui.RefImgzoomslider.value()
        self.ui.RefImgZoomComboBox.setCurrentText(str(RefImgzoomValue) + " %")
        print(RefImgzoomValue)
        self.scale = RefImgzoomValue/100
        print(self.scale)
    
    def on_RefImgzoom(self):
        seltext = self.ui.RefImgZoomComboBox.currentText()
        if self.ui.RefImgzoomslider.isEnabled():
            self.on_RefImgzoomslider()
        #elif seltext != "Best_Fit":
            #print("Best fit not selected")
        selnumtext = seltext.split(" ")
        print(selnumtext[0])
        self.scale = float(selnumtext[0])/100
        print(self.scale)
        
        self.resize_RefImg()

    def resize_RefImg(self):

        self.refimgsize = self.refimgpixmap.size()       
        self.origheight = self.refimgpixmap.height
        self.origwidth = self.refimgpixmap.width
        scaled_pixmap = self.refimgpixmap.scaled(self.scale * self.refimgsize, qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)
        self.ui.RefImg.setPixmap(scaled_pixmap)
 
    def changed_RefImg(self):
        self.RefImgchangesSaved = False

    # Image Controllers

    def sortImageFiles(self):
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
        self.sorted_imagefilelist = sorted(self.imagefileList, key=alphanum_key)
        #self.fileList.sort()
        #print(self.sorted_imagefilelist)
        self.imagedirIterator = iter(self.sorted_imagefilelist)
        self.nextimage = next(self.imagedirIterator)
        self.imagedirRevIterator = reversed(self.sorted_imagefilelist)
        self.previmage = next(self.imagedirRevIterator)
        while True:
            # cycle through the iterator until the current file is found
            if next(self.imagedirIterator) == self.imagepath:
                break
        while True:
            # cycle through the reverse iterator until the current file is found
            if next(self.imagedirRevIterator) == self.imagepath:
                break

    def get_Imagezoom(self):
        self.ui.Imagezoomslider.setEnabled(True)
        self.ui.Imagezoomslider.show()
        zoomValue = self.ui.Imagezoomslider.value()
        
    def disable_Imagezoomslider(self):
        self.ui.Imagezoomslider.hide()
        self.ui.Imagezoomslider.setEnabled(False)

    def move_Imagezoomslider(self):
        self.ui.Imagezoomslider.setEnabled(True)
        self.ui.Imagezoomslider.setValue(int(self.ui.ImageZoomComboBox.currentText()[0]))

    def show_Imagezoomcombo(self):
        self.ui.ImageZoomComboBox.show()

    def on_Imagezoomslider(self):
        #if self.ui.Zoomslider.isEnabled():
        zoomValue = self.ui.Imagezoomslider.value()
        self.ui.ImageZoomComboBox.setCurrentText(str(zoomValue) + " %")
        print(zoomValue)
        self.scale = zoomValue/100
        print(self.scale)
    
    def on_Imagezoom(self):
        seltext = self.ui.ImageZoomComboBox.currentText()
        if self.ui.Imagezoomslider.isEnabled():
            self.on_zoomslider()
        #elif seltext != "Best_Fit":
            #print("Best fit not selected")
        selnumtext = seltext.split(" ")
        print(selnumtext[0])
        self.scale = float(selnumtext[0])/100
        print(self.scale)
        
        self.resize_image()

    def nextImage(self):      
        # ensure that the file list has not been cleared due to missing files     
        filestr = os.path.basename(self.imagepath)           
        filesplit = os.path.splitext(filestr)
        filename = filesplit[0]
        fileext = filesplit[1]
        
        if self.imagefileList:
            try:
                imagefilename = self.imagepath
                nextimagefilename = next(self.imagedirIterator)
                self.ui.ImageLe.setText(os.path.basename(nextimagefilename))
                if fileext == '.tif':
                    print(nextimagefilename)
                    self.loadStackFromFile(nextimagefilename)
                    self.showFrame(0)
                    pixmap = qtg.QPixmap.fromImage(self.qimage).scaled(self.ui.Image.size(), 
                        qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)
                else:
                    pixmap = qtg.QPixmap(nextimagefilename).scaled(self.ui.Image.size(), 
                        qtc.Qt.KeepAspectRatio)

            except:
                # the iterator has finished, restart it
                self.imagedirIterator = iter(self.imagefileList)
                #self.imgdirRevIterator = reversed(self.imgfileList)
                #print(self.imgfileList)
                self.prevImage()
            
            self.imagepath = nextimagefilename
            self.showImage(nextimagefilename)            

        else:
            # no file list found, load an image
            # self.OpenImageFileDialog()
            self.loadImage()

    def prevImage(self):
        # ensure that the file list has not been cleared due to missing files     
        filestr = os.path.basename(self.imagepath)           
        filesplit = os.path.splitext(filestr)
        filename = filesplit[0]
        fileext = filesplit[1]
        
        if self.imagefileList:
            try:
                imagefilename = self.imagepath
                previmagefilename = next(self.imagedirRevIterator)
                self.ui.ImageLe.setText(os.path.basename(previmagefilename))
                if fileext == '.tif':
                    print(previmagefilename)
                    self.loadStackFromFile(previmagefilename)
                    self.showFrame(0)
                    pixmap = qtg.QPixmap.fromImage(self.qimage).scaled(self.ui.Image.size(), 
                        qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)
                else:
                    pixmap = qtg.QPixmap(previmagefilename).scaled(self.ui.Image.size(), 
                        qtc.Qt.KeepAspectRatio)

            except:
                # the iterator has finished, restart it
                self.imagedirRevIterator = reversed(self.imagefileList)
                #self.imagedirIterator = iter(self.imagefileList)
                #self.nextImage()
            
            self.imagepath = previmagefilename
            self.showImage(previmagefilename)
            

        else:
            # no file list found, load an image
            # self.OpenImageFileDialog()
            self.loadImage()

    def reloadImage(self):
        if self.imagepath:
            self.ui.ImageLe.setText(os.path.basename(self.imagepath))
            self.showImage(self.imagepath)
            self.sortImgFiles()  

    def resize_Image(self):
        self.imagesize = self.imagepixmap.size()       
        self.origheight = self.imagepixmap.height
        self.origwidth = self.imagepixmap.width
        scaled_pixmap = self.imagepixmap.scaled(self.scale * self.imagesize, qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)
        self.ui.RefImg.setPixmap(scaled_pixmap)

    def ExportImage(self):
        pass

    def SaveImageAs(self):
        path = qtw.QFileDialog.getSaveFileName(
            self.ui.centralwidget, 'Save cropped tiff file', '',
            'Tiff files (*.tif)')[0]
        #my_Image = self.ui.Cropped.pixmap().toImage()
        my_Image = self.imagepixmap.toImage()
        my_Image.save(path)
        # Write accepted ROI to correct folder/file
        buffer = qtc.QBuffer()
        buffer.open(qtc.QBuffer.ReadWrite)
        my_Image.save(buffer, "PNG")
        PILimage = pilimg.open(io.BytesIO(buffer.data()))
        outfile = path
        print("Generating: " + outfile)
        PILimage.save(outfile, "TIFF", dpi=(300,300), compression = "tiff_lzw")
        #filename = os.path.basename(path)
        self.ui.ImageLE.setText(path)
        #file.close()
        
    def SaveImage(self):
        
        defaultpath = self.ui.ImageLE.displayText()
        filename = os.path.basename(defaultpath)
        
        if defaultpath:
            path = defaultpath
            
        else:
            path = qtw.QFileDialog.getSaveFileName(
                self.centralwidget, 'Save modified tif file', '',
                'Tif files (*.tif)')[0]
        
        #self.ui.Cropped.self.pixmap.save(path)
        self.imagepixmap.save(path)
        filename = os.path.basename(path)
        self.ui.ImageLe.setText(filename)
        file.close()

    def changed_Image(self):
        self.changesSaved = False
  
class ResizableRubberBand(QWidget):
    """Wrapper to make QRubberBand mouse-resizable using QSizeGrip

    Source: http://stackoverflow.com/a/19067132/435253
    """
    def __init__(self, parent=None):
        super(ResizableRubberBand, self).__init__(parent)

        self.setWindowFlags(Qt.SubWindow)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.grip1 = QSizeGrip(self)
        self.grip2 = QSizeGrip(self)
        self.layout.addWidget(self.grip1, 0, Qt.AlignLeft | Qt.AlignTop)
        self.layout.addWidget(self.grip2, 0, Qt.AlignRight | Qt.AlignBottom)

        self.rubberband = QRubberBand(QRubberBand.Rectangle, self)
        self.rubberband.move(0, 0)
        self.rubberband.show()
        self.show()

    def resizeEvent(self, event):
        self.rubberband.resize(self.size())

def main():
    app = qtw.QApplication(sys.argv)

    main = Main()
    main.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()