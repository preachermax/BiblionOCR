from __future__ import annotations

from pathlib import Path

from Core.project_database import (
    DEFAULT_PROJECT_THEME,
    PROJECT_DATABASE_FILENAME,
    PROJECT_THEME_IDS,
    create_project_database,
    load_project_database_record,
)


def project_theme_database_path(project_root) -> Path:
    return (
        Path(project_root)
        / "Model"
        / "Project"
        / "Data"
        / "sqlite"
        / PROJECT_DATABASE_FILENAME
    )


def load_project_theme(project_root) -> str:
    if not project_root:
        return DEFAULT_PROJECT_THEME
    record = load_project_database_record(str(project_theme_database_path(project_root)))
    theme_id = str(record.get("ProjectTheme") or DEFAULT_PROJECT_THEME)
    return theme_id if theme_id in PROJECT_THEME_IDS else DEFAULT_PROJECT_THEME


def save_project_theme(project_root, theme_id: str) -> str:
    normalized = str(theme_id or DEFAULT_PROJECT_THEME).strip().lower().replace(" ", "_")
    if normalized not in PROJECT_THEME_IDS:
        raise ValueError(f"Unknown project theme: {theme_id}")

    database_path = project_theme_database_path(project_root)
    values = load_project_database_record(str(database_path))
    values["ProjectTheme"] = normalized
    create_project_database(str(database_path), values)
    return normalized