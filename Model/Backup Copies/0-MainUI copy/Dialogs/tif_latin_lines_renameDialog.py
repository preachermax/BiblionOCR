# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './QtDesignerUI/tif_latin_lines_renameDialog.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_tiflatinrenamelinesDialog(object):
    def setupUi(self, tiflatinrenamelinesDialog):
        tiflatinrenamelinesDialog.setObjectName("tiflatinrenamelinesDialog")
        tiflatinrenamelinesDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        tiflatinrenamelinesDialog.resize(466, 237)
        tiflatinrenamelinesDialog.setWindowOpacity(5.0)
        self.buttonBox = QtWidgets.QDialogButtonBox(tiflatinrenamelinesDialog)
        self.buttonBox.setGeometry(QtCore.QRect(260, 180, 171, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.SourceLineEdit = QtWidgets.QLineEdit(tiflatinrenamelinesDialog)
        self.SourceLineEdit.setGeometry(QtCore.QRect(10, 50, 301, 25))
        self.SourceLineEdit.setObjectName("SourceLineEdit")
        self.SourceButton = QtWidgets.QPushButton(tiflatinrenamelinesDialog)
        self.SourceButton.setEnabled(False)
        self.SourceButton.setGeometry(QtCore.QRect(330, 50, 101, 25))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Icons/Icons/tiff-file.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.SourceButton.setIcon(icon)
        self.SourceButton.setObjectName("SourceButton")
        self.DestinationButton = QtWidgets.QPushButton(tiflatinrenamelinesDialog)
        self.DestinationButton.setGeometry(QtCore.QRect(330, 120, 101, 25))
        self.DestinationButton.setIcon(icon)
        self.DestinationButton.setObjectName("DestinationButton")
        self.DestinationLineEdit = QtWidgets.QLineEdit(tiflatinrenamelinesDialog)
        self.DestinationLineEdit.setGeometry(QtCore.QRect(10, 120, 301, 25))
        self.DestinationLineEdit.setObjectName("DestinationLineEdit")
        self.SourceLabel = QtWidgets.QLabel(tiflatinrenamelinesDialog)
        self.SourceLabel.setGeometry(QtCore.QRect(20, 30, 261, 17))
        self.SourceLabel.setObjectName("SourceLabel")
        self.DestinationLabel = QtWidgets.QLabel(tiflatinrenamelinesDialog)
        self.DestinationLabel.setGeometry(QtCore.QRect(20, 100, 291, 17))
        self.DestinationLabel.setObjectName("DestinationLabel")
        self.defaultsrcBox = QtWidgets.QCheckBox(tiflatinrenamelinesDialog)
        self.defaultsrcBox.setGeometry(QtCore.QRect(330, 20, 101, 23))
        self.defaultsrcBox.setChecked(True)
        self.defaultsrcBox.setObjectName("defaultsrcBox")

        self.retranslateUi(tiflatinrenamelinesDialog)
        self.buttonBox.accepted.connect(tiflatinrenamelinesDialog.accept)
        self.buttonBox.rejected.connect(tiflatinrenamelinesDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(tiflatinrenamelinesDialog)

    def retranslateUi(self, tiflatinrenamelinesDialog):
        _translate = QtCore.QCoreApplication.translate
        tiflatinrenamelinesDialog.setWindowTitle(_translate("tiflatinrenamelinesDialog", "Rename Latin tif lines"))
        self.SourceLineEdit.setPlaceholderText(_translate("tiflatinrenamelinesDialog", "(default) working temp folder"))
        self.SourceButton.setText(_translate("tiflatinrenamelinesDialog", "Source"))
        self.DestinationButton.setText(_translate("tiflatinrenamelinesDialog", "Destination"))
        self.SourceLabel.setText(_translate("tiflatinrenamelinesDialog", "Rename Latin tif lines source folder"))
        self.DestinationLabel.setText(_translate("tiflatinrenamelinesDialog", "Rename Latin tif lines destination folder"))
        self.defaultsrcBox.setText(_translate("tiflatinrenamelinesDialog", "Use default"))

import UI_Icons

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    tiflatinrenamelinesDialog = QtWidgets.QDialog()
    ui = Ui_tiflatinrenamelinesDialog()
    ui.setupUi(tiflatinrenamelinesDialog)
    tiflatinrenamelinesDialog.show()
    sys.exit(app.exec_())

