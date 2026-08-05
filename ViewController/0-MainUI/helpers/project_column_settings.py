import os

from Core.project_database import (
    PROJECT_DATABASE_FILENAME,
    create_project_database,
    load_project_database_record,
)


def project_metadata_db_path(project_root: str) -> str:
    return os.path.join(
        os.path.abspath(project_root),
        "Model",
        "Project",
        "Data",
        "sqlite",
        PROJECT_DATABASE_FILENAME,
    )


def update_project_columns(project_root: str, number_columns: int) -> dict:
    metadata_path = project_metadata_db_path(project_root)
    current_values = load_project_database_record(metadata_path)
    current_values["NumberColumns"] = int(number_columns)
    current_values["NumberPageBoxes"] = int(number_columns)
    return create_project_database(metadata_path, current_values)
