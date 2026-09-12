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

        original_tree.hide()
        original_tree.setParent(None)
        self.treeView = ExplorerTreeView(self.browserSplitter)
        self.treeView.setMinimumWidth(220)
        self.treeView.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding,
        )
        self.browserSplitter.insertWidget(0, self.treeView)
        self.browserSplitter.setStretchFactor(0, 0)
        self.browserSplitter.setStretchFactor(1, 1)

        original_tree.deleteLater()

        self.exclude_empty_checkbox.setChecked(
            not self.allow_folder_selection
        )

        self.treeView.setContextMenuPolicy(
            QtCore.Qt.CustomContextMenu
        )

        self.treeView.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection
        )

        self.treeView.setDragDropMode(
            QtWidgets.QAbstractItemView.DragDrop
        )

        self.treeView.setDragEnabled(True)
        self.treeView.setAcceptDrops(True)
        self.treeView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.treeView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        self.treeView.customContextMenuRequested.connect(
            lambda position: self.context_menu(position, self.treeView)
        )

        for content_view in (self.detailsView, self.itemsView):
            content_view.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding,
                QtWidgets.QSizePolicy.Expanding,
            )
            content_view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
            content_view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
            content_view.setSelectionMode(
                QtWidgets.QAbstractItemView.ExtendedSelection
            )
            content_view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            content_view.customContextMenuRequested.connect(
                lambda position, view=content_view: self.context_menu(position, view)
            )
            content_view.doubleClicked.connect(self._on_content_double_clicked)

        self.detailsView.setRootIsDecorated(False)
        self.detailsView.setItemsExpandable(False)
        self.detailsView.header().setSectionsClickable(True)
        self.detailsView.header().setSortIndicatorShown(True)
        self.itemsView.setResizeMode(QtWidgets.QListView.Adjust)
        self.itemsView.setUniformItemSizes(True)

        self._view_mode_group = QtWidgets.QActionGroup(self)
        self._view_mode_group.setExclusive(True)
        for action in (
            self.actionSimple_List,
            self.actionDetails,
            self.actionIcons,
        ):
            self._view_mode_group.addAction(action)

        self.actionSimple_List.triggered.connect(
            lambda: self._set_content_view_mode("list")
        )
        self.actionDetails.triggered.connect(
            lambda: self._set_content_view_mode("details")
        )
        self.actionIcons.triggered.connect(
            lambda: self._set_content_view_mode("icons")
        )
        self.actionOpen.triggered.connect(self.open_file)

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
            self._on_folder_selection_changed
        )

        self.treeView.selectionModel().selectionChanged.connect(
            self._update_edit_action_state
        )

        self.detailsView.selectionModel().selectionChanged.connect(
            self._update_edit_action_state
        )

        self.detailsView.selectionModel().selectionChanged.connect(
            lambda *_args: self._update_relative_path(self.detailsView)
        )

        self.itemsView.selectionModel().selectionChanged.connect(
            self._update_edit_action_state
        )

        self.itemsView.selectionModel().selectionChanged.connect(
            lambda *_args: self._update_relative_path(self.itemsView)
        )

        self.menuEdit.aboutToShow.connect(
            self._update_edit_action_state
        )

        self._update_edit_action_state()
        self._set_content_view_mode("details")

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

        self.folder_model = QtWidgets.QFileSystemModel()
        self.folder_model.setFilter(
            QtCore.QDir.AllDirs | QtCore.QDir.NoDotAndDotDot
        )
        self.folder_model.setRootPath(root_dir)
        self.folder_model.setReadOnly(False)
        self.model = self.folder_model

        self.proxy_model = EmptyFolderFilterProxyModel(self)

        self.proxy_model.setSourceModel(
            self.folder_model
        )

        self.proxy_model.setExcludeEmptyDirs(
            self.exclude_empty_checkbox.isChecked()
        )

        self.treeView.setModel(
            self.proxy_model
        )

        for column in range(1, 4):
            self.treeView.hideColumn(column)

        self.content_model = QtWidgets.QFileSystemModel()
        self.content_model.setFilter(
            QtCore.QDir.AllEntries | QtCore.QDir.NoDotAndDotDot
        )
        self.content_model.setRootPath(root_dir)
        self.content_model.setReadOnly(False)
        self.detailsView.setModel(self.content_model)
        self.itemsView.setModel(self.content_model)

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

        self.folder_model.sort(
            0,
            QtCore.Qt.AscendingOrder
        )

        self.detailsView.setSortingEnabled(True)
        self.detailsView.sortByColumn(0, QtCore.Qt.AscendingOrder)
        self.content_model.sort(0, QtCore.Qt.AscendingOrder)
        self._show_directory(dir_path)

        QtCore.QTimer.singleShot(
            0,
            self._initialize_browser_geometry
        )

    def _initialize_browser_geometry(self):
        if (
            not getattr(self, "treeView", None)
            or self.treeView.model() is None
            or self.detailsView.model() is None
        ):
            return

        available_width = max(1, self.browserSplitter.width())
        left_width = min(260, max(220, available_width // 4))
        self.browserSplitter.setSizes(
            [left_width, max(1, available_width - left_width)]
        )

        header = self.detailsView.header()
        header.setStretchLastSection(False)
        header.setMinimumSectionSize(60)
        header.setDefaultSectionSize(120)

        for column in range(4):
            header.setSectionResizeMode(
                column,
                QtWidgets.QHeaderView.Interactive
            )

        initial_widths = (320, 110, 150, 180)
        for column, width in enumerate(initial_widths):
            self.detailsView.setColumnWidth(column, width)

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
        paths = self._selected_existing_paths()
        return paths[0] if paths else ""

    def _active_browser_view(self):
        focused = QtWidgets.QApplication.focusWidget()
        for view in (self.detailsView, self.itemsView, self.treeView):
            if focused is view or (focused is not None and view.isAncestorOf(focused)):
                return view
        if self.contentStack.currentWidget() is self.detailsPage:
            return self.detailsView
        return self.itemsView

    def _path_for_index(self, view, index):
        if not index.isValid():
            return ""

        if view is self.treeView:
            source_index = self.proxy_model.mapToSource(index)
            return self.folder_model.filePath(source_index)

        return self.content_model.filePath(index)

    def _selected_existing_paths(self, view=None):
        view = view or self._active_browser_view()
        selection_model = view.selectionModel()
        indexes = selection_model.selectedRows(0) if selection_model else []

        if not indexes and view.currentIndex().isValid():
            indexes = [view.currentIndex()]

        paths = []
        for index in indexes:
            path = self._path_for_index(view, index)
            if path and os.path.exists(path) and path not in paths:
                paths.append(path)
        return paths

    def _selected_existing_path(self):
        paths = self._selected_existing_paths()
        return paths[0] if paths else ""

    def _operation_selected_paths(self):
        paths = self._selected_existing_paths()
        primary_path = self._selected_existing_path()
        if primary_path and primary_path not in paths:
            paths.insert(0, primary_path)
        return paths

    def _update_relative_path(self, view=None, path=""):
        selected_path = path
        if not selected_path and view is not None:
            selected_paths = self._selected_existing_paths(view)
            selected_path = selected_paths[0] if selected_paths else ""

        root_directory = os.path.abspath(self._resolve_root_directory())
        if selected_path:
            selected_path = os.path.abspath(selected_path)
            try:
                if os.path.commonpath((selected_path, root_directory)) == root_directory:
                    selected_path = os.path.relpath(selected_path, root_directory)
            except ValueError:
                selected_path = ""

        self.relativePathLineEdit.setText(selected_path)

    def _show_directory(self, directory):
        if not directory or not os.path.isdir(directory):
            return

        directory = os.path.abspath(directory)
        self.current_directory_path = directory
        root_index = self.content_model.index(directory)
        self.detailsView.setRootIndex(root_index)
        self.itemsView.setRootIndex(root_index)
        self.statusbar.showMessage(directory)
        self._update_relative_path(path=directory)

    def _on_folder_selection_changed(self, *_args):
        index = self.treeView.currentIndex()
        path = self._path_for_index(self.treeView, index)
        if os.path.isdir(path):
            self._show_directory(path)

    def _set_content_view_mode(self, mode):
        if mode == "details":
            self.contentStack.setCurrentWidget(self.detailsPage)
            self.actionDetails.setChecked(True)
            return

        self.contentStack.setCurrentWidget(self.itemsPage)
        if mode == "icons":
            self.itemsView.setViewMode(QtWidgets.QListView.IconMode)
            self.itemsView.setIconSize(QtCore.QSize(48, 48))
            self.itemsView.setGridSize(QtCore.QSize(112, 84))
            self.actionIcons.setChecked(True)
        else:
            self.itemsView.setViewMode(QtWidgets.QListView.ListMode)
            self.itemsView.setIconSize(QtCore.QSize(20, 20))
            self.itemsView.setGridSize(QtCore.QSize())
            self.actionSimple_List.setChecked(True)

    def _select_folder_in_tree(self, directory):
        source_index = self.folder_model.index(directory)
        if not source_index.isValid():
            return
        proxy_index = self.proxy_model.mapFromSource(source_index)
        if proxy_index.isValid():
            self.treeView.setCurrentIndex(proxy_index)
            self.treeView.scrollTo(proxy_index)

    def _on_content_double_clicked(self, index):
        view = self.sender()
        path = self._path_for_index(view, index)
        if os.path.isdir(path):
            self._show_directory(path)
            self._select_folder_in_tree(path)
        elif path:
            if self.select_mode and self.allow_file_selection:
                self.select_current_selection("file")
            else:
                self._open_path(path)

    def _current_directory(self):
        view = self._active_browser_view()
        if view is self.treeView:
            path = self._current_path()
            if os.path.isdir(path):
                return path
        return getattr(self, "current_directory_path", "")

    def _is_root_path(self, path):
        if not path:
            return False

        return os.path.abspath(path) == os.path.abspath(
            self._resolve_root_directory()
        )

    def _update_edit_action_state(self, *_args):
        selected_paths = self._selected_existing_paths()
        current_directory = self._current_directory()
        editable_selection = bool(selected_paths) and all(
            not self._is_root_path(path) for path in selected_paths
        )
        clipboard_sources = self._clipboard_sources()

        self.actionNew_folder.setEnabled(
            bool(current_directory and os.path.isdir(current_directory))
        )
        self.actionCut.setEnabled(editable_selection)
        self.actionCopy.setEnabled(bool(selected_paths))
        self.actionOpen.setEnabled(bool(selected_paths))
        self.actionPaste.setEnabled(
            bool(
                current_directory
                and os.path.isdir(current_directory)
                and clipboard_sources
                and all(os.path.exists(path) for path in clipboard_sources)
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

    def _clipboard_sources(self):
        if not self._file_clipboard:
            return []
        if "sources" in self._file_clipboard:
            return list(self._file_clipboard["sources"])
        source = self._file_clipboard.get("source", "")
        return [source] if source else []

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
        source_paths = [
            path for path in self._operation_selected_paths()
            if not self._is_root_path(path)
        ]
        if not source_paths:
            return

        self._file_clipboard = {
            "mode": "cut",
            "sources": source_paths,
        }
        self.statusbar.showMessage(f"Cut {len(source_paths)} item(s).", 5000)
        self._update_edit_action_state()

    def copy_selected(self):
        source_paths = self._operation_selected_paths()
        if not source_paths:
            return

        self._file_clipboard = {
            "mode": "copy",
            "sources": source_paths,
        }
        self.statusbar.showMessage(f"Copied {len(source_paths)} item(s).", 5000)
        self._update_edit_action_state()

    def paste_into_current_directory(self):
        if not self._file_clipboard:
            return

        source_paths = self._clipboard_sources()
        destination_directory = self._current_directory()

        if not source_paths or not destination_directory:
            self._update_edit_action_state()
            return

        operations = []
        try:
            for source_path in source_paths:
                if not os.path.exists(source_path):
                    continue
                self._ensure_move_is_safe(source_path, destination_directory)
                destination_path = ExplorerTreeView._unique_destination_path(
                    destination_directory,
                    os.path.basename(source_path),
                )

                if self._file_clipboard["mode"] == "cut":
                    shutil.move(source_path, destination_path)
                    operations.append({
                        "kind": "move",
                        "source": source_path,
                        "destination": destination_path,
                    })
                else:
                    self._copy_path(source_path, destination_path)
                    operations.append({
                        "kind": "create",
                        "path": destination_path,
                        "stash": self._undo_stash_path(destination_path),
                    })
        except (OSError, ValueError) as exc:
            self._show_file_operation_error("Paste", exc)
            return

        if self._file_clipboard["mode"] == "cut":
            self._file_clipboard = None
        if operations:
            self._record_file_operation({"kind": "batch", "operations": operations})
            self.statusbar.showMessage(
                f"Pasted {len(operations)} item(s) to: {destination_directory}", 5000
            )

    def delete_selected(self):
        source_paths = [
            path for path in self._operation_selected_paths()
            if not self._is_root_path(path)
        ]
        if not source_paths:
            return

        answer = QtWidgets.QMessageBox.question(
            self,
            "Delete",
            f"Delete {len(source_paths)} selected item(s)? Undo remains available during this MyExplorer session.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )

        if answer != QtWidgets.QMessageBox.Yes:
            return

        operations = []
        try:
            for source_path in source_paths:
                stash_path = self._undo_stash_path(source_path)
                shutil.move(source_path, stash_path)
                operations.append({
                    "kind": "delete",
                    "path": source_path,
                    "stash": stash_path,
                })
        except OSError as exc:
            self._show_file_operation_error("Delete", exc)
            return

        self._record_file_operation({"kind": "batch", "operations": operations})
        self.statusbar.showMessage(f"Deleted {len(operations)} item(s).", 5000)

    def move_selected(self):
        source_paths = [
            path for path in self._operation_selected_paths()
            if not self._is_root_path(path)
        ]
        if not source_paths:
            return

        destination_directory = run_myexplorer_selection(
            "Move To Folder",
            self._current_directory(),
            "folder",
        )

        if not destination_directory:
            return

        operations = []
        try:
            for source_path in source_paths:
                self._ensure_move_is_safe(source_path, destination_directory)
                destination_path = ExplorerTreeView._unique_destination_path(
                    destination_directory,
                    os.path.basename(source_path),
                )
                shutil.move(source_path, destination_path)
                operations.append({
                    "kind": "move",
                    "source": source_path,
                    "destination": destination_path,
                })
        except (OSError, ValueError) as exc:
            self._show_file_operation_error("Move", exc)
            return

        self._record_file_operation({"kind": "batch", "operations": operations})
        self.statusbar.showMessage(
            f"Moved {len(operations)} item(s) to: {destination_directory}", 5000
        )

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

        if kind == "batch":
            items = operation["operations"]
            for item in reversed(items) if undo else items:
                self._apply_history_operation(item, undo)
            return

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
        path = self._path_for_index(self.treeView, _index)
        if os.path.isdir(path):
            self._show_directory(path)
        if self.select_mode and self.allow_folder_selection:
            self.select_current_selection(
                "folder"
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

    def context_menu(self, position, view=None):
        view = view or self.treeView
        clicked_index = view.indexAt(position)

        if clicked_index.isValid():
            view.setCurrentIndex(clicked_index)
            view.setFocus()

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
            view,
            is_text_widget=False
        )

        menu.exec_(
            view.viewport().mapToGlobal(position)
        )

    def open_file(self):
        for file_path in self._selected_existing_paths():
            if os.path.isdir(file_path):
                self._show_directory(file_path)
                self._select_folder_in_tree(file_path)
            else:
                self._open_path(file_path)

    def _open_path(self, file_path):

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