from __future__ import annotations

import json
import os
import tempfile
import unittest

from Core.engine import ProjectCreationEngine


class _DummyEventBus:
    def emit(self, _event):
        return None


class ProjectStructureMinimumTests(unittest.TestCase):
    def test_project_manifests_include_required_theme_entries(self) -> None:
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        for filename in ("ScriptureProjectFolderList.txt", "GeneralProjectFolderList.txt"):
            with self.subTest(filename=filename):
                manifest_path = os.path.join(repo_root, "ViewController", filename)
                with open(manifest_path, "r", encoding="utf-8-sig") as handle:
                    entries = {line.strip() for line in handle if line.strip()}
                self.assertTrue(set(ProjectCreationEngine.REQUIRED_THEME_ENTRIES).issubset(entries))

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

            self.assertTrue(os.path.isdir(os.path.join(project_root, "Model", "OT_BookFolders")))
            self.assertFalse(
                os.path.isdir(
                    os.path.join(
                        project_root,
                        "Model",
                        "Project",
                        "Text",
                        "MyServer",
                        "Workflow",
                        "Greek",
                        "txt_greek_pages",
                        "book_40_Matthew",
                    )
                )
            )

    def test_explicit_folder_selection_controls_scripture_manifest_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            engine = ProjectCreationEngine(tmpdir, _DummyEventBus())
            engine.context = {
                "project_name": "scripture_project",
                "ProjectType": "Scriptural",
                "ScripturalSource": "new_testament",
                "SelectedProjectFolders": ["Model/Project/Text/MyServer/Workflow/Greek/txt_greek_pages"],
            }
            engine._resolve_folder_list_path = lambda: os.path.join(repo_root, "ViewController", "ScriptureProjectFolderList.txt")

            project_root = os.path.join(tmpdir, "project")
            os.makedirs(project_root, exist_ok=True)
            engine._create_project_structure(project_root)

            self.assertTrue(
                os.path.isdir(
                    os.path.join(
                        project_root,
                        "Model",
                        "Project",
                        "Text",
                        "MyServer",
                        "Workflow",
                        "Greek",
                        "txt_greek_pages",
                        "book_40_Matthew",
                    )
                )
            )
            self.assertFalse(
                os.path.isdir(
                    os.path.join(
                        project_root,
                        "Model",
                        "Project",
                        "Text",
                        "MyReader",
                        "Workflow",
                        "Greek",
                        "txt_greek_wordlist",
                        "book_40_Matthew",
                    )
                )
            )

    def test_scripture_manifest_keeps_process_modules(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            engine = ProjectCreationEngine(tmpdir, _DummyEventBus())
            engine.context = {
                "project_name": "scripture_project",
                "ProjectType": "Scriptural",
                "ScripturalSource": "both",
            }
            engine._resolve_folder_list_path = lambda: os.path.join(repo_root, "ViewController", "ScriptureProjectFolderList.txt")

            project_root = os.path.join(tmpdir, "project")
            os.makedirs(project_root, exist_ok=True)
            engine._create_project_structure(project_root)

            manifest_path = os.path.join(project_root, "src", "manifests", "ProjectFolderList.txt")
            with open(manifest_path, "r", encoding="utf-8") as handle:
                manifest_text = handle.read()

            self.assertIn("ViewController/3-Process/MyLexer.py", manifest_text)
            self.assertIn("ViewController/3-Process/MyResolver.py", manifest_text)
            self.assertIn("ViewController/3-Process/MyVersifier.py", manifest_text)

    def test_required_theme_files_are_copied_without_setup_selection(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            manifest_path = os.path.join(tmpdir, "ProjectFolderList.txt")
            with open(manifest_path, "w", encoding="utf-8") as handle:
                handle.write("\n".join(ProjectCreationEngine.REQUIRED_THEME_ENTRIES) + "\n")

            engine = ProjectCreationEngine(tmpdir, _DummyEventBus(), folder_list_path=manifest_path)
            engine.context = {
                "project_name": "default_theme_project",
                "SelectedProjectFolders": ["Model/Project/Data"],
            }
            project_root = os.path.join(tmpdir, "project")
            os.makedirs(project_root, exist_ok=True)
            engine._create_project_structure(project_root)

            relative_theme_dir = os.path.join("ViewController", "0-MainUI", "helpers", "Stylesheets")
            source_theme_dir = os.path.join(repo_root, relative_theme_dir)
            project_theme_dir = os.path.join(project_root, relative_theme_dir)
            source_files = set()
            for root, directories, files in os.walk(source_theme_dir):
                directories[:] = [name for name in directories if name != "__pycache__"]
                source_files.update(
                    os.path.relpath(os.path.join(root, filename), source_theme_dir)
                    for filename in files
                    if not filename.endswith(".pyc")
                )
            project_files = {
                os.path.relpath(os.path.join(root, filename), project_theme_dir)
                for root, _directories, files in os.walk(project_theme_dir)
                for filename in files
                if filename != ".gitkeep"
            }
            self.assertEqual(source_files, project_files)
            self.assertTrue(
                os.path.isfile(
                    os.path.join(
                        project_root,
                        "ViewController",
                        "0-MainUI",
                        "helpers",
                        "Dialogs",
                        "ThemeEditorDialog.py",
                    )
                )
            )

            with open(os.path.join(project_theme_dir, "theme_manifest.json"), "r", encoding="utf-8") as handle:
                theme_manifest = json.load(handle)
            self.assertEqual("default", next(iter(theme_manifest["themes"])))
            self.assertTrue(theme_manifest["themes"]["default"]["native"])
            self.assertFalse(any("theme" in key.lower() for key in engine.context))


if __name__ == "__main__":
    unittest.main()
