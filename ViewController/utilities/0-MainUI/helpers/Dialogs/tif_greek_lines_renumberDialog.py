# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './QtDesignerUI/tif_greek_lines_renumberDialog.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_tifgreekrenumberlinesDialog(object):
    def setupUi(self, tifgreekrenumberlinesDialog):
        tifgreekrenumberlinesDialog.setObjectName("tifgreekrenumberlinesDialog")
        tifgreekrenumberlinesDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        tifgreekrenumberlinesDialog.resize(466, 289)
        self.buttonBox = QtWidgets.QDialogButtonBox(tifgreekrenumberlinesDialog)
        self.buttonBox.setGeometry(QtCore.QRect(260, 250, 171, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.SourceLineEdit = QtWidgets.QLineEdit(tifgreekrenumberlinesDialog)
        self.SourceLineEdit.setGeometry(QtCore.QRect(10, 50, 301, 25))
        self.SourceLineEdit.setObjectName("SourceLineEdit")
        self.SourceButton = QtWidgets.QPushButton(tifgreekrenumberlinesDialog)
        self.SourceButton.setEnabled(False)
        self.SourceButton.setGeometry(QtCore.QRect(330, 50, 101, 25))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Icons/Icons/tiff-file.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.SourceButton.setIcon(icon)
        self.SourceButton.setObjectName("SourceButton")
        self.DestinationButton = QtWidgets.QPushButton(tifgreekrenumberlinesDialog)
        self.DestinationButton.setEnabled(False)
        self.DestinationButton.setGeometry(QtCore.QRect(330, 120, 101, 25))
        self.DestinationButton.setIcon(icon)
        self.DestinationButton.setObjectName("DestinationButton")
        self.DestinationLineEdit = QtWidgets.QLineEdit(tifgreekrenumberlinesDialog)
        self.DestinationLineEdit.setGeometry(QtCore.QRect(10, 120, 301, 25))
        self.DestinationLineEdit.setObjectName("DestinationLineEdit")
        self.SourceLabel = QtWidgets.QLabel(tifgreekrenumberlinesDialog)
        self.SourceLabel.setGeometry(QtCore.QRect(10, 30, 271, 17))
        self.SourceLabel.setObjectName("SourceLabel")
        self.DestinationLabel = QtWidgets.QLabel(tifgreekrenumberlinesDialog)
        self.DestinationLabel.setGeometry(QtCore.QRect(10, 100, 301, 17))
        self.DestinationLabel.setObjectName("DestinationLabel")
        self.defaultsrcBox = QtWidgets.QCheckBox(tifgreekrenumberlinesDialog)
        self.defaultsrcBox.setGeometry(QtCore.QRect(330, 20, 101, 23))
        self.defaultsrcBox.setChecked(True)
        self.defaultsrcBox.setObjectName("defaultsrcBox")
        self.StartPageLineEdit = QtWidgets.QLineEdit(tifgreekrenumberlinesDialog)
        self.StartPageLineEdit.setGeometry(QtCore.QRect(60, 190, 41, 25))
        self.StartPageLineEdit.setObjectName("StartPageLineEdit")
        self.StartPageLabel = QtWidgets.QLabel(tifgreekrenumberlinesDialog)
        self.StartPageLabel.setGeometry(QtCore.QRect(30, 160, 101, 20))
        self.StartPageLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.StartPageLabel.setObjectName("StartPageLabel")
        self.EndPageLabel = QtWidgets.QLabel(tifgreekrenumberlinesDialog)
        self.EndPageLabel.setGeometry(QtCore.QRect(190, 160, 101, 20))
        self.EndPageLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.EndPageLabel.setObjectName("EndPageLabel")
        self.EndPageLineEdit = QtWidgets.QLineEdit(tifgreekrenumberlinesDialog)
        self.EndPageLineEdit.setGeometry(QtCore.QRect(220, 190, 41, 25))
        self.EndPageLineEdit.setObjectName("EndPageLineEdit")

        self.retranslateUi(tifgreekrenumberlinesDialog)
        self.buttonBox.accepted.connect(tifgreekrenumberlinesDialog.accept)
        self.buttonBox.rejected.connect(tifgreekrenumberlinesDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(tifgreekrenumberlinesDialog)

    def retranslateUi(self, tifgreekrenumberlinesDialog):
        _translate = QtCore.QCoreApplication.translate
        tifgreekrenumberlinesDialog.setWindowTitle(_translate("tifgreekrenumberlinesDialog", "Renumber Greek tif lines"))
        self.SourceLineEdit.setPlaceholderText(_translate("tifgreekrenumberlinesDialog", "(default) working temp folder"))
        self.SourceButton.setText(_translate("tifgreekrenumberlinesDialog", "Source"))
        self.DestinationButton.setText(_translate("tifgreekrenumberlinesDialog", "Destination"))
        self.SourceLabel.setText(_translate("tifgreekrenumberlinesDialog", "Renumber Greek tif lines source folder"))
        self.DestinationLabel.setText(_translate("tifgreekrenumberlinesDialog", "Renumber Greek tif lines destination folder"))
        self.defaultsrcBox.setText(_translate("tifgreekrenumberlinesDialog", "Use default"))
        self.StartPageLabel.setText(_translate("tifgreekrenumberlinesDialog", "Starting Page"))
        self.EndPageLabel.setText(_translate("tifgreekrenumberlinesDialog", "Ending Page"))

import UI_Icons

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    tifgreekrenumberlinesDialog = QtWidgets.QDialog()
    ui = Ui_tifgreekrenumberlinesDialog()
    ui.setupUi(tifgreekrenumberlinesDialog)
    tifgreekrenumberlinesDialog.show()
    sys.exit(app.exec_())

