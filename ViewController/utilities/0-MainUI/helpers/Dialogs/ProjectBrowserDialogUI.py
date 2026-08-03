# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './QtDesignerUI/ProjectBrowserDialogUI.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_ProjectBrowserDialog(object):
    def setupUi(self, ProjectBrowserDialog):
        ProjectBrowserDialog.setObjectName("ProjectBrowserDialog")
        ProjectBrowserDialog.resize(798, 646)
        self.buttonBox = QtWidgets.QDialogButtonBox(ProjectBrowserDialog)
        self.buttonBox.setGeometry(QtCore.QRect(440, 600, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.frame = QtWidgets.QFrame(ProjectBrowserDialog)
        self.frame.setGeometry(QtCore.QRect(10, 30, 782, 538))
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.frame)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.treeView = QtWidgets.QTreeView(self.frame)
        self.treeView.setObjectName("treeView")
        self.gridLayout_2.addWidget(self.treeView, 0, 0, 1, 1)

        self.retranslateUi(ProjectBrowserDialog)
        self.buttonBox.accepted.connect(ProjectBrowserDialog.accept)
        self.buttonBox.rejected.connect(ProjectBrowserDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(ProjectBrowserDialog)

    def retranslateUi(self, ProjectBrowserDialog):
        _translate = QtCore.QCoreApplication.translate
        ProjectBrowserDialog.setWindowTitle(_translate("ProjectBrowserDialog", "Project Browser Dialog"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ProjectBrowserDialog = QtWidgets.QDialog()
    ui = Ui_ProjectBrowserDialog()
    ui.setupUi(ProjectBrowserDialog)
    ProjectBrowserDialog.show()
    sys.exit(app.exec_())

