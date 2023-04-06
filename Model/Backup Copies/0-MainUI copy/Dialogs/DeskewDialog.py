# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './QtDesignerUI/DeskewDialog.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(484, 259)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(290, 200, 171, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.Source = QtWidgets.QLineEdit(Dialog)
        self.Source.setGeometry(QtCore.QRect(10, 50, 301, 25))
        self.Source.setObjectName("Source")
        self.SourceButton = QtWidgets.QPushButton(Dialog)
        self.SourceButton.setEnabled(False)
        self.SourceButton.setGeometry(QtCore.QRect(330, 50, 131, 25))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Icons/Icons/tiff-file.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.SourceButton.setIcon(icon)
        self.SourceButton.setObjectName("SourceButton")
        self.DestinationButton = QtWidgets.QPushButton(Dialog)
        self.DestinationButton.setGeometry(QtCore.QRect(330, 100, 131, 25))
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/Icons/Icons/png-file.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.DestinationButton.setIcon(icon1)
        self.DestinationButton.setObjectName("DestinationButton")
        self.Destination = QtWidgets.QLineEdit(Dialog)
        self.Destination.setGeometry(QtCore.QRect(10, 100, 301, 25))
        self.Destination.setObjectName("Destination")
        self.DestinationButton_2 = QtWidgets.QPushButton(Dialog)
        self.DestinationButton_2.setGeometry(QtCore.QRect(330, 150, 131, 25))
        self.DestinationButton_2.setIcon(icon)
        self.DestinationButton_2.setObjectName("DestinationButton_2")
        self.Destination_2 = QtWidgets.QLineEdit(Dialog)
        self.Destination_2.setGeometry(QtCore.QRect(10, 150, 301, 25))
        self.Destination_2.setObjectName("Destination_2")
        self.defaultsrcBox = QtWidgets.QCheckBox(Dialog)
        self.defaultsrcBox.setGeometry(QtCore.QRect(330, 20, 101, 23))
        self.defaultsrcBox.setChecked(True)
        self.defaultsrcBox.setObjectName("defaultsrcBox")

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Deskew"))
        self.Source.setPlaceholderText(_translate("Dialog", "(default) working temp folder"))
        self.SourceButton.setText(_translate("Dialog", "tif Source File"))
        self.DestinationButton.setText(_translate("Dialog", "png Destination"))
        self.DestinationButton_2.setText(_translate("Dialog", "tif Destination"))
        self.defaultsrcBox.setText(_translate("Dialog", "Use default"))

import UI_Icons

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())

