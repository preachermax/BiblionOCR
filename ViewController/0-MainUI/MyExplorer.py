from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore
import os
import shlex
import shutil
import sys

script_dir = os.path.dirname(os.path.realpath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir))

import MyExplorerUI


class ExplorerTreeView(QtWidgets.QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDropIndicatorShown(True)

    def dragEnterEvent(self, event):
        if self._has_local_urls(event.mimeData()):
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if self._has_local_urls(event.mimeData()):
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.source() is self:
            super().dropEvent(event)
            return

        if not self._has_local_urls(event.mimeData()):
            super().dropEvent(event)
            return

        target_dir = self._target_directory(event.pos())
        if not target_dir:
            event.ignore()
            return

        copied_any = False
        for url in event.mimeData().urls():
            if not url.isLocalFile():
                continue
            source_path = url.toLocalFile()
            if not source_path or not os.path.exists(source_path):
                continue

            destination_path = self._unique_destination_path(target_dir, os.path.basename(source_path))
            if os.path.isdir(source_path):
                shutil.copytree(source_path, destination_path)
            else:
                shutil.copy2(source_path, destination_path)
            copied_any = True

        if copied_any:
            event.acceptProposedAction()
        else:
            event.ignore()

    def _target_directory(self, position):
        model = self.model()
        if model is None:
            return ""

        index = self.indexAt(position)
        if index.isValid() and not model.isDir(index):
            index = index.parent()

        if index.isValid():
            return model.filePath(index)
        return model.rootPath()

    @staticmethod
    def _has_local_urls(mime_data):
        if not mime_data.hasUrls():
            return False
        return any(url.isLocalFile() for url in mime_data.urls())

    @staticmethod
    def _unique_destination_path(target_dir, name):
        base_name, extension = os.path.splitext(name)
        candidate = os.path.join(target_dir, name)
        counter = 1
        while os.path.exists(candidate):
            candidate = os.path.join(target_dir, f"{base_name} ({counter}){extension}")
            counter += 1
        return candidate

class MyFileBrowser(MyExplorerUI.Ui_Explorer, QtWidgets.QMainWindow):
    def __init__(self, maya=False):
        super(MyFileBrowser, self).__init__()
        self.setupUi(self)
        original_tree = self.treeView
        self.treeView = ExplorerTreeView(self.frame)
        self.gridLayout_2.replaceWidget(original_tree, self.treeView)
        original_tree.deleteLater()
        self.treeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeView.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.treeView.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.treeView.setDragEnabled(True)
        self.treeView.setAcceptDrops(True)
        self.treeView.customContextMenuRequested.connect(self.context_menu)
        
        self.populate()

    def populate(self):
        dir_path = os.path.join(project_root, 'Model', 'Project')
        self.model = QtWidgets.QFileSystemModel()
        self.model.setRootPath(dir_path)
        self.model.setReadOnly(False)
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