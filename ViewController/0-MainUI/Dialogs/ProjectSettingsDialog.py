import base64
import csv
import hashlib
import json
import os
import re
import sqlite3
import time

from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5 import QtWidgets as qtw


PROJECT_SETTINGS_DB_NAME = "Project Settings.db"
PROJECT_SETTINGS_SESSION_FILE = "Session.json"
PROJECT_SETTINGS_TAB_KEY = "self.project_settings_active_tab"
PROJECT_SETTINGS_GEOMETRY_KEY = "self.project_settings_dialog_geometry"
FIELD_KEY_ROLE = qtc.Qt.UserRole + 1

RIS_FIELD_SPECS = [
    ("project_name", "Project Name", "Local project identifier."),
    ("project_purpose", "Project Purpose", "Why this project exists."),
    ("creation_trigger", "Creation Trigger", "What initiated project creation or provenance capture."),
    ("source_context", "Source Context", "Source UI or workflow context for the project."),
    ("user_intent_summary", "User Intent Summary", "Short statement of the project goal."),
    ("creator", "Creator", "Person responsible for the project or provenance record."),
    ("source_provenance_path", "Source Provenance Path", "Original path of an imported provenance file, if any."),
    ("source_provenance_format", "Source Provenance Format", "Imported provenance format such as json, ris, txt, or csv."),
    ("reference_type", "Reference Type (TY)", "RIS type of reference."),
    ("title", "Title (TI/T1)", "Primary title of the work."),
    ("secondary_title", "Secondary Title (T2)", "Journal, book, or container title."),
    ("tertiary_title", "Tertiary Title (T3)", "Series title or tertiary title."),
    ("authors_primary", "Primary Authors (A1/AU)", "Primary authors; separate multiple values with ';'."),
    ("authors_secondary", "Secondary Authors (A2)", "Secondary authors or editors; separate multiple values with ';'."),
    ("authors_tertiary", "Tertiary Authors (A3)", "Tertiary authors; separate multiple values with ';'."),
    ("authors_subsidiary", "Subsidiary Authors (A4)", "Subsidiary authors; separate multiple values with ';'."),
    ("editor", "Editor (ED)", "Editor names; separate multiple values with ';'."),
    ("year", "Year (PY/Y1)", "Publication year."),
    ("date_secondary", "Secondary Date (Y2)", "Secondary or access date."),
    ("journal", "Journal (JO/JF)", "Journal or periodical title."),
    ("journal_abbrev", "Journal Abbrev (JA/J2)", "Abbreviated journal title."),
    ("volume", "Volume (VL)", "Volume number."),
    ("issue", "Issue (IS)", "Issue number."),
    ("start_page", "Start Page (SP)", "Starting page."),
    ("end_page", "End Page (EP)", "Ending page."),
    ("publisher", "Publisher (PB)", "Publisher name."),
    ("place_published", "Place Published (CY)", "Place of publication."),
    ("issn_isbn", "ISSN/ISBN (SN)", "Serial or book identifier."),
    ("doi", "DOI (DO)", "Digital object identifier."),
    ("url", "URL (UR)", "Canonical URL for the resource."),
    ("language", "Language (LA)", "Language code or language name."),
    ("keywords", "Keywords (KW)", "Keywords; separate multiple values with ';'."),
    ("abstract", "Abstract (AB)", "Abstract or summary text."),
    ("notes", "Notes (N1)", "General notes."),
    ("type_of_work", "Type of Work (M3)", "Type, medium, or material identifier."),
    ("edition", "Edition (ET)", "Edition statement."),
    ("accession_number", "Accession Number (ID)", "Database accession or call number."),
    ("database_name", "Database Name (DB)", "Database or service name."),
    ("attachments_file", "File Attachments (L1)", "File attachments or local file references."),
    ("attachments_full_text", "Full Text Attachments (L2)", "Full text attachment paths or URLs."),
    ("attachments_image", "Image Attachments (L4)", "Image attachment paths or URLs."),
    ("website_link", "Website Link (LK)", "Related website link."),
    ("research_notes", "Research Notes (RN)", "Researcher notes."),
    ("custom_1", "Custom 1 (C1)", "Custom field 1."),
    ("custom_2", "Custom 2 (C2)", "Custom field 2."),
    ("custom_3", "Custom 3 (C3)", "Custom field 3."),
    ("custom_4", "Custom 4 (C4)", "Custom field 4."),
    ("custom_5", "Custom 5 (C5)", "Custom field 5."),
    ("ris_version", "RIS Version", "Local RIS record version."),
    ("timestamp", "Timestamp", "Last RIS update timestamp."),
    ("_locked", "Locked", "Whether the RIS record is considered locked."),
    ("_hash", "Hash", "Computed integrity hash for the RIS payload."),
]

RIS_TAG_TO_FIELD_KEY = {
    "TY": "reference_type",
    "T1": "title",
    "TI": "title",
    "T2": "secondary_title",
    "JO": "journal",
    "JF": "journal",
    "T3": "tertiary_title",
    "A1": "authors_primary",
    "AU": "authors_primary",
    "A2": "authors_secondary",
    "A3": "authors_tertiary",
    "A4": "authors_subsidiary",
    "ED": "editor",
    "PY": "year",
    "Y1": "year",
    "Y2": "date_secondary",
    "JA": "journal_abbrev",
    "J2": "journal_abbrev",
    "VL": "volume",
    "IS": "issue",
    "SP": "start_page",
    "EP": "end_page",
    "PB": "publisher",
    "CY": "place_published",
    "SN": "issn_isbn",
    "DO": "doi",
    "UR": "url",
    "LA": "language",
    "KW": "keywords",
    "AB": "abstract",
    "N1": "notes",
    "M3": "type_of_work",
    "ET": "edition",
    "ID": "accession_number",
    "DB": "database_name",
    "L1": "attachments_file",
    "L2": "attachments_full_text",
    "L4": "attachments_image",
    "LK": "website_link",
    "RN": "research_notes",
    "C1": "custom_1",
    "C2": "custom_2",
    "C3": "custom_3",
    "C4": "custom_4",
    "C5": "custom_5",
}

MULTI_VALUE_RIS_FIELDS = {
    "authors_primary",
    "authors_secondary",
    "authors_tertiary",
    "authors_subsidiary",
    "editor",
    "keywords",
}

PROVENANCE_SEARCH_DIRS = (
    "",
    os.path.join("Model", "Project", "Data"),
    os.path.join("Project", "Data"),
)


class ProjectSettingsStore:
    def __init__(self, project_root):
        self.project_root = os.path.abspath(project_root)
        self.sqlite_dir = os.path.join(self.project_root, "Model", "Project", "Data", "SQLite")
        self.db_path = os.path.join(self.sqlite_dir, PROJECT_SETTINGS_DB_NAME)
        self.ris_json_path = os.path.join(self.project_root, "project.ris.json")
        self.last_loaded_provenance_source = ""

    def load_ris_values(self):
        self.last_loaded_provenance_source = ""
        values = self._default_values()
        values.update(self._load_project_imported_provenance())
        values.update(self._load_project_ris_json())
        values.update(self._load_ris_table())
        values.setdefault("project_name", os.path.basename(self.project_root))
        values.setdefault("ris_version", "1.1")
        values.setdefault("_locked", True)
        values.setdefault("timestamp", time.time())
        values["_hash"] = self._hash_ris(values)
        return values

    def save_ris_values(self, values):
        payload = self._normalize_values(values)
        payload["timestamp"] = time.time()
        payload["ris_version"] = str(payload.get("ris_version") or "1.1")
        payload["_locked"] = self._coerce_bool(payload.get("_locked", True))
        payload["_hash"] = self._hash_ris(payload)

        self._ensure_database()
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ris (
                    field_key TEXT PRIMARY KEY,
                    field_value TEXT,
                    field_label TEXT,
                    field_description TEXT,
                    field_order INTEGER NOT NULL,
                    updated_at REAL NOT NULL
                )
                """
            )
            conn.execute("DELETE FROM ris")
            now = time.time()
            rows = []
            for order_index, (field_key, field_label, field_description) in enumerate(self._ordered_field_specs(payload)):
                rows.append((
                    field_key,
                    json.dumps(payload.get(field_key, ""), ensure_ascii=False),
                    field_label,
                    field_description,
                    order_index,
                    now,
                ))
            conn.executemany(
                """
                INSERT INTO ris (
                    field_key,
                    field_value,
                    field_label,
                    field_description,
                    field_order,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
            conn.commit()
        finally:
            conn.close()

        with open(self.ris_json_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)

        return payload

    def _ensure_database(self):
        os.makedirs(self.sqlite_dir, exist_ok=True)

    def _default_values(self):
        return {
            "project_name": os.path.basename(self.project_root),
            "project_purpose": "",
            "creation_trigger": "manual_edit",
            "source_context": "MyServer_UI",
            "user_intent_summary": "",
            "creator": "",
            "source_provenance_path": "",
            "source_provenance_format": "",
            "reference_type": "",
            "title": "",
            "secondary_title": "",
            "tertiary_title": "",
            "authors_primary": "",
            "authors_secondary": "",
            "authors_tertiary": "",
            "authors_subsidiary": "",
            "editor": "",
            "year": "",
            "date_secondary": "",
            "journal": "",
            "journal_abbrev": "",
            "volume": "",
            "issue": "",
            "start_page": "",
            "end_page": "",
            "publisher": "",
            "place_published": "",
            "issn_isbn": "",
            "doi": "",
            "url": "",
            "language": "",
            "keywords": "",
            "abstract": "",
            "notes": "",
            "type_of_work": "",
            "edition": "",
            "accession_number": "",
            "database_name": "",
            "attachments_file": "",
            "attachments_full_text": "",
            "attachments_image": "",
            "website_link": "",
            "research_notes": "",
            "custom_1": "",
            "custom_2": "",
            "custom_3": "",
            "custom_4": "",
            "custom_5": "",
            "ris_version": "1.1",
            "timestamp": time.time(),
            "_locked": True,
            "_hash": "",
        }

    def _load_project_imported_provenance(self):
        for candidate_path in self._candidate_provenance_paths():
            try:
                payload = self._load_provenance_file(candidate_path)
            except Exception:
                continue

            if not payload:
                continue

            payload["source_provenance_path"] = self._display_path(candidate_path)
            self.last_loaded_provenance_source = payload["source_provenance_path"]
            return payload

        return {}

    def _candidate_provenance_paths(self):
        candidates = []
        seen = set()

        for hinted_path in self._stored_provenance_paths():
            for resolved_path in self._resolve_candidate_path(hinted_path):
                normalized = os.path.normpath(resolved_path)
                if normalized in seen or not os.path.isfile(normalized):
                    continue
                seen.add(normalized)
                candidates.append(normalized)

        for relative_dir in PROVENANCE_SEARCH_DIRS:
            search_root = os.path.join(self.project_root, relative_dir)
            if not os.path.isdir(search_root):
                continue

            for root_dir, dirnames, filenames in os.walk(search_root):
                dirnames[:] = [
                    dirname for dirname in dirnames if dirname not in {".git", "__pycache__", "node_modules", "venv"}
                ]
                for filename in sorted(filenames):
                    lower_name = filename.lower()
                    if not lower_name.endswith(".ris"):
                        continue
                    path = os.path.normpath(os.path.join(root_dir, filename))
                    if path in seen or path == os.path.normpath(self.ris_json_path):
                        continue
                    seen.add(path)
                    candidates.append(path)

        return candidates

    def _stored_provenance_paths(self):
        paths = []

        json_payload = self._load_project_ris_json()
        json_path = str(json_payload.get("source_provenance_path", "")).strip()
        if json_path:
            paths.append(json_path)

        table_payload = self._load_ris_table()
        table_path = str(table_payload.get("source_provenance_path", "")).strip()
        if table_path and table_path not in paths:
            paths.append(table_path)

        return paths

    def _resolve_candidate_path(self, candidate_path):
        if not candidate_path:
            return []

        resolved = []
        normalized = os.path.normpath(candidate_path)
        resolved.append(normalized)

        if not os.path.isabs(normalized):
            resolved.append(os.path.normpath(os.path.join(self.project_root, normalized)))
        else:
            basename = os.path.basename(normalized)
            if basename:
                resolved.append(os.path.normpath(os.path.join(self.project_root, basename)))

        unique_paths = []
        seen = set()
        for path in resolved:
            if path in seen:
                continue
            seen.add(path)
            unique_paths.append(path)
        return unique_paths

    def _display_path(self, path):
        try:
            relative_path = os.path.relpath(path, self.project_root)
        except ValueError:
            return path

        if relative_path.startswith(".."):
            return path
        return relative_path.replace("\\", "/")

    def _load_project_ris_json(self):
        if not os.path.exists(self.ris_json_path):
            return {}
        with open(self.ris_json_path, "r", encoding="utf-8-sig") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}

    def _load_ris_table(self):
        if not os.path.exists(self.db_path):
            return {}

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute(
                "SELECT field_key, field_value FROM ris ORDER BY field_order ASC, field_key ASC"
            )
            values = {}
            for field_key, field_value in cursor.fetchall():
                if not field_key:
                    continue
                try:
                    values[field_key] = json.loads(field_value) if field_value is not None else ""
                except json.JSONDecodeError:
                    values[field_key] = field_value or ""
            return values
        finally:
            conn.close()

    def _load_provenance_file(self, path):
        extension = os.path.splitext(path)[1].lower()
        if extension == ".json":
            payload = self._load_json_provenance(path)
        elif extension == ".csv":
            payload = self._load_csv_provenance(path)
        elif extension in {".ris", ".txt"}:
            payload = self._load_text_provenance(path)
        else:
            raise ValueError("Unsupported provenance file type: {0}".format(extension))

        payload.setdefault("source_provenance_format", extension.lstrip(".") or "unknown")
        return payload

    def _load_json_provenance(self, path):
        with open(path, "r", encoding="utf-8-sig") as handle:
            payload = json.load(handle)
        if isinstance(payload, list):
            payload = payload[0] if payload else {}
        if not isinstance(payload, dict):
            raise ValueError("JSON provenance file must contain an object.")
        payload = dict(payload)
        payload.setdefault("source_provenance_format", "json")
        return self._normalize_imported_payload(payload)

    def _load_csv_provenance(self, path):
        with open(path, "r", encoding="utf-8-sig", newline="") as handle:
            sample = handle.read()
        if not sample.strip():
            raise ValueError("CSV provenance file is empty.")

        rows = list(csv.reader(sample.splitlines()))
        normalized_rows = [row for row in rows if any(cell.strip() for cell in row)]
        if not normalized_rows:
            raise ValueError("CSV provenance file is empty.")

        payload = {"source_provenance_format": "csv"}
        is_key_value = all(len(row) >= 2 for row in normalized_rows) and any(
            row[0].strip().lower() in {
                "project_name", "project_purpose", "title", "creator", "author", "authors", "user_intent_summary"
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
            return self._normalize_imported_payload(payload)

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
            elif current_tag is not None and tags.get(current_tag):
                tags[current_tag][-1] = (tags[current_tag][-1] + " " + line.strip()).strip()

        payload = {
            "source_provenance_format": "ris",
            "source_provenance_tags": tags,
        }
        for tag, field_key in RIS_TAG_TO_FIELD_KEY.items():
            if not tags.get(tag) or field_key in payload:
                continue

            values = tags[tag]
            if field_key in MULTI_VALUE_RIS_FIELDS:
                payload[field_key] = "; ".join(value for value in values if value)
            else:
                payload[field_key] = values[0]

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
        lowered = {str(key).strip().lower(): value for key, value in normalized.items()}

        tag_payload = normalized.get("source_provenance_tags")
        if isinstance(tag_payload, dict):
            for tag, field_key in RIS_TAG_TO_FIELD_KEY.items():
                values = tag_payload.get(tag)
                if not values or normalized.get(field_key):
                    continue
                if field_key in MULTI_VALUE_RIS_FIELDS:
                    normalized[field_key] = "; ".join(str(value) for value in values if value)
                else:
                    normalized[field_key] = str(values[0])

        alias_map = {
            "name": "project_name",
            "projectname": "project_name",
            "purpose": "project_purpose",
            "intent": "user_intent_summary",
            "author": "authors_primary",
            "authors": "authors_primary",
            "publication_year": "year",
            "publicationyear": "year",
            "publication_place": "place_published",
            "publicationplace": "place_published",
            "source_identifier": "accession_number",
            "sourceidentifier": "accession_number",
            "link": "website_link",
            "website": "website_link",
        }

        for source_key, target_key in alias_map.items():
            value = lowered.get(source_key)
            if value in {None, ""} or normalized.get(target_key):
                continue
            normalized[target_key] = self._stringify_value(value, target_key)

        title = lowered.get("title") or lowered.get("t1") or lowered.get("ti")
        if title and not normalized.get("project_purpose"):
            normalized["project_purpose"] = self._stringify_value(title, "project_purpose")

        creator = lowered.get("creator")
        if creator and not normalized.get("creator"):
            normalized["creator"] = self._stringify_value(creator, "creator")

        project_name = lowered.get("project_name") or lowered.get("name")
        if project_name and not normalized.get("project_name"):
            normalized["project_name"] = self._stringify_value(project_name, "project_name")

        return normalized

    def _normalize_values(self, values):
        normalized = {}
        for field_key, value in values.items():
            if value is None:
                normalized[field_key] = ""
                continue
            if field_key == "timestamp":
                normalized[field_key] = self._coerce_float(value, time.time())
            elif field_key == "_locked":
                normalized[field_key] = self._coerce_bool(value)
            else:
                normalized[field_key] = value
        return normalized

    def _ordered_field_specs(self, payload):
        ordered = []
        seen = set()
        for field_key, field_label, field_description in RIS_FIELD_SPECS:
            ordered.append((field_key, field_label, field_description))
            seen.add(field_key)
        for field_key in sorted(payload.keys()):
            if field_key in seen:
                continue
            ordered.append((field_key, field_key, "Custom RIS field."))
        return ordered

    def _stringify_value(self, value, field_key):
        if isinstance(value, list):
            separator = "; " if field_key in MULTI_VALUE_RIS_FIELDS else " "
            return separator.join(str(item) for item in value if item not in {None, ""})
        if value is None:
            return ""
        return str(value)

    @staticmethod
    def _coerce_bool(value):
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        return text in {"1", "true", "yes", "y", "on"}

    @staticmethod
    def _coerce_float(value, default_value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default_value

    @staticmethod
    def _hash_ris(ris_values):
        payload = dict(ris_values)
        payload.pop("_hash", None)
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()


class ProjectSettingsDialog(qtw.QDialog):
    def __init__(self, project_root, session_manager, parent=None):
        super().__init__(parent)
        self.project_root = os.path.abspath(project_root)
        self.session_manager = session_manager
        self.store = ProjectSettingsStore(self.project_root)
        self._base_field_keys = [field_key for field_key, _label, _description in RIS_FIELD_SPECS]
        self._field_descriptions = {
            field_key: description for field_key, _label, description in RIS_FIELD_SPECS
        }
        self._mainui_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.setWindowTitle("Project Settings")
        self.setMinimumSize(920, 680)
        self.resize(980, 720)
        self.setSizeGripEnabled(True)
        self._apply_workflow_font()

        self.tabs = None
        self.ris_table = None
        self.status_label = None

        self._build_ui()
        self._load_values_into_table(self.store.load_ris_values())
        if self.store.last_loaded_provenance_source:
            self.status_label.setText(
                "Loaded project provenance from {0}. Saved project settings still take precedence.".format(
                    self.store.last_loaded_provenance_source
                )
            )
        self._restore_session_state()

    def _apply_workflow_font(self):
        try:
            workflow_font = self.session_manager.build_workflow_font(
                "FROMVS [MAXR]",
                point_size=9,
                module_dir=self._mainui_dir,
            )
            self.setFont(workflow_font)
        except Exception:
            pass

    def _build_ui(self):
        layout = qtw.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        intro_label = qtw.QLabel(
            "Edit project settings and provenance. The RIS tab persists to the project-local SQLite store and project.ris.json."
        )
        intro_label.setWordWrap(True)
        layout.addWidget(intro_label)

        self.tabs = qtw.QTabWidget(self)
        layout.addWidget(self.tabs, 1)

        ris_tab = qtw.QWidget(self)
        ris_layout = qtw.QVBoxLayout(ris_tab)
        ris_layout.setContentsMargins(8, 8, 8, 8)
        ris_layout.setSpacing(8)

        ris_help = qtw.QLabel(
            "Imported RIS content found inside the project is merged into these fields automatically. Clear a value to leave it blank."
        )
        ris_help.setWordWrap(True)
        ris_layout.addWidget(ris_help)

        toolbar_layout = qtw.QHBoxLayout()
        add_field_button = qtw.QPushButton("Add Custom Field")
        add_field_button.clicked.connect(self._add_custom_field)
        toolbar_layout.addWidget(add_field_button)

        remove_field_button = qtw.QPushButton("Remove Custom Field")
        remove_field_button.clicked.connect(self._remove_selected_custom_field)
        toolbar_layout.addWidget(remove_field_button)
        toolbar_layout.addStretch(1)
        ris_layout.addLayout(toolbar_layout)

        self.ris_table = qtw.QTableWidget(0, 3, self)
        self.ris_table.setHorizontalHeaderLabels(["RIS Field", "Value", "Notes"])
        self.ris_table.verticalHeader().setVisible(False)
        self.ris_table.setSelectionBehavior(qtw.QAbstractItemView.SelectRows)
        self.ris_table.setSelectionMode(qtw.QAbstractItemView.SingleSelection)
        self.ris_table.setAlternatingRowColors(True)
        self.ris_table.setWordWrap(True)
        self.ris_table.horizontalHeader().setSectionResizeMode(0, qtw.QHeaderView.ResizeToContents)
        self.ris_table.horizontalHeader().setSectionResizeMode(1, qtw.QHeaderView.Stretch)
        self.ris_table.horizontalHeader().setSectionResizeMode(2, qtw.QHeaderView.Stretch)
        ris_layout.addWidget(self.ris_table, 1)

        self.status_label = qtw.QLabel("")
        self.status_label.setWordWrap(True)
        ris_layout.addWidget(self.status_label)

        self.tabs.addTab(ris_tab, "RIS")

        buttons = qtw.QDialogButtonBox(
            qtw.QDialogButtonBox.Save | qtw.QDialogButtonBox.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_values_into_table(self, values):
        self.ris_table.setRowCount(0)
        ordered_specs = self.store._ordered_field_specs(values)
        for field_key, field_label, description in ordered_specs:
            display_value = self._format_value(values.get(field_key, ""))
            self._append_row(field_key, display_value, description, field_label)

    def _append_row(self, field_key, field_value, description, field_label=None):
        row = self.ris_table.rowCount()
        self.ris_table.insertRow(row)

        display_label = field_label or field_key
        key_item = qtw.QTableWidgetItem(display_label)
        key_item.setFlags(key_item.flags() & ~qtc.Qt.ItemIsEditable)
        key_item.setToolTip("{0}\n\nKey: {1}".format(description, field_key))
        key_item.setData(FIELD_KEY_ROLE, field_key)
        self.ris_table.setItem(row, 0, key_item)

        value_item = qtw.QTableWidgetItem(field_value)
        value_item.setToolTip(description)
        self.ris_table.setItem(row, 1, value_item)

        note_item = qtw.QTableWidgetItem(description)
        note_item.setFlags(note_item.flags() & ~qtc.Qt.ItemIsEditable)
        note_item.setToolTip(description)
        self.ris_table.setItem(row, 2, note_item)

    def _add_custom_field(self):
        field_key, accepted = qtw.QInputDialog.getText(
            self,
            "Custom RIS Field",
            "Field key:",
        )
        if not accepted:
            return
        field_key = field_key.strip()
        if not field_key:
            return
        if self._find_row(field_key) is not None:
            qtw.QMessageBox.information(self, "Project Settings", "Field already exists: {0}".format(field_key))
            return

        self._append_row(field_key, "", "Custom RIS field.", field_key)
        self.ris_table.scrollToBottom()
        self.ris_table.setCurrentCell(self.ris_table.rowCount() - 1, 1)

    def _remove_selected_custom_field(self):
        row = self.ris_table.currentRow()
        if row < 0:
            return
        key_item = self.ris_table.item(row, 0)
        field_key = self._field_key_from_item(key_item)
        if not field_key:
            return
        if field_key in self._base_field_keys:
            qtw.QMessageBox.information(
                self,
                "Project Settings",
                "Built-in RIS fields cannot be removed. Clear the value instead.",
            )
            return
        self.ris_table.removeRow(row)

    def _find_row(self, field_key):
        for row in range(self.ris_table.rowCount()):
            item = self.ris_table.item(row, 0)
            if self._field_key_from_item(item) == field_key:
                return row
        return None

    def _field_key_from_item(self, item):
        if item is None:
            return ""
        field_key = item.data(FIELD_KEY_ROLE)
        if field_key:
            return str(field_key).strip()
        return item.text().strip()

    def _collect_values(self):
        values = {}
        for row in range(self.ris_table.rowCount()):
            key_item = self.ris_table.item(row, 0)
            value_item = self.ris_table.item(row, 1)
            field_key = self._field_key_from_item(key_item)
            if not field_key:
                continue
            field_value = value_item.text() if value_item is not None else ""
            values[field_key] = field_value
        return values

    def _format_value(self, value):
        if isinstance(value, bool):
            return "true" if value else "false"
        if value is None:
            return ""
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)

    def _restore_session_state(self):
        values = self._load_session_values()
        active_tab = values.get(PROJECT_SETTINGS_TAB_KEY)
        if active_tab is not None:
            try:
                tab_index = int(active_tab)
            except (TypeError, ValueError):
                tab_index = 0
            if 0 <= tab_index < self.tabs.count():
                self.tabs.setCurrentIndex(tab_index)

        geometry_b64 = values.get(PROJECT_SETTINGS_GEOMETRY_KEY)
        if geometry_b64:
            try:
                geometry_bytes = base64.b64decode(str(geometry_b64).encode("ascii"))
                self.restoreGeometry(qtc.QByteArray(geometry_bytes))
            except Exception:
                pass

    def _persist_session_state(self):
        geometry_b64 = base64.b64encode(bytes(self.saveGeometry())).decode("ascii")
        self._update_session_values({
            PROJECT_SETTINGS_TAB_KEY: self.tabs.currentIndex(),
            PROJECT_SETTINGS_GEOMETRY_KEY: geometry_b64,
        })

    def _load_session_values(self):
        try:
            return self.session_manager.values(PROJECT_SETTINGS_SESSION_FILE)
        except Exception:
            return {}

    def _update_session_values(self, updates):
        try:
            self.session_manager.update(PROJECT_SETTINGS_SESSION_FILE, updates)
        except Exception:
            session_path = self.session_manager.session_path(PROJECT_SETTINGS_SESSION_FILE)
            session_dir = os.path.dirname(session_path)
            os.makedirs(session_dir, exist_ok=True)
            if not os.path.exists(session_path):
                with open(session_path, "w", encoding="utf-8") as handle:
                    json.dump([], handle, indent=4)
            self.session_manager.update(PROJECT_SETTINGS_SESSION_FILE, updates)

    def accept(self):
        try:
            saved_values = self.store.save_ris_values(self._collect_values())
        except Exception as exc:
            qtw.QMessageBox.warning(self, "Project Settings", "Failed to save project settings: {0}".format(exc))
            return

        self._persist_session_state()
        hash_row = self._find_row("_hash")
        if hash_row is not None:
            self.ris_table.item(hash_row, 1).setText(str(saved_values.get("_hash", "")))
        timestamp_row = self._find_row("timestamp")
        if timestamp_row is not None:
            self.ris_table.item(timestamp_row, 1).setText(str(saved_values.get("timestamp", "")))
        self.status_label.setText("Project settings saved to SQLite and project.ris.json.")
        super().accept()

    def reject(self):
        self._persist_session_state()
        super().reject()

    def closeEvent(self, event):
        self._persist_session_state()
        super().closeEvent(event)