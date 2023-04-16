# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/jetson/Projects/BiblionOCR/ViewController/0-MainUI/QtDesignerUI/tif_greek_lines_stageDialog.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_tifgreekstagelinesDialog(object):
    def setupUi(self, tifgreekstagelinesDialog):
        tifgreekstagelinesDialog.setObjectName("tifgreekstagelinesDialog")
        tifgreekstagelinesDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        tifgreekstagelinesDialog.resize(466, 289)
        self.buttonBox = QtWidgets.QDialogButtonBox(tifgreekstagelinesDialog)
        self.buttonBox.setGeometry(QtCore.QRect(260, 250, 171, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.SourceLineEdit = QtWidgets.QLineEdit(tifgreekstagelinesDialog)
        self.SourceLineEdit.setGeometry(QtCore.QRect(10, 50, 301, 25))
        self.SourceLineEdit.setObjectName("SourceLineEdit")
        self.SourceButton = QtWidgets.QPushButton(tifgreekstagelinesDialog)
        self.SourceButton.setEnabled(False)
        self.SourceButton.setGeometry(QtCore.QRect(330, 50, 101, 25))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Icons/Icons/tiff-file.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.SourceButton.setIcon(icon)
        self.SourceButton.setObjectName("SourceButton")
        self.DestinationButton = QtWidgets.QPushButton(tifgreekstagelinesDialog)
        self.DestinationButton.setEnabled(False)
        self.DestinationButton.setGeometry(QtCore.QRect(330, 120, 101, 25))
        self.DestinationButton.setIcon(icon)
        self.DestinationButton.setObjectName("DestinationButton")
        self.DestinationLineEdit = QtWidgets.QLineEdit(tifgreekstagelinesDialog)
        self.DestinationLineEdit.setGeometry(QtCore.QRect(10, 120, 301, 25))
        self.DestinationLineEdit.setObjectName("DestinationLineEdit")
        self.SourceLabel = QtWidgets.QLabel(tifgreekstagelinesDialog)
        self.SourceLabel.setGeometry(QtCore.QRect(10, 30, 271, 17))
        self.SourceLabel.setObjectName("SourceLabel")
        self.DestinationLabel = QtWidgets.QLabel(tifgreekstagelinesDialog)
        self.DestinationLabel.setGeometry(QtCore.QRect(10, 100, 301, 17))
        self.DestinationLabel.setObjectName("DestinationLabel")
        self.defaultsrcBox = QtWidgets.QCheckBox(tifgreekstagelinesDialog)
        self.defaultsrcBox.setGeometry(QtCore.QRect(330, 20, 101, 23))
        self.defaultsrcBox.setChecked(True)
        self.defaultsrcBox.setObjectName("defaultsrcBox")
        self.StartPageLineEdit = QtWidgets.QLineEdit(tifgreekstagelinesDialog)
        self.StartPageLineEdit.setGeometry(QtCore.QRect(60, 190, 41, 25))
        self.StartPageLineEdit.setObjectName("StartPageLineEdit")
        self.StartPageLabel = QtWidgets.QLabel(tifgreekstagelinesDialog)
        self.StartPageLabel.setGeometry(QtCore.QRect(30, 160, 101, 20))
        self.StartPageLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.StartPageLabel.setObjectName("StartPageLabel")
        self.EndPageLabel = QtWidgets.QLabel(tifgreekstagelinesDialog)
        self.EndPageLabel.setGeometry(QtCore.QRect(190, 160, 101, 20))
        self.EndPageLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.EndPageLabel.setObjectName("EndPageLabel")
        self.EndPageLineEdit = QtWidgets.QLineEdit(tifgreekstagelinesDialog)
        self.EndPageLineEdit.setGeometry(QtCore.QRect(220, 190, 41, 25))
        self.EndPageLineEdit.setObjectName("EndPageLineEdit")

        self.retranslateUi(tifgreekstagelinesDialog)
        self.buttonBox.accepted.connect(tifgreekstagelinesDialog.accept)
        self.buttonBox.rejected.connect(tifgreekstagelinesDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(tifgreekstagelinesDialog)

    def retranslateUi(self, tifgreekstagelinesDialog):
        _translate = QtCore.QCoreApplication.translate
        tifgreekstagelinesDialog.setWindowTitle(_translate("tifgreekstagelinesDialog", "Stage Greek tif lines"))
        tifgreekstagelinesDialog.setToolTip(_translate("tifgreekstagelinesDialog", "Stage Greek tif lines for Ground Truth"))
        self.SourceLineEdit.setPlaceholderText(_translate("tifgreekstagelinesDialog", "(default) working split lines folder"))
        self.SourceButton.setText(_translate("tifgreekstagelinesDialog", "Source"))
        self.DestinationButton.setText(_translate("tifgreekstagelinesDialog", "Destination"))
        self.DestinationLineEdit.setPlaceholderText(_translate("tifgreekstagelinesDialog", "(default) working ground truth folder"))
        self.SourceLabel.setText(_translate("tifgreekstagelinesDialog", "Stage Greek tif lines source folder"))
        self.DestinationLabel.setText(_translate("tifgreekstagelinesDialog", "Stage Greek tif lines destination folder"))
        self.defaultsrcBox.setText(_translate("tifgreekstagelinesDialog", "Use default"))
        self.StartPageLabel.setText(_translate("tifgreekstagelinesDialog", "Starting Page"))
        self.EndPageLabel.setText(_translate("tifgreekstagelinesDialog", "Ending Page"))
import UI_Icons


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    tifgreekstagelinesDialog = QtWidgets.QDialog()
    ui = Ui_tifgreekstagelinesDialog()
    ui.setupUi(tifgreekstagelinesDialog)
    tifgreekstagelinesDialog.show()
    sys.exit(app.exec_())
