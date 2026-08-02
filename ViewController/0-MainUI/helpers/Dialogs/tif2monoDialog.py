# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './QtDesignerUI/tif2monoDialog.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_tif2monoDialog(object):
    def setupUi(self, tif2monoDialog):
        tif2monoDialog.setObjectName("tif2monoDialog")
        tif2monoDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        tif2monoDialog.resize(484, 237)
        self.buttonBox = QtWidgets.QDialogButtonBox(tif2monoDialog)
        self.buttonBox.setGeometry(QtCore.QRect(260, 180, 171, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.SourceLineEdit = QtWidgets.QLineEdit(tif2monoDialog)
        self.SourceLineEdit.setGeometry(QtCore.QRect(10, 50, 301, 25))
        self.SourceLineEdit.setObjectName("SourceLineEdit")
        self.SourceButton = QtWidgets.QPushButton(tif2monoDialog)
        self.SourceButton.setEnabled(False)
        self.SourceButton.setGeometry(QtCore.QRect(330, 50, 101, 25))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Icons/Icons/tiff-icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.SourceButton.setIcon(icon)
        self.SourceButton.setObjectName("SourceButton")
        self.DestinationButton = QtWidgets.QPushButton(tif2monoDialog)
        self.DestinationButton.setEnabled(False)
        self.DestinationButton.setGeometry(QtCore.QRect(330, 120, 101, 25))
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/Icons/Icons/tiff-file.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.DestinationButton.setIcon(icon1)
        self.DestinationButton.setObjectName("DestinationButton")
        self.DestinationLineEdit = QtWidgets.QLineEdit(tif2monoDialog)
        self.DestinationLineEdit.setGeometry(QtCore.QRect(10, 120, 301, 25))
        self.DestinationLineEdit.setObjectName("DestinationLineEdit")
        self.SourceLabel = QtWidgets.QLabel(tif2monoDialog)
        self.SourceLabel.setGeometry(QtCore.QRect(20, 30, 171, 17))
        self.SourceLabel.setObjectName("SourceLabel")
        self.DestinationLabel = QtWidgets.QLabel(tif2monoDialog)
        self.DestinationLabel.setGeometry(QtCore.QRect(20, 100, 271, 17))
        self.DestinationLabel.setObjectName("DestinationLabel")
        self.defaultsrcBox = QtWidgets.QCheckBox(tif2monoDialog)
        self.defaultsrcBox.setGeometry(QtCore.QRect(330, 20, 101, 23))
        self.defaultsrcBox.setChecked(True)
        self.defaultsrcBox.setObjectName("defaultsrcBox")

        self.retranslateUi(tif2monoDialog)
        self.buttonBox.accepted.connect(tif2monoDialog.accept)
        self.buttonBox.rejected.connect(tif2monoDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(tif2monoDialog)

    def retranslateUi(self, tif2monoDialog):
        _translate = QtCore.QCoreApplication.translate
        tif2monoDialog.setWindowTitle(_translate("tif2monoDialog", "Convert tif pages into indexed mono pages"))
        self.SourceLineEdit.setPlaceholderText(_translate("tif2monoDialog", "(default) working temp folder"))
        self.SourceButton.setText(_translate("tif2monoDialog", "Source"))
        self.DestinationButton.setText(_translate("tif2monoDialog", "Destination"))
        self.DestinationLineEdit.setPlaceholderText(_translate("tif2monoDialog", "(default) working temp folder"))
        self.SourceLabel.setText(_translate("tif2monoDialog", "Tif pages source folder"))
        self.DestinationLabel.setText(_translate("tif2monoDialog", "Indexed mono pages destination folder"))
        self.defaultsrcBox.setText(_translate("tif2monoDialog", "Use default"))

import UI_Icons

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    tif2monoDialog = QtWidgets.QDialog()
    ui = Ui_tif2monoDialog()
    ui.setupUi(tif2monoDialog)
    tif2monoDialog.show()
    sys.exit(app.exec_())

