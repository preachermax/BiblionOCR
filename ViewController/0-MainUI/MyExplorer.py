from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore
import os
import shlex
import sys

script_dir = os.path.dirname(os.path.realpath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir))

import MyExplorerUI

class MyFileBrowser(MyExplorerUI.Ui_Explorer, QtWidgets.QMainWindow):
    def __init__(self, maya=False):
        super(MyFileBrowser, self).__init__()
        self.setupUi(self)
        self.treeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeView.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.treeView.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.treeView.setDragEnabled(True)
        self.treeView.customContextMenuRequested.connect(self.context_menu)
        
        self.populate()

    def populate(self):
        dir_path = os.path.join(project_root, 'Model', 'Project')
        self.model = QtWidgets.QFileSystemModel()
        self.model.setRootPath(dir_path)
        self.treeView.setModel(self.model)
        self.treeView.setRootIndex(self.model.index(dir_path))
        self.treeView.setSortingEnabled(True)

    def context_menu(self):
        menu = QtWidgets.QMenu()
        open = menu.addAction("Open with operating system")
        open.triggered.connect(self.open_file)
        cursor = QtGui.QCursor()
        menu.exec_(cursor.pos())

    def open_file(self):
        index = self.treeView.currentIndex()
        file_path = self.model.filePath(index)
        # For Windows: os.startfile(file_path)
        os.system("xdg-open " + shlex.quote(file_path))

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    fb = MyFileBrowser()
    fb.show()
    app.exec_()