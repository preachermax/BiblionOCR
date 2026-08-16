from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

from Core.project_database import create_project_database


HELPERS_DIR = Path(__file__).resolve().parents[1] / "ViewController" / "0-MainUI" / "helpers"
if str(HELPERS_DIR) not in sys.path:
    sys.path.insert(0, str(HELPERS_DIR))

from SessionManager import SessionManager


class ProjectSessionManager(SessionManager):
    def __init__(self, project_root: str):
        super().__init__(base_dir=str(Path(project_root) / "sessions"))
        self.project_root = project_root

    def get_active_project_root(self, filename: str = "Session.json") -> str:
        return self.project_root


class SessionManagerFontRoleTests(unittest.TestCase):
    def test_default_ui_font_resolves_to_bundled_fromvs_file(self) -> None:
        manager = SessionManager()

        resolved = manager.resolve_font_path("FROMVS.ttf")

        self.assertIsNotNone(resolved)
        self.assertTrue(resolved.endswith("ViewController/0-MainUI/helpers/fonts/FROMVS.ttf"))

    def test_ui_and_tesseract_project_fonts_are_loaded_independently(self) -> None:
        with tempfile.TemporaryDirectory() as project_root:
            create_project_database(
                str(Path(project_root) / "project_metadata.sqlite"),
                {"UIFont": "FROMVS.ttf", "ProjectFont": "GrowingProjectFont.ttf"},
                available_languages=("eng",),
            )
            manager = ProjectSessionManager(project_root)

            self.assertEqual("FROMVS.ttf", manager.get_active_ui_font())
            self.assertEqual("GrowingProjectFont.ttf", manager.get_active_project_font())

    def test_legacy_project_font_remains_the_ui_font_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as project_root:
            database_path = Path(project_root) / "project_metadata.sqlite"
            with sqlite3.connect(database_path) as connection:
                connection.execute(
                    "CREATE TABLE project_metadata (id INTEGER PRIMARY KEY, ProjectFont TEXT)"
                )
                connection.execute(
                    "INSERT INTO project_metadata (id, ProjectFont) VALUES (1, ?)",
                    ("LegacyFont.ttf",),
                )

            manager = ProjectSessionManager(project_root)
            self.assertEqual("LegacyFont.ttf", manager.get_active_ui_font())


if __name__ == "__main__":
    unittest.main()