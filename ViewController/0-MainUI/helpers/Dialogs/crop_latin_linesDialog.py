# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './QtDesignerUI/crop_latin_linesDialog.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_crop_latin_linesDialog(object):
    def setupUi(self, crop_latin_linesDialog):
        crop_latin_linesDialog.setObjectName("crop_latin_linesDialog")
        crop_latin_linesDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        crop_latin_linesDialog.resize(484, 279)
        self.buttonBox = QtWidgets.QDialogButtonBox(crop_latin_linesDialog)
        self.buttonBox.setGeometry(QtCore.QRect(260, 230, 171, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.SourceLineEdit = QtWidgets.QLineEdit(crop_latin_linesDialog)
        self.SourceLineEdit.setGeometry(QtCore.QRect(10, 50, 301, 25))
        self.SourceLineEdit.setObjectName("SourceLineEdit")
        self.SourceButton = QtWidgets.QPushButton(crop_latin_linesDialog)
        self.SourceButton.setEnabled(False)
        self.SourceButton.setGeometry(QtCore.QRect(330, 50, 101, 25))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Icons/Icons/tiff-file.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.SourceButton.setIcon(icon)
        self.SourceButton.setObjectName("SourceButton")
        self.SourceLabel = QtWidgets.QLabel(crop_latin_linesDialog)
        self.SourceLabel.setGeometry(QtCore.QRect(20, 30, 211, 17))
        self.SourceLabel.setObjectName("SourceLabel")
        self.LatinBoxFolderLineEdit = QtWidgets.QLineEdit(crop_latin_linesDialog)
        self.LatinBoxFolderLineEdit.setGeometry(QtCore.QRect(10, 110, 301, 25))
        self.LatinBoxFolderLineEdit.setObjectName("LatinBoxFolderLineEdit")
        self.LatinBoxFolderLabel = QtWidgets.QLabel(crop_latin_linesDialog)
        self.LatinBoxFolderLabel.setGeometry(QtCore.QRect(20, 90, 271, 17))
        self.LatinBoxFolderLabel.setObjectName("LatinBoxFolderLabel")
        self.LatinBoxFolderButton = QtWidgets.QPushButton(crop_latin_linesDialog)
        self.LatinBoxFolderButton.setGeometry(QtCore.QRect(330, 110, 101, 25))
        self.LatinBoxFolderButton.setIcon(icon)
        self.LatinBoxFolderButton.setObjectName("LatinBoxFolderButton")
        self.DestLatinLineEdit = QtWidgets.QLineEdit(crop_latin_linesDialog)
        self.DestLatinLineEdit.setGeometry(QtCore.QRect(10, 170, 301, 25))
        self.DestLatinLineEdit.setObjectName("DestLatinLineEdit")
        self.DestLatinButton = QtWidgets.QPushButton(crop_latin_linesDialog)
        self.DestLatinButton.setGeometry(QtCore.QRect(330, 170, 101, 25))
        self.DestLatinButton.setIcon(icon)
        self.DestLatinButton.setObjectName("DestLatinButton")
        self.DestLatinLabel = QtWidgets.QLabel(crop_latin_linesDialog)
        self.DestLatinLabel.setGeometry(QtCore.QRect(20, 150, 271, 17))
        self.DestLatinLabel.setObjectName("DestLatinLabel")
        self.defaultsrcBox = QtWidgets.QCheckBox(crop_latin_linesDialog)
        self.defaultsrcBox.setGeometry(QtCore.QRect(330, 20, 101, 23))
        self.defaultsrcBox.setChecked(True)
        self.defaultsrcBox.setObjectName("defaultsrcBox")

        self.retranslateUi(crop_latin_linesDialog)
        self.buttonBox.accepted.connect(crop_latin_linesDialog.accept)
        self.buttonBox.rejected.connect(crop_latin_linesDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(crop_latin_linesDialog)

    def retranslateUi(self, crop_latin_linesDialog):
        _translate = QtCore.QCoreApplication.translate
        crop_latin_linesDialog.setWindowTitle(_translate("crop_latin_linesDialog", "Crop Latin tif page files into tif line files"))
        self.SourceLineEdit.setPlaceholderText(_translate("crop_latin_linesDialog", "(default) working temp folder"))
        self.SourceButton.setText(_translate("crop_latin_linesDialog", "Source"))
        self.SourceLabel.setText(_translate("crop_latin_linesDialog", "Mono tif pages source folder"))
        self.LatinBoxFolderLabel.setText(_translate("crop_latin_linesDialog", "Latin linebox files folder"))
        self.LatinBoxFolderButton.setText(_translate("crop_latin_linesDialog", "Destination"))
        self.DestLatinButton.setText(_translate("crop_latin_linesDialog", "Destination"))
        self.DestLatinLabel.setText(_translate("crop_latin_linesDialog", "Latin tif lines destination folder"))
        self.defaultsrcBox.setText(_translate("crop_latin_linesDialog", "Use default"))

import UI_Icons

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    crop_latin_linesDialog = QtWidgets.QDialog()
    ui = Ui_crop_latin_linesDialog()
    ui.setupUi(crop_latin_linesDialog)
    crop_latin_linesDialog.show()
    sys.exit(app.exec_())

