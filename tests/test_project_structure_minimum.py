from __future__ import annotations

import os
import tempfile
import unittest

from Core.engine import ProjectCreationEngine


class _DummyEventBus:
    def emit(self, _event):
        return None


class ProjectStructureMinimumTests(unittest.TestCase):
    def test_default_structure_includes_required_model_project_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = ProjectCreationEngine(tmpdir, _DummyEventBus())
            engine._resolve_folder_list_path = lambda: None

            project_root = os.path.join(tmpdir, "project")
            os.makedirs(project_root, exist_ok=True)
            engine._create_project_structure(project_root)

            required_dirs = [
                "Model/Project/Data",
                "Model/Project/Images",
                "Model/Project/Text",
                "Model/Project/Images/MyServer",
                "Model/Project/Images/MyScanner",
                "Model/Project/Images/MyBoxer",
                "Model/Project/Images/MyGlypher",
                "Model/Project/Images/MyReader",
                "Model/Project/Images/MyGrounder",
                "Model/Project/Images/MyTrainer",
                "Model/Project/Images/MyServer/Source",
                "Model/Project/Images/MyServer/Workflow",
                "Model/Project/Images/MyServer/Complete",
                "Model/Project/Images/MyScanner/Source",
                "Model/Project/Images/MyScanner/Workflow",
                "Model/Project/Images/MyScanner/Complete",
                "Model/Project/Text/MyServer/Reference",
                "Model/Project/Text/MyServer/Workflow",
                "Model/Project/Text/MyServer/Complete",
                "Model/Project/Text/MyScanner/Reference",
                "Model/Project/Text/MyScanner/Workflow",
                "Model/Project/Text/MyScanner/Complete",
                "Model/Project/Text/MyBoxer/Reference",
                "Model/Project/Text/MyBoxer/Workflow",
                "Model/Project/Text/MyBoxer/Complete",
                "Model/Project/Text/MyReader/Reference",
                "Model/Project/Text/MyReader/Workflow",
                "Model/Project/Text/MyReader/Complete",
                "Model/Project/Text/MyGrounder/Reference",
                "Model/Project/Text/MyGrounder/Workflow",
                "Model/Project/Text/MyGrounder/Complete",
                "Model/Project/Text/MyTrainer/Reference",
                "Model/Project/Text/MyTrainer/Workflow",
                "Model/Project/Text/MyTrainer/Complete",
                "Model/Project/Text/MyLexer/Reference",
                "Model/Project/Text/MyLexer/Workflow",
                "Model/Project/Text/MyLexer/Complete",
                "Model/Project/Text/MyWriter/Reference",
                "Model/Project/Text/MyWriter/Workflow",
                "Model/Project/Text/MyWriter/Complete",
            ]

            for relative_dir in required_dirs:
                with self.subTest(relative_dir=relative_dir):
                    self.assertTrue(
                        os.path.isdir(os.path.join(project_root, *relative_dir.split("/"))),
                        msg=f"Missing required directory: {relative_dir}",
                    )

    def test_scriptural_projects_include_selected_scripture_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            engine = ProjectCreationEngine(tmpdir, _DummyEventBus())
            engine.context = {
                "project_name": "scripture_project",
                "ProjectType": "Scriptural",
                "ScripturalSource": "old_testament",
            }
            engine._resolve_folder_list_path = lambda: os.path.join(repo_root, "ViewController", "ScriptureProjectFolderList.txt")

            project_root = os.path.join(tmpdir, "project")
            os.makedirs(project_root, exist_ok=True)
            engine._create_project_structure(project_root)

            manifest_path = os.path.join(project_root, "src", "manifests", "ProjectFolderList.txt")
            with open(manifest_path, "r", encoding="utf-8") as handle:
                manifest_text = handle.read()

            self.assertIn("Model/OT_BookFolders", manifest_text)
            self.assertNotIn("Model/NT_BookFolders", manifest_text)
            self.assertIn("Model/Project/Data/csv/BooksAbbrName.csv", manifest_text)

    def test_explicit_folder_selection_controls_scripture_manifest_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            engine = ProjectCreationEngine(tmpdir, _DummyEventBus())
            engine.context = {
                "project_name": "scripture_project",
                "ProjectType": "Scriptural",
                "ScripturalSource": "both",
                "SelectedProjectFolders": ["Model/NT_BookFolders"],
            }
            engine._resolve_folder_list_path = lambda: os.path.join(repo_root, "ViewController", "ScriptureProjectFolderList.txt")

            project_root = os.path.join(tmpdir, "project")
            os.makedirs(project_root, exist_ok=True)
            engine._create_project_structure(project_root)

            manifest_path = os.path.join(project_root, "src", "manifests", "ProjectFolderList.txt")
            with open(manifest_path, "r", encoding="utf-8") as handle:
                manifest_text = handle.read()

            self.assertNotIn("Model/OT_BookFolders", manifest_text)
            self.assertIn("Model/NT_BookFolders", manifest_text)


if __name__ == "__main__":
    unittest.main()
