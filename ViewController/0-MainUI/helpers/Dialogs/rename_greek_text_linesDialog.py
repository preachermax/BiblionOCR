# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './QtDesignerUI/rename_greek_text_linesDialog.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_renamegreektextlinesDialog(object):
    def setupUi(self, renamegreektextlinesDialog):
        renamegreektextlinesDialog.setObjectName("renamegreektextlinesDialog")
        renamegreektextlinesDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        renamegreektextlinesDialog.resize(466, 237)
        renamegreektextlinesDialog.setSizeGripEnabled(True)
        self.buttonBox = QtWidgets.QDialogButtonBox(renamegreektextlinesDialog)
        self.buttonBox.setGeometry(QtCore.QRect(260, 180, 171, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.SourceLineEdit = QtWidgets.QLineEdit(renamegreektextlinesDialog)
        self.SourceLineEdit.setGeometry(QtCore.QRect(10, 50, 301, 25))
        self.SourceLineEdit.setObjectName("SourceLineEdit")
        self.SourceButton = QtWidgets.QPushButton(renamegreektextlinesDialog)
        self.SourceButton.setEnabled(False)
        self.SourceButton.setGeometry(QtCore.QRect(330, 50, 101, 25))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Icons/Icons/tiff-file.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.SourceButton.setIcon(icon)
        self.SourceButton.setObjectName("SourceButton")
        self.DestinationButton = QtWidgets.QPushButton(renamegreektextlinesDialog)
        self.DestinationButton.setEnabled(False)
        self.DestinationButton.setGeometry(QtCore.QRect(330, 120, 101, 25))
        self.DestinationButton.setIcon(icon)
        self.DestinationButton.setObjectName("DestinationButton")
        self.DestinationLineEdit = QtWidgets.QLineEdit(renamegreektextlinesDialog)
        self.DestinationLineEdit.setGeometry(QtCore.QRect(10, 120, 301, 25))
        self.DestinationLineEdit.setObjectName("DestinationLineEdit")
        self.SourceLabel = QtWidgets.QLabel(renamegreektextlinesDialog)
        self.SourceLabel.setGeometry(QtCore.QRect(20, 30, 261, 17))
        self.SourceLabel.setObjectName("SourceLabel")
        self.DestinationLabel = QtWidgets.QLabel(renamegreektextlinesDialog)
        self.DestinationLabel.setGeometry(QtCore.QRect(20, 100, 291, 17))
        self.DestinationLabel.setObjectName("DestinationLabel")
        self.defaultsrcBox = QtWidgets.QCheckBox(renamegreektextlinesDialog)
        self.defaultsrcBox.setGeometry(QtCore.QRect(330, 20, 101, 23))
        self.defaultsrcBox.setChecked(True)
        self.defaultsrcBox.setObjectName("defaultsrcBox")

        self.retranslateUi(renamegreektextlinesDialog)
        self.buttonBox.accepted.connect(renamegreektextlinesDialog.accept)
        self.buttonBox.rejected.connect(renamegreektextlinesDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(renamegreektextlinesDialog)

    def retranslateUi(self, renamegreektextlinesDialog):
        _translate = QtCore.QCoreApplication.translate
        renamegreektextlinesDialog.setWindowTitle(_translate("renamegreektextlinesDialog", "Rename Greek text lines"))
        self.SourceLineEdit.setPlaceholderText(_translate("renamegreektextlinesDialog", "(default) working temp folder"))
        self.SourceButton.setText(_translate("renamegreektextlinesDialog", "Source"))
        self.DestinationButton.setText(_translate("renamegreektextlinesDialog", "Destination"))
        self.SourceLabel.setText(_translate("renamegreektextlinesDialog", "Rename Greek text lines source folder"))
        self.DestinationLabel.setText(_translate("renamegreektextlinesDialog", "Rename Greek text lines destination folder"))
        self.defaultsrcBox.setText(_translate("renamegreektextlinesDialog", "Use default"))

import UI_Icons

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    renamegreektextlinesDialog = QtWidgets.QDialog()
    ui = Ui_renamegreektextlinesDialog()
    ui.setupUi(renamegreektextlinesDialog)
    renamegreektextlinesDialog.show()
    sys.exit(app.exec_())

