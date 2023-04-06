# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './QtDesignerUI/greekmono2pngDialog.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_greekmono2pngDialog(object):
    def setupUi(self, greekmono2pngDialog):
        greekmono2pngDialog.setObjectName("greekmono2pngDialog")
        greekmono2pngDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        greekmono2pngDialog.resize(457, 237)
        self.buttonBox = QtWidgets.QDialogButtonBox(greekmono2pngDialog)
        self.buttonBox.setGeometry(QtCore.QRect(260, 180, 171, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.SourceLineEdit = QtWidgets.QLineEdit(greekmono2pngDialog)
        self.SourceLineEdit.setGeometry(QtCore.QRect(10, 50, 301, 25))
        self.SourceLineEdit.setObjectName("SourceLineEdit")
        self.SourceButton = QtWidgets.QPushButton(greekmono2pngDialog)
        self.SourceButton.setEnabled(False)
        self.SourceButton.setGeometry(QtCore.QRect(330, 50, 101, 25))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Icons/Icons/tiff-file.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.SourceButton.setIcon(icon)
        self.SourceButton.setObjectName("SourceButton")
        self.DestinationButton = QtWidgets.QPushButton(greekmono2pngDialog)
        self.DestinationButton.setEnabled(False)
        self.DestinationButton.setGeometry(QtCore.QRect(330, 120, 101, 25))
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/Icons/Icons/png-file.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.DestinationButton.setIcon(icon1)
        self.DestinationButton.setObjectName("DestinationButton")
        self.DestinationLineEdit = QtWidgets.QLineEdit(greekmono2pngDialog)
        self.DestinationLineEdit.setGeometry(QtCore.QRect(10, 120, 301, 25))
        self.DestinationLineEdit.setObjectName("DestinationLineEdit")
        self.SourceLabel = QtWidgets.QLabel(greekmono2pngDialog)
        self.SourceLabel.setGeometry(QtCore.QRect(20, 30, 251, 17))
        self.SourceLabel.setObjectName("SourceLabel")
        self.DestinationLabel = QtWidgets.QLabel(greekmono2pngDialog)
        self.DestinationLabel.setGeometry(QtCore.QRect(20, 100, 291, 17))
        self.DestinationLabel.setObjectName("DestinationLabel")
        self.defaultsrcBox = QtWidgets.QCheckBox(greekmono2pngDialog)
        self.defaultsrcBox.setGeometry(QtCore.QRect(330, 20, 101, 23))
        self.defaultsrcBox.setChecked(True)
        self.defaultsrcBox.setObjectName("defaultsrcBox")

        self.retranslateUi(greekmono2pngDialog)
        self.buttonBox.accepted.connect(greekmono2pngDialog.accept)
        self.buttonBox.rejected.connect(greekmono2pngDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(greekmono2pngDialog)

    def retranslateUi(self, greekmono2pngDialog):
        _translate = QtCore.QCoreApplication.translate
        greekmono2pngDialog.setWindowTitle(_translate("greekmono2pngDialog", "Convert  Greek mono tif pages into png pages"))
        self.SourceLineEdit.setPlaceholderText(_translate("greekmono2pngDialog", "(default) working temp folder"))
        self.SourceButton.setText(_translate("greekmono2pngDialog", "Source"))
        self.DestinationButton.setText(_translate("greekmono2pngDialog", "Destination"))
        self.DestinationLineEdit.setPlaceholderText(_translate("greekmono2pngDialog", "(default) working temp folder"))
        self.SourceLabel.setText(_translate("greekmono2pngDialog", "Greek mono tif pages source folder"))
        self.DestinationLabel.setText(_translate("greekmono2pngDialog", "Greek mono png pages destination folder"))
        self.defaultsrcBox.setText(_translate("greekmono2pngDialog", "Use default"))

import UI_Icons

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    greekmono2pngDialog = QtWidgets.QDialog()
    ui = Ui_greekmono2pngDialog()
    ui.setupUi(greekmono2pngDialog)
    greekmono2pngDialog.show()
    sys.exit(app.exec_())

