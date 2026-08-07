import os
import subprocess
import sys
from typing import Optional

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


def append_default_context_actions(menu: qtw.QMenu, widget: qtw.QWidget, *, is_text_widget: Optional[bool] = None) -> None:
    if is_text_widget is None:
        is_text_widget = isinstance(widget, (qtw.QLineEdit, qtw.QTextEdit, qtw.QPlainTextEdit, qtw.QTextBrowser))

    action_map = {}
    for action in menu.actions():
        key = _canonical_action_name(action.text())
        if key:
            action_map[key] = action

    ordered_keys = ["help", "undo", "redo"]
    if is_text_widget:
        ordered_keys.extend(["cut", "copy", "paste"])

    for key in ordered_keys:
        action = action_map.get(key)
        if action is None:
            action = qtw.QAction(key.title(), menu)
            if key == "undo":
                action.triggered.connect(lambda _checked=False, w=widget: _invoke_widget_method(w, "undo"))
            elif key == "redo":
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
            continue
        if action.shortcut().isEmpty():
            action.setShortcut(DEFAULT_MENU_SHORTCUTS[canonical])


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
