# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/jetson/Projects/BiblionOCR/ViewController/0-MainUI/QtDesignerUI/MyExplorerUI.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Explorer(object):
    def setupUi(self, Explorer):
        Explorer.setObjectName("Explorer")
        Explorer.setWindowModality(QtCore.Qt.NonModal)
        Explorer.resize(800, 600)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Icons/Icons/BiblionExplorer.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Explorer.setWindowIcon(icon)
        self.centralwidget = QtWidgets.QWidget(Explorer)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.frame = QtWidgets.QFrame(self.centralwidget)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.frame)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.treeView = QtWidgets.QTreeView(self.frame)
        self.treeView.setObjectName("treeView")
        self.gridLayout_2.addWidget(self.treeView, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.frame, 0, 0, 1, 1)
        Explorer.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(Explorer)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 22))
        self.menubar.setObjectName("menubar")
        Explorer.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(Explorer)
        self.statusbar.setObjectName("statusbar")
        Explorer.setStatusBar(self.statusbar)

        self.retranslateUi(Explorer)
        QtCore.QMetaObject.connectSlotsByName(Explorer)

    def retranslateUi(self, Explorer):
        _translate = QtCore.QCoreApplication.translate
        Explorer.setWindowTitle(_translate("Explorer", "Project Explorer"))
import UI_Icons


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Explorer = QtWidgets.QMainWindow()
    ui = Ui_Explorer()
    ui.setupUi(Explorer)
    Explorer.show()
    sys.exit(app.exec_())
