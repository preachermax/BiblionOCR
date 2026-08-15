import csv
import json
import os
import shutil
import sqlite3
import subprocess
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence


PROJECT_DATABASE_FILENAME = "project_metadata.sqlite"
PROJECT_DATABASE_EXPORT_FILENAME = "project_metadata.json"
PROJECT_DATABASE_EXPORT_CSV_FILENAME = "project_metadata.csv"
PROJECT_DATABASE_TABLE = "project_metadata"
DEFAULT_SCRIPTURE_COLUMN_LANGUAGES = ["english", "greek", "hebrew", "latin"]
DEFAULT_PROJECT_FONT = "FROMVS.ttf"


@dataclass(frozen=True)
class ProjectFieldDefinition:
    key: str
    label: str
    field_type: str
    default: Any = None
    required: bool = False
    options: Sequence[str] = ()
    help_text: str = ""


def discover_installed_tesseract_languages() -> List[str]:
    tesseract = shutil.which("tesseract")
    if not tesseract:
        return []

    result = subprocess.run(
        [tesseract, "--list-langs"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []

    languages = []
    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        if not line or line.lower().startswith("list of available languages"):
            continue
        languages.append(line)
    return sorted(dict.fromkeys(languages))


def build_project_field_definitions(available_languages: Optional[Sequence[str]] = None) -> List[ProjectFieldDefinition]:
    languages = tuple(available_languages or discover_installed_tesseract_languages())
    return [
        ProjectFieldDefinition("ProjectName", "Project Name", "text", default="", required=True),
        ProjectFieldDefinition(
            "ProjectDatabase",
            "Project Database",
            "text",
            default="",
            help_text="Primary project SQLite database filename.",
        ),
        ProjectFieldDefinition(
            "ProjectType",
            "Project Type",
            "choice",
            default="Scriptural",
            required=True,
            options=("Scriptural",),
        ),
        ProjectFieldDefinition(
            "SourceType",
            "Source Type",
            "choice",
            default="Scan",
            required=True,
            options=("PDF", "TIFF", "JPG", "PNG", "Scan", "other"),
        ),
        ProjectFieldDefinition(
            "RefTextType",
            "Reference Text Type",
            "choice",
            default="Scriptural",
            options=("Scriptural",),
        ),
        ProjectFieldDefinition("ProvenancePath", "Provenance Path", "path", default=""),
        ProjectFieldDefinition("NumberPages", "Number of Pages", "int", default=0),
        ProjectFieldDefinition("ProjectPageNumber", "Project Page Number", "int", default=1),
        ProjectFieldDefinition(
            "ProjectPageProgress",
            "Project Page Progress (%)",
            "int",
            default=0,
            help_text="Current page progress percentage from 0 to 100.",
        ),
        ProjectFieldDefinition(
            "ProjectBook",
            "Project Book",
            "text",
            default="",
            help_text="Scriptural projects only.",
        ),
        ProjectFieldDefinition(
            "ProjectVerse",
            "Project Verse",
            "text",
            default="",
            help_text="Scriptural projects only.",
        ),
        ProjectFieldDefinition(
            "ProjectWord",
            "Project Word",
            "text",
            default="",
            help_text="Scriptural projects only.",
        ),
        ProjectFieldDefinition(
            "ScripturalSource",
            "Scriptural Source",
            "choice",
            default="both",
            options=("old_testament", "new_testament", "both"),
            help_text="Scriptural projects only: choose old testament, new testament, or both.",
        ),
        ProjectFieldDefinition(
            "NumberColumns",
            "Number of Columns",
            "int",
            default=4,
            required=True,
            help_text="Maximum of 4 columns per source page.",
        ),
        ProjectFieldDefinition(
            "ColumnName",
            "Column Name",
            "text",
            default=",".join(language.title() for language in DEFAULT_SCRIPTURE_COLUMN_LANGUAGES),
            required=True,
            help_text="Comma-separated column names based on NumberColumns, defaulting to language names.",
        ),
        ProjectFieldDefinition(
            "ColumnLanguage",
            "Column Language",
            "text",
            default=",".join(DEFAULT_SCRIPTURE_COLUMN_LANGUAGES),
            required=True,
            help_text="Comma-separated column language names based on NumberColumns.",
        ),
        ProjectFieldDefinition(
            "CurrentLanguage",
            "Current Language",
            "choice",
            default="eng" if "eng" in languages else (languages[0] if languages else ""),
            options=languages,
            help_text="Active OCR language from installed Tesseract languages.",
        ),
        ProjectFieldDefinition(
            "ProjectFont",
            "Project Font",
            "text",
            default=DEFAULT_PROJECT_FONT,
            help_text="Primary project font family used during transcription and rendering.",
        ),
        ProjectFieldDefinition("Notes", "Notes", "text", default=""),
        ProjectFieldDefinition(
            "NumberPageBoxes",
            "Number of Page Boxes",
            "int",
            default=2,
            help_text="Defaults to the number of columns per page.",
        ),
        ProjectFieldDefinition("NumberLanguages", "Number of Languages", "int", default=0),
        ProjectFieldDefinition(
            "Languages",
            "Languages",
            "multi_choice",
            default=[],
            options=languages,
            help_text="Select one or more installed Tesseract languages.",
        ),
        ProjectFieldDefinition("CurrentPage", "Current Page", "int", default=1),
        ProjectFieldDefinition("CurrentProjectPage", "Current Project Page", "int", default=1),
        ProjectFieldDefinition(
            "CurrentProjectMilestone",
            "Current Project Milestone",
            "text",
            default="",
        ),
        ProjectFieldDefinition(
            "CurrentPageMilestone",
            "Current Page Milestone",
            "text",
            default="",
        ),
        ProjectFieldDefinition("CurrentColumn", "Current Column", "int", default=1),
        ProjectFieldDefinition("CurrentLine", "Current Line", "int", default=1),
        ProjectFieldDefinition("CurrentBook", "Current Book", "int", default=1),
        ProjectFieldDefinition("CurrentVerse", "Current Verse", "int", default=1),
        ProjectFieldDefinition("CurrentWord", "Current Word", "int", default=1),
        ProjectFieldDefinition("CurrentGlyph", "Current Glyph", "text", default=""),
    ]


def normalize_project_database_values(
    values: Optional[Dict[str, Any]],
    available_languages: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    definitions = build_project_field_definitions(available_languages)
    incoming = dict(values or {})

    if not incoming.get("ProjectName") and incoming.get("project_name"):
        incoming["ProjectName"] = incoming.get("project_name")
    if incoming.get("project_database") and incoming.get("ProjectDatabase") in (None, ""):
        incoming["ProjectDatabase"] = incoming.get("project_database")
    if incoming.get("CurrentPage") is not None and incoming.get("ProjectPageNumber") in (None, ""):
        incoming["ProjectPageNumber"] = incoming.get("CurrentPage")
    if incoming.get("CurrentProjectPage") is None:
        if incoming.get("CurrentPage") not in (None, ""):
            incoming["CurrentProjectPage"] = incoming.get("CurrentPage")
        elif incoming.get("ProjectPageNumber") not in (None, ""):
            incoming["CurrentProjectPage"] = incoming.get("ProjectPageNumber")
    if incoming.get("CurrentProjectMilestone") in (None, "") and incoming.get("CurrentPageMilestone") not in (None, ""):
        incoming["CurrentProjectMilestone"] = incoming.get("CurrentPageMilestone")
    if incoming.get("CurrentPageMilestone") in (None, "") and incoming.get("CurrentProjectMilestone") not in (None, ""):
        incoming["CurrentPageMilestone"] = incoming.get("CurrentProjectMilestone")
    if incoming.get("CurrentBook") is not None and incoming.get("ProjectBook") in (None, ""):
        incoming["ProjectBook"] = incoming.get("CurrentBook")
    if incoming.get("CurrentVerse") is not None and incoming.get("ProjectVerse") in (None, ""):
        incoming["ProjectVerse"] = incoming.get("CurrentVerse")
    if incoming.get("CurrentWord") is not None and incoming.get("ProjectWord") in (None, ""):
        incoming["ProjectWord"] = incoming.get("CurrentWord")
    if incoming.get("project_font") and incoming.get("ProjectFont") in (None, ""):
        incoming["ProjectFont"] = incoming.get("project_font")
    if incoming.get("ProjectFont") in (None, ""):
        incoming["ProjectFont"] = DEFAULT_PROJECT_FONT

    normalized: Dict[str, Any] = {}

    for definition in definitions:
        raw_value = incoming.get(definition.key, definition.default)
        if definition.field_type == "int":
            normalized[definition.key] = _coerce_int(raw_value, definition.default)
        elif definition.field_type == "choice":
            normalized[definition.key] = _coerce_choice(raw_value, definition.options, definition.default)
        elif definition.field_type == "multi_choice":
            normalized[definition.key] = _coerce_multi_choice(raw_value, definition.options)
        else:
            normalized[definition.key] = "" if raw_value is None else str(raw_value)

    normalized["ProjectType"] = _normalize_project_type(normalized.get("ProjectType"))
    normalized["RefTextType"] = _normalize_project_type(normalized.get("RefTextType"))

    normalized["ProjectPageNumber"] = max(1, _coerce_int(normalized.get("ProjectPageNumber"), 1))
    normalized["ProjectPageProgress"] = _clamp(_coerce_int(normalized.get("ProjectPageProgress"), 0), 0, 100)

    normalized["NumberColumns"] = _clamp(_coerce_int(normalized.get("NumberColumns"), 4), 1, 4)
    normalized["ColumnName"] = _normalize_column_names(
        normalized.get("ColumnName"),
        normalized["NumberColumns"],
    )

    base_language = str(normalized.get("CurrentLanguage") or "").strip()
    if not base_language:
        languages = normalized.get("Languages", [])
        if languages:
            base_language = str(languages[0]).strip()
    normalized["ColumnLanguage"] = _normalize_column_languages(
        normalized.get("ColumnLanguage"),
        normalized["NumberColumns"],
        base_language,
    )

    normalized["ProjectType"] = "Scriptural"
    normalized["RefTextType"] = "Scriptural"
    normalized["ScripturalSource"] = _coerce_choice(
        normalized.get("ScripturalSource"),
        ("old_testament", "new_testament", "both"),
        "both",
    )

    # Keep legacy fields synchronized while phase 1 introduces page-centric naming.
    normalized["CurrentPage"] = normalized["ProjectPageNumber"]
    normalized["CurrentProjectPage"] = max(1, _coerce_int(normalized.get("CurrentProjectPage"), normalized["ProjectPageNumber"]))
    normalized["CurrentPage"] = normalized["CurrentProjectPage"]
    normalized["ProjectPageNumber"] = normalized["CurrentProjectPage"]
    normalized["CurrentBook"] = _coerce_int(normalized.get("ProjectBook"), normalized.get("CurrentBook", 1))
    normalized["CurrentVerse"] = _coerce_int(normalized.get("ProjectVerse"), normalized.get("CurrentVerse", 1))
    normalized["CurrentWord"] = _coerce_int(normalized.get("ProjectWord"), normalized.get("CurrentWord", 1))
    normalized["CurrentColumn"] = _clamp(
        _coerce_int(normalized.get("CurrentColumn"), 1),
        1,
        normalized["NumberColumns"],
    )
    normalized["CurrentProjectMilestone"] = str(normalized.get("CurrentProjectMilestone") or "").strip()
    normalized["CurrentPageMilestone"] = str(normalized.get("CurrentPageMilestone") or normalized["CurrentProjectMilestone"] or "").strip()
    if not normalized["CurrentProjectMilestone"]:
        normalized["CurrentProjectMilestone"] = normalized["CurrentPageMilestone"]

    current_language_was_blank = str(incoming.get("CurrentLanguage", "")).strip() == ""
    if current_language_was_blank or not normalized.get("CurrentLanguage"):
        languages = normalized.get("Languages", [])
        if languages:
            normalized["CurrentLanguage"] = str(languages[0])

    normalized["ColumnLanguage"] = _normalize_column_languages(
        normalized.get("ColumnLanguage"),
        normalized["NumberColumns"],
        str(normalized.get("CurrentLanguage") or "").strip(),
    )

    if not normalized.get("NumberLanguages"):
        normalized["NumberLanguages"] = len(normalized.get("Languages", []))

    if not normalized.get("NumberPageBoxes"):
        normalized["NumberPageBoxes"] = normalized["NumberColumns"]

    if not normalized.get("ProjectName") and incoming.get("project_name"):
        normalized["ProjectName"] = str(incoming["project_name"])

    # Project database defaults to a per-project SQLite file.
    project_name_for_db = str(normalized.get("ProjectName") or "").strip()
    project_database = str(normalized.get("ProjectDatabase") or "").strip()
    if not project_database:
        if project_name_for_db:
            project_database = f"{project_name_for_db}.db"
        else:
            project_database = "project.db"
    if not project_database.lower().endswith(".db"):
        project_database = f"{project_database}.db"
    normalized["ProjectDatabase"] = project_database

    if not str(normalized.get("ProjectFont") or "").strip():
        normalized["ProjectFont"] = DEFAULT_PROJECT_FONT

    return normalized


def create_project_database(
    database_path: str,
    values: Optional[Dict[str, Any]] = None,
    available_languages: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    normalized = normalize_project_database_values(values, available_languages)
    os.makedirs(os.path.dirname(database_path) or ".", exist_ok=True)

    definitions = build_project_field_definitions(available_languages)
    columns_sql = ", ".join(
        f'"{definition.key}" {_sqlite_type(definition.field_type)}'
        for definition in definitions
    )

    with sqlite3.connect(database_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {PROJECT_DATABASE_TABLE} ("
            "id INTEGER PRIMARY KEY CHECK (id = 1), "
            f"{columns_sql}"
            ")"
        )
        _ensure_project_database_schema(cursor, definitions)
        cursor.execute(f"DELETE FROM {PROJECT_DATABASE_TABLE}")

        columns = [definition.key for definition in definitions]
        placeholders = ", ".join("?" for _ in columns)
        stored_values = [
            _serialize_for_sqlite(normalized.get(column))
            for column in columns
        ]
        cursor.execute(
            f"INSERT INTO {PROJECT_DATABASE_TABLE} (id, {', '.join(columns)}) VALUES (1, {placeholders})",
            stored_values,
        )
        connection.commit()

    sync_project_database_mirrors(database_path)

    return normalized


def export_project_database_json(
    database_path: str,
    export_path: Optional[str] = None,
) -> Dict[str, Any]:
    record = load_project_database_record(database_path)
    export_path = export_path or os.path.splitext(database_path)[0] + ".json"
    with open(export_path, "w", encoding="utf-8") as handle:
        json.dump(record, handle, indent=2)
    return record


def export_project_database_csv(
    database_path: str,
    export_path: Optional[str] = None,
) -> Dict[str, Any]:
    record = load_project_database_record(database_path)
    export_path = export_path or os.path.splitext(database_path)[0] + ".csv"
    with open(export_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Field", "Value"])
        for key in sorted(record.keys()):
            value = record.get(key)
            if isinstance(value, list):
                serialized_value = json.dumps(value, ensure_ascii=False)
            else:
                serialized_value = "" if value is None else str(value)
            writer.writerow([key, serialized_value])
    return record


def sync_project_database_mirrors(database_path: str) -> Dict[str, Any]:
    """Keep SQLite project metadata mirrored to adjacent JSON and CSV exports."""
    record = load_project_database_record(database_path)
    base_dir = os.path.dirname(database_path)
    json_path = os.path.join(base_dir, PROJECT_DATABASE_EXPORT_FILENAME)
    csv_path = os.path.join(base_dir, PROJECT_DATABASE_EXPORT_CSV_FILENAME)

    export_project_database_json(database_path, json_path)
    export_project_database_csv(database_path, csv_path)
    return record


def load_project_database_record(database_path: str) -> Dict[str, Any]:
    if not os.path.exists(database_path):
        return {}

    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        try:
            row = cursor.execute(f"SELECT * FROM {PROJECT_DATABASE_TABLE} WHERE id = 1").fetchone()
        except sqlite3.Error:
            return {}

        if row is None:
            return {}

        record = dict(row)
        record.pop("id", None)
        languages = record.get("Languages")
        if isinstance(languages, str):
            try:
                record["Languages"] = json.loads(languages)
            except json.JSONDecodeError:
                record["Languages"] = [language for language in languages.split(",") if language]
        return normalize_project_database_values(record)


def _ensure_project_database_schema(cursor: sqlite3.Cursor, definitions: Sequence[ProjectFieldDefinition]) -> None:
    existing_columns = {
        row[1]
        for row in cursor.execute(f"PRAGMA table_info({PROJECT_DATABASE_TABLE})").fetchall()
    }

    for definition in definitions:
        if definition.key in existing_columns:
            continue
        cursor.execute(
            f'ALTER TABLE {PROJECT_DATABASE_TABLE} ADD COLUMN "{definition.key}" {_sqlite_type(definition.field_type)}'
        )


def _sqlite_type(field_type: str) -> str:
    if field_type == "int":
        return "INTEGER"
    return "TEXT"


def _coerce_int(value: Any, default: Any) -> int:
    try:
        if value is None or value == "":
            return int(default or 0)
        return int(value)
    except (TypeError, ValueError):
        return int(default or 0)


def _coerce_choice(value: Any, options: Sequence[str], default: Any) -> str:
    if value is None:
        return "" if default is None else str(default)

    text = str(value).strip()
    if not text:
        return "" if default is None else str(default)

    if not options:
        return text

    normalized_options = {str(option).strip().lower(): str(option) for option in options}
    resolved = normalized_options.get(text.lower())
    if resolved is not None:
        return resolved

    return "" if default is None else str(default)


def _coerce_multi_choice(value: Any, options: Sequence[str]) -> List[str]:
    if value is None:
        return []

    if isinstance(value, str):
        candidates = [item.strip() for item in value.split(",") if item.strip()]
    else:
        candidates = [str(item).strip() for item in value if str(item).strip()]

    if not options:
        return list(dict.fromkeys(candidates))

    allowed = set(options)
    return [candidate for candidate in dict.fromkeys(candidates) if candidate in allowed]


def _normalize_project_type(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"scripture", "scriptural"}:
        return "Scriptural"
    return "Scriptural"


def _default_column_names(column_count: int) -> List[str]:
    return [language.title() for language in DEFAULT_SCRIPTURE_COLUMN_LANGUAGES[:max(1, column_count)]]


def _normalize_column_names(value: Any, column_count: int) -> str:
    defaults = _default_column_names(column_count)

    if isinstance(value, str):
        candidates = [part.strip() for part in value.split(",") if part.strip()]
    elif isinstance(value, Iterable):
        candidates = [str(part).strip() for part in value if str(part).strip()]
    else:
        candidates = []

    if not candidates:
        return ",".join(defaults)

    normalized = candidates[:column_count]
    if len(normalized) < column_count:
        normalized.extend(defaults[len(normalized):column_count])

    return ",".join(normalized)


def _default_column_languages(column_count: int, base_language: str) -> List[str]:
    if column_count <= len(DEFAULT_SCRIPTURE_COLUMN_LANGUAGES):
        return DEFAULT_SCRIPTURE_COLUMN_LANGUAGES[:column_count]

    language = str(base_language or "").strip().lower()
    if not language:
        language = "english"
    return [language] * column_count


def _normalize_column_languages(value: Any, column_count: int, base_language: str) -> str:
    defaults = _default_column_languages(column_count, base_language)

    if isinstance(value, str):
        candidates = [part.strip() for part in value.split(",") if part.strip()]
    elif isinstance(value, Iterable):
        candidates = [str(part).strip() for part in value if str(part).strip()]
    else:
        candidates = []

    if not candidates:
        return ",".join(defaults)

    normalized = candidates[:column_count]
    if len(normalized) < column_count:
        fill_value = normalized[-1] if normalized else ""
        while len(normalized) < column_count:
            normalized.append(fill_value or defaults[len(normalized)])

    return ",".join(normalized)


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, int(value)))


def _serialize_for_sqlite(value: Any) -> Any:
    if isinstance(value, (list, tuple, set)):
        return json.dumps(list(value))
    return value