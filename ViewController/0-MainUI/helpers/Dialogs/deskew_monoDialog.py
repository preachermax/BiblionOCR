# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './QtDesignerUI/deskew_monoDialog.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_deskew_monoDialog(object):
    def setupUi(self, deskew_monoDialog):
        deskew_monoDialog.setObjectName("deskew_monoDialog")
        deskew_monoDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        deskew_monoDialog.resize(484, 305)
        self.buttonBox = QtWidgets.QDialogButtonBox(deskew_monoDialog)
        self.buttonBox.setGeometry(QtCore.QRect(260, 230, 171, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.SourceLineEdit = QtWidgets.QLineEdit(deskew_monoDialog)
        self.SourceLineEdit.setGeometry(QtCore.QRect(10, 50, 301, 25))
        self.SourceLineEdit.setObjectName("SourceLineEdit")
        self.SourceButton = QtWidgets.QPushButton(deskew_monoDialog)
        self.SourceButton.setEnabled(False)
        self.SourceButton.setGeometry(QtCore.QRect(330, 50, 101, 25))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Icons/Icons/tiff-file.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.SourceButton.setIcon(icon)
        self.SourceButton.setObjectName("SourceButton")
        self.DestPngButton = QtWidgets.QPushButton(deskew_monoDialog)
        self.DestPngButton.setEnabled(False)
        self.DestPngButton.setGeometry(QtCore.QRect(330, 170, 101, 25))
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/Icons/Icons/png-file.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.DestPngButton.setIcon(icon1)
        self.DestPngButton.setObjectName("DestPngButton")
        self.DestPngLineEdit = QtWidgets.QLineEdit(deskew_monoDialog)
        self.DestPngLineEdit.setGeometry(QtCore.QRect(10, 170, 301, 25))
        self.DestPngLineEdit.setObjectName("DestPngLineEdit")
        self.SourceLabel = QtWidgets.QLabel(deskew_monoDialog)
        self.SourceLabel.setGeometry(QtCore.QRect(20, 30, 201, 17))
        self.SourceLabel.setObjectName("SourceLabel")
        self.DestPngLabel = QtWidgets.QLabel(deskew_monoDialog)
        self.DestPngLabel.setGeometry(QtCore.QRect(20, 150, 271, 17))
        self.DestPngLabel.setObjectName("DestPngLabel")
        self.DestTifLineEdit = QtWidgets.QLineEdit(deskew_monoDialog)
        self.DestTifLineEdit.setGeometry(QtCore.QRect(10, 110, 301, 25))
        self.DestTifLineEdit.setObjectName("DestTifLineEdit")
        self.DestTifLabel = QtWidgets.QLabel(deskew_monoDialog)
        self.DestTifLabel.setGeometry(QtCore.QRect(20, 90, 271, 17))
        self.DestTifLabel.setObjectName("DestTifLabel")
        self.DestTifButton = QtWidgets.QPushButton(deskew_monoDialog)
        self.DestTifButton.setEnabled(False)
        self.DestTifButton.setGeometry(QtCore.QRect(330, 110, 101, 25))
        self.DestTifButton.setIcon(icon)
        self.DestTifButton.setObjectName("DestTifButton")
        self.defaultsrcBox = QtWidgets.QCheckBox(deskew_monoDialog)
        self.defaultsrcBox.setGeometry(QtCore.QRect(330, 20, 101, 23))
        self.defaultsrcBox.setChecked(True)
        self.defaultsrcBox.setObjectName("defaultsrcBox")

        self.retranslateUi(deskew_monoDialog)
        self.buttonBox.accepted.connect(deskew_monoDialog.accept)
        self.buttonBox.rejected.connect(deskew_monoDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(deskew_monoDialog)

    def retranslateUi(self, deskew_monoDialog):
        _translate = QtCore.QCoreApplication.translate
        deskew_monoDialog.setWindowTitle(_translate("deskew_monoDialog", "Deskew  tif and png mono pages"))
        self.SourceLineEdit.setPlaceholderText(_translate("deskew_monoDialog", "(default) working temp folder"))
        self.SourceButton.setText(_translate("deskew_monoDialog", "Source"))
        self.DestPngButton.setText(_translate("deskew_monoDialog", "Destination"))
        self.SourceLabel.setText(_translate("deskew_monoDialog", "Mono tif pages source folder"))
        self.DestPngLabel.setText(_translate("deskew_monoDialog", "Deskewed png pages destination folder"))
        self.DestTifLabel.setText(_translate("deskew_monoDialog", "Deskewed tif pages destination folder"))
        self.DestTifButton.setText(_translate("deskew_monoDialog", "Destination"))
        self.defaultsrcBox.setText(_translate("deskew_monoDialog", "Use default"))

import UI_Icons

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    deskew_monoDialog = QtWidgets.QDialog()
    ui = Ui_deskew_monoDialog()
    ui.setupUi(deskew_monoDialog)
    deskew_monoDialog.show()
    sys.exit(app.exec_())

