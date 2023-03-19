# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './QtDesignerUI/MySlidersDialogUI.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_SliderDialog(object):
    def setupUi(self, SliderDialog):
        SliderDialog.setObjectName("SliderDialog")
        SliderDialog.resize(369, 166)
        font = QtGui.QFont()
        font.setFamily("FROMVS [MAXR]")
        SliderDialog.setFont(font)
        self.SliderbuttonBox = QtWidgets.QDialogButtonBox(SliderDialog)
        self.SliderbuttonBox.setGeometry(QtCore.QRect(70, 110, 261, 32))
        self.SliderbuttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.SliderbuttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Discard|QtWidgets.QDialogButtonBox.Ok)
        self.SliderbuttonBox.setObjectName("SliderbuttonBox")
        self.Sliderhorizontal = QtWidgets.QSlider(SliderDialog)
        self.Sliderhorizontal.setGeometry(QtCore.QRect(20, 60, 241, 20))
        font = QtGui.QFont()
        font.setFamily("FROMVS [MAXR]")
        self.Sliderhorizontal.setFont(font)
        self.Sliderhorizontal.setOrientation(QtCore.Qt.Horizontal)
        self.Sliderhorizontal.setObjectName("Sliderhorizontal")
        self.SliderspinBox = QtWidgets.QSpinBox(SliderDialog)
        self.SliderspinBox.setGeometry(QtCore.QRect(270, 50, 81, 26))
        self.SliderspinBox.setObjectName("SliderspinBox")
        self.Sliderlabel = QtWidgets.QLabel(SliderDialog)
        self.Sliderlabel.setEnabled(True)
        self.Sliderlabel.setGeometry(QtCore.QRect(20, 20, 271, 20))
        font = QtGui.QFont()
        font.setFamily("FROMVS [MAXR]")
        self.Sliderlabel.setFont(font)
        self.Sliderlabel.setObjectName("Sliderlabel")

        self.retranslateUi(SliderDialog)
        self.SliderbuttonBox.accepted.connect(SliderDialog.accept)
        self.SliderbuttonBox.rejected.connect(SliderDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(SliderDialog)

    def retranslateUi(self, SliderDialog):
        _translate = QtCore.QCoreApplication.translate
        SliderDialog.setWindowTitle(_translate("SliderDialog", "Dialog"))
        self.Sliderlabel.setText(_translate("SliderDialog", "Slider label text goes here"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    SliderDialog = QtWidgets.QDialog()
    ui = Ui_SliderDialog()
    ui.setupUi(SliderDialog)
    SliderDialog.show()
    sys.exit(app.exec_())

