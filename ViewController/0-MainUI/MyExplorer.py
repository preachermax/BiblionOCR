import os
import shlex
import shutil
import sys
from gui_runtime_env import sanitize_current_process_and_reexec
from SessionManager import SessionManager


sanitize_current_process_and_reexec()

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

RUNTIME_PATHS = SessionManager.export_runtime_paths(
    globals(),
    __file__,
    add_developer_view=True,
)

from project_status_controller import ProjectStatusController

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
    def __init__(self, start_dir=None, maya=False):
        super(MyFileBrowser, self).__init__()
        self.start_dir = start_dir
        self.session_manager = SessionManager()
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
        self.project_status_controller = ProjectStatusController(
            self,
            'MyExplorer',
            session_manager=self.session_manager,
        )

    def _resolve_initial_directory(self):
        candidate = self.start_dir if self.start_dir and os.path.isdir(self.start_dir) else RUNTIME_PATHS.model_dir
        if not os.path.isdir(candidate):
            candidate = RUNTIME_PATHS.project_root

        normalized = os.path.abspath(candidate)

        if os.path.basename(normalized) == 'Project' and os.path.basename(os.path.dirname(normalized)) == 'Model':
            normalized = os.path.dirname(normalized)
        elif os.path.isdir(os.path.join(normalized, 'Model', 'Project')):
            normalized = os.path.join(normalized, 'Model')

        if os.path.isdir(normalized):
            return normalized
        if os.path.isdir(RUNTIME_PATHS.model_dir):
            return RUNTIME_PATHS.model_dir
        return RUNTIME_PATHS.project_root

    def _resolve_project_root_directory(self):
        active_project_root = self.session_manager.get_active_project_root()
        candidates = [
            active_project_root,
            self.start_dir,
            RUNTIME_PATHS.project_root,
        ]

        for candidate in candidates:
            if not candidate or not os.path.isdir(candidate):
                continue

            normalized = os.path.abspath(candidate)

            if os.path.basename(normalized) == 'Project' and os.path.basename(os.path.dirname(normalized)) == 'Model':
                normalized = os.path.dirname(os.path.dirname(normalized))
            elif os.path.basename(normalized) == 'Model' and os.path.isdir(os.path.join(normalized, 'Project')):
                normalized = os.path.dirname(normalized)
            elif os.path.isdir(os.path.join(normalized, 'Model', 'Project')):
                return normalized

            if os.path.isdir(os.path.join(normalized, 'Model', 'Project')):
                return normalized

        return RUNTIME_PATHS.project_root

    def populate(self):
        dir_path = self._resolve_initial_directory()
        root_dir = self._resolve_project_root_directory()

        self.model = QtWidgets.QFileSystemModel()
        self.model.setRootPath(root_dir)
        self.model.setReadOnly(False)
        self.treeView.setModel(self.model)
        root_index = self.model.index(root_dir)
        self.treeView.setRootIndex(root_index)

        try:
            if os.path.commonpath([os.path.abspath(dir_path), os.path.abspath(root_dir)]) != os.path.abspath(root_dir):
                dir_path = root_dir
        except ValueError:
            dir_path = root_dir

        target_index = self.model.index(dir_path)
        if target_index.isValid():
            self.treeView.setCurrentIndex(target_index)
            self.treeView.scrollTo(target_index, QtWidgets.QAbstractItemView.PositionAtCenter)

            parent_index = target_index.parent()
            while parent_index.isValid():
                self.treeView.expand(parent_index)
                parent_index = parent_index.parent()

            self.treeView.expand(target_index)
        self.treeView.setSortingEnabled(True)
        self.treeView.sortByColumn(0, QtCore.Qt.AscendingOrder)
        self.model.sort(0, QtCore.Qt.AscendingOrder)

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
    start_dir = sys.argv[1] if len(sys.argv) > 1 else None
    fb = MyFileBrowser(start_dir=start_dir)
    fb.show()
    app.exec_()