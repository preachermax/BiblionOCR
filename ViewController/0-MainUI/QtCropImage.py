#print(len(locals()))

# Python imports
import sys
import os
import io
import tiffcapture
import qimage2ndarray
from PIL import Image as pilimg

# PyQt5 imports
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QPoint, QRect, QSize, Qt
from PyQt5.QtWidgets import QRubberBand, QWidget, QHBoxLayout, QSizeGrip

# Custom imports
import CropTif as croptif 
#import CropTifDialog as cropdialog


class MainWindow(qtw.QMainWindow):
#class CropImage(object):
# Menu and Toolbar Action Methods 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # pre-compiled QtDesigner Ui_MainUI and extended slots code starts here:        
        # load the pre-compiled QtDesigner Ui_MainUI user interface
        
        #self.ui = cropdialog.Ui_CropTifDialog()
        self.ui = croptif.Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.ui.OpenImageFilebutton.clicked.connect(self.OpenCropFileDialog)
        self.ui.Cropbutton.clicked.connect(self.crop)
        self.ui.Zoombutton.clicked.connect(self.show_combo)
        self.ui.ZoomComboBox.currentTextChanged.connect(self.on_zoom)
        #self.ui.ZoomOutbutton.clicked.connect(self.on_zoom_out)
        
        self.ui.SaveCroppedImgAsbutton.clicked.connect(self.SaveCropAs)
        self.ui.SaveCroppedImgbutton.clicked.connect(self.SaveCrop)
        
        self.ui.ZoomComboBox.hide()
        #self.initUI()
        
        #self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.rubberBand = ResizableRubberBand(self)
        
        self.origin = QPoint()
        self.scale = 1
        self.origsize = 1
        self.pixmap = qtg.QPixmap()
        self.origpixmap = qtg.QPixmap()
        self.croppixmap = qtg.QPixmap()
        self.origcroppixmap = qtg.QPixmap()
        self.currentQRect = self.rubberBand.geometry()
        
        #self.origQRect = self.ui.Image.pixmap().geometry()

    #def initUI (self):
        #self.setPixmap(QPixmap('/home/max/Projects/Python/Images/Source/png_black_white_deskew/source_book_41_Mark/1516_Page_081.png'))
    '''
    def mousePressEvent (self, eventQMouseEvent):
        self.originQPoint = eventQMouseEvent.pos()
        self.currentQRubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.currentQRubberBand.setGeometry(QRect(self.originQPoint, qtc.QSize()))
        self.currentQRubberBand.show()

    def mouseMoveEvent (self, eventQMouseEvent):
        self.currentQRubberBand.setGeometry(QRect(self.originQPoint, eventQMouseEvent.pos()).normalized())

    def mouseReleaseEvent (self, eventQMouseEvent):
        #self.currentQRubberBand.hide()
        currentQRect = self.currentQRubberBand.geometry()
        self.currentQRubberBand.deleteLater()
        cropQPixmap = self.ui.Image.pixmap().copy(currentQRect)
        self.ui.CroppedImg.setPixmap(cropQPixmap)
        #cropQPixmap.save('/home/max/Projects/Python/Images/Source/png_black_white_deskew/source_book_41_Mark/1516_Page_081_crop.png')
    ''' 
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
            self.croppixmap = self.ui.Image.pixmap().copy(self.currentQRect)
            
            #self.ui.Cropped.setPixmap(self.croppixmap)
            
            #croppedimg = self.ui.Image[x:x+w,y:y+h]
            #self.rubberBand.hide()

    def setImageStack(self, tiffCaptureHandle):
        """ Set the scene's current TIFF image stack to the input TiffCapture object.
        Raises a RuntimeError if the input tiffCaptureHandle has type other than TiffCapture.
        :type tiffCaptureHandle: TiffCapture
        """
        if type(tiffCaptureHandle) is not tiffcapture.TiffCapture:
            raise RuntimeError("MultiPageTIFFViewerQt.setImageStack: Argument must be a TiffCapture object.")
        self._tiffCaptureHandle = tiffCaptureHandle
        self.showFrame(0)

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


    def OpenCropFileDialog(self):
        self.path = qtw.QFileDialog.getOpenFileName(
            self.ui.centralwidget, 'Open image file', '',
            'Images (*.png *.xpm *.jpg *.bmp *.gif *.tif)')[0]
                
        if self.path:
            file = qtc.QFile(self.path)
            filestr = os.path.basename(self.path)
            self.ui.ImageLe.setText(self.path)
            filesplit = os.path.splitext(filestr)
            filename = filesplit[0]
            fileext = filesplit[1]
                        
            if file.open(qtc.QIODevice.ReadOnly):
                info = qtc.QFileInfo(self.path)
                
                if fileext == '.tif':
                    self.loadImageStackFromFile(str(self.path))
                    self.showFrame(0)
                    #pixmap = qtg.QPixmap.fromImage(self.qimage).scaled(self.ui.Image.size(), qtc.Qt.KeepAspectRatio)
                    self.origpixmap = qtg.QPixmap.fromImage(self.qimage)
                    self.ui.Image.setPixmap(qtg.QPixmap(self.origpixmap))
                else:
                    self.origpixmap = qtg.QPixmap(self.path)
                    self.ui.Image.setPixmap(self.origpixmap)
                
                self.pixmap = self.origpixmap
                file.close()

    def getmain(self,recpath,recorig):
        self.origpixmap = recorig
        self.scale = .10
        self.ui.ImageLe.setText(recpath)
        self.resize_image()
    
    def crop(self):

        if self.currentQRect != None:
            self.currentQRect = self.rubberBand.geometry()
            h = self.rubberBand.height()
            w = self.rubberBand.width()
            x = self.rubberBand.x()
            y = self.rubberBand.y()
            modx = x/self.scale
            mody = y/self.scale
            modw = w/self.scale
            modh = h/self.scale           
            
            print(x,y,w,h)
            print(self.currentQRect)

            print(modx,mody,modw,modh)
            currentQRect = QRect(modx,mody,modw,modh)
            print(currentQRect)
            self.ui.Image.setPixmap(self.origpixmap)
            self.ui.Cropped.setAlignment(qtc.Qt.AlignLeft | qtc.Qt.AlignTop)       
            self.origcroppixmap = self.ui.Image.pixmap().copy(currentQRect)
            self.ui.Cropped.setPixmap(self.origcroppixmap)
            self.croppixmap = self.origcroppixmap
            self.resize_image()
            self.resize_cropped()

            '''
            # RefImg QRect
            print("This is the new crop method of the Pixer class")
            
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
            self.resize_Image()'''

    def show_combo(self):
        self.ui.ZoomComboBox.show()
    
    def on_zoom(self):
        seltext = self.ui.ZoomComboBox.currentText()
        selnumtext = seltext.split(" ")
        print(selnumtext[0])
        self.scale = float(selnumtext[0])/100
        
        #self.scale *= 2
        print(self.scale)
        self.ui.ZoomComboBox.hide()
        self.resize_image()
    
    '''def on_zoom_in(self):
        self.scale *= 2
        self.resize_image()

    def on_zoom_out(self):
        self.scale /= 1.5
        self.resize_image()'''

    def resize_image(self):
        self.origsize = self.origpixmap.size()       
        scaled_pixmap = self.origpixmap.scaled(self.scale * self.origsize, qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)
        self.ui.Image.setPixmap(scaled_pixmap)

    def resize_cropped(self):
        self.origsize = self.croppixmap.size()       
        scaled_pixmap = self.croppixmap.scaled(self.scale * self.origsize, qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation)
        self.ui.Cropped.setPixmap(scaled_pixmap)
    
    def SaveCropAs(self):
        path = qtw.QFileDialog.getSaveFileName(
            self.ui.centralwidget, 'Save cropped tiff file', '',
            'Tiff files (*.tif)')[0]
        #my_CroppedImg = self.ui.Cropped.pixmap().toImage()
        my_CroppedImg = self.origcroppixmap.toImage()
        my_CroppedImg.save(path)
        # Write accepted ROI to correct folder/file
        buffer = qtc.QBuffer()
        buffer.open(qtc.QBuffer.ReadWrite)
        my_CroppedImg.save(buffer, "PNG")
        PILimage = pilimg.open(io.BytesIO(buffer.data()))
        outfile = path
        print("Generating: " + outfile)
        PILimage.save(outfile, "TIFF", dpi=(300,300), compression = "tiff_lzw")
        #filename = os.path.basename(path)
        self.ui.CroppedLe.setText(path)
        #file.close()
        

    def SaveCrop(self):
        
        #defaultdir = r"/home/max/Projects/Python/EstablishTruth/Greek txt pages/greek_book_41_Mark/"
        defaultpath = self.ui.TextLE.displayText()
        filename = os.path.basename(defaultpath)
        
        if defaultpath:
            path = defaultpath
            
        else:
            path = qtw.QFileDialog.getSaveFileName(
                self.centralwidget, 'Save cropped tiff file', '',
                'Tiff files (*.tif)')[0]
        
        #self.ui.Cropped.self.pixmap.save(path)
        self.origcroppixmap.save(path)
        filename = os.path.basename(path)
        self.ui.CroppedLe.setText(filename)
        file.close()

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
        
'''
class ResizableRubberBand(QWidget):
    def __init__(self, main):
        super(ResizableRubberBand, self).__init__(main.gv)
        self.get_zoom_factor = main.get_zoom_factor

        self.img_class, self.update, self.zoom_factor = main.img_class, main.update, main.zoom_factor
        self.draggable, self.mousePressPos, self.mouseMovePos = True, None, None
        self.left, self.right, self.top, self.bottom = None, None, None, None
        self.borderRadius = 0

        self.setWindowFlags(Qt.SubWindow)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QSizeGrip(self), 0, Qt.AlignLeft | Qt.AlignTop)
        layout.addWidget(QSizeGrip(self), 0, Qt.AlignRight | Qt.AlignBottom)

        self._band = QRubberBand(QRubberBand.Rectangle, self)
        self._band.show()
        self.show()

    def update_dim(self):
        self.left, self.top = self.pos().x(), self.pos().y()
        self.right, self.bottom = self._band.width() + self.left, self._band.height() + self.top

    def resizeEvent(self, event):
        try:
            self.left, self.top = self.pos().x(), self.pos().y()
            self.right, self.bottom = self._band.width() + self.left, self._band.height() + self.top
        except:
            pass
        self._band.resize(self.size())

    def paintEvent(self, event):
        # Get current window size
        window_size = self.size()
        qp = QPainter(self)
        qp.drawRoundedRect(0, 0, window_size.width(), window_size.height(), self.borderRadius, self.borderRadius)

    def mousePressEvent(self, event):
        self.zoom_factor = self.get_zoom_factor()
        if self.draggable and event.button() == Qt.LeftButton:
            self.mousePressPos = event.globalPos()  # global
            self.mouseMovePos = event.globalPos() - self.pos()  # local

    def mouseMoveEvent(self, event):
        if self.draggable and event.buttons() & Qt.LeftButton:
            if self.right <= int(self.img_class.img.shape[1] * self.zoom_factor) and self.bottom <= \
                    int(self.img_class.img.shape[0] * self.zoom_factor) and self.left >= 0 and self.top >= 0:
                globalPos = event.globalPos()
                diff = globalPos - self.mouseMovePos
                self.move(diff)  # move window
                self.mouseMovePos = globalPos - self.pos()

            self.left, self.top = self.pos().x(), self.pos().y()
            self.right, self.bottom = self._band.width() + self.left, self._band.height() + self.top

    def mouseReleaseEvent(self, event):
        if self.mousePressPos is not None:
            if event.button() == Qt.LeftButton:
                self.mousePressPos = None

        if self.left < 0:
            self.left = 0
            self.move(0, self.top)
        if self.right > int(self.img_class.img.shape[1] * self.zoom_factor):
            self.left = int(self.img_class.img.shape[1] * self.zoom_factor) - self._band.width()
            self.move(self.left, self.top)
        if self.bottom > int(self.img_class.img.shape[0] * self.zoom_factor):
            self.top = int(self.img_class.img.shape[0] * self.zoom_factor) - self._band.height()
            self.move(self.left, self.top)
        if self.top < 0:
            self.top = 0
            self.move(self.left, 0)
'''




# Only run this code if I am actually running this script
if __name__ == '__main__': 
    app = qtw.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec()
    '''app = qtw.QApplication(sys.argv)
    CropImage = qtw.QMainWindow()  
    CropImage.show()
    sys.exit(app.exec_())'''