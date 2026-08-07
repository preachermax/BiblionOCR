from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest

from Core.project_database import (
    PROJECT_DATABASE_TABLE,
    build_project_field_definitions,
    create_project_database,
    load_project_database_record,
    normalize_project_database_values,
)


class ProjectDatabaseSchemaTests(unittest.TestCase):
    def test_phase1_defaults_and_normalization(self) -> None:
        normalized = normalize_project_database_values(
            {
                "ProjectName": "Demo",
                "ProjectType": "Scripture",
                "ProjectPageProgress": 130,
                "NumberColumns": 5,
                "ColumnName": "left",
                "ColumnLanguage": "grc",
                "ProjectFont": "EB Garamond",
                "CurrentPage": 7,
            },
            available_languages=("eng", "grc"),
        )

        self.assertEqual("Scriptural", normalized["ProjectType"])
        self.assertEqual(7, normalized["ProjectPageNumber"])
        self.assertEqual(100, normalized["ProjectPageProgress"])
        self.assertEqual(4, normalized["NumberColumns"])
        self.assertEqual("left,Greek,Hebrew,Latin", normalized["ColumnName"])
        self.assertEqual("grc,grc,grc,grc", normalized["ColumnLanguage"])
        self.assertEqual("EB Garamond", normalized["ProjectFont"])
        self.assertEqual(7, normalized["CurrentPage"])
        self.assertEqual(7, normalized["CurrentProjectPage"])
        self.assertEqual("", normalized["CurrentProjectMilestone"])
        self.assertEqual("", normalized["CurrentPageMilestone"])

    def test_column_defaults_follow_column_count_rules(self) -> None:
        normalized = normalize_project_database_values(
            {
                "ProjectName": "Columns Demo",
                "NumberColumns": 2,
                "CurrentLanguage": "eng",
                "ColumnName": "",
                "ColumnLanguage": "",
            },
            available_languages=("eng", "grc"),
        )

        self.assertEqual("English,Greek", normalized["ColumnName"])
        self.assertEqual("english,greek", normalized["ColumnLanguage"])

    def test_column_fields_are_marked_required(self) -> None:
        definitions = {
            definition.key: definition
            for definition in build_project_field_definitions(("eng", "grc"))
        }

        self.assertTrue(definitions["NumberColumns"].required)
        self.assertTrue(definitions["ColumnName"].required)
        self.assertTrue(definitions["ColumnLanguage"].required)

    def test_project_font_legacy_alias_is_supported(self) -> None:
        normalized = normalize_project_database_values(
            {
                "ProjectName": "Alias Demo",
                "project_font": "Linux Libertine",
            },
            available_languages=("eng",),
        )

        self.assertEqual("Linux Libertine", normalized["ProjectFont"])

    def test_project_type_is_forced_to_scriptural(self) -> None:
        normalized = normalize_project_database_values(
            {
                "ProjectName": "Coerced Demo",
                "ProjectType": "UnsupportedType",
                "RefTextType": "UnsupportedType",
                "ProjectBook": "Genesis",
                "ProjectVerse": "1:1",
                "ProjectWord": "In",
            },
            available_languages=("eng",),
        )

        self.assertEqual("Scriptural", normalized["ProjectType"])
        self.assertEqual("Scriptural", normalized["RefTextType"])
        self.assertEqual("Genesis", normalized["ProjectBook"])
        self.assertEqual("1:1", normalized["ProjectVerse"])
        self.assertEqual("In", normalized["ProjectWord"])

    def test_current_language_defaults_from_selected_languages(self) -> None:
        normalized = normalize_project_database_values(
            {
                "ProjectName": "Lang Demo",
                "Languages": ["grc", "eng"],
                "CurrentLanguage": "",
            },
            available_languages=("eng", "grc"),
        )

        self.assertEqual("grc", normalized["CurrentLanguage"])
        self.assertEqual(2, normalized["NumberLanguages"])

    def test_create_project_database_migrates_legacy_columns(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            database_path = os.path.join(tmpdir, "project_metadata.sqlite")

            with sqlite3.connect(database_path) as connection:
                cursor = connection.cursor()
                cursor.execute(
                    f"CREATE TABLE {PROJECT_DATABASE_TABLE} ("
                    "id INTEGER PRIMARY KEY CHECK (id = 1), "
                    '"ProjectName" TEXT, '
                    '"CurrentPage" INTEGER'
                    ")"
                )
                cursor.execute(
                    f"INSERT INTO {PROJECT_DATABASE_TABLE} (id, ProjectName, CurrentPage) VALUES (1, ?, ?)",
                    ("Legacy", 3),
                )
                connection.commit()

            create_project_database(
                database_path,
                {
                    "ProjectName": "Migrated",
                    "ProjectType": "Scriptural",
                    "ProjectPageNumber": 4,
                    "ProjectPageProgress": 50,
                    "CurrentProjectPage": 4,
                    "CurrentProjectMilestone": "source_acquired",
                    "CurrentPageMilestone": "source_acquired",
                    "NumberColumns": 2,
                    "ColumnName": "left,right",
                    "ColumnLanguage": "eng,lat",
                    "ProjectFont": "Junicode",
                    "CurrentLanguage": "eng",
                },
                available_languages=("eng",),
            )

            with sqlite3.connect(database_path) as connection:
                columns = {
                    row[1]
                    for row in connection.execute(f"PRAGMA table_info({PROJECT_DATABASE_TABLE})").fetchall()
                }

            for definition in build_project_field_definitions(("eng",)):
                self.assertIn(definition.key, columns)

            record = load_project_database_record(database_path)
            self.assertEqual("Migrated", record["ProjectName"])
            self.assertEqual(4, record["ProjectPageNumber"])
            self.assertEqual(50, record["ProjectPageProgress"])
            self.assertEqual(4, record["CurrentProjectPage"])
            self.assertEqual("source_acquired", record["CurrentProjectMilestone"])
            self.assertEqual("source_acquired", record["CurrentPageMilestone"])
            self.assertEqual(2, record["NumberColumns"])
            self.assertEqual("left,right", record["ColumnName"])
            self.assertEqual("eng,lat", record["ColumnLanguage"])
            self.assertEqual("Junicode", record["ProjectFont"])

    def test_new_project_page_fields_are_present(self) -> None:
        definitions = {
            definition.key: definition
            for definition in build_project_field_definitions(("eng", "grc"))
        }

        self.assertIn("CurrentProjectPage", definitions)
        self.assertIn("CurrentProjectMilestone", definitions)
        self.assertIn("CurrentPageMilestone", definitions)


if __name__ == "__main__":
    unittest.main()
