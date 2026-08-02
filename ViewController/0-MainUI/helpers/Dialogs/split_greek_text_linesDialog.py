# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './QtDesignerUI/split_greek_text_linesDialog.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_splitgreektextlinesDialog(object):
    def setupUi(self, splitgreektextlinesDialog):
        splitgreektextlinesDialog.setObjectName("splitgreektextlinesDialog")
        splitgreektextlinesDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        splitgreektextlinesDialog.resize(466, 237)
        self.buttonBox = QtWidgets.QDialogButtonBox(splitgreektextlinesDialog)
        self.buttonBox.setGeometry(QtCore.QRect(260, 180, 171, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.SourceLineEdit = QtWidgets.QLineEdit(splitgreektextlinesDialog)
        self.SourceLineEdit.setGeometry(QtCore.QRect(10, 50, 301, 25))
        self.SourceLineEdit.setObjectName("SourceLineEdit")
        self.SourceButton = QtWidgets.QPushButton(splitgreektextlinesDialog)
        self.SourceButton.setEnabled(False)
        self.SourceButton.setGeometry(QtCore.QRect(330, 50, 101, 25))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Icons/Icons/tiff-file.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.SourceButton.setIcon(icon)
        self.SourceButton.setObjectName("SourceButton")
        self.DestinationButton = QtWidgets.QPushButton(splitgreektextlinesDialog)
        self.DestinationButton.setEnabled(False)
        self.DestinationButton.setGeometry(QtCore.QRect(330, 120, 101, 25))
        self.DestinationButton.setIcon(icon)
        self.DestinationButton.setObjectName("DestinationButton")
        self.DestinationLineEdit = QtWidgets.QLineEdit(splitgreektextlinesDialog)
        self.DestinationLineEdit.setGeometry(QtCore.QRect(10, 120, 301, 25))
        self.DestinationLineEdit.setObjectName("DestinationLineEdit")
        self.SourceLabel = QtWidgets.QLabel(splitgreektextlinesDialog)
        self.SourceLabel.setGeometry(QtCore.QRect(20, 30, 261, 17))
        self.SourceLabel.setObjectName("SourceLabel")
        self.DestinationLabel = QtWidgets.QLabel(splitgreektextlinesDialog)
        self.DestinationLabel.setGeometry(QtCore.QRect(20, 100, 291, 17))
        self.DestinationLabel.setObjectName("DestinationLabel")
        self.defaultsrcBox = QtWidgets.QCheckBox(splitgreektextlinesDialog)
        self.defaultsrcBox.setGeometry(QtCore.QRect(330, 20, 101, 23))
        self.defaultsrcBox.setChecked(True)
        self.defaultsrcBox.setObjectName("defaultsrcBox")

        self.retranslateUi(splitgreektextlinesDialog)
        self.buttonBox.accepted.connect(splitgreektextlinesDialog.accept)
        self.buttonBox.rejected.connect(splitgreektextlinesDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(splitgreektextlinesDialog)

    def retranslateUi(self, splitgreektextlinesDialog):
        _translate = QtCore.QCoreApplication.translate
        splitgreektextlinesDialog.setWindowTitle(_translate("splitgreektextlinesDialog", "Split Greek text lines"))
        self.SourceLineEdit.setPlaceholderText(_translate("splitgreektextlinesDialog", "(default) working temp folder"))
        self.SourceButton.setText(_translate("splitgreektextlinesDialog", "Source"))
        self.DestinationButton.setText(_translate("splitgreektextlinesDialog", "Destination"))
        self.SourceLabel.setText(_translate("splitgreektextlinesDialog", "Split Greek text lines source folder"))
        self.DestinationLabel.setText(_translate("splitgreektextlinesDialog", "Split Greek text lines destination folder"))
        self.defaultsrcBox.setText(_translate("splitgreektextlinesDialog", "Use default"))

import UI_Icons

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    splitgreektextlinesDialog = QtWidgets.QDialog()
    ui = Ui_splitgreektextlinesDialog()
    ui.setupUi(splitgreektextlinesDialog)
    splitgreektextlinesDialog.show()
    sys.exit(app.exec_())

