# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './QtDesignerUI/latinmono2pngDialog.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_latinmono2pngDialog(object):
    def setupUi(self, latinmono2pngDialog):
        latinmono2pngDialog.setObjectName("latinmono2pngDialog")
        latinmono2pngDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        latinmono2pngDialog.resize(457, 237)
        self.buttonBox = QtWidgets.QDialogButtonBox(latinmono2pngDialog)
        self.buttonBox.setGeometry(QtCore.QRect(260, 180, 171, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.SourceLineEdit = QtWidgets.QLineEdit(latinmono2pngDialog)
        self.SourceLineEdit.setGeometry(QtCore.QRect(10, 50, 301, 25))
        self.SourceLineEdit.setObjectName("SourceLineEdit")
        self.SourceButton = QtWidgets.QPushButton(latinmono2pngDialog)
        self.SourceButton.setEnabled(False)
        self.SourceButton.setGeometry(QtCore.QRect(330, 50, 101, 25))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Icons/Icons/tiff-file.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.SourceButton.setIcon(icon)
        self.SourceButton.setObjectName("SourceButton")
        self.DestinationButton = QtWidgets.QPushButton(latinmono2pngDialog)
        self.DestinationButton.setGeometry(QtCore.QRect(330, 120, 101, 25))
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/Icons/Icons/png-file.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.DestinationButton.setIcon(icon1)
        self.DestinationButton.setObjectName("DestinationButton")
        self.DestinationLineEdit = QtWidgets.QLineEdit(latinmono2pngDialog)
        self.DestinationLineEdit.setGeometry(QtCore.QRect(10, 120, 301, 25))
        self.DestinationLineEdit.setObjectName("DestinationLineEdit")
        self.SourceLabel = QtWidgets.QLabel(latinmono2pngDialog)
        self.SourceLabel.setGeometry(QtCore.QRect(20, 30, 251, 17))
        self.SourceLabel.setObjectName("SourceLabel")
        self.DestinationLabel = QtWidgets.QLabel(latinmono2pngDialog)
        self.DestinationLabel.setGeometry(QtCore.QRect(20, 100, 291, 17))
        self.DestinationLabel.setObjectName("DestinationLabel")
        self.defaultsrcBox = QtWidgets.QCheckBox(latinmono2pngDialog)
        self.defaultsrcBox.setGeometry(QtCore.QRect(330, 20, 101, 23))
        self.defaultsrcBox.setChecked(True)
        self.defaultsrcBox.setObjectName("defaultsrcBox")

        self.retranslateUi(latinmono2pngDialog)
        self.buttonBox.accepted.connect(latinmono2pngDialog.accept)
        self.buttonBox.rejected.connect(latinmono2pngDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(latinmono2pngDialog)

    def retranslateUi(self, latinmono2pngDialog):
        _translate = QtCore.QCoreApplication.translate
        latinmono2pngDialog.setWindowTitle(_translate("latinmono2pngDialog", "Convert Latin mono tif pages into png pages"))
        self.SourceLineEdit.setPlaceholderText(_translate("latinmono2pngDialog", "(default) working temp folder"))
        self.SourceButton.setText(_translate("latinmono2pngDialog", "Source"))
        self.DestinationButton.setText(_translate("latinmono2pngDialog", "Destination"))
        self.SourceLabel.setText(_translate("latinmono2pngDialog", "Latin mono tif pages source folder"))
        self.DestinationLabel.setText(_translate("latinmono2pngDialog", "Latin mono png pages destination folder"))
        self.defaultsrcBox.setText(_translate("latinmono2pngDialog", "Use default"))

import UI_Icons

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    latinmono2pngDialog = QtWidgets.QDialog()
    ui = Ui_latinmono2pngDialog()
    ui.setupUi(latinmono2pngDialog)
    latinmono2pngDialog.show()
    sys.exit(app.exec_())

