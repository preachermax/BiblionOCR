# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './QtDesignerUI/tif_latin_lines_moveDialog.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_tiflatinmovelinesDialog(object):
    def setupUi(self, tiflatinmovelinesDialog):
        tiflatinmovelinesDialog.setObjectName("tiflatinmovelinesDialog")
        tiflatinmovelinesDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        tiflatinmovelinesDialog.resize(466, 237)
        tiflatinmovelinesDialog.setWindowOpacity(5.0)
        self.buttonBox = QtWidgets.QDialogButtonBox(tiflatinmovelinesDialog)
        self.buttonBox.setGeometry(QtCore.QRect(260, 180, 171, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.SourceLineEdit = QtWidgets.QLineEdit(tiflatinmovelinesDialog)
        self.SourceLineEdit.setGeometry(QtCore.QRect(10, 50, 301, 25))
        self.SourceLineEdit.setObjectName("SourceLineEdit")
        self.SourceButton = QtWidgets.QPushButton(tiflatinmovelinesDialog)
        self.SourceButton.setEnabled(False)
        self.SourceButton.setGeometry(QtCore.QRect(330, 50, 101, 25))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Icons/Icons/tiff-file.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.SourceButton.setIcon(icon)
        self.SourceButton.setObjectName("SourceButton")
        self.DestinationButton = QtWidgets.QPushButton(tiflatinmovelinesDialog)
        self.DestinationButton.setGeometry(QtCore.QRect(330, 120, 101, 25))
        self.DestinationButton.setIcon(icon)
        self.DestinationButton.setObjectName("DestinationButton")
        self.DestinationLineEdit = QtWidgets.QLineEdit(tiflatinmovelinesDialog)
        self.DestinationLineEdit.setGeometry(QtCore.QRect(10, 120, 301, 25))
        self.DestinationLineEdit.setObjectName("DestinationLineEdit")
        self.SourceLabel = QtWidgets.QLabel(tiflatinmovelinesDialog)
        self.SourceLabel.setGeometry(QtCore.QRect(20, 30, 261, 17))
        self.SourceLabel.setObjectName("SourceLabel")
        self.DestinationLabel = QtWidgets.QLabel(tiflatinmovelinesDialog)
        self.DestinationLabel.setGeometry(QtCore.QRect(20, 100, 291, 17))
        self.DestinationLabel.setObjectName("DestinationLabel")
        self.defaultsrcBox = QtWidgets.QCheckBox(tiflatinmovelinesDialog)
        self.defaultsrcBox.setGeometry(QtCore.QRect(330, 20, 101, 23))
        self.defaultsrcBox.setChecked(True)
        self.defaultsrcBox.setObjectName("defaultsrcBox")

        self.retranslateUi(tiflatinmovelinesDialog)
        self.buttonBox.accepted.connect(tiflatinmovelinesDialog.accept)
        self.buttonBox.rejected.connect(tiflatinmovelinesDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(tiflatinmovelinesDialog)

    def retranslateUi(self, tiflatinmovelinesDialog):
        _translate = QtCore.QCoreApplication.translate
        tiflatinmovelinesDialog.setWindowTitle(_translate("tiflatinmovelinesDialog", "Move Latin tif lines"))
        self.SourceLineEdit.setPlaceholderText(_translate("tiflatinmovelinesDialog", "(default) working temp folder"))
        self.SourceButton.setText(_translate("tiflatinmovelinesDialog", "Source"))
        self.DestinationButton.setText(_translate("tiflatinmovelinesDialog", "Destination"))
        self.SourceLabel.setText(_translate("tiflatinmovelinesDialog", "Move Latin tif lines source folder"))
        self.DestinationLabel.setText(_translate("tiflatinmovelinesDialog", "Move Latin tif lines destination folder"))
        self.defaultsrcBox.setText(_translate("tiflatinmovelinesDialog", "Use default"))

import UI_Icons

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    tiflatinmovelinesDialog = QtWidgets.QDialog()
    ui = Ui_tiflatinmovelinesDialog()
    ui.setupUi(tiflatinmovelinesDialog)
    tiflatinmovelinesDialog.show()
    sys.exit(app.exec_())

