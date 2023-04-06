# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './QtDesignerUI/ImageTextPairDialog.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_ImageTextPairDialog(object):
    def setupUi(self, ImageTextPairDialog):
        ImageTextPairDialog.setObjectName("ImageTextPairDialog")
        ImageTextPairDialog.resize(400, 169)
        self.buttonBox = QtWidgets.QDialogButtonBox(ImageTextPairDialog)
        self.buttonBox.setGeometry(QtCore.QRect(220, 130, 171, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.label = QtWidgets.QLabel(ImageTextPairDialog)
        self.label.setGeometry(QtCore.QRect(30, 10, 101, 17))
        self.label.setObjectName("label")
        self.MatchTxt2Imgbutton = QtWidgets.QRadioButton(ImageTextPairDialog)
        self.MatchTxt2Imgbutton.setGeometry(QtCore.QRect(30, 50, 221, 23))
        self.MatchTxt2Imgbutton.setObjectName("MatchTxt2Imgbutton")
        self.MatchImg2Txtbutton = QtWidgets.QRadioButton(ImageTextPairDialog)
        self.MatchImg2Txtbutton.setGeometry(QtCore.QRect(30, 90, 221, 23))
        self.MatchImg2Txtbutton.setObjectName("MatchImg2Txtbutton")

        self.retranslateUi(ImageTextPairDialog)
        self.buttonBox.accepted.connect(ImageTextPairDialog.accept)
        self.buttonBox.rejected.connect(ImageTextPairDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(ImageTextPairDialog)

    def retranslateUi(self, ImageTextPairDialog):
        _translate = QtCore.QCoreApplication.translate
        ImageTextPairDialog.setWindowTitle(_translate("ImageTextPairDialog", "Dialog"))
        self.label.setText(_translate("ImageTextPairDialog", "Select option:"))
        self.MatchTxt2Imgbutton.setText(_translate("ImageTextPairDialog", "Match text to current image"))
        self.MatchImg2Txtbutton.setText(_translate("ImageTextPairDialog", "Match image to current text"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ImageTextPairDialog = QtWidgets.QDialog()
    ui = Ui_ImageTextPairDialog()
    ui.setupUi(ImageTextPairDialog)
    ImageTextPairDialog.show()
    sys.exit(app.exec_())

