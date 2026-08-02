# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './QtDesignerUI/tif_greek_lines_stageDialog.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_tifgreekstagelinesDialog(object):
    def setupUi(self, tifgreekstagelinesDialog):
        tifgreekstagelinesDialog.setObjectName("tifgreekstagelinesDialog")
        tifgreekstagelinesDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        tifgreekstagelinesDialog.resize(466, 362)
        self.buttonBox = QtWidgets.QDialogButtonBox(tifgreekstagelinesDialog)
        self.buttonBox.setGeometry(QtCore.QRect(260, 250, 171, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.SourceRenamedLineEdit = QtWidgets.QLineEdit(tifgreekstagelinesDialog)
        self.SourceRenamedLineEdit.setGeometry(QtCore.QRect(10, 50, 301, 25))
        self.SourceRenamedLineEdit.setObjectName("SourceRenamedLineEdit")
        self.SourceRenamedButton = QtWidgets.QPushButton(tifgreekstagelinesDialog)
        self.SourceRenamedButton.setEnabled(False)
        self.SourceRenamedButton.setGeometry(QtCore.QRect(330, 50, 101, 25))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Icons/Icons/tiff-file.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.SourceRenamedButton.setIcon(icon)
        self.SourceRenamedButton.setObjectName("SourceRenamedButton")
        self.DestinationButton = QtWidgets.QPushButton(tifgreekstagelinesDialog)
        self.DestinationButton.setEnabled(False)
        self.DestinationButton.setGeometry(QtCore.QRect(330, 190, 101, 25))
        self.DestinationButton.setIcon(icon)
        self.DestinationButton.setObjectName("DestinationButton")
        self.DestinationLineEdit = QtWidgets.QLineEdit(tifgreekstagelinesDialog)
        self.DestinationLineEdit.setGeometry(QtCore.QRect(10, 190, 301, 25))
        self.DestinationLineEdit.setObjectName("DestinationLineEdit")
        self.SourceRenamedLabel = QtWidgets.QLabel(tifgreekstagelinesDialog)
        self.SourceRenamedLabel.setGeometry(QtCore.QRect(20, 30, 261, 17))
        self.SourceRenamedLabel.setObjectName("SourceRenamedLabel")
        self.DestinationLabel = QtWidgets.QLabel(tifgreekstagelinesDialog)
        self.DestinationLabel.setGeometry(QtCore.QRect(20, 170, 291, 17))
        self.DestinationLabel.setObjectName("DestinationLabel")
        self.defaultsrcBox = QtWidgets.QCheckBox(tifgreekstagelinesDialog)
        self.defaultsrcBox.setGeometry(QtCore.QRect(330, 20, 101, 23))
        self.defaultsrcBox.setChecked(True)
        self.defaultsrcBox.setObjectName("defaultsrcBox")
        self.SourceRenumberedLineEdit = QtWidgets.QLineEdit(tifgreekstagelinesDialog)
        self.SourceRenumberedLineEdit.setGeometry(QtCore.QRect(10, 120, 301, 25))
        self.SourceRenumberedLineEdit.setObjectName("SourceRenumberedLineEdit")
        self.SourceRenumberedLabel = QtWidgets.QLabel(tifgreekstagelinesDialog)
        self.SourceRenumberedLabel.setGeometry(QtCore.QRect(20, 100, 281, 17))
        self.SourceRenumberedLabel.setObjectName("SourceRenumberedLabel")
        self.SourceRenumberedButton = QtWidgets.QPushButton(tifgreekstagelinesDialog)
        self.SourceRenumberedButton.setEnabled(False)
        self.SourceRenumberedButton.setGeometry(QtCore.QRect(330, 120, 101, 25))
        self.SourceRenumberedButton.setIcon(icon)
        self.SourceRenumberedButton.setObjectName("SourceRenumberedButton")

        self.retranslateUi(tifgreekstagelinesDialog)
        self.buttonBox.accepted.connect(tifgreekstagelinesDialog.accept)
        self.buttonBox.rejected.connect(tifgreekstagelinesDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(tifgreekstagelinesDialog)

    def retranslateUi(self, tifgreekstagelinesDialog):
        _translate = QtCore.QCoreApplication.translate
        tifgreekstagelinesDialog.setWindowTitle(_translate("tifgreekstagelinesDialog", "Stage Greek tif lines"))
        self.SourceRenamedLineEdit.setPlaceholderText(_translate("tifgreekstagelinesDialog", "(default) working temp folder"))
        self.SourceRenamedButton.setText(_translate("tifgreekstagelinesDialog", "Source"))
        self.DestinationButton.setText(_translate("tifgreekstagelinesDialog", "Destination"))
        self.SourceRenamedLabel.setText(_translate("tifgreekstagelinesDialog", "Stage Greek tif lines renamed folder"))
        self.DestinationLabel.setText(_translate("tifgreekstagelinesDialog", "Stage Greek tif lines destination folder"))
        self.defaultsrcBox.setText(_translate("tifgreekstagelinesDialog", "Use default"))
        self.SourceRenumberedLineEdit.setPlaceholderText(_translate("tifgreekstagelinesDialog", "(default) working temp folder"))
        self.SourceRenumberedLabel.setText(_translate("tifgreekstagelinesDialog", "Stage Greek tif lines renumbered folder"))
        self.SourceRenumberedButton.setText(_translate("tifgreekstagelinesDialog", "Source"))

import UI_Icons

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    tifgreekstagelinesDialog = QtWidgets.QDialog()
    ui = Ui_tifgreekstagelinesDialog()
    ui.setupUi(tifgreekstagelinesDialog)
    tifgreekstagelinesDialog.show()
    sys.exit(app.exec_())

