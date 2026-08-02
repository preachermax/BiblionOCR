# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './QtDesignerUI/crop_greek_linesDialog.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_crop_greek_linesDialog(object):
    def setupUi(self, crop_greek_linesDialog):
        crop_greek_linesDialog.setObjectName("crop_greek_linesDialog")
        crop_greek_linesDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        crop_greek_linesDialog.resize(484, 279)
        self.buttonBox = QtWidgets.QDialogButtonBox(crop_greek_linesDialog)
        self.buttonBox.setGeometry(QtCore.QRect(260, 230, 171, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.SourceLineEdit = QtWidgets.QLineEdit(crop_greek_linesDialog)
        self.SourceLineEdit.setGeometry(QtCore.QRect(10, 50, 301, 25))
        self.SourceLineEdit.setObjectName("SourceLineEdit")
        self.SourceButton = QtWidgets.QPushButton(crop_greek_linesDialog)
        self.SourceButton.setEnabled(False)
        self.SourceButton.setGeometry(QtCore.QRect(330, 50, 101, 25))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Icons/Icons/tiff-file.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.SourceButton.setIcon(icon)
        self.SourceButton.setObjectName("SourceButton")
        self.SourceLabel = QtWidgets.QLabel(crop_greek_linesDialog)
        self.SourceLabel.setGeometry(QtCore.QRect(20, 30, 211, 17))
        self.SourceLabel.setObjectName("SourceLabel")
        self.GreekBoxFolderLineEdit = QtWidgets.QLineEdit(crop_greek_linesDialog)
        self.GreekBoxFolderLineEdit.setGeometry(QtCore.QRect(10, 110, 301, 25))
        self.GreekBoxFolderLineEdit.setObjectName("GreekBoxFolderLineEdit")
        self.GreekBoxFolderLabel = QtWidgets.QLabel(crop_greek_linesDialog)
        self.GreekBoxFolderLabel.setGeometry(QtCore.QRect(20, 90, 271, 17))
        self.GreekBoxFolderLabel.setObjectName("GreekBoxFolderLabel")
        self.GreekBoxFolderButton = QtWidgets.QPushButton(crop_greek_linesDialog)
        self.GreekBoxFolderButton.setEnabled(False)
        self.GreekBoxFolderButton.setGeometry(QtCore.QRect(330, 110, 101, 25))
        self.GreekBoxFolderButton.setIcon(icon)
        self.GreekBoxFolderButton.setObjectName("GreekBoxFolderButton")
        self.DestGreekLineEdit = QtWidgets.QLineEdit(crop_greek_linesDialog)
        self.DestGreekLineEdit.setGeometry(QtCore.QRect(10, 170, 301, 25))
        self.DestGreekLineEdit.setObjectName("DestGreekLineEdit")
        self.DestGreekButton = QtWidgets.QPushButton(crop_greek_linesDialog)
        self.DestGreekButton.setEnabled(False)
        self.DestGreekButton.setGeometry(QtCore.QRect(330, 170, 101, 25))
        self.DestGreekButton.setIcon(icon)
        self.DestGreekButton.setObjectName("DestGreekButton")
        self.DestGreekLabel = QtWidgets.QLabel(crop_greek_linesDialog)
        self.DestGreekLabel.setGeometry(QtCore.QRect(20, 150, 271, 17))
        self.DestGreekLabel.setObjectName("DestGreekLabel")
        self.defaultsrcBox = QtWidgets.QCheckBox(crop_greek_linesDialog)
        self.defaultsrcBox.setGeometry(QtCore.QRect(330, 20, 101, 23))
        self.defaultsrcBox.setChecked(True)
        self.defaultsrcBox.setObjectName("defaultsrcBox")

        self.retranslateUi(crop_greek_linesDialog)
        self.buttonBox.accepted.connect(crop_greek_linesDialog.accept)
        self.buttonBox.rejected.connect(crop_greek_linesDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(crop_greek_linesDialog)

    def retranslateUi(self, crop_greek_linesDialog):
        _translate = QtCore.QCoreApplication.translate
        crop_greek_linesDialog.setWindowTitle(_translate("crop_greek_linesDialog", "Crop Greek tif page files into tif line files"))
        self.SourceLineEdit.setPlaceholderText(_translate("crop_greek_linesDialog", "(default) working temp folder"))
        self.SourceButton.setText(_translate("crop_greek_linesDialog", "Source"))
        self.SourceLabel.setText(_translate("crop_greek_linesDialog", "Mono tif pages source folder"))
        self.GreekBoxFolderLabel.setText(_translate("crop_greek_linesDialog", "Greek linebox files folder"))
        self.GreekBoxFolderButton.setText(_translate("crop_greek_linesDialog", "Destination"))
        self.DestGreekButton.setText(_translate("crop_greek_linesDialog", "Destination"))
        self.DestGreekLabel.setText(_translate("crop_greek_linesDialog", "Greek tif lines destination folder"))
        self.defaultsrcBox.setText(_translate("crop_greek_linesDialog", "Use default"))

import UI_Icons

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    crop_greek_linesDialog = QtWidgets.QDialog()
    ui = Ui_crop_greek_linesDialog()
    ui.setupUi(crop_greek_linesDialog)
    crop_greek_linesDialog.show()
    sys.exit(app.exec_())

