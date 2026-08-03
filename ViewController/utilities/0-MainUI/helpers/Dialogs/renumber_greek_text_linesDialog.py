# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './QtDesignerUI/renumber_greek_text_linesDialog.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_renumbergreektextlinesDialog(object):
    def setupUi(self, renumbergreektextlinesDialog):
        renumbergreektextlinesDialog.setObjectName("renumbergreektextlinesDialog")
        renumbergreektextlinesDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        renumbergreektextlinesDialog.resize(466, 290)
        renumbergreektextlinesDialog.setSizeGripEnabled(True)
        self.buttonBox = QtWidgets.QDialogButtonBox(renumbergreektextlinesDialog)
        self.buttonBox.setGeometry(QtCore.QRect(260, 250, 171, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.SourceLineEdit = QtWidgets.QLineEdit(renumbergreektextlinesDialog)
        self.SourceLineEdit.setGeometry(QtCore.QRect(10, 50, 301, 25))
        self.SourceLineEdit.setObjectName("SourceLineEdit")
        self.SourceButton = QtWidgets.QPushButton(renumbergreektextlinesDialog)
        self.SourceButton.setEnabled(False)
        self.SourceButton.setGeometry(QtCore.QRect(330, 50, 101, 25))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Icons/Icons/tiff-file.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.SourceButton.setIcon(icon)
        self.SourceButton.setObjectName("SourceButton")
        self.DestinationButton = QtWidgets.QPushButton(renumbergreektextlinesDialog)
        self.DestinationButton.setEnabled(False)
        self.DestinationButton.setGeometry(QtCore.QRect(330, 120, 101, 25))
        self.DestinationButton.setIcon(icon)
        self.DestinationButton.setObjectName("DestinationButton")
        self.DestinationLineEdit = QtWidgets.QLineEdit(renumbergreektextlinesDialog)
        self.DestinationLineEdit.setGeometry(QtCore.QRect(10, 120, 301, 25))
        self.DestinationLineEdit.setObjectName("DestinationLineEdit")
        self.SourceLabel = QtWidgets.QLabel(renumbergreektextlinesDialog)
        self.SourceLabel.setGeometry(QtCore.QRect(10, 30, 281, 17))
        self.SourceLabel.setObjectName("SourceLabel")
        self.DestinationLabel = QtWidgets.QLabel(renumbergreektextlinesDialog)
        self.DestinationLabel.setGeometry(QtCore.QRect(10, 100, 311, 17))
        self.DestinationLabel.setObjectName("DestinationLabel")
        self.defaultsrcBox = QtWidgets.QCheckBox(renumbergreektextlinesDialog)
        self.defaultsrcBox.setGeometry(QtCore.QRect(330, 20, 101, 23))
        self.defaultsrcBox.setChecked(True)
        self.defaultsrcBox.setObjectName("defaultsrcBox")
        self.EndPageLabel = QtWidgets.QLabel(renumbergreektextlinesDialog)
        self.EndPageLabel.setGeometry(QtCore.QRect(190, 160, 101, 20))
        self.EndPageLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.EndPageLabel.setObjectName("EndPageLabel")
        self.StartPageLabel = QtWidgets.QLabel(renumbergreektextlinesDialog)
        self.StartPageLabel.setGeometry(QtCore.QRect(30, 160, 101, 20))
        self.StartPageLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.StartPageLabel.setObjectName("StartPageLabel")
        self.StartPageLineEdit = QtWidgets.QLineEdit(renumbergreektextlinesDialog)
        self.StartPageLineEdit.setGeometry(QtCore.QRect(60, 190, 41, 25))
        self.StartPageLineEdit.setObjectName("StartPageLineEdit")
        self.EndPageLineEdit = QtWidgets.QLineEdit(renumbergreektextlinesDialog)
        self.EndPageLineEdit.setGeometry(QtCore.QRect(220, 190, 41, 25))
        self.EndPageLineEdit.setObjectName("EndPageLineEdit")

        self.retranslateUi(renumbergreektextlinesDialog)
        self.buttonBox.accepted.connect(renumbergreektextlinesDialog.accept)
        self.buttonBox.rejected.connect(renumbergreektextlinesDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(renumbergreektextlinesDialog)

    def retranslateUi(self, renumbergreektextlinesDialog):
        _translate = QtCore.QCoreApplication.translate
        renumbergreektextlinesDialog.setWindowTitle(_translate("renumbergreektextlinesDialog", "Renumber Greek text lines"))
        self.SourceLineEdit.setPlaceholderText(_translate("renumbergreektextlinesDialog", "(default) working temp folder"))
        self.SourceButton.setText(_translate("renumbergreektextlinesDialog", "Source"))
        self.DestinationButton.setText(_translate("renumbergreektextlinesDialog", "Destination"))
        self.SourceLabel.setText(_translate("renumbergreektextlinesDialog", "Renumber Greek text lines source folder"))
        self.DestinationLabel.setText(_translate("renumbergreektextlinesDialog", "Renumber Greek text lines destination folder"))
        self.defaultsrcBox.setText(_translate("renumbergreektextlinesDialog", "Use default"))
        self.EndPageLabel.setText(_translate("renumbergreektextlinesDialog", "Ending Page"))
        self.StartPageLabel.setText(_translate("renumbergreektextlinesDialog", "Starting Page"))

import UI_Icons

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    renumbergreektextlinesDialog = QtWidgets.QDialog()
    ui = Ui_renumbergreektextlinesDialog()
    ui.setupUi(renumbergreektextlinesDialog)
    renumbergreektextlinesDialog.show()
    sys.exit(app.exec_())

