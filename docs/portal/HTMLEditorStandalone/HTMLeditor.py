import sys
import os
import json
from html import escape

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from gui_runtime_env import sanitize_current_process_and_reexec

sanitize_current_process_and_reexec()

from PyQt5.QtWidgets import (QApplication, QDialog, QMessageBox, QColorDialog, 
                             QComboBox, QInputDialog, QFileDialog, QTextEdit, 
                             QPushButton, QHBoxLayout, QVBoxLayout, QWidget,
                             QLabel, QRadioButton, QButtonGroup)
from PyQt5.QtGui import QFontDatabase, QColor, QTextCursor, QKeySequence
from PyQt5.QtCore import Qt, QEvent

# Import your cleanly compiled class from HTMLeditorUI.py
from HTMLeditorUI import Ui_HTMLDialog

class PersistentComboBox(QComboBox):
    """A ComboBox whose popup view stays open until an item is explicitly selected."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.view().viewport().installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.view().viewport() and event.type() == QEvent.MouseButtonRelease:
            index = self.view().indexAt(event.pos())
            if index.isValid():
                self.setCurrentIndex(index.row())
            return True
        return super().eventFilter(obj, event)


class HTMLDialogEditor(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Instantiate and declare the UI layout explicitly
        self.ui = Ui_HTMLDialog()
        self.ui.setupUi(self)
        
        self.current_file_path = None
        self.document_mode = "html"
        
        # Tracking states for multi-block text selections using Ctrl key
        self.multi_selections = []
        self.is_ctrl_selecting = False
        self.current_selection_start = None
        self.is_applying_multi_edit = False

        # Inject dynamic runtime configurations
        self.init_toolbar_extensions()
        self.inject_html_source_button()
        self.connect_actions()
        self.setup_multi_selection_handlers()
        
        # Enforce rich text mode to ensure HTML content parses and renders visually
        self.ui.editor.setAcceptRichText(True)
        self.ui.editor.setLineWrapMode(QTextEdit.WidgetWidth)

    def init_toolbar_extensions(self):
        """Appends custom PersistentComboBox components onto the toolbar layout."""
        self.font_combo = PersistentComboBox()
        db = QFontDatabase()
        system_fonts = db.families()
        self.font_combo.addItems(system_fonts)
        
        # Type-safe string resolution avoiding list assignment errors
        default_font = "Arial" if "Arial" in system_fonts else system_fonts[0] if system_fonts else ""
        self.font_combo.setCurrentText(default_font)
        self.font_combo.currentTextChanged.connect(self.set_font_family)
        
        self.size_combo = PersistentComboBox()
        sizes = [str(x) for x in range(8, 73, 2)]
        self.size_combo.addItems(sizes)
        self.size_combo.setCurrentText("12")
        self.size_combo.currentTextChanged.connect(self.set_font_size)
        
        self.ui.formatToolBar.addSeparator()
        self.ui.formatToolBar.addWidget(self.font_combo)
        self.ui.formatToolBar.addWidget(self.size_combo)

    def inject_html_source_button(self):
        """Creates and embeds source-view controls at the bottom of the dialog."""
        main_layout = self.layout()
        if not main_layout:
            return
            
        button_container = QWidget()
        hbox = QHBoxLayout(button_container)
        hbox.setContentsMargins(0, 5, 0, 0)
        hbox.addStretch() 

        source_label = QLabel("Source View:")
        hbox.addWidget(source_label)

        self.source_mode_group = QButtonGroup(self)
        self.radio_view_html = QRadioButton("HTML")
        self.radio_view_markdown = QRadioButton("Markdown")
        self.radio_view_json = QRadioButton("JSON")
        self.radio_view_html.setChecked(True)

        for button in (self.radio_view_html, self.radio_view_markdown, self.radio_view_json):
            self.source_mode_group.addButton(button)
            hbox.addWidget(button)
        
        self.btn_view_source = QPushButton("View Source Code")
        self.btn_view_source.setStyleSheet("padding: 6px 12px; font-weight: bold;")
        self.btn_view_source.clicked.connect(self.show_raw_html_code)
        
        hbox.addWidget(self.btn_view_source)
        main_layout.addWidget(button_container)

    def setup_multi_selection_handlers(self):
        """Installs mouse and keyboard hooks into the text editor viewport."""
        self.ui.editor.installEventFilter(self)
        self.ui.editor.viewport().installEventFilter(self)
        self.ui.editor.textChanged.connect(self.handle_editor_text_changed)

    def eventFilter(self, obj, event):
        """Intercepts modifications while preserving native rendering properties."""
        if obj == self.ui.editor and event.type() == QEvent.KeyPress:
            if self.multi_selections and self.handle_multi_selection_keypress(event):
                return True

            if event.matches(QKeySequence.Paste) and self.document_mode in {"markdown", "text"}:
                self.paste_from_clipboard()
                return True

        if obj == self.ui.editor.viewport():
            modifiers = QApplication.keyboardModifiers()
            
            # Detect Ctrl press + mouse down interaction
            if event.type() == QEvent.MouseButtonPress and (modifiers & Qt.ControlModifier):
                self.is_ctrl_selecting = True
                cursor = self.ui.editor.cursorForPosition(event.pos())
                self.current_selection_start = cursor.position()
                return True 
                
            # Track active drag movement
            elif event.type() == QEvent.MouseMove and self.is_ctrl_selecting:
                cursor = self.ui.editor.cursorForPosition(event.pos())
                current_pos = cursor.position()
                self.update_active_selection_view(self.current_selection_start, current_pos)
                return True
                
            # Save tracked block when mouse release occurs
            elif event.type() == QEvent.MouseButtonRelease and self.is_ctrl_selecting:
                cursor = self.ui.editor.cursorForPosition(event.pos())
                end_pos = cursor.position()
                
                if self.current_selection_start != end_pos:
                    sel = QTextEdit.ExtraSelection()
                    sel.cursor = self.ui.editor.textCursor()
                    sel.cursor.setPosition(self.current_selection_start)
                    sel.cursor.setPosition(end_pos, QTextCursor.KeepAnchor)
                    sel.format.setBackground(QColor(0, 120, 215, 60)) 
                    self.multi_selections.append(sel)
                    
                self.is_ctrl_selecting = False
                self.render_selections()
                return True
                
            # Clear multi-blocks if a standard left-click occurs without the Ctrl key
            elif event.type() == QEvent.MouseButtonPress and not (modifiers & Qt.ControlModifier):
                self.clear_multi_selections()

        return super().eventFilter(obj, event)

    def update_active_selection_view(self, start, current):
        active_sel = QTextEdit.ExtraSelection()
        active_sel.cursor = self.ui.editor.textCursor()
        active_sel.cursor.setPosition(start)
        active_sel.cursor.setPosition(current, QTextCursor.KeepAnchor)
        active_sel.format.setBackground(QColor(0, 120, 215, 60))
        self.ui.editor.setExtraSelections(self.multi_selections + [active_sel])

    def render_selections(self):
        self.ui.editor.setExtraSelections(self.multi_selections)

    def clear_multi_selections(self):
        if self.multi_selections:
            self.multi_selections = []
            self.ui.editor.setExtraSelections([])

    def handle_editor_text_changed(self):
        if self.is_applying_multi_edit:
            return

        self.clear_multi_selections()

    def multi_selection_ranges(self):
        ranges = []
        for selection in self.multi_selections:
            cursor = selection.cursor
            ranges.append((cursor.selectionStart(), cursor.selectionEnd()))
        return sorted(ranges)

    def restore_multi_selections(self, ranges):
        restored = []
        max_position = max(0, self.ui.editor.document().characterCount() - 1)
        for start, end in ranges:
            start = max(0, min(start, max_position))
            end = max(0, min(end, max_position))
            selection = QTextEdit.ExtraSelection()
            selection.cursor = QTextCursor(self.ui.editor.document())
            selection.cursor.setPosition(start)
            selection.cursor.setPosition(end, QTextCursor.KeepAnchor)
            selection.format.setBackground(QColor(0, 120, 215, 60))
            restored.append(selection)

        self.multi_selections = restored
        self.render_selections()

        if restored:
            primary_cursor = QTextCursor(restored[0].cursor)
            primary_cursor.clearSelection()
            self.ui.editor.setTextCursor(primary_cursor)

    def replace_multi_selection_text(self, text):
        ranges = self.multi_selection_ranges()
        if not ranges:
            return

        updated_ranges = []
        self.is_applying_multi_edit = True
        try:
            for start, end in sorted(ranges, reverse=True):
                cursor = QTextCursor(self.ui.editor.document())
                cursor.setPosition(start)
                cursor.setPosition(end, QTextCursor.KeepAnchor)
                cursor.insertText(text)
                new_position = start + len(text)
                updated_ranges.append((new_position, new_position))
        finally:
            self.is_applying_multi_edit = False

        self.restore_multi_selections(sorted(updated_ranges))

    def delete_multi_selection_text(self, backward):
        ranges = self.multi_selection_ranges()
        if not ranges:
            return

        updated_ranges = []
        self.is_applying_multi_edit = True
        try:
            for start, end in sorted(ranges, reverse=True):
                cursor = QTextCursor(self.ui.editor.document())
                if start != end:
                    cursor.setPosition(start)
                    cursor.setPosition(end, QTextCursor.KeepAnchor)
                    cursor.removeSelectedText()
                    updated_ranges.append((start, start))
                    continue

                cursor.setPosition(start)
                if backward:
                    if start == 0:
                        updated_ranges.append((0, 0))
                    else:
                        cursor.deletePreviousChar()
                        updated_ranges.append((start - 1, start - 1))
                else:
                    cursor.deleteChar()
                    updated_ranges.append((start, start))
        finally:
            self.is_applying_multi_edit = False

        self.restore_multi_selections(sorted(updated_ranges))

    def handle_multi_selection_keypress(self, event):
        if event.matches(QKeySequence.Paste):
            self.paste_into_multi_selections()
            return True

        if event.key() in (Qt.Key_Backspace, Qt.Key_Delete):
            self.delete_multi_selection_text(backward=event.key() == Qt.Key_Backspace)
            return True

        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.replace_multi_selection_text("\n")
            return True

        if event.modifiers() & (Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier):
            return False

        typed_text = event.text()
        if not typed_text:
            return False

        self.replace_multi_selection_text(typed_text)
        return True

    def show_raw_html_code(self):
        """Brings up a sub-dialog containing the selected source representation."""
        source_name, source_text = self.current_source_output()
        
        html_box = QDialog(self)
        html_box.setWindowTitle(f"Generated {source_name} Source Code")
        html_box.resize(600, 450)
        
        layout = QVBoxLayout(html_box)
        text_area = QTextEdit()
        text_area.setPlainText(source_text)
        text_area.setReadOnly(True)
        
        layout.addWidget(text_area)
        html_box.exec_()

    def current_source_output(self):
        if self.radio_view_markdown.isChecked():
            return "Markdown", self.current_markdown_output()
        if self.radio_view_json.isChecked():
            return "JSON", json.dumps(self.serialize_document(), indent=2, ensure_ascii=False)
        return "HTML", self.current_html_output()

    def connect_actions(self):
        """Binds UI actions to controller logic handlers."""
        self.ui.actionNew.triggered.connect(self.file_new)
        self.ui.actionOpen.triggered.connect(self.file_open)
        self.ui.actionSave.triggered.connect(self.file_save)
        self.ui.actionSaveAs.triggered.connect(self.file_save_as)
        
        self.ui.actionCut.triggered.connect(self.cut_selection)
        self.ui.actionCopy.triggered.connect(self.copy_selection)
        self.ui.actionPaste.triggered.connect(self.paste_into_multi_selections)
        self.ui.actionToggleWrap.triggered.connect(self.toggle_word_wrap)
        self.ui.actionBold.triggered.connect(self.set_bold)
        self.ui.actionColor.triggered.connect(self.set_text_color)
        
        self.ui.actionInsertLink.triggered.connect(self.insert_link)
        self.ui.actionInsertImage.triggered.connect(self.insert_image)
        self.ui.actionInsertDiv.triggered.connect(self.insert_div_container)

    # === Formatting Actions ===
    def set_bold(self):
        if self.multi_selections:
            for sel in self.multi_selections:
                current_weight = sel.cursor.charFormat().fontWeight()
                new_weight = 700 if current_weight <= 400 else 400
                fmt = sel.cursor.charFormat()
                fmt.setFontWeight(new_weight)
                sel.cursor.mergeCharFormat(fmt)
            self.clear_multi_selections()
        else:
            current_weight = self.ui.editor.fontWeight()
            new_weight = 700 if current_weight <= 400 else 400
            self.ui.editor.setFontWeight(new_weight)

    def set_text_color(self):
        color = QColorDialog.getColor(Qt.black, self, "Select Text Color")
        if not color.isValid(): return
        
        if self.multi_selections:
            for sel in self.multi_selections:
                fmt = sel.cursor.charFormat()
                fmt.setForeground(color)
                sel.cursor.mergeCharFormat(fmt)
            self.clear_multi_selections()
        else:
            self.ui.editor.setTextColor(color)

    def set_font_size(self, size_text):
        if not size_text: return
        if self.multi_selections:
            for sel in self.multi_selections:
                fmt = sel.cursor.charFormat()
                fmt.setFontPointSize(float(size_text))
                sel.cursor.mergeCharFormat(fmt)
        else:
            self.ui.editor.setFontPointSize(float(size_text))

    def set_font_family(self, font_name):
        if not font_name: return
        if self.multi_selections:
            for sel in self.multi_selections:
                fmt = sel.cursor.charFormat()
                fmt.setFontFamily(font_name)
                sel.cursor.mergeCharFormat(fmt)
            self.clear_multi_selections()
        else:
            self.ui.editor.setFontFamily(font_name)

    # === File Actions ===
    def detect_storage_format(self, file_path):
        extension = os.path.splitext(file_path)[1].lower()
        if extension in {".html", ".htm"}:
            return "html"
        if extension in {".md", ".markdown"}:
            return "markdown"
        if extension == ".json":
            return "json"
        return "text"

    def load_serialized_document(self, payload):
        if not isinstance(payload, dict):
            raise ValueError("JSON document must be an object.")

        document_mode = payload.get("document_mode", "html")
        if document_mode not in {"html", "markdown", "text"}:
            raise ValueError(f"Unsupported JSON document mode: {document_mode}")

        if document_mode == "html":
            content = payload.get("content") or payload.get("html") or ""
        else:
            content = payload.get("content")
            if content is None:
                content = payload.get("plain_text", "")

        self.load_document_content(content, document_mode)

    def serialize_document(self):
        return {
            "format": "biblion-html-editor",
            "version": 1,
            "document_mode": self.document_mode,
            "content": self.ui.editor.toPlainText() if self.document_mode in {"markdown", "text"} else self.ui.editor.toHtml(),
            "plain_text": self.ui.editor.toPlainText(),
            "html": self.current_html_output(),
        }

    def load_document_content(self, content, document_mode):
        self.document_mode = document_mode
        self.clear_multi_selections()
        if document_mode == "html":
            self.ui.editor.setHtml(content)
        else:
            self.ui.editor.setPlainText(content)

    def current_html_output(self):
        if self.document_mode == "markdown":
            markdown_source = self.ui.editor.toPlainText()
            markdown_renderer = QTextEdit()
            if hasattr(markdown_renderer, "setMarkdown"):
                markdown_renderer.setMarkdown(markdown_source)
            else:
                markdown_renderer.setPlainText(markdown_source)
            return markdown_renderer.toHtml()

        return self.ui.editor.toHtml()

    def current_markdown_output(self):
        if self.document_mode == "markdown":
            return self.ui.editor.toPlainText()

        if hasattr(self.ui.editor, "toMarkdown"):
            return self.ui.editor.toMarkdown()

        return self.ui.editor.toPlainText()

    def file_new(self):
        if not self.confirm_discard_changes():
            return

        self.ui.editor.clear()
        self.current_file_path = None
        self.document_mode = "html"
        self.ui.editor.document().setModified(False)

    def file_open(self):
        if not self.confirm_discard_changes():
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open HTML File",
            self.current_file_path or "",
            "HTML Files (*.html *.htm);;Markdown Files (*.md *.markdown);;JSON Files (*.json);;Text Files (*.txt);;All Files (*)",
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as handle:
                content = handle.read()
        except OSError as error:
            QMessageBox.critical(self, "Open Failed", f"Could not open file:\n{error}")
            return

        storage_format = self.detect_storage_format(file_path)
        try:
            if storage_format == "json":
                self.load_serialized_document(json.loads(content))
            else:
                self.load_document_content(content, storage_format)
        except (ValueError, json.JSONDecodeError) as error:
            QMessageBox.critical(self, "Open Failed", f"Could not parse file:\n{error}")
            return

        self.current_file_path = file_path
        self.ui.editor.document().setModified(False)

    def file_save(self):
        if not self.current_file_path:
            return self.file_save_as()

        return self.write_document(self.current_file_path)

    def file_save_as(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save HTML File",
            self.current_file_path or self.default_save_name(),
            "HTML Files (*.html *.htm);;Markdown Files (*.md *.markdown);;JSON Files (*.json);;Text Files (*.txt);;All Files (*)",
        )
        if not file_path:
            return False

        if not os.path.splitext(file_path)[1]:
            file_path = f"{file_path}{self.default_extension()}"

        if self.write_document(file_path):
            self.current_file_path = file_path
            return True
        return False

    def write_document(self, file_path):
        storage_format = self.detect_storage_format(file_path)
        try:
            with open(file_path, "w", encoding="utf-8") as handle:
                if storage_format == "json":
                    json.dump(self.serialize_document(), handle, indent=2, ensure_ascii=False)
                elif storage_format in {"markdown", "text"}:
                    handle.write(self.ui.editor.toPlainText())
                else:
                    handle.write(self.current_html_output())
        except OSError as error:
            QMessageBox.critical(self, "Save Failed", f"Could not save file:\n{error}")
            return False

        self.ui.editor.document().setModified(False)
        return True

    def default_extension(self):
        if self.document_mode == "markdown":
            return ".md"
        if self.document_mode == "text":
            return ".txt"
        return ".html"

    def default_save_name(self):
        return f"document{self.default_extension()}"

    def confirm_discard_changes(self):
        if not self.ui.editor.document().isModified():
            return True

        result = QMessageBox.question(
            self,
            "Unsaved Changes",
            "Discard the current unsaved changes?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return result == QMessageBox.Yes

    # === Editor Actions ===
    def toggle_word_wrap(self):
        wrap_enabled = self.ui.editor.lineWrapMode() != QTextEdit.NoWrap
        new_mode = QTextEdit.NoWrap if wrap_enabled else QTextEdit.WidgetWidth
        self.ui.editor.setLineWrapMode(new_mode)
        self.ui.actionToggleWrap.setText(
            "Word Wrap: OFF" if wrap_enabled else "Word Wrap: ON"
        )

    def copy_selection(self):
        if not self.multi_selections:
            self.ui.editor.copy()
            return

        fragments = []
        for start, end in self.multi_selection_ranges():
            cursor = QTextCursor(self.ui.editor.document())
            cursor.setPosition(start)
            cursor.setPosition(end, QTextCursor.KeepAnchor)
            fragments.append(cursor.selectedText().replace("\u2029", "\n"))

        QApplication.clipboard().setText("\n".join(fragments))

    def cut_selection(self):
        if not self.multi_selections:
            self.ui.editor.cut()
            return

        self.copy_selection()
        self.delete_multi_selection_text(backward=True)

    def paste_into_multi_selections(self):
        if not self.multi_selections:
            self.paste_from_clipboard()
            return

        self.replace_multi_selection_text(QApplication.clipboard().text())

    def paste_from_clipboard(self):
        clipboard_text = QApplication.clipboard().text()
        if self.document_mode in {"markdown", "text"}:
            self.ui.editor.textCursor().insertText(clipboard_text)
        else:
            self.ui.editor.paste()

    def insert_link(self):
        url, ok = QInputDialog.getText(self, "Insert Hyperlink", "URL:")
        if not ok or not url.strip():
            return

        link_text, ok = QInputDialog.getText(
            self,
            "Insert Hyperlink",
            "Display text:",
            text=url.strip(),
        )
        if not ok:
            return

        safe_url = escape(url.strip(), quote=True)
        safe_text = escape(link_text or url.strip())
        self.ui.editor.textCursor().insertHtml(f'<a href="{safe_url}">{safe_text}</a>')

    def insert_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Insert Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;All Files (*)",
        )
        if not file_path:
            return

        image_path = escape(file_path, quote=True)
        alt_text = escape(os.path.basename(file_path), quote=True)
        self.ui.editor.textCursor().insertHtml(f'<img src="{image_path}" alt="{alt_text}">')

    def insert_div_container(self):
        cursor = self.ui.editor.textCursor()
        if cursor.hasSelection():
            inner_html = escape(cursor.selectedText()).replace("\u2029", "<br>")
        else:
            inner_html = "Content"
        cursor.insertHtml(
            '<table border="1" cellspacing="0" cellpadding="8" width="100%"'
            ' style="margin:6px 0; border:1px solid #999;">'
            '<tr><td style="border:1px solid #999;">'
            f"{inner_html}"
            "</td></tr></table>"
        )

if __name__ == "__main__":
    import traceback
    
    # Forcefully unset Snap environment variables before initialization
    # to stop sandboxed theme engines from throwing symbol lookup crashes
    for env_name in (
        "GTK_PATH",
        "GIO_MODULE_DIR",
        "GTK_MODULES",
        "GTK_EXE_PREFIX",
        "GTK_IM_MODULE_FILE",
    ):
        os.environ.pop(env_name, None)
    
    try:
        app = QApplication(sys.argv)
        dialog = HTMLDialogEditor()
        dialog.show()
        sys.exit(app.exec_())
        
    except Exception as fatal_error:
        print("\n!!! CRITICAL APPLICATION INITIALIZATION CRASH !!!\n")
        traceback.print_exc()
