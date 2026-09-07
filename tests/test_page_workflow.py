from __future__ import annotations

import csv
import os
import re
import tempfile
import unittest

from Core.page_workflow import (
    PageWorkflowStep,
    advance_page_workflow_files,
    load_page_workflow,
    load_page_workflow_milestones,
    resolve_page_workflow_path,
    select_page_workflow_step,
)


class PageWorkflowWorkbookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def test_page_workflow_csv_defines_section_aware_mypixler_sequences_and_notes(self) -> None:
        steps, notes = load_page_workflow(self.workspace_root)

        self.assertEqual(38, len(steps))
        self.assertEqual({f"Note {number}" for number in range(1, 7)}, set(notes))
        self.assertTrue(notes["Note 5"].startswith("Stage Dialog/Method must be developed."))

        staging = [step for step in steps if step.method == "actionstage_pdf"]
        self.assertEqual(
            ["FrontSection", "MiddleSections", "VerseSections", "BackSection"],
            [step.page_section for step in staging],
        )
        self.assertEqual(
            ["SSHF", "SSHM", "SSHV", "SSHB"],
            [step.sequence for step in staging],
        )

    def test_page_workflow_milestones_come_from_workbook_worksheet(self) -> None:
        milestones = load_page_workflow_milestones(self.workspace_root)

        self.assertEqual(52, len(milestones))
        self.assertEqual("src_pages_front_matter_staged", milestones[0].name)
        self.assertEqual("col_tif_pages_published", milestones[-1].name)
        self.assertAlmostEqual(1.82, milestones[0].progress_percent)
        self.assertFalse(milestones[0].override_allowed)
        self.assertEqual("MyPixler", milestones[0].module)

    def test_workflow_methods_include_sequence_and_milestone_comments(self) -> None:
        module_paths = {
            "MyServer": os.path.join(self.workspace_root, "ViewController", "0-MainUI", "MyServer.py"),
            "MyScanner": os.path.join(self.workspace_root, "ViewController", "0-MainUI", "MyScanner.py"),
            "MyPixler": os.path.join(self.workspace_root, "ViewController", "1-PreProcess", "MyPixler.py"),
            "MyBoxer": os.path.join(self.workspace_root, "ViewController", "1-PreProcess", "MyBoxer.py"),
        }
        references = {}
        workflow_specs = (
            ("page_workflow.csv", "Module", {}),
            (
                "project_workflow.csv",
                "SourceModule",
                {"on_new_project_clicked": "MyServer"},
            ),
        )
        for filename, module_column, method_modules in workflow_specs:
            workflow_path = os.path.join(
                self.workspace_root,
                "Model",
                "Project",
                "Data",
                "csv",
                filename,
            )
            with open(workflow_path, newline="", encoding="utf-8-sig") as workflow_file:
                for row in csv.DictReader(workflow_file):
                    method_name = (row.get("Method") or "").strip()
                    module_name = method_modules.get(
                        method_name,
                        (row.get(module_column) or "").strip(),
                    )
                    sequence = (row.get("Sequence") or "").strip()
                    milestone_name = (row.get("MilestoneName") or "").strip()
                    if not method_name or module_name not in module_paths:
                        continue
                    references.setdefault((module_name, method_name), set()).add(
                        (sequence, milestone_name)
                    )

        for (module_name, method_name), method_references in references.items():
            with open(module_paths[module_name], encoding="utf-8") as source_file:
                source_lines = source_file.readlines()
            definition_indexes = [
                index
                for index, line in enumerate(source_lines)
                if re.match(rf"\s+def {re.escape(method_name)}\(", line)
            ]
            self.assertTrue(definition_indexes, f"Missing {module_name}.{method_name}")
            for definition_index in definition_indexes:
                comment_lines = []
                index = definition_index - 1
                while index >= 0 and source_lines[index].lstrip().startswith("#"):
                    comment_lines.append(source_lines[index].strip())
                    index -= 1
                comment_text = "\n".join(reversed(comment_lines))
                for sequence, milestone_name in method_references:
                    self.assertIn(
                        f"Sequence {sequence}; MilestoneName {milestone_name}",
                        comment_text,
                        f"Missing workflow comment above {module_name}.{method_name}",
                    )

    def test_project_workflow_method_cells_name_runtime_methods(self) -> None:
        workflow_path = os.path.join(
            self.workspace_root,
            "Model",
            "Project",
            "Data",
            "csv",
            "project_workflow.csv",
        )
        with open(workflow_path, newline="", encoding="utf-8-sig") as workflow_file:
            methods = [
                (row.get("Method") or "").strip()
                for row in csv.DictReader(workflow_file)
                if (row.get("Method") or "").strip()
            ]

        self.assertEqual(
            ["on_new_project_clicked", "actionScanImage", "actionCombineSourcePages"],
            methods,
        )

    def test_selects_next_incomplete_method_for_active_section(self) -> None:
        step = select_page_workflow_step(
            self.workspace_root,
            "MyPixler",
            "actionextract_pdf",
            "Scripture",
            completed_milestones={"src_pages_verses_extracted"},
        )

        self.assertIsNotNone(step)
        assert step is not None
        self.assertEqual("EV2B", step.sequence)
        self.assertEqual("verse_pages_extracted_to_books", step.milestone_name)
        self.assertTrue(resolve_page_workflow_path(self.workspace_root, step.workflow_source).startswith(self.workspace_root))

    def test_stage_transition_copies_to_complete_and_next_workflow_then_clears_source(self) -> None:
        with tempfile.TemporaryDirectory() as project_root:
            step = PageWorkflowStep(
                sequence="SSHF",
                description="stage",
                milestone_name="src_pages_front_matter_staged",
                page_section="FrontSection",
                module="MyPixler",
                ui_trigger="actionStage_pdf.triggered",
                method="actionstage_pdf",
                dialog_ui="StageDialog",
                notes="See Note 5",
                workflow_source="workflow/source",
                complete_destination="complete/source",
                workflow_handshake="workflow/next",
            )
            source = resolve_page_workflow_path(project_root, step.workflow_source)
            os.makedirs(source, exist_ok=True)
            with open(os.path.join(source, "source.pdf"), "wb") as handle:
                handle.write(b"pdf")

            workflow_source, complete, handshake = advance_page_workflow_files(
                project_root,
                step,
                stage_source=True,
            )

            self.assertEqual([], os.listdir(workflow_source))
            self.assertTrue(os.path.isfile(os.path.join(complete, "source.pdf")))
            self.assertTrue(os.path.isfile(os.path.join(handshake, "source.pdf")))

    def test_processed_transition_copies_complete_forward_then_clears_source(self) -> None:
        with tempfile.TemporaryDirectory() as project_root:
            step = PageWorkflowStep(
                sequence="EF1",
                description="extract",
                milestone_name="src_pages_front_matter_extracted",
                page_section="FrontSection",
                module="MyPixler",
                ui_trigger="actionExtract_pdf.triggered",
                method="actionextract_pdf",
                dialog_ui="ExtractDialog",
                notes="See Notes 1 and 2",
                workflow_source="workflow/source",
                complete_destination="complete/output",
                workflow_handshake="workflow/next",
            )
            source = resolve_page_workflow_path(project_root, step.workflow_source)
            complete = resolve_page_workflow_path(project_root, step.complete_destination)
            os.makedirs(source, exist_ok=True)
            os.makedirs(complete, exist_ok=True)
            with open(os.path.join(source, "source.pdf"), "wb") as handle:
                handle.write(b"pdf")
            with open(os.path.join(complete, "page-1.tif"), "wb") as handle:
                handle.write(b"tiff")

            workflow_source, complete, handshake = advance_page_workflow_files(project_root, step)

            self.assertEqual([], os.listdir(workflow_source))
            self.assertTrue(os.path.isfile(os.path.join(complete, "page-1.tif")))
            self.assertTrue(os.path.isfile(os.path.join(handshake, "page-1.tif")))


if __name__ == "__main__":
    unittest.main()