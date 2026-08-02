from __future__ import annotations

import json
import os
import tempfile
import unittest

from Core.project_database import create_project_database
from Core.project_tracking import ProjectWorkflowTracker


class ProjectTrackingSnapshotTests(unittest.TestCase):
    def _create_project_root(self, base_dir: str, name: str = "DemoProject") -> str:
        project_root = os.path.join(base_dir, name)
        os.makedirs(os.path.join(project_root, "Model", "Project", "Data", "json"), exist_ok=True)
        return project_root

    def test_snapshot_includes_project_metadata_context_from_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = self._create_project_root(tmpdir)
            metadata_path = os.path.join(project_root, "project_metadata.json")
            with open(metadata_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "ProjectPageNumber": 12,
                        "ProjectPageProgress": 65,
                        "ColumnName": "left,center,right",
                        "CurrentColumn": 2,
                        "CurrentLanguage": "grc",
                        "ProjectFont": "Junicode",
                    },
                    handle,
                    indent=2,
                )

            tracker = ProjectWorkflowTracker()
            snapshot = tracker.snapshot("MyServer", project_root=project_root)
            context = snapshot.get("project_context", {})

            self.assertEqual(12, context.get("ProjectPageNumber"))
            self.assertEqual(65, context.get("ProjectPageProgress"))
            self.assertEqual("left,center,right", context.get("ColumnName"))
            self.assertEqual(2, context.get("CurrentColumn"))
            self.assertEqual("center", context.get("ActiveColumnName"))
            self.assertEqual("grc", context.get("CurrentLanguage"))
            self.assertEqual("Junicode", context.get("ProjectFont"))

    def test_snapshot_falls_back_to_sqlite_when_json_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = self._create_project_root(tmpdir)
            sqlite_path = os.path.join(project_root, "project_metadata.sqlite")

            create_project_database(
                sqlite_path,
                {
                    "ProjectName": "SQLiteProject",
                    "ProjectPageNumber": 3,
                    "ProjectPageProgress": 40,
                    "NumberColumns": 2,
                    "ColumnName": "left,right",
                    "CurrentColumn": 2,
                    "Languages": ["eng", "grc"],
                    "CurrentLanguage": "",
                    "ProjectFont": "EB Garamond",
                },
                available_languages=("eng", "grc"),
            )

            tracker = ProjectWorkflowTracker()
            snapshot = tracker.snapshot("MyServer", project_root=project_root)
            context = snapshot.get("project_context", {})

            self.assertEqual(3, context.get("ProjectPageNumber"))
            self.assertEqual(40, context.get("ProjectPageProgress"))
            self.assertEqual("left,right", context.get("ColumnName"))
            self.assertEqual(2, context.get("CurrentColumn"))
            self.assertEqual("right", context.get("ActiveColumnName"))
            self.assertEqual("eng", context.get("CurrentLanguage"))
            self.assertEqual("EB Garamond", context.get("ProjectFont"))


if __name__ == "__main__":
    unittest.main()
