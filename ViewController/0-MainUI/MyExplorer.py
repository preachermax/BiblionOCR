import os
import shlex
import shutil
import subprocess
import sys
from urllib.parse import unquote

script_dir = os.path.dirname(os.path.realpath(__file__))
helpers_dir = os.path.join(script_dir, "helpers")
project_root = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)
if helpers_dir not in sys.path:
    sys.path.insert(0, helpers_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from gui_runtime_env import sanitize_current_process_and_reexec
from SessionManager import SessionManager
from Core.workflow_wizard_actions import (
    append_default_context_actions,
    install_workflow_wizard_menu_actions,
    open_default_module_page_workflow_wizard,
)


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

from LocalFileDrop import EmptyFolderFilterProxyModel
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
            return self._resolve_model_path(model, index)
        return self._resolve_root_path(model)

    @staticmethod
    def _resolve_model_path(model, index):
        if hasattr(model, "mapToSource") and hasattr(model, "sourceModel"):
            source_model = model.sourceModel()
            if source_model is not None:
                source_index = model.mapToSource(index)
                if source_index.isValid():
                    return source_model.filePath(source_index)
        if hasattr(model, "filePath"):
            return model.filePath(index)
        return ""

    @staticmethod
    def _resolve_root_path(model):
        if hasattr(model, "rootPath"):
            return model.rootPath()
        if hasattr(model, "sourceModel") and model.sourceModel() is not None:
            return model.sourceModel().rootPath()
        return ""

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
    def __init__(self, start_dir=None, maya=False, select_mode=False, selection_output_path="", window_title=""):
        super(MyFileBrowser, self).__init__()
        self.start_dir = start_dir
        self.select_mode = bool(select_mode)
        self.selection_output_path = str(selection_output_path or "")
        self.session_manager = SessionManager()
        self.setupUi(self)
        if window_title:
            self.setWindowTitle(window_title)
        install_workflow_wizard_menu_actions(
            self,
            'MyExplorer',
            include_project_wizard=False,
            include_page_wizard=True,
        )
        self.open_page_workflow_wizard = (
            lambda _requested_module=None: open_default_module_page_workflow_wizard(self, 'MyExplorer')
        )
        original_tree = self.treeView
        self.treeView = ExplorerTreeView(self.frame)
        self.gridLayout_2.replaceWidget(original_tree, self.treeView)
        original_tree.deleteLater()

        self.exclude_empty_checkbox.setChecked(True)

        self.treeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeView.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.treeView.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.treeView.setDragEnabled(True)
        self.treeView.setAcceptDrops(True)
        self.treeView.customContextMenuRequested.connect(self.context_menu)
        self.exclude_empty_checkbox.toggled.connect(self._toggle_empty_folder_filter)
        self.treeView.doubleClicked.connect(self._on_tree_double_clicked)

        if hasattr(self, "actionSelect_Folder"):
            self.actionSelect_Folder.triggered.connect(self.select_current_folder)
            self.actionSelect_Folder.setEnabled(self.select_mode)
        if hasattr(self, "actionOpen_Trash"):
            self.actionOpen_Trash.triggered.connect(self.open_system_trash)
        if hasattr(self, "actionRestore_From_Trash"):
            self.actionRestore_From_Trash.triggered.connect(self.restore_from_trash)
        if hasattr(self, "actionRestore_From_Backup"):
            self.actionRestore_From_Backup.triggered.connect(self.restore_from_backup)
        if hasattr(self, "actionExit"):
            self.actionExit.triggered.connect(self.close)

        self.populate()
        self.project_status_controller = ProjectStatusController(
            self,
            'MyExplorer',
            session_manager=self.session_manager,
        )
        QtCore.QTimer.singleShot(0, self._stabilize_window_visibility)

    def _stabilize_window_visibility(self):
        # Keep the window visible and focused even when many modules start together.
        self.showNormal()
        self.raise_()
        self.activateWindow()

        screen = QtWidgets.QApplication.primaryScreen()
        if screen is None:
            return

        available = screen.availableGeometry()
        frame = self.frameGeometry()
        new_left = max(available.left(), min(frame.left(), available.right() - frame.width() + 1))
        new_top = max(available.top(), min(frame.top(), available.bottom() - frame.height() + 1))

        if new_left != frame.left() or new_top != frame.top():
            self.move(new_left, new_top)

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

        self.proxy_model = EmptyFolderFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setExcludeEmptyDirs(self.exclude_empty_checkbox.isChecked())
        self.treeView.setModel(self.proxy_model)

        root_index = self.model.index(root_dir)
        self.treeView.setRootIndex(self.proxy_model.mapFromSource(root_index))

        try:
            if os.path.commonpath([os.path.abspath(dir_path), os.path.abspath(root_dir)]) != os.path.abspath(root_dir):
                dir_path = root_dir
        except ValueError:
            dir_path = root_dir

        target_index = self.model.index(dir_path)
        if target_index.isValid():
            proxy_index = self.proxy_model.mapFromSource(target_index)
            self.treeView.setCurrentIndex(proxy_index)
            self.treeView.scrollTo(proxy_index, QtWidgets.QAbstractItemView.PositionAtCenter)

            parent_index = proxy_index.parent()
            while parent_index.isValid():
                self.treeView.expand(parent_index)
                parent_index = parent_index.parent()

            self.treeView.expand(proxy_index)
        self.treeView.setSortingEnabled(True)
        self.treeView.sortByColumn(0, QtCore.Qt.AscendingOrder)
        self.model.sort(0, QtCore.Qt.AscendingOrder)

    def _toggle_empty_folder_filter(self, enabled):
        self.proxy_model.setExcludeEmptyDirs(enabled)

    def _current_path(self):
        index = self.treeView.currentIndex()
        if not index.isValid():
            return ""
        if hasattr(self.proxy_model, "mapToSource"):
            source_index = self.proxy_model.mapToSource(index)
            return self.model.filePath(source_index)
        return self.model.filePath(index)

    def _current_directory(self):
        path = self._current_path()
        if not path:
            return ""
        if os.path.isdir(path):
            return path
        return os.path.dirname(path)

    def _on_tree_double_clicked(self, _index):
        if self.select_mode:
            self.select_current_folder()

    def _write_selection_output(self, selected_path):
        if not self.selection_output_path:
            return
        try:
            with open(self.selection_output_path, "w", encoding="utf-8") as handle:
                handle.write(selected_path)
        except OSError as exc:
            QtWidgets.QMessageBox.warning(
                self,
                "MyExplorer",
                f"Could not persist selection output:\n{exc}",
            )

    def select_current_folder(self):
        selected_dir = self._current_directory()
        if not selected_dir:
            QtWidgets.QMessageBox.information(self, "Select Folder", "Select a folder first.")
            return

        self._write_selection_output(selected_dir)
        if self.select_mode:
            self.close()

    def open_system_trash(self):
        if sys.platform.startswith("win"):
            subprocess.Popen(["explorer.exe", "shell:RecycleBinFolder"])
            return

        if sys.platform == "darwin":
            subprocess.Popen(["open", os.path.expanduser("~/.Trash")])
            return

        trash_dir = os.path.expanduser("~/.local/share/Trash/files")
        if not os.path.isdir(trash_dir):
            QtWidgets.QMessageBox.information(self, "System Trash", "Trash folder was not found on this system.")
            return
        subprocess.Popen(["xdg-open", trash_dir])

    def _trash_paths(self):
        trash_files = os.path.expanduser("~/.local/share/Trash/files")
        trash_info = os.path.expanduser("~/.local/share/Trash/info")
        return trash_files, trash_info

    def _trash_original_path(self, info_path):
        if not os.path.isfile(info_path):
            return ""

        try:
            with open(info_path, "r", encoding="utf-8") as handle:
                for line in handle:
                    if line.startswith("Path="):
                        return unquote(line.strip().split("=", 1)[1])
        except OSError:
            return ""
        return ""

    def restore_from_trash(self):
        if sys.platform.startswith("win"):
            QtWidgets.QMessageBox.information(
                self,
                "Restore From Trash",
                "Windows recycle-bin restore is not implemented in MyExplorer yet.",
            )
            return

        trash_files, trash_info = self._trash_paths()
        if not os.path.isdir(trash_files):
            QtWidgets.QMessageBox.information(self, "Restore From Trash", "No trash folder is available.")
            return

        items = sorted([name for name in os.listdir(trash_files) if name not in (".", "..")])
        if not items:
            QtWidgets.QMessageBox.information(self, "Restore From Trash", "Trash is empty.")
            return

        selected_item, ok = QtWidgets.QInputDialog.getItem(
            self,
            "Restore From Trash",
            "Select trashed item:",
            items,
            0,
            False,
        )
        if not ok or not selected_item:
            return

        trashed_path = os.path.join(trash_files, selected_item)
        info_path = os.path.join(trash_info, f"{selected_item}.trashinfo")
        original_path = self._trash_original_path(info_path)

        default_target = self._current_directory() or RUNTIME_PATHS.project_root
        if original_path:
            original_parent = os.path.dirname(original_path)
            if original_parent and os.path.isdir(original_parent):
                default_target = original_parent

        restore_dir = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Restore From Trash: Select destination folder",
            default_target,
        )
        if not restore_dir:
            return

        destination = ExplorerTreeView._unique_destination_path(restore_dir, os.path.basename(trashed_path))
        try:
            shutil.move(trashed_path, destination)
            if os.path.isfile(info_path):
                os.remove(info_path)
        except OSError as exc:
            QtWidgets.QMessageBox.critical(self, "Restore From Trash", f"Restore failed:\n{exc}")
            return

        QtWidgets.QMessageBox.information(self, "Restore From Trash", f"Item restored to:\n{destination}")

    def restore_from_backup(self):
        destination_dir = self._current_directory() or RUNTIME_PATHS.project_root
        source_type, ok = QtWidgets.QInputDialog.getItem(
            self,
            "Restore From Backup",
            "Select backup source type:",
            ["File", "Folder"],
            0,
            False,
        )
        if not ok or not source_type:
            return

        source_path = ""
        if source_type == "File":
            source_path = QtWidgets.QFileDialog.getOpenFileName(
                self,
                "Restore From Backup: Select source file",
                destination_dir,
                "All Files (*.*)",
            )[0]
        else:
            source_path = QtWidgets.QFileDialog.getExistingDirectory(
                self,
                "Restore From Backup: Select source folder",
                destination_dir,
            )

        if not source_path:
            return
        if not os.path.exists(source_path):
            QtWidgets.QMessageBox.warning(self, "Restore From Backup", "Selected source does not exist.")
            return

        destination_path = ExplorerTreeView._unique_destination_path(
            destination_dir,
            os.path.basename(source_path),
        )

        try:
            if os.path.isdir(source_path):
                shutil.copytree(source_path, destination_path)
            else:
                shutil.copy2(source_path, destination_path)
        except OSError as exc:
            QtWidgets.QMessageBox.critical(self, "Restore From Backup", f"Restore failed:\n{exc}")
            return

        QtWidgets.QMessageBox.information(self, "Restore From Backup", f"Copied to:\n{destination_path}")

    def context_menu(self):
        menu = QtWidgets.QMenu()
        open = menu.addAction("Open with operating system")
        open.triggered.connect(self.open_file)
        append_default_context_actions(menu, self.treeView, is_text_widget=False)
        cursor = QtGui.QCursor()
        menu.exec_(cursor.pos())

    def open_file(self):
        index = self.treeView.currentIndex()
        if not index.isValid():
            return
        if hasattr(self.proxy_model, "mapToSource"):
            source_index = self.proxy_model.mapToSource(index)
            file_path = self.model.filePath(source_index)
        else:
            file_path = self.model.filePath(index)
        if sys.platform.startswith("win"):
            os.startfile(file_path)
            return
        if sys.platform == "darwin":
            subprocess.Popen(["open", file_path])
            return
        subprocess.Popen(["xdg-open", file_path])

if __name__ == '__main__':
    app = QtWidgets.QApplication([])

    start_dir = None
    select_dir_mode = False
    output_file = ""
    window_title = ""

    argv = list(sys.argv[1:])
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--select-dir":
            select_dir_mode = True
        elif arg == "--start-dir" and i + 1 < len(argv):
            i += 1
            start_dir = argv[i]
        elif arg == "--output-file" and i + 1 < len(argv):
            i += 1
            output_file = argv[i]
        elif arg == "--title" and i + 1 < len(argv):
            i += 1
            window_title = argv[i]
        elif not arg.startswith("--") and start_dir is None:
            start_dir = arg
        i += 1

    fb = MyFileBrowser(
        start_dir=start_dir,
        select_mode=select_dir_mode,
        selection_output_path=output_file,
        window_title=window_title,
    )
    fb.show()
    app.exec_()