# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './QtDesignerUI/png_latin_lines_moveDialog.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_latinmovelinespngDialog(object):
    def setupUi(self, latinmovelinespngDialog):
        latinmovelinespngDialog.setObjectName("latinmovelinespngDialog")
        latinmovelinespngDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        latinmovelinespngDialog.resize(466, 237)
        latinmovelinespngDialog.setWindowOpacity(5.0)
        self.buttonBox = QtWidgets.QDialogButtonBox(latinmovelinespngDialog)
        self.buttonBox.setGeometry(QtCore.QRect(260, 180, 171, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.SourceLineEdit = QtWidgets.QLineEdit(latinmovelinespngDialog)
        self.SourceLineEdit.setGeometry(QtCore.QRect(10, 50, 301, 25))
        self.SourceLineEdit.setObjectName("SourceLineEdit")
        self.SourceButton = QtWidgets.QPushButton(latinmovelinespngDialog)
        self.SourceButton.setEnabled(False)
        self.SourceButton.setGeometry(QtCore.QRect(330, 50, 101, 25))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Icons/Icons/png-file.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.SourceButton.setIcon(icon)
        self.SourceButton.setObjectName("SourceButton")
        self.DestinationButton = QtWidgets.QPushButton(latinmovelinespngDialog)
        self.DestinationButton.setGeometry(QtCore.QRect(330, 120, 101, 25))
        self.DestinationButton.setIcon(icon)
        self.DestinationButton.setObjectName("DestinationButton")
        self.DestinationLineEdit = QtWidgets.QLineEdit(latinmovelinespngDialog)
        self.DestinationLineEdit.setGeometry(QtCore.QRect(10, 120, 301, 25))
        self.DestinationLineEdit.setObjectName("DestinationLineEdit")
        self.SourceLabel = QtWidgets.QLabel(latinmovelinespngDialog)
        self.SourceLabel.setGeometry(QtCore.QRect(20, 30, 261, 17))
        self.SourceLabel.setObjectName("SourceLabel")
        self.DestinationLabel = QtWidgets.QLabel(latinmovelinespngDialog)
        self.DestinationLabel.setGeometry(QtCore.QRect(20, 100, 291, 17))
        self.DestinationLabel.setObjectName("DestinationLabel")
        self.defaultsrcBox = QtWidgets.QCheckBox(latinmovelinespngDialog)
        self.defaultsrcBox.setGeometry(QtCore.QRect(330, 20, 101, 23))
        self.defaultsrcBox.setChecked(True)
        self.defaultsrcBox.setObjectName("defaultsrcBox")

        self.retranslateUi(latinmovelinespngDialog)
        self.buttonBox.accepted.connect(latinmovelinespngDialog.accept)
        self.buttonBox.rejected.connect(latinmovelinespngDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(latinmovelinespngDialog)

    def retranslateUi(self, latinmovelinespngDialog):
        _translate = QtCore.QCoreApplication.translate
        latinmovelinespngDialog.setWindowTitle(_translate("latinmovelinespngDialog", "Move Latin png lines"))
        self.SourceLineEdit.setPlaceholderText(_translate("latinmovelinespngDialog", "(default) working temp folder"))
        self.SourceButton.setText(_translate("latinmovelinespngDialog", "Source"))
        self.DestinationButton.setText(_translate("latinmovelinespngDialog", "Destination"))
        self.SourceLabel.setText(_translate("latinmovelinespngDialog", "Move Latin png lines source folder"))
        self.DestinationLabel.setText(_translate("latinmovelinespngDialog", "Move Latin png lines destination folder"))
        self.defaultsrcBox.setText(_translate("latinmovelinespngDialog", "Use default"))

import UI_Icons

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    latinmovelinespngDialog = QtWidgets.QDialog()
    ui = Ui_latinmovelinespngDialog()
    ui.setupUi(latinmovelinespngDialog)
    latinmovelinespngDialog.show()
    sys.exit(app.exec_())

