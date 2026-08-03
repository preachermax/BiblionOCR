import random, sys
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc
from PyQt5.QtCore import QPoint, QRect, QSize, Qt
from PyQt5.QtGui import QPixmap, QColor, QPainter, QPolygon
from PyQt5.QtWidgets import QLabel,QApplication,QRubberBand

class Window(QLabel):

    def __init__(self, parent = None):
    
        QLabel.__init__(self, parent)
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.origin = QPoint()
    
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
            self.cropregion(x,y,w,h)
            self.rubberBand.hide()

    def cropregion(self,x,y,w,h):
        #pass
        #im = Image.open('card.png')
        #im = im.crop( (1, 0, 826, 1125) ) # previously, image was 826 pixels wide, cropping to 825 pixels wide
        #im.save('card.png') # saves the image
        #im.show() # opens the image
        #self.img = self.img[left:right, top:bottom]
        #img = window.pixmap()[x:x+w, y:y+h]
        currentQRect = self.rubberBand.geometry()
        cropQPixmap = window.pixmap().copy(currentQRect)
        window.setPixmap(cropQPixmap)
        #self.ui.CroppedImg.setPixmap(cropQPixmap)

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

if __name__ == "__main__":

    app = QApplication(sys.argv)
    random.seed()
    
    window = Window()
    window.setPixmap(create_pixmap())
    window.resize(400, 300)
    window.show()
    
    sys.exit(app.exec_())