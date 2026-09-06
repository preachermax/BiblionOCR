
import re
import os
import sys
from pathlib import Path
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QListWidget,
    QCheckBox, QMessageBox, QComboBox, QMenu, QAction, QDialog, QTextBrowser
)

# List of common regex snippets: (Display Text, Actual Pattern Insertion)
REGEX_SNIPPETS = [
    ("-- Select a Regex Snippet to Insert --", ""),
    ("Digits / Numbers (\\d+)", "\\d+"),
    ("Letters & Words (\\w+)", "\\w+"),
    ("Spaces / Whitespace (\\s+)", "\\s+"),
    ("Start of Filename (^)", "^"),
    ("End of Filename ($)", "$"),
    ("Any Characters (.*)", ".*"),
    ("Capture Group 1 (\\1)", "\\1"),
    ("Capture Group 2 (\\2)", "\\2"),
    ("Year-Month-Day Date Pattern", "(\\d{4})-(\\d{2})-(\\d{2})"),
    ("Remove Parentheses Content", "\\s\\(.*\\)"),
]

class UnifiedContextFilter(QMenu):
    """An event filter that generates custom context menus globally for all widgets."""
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_win = main_window

    def eventFilter(self, obj, event):
        if event.type() == QEvent.ContextMenu:
            # Create a localized context menu
            menu = QMenu(obj)

            # Identify if the target widget supports text manipulation
            is_line_edit = isinstance(obj, QLineEdit)

            # Context Menu Actions
            act_undo = QAction("Undo", obj)
            act_redo = QAction("Redo", obj)
            act_cut = QAction("Cut", obj)
            act_copy = QAction("Copy", obj)
            act_paste = QAction("Paste", obj)
            act_help = QAction("Help (User Guide)", obj)

            # Connect standard text manipulation slots if applicable
            if is_line_edit:
                act_undo.setEnabled(obj.isUndoAvailable())
                act_redo.setEnabled(obj.isRedoAvailable())
                act_cut.setEnabled(obj.hasSelectedText())
                act_copy.setEnabled(obj.hasSelectedText())
                act_paste.setEnabled(True)

                act_undo.triggered.connect(obj.undo)
                act_redo.triggered.connect(obj.redo)
                act_cut.triggered.connect(obj.cut)
                act_copy.triggered.connect(obj.copy)
                act_paste.triggered.connect(obj.paste)
            elif isinstance(obj, QListWidget):
                act_undo.setEnabled(False)
                act_redo.setEnabled(False)
                act_cut.setEnabled(False)
                act_copy.setEnabled(obj.currentItem() is not None)
                act_paste.setEnabled(False)
                act_copy.triggered.connect(lambda: QApplication.clipboard().setText(obj.currentItem().text() if obj.currentItem() else ""))
            else:
                # Disable text operations for layout containers or non-input elements
                act_undo.setEnabled(False)
                act_redo.setEnabled(False)
                act_cut.setEnabled(False)
                act_copy.setEnabled(False)
                act_paste.setEnabled(False)

            # Global action hook to launch markdown help
            act_help.triggered.connect(self.main_win.show_help_dialog)

            # Build and display menu layout structure
            menu.addAction(act_undo)
            menu.addAction(act_redo)
            menu.addSeparator()
            menu.addAction(act_cut)
            menu.addAction(act_copy)
            menu.addAction(act_paste)
            menu.addSeparator()
            menu.addAction(act_help)

            menu.exec_(event.globalPos())
            return True
        return False


class AdvancedBulkRenamer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced Bulk Rename Tool")
        self.resize(650, 550)

        # Keep track of which input field was clicked last for Regex insertion
        self.last_focused_input = None

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Directory Picker
        dir_layout = QHBoxLayout()
        self.dir_input = QLineEdit()
        btn_browse = QPushButton("Browse")
        btn_browse.clicked.connect(self.select_directory)
        dir_layout.addWidget(self.dir_input)
        dir_layout.addWidget(btn_browse)
        layout.addLayout(dir_layout)

        # Options: Recursive & Regex Checkboxes
        options_layout = QHBoxLayout()
        self.chk_recursive = QCheckBox("Include Subfolders (Recursive)")
        self.chk_regex = QCheckBox("Use Regular Expressions (Regex)")
        options_layout.addWidget(self.chk_recursive)
        options_layout.addWidget(self.chk_regex)
        layout.addLayout(options_layout)

        # Search & Replace Fields
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Text or Regex pattern to search")
        self.search_input.focused = lambda: self.set_active_input(self.search_input)

        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("Replacement text")
        self.replace_input.focused = lambda: self.set_active_input(self.replace_input)

        # Override focus events to track active field
        self.search_input.focusInEvent = lambda e: (QLineEdit.focusInEvent(self.search_input, e), self.set_active_input(self.search_input))
        self.replace_input.focusInEvent = lambda e: (QLineEdit.focusInEvent(self.replace_input, e), self.set_active_input(self.replace_input))

        # Quick Regex Dropdown Component
        regex_hint_layout = QHBoxLayout()
        regex_hint_layout.addWidget(QLabel("Regex Snippet Builder:"))
        self.combo_regex = QComboBox()
        for title, pattern in REGEX_SNIPPETS:
            self.combo_regex.addItem(title, pattern)
        self.combo_regex.currentIndexChanged.connect(self.insert_regex_snippet)
        regex_hint_layout.addWidget(self.combo_regex)

        layout.addWidget(QLabel("Search for:"))
        layout.addWidget(self.search_input)
        layout.addLayout(regex_hint_layout)
        layout.addWidget(QLabel("Replace with:"))
        layout.addWidget(self.replace_input)

        # File Preview List
        self.file_list = QListWidget()
        layout.addWidget(self.file_list)

        # Action Buttons Layout
        btn_layout = QHBoxLayout()
        btn_preview = QPushButton("Preview Changes")
        btn_preview.clicked.connect(self.preview_rename)
        btn_rename = QPushButton("Apply Rename")
        btn_rename.clicked.connect(self.apply_rename)

        btn_layout.addWidget(btn_preview)
        btn_layout.addWidget(btn_rename)
        layout.addLayout(btn_layout)

        # Initialize and install unified context menu event filter
        self.context_filter = UnifiedContextFilter(self)
        QApplication.instance().installEventFilter(self.context_filter)

        # Set default focus tracking
        self.last_focused_input = self.search_input

    def set_active_input(self, target_widget):
        self.last_focused_input = target_widget

    def insert_regex_snippet(self, index):
        if index <= 0 or not self.last_focused_input:
            return

        snippet = self.combo_regex.itemData(index)
        if snippet:
            # Auto-enable the regex checkbox if the user uses the dropdown helper
            self.chk_regex.setChecked(True)
            # Insert syntax pattern string into current cursor position smoothly
            current_text = self.last_focused_input.text()
            cursor_pos = self.last_focused_input.cursorPosition()
            new_text = current_text[:cursor_pos] + snippet + current_text[cursor_pos:]
            self.last_focused_input.setText(new_text)
            self.last_focused_input.setCursorPosition(cursor_pos + len(snippet))
            self.last_focused_input.setFocus()

        # Reset dropdown index selection to prompt text
        self.combo_regex.setCurrentIndex(0)

    def show_help_dialog(self):
        """Finds and loads README.md dynamically relative to the application layer path."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Application Documentation & User Guide")
        dialog.resize(600, 500)

        layout = QVBoxLayout(dialog)
        viewer = QTextBrowser()

        # Locate path relative to script folder pathing structures
        script_dir = os.path.dirname(os.path.abspath(__file__))
        readme_path = os.path.join(script_dir, "README.md")

        if os.path.exists(readme_path):
            with open(readme_path, "r", encoding="utf-8") as file:
                viewer.setMarkdown(file.read())
        else:
            viewer.setHtml(f"<h3>Documentation File Missing</h3><p>Could not locate file: <code>{readme_path}</code></p>")

        layout.addWidget(viewer)
        dialog.exec_()

    def select_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if dir_path:
            self.dir_input.setText(dir_path)
            self.load_files()

    def get_target_paths(self, folder_path):
        path = Path(folder_path)
        if self.chk_recursive.isChecked():
            paths = list(path.rglob("*"))
        else:
            paths = list(path.iterdir())
        paths.sort(key=lambda p: len(p.parts), reverse=True)
        return paths

    def load_files(self):
        self.file_list.clear()
        folder = self.dir_input.text()
        if not folder or not Path(folder).exists():
            return

        paths = self.get_target_paths(folder)
        for item in reversed(paths):
            self.file_list.addItem(str(item.relative_to(folder)))

    def preview_rename(self):
        self.file_list.clear()
        folder = self.dir_input.text()
        search = self.search_input.text()
        replace = self.replace_input.text()
        if not folder or not search:
            self.load_files()
            return
        paths = self.get_target_paths(folder)
        for item in reversed(paths):
            old_name = item.name
            try:
                if self.chk_regex.isChecked():
                    if re.search(search, old_name):
                        new_name = re.sub(search, replace, old_name)
                        self.file_list.addItem(f"{item.relative_to(folder)}  ->  {new_name}")
                    else:
                        self.file_list.addItem(str(item.relative_to(folder)))
                else:
                    if search in old_name:
                        new_name = old_name.replace(search, replace)
                        self.file_list.addItem(f"{item.relative_to(folder)}  ->  {new_name}")
                    else:
                        self.file_list.addItem(str(item.relative_to(folder)))
            except re.error as e:
                QMessageBox.critical(self, "Regex Error", f"Invalid Regular Expression: {e}")
                return

    def apply_rename(self):
        folder = self.dir_input.text()
        search = self.search_input.text()
        replace = self.replace_input.text()
        if not folder or not search:
            QMessageBox.warning(self, "Warning", "Please select a folder and enter search criteria.")
            return
        paths = self.get_target_paths(folder)
        renamed_count = 0
        try:
            for item in paths:
                old_name = item.name
                if self.chk_regex.isChecked():
                    if re.search(search, old_name):
                        new_name = re.sub(search, replace, old_name)
                        item.rename(item.with_name(new_name))
                        renamed_count += 1
                else:
                    if search in old_name:
                        new_name = old_name.replace(search, replace)
                        item.rename(item.with_name(new_name))
                        renamed_count += 1
        except re.error as e:
            QMessageBox.critical(self, "Regex Error", f"Invalid Regular Expression: {e}")
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred during renaming: {e}")
            return
        QMessageBox.information(self, "Success", f"Successfully renamed {renamed_count} items.")
        self.load_files()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AdvancedBulkRenamer()
    window.show()
    sys.exit(app.exec_())