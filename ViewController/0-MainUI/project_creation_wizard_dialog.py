import csv
import json
import os
import re

from PyQt5 import QtWidgets as qtw


class ProjectCreationWizardDialog(qtw.QDialog):
    def __init__(self, projects_base_path, parent=None):
        super().__init__(parent)
        self.projects_base_path = projects_base_path
        self.setWindowTitle("New Project")
        self.setModal(True)
        self.resize(640, 420)
        self._page_titles = [
            "Step 1 of 2: RIS import",
            "Step 2 of 2: Project details",
        ]
        self.imported_provenance = {}
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

    def _refresh_review(self):
        creator = self.creator_edit.text().strip() or "Not set"
        entered_name = self.project_name_edit.text().strip()
        sanitized_name = self._sanitize_project_name(entered_name) or "Not set"
        name_line = f"Project name: {entered_name or 'Not set'}"
        if entered_name and sanitized_name != entered_name:
            name_line += f" -> {sanitized_name}"
        review_lines = [
            name_line,
            f"Purpose: {self.project_purpose_edit.toPlainText().strip() or 'Not set'}",
            f"Intent: {self.user_intent_edit.toPlainText().strip() or 'Not set'}",
            f"Trigger: {self.creation_trigger_edit.text().strip() or 'MyServer_button'}",
            f"Source context: {self.source_context_edit.text().strip() or 'MyServer_UI'}",
            f"Creator: {creator}",
        ]
        self.review_label.setText("\n".join(review_lines))

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
        payload = {
            "project_name": sanitized_name,
            "project_purpose": self.project_purpose_edit.toPlainText().strip(),
            "creation_trigger": self.creation_trigger_edit.text().strip() or "MyServer_button",
            "source_context": self.source_context_edit.text().strip() or "MyServer_UI",
            "user_intent_summary": self.user_intent_edit.toPlainText().strip(),
        }
        creator = self.creator_edit.text().strip()
        if creator:
            payload["creator"] = creator
        if self.imported_provenance:
            payload.update(self.imported_provenance)
        return payload