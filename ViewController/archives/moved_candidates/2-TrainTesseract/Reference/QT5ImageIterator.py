from PyQt5 import QtCore, QtGui, QtWidgets
import os
import re

class ImageLoader(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        layout = QtWidgets.QGridLayout(self)

        self.label = QtWidgets.QLabel()
        layout.addWidget(self.label, 0, 0, 1, 2)
        self.label.setMinimumSize(200, 200)
        # the label alignment property is always maintained even when the contents
        # change, so there is no need to set it each time
        self.label.setAlignment(QtCore.Qt.AlignCenter)

        self.loadImageButton = QtWidgets.QPushButton('Load image')
        layout.addWidget(self.loadImageButton, 1, 0)

        self.nextImageButton = QtWidgets.QPushButton('Next image')
        layout.addWidget(self.nextImageButton)

        self.loadImageButton.clicked.connect(self.loadImage)
        self.nextImageButton.clicked.connect(self.nextImage)

        self.dirIterator = None
        self.fileList = []

    
    '''def sorted_alphanumeric(data):
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
        return sorted(data, key=alphanum_key)
        #usage:dirlist = sorted_alphanumeric(os.listdir(...)) - works great!'''
    
    def loadImage(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Select Image', '', 'Image Files (*.png *.jpg *.jpeg)')
        if filename:
            pixmap = QtGui.QPixmap(filename).scaled(self.label.size(), 
                QtCore.Qt.KeepAspectRatio)
            if pixmap.isNull():
                return
            self.label.setPixmap(pixmap)
            dirpath = os.path.dirname(filename)
            self.fileList = []
            for f in os.listdir(dirpath):
                fpath = os.path.join(dirpath, f)
                if os.path.isfile(fpath) and f.endswith(('.png', '.jpg', '.jpeg')):
                    self.fileList.append(fpath)
            convert = lambda text: int(text) if text.isdigit() else text.lower()
            alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
            sorted_filelist = sorted(self.fileList, key=alphanum_key)
            #self.fileList.sort()
            print(sorted_filelist)
            self.dirIterator = iter(sorted_filelist)
            while True:
                # cycle through the iterator until the current file is found
                if next(self.dirIterator) == filename:
                    break

    def nextImage(self):
        # ensure that the file list has not been cleared due to missing files
        if self.fileList:
            try:
                filename = next(self.dirIterator)
                pixmap = QtGui.QPixmap(filename).scaled(self.label.size(), 
                    QtCore.Qt.KeepAspectRatio)
                if pixmap.isNull():
                    # the file is not a valid image, remove it from the list
                    # and try to load the next one
                    self.fileList.remove(filename)
                    self.nextImage()
                else:
                    self.label.setPixmap(pixmap)
            except:
                # the iterator has finished, restart it
                self.dirIterator = iter(self.fileList)
                self.nextImage()
        else:
            # no file list found, load an image
            self.loadImage()


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    imageLoader = ImageLoader()
    imageLoader.show()
    sys.exit(app.exec_())