# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './QtDesignerUI/png_greek_lines_renameDialog.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_greekmovelinespngDialog(object):
    def setupUi(self, greekmovelinespngDialog):
        greekmovelinespngDialog.setObjectName("greekmovelinespngDialog")
        greekmovelinespngDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        greekmovelinespngDialog.resize(466, 237)
        self.buttonBox = QtWidgets.QDialogButtonBox(greekmovelinespngDialog)
        self.buttonBox.setGeometry(QtCore.QRect(260, 180, 171, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.SourceLineEdit = QtWidgets.QLineEdit(greekmovelinespngDialog)
        self.SourceLineEdit.setGeometry(QtCore.QRect(10, 50, 301, 25))
        self.SourceLineEdit.setObjectName("SourceLineEdit")
        self.SourceButton = QtWidgets.QPushButton(greekmovelinespngDialog)
        self.SourceButton.setEnabled(False)
        self.SourceButton.setGeometry(QtCore.QRect(330, 50, 101, 25))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Icons/Icons/png-file.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.SourceButton.setIcon(icon)
        self.SourceButton.setObjectName("SourceButton")
        self.DestinationButton = QtWidgets.QPushButton(greekmovelinespngDialog)
        self.DestinationButton.setGeometry(QtCore.QRect(330, 120, 101, 25))
        self.DestinationButton.setIcon(icon)
        self.DestinationButton.setObjectName("DestinationButton")
        self.DestinationLineEdit = QtWidgets.QLineEdit(greekmovelinespngDialog)
        self.DestinationLineEdit.setGeometry(QtCore.QRect(10, 120, 301, 25))
        self.DestinationLineEdit.setObjectName("DestinationLineEdit")
        self.SourceLabel = QtWidgets.QLabel(greekmovelinespngDialog)
        self.SourceLabel.setGeometry(QtCore.QRect(20, 30, 261, 17))
        self.SourceLabel.setObjectName("SourceLabel")
        self.DestinationLabel = QtWidgets.QLabel(greekmovelinespngDialog)
        self.DestinationLabel.setGeometry(QtCore.QRect(20, 100, 291, 17))
        self.DestinationLabel.setObjectName("DestinationLabel")
        self.defaultsrcBox = QtWidgets.QCheckBox(greekmovelinespngDialog)
        self.defaultsrcBox.setGeometry(QtCore.QRect(330, 20, 101, 23))
        self.defaultsrcBox.setChecked(True)
        self.defaultsrcBox.setObjectName("defaultsrcBox")

        self.retranslateUi(greekmovelinespngDialog)
        self.buttonBox.accepted.connect(greekmovelinespngDialog.accept)
        self.buttonBox.rejected.connect(greekmovelinespngDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(greekmovelinespngDialog)

    def retranslateUi(self, greekmovelinespngDialog):
        _translate = QtCore.QCoreApplication.translate
        greekmovelinespngDialog.setWindowTitle(_translate("greekmovelinespngDialog", "Move Greek png lines"))
        self.SourceLineEdit.setPlaceholderText(_translate("greekmovelinespngDialog", "(default) working temp folder"))
        self.SourceButton.setText(_translate("greekmovelinespngDialog", "Source"))
        self.DestinationButton.setText(_translate("greekmovelinespngDialog", "Destination"))
        self.SourceLabel.setText(_translate("greekmovelinespngDialog", "Move Greek png lines source folder"))
        self.DestinationLabel.setText(_translate("greekmovelinespngDialog", "Move Greek png lines destination folder"))
        self.defaultsrcBox.setText(_translate("greekmovelinespngDialog", "Use default"))

import UI_Icons

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    greekmovelinespngDialog = QtWidgets.QDialog()
    ui = Ui_greekmovelinespngDialog()
    ui.setupUi(greekmovelinespngDialog)
    greekmovelinespngDialog.show()
    sys.exit(app.exec_())

