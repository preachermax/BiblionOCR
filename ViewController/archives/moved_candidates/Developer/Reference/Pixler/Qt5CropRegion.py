import random, sys
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc
from PyQt5.QtCore import QPoint, QRect, QSize, Qt
from PyQt5.QtGui import QPixmap, QColor, QPainter, QPolygon
from PyQt5.QtWidgets import QLabel,QApplication,QRubberBand,QWidget

class Window(QLabel):

    def __init__(self, parent = None):
    
        QLabel.__init__(self, parent)
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.origin = QPoint()
    
    def mousePressEvent(self, event):
        '''
        if event.button() == Qt.LeftButton:
            
            self.origin = QPoint(event.pos())
            self.rubberBand.setGeometry(QRect(self.origin, QSize()))
            self.rubberBand.show()
            '''

        self.zoom_factor = self.get_zoom_factor()
        if self.draggable and event.button() == Qt.LeftButton:
            self.mousePressPos = event.globalPos()  # global
            self.mouseMovePos = event.globalPos() - self.pos()  # local
    
    def mouseMoveEvent(self, event):
        '''
        if not self.origin.isNull():
            self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())
        '''

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
        '''
        if event.button() == Qt.LeftButton:
            self.rubberBand.hide()
        '''
        
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


    def cropregion(self):
        #pass
        im = Image.open('card.png')
        im = im.crop( (1, 0, 826, 1125) ) # previously, image was 826 pixels wide, cropping to 825 pixels wide
        #im.save('card.png') # saves the image
        im.show() # opens the image
        self.img = self.img[left:right, top:bottom]

    def create_pixmap():

        def color():
            r = random.randrange(0, 255)
            g = random.randrange(0, 255)
            b = random.randrange(0, 255)
            return QColor(r, g, b)
        
        def point():
            return QPoint(random.randrange(0, 400), random.randrange(0, 300))
        
        pixmap = QPixmap(400, 300)
        pixmap.fill(color())
        painter = QPainter()
        painter.begin(pixmap)
        i = 0
        while i < 1000:
            painter.setBrush(color())
            painter.drawPolygon(QPolygon([point(), point(), point()]))
            i += 1
        
        painter.end()
        return pixmap

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

if __name__ == "__main__":

    app = QApplication(sys.argv)
    random.seed()
    
    window = Window()
    window.setPixmap(create_pixmap())
    window.resize(400, 300)
    window.show()
    
    sys.exit(app.exec_())