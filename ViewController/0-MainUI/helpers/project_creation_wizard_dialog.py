import csv
import json
import os
import re
import subprocess

from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5 import QtWidgets as qtw

from Core.project_database import build_project_field_definitions
from Core.project_tracking import MODULE_SEQUENCE, ProjectWorkflowTracker


class ProjectCreationWizardDialog(qtw.QDialog):
    DEFAULT_TESSERACT_LANGUAGES = ["Greek", "Latin", "Hebrew", "English"]
    LANGUAGE_NAME_TO_TESSERACT_CODE = {
        "Greek": "ell",
        "Latin": "lat",
        "Hebrew": "heb",
        "English": "eng",
    }
    RIS_TAG_SPECS = [
        ("TY", "Reference type"),
        ("A1", "Primary author"),
        ("A2", "Secondary author"),
        ("A3", "Tertiary author"),
        ("A4", "Subsidiary author"),
        ("AB", "Abstract"),
        ("AD", "Author address"),
        ("AN", "Accession number"),
        ("AU", "Author"),
        ("AV", "Availability"),
        ("BT", "Book title"),
        ("C1", "Custom 1"),
        ("C2", "Custom 2"),
        ("C3", "Custom 3"),
        ("C4", "Custom 4"),
        ("C5", "Custom 5"),
        ("C6", "Custom 6"),
        ("C7", "Custom 7"),
        ("C8", "Custom 8"),
        ("CA", "Caption"),
        ("CN", "Call number"),
        ("CY", "Place published"),
        ("DA", "Date"),
        ("DB", "Database name"),
        ("DO", "DOI"),
        ("DP", "Database provider"),
        ("ED", "Editor"),
        ("EP", "End page"),
        ("ET", "Edition"),
        ("ID", "Reference ID"),
        ("IS", "Issue number"),
        ("J1", "Periodical name (user abbrev.)"),
        ("J2", "Alternate title"),
        ("JA", "Journal abbreviation"),
        ("JF", "Journal/full publication title"),
        ("JO", "Journal name"),
        ("KW", "Keyword"),
        ("L1", "File attachment 1"),
        ("L2", "File attachment 2"),
        ("L3", "Figure"),
        ("L4", "Image"),
        ("LA", "Language"),
        ("LB", "Label"),
        ("LK", "Website link"),
        ("M1", "Number"),
        ("M2", "Misc 2"),
        ("M3", "Type of work"),
        ("N1", "Notes"),
        ("N2", "Abstract notes"),
        ("NV", "Number of volumes"),
        ("OP", "Original publication"),
        ("PB", "Publisher"),
        ("PP", "Publishing place"),
        ("PY", "Publication year"),
        ("RI", "Reviewed item"),
        ("RN", "Research notes"),
        ("RP", "Reprint edition"),
        ("SE", "Section"),
        ("SN", "ISBN/ISSN"),
        ("SP", "Start page"),
        ("ST", "Short title"),
        ("T1", "Primary title"),
        ("T2", "Secondary title"),
        ("T3", "Tertiary title"),
        ("TA", "Translated author"),
        ("TI", "Title"),
        ("TT", "Translated title"),
        ("U1", "User field 1"),
        ("U2", "User field 2"),
        ("U3", "User field 3"),
        ("U4", "User field 4"),
        ("UR", "URL"),
        ("VL", "Volume"),
        ("VO", "Published standard number"),
        ("Y1", "Primary date"),
        ("Y2", "Access date"),
        ("ER", "End of reference"),
    ]
    PAGE_HORIZONTAL_SCROLL_POLICY = qtc.Qt.ScrollBarPolicy.ScrollBarAlwaysOn
    PAGE_VERTICAL_SCROLL_POLICY = qtc.Qt.ScrollBarPolicy.ScrollBarAsNeeded
    _QT_ITEM_FLAG_CLASS = getattr(qtc.Qt, "ItemFlag", None)
    _QT_ALIGNMENT_FLAG_CLASS = getattr(qtc.Qt, "AlignmentFlag", None)
    ITEM_IS_EDITABLE_FLAG = (
        _QT_ITEM_FLAG_CLASS.ItemIsEditable
        if _QT_ITEM_FLAG_CLASS is not None
        else getattr(qtc.Qt, "ItemIsEditable")
    )
    ALIGN_CENTER_FLAG = (
        _QT_ALIGNMENT_FLAG_CLASS.AlignCenter
        if _QT_ALIGNMENT_FLAG_CLASS is not None
        else getattr(qtc.Qt, "AlignCenter")
    )

    def __init__(self, projects_base_path, parent=None):
        super().__init__(parent)
        self.projects_base_path = projects_base_path
        self.setWindowTitle("New Project")
        self.setModal(True)
        self.resize(640, 420)
        self.setSizeGripEnabled(True)
        self._page_titles = [
            "Step 1 of 5: RIS import",
            "Step 2 of 5: Project details",
            "Step 3 of 5: Project settings",
            "Step 4 of 5: Milestones",
            "Step 5 of 5: Project folders",
        ]
        self.imported_provenance = {}
        self._updating_ris_editor = False
        self._ris_tag_row_map = {}
        self._updating_column_rows = False
        self._column_name_edits = []
        self._column_language_combos = []
        self.available_tesseract_languages = self._detect_installed_tesseract_languages()
        self.folder_selection_pages = {}
        self.folder_selection_checkboxes = {}
        self.folder_selection_state = {"scriptural": set()}
        self.workflow_tracker = ProjectWorkflowTracker(
            workspace_root=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
        )
        self._project_db_definitions = build_project_field_definitions()
        self._project_db_definition_map = {
            definition.key: definition for definition in self._project_db_definitions
        }
        self.project_db_table = None
        self.milestones_table = None
        self.handshake_table = None
        self._build_ui()
        self._update_page_state()

    def _make_scroll_page(self, content_widget):
        scroll = qtw.QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(qtw.QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(self.PAGE_HORIZONTAL_SCROLL_POLICY)
        scroll.setVerticalScrollBarPolicy(self.PAGE_VERTICAL_SCROLL_POLICY)
        scroll.setWidget(content_widget)
        return scroll

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

        self.ris_editor_group = qtw.QGroupBox("RIS metadata fields (full spec)")
        ris_editor_layout = qtw.QVBoxLayout(self.ris_editor_group)
        ris_editor_help = qtw.QLabel(
            "Edit all RIS tags here. Use semicolons to separate multiple values for a tag."
        )
        ris_editor_help.setWordWrap(True)
        ris_editor_layout.addWidget(ris_editor_help)

        self.ris_editor_table = qtw.QTableWidget(0, 3, self)
        ris_table = self.ris_editor_table
        ris_table.setHorizontalHeaderLabels(["Tag", "Field", "Value(s)"])
        ris_vertical_header = ris_table.verticalHeader()
        if ris_vertical_header is not None:
            ris_vertical_header.setVisible(False)
        ris_table.setSelectionBehavior(qtw.QAbstractItemView.SelectRows)
        ris_table.setSelectionMode(qtw.QAbstractItemView.SingleSelection)
        ris_table.setAlternatingRowColors(True)
        ris_horizontal_header = ris_table.horizontalHeader()
        if ris_horizontal_header is not None:
            ris_horizontal_header.setSectionResizeMode(0, qtw.QHeaderView.ResizeToContents)
            ris_horizontal_header.setSectionResizeMode(1, qtw.QHeaderView.ResizeToContents)
            ris_horizontal_header.setSectionResizeMode(2, qtw.QHeaderView.Stretch)
        ris_table.itemChanged.connect(self._sync_ris_editor_to_imported_provenance)
        ris_editor_layout.addWidget(ris_table)
        self._build_ris_spec_editor_rows()
        self.ris_editor_group.setVisible(False)
        ris_layout.addWidget(self.ris_editor_group)

        ris_layout.addStretch(1)
        self.page_stack.addWidget(self._make_scroll_page(ris_page))

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
        project_scope_column.addWidget(qtw.QLabel("Project type (fixed)"))
        self.project_type_combo = qtw.QComboBox()
        self.project_type_combo.addItems(["Scriptural"])
        self.project_type_combo.setCurrentText("Scriptural")
        self.project_type_combo.setEnabled(False)
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
        page_model_layout.addWidget(qtw.QLabel("Total Source Document Pages"), 0, 0)
        self.source_pages_combo = qtw.QComboBox()
        for page_number in range(1, 1001):
            self.source_pages_combo.addItem(str(page_number))
        page_model_layout.addWidget(self.source_pages_combo, 0, 1)

        source_pages_note = qtw.QLabel(
            "Source pages are determined by extract (MyServer) or multi-page scans (MyScanner)."
        )
        source_pages_note.setWordWrap(True)
        page_model_layout.addWidget(source_pages_note, 1, 0, 1, 2)
        self._configure_source_pages_dropdown()

        page_model_layout.addWidget(qtw.QLabel("Number of Columns Per Page"), 2, 0)
        self.columns_per_page_spin = qtw.QSpinBox()
        self.columns_per_page_spin.setRange(1, 3)
        self.columns_per_page_spin.setValue(1)
        page_model_layout.addWidget(self.columns_per_page_spin, 2, 1)

        page_model_layout.addWidget(qtw.QLabel("UI Font"), 3, 0)
        self.ui_font_combo = qtw.QFontComboBox()
        page_model_layout.addWidget(self.ui_font_combo, 3, 1)
        self._configure_ui_font_selector()

        self.column_config_group = qtw.QGroupBox("Column language and name editor")
        self.column_config_layout = qtw.QGridLayout(self.column_config_group)
        self.column_config_layout.addWidget(qtw.QLabel("Column"), 0, 0)
        self.column_config_layout.addWidget(qtw.QLabel("Column name"), 0, 1)
        self.column_config_layout.addWidget(qtw.QLabel("Tesseract language"), 0, 2)

        for index, default_language in enumerate(self.DEFAULT_TESSERACT_LANGUAGES):
            row = index + 1
            row_label = qtw.QLabel(f"{index + 1}")
            self.column_config_layout.addWidget(row_label, row, 0)

            name_edit = qtw.QLineEdit(default_language)
            name_edit.textChanged.connect(self._on_column_configuration_changed)
            self.column_config_layout.addWidget(name_edit, row, 1)
            self._column_name_edits.append(name_edit)

            language_combo = qtw.QComboBox()
            language_combo.addItems(self.available_tesseract_languages)
            language_combo.setCurrentText(default_language if default_language in self.available_tesseract_languages else self.available_tesseract_languages[0])
            language_combo.currentIndexChanged.connect(self._on_column_configuration_changed)
            self.column_config_layout.addWidget(language_combo, row, 2)
            self._column_language_combos.append(language_combo)

        page_model_layout.addWidget(self.column_config_group, 3, 0, 1, 2)

        self.column_preview_label = qtw.QLabel("")
        self.column_preview_label.setWordWrap(True)
        page_model_layout.addWidget(self.column_preview_label, 4, 0, 1, 2)
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
        self.page_stack.addWidget(self._make_scroll_page(details_page))

        project_settings_page = qtw.QWidget()
        project_settings_layout = qtw.QVBoxLayout(project_settings_page)
        project_settings_layout.setSpacing(10)

        project_settings_label = qtw.QLabel("Project settings")
        project_settings_layout.addWidget(project_settings_label)

        project_settings_help = qtw.QLabel(
            "These values initialize project_metadata.sqlite. Recommended tools: DB Browser for SQLite."
        )
        project_settings_help.setWordWrap(True)
        project_settings_layout.addWidget(project_settings_help)

        self.project_db_table = qtw.QTableWidget(0, 3, self)
        project_db_table = self.project_db_table
        project_db_table.setHorizontalHeaderLabels(["Field", "Value", "Notes"])
        project_db_vertical_header = project_db_table.verticalHeader()
        if project_db_vertical_header is not None:
            project_db_vertical_header.setVisible(False)
        project_db_table.setSelectionBehavior(qtw.QAbstractItemView.SelectRows)
        project_db_table.setSelectionMode(qtw.QAbstractItemView.SingleSelection)
        project_db_table.setAlternatingRowColors(True)
        project_db_horizontal_header = project_db_table.horizontalHeader()
        if project_db_horizontal_header is not None:
            project_db_horizontal_header.setSectionResizeMode(0, qtw.QHeaderView.ResizeToContents)
            project_db_horizontal_header.setSectionResizeMode(1, qtw.QHeaderView.Stretch)
            project_db_horizontal_header.setSectionResizeMode(2, qtw.QHeaderView.Stretch)
        project_settings_layout.addWidget(project_db_table, 1)

        self.page_stack.addWidget(self._make_scroll_page(project_settings_page))
        self._load_project_database_defaults()

        milestones_page = qtw.QWidget()
        milestones_layout = qtw.QVBoxLayout(milestones_page)
        milestones_layout.setSpacing(10)

        milestones_label = qtw.QLabel("Milestone and module handshake settings")
        milestones_layout.addWidget(milestones_label)

        milestones_help = qtw.QLabel(
            "Milestones and handshakes are grouped by module and shown in sequential order."
        )
        milestones_help.setWordWrap(True)
        milestones_layout.addWidget(milestones_help)

        milestones_tabs = qtw.QTabWidget(self)

        milestone_tab = qtw.QWidget()
        milestone_tab_layout = qtw.QVBoxLayout(milestone_tab)
        self.milestones_table = qtw.QTableWidget(0, 6, self)
        milestones_table = self.milestones_table
        milestones_table.setHorizontalHeaderLabels(["Module", "Sequence", "Milestone Key", "Label", "Weight", "Complete"])
        milestones_vertical_header = milestones_table.verticalHeader()
        if milestones_vertical_header is not None:
            milestones_vertical_header.setVisible(False)
        milestones_table.setSelectionBehavior(qtw.QAbstractItemView.SelectRows)
        milestones_table.setAlternatingRowColors(True)
        milestones_horizontal_header = milestones_table.horizontalHeader()
        if milestones_horizontal_header is not None:
            milestones_horizontal_header.setSectionResizeMode(0, qtw.QHeaderView.ResizeToContents)
            milestones_horizontal_header.setSectionResizeMode(1, qtw.QHeaderView.ResizeToContents)
            milestones_horizontal_header.setSectionResizeMode(2, qtw.QHeaderView.ResizeToContents)
            milestones_horizontal_header.setSectionResizeMode(3, qtw.QHeaderView.Stretch)
            milestones_horizontal_header.setSectionResizeMode(4, qtw.QHeaderView.ResizeToContents)
            milestones_horizontal_header.setSectionResizeMode(5, qtw.QHeaderView.ResizeToContents)
        milestone_tab_layout.addWidget(milestones_table)
        milestones_tabs.addTab(milestone_tab, "Milestones")

        handshake_tab = qtw.QWidget()
        handshake_tab_layout = qtw.QVBoxLayout(handshake_tab)
        self.handshake_table = qtw.QTableWidget(0, 6, self)
        handshake_table = self.handshake_table
        handshake_table.setHorizontalHeaderLabels(["Module", "Sequence", "Milestone", "Language", "Input Path", "Output Path"])
        handshake_vertical_header = handshake_table.verticalHeader()
        if handshake_vertical_header is not None:
            handshake_vertical_header.setVisible(False)
        handshake_table.setSelectionBehavior(qtw.QAbstractItemView.SelectRows)
        handshake_table.setAlternatingRowColors(True)
        handshake_table.setEditTriggers(qtw.QAbstractItemView.NoEditTriggers)
        handshake_horizontal_header = handshake_table.horizontalHeader()
        if handshake_horizontal_header is not None:
            handshake_horizontal_header.setSectionResizeMode(0, qtw.QHeaderView.ResizeToContents)
            handshake_horizontal_header.setSectionResizeMode(1, qtw.QHeaderView.ResizeToContents)
            handshake_horizontal_header.setSectionResizeMode(2, qtw.QHeaderView.ResizeToContents)
            handshake_horizontal_header.setSectionResizeMode(3, qtw.QHeaderView.ResizeToContents)
            handshake_horizontal_header.setSectionResizeMode(4, qtw.QHeaderView.Stretch)
            handshake_horizontal_header.setSectionResizeMode(5, qtw.QHeaderView.Stretch)
        handshake_tab_layout.addWidget(handshake_table)
        milestones_tabs.addTab(handshake_tab, "Module Handshakes")

        milestones_layout.addWidget(milestones_tabs, 1)
        self.page_stack.addWidget(self._make_scroll_page(milestones_page))
        self._load_milestones_defaults()
        self._load_handshake_rows()

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

        self.page_stack.addWidget(self._make_scroll_page(folder_selection_page))

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
        self.source_pages_combo.currentIndexChanged.connect(self._refresh_column_preview)
        self.columns_per_page_spin.valueChanged.connect(self._refresh_column_preview)
        self.ui_font_combo.currentFontChanged.connect(self._on_ui_font_changed)
        self.project_type_combo.currentIndexChanged.connect(self._refresh_column_preview)
        self._update_project_scope_state()
        self._refresh_column_preview()

    def _configure_source_pages_dropdown(self):
        self.source_pages_combo.setCurrentText("1")

    def _source_pages_value(self):
        selected_text = self.source_pages_combo.currentText().strip()
        if selected_text.isdigit():
            return max(1, int(selected_text))
        return 1

    def _detect_installed_tesseract_languages(self):
        codes = []
        try:
            output = subprocess.check_output(
                ["tesseract", "--list-langs"],
                stderr=subprocess.STDOUT,
                text=True,
                timeout=3,
            )
            for raw_line in output.splitlines():
                candidate = raw_line.strip()
                if not candidate or candidate.lower().startswith("list of available languages"):
                    continue
                if re.fullmatch(r"\d+", candidate):
                    continue
                codes.append(candidate)
        except (OSError, subprocess.SubprocessError):
            codes = []

        code_to_name = {value: key for key, value in self.LANGUAGE_NAME_TO_TESSERACT_CODE.items()}
        detected_names = []
        for code in codes:
            detected_names.append(code_to_name.get(code, code))

        ordered = []
        for default_name in self.DEFAULT_TESSERACT_LANGUAGES:
            if default_name not in ordered:
                ordered.append(default_name)
        for detected in detected_names:
            if detected not in ordered:
                ordered.append(detected)

        return ordered

    def _on_column_configuration_changed(self, *_args):
        if self._updating_column_rows:
            return
        self._refresh_column_preview()

    def _selected_column_languages(self):
        count = max(1, int(self.columns_per_page_spin.value()))
        selected = []
        for index in range(min(count, len(self._column_language_combos))):
            selected.append(self._column_language_combos[index].currentText().strip())
        return selected

    def _selected_column_names(self):
        count = max(1, int(self.columns_per_page_spin.value()))
        selected_languages = self._selected_column_languages()
        names = []
        for index in range(min(count, len(self._column_name_edits))):
            entered_name = self._column_name_edits[index].text().strip()
            fallback_name = selected_languages[index] if index < len(selected_languages) else f"Column {index + 1}"
            names.append(entered_name or fallback_name)
        return names

    def _selected_tesseract_language_codes(self):
        codes = []
        for language_name in self._selected_column_languages():
            mapped_code = self.LANGUAGE_NAME_TO_TESSERACT_CODE.get(language_name)
            if mapped_code:
                codes.append(mapped_code)
            else:
                codes.append(language_name.lower())
        return codes

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
        self.project_type_combo.setCurrentText("Scriptural")
        self.scriptural_source_combo.setEnabled(True)
        self.columns_per_page_spin.setEnabled(True)
        self.columns_per_page_spin.setRange(1, 3)
        self._refresh_review()
        self._refresh_folder_selection_page()
        self._refresh_column_preview()
        self._update_validation_state()

    def _update_validation_state(self):
        errors = self._required_field_errors()
        entered_name = self.project_name_edit.text().strip()
        sanitized_name = self._sanitize_project_name(entered_name)
        if self.project_db_table is not None:
            self._set_project_db_value("ProjectName", sanitized_name)
            self._set_project_db_value("ProjectType", self.project_type_combo.currentText().strip())
            self._set_project_db_value("ScripturalSource", self._normalized_scriptural_source_choice())
            self._set_project_db_value("NumberPages", str(self._source_pages_value()))
            self._set_project_db_value("NumberColumns", str(self.columns_per_page_spin.value()))
            self._set_project_db_value("ColumnName", ",".join(self._selected_column_names()))
            self._set_project_db_value("ColumnLanguage", ",".join(self._selected_tesseract_language_codes()))
            self._set_project_db_value("Languages", ",".join(self._selected_tesseract_language_codes()))
            self._set_project_db_value("NumberLanguages", str(len(self._selected_tesseract_language_codes())))
            self._set_project_db_value("ProjectDatabase", self._default_project_database_name())
            self._set_project_db_value("UIFont", self._selected_ui_font())
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
        scroll_area.setHorizontalScrollBarPolicy(self.PAGE_HORIZONTAL_SCROLL_POLICY)
        scroll_area.setVerticalScrollBarPolicy(self.PAGE_VERTICAL_SCROLL_POLICY)
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
        self.folder_selection_stack.setCurrentWidget(self.folder_selection_stack.widget(0))
        self._populate_folder_selection_page("scriptural")

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
        if page_key != "scriptural":
            return []
        template_path = os.path.join(repo_root, "ViewController", "ScriptureProjectFolderList.txt")

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
        source_pages = self._source_pages_value()
        columns_per_page = int(self.columns_per_page_spin.value())
        selected_languages = self._selected_column_languages()
        selected_names = self._selected_column_names()
        total_column_pages = source_pages * max(1, columns_per_page)
        language_rows = []
        for index, language in enumerate(selected_languages):
            column_name = selected_names[index] if index < len(selected_names) else language
            language_rows.append(f"{column_name} [{language}]")
        review_lines = [
            name_line,
            f"Purpose: {self.project_purpose_edit.toPlainText().strip() or 'Not set'}",
            f"Intent: {self.user_intent_edit.toPlainText().strip() or 'Not set'}",
            f"Project type: {project_type}",
            f"Scriptural source: {scripture_source}",
            f"Total source document pages: {source_pages}",
            f"Columns per source page: {columns_per_page}",
            f"UI font: {self._selected_ui_font()}",
            f"Column language/name: {', '.join(language_rows)}",
            f"Total project pages: {total_column_pages}",
            f"Trigger: {self.creation_trigger_edit.text().strip() or 'MyServer_button'}",
            f"Source context: {self.source_context_edit.text().strip() or 'MyServer_UI'}",
            f"Creator: {creator}",
        ]
        self.review_label.setText("\n".join(review_lines))

    def _refresh_column_preview(self):
        count = max(1, int(self.columns_per_page_spin.value()))
        self._updating_column_rows = True
        try:
            for index, name_edit in enumerate(self._column_name_edits):
                active = index < count
                name_edit.setEnabled(active)
                self._column_language_combos[index].setEnabled(active)
        finally:
            self._updating_column_rows = False

        selected_languages = self._selected_column_languages()
        selected_names = self._selected_column_names()
        named_columns = [
            f"Column {index + 1}: {selected_names[index]} [{language}]"
            for index, language in enumerate(selected_languages)
        ]
        source_pages = self._source_pages_value()
        columns_per_page = max(1, int(self.columns_per_page_spin.value()))
        total_column_pages = source_pages * columns_per_page
        self.column_preview_label.setText(
            "\n".join([
                "Columns are named from the editable column name and language rows:",
                *named_columns,
                f"Total project pages = source document pages ({source_pages}) x columns per page ({columns_per_page}) = {total_column_pages}",
            ])
        )
        self._refresh_review()

    def _module_rank(self, module_name):
        module = str(module_name or "").strip()
        if module in MODULE_SEQUENCE:
            return MODULE_SEQUENCE.index(module)
        return len(MODULE_SEQUENCE)

    def _load_project_database_defaults(self):
        table = self.project_db_table
        if table is None:
            return

        table.setRowCount(0)
        for definition in self._project_db_definitions:
            row = table.rowCount()
            table.insertRow(row)

            key_item = qtw.QTableWidgetItem(definition.key)
            key_item.setFlags(key_item.flags() & ~self.ITEM_IS_EDITABLE_FLAG)
            table.setItem(row, 0, key_item)

            default_value = definition.default
            if isinstance(default_value, list):
                display_value = ",".join(str(part) for part in default_value)
            else:
                display_value = "" if default_value is None else str(default_value)
            value_item = qtw.QTableWidgetItem(display_value)
            if definition.key == "ProjectFont":
                value_item.setFlags(value_item.flags() & ~self.ITEM_IS_EDITABLE_FLAG)
            table.setItem(row, 1, value_item)

            notes = definition.help_text or definition.label
            notes_item = qtw.QTableWidgetItem(notes)
            notes_item.setFlags(notes_item.flags() & ~self.ITEM_IS_EDITABLE_FLAG)
            table.setItem(row, 2, notes_item)

        # Synchronize key defaults with wizard controls.
        self._set_project_db_value("ProjectName", self._sanitize_project_name(self.project_name_edit.text().strip()))
        self._set_project_db_value("ProjectType", self.project_type_combo.currentText().strip())
        self._set_project_db_value("ScripturalSource", self._normalized_scriptural_source_choice())
        self._set_project_db_value("NumberPages", str(self._source_pages_value()))
        self._set_project_db_value("NumberColumns", str(self.columns_per_page_spin.value()))
        self._set_project_db_value("ColumnName", ",".join(self._selected_column_names()))
        self._set_project_db_value("ColumnLanguage", ",".join(self._selected_tesseract_language_codes()))
        self._set_project_db_value("Languages", ",".join(self._selected_tesseract_language_codes()))
        self._set_project_db_value("NumberLanguages", str(len(self._selected_tesseract_language_codes())))
        self._set_project_db_value("ProjectDatabase", self._default_project_database_name())
        self._set_project_db_value("UIFont", self._selected_ui_font())

    def _load_milestones_defaults(self):
        table = self.milestones_table
        if table is None:
            return

        table.setRowCount(0)
        rows = []
        for index, (key, label, weight) in enumerate(getattr(self.workflow_tracker, "_milestone_catalog", []), start=1):
            module_name = self.workflow_tracker._module_for_milestone(key) if hasattr(self.workflow_tracker, "_module_for_milestone") else "Workflow"
            rows.append(
                {
                    "module": module_name,
                    "sequence": index,
                    "key": key,
                    "label": label,
                    "weight": max(1, int(weight)),
                    "complete": False,
                }
            )

        rows = sorted(rows, key=lambda row: (self._module_rank(row.get("module")), int(row.get("sequence", 10_000)), str(row.get("key", ""))))

        for row_data in rows:
            row = table.rowCount()
            table.insertRow(row)

            module_item = qtw.QTableWidgetItem(str(row_data.get("module", "Workflow")))
            module_item.setFlags(module_item.flags() & ~self.ITEM_IS_EDITABLE_FLAG)
            table.setItem(row, 0, module_item)

            sequence_item = qtw.QTableWidgetItem(str(row_data.get("sequence", row + 1)))
            sequence_item.setFlags(sequence_item.flags() & ~self.ITEM_IS_EDITABLE_FLAG)
            table.setItem(row, 1, sequence_item)

            key_item = qtw.QTableWidgetItem(str(row_data.get("key", "")))
            key_item.setFlags(key_item.flags() & ~self.ITEM_IS_EDITABLE_FLAG)
            table.setItem(row, 2, key_item)

            label_item = qtw.QTableWidgetItem(str(row_data.get("label", "")))
            label_item.setFlags(label_item.flags() & ~self.ITEM_IS_EDITABLE_FLAG)
            table.setItem(row, 3, label_item)

            table.setItem(row, 4, qtw.QTableWidgetItem(str(row_data.get("weight", 1))))

            complete_checkbox = qtw.QCheckBox()
            complete_checkbox.setChecked(bool(row_data.get("complete", False)))
            complete_widget = qtw.QWidget()
            complete_layout = qtw.QHBoxLayout(complete_widget)
            complete_layout.setContentsMargins(0, 0, 0, 0)
            complete_layout.setAlignment(self.ALIGN_CENTER_FLAG)
            complete_layout.addWidget(complete_checkbox)
            table.setCellWidget(row, 5, complete_widget)

    def _load_handshake_rows(self):
        table = self.handshake_table
        if table is None:
            return

        table.setRowCount(0)
        rows = list(getattr(self.workflow_tracker, "_handshake_rows", []) or [])
        for index, row_data in enumerate(rows):
            row_data["_source_index"] = index

        rows = sorted(
            rows,
            key=lambda row: (
                self._module_rank(row.get("OutputModule") or row.get("InputModule") or "Workflow"),
                int(row.get("_source_index", 10_000)),
            ),
        )

        for sequence, row_data in enumerate(rows, start=1):
            row = table.rowCount()
            table.insertRow(row)

            module_name = str(row_data.get("OutputModule") or row_data.get("InputModule") or "Workflow")
            values = [
                module_name,
                str(sequence),
                str(row_data.get("MilestoneName", "")),
                str(row_data.get("Language", "")),
                str(row_data.get("InputPath", "")),
                str(row_data.get("OutputPath", "")),
            ]
            for column_index, value in enumerate(values):
                item = qtw.QTableWidgetItem(value)
                item.setFlags(item.flags() & ~self.ITEM_IS_EDITABLE_FLAG)
                table.setItem(row, column_index, item)

    def _default_project_database_name(self):
        project_name = self._sanitize_project_name(self.project_name_edit.text().strip()) or "project"
        return f"{project_name}.db"

    def _configure_ui_font_selector(self):
        font_path = os.path.join(os.path.dirname(__file__), "fonts", "FROMVS.ttf")
        font_family = "FROMVS"
        if os.path.isfile(font_path):
            font_id = qtg.QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                families = qtg.QFontDatabase.applicationFontFamilies(font_id)
                if families:
                    font_family = families[0]
        self._default_ui_font_family = font_family
        self.ui_font_combo.setCurrentFont(qtg.QFont(font_family))

    def _selected_ui_font(self):
        family = self.ui_font_combo.currentFont().family().strip()
        if family.casefold() in {
            self._default_ui_font_family.casefold(),
            "fromvs",
            "fromvs [maxr]",
        }:
            return "FROMVS.ttf"
        return family or "FROMVS.ttf"

    def _on_ui_font_changed(self, _font=None):
        self._set_project_db_value("UIFont", self._selected_ui_font())
        self._refresh_review()

    def _find_project_db_row(self, field_key):
        table = self.project_db_table
        if table is None:
            return None
        for row in range(table.rowCount()):
            item = table.item(row, 0)
            if item is not None and item.text().strip() == field_key:
                return row
        return None

    def _set_project_db_value(self, field_key, value):
        table = self.project_db_table
        if table is None:
            return
        row = self._find_project_db_row(field_key)
        if row is None:
            return
        item = table.item(row, 1)
        if item is None:
            item = qtw.QTableWidgetItem()
            table.setItem(row, 1, item)
        item.setText("" if value is None else str(value))

    def _collect_project_db_values(self):
        values = {}
        table = self.project_db_table
        if table is None:
            return values
        for row in range(table.rowCount()):
            key_item = table.item(row, 0)
            value_item = table.item(row, 1)
            if key_item is None:
                continue
            key = key_item.text().strip()
            if not key:
                continue
            raw_value = value_item.text().strip() if value_item is not None else ""
            definition = self._project_db_definition_map.get(key)
            if definition is None:
                values[key] = raw_value
                continue
            if definition.field_type == "int":
                try:
                    values[key] = int(raw_value)
                except ValueError:
                    values[key] = definition.default if definition.default is not None else 0
            elif definition.field_type == "multi_choice":
                values[key] = [part.strip() for part in raw_value.split(",") if part.strip()]
            else:
                values[key] = raw_value
        return values

    def _collect_milestone_settings(self):
        updates = {}
        if self.milestones_table is None:
            return updates
        for row in range(self.milestones_table.rowCount()):
            key_item = self.milestones_table.item(row, 2)
            weight_item = self.milestones_table.item(row, 4)
            complete_widget = self.milestones_table.cellWidget(row, 5)
            if key_item is None:
                continue
            milestone_key = key_item.text().strip()
            if not milestone_key:
                continue
            try:
                milestone_weight = max(1, int((weight_item.text() if weight_item else "1").strip()))
            except (TypeError, ValueError, AttributeError):
                milestone_weight = 1
            milestone_complete = False
            if complete_widget is not None:
                checkbox = complete_widget.findChild(qtw.QCheckBox)
                if checkbox is not None:
                    milestone_complete = checkbox.isChecked()
            updates[milestone_key] = {
                "weight": milestone_weight,
                "complete": milestone_complete,
            }
        return updates

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
        self.status_label.setText("Provenance loaded. Edit fields below or continue to project details.")
        self.page_stack.setCurrentIndex(0)
        self._update_page_state()

    def _clear_ris(self):
        self.ris_path_edit.clear()
        self.imported_provenance = {}
        self._updating_ris_editor = True
        try:
            for row in range(self.ris_editor_table.rowCount()):
                value_item = self.ris_editor_table.item(row, 2)
                if value_item is None:
                    value_item = qtw.QTableWidgetItem("")
                    self.ris_editor_table.setItem(row, 2, value_item)
                else:
                    value_item.setText("")
        finally:
            self._updating_ris_editor = False
        self.ris_editor_group.setVisible(False)
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
        self.project_type_combo.setCurrentText("Scriptural")
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

        self._populate_ris_editor(payload)
        self._refresh_review()

    def _build_ris_spec_editor_rows(self):
        self.ris_editor_table.setRowCount(0)
        self._ris_tag_row_map = {}
        for row, (tag, label) in enumerate(self.RIS_TAG_SPECS):
            self.ris_editor_table.insertRow(row)

            tag_item = qtw.QTableWidgetItem(tag)
            self.ris_editor_table.setItem(row, 0, tag_item)

            label_item = qtw.QTableWidgetItem(label)
            self.ris_editor_table.setItem(row, 1, label_item)

            self.ris_editor_table.setItem(row, 2, qtw.QTableWidgetItem(""))
            self._ris_tag_row_map[tag] = row

    def _extract_ris_tags_from_payload(self, payload):
        tags = payload.get("source_provenance_tags")
        if isinstance(tags, dict):
            extracted = {}
            for key, value in tags.items():
                tag = str(key).strip().upper()
                if not tag:
                    continue
                if isinstance(value, list):
                    extracted[tag] = [str(item).strip() for item in value if str(item).strip()]
                else:
                    text_value = str(value).strip()
                    extracted[tag] = [text_value] if text_value else []
            return extracted
        return {}

    def _populate_ris_editor(self, payload):
        tags = self._extract_ris_tags_from_payload(payload)
        self._updating_ris_editor = True
        try:
            for row in range(self.ris_editor_table.rowCount()):
                value_item = self.ris_editor_table.item(row, 2)
                if value_item is None:
                    value_item = qtw.QTableWidgetItem("")
                    self.ris_editor_table.setItem(row, 2, value_item)
                else:
                    value_item.setText("")

            for tag, values in tags.items():
                row = self._ris_tag_row_map.get(tag)
                if row is None:
                    continue
                value_item = self.ris_editor_table.item(row, 2)
                if value_item is None:
                    value_item = qtw.QTableWidgetItem("")
                    self.ris_editor_table.setItem(row, 2, value_item)
                value_item.setText("; ".join(values))
        finally:
            self._updating_ris_editor = False
        self.ris_editor_group.setVisible(True)
        self._sync_ris_editor_to_imported_provenance()

    def _collect_ris_tags_from_editor(self):
        tags = {}
        for tag, row in self._ris_tag_row_map.items():
            value_item = self.ris_editor_table.item(row, 2)
            value_text = value_item.text().strip() if value_item is not None else ""
            if not value_text:
                continue
            values = [part.strip() for part in value_text.split(";") if part.strip()]
            if values:
                tags[tag] = values
        return tags

    def _sync_derived_fields_from_ris_tags(self, tags):
        def _first(*candidates):
            for candidate in candidates:
                values = tags.get(candidate)
                if values:
                    return values[0]
            return ""

        title = _first("T1", "TI", "T2")
        if title:
            self.imported_provenance["title"] = title
        else:
            self.imported_provenance.pop("title", None)

        authors = tags.get("AU") or tags.get("A1") or []
        if authors:
            self.imported_provenance["authors"] = authors
        else:
            self.imported_provenance.pop("authors", None)

        publication_year = _first("Y1", "PY")
        if publication_year:
            self.imported_provenance["publication_year"] = publication_year
        else:
            self.imported_provenance.pop("publication_year", None)

        doi = _first("DO")
        if doi:
            self.imported_provenance["doi"] = doi
        else:
            self.imported_provenance.pop("doi", None)

        publisher = _first("PB")
        if publisher:
            self.imported_provenance["publisher"] = publisher
        else:
            self.imported_provenance.pop("publisher", None)

        publication_place = _first("CY", "PP")
        if publication_place:
            self.imported_provenance["publication_place"] = publication_place
        else:
            self.imported_provenance.pop("publication_place", None)

        source_identifier = _first("ID")
        if source_identifier:
            self.imported_provenance["source_identifier"] = source_identifier
        else:
            self.imported_provenance.pop("source_identifier", None)

    def _sync_ris_editor_to_imported_provenance(self, changed_item=None):
        if self._updating_ris_editor:
            return
        if changed_item is not None and changed_item.column() != 2:
            return

        tags = self._collect_ris_tags_from_editor()
        if tags:
            self.imported_provenance["source_provenance_tags"] = tags
            self.imported_provenance["source_provenance_format"] = "ris"
        else:
            self.imported_provenance.pop("source_provenance_tags", None)

        self._sync_derived_fields_from_ris_tags(tags)

        if hasattr(self, "creator_edit"):
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
        number_pages = self._source_pages_value()
        self._set_project_db_value("UIFont", self._selected_ui_font())
        project_db_values = self._collect_project_db_values()
        milestone_settings = self._collect_milestone_settings()

        project_database_name = str(project_db_values.get("ProjectDatabase") or self._default_project_database_name()).strip()
        if not project_database_name.lower().endswith(".db"):
            project_database_name = f"{project_database_name}.db"

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
            "ColumnName": ",".join(self._selected_column_names()),
            "ColumnLanguage": ",".join(self._selected_tesseract_language_codes()),
            "Languages": self._selected_tesseract_language_codes(),
            "NumberLanguages": len(self._selected_tesseract_language_codes()),
            "TotalProjectPages": number_pages * number_columns,
            "TotalColumnPages": number_pages * number_columns,
            "SelectedProjectFolders": self._selected_project_folders(),
            "ProjectDatabase": project_database_name,
            "UIFont": self._selected_ui_font(),
            "ProjectDatabaseFields": project_db_values,
            "MilestoneSettings": milestone_settings,
        }
        creator = self.creator_edit.text().strip()
        if creator:
            payload["creator"] = creator
        if self.imported_provenance:
            payload.update(self.imported_provenance)
        return payload

    def _selected_project_folders(self):
        selection = self.folder_selection_state.get("scriptural", set())
        if not selection:
            selection = set(self._folder_selection_entries("scriptural"))
        return sorted(selection)