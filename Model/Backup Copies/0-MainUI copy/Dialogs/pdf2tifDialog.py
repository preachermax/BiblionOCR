# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './QtDesignerUI/pdf2tifDialog.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_pdf2tifDialog(object):
    def setupUi(self, pdf2tifDialog):
        pdf2tifDialog.setObjectName("pdf2tifDialog")
        pdf2tifDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        pdf2tifDialog.resize(484, 273)
        self.buttonBox = QtWidgets.QDialogButtonBox(pdf2tifDialog)
        self.buttonBox.setGeometry(QtCore.QRect(260, 210, 171, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.SourceLineEdit = QtWidgets.QLineEdit(pdf2tifDialog)
        self.SourceLineEdit.setGeometry(QtCore.QRect(10, 50, 301, 25))
        self.SourceLineEdit.setObjectName("SourceLineEdit")
        self.SourceButton = QtWidgets.QPushButton(pdf2tifDialog)
        self.SourceButton.setEnabled(False)
        self.SourceButton.setGeometry(QtCore.QRect(330, 50, 101, 25))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Icons/Icons/pdf4tiff.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.SourceButton.setIcon(icon)
        self.SourceButton.setObjectName("SourceButton")
        self.DestinationButton = QtWidgets.QPushButton(pdf2tifDialog)
        self.DestinationButton.setEnabled(False)
        self.DestinationButton.setGeometry(QtCore.QRect(330, 150, 101, 25))
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/Icons/Icons/pdf2tiff.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.DestinationButton.setIcon(icon1)
        self.DestinationButton.setObjectName("DestinationButton")
        self.DestinationLineEdit = QtWidgets.QLineEdit(pdf2tifDialog)
        self.DestinationLineEdit.setGeometry(QtCore.QRect(10, 150, 301, 25))
        self.DestinationLineEdit.setObjectName("DestinationLineEdit")
        self.SourceLabel = QtWidgets.QLabel(pdf2tifDialog)
        self.SourceLabel.setGeometry(QtCore.QRect(20, 30, 171, 17))
        self.SourceLabel.setObjectName("SourceLabel")
        self.DestinationLabel = QtWidgets.QLabel(pdf2tifDialog)
        self.DestinationLabel.setGeometry(QtCore.QRect(20, 180, 211, 17))
        self.DestinationLabel.setObjectName("DestinationLabel")
        self.StartPageLabel = QtWidgets.QLabel(pdf2tifDialog)
        self.StartPageLabel.setGeometry(QtCore.QRect(20, 100, 241, 20))
        self.StartPageLabel.setObjectName("StartPageLabel")
        self.StartPageLineEdit = QtWidgets.QLineEdit(pdf2tifDialog)
        self.StartPageLineEdit.setGeometry(QtCore.QRect(280, 100, 31, 25))
        self.StartPageLineEdit.setAlignment(QtCore.Qt.AlignCenter)
        self.StartPageLineEdit.setObjectName("StartPageLineEdit")
        self.defaultsrcBox = QtWidgets.QCheckBox(pdf2tifDialog)
        self.defaultsrcBox.setGeometry(QtCore.QRect(330, 20, 101, 23))
        self.defaultsrcBox.setChecked(True)
        self.defaultsrcBox.setObjectName("defaultsrcBox")

        self.retranslateUi(pdf2tifDialog)
        self.buttonBox.accepted.connect(pdf2tifDialog.accept)
        self.buttonBox.rejected.connect(pdf2tifDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(pdf2tifDialog)

    def retranslateUi(self, pdf2tifDialog):
        _translate = QtCore.QCoreApplication.translate
        pdf2tifDialog.setWindowTitle(_translate("pdf2tifDialog", "Convert pdf pages into tif files"))
        self.SourceLineEdit.setPlaceholderText(_translate("pdf2tifDialog", "(default) working temp folder"))
        self.SourceButton.setText(_translate("pdf2tifDialog", "Source"))
        self.DestinationButton.setText(_translate("pdf2tifDialog", "Destination"))
        self.SourceLabel.setText(_translate("pdf2tifDialog", "Pdf pages source folder"))
        self.DestinationLabel.setText(_translate("pdf2tifDialog", "Pdf pages destination folder"))
        self.StartPageLabel.setText(_translate("pdf2tifDialog", "Renumber tif files starting at page:"))
        self.defaultsrcBox.setText(_translate("pdf2tifDialog", "Use default"))

import UI_Icons

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    pdf2tifDialog = QtWidgets.QDialog()
    ui = Ui_pdf2tifDialog()
    ui.setupUi(pdf2tifDialog)
    pdf2tifDialog.show()
    sys.exit(app.exec_())

