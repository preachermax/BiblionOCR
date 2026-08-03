# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/max/Projects/Python/Workflow/0-MainUI/ExtractPdf.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_ExtractDialog(object):
    def setupUi(self, ExtractDialog):
        ExtractDialog.setObjectName("ExtractDialog")
        ExtractDialog.resize(400, 300)
        self.buttonBox = QtWidgets.QDialogButtonBox(ExtractDialog)
        self.buttonBox.setGeometry(QtCore.QRect(10, 240, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.lineEdit = QtWidgets.QLineEdit(ExtractDialog)
        self.lineEdit.setGeometry(QtCore.QRect(20, 40, 291, 25))
        self.lineEdit.setObjectName("lineEdit")
        self.lineEdit_2 = QtWidgets.QLineEdit(ExtractDialog)
        self.lineEdit_2.setGeometry(QtCore.QRect(20, 100, 291, 25))
        self.lineEdit_2.setObjectName("lineEdit_2")
        self.pushButton = QtWidgets.QPushButton(ExtractDialog)
        self.pushButton.setGeometry(QtCore.QRect(320, 40, 31, 25))
        self.pushButton.setObjectName("pushButton")
        self.pushButton_2 = QtWidgets.QPushButton(ExtractDialog)
        self.pushButton_2.setGeometry(QtCore.QRect(320, 100, 31, 25))
        self.pushButton_2.setObjectName("pushButton_2")
        self.lineEdit_3 = QtWidgets.QLineEdit(ExtractDialog)
        self.lineEdit_3.setGeometry(QtCore.QRect(20, 160, 113, 25))
        self.lineEdit_3.setObjectName("lineEdit_3")
        self.lineEdit_4 = QtWidgets.QLineEdit(ExtractDialog)
        self.lineEdit_4.setGeometry(QtCore.QRect(200, 160, 113, 25))
        self.lineEdit_4.setObjectName("lineEdit_4")
        self.label = QtWidgets.QLabel(ExtractDialog)
        self.label.setGeometry(QtCore.QRect(20, 20, 81, 17))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(ExtractDialog)
        self.label_2.setGeometry(QtCore.QRect(20, 80, 131, 17))
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(ExtractDialog)
        self.label_3.setGeometry(QtCore.QRect(20, 140, 81, 17))
        self.label_3.setObjectName("label_3")
        self.label_4 = QtWidgets.QLabel(ExtractDialog)
        self.label_4.setGeometry(QtCore.QRect(200, 140, 71, 17))
        self.label_4.setObjectName("label_4")

        self.retranslateUi(ExtractDialog)
        self.buttonBox.accepted.connect(ExtractDialog.accept)
        self.buttonBox.rejected.connect(ExtractDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(ExtractDialog)

    def retranslateUi(self, ExtractDialog):
        _translate = QtCore.QCoreApplication.translate
        ExtractDialog.setWindowTitle(_translate("ExtractDialog", "Extract pdf pages "))
        self.lineEdit.setText(_translate("ExtractDialog", "./Images/Source/pdf_source/1516.pdf"))
        self.lineEdit_2.setText(_translate("ExtractDialog", "./Images/Source/pdf_source/"))
        self.pushButton.setText(_translate("ExtractDialog", "..."))
        self.pushButton_2.setText(_translate("ExtractDialog", "..."))
        self.label.setText(_translate("ExtractDialog", "Source File"))
        self.label_2.setText(_translate("ExtractDialog", "Destination  Folder"))
        self.label_3.setText(_translate("ExtractDialog", "Start Page"))
        self.label_4.setText(_translate("ExtractDialog", "End Page"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ExtractDialog = QtWidgets.QDialog()
    ui = Ui_ExtractDialog()
    ui.setupUi(ExtractDialog)
    ExtractDialog.show()
    sys.exit(app.exec_())

