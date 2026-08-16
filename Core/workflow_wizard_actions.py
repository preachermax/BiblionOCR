import os
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Callable, Optional

from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5 import QtWidgets as qtw

from .myexplorer_picker import run_myexplorer_selection
from .project_tracking import ProjectWorkflowTracker


@dataclass(frozen=True)
class WorkflowStepSpec:
    label: str
    method_name: Optional[str] = None
    dialog_name: str = ""
    picker_kind: str = "file"


def apply_active_project_theme(window) -> str:
    """Apply the active project's theme so workflow dialogs inherit it."""
    session_manager = getattr(window, "session_manager", None)
    project_root = ""
    if session_manager is not None and hasattr(session_manager, "get_active_project_root"):
        project_root = session_manager.get_active_project_root()
    if not project_root:
        project_root = str(getattr(window, "current_project_root", "") or "")

    try:
        from Stylesheets import apply_theme, load_project_theme
    except ImportError:
        from helpers.Stylesheets import apply_theme, load_project_theme

    theme_id = load_project_theme(project_root)
    window_theme_applier = getattr(window, "_apply_project_theme", None)
    if callable(window_theme_applier):
        window_theme_applier(theme_id)
        return theme_id

    application = qtw.QApplication.instance()
    if application is not None:
        apply_theme(theme_id, application)
    return theme_id


# NOTE:
# The sequence declared below is a provisional baseline inferred from menu/toolbar order.
# During module-by-module prompt-pack passes, the exact step order is expected to be
# re-established and edited to match each module's real workflow behavior.
MODULE_PAGE_WORKFLOW_STEPS = {
    "MyServer": [
        WorkflowStepSpec("Review active project status", None, "Project status dialog", "file"),
        WorkflowStepSpec("Validate project workflow readiness", None, "Workflow readiness dialog", "file"),
        WorkflowStepSpec("Hand off module launch for next page stage", None, "Module launch dialog", "file"),
    ],
    "MyExplorer": [
        WorkflowStepSpec("Confirm project folder target", None, "Project folder picker", "folder"),
        WorkflowStepSpec("Review page asset locations", None, "Asset review picker", "folder"),
        WorkflowStepSpec("Open file target in operating system", None, "System opener", "file"),
    ],
    "MyScanner": [
        WorkflowStepSpec("Acquire or import source page image", "loadImage", "Image picker", "file"),
        WorkflowStepSpec("Validate image orientation/quality", None, "Image validation dialog", "file"),
        WorkflowStepSpec("Export page image into project structure", None, "Export dialog", "file"),
    ],
    "MyPixler": [
        WorkflowStepSpec("Open current page image", "loadImage", "Image picker", "file"),
        WorkflowStepSpec("Apply cleanup adjustments", None, "Cleanup dialog", "file"),
        WorkflowStepSpec("Save updated page image", None, "Save dialog", "file"),
    ],
    "MyBoxer": [
        WorkflowStepSpec("Open page segmentation workspace", "loadImage", "Image picker", "file"),
        WorkflowStepSpec("Run page/line box adjustments", "loadText", "Text picker", "file"),
        WorkflowStepSpec("Save box geometry updates", None, "Save dialog", "file"),
    ],
    "MyGlypher": [
        WorkflowStepSpec("Load page line image", "loadImage", "Image picker", "file"),
        WorkflowStepSpec("Extract glyph set", None, "Glyph extraction dialog", "file"),
        WorkflowStepSpec("Save glyph updates", None, "Save dialog", "file"),
    ],
    "MyReader": [
        WorkflowStepSpec("Load page image and OCR text", "loadImage", "Image picker", "file"),
        WorkflowStepSpec("Review OCR output", "loadText", "Text picker", "file"),
        WorkflowStepSpec("Save text corrections", None, "Save dialog", "file"),
    ],
    "MyGrounder": [
        WorkflowStepSpec("Load page reference assets", "loadImage", "Image picker", "file"),
        WorkflowStepSpec("Validate ground-truth alignment", "loadText", "Ground-truth dialog", "file"),
        WorkflowStepSpec("Save ground-truth updates", None, "Save dialog", "file"),
    ],
    "MyTrainer": [
        WorkflowStepSpec("Validate training inputs", None, "Training input dialog", "file"),
        WorkflowStepSpec("Run training step for current page set", None, "Training dialog", "file"),
        WorkflowStepSpec("Review training log/output", None, "Training log dialog", "file"),
    ],
    "MyLexer": [
        WorkflowStepSpec("Load page text artifact", "loadText", "Text picker", "file"),
        WorkflowStepSpec("Run lexical processing", None, "Lexical processing dialog", "file"),
        WorkflowStepSpec("Save lexical updates", None, "Save dialog", "file"),
    ],
    "MyResolver": [
        WorkflowStepSpec("Load unresolved variants", None, "Variant picker", "file"),
        WorkflowStepSpec("Apply resolution decisions", None, "Resolution dialog", "file"),
        WorkflowStepSpec("Save resolved variant updates", None, "Save dialog", "file"),
    ],
    "MyVersifier": [
        WorkflowStepSpec("Load verse comparison view", "loadText", "Text picker", "file"),
        WorkflowStepSpec("Apply verse alignment updates", None, "Verse alignment dialog", "file"),
        WorkflowStepSpec("Save verse corrections", None, "Save dialog", "file"),
    ],
    "MyWriter": [
        WorkflowStepSpec("Load publication-ready text", None, "Text picker", "file"),
        WorkflowStepSpec("Run final page validation", None, "Validation dialog", "file"),
        WorkflowStepSpec("Export page output", None, "Export dialog", "file"),
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

_PAGE_WORKFLOW_DIALOG_ATTRS = {
    "loadImage": "_image_open_dialog",
    "loadText": "_text_open_dialog",
}

_PAGE_WORKFLOW_PICKER_KIND = {
    "loadImage": "file",
    "loadText": "file",
}

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


def _explorer_get_open_file_name(parent=None, caption="", directory="", _filter="", *args, **kwargs):
    selected_path = run_myexplorer_selection(caption or "Open File", directory, "file")
    return selected_path, ""


def _explorer_get_save_file_name(parent=None, caption="", directory="", _filter="", *args, **kwargs):
    suggested_name = ""
    if directory:
        suggested_name = os.path.basename(directory) if os.path.basename(directory) else ""
    start_dir = os.path.dirname(directory) if directory and suggested_name else directory
    selected_path = run_myexplorer_selection(caption or "Save File", start_dir, "both")
    if selected_path and os.path.isdir(selected_path) and suggested_name:
        selected_path = os.path.join(selected_path, suggested_name)
    return selected_path, ""


def _explorer_get_existing_directory(parent=None, caption="", directory="", *args, **kwargs):
    return run_myexplorer_selection(caption or "Select Folder", directory, "directory")


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
        action.setShortcutVisibleInContextMenu(True)


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
            action.setShortcutVisibleInContextMenu(True)
            continue
        if action.shortcut().isEmpty():
            action.setShortcut(DEFAULT_MENU_SHORTCUTS[canonical])
        action.setShortcutVisibleInContextMenu(True)


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
        auto_run: bool = False,
        auto_run_delay_ms: int = 0,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(860, 520)
        self.setSizeGripEnabled(True)
        self.stage_plan = stage_plan
        self.run_stage_callback = run_stage_callback
        self.run_all_callback = run_all_callback
        self._auto_run = bool(auto_run)
        self._auto_run_delay_ms = max(0, int(auto_run_delay_ms))
        self._build_ui(intro_text)
        self._populate_stage_pages()
        if self._auto_run:
            qtc.QTimer.singleShot(self._auto_run_delay_ms, self._run_all)

    def _build_default_summary_widget(self, defaults: dict) -> qtw.QWidget:
        container = qtw.QGroupBox("Session Defaults", self)
        layout = qtw.QFormLayout(container)
        layout.setLabelAlignment(qtc.Qt.AlignLeft)
        layout.setFormAlignment(qtc.Qt.AlignTop)

        if not defaults:
            layout.addRow(qtw.QLabel("No session defaults are available."))
            return container

        for key, value in defaults.items():
            label = str(key).replace('_', ' ').title()
            rendered_value = str(value or '').strip() or '—'
            field = qtw.QLabel(rendered_value)
            field.setWordWrap(True)
            layout.addRow(label, field)

        return container

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
            defaults = stage.get("defaults", {})
            module_name = stage.get("module_name", stage.get("key", ""))

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

            if defaults:
                layout.addWidget(self._build_default_summary_widget(defaults))

            step_list = qtw.QListWidget(page)
            for step in _module_workflow_steps(module_name):
                dialog_name = step.get('dialog', '')
                if dialog_name:
                    step_list.addItem(f"{module_name or step.get('module', 'Module')}: {step.get('label', '')} -> {dialog_name}")
                else:
                    step_list.addItem(f"{module_name or step.get('module', 'Module')}: {step.get('label', '')}")
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


def _launch_myexplorer_picker(title: str, start_dir: str, selection_kind: str) -> str:
    return run_myexplorer_selection(title, start_dir, selection_kind)


def _workflow_start_directory(window, module_name: str, load_method_name: str) -> str:
    candidates = []
    for attr_name in ("imgdir", "txtdir", "directory", "projecthome", "current_project_root"):
        value = getattr(window, attr_name, "")
        if value:
            candidates.append(str(value))

    session_manager = getattr(window, "session_manager", None)
    if hasattr(session_manager, "get_active_project_root"):
        project_root = session_manager.get_active_project_root("Session.json")
        if project_root:
            candidates.append(project_root)

    candidates.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

    for candidate in candidates:
        if candidate and os.path.isdir(candidate):
            return os.path.abspath(candidate)
    return os.getcwd()


def _invoke_page_workflow_loader(window, load_method_name: str, selected_path: str) -> None:
    load_method = getattr(window, load_method_name, None)
    if not callable(load_method):
        return

    selected_path = str(selected_path or "").strip()
    if not selected_path:
        return

    original_image_picker = getattr(window, "open_non_modal_image_picker", None)
    original_text_picker = getattr(window, "open_non_modal_text_picker", None)
    original_file_picker = getattr(window, "open_non_modal_file_picker", None)

    def _direct_picker(_title, _directory, selected_handler, _dialog_attr_name, *_args, **_kwargs):
        return selected_handler(selected_path)

    try:
        window.open_non_modal_file_picker = _direct_picker
        window.open_non_modal_image_picker = _direct_picker
        window.open_non_modal_text_picker = _direct_picker
        load_method()
    finally:
        if original_file_picker is not None:
            window.open_non_modal_file_picker = original_file_picker
        if original_image_picker is not None:
            window.open_non_modal_image_picker = original_image_picker
        if original_text_picker is not None:
            window.open_non_modal_text_picker = original_text_picker


def _prompt_page_workflow_load(window, module_name: str, load_method_name: str) -> bool:
    selection_kind = _PAGE_WORKFLOW_PICKER_KIND.get(load_method_name, "file")
    start_dir = _workflow_start_directory(window, module_name, load_method_name)
    prompt_title = f"{module_name}: select {load_method_name.replace('load', '').lower() or 'workflow input'}"
    selected_path = _launch_myexplorer_picker(prompt_title, start_dir, selection_kind)
    if not selected_path:
        return False

    _invoke_page_workflow_loader(window, load_method_name, selected_path)
    return True


def _prompt_module_page_workflow_inputs(window, module_name: str) -> bool:
    for step in _module_workflow_steps(module_name):
        if not step.method_name:
            continue
        if not _prompt_page_workflow_load(window, module_name, step.method_name):
            return False
    return True


def _module_workflow_steps(module_name: str):
    steps = MODULE_PAGE_WORKFLOW_STEPS.get(module_name)
    if steps:
        return steps
    return [
        WorkflowStepSpec("Load page context", "loadImage", "Generic input dialog", "file"),
        WorkflowStepSpec("Run module workflow", None, "Execution dialog", "file"),
        WorkflowStepSpec("Save module output", None, "Save dialog", "file"),
    ]


def open_default_module_page_workflow_wizard(window, module_name: str) -> None:
    """Open the default module-local page workflow wizard for a module window."""

    apply_active_project_theme(window)
    session_manager = getattr(window, "session_manager", None)

    if not _prompt_module_page_workflow_inputs(window, module_name):
        return

    steps = [
        {
            "module": module_name,
            "label": step.label,
            "dialog": step.dialog_name,
            "method": step.method_name or "",
            "picker_kind": step.picker_kind,
        }
        for step in _module_workflow_steps(module_name)
    ]
    defaults = {}
    if hasattr(session_manager, "build_workflow_wizard_defaults"):
        defaults = session_manager.build_workflow_wizard_defaults("page", module_name)
    defaults.update(
        {
            "stage_key": f"{module_name.lower()}_page_stage",
            "stage_modules": module_name,
            "step_count": len(steps),
        }
    )

    stage_plan = [
        {
            "key": f"{module_name.lower()}_page_stage",
            "module_name": module_name,
            "title": f"{module_name} Page Workflow",
            "description": (
                f"Run the standardized {module_name} page workflow sequence for the active page context."
            ),
            "steps": steps,
            "defaults": defaults,
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
        if module_name == "MyWriter":
            project_root = str(defaults.get("active_project_root") or "").strip()
            if project_root:
                tracker = ProjectWorkflowTracker()
                context = tracker._load_project_context(project_root)
                page_number = context.get("CurrentProjectPage", context.get("ProjectPageNumber", 1))
                tracker.record_page_completion(project_root, page_number)

    dialog = ModulePageWorkflowWizardDialog(
        title=f"{module_name} Page Workflow Wizard",
        intro_text=(
            "Module-specific page workflow wizard. "
            "It uses the shared step sequence -> dialog structure and pauses for MyExplorer file selection overrides before continuing."
        ),
        stage_plan=stage_plan,
        run_stage_callback=run_stage,
        run_all_callback=run_all,
        auto_run=True,
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
    apply_active_project_theme(window)
    _install_default_context_menu_behavior(window)
    _install_explorer_backed_file_dialogs(window)
    _install_myexplorer_method_aliases(window)
    _install_myexplorer_icon_lockstep(window)
    _install_panel_file_drop_behavior(window)
    _install_save_confirmation_wrappers(window)
    if module_name not in {"MyExplorer", "MyWriter"}:
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
