import csv
import json
import os
import re

from PyQt5 import QtWidgets as qtw


class ProjectCreationWizardDialog(qtw.QDialog):
    DEFAULT_TESSERACT_LANGUAGES = ["English", "Greek", "Hebrew", "Latin"]

    def __init__(self, projects_base_path, parent=None):
        super().__init__(parent)
        self.projects_base_path = projects_base_path
        self.setWindowTitle("New Project")
        self.setModal(True)
        self.resize(640, 420)
        self._page_titles = [
            "Step 1 of 3: RIS import",
            "Step 2 of 3: Project details",
            "Step 3 of 3: Project folders",
        ]
        self.imported_provenance = {}
        self.folder_selection_pages = {}
        self.folder_selection_checkboxes = {}
        self.folder_selection_state = {"scriptural": set(), "general": set()}
        self._build_ui()
        self._update_page_state()

    def _build_ui(self):
        layout = qtw.QVBoxLayout(self)
        layout.setSpacing(10)

        intro_label = qtw.QLabel(
            "Create a new project from the current trimmed manifest. You can also load provenance from JSON, RIS, TXT, or CSV before creation starts."
        )
        intro_label.setWordWrap(True)
        layout.addWidget(intro_label)

        self.page_title_label = qtw.QLabel("")
        layout.addWidget(self.page_title_label)

        self.page_stack = qtw.QStackedWidget(self)
        layout.addWidget(self.page_stack, 1)

        ris_page = qtw.QWidget()
        ris_layout = qtw.QVBoxLayout(ris_page)
        ris_layout.setSpacing(10)

        ris_label = qtw.QLabel("Optional: load an existing RIS file")
        ris_layout.addWidget(ris_label)

        ris_help = qtw.QLabel(
            "If you already have provenance metadata, load it here to prefill the project fields before continuing."
        )
        ris_help.setWordWrap(True)
        ris_layout.addWidget(ris_help)

        ris_row = qtw.QHBoxLayout()
        self.ris_path_edit = qtw.QLineEdit()
        self.ris_path_edit.setPlaceholderText("project.ris.json, Primo_RIS_Export.ris, or similar")
        self.ris_path_edit.setReadOnly(True)
        ris_row.addWidget(self.ris_path_edit, 1)

        self.ris_browse_button = qtw.QPushButton("Load RIS...")
        self.ris_browse_button.clicked.connect(self._browse_for_ris)
        ris_row.addWidget(self.ris_browse_button)

        self.ris_clear_button = qtw.QPushButton("Clear RIS")
        self.ris_clear_button.clicked.connect(self._clear_ris)
        ris_row.addWidget(self.ris_clear_button)

        ris_layout.addLayout(ris_row)

        self.status_label = qtw.QLabel("")
        self.status_label.setWordWrap(True)
        ris_layout.addWidget(self.status_label)

        ris_layout.addStretch(1)
        self.page_stack.addWidget(ris_page)

        details_page = qtw.QWidget()
        details_layout = qtw.QVBoxLayout(details_page)
        details_layout.setSpacing(10)

        details_label = qtw.QLabel("Project details")
        details_layout.addWidget(details_label)

        self.project_name_label = qtw.QLabel("Project name")
        self.project_name_edit = qtw.QLineEdit()
        self.project_name_edit.setPlaceholderText("Erasmus1523")
        details_layout.addWidget(self.project_name_label)
        details_layout.addWidget(self.project_name_edit)

        self.project_name_hint_label = qtw.QLabel("")
        self.project_name_hint_label.setWordWrap(True)
        details_layout.addWidget(self.project_name_hint_label)

        self.project_purpose_label = qtw.QLabel("Project purpose")
        self.project_purpose_edit = qtw.QPlainTextEdit()
        self.project_purpose_edit.setPlaceholderText("Create a readable text version of the source file with duplicate font")
        self.project_purpose_edit.setFixedHeight(72)
        details_layout.addWidget(self.project_purpose_label)
        details_layout.addWidget(self.project_purpose_edit)

        project_scope_row = qtw.QHBoxLayout()
        project_scope_column = qtw.QVBoxLayout()
        project_scope_column.addWidget(qtw.QLabel("Project type"))
        self.project_type_combo = qtw.QComboBox()
        self.project_type_combo.addItems(["Scriptural", "Secular"])
        self.project_type_combo.setCurrentText("Scriptural")
        project_scope_column.addWidget(self.project_type_combo)
        project_scope_row.addLayout(project_scope_column)

        scripture_scope_column = qtw.QVBoxLayout()
        scripture_scope_column.addWidget(qtw.QLabel("Scriptural source"))
        self.scriptural_source_combo = qtw.QComboBox()
        self.scriptural_source_combo.addItems(["both", "OT", "NT"])
        self.scriptural_source_combo.setCurrentText("both")
        scripture_scope_column.addWidget(self.scriptural_source_combo)
        project_scope_row.addLayout(scripture_scope_column)
        details_layout.addLayout(project_scope_row)

        page_model_group = qtw.QGroupBox("Source page model")
        page_model_layout = qtw.QGridLayout(page_model_group)
        page_model_layout.addWidget(qtw.QLabel("Source pages"), 0, 0)
        self.source_pages_spin = qtw.QSpinBox()
        self.source_pages_spin.setRange(1, 1000000)
        self.source_pages_spin.setValue(1)
        page_model_layout.addWidget(self.source_pages_spin, 0, 1)

        page_model_layout.addWidget(qtw.QLabel("Columns per source page"), 1, 0)
        self.columns_per_page_spin = qtw.QSpinBox()
        self.columns_per_page_spin.setRange(1, len(self.DEFAULT_TESSERACT_LANGUAGES))
        self.columns_per_page_spin.setValue(len(self.DEFAULT_TESSERACT_LANGUAGES))
        page_model_layout.addWidget(self.columns_per_page_spin, 1, 1)

        self.column_preview_label = qtw.QLabel("")
        self.column_preview_label.setWordWrap(True)
        page_model_layout.addWidget(self.column_preview_label, 2, 0, 1, 2)
        details_layout.addWidget(page_model_group)

        self.user_intent_label = qtw.QLabel("User intent summary")
        self.user_intent_edit = qtw.QPlainTextEdit()
        self.user_intent_edit.setPlaceholderText("Describe the user intent for this project")
        self.user_intent_edit.setFixedHeight(72)
        details_layout.addWidget(self.user_intent_label)
        details_layout.addWidget(self.user_intent_edit)

        metadata_row = qtw.QHBoxLayout()

        trigger_column = qtw.QVBoxLayout()
        trigger_column.addWidget(qtw.QLabel("Creation trigger"))
        self.creation_trigger_edit = qtw.QLineEdit("MyServer_button")
        trigger_column.addWidget(self.creation_trigger_edit)
        metadata_row.addLayout(trigger_column)

        context_column = qtw.QVBoxLayout()
        context_column.addWidget(qtw.QLabel("Source context"))
        self.source_context_edit = qtw.QLineEdit("MyServer_UI")
        context_column.addWidget(self.source_context_edit)
        metadata_row.addLayout(context_column)

        details_layout.addLayout(metadata_row)

        details_layout.addWidget(qtw.QLabel("Creator (optional)"))
        self.creator_edit = qtw.QLineEdit()
        self.creator_edit.setPlaceholderText("Optional")
        details_layout.addWidget(self.creator_edit)

        details_layout.addWidget(qtw.QLabel("Review"))
        self.review_label = qtw.QLabel("")
        self.review_label.setWordWrap(True)
        details_layout.addWidget(self.review_label)

        self.details_status_label = qtw.QLabel("")
        self.details_status_label.setWordWrap(True)
        details_layout.addWidget(self.details_status_label)

        details_layout.addStretch(1)
        self.page_stack.addWidget(details_page)

        folder_selection_page = qtw.QWidget()
        folder_selection_layout = qtw.QVBoxLayout(folder_selection_page)
        folder_selection_layout.setSpacing(10)

        folder_selection_label = qtw.QLabel("Choose project folders")
        folder_selection_layout.addWidget(folder_selection_label)

        folder_selection_help = qtw.QLabel(
            "The defaults below are already preselected. You can keep the current selection and continue with Next."
        )
        folder_selection_help.setWordWrap(True)
        folder_selection_layout.addWidget(folder_selection_help)

        self.folder_selection_stack = qtw.QStackedWidget(self)
        folder_selection_layout.addWidget(self.folder_selection_stack, 1)

        self._build_folder_selection_page("scriptural", "Scriptural project folders")
        self._build_folder_selection_page("general", "General project folders")

        self.page_stack.addWidget(folder_selection_page)

        button_row = qtw.QHBoxLayout()
        self.back_button = qtw.QPushButton("Back")
        self.back_button.clicked.connect(self._go_back)
        button_row.addWidget(self.back_button)

        self.next_button = qtw.QPushButton("Next")
        self.next_button.clicked.connect(self._go_next)
        button_row.addWidget(self.next_button)

        button_row.addStretch(1)
        self.cancel_button = qtw.QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_row.addWidget(self.cancel_button)

        self.create_button = qtw.QPushButton("Create Project")
        self.create_button.clicked.connect(self._attempt_accept)
        button_row.addWidget(self.create_button)
        layout.addLayout(button_row)

        self.project_name_edit.textChanged.connect(self._update_validation_state)
        self.project_purpose_edit.textChanged.connect(self._update_validation_state)
        self.user_intent_edit.textChanged.connect(self._update_validation_state)
        self.creation_trigger_edit.textChanged.connect(self._update_validation_state)
        self.source_context_edit.textChanged.connect(self._update_validation_state)
        self.creator_edit.textChanged.connect(self._update_validation_state)
        self.project_type_combo.currentIndexChanged.connect(self._update_project_scope_state)
        self.scriptural_source_combo.currentIndexChanged.connect(self._refresh_folder_selection_page)
        self.source_pages_spin.valueChanged.connect(self._refresh_column_preview)
        self.columns_per_page_spin.valueChanged.connect(self._refresh_column_preview)
        self.project_type_combo.currentIndexChanged.connect(self._refresh_column_preview)
        self._update_project_scope_state()
        self._refresh_column_preview()

    def _go_back(self):
        index = self.page_stack.currentIndex()
        if index > 0:
            self.page_stack.setCurrentIndex(index - 1)
            self._update_page_state()

    def _go_next(self):
        index = self.page_stack.currentIndex()
        if index < self.page_stack.count() - 1:
            self.page_stack.setCurrentIndex(index + 1)
            self._update_page_state()

    def _update_page_state(self):
        index = self.page_stack.currentIndex()
        self.page_title_label.setText(self._page_titles[index])
        self.back_button.setEnabled(index > 0)
        self.next_button.setVisible(index < self.page_stack.count() - 1)
        self.create_button.setVisible(index == self.page_stack.count() - 1)
        self._update_validation_state()

    def _required_field_errors(self):
        errors = []
        if not self.project_name_edit.text().strip():
            errors.append("Project name is required.")
        if not self.project_purpose_edit.toPlainText().strip():
            errors.append("Project purpose is required.")
        if not self.user_intent_edit.toPlainText().strip():
            errors.append("User intent summary is required.")
        return errors

    def _update_project_scope_state(self):
        project_type = self.project_type_combo.currentText().strip()
        scripture_enabled = project_type.lower() == "scriptural"
        self.scriptural_source_combo.setEnabled(scripture_enabled)
        self.columns_per_page_spin.setEnabled(scripture_enabled)
        if scripture_enabled:
            self.columns_per_page_spin.setRange(1, len(self.DEFAULT_TESSERACT_LANGUAGES))
        else:
            self.columns_per_page_spin.setRange(1, 1)
            self.columns_per_page_spin.setValue(1)
        self._refresh_review()
        self._refresh_folder_selection_page()
        self._refresh_column_preview()
        self._update_validation_state()

    def _update_validation_state(self):
        errors = self._required_field_errors()
        entered_name = self.project_name_edit.text().strip()
        sanitized_name = self._sanitize_project_name(entered_name)
        self._refresh_review()
        self._apply_required_field_state(self.project_name_edit, self.project_name_label, not self.project_name_edit.text().strip())
        self._apply_required_field_state(self.project_purpose_edit, self.project_purpose_label, not self.project_purpose_edit.toPlainText().strip())
        self._apply_required_field_state(self.user_intent_edit, self.user_intent_label, not self.user_intent_edit.toPlainText().strip())

        if not entered_name:
            self.project_name_hint_label.setText("Enter the project name you want to create.")
            self.project_name_hint_label.setStyleSheet("")
        elif sanitized_name != entered_name:
            self.project_name_hint_label.setText(f"Project will be created as: {sanitized_name}")
            self.project_name_hint_label.setStyleSheet("color: #8a6d1f;")
        else:
            self.project_name_hint_label.setText(f"Project will be created as: {sanitized_name}")
            self.project_name_hint_label.setStyleSheet("color: #2f6b3b;")

        if errors:
            self.details_status_label.setText("Complete the required fields before creating the project.")
            self.details_status_label.setStyleSheet("color: #9f3a38;")
        else:
            self.details_status_label.setText("Required fields are complete. Review the summary and create the project when ready.")
            self.details_status_label.setStyleSheet("color: #2f6b3b;")

        self.create_button.setEnabled(not errors)

    def _apply_required_field_state(self, widget, label, is_missing):
        if is_missing:
            label.setStyleSheet("color: #9f3a38;")
            widget.setStyleSheet("border: 1px solid #9f3a38;")
        else:
            label.setStyleSheet("")
            widget.setStyleSheet("")

    def _attempt_accept(self):
        errors = self._required_field_errors()
        if errors:
            self._update_validation_state()
            return
        self.accept()

    def _sanitize_project_name(self, name):
        stripped = name.strip()
        if not stripped:
            return ""
        return re.sub(r"[^A-Za-z0-9_. -]+", "_", stripped).strip(" .")

    def _build_folder_selection_page(self, page_key, title):
        page = qtw.QWidget()
        layout = qtw.QVBoxLayout(page)
        layout.setSpacing(6)
        layout.addWidget(qtw.QLabel(title))

        scroll_area = qtw.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = qtw.QWidget()
        scroll_layout = qtw.QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(4)
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area, 1)

        self.folder_selection_pages[page_key] = scroll_content
        self.folder_selection_checkboxes[page_key] = []
        self.folder_selection_stack.addWidget(page)

    def _refresh_folder_selection_page(self):
        project_type = self.project_type_combo.currentText().strip()
        page_key = "scriptural" if project_type.lower() == "scriptural" else "general"
        self.folder_selection_stack.setCurrentWidget(self.folder_selection_stack.widget(0 if page_key == "scriptural" else 1))
        self._populate_folder_selection_page(page_key)

    def _populate_folder_selection_page(self, page_key):
        container = self.folder_selection_pages.get(page_key)
        if container is None:
            return

        for checkbox in self.folder_selection_checkboxes.get(page_key, []):
            checkbox.deleteLater()
        self.folder_selection_checkboxes[page_key] = []

        layout = container.layout()
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        available_entries = self._folder_selection_entries(page_key)
        if not available_entries:
            empty_label = qtw.QLabel("No folder options are available for the current selection.")
            layout.addWidget(empty_label)
            return

        for entry in available_entries:
            checkbox = qtw.QCheckBox(entry)
            checkbox.setChecked(entry in self.folder_selection_state.get(page_key, set()))
            checkbox.toggled.connect(lambda checked, entry=entry: self._toggle_folder_selection(page_key, entry, checked))
            self.folder_selection_checkboxes[page_key].append(checkbox)
            layout.addWidget(checkbox)

        self._apply_default_folder_selection_state(page_key, available_entries)

    def _apply_default_folder_selection_state(self, page_key, available_entries):
        current_selection = self.folder_selection_state.get(page_key)
        if current_selection:
            return
        default_selection = set(available_entries)
        self.folder_selection_state[page_key] = default_selection
        for checkbox in self.folder_selection_checkboxes.get(page_key, []):
            checkbox.setChecked(checkbox.text() in default_selection)

    def _toggle_folder_selection(self, page_key, entry, checked):
        selection = self.folder_selection_state.setdefault(page_key, set())
        if checked:
            selection.add(entry)
        else:
            selection.discard(entry)

    def _folder_selection_entries(self, page_key):
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        if page_key == "scriptural":
            template_path = os.path.join(repo_root, "ViewController", "ScriptureProjectFolderList.txt")
        else:
            template_path = os.path.join(repo_root, "ViewController", "GeneralProjectFolderList.txt")

        if not os.path.exists(template_path):
            return []

        entries = []
        with open(template_path, "r", encoding="utf-8-sig") as handle:
            for raw_line in handle:
                candidate = raw_line.strip()
                if not candidate:
                    continue
                normalized = candidate.replace("\\", "/").strip()
                if not normalized:
                    continue
                source_choice = self._normalized_scriptural_source_choice()
                if page_key == "scriptural" and not self._scriptural_source_allows_entry(normalized, source_choice):
                    continue
                source_entry, destination_entry = self._split_structure_copy_entry(normalized)
                candidate_path = destination_entry or source_entry
                if not candidate_path:
                    continue
                candidate_path = candidate_path.strip()
                if candidate_path.endswith(".py") or candidate_path.endswith(".txt") or candidate_path.endswith(".md") or candidate_path.endswith(".json") or candidate_path.endswith(".csv") or candidate_path.endswith(".ui") or candidate_path.endswith(".qrc") or candidate_path.endswith(".rtf") or candidate_path.endswith(".xml"):
                    continue
                if candidate_path.startswith("Model/Project/Images") or candidate_path.startswith("Model/Project/Text") or candidate_path.startswith("Model/Project/Data") or candidate_path.startswith("Model/"):
                    entries.append(candidate_path)

        if page_key == "scriptural":
            scripture_source = self._normalized_scriptural_source_choice()
            if scripture_source == "old_testament" and not self._has_scriptural_book_folder_mapping(entries, "Model/OT_BookFolders"):
                entries.append("Model/OT_BookFolders")
            elif scripture_source == "new_testament" and not self._has_scriptural_book_folder_mapping(entries, "Model/NT_BookFolders"):
                entries.append("Model/NT_BookFolders")
            else:
                if not self._has_scriptural_book_folder_mapping(entries, "Model/OT_BookFolders"):
                    entries.append("Model/OT_BookFolders")
                if not self._has_scriptural_book_folder_mapping(entries, "Model/NT_BookFolders"):
                    entries.append("Model/NT_BookFolders")

        entries = list(dict.fromkeys(entries))
        return sorted(entries)

    def _has_scriptural_book_folder_mapping(self, entries, source_root):
        for entry in entries:
            source_entry, destination_entry = self._split_structure_copy_entry(entry)
            if source_entry == source_root and destination_entry:
                return True
        return False

    def _normalized_scriptural_source_choice(self):
        scripture_source = self.scriptural_source_combo.currentText().strip()
        if scripture_source == "OT":
            return "old_testament"
        if scripture_source == "NT":
            return "new_testament"
        return "both"

    def _scriptural_source_allows_entry(self, entry, source_choice):
        source_entry, _destination_entry = self._split_structure_copy_entry(entry)
        if source_entry == "Model/OT_BookFolders":
            return source_choice in {"old_testament", "both"}
        if source_entry == "Model/NT_BookFolders":
            return source_choice in {"new_testament", "both"}
        return True

    def _split_structure_copy_entry(self, entry):
        if "=>" not in entry:
            return entry.strip(), None
        source_entry, destination_entry = entry.split("=>", 1)
        source_entry = source_entry.strip()
        destination_entry = destination_entry.strip()
        if not source_entry or not destination_entry:
            return entry.strip(), None
        return source_entry, destination_entry

    def _refresh_review(self):
        creator = self.creator_edit.text().strip() or "Not set"
        entered_name = self.project_name_edit.text().strip()
        sanitized_name = self._sanitize_project_name(entered_name) or "Not set"
        name_line = f"Project name: {entered_name or 'Not set'}"
        if entered_name and sanitized_name != entered_name:
            name_line += f" -> {sanitized_name}"
        project_type = self.project_type_combo.currentText().strip() or "Scriptural"
        scripture_source = self.scriptural_source_combo.currentText().strip() or "both"
        source_pages = int(self.source_pages_spin.value())
        columns_per_page = int(self.columns_per_page_spin.value())
        selected_languages = self._selected_column_languages()
        total_column_pages = source_pages * max(1, columns_per_page)
        review_lines = [
            name_line,
            f"Purpose: {self.project_purpose_edit.toPlainText().strip() or 'Not set'}",
            f"Intent: {self.user_intent_edit.toPlainText().strip() or 'Not set'}",
            f"Project type: {project_type}",
            f"Scriptural source: {scripture_source}",
            f"Source pages: {source_pages}",
            f"Columns per source page: {columns_per_page}",
            f"Column languages: {', '.join(selected_languages)}",
            f"Total column pages: {total_column_pages}",
            f"Trigger: {self.creation_trigger_edit.text().strip() or 'MyServer_button'}",
            f"Source context: {self.source_context_edit.text().strip() or 'MyServer_UI'}",
            f"Creator: {creator}",
        ]
        self.review_label.setText("\n".join(review_lines))

    def _selected_column_languages(self):
        count = max(1, int(self.columns_per_page_spin.value()))
        return self.DEFAULT_TESSERACT_LANGUAGES[:count]

    def _refresh_column_preview(self):
        selected_languages = self._selected_column_languages()
        named_columns = [f"Column {index + 1}: {language}" for index, language in enumerate(selected_languages)]
        source_pages = int(self.source_pages_spin.value())
        columns_per_page = max(1, int(self.columns_per_page_spin.value()))
        total_column_pages = source_pages * columns_per_page
        self.column_preview_label.setText(
            "\n".join([
                "Columns are automatically named from the selected language list:",
                *named_columns,
                f"Total column pages = source pages ({source_pages}) x columns per page ({columns_per_page}) = {total_column_pages}",
            ])
        )
        self._refresh_review()

    def _browse_for_ris(self):
        path, _ = qtw.QFileDialog.getOpenFileName(
            self,
            "Select Provenance File",
            self.projects_base_path,
            "Provenance files (*.json *.ris *.txt *.csv);;JSON files (*.json);;RIS text files (*.ris *.txt);;CSV files (*.csv);;All Files (*.*)",
        )
        if not path:
            return

        try:
            payload = self._load_provenance_file(path)
        except (OSError, ValueError, json.JSONDecodeError, csv.Error) as exc:
            qtw.QMessageBox.warning(self, "Load Provenance", f"Could not load provenance file.\n\n{exc}")
            return

        self.ris_path_edit.setText(path)
        self._apply_ris_payload(payload)
        self.status_label.setText("Provenance loaded. You can adjust any field before creating the project.")
        self.page_stack.setCurrentIndex(1)
        self._update_page_state()

    def _clear_ris(self):
        self.ris_path_edit.clear()
        self.imported_provenance = {}
        self.status_label.setText("Imported provenance cleared. Continue with manual entry.")

    def _apply_ris_payload(self, payload):
        self.imported_provenance = {
            key: value
            for key, value in payload.items()
            if key not in {
                "project_name",
                "project_purpose",
                "creation_trigger",
                "source_context",
                "user_intent_summary",
                "creator",
            }
        }

        if not self.project_name_edit.text().strip():
            self.project_name_edit.setText(str(payload.get("project_name", "")))
        if not self.project_purpose_edit.toPlainText().strip():
            self.project_purpose_edit.setPlainText(str(payload.get("project_purpose", "")))
        if not self.user_intent_edit.toPlainText().strip():
            self.user_intent_edit.setPlainText(str(payload.get("user_intent_summary", "")))
        project_type = payload.get("ProjectType") or payload.get("project_type") or payload.get("projectType")
        if project_type:
            project_type_text = str(project_type).strip()
            if project_type_text.lower() in {"scriptural", "scripture"}:
                self.project_type_combo.setCurrentText("Scriptural")
            elif project_type_text.lower() in {"secular", "general"}:
                self.project_type_combo.setCurrentText("Secular")
        scriptural_source = payload.get("ScripturalSource") or payload.get("scriptural_source") or payload.get("scripturalSource")
        if scriptural_source:
            source_value = str(scriptural_source).strip().lower()
            if source_value in {"ot", "old", "old_testament", "old-testament"}:
                self.scriptural_source_combo.setCurrentText("OT")
            elif source_value in {"nt", "new", "new_testament", "new-testament"}:
                self.scriptural_source_combo.setCurrentText("NT")
            else:
                self.scriptural_source_combo.setCurrentText("both")
        self.creation_trigger_edit.setText(str(payload.get("creation_trigger", "MyServer_button")))
        self.source_context_edit.setText(str(payload.get("source_context", "MyServer_UI")))
        if payload.get("creator") and not self.creator_edit.text().strip():
            self.creator_edit.setText(str(payload.get("creator", "")))
        self._refresh_review()

    def _load_provenance_file(self, path):
        extension = os.path.splitext(path)[1].lower()
        if extension == ".json":
            payload = self._load_json_provenance(path)
        elif extension == ".csv":
            payload = self._load_csv_provenance(path)
        elif extension in {".ris", ".txt"}:
            payload = self._load_text_provenance(path)
        else:
            raise ValueError(f"Unsupported provenance file type: {extension}")

        payload.setdefault("creation_trigger", "MyServer_button")
        payload.setdefault("source_context", "MyServer_UI")
        payload.setdefault("user_intent_summary", "Create project using imported provenance")
        payload.setdefault("project_name", self._project_name_from_source(path, payload))
        payload.setdefault("project_purpose", self._project_purpose_from_source(payload))
        payload["source_provenance_path"] = path
        return payload

    def _load_json_provenance(self, path):
        with open(path, "r", encoding="utf-8-sig") as handle:
            payload = json.load(handle)
        if isinstance(payload, list):
            if not payload:
                raise ValueError("JSON provenance file is empty.")
            payload = payload[0]
        if not isinstance(payload, dict):
            raise ValueError("JSON provenance file must contain an object.")
        payload = dict(payload)
        payload.setdefault("source_provenance_format", "json")
        return payload

    def _load_csv_provenance(self, path):
        with open(path, "r", encoding="utf-8-sig", newline="") as handle:
            sample = handle.read()
        if not sample.strip():
            raise ValueError("CSV provenance file is empty.")

        rows = list(csv.reader(sample.splitlines()))
        if not rows:
            raise ValueError("CSV provenance file is empty.")

        payload = {"source_provenance_format": "csv"}
        normalized_rows = [row for row in rows if any(cell.strip() for cell in row)]
        if not normalized_rows:
            raise ValueError("CSV provenance file is empty.")

        is_key_value = all(len(row) >= 2 for row in normalized_rows) and any(
            row[0].strip().lower() in {
                "project_name", "project_purpose", "title", "creator", "author", "user_intent_summary", "source_context", "creation_trigger"
            }
            for row in normalized_rows
        )

        if is_key_value:
            for row in normalized_rows:
                key = row[0].strip()
                value = row[1].strip() if len(row) > 1 else ""
                if key:
                    payload[key] = value
        else:
            with open(path, "r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                first_row = next(reader, None)
            if not first_row:
                raise ValueError("CSV provenance file must contain at least one data row.")
            payload.update({key: value for key, value in first_row.items() if key})

        return self._normalize_imported_payload(payload)

    def _load_text_provenance(self, path):
        with open(path, "r", encoding="utf-8-sig") as handle:
            text = handle.read()
        if not text.strip():
            raise ValueError("Text provenance file is empty.")

        stripped = text.lstrip()
        if stripped.startswith("{"):
            payload = json.loads(text)
            if not isinstance(payload, dict):
                raise ValueError("JSON text provenance file must contain an object.")
            payload = dict(payload)
            payload.setdefault("source_provenance_format", "json-text")
            return payload

        if self._looks_like_ris_text(text):
            return self._parse_ris_text(text)

        payload = self._parse_key_value_text(text)
        if payload:
            payload.setdefault("source_provenance_format", "text-key-value")
            return self._normalize_imported_payload(payload)

        return {
            "source_provenance_format": "plain-text",
            "source_provenance_raw_text": text,
        }

    def _looks_like_ris_text(self, text):
        return bool(re.search(r"^([A-Z0-9]{2})\s{1,2}-\s", text, re.MULTILINE))

    def _parse_ris_text(self, text):
        tags = {}
        current_tag = None
        for raw_line in text.splitlines():
            line = raw_line.rstrip()
            if not line.strip():
                continue
            match = re.match(r"^([A-Z0-9]{2})\s{1,2}-\s(.*)$", line)
            if match:
                current_tag = match.group(1)
                tags.setdefault(current_tag, []).append(match.group(2).strip())
            elif current_tag is not None:
                tags[current_tag][-1] = (tags[current_tag][-1] + " " + line.strip()).strip()

        payload = {
            "source_provenance_format": "ris",
            "source_provenance_tags": tags,
        }
        if tags.get("T1"):
            payload["title"] = tags["T1"][0]
        elif tags.get("TI"):
            payload["title"] = tags["TI"][0]
        if tags.get("AU"):
            payload["authors"] = tags["AU"]
        if tags.get("A1"):
            payload.setdefault("authors", tags["A1"])
        if tags.get("Y1"):
            payload["publication_year"] = tags["Y1"][0]
        elif tags.get("PY"):
            payload["publication_year"] = tags["PY"][0]
        if tags.get("DO"):
            payload["doi"] = tags["DO"][0]
        if tags.get("PB"):
            payload["publisher"] = tags["PB"][0]
        if tags.get("CY"):
            payload["publication_place"] = tags["CY"][0]
        if tags.get("ID"):
            payload["source_identifier"] = tags["ID"][0]
        return self._normalize_imported_payload(payload)

    def _parse_key_value_text(self, text):
        payload = {}
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            match = re.match(r"^([^:=\t]+)\s*[:=\t]\s*(.+)$", line)
            if not match:
                continue
            key = match.group(1).strip()
            value = match.group(2).strip()
            if key:
                payload[key] = value
        return payload

    def _normalize_imported_payload(self, payload):
        normalized = dict(payload)
        lowered = {str(key).strip().lower(): value for key, value in payload.items()}

        title = lowered.get("title") or lowered.get("t1") or lowered.get("ti")
        if title:
            normalized.setdefault("project_purpose", str(title))

        project_name = lowered.get("project_name") or lowered.get("name")
        if project_name:
            normalized.setdefault("project_name", str(project_name))

        creator = lowered.get("creator")
        if creator:
            normalized.setdefault("creator", str(creator))

        intent = lowered.get("user_intent_summary") or lowered.get("intent")
        if intent:
            normalized.setdefault("user_intent_summary", str(intent))

        source_context = lowered.get("source_context")
        if source_context:
            normalized.setdefault("source_context", str(source_context))

        creation_trigger = lowered.get("creation_trigger")
        if creation_trigger:
            normalized.setdefault("creation_trigger", str(creation_trigger))

        return normalized

    def _project_name_from_source(self, path, payload):
        title = payload.get("title") or payload.get("project_name") or ""
        if title:
            sanitized = re.sub(r"[^A-Za-z0-9_. -]+", "_", str(title)).strip(" .")
            if sanitized:
                words = sanitized.split()
                if len(words) > 6:
                    sanitized = " ".join(words[:6])
                return sanitized
        return os.path.splitext(os.path.basename(path))[0]

    def _project_purpose_from_source(self, payload):
        title = payload.get("title") or payload.get("project_purpose")
        if title:
            return str(title)
        return "Create project using imported provenance"

    def get_payload(self):
        sanitized_name = self._sanitize_project_name(self.project_name_edit.text())
        scriptural_source = self.scriptural_source_combo.currentText().strip()
        if scriptural_source == "OT":
            scriptural_source = "old_testament"
        elif scriptural_source == "NT":
            scriptural_source = "new_testament"
        elif scriptural_source == "both":
            scriptural_source = "both"

        selected_languages = self._selected_column_languages()
        number_columns = max(1, int(self.columns_per_page_spin.value()))
        number_pages = max(1, int(self.source_pages_spin.value()))
        payload = {
            "project_name": sanitized_name,
            "project_purpose": self.project_purpose_edit.toPlainText().strip(),
            "creation_trigger": self.creation_trigger_edit.text().strip() or "MyServer_button",
            "source_context": self.source_context_edit.text().strip() or "MyServer_UI",
            "user_intent_summary": self.user_intent_edit.toPlainText().strip(),
            "ProjectType": self.project_type_combo.currentText().strip(),
            "ScripturalSource": scriptural_source,
            "NumberPages": number_pages,
            "NumberColumns": number_columns,
            "ColumnName": ",".join(selected_languages),
            "ColumnLanguage": ",".join(language.lower() for language in selected_languages),
            "Languages": [language.lower() for language in selected_languages],
            "NumberLanguages": len(selected_languages),
            "TotalColumnPages": number_pages * number_columns,
            "SelectedProjectFolders": self._selected_project_folders(),
        }
        creator = self.creator_edit.text().strip()
        if creator:
            payload["creator"] = creator
        if self.imported_provenance:
            payload.update(self.imported_provenance)
        return payload

    def _selected_project_folders(self):
        project_type = self.project_type_combo.currentText().strip()
        page_key = "scriptural" if project_type.lower() == "scriptural" else "general"
        selection = self.folder_selection_state.get(page_key, set())
        if not selection:
            selection = set(self._folder_selection_entries(page_key))
        return sorted(selection)