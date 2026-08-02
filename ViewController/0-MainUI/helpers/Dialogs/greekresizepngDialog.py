# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './QtDesignerUI/greekresizepngDialog.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_greekresizepngDialog(object):
    def setupUi(self, greekresizepngDialog):
        greekresizepngDialog.setObjectName("greekresizepngDialog")
        greekresizepngDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        greekresizepngDialog.resize(466, 237)
        self.buttonBox = QtWidgets.QDialogButtonBox(greekresizepngDialog)
        self.buttonBox.setGeometry(QtCore.QRect(260, 180, 171, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.SourceLineEdit = QtWidgets.QLineEdit(greekresizepngDialog)
        self.SourceLineEdit.setGeometry(QtCore.QRect(10, 50, 301, 25))
        self.SourceLineEdit.setObjectName("SourceLineEdit")
        self.SourceButton = QtWidgets.QPushButton(greekresizepngDialog)
        self.SourceButton.setEnabled(False)
        self.SourceButton.setGeometry(QtCore.QRect(330, 50, 101, 25))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Icons/Icons/png-file.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.SourceButton.setIcon(icon)
        self.SourceButton.setObjectName("SourceButton")
        self.DestinationButton = QtWidgets.QPushButton(greekresizepngDialog)
        self.DestinationButton.setEnabled(False)
        self.DestinationButton.setGeometry(QtCore.QRect(330, 120, 101, 25))
        self.DestinationButton.setIcon(icon)
        self.DestinationButton.setObjectName("DestinationButton")
        self.DestinationLineEdit = QtWidgets.QLineEdit(greekresizepngDialog)
        self.DestinationLineEdit.setEnabled(True)
        self.DestinationLineEdit.setGeometry(QtCore.QRect(10, 120, 301, 25))
        self.DestinationLineEdit.setObjectName("DestinationLineEdit")
        self.SourceLabel = QtWidgets.QLabel(greekresizepngDialog)
        self.SourceLabel.setGeometry(QtCore.QRect(20, 30, 261, 17))
        self.SourceLabel.setObjectName("SourceLabel")
        self.DestinationLabel = QtWidgets.QLabel(greekresizepngDialog)
        self.DestinationLabel.setGeometry(QtCore.QRect(20, 100, 291, 17))
        self.DestinationLabel.setObjectName("DestinationLabel")
        self.defaultsrcBox = QtWidgets.QCheckBox(greekresizepngDialog)
        self.defaultsrcBox.setGeometry(QtCore.QRect(330, 20, 101, 23))
        self.defaultsrcBox.setChecked(True)
        self.defaultsrcBox.setObjectName("defaultsrcBox")

        self.retranslateUi(greekresizepngDialog)
        self.buttonBox.accepted.connect(greekresizepngDialog.accept)
        self.buttonBox.rejected.connect(greekresizepngDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(greekresizepngDialog)

    def retranslateUi(self, greekresizepngDialog):
        _translate = QtCore.QCoreApplication.translate
        greekresizepngDialog.setWindowTitle(_translate("greekresizepngDialog", "Resize Greek png pages"))
        self.SourceLineEdit.setPlaceholderText(_translate("greekresizepngDialog", "(default) working temp folder"))
        self.SourceButton.setText(_translate("greekresizepngDialog", "Source"))
        self.DestinationButton.setText(_translate("greekresizepngDialog", "Destination"))
        self.DestinationLineEdit.setPlaceholderText(_translate("greekresizepngDialog", "(default) working temp folder"))
        self.SourceLabel.setText(_translate("greekresizepngDialog", "Resize Greek png pages source folder"))
        self.DestinationLabel.setText(_translate("greekresizepngDialog", "Resize Greek png pages destination folder"))
        self.defaultsrcBox.setText(_translate("greekresizepngDialog", "Use default"))

import UI_Icons

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    greekresizepngDialog = QtWidgets.QDialog()
    ui = Ui_greekresizepngDialog()
    ui.setupUi(greekresizepngDialog)
    greekresizepngDialog.show()
    sys.exit(app.exec_())

