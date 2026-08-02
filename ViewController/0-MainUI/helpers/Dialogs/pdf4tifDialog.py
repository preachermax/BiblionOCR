# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './QtDesignerUI/pdf4tifDialog.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_pdf4tifDialog(object):
    def setupUi(self, pdf4tifDialog):
        pdf4tifDialog.setObjectName("pdf4tifDialog")
        pdf4tifDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        pdf4tifDialog.resize(484, 235)
        self.buttonBox = QtWidgets.QDialogButtonBox(pdf4tifDialog)
        self.buttonBox.setGeometry(QtCore.QRect(260, 180, 171, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.SourceLineEdit = QtWidgets.QLineEdit(pdf4tifDialog)
        self.SourceLineEdit.setGeometry(QtCore.QRect(10, 50, 301, 25))
        self.SourceLineEdit.setObjectName("SourceLineEdit")
        self.SourceButton = QtWidgets.QPushButton(pdf4tifDialog)
        self.SourceButton.setEnabled(False)
        self.SourceButton.setGeometry(QtCore.QRect(330, 50, 101, 25))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Icons/Icons/pdf-extract1.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.SourceButton.setIcon(icon)
        self.SourceButton.setObjectName("SourceButton")
        self.DestinationButton = QtWidgets.QPushButton(pdf4tifDialog)
        self.DestinationButton.setEnabled(False)
        self.DestinationButton.setGeometry(QtCore.QRect(330, 120, 101, 25))
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/Icons/Icons/pdf4tiff.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.DestinationButton.setIcon(icon1)
        self.DestinationButton.setObjectName("DestinationButton")
        self.DestinationLineEdit = QtWidgets.QLineEdit(pdf4tifDialog)
        self.DestinationLineEdit.setGeometry(QtCore.QRect(10, 120, 301, 25))
        self.DestinationLineEdit.setObjectName("DestinationLineEdit")
        self.SourceLabel = QtWidgets.QLabel(pdf4tifDialog)
        self.SourceLabel.setGeometry(QtCore.QRect(20, 30, 171, 17))
        self.SourceLabel.setObjectName("SourceLabel")
        self.DestinationLabel = QtWidgets.QLabel(pdf4tifDialog)
        self.DestinationLabel.setGeometry(QtCore.QRect(20, 100, 211, 17))
        self.DestinationLabel.setObjectName("DestinationLabel")
        self.defaultsrcBox = QtWidgets.QCheckBox(pdf4tifDialog)
        self.defaultsrcBox.setGeometry(QtCore.QRect(330, 20, 101, 23))
        self.defaultsrcBox.setChecked(True)
        self.defaultsrcBox.setObjectName("defaultsrcBox")

        self.retranslateUi(pdf4tifDialog)
        self.buttonBox.accepted.connect(pdf4tifDialog.accept)
        self.buttonBox.rejected.connect(pdf4tifDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(pdf4tifDialog)

    def retranslateUi(self, pdf4tifDialog):
        _translate = QtCore.QCoreApplication.translate
        pdf4tifDialog.setWindowTitle(_translate("pdf4tifDialog", "Extract pdf pages for tif"))
        self.SourceLineEdit.setPlaceholderText(_translate("pdf4tifDialog", "(default) working temp folder"))
        self.SourceButton.setText(_translate("pdf4tifDialog", "Source"))
        self.DestinationButton.setText(_translate("pdf4tifDialog", "Destination"))
        self.SourceLabel.setText(_translate("pdf4tifDialog", "pdf Pages Source File"))
        self.DestinationLabel.setText(_translate("pdf4tifDialog", "pdf Pages Destination Folder"))
        self.defaultsrcBox.setText(_translate("pdf4tifDialog", "Use default"))

import UI_Icons

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    pdf4tifDialog = QtWidgets.QDialog()
    ui = Ui_pdf4tifDialog()
    ui.setupUi(pdf4tifDialog)
    pdf4tifDialog.show()
    sys.exit(app.exec_())

