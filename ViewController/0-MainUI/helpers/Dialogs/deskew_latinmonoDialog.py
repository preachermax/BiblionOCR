# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './QtDesignerUI/deskew_latinmonoDialog.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_deskew_latinmonoDialog(object):
    def setupUi(self, deskew_latinmonoDialog):
        deskew_latinmonoDialog.setObjectName("deskew_latinmonoDialog")
        deskew_latinmonoDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        deskew_latinmonoDialog.resize(484, 305)
        self.buttonBox = QtWidgets.QDialogButtonBox(deskew_latinmonoDialog)
        self.buttonBox.setGeometry(QtCore.QRect(260, 230, 171, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.SourceLineEdit = QtWidgets.QLineEdit(deskew_latinmonoDialog)
        self.SourceLineEdit.setGeometry(QtCore.QRect(10, 50, 321, 25))
        self.SourceLineEdit.setObjectName("SourceLineEdit")
        self.SourceButton = QtWidgets.QPushButton(deskew_latinmonoDialog)
        self.SourceButton.setEnabled(False)
        self.SourceButton.setGeometry(QtCore.QRect(360, 50, 101, 25))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Icons/Icons/tiff-file.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.SourceButton.setIcon(icon)
        self.SourceButton.setObjectName("SourceButton")
        self.DestPngButton = QtWidgets.QPushButton(deskew_latinmonoDialog)
        self.DestPngButton.setGeometry(QtCore.QRect(360, 170, 101, 25))
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/Icons/Icons/png-file.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.DestPngButton.setIcon(icon1)
        self.DestPngButton.setObjectName("DestPngButton")
        self.DestPngLineEdit = QtWidgets.QLineEdit(deskew_latinmonoDialog)
        self.DestPngLineEdit.setGeometry(QtCore.QRect(10, 170, 321, 25))
        self.DestPngLineEdit.setObjectName("DestPngLineEdit")
        self.SourceLabel = QtWidgets.QLabel(deskew_latinmonoDialog)
        self.SourceLabel.setGeometry(QtCore.QRect(20, 30, 251, 17))
        self.SourceLabel.setObjectName("SourceLabel")
        self.DestPngLabel = QtWidgets.QLabel(deskew_latinmonoDialog)
        self.DestPngLabel.setGeometry(QtCore.QRect(20, 150, 321, 17))
        self.DestPngLabel.setObjectName("DestPngLabel")
        self.DestTifLineEdit = QtWidgets.QLineEdit(deskew_latinmonoDialog)
        self.DestTifLineEdit.setGeometry(QtCore.QRect(10, 110, 321, 25))
        self.DestTifLineEdit.setObjectName("DestTifLineEdit")
        self.DestTifLabel = QtWidgets.QLabel(deskew_latinmonoDialog)
        self.DestTifLabel.setGeometry(QtCore.QRect(20, 90, 311, 17))
        self.DestTifLabel.setObjectName("DestTifLabel")
        self.DestTifButton = QtWidgets.QPushButton(deskew_latinmonoDialog)
        self.DestTifButton.setGeometry(QtCore.QRect(360, 110, 101, 25))
        self.DestTifButton.setIcon(icon)
        self.DestTifButton.setObjectName("DestTifButton")
        self.defaultsrcBox = QtWidgets.QCheckBox(deskew_latinmonoDialog)
        self.defaultsrcBox.setGeometry(QtCore.QRect(360, 20, 101, 23))
        self.defaultsrcBox.setChecked(True)
        self.defaultsrcBox.setObjectName("defaultsrcBox")

        self.retranslateUi(deskew_latinmonoDialog)
        self.buttonBox.accepted.connect(deskew_latinmonoDialog.accept)
        self.buttonBox.rejected.connect(deskew_latinmonoDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(deskew_latinmonoDialog)

    def retranslateUi(self, deskew_latinmonoDialog):
        _translate = QtCore.QCoreApplication.translate
        deskew_latinmonoDialog.setWindowTitle(_translate("deskew_latinmonoDialog", "Deskew Latin tif and png mono pages"))
        self.SourceLineEdit.setPlaceholderText(_translate("deskew_latinmonoDialog", "(default) working temp folder"))
        self.SourceButton.setText(_translate("deskew_latinmonoDialog", "Source"))
        self.DestPngButton.setText(_translate("deskew_latinmonoDialog", "Destination"))
        self.SourceLabel.setText(_translate("deskew_latinmonoDialog", "Latin mono tif pages source folder"))
        self.DestPngLabel.setText(_translate("deskew_latinmonoDialog", "Deskewed Latin png pages destination folder"))
        self.DestTifLabel.setText(_translate("deskew_latinmonoDialog", "Deskewed Latin tif pages destination folder"))
        self.DestTifButton.setText(_translate("deskew_latinmonoDialog", "Destination"))
        self.defaultsrcBox.setText(_translate("deskew_latinmonoDialog", "Use default"))

import UI_Icons

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    deskew_latinmonoDialog = QtWidgets.QDialog()
    ui = Ui_deskew_latinmonoDialog()
    ui.setupUi(deskew_latinmonoDialog)
    deskew_latinmonoDialog.show()
    sys.exit(app.exec_())

