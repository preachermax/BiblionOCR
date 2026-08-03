# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './QtDesignerUI/png_latin_lines_renameDialog.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_latinrenamelinespngDialog(object):
    def setupUi(self, latinrenamelinespngDialog):
        latinrenamelinespngDialog.setObjectName("latinrenamelinespngDialog")
        latinrenamelinespngDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        latinrenamelinespngDialog.resize(466, 237)
        latinrenamelinespngDialog.setWindowOpacity(5.0)
        self.buttonBox = QtWidgets.QDialogButtonBox(latinrenamelinespngDialog)
        self.buttonBox.setGeometry(QtCore.QRect(260, 180, 171, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.SourceLineEdit = QtWidgets.QLineEdit(latinrenamelinespngDialog)
        self.SourceLineEdit.setGeometry(QtCore.QRect(10, 50, 301, 25))
        self.SourceLineEdit.setObjectName("SourceLineEdit")
        self.SourceButton = QtWidgets.QPushButton(latinrenamelinespngDialog)
        self.SourceButton.setEnabled(False)
        self.SourceButton.setGeometry(QtCore.QRect(330, 50, 101, 25))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Icons/Icons/png-file.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.SourceButton.setIcon(icon)
        self.SourceButton.setObjectName("SourceButton")
        self.DestinationButton = QtWidgets.QPushButton(latinrenamelinespngDialog)
        self.DestinationButton.setGeometry(QtCore.QRect(330, 120, 101, 25))
        self.DestinationButton.setIcon(icon)
        self.DestinationButton.setObjectName("DestinationButton")
        self.DestinationLineEdit = QtWidgets.QLineEdit(latinrenamelinespngDialog)
        self.DestinationLineEdit.setGeometry(QtCore.QRect(10, 120, 301, 25))
        self.DestinationLineEdit.setObjectName("DestinationLineEdit")
        self.SourceLabel = QtWidgets.QLabel(latinrenamelinespngDialog)
        self.SourceLabel.setGeometry(QtCore.QRect(20, 30, 261, 17))
        self.SourceLabel.setObjectName("SourceLabel")
        self.DestinationLabel = QtWidgets.QLabel(latinrenamelinespngDialog)
        self.DestinationLabel.setGeometry(QtCore.QRect(20, 100, 291, 17))
        self.DestinationLabel.setObjectName("DestinationLabel")
        self.defaultsrcBox = QtWidgets.QCheckBox(latinrenamelinespngDialog)
        self.defaultsrcBox.setGeometry(QtCore.QRect(330, 20, 101, 23))
        self.defaultsrcBox.setChecked(True)
        self.defaultsrcBox.setObjectName("defaultsrcBox")

        self.retranslateUi(latinrenamelinespngDialog)
        self.buttonBox.accepted.connect(latinrenamelinespngDialog.accept)
        self.buttonBox.rejected.connect(latinrenamelinespngDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(latinrenamelinespngDialog)

    def retranslateUi(self, latinrenamelinespngDialog):
        _translate = QtCore.QCoreApplication.translate
        latinrenamelinespngDialog.setWindowTitle(_translate("latinrenamelinespngDialog", "Rename Latin png lines"))
        self.SourceLineEdit.setPlaceholderText(_translate("latinrenamelinespngDialog", "(default) working temp folder"))
        self.SourceButton.setText(_translate("latinrenamelinespngDialog", "Source"))
        self.DestinationButton.setText(_translate("latinrenamelinespngDialog", "Destination"))
        self.SourceLabel.setText(_translate("latinrenamelinespngDialog", "Rename Latin png lines source folder"))
        self.DestinationLabel.setText(_translate("latinrenamelinespngDialog", "Rename Latin png lines destination folder"))
        self.defaultsrcBox.setText(_translate("latinrenamelinespngDialog", "Use default"))

import UI_Icons

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    latinrenamelinespngDialog = QtWidgets.QDialog()
    ui = Ui_latinrenamelinespngDialog()
    ui.setupUi(latinrenamelinespngDialog)
    latinrenamelinespngDialog.show()
    sys.exit(app.exec_())

