import os
import re
import subprocess
import sys
from typing import Callable, Optional

from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5 import QtWidgets as qtw


MODULE_PAGE_WORKFLOW_MILESTONES = {
    "MyServer": [
        "Review active project status",
        "Validate project workflow readiness",
        "Hand off module launch for next page stage",
    ],
    "MyExplorer": [
        "Confirm project folder target",
        "Review page asset locations",
        "Open file target in operating system",
    ],
    "MyScanner": [
        "Acquire or import source page image",
        "Validate image orientation/quality",
        "Export page image into project structure",
    ],
    "MyPixler": [
        "Open current page image",
        "Apply cleanup adjustments",
        "Save updated page image",
    ],
    "MyBoxer": [
        "Open page segmentation workspace",
        "Run page/line box adjustments",
        "Save box geometry updates",
    ],
    "MyGlypher": [
        "Load page line image",
        "Extract glyph set",
        "Save glyph updates",
    ],
    "MyReader": [
        "Load page image and OCR text",
        "Review OCR output",
        "Save text corrections",
    ],
    "MyGrounder": [
        "Load page reference assets",
        "Validate ground-truth alignment",
        "Save ground-truth updates",
    ],
    "MyTrainer": [
        "Validate training inputs",
        "Run training step for current page set",
        "Review training log/output",
    ],
    "MyLexer": [
        "Load page text artifact",
        "Run lexical processing",
        "Save lexical updates",
    ],
    "MyResolver": [
        "Load unresolved variants",
        "Apply resolution decisions",
        "Save resolved variant updates",
    ],
    "MyVersifier": [
        "Load verse comparison view",
        "Apply verse alignment updates",
        "Save verse corrections",
    ],
    "MyWriter": [
        "Load publication-ready text",
        "Run final page validation",
        "Export page output",
    ],
}


DEFAULT_MENU_SHORTCUTS = {
    "undo": qtg.QKeySequence.Undo,
    "redo": qtg.QKeySequence.Redo,
    "cut": qtg.QKeySequence.Cut,
    "copy": qtg.QKeySequence.Copy,
    "paste": qtg.QKeySequence.Paste,
    "help": qtg.QKeySequence.HelpContents,
}


SAVE_ACTION_SHORTCUTS = {
    "actionsave_image": qtg.QKeySequence("Ctrl+S"),
    "actionsave_as_image": qtg.QKeySequence("Ctrl+Shift+S"),
    "actionsave_text": qtg.QKeySequence("Ctrl+Alt+S"),
    "actionsave_as_text": qtg.QKeySequence("Ctrl+Alt+Shift+S"),
    "actionsave_line_image": qtg.QKeySequence("Ctrl+S"),
    "actionsave_as_line_image": qtg.QKeySequence("Ctrl+Shift+S"),
    "actionsave_line_text": qtg.QKeySequence("Ctrl+Alt+S"),
    "actionsave_as_line_text": qtg.QKeySequence("Ctrl+Alt+Shift+S"),
}


SAVE_METHOD_NAME = re.compile(r"^(save($|[A-Z_])|Save)")
SAVE_METHOD_EXCLUSIONS = {
    "save_session_settings",
}

_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".gif", ".webp"}
_TEXT_EXTENSIONS = {".txt", ".nt", ".md", ".json", ".csv", ".tsv", ".xml", ".html", ".htm", ".ris"}

_IMAGE_HANDLER_CANDIDATES = (
    "showImage",
    "getImage",
    "loadDropImageEvent",
    "loadImagePath",
    "loadImageFromPath",
)

_TEXT_HANDLER_CANDIDATES = (
    "showText",
    "getText",
    "getRefText",
    "getVerseText",
    "loadDropTextEvent",
    "loadTextPath",
    "loadTextFromPath",
)

_MYEXPLORER_ALIAS_CANDIDATES = {
    "open_image_with_myexplorer": ("loadImage", "loadRefImg", "getImage"),
    "open_text_with_myexplorer": ("loadText", "getText"),
    "save_image_with_myexplorer": ("SaveImage", "saveWordBoxImage", "SaveImgFileDialog"),
    "save_image_as_with_myexplorer": ("SaveImageAs", "SaveImgFileDialog", "saveWordBoxImage"),
    "save_text_with_myexplorer": ("SaveCorrectedTextFileDialog", "SaveVerseTextDialog", "SavePageTextDialog", "save"),
    "save_text_as_with_myexplorer": ("SaveAsCorrectedTextFileDialog", "SaveAsVerseTextDialog", "SaveAsPageTextDialog", "saveastextDialog"),
}

_MYEXPLORER_ICON_TARGET_PATTERNS = (
    "openimage",
    "opentext",
    "saveimage",
    "savetext",
    "open_line_image",
    "open_line_text",
    "save_line_image",
    "save_line_text",
    "open_word_box",
    "save_word_box",
    "openreffimg",
)


_ORIGINAL_GET_OPEN_FILE_NAME = qtw.QFileDialog.getOpenFileName
_ORIGINAL_GET_SAVE_FILE_NAME = qtw.QFileDialog.getSaveFileName
_ORIGINAL_GET_EXISTING_DIRECTORY = qtw.QFileDialog.getExistingDirectory


def _project_root_from_core() -> str:
    core_dir = os.path.abspath(os.path.dirname(__file__))
    return os.path.abspath(os.path.join(core_dir, ".."))


def _coerce_start_directory(path_hint: str) -> str:
    if not path_hint:
        return _project_root_from_core()
    candidate = os.path.abspath(path_hint)
    if os.path.isfile(candidate):
        candidate = os.path.dirname(candidate)
    if os.path.isdir(candidate):
        return candidate
    parent = os.path.dirname(candidate)
    if os.path.isdir(parent):
        return parent
    return _project_root_from_core()


class _ExplorerPickerDialog(qtw.QDialog):
    def __init__(self, parent, caption: str, start_dir: str, mode: str, suggested_name: str = ""):
        super().__init__(parent)
        self._mode = mode
        self._selected_path = ""
        self.setWindowTitle(caption or "Select Path")
        self.resize(860, 560)

        root = _project_root_from_core()
        initial_dir = _coerce_start_directory(start_dir)

        layout = qtw.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self._model = qtw.QFileSystemModel(self)
        self._model.setRootPath(root)
        self._model.setReadOnly(False)

        self._tree = qtw.QTreeView(self)
        self._tree.setModel(self._model)
        self._tree.setRootIndex(self._model.index(root))
        self._tree.setSortingEnabled(True)
        self._tree.sortByColumn(0, qtc.Qt.AscendingOrder)
        self._tree.setSelectionMode(qtw.QAbstractItemView.SingleSelection)
        self._tree.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self._tree, 1)

        form = qtw.QHBoxLayout()
        form.addWidget(qtw.QLabel("Selected:"))
        self._path_display = qtw.QLineEdit(self)
        self._path_display.setReadOnly(True)
        form.addWidget(self._path_display, 1)
        layout.addLayout(form)

        self._name_edit = qtw.QLineEdit(self)
        if mode == "save_file":
            self._name_edit.setPlaceholderText("File name")
            if suggested_name:
                self._name_edit.setText(suggested_name)
            layout.addWidget(self._name_edit)

        button_row = qtw.QHBoxLayout()
        button_row.addStretch(1)
        self._select_button = qtw.QPushButton("Select", self)
        self._cancel_button = qtw.QPushButton("Cancel", self)
        button_row.addWidget(self._select_button)
        button_row.addWidget(self._cancel_button)
        layout.addLayout(button_row)

        self._select_button.clicked.connect(self._accept_selection)
        self._cancel_button.clicked.connect(self.reject)
        self._tree.selectionModel().currentChanged.connect(self._on_selection_changed)

        initial_index = self._model.index(initial_dir)
        if initial_index.isValid():
            self._tree.setCurrentIndex(initial_index)
            self._tree.scrollTo(initial_index, qtw.QAbstractItemView.PositionAtCenter)
        self._on_selection_changed(self._tree.currentIndex(), qtc.QModelIndex())

    def selected_path(self) -> str:
        return self._selected_path

    def _on_selection_changed(self, current, _previous) -> None:
        if not current.isValid():
            self._path_display.clear()
            return
        self._path_display.setText(self._model.filePath(current))

    def _on_double_click(self, index) -> None:
        if self._mode != "open_file":
            return
        if not index.isValid():
            return
        path = self._model.filePath(index)
        if os.path.isfile(path):
            self._selected_path = path
            self.accept()

    def _accept_selection(self) -> None:
        index = self._tree.currentIndex()
        if not index.isValid():
            qtw.QMessageBox.information(self, "Select Path", "Please select a location.")
            return

        selected = self._model.filePath(index)
        if self._mode == "directory":
            if os.path.isfile(selected):
                selected = os.path.dirname(selected)
            if not os.path.isdir(selected):
                qtw.QMessageBox.information(self, "Select Folder", "Please select a folder.")
                return
            self._selected_path = selected
            self.accept()
            return

        if self._mode == "open_file":
            if not os.path.isfile(selected):
                qtw.QMessageBox.information(self, "Open File", "Please select a file.")
                return
            self._selected_path = selected
            self.accept()
            return

        if self._mode == "save_file":
            filename = self._name_edit.text().strip() if hasattr(self, "_name_edit") else ""
            if not filename and os.path.isfile(selected):
                filename = os.path.basename(selected)
                selected = os.path.dirname(selected)
            if not filename:
                qtw.QMessageBox.information(self, "Save File", "Please enter a file name.")
                return
            if os.path.isfile(selected):
                selected = os.path.dirname(selected)
            if not os.path.isdir(selected):
                qtw.QMessageBox.information(self, "Save File", "Please select a valid destination folder.")
                return
            self._selected_path = os.path.join(selected, filename)
            self.accept()


def _explorer_get_open_file_name(parent=None, caption="", directory="", _filter="", *args, **kwargs):
    dialog = _ExplorerPickerDialog(parent, caption or "Open File", directory, "open_file")
    if dialog.exec_() == qtw.QDialog.Accepted:
        return dialog.selected_path(), ""
    return "", ""


def _explorer_get_save_file_name(parent=None, caption="", directory="", _filter="", *args, **kwargs):
    suggested_name = ""
    if directory:
        suggested_name = os.path.basename(directory) if os.path.basename(directory) else ""
    dialog = _ExplorerPickerDialog(parent, caption or "Save File", directory, "save_file", suggested_name)
    if dialog.exec_() == qtw.QDialog.Accepted:
        return dialog.selected_path(), ""
    return "", ""


def _explorer_get_existing_directory(parent=None, caption="", directory="", *args, **kwargs):
    dialog = _ExplorerPickerDialog(parent, caption or "Select Folder", directory, "directory")
    if dialog.exec_() == qtw.QDialog.Accepted:
        return dialog.selected_path()
    return ""


def _install_explorer_backed_file_dialogs(window) -> None:
    if window is None:
        return
    if getattr(window, "_workflow_explorer_file_dialogs_installed", False):
        return

    qtw.QFileDialog.getOpenFileName = staticmethod(_explorer_get_open_file_name)
    qtw.QFileDialog.getSaveFileName = staticmethod(_explorer_get_save_file_name)
    qtw.QFileDialog.getExistingDirectory = staticmethod(_explorer_get_existing_directory)
    setattr(window, "_workflow_explorer_file_dialogs_installed", True)


def install_explorer_file_dialogs(window) -> None:
    _install_explorer_backed_file_dialogs(window)


class _DefaultContextMenuEventFilter(qtc.QObject):
    """Attach consistent default context menus across module panels."""

    def eventFilter(self, obj, event):
        if event.type() != qtc.QEvent.ContextMenu:
            return False
        if not isinstance(obj, qtw.QWidget):
            return False
        if obj.contextMenuPolicy() == qtc.Qt.ContextMenuPolicy.CustomContextMenu:
            return False

        menu = self._build_context_menu(obj)
        if menu is None:
            return False

        menu.exec_(event.globalPos())
        return True

    def _build_context_menu(self, widget: qtw.QWidget) -> Optional[qtw.QMenu]:
        menu = None
        is_text_widget = isinstance(widget, (qtw.QLineEdit, qtw.QTextEdit, qtw.QPlainTextEdit, qtw.QTextBrowser))

        if is_text_widget and hasattr(widget, "createStandardContextMenu"):
            menu = widget.createStandardContextMenu()
        else:
            menu = qtw.QMenu(widget)

        if menu is None:
            return None

        append_default_context_actions(menu, widget, is_text_widget=is_text_widget)
        return menu


class _CloseConfirmationEventFilter(qtc.QObject):
    def __init__(self, window):
        super().__init__(window)
        self._window = window

    def eventFilter(self, obj, event):
        if obj is not self._window:
            return False
        if event.type() != qtc.QEvent.Close:
            return False
        if not _confirm_close_operation(self._window, event):
            event.ignore()
            return True
        return False


class _PanelFileDropEventFilter(qtc.QObject):
    def __init__(self, window, target_widgets):
        super().__init__(window)
        self._window = window
        self._targets = set(target_widgets)

    def eventFilter(self, watched, event):
        if watched not in self._targets:
            return False
        if event.type() in (qtc.QEvent.DragEnter, qtc.QEvent.DragMove):
            if _mime_has_local_urls(event.mimeData()):
                event.acceptProposedAction()
                return True
        if event.type() == qtc.QEvent.Drop:
            file_path = _first_local_drop_path(event.mimeData())
            if not file_path:
                return False
            if _dispatch_panel_drop_file(self._window, file_path):
                event.acceptProposedAction()
                return True
        return False


def append_default_context_actions(
    menu: qtw.QMenu,
    widget: qtw.QWidget,
    *,
    is_text_widget: Optional[bool] = None,
    include_undo_redo: bool = False,
    undo_callback: Optional[Callable[[], None]] = None,
    redo_callback: Optional[Callable[[], None]] = None,
) -> None:
    if is_text_widget is None:
        is_text_widget = isinstance(widget, (qtw.QLineEdit, qtw.QTextEdit, qtw.QPlainTextEdit, qtw.QTextBrowser))

    action_map = {}
    for action in menu.actions():
        key = _canonical_action_name(action.text())
        if key:
            action_map[key] = action

    has_help_text = bool((widget.toolTip() or "").strip() or (widget.whatsThis() or "").strip())

    ordered_keys = []
    if has_help_text:
        ordered_keys.append("help")
    if is_text_widget or include_undo_redo:
        ordered_keys.extend(["undo", "redo"])
    if is_text_widget:
        ordered_keys.extend(["cut", "copy", "paste"])

    for key in ordered_keys:
        action = action_map.get(key)
        if action is None:
            if key != "help":
                method_name = {
                    "undo": "undo",
                    "redo": "redo",
                    "cut": "cut",
                    "copy": "copy",
                    "paste": "paste",
                }.get(key)
                callback = None
                if key == "undo" and undo_callback is not None:
                    callback = undo_callback
                elif key == "redo" and redo_callback is not None:
                    callback = redo_callback

                if callback is None and method_name and not callable(getattr(widget, method_name, None)):
                    continue

            action = qtw.QAction(key.title(), menu)
            if key == "undo":
                if undo_callback is not None:
                    action.triggered.connect(lambda _checked=False, cb=undo_callback: cb())
                else:
                    action.triggered.connect(lambda _checked=False, w=widget: _invoke_widget_method(w, "undo"))
            elif key == "redo":
                if redo_callback is not None:
                    action.triggered.connect(lambda _checked=False, cb=redo_callback: cb())
                else:
                    action.triggered.connect(lambda _checked=False, w=widget: _invoke_widget_method(w, "redo"))
            elif key == "cut":
                action.triggered.connect(lambda _checked=False, w=widget: _invoke_widget_method(w, "cut"))
            elif key == "copy":
                action.triggered.connect(lambda _checked=False, w=widget: _invoke_widget_method(w, "copy"))
            elif key == "paste":
                action.triggered.connect(lambda _checked=False, w=widget: _invoke_widget_method(w, "paste"))
            elif key == "help":
                action.triggered.connect(lambda _checked=False, w=widget: _show_widget_help(w))
            menu.addAction(action)

        if action.shortcut().isEmpty():
            action.setShortcut(DEFAULT_MENU_SHORTCUTS[key])


def _canonical_action_name(raw_text: str) -> str:
    text = (raw_text or "").replace("&", "").strip().lower()
    if text in {"undo", "redo", "cut", "copy", "paste", "help"}:
        return text
    return ""


def _invoke_widget_method(widget: qtw.QWidget, method_name: str) -> None:
    method = getattr(widget, method_name, None)
    if callable(method):
        method()


def _show_widget_help(widget: qtw.QWidget) -> None:
    help_text = widget.toolTip() or widget.whatsThis() or "No panel-specific help text is available."
    qtw.QMessageBox.information(widget, "Help", help_text)


def _install_default_context_menu_behavior(window) -> None:
    if window is None:
        return

    if getattr(window, "_default_context_menu_filter", None) is None:
        filter_obj = _DefaultContextMenuEventFilter(window)
        setattr(window, "_default_context_menu_filter", filter_obj)
    else:
        filter_obj = getattr(window, "_default_context_menu_filter")

    window.installEventFilter(filter_obj)
    for child in window.findChildren(qtw.QWidget):
        child.installEventFilter(filter_obj)


def _ensure_module_menu_shortcuts(window) -> None:
    if window is None:
        return

    for action in window.findChildren(qtw.QAction):
        canonical = _canonical_action_name(action.text())
        if not canonical:
            object_name = (action.objectName() or "").replace("-", "_").lower()
            object_name = object_name.replace("__", "_")
            object_name = object_name.replace("_as_", "_as_")
            object_name = object_name.replace("_as", "_as")
            object_name = object_name.replace("save_as", "save_as")
            object_name = object_name.replace("saveas", "save_as")
            shortcut = SAVE_ACTION_SHORTCUTS.get(object_name)
            if shortcut is not None and action.shortcut().isEmpty():
                action.setShortcut(shortcut)
            continue
        if action.shortcut().isEmpty():
            action.setShortcut(DEFAULT_MENU_SHORTCUTS[canonical])


def _confirm_save_operation(window, label: str) -> bool:
    title = "Confirm Save"
    prompt = f"Are you sure you want to {label}?"
    answer = qtw.QMessageBox.question(
        window,
        title,
        prompt,
        qtw.QMessageBox.Yes | qtw.QMessageBox.No,
        qtw.QMessageBox.No,
    )
    return answer == qtw.QMessageBox.Yes


def _install_save_confirmation_wrappers(window) -> None:
    if window is None:
        return
    if getattr(window, "_workflow_save_confirmation_installed", False):
        return

    wrapped_names = set()
    for name in dir(window):
        if name in SAVE_METHOD_EXCLUSIONS:
            continue
        if not SAVE_METHOD_NAME.match(name):
            continue
        lowered = name.lower()
        if "setting" in lowered or "session" in lowered:
            continue

        candidate = getattr(window, name, None)
        if not callable(candidate):
            continue
        if getattr(candidate, "_workflow_save_wrapper", False):
            continue

        def _make_wrapper(method_name: str, method_callable):
            def _wrapped(*args, **kwargs):
                label = method_name.replace("_", " ")
                if not _confirm_save_operation(window, label):
                    return None
                return method_callable(*args, **kwargs)

            _wrapped._workflow_save_wrapper = True  # type: ignore[attr-defined]
            return _wrapped

        setattr(window, name, _make_wrapper(name, candidate))
        wrapped_names.add(name)

    setattr(window, "_workflow_wrapped_save_methods", wrapped_names)
    setattr(window, "_workflow_save_confirmation_installed", True)


def _confirm_close_operation(window, event) -> bool:
    if hasattr(window, "changesSaved") and getattr(window, "changesSaved") is False and callable(getattr(window, "save", None)):
        popup = qtw.QMessageBox(window)
        popup.setIcon(qtw.QMessageBox.Warning)
        popup.setText("The document has been modified")
        popup.setInformativeText("Do you want to save your changes?")
        popup.setStandardButtons(
            qtw.QMessageBox.Save |
            qtw.QMessageBox.Cancel |
            qtw.QMessageBox.Discard
        )
        popup.setDefaultButton(qtw.QMessageBox.Save)
        answer = popup.exec_()
        if answer == qtw.QMessageBox.Save:
            if _confirm_save_operation(window, "save your changes"):
                window.save()
                return True
            return False
        if answer == qtw.QMessageBox.Discard:
            return True
        return False

    answer = qtw.QMessageBox.question(
        window,
        "Confirm Close",
        "Are you sure you want to close this module?",
        qtw.QMessageBox.Yes | qtw.QMessageBox.No,
        qtw.QMessageBox.No,
    )
    return answer == qtw.QMessageBox.Yes


def _install_close_confirmation(window) -> None:
    if window is None:
        return
    if getattr(window, "_workflow_close_confirmation_filter", None) is not None:
        return

    filter_obj = _CloseConfirmationEventFilter(window)
    setattr(window, "_workflow_close_confirmation_filter", filter_obj)
    window.installEventFilter(filter_obj)


def _mime_has_local_urls(mime_data) -> bool:
    if not mime_data.hasUrls():
        return False
    return any(url.isLocalFile() for url in mime_data.urls())


def _first_local_drop_path(mime_data) -> str:
    for url in mime_data.urls():
        if url.isLocalFile():
            return url.toLocalFile()
    return ""


def _is_image_file(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in _IMAGE_EXTENSIONS


def _is_text_file(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in _TEXT_EXTENSIONS


def _invoke_handler_with_path(window, handler_name: str, file_path: str) -> bool:
    handler = getattr(window, handler_name, None)
    if not callable(handler):
        return False
    try:
        handler(file_path)
        return True
    except TypeError:
        # Keep compatibility with methods that only support no-arg mode.
        return False


def _dispatch_panel_drop_file(window, file_path: str) -> bool:
    if _is_image_file(file_path):
        for handler_name in _IMAGE_HANDLER_CANDIDATES:
            if _invoke_handler_with_path(window, handler_name, file_path):
                return True
    if _is_text_file(file_path):
        for handler_name in _TEXT_HANDLER_CANDIDATES:
            if _invoke_handler_with_path(window, handler_name, file_path):
                return True
    return False


def _iter_candidate_drop_widgets(window):
    ui = getattr(window, "ui", None)
    if ui is None:
        return

    for attr_name in dir(ui):
        widget = getattr(ui, attr_name, None)
        if not isinstance(widget, qtw.QWidget):
            continue
        if isinstance(widget, (qtw.QPushButton, qtw.QToolButton, qtw.QComboBox, qtw.QSpinBox, qtw.QSlider, qtw.QCheckBox, qtw.QRadioButton, qtw.QProgressBar, qtw.QMenuBar, qtw.QToolBar, qtw.QStatusBar, qtw.QTableWidget, qtw.QTreeView, qtw.QListView)):
            continue
        lowered_name = attr_name.lower()
        if "image" in lowered_name or "text" in lowered_name or "ocr" in lowered_name or "verse" in lowered_name or "ref" in lowered_name:
            yield widget


def _install_panel_file_drop_behavior(window) -> None:
    if window is None:
        return
    if getattr(window, "_workflow_panel_drop_filter", None) is not None:
        return

    targets = []
    for widget in _iter_candidate_drop_widgets(window):
        widget.setAcceptDrops(True)
        if hasattr(widget, "viewport") and callable(getattr(widget, "viewport", None)):
            viewport = widget.viewport()
            if viewport is not None:
                viewport.setAcceptDrops(True)
                targets.append(viewport)
        targets.append(widget)

    if not targets:
        return

    filter_obj = _PanelFileDropEventFilter(window, targets)
    setattr(window, "_workflow_panel_drop_filter", filter_obj)
    for target in targets:
        target.installEventFilter(filter_obj)


def install_panel_file_drops(window) -> None:
    _install_panel_file_drop_behavior(window)


def _install_myexplorer_method_aliases(window) -> None:
    if window is None:
        return
    if getattr(window, "_workflow_myexplorer_aliases_installed", False):
        return

    for alias_name, candidates in _MYEXPLORER_ALIAS_CANDIDATES.items():
        if callable(getattr(window, alias_name, None)):
            continue
        for candidate_name in candidates:
            target = getattr(window, candidate_name, None)
            if not callable(target):
                continue

            def _make_alias(method):
                return lambda *args, **kwargs: method(*args, **kwargs)

            setattr(window, alias_name, _make_alias(target))
            break

    setattr(window, "_workflow_myexplorer_aliases_installed", True)


def install_myexplorer_method_aliases(window) -> None:
    _install_myexplorer_method_aliases(window)


def _resolve_myexplorer_icon(window):
    ui = getattr(window, "ui", None)
    candidates = []
    if ui is not None:
        candidates.extend([
            getattr(ui, "MyExplorerbutton", None),
            getattr(ui, "actionProject_Browser", None),
            getattr(ui, "actionExplorer", None),
            getattr(ui, "actionMy_Explorer", None),
            getattr(ui, "actionProject_Explorer", None),
        ])
    candidates.extend([
        getattr(window, "actionProject_Browser", None),
        getattr(window, "actionExplorer", None),
        getattr(window, "actionMy_Explorer", None),
        getattr(window, "actionProject_Explorer", None),
    ])

    for candidate in candidates:
        if candidate is None:
            continue
        icon = candidate.icon() if hasattr(candidate, "icon") else qtg.QIcon()
        if icon is not None and not icon.isNull():
            return icon
    return qtg.QIcon()


def _install_myexplorer_icon_lockstep(window) -> None:
    if window is None:
        return
    if getattr(window, "_workflow_myexplorer_icon_lockstep_installed", False):
        return

    icon = _resolve_myexplorer_icon(window)
    if icon.isNull():
        return

    ui = getattr(window, "ui", None)
    owners = [window]
    if ui is not None:
        owners.append(ui)

    for owner in owners:
        for attr_name in dir(owner):
            lowered = attr_name.lower()
            if not any(token in lowered for token in _MYEXPLORER_ICON_TARGET_PATTERNS):
                continue
            target = getattr(owner, attr_name, None)
            if target is None or not hasattr(target, "setIcon"):
                continue
            try:
                target.setIcon(icon)
            except Exception:
                pass

    setattr(window, "_workflow_myexplorer_icon_lockstep_installed", True)


def install_myexplorer_icon_lockstep(window) -> None:
    _install_myexplorer_icon_lockstep(window)


class ModulePageWorkflowWizardDialog(qtw.QDialog):
    """Module-local stacked page workflow wizard with run controls."""

    def __init__(
        self,
        title: str,
        intro_text: str,
        stage_plan,
        run_stage_callback,
        run_all_callback,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(860, 520)
        self.setSizeGripEnabled(True)
        self.stage_plan = stage_plan
        self.run_stage_callback = run_stage_callback
        self.run_all_callback = run_all_callback
        self._build_ui(intro_text)
        self._populate_stage_pages()

    def _make_scroll_page(self, content_widget: qtw.QWidget) -> qtw.QScrollArea:
        scroll = qtw.QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(qtw.QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(qtc.Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(qtc.Qt.ScrollBarAsNeeded)
        scroll.setWidget(content_widget)
        return scroll

    def _build_ui(self, intro_text: str) -> None:
        root_layout = qtw.QVBoxLayout(self)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(8)

        intro_label = qtw.QLabel(intro_text)
        intro_label.setWordWrap(True)
        root_layout.addWidget(intro_label)

        body_layout = qtw.QHBoxLayout()
        body_layout.setSpacing(8)
        root_layout.addLayout(body_layout, 1)

        self.stage_nav = qtw.QListWidget(self)
        self.stage_nav.setMinimumWidth(220)
        body_layout.addWidget(self.stage_nav)

        self.stage_stack = qtw.QStackedWidget(self)
        body_layout.addWidget(self.stage_stack, 1)

        self.stage_nav.currentRowChanged.connect(self.stage_stack.setCurrentIndex)

        footer_layout = qtw.QHBoxLayout()
        footer_layout.addStretch(1)

        self.run_all_button = qtw.QPushButton("Run Full Wizard")
        self.run_all_button.clicked.connect(self._run_all)
        footer_layout.addWidget(self.run_all_button)

        close_button = qtw.QPushButton("Close")
        close_button.clicked.connect(self.accept)
        footer_layout.addWidget(close_button)

        root_layout.addLayout(footer_layout)

    def _populate_stage_pages(self) -> None:
        for stage in self.stage_plan:
            stage_title = stage.get("title", "Stage")
            description = stage.get("description", "")
            steps = stage.get("steps", [])

            self.stage_nav.addItem(stage_title)

            page = qtw.QWidget(self)
            layout = qtw.QVBoxLayout(page)
            layout.setContentsMargins(8, 8, 8, 8)
            layout.setSpacing(8)

            title_label = qtw.QLabel(stage_title)
            title_font = title_label.font()
            title_font.setBold(True)
            title_label.setFont(title_font)
            layout.addWidget(title_label)

            desc_label = qtw.QLabel(description)
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

            step_list = qtw.QListWidget(page)
            for step in steps:
                step_list.addItem(f"{step.get('module', 'Module')}: {step.get('label', '')}")
            layout.addWidget(step_list, 1)

            run_stage_button = qtw.QPushButton(f"Run {stage_title} Wizard")
            run_stage_button.clicked.connect(
                lambda _checked=False, stage_key=stage.get("key", ""): self._run_stage(stage_key)
            )
            layout.addWidget(run_stage_button)

            self.stage_stack.addWidget(self._make_scroll_page(page))

        if self.stage_nav.count() > 0:
            self.stage_nav.setCurrentRow(0)

    def _run_stage(self, stage_key: str) -> None:
        if not stage_key:
            return
        self.run_stage_callback(stage_key)

    def _run_all(self) -> None:
        self.run_all_callback()


def _launcher_script_path() -> str:
    core_dir = os.path.abspath(os.path.dirname(__file__))
    project_root = os.path.abspath(os.path.join(core_dir, ".."))
    return os.path.join(project_root, "ViewController", "0-MainUI", "MyLauncher.py")


def _find_menu_from_window(window) -> Optional[qtw.QMenu]:
    ui = getattr(window, "ui", None)

    # Prefer explicit Project menu, then File, then Help fallback.
    for menu_name in ("menuProject", "menuFile", "menuHelp"):
        menu = getattr(window, menu_name, None)
        if isinstance(menu, qtw.QMenu):
            return menu
        if ui is not None:
            menu = getattr(ui, menu_name, None)
            if isinstance(menu, qtw.QMenu):
                return menu

    menu_bar = window.menuBar() if hasattr(window, "menuBar") else None
    if menu_bar is None:
        return None

    for action in menu_bar.actions():
        menu = action.menu()
        if menu is None:
            continue
        title = (menu.title() or "").strip().lower()
        if title == "project":
            return menu

    for action in menu_bar.actions():
        menu = action.menu()
        if menu is None:
            continue
        title = (menu.title() or "").strip().lower()
        if title == "file":
            return menu

    return menu_bar.addMenu("Project")


def _iter_window_menus(window):
    seen = set()
    ui = getattr(window, "ui", None)

    for owner in (window, ui):
        if owner is None:
            continue
        for attr_name in dir(owner):
            if not attr_name.startswith("menu"):
                continue
            menu = getattr(owner, attr_name, None)
            if not isinstance(menu, qtw.QMenu):
                continue
            key = id(menu)
            if key in seen:
                continue
            seen.add(key)
            yield menu

    menu_bar = window.menuBar() if hasattr(window, "menuBar") else None
    if menu_bar is None:
        return

    for action in menu_bar.actions():
        menu = action.menu()
        if not isinstance(menu, qtw.QMenu):
            continue
        key = id(menu)
        if key in seen:
            continue
        seen.add(key)
        yield menu


def _detach_action_from_all_menus(window, action: qtw.QAction) -> None:
    for menu in _iter_window_menus(window):
        menu.removeAction(action)


def _attach_action_to_menu_only(window, target_menu: qtw.QMenu, action: qtw.QAction) -> None:
    _detach_action_from_all_menus(window, action)
    if action not in target_menu.actions():
        target_menu.addAction(action)


def _open_launcher_wizard(window, mode: str, requested_module: Optional[str] = None) -> None:
    launcher_path = _launcher_script_path()
    if not os.path.exists(launcher_path):
        qtw.QMessageBox.warning(
            window,
            "Workflow Wizard",
            f"MyLauncher entrypoint not found: {launcher_path}",
        )
        return

    creationflags = 0
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)

    command = [sys.executable, launcher_path, "--workflow-wizard", mode]
    if requested_module:
        command.extend(["--workflow-module", requested_module])

    subprocess.Popen(command, creationflags=creationflags)


def _open_module_page_wizard(window, module_name: str) -> None:
    # Prefer per-module page workflow implementation when provided.
    page_handler = getattr(window, "open_page_workflow_wizard", None)
    if callable(page_handler):
        try:
            page_handler(module_name)
        except TypeError:
            page_handler()
        return

    open_default_module_page_workflow_wizard(window, module_name)


def open_default_module_page_workflow_wizard(window, module_name: str) -> None:
    """Open the default module-local page workflow wizard for a module window."""

    steps = [
        {"module": module_name, "label": item}
        for item in MODULE_PAGE_WORKFLOW_MILESTONES.get(
            module_name,
            [
                "Load page context",
                "Run page-specific workflow action",
                "Save page workflow result",
            ],
        )
    ]

    stage_plan = [
        {
            "key": f"{module_name.lower()}_page_stage",
            "title": f"{module_name} Page Workflow",
            "description": (
                f"Run the {module_name} page workflow milestones for the active page context."
            ),
            "steps": steps,
        }
    ]

    def run_stage(stage_key: str) -> None:
        stage_label = stage_key or f"{module_name} page workflow"
        handler = getattr(window, "run_page_workflow_stage", None)
        if callable(handler):
            try:
                handler(stage_label)
            except TypeError:
                handler(module_name, stage_label)
            return

        status_bar = window.statusBar() if hasattr(window, "statusBar") else None
        if status_bar is not None:
            status_bar.showMessage(f"{module_name}: completed {stage_label}", 5000)
        qtw.QMessageBox.information(
            window,
            "Page Workflow Wizard",
            f"{module_name}: completed {stage_label}.",
        )

    def run_all() -> None:
        for stage in stage_plan:
            run_stage(stage.get("key", ""))

    dialog = ModulePageWorkflowWizardDialog(
        title=f"{module_name} Page Workflow Wizard",
        intro_text=(
            "Module-specific page workflow wizard. "
            "Use Run buttons to execute page milestones for this module."
        ),
        stage_plan=stage_plan,
        run_stage_callback=run_stage,
        run_all_callback=run_all,
        parent=window,
    )
    dialog.exec_()


def install_workflow_wizard_menu_actions(
    window,
    module_name: str,
    *,
    include_project_wizard: Optional[bool] = None,
    include_page_wizard: bool = True,
) -> None:
    _install_default_context_menu_behavior(window)
    _install_explorer_backed_file_dialogs(window)
    _install_myexplorer_method_aliases(window)
    _install_myexplorer_icon_lockstep(window)
    _install_panel_file_drop_behavior(window)
    _install_save_confirmation_wrappers(window)
    if module_name != "MyWriter":
        _install_close_confirmation(window)
    _ensure_module_menu_shortcuts(window)

    target_menu = _find_menu_from_window(window)
    if target_menu is None:
        return

    if include_project_wizard is None:
        include_project_wizard = module_name == "MyServer"

    project_action_name = "actionProject_Workflow_Wizard"
    page_action_name = "actionPage_Workflow_Wizard"

    existing_project_action = getattr(window, project_action_name, None)
    if existing_project_action is None:
        existing_project_action = getattr(getattr(window, "ui", None), project_action_name, None)

    existing_page_action = getattr(window, page_action_name, None)
    if existing_page_action is None:
        existing_page_action = getattr(getattr(window, "ui", None), page_action_name, None)

    if not include_project_wizard and isinstance(existing_project_action, qtw.QAction):
        _detach_action_from_all_menus(window, existing_project_action)
        existing_project_action.setVisible(False)
        existing_project_action.setEnabled(False)
        try:
            existing_project_action.triggered.disconnect()
        except TypeError:
            pass
        if getattr(window, project_action_name, None) is not None:
            setattr(window, project_action_name, None)

    if include_project_wizard and not isinstance(existing_project_action, qtw.QAction):
        project_action = qtw.QAction("Project Workflow Wizard", window)
        project_action.setObjectName(project_action_name)
        project_action.setStatusTip(f"Open project workflow wizard from {module_name}")
        project_action.triggered.connect(
            lambda: _open_launcher_wizard(window, "project", module_name)
        )
        setattr(window, project_action_name, project_action)
        _attach_action_to_menu_only(window, target_menu, project_action)
    elif include_project_wizard and isinstance(existing_project_action, qtw.QAction):
        try:
            existing_project_action.triggered.disconnect()
        except TypeError:
            pass
        existing_project_action.triggered.connect(
            lambda: _open_launcher_wizard(window, "project", module_name)
        )
        existing_project_action.setVisible(True)
        existing_project_action.setEnabled(True)
        _attach_action_to_menu_only(window, target_menu, existing_project_action)
        setattr(window, project_action_name, existing_project_action)

    if include_page_wizard and not isinstance(existing_page_action, qtw.QAction):
        page_action = qtw.QAction("Page Workflow Wizard", window)
        page_action.setObjectName(page_action_name)
        page_action.setStatusTip(f"Open page workflow wizard from {module_name}")
        page_action.triggered.connect(
            lambda: _open_module_page_wizard(window, module_name)
        )
        setattr(window, page_action_name, page_action)
        _attach_action_to_menu_only(window, target_menu, page_action)
    elif include_page_wizard and isinstance(existing_page_action, qtw.QAction):
        try:
            existing_page_action.triggered.disconnect()
        except TypeError:
            pass
        existing_page_action.triggered.connect(
            lambda: _open_module_page_wizard(window, module_name)
        )
        existing_page_action.setVisible(True)
        existing_page_action.setEnabled(True)
        _attach_action_to_menu_only(window, target_menu, existing_page_action)
        setattr(window, page_action_name, existing_page_action)

    if not include_page_wizard and isinstance(existing_page_action, qtw.QAction):
        _detach_action_from_all_menus(window, existing_page_action)
        existing_page_action.setVisible(False)
        existing_page_action.setEnabled(False)
        try:
            existing_page_action.triggered.disconnect()
        except TypeError:
            pass
        if getattr(window, page_action_name, None) is not None:
            setattr(window, page_action_name, None)
