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
                        "CurrentProjectPage": 12,
                        "CurrentProjectMilestone": "source_acquired",
                        "CurrentPageMilestone": "source_acquired",
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
            self.assertEqual(12, context.get("CurrentProjectPage"))
            self.assertEqual("source_acquired", context.get("CurrentProjectMilestone"))
            self.assertEqual("source_acquired", context.get("CurrentPageMilestone"))
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
                    "CurrentProjectPage": 3,
                    "CurrentProjectMilestone": "pages_prepared",
                    "CurrentPageMilestone": "pages_prepared",
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
            self.assertEqual(3, context.get("CurrentProjectPage"))
            self.assertEqual("pages_prepared", context.get("CurrentProjectMilestone"))
            self.assertEqual("pages_prepared", context.get("CurrentPageMilestone"))
            self.assertEqual(40, context.get("ProjectPageProgress"))
            self.assertEqual("left,right", context.get("ColumnName"))
            self.assertEqual(2, context.get("CurrentColumn"))
            self.assertEqual("right", context.get("ActiveColumnName"))
            self.assertEqual("eng", context.get("CurrentLanguage"))
            self.assertEqual("EB Garamond", context.get("ProjectFont"))

    def test_text_outputs_started_detects_workflow_output_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = self._create_project_root(tmpdir)
            workflow_dir = os.path.join(project_root, "Model", "Project", "Text", "Workflow")
            os.makedirs(workflow_dir, exist_ok=True)
            with open(os.path.join(workflow_dir, "sample.txt"), "w", encoding="utf-8") as handle:
                handle.write("workflow output")

            tracker = ProjectWorkflowTracker()

            self.assertTrue(tracker._text_outputs_started(project_root))

    def test_total_pages_use_derived_project_page_count(self) -> None:
        tracker = ProjectWorkflowTracker()

        self.assertEqual(
            200,
            tracker._context_total_pages(
                {"NumberPages": 100, "NumberColumns": 2, "TotalProjectPages": 200}
            ),
        )
        self.assertEqual(
            200,
            tracker._context_total_pages({"NumberPages": 100, "NumberColumns": 2}),
        )

    def test_snapshot_counts_unique_completed_pages_and_requires_all_pages(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = self._create_project_root(tmpdir)
            create_project_database(
                os.path.join(project_root, "project_metadata.sqlite"),
                {"ProjectName": "Pages", "NumberPages": 2, "NumberColumns": 2},
                available_languages=("eng",),
            )
            tracker = ProjectWorkflowTracker()

            tracker.record_page_completion(project_root, 1)
            tracker.record_page_completion(project_root, 1)
            snapshot = tracker.snapshot("MyServer", project_root=project_root)
            self.assertEqual(4, snapshot["total_pages"])
            self.assertEqual(1, snapshot["completed_pages"])
            self.assertEqual(25, snapshot["page_percent"])
            self.assertLess(snapshot["project_percent"], 100)

            for page_number in (2, 3, 4):
                tracker.record_page_completion(project_root, page_number)
            snapshot = tracker.snapshot("MyServer", project_root=project_root)
            self.assertEqual(4, snapshot["completed_pages"])
            self.assertEqual(100, snapshot["page_percent"])


if __name__ == "__main__":
    unittest.main()
