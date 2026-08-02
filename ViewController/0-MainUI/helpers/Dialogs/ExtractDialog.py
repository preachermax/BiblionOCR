# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './QtDesignerUI/ExtractDialog.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_ExtractDialog(object):
    def setupUi(self, ExtractDialog):
        ExtractDialog.setObjectName("ExtractDialog")
        ExtractDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        ExtractDialog.resize(484, 294)
        self.buttonBox = QtWidgets.QDialogButtonBox(ExtractDialog)
        self.buttonBox.setGeometry(QtCore.QRect(260, 210, 171, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.SourceLineEdit = QtWidgets.QLineEdit(ExtractDialog)
        self.SourceLineEdit.setGeometry(QtCore.QRect(10, 50, 301, 25))
        self.SourceLineEdit.setObjectName("SourceLineEdit")
        self.SourceButton = QtWidgets.QPushButton(ExtractDialog)
        self.SourceButton.setEnabled(False)
        self.SourceButton.setGeometry(QtCore.QRect(330, 50, 141, 25))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Icons/Icons/pdf-extract1.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.SourceButton.setIcon(icon)
        self.SourceButton.setObjectName("SourceButton")
        self.FirstPageLineEdit = QtWidgets.QLineEdit(ExtractDialog)
        self.FirstPageLineEdit.setGeometry(QtCore.QRect(160, 100, 31, 25))
        self.FirstPageLineEdit.setObjectName("FirstPageLineEdit")
        self.FirstPageLabel = QtWidgets.QLabel(ExtractDialog)
        self.FirstPageLabel.setGeometry(QtCore.QRect(20, 100, 131, 17))
        self.FirstPageLabel.setObjectName("FirstPageLabel")
        self.LastPageLineEdit = QtWidgets.QLineEdit(ExtractDialog)
        self.LastPageLineEdit.setGeometry(QtCore.QRect(280, 100, 31, 25))
        self.LastPageLineEdit.setObjectName("LastPageLineEdit")
        self.LastPageLabel = QtWidgets.QLabel(ExtractDialog)
        self.LastPageLabel.setGeometry(QtCore.QRect(210, 100, 71, 17))
        self.LastPageLabel.setObjectName("LastPageLabel")
        self.DestinationButton = QtWidgets.QPushButton(ExtractDialog)
        self.DestinationButton.setEnabled(False)
        self.DestinationButton.setGeometry(QtCore.QRect(330, 150, 141, 25))
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/Icons/Icons/folder-open-image.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.DestinationButton.setIcon(icon1)
        self.DestinationButton.setObjectName("DestinationButton")
        self.DestinationLineEdit = QtWidgets.QLineEdit(ExtractDialog)
        self.DestinationLineEdit.setGeometry(QtCore.QRect(10, 150, 301, 25))
        self.DestinationLineEdit.setObjectName("DestinationLineEdit")
        self.SourceLabel = QtWidgets.QLabel(ExtractDialog)
        self.SourceLabel.setGeometry(QtCore.QRect(20, 30, 121, 17))
        self.SourceLabel.setObjectName("SourceLabel")
        self.DestinationLabel = QtWidgets.QLabel(ExtractDialog)
        self.DestinationLabel.setGeometry(QtCore.QRect(20, 180, 131, 17))
        self.DestinationLabel.setObjectName("DestinationLabel")
        self.defaultsrcBox = QtWidgets.QCheckBox(ExtractDialog)
        self.defaultsrcBox.setGeometry(QtCore.QRect(330, 20, 101, 23))
        self.defaultsrcBox.setChecked(True)
        self.defaultsrcBox.setObjectName("defaultsrcBox")

        self.retranslateUi(ExtractDialog)
        self.buttonBox.accepted.connect(ExtractDialog.accept)
        self.buttonBox.rejected.connect(ExtractDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(ExtractDialog)

    def retranslateUi(self, ExtractDialog):
        _translate = QtCore.QCoreApplication.translate
        ExtractDialog.setWindowTitle(_translate("ExtractDialog", "Exract pdf pages"))
        self.SourceLineEdit.setPlaceholderText(_translate("ExtractDialog", "(default) working temp folder"))
        self.SourceButton.setText(_translate("ExtractDialog", "Select source"))
        self.FirstPageLabel.setText(_translate("ExtractDialog", "Extract from page:"))
        self.LastPageLabel.setText(_translate("ExtractDialog", "to page:"))
        self.DestinationButton.setText(_translate("ExtractDialog", "Select destination"))
        self.DestinationLineEdit.setPlaceholderText(_translate("ExtractDialog", "(default) working temp folder"))
        self.SourceLabel.setText(_translate("ExtractDialog", "Pdf source file"))
        self.DestinationLabel.setText(_translate("ExtractDialog", "Pdf pages location"))
        self.defaultsrcBox.setText(_translate("ExtractDialog", "Use default"))

import UI_Icons

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ExtractDialog = QtWidgets.QDialog()
    ui = Ui_ExtractDialog()
    ui.setupUi(ExtractDialog)
    ExtractDialog.show()
    sys.exit(app.exec_())

