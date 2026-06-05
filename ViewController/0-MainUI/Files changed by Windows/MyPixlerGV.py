# -*- coding: utf-8 -*-

# Python imports
import sys
import os
import re
import json
import io
import tiffcapture
import qimage2ndarray
from queue import Queue
from PIL import Image as pilimg
from PIL import ImageQt as pilqimg
import shutil
import cv2
import numpy as np
from scipy import ndimage
import math
from copy import deepcopy

# PyQt5 imports
from PyQt5.QtWidgets import QRubberBand, QWidget, QHBoxLayout, QSizeGrip
from PyQt5 import QtWidgets as qtw
from PyQt5.QtGui import QPainter, QBrush, QPen
from PyQt5 import QtGui as qtg
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QPoint, QRect, QSize, Qt, QUrl
from PyQt5 import QtCore as qtc
#from PyQt5.QtWebEngineWidgets import QWebEngineSettings, QWebEngineView
#from PyQt5 import QtPrintSupport
#from PyQt5 import QPrintPreviewDialog, QPrintDialog

# Custom imports
from MySlidersUI import Ui_SliderDialog
from PreProcess import PreProcess as pp
#from MyScanner import Ui_Scanner
from MyPixlerGVUI import Ui_PixlerGV

# Dialog Imports
from Dialogs.ExtractDialog import Ui_ExtractDialog
from Dialogs.pdf4tifDialog import Ui_pdf4tifDialog
from Dialogs.pdf2tifDialog import Ui_pdf2tifDialog
from Dialogs.tif2monoDialog import Ui_tif2monoDialog
from Dialogs.pdf2tifDialog import Ui_pdf2tifDialog
from Dialogs.mono2pngDialog import Ui_mono2pngDialog
from Dialogs.deskew_monoDialog import Ui_deskew_monoDialog
from Dialogs.crop_languagesDialog import Ui_crop_languagesDialog
from Dialogs.greekmono2pngDialog import Ui_greekmono2pngDialog
from Dialogs.deskew_greekmonoDialog import Ui_deskew_greekmonoDialog
from Dialogs.greekresizepngDialog import Ui_greekresizepngDialog
from Dialogs.latinmono2pngDialog import Ui_latinmono2pngDialog
from Dialogs.deskew_latinmonoDialog import Ui_deskew_latinmonoDialog
from Dialogs.latinresizepngDialog import Ui_latinresizepngDialog

# The new Stream Object which replaces the default stream associated with sys.stdout
# This object just puts data in a queue!
class WriteStream(object):
    def __init__(self,queue):
        self.queue = queue

    def write(self, text):
        self.queue.put(text)

    def flush(self):
        """
        Stream flush implementation
        """
        pass
    
# A QObject (to be run in a QThread) which sits waiting for data to come through a Queue.Queue().
# It blocks until data is available, and once it has got something from the queue, it sends
# it to the "MainThread" by emitting a Qt Signal 
class ThreadConsoleTextQueueReceiver(qtc.QObject):
    
    queue_element_received_signal = qtc.pyqtSignal(str)

    def __init__(self, q: Queue, *args, **kwargs):
        qtc.QObject.__init__(self, *args, **kwargs)
        self.queue = q

    @qtc.pyqtSlot()
    def run(self):
        self.queue_element_received_signal.emit('---> Console text queue reception Started <---\n')
        while True:
            text = self.queue.get()
            self.queue_element_received_signal.emit(text)

    @qtc.pyqtSlot()
    def finished(self):
        self.queue_element_received_signal.emit('---> Console text queue reception Stopped <---\n')


class PixlerMain(qtw.QMainWindow):
# Application View
    def __init__(self,parent=None):
        qtw.QMainWindow.__init__(self,parent)

        self.imgpath = ""
        self.imgdir = ""
        self.RefImgchangesSaved = True

        self.ui = Ui_PixlerGV()
        self.ui.setupUi(self)
        self.initUI()
        self.refscene = qtw.QGraphicsScene()
        self.ui.RefImg.setScene(self.refscene)

        # extended slots code
       
        self.ui.actionExtract_pdf.triggered.connect(self.actionextract_pdf)      
        self.ui.actionpdf_For_tiff.triggered.connect(self.actionpdf_for_tiff)
        self.ui.actionpdf_To_tiff.triggered.connect(self.actionpdf_to_tiff)
        self.ui.actiontiff_indexed.triggered.connect(self.actiontiff_to_mono)
        #self.ui.actiondeskew_mono.triggered.connect(self.actiondeskew_mono)
        self.ui.actionpng_indexed.triggered.connect(self.actionmono_to_png)
        self.ui.actionAuto_Crop_Languages.triggered.connect(self.actionCrop_Languages)
        
        self.ui.actionManually_Crop_Language_Pages.triggered.connect(self.crop)
        
        self.ui.actionEdit_Image_tb.triggered.connect(self.actionGimpEdit) 
        self.ui.actionConvert_Greek_tiff_To_png.triggered.connect(self.actionConvert_Greek_tiff_To_png)
        self.ui.actionDeskew_Greek_tiff.triggered.connect(self.actionDeskew_Greek_tiff)
        self.ui.actionResize_Greek_png_pages.triggered.connect(self.actionResize_Greek_png)
        self.ui.actionConvert_Latin_tiff_To_png.triggered.connect(self.actionConvert_Latin_tiff_To_png)
        self.ui.actionDeskew_Latin_tiff.triggered.connect(self.actionDeskew_Latin_tiff)
        self.ui.actionResize_Latin_png_pages.triggered.connect(self.actionResize_Latin_png)

        
        #self.refimg_xoffset = self.ui.RefImg.x()
        #self.refimg_yoffset = self.ui.RefImg.y()
        
        #self.rubberBand = ResizableRubberBand(self)
        
        #self.origin = QPoint(int(self.refimg_xoffset),int(self.refimg_yoffset))
        self.origin = QPoint()
        self.refimgscale = 1
        self.imagescale = 1
        self.refimgdir=""
        self.imagedir=""
        self.refimgpath=""
        self.imagepath=""

        self.refimgsize = 1
        self.refimgpixmap = qtg.QPixmap()
        self.refimgqimage = qtg.QImage()
        self.imagesize = 1
        self.imagepixmap = qtg.QPixmap()
        self.imageqimage = qtg.QImage()
        #self.currentQRect = self.rubberBand.geometry()
    
    @qtc.pyqtSlot(str)
    def append_text(self,text):
        #self.ui.OutputText.moveCursor(QTextCursor.End)
        #self.ui.OutputText.insertPlainText(text)
        self.ui.OutputText.append(text)    

#custom method to write anything printed out to console/terminal to my QTextEdit widget via append function.
    def output_terminal_written(self, text):
        self.ui.OutputText.append(text)
  
# Session View

    def get_session_settings(self):
        # get session settings
        # Define json data
        print("importing Scanner session settings: imgpath and imgdir")
        with open('/home/max/Projects/BiblionOCR/Model/Project/Data/json/ScannerSession.json') as f:
            # returns JSON object as a dictionary
            data = json.load(f)
            
            imgpath_key = r"self.imgpath"
            imgdir_key = r"self.imgdir"
            # Find the json key values using 'in' operator
            # Define session variables from json key values
            for Setting in data:
                print('Setting: ',Setting['Setting'],Setting['CurrentValue'])
                if Setting['Setting'] == imgpath_key:
                    self.imgpath = Setting['CurrentValue']
                elif Setting['Setting'] == imgdir_key:  
                    self.imgdir = Setting['CurrentValue']

            print('New Setting: ',Setting['Setting'],Setting['CurrentValue'])
            f.close()

        print("loading session")
        with open('/home/max/Projects/BiblionOCR/Model/Project/Data/json/PixlerSession.json') as f:
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
            refimg_xoffset_key = r"self.refimg_xoffset"
            refimg_yoffset_key = r"self.refimg_yoffset"
            refimgtfileList_key = r"self.refimgtfileList"
            refimgzoom_key = r"self.refimgzoom"
            refimgzoomslidervalue_key = r"self.refimgzoomslidervalue"
            imagepath_key = r"self.imagepath"
            imagedir_key = r"self.imagedir"
            image_xoffset_key = r"self.image_xoffset"
            image_yoffset_key = r"self.image_yoffset"
            imagefileList_key = r"self.imagefileList"
            imagezoom_key = r"self.imagezoom"
            imagezoomslidervalue_key = r"self.imagezoomslidervalue"
            pixerrefimgpath_key = r"self.pixerrefimgpath"
            pixerrefimgpixmap_key = r"self.pixerrefimgpixmap"
            pixerrefimgqimage_key = r"self.pixerrefimgqimage"
            pixerrefimgdir_key = r"self.pixerrefimgdir"
            pixerpagesboxfileList_key = r"self.pixerpagesboxfileList"
            pixerpagesboxpixmap_key = r"self.pixerpagesboxpixmap"
            pixerpagesboxqimage_key = r"self.pixerpagesboxqimage"
            pixerpagesboxpath_key = r"self.pixerpagesboxpath"
            pixerpagesboxdir_key = r"self.pixerpagesboxdir"
            pixerpagescropfileList_key = r"self.pixerpagescropfileList"
            pixerpagescroppixmap_key = r"self.pixerpagescroppixmap"
            pixerpagescropqimage_key = r"self.pixerpagescropqimage"
            pixerpagescroppath_key = r"self.pixerpagescroppath"
            pixerpagescropdir_key = r"self.pixerpagescropdir"
            pixerpagesdeskewfileList_key = r"self.pixerpagesdeskewfileList"
            pixerpagesdeskewpixmap_key = r"self.pixerpagesdeskewpixmap"
            pixerpagesdeskewqimage_key = r"self.pixerpagesdeskewqimage"
            pixerpagesdeskewpath_key = r"self.pixerpagesdeskewpath"
            pixerpagesdeskewdir_key = r"self.pixerpagesdeskewdir"
            pixerpagesdenoisefileList_key = r"self.pixerpagesdenoisefileList"
            pixerpagesdenoisepixmap_key = r"self.pixerpagesdenoisepixmap"
            pixerpagesdenoiseqimage_key = r"self.pixerpagesdenoiseqimage"
            pixerpagesdenoisepath_key = r"self.pixerpagesdenoisepath"
            pixerpagesdenoisedir_key = r"self.pixerpagesdenoisedir"
            pixerpagesrotatefileList_key = r"self.pixerpagesrotatefileList"
            pixerpagesrotatepixmap_key = r"self.pixerpagesrotatepixmap"
            pixerpagesrotateqimage_key = r"self.pixerpagesrotateqimage"
            pixerpagesrotatepath_key = r"self.pixerpagesrotatepath"
            pixerpagesrotatedir_key = r"self.pixerpagesrotatedir"
            pixerpagescleanfileList_key = r"self.pixerpagescleanfileList"
            pixerpagescleanpixmap_key = r"self.pixerpagescleanpixmap"
            pixerpagescleanqimage_key = r"self.pixerpagescleanqimage"
            pixerpagescleanpath_key = r"self.pixerpagescleanpath"
            pixerpagescleandir_key = r"self.pixerpagescleandir"
            pixerlinesboxfileList_key = r"self.pixerlinesboxfileList"
            pixerlinesboxpixmap_key = r"self.pixerlinesboxpixmap"
            pixerlinesboxqimage_key = r"self.pixerlinesboxqimage"
            pixerlinesboxpath_key = r"self.pixerlinesboxpath"
            pixerlinesboxdir_key = r"self.pixerlinesboxdir"
            pixerlinescropfileList_key = r"self.pixerlinescropfileList"
            pixerlinescroppixmap_key = r"self.pixerlinescroppixmap"
            pixerlinescropqimage_key = r"self.pixerlinescropqimage"
            pixerlinescroppath_key = r"self.pixerlinescroppath"
            pixerlinescropdir_key = r"self.pixerlinescropdir"
            pixerlinesdeskewfileList_key = r"self.pixerlinesdeskewfileList"
            pixerlinesdeskewpixmap_key = r"self.pixerlinesdeskewpixmap"
            pixerlinesdeskewqimage_key = r"self.pixerlinesdeskewqimage"
            pixerlinesdeskewpath_key = r"self.pixerlinesdeskewpath"
            pixerlinesdeskewdir_key = r"self.pixerlinesdeskewdir"
            pixerlinesdenoisefileList_key = r"self.pixerlinesdenoisefileList"
            pixerlinesdenoisepixmap_key = r"self.pixerlinesdenoisepixmap"
            pixerlinesdenoiseqimage_key = r"self.pixerlinesdenoiseqimage"
            pixerlinesdenoisepath_key = r"self.pixerlinesdenoisepath"
            pixerlinesdenoisedir_key = r"self.pixerlinesdenoisedir"
            pixerlinesrotatefileList_key = r"self.pixerlinesrotatefileList"
            pixerlinesrotatepixmap_key = r"self.pixerlinesrotatepixmap"
            pixerlinesrotateqimage_key = r"self.pixerlinesrotateqimage"
            pixerlinesrotatepath_key = r"self.pixerlinesrotatepath"
            pixerlinesrotatedir_key = r"self.pixerlinesrotatedir"
            pixerlinescleanfileList_key = r"self.pixerlinescleanfileList"
            pixerlinescleanpixmap_key = r"self.pixerlinescleanpixmap"
            pixerlinescleanqimage_key = r"self.pixerlinescleanqimage"
            pixerlinescleanpath_key = r"self.pixerlinescleanpath"
            pixerlinescleandir_key = r"self.pixerlinescleandir"
            greekpagesdenoised_key = r"self.greekpagesdenoised"
            greekpagesrotated_key = r"self.greekpagesrotated"
            greekpagesdeskewed_key = r"self.greekpagesdeskewed"
            greekpagescropped_key = r"self.greekpagescropped"
            greekpagescleaned_key = r"self.greekpagescleaned"
            greekpagesbox_key = r"self.greekpagesbox"
            greeklinescropped_key = r"self.greeklinescropped"
            greeklinescleaned_key = r"self.greeklinescleaned"
            greeklinesbox_key = r"self.greeklinesbox"
            latinpagesdenoised_key = r"self.latinpagesdenoised"
            latinpagesrotated_key = r"self.latinpagesrotated"
            latinpagesdeskewed_key = r"self.latinpagesdeskewed"
            latinpagescropped_key = r"self.latinpagescroppe"
            latinpagescleaned_key = r"self.latinpagescleaned"
            latinpagesbox_key = r"self.latinpagesbox"
            latinlinescropped_key = r"self.latinlinescropped"
            latinlinescleaned_key = r"self.latinlinescleaned"
            latinlinesbox_key = r"self.latinlinesbox"
            hebrewpagesdenoised_key = r"self.hebrewpagesdenoised"           
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
                elif Setting['Setting'] == refimg_xoffset_key:
                    self.refimg_xoffset = Setting['CurrentValue']
                elif Setting['Setting'] == refimg_yoffset_key:
                    self.refimg_yoffset = Setting['CurrentValue']
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
                elif Setting['Setting'] == image_xoffset_key:
                    self.image_xoffset = Setting['CurrentValue']
                elif Setting['Setting'] == image_yoffset_key:
                    self.image_yoffset = Setting['CurrentValue']
                elif Setting['Setting'] == imagefileList_key:
                    self.imagefileList = Setting['CurrentValue']
                elif Setting['Setting'] == imagezoom_key:
                    self.imagezoom = Setting['CurrentValue']
                elif Setting['Setting'] == imagezoomslidervalue_key:
                    self.imagezoomslidervalue = Setting['CurrentValue']
                elif Setting['Setting'] == pixerrefimgpath_key:
                    self.pixerrefimgpath = Setting['CurrentValue']
                elif Setting['Setting'] == pixerrefimgpixmap_key:
                    self.pixerrefimgpixmap = Setting['CurrentValue']
                elif Setting['Setting'] == pixerrefimgqimage_key:
                    self.pixerrefimgqimage = Setting['CurrentValue']
                elif Setting['Setting'] == pixerrefimgdir_key:
                    self.pixerrefimgdir = Setting['CurrentValue']
                elif Setting['Setting'] == pixerpagesboxfileList_key:
                    self.pixerpagesboxfileList = Setting['CurrentValue']
                elif Setting['Setting'] == pixerpagesboxpixmap_key:
                    self.pixerpagesboxpixmap = Setting['CurrentValue']
                elif Setting['Setting'] == pixerpagesboxqimage_key:
                    self.pixerpagesboxqimage = Setting['CurrentValue']
                elif Setting['Setting'] == pixerpagesboxpath_key:
                    self.pixerpagesboxpath = Setting['CurrentValue']
                elif Setting['Setting'] == pixerpagesboxdir_key:
                    self.pixerpagesboxdir = Setting['CurrentValue']
                elif Setting['Setting'] == pixerpagescropfileList_key:
                    self.pixerpagescropfileList = Setting['CurrentValue']
                elif Setting['Setting'] == pixerpagescroppixmap_key:
                    self.pixerpagescroppixmap = Setting['CurrentValue']
                elif Setting['Setting'] == pixerpagescropqimage_key:
                    self.pixerpagescropqimage = Setting['CurrentValue']
                elif Setting['Setting'] == pixerpagescroppath_key:
                    self.pixerpagescroppath = Setting['CurrentValue']
                elif Setting['Setting'] == pixerpagescropdir_key:
                    self.pixerpagescropdir = Setting['CurrentValue']
                elif Setting['Setting'] == pixerpagesdeskewfileList_key:
                    self.pixerpagesdeskewfileList = Setting['CurrentValue']
                elif Setting['Setting'] == pixerpagesdeskewpixmap_key:
                    self.pixerpagesdeskewpixmap = Setting['CurrentValue']
                elif Setting['Setting'] == pixerpagesdeskewqimage_key:
                    self.pixerpagesdeskewqimage = Setting['CurrentValue']
                elif Setting['Setting'] == pixerpagesdeskewpath_key:
                    self.pixerpagesdeskewpath = Setting['CurrentValue']
                elif Setting['Setting'] == pixerpagesdeskewdir_key:
                    self.pixerpagesdeskewdir = Setting['CurrentValue']
                elif Setting['Setting'] == pixerpagesdenoisefileList_key:
                    self.pixerpagesdenoisefileList = Setting['CurrentValue']
                elif Setting['Setting'] == pixerpagesdenoisepixmap_key:
                    self.pixerpagesdenoisepixmap = Setting['CurrentValue']
                elif Setting['Setting'] == pixerpagesdenoiseqimage_key:
                    self.pixerpagesdenoiseqimage = Setting['CurrentValue']
                elif Setting['Setting'] == pixerpagesdenoisepath_key:
                    self.pixerpagesdenoisepath = Setting['CurrentValue']
                elif Setting['Setting'] == pixerpagesdenoisedir_key:
                    self.pixerpagesdenoisedir = Setting['CurrentValue']
                elif Setting['Setting'] == pixerpagesrotatefileList_key:
                    self.pixerpagesrotatefileList = Setting['CurrentValue']
                elif Setting['Setting'] == pixerpagesrotatepixmap_key:
                    self.pixerpagesrotatepixmap = Setting['CurrentValue']
                elif Setting['Setting'] == pixerpagesrotateqimage_key:
                    self.pixerpagesrotateqimage = Setting['CurrentValue']
                elif Setting['Setting'] == pixerpagesrotatepath_key:
                    self.pixerpagesrotatepath = Setting['CurrentValue']
                elif Setting['Setting'] == pixerpagesrotatedir_key:
                    self.pixerpagesrotatedir = Setting['CurrentValue']
                elif Setting['Setting'] == pixerpagescleanfileList_key:
                    self.pixerpagescleanfileList = Setting['CurrentValue']
                elif Setting['Setting'] == pixerpagescleanpixmap_key:
                    self.pixerpagescleanpixmap = Setting['CurrentValue']
                elif Setting['Setting'] == pixerpagescleanqimage_key:
                    self.pixerpagescleanqimage = Setting['CurrentValue']
                elif Setting['Setting'] == pixerpagescleanpath_key:
                    self.pixerpagescleanpath = Setting['CurrentValue']
                elif Setting['Setting'] == pixerpagescleandir_key:
                    self.pixerpagescleandir = Setting['CurrentValue']
                elif Setting['Setting'] == pixerlinesboxfileList_key:
                    self.pixerlinesboxfileList = Setting['CurrentValue']
                elif Setting['Setting'] == pixerlinesboxpixmap_key:
                    self.pixerlinesboxpixmap = Setting['CurrentValue']
                elif Setting['Setting'] == pixerlinesboxqimage_key:
                    self.pixerlinesboxqimage = Setting['CurrentValue']
                elif Setting['Setting'] == pixerlinesboxpath_key:
                    self.pixerlinesboxpath = Setting['CurrentValue']
                elif Setting['Setting'] == pixerlinesboxdir_key:
                    self.pixerlinesboxdir = Setting['CurrentValue']
                elif Setting['Setting'] == pixerlinescropfileList_key:
                    self.pixerlinescropfileList = Setting['CurrentValue']
                elif Setting['Setting'] == pixerlinescroppixmap_key:
                    self.pixerlinescroppixmap = Setting['CurrentValue']
                elif Setting['Setting'] == pixerlinescropqimage_key:
                    self.pixerlinescropqimage = Setting['CurrentValue']
                elif Setting['Setting'] == pixerlinescroppath_key:
                    self.pixerlinescroppath = Setting['CurrentValue']
                elif Setting['Setting'] == pixerlinescropdir_key:
                    self.pixerlinescropdir = Setting['CurrentValue']
                elif Setting['Setting'] == pixerlinesdeskewfileList_key:
                    self.pixerlinesdeskewfileList = Setting['CurrentValue']
                elif Setting['Setting'] == pixerlinesdeskewpixmap_key:
                    self.pixerlinesdeskewpixmap = Setting['CurrentValue']
                elif Setting['Setting'] == pixerlinesdeskewqimage_key:
                    self.pixerlinesdeskewqimage = Setting['CurrentValue']
                elif Setting['Setting'] == pixerlinesdeskewpath_key:
                    self.pixerlinesdeskewpath = Setting['CurrentValue']
                elif Setting['Setting'] == pixerlinesdeskewdir_key:
                    self.pixerlinesdeskewdir = Setting['CurrentValue']
                elif Setting['Setting'] == pixerlinesdenoisefileList_key:
                    self.pixerlinesdenoisefileList = Setting['CurrentValue']
                elif Setting['Setting'] == pixerlinesdenoisepixmap_key:
                    self.pixerlinesdenoisepixmap = Setting['CurrentValue']
                elif Setting['Setting'] == pixerlinesdenoiseqimage_key:
                    self.pixerlinesdenoiseqimage = Setting['CurrentValue']
                elif Setting['Setting'] == pixerlinesdenoisepath_key:
                    self.pixerlinesdenoisepath = Setting['CurrentValue']
                elif Setting['Setting'] == pixerlinesdenoisedir_key:
                    self.pixerlinesdenoisedir = Setting['CurrentValue']
                elif Setting['Setting'] == pixerlinesrotatefileList_key:
                    self.pixerlinesrotatefileList = Setting['CurrentValue']
                elif Setting['Setting'] == pixerlinesrotatepixmap_key:
                    self.pixerlinesrotatepixmap = Setting['CurrentValue']
                elif Setting['Setting'] == pixerlinesrotateqimage_key:
                    self.pixerlinesrotateqimage = Setting['CurrentValue']
                elif Setting['Setting'] == pixerlinesrotatepath_key:
                    self.pixerlinesrotatepath = Setting['CurrentValue']
                elif Setting['Setting'] == pixerlinesrotatedir_key:
                    self.pixerlinesrotatedir = Setting['CurrentValue']
                elif Setting['Setting'] == pixerlinescleanfileList_key:
                    self.pixerlinescleanfileList = Setting['CurrentValue']
                elif Setting['Setting'] == pixerlinescleanpixmap_key:
                    self.pixerlinescleanpixmap = Setting['CurrentValue']
                elif Setting['Setting'] == pixerlinescleanqimage_key:
                    self.pixerlinescleanqimage = Setting['CurrentValue']
                elif Setting['Setting'] == pixerlinescleanpath_key:
                    self.pixerlinescleanpath = Setting['CurrentValue']
                elif Setting['Setting'] == pixerlinescleandir_key:
                    self.pixerlinescleandir = Setting['CurrentValue']               
                elif Setting['Setting'] == greekpagesdenoised_key:
                    self.greekpagesdenoised = Setting['CurrentValue']          
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
                elif Setting['Setting'] == latinpagesdenoised_key:
                    self.latinpagesdenoised = Setting['CurrentValue']
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
                elif Setting['Setting'] == hebrewpagesdenoised_key:
                    self.hebrewpagesdenoised = Setting['CurrentValue']
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

    def get_workflow_settings(self):

        # Opening JSON file
        with open('/home/max/Projects/BiblionOCR/Model/SQLite/json/Workflow.json') as f:
            # returns JSON object as
            # a dictionary
            data = json.load(f)
        
        # Iterating through the json
        # list
        for Sequence in data:
            print(Sequence['Sequence'], Sequence['DialogUi'],Sequence['DefaultSource'])
        
        # Closing file
        f.close() 

    def initToolbar(self):
        # Signals(Slots)
        self.ui.actionCropRefImg.triggered.connect(self.crop)
        self.ui.actionDeskewRefImg.triggered.connect(self.deskewRefImg)
        self.ui.actionRotateRefImg_360_deg.triggered.connect(self.rotateRefImg)
        #self.ui.actionDenoise.triggered.connect()
        self.ui.actionClipRefImg.triggered.connect(self.clip)
        self.ui.actionErase.triggered.connect(self.eraser)
        #self.ui.actionFlipRefImg.triggered.connect()
        self.ui.actionRotateRefImg_90_CW.triggered.connect(self.rotateRefImg90CW)
        self.ui.actionRotateRefImg_90_CCW.triggered.connect(self.rotateRefImg90CCW)
        self.ui.actionRotateRefImg_180_deg_CW.triggered.connect(self.rotateRefImg180CW)
        #self.ui.actionFillTransparent.triggered.connect()     
  
    def initMenubar(self):
        
        # File menu Signals(Slots)
 
        self.ui.actionOpen_Reference_Image.triggered.connect(self.loadRefImg)
        #self.ui.actionOpen_Image.triggered.connect(self.x)
        self.ui.actionSave_Image.triggered.connect(self.SaveImage)
        self.ui.actionSave_As_Image.triggered.connect(self.SaveImageAs)
        self.ui.actionOverwrite_Reference_Image.triggered.connect(self.OverwriteRefImg)
        self.ui.actionImport_Current_Image.triggered.connect(self.importRefImg)
        #self.ui.actionExport_Image.triggered.connect()
        
        # Edit Menu Signals(Slots)

        '''self.ui.actionFillSelection.triggered.connect()
        self.ui.actionFillBackground.triggered.connect()
        self.ui.actionFillForeground.triggered.connect()'''

    def initUI(self):

        self.get_session_settings()        
        '''if self.imgpath != "":
            self.refimgpath = self.imgpath
            self.importRefImg()'''
        
        self.initMenubar()
        self.initToolbar()

        # Button Row Signals(Slots)
        
        # Ref Image
        
        self.ui.OpenRefImgbutton.clicked.connect(self.loadRefImg)
        self.ui.ImportRefImgFilebutton.clicked.connect(self.importRefImg)
        self.ui.Deskewbutton.clicked.connect(self.deskewRefImg)
        
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
        
        self.ui.reloadImagebutton.clicked.connect(self.reloadImage)
        self.ui.reloadRefImgbutton.clicked.connect(self.reloadRefImg)

        # Image
        self.ui.ImageLE.textChanged.connect(self.changed_RefImg)
        
        self.ui.PrevImagebutton.clicked.connect(self.prevImage)
        self.ui.NextImagebutton.clicked.connect(self.nextImage)
        
        self.ui.Imagezoomslider.valueChanged.connect(self.on_Imagezoomslider)
        self.ui.ImageZoomComboBox.currentTextChanged.connect(self.on_Imagezoom)
        self.ui.ImageZoombutton.clicked.connect(self.get_Imagezoom)
        self.ui.Imagezoomslider.sliderReleased.connect(self.disable_Imagezoomslider)
        
        self.ui.ExportRefImgFilebutton.clicked.connect(self.ExportImage)
        self.ui.SaveImagebutton.clicked.connect(self.SaveImage)
        self.ui.SaveAsImagebutton.clicked.connect(self.SaveImageAs)
        
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
        # Get reference image size
        PILRefImg = pilimg.open(imgfilename)
        self.RefImg_width = PILRefImg.width
        self.RefImg_height = PILRefImg.height
        self.RefImg_size = PILRefImg.size
        PILRefImg.close()
        
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
                self.origpixmap = qtg.QPixmap.fromImage(self.qimage)
                #self.ui.RefImg.setPixmap(qtg.QPixmap(self.origpixmap))
                #self.refimgpixmap = qtg.QPixmap.fromImage(self.qimage)                
                self.refimgpixmap = qtg.QPixmap.fromImage(self.qimage).scaled(self.ui.Image.size(), qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)  
            else:
                self.origpixmap = qtg.QPixmap(self.refimgpath)
                self.refimgpixmap = qtg.QPixmap(self.refimgpath)
        
        self.pixmap = self.origpixmap
        file.close()

        if self.refimgpixmap.isNull():
            return
        
        self.on_RefImgzoom()
        
        self.refimgdir = os.path.dirname(imgfilename)
        self.ui.RefImgLE.setText(filestr)
        jsonfile = '/home/max/Projects/BiblionOCR/Model/Project/Data/json/PixlerSession.json'
                
        with open(jsonfile, 'r') as f:
            data = json.load(f)
            refimgpath_key = r"self.refimgpath"
            refimgdir_key = r"self.refimgdir"
            #refimgpixmap_key = r"self.refimgpixmap"
            #refimgqimage_key = r"self.refimgqimage"
            for Setting in data:
                if Setting['Setting'] == refimgpath_key:
                    Setting['CurrentValue'] = self.refimgpath
                    print(Setting['CurrentValue'])
                elif Setting['Setting'] == refimgdir_key:  
                    Setting['CurrentValue'] = self.refimgdir
                    print(Setting['CurrentValue'])
                '''elif Setting['Setting'] == refimgpixmap_key:
                    Setting['CurrentValue'] = self.refimgpixmap
                    print(Setting['CurrentValue'])
                elif Setting['Setting'] == refimgqimage_key:
                    Setting['CurrentValue'] = self.refimgqimage
                    print(Setting['CurrentValue'])'''
        f.close()

        os.remove(jsonfile)
        with open(jsonfile, 'w') as f:
            json.dump(data, f, indent=4)
        f.close()
        
        self.refimgfileList = []
        for i in os.listdir(self.refimgdir):
            ipath = os.path.normpath(os.path.join(self.refimgdir, i))
            if os.path.isfile(ipath) and i.lower().endswith(('.png', '.jpg', '.jpeg', '.tif')):
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
        jsonfile = '/home/max/Projects/BiblionOCR/Model/Project/Data/json/PixlerSession.json'
                
        with open(jsonfile, 'r') as f:
            data = json.load(f)
            imagepath_key = r"self.imagepath"
            imagedir_key = r"self.imagedir"
            #imagepixmap_key = r"self.imagepixmap"
            #imageqimage_key = r"self.imageqimage"
            for Setting in data:
                if Setting['Setting'] == imagepath_key:
                    Setting['CurrentValue'] = self.imagepath
                    print(Setting['CurrentValue'])
                elif Setting['Setting'] == imagedir_key:  
                    Setting['CurrentValue'] = self.imagedir
                    print(Setting['CurrentValue'])
                '''elif Setting['Setting'] == imagepixmap_key:
                    Setting['CurrentValue'] = self.imagepixmap
                    print(Setting['CurrentValue'])
                elif Setting['Setting'] == imageqimage_key:
                    Setting['CurrentValue'] = self.imageqimage
                    print(Setting['CurrentValue'])'''
        f.close()

        os.remove(jsonfile)
        with open(jsonfile, 'w') as f:
            json.dump(data, f, indent=4)
        f.close()
        
        self.imagefileList = []
        for i in os.listdir(self.imagedir):
            ipath = os.path.normpath(os.path.join(self.imagedir, i))
            if os.path.isfile(ipath) and i.lower().endswith(('.png', '.jpg', '.jpeg', '.tif')):
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

    # Workflow Controllers
    def actionextract_pdf(self):
        print("extracting pdf pages from source pdf")
        
        def accept():
        #if self.pdfxDialog.Accepted:
            # Empty default Workflow folder
            print('Workflow Folder:'+ workflow_folder,'Complete Folder:'+ complete_folder)
            for filename in os.listdir(workflow_folder):
                file_path = os.path.join(workflow_folder, filename)
                #print('File Name:'+filename, 'File Path:'+file_path)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))
            
            self.sourcefile = self.pdfx_ui.SourceLineEdit.text()
            self.firstpage = self.pdfx_ui.FirstPageLineEdit.text()
            self.lastpage = self.pdfx_ui.LastPageLineEdit.text()
            
            # Extract to default Workflow folder
            print(self.pdfx_ui.SourceLineEdit.text(), self.pdfx_ui.DestinationLineEdit.text(),self.pdfx_ui.FirstPageLineEdit.text(),self.pdfx_ui.LastPageLineEdit.text())
            pp.pdfExtractPages(self.pdfx_ui.SourceLineEdit.text(), self.pdfx_ui.DestinationLineEdit.text(),self.pdfx_ui.FirstPageLineEdit.text(),self.pdfx_ui.LastPageLineEdit.text())
            
            
            # Extract to default Complete folder
            #if complete_folder:
                #pp.pdfExtractPages(self.pdfx_ui.SourceLineEdit.text(), complete_folder, self.pdfx_ui.FirstPageLineEdit.text(),self.pdfx_ui.LastPageLineEdit.text())
            
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
            print("pdf page extraction complete")
        

            jsonfile = '/home/max/Projects/BiblionOCR/Model/Project/Data/json/Session.json'
            
            with open(jsonfile, 'r') as f:
                data = json.load(f)
                sourcefile_key = r"self.sourcefile"
                firstpage_key = r"self.firstpage"
                lastpage_key = r"self.lastpage"
                for Setting in data:
                    if Setting['Setting'] == sourcefile_key:
                        Setting['CurrentValue'] = self.sourcefile
                        print(Setting['CurrentValue'])
                    elif Setting['Setting'] == firstpage_key:  
                        Setting['CurrentValue'] = self.firstpage
                        print(Setting['CurrentValue'])
                    elif Setting['Setting'] == lastpage_key:  
                        Setting['CurrentValue'] = self.lastpage
                        print(Setting['CurrentValue'])
            f.close()

            os.remove(jsonfile)
            with open(jsonfile, 'w') as f:
                json.dump(data, f, indent=4)
            f.close()
        
        def reject():
            pass
        
        self.pdfxDialog = qtw.QDialog()
        self.pdfx_ui = Ui_ExtractDialog()
        self.pdfx_ui.setupUi(self.pdfxDialog)
        self.pdfxDialog.show()
        #self.pdfxDialog.exec_()
        seq = "SP1"
        
        def setdefault():
            if self.pdfx_ui.defaultsrcBox.isChecked():
                self.pdfx_ui.SourceButton.setEnabled(False)
                self.pdfx_ui.DestinationButton.setEnabled(False)
            else:
                self.pdfx_ui.SourceButton.setEnabled(True)
                self.pdfx_ui.DestinationButton.setEnabled(True)

        self.pdfx_ui.defaultsrcBox.stateChanged.connect(setdefault)
        self.pdfx_ui.SourceButton.clicked.connect(self.OpenPdfFileDialog)
        self.pdfx_ui.DestinationButton.clicked.connect(self.DestPdfFileDialog)
        self.pdfx_ui.buttonBox.accepted.connect(accept)
        self.pdfx_ui.buttonBox.rejected.connect(reject)

        if self.pdfx_ui.defaultsrcBox.isChecked(): 
            # disable source button (default)
            
            # get default folder
            # Define json data        
            with open('/home/max/Projects/BiblionOCR/Model/Project/Data/json/Workflow.json') as f:
                # returns JSON object as
                # a dictionary
                data = json.load(f)
                # Search the key value using 'in' operator
                for Sequence in data:
                    print(Sequence['Sequence'])
                    if Sequence['Sequence'] == seq:
                        # set source line edit to default workflow folder
                        self.pdfx_ui.SourceLineEdit.setText(Sequence['DefaultSource'])
                        self.pdfx_ui.DestinationLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                        workflow_folder = Sequence['WorkflowFullPath']+r'/'
                        complete_folder = Sequence['CompleteFullPath']+r'/'
       
        rsp = self.pdfxDialog.exec_()
   
    def actionpdf_for_tiff(self):
        print("extracting pdf pages for tif")
        
        def accept():
            # if self.pdf4tifDialog.Accepted:
            # Empty default Workflow folder
            print('Workflow Folder:'+ workflow_folder,'Complete Folder:'+ complete_folder)
            for filename in os.listdir(workflow_folder):
                file_path = os.path.join(workflow_folder, filename)
                print('File Name:'+filename, 'File Path:'+file_path)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))
            
            for filename in os.listdir(source_folder):
                print(source_folder,filename)
                source_file_path = os.path.join(source_folder, filename)
            
            # Extract to default Workflow folder
            print(source_file_path, workflow_folder)
            pp.pdf4tif(source_file_path, workflow_folder)
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
            print("pdf pages for tif extraction complete")
        def reject():
            pass

        self.pdf4tifDialog = qtw.QDialog()
        self.pdf4tif_ui = Ui_pdf4tifDialog()
        self.pdf4tif_ui.setupUi(self.pdf4tifDialog)
        self.pdf4tifDialog.show()

        seq = "SP2"
        
        def setdefault():
            if self.pdf4tif_ui.defaultsrcBox.isChecked():
                self.pdf4tif_ui.SourceButton.setEnabled(False)
                self.pdf4tif_ui.DestinationButton.setEnabled(False)
            else:
                self.pdf4tif_ui.SourceButton.setEnabled(True)
                self.pdf4tif_ui.DestinationButton.setEnabled(True)

        self.pdf4tif_ui.defaultsrcBox.stateChanged.connect(setdefault)
        self.pdf4tif_ui.SourceButton.clicked.connect(self.PdfForTifDialog)
        self.pdf4tif_ui.DestinationButton.clicked.connect(self.DestPdfForTifDialog)
        self.pdf4tif_ui.buttonBox.accepted.connect(accept)
        self.pdf4tif_ui.buttonBox.rejected.connect(reject)
        

        if self.pdf4tif_ui.defaultsrcBox.isChecked(): 
            # disable source button (default)
            
            # get default folder
            # Define json data        
            with open('/home/max/Projects/BiblionOCR/Model/Data/json/Workflow.json') as f:
                # returns JSON object as
                # a dictionary
                data = json.load(f)
                # Search the key value using 'in' operator
                for Sequence in data:
                    print(Sequence['Sequence'])
                    if Sequence['Sequence'] == seq:
                        # set source line edit to default workflow folder
                        self.pdf4tif_ui.SourceLineEdit.setText(Sequence['DefaultSource'])
                        self.pdf4tif_ui.DestinationLineEdit.setText(Sequence['WorkflowFullPath'])
                        source_folder = Sequence['DefaultSource']+r'/'
                        workflow_folder = Sequence['WorkflowFullPath']+r'/'
                        complete_folder = Sequence['CompleteFullPath']+r'/'
                        print(source_folder,workflow_folder,complete_folder)

        rsp = self.pdf4tifDialog.exec_()

    def actionpdf_to_tiff(self):
        print("converting pdf pages to tiff")
        
        def accept():
        # if self.pdf2tifDialog.Accepted:
            # Empty default Workflow folder
            print('Workflow Folder:'+ workflow_folder,'Complete Folder:'+ complete_folder)
            for filename in os.listdir(workflow_folder):
                file_path = os.path.join(workflow_folder, filename)
                print('File Name:'+filename, 'File Path:'+file_path)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))
            
            for filename in os.listdir(source_folder):
                print(source_folder,filename)
                source_file_path = os.path.join(source_folder, filename)
            
            # Extract to default Workflow folder
            print(source_folder, workflow_folder)
            #pp.pdf2tif(source_folder, workflow_folder, self.pdf2tif_ui.StartPageLineEdit.text())
            pp.pdf2tif(self.pdf2tif_ui.SourceLineEdit.text(), self.pdf2tif_ui.DestinationLineEdit.text(), self.pdf2tif_ui.StartPageLineEdit.text())
            # Copy Workflow folder to default Complete folder
            if complete_folder:
                #pp.pdf2tif(source_folder, complete_folder, self.pdf2tif_ui.StartPageLineEdit.text())
                symlinks=False
                ignore=None
                for item in os.listdir(workflow_folder):
                    source = os.path.join(workflow_folder, item)
                    destination = os.path.join(complete_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)
        def reject():
            pass

        self.pdf2tifDialog = qtw.QDialog()
        self.pdf2tif_ui = Ui_pdf2tifDialog()
        self.pdf2tif_ui.setupUi(self.pdf2tifDialog)
        self.pdf2tifDialog.show()

        seq = "SP3"
        
        def setdefault():
            if self.pdf2tif_ui.defaultsrcBox.isChecked():
                self.pdf2tif_ui.SourceButton.setEnabled(False)
                self.pdf2tif_ui.DestinationButton.setEnabled(False)
            else:
                self.pdf2tif_ui.SourceButton.setEnabled(True)
                self.pdf2tif_ui.DestinationButton.setEnabled(True)

        self.pdf2tif_ui.defaultsrcBox.stateChanged.connect(setdefault)
        self.pdf2tif_ui.SourceButton.clicked.connect(self.PdfToTifDialog)
        self.pdf2tif_ui.DestinationButton.clicked.connect(self.DestPdfToTifDialog)
        self.pdf2tif_ui.buttonBox.accepted.connect(accept)
        self.pdf2tif_ui.buttonBox.rejected.connect(reject)

        if self.pdf2tif_ui.defaultsrcBox.isChecked(): 
            # disable source button (default)
            
            # get default folder
            # Define json data        
            with open('/home/max/Projects/BiblionOCR/Model/Data/json/Workflow.json') as f:
                # returns JSON object as
                # a dictionary
                data = json.load(f)
                # Search the key value using 'in' operator
                for Sequence in data:
                    print(Sequence['Sequence'])
                    if Sequence['Sequence'] == seq:
                        # set source line edit to default workflow folder
                        self.pdf2tif_ui.SourceLineEdit.setText(Sequence['DefaultSource']+r'/')
                        self.pdf2tif_ui.DestinationLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                        source_folder = Sequence['DefaultSource']+r'/'
                        workflow_folder = Sequence['WorkflowFullPath']+r'/'
                        complete_folder = Sequence['CompleteFullPath']+r'/'
                        start_page = self.firstpage
                        self.pdf2tif_ui.StartPageLineEdit.setText(start_page)
                        print(source_folder,workflow_folder,complete_folder,start_page)

        rsp = self.pdf2tifDialog.exec_()
        

            
        print("tif pages conversion complete")

    def actiontiff_to_mono(self):
        print("creating indexed(BW) tiff")
        
        def accept():
            # if self.tif2monoDialog.Accepted:
            # Empty default Workflow folder
            print('Workflow Folder:'+ workflow_folder,'Complete Folder:'+ complete_folder)
            for filename in os.listdir(workflow_folder):
                file_path = os.path.join(workflow_folder, filename)
                print('File Name:'+filename, 'File Path:'+file_path)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))
            
            for filename in os.listdir(source_folder):
                print(source_folder,filename)
                source_file_path = os.path.join(source_folder, filename)
            
            # Extract to default Workflow folder
            print(source_folder, workflow_folder)
            pp.tiff2tiffidx(self.tif2mono_ui.SourceLineEdit.text(), self.tif2mono_ui.DestinationLineEdit.text())
            # Copy Workflow folder to default Complete folder
            if complete_folder:
                #pp.pdf2tif(source_folder, complete_folder, self.pdf2tif_ui.StartPageLineEdit.text())
                symlinks=False
                ignore=None
                for item in os.listdir(workflow_folder):
                    source = os.path.join(workflow_folder, item)
                    destination = os.path.join(complete_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)
        def reject():
            pass
        
        #usage: pp.tiff2tiffidx(source, destination)      
        
        self.tif2monoDialog = qtw.QDialog()
        self.tif2mono_ui = Ui_tif2monoDialog()
        self.tif2mono_ui.setupUi(self.tif2monoDialog)
        self.tif2monoDialog.show()

        seq = "SP4"
        
        def setdefault():
            if self.tif2mono_ui.defaultsrcBox.isChecked():
                self.tif2mono_ui.SourceButton.setEnabled(False)
                self.tif2mono_ui.DestinationButton.setEnabled(False)
            else:
                self.tif2mono_ui.SourceButton.setEnabled(True)
                self.tif2mono_ui.DestinationButton.setEnabled(True)

        self.tif2mono_ui.defaultsrcBox.stateChanged.connect(setdefault)
        self.tif2mono_ui.SourceButton.clicked.connect(self.TifToMonoDialog)
        self.tif2mono_ui.DestinationButton.clicked.connect(self.DestTifToMonoDialog)
        self.tif2mono_ui.buttonBox.accepted.connect(accept)
        self.tif2mono_ui.buttonBox.rejected.connect(reject)

        if self.tif2mono_ui.defaultsrcBox.isChecked(): 
            # disable source button (default)
            
            # get default folder
            # Define json data        
            with open('/home/max/Projects/BiblionOCR/Model/Data/json/Workflow.json') as f:
                # returns JSON object as
                # a dictionary
                data = json.load(f)
                # Search the key value using 'in' operator
                for Sequence in data:
                    print(Sequence['Sequence'])
                    if Sequence['Sequence'] == seq:
                        # set source line edit to default workflow folder
                        self.tif2mono_ui.SourceLineEdit.setText(Sequence['DefaultSource']+r'/')
                        self.tif2mono_ui.DestinationLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                        source_folder = Sequence['DefaultSource']+r'/'
                        workflow_folder = Sequence['WorkflowFullPath']+r'/'
                        complete_folder = Sequence['CompleteFullPath']+r'/'+self.sourcebookmarkdown+r'/'
                        print(source_folder,workflow_folder,complete_folder)

        rsp = self.tif2monoDialog.exec_()
        

            
        print("completed creating indexed(BW) tiff")

    def actionmono_to_png(self):
        print("creating indexed(BW) png")
        
        def accept():
            # if self.mono2pngDialog.Accepted:
            # Empty default Workflow folder
            print('Workflow Folder:'+ workflow_folder,'Complete Folder:'+ complete_folder)
            for filename in os.listdir(workflow_folder):
                file_path = os.path.join(workflow_folder, filename)
                print('File Name:'+filename, 'File Path:'+file_path)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))
            
            for filename in os.listdir(source_folder):
                print(source_folder,filename)
                source_file_path = os.path.join(source_folder, filename)
            
            # Extract to default Workflow folder
            print(source_folder, workflow_folder)
            pp.tiff2pngidx(self.mono2png_ui.SourceLineEdit.text(), self.mono2png_ui.DestinationLineEdit.text())
            # Copy Workflow folder to default Complete folder
            if complete_folder:
                #pp.pdf2tif(source_folder, complete_folder, self.pdf2tif_ui.StartPageLineEdit.text())
                symlinks=False
                ignore=None
                for item in os.listdir(workflow_folder):
                    source = os.path.join(workflow_folder, item)
                    destination = os.path.join(complete_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)
        def reject():
            pass

        #usage: pp.tiff2pngidx(source, destination)

        self.mono2pngDialog = qtw.QDialog()
        self.mono2png_ui = Ui_mono2pngDialog()
        self.mono2png_ui.setupUi(self.mono2pngDialog)
        self.mono2pngDialog.show()

        seq = "SP5"
        
        def setdefault():
            if self.mono2png_ui.defaultsrcBox.isChecked():
                self.mono2png_ui.SourceButton.setEnabled(False)
                self.mono2png_ui.DestinationButton.setEnabled(False)
            else:
                self.mono2png_ui.SourceButton.setEnabled(True)
                self.mono2png_ui.DestinationButton.setEnabled(True)

        self.mono2png_ui.defaultsrcBox.stateChanged.connect(setdefault)
        self.mono2png_ui.SourceButton.clicked.connect(self.MonoToPngDialog)
        self.mono2png_ui.DestinationButton.clicked.connect(self.DestMonoToPngDialog)
        self.mono2png_ui.buttonBox.accepted.connect(accept)
        self.mono2png_ui.buttonBox.rejected.connect(reject)
        

        if self.mono2png_ui.defaultsrcBox.isChecked(): 
            # disable source button (default)
            
            # get default folder
            # Define json data        
            with open('/home/max/Projects/BiblionOCR/Model/Data/json/Workflow.json') as f:
                # returns JSON object as
                # a dictionary
                data = json.load(f)
                # Search the key value using 'in' operator
                for Sequence in data:
                    print(Sequence['Sequence'])
                    if Sequence['Sequence'] == seq:
                        # set source line edit to default workflow folder
                        self.mono2png_ui.SourceLineEdit.setText(Sequence['DefaultSource']+r'/')
                        self.mono2png_ui.DestinationLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                        source_folder = Sequence['DefaultSource']+r'/'
                        workflow_folder = Sequence['WorkflowFullPath']+r'/'
                        complete_folder = Sequence['CompleteFullPath']+r'/'+self.sourcebookmarkdown+r'/'
                        print(source_folder,workflow_folder,complete_folder)

        rsp = self.mono2pngDialog.exec_()
        
    
        print("completed creating indexed(BW) png")

    def actiondeskew_mono(self):
        print("deskewing monochrome tiff and png files")
        
        def accept():
            # if self.deskew_monoDialog.Accepted:
            # Empty default Workflow folders
            print('tif Workflow Folder:'+ tif_workflow_folder,'tif Complete Folder:'+ tif_complete_folder)
            print('png Workflow Folder:'+ png_workflow_folder,'png Complete Folder:'+ png_complete_folder)
            # Empty default tif Workflow folders
            for filename in os.listdir(tif_workflow_folder):
                file_path = os.path.join(tif_workflow_folder, filename)
                print('tif File Name:'+filename, 'tif File Path:'+file_path)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))
            # Empty default png Workflow folders
            for filename in os.listdir(png_workflow_folder):
                file_path = os.path.join(png_workflow_folder, filename)
                print('png File Name:'+filename, 'png File Path:'+file_path)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))
            
            for filename in os.listdir(source_folder):
                print(source_folder,filename)
                source_file_path = os.path.join(source_folder, filename)
            
            # Extract to default Workflow folders
            print(source_folder, png_workflow_folder, tif_workflow_folder)
            pp.deskewfiles(self.deskew_mono_ui.SourceLineEdit.text(), self.deskew_mono_ui.DestPngLineEdit.text(),self.deskew_mono_ui.DestTifLineEdit.text())
            # Copy Workflow folder to default Complete folders
            if tif_complete_folder:
                symlinks=False
                ignore=None
                for item in os.listdir(tif_workflow_folder):
                    source = os.path.join(tif_workflow_folder, item)
                    destination = os.path.join(tif_complete_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)
            if png_complete_folder:
                symlinks=False
                ignore=None
                for item in os.listdir(png_workflow_folder):
                    source = os.path.join(png_workflow_folder, item)
                    destination = os.path.join(png_complete_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)
        def reject():
            pass
        
        #usage: dsk.deskewfiles(source, pngdest, tifdest)

        self.deskew_monoDialog = qtw.QDialog()
        self.deskew_mono_ui = Ui_deskew_monoDialog()
        self.deskew_mono_ui.setupUi(self.deskew_monoDialog)
        self.deskew_monoDialog.show()

        seq = "SP6"
        
        def setdefault():
            if self.deskew_mono_ui.defaultsrcBox.isChecked():
                self.deskew_mono_ui.SourceButton.setEnabled(False)
                self.deskew_mono_ui.DestTifButton.setEnabled(False)
            else:
                self.deskew_mono_ui.SourceButton.setEnabled(True)
                self.deskew_mono_ui.DestTifButton.setEnabled(True)

        if self.deskew_mono_ui.defaultsrcBox.isChecked(): 
            # disable source button (default)
            
            # get default folder
            # Define json data        
            with open('/home/max/Projects/BiblionOCR/Model/Data/json/Workflow.json') as f:
                # returns JSON object as
                # a dictionary
                data = json.load(f)
                # Search the key value using 'in' operator
                for Sequence in data:
                    print(Sequence['Sequence'])
                    if Sequence['Sequence'] == seq:
                        # set source line edit to default workflow folder
                        self.deskew_mono_ui.SourceLineEdit.setText(Sequence['DefaultSource']+r'/')
                        self.deskew_mono_ui.DestTifLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                        source_folder = Sequence['DefaultSource']+r'/'
                        tif_workflow_folder = Sequence['WorkflowFullPath']+r'/'
                        tif_complete_folder = Sequence['CompleteFullPath']+r'/'+self.sourcebookmarkdown+r'/'
                        print(source_folder,tif_workflow_folder,tif_complete_folder)  
            
        seq = "SP7"
        
        def setdefault():
            if self.deskew_mono_ui.defaultsrcBox.isChecked():
                self.deskew_mono_ui.SourceButton.setEnabled(False)
                self.deskew_mono_ui.DestPngButton.setEnabled(False)
            else:
                self.deskew_mono_ui.SourceButton.setEnabled(True)
                self.deskew_mono_ui.DestPngButton.setEnabled(True)

        self.deskew_mono_ui.SourceButton.clicked.connect(self.DeskewMonoDialog)
        self.deskew_mono_ui.DestPngButton.clicked.connect(self.DestDeskewPngDialog)
        self.deskew_mono_ui.DestTifButton.clicked.connect(self.DestDeskewTifDialog)
        self.deskew_mono_ui.buttonBox.accepted.connect(accept)
        self.deskew_mono_ui.buttonBox.rejected.connect(reject)

        if self.deskew_mono_ui.defaultsrcBox.isChecked(): 
            # disable source button (default)
            
            # get default folder
            # Define json data        
            with open('/home/max/Projects/BiblionOCR/Model/Data/json/Workflow.json') as f:
                # returns JSON object as
                # a dictionary
                data = json.load(f)
                # Search the key value using 'in' operator
                for Sequence in data:
                    print(Sequence['Sequence'])
                    if Sequence['Sequence'] == seq:
                        # set source line edit to default workflow folder
                        self.deskew_mono_ui.SourceLineEdit.setText(Sequence['DefaultSource']+r'/')
                        self.deskew_mono_ui.DestPngLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                        #source_folder = Sequence['DefaultSource']+r'/'
                        png_workflow_folder = Sequence['WorkflowFullPath']+r'/'
                        png_complete_folder = Sequence['CompleteFullPath']+r'/'+self.sourcebookmarkdown+r'/'
                        print(png_workflow_folder,png_complete_folder)

        rsp = self.deskew_monoDialog.exec_() 
        print("completed deskewing monochrome tiff and png files")
     
    def actionCrop_Languages(self):
        print("creating cropped language tif files")

        def accept():
        #if self.crop_languagesDialog.Accepted:
            # Empty default tif Workflow folders
            if workflow_greek_folder:
                for filename in os.listdir(workflow_greek_folder):
                    file_path = os.path.join(workflow_greek_folder, filename)
                    print('tif File Name:'+filename, 'tif File Path:'+file_path)
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        print('Failed to delete %s. Reason: %s' % (file_path, e))
                    # Empty default tif Workflow folders
            if workflow_latin_folder:
                for filename in os.listdir(workflow_latin_folder):
                    file_path = os.path.join(workflow_latin_folder, filename)
                    print('tif File Name:'+filename, 'tif File Path:'+file_path)
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        print('Failed to delete %s. Reason: %s' % (file_path, e))
            pp.croplangs(self.crop_languages_ui.SourceLineEdit.text(), self.crop_languages_ui.BoxFolderLineEdit.text(),self.crop_languages_ui.DestGreekLineEdit.text(),self.crop_languages_ui.DestLatinLineEdit.text(),self.crop_languages_ui.ElimFolderLineEdit.text())
            print("completed creating cropped language tif files")
            # copy workflow images to complete images
            if workflow_box_folder:
                symlinks=False
                ignore=None
                for item in os.listdir(workflow_box_folder):
                    source = os.path.join(workflow_box_folder, item)
                    destination = os.path.join(complete_box_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)
            if workflow_elim_folder:
                symlinks=False
                ignore=None
                for item in os.listdir(workflow_elim_folder):
                    source = os.path.join(workflow_elim_folder, item)
                    destination = os.path.join(complete_elim_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)
            
            if workflow_greek_folder:
                symlinks=False
                ignore=None
                for item in os.listdir(workflow_greek_folder):
                    source = os.path.join(workflow_greek_folder, item)
                    destination = os.path.join(complete_greek_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)

            '''if workflow_dup_greek_folder: 
                symlinks=False
                ignore=None
                for item in os.listdir(workflow_greek_folder):
                    source = os.path.join(workflow_greek_folder, item)
                    destination = os.path.join(workflow_dup_greek_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)
                    # enable section below to remove files from workflow_greek_folder
                    file_path = os.path.join(workflow_greek_folder, filename)
                    print('File Name:'+filename, 'File Path:'+file_path)
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        print('Failed to delete %s. Reason: %s' % (file_path, e))'''

            if workflow_latin_folder:
                symlinks=False
                ignore=None
                for item in os.listdir(workflow_latin_folder):
                    source = os.path.join(workflow_latin_folder, item)
                    destination = os.path.join(complete_latin_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)
            '''if workflow_dup_latin_folder:
                #symlinks=False
                #ignore=None
                for item in os.listdir(workflow_latin_folder):
                    source = os.path.join(workflow_latin_folder, item)
                    destination = os.path.join(workflow_dup_latin_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)
                    file_path = os.path.join(workflow_latin_folder, filename)
                    print('File Name:'+filename, 'File Path:'+file_path)
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        print('Failed to delete %s. Reason: %s' % (file_path, e))'''

        def reject():
            pass
 
        #usage: pp.croplangs(source, boxdir, greekdir, latindir, elimdir)
        self.crop_languagesDialog = qtw.QDialog()
        self.crop_languages_ui = Ui_crop_languagesDialog()
        self.crop_languages_ui.setupUi(self.crop_languagesDialog)
        self.crop_languagesDialog.show()


        self.crop_languages_ui.SourceButton.clicked.connect(self.CropLanguagesDialog)
        self.crop_languages_ui.BoxFolderButton.clicked.connect(self.BoxFolderDialog)
        self.crop_languages_ui.ElimFolderButton.clicked.connect(self.ElimFolderDialog)
        self.crop_languages_ui.DestGreekButton.clicked.connect(self.DestGreekDialog)
        self.crop_languages_ui.DestLatinButton.clicked.connect(self.DestLatinDialog)
        self.crop_languages_ui.buttonBox.accepted.connect(accept)
        self.crop_languages_ui.buttonBox.rejected.connect(reject)

        seq = ["SP10","SP11","GP1","GP2","LP1","LP2"]

        if self.crop_languages_ui.defaultsrcBox.isChecked(): 
            # disable source button (default)
            
            for step in seq:

                # Define json data        
                with open('/home/max/Projects/BiblionOCR/Model/Data/json/Workflow.json') as f:
                    # returns JSON object as
                    # a dictionary
                    data = json.load(f)

                    # Search the key value using 'in' operator
                    for Sequence in data:
                        print(Sequence['Sequence'])
                        if Sequence['Sequence'] == step:
                            # set line edits to their default workflow folders
                            if step == "SP10":
                                self.crop_languages_ui.SourceLineEdit.setText(Sequence['DefaultSource']+r'/')
                                source_folder = Sequence['DefaultSource']+r'/'
                                self.crop_languages_ui.BoxFolderLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                                workflow_box_folder = Sequence['WorkflowFullPath']+r'/'
                                complete_box_folder = Sequence['CompleteFullPath']+r'/'+self.sourcebookmarkdown+r'/'
                            elif step == "SP11":
                                self.crop_languages_ui.ElimFolderLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                                workflow_elim_folder = Sequence['WorkflowFullPath']+r'/'
                                complete_elim_folder = Sequence['CompleteFullPath']+r'/'+self.sourcebookmarkdown+r'/'
                            elif step == "GP1":
                                self.crop_languages_ui.DestGreekLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                                workflow_greek_folder = Sequence['WorkflowFullPath']+r'/'
                                complete_greek_folder = Sequence['CompleteFullPath']+r'/'+self.greekbookmarkdown+r'/'                             
                            elif step == "GP2":
                                #self.crop_languages_ui.DestGreekLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                                workflow_dup_greek_folder = Sequence['WorkflowFullPath']+r'/'
                                #complete_greek_folder = Sequence['CompleteFullPath']+r'/'+self.greekbookmarkdown+r'/'                                
                            elif step == "LP1":                         
                                self.crop_languages_ui.DestLatinLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                                workflow_latin_folder = Sequence['WorkflowFullPath']+r'/'
                                complete_latin_folder = Sequence['CompleteFullPath']+r'/'+self.latinbookmarkdown+r'/'                            
                            elif step == "LP2":                         
                                #self.crop_languages_ui.DestLatinLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                                workflow_dup_latin_folder = Sequence['WorkflowFullPath']+r'/'
                                #complete_latin_folder = Sequence['CompleteFullPath']+r'/'+self.latinbookmarkdown+r'/'

                f.close()
        print(source_folder,workflow_box_folder,workflow_elim_folder,workflow_greek_folder,workflow_latin_folder)                  
        rsp = self.crop_languagesDialog.exec_()

    def actionConvert_Greek_tiff_To_png(self):
        print("creating indexed(BW) Greek png files")
        #usage: pp.tiff2pngidx(source, destination)
        def accept():
            # if self.mono2pngDialog.Accepted:
            # Empty default Workflow folder
            print('Workflow Folder:'+ workflow_folder,'Complete Folder:'+ complete_folder)
            for filename in os.listdir(workflow_folder):
                file_path = os.path.join(workflow_folder, filename)
                print('File Name:'+filename, 'File Path:'+file_path)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))
            
            for filename in os.listdir(source_folder):
                print(source_folder,filename)
                source_file_path = os.path.join(source_folder, filename)
            
            # Extract to default Workflow folder
            print(source_folder, workflow_folder)
            pp.tiff2pngidx(self.greekmono2png_ui.SourceLineEdit.text(), self.greekmono2png_ui.DestinationLineEdit.text())
            # Copy Workflow folder to default Complete folder
            if complete_folder:
                #pp.pdf2tif(source_folder, complete_folder, self.pdf2tif_ui.StartPageLineEdit.text())
                symlinks=False
                ignore=None
                for item in os.listdir(workflow_folder):
                    source = os.path.join(workflow_folder, item)
                    destination = os.path.join(complete_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)
        def reject():
            pass

        #usage: pp.tiff2pngidx(source, destination)

        self.greekmono2pngDialog = qtw.QDialog()
        self.greekmono2png_ui = Ui_greekmono2pngDialog()
        self.greekmono2png_ui.setupUi(self.greekmono2pngDialog)
        self.greekmono2pngDialog.show()
        
        seq = "GP5"
        
        def setdefault():
            if self.greekmono2png_ui.defaultsrcBox.isChecked():
                self.greekmono2png_ui.SourceButton.setEnabled(False)
                self.greekmono2png_ui.DestinationButton.setEnabled(False)
            else:
                self.greekmono2png_ui.SourceButton.setEnabled(True)
                self.greekmono2png_ui.DestinationButton.setEnabled(True)

        self.greekmono2png_ui.defaultsrcBox.stateChanged.connect(setdefault)
        self.greekmono2png_ui.SourceButton.clicked.connect(self.GreekMonoToPngDialog)
        self.greekmono2png_ui.DestinationButton.clicked.connect(self.GreekDestMonoToPngDialog)
        self.greekmono2png_ui.buttonBox.accepted.connect(accept)
        self.greekmono2png_ui.buttonBox.rejected.connect(reject)
        

        if self.greekmono2png_ui.defaultsrcBox.isChecked(): 
            # disable source button (default)
            
            # get default folder
            # Define json data        
            with open('/home/max/Projects/BiblionOCR/Model/Data/json/Workflow.json') as f:
                # returns JSON object as
                # a dictionary
                data = json.load(f)
                # Search the key value using 'in' operator
                for Sequence in data:
                    print(Sequence['Sequence'])
                    if Sequence['Sequence'] == seq:
                        # set source line edit to default workflow folder
                        self.greekmono2png_ui.SourceLineEdit.setText(Sequence['DefaultSource']+r'/')
                        self.greekmono2png_ui.DestinationLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                        source_folder = Sequence['DefaultSource']+r'/'
                        workflow_folder = Sequence['WorkflowFullPath']+r'/'
                        complete_folder = Sequence['CompleteFullPath']+r'/'+self.greekbookmarkdown+r'/'
                        print(source_folder,workflow_folder,complete_folder)

        rsp = self.greekmono2pngDialog.exec_()
        print("completed creating indexed(BW) png")
        #pp.tiff2pngidx(r"/home/max/Projects/Python/Images/Source/tif_black_white/source_book_40_Matthew/", "/home/max/Projects/Python/Images/Source/tif_black_white_2png/source_book_40_Matthew/")
        #pp.tiff2pngidx(r"/home/max/Projects/Python/Images/Greek/tif_greek/greek_book_41_Mark/", "/home/max/Projects/Python/Images/Greek/png_greek/greek_book_41_Mark/")

    def actionDeskew_Greek_tiff(self):
        print("deskewing Greek tiff files")
        #usage: dsk.deskewfiles(source, pngdest, tifdest)
        
        def accept():
            # if self.deskew_greekmonoDialog.Accepted:
            # Empty default Workflow folders
            print('tif Workflow Folder:'+ tif_workflow_folder,'tif Complete Folder:'+ tif_complete_folder)
            print('png Workflow Folder:'+ png_workflow_folder,'png Complete Folder:'+ png_complete_folder)
            # Empty default tif Workflow folders
            for filename in os.listdir(tif_workflow_folder):
                file_path = os.path.join(tif_workflow_folder, filename)
                print('tif File Name:'+filename, 'tif File Path:'+file_path)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))
            # Empty default png Workflow folders
            for filename in os.listdir(png_workflow_folder):
                file_path = os.path.join(png_workflow_folder, filename)
                print('png File Name:'+filename, 'png File Path:'+file_path)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))
            
            for filename in os.listdir(source_folder):
                print(source_folder,filename)
                source_file_path = os.path.join(source_folder, filename)
            
            # Extract to default Workflow folders
            print(source_folder, png_workflow_folder, tif_workflow_folder)
            pp.deskewfiles(self.deskew_greekmono_ui.SourceLineEdit.text(), self.deskew_greekmono_ui.DestPngLineEdit.text(),self.deskew_greekmono_ui.DestTifLineEdit.text())
            # Copy Workflow folder to default Complete folders
            if tif_complete_folder:
                symlinks=False
                ignore=None
                for item in os.listdir(tif_workflow_folder):
                    source = os.path.join(tif_workflow_folder, item)
                    destination = os.path.join(tif_complete_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)
            if png_complete_folder:
                symlinks=False
                ignore=None
                for item in os.listdir(png_workflow_folder):
                    source = os.path.join(png_workflow_folder, item)
                    destination = os.path.join(png_complete_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)
        def reject():
            pass
        
        #usage: dsk.deskewfiles(source, pngdest, tifdest)

        self.deskew_greekmonoDialog = qtw.QDialog()
        self.deskew_greekmono_ui = Ui_deskew_greekmonoDialog()
        self.deskew_greekmono_ui.setupUi(self.deskew_greekmonoDialog)
        self.deskew_greekmonoDialog.show()

        seq = "GP6"
        
        def setdefault():
            if self.deskew_greekmono_ui.defaultsrcBox.isChecked():
                self.deskew_greekmono_ui.SourceButton.setEnabled(False)
                self.deskew_greekmono_ui.DestTifButton.setEnabled(False)
            else:
                self.deskew_greekmono_ui.SourceButton.setEnabled(True)
                self.deskew_greekmono_ui.DestTifButton.setEnabled(True)

        if self.deskew_greekmono_ui.defaultsrcBox.isChecked(): 
            # disable source button (default)
            
            # get default folder
            # Define json data        
            with open('/home/max/Projects/BiblionOCR/Model/Data/json/Workflow.json') as f:
                # returns JSON object as
                # a dictionary
                data = json.load(f)
                # Search the key value using 'in' operator
                for Sequence in data:
                    print(Sequence['Sequence'])
                    if Sequence['Sequence'] == seq:
                        # set source line edit to default workflow folder
                        self.deskew_greekmono_ui.SourceLineEdit.setText(Sequence['DefaultSource']+r'/')
                        self.deskew_greekmono_ui.DestTifLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                        source_folder = Sequence['DefaultSource']+r'/'
                        tif_workflow_folder = Sequence['WorkflowFullPath']+r'/'
                        tif_complete_folder = Sequence['CompleteFullPath']+r'/'+self.greekbookmarkdown+r'/'
                        print(source_folder,tif_workflow_folder,tif_complete_folder)  
            
        seq = "GP7"
        
        def setdefault():
            if self.deskew_greekmono_ui.defaultsrcBox.isChecked():
                self.deskew_greekmono_ui.SourceButton.setEnabled(False)
                self.deskew_greekmono_ui.DestPngButton.setEnabled(False)
            else:
                self.deskew_greekmono_ui.SourceButton.setEnabled(True)
                self.deskew_greekmono_ui.DestPngButton.setEnabled(True)

        self.deskew_greekmono_ui.SourceButton.clicked.connect(self.DeskewGreekMonoDialog)
        self.deskew_greekmono_ui.DestPngButton.clicked.connect(self.DestDeskewGreekPngDialog)
        self.deskew_greekmono_ui.DestTifButton.clicked.connect(self.DestDeskewGreekTifDialog)
        self.deskew_greekmono_ui.buttonBox.accepted.connect(accept)
        self.deskew_greekmono_ui.buttonBox.rejected.connect(reject)

        if self.deskew_greekmono_ui.defaultsrcBox.isChecked(): 
            # disable source button (default)
            
            # get default folder
            # Define json data        
            with open('/home/max/Projects/BiblionOCR/Model/Data/json/Workflow.json') as f:
                # returns JSON object as
                # a dictionary
                data = json.load(f)
                # Search the key value using 'in' operator
                for Sequence in data:
                    print(Sequence['Sequence'])
                    if Sequence['Sequence'] == seq:
                        # set source line edit to default workflow folder
                        #self.deskew_greekmono_ui.SourceLineEdit.setText(Sequence['DefaultSource']+r'/')
                        self.deskew_greekmono_ui.DestPngLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                        #source_folder = Sequence['DefaultSource']+r'/'
                        png_workflow_folder = Sequence['WorkflowFullPath']+r'/'
                        png_complete_folder = Sequence['CompleteFullPath']+r'/'+self.greekbookmarkdown+r'/'
                        print(source_folder,png_workflow_folder,png_complete_folder)

        rsp = self.deskew_greekmonoDialog.exec_()
        
        
        #dsk.deskewfiles("/home/max/Projects/Python/Images/Greek/png_greek/greek_book_40_Matthew/", "/home/max/Projects/Python/Images/Greek/png_greek_deskew/greek_book_40_Matthew/","/home/max/Projects/Python/Images/Greek/tif_greek_deskew/greek_book_40_Matthew/")
        #pp.deskewfiles("/home/max/Projects/Python/Images/Greek/png_greek/greek_book_41_Mark/", "/home/max/Projects/Python/Images/Greek/png_greek_deskew/greek_book_41_Mark/","/home/max/Projects/Python/Images/Greek/tif_greek_deskew/greek_book_41_Mark/")


    def actionResize_Greek_png(self):
        print("resizing Greek png files")
        #usage: pp.resizepngs(source, destination)
        def accept():
            # if self.mono2pngDialog.Accepted:
            # Empty default Workflow folder
            print('Workflow Folder:'+ workflow_folder,'Complete Folder:'+ complete_folder)
            for filename in os.listdir(workflow_folder):
                file_path = os.path.join(workflow_folder, filename)
                print('File Name:'+filename, 'File Path:'+file_path)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))
            
            for filename in os.listdir(source_folder):
                print(source_folder,filename)
                source_file_path = os.path.join(source_folder, filename)
            
            # Extract to default Workflow folder
            print(source_folder, workflow_folder)
            pp.resizepngs(self.greekresizepng_ui.SourceLineEdit.text(), self.greekresizepng_ui.DestinationLineEdit.text())

            # Copy Workflow folder to default Complete folder
            if complete_folder:
                #pp.pdf2tif(source_folder, complete_folder, self.pdf2tif_ui.StartPageLineEdit.text())
                symlinks=False
                ignore=None
                for item in os.listdir(workflow_folder):
                    source = os.path.join(workflow_folder, item)
                    destination = os.path.join(complete_folder, item)
                    if os.path.isdir(source):
                        shutil.copytree(source, destination, symlinks, ignore)
                    else:
                        shutil.copy2(source, destination)
        def reject():
            pass

        #usage: pp.tiff2pngidx(source, destination)

        self.greekresizepngDialog = qtw.QDialog()
        self.greekresizepng_ui = Ui_greekresizepngDialog()
        self.greekresizepng_ui.setupUi(self.greekresizepngDialog)
        self.greekresizepngDialog.show()
        
        seq = "GP10"
        
        def setdefault():
            if self.greekresizepng_ui.defaultsrcBox.isChecked():
                self.greekresizepng_ui.SourceButton.setEnabled(False)
                self.greekresizepng_ui.DestinationButton.setEnabled(False)
            else:
                self.greekresizepng_ui.SourceButton.setEnabled(True)
                self.greekresizepng_ui.DestinationButton.setEnabled(True)

        self.greekresizepng_ui.defaultsrcBox.stateChanged.connect(setdefault)
        self.greekresizepng_ui.SourceButton.clicked.connect(self.GreekResizePngDialog)
        self.greekresizepng_ui.DestinationButton.clicked.connect(self.DestGreekResizePngDialog)
        self.greekresizepng_ui.buttonBox.accepted.connect(accept)
        self.greekresizepng_ui.buttonBox.rejected.connect(reject)
        

        if self.greekresizepng_ui.defaultsrcBox.isChecked(): 
            # disable source button (default)
            
            # get default folder
            # Define json data        
            with open('/home/max/Projects/BiblionOCR/Model/Data/json/Workflow.json') as f:
                # returns JSON object as
                # a dictionary
                data = json.load(f)
                # Search the key value using 'in' operator
                for Sequence in data:
                    print(Sequence['Sequence'])
                    if Sequence['Sequence'] == seq:
                        # set source line edit to default workflow folder
                        self.greekresizepng_ui.SourceLineEdit.setText(Sequence['DefaultSource']+r'/')
                        self.greekresizepng_ui.DestinationLineEdit.setText(Sequence['WorkflowFullPath']+r'/')
                        source_folder = Sequence['DefaultSource']+r'/'
                        workflow_folder = Sequence['WorkflowFullPath']+r'/'
                        complete_folder = Sequence['CompleteFullPath']+r'/'+self.greekbookmarkdown+r'/'
                        print(source_folder,workflow_folder,complete_folder)

        rsp = self.greekresizepngDialog.exec_()
        print("completed resizing indexed(BW) png")
        #pp.tiff2pngidx(r"/home/max/Projects/Python/Images/Source/tif_black_white/source_book_40_Matthew/", "/home/max/Projects/Python/Images/Source/tif_black_white_2png/source_book_40_Matthew/")
        #pp.tiff2pngidx(r"/home/max/Projects/Python/Images/Greek/tif_greek/greek_book_41_Mark/", "/home/max/Projects/Python/Images/Greek/png_greek/greek_book_41_Mark/")

        #pp.resizepngs(r"/home/max/Projects/Python/Images/Greek/png_greek_deskew/greek_book_40_Matthew/","/home/max/Projects/Python/Images/Greek/png_greek_resize/greek_book_40_Matthew/")
        #pp.resizepngs(r"/home/max/Projects/Python/Images/Greek/png_greek_deskew/greek_book_41_Mark/","/home/max/Projects/Python/Images/Greek/png_greek_resize/greek_book_41_Mark/")

    def actionConvert_Latin_tiff_To_png(self):
        print("creating indexed(BW) Latin png files")
        #usage: pp.tiff2pngidx(source, destination)
        self.latinmono2pngDialog = qtw.QDialog()
        self.latinmono2png_ui = Ui_latinmono2pngDialog()
        self.latinmono2png_ui.setupUi(self.latinmono2pngDialog)
        self.latinmono2pngDialog.show()

        self.latinmono2png_ui.SourceButton.clicked.connect(self.LatinMonoToPngDialog)
        self.latinmono2png_ui.DestinationButton.clicked.connect(self.LatinDestMonoToPngDialog)

        rsp = self.latinmono2pngDialog.exec_()
        
        if self.latinmono2pngDialog.Accepted:
            pp.tiff2pngidx(self.latinmono2png_ui.SourceLineEdit.text(), self.latinmono2png_ui.DestinationLineEdit.text())
            print("completed creating indexed(BW) png")
        #pp.tiff2pngidx(r"/home/max/Projects/Python/Images/Source/tif_black_white/source_book_40_Matthew/", "/home/max/Projects/Python/Images/Source/tif_black_white_2png/source_book_40_Matthew/")
        #pp.tiff2pngidx(r"/home/max/Projects/Python/Images/Latin/tif_latin/latin_book_41_Mark/", "/home/max/Projects/Python/Images/Latin/png_latin/latin_book_41_Mark/")

    def actionDeskew_Latin_tiff(self):
        print("deskewing Latin tiff files")
        #usage: dsk.deskewfiles(source, pngdest, tifdest)
        self.deskew_latinmonoDialog = qtw.QDialog()
        self.deskew_latinmono_ui = Ui_deskew_latinmonoDialog()
        self.deskew_latinmono_ui.setupUi(self.deskew_latinmonoDialog)
        self.deskew_latinmonoDialog.show()

        self.deskew_latinmono_ui.SourceButton.clicked.connect(self.DeskewLatinMonoDialog)
        self.deskew_latinmono_ui.DestPngButton.clicked.connect(self.DestDeskewLatinPngDialog)
        self.deskew_latinmono_ui.DestTifButton.clicked.connect(self.DestDeskewLatinTifDialog)

        rsp = self.deskew_latinmonoDialog.exec_()
        
        if self.deskew_latinmonoDialog.Accepted:
            pp.deskewfiles(self.deskew_latinmono_ui.SourceLineEdit.text(), self.deskew_latinmono_ui.DestPngLineEdit.text(),self.deskew_latinmono_ui.DestTifLineEdit.text())
            print("completed deskewing monochrome tiff and png files")
        #dsk.deskewfiles("/home/max/Projects/Python/Images/Latin/png_latin/latin_book_40_Matthew/", "/home/max/Projects/Python/Images/Latin/png_latin_deskew/latin_book_40_Matthew/","/home/max/Projects/Python/Images/Latin/tif_latin_deskew/latin_book_40_Matthew/")
        #pp.deskewfiles("/home/max/Projects/Python/Images/Latin/png_latin/latin_book_41_Mark/", "/home/max/Projects/Python/Images/Latin/png_latin_deskew/latin_book_41_Mark/","/home/max/Projects/Python/Images/Latin/tif_latin_deskew/latin_book_41_Mark/")
    
    def actionResize_Latin_png(self):
        print("resizing Latin png files")
        #usage: pp.resizepngs(source, destination)
        self.latinresizepngDialog = qtw.QDialog()
        self.latinresizepng_ui = Ui_latinresizepngDialog()
        self.latinresizepng_ui.setupUi(self.latinresizepngDialog)
        self.latinresizepngDialog.show()

        self.latinresizepng_ui.SourceButton.clicked.connect(self.LatinResizePngDialog)
        self.latinresizepng_ui.DestinationButton.clicked.connect(self.DestLatinResizePngDialog)

        rsp = self.latinresizepngDialog.exec_()
        
        if self.latinresizepngDialog.Accepted:
            pp.resizepngs(self.latinresizepng_ui.SourceLineEdit.text(), self.latinresizepng_ui.DestinationLineEdit.text())
            print("completed creating indexed(BW) png")
        #pp.resizepngs(r"/home/max/Projects/Python/Images/Greek/png_latin_deskew/latin_book_40_Matthew/","/home/max/Projects/Python/Images/Greek/png_latin_resize/latin_book_40_Matthew/")
        #pp.resizepngs(r"/home/max/Projects/Python/Images/Latin/png_latin_deskew/latin_book_41_Mark/","/home/max/Projects/Python/Images/Latin/png_latin_resize/latin_book_41_Mark/")

    # Dialog Controllers

    def OpenPdfFileDialog(self):
        self.path = qtw.QFileDialog.getOpenFileName(self.ui.centralwidget,'Select pdf source file','','*.pdf')[0]

        if self.path:
            self.pdfx_ui.SourceLineEdit.setText(self.path)

    def DestPdfFileDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select destination folder"))
        
        if self.directory:
            self.pdfx_ui.DestinationLineEdit.setText(self.directory+r'/')

    def PdfForTifDialog(self):
        self.path = qtw.QFileDialog.getOpenFileName(self.ui.centralwidget,'Select pdf pages source file','','*.pdf')[0]

        if self.path:
            self.pdf4tif_ui.SourceLineEdit.setText(self.path)

    def DestPdfForTifDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select destination folder"))
        
        if self.directory:
            self.pdf4tif_ui.DestinationLineEdit.setText(self.directory+r'/')

    def PdfToTifDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select pdf pages source folder"))
        
        if self.directory:
            self.pdf2tif_ui.SourceLineEdit.setText(self.directory+r'/')

    def DestPdfToTifDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select destination folder"))
        
        if self.directory:
            self.pdf2tif_ui.DestinationLineEdit.setText(self.directory+r'/')
    
    def TifToMonoDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select pdf pages source folder"))
        
        if self.directory:
            self.tif2mono_ui.SourceLineEdit.setText(self.directory+r'/')

    def DestTifToMonoDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select destination folder"))
        
        if self.directory:
            self.tif2mono_ui.DestinationLineEdit.setText(self.directory+r'/')

    def MonoToPngDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select mono tif pages source folder"))
        
        if self.directory:
            self.mono2png_ui.SourceLineEdit.setText(self.directory+r'/')

    def DestMonoToPngDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select destination folder"))
        
        if self.directory:
            self.mono2png_ui.DestinationLineEdit.setText(self.directory+r'/')    
    
    def GreekMonoToPngDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select greek mono tif pages source folder"))
        
        if self.directory:
            self.greekmono2png_ui.SourceLineEdit.setText(self.directory+r'/')

    def GreekDestMonoToPngDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select destination folder"))
        
        if self.directory:
            self.greekmono2png_ui.DestinationLineEdit.setText(self.directory+r'/')

    def DeskewMonoDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select pdf pages source folder"))
        
        if self.directory:
            self.deskew_mono_ui.SourceLineEdit.setText(self.directory+r'/')

    def DestDeskewPngDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select destination folder"))
        
        if self.directory:
            self.deskew_mono_ui.DestPngLineEdit.setText(self.directory+r'/')

    def DestDeskewTifDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select destination folder"))
        
        if self.directory:
            self.deskew_mono_ui.DestTifLineEdit.setText(self.directory+r'/')

    def DeskewGreekMonoDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select greek pages source folder"))
        
        if self.directory:
            self.deskew_greekmono_ui.SourceLineEdit.setText(self.directory+r'/')
   
    def DestDeskewGreekPngDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select greek png pages destination folder"))
        
        if self.directory:
            self.deskew_greekmono_ui.DestPngLineEdit.setText(self.directory+r'/')

    def DestDeskewGreekTifDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select greek tif pages destination folder"))
        
        if self.directory:
            self.deskew_greekmono_ui.DestTifLineEdit.setText(self.directory+r'/')

    def GreekResizePngDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select greek pages source folder"))
        
        if self.directory:
            self.greekresizepng_ui.SourceLineEdit.setText(self.directory+r'/')

    def DestGreekResizePngDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select greek png pages destination folder"))
        
        if self.directory:
            self.greekresizepng_ui.DestinationLineEdit.setText(self.directory+r'/')

    def DeskewLatinMonoDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select latin pages source folder"))
        
        if self.directory:
            self.deskew_latinmono_ui.SourceLineEdit.setText(self.directory+r'/')

    def LatinMonoToPngDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select latin mono tif pages source folder"))
        
        if self.directory:
            self.latinmono2png_ui.SourceLineEdit.setText(self.directory+r'/')

    def LatinDestMonoToPngDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select destination folder"))
        
        if self.directory:
            self.latinmono2png_ui.DestinationLineEdit.setText(self.directory+r'/')

    def DestMonoToPngDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select destination folder"))
        
        if self.directory:
            self.mono2png_ui.DestinationLineEdit.setText(self.directory+r'/')

    def DeskewMonoDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select pdf pages source folder"))
        
        if self.directory:
            self.deskew_mono_ui.SourceLineEdit.setText(self.directory+r'/')

    def DestDeskewPngDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select destination folder"))
        
        if self.directory:
            self.deskew_mono_ui.DestPngLineEdit.setText(self.directory+r'/')

    def DestDeskewTifDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select destination folder"))
        
        if self.directory:
            self.deskew_mono_ui.DestTifLineEdit.setText(self.directory+r'/')

    def DestDeskewLatinPngDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select latin png pages destination folder"))
        
        if self.directory:
            self.deskew_latinmono_ui.DestPngLineEdit.setText(self.directory+r'/')

    def DestDeskewLatinTifDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select latin tif pages destination folder"))
        
        if self.directory:
            self.deskew_latinmono_ui.DestTifLineEdit.setText(self.directory+r'/')

    def LatinResizePngDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select latin pages source folder"))
        
        if self.directory:
            self.latinresizepng_ui.SourceLineEdit.setText(self.directory+r'/')

    def DestLatinResizePngDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select latin png pages destination folder"))
        
        if self.directory:
            self.latinresizepng_ui.DestinationLineEdit.setText(self.directory+r'/')
    
    def CropLanguagesDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select pdf pages source folder"))
        
        if self.directory:
            self.crop_languages_ui.SourceLineEdit.setText(self.directory+r'/')

    def BoxFolderDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select destination folder"))
        
        if self.directory:
            self.crop_languages_ui.BoxFolderLineEdit.setText(self.directory+r'/')

    def ElimFolderDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select destination folder"))
        
        if self.directory:
            self.crop_languages_ui.ElimFolderLineEdit.setText(self.directory+r'/')

    def DestGreekDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select destination folder"))
        
        if self.directory:
            self.crop_languages_ui.DestGreekLineEdit.setText(self.directory+r'/')

    def DestLatinDialog(self):
        self.directory = str(qtw.QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select destination folder"))

        if self.directory:
            self.crop_languages_ui.DestLatinLineEdit.setText(self.directory+r'/')


    # Mouse Controllers
    def mousePressEvent(self, event):
    
        if event.button() == Qt.LeftButton:
            '''self.refimg_xoffset = self.ui.RefImg.x()
            self.refimg_yoffset = self.ui.RefImg.y()
            (x,y) = event.pos()
            x = self.refimg_xoffset + x
            y = self.refimg_yoffset + y
            self.origin = QPoint(x,y)

            self.rubberBand.setGeometry(QRect(self.origin, QSize()))
            self.rubberBand.show()'''
            self.rubberBand = ResizableRubberBand(self)
            self.origin = QPoint(event.pos())
            self.rubberBand.setGeometry(QRect(self.origin, QSize()))
            self.rubberBand.show()

    def mouseMoveEvent(self, event):
    
        '''if not self.origin.isNull():
            self.refimg_xoffset = self.ui.RefImg.x()
            self.refimg_yoffset = self.ui.RefImg.y()
            (x,y) = event.pos()
            x = self.refimg_xoffset + x
            y = self.refimg_yoffset + y
            pos = QPoint(x,y)
            print(str(pos))
            self.rubberBand.setGeometry(QRect(self.origin, pos).normalized())'''
        if not self.origin.isNull():
            self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())

    def mouseReleaseEvent(self, event):
    
        if event.button() == Qt.LeftButton:
            geo = self.rubberBand.geometry()
            h = self.rubberBand.height()
            w = self.rubberBand.width()
            x = self.rubberBand.x()
            y = self.rubberBand.y()
            #x = self.rubberBand.x() + self.refimg_xoffset
            #y = self.rubberBand.y() + self.refimg_yoffset
            #print("selection geometry = " + geo)
            print("selection x = " + str(x))
            print("selection w = " + str(w))
            print("selection x+ w = " + str(x+w))
            print("selection y = " + str(y))
            print("selection h = " + str(h))
            print("selection y+h = " + str(y+h))
            print(x,":",x+w,",",y,":",y+h)
            #self.cropregion(x,y,w,h)'''
            self.currentQRect = self.rubberBand.geometry()
            #self.croppixmap = self.ui.RefImg.pixmap().copy(self.currentQRect)
            self.croppixmap = self.refscenepixmap(self.currentQRect)
            
            #self.croppixmap = self.refimgpixmap(self.currentQRect)
            #self.ui.Image.setPixmap(self.imagepixmap)
            
            #croppedimg = self.ui.Image[x:x+w,y:y+h]
            #self.rubberBand.hide()

    # Reference Image Edit Controllers
    def importRefImg(self):
        print("Importing current reference image path provided by get_session")
        if self.imgpath:
            print(self.imgpath)
            self.refimgpath = self.imgpath
            self.ui.RefImgLE.setText(os.path.basename(self.refimgpath))
            #with open(self.filename) as file:  
            self.showRefImg(self.refimgpath)
            #self.sortRefImgFiles()

    def loadRefImg(self):     
        print("Loading current reference image path provided by open file dialog")
        self.refimgpath = qtw.QFileDialog.getOpenFileName(self.ui.centralwidget, 'Open image file',self.refimgdir,'Images (*.png *.jpeg *.jpg *.bmp *.gif *.tif)')[0]
        if self.refimgpath:
            self.ui.RefImgLE.setText(os.path.basename(self.refimgpath))
            self.showRefImg(self.refimgpath)
            #self.sortRefImgFiles()       
        
        
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
                self.ui.RefImgLE.setText(os.path.basename(nextrefimgfilename))
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
            self.showRefImg(nextrefimgfilename)           
           

        else:
            # no file list found, load an image
            # self.OpenImageFileDialog()
            loadRefImg()

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
                self.ui.RefImgLE.setText(os.path.basename(prevrefimgfilename))
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
            self.showRefImg(prevrefimgfilename)            

            

        else:
            # no file list found, load an image
            # self.OpenImageFileDialog()
            self.loadRefImg()

    def reloadRefImg(self):
        if self.refimgpath:
            self.ui.RefImgLE.setText(os.path.basename(self.refimgpath))
            self.showRefImg(self.refimgpath)
            #self.sortRefImgFiles()  

    '''def OverwriteRefImg(self):
    
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
        file.close()'''

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
        self.refimgscale = RefImgzoomValue/100
        print(self.refimgscale)
    
    def on_RefImgzoom(self):
        seltext = self.ui.RefImgZoomComboBox.currentText()
        if self.ui.RefImgzoomslider.isEnabled():
            self.on_RefImgzoomslider()
        #elif seltext != "Best_Fit":
            #print("Best fit not selected")
        selnumtext = seltext.split(" ")
        print(selnumtext[0])
        self.refimgscale = float(selnumtext[0])/100
        print(self.refimgscale)
        
        self.resize_RefImg()

    def resize_RefImg(self):

        self.refimgsize = self.refimgpixmap.size()       
        print(self.refimgsize)
        self.origheight = self.refimgpixmap.height
        self.origwidth = self.refimgpixmap.width
        scaled_pixmap = self.refimgpixmap.scaled(self.refimgscale * self.refimgsize, qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)
        
        # Display scaled ref image file in Graphics View
        self.refscene.clear()
        self.refscenepixmap = qtw.QGraphicsPixmapItem()
        self.refscenepixmap.setPixmap(scaled_pixmap)
        self.refscene.addItem(self.refscenepixmap)

        #self.ui.RefImg.setPixmap(scaled_pixmap)
 
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

    def on_Imagezoomslider(self):
        #if self.ui.Zoomslider.isEnabled():
        zoomValue = self.ui.Imagezoomslider.value()
        self.ui.ImageZoomComboBox.setCurrentText(str(zoomValue) + " %")
        print(zoomValue)
        self.imagescale = zoomValue/100
        print(self.imagescale)
    
    def on_Imagezoom(self):
        seltext = self.ui.ImageZoomComboBox.currentText()
        if self.ui.Imagezoomslider.isEnabled():
            self.on_Imagezoomslider()
        #elif seltext != "Best_Fit":
            #print("Best fit not selected")
        selnumtext = seltext.split(" ")
        print(selnumtext[0])
        self.imagescale = float(selnumtext[0])/100
        print(self.imagescale)
        
        self.resize_Image()

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
            loadRefImg()

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
            loadRefImg()

    def reloadImage(self):
        if self.imagepath:
            self.ui.ImageLe.setText(os.path.basename(self.imagepath))
            self.showImage(self.imagepath)
            self.sortImgFiles()  

    def resize_Image(self):
        self.imagesize = self.imagepixmap.size()       
        self.origheight = self.imagepixmap.height
        self.origwidth = self.imagepixmap.width
        print("resizing " + str(self.imagesize))
        scaled_pixmap = self.imagepixmap.scaled(self.imagescale * self.imagesize, qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)
        self.ui.Image.setPixmap(scaled_pixmap)

    def ExportImage(self):
        pass

    def SaveImageAs(self):
        path = qtw.QFileDialog.getSaveFileName(
            self.ui.centralwidget, 'Save cropped tiff file', '',
            'Tiff files (*.tif)')[0]
        #my_Image = self.ui.Cropped.pixmap().toImage()
        my_Image = self.imagepixmap.toImage()
        # Write accepted ROI to correct folder/file
        buffer = qtc.QBuffer()
        buffer.open(qtc.QBuffer.ReadWrite)
        my_Image.save(buffer, "PNG")
        PILimage = pilimg.open(io.BytesIO(buffer.data()))
        outfile = path
        print("Generating: " + outfile)
        PILimage.save(outfile, "TIFF", dpi=(300,300), compression = "tiff_lzw")
        #PILimage.save(outfile, "TIFF", dpi=(300,300))
        filename = os.path.basename(path)
        self.ui.ImageLE.setText(filename)
        #file.close()
        RefImgchangesSaved = True
        
    def SaveImage(self):
        
        filename = self.ui.ImageLE.displayText()
        
        if self.workflowdir:
            path = self.workflowdir + "/" + filename
            
        else:
            path = qtw.QFileDialog.getSaveFileName(
                self.centralwidget, 'Save modified tif file', '',
                'Tif files (*.tif)')[0]
        
        #self.ui.Cropped.self.pixmap.save(path)
        my_Image = self.imagepixmap.toImage()
        #my_Image.save(path)
        buffer = qtc.QBuffer()
        buffer.open(qtc.QBuffer.ReadWrite)
        my_Image.save(buffer, "PNG")
        PILimage = pilimg.open(io.BytesIO(buffer.data()))
        outfile = path
        print("Generating: " + outfile)
        PILimage.save(outfile, "TIFF", dpi=(300,300), compression = "tiff_lzw")
        #self.imagepixmap.save(path)
        filename = os.path.basename(path)
        self.ui.ImageLE.setText(filename)
        #file.close()

        RefImgchangesSaved = True

    def OverwriteRefImg(self):
        path = self.refimgpath
        #filename = self.ui.RefImgLE.displayText()
        
        '''if self.worflowdir:
            path = self.workflowdir + "/" + filename
            
        else:
            path = qtw.QFileDialog.getSaveFileName(
                self.centralwidget, 'Save modified tif file', '',
                'Tif files (*.tif)')[0]'''
        
        #self.ui.Cropped.self.pixmap.save(path)
        my_Image = self.imagepixmap.toImage()
        #my_Image.save(path)
        buffer = qtc.QBuffer()
        buffer.open(qtc.QBuffer.ReadWrite)
        my_Image.save(buffer, "PNG")
        PILimage = pilimg.open(io.BytesIO(buffer.data()))
        outfile = path
        print("Generating: " + outfile)
        PILimage.save(outfile, "TIFF", dpi=(300,300), compression = "tiff_lzw")
        #self.imagepixmap.save(path)
        filename = os.path.basename(path)
        self.ui.RefImgLE.setText(filename)
        #file.close()

        RefImgchangesSaved = True

    def changed_Image(self):
        self.ImagechangesSaved = False

    def clip(self):
        # RefImg QRect
        print("This is the new clip method of the Pixler class")
        
        # Initialize RefImg QRect
        RefImg_qimage = qtg.QPixmap.toImage(self.ui.RefImg.pixmap())
        RefImg_qimage_size = RefImg_qimage.size()
        RefImg_xr = self.ui.RefImg.geometry().x()
        RefImg_yr = self.ui.RefImg.geometry().y()
        RefImg_wr = self.RefImg_width
        RefImg_hr = self.RefImg_height
        #RefImg_wr = self.ui.RefImg.pixmap().width()
        #RefImg_hr = self.ui.RefImg.pixmap().height()
        RefImg_qrect = QRect(RefImg_xr, RefImg_yr, RefImg_wr, RefImg_hr)
        print("Reference Image QRect = " + str(RefImg_qrect))

        # Initialize Scaled RefImg QRect
        RefImg_xs = 0
        RefImg_ys = 0
        RefImg_ws = 0
        RefImg_hs = 0
        RefImg_xs = RefImg_xr * self.refimgscale
        RefImg_ys = RefImg_yr * self.refimgscale
        RefImg_ws = RefImg_wr * self.refimgscale
        RefImg_hs = RefImg_hr * self.refimgscale
        RefImg_sqrect = QRect(RefImg_xs,RefImg_ys,RefImg_ws,RefImg_hs)
        print("Reference Image Scaled QRect = " + str(RefImg_sqrect))
        
        # ClipImg QRect

        # Get ClipImg QRect from event.pos()
        ClipImg_xc = self.rubberBand.x() 
        ClipImg_yc = self.rubberBand.y()
        ClipImg_wc = self.rubberBand.width()
        ClipImg_hc = self.rubberBand.height()
        ClipImg_cqrect = QRect(ClipImg_xc,ClipImg_yc,ClipImg_wc,ClipImg_hc)
        print("Reference Image Clipped QRect = " + str(ClipImg_cqrect))
        
        # Move ClipImg QRect to RefImg MainWindow origin(0,0)
        ClipImg_xm = self.rubberBand.x() - int(self.refimg_xoffset) 
        ClipImg_ym= self.rubberBand.y() - int(self.refimg_yoffset)
        ClipImg_wm = self.rubberBand.width()
        ClipImg_hm = self.rubberBand.height()
        ClipImg_mqrect = QRect(ClipImg_xm,ClipImg_ym,ClipImg_wm,ClipImg_hm)
        print("Crop Image Cropped2Main QRect = " + str(ClipImg_mqrect))
            
        # Upscale ClipImg QRect at RefImg MainWindow origin(0,0)
        ClipImg_xu = 0
        ClipImg_yu = 0
        ClipImg_wu = 0
        ClipImg_hu = 0
        ClipImg_xu = ClipImg_xm / self.refimgscale
        ClipImg_yu = ClipImg_ym / self.refimgscale
        ClipImg_wu = ClipImg_wm / self.refimgscale
        ClipImg_hu = ClipImg_hm / self.refimgscale
        ClipImg_uqrect = QRect(ClipImg_xu,ClipImg_yu,ClipImg_wu,ClipImg_hu)
        print("Crop Image Upscaled QRect = " + str(ClipImg_uqrect))

        # Show Cropped Image
        #self.ui.RefImg.setPixmap(self.origpixmap)
        self.ui.Image.setAlignment(qtc.Qt.AlignLeft | qtc.Qt.AlignTop)
        self.clippixmap = self.refimgpixmap.copy(ClipImg_uqrect)
        print("Clipped Image Size = " + str(self.clippixmap.size()))       
        #self.croppixmap = self.ui.RefImg.pixmap().copy(ClipImg_uqrect)
        #print("Cropped Image Size = " + str(self.ui.RefImg.pixmap().size()))
        self.imagepixmap = self.clippixmap
        self.ui.Image.setPixmap(self.imagepixmap)
        self.resize_Image()
        self.rubberBand.hide()

    def eraser(self):
        # RefImg QRect
        print("This is the new eraser method of the Pixler class")
        
        # Initialize RefImg QRect
        RefImg_qimage = qtg.QPixmap.toImage(self.ui.RefImg.pixmap())
        RefImg_qimage_size = RefImg_qimage.size()
        RefImg_xr = self.ui.RefImg.geometry().x()
        RefImg_yr = self.ui.RefImg.geometry().y()
        RefImg_wr = self.RefImg_width
        RefImg_hr = self.RefImg_height
        #RefImg_wr = self.ui.RefImg.pixmap().width()
        #RefImg_hr = self.ui.RefImg.pixmap().height()
        RefImg_qrect = QRect(RefImg_xr, RefImg_yr, RefImg_wr, RefImg_hr)
        print("Reference Image QRect = " + str(RefImg_qrect))

        # Initialize Scaled RefImg QRect
        RefImg_xs = 0
        RefImg_ys = 0
        RefImg_ws = 0
        RefImg_hs = 0
        RefImg_xs = RefImg_xr * self.refimgscale
        RefImg_ys = RefImg_yr * self.refimgscale
        RefImg_ws = RefImg_wr * self.refimgscale
        RefImg_hs = RefImg_hr * self.refimgscale
        RefImg_sqrect = QRect(RefImg_xs,RefImg_ys,RefImg_ws,RefImg_hs)
        print("Reference Image Scaled QRect = " + str(RefImg_sqrect))
        
        # CropImg QRect

        # Get CropImg QRect from event.pos()
        CropImg_xc = self.rubberBand.x() 
        CropImg_yc = self.rubberBand.y()
        CropImg_wc = self.rubberBand.width()
        CropImg_hc = self.rubberBand.height()
        CropImg_cqrect = QRect(CropImg_xc,CropImg_yc,CropImg_wc,CropImg_hc)
        print("Reference Image Cropped QRect = " + str(CropImg_cqrect))
        
        # Move CropImg QRect to RefImg MainWindow origin(0,0)
        CropImg_xm = self.rubberBand.x() - int(self.refimg_xoffset) 
        CropImg_ym= self.rubberBand.y() - int(self.refimg_yoffset)
        CropImg_wm = self.rubberBand.width()
        CropImg_hm = self.rubberBand.height()
        CropImg_mqrect = QRect(CropImg_xm,CropImg_ym,CropImg_wm,CropImg_hm)
        print("Crop Image Cropped2Main QRect = " + str(CropImg_mqrect))
            
        # Upscale CropImg QRect at RefImg MainWindow origin(0,0)
        CropImg_xu = 0
        CropImg_yu = 0
        CropImg_wu = 0
        CropImg_hu = 0
        CropImg_xu = CropImg_xm / self.refimgscale
        CropImg_yu = CropImg_ym / self.refimgscale
        CropImg_wu = CropImg_wm / self.refimgscale
        CropImg_hu = CropImg_hm / self.refimgscale
        CropImg_uqrect = QRect(CropImg_xu,CropImg_yu,CropImg_wu,CropImg_hu)
        print("Crop Image Upscaled QRect = " + str(CropImg_uqrect))

        # Show Cropped Image
        #self.ui.RefImg.setPixmap(self.origpixmap)
        self.ui.Image.setAlignment(qtc.Qt.AlignLeft | qtc.Qt.AlignTop)
        self.croppixmap = self.refimgpixmap.copy(CropImg_uqrect)
        print("Cropped Image Size = " + str(self.croppixmap.size()))       
        #self.croppixmap = self.ui.RefImg.pixmap().copy(CropImg_uqrect)
        #print("Cropped Image Size = " + str(self.ui.RefImg.pixmap().size()))
        self.imagepixmap = self.croppixmap
        self.ui.Image.setPixmap(self.imagepixmap)
        self.resize_Image()
        self.rubberBand.hide()

    def crop(self):
        # RefImg QRect
        print("This is the new crop method of the Pixler class")
        
        # Initialize RefImg QRect
        #self.refimgpixmap
        RefImg_qimage = qtg.QPixmap.toImage(self.refscene.pixmap())
        RefImg_qimage_size = RefImg_qimage.size()
        RefImg_xr = self.ui.RefImg.geometry().x()
        RefImg_yr = self.ui.RefImg.geometry().y()
        RefImg_wr = self.RefImg_width
        RefImg_hr = self.RefImg_height
        #RefImg_wr = self.ui.RefImg.pixmap().width()
        #RefImg_hr = self.ui.RefImg.pixmap().height()
        RefImg_qrect = QRect(RefImg_xr, RefImg_yr, RefImg_wr, RefImg_hr)
        print("Reference Image QRect = " + str(RefImg_qrect))

        # Initialize Scaled RefImg QRect
        RefImg_xs = 0
        RefImg_ys = 0
        RefImg_ws = 0
        RefImg_hs = 0
        RefImg_xs = RefImg_xr * self.refimgscale
        RefImg_ys = RefImg_yr * self.refimgscale
        RefImg_ws = RefImg_wr * self.refimgscale
        RefImg_hs = RefImg_hr * self.refimgscale
        RefImg_sqrect = QRect(RefImg_xs,RefImg_ys,RefImg_ws,RefImg_hs)
        print("Reference Image Scaled QRect = " + str(RefImg_sqrect))
        
        # CropImg QRect

        # Get CropImg QRect from event.pos()
        CropImg_xc = self.rubberBand.x() 
        CropImg_yc = self.rubberBand.y()
        CropImg_wc = self.rubberBand.width()
        CropImg_hc = self.rubberBand.height()
        CropImg_cqrect = QRect(CropImg_xc,CropImg_yc,CropImg_wc,CropImg_hc)
        print("Reference Image Cropped QRect = " + str(CropImg_cqrect))
        
        # Move CropImg QRect to RefImg MainWindow origin(0,0)
        CropImg_xm = self.rubberBand.x() - int(self.refimg_xoffset) 
        CropImg_ym= self.rubberBand.y() - int(self.refimg_yoffset)
        CropImg_wm = self.rubberBand.width()
        CropImg_hm = self.rubberBand.height()
        CropImg_mqrect = QRect(CropImg_xm,CropImg_ym,CropImg_wm,CropImg_hm)
        print("Crop Image Cropped2Main QRect = " + str(CropImg_mqrect))
            
        # Upscale CropImg QRect at RefImg MainWindow origin(0,0)
        CropImg_xu = 0
        CropImg_yu = 0
        CropImg_wu = 0
        CropImg_hu = 0
        CropImg_xu = CropImg_xm / self.refimgscale
        CropImg_yu = CropImg_ym / self.refimgscale
        CropImg_wu = CropImg_wm / self.refimgscale
        CropImg_hu = CropImg_hm / self.refimgscale
        CropImg_uqrect = QRect(CropImg_xu,CropImg_yu,CropImg_wu,CropImg_hu)
        print("Crop Image Upscaled QRect = " + str(CropImg_uqrect))

        # Show Cropped Image
        #self.ui.RefImg.setPixmap(self.origpixmap)
        self.ui.Image.setAlignment(qtc.Qt.AlignLeft | qtc.Qt.AlignTop)
        self.croppixmap = self.refimgpixmap.copy(CropImg_uqrect)
        print("Cropped Image Size = " + str(self.croppixmap.size()))       
        #self.croppixmap = self.ui.RefImg.pixmap().copy(CropImg_uqrect)
        #print("Cropped Image Size = " + str(self.ui.RefImg.pixmap().size()))
        self.imagepixmap = self.croppixmap
        self.ui.Image.setPixmap(self.imagepixmap)
        self.resize_Image()
        self.rubberBand.hide()


    def actionGimpEdit(self):
        #gimp_cmd = "/usr/bin/flatpak run --branch=stable --arch=aarch64 --command=gimp-2.10 --file-forwarding org.gimp.GIMP"
        gimp_cmd = "/usr/bin/flatpak run --branch=stable --arch=aarch64 --command=gimp-2.10 --file-forwarding org.gimp.GIMP @@ " + self.refimgpath + " @@"
        
        '''if 'self.refimgpath' in locals():
            gimp_cmd = "/usr/bin/flatpak run --branch=stable --arch=aarch64 --command=gimp-2.10 --file-forwarding org.gimp.GIMP @@ " + self.refimgpath + " @@"
            print(self.refimgpath)
        else:
            gimp_cmd = "/usr/bin/flatpak run --branch=stable --arch=aarch64 --command=gimp-2.10 --file-forwarding org.gimp.GIMP" '''       
        
        os.system(gimp_cmd)
    
    def deskewRefImg(self):
        print("Deskewing current reference image")
        if self.refimgpath != "":
            pp.deskewimage(self.refimgpath)
            print("Reloading deskewed image")
            self.reloadRefImg()
        print("Deskew current image complete")
    
    '''def deskewRefImgold(self):
        print("Auto deskewing reference image")
        self.workflowdir = self.pixerpagesdeskewdir
        # Calculate skew angle of an image
        def getSkewAngle(cvImage) -> float:
            # Prep image, copy, convert to gray scale, blur, and threshold
            newImage = cvImage.copy()
            gray = cv2.cvtColor(newImage, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (9, 9), 0)
            thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

            # Apply dilate to merge text into meaningful lines/paragraphs.
            # Use larger kernel on X axis to merge characters into single line, cancelling out any spaces.
            # But use smaller kernel on Y axis to separate between different blocks of text
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 5))
            dilate = cv2.dilate(thresh, kernel, iterations=5)

            # Find all contours
            dilated, contours, hierarchy = cv2.findContours(dilate, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            contours = sorted(contours, key = cv2.contourArea, reverse = True)

            # Find largest contour and surround in min area box
            largestContour = contours[0]
            minAreaRect = cv2.minAreaRect(largestContour)

            # Determine the angle. Convert it to the value that was originally used to obtain skewed image
            angle = minAreaRect[-1]
            if angle < -45:
                angle = 90 + angle
            return -1.0 * angle

        def deskewRefImg(self):

        # Rotate the image around its center
        def rotateImage(cvImage, angle: float):
            newImage = cvImage.copy()
            (h, w) = newImage.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            newImage = cv2.warpAffine(newImage, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            return newImage

        # Deskew image
        def deskew(cvImage):
            angle = getSkewAngle(cvImage)
            # show the angle info
            print(filename + "[INFO] angle: {:.3f}".format(angle))
            return rotateImage(cvImage, -1.0 * angle)
           
        if self.refimgpath != "":
        
            filestr = os.path.basename(self.refimgpath)
            filesplit = os.path.splitext(filestr)
            filename = filesplit[0]
            fileext = filesplit[1]

            image = cv2.imread(self.refimgpath)
            print("Converting image to cv2 image")
            newImage = deskew(image)

            #print(filename + "[INFO] angle: {:.3f}".format(angle))

            #write rotated file to destination folder
            PILimage = pilimg.fromarray(newImage)
            thresh = 127
            fn = lambda x : 255 if x > thresh else 0
            PIL_BWimage = PILimage.convert('L').point(fn, mode='1')
            
            outfile = self.workflowdir + "/" + filename
            print("Converting cv2 image to PIL image: " + outfile)
            #png_outfile = self.imgpath + self.ui.ImageLe.text()

            #self.showImage(self.imagepath)
            print("Previewing deskewed image")
            rqimage = pilqimg.ImageQt(PIL_BWimage)
            rpixmap = qtg.QPixmap.fromImage(rqimage)
            self.ui.Image.setPixmap(rpixmap)
            self.imagedir = os.path.dirname(outfile)
            self.ui.ImageLE.setText(os.path.basename(self.refimgpath))
            self.imagepixmap = rpixmap
            self.on_Imagezoom()

            try:
                print("Generating: " + outfile)
                PIL_BWimage.save(outfile)
                
                #print("Generating: " + png_outfile)
                #PIL_BWimage.save(png_outfile, "PNG", dpi=(300,300))
                #my_img_resized.save(outfile, "PNG")

            except Exception as e:
                print(e)
            
            print("Deskew complete")'''

    def initcvimg(self):
        print("RefImg path = " + self.refimgpath)
        self.cvimg = cv2.imread(self.refimgpath, 1)
        '''if self.cvimg.shape[0] / self.cvimg.shape[1] < 0.76:
            self.cvimg_width = 1100
            self.cvimg_height = int(self.cvimg_width * self.cvimg.shape[0] / self.cvimg.shape[1])
        else:
            self.cvimg_height = 700
            self.cvimg_width = int(self.cvimg_height * self.cvimg.shape[1] / self.cvimg.shape[0])

        self.cvimg = cv2.resize(self.cvimg, (self.cvimg_width, self.cvimg_height))'''
        #self.cvimg_copy = deepcopy(self.cvimg)
        #self.grand_img_copy = deepcopy(self.cvimg)

        #self.cvimg_name = self.refimgpath.split('/')[-1].split(".")[0]
        #self.cvimg_format = self.refimgpath('/')[-1].split(".")[1]

        #self.cvleft, self.cvright, self.cvtop, self.cvbottom = None, None, None, None

    def rotateRefImg(self):           
        self.workflowdir = self.pixerpagesrotatedir
        def on_Spinner():
            self.rotateDialog_ui.Sliderhorizontal.setValue(self.rotateDialog_ui.SliderspinBox.value())
            angle = self.rotateDialog_ui.Sliderhorizontal.value()
            print("New Rotation Angle = " + str(angle) + " degrees")
            self.rotatedpixmap = self.ui.RefImg.pixmap().transformed(qtg.QTransform().rotate(angle))
            self.ui.Image.setPixmap(self.rotatedpixmap)

        def on_Slider():
            self.rotateDialog_ui.SliderspinBox.setValue(self.rotateDialog_ui.Sliderhorizontal.value())
            angle = self.rotateDialog_ui.SliderspinBox.value()

        def accept():
            print("Rotating Original Reference Image")
            angle = self.rotateDialog_ui.SliderspinBox.value()
            self.imagepixmap = self.origpixmap.transformed(qtg.QTransform().rotate(angle))
            self.ui.Image.setPixmap(self.imagepixmap)
            self.ui.ImageLE.setText(os.path.basename(self.refimgpath))
            self.on_Imagezoom()

        def reject():
            print("Rotation cancelled")
            self.ui.Image.clear()

        self.rotateDialog = qtw.QDialog()
        self.rotateDialog_ui = Ui_SliderDialog()
        self.rotateDialog_ui.setupUi(self.rotateDialog)
        self.rotateDialog.show()
        
        '''Configure slider to adjust rotation angle (0:360)'''
        self.rotateDialog_ui.Sliderhorizontal.setEnabled(True)
        self.rotateDialog_ui.Sliderlabel.setEnabled(True)
        self.rotateDialog_ui.Sliderlabel.setText("Adjust rotation angle from 0 to 360 degrees")
        self.rotateDialog_ui.Sliderhorizontal.setMinimum(0)
        self.rotateDialog_ui.Sliderhorizontal.setMaximum(360)
        self.rotateDialog_ui.Sliderhorizontal.setSingleStep(1)
        self.rotateDialog_ui.Sliderhorizontal.setPageStep(15)
        self.rotateDialog_ui.Sliderhorizontal.setProperty("value", 180)
        self.rotateDialog_ui.Sliderhorizontal.setSliderPosition(180)
        self.rotateDialog_ui.Sliderhorizontal.setOrientation(Qt.Horizontal)
        self.rotateDialog_ui.Sliderhorizontal.setInvertedAppearance(False)
        self.rotateDialog_ui.SliderspinBox.setEnabled(True)
        self.rotateDialog_ui.SliderspinBox.setMinimum(0)
        self.rotateDialog_ui.SliderspinBox.setMaximum(360)
        self.rotateDialog_ui.SliderspinBox.setSingleStep(1)
        self.rotateDialog_ui.SliderspinBox.setValue(180)
        self.rotateDialog_ui.SliderspinBox.setSuffix(" deg")
        self.rotateDialog_ui.Sliderhorizontal.valueChanged.connect(on_Slider)
        self.rotateDialog_ui.SliderspinBox.valueChanged.connect(on_Spinner)
        self.rotateDialog_ui.SliderbuttonBox.accepted.connect(accept)
        self.rotateDialog_ui.SliderbuttonBox.rejected.connect(reject)
        #self.initcvimg()

    def rotateRefImg90CW(self):
        self.workflowdir = self.pixerpagesrotatedir
        # Reading an image in default mode
        src = cv2.imread(self.refimgpath)
        
        # Using cv2.ROTATE_90_CLOCKWISE rotate
        # by 90 degrees clockwise
        newImage = cv2.rotate(src, cv2.ROTATE_90_CLOCKWISE)
        
        # Displaying the image
        #write rotated file to destination folder
        PILimage = pilimg.fromarray(newImage)
        thresh = 127
        fn = lambda x : 255 if x > thresh else 0
        PIL_BWimage = PILimage.convert('L').point(fn, mode='1')

        outfile = self.pixerpagesrotatedir + "/" + os.path.basename(self.refimgpath) 
        print("Converting cv2 image to PIL image: " + outfile)
        self.imagepath = outfile
        
        #self.showImage(self.imagepath)
        print("Reloading rotated image")
        rqimage = pilqimg.ImageQt(PIL_BWimage)
        rpixmap = qtg.QPixmap.fromImage(rqimage)
        self.ui.Image.setPixmap(rpixmap)
        self.imagedir = os.path.dirname(outfile)
        self.ui.ImageLE.setText(os.path.basename(self.refimgpath))
        self.imagepixmap = rpixmap
        self.on_Imagezoom()
        #png_outfile = self.imgpath + self.ui.ImageLe.text()
            
        # Save workflow image to Pixler rotated workflow folder
        try:
            print("Generating: " + outfile)
            PIL_BWimage.save(outfile)
            
            #print("Generating: " + png_outfile)
            #PIL_BWimage.save(png_outfile, "PNG", dpi=(300,300))
            #my_img_resized.save(outfile, "PNG")

        except Exception as e:
            print(e)
        

        print("Auto rotation by 90 degrees clockwise complete")

    def rotateRefImg90CCW(self):
        self.workflowdir = self.pixerpagesrotatedir
        # Reading an image in default mode
        src = cv2.imread(self.refimgpath)

        # Using cv2.ROTATE_90_CLOCKWISE rotate
        # by 90 degrees clockwise
        newImage = cv2.rotate(src, cv2.ROTATE_90_COUNTERCLOCKWISE)
        
        # Displaying the image

        #write rotated file to destination folder
        PILimage = pilimg.fromarray(newImage)
        thresh = 127
        fn = lambda x : 255 if x > thresh else 0
        PIL_BWimage = PILimage.convert('L').point(fn, mode='1')
        
        outfile = self.pixerpagesrotatedir + "/" + os.path.basename(self.refimgpath) 
        print("Converting cv2 image to PIL image: " + outfile)
        self.imagepath = outfile
        
        #self.showImage(self.imagepath)
        print("Reloading rotated image")
        rqimage = pilqimg.ImageQt(PIL_BWimage)
        rpixmap = qtg.QPixmap.fromImage(rqimage)
        self.ui.Image.setPixmap(rpixmap)
        self.imagedir = os.path.dirname(outfile)
        self.ui.ImageLE.setText(os.path.basename(self.refimgpath))
        self.imagepixmap = rpixmap
        self.on_Imagezoom()
        #png_outfile = self.imgpath + self.ui.ImageLe.text()
            
        # Save workflow image to Pixler rotated workflow folder
        try:
            print("Generating: " + outfile)
            PIL_BWimage.save(outfile)
            
            #print("Generating: " + png_outfile)
            #PIL_BWimage.save(png_outfile, "PNG", dpi=(300,300))
            #my_img_resized.save(outfile, "PNG")

        except Exception as e:
            print(e)
            
        print("Auto rotation by 90 degrees counter-clockwise complete")

    def rotateRefImg180CW(self):
        self.workflowdir = self.pixerpagesrotatedir
        # Reading an image in default mode
        src = cv2.imread(self.refimgpath)

        # Using cv2.ROTATE_180 rotate by 
        # 180 degrees clockwise
        newImage = cv2.rotate(src, cv2.ROTATE_180)

                # Displaying the image

        #write rotated file to destination folder
        PILimage = pilimg.fromarray(newImage)
        thresh = 127
        fn = lambda x : 255 if x > thresh else 0
        PIL_BWimage = PILimage.convert('L').point(fn, mode='1')
        
        outfile = self.pixerpagesrotatedir + "/" + os.path.basename(self.refimgpath) 
        print("Converting cv2 image to PIL image: " + outfile)
        self.imagepath = outfile
        
        #self.showImage(self.imagepath)
        print("Reloading rotated image")
        rqimage = pilqimg.ImageQt(PIL_BWimage)
        rpixmap = qtg.QPixmap.fromImage(rqimage)
        self.ui.Image.setPixmap(rpixmap)
        self.imagedir = os.path.dirname(outfile)
        self.ui.ImageLE.setText(os.path.basename(self.refimgpath))
        self.imagepixmap = rpixmap
        self.on_Imagezoom()
        #png_outfile = self.imgpath + self.ui.ImageLe.text()
            
        # Save workflow image to Pixler rotated workflow folder
        try:
            print("Generating: " + outfile)
            PIL_BWimage.save(outfile)
            
            #print("Generating: " + png_outfile)
            #PIL_BWimage.save(png_outfile, "PNG", dpi=(300,300))
            #my_img_resized.save(outfile, "PNG")

        except Exception as e:
            print(e)
        print("Auto rotation by 180 degrees clockwise complete")


# Start of Images class
# From main.py to use?
    # from main.py _init_
        '''self.img = QPixmap(qimage2ndarray.array2qimage(cv2.cvtColor(self.img_class.img, cv2.COLOR_BGR2RGB)))
        # display img
        self.gv = self.findChild(QGraphicsView, "gv")
        self.scene = QGraphicsScene()
        self.scene_img = self.scene.addPixmap(self.img)
        self.gv.setScene(self.scene)

        # zoom in
        self.zoom_moment = False
        self._zoom = 0

        # misc
        self.rotate_value, self.brightness_value, self.contrast_value, self.saturation_value = 0, 0, 1, 0
        self.flip = [False, False]
        self.zoom_factor = 1'''



class Images:
    def __init__(self, img):
        self.img = cv2.imread(img, 1)
        if self.img.shape[0] / self.img.shape[1] < 0.76:
            self.img_width = 1100
            self.img_height = int(self.img_width * self.img.shape[0] / self.img.shape[1])
        else:
            self.img_height = 700
            self.img_width = int(self.img_height * self.img.shape[1] / self.img.shape[0])

        self.img = cv2.resize(self.img, (self.img_width, self.img_height))
        self.img_copy = deepcopy(self.img)
        self.grand_img_copy = deepcopy(self.img)

        self.img_name = img.split('/')[-1].split(".")[0]
        self.img_format = img.split('/')[-1].split(".")[1]

        self.left, self.right, self.top, self.cvbottom = None, None, None, None

        # self.bypass_censorship()

    def auto_contrast(self):
        clip_hist_percent = 20
        gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)

        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist_size = len(hist)
        accumulator = [float(hist[0])]
        for index in range(1, hist_size):
            accumulator.append(accumulator[index - 1] + float(hist[index]))
        maximum = accumulator[-1]
        clip_hist_percent *= (maximum / 100.0)
        clip_hist_percent /= 2.0
        minimum_gray = 0
        while accumulator[minimum_gray] < clip_hist_percent:
            minimum_gray += 1
        maximum_gray = hist_size - 1
        while accumulator[maximum_gray] >= (maximum - clip_hist_percent):
            maximum_gray -= 1
        alpha = 255 / (maximum_gray - minimum_gray)
        beta = -minimum_gray * alpha

        self.img = cv2.convertScaleAbs(self.img, alpha=alpha, beta=beta)

    def auto_sharpen(self):
        self.img = cv2.detailEnhance(self.img, sigma_s=10, sigma_r=0.3)

    def auto_cartoon(self, style=0):
        edges1 = cv2.bitwise_not(cv2.Canny(self.img, 100, 200))
        gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, 5)
        edges2 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 7, 7)
        dst = cv2.edgePreservingFilter(self.img, flags=2, sigma_s=64, sigma_r=0.25)

        if not style:
            # less blurry
            self.img = cv2.bitwise_and(dst, dst, mask=edges1)
        else:
            # more blurry
            self.img = cv2.bitwise_and(dst, dst, mask=edges2)

    def auto_invert(self):
        self.img = cv2.bitwise_not(self.img)

    def change_b_c(self, alpha=1, beta=0):
        # contrast from 0 to 3, brightness from -100 to 100
        self.img = cv2.convertScaleAbs(self.img, alpha=alpha, beta=beta)

    def change_saturation(self, value):
        # -300 to 300
        img_hsv = cv2.cvtColor(self.img, cv2.COLOR_BGR2HSV).astype("float32")
        (h, s, v) = cv2.split(img_hsv)
        s += value
        s = np.clip(s, 0, 255)
        img_hsv = cv2.merge([h, s, v])
        self.img = cv2.cvtColor(img_hsv.astype("uint8"), cv2.COLOR_HSV2BGR)

    def remove_color(self, color):
        h = color.lstrip('#')
        color = np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)])

        img_hsv = cv2.cvtColor(self.img, cv2.COLOR_BGR2HSV).astype("float32")
        low = np.array([color[0] - 15, 0, 20])
        high = np.array([color[0] + 15, 255, 255])
        mask = cv2.inRange(img_hsv, low, high)
        img_hsv[mask > 0] = (0, 0, 255)
        self.img = cv2.cvtColor(img_hsv.astype("uint8"), cv2.COLOR_HSV2BGR)

    def crop_img(self, left, right, top, bottom):
        self.img = self.img[left:right, top:bottom]

    def rotate_img(self, angle, crop=False, flip=[False, False]):
        self.reset(flip)
        if not crop:
            self.img = cv2.resize(self.img, (0, 0), fx=0.5, fy=0.5)
            w, h = self.img.shape[1], self.img.shape[0]
        else:
            w, h = self.img_width, self.img_height

        self.img = ndimage.rotate(self.img, angle)

        angle = math.radians(angle)
        quadrant = int(math.floor(angle / (math.pi / 2))) & 3
        sign_alpha = angle if ((quadrant & 1) == 0) else math.pi - angle
        alpha = (sign_alpha % math.pi + math.pi) % math.pi
        bb_w = w * math.cos(alpha) + h * math.sin(alpha)
        bb_h = w * math.sin(alpha) + h * math.cos(alpha)
        gamma = math.atan2(bb_w, bb_w) if (w < h) else math.atan2(bb_w, bb_w)
        delta = math.pi - alpha - gamma
        length = h if (w < h) else w
        d = length * math.cos(alpha)
        a = d * math.sin(alpha) / math.sin(delta)
        y = a * math.cos(gamma)
        x = y * math.tan(gamma)
        wr, hr = bb_w - 2 * x, bb_h - 2 * y

        midpoint = (np.array(self.img.shape[:-1]) // 2)[::-1]
        half_w, half_h = wr // 2, hr // 2
        self.left, self.right, self.top, self.bottom = int(midpoint[0] - half_w), int(midpoint[0] + half_w), \
                                                       int(midpoint[1] - half_h), int(midpoint[1] + half_h)

    def detect_face(self):
        face_cascade = cv2.CascadeClassifier('data/haarcascade_frontalface_alt2.xml')
        # eye_cascade = cv2.CascadeClassifier('data/haarcascade_eye.xml')

        gray_scale_img = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
        face_coord = face_cascade.detectMultiScale(gray_scale_img)

        return face_coord

    def bypass_censorship(self):
        width = self.img.shape[1]
        height = self.img.shape[0]
        smaller_img = cv2.resize(self.img, (width // 2, height // 2))
        image = np.zeros(self.img.shape, np.uint8)

        try:
            image[:height // 2, :width // 2] = cv2.rotate(smaller_img, cv2.cv2.ROTATE_180)
            image[height // 2:, :width // 2] = smaller_img
            image[height // 2:, width // 2:] = cv2.rotate(smaller_img, cv2.cv2.ROTATE_180)
            image[:height // 2, width // 2:] = smaller_img
        except:
            try:
                image[:height // 2, :width // 2] = cv2.rotate(smaller_img, cv2.cv2.ROTATE_180)
                image[height // 2 + 1:, :width // 2] = smaller_img
                image[height // 2 + 1:, width // 2:] = cv2.rotate(smaller_img, cv2.cv2.ROTATE_180)
                image[:height // 2, width // 2:] = smaller_img
            except:
                image[:height // 2, :width // 2] = cv2.rotate(smaller_img, cv2.cv2.ROTATE_180)
                image[height // 2:, :width // 2] = smaller_img
                image[height // 2:, width // 2 + 1:] = cv2.rotate(smaller_img, cv2.cv2.ROTATE_180)
                image[:height // 2, width // 2 + 1:] = smaller_img
        self.img = image

    def save_img(self, file):
        cv2.imwrite(file, self.img)

    def reset(self, flip=None):
        if flip is None:
            flip = [False, False]
        self.img = deepcopy(self.img_copy)
        if flip[0]:
            self.img = cv2.flip(self.img, 0)
        if flip[1]:
            self.img = cv2.flip(self.img, 1)

    def grand_reset(self):
        self.img = deepcopy(self.grand_img_copy)
        self.img_copy = deepcopy(self.grand_img_copy)

class Brightness(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi(f"{pathlib.Path(__file__).parent.absolute()}/ui/brightness_btn.ui", self)

        self.frame = self.findChild(QFrame, "frame")
        self.vbox2 = self.findChild(QVBoxLayout, "vbox2")
        self.y_btn = self.findChild(QPushButton, "y_btn")
        self.y_btn.setIcon(QIcon(f"{pathlib.Path(__file__).parent.absolute()}/icon/check.png"))
        self.y_btn.setStyleSheet("QPushButton{border: 0px solid;}")
        self.y_btn.setIconSize(QSize(70, 70))
        self.n_btn = self.findChild(QPushButton, "n_btn")
        self.n_btn.setIcon(QIcon(f"{pathlib.Path(__file__).parent.absolute()}/icon/cross.png"))
        self.n_btn.setStyleSheet("QPushButton{border: 0px solid;}")
        self.n_btn.setIconSize(QSize(70, 70))

        self.pten = self.findChild(QPushButton, "pten")
        self.pten.setStyleSheet("QPushButton{border: 0px solid;}")
        self.mten = self.findChild(QPushButton, "mten")
        self.mten.setStyleSheet("QPushButton{border: 0px solid;}")

class Filter(QWidget):
    def __init__(self, main):
        super().__init__()
        uic.loadUi(f"{pathlib.Path(__file__).parent.absolute()}/ui/filter_frame.ui", self)
        self.img_class, self.update_img, self.base_frame, self.vbox = \
            main.img_class, main.update_img, main.base_frame, main.vbox

        self.frame = self.findChild(QFrame, "frame")
        self.contrast_btn = self.findChild(QPushButton, "contrast_btn")
        self.sharpen_btn = self.findChild(QPushButton, "sharpen_btn")
        self.cartoon_btn = self.findChild(QPushButton, "cartoon_btn")
        self.cartoon_btn1 = self.findChild(QPushButton, "cartoon_btn2")
        self.invert_btn = self.findChild(QPushButton, "invert_btn")
        self.bypass_btn = self.findChild(QPushButton, "bypass_btn")

        self.y_btn = self.findChild(QPushButton, "y_btn")
        self.y_btn.setIcon(QIcon(f"{pathlib.Path(__file__).parent.absolute()}/icon/check.png"))
        self.y_btn.setStyleSheet("QPushButton{border: 0px solid;}")
        self.y_btn.setIconSize(QSize(60, 60))
        self.n_btn = self.findChild(QPushButton, "n_btn")
        self.n_btn.setIcon(QIcon(f"{pathlib.Path(__file__).parent.absolute()}/icon/cross.png"))
        self.n_btn.setStyleSheet("QPushButton{border: 0px solid;}")
        self.n_btn.setIconSize(QSize(60, 60))

        self.y_btn.clicked.connect(lambda _: self.click_y())
        self.n_btn.clicked.connect(lambda _: self.click_n())
        self.contrast_btn.clicked.connect(lambda _: self.click_contrast())
        self.sharpen_btn.clicked.connect(lambda _: self.click_sharpen())
        self.cartoon_btn.clicked.connect(lambda _: self.click_cartoon())
        self.cartoon_btn1.clicked.connect(lambda _: self.click_cartoon1())
        self.invert_btn.clicked.connect(lambda _: self.click_invert())
        self.bypass_btn.clicked.connect(lambda _: self.click_bypass())

    def click_contrast(self):
        self.img_class.auto_contrast()
        self.update_img()
        self.contrast_btn.clicked.disconnect()

    def click_sharpen(self):
        self.img_class.auto_sharpen()
        self.update_img()
        self.sharpen_btn.clicked.disconnect()

    def click_cartoon(self):
        self.img_class.auto_cartoon()
        self.update_img()
        self.cartoon_btn.clicked.disconnect()

    def click_cartoon1(self):
        self.img_class.auto_cartoon(1)
        self.update_img()
        self.cartoon_btn1.clicked.disconnect()

    def click_invert(self):
        self.img_class.auto_invert()
        self.update_img()
        self.invert_btn.clicked.disconnect()

    def click_bypass(self):
        self.img_class.bypass_censorship()
        self.update_img()
        self.bypass_btn.clicked.disconnect()

    def click_y(self):
        self.frame.setParent(None)
        self.img_class.img_copy = deepcopy(self.img_class.img)
        self.img_class.grand_img_copy = deepcopy(self.img_class.img)
        self.vbox.addWidget(self.base_frame)

    def click_n(self):
        if not np.array_equal(self.img_class.grand_img_copy, self.img_class.img):
            msg = QMessageBox.question(self, "Cancel edits", "Confirm to discard all the changes?   ",
                                       QMessageBox.Yes | QMessageBox.No)
            if msg != QMessageBox.Yes:
                return False

        self.frame.setParent(None)
        self.img_class.grand_reset()
        self.update_img()
        self.vbox.addWidget(self.base_frame)

class Adjust(QWidget):
    def __init__(self, main):
        super().__init__()
        uic.loadUi(f"{pathlib.Path(__file__).parent.absolute()}/ui/adjust_frame.ui", self)
        self.get_zoom_factor = main.get_zoom_factor

        self.img_class, self.update_img, self.base_frame = main.img_class, main.update_img, main.base_frame
        self.rb, self.vbox, self.flip, self.zoom_factor = main.rb, main.vbox, main.flip, main.zoom_factor
        self.zoom_moment, self.slider, self.gv, self.vbox1 = main.zoom_moment, main.slider, main.gv, main.vbox1
        self.start_detect = False

        self.frame = self.findChild(QFrame, "frame")
        self.crop_btn = self.findChild(QPushButton, "crop_btn")
        self.rotate_btn = self.findChild(QPushButton, "rotate_btn")
        self.brightness_btn = self.findChild(QPushButton, "brightness_btn")
        self.contrast_btn = self.findChild(QPushButton, "contrast_btn")
        self.saturation_btn = self.findChild(QPushButton, "saturation_btn")
        self.mask_btn = self.findChild(QPushButton, "mask_btn")

        self.y_btn = self.findChild(QPushButton, "y_btn")
        self.y_btn.setIcon(QIcon(f"{pathlib.Path(__file__).parent.absolute()}/icon/check.png"))
        self.y_btn.setStyleSheet("QPushButton{border: 0px solid;}")
        self.y_btn.setIconSize(QSize(60, 60))
        self.n_btn = self.findChild(QPushButton, "n_btn")
        self.n_btn.setIcon(QIcon(f"{pathlib.Path(__file__).parent.absolute()}/icon/cross.png"))
        self.n_btn.setStyleSheet("QPushButton{border: 0px solid;}")
        self.n_btn.setIconSize(QSize(60, 60))

        self.y_btn.clicked.connect(lambda _: self.click_y())
        self.n_btn.clicked.connect(lambda _: self.click_n())
        self.crop_btn.clicked.connect(lambda _: self.click_crop())
        self.rotate_btn.clicked.connect(lambda _: self.click_crop(rotate=True))
        self.brightness_btn.clicked.connect(lambda _: self.click_brightness())
        self.contrast_btn.clicked.connect(lambda _: self.click_brightness(mode=1))
        self.saturation_btn.clicked.connect(lambda _: self.click_brightness(mode=2))
        self.mask_btn.clicked.connect(lambda _: self.click_brightness(mode=3))

    def click_crop(self, rotate=False):
        def click_y1():
            self.rb.update_dim()
            if rotate:
                self.img_class.rotate_img(self.rotate_value, crop=True, flip=self.flip)
                self.img_class.crop_img(int(self.rb.top * 2 / self.zoom_factor),
                                        int(self.rb.bottom * 2 / self.zoom_factor),
                                        int(self.rb.left * 2 / self.zoom_factor),
                                        int(self.rb.right * 2 / self.zoom_factor))
            else:
                self.img_class.reset(self.flip)
                self.img_class.crop_img(int(self.rb.top / self.zoom_factor), int(self.rb.bottom / self.zoom_factor),
                                        int(self.rb.left // self.zoom_factor), int(self.rb.right // self.zoom_factor))

            self.update_img()
            self.zoom_moment = False

            self.img_class.img_copy = deepcopy(self.img_class.img)
            self.slider.setParent(None)
            self.slider.valueChanged.disconnect()
            crop_frame.frame.setParent(None)
            self.vbox.addWidget(self.frame)
            self.rb.close()

        def click_n1():
            if not np.array_equal(img_copy, self.img_class.img):
                msg = QMessageBox.question(self, "Cancel edits", "Confirm to discard all the changes?   ",
                                           QMessageBox.Yes | QMessageBox.No)
                if msg != QMessageBox.Yes:
                    return False

            self.img_class.reset()
            self.update_img()
            self.zoom_moment = False

            self.slider.setParent(None)
            self.slider.valueChanged.disconnect()
            crop_frame.frame.setParent(None)
            self.vbox.addWidget(self.frame)
            self.rb.close()

        def change_slide():
            self.rotate_value = self.slider.value()
            self.slider.setValue(self.rotate_value)

            self.img_class.rotate_img(self.rotate_value)

            self.rb.setGeometry(int(self.img_class.left * self.zoom_factor), int(self.img_class.top * self.zoom_factor),
                                int((self.img_class.right - self.img_class.left) * self.zoom_factor),
                                int((self.img_class.bottom - self.img_class.top) * self.zoom_factor))

            self.rb.update_dim()
            self.update_img(True)

        def add_90():
            if self.rotate_value <= 270:
                self.rotate_value += 90
            else:
                self.rotate_value = 360
            self.slider.setValue(self.rotate_value)
            change_slide()

        def subtract_90():
            if self.rotate_value >= 90:
                self.rotate_value -= 90
            else:
                self.rotate_value = 0
            self.slider.setValue(self.rotate_value)
            change_slide()

        def vertical_flip():
            nonlocal vflip_ct
            self.img_class.img = cv2.flip(self.img_class.img, 0)
            if rotate:
                self.update_img(True)
            else:
                self.update_img()
            vflip_ct += 1
            self.flip[0] = vflip_ct % 2 == 1

        def horizontal_flip():
            nonlocal hflip_ct
            self.img_class.img = cv2.flip(self.img_class.img, 1)
            if rotate:
                self.update_img(True)
            else:
                self.update_img()
            hflip_ct += 1
            self.flip[1] = hflip_ct % 2 == 1

        crop_frame = Crop()
        crop_frame.n_btn.clicked.connect(click_n1)
        crop_frame.y_btn.clicked.connect(click_y1)
        crop_frame.rotate.clicked.connect(add_90)
        crop_frame.rotatect.clicked.connect(subtract_90)
        crop_frame.vflip.clicked.connect(vertical_flip)
        crop_frame.hflip.clicked.connect(horizontal_flip)
        self.flip = [False, False]
        vflip_ct = 2
        hflip_ct = 2

        self.frame.setParent(None)
        self.vbox.addWidget(crop_frame.frame)
        self.zoom_factor = self.get_zoom_factor()

        self.rb = ResizableRubberBand(self)
        self.rb.setGeometry(0, 0, self.img_class.img.shape[1] * self.zoom_factor,
                            self.img_class.img.shape[0] * self.zoom_factor)
        self.img_class.change_b_c(beta=-40)
        self.slider.valueChanged.connect(change_slide)


        if not rotate:
            self.update_img()
            crop_frame.rotate.setParent(None)
            crop_frame.rotatect.setParent(None)
        else:
            self.vbox1.insertWidget(1, self.slider)
            self.slider.setRange(0, 360)
            self.slider.setValue(0)
            self.zoom_moment = True
            self.img_class.rotate_img(0)
            self.rb.setGeometry(0, 0, int(self.img_class.img.shape[1] * self.zoom_factor),
                                int(self.img_class.img.shape[0] * self.zoom_factor))
            self.update_img(True)

        img_copy = deepcopy(self.img_class.img)

    def click_brightness(self, mode=0):
        def click_y1():
            self.img_class.img_copy = deepcopy(self.img_class.img)
            if mode != 3:
                self.slider.setParent(None)
                self.slider.valueChanged.disconnect()
            brightness_frame.frame.setParent(None)
            self.vbox.addWidget(self.frame)

        def click_n1():
            if not np.array_equal(self.img_class.img_copy, self.img_class.img):
                msg = QMessageBox.question(self, "Cancel edits", "Confirm to discard all the changes?   ",
                                           QMessageBox.Yes | QMessageBox.No)
                if msg != QMessageBox.Yes:
                    return False
            self.img_class.reset()
            self.update_img()

            if mode != 3:
                self.slider.setParent(None)
                self.slider.valueChanged.disconnect()
            brightness_frame.frame.setParent(None)
            self.vbox.addWidget(self.frame)

        def change_slide():
            self.brightness_value = self.slider.value()
            self.img_class.reset()
            self.img_class.change_b_c(beta=self.brightness_value)
            self.update_img()

        def change_slide_contr():
            self.contrast_value = self.slider.value() / 100
            self.img_class.reset()
            self.img_class.change_b_c(alpha=self.contrast_value)
            self.update_img()

        def change_slide_sat():
            self.saturation_value = self.slider.value() / 250
            self.img_class.reset()
            self.img_class.change_b_c(alpha=self.saturation_value)
            self.update_img()

        def color_dialog():
            color = QColorDialog.getColor()
            self.img_class.remove_color(color.name())
            self.update_img()

        brightness_frame = Brightness()
        brightness_frame.y_btn.clicked.connect(click_y1)
        brightness_frame.n_btn.clicked.connect(click_n1)

        self.frame.setParent(None)
        self.vbox.addWidget(brightness_frame.frame)

        if mode == 1:
            self.vbox1.insertWidget(1, self.slider)
            self.slider.setRange(0, 300)
            self.slider.setValue(100)
            self.slider.valueChanged.connect(change_slide_contr)
        elif mode == 2:
            self.vbox1.insertWidget(1, self.slider)
            self.slider.setRange(0, 1000)
            self.slider.setValue(250)
            self.slider.valueChanged.connect(change_slide_sat)
        elif mode == 3:
            btnn = QPushButton("Select color", brightness_frame)
            btnn.setFont(QFont("Neue Haas Grotesk Text Pro Medi", 14))
            btnn.setStyleSheet("QPushButton{border: 0px solid;}")
            btnn.setMaximumHeight(50)
            btnn.clicked.connect(color_dialog)
            brightness_frame.vbox2.insertWidget(0, btnn)
        else:
            self.vbox1.insertWidget(1, self.slider)
            self.slider.setRange(-120, 160)
            self.slider.setValue(0)
            self.slider.valueChanged.connect(change_slide)

    def click_y(self):
        self.start_detect = False
        self.frame.setParent(None)
        self.img_class.img_copy = deepcopy(self.img_class.img)
        self.img_class.grand_img_copy = deepcopy(self.img_class.img)
        self.vbox.addWidget(self.base_frame)

    def click_n(self):
        if not np.array_equal(self.img_class.grand_img_copy, self.img_class.img):
            msg = QMessageBox.question(self, "Cancel edits", "Confirm to discard all the changes?   ",
                                       QMessageBox.Yes | QMessageBox.No)
            if msg != QMessageBox.Yes:
                return False

        self.start_detect = False
        self.frame.setParent(None)
        self.img_class.grand_reset()
        self.update_img()
        self.vbox.addWidget(self.base_frame)

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

    main = PixlerMain()
    main.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()