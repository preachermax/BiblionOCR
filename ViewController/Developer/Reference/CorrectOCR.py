# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'OCRCorrection.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

import sys
import sys, os
from PyQt5 import QtCore, QtGui, QtWidgets
import pytesseract
import tiffcapture
import qimage2ndarray

class CorrectOCR():

    def setImageStack(self, tiffCaptureHandle):
        """ Set the scene's current TIFF image stack to the input TiffCapture object.
        Raises a RuntimeError if the input tiffCaptureHandle has type other than TiffCapture.
        :type tiffCaptureHandle: TiffCapture
        """
        if type(tiffCaptureHandle) is not tiffcapture.TiffCapture:
            raise RuntimeError("MultiPageTIFFViewerQt.setImageStack: Argument must be a TiffCapture object.")
        self.ui._tiffCaptureHandle = tiffCaptureHandle
        self.ui.showFrame(0)

    def loadImageStackFromFile(self,fileName=''):
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
            self.ui._tiffCaptureHandle = tiffcapture.opentiff(fileName)
            
    def numFrames(self):
        """ Return the number of image frames in the stack.
        """
        if self.ui._tiffCaptureHandle is not None:
            # !!! tiffcapture has length=0 for a single page TIFF.
            # If our handle is valid, we'll assume we have at least one image.
            return max([1, self.ui._tiffCaptureHandle.length])
        return 0

    def getFrame(self, i=None):
        """ Return the i^th image frame as a NumPy ndarray.
        If i is None, return the current image frame.
        """
        if self.ui._tiffCaptureHandle is None:
            return None
        if i is None:
            i = self.ui.currentFrameIndex
        if (i is None) or (i < 0) or (i >= self.ui.numFrames()):
            return None
        return self.ui._tiffCaptureHandle.find_and_read(i)

    def showFrame(self, i=None):
        """ Display the i^th frame in the viewer.
        Also update the frame slider position and current frame text.
        """
        self.ui.frame = self.ui.getFrame(i)
        if self.ui.frame is None:
            return
        # Convert frame ndarray to a QImage.
        self.ui.qimage = qimage2ndarray.array2qimage(self.ui.frame, normalize=True)
    
    def OpenImageFileDialog(self):
        path = QtWidgets.QFileDialog.getOpenFileName(
            self.ui.centralwidget, 'Open image file', '',
            'Images (*.png *.xpm *.jpg *.bmp *.gif *.tif)')[0]
                
        if path:
            file = QtCore.QFile(path)
            filestr = os.path.basename(path)
            self.ui.ImageLe.setText(filestr)
            filesplit = os.path.splitext(filestr)
            filename = filesplit[0]
            fileext = filesplit[1]
                        
            if file.open(QtCore.QIODevice.ReadOnly):
                info = QtCore.QFileInfo(path)
                
                if fileext == '.tif':
                    self.loadImageStackFromFile(str(path))
                    self.showFrame(0)
                    pixmap = QtGui.QPixmap.fromImage(self.ui.qimage).scaled(self.ui.Image.size(), 
                        QtCore.Qt.KeepAspectRatio)
                    self.ui.Image.setPixmap(QtGui.QPixmap(pixmap))
                else:
                    
                    self.ui.Image.setPixmap(QtGui.QPixmap(path))
                
                file.close()
    
    def GetRawOCRtext(self):
        path = QtWidgets.QFileDialog.getOpenFileName(
            self.ui.centralwidget, 'Open tif image file', '',
            'Images (*.tif)')[0]
        if path:
            file = QtCore.QFile(path)
            if file.open(QtCore.QIODevice.ReadOnly):
                info = QtCore.QFileInfo(path)
                my_OCR_rawtext = pytesseract.image_to_string(path,lang="feg")
                #self.ui.OCRDocument.insertPlainText(my_OCR_rawtext)
                self.ui.OCRText.insertPlainText(my_OCR_rawtext)
                file.close()
    
    def SetLineSpacing(self, MainWindow):
        num,ok = QtWidgets.QInputDialog.getInt(self.ui.centralwidget,"Proportional Line Spacing","Enter a percent value from 0-200")
        if ok:
            lineSpacing = num
        else:
            lineSpacing = 145
            
        cursor = self.ui.OCRText.textCursor()
        if not cursor.hasSelection():
            cursor.select(QtGui.QTextCursor.Document)
        bf = self.ui.OCRCursor.blockFormat()
        bf.setLineHeight(lineSpacing, self.ui.OCRBlockFormat.ProportionalHeight) 
        cursor.mergeBlockFormat(bf)
    
    def OpenTextFileDialog(self, MainWindow):
        path = QtWidgets.QFileDialog.getOpenFileName(
            self.ui.centralwidget, 'Open text file', '',
            'Text files (*.txt)')[0]
        if path:
            file = QtCore.QFile(path)
            filename = os.path.basename(path)
            self.ui.TextLe.setText(filename)
            if file.open(QtCore.QIODevice.ReadOnly):
                stream = QtCore.QTextStream(file)
                text = stream.readAll()
                info = QtCore.QFileInfo(path)
                if info.completeSuffix() == 'txt':
                    #self.ui.editor_text.setHtml(text)
                    self.ui.OCRText.insertPlainText(text)
                else:
                    self.ui.OCRText.setPlainText(text)
                file.close()
        
    def SaveRawTextFileDialog(self, MainWindow):
        path = QtWidgets.QFileDialog.getSaveFileName(
            self.ui.centralwidget, 'Save Raw text file', '',
            'Text files (*.txt)')[0]
        with open(path, 'w') as file:
            my_RawText = self.ui.OCRDocument.toPlainText()
            file.write(my_RawText)
        filename = os.path.basename(path)
        self.ui.TextLe.setText(filename)
        file.close()
        
    def SaveAsCorrectedTextFileDialog(self, MainWindow):
        path = QtWidgets.QFileDialog.getSaveFileName(
            self.ui.centralwidget, 'Save Corrected text file', '',
            'Text files (*.txt)')[0]
        with open(path, 'w') as file:
            my_CorrectedText = self.ui.OCRDocument.toPlainText()
            file.write(my_CorrectedText)
        filename = os.path.basename(path)
        self.ui.TextLe.setText(filename)
        file.close()

    def SaveCorrectedTextFileDialog(self, MainWindow):
        defaultdir = r"/home/max/Projects/Python/EstablishTruth/Greek txt pages/greek_book_40_Matthew/"
        defaultfile = self.ui.TextLe.displayText()

        if defaultfile:
            path = defaultdir + defaultfile
            filename = defaultfile
        else:
            path = QtWidgets.QFileDialog.getSaveFileName(
                self.ui.centralwidget, 'Save Corrected text file', '',
                'Text files (*.txt)')[0]
            filename = os.path.basename(path)
        with open(path, 'w') as file:
            my_CorrectedText = self.ui.OCRDocument.toPlainText()
            file.write(my_CorrectedText)
        
        self.ui.TextLe.setText(filename)
        file.close()
