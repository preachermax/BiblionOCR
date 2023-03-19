# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './QtDesignerUI/MoveDialog.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(484, 180)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(260, 130, 171, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.Source = QtWidgets.QLineEdit(Dialog)
        self.Source.setGeometry(QtCore.QRect(10, 30, 301, 25))
        self.Source.setObjectName("Source")
        self.SourceButton = QtWidgets.QPushButton(Dialog)
        self.SourceButton.setGeometry(QtCore.QRect(330, 30, 101, 25))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Icons/Icons/pdf-extract1.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.SourceButton.setIcon(icon)
        self.SourceButton.setObjectName("SourceButton")
        self.DestinationButton = QtWidgets.QPushButton(Dialog)
        self.DestinationButton.setGeometry(QtCore.QRect(330, 80, 101, 25))
        self.DestinationButton.setIcon(icon)
        self.DestinationButton.setObjectName("DestinationButton")
        self.Destination = QtWidgets.QLineEdit(Dialog)
        self.Destination.setGeometry(QtCore.QRect(10, 80, 301, 25))
        self.Destination.setObjectName("Destination")

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Convert pdf to tif"))
        self.SourceButton.setText(_translate("Dialog", "Source"))
        self.DestinationButton.setText(_translate("Dialog", "Destination"))

import UI_Icons

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())

