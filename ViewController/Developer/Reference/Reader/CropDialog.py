# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './QtDesignerUI/CropTifDialog.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_CropTifDialog(object):
    def setupUi(self, CropTifDialog):
        CropTifDialog.setObjectName("CropTifDialog")
        CropTifDialog.resize(612, 785)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Icons/image-crop.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        CropTifDialog.setWindowIcon(icon)
        self.buttonBox = QtWidgets.QDialogButtonBox(CropTifDialog)
        self.buttonBox.setGeometry(QtCore.QRect(430, 730, 181, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.Image = QtWidgets.QLabel(CropTifDialog)
        self.Image.setGeometry(QtCore.QRect(0, 0, 600, 600))
        self.Image.setText("")
        self.Image.setObjectName("Image")
        self.OpenImageFilebutton = QtWidgets.QPushButton(CropTifDialog)
        self.OpenImageFilebutton.setGeometry(QtCore.QRect(110, 660, 91, 25))
        font = QtGui.QFont()
        font.setFamily("FROMVS [MAXR]")
        font.setPointSize(8)
        self.OpenImageFilebutton.setFont(font)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/Icons/Icons/tiff-file.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.OpenImageFilebutton.setIcon(icon1)
        self.OpenImageFilebutton.setObjectName("OpenImageFilebutton")
        self.ImageLe = QtWidgets.QLineEdit(CropTifDialog)
        self.ImageLe.setGeometry(QtCore.QRect(110, 620, 421, 25))
        font = QtGui.QFont()
        font.setFamily("FROMVS")
        font.setPointSize(8)
        self.ImageLe.setFont(font)
        self.ImageLe.setObjectName("ImageLe")
        self.ImagePathLabel = QtWidgets.QLabel(CropTifDialog)
        self.ImagePathLabel.setGeometry(QtCore.QRect(50, 620, 51, 17))
        font = QtGui.QFont()
        font.setFamily("FROMVS")
        font.setPointSize(8)
        self.ImagePathLabel.setFont(font)
        self.ImagePathLabel.setObjectName("ImagePathLabel")
        self.SaveCroppedImgAsbutton = QtWidgets.QPushButton(CropTifDialog)
        self.SaveCroppedImgAsbutton.setGeometry(QtCore.QRect(330, 660, 89, 25))
        font = QtGui.QFont()
        font.setFamily("FROMVS [MAXR]")
        font.setPointSize(8)
        self.SaveCroppedImgAsbutton.setFont(font)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/Icons/Icons/disk-rename.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.SaveCroppedImgAsbutton.setIcon(icon2)
        self.SaveCroppedImgAsbutton.setObjectName("SaveCroppedImgAsbutton")
        self.SaveCroppedImgbutton = QtWidgets.QPushButton(CropTifDialog)
        self.SaveCroppedImgbutton.setGeometry(QtCore.QRect(440, 660, 89, 25))
        font = QtGui.QFont()
        font.setFamily("FROMVS [MAXR]")
        font.setPointSize(8)
        self.SaveCroppedImgbutton.setFont(font)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/Icons/Icons/disk.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.SaveCroppedImgbutton.setIcon(icon3)
        self.SaveCroppedImgbutton.setObjectName("SaveCroppedImgbutton")
        self.pushButton = QtWidgets.QPushButton(CropTifDialog)
        self.pushButton.setGeometry(QtCore.QRect(220, 660, 89, 25))
        font = QtGui.QFont()
        font.setFamily("FROMVS")
        font.setPointSize(8)
        self.pushButton.setFont(font)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(":/Icons/Icons/image-crop.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton.setIcon(icon4)
        self.pushButton.setObjectName("pushButton")

        self.retranslateUi(CropTifDialog)
        self.buttonBox.accepted.connect(CropTifDialog.accept)
        self.buttonBox.rejected.connect(CropTifDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(CropTifDialog)

    def retranslateUi(self, CropTifDialog):
        _translate = QtCore.QCoreApplication.translate
        CropTifDialog.setWindowTitle(_translate("CropTifDialog", "Crop tiff image"))
        self.OpenImageFilebutton.setText(_translate("CropTifDialog", "Open Tif Image"))
        self.ImagePathLabel.setText(_translate("CropTifDialog", "Image Path"))
        self.SaveCroppedImgAsbutton.setText(_translate("CropTifDialog", "Save As"))
        self.SaveCroppedImgbutton.setText(_translate("CropTifDialog", "Save"))
        self.pushButton.setText(_translate("CropTifDialog", "Crop Selection"))

import UI_Icons

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    CropTifDialog = QtWidgets.QDialog()
    ui = Ui_CropTifDialog()
    ui.setupUi(CropTifDialog)
    CropTifDialog.show()
    sys.exit(app.exec_())

