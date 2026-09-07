import os
import shlex
import shutil
import subprocess
import sys
from urllib.parse import unquote

script_dir = os.path.dirname(os.path.realpath(__file__))
helpers_dir = os.path.join(script_dir, "helpers")
bulk_rename_dir = os.path.join(helpers_dir, "BulkRenameUtility")
project_root = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir))

if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

if helpers_dir not in sys.path:
    sys.path.insert(0, helpers_dir)

if bulk_rename_dir not in sys.path:
    sys.path.insert(0, bulk_rename_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)


from gui_runtime_env import sanitize_current_process_and_reexec
from SessionManager import SessionManager
from Core.myexplorer_picker import run_myexplorer_selection
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

from AdvancedBulkRenamer import AdvancedBulkRenamer

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

            destination_path = self._unique_destination_path(
                target_dir,
                os.path.basename(source_path),
            )

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

        return any(
            url.isLocalFile()
            for url in mime_data.urls()
        )

    @staticmethod
    def _unique_destination_path(target_dir, name):
        base_name, extension = os.path.splitext(name)

        candidate = os.path.join(
            target_dir,
            name,
        )

        counter = 1

        while os.path.exists(candidate):
            candidate = os.path.join(
                target_dir,
                f"{base_name} ({counter}){extension}",
            )
            counter += 1

        return candidate


class MyFileBrowser(MyExplorerUI.Ui_Explorer, QtWidgets.QMainWindow):
    def __init__(
        self,
        start_dir=None,
        maya=False,
        select_mode=False,
        selection_output_path="",
        window_title="",
        selection_kind="folder",
        allow_folder_selection=None,
        allow_file_selection=None,
    ):
        super(MyFileBrowser, self).__init__()

        self.start_dir = start_dir
        self.select_mode = bool(select_mode)
        self.selection_output_path = str(selection_output_path or "")

        self.selection_kind = (
            "file"
            if str(selection_kind or "").strip().lower() == "file"
            else "folder"
        )

        self.allow_folder_selection = (
            self.select_mode and self.selection_kind == "folder"
            if allow_folder_selection is None
            else bool(allow_folder_selection)
        )

        self.allow_file_selection = (
            self.select_mode and self.selection_kind == "file"
            if allow_file_selection is None
            else bool(allow_file_selection)
        )

        self.session_manager = SessionManager()

        self.setupUi(self)

        self._file_clipboard = None
        self._undo_stack = []
        self._redo_stack = []
        self._undo_directory = QtCore.QTemporaryDir()

        if window_title:
            self.setWindowTitle(window_title)

        install_workflow_wizard_menu_actions(
            self,
            'MyExplorer',
            include_project_wizard=False,
            include_page_wizard=True,
        )

        if isinstance(
            getattr(self, "actionPage_Workflow_Wizard", None),
            QtWidgets.QAction,
        ):
            self.actionPage_Workflow_Wizard.setShortcut(
                QtGui.QKeySequence("Ctrl+Alt+W")
            )
            self.actionPage_Workflow_Wizard.setShortcutVisibleInContextMenu(
                True
            )

        self.open_page_workflow_wizard = (
            lambda _requested_module=None:
            open_default_module_page_workflow_wizard(
                self,
                'MyExplorer'
            )
        )

        original_tree = self.treeView

        self.treeView = ExplorerTreeView(self.frame)

        self.gridLayout_2.replaceWidget(
            original_tree,
            self.treeView
        )

        original_tree.deleteLater()

        self.exclude_empty_checkbox.setChecked(
            not self.allow_folder_selection
        )

        self.treeView.setContextMenuPolicy(
            QtCore.Qt.CustomContextMenu
        )

        self.treeView.setSelectionMode(
            QtWidgets.QAbstractItemView.SingleSelection
        )

        self.treeView.setDragDropMode(
            QtWidgets.QAbstractItemView.DragDrop
        )

        self.treeView.setDragEnabled(True)
        self.treeView.setAcceptDrops(True)

        self.treeView.customContextMenuRequested.connect(
            self.context_menu
        )

        self.exclude_empty_checkbox.toggled.connect(
            self._toggle_empty_folder_filter
        )

        if hasattr(self, "show_system_files_checkbox"):
            self.show_system_files_checkbox.setChecked(False)

            self.show_system_files_checkbox.toggled.connect(
                self._toggle_system_files_visibility
            )

        self.treeView.doubleClicked.connect(
            self._on_tree_double_clicked
        )

        if hasattr(self, "actionSelect_Folder"):
            self.actionSelect_Folder.triggered.connect(
                self.select_current_selection
            )

            self.actionSelect_Folder.setEnabled(
                self.select_mode
            )

            if self.select_mode and self.selection_kind == "file":
                self.actionSelect_Folder.setText(
                    "Select File"
                )

        self.selectFolderButton.setVisible(
            self.select_mode
        )

        self.selectFileButton.setVisible(
            self.select_mode
        )

        self.selectFolderButton.setEnabled(
            self.select_mode and self.allow_folder_selection
        )

        self.selectFileButton.setEnabled(
            self.select_mode and self.allow_file_selection
        )

        self.selectFolderButton.clicked.connect(
            lambda: self.select_current_selection("folder")
        )

        self.selectFileButton.clicked.connect(
            lambda: self.select_current_selection("file")
        )

        if hasattr(self, "actionOpen_Trash"):
            self.actionOpen_Trash.triggered.connect(
                self.open_system_trash
            )

        if hasattr(self, "actionRestore_From_Trash"):
            self.actionRestore_From_Trash.triggered.connect(
                self.restore_from_trash
            )

        if hasattr(self, "actionRestore_From_Backup"):
            self.actionRestore_From_Backup.triggered.connect(
                self.restore_from_backup
            )

        if hasattr(self, "actionExit"):
            self.actionExit.triggered.connect(
                self.close
            )

        edit_action_handlers = {
            "actionNew_folder": self.create_new_folder,
            "actionCut": self.cut_selected,
            "actionCopy": self.copy_selected,
            "actionPaste": self.paste_into_current_directory,
            "actionDelete": self.delete_selected,
            "actionMove": self.move_selected,
            "actionUndo": self.undo_file_operation,
            "actionRedo": self.redo_file_operation,
        }

        for action_name, handler in edit_action_handlers.items():
            action = getattr(self, action_name, None)

            if action is not None:
                action.triggered.connect(handler)

        # ---------------------------------------------------------
        # Bulk Rename
        # ---------------------------------------------------------
        if hasattr(self, "actionBulk_Rename"):
            self.actionBulk_Rename.triggered.connect(
                self.open_bulk_rename
            )

        self.populate()

        self.treeView.selectionModel().selectionChanged.connect(
            self._update_edit_action_state
        )

        self.menuEdit.aboutToShow.connect(
            self._update_edit_action_state
        )

        self._update_edit_action_state()

        self.project_status_controller = ProjectStatusController(
            self,
            'MyExplorer',
            session_manager=self.session_manager,
        )

        QtCore.QTimer.singleShot(
            0,
            self._stabilize_window_visibility
        )

    def _stabilize_window_visibility(self):
        # Keep the window visible and focused even when many modules start together.
        if not self.isVisible():
            return

        self.showNormal()
        self.raise_()
        self.activateWindow()

        screen = QtWidgets.QApplication.primaryScreen()

        if screen is None:
            return

        available = screen.availableGeometry()
        frame = self.frameGeometry()

        new_left = max(
            available.left(),
            min(
                frame.left(),
                available.right() - frame.width() + 1
            )
        )

        new_top = max(
            available.top(),
            min(
                frame.top(),
                available.bottom() - frame.height() + 1
            )
        )

        if new_left != frame.left() or new_top != frame.top():
            self.move(
                new_left,
                new_top
            )

    def _resolve_initial_directory(self):
        candidate = (
            self.start_dir
            if self.start_dir and os.path.isdir(self.start_dir)
            else self._resolve_root_directory()
        )

        if not os.path.isdir(candidate):
            candidate = self._resolve_root_directory()

        normalized = os.path.abspath(candidate)

        root_dir = self._resolve_root_directory()

        try:
            if os.path.commonpath(
                [normalized, root_dir]
            ) != os.path.abspath(root_dir):
                normalized = root_dir

        except ValueError:
            normalized = root_dir

        if os.path.isdir(normalized):
            return normalized

        return root_dir

    def _resolve_root_directory(self):
        if (
            getattr(
                self,
                "show_system_files_checkbox",
                None
            ) is not None
            and self.show_system_files_checkbox.isChecked()
        ):
            return os.path.abspath(os.sep)

        if (
            self.select_mode
            and self.start_dir
            and os.path.isdir(self.start_dir)
        ):
            return os.path.abspath(self.start_dir)

        return self._resolve_project_root_directory()

    def _resolve_project_root_directory(self):
        active_project_root = (
            self.session_manager.get_active_project_root()
        )

        candidates = [
            active_project_root,
            self.start_dir,
            RUNTIME_PATHS.project_root,
        ]

        for candidate in candidates:
            if not candidate or not os.path.isdir(candidate):
                continue

            normalized = os.path.abspath(candidate)

            if (
                os.path.basename(normalized) == 'Project'
                and os.path.basename(
                    os.path.dirname(normalized)
                ) == 'Model'
            ):
                normalized = os.path.dirname(
                    os.path.dirname(normalized)
                )

            elif (
                os.path.basename(normalized) == 'Model'
                and os.path.isdir(
                    os.path.join(
                        normalized,
                        'Project'
                    )
                )
            ):
                normalized = os.path.dirname(normalized)

            elif os.path.isdir(
                os.path.join(
                    normalized,
                    'Model',
                    'Project'
                )
            ):
                return normalized

            if os.path.isdir(
                os.path.join(
                    normalized,
                    'Model',
                    'Project'
                )
            ):
                return normalized

        return RUNTIME_PATHS.project_root

    def populate(self):
        dir_path = self._resolve_initial_directory()
        root_dir = self._resolve_root_directory()

        self.model = QtWidgets.QFileSystemModel()
        self.model.setRootPath(root_dir)
        self.model.setReadOnly(False)

        self.model.directoryLoaded.connect(
            lambda _path:
            QtCore.QTimer.singleShot(
                0,
                self._size_tree_columns
            )
        )

        self.proxy_model = EmptyFolderFilterProxyModel(self)

        self.proxy_model.setSourceModel(
            self.model
        )

        self.proxy_model.setExcludeEmptyDirs(
            self.exclude_empty_checkbox.isChecked()
        )

        self.treeView.setModel(
            self.proxy_model
        )

        root_index = self.model.index(root_dir)

        self.treeView.setRootIndex(
            self.proxy_model.mapFromSource(root_index)
        )

        try:
            if os.path.commonpath(
                [
                    os.path.abspath(dir_path),
                    os.path.abspath(root_dir)
                ]
            ) != os.path.abspath(root_dir):
                dir_path = root_dir

        except ValueError:
            dir_path = root_dir

        target_index = self.model.index(dir_path)

        if target_index.isValid():
            proxy_index = (
                self.proxy_model.mapFromSource(
                    target_index
                )
            )

            self.treeView.setCurrentIndex(
                proxy_index
            )

            self.treeView.scrollTo(
                proxy_index,
                QtWidgets.QAbstractItemView.PositionAtCenter
            )

            parent_index = proxy_index.parent()

            while parent_index.isValid():
                self.treeView.expand(parent_index)
                parent_index = parent_index.parent()

            self.treeView.expand(proxy_index)

        self.treeView.setSortingEnabled(True)

        self.treeView.sortByColumn(
            0,
            QtCore.Qt.AscendingOrder
        )

        self.model.sort(
            0,
            QtCore.Qt.AscendingOrder
        )

        QtCore.QTimer.singleShot(
            0,
            self._size_tree_columns
        )

    def _size_tree_columns(self):
        if (
            not getattr(self, "treeView", None)
            or self.treeView.model() is None
        ):
            return

        header = self.treeView.header()
        header.setStretchLastSection(False)

        for column in range(4):
            header.setSectionResizeMode(
                column,
                QtWidgets.QHeaderView.Fixed
            )

        available_width = self.treeView.viewport().width()

        if not self.treeView.verticalScrollBar().isVisible():
            available_width -= (
                self.treeView.style().pixelMetric(
                    QtWidgets.QStyle.PM_ScrollBarExtent
                )
            )

        available_width = max(
            4,
            available_width
        )

        proportions = (
            0.48,
            0.13,
            0.17
        )

        assigned_width = 0

        for column, proportion in enumerate(proportions):
            width = max(
                1,
                int(available_width * proportion)
            )

            self.treeView.setColumnWidth(
                column,
                width
            )

            assigned_width += width

        self.treeView.setColumnWidth(
            3,
            max(
                1,
                available_width - assigned_width
            )
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._size_tree_columns()

    def _toggle_empty_folder_filter(self, enabled):
        self.proxy_model.setExcludeEmptyDirs(enabled)

    def _toggle_system_files_visibility(self, _enabled):
        current_path = self._current_path()

        self.populate()

        if current_path and os.path.isdir(current_path):
            candidate = os.path.abspath(current_path)
            root_dir = self._resolve_root_directory()

            try:
                if os.path.commonpath(
                    [candidate, root_dir]
                ) == os.path.abspath(root_dir):

                    target_index = self.model.index(candidate)

                    if target_index.isValid():
                        proxy_index = (
                            self.proxy_model.mapFromSource(
                                target_index
                            )
                        )

                        if proxy_index.isValid():
                            self.treeView.setCurrentIndex(
                                proxy_index
                            )

                            self.treeView.scrollTo(
                                proxy_index,
                                QtWidgets.QAbstractItemView.PositionAtCenter
                            )

            except ValueError:
                pass

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

    def _selected_existing_path(self):
        path = self._current_path()
        return path if path and os.path.exists(path) else ""

    def _is_root_path(self, path):
        if not path:
            return False

        return os.path.abspath(path) == os.path.abspath(
            self._resolve_root_directory()
        )

    def _update_edit_action_state(self, *_args):
        selected_path = self._selected_existing_path()
        current_directory = self._current_directory()
        editable_selection = bool(
            selected_path
            and not self._is_root_path(selected_path)
        )
        clipboard_source = (
            self._file_clipboard.get("source", "")
            if self._file_clipboard
            else ""
        )

        self.actionNew_folder.setEnabled(
            bool(current_directory and os.path.isdir(current_directory))
        )
        self.actionCut.setEnabled(editable_selection)
        self.actionCopy.setEnabled(bool(selected_path))
        self.actionPaste.setEnabled(
            bool(
                current_directory
                and os.path.isdir(current_directory)
                and clipboard_source
                and os.path.exists(clipboard_source)
            )
        )
        self.actionDelete.setEnabled(editable_selection)
        self.actionMove.setEnabled(editable_selection)
        self.actionUndo.setEnabled(bool(self._undo_stack))
        self.actionRedo.setEnabled(bool(self._redo_stack))

    def _edit_actions(self):
        return (
            self.actionNew_folder,
            self.actionCut,
            self.actionCopy,
            self.actionPaste,
            self.actionDelete,
            self.actionMove,
            self.actionUndo,
            self.actionRedo,
        )

    def _show_file_operation_error(self, title, error):
        QtWidgets.QMessageBox.critical(
            self,
            title,
            f"The file operation could not be completed:\n{error}"
        )

    def _record_file_operation(self, operation):
        self._undo_stack.append(operation)
        self._redo_stack.clear()
        self._update_edit_action_state()

    def _undo_stash_path(self, source_path):
        return ExplorerTreeView._unique_destination_path(
            self._undo_directory.path(),
            os.path.basename(source_path),
        )

    @staticmethod
    def _copy_path(source_path, destination_path):
        if os.path.isdir(source_path):
            shutil.copytree(source_path, destination_path)
        else:
            shutil.copy2(source_path, destination_path)

    @staticmethod
    def _ensure_move_is_safe(source_path, destination_directory):
        if not os.path.isdir(source_path):
            return

        source_path = os.path.abspath(source_path)
        destination_directory = os.path.abspath(destination_directory)

        try:
            if os.path.commonpath(
                [source_path, destination_directory]
            ) == source_path:
                raise ValueError(
                    "A folder cannot be copied or moved into itself."
                )
        except ValueError:
            raise

    def create_new_folder(self):
        parent_directory = self._current_directory()

        if not parent_directory:
            return

        folder_name, accepted = QtWidgets.QInputDialog.getText(
            self,
            "New Folder",
            "Folder name:",
        )

        folder_name = folder_name.strip()

        if not accepted or not folder_name:
            return

        if os.path.basename(folder_name) != folder_name:
            QtWidgets.QMessageBox.warning(
                self,
                "New Folder",
                "Enter a folder name without path separators."
            )
            return

        folder_path = os.path.join(parent_directory, folder_name)

        try:
            os.mkdir(folder_path)
        except OSError as exc:
            self._show_file_operation_error("New Folder", exc)
            return

        self._record_file_operation({
            "kind": "create",
            "path": folder_path,
            "stash": self._undo_stash_path(folder_path),
        })
        self.statusbar.showMessage(f"Created folder: {folder_path}", 5000)

    def cut_selected(self):
        source_path = self._selected_existing_path()

        if not source_path or self._is_root_path(source_path):
            return

        self._file_clipboard = {
            "mode": "cut",
            "source": source_path,
        }
        self.statusbar.showMessage(f"Cut: {source_path}", 5000)
        self._update_edit_action_state()

    def copy_selected(self):
        source_path = self._selected_existing_path()

        if not source_path:
            return

        self._file_clipboard = {
            "mode": "copy",
            "source": source_path,
        }
        self.statusbar.showMessage(f"Copied: {source_path}", 5000)
        self._update_edit_action_state()

    def paste_into_current_directory(self):
        if not self._file_clipboard:
            return

        source_path = self._file_clipboard.get("source", "")
        destination_directory = self._current_directory()

        if not source_path or not os.path.exists(source_path) or not destination_directory:
            self._update_edit_action_state()
            return

        try:
            self._ensure_move_is_safe(source_path, destination_directory)
            destination_path = ExplorerTreeView._unique_destination_path(
                destination_directory,
                os.path.basename(source_path),
            )

            if self._file_clipboard["mode"] == "cut":
                shutil.move(source_path, destination_path)
                operation = {
                    "kind": "move",
                    "source": source_path,
                    "destination": destination_path,
                }
                self._file_clipboard = None
            else:
                self._copy_path(source_path, destination_path)
                operation = {
                    "kind": "create",
                    "path": destination_path,
                    "stash": self._undo_stash_path(destination_path),
                }
        except (OSError, ValueError) as exc:
            self._show_file_operation_error("Paste", exc)
            return

        self._record_file_operation(operation)
        self.statusbar.showMessage(f"Pasted to: {destination_path}", 5000)

    def delete_selected(self):
        source_path = self._selected_existing_path()

        if not source_path or self._is_root_path(source_path):
            return

        answer = QtWidgets.QMessageBox.question(
            self,
            "Delete",
            f"Delete this item? Undo remains available during this MyExplorer session.\n\n{source_path}",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )

        if answer != QtWidgets.QMessageBox.Yes:
            return

        stash_path = self._undo_stash_path(source_path)

        try:
            shutil.move(source_path, stash_path)
        except OSError as exc:
            self._show_file_operation_error("Delete", exc)
            return

        self._record_file_operation({
            "kind": "delete",
            "path": source_path,
            "stash": stash_path,
        })
        self.statusbar.showMessage(f"Deleted: {source_path}", 5000)

    def move_selected(self):
        source_path = self._selected_existing_path()

        if not source_path or self._is_root_path(source_path):
            return

        destination_directory = run_myexplorer_selection(
            "Move To Folder",
            self._current_directory(),
            "folder",
        )

        if not destination_directory:
            return

        try:
            self._ensure_move_is_safe(source_path, destination_directory)
            destination_path = ExplorerTreeView._unique_destination_path(
                destination_directory,
                os.path.basename(source_path),
            )
            shutil.move(source_path, destination_path)
        except (OSError, ValueError) as exc:
            self._show_file_operation_error("Move", exc)
            return

        self._record_file_operation({
            "kind": "move",
            "source": source_path,
            "destination": destination_path,
        })
        self.statusbar.showMessage(f"Moved to: {destination_path}", 5000)

    @staticmethod
    def _move_without_overwrite(source_path, destination_path):
        if not os.path.exists(source_path):
            raise FileNotFoundError(source_path)
        if os.path.exists(destination_path):
            raise FileExistsError(destination_path)

        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        shutil.move(source_path, destination_path)

    def _apply_history_operation(self, operation, undo):
        kind = operation["kind"]

        if kind == "move":
            source_path = operation["destination"] if undo else operation["source"]
            destination_path = operation["source"] if undo else operation["destination"]
        elif kind == "delete":
            source_path = operation["stash"] if undo else operation["path"]
            destination_path = operation["path"] if undo else operation["stash"]
        else:
            source_path = operation["path"] if undo else operation["stash"]
            destination_path = operation["stash"] if undo else operation["path"]

        self._move_without_overwrite(source_path, destination_path)

    def undo_file_operation(self):
        if not self._undo_stack:
            return

        operation = self._undo_stack[-1]

        try:
            self._apply_history_operation(operation, undo=True)
        except OSError as exc:
            self._show_file_operation_error("Undo", exc)
            return

        self._redo_stack.append(self._undo_stack.pop())
        self.statusbar.showMessage("File operation undone.", 5000)
        self._update_edit_action_state()

    def redo_file_operation(self):
        if not self._redo_stack:
            return

        operation = self._redo_stack[-1]

        try:
            self._apply_history_operation(operation, undo=False)
        except OSError as exc:
            self._show_file_operation_error("Redo", exc)
            return

        self._undo_stack.append(self._redo_stack.pop())
        self.statusbar.showMessage("File operation redone.", 5000)
        self._update_edit_action_state()

    def _on_tree_double_clicked(self, _index):
        if self.select_mode:
            self.select_current_selection(
                self.selection_kind
            )

    def _write_selection_output(self, selected_path):
        if not self.selection_output_path:
            return

        try:
            with open(
                self.selection_output_path,
                "w",
                encoding="utf-8"
            ) as handle:
                handle.write(selected_path)

        except OSError as exc:
            QtWidgets.QMessageBox.warning(
                self,
                "MyExplorer",
                f"Could not persist selection output:\n{exc}",
            )

    def select_current_selection(self, selection_kind=None):
        selection_kind = (
            selection_kind
            or self.selection_kind
        )

        if (
            selection_kind == "file"
            and not self.allow_file_selection
        ):
            return

        if (
            selection_kind == "folder"
            and not self.allow_folder_selection
        ):
            return

        if selection_kind == "file":
            selected_path = self._current_path()

            if (
                not selected_path
                or not os.path.isfile(selected_path)
            ):
                QtWidgets.QMessageBox.information(
                    self,
                    "Select File",
                    "Select a file first."
                )
                return

            self._write_selection_output(
                selected_path
            )

        else:
            selected_dir = self._current_directory()

            if not selected_dir:
                QtWidgets.QMessageBox.information(
                    self,
                    "Select Folder",
                    "Select a folder first."
                )
                return

            self._write_selection_output(
                selected_dir
            )

        if self.select_mode:
            self.close()

    def select_current_folder(self):
        self.select_current_selection()

    def open_bulk_rename(self):
        """
        Launch the Advanced Bulk Rename utility.

        The utility is kept as a separate tool under:

            helpers/BulkRenameUtility/

        MyExplorer supplies the currently selected directory
        as the initial directory for the renamer.
        """

        existing = getattr(
            self,
            "bulk_renamer",
            None
        )

        if existing is not None:
            try:
                if existing.isVisible():
                    existing.showNormal()
                    existing.raise_()
                    existing.activateWindow()
                    return

            except RuntimeError:
                self.bulk_renamer = None

        self.bulk_renamer = AdvancedBulkRenamer()

        start_dir = (
            self._current_directory()
            or self._resolve_initial_directory()
        )

        if start_dir and os.path.isdir(start_dir):
            self.bulk_renamer.dir_input.setText(
                start_dir
            )

            self.bulk_renamer.load_files()

        self.bulk_renamer.setAttribute(
            QtCore.Qt.WA_DeleteOnClose,
            True
        )

        self.bulk_renamer.destroyed.connect(
            lambda:
            setattr(
                self,
                "bulk_renamer",
                None
            )
        )

        self.bulk_renamer.show()
        self.bulk_renamer.raise_()
        self.bulk_renamer.activateWindow()

    def open_system_trash(self):
        if sys.platform.startswith("win"):
            subprocess.Popen(
                [
                    "explorer.exe",
                    "shell:RecycleBinFolder"
                ]
            )
            return

        if sys.platform == "darwin":
            subprocess.Popen(
                [
                    "open",
                    os.path.expanduser("~/.Trash")
                ]
            )
            return

        trash_dir = os.path.expanduser(
            "~/.local/share/Trash/files"
        )

        if not os.path.isdir(trash_dir):
            QtWidgets.QMessageBox.information(
                self,
                "System Trash",
                "Trash folder was not found on this system."
            )
            return

        subprocess.Popen(
            [
                "xdg-open",
                trash_dir
            ]
        )

    def _trash_paths(self):
        trash_files = os.path.expanduser(
            "~/.local/share/Trash/files"
        )

        trash_info = os.path.expanduser(
            "~/.local/share/Trash/info"
        )

        return trash_files, trash_info

    def _trash_original_path(self, info_path):
        if not os.path.isfile(info_path):
            return ""

        try:
            with open(
                info_path,
                "r",
                encoding="utf-8"
            ) as handle:

                for line in handle:
                    if line.startswith("Path="):
                        return unquote(
                            line.strip().split(
                                "=",
                                1
                            )[1]
                        )

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
            QtWidgets.QMessageBox.information(
                self,
                "Restore From Trash",
                "No trash folder is available."
            )
            return

        items = sorted(
            [
                name
                for name in os.listdir(trash_files)
                if name not in (".", "..")
            ]
        )

        if not items:
            QtWidgets.QMessageBox.information(
                self,
                "Restore From Trash",
                "Trash is empty."
            )
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

        trashed_path = os.path.join(
            trash_files,
            selected_item
        )

        info_path = os.path.join(
            trash_info,
            f"{selected_item}.trashinfo"
        )

        original_path = self._trash_original_path(
            info_path
        )

        default_target = (
            self._current_directory()
            or RUNTIME_PATHS.project_root
        )

        if original_path:
            original_parent = os.path.dirname(
                original_path
            )

            if (
                original_parent
                and os.path.isdir(original_parent)
            ):
                default_target = original_parent

        restore_dir = (
            QtWidgets.QFileDialog.getExistingDirectory(
                self,
                "Restore From Trash: Select destination folder",
                default_target,
            )
        )

        if not restore_dir:
            return

        destination = (
            ExplorerTreeView._unique_destination_path(
                restore_dir,
                os.path.basename(trashed_path)
            )
        )

        try:
            shutil.move(
                trashed_path,
                destination
            )

            if os.path.isfile(info_path):
                os.remove(info_path)

        except OSError as exc:
            QtWidgets.QMessageBox.critical(
                self,
                "Restore From Trash",
                f"Restore failed:\n{exc}"
            )
            return

        QtWidgets.QMessageBox.information(
            self,
            "Restore From Trash",
            f"Item restored to:\n{destination}"
        )

    def restore_from_backup(self):
        destination_dir = (
            self._current_directory()
            or RUNTIME_PATHS.project_root
        )

        source_type, ok = QtWidgets.QInputDialog.getItem(
            self,
            "Restore From Backup",
            "Select backup source type:",
            [
                "File",
                "Folder"
            ],
            0,
            False,
        )

        if not ok or not source_type:
            return

        source_path = ""

        if source_type == "File":
            source_path = (
                QtWidgets.QFileDialog.getOpenFileName(
                    self,
                    "Restore From Backup: Select source file",
                    destination_dir,
                    "All Files (*.*)",
                )[0]
            )

        else:
            source_path = (
                QtWidgets.QFileDialog.getExistingDirectory(
                    self,
                    "Restore From Backup: Select source folder",
                    destination_dir,
                )
            )

        if not source_path:
            return

        if not os.path.exists(source_path):
            QtWidgets.QMessageBox.warning(
                self,
                "Restore From Backup",
                "Selected source does not exist."
            )
            return

        destination_path = (
            ExplorerTreeView._unique_destination_path(
                destination_dir,
                os.path.basename(source_path),
            )
        )

        try:
            if os.path.isdir(source_path):
                shutil.copytree(
                    source_path,
                    destination_path
                )
            else:
                shutil.copy2(
                    source_path,
                    destination_path
                )

        except OSError as exc:
            QtWidgets.QMessageBox.critical(
                self,
                "Restore From Backup",
                f"Restore failed:\n{exc}"
            )
            return

        QtWidgets.QMessageBox.information(
            self,
            "Restore From Backup",
            f"Copied to:\n{destination_path}"
        )

    def context_menu(self, position):
        clicked_index = self.treeView.indexAt(position)

        if clicked_index.isValid():
            self.treeView.setCurrentIndex(clicked_index)

        self._update_edit_action_state()

        menu = QtWidgets.QMenu(self)

        open_action = menu.addAction(
            "Open with operating system"
        )

        open_action.setEnabled(
            bool(self._selected_existing_path())
        )

        open_action.triggered.connect(
            self.open_file
        )

        menu.addSeparator()

        edit_actions = self._edit_actions()

        for action in edit_actions[:6]:
            menu.addAction(action)

        menu.addSeparator()
        menu.addAction(edit_actions[6])
        menu.addAction(edit_actions[7])

        menu.addSeparator()

        append_default_context_actions(
            menu,
            self.treeView,
            is_text_widget=False
        )

        menu.exec_(
            self.treeView.viewport().mapToGlobal(position)
        )

    def open_file(self):
        index = self.treeView.currentIndex()

        if not index.isValid():
            return

        if hasattr(self.proxy_model, "mapToSource"):
            source_index = self.proxy_model.mapToSource(
                index
            )

            file_path = self.model.filePath(
                source_index
            )

        else:
            file_path = self.model.filePath(
                index
            )

        if sys.platform.startswith("win"):
            os.startfile(file_path)
            return

        if sys.platform == "darwin":
            subprocess.Popen(
                [
                    "open",
                    file_path
                ]
            )
            return

        subprocess.Popen(
            [
                "xdg-open",
                file_path
            ]
        )


if __name__ == '__main__':
    app = QtWidgets.QApplication([])

    start_dir = None
    select_dir_mode = False
    select_file_mode = False
    output_file = ""
    window_title = ""

    argv = list(sys.argv[1:])
    i = 0

    while i < len(argv):
        arg = argv[i]

        if arg == "--select-dir":
            select_dir_mode = True

        elif arg == "--select-file":
            select_file_mode = True
            window_title = (
                window_title
                or "MyExplorer File Picker"
            )

        elif (
            arg == "--start-dir"
            and i + 1 < len(argv)
        ):
            i += 1
            start_dir = argv[i]

        elif (
            arg == "--output-file"
            and i + 1 < len(argv)
        ):
            i += 1
            output_file = argv[i]

        elif (
            arg == "--title"
            and i + 1 < len(argv)
        ):
            i += 1
            window_title = argv[i]

        elif (
            not arg.startswith("--")
            and start_dir is None
        ):
            start_dir = arg

        i += 1

    fb = MyFileBrowser(
        start_dir=start_dir,
        select_mode=(
            select_dir_mode
            or select_file_mode
        ),
        selection_output_path=output_file,
        window_title=window_title,
        selection_kind=(
            "file"
            if select_file_mode
            else "folder"
        ),
        allow_folder_selection=select_dir_mode,
        allow_file_selection=select_file_mode,
    )

    fb.show()
    app.exec_()