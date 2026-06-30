#!/usr/bin/env python3
"""
Rebuild/update ProjectFolderList.txt for BiblionOCR.

This script captures the cleanup rules used while curating ProjectFolderList.txt:
- seed from the current ProjectFolderList.txt when it exists;
- add folders referenced by Model/Project/Data/json/*Session.json;
- include Model/Project/Data file contents for csv/json/SQLite-driven project setup;
- reduce Model/Project/Images file entries to folders only;
- normalize project-absolute paths to project-relative paths;
- reduce file paths to their containing folders;
- redirect Model/Developer and old Model/Utilities references to Model/Project/Utilities;
- explicitly prevent Model/Developer and old Model/Utilities references from being written;
- always include existing folders under Model/Project/Utilities;
- always include project-local training assets for Tesseract workflows;
- always include required ViewController folders and MainUI files;
- exclude Model/Project/Utilities/Reference folders;
- exclude external/system font, Tesseract, home, and user profile folders;
- exclude .duplicity folders and ViewController/Developer references;
- remove duplicates and sort the final list consistently.

Run from anywhere inside the repository:
    python ViewController/0-MainUI/ProjectFolderList.py

Options:
    --dry-run       Print the generated list without writing ProjectFolderList.txt.
    --scan          Also discover real folders under Model and ViewController.
    --no-existing   Do not seed from the current ProjectFolderList.txt.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
from pathlib import Path, PurePosixPath
from typing import Iterable, Optional, Set


PROJECT_LIST_FILENAME = "ProjectFolderList.txt"
SESSION_JSON_GLOB = "*Session.json"

REQUIRED_PROJECT_FILES = {
    "requirements.txt",
}

# Manifest copy overrides use the form:
#   source_template => generated_project_destination
# New projects must receive the project-safe MyServer bundle from Core/, not
# the source BiblionOCR MyServer bundle from ViewController/0-MainUI/.
PROJECT_MANIFEST_TEMPLATE_OVERRIDES = {
    "Core/MyServer.py => ViewController/0-MainUI/MyServer.py",
    "Core/MyServerUI.py => ViewController/0-MainUI/MyServerUI.py",
    "Core/MyServerUI.ui => ViewController/QtDesignerUI/MyServerUI.ui",
}

# These are the source BiblionOCR MyServer files that must not be copied into
# generated projects. Core/MyServer* files are intentionally NOT listed here;
# they are the replacement template sources used by the overrides above.
OMITTED_SOURCE_MYSERVER_REFERENCES = {
    "ViewController/0-MainUI/MyServer.py",
    "ViewController/0-MainUI/MyServerUI.py",
    "ViewController/0-MainUI/QtDesignerUI/MyServerUI.ui",
}

STATIC_EXTERNAL_FOLDERS = {
    "/.fonts",
    "/.local/share/fonts",
    "/Documents/MyForge",
    "/home",
    "/home/jetson",
    "/Projects",
    "/tesseract",
    "/tesseract/tessdata",
    "/tesseract/tesstrain-raw-Gospels",
    "/tesseract/tesstrain-raw-Gospels/fonts",
    "/usr/local/share/fonts",
    "/usr/share/fonts/truetype",
    "/usr/share/fonts/truetype/FROMVS",
    "c:/Program Files/Tesseract-OCR",
    "c:/Program Files/Tesseract-OCR/tessdata",
    "c:/Program Files/Tesseract-OCR/tesstrain-raw-Gospels",
    "c:/Program Files/Tesseract-OCR/tesstrain-raw-Gospels/fonts",
    "c:/users",
    "c:/users/max",
    "c:/users/max/tesseract/tesstrain-raw-Gospels/fonts",
    "c:/users/max/tesseract/tesstrain-raw-Gospels/fonts/FROMVS",
    "c:/Windows/font",
    "c:/Windows/Fonts",
    "c:/Windows/fonts/FROMVS",
}

STATIC_PROJECT_FOLDERS = {
    "Model/Project/Images",
    "Model/Project/Images/Complete",
    "Model/Project/Data/json",
    "Model/Project/Data/SQLite",
    "Model/Project/Utilities",
    "Model/Project/Images/Complete/Greek",
    "Model/Project/Images/Complete/Latin",
    "Model/Project/Images/Complete/Source",
    "Model/Project/Images/Workflow",
    "Model/Project/Images/Workflow/Greek",
    "Model/Project/Images/Workflow/Latin",
    "Model/Project/Images/Workflow/Source",
    "Model/Project/Images/Workflow/pixler",
    "Model/Project/Images/Workflow/pixler/pixler_pages_cropped",
    "ViewController/0-MainUI",
    "ViewController/0-MainUI/fonts",
    "ViewController/QtDesignerUI",
}

MINIMAL_IMAGE_FOLDERS = {
    "Model/Project/Images",
    "Model/Project/Images/Complete",
    "Model/Project/Images/Complete/Greek",
    "Model/Project/Images/Complete/Latin",
    "Model/Project/Images/Complete/Source",
    "Model/Project/Images/Workflow",
    "Model/Project/Images/Workflow/Greek",
    "Model/Project/Images/Workflow/Latin",
    "Model/Project/Images/Workflow/Source",
    "Model/Project/Images/Workflow/pixler",
    "Model/Project/Images/Workflow/pixler/pixler_pages_cropped",
}

MAINUI_MODULE_SEEDS = {
    "MyBoxer.py",
    "MyExplorer.py",
    "MyGlypher.py",
    "MyGrounder.py",
    "MyLauncher.py",
    "MyLexer.py",
    "MyPixler.py",
    "MyReader.py",
    "MyResolver.py",
    "MyScanner.py",
    "MyVersifier.py",
    "MyWriter.py",
}

REQUIRED_VIEWCONTROLLER_REFERENCES = {
    "ViewController/4-PostProcess",
    "ViewController/3-ConductOCR",
    "ViewController/2-TrainTesseract",
    "ViewController/1-PreProcess",
    "ViewController/0-MainUI/worker.py",
    "ViewController/0-MainUI/update_UI_Resources.txt",
    "ViewController/0-MainUI/update_fonts.txt",
    "ViewController/0-MainUI/update_fonts.py",
    "ViewController/0-MainUI/Ui2Py.py",
    "ViewController/0-MainUI/UI_Icons.qrc",
    "ViewController/0-MainUI/UI_Icons.py",
    "ViewController/0-MainUI/Training.py",
    "ViewController/0-MainUI/tift2mono.py",
    "ViewController/0-MainUI/tif_greek_lines_stageDialog.py",
    "ViewController/0-MainUI/TextDragandDrop.py",
    "ViewController/0-MainUI/StageLineImages2GroundTruth.py",
    "ViewController/0-MainUI/SqliteMain.py",
    "ViewController/0-MainUI/SqliteHelper.py",
    "ViewController/0-MainUI/sqlite3-mysql.txt",
    "ViewController/0-MainUI/scanner_app.py",
    "ViewController/0-MainUI/RenameFiles.py",
    "ViewController/0-MainUI/README_HELP_SYSTEM.md",
    "ViewController/0-MainUI/QUICK_REFERENCE.md",
    "ViewController/0-MainUI/pyTesseractTrainer-1.03.py",
    "ViewController/0-MainUI/ProjectFolderList.txt",
    "ViewController/0-MainUI/ProjectFolderList.py",
    "ViewController/0-MainUI/Dialogs/ProjectSettingsDialog.py",
    "ViewController/0-MainUI/PROJECT_ARCHITECTURE.md",
    "ViewController/0-MainUI/PreviewStudio.py",
    "ViewController/0-MainUI/PreProcess.py",
    "ViewController/0-MainUI/PageVerseHelper.ipynb",
    "ViewController/0-MainUI/PageVerseCrossReferenceUI.py",
    "ViewController/0-MainUI/PageVerseCrossReference.py",
    "ViewController/0-MainUI/PageVerseCrossReference.ipynb",
    "ViewController/0-MainUI/ocr_preprocess_tool.ui",
    "ViewController/0-MainUI/ocr_preprocess_tool.py",
    "ViewController/0-MainUI/NormalizeVerseText.py",
    "ViewController/0-MainUI/NormalizeRefText.py",
    "ViewController/0-MainUI/MyWriterUI.py",
    "ViewController/0-MainUI/MyWriter.py",
    "ViewController/0-MainUI/MyVersifierUI.py",
    "ViewController/0-MainUI/MyVersifier.py",
    "ViewController/0-MainUI/MyTrainerUI.py",
    "ViewController/0-MainUI/MyTrainer.py",
    "ViewController/0-MainUI/MySlidersUI.py",
    "ViewController/0-MainUI/MySliders.py",

    "ViewController/0-MainUI/MyScanner.py",
    "ViewController/0-MainUI/MyResolverUI.py",
    "ViewController/0-MainUI/MyResolver.py",
    "ViewController/0-MainUI/MyReaderUI.py",
    "ViewController/0-MainUI/MyScannerUI.py",
    "ViewController/0-MainUI/MyScannerWin.py",
    *PROJECT_MANIFEST_TEMPLATE_OVERRIDES,
    "ViewController/0-MainUI/MyReader.py",
    "ViewController/0-MainUI/MyPixlerUI.py",
    "ViewController/0-MainUI/MyPixlerGVUI.py",
    "ViewController/0-MainUI/MyPixler.py",
    "ViewController/0-MainUI/MyLexerUI.py",
    "ViecMyLexer.py",
    "ViewController/0-MainUI/MyLauncherUI.py",
    "ViewController/0-MainUI/MyLauncher.py",
    "ViewController/0-MainUI/MyGrounderUI.py",
    "ViewController/0-MainUI/MyGrounder.py",
    "ViewController/0-MainUI/MyGlypherUI.py",
    "ViewController/0-MainUI/MyGlypher.py",
    "ViewController/0-MainUI/MyExplorerUI.py",
    "ViewController/0-MainUI/MyExplorer.py",
    "ViewController/0-MainUI/MyBoxerUI.py",
    "ViewController/0-MainUI/MyBoxer.py",
    "ViewController/0-MainUI/MainUI.py",
    "ViewController/0-MainUI/mainfind.py",
    "ViewController/0-MainUI/main.py",
    "ViewController/0-MainUI/LICENSE",
    "ViewController/0-MainUI/lexicon core.py",
    "ViewController/0-MainUI/keepforundo",
    "ViewController/0-MainUI/ImagePreviewDialog.py",
    "ViewController/0-MainUI/ImageLoadWorker.py",
    "ViewController/0-MainUI/ImageFileRenameMove4GroundTruth.py",
    "ViewController/0-MainUI/HelpSystem.py",
    "ViewController/0-MainUI/HELP_INTEGRATION_GUIDE.md",
    "ViewController/0-MainUI/getPlatform.py",
    "ViewController/0-MainUI/getFontInfo.py",
    "ViewController/0-MainUI/font_glyf2csv2json.py",
    "ViewController/0-MainUI/font_glyf_splines2csv2json.py",
    "ViewController/0-MainUI/font_cmap2csv2json.py",
    "ViewController/0-MainUI/find.py",
    "ViewController/0-MainUI/FileExplorer.py",
    "ViewController/0-MainUI/DragandDropNotes.txt",
    "ViewController/0-MainUI/DragandDrop.py",
    "ViewController/0-MainUI/dev_notebook.md",
    "ViewController/0-MainUI/DEPENDENCIES_AND_RELATIONSHIPS.md",
    "ViewController/0-MainUI/commit_checklist.md",
    "ViewController/0-MainUI/Co-pilot Instructions.txt",
    "ViewController/0-MainUI/Co-pilot Instructions.odt",
    "ViewController/0-MainUI/Co-pilot diff text on FROMVS in Windows.txt",
    "ViewController/0-MainUI/cmap2csv2 json.py",
    "ViewController/0-MainUI/ChrReferenceDialog.py",
    "ViewController/0-MainUI/ChrReference.py",
    "ViewController/0-MainUI/ChrReference copy.py",
    "ViewController/0-MainUI/AIcommitWorkflow.md",
    "ViewController/0-MainUI/advanced_scanner.py",
    "ViewController/0-MainUI/advanced_scanner-twain-too much.py",
    "ViewController/0-MainUI/advanced_scanner-twain py",
    "ViewController/0-MainUI/Adjust.py",
    "ViewController/0-MainUI/UI_Images",
    "ViewController/0-MainUI/web",
}

TRAINING_SUPPORT_ROOTS = {
    "Model/Project/Training",
    "ViewController/0-MainUI/TessTrainBoxFiles",
    "ViewController/2-TrainTesseract",
}

KNOWN_FILE_EXTENSIONS = {
    ".bmp",
    ".csv",
    ".db",
    ".gif",
    ".jpeg",
    ".jpg",
    ".json",
    ".otf",
    ".pdf",
    ".png",
    ".py",
    ".sfd",
    ".tif",
    ".tiff",
    ".ttf",
    ".txt",
    ".ui",
    ".xml",
}

SETTING_NAME_RE = re.compile(r"(dir|path|file|font|tess|sfd|db|sourcefile)$", re.IGNORECASE)
PROJECT_ABSOLUTE_MARKERS = (
    "c:/users/max/projects/biblionocr/",
    "/home/jetson/projects/biblionocr/",
    "/home/max/projects/biblionocr/",
    "/projects/biblionocr/",
)
EXCLUDED_SEGMENTS = {
    ".git",
    ".idea",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "node_modules",
}


class ProjectFolderListBuilder:
    """Build and write the curated ProjectFolderList.txt inventory."""

    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()
        self.project_list_path = self.project_root / PROJECT_LIST_FILENAME
        self.main_ui_project_list_path = (
            self.project_root / "ViewController" / "0-MainUI" / PROJECT_LIST_FILENAME
        )
        self.session_json_dir = self.project_root / "Model" / "Project" / "Data" / "json"

    @staticmethod
    def find_project_root(start: Optional[Path] = None) -> Path:
        here = (start or Path(__file__)).resolve()
        if here.is_file():
            here = here.parent

        for candidate in (here, *here.parents):
            if (candidate / "Model").is_dir() and (candidate / "ViewController").is_dir():
                return candidate

        for candidate in (here, *here.parents):
            if (candidate / PROJECT_LIST_FILENAME).exists():
                return candidate

        raise FileNotFoundError(
            "Could not find project root. Expected ProjectFolderList.txt or Model/ and ViewController/."
        )

    def build(self, include_existing: bool = True, scan_filesystem: bool = False) -> list[str]:
        folders: Set[str] = set(STATIC_PROJECT_FOLDERS)
        files: Set[str] = set()
        existing_entries: Set[str] = set()

        if include_existing:
            existing_entries = self._read_existing_list()

        existing_folders, existing_files = self._partition_existing_entries(existing_entries)
        folders.update(existing_folders)
        files.update(existing_files)
        files.update(REQUIRED_PROJECT_FILES)

        required_viewcontroller_folders, required_viewcontroller_files = self._partition_existing_entries(
            REQUIRED_VIEWCONTROLLER_REFERENCES,
            exclude_viewcontroller=False,
        )
        folders.update(required_viewcontroller_folders)
        files.update(required_viewcontroller_files)

        folders.update(self._collect_project_utilities_folders())
        folders.update(self._collect_session_json_folders())
        folders.update(self._collect_model_data_folders())
        files.update(self._collect_model_data_files())
        training_folders, training_files = self._collect_recursive_support_entries(TRAINING_SUPPORT_ROOTS)
        folders.update(training_folders)
        files.update(training_files)
        folders.update(self._collect_workflow_image_folders())
        files.update(self._collect_mainui_module_files())
        files.update(self._collect_mainui_font_files())

        # Explicit project-local folder used by SessionManager font handling.
        folders.add("ViewController/0-MainUI/fonts")

        if scan_filesystem:
            folders.update(self._scan_filesystem_folders())

        cleaned = {p for p in (self.normalize_path(path) for path in folders) if p}
        cleaned.update(
            p for p in (self.normalize_path(path, reduce_file_paths=False) for path in files) if p
        )
        cleaned.difference_update(OMITTED_SOURCE_MYSERVER_REFERENCES)
        cleaned.update(PROJECT_MANIFEST_TEMPLATE_OVERRIDES)
        self._assert_no_deprecated_model_references(cleaned)
        return sorted(cleaned, key=self.sort_key)

    def write(self, folders: Iterable[str]) -> None:
        folder_list = list(folders)
        self._assert_no_deprecated_model_references(folder_list)
        text = "\n".join(folder_list).rstrip() + "\n"

        output_paths = [self.project_list_path]
        if self.main_ui_project_list_path != self.project_list_path:
            output_paths.append(self.main_ui_project_list_path)

        for output_path in output_paths:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(text, encoding="utf-8")

    def _read_existing_list(self) -> Set[str]:
        if not self.project_list_path.exists():
            return set()
        return {
            line.strip()
            for line in self.project_list_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }

    def _partition_existing_entries(
        self,
        entries: Iterable[str],
        exclude_viewcontroller: bool = True,
    ) -> tuple[Set[str], Set[str]]:
        folders: Set[str] = set()
        files: Set[str] = set()

        for entry in entries:
            normalized = self.normalize_path(entry, reduce_file_paths=False)
            if not normalized:
                continue

            if normalized == "Model/Project/Data/Archive" or normalized.startswith("Model/Project/Data/Archive/"):
                continue

            if self._is_omitted_myserver_reference(normalized):
                continue

            if exclude_viewcontroller and normalized.startswith("ViewController/"):
                continue

            if normalized.startswith("Model/Project/Images/"):
                continue

            if normalized.startswith("Model/Project/Data/"):
                if self._is_file_reference(normalized):
                    files.add(normalized)
                else:
                    folder_entry = self.normalize_path(normalized)
                    if folder_entry:
                        folders.add(folder_entry)
                continue

            if self._is_file_reference(normalized):
                files.add(normalized)
            else:
                folders.add(normalized)

        return folders, files

    def _collect_project_utilities_folders(self) -> Set[str]:
        """Collect every existing folder under Model/Project/Utilities.

        These folders are always added independently from the current
        ProjectFolderList.txt, so manually removing them from the text file will
        not prevent this script from restoring them on the next update.
        """
        folders: Set[str] = set()
        utilities_root = self.project_root / "Model" / "Project" / "Utilities"
        if not utilities_root.exists():
            return folders

        for current, dirnames, _filenames in os.walk(utilities_root):
            relative = self._to_project_relative(Path(current))
            if not relative:
                continue
            if self.should_exclude(relative):
                dirnames[:] = []
                continue
            dirnames[:] = [d for d in dirnames if not self.should_exclude(f"{relative}/{d}")]
            folders.add(relative)

        return folders

    def _collect_model_data_folders(self) -> Set[str]:
        folders: Set[str] = set()
        data_root = self.project_root / "Model" / "Project" / "Data"
        if not data_root.exists():
            return folders

        for current, dirnames, filenames in os.walk(data_root):
            relative = self._to_project_relative(Path(current))
            if not relative:
                continue
            if relative == "Model/Project/Data/Archive" or relative.startswith("Model/Project/Data/Archive/"):
                dirnames[:] = []
                continue
            if self.should_exclude(relative):
                dirnames[:] = []
                continue
            dirnames[:] = [d for d in dirnames if not self.should_exclude(f"{relative}/{d}")]

            if filenames or dirnames or relative == "Model/Project/Data":
                folders.add(relative)

        return folders

    def _collect_model_data_files(self) -> Set[str]:
        files: Set[str] = set()
        data_root = self.project_root / "Model" / "Project" / "Data"
        if not data_root.exists():
            return files

        for current, dirnames, filenames in os.walk(data_root):
            relative = self._to_project_relative(Path(current))
            if not relative:
                continue
            if relative == "Model/Project/Data/Archive" or relative.startswith("Model/Project/Data/Archive/"):
                dirnames[:] = []
                continue
            if self.should_exclude(relative):
                dirnames[:] = []
                continue
            dirnames[:] = [d for d in dirnames if not self.should_exclude(f"{relative}/{d}")]

            for filename in filenames:
                normalized = self.normalize_path(f"{relative}/{filename}", reduce_file_paths=False)
                if normalized:
                    files.add(normalized)

        return files

    def _collect_recursive_support_entries(self, relative_roots: Iterable[str]) -> tuple[Set[str], Set[str]]:
        folders: Set[str] = set()
        files: Set[str] = set()

        for relative_root in relative_roots:
            root_path = self.project_root / Path(relative_root)
            if not root_path.exists():
                continue

            if root_path.is_file():
                normalized = self.normalize_path(relative_root, reduce_file_paths=False)
                if normalized:
                    files.add(normalized)
                continue

            for current, dirnames, filenames in os.walk(root_path):
                relative = self._to_project_relative(Path(current))
                if not relative:
                    continue
                if self.should_exclude(relative):
                    dirnames[:] = []
                    continue
                dirnames[:] = [d for d in dirnames if not self.should_exclude(f"{relative}/{d}")]

                folders.add(relative)

                for filename in filenames:
                    normalized = self.normalize_path(f"{relative}/{filename}", reduce_file_paths=False)
                    if normalized:
                        files.add(normalized)

        return folders, files

    def _collect_workflow_image_folders(self) -> Set[str]:
        return set(MINIMAL_IMAGE_FOLDERS)

    def _collect_mainui_module_files(self) -> Set[str]:
        files: Set[str] = set()
        mainui_root = self.project_root / "ViewController" / "0-MainUI"
        pending = sorted(MAINUI_MODULE_SEEDS)
        visited: Set[str] = set()

        while pending:
            relative_path = pending.pop()
            if relative_path in visited:
                continue
            visited.add(relative_path)

            file_path = mainui_root / relative_path
            if not file_path.exists() or not file_path.is_file():
                continue

            project_relative = self._to_project_relative(file_path)
            if project_relative:
                files.add(project_relative)

            if file_path.suffix.lower() != ".py":
                continue

            for dependency in self._resolve_mainui_local_dependencies(file_path, mainui_root):
                if dependency not in visited:
                    pending.append(dependency)

        return files

    def _collect_mainui_font_files(self) -> Set[str]:
        files: Set[str] = set()
        fonts_root = self.project_root / "ViewController" / "0-MainUI" / "fonts"
        if not fonts_root.exists() or not fonts_root.is_dir():
            return files

        for candidate in sorted(fonts_root.iterdir()):
            if not candidate.is_file():
                continue

            project_relative = self._to_project_relative(candidate)
            if project_relative:
                files.add(project_relative)

        return files

    def _resolve_mainui_local_dependencies(self, file_path: Path, mainui_root: Path) -> Set[str]:
        dependencies: Set[str] = set()

        try:
            tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
        except (OSError, SyntaxError, UnicodeDecodeError):
            return dependencies

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    dependencies.update(self._resolve_import_target(alias.name, mainui_root))
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module or ""
                dependencies.update(self._resolve_import_target(module_name, mainui_root))

                if module_name in {"ext", "Dialogs"}:
                    package_root = mainui_root / module_name
                    init_file = package_root / "__init__.py"
                    if init_file.exists():
                        dependencies.add(init_file.relative_to(mainui_root).as_posix())

                    if any(alias.name == "*" for alias in node.names):
                        dependencies.update(self._collect_package_python_files(package_root, mainui_root))
                    else:
                        for alias in node.names:
                            candidate = package_root / f"{alias.name}.py"
                            if candidate.exists():
                                dependencies.add(candidate.relative_to(mainui_root).as_posix())

        return dependencies

    def _resolve_import_target(self, module_name: str, mainui_root: Path) -> Set[str]:
        if not module_name:
            return set()

        candidate = mainui_root / Path(*module_name.split("."))
        if candidate.with_suffix(".py").exists():
            return {candidate.with_suffix(".py").relative_to(mainui_root).as_posix()}

        if candidate.is_dir() and (candidate / "__init__.py").exists():
            return {(candidate / "__init__.py").relative_to(mainui_root).as_posix()}

        return set()

    def _collect_package_python_files(self, package_root: Path, mainui_root: Path) -> Set[str]:
        files: Set[str] = set()
        if not package_root.exists() or not package_root.is_dir():
            return files

        for candidate in package_root.glob("*.py"):
            files.add(candidate.relative_to(mainui_root).as_posix())

        return files

    def _is_allowed_workflow_image_path(self, path: str) -> bool:
        normalized = path.replace("\\", "/").strip("/")
        return normalized in MINIMAL_IMAGE_FOLDERS

    def _is_file_reference(self, path: str) -> bool:
        source_path, destination_path = self._split_manifest_copy_entry(path)
        pure_path = PurePosixPath(destination_path or source_path)
        if pure_path.suffix.lower() in KNOWN_FILE_EXTENSIONS:
            return True

        candidate = self.project_root / Path(source_path)
        if candidate.is_file():
            return True
        if candidate.is_dir():
            return False

        return False

    def _collect_session_json_folders(self) -> Set[str]:
        folders: Set[str] = set()
        if not self.session_json_dir.exists():
            return folders

        for json_file in sorted(self.session_json_dir.glob(SESSION_JSON_GLOB)):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                print(f"Warning: could not read {json_file}: {exc}")
                continue

            if not isinstance(data, list):
                continue

            for item in data:
                if not isinstance(item, dict):
                    continue
                setting_name = str(item.get("Setting", ""))
                for field_name in ("CurrentValue", "DefaultValue"):
                    value = item.get(field_name)
                    if not isinstance(value, str):
                        continue
                    if not self._looks_like_path_setting(setting_name, value):
                        continue
                    normalized = self.normalize_path(value)
                    if normalized:
                        if normalized.startswith("ViewController/"):
                            continue
                        if normalized.startswith("Model/Project/Images/"):
                            continue
                        folders.add(normalized)

        return folders

    def _scan_filesystem_folders(self) -> Set[str]:
        """Optionally discover real folders under Model and ViewController.

        This is opt-in because ProjectFolderList.txt is a curated inventory, not
        necessarily a full filesystem dump.
        """
        folders: Set[str] = set()
        for base in (self.project_root / "Model", self.project_root / "ViewController"):
            if not base.exists():
                continue
            for current, dirnames, _filenames in os.walk(base):
                relative = self._to_project_relative(Path(current))
                if not relative:
                    continue
                if self.should_exclude(relative):
                    dirnames[:] = []
                    continue
                dirnames[:] = [d for d in dirnames if not self.should_exclude(f"{relative}/{d}")]
                folders.add(relative)
        return folders

    def _looks_like_path_setting(self, setting_name: str, value: str) -> bool:
        value = value.strip()
        if not value or value in {".", "None", "[]", "[", "]"}:
            return False
        if "/" not in value and "\\" not in value:
            return False

        leaf_setting_name = setting_name.split(".")[-1]
        if SETTING_NAME_RE.search(leaf_setting_name):
            return True

        lower_value = value.lower().rstrip("’'\"` ")
        return any(lower_value.endswith(ext) for ext in KNOWN_FILE_EXTENSIONS)


    @staticmethod
    def _split_manifest_copy_entry(path: str) -> tuple[str, Optional[str]]:
        if "=>" in path:
            source_path, destination_path = path.split("=>", 1)
            return source_path.strip(), destination_path.strip()
        return path.strip(), None

    @classmethod
    def _manifest_entry_destination(cls, path: str) -> str:
        _source_path, destination_path = cls._split_manifest_copy_entry(path)
        return destination_path or path.strip()

    @classmethod
    def _is_omitted_myserver_reference(cls, path: str) -> bool:
        destination = cls._manifest_entry_destination(path)
        return path.strip() in OMITTED_SOURCE_MYSERVER_REFERENCES or destination in OMITTED_SOURCE_MYSERVER_REFERENCES

    def normalize_path(self, raw_path: object, reduce_file_paths: bool = True) -> Optional[str]:
        if not isinstance(raw_path, str):
            return None

        path = raw_path.strip().strip("[]")
        path = re.sub(r"[’'\"`]+$", "", path).strip()
        if not path or path in {".", "None"}:
            return None

        path = path.replace("\\", "/").replace("’", "")
        if "=>" in path:
            source_path, destination_path = self._split_manifest_copy_entry(path)
            if self._is_omitted_myserver_reference(destination_path or source_path):
                return None
            return f"{source_path} => {destination_path}"

        if self._is_omitted_myserver_reference(path):
            return None

        lower_path = path.lower()

        for marker in PROJECT_ABSOLUTE_MARKERS:
            idx = lower_path.find(marker)
            if idx != -1:
                path = path[idx + len(marker) :]
                break

        pure_path = PurePosixPath(path)

        if reduce_file_paths and pure_path.suffix.lower() in KNOWN_FILE_EXTENSIONS:
            path = str(pure_path.parent)

        path = path.rstrip("/")
        if path in {"", ".", "/"}:
            return None

        if path == "Model/Developer":
            path = "Model/Project/Utilities"
        elif path.startswith("Model/Developer/"):
            path = "Model/Project/Utilities/" + path[len("Model/Developer/") :]
        elif path == "Model/Utilities":
            path = "Model/Project/Utilities"
        elif path.startswith("Model/Utilities/"):
            path = "Model/Project/Utilities/" + path[len("Model/Utilities/") :]

        if self.should_exclude(path):
            return None

        return path

    def should_exclude(self, path: str) -> bool:
        raw_normalized = path.replace("\\", "/").strip().rstrip("/")
        normalized = raw_normalized.strip("/")
        parts = normalized.split("/") if normalized else []

        if any(part in EXCLUDED_SEGMENTS for part in parts):
            return True
        if raw_normalized.lower() in {folder.rstrip('/').lower() for folder in STATIC_EXTERNAL_FOLDERS}:
            return True
        if ".duplicity" in parts:
            return True
        if self.is_model_developer_reference(normalized):
            return True
        if self.is_project_utilities_reference_reference(normalized):
            return True
        if normalized == "ViewController/Developer" or normalized.startswith("ViewController/Developer/"):
            return True
        return False

    @staticmethod
    def is_model_developer_reference(path: str) -> bool:
        normalized = path.replace("\\", "/").strip("/")
        return normalized == "Model/Developer" or normalized.startswith("Model/Developer/")

    @staticmethod
    def is_old_model_utilities_reference(path: str) -> bool:
        normalized = path.replace("\\", "/").strip("/")
        return normalized == "Model/Utilities" or normalized.startswith("Model/Utilities/")

    @staticmethod
    def is_project_utilities_reference_reference(path: str) -> bool:
        normalized = path.replace("\\", "/").strip("/")
        return normalized == "Model/Project/Utilities/Reference" or normalized.startswith(
            "Model/Project/Utilities/Reference/"
        )

    def _assert_no_deprecated_model_references(self, folders: Iterable[str]) -> None:
        forbidden = sorted(
            path
            for path in folders
            if self.is_model_developer_reference(path)
            or self.is_old_model_utilities_reference(path)
            or self.is_project_utilities_reference_reference(path)
        )
        if forbidden:
            preview = "\n".join(forbidden[:20])
            raise ValueError(
                "ProjectFolderList.py refused to write deprecated or excluded Model references. "
                "Use Model/Project/Utilities instead, excluding Model/Project/Utilities/Reference. "
                f"Forbidden entries found:\n{preview}"
            )

    def _to_project_relative(self, path: Path) -> Optional[str]:
        try:
            return path.resolve().relative_to(self.project_root).as_posix()
        except ValueError:
            return None

    @staticmethod
    def sort_key(path: str) -> tuple[str, str]:
        lower = path.lower()
        if path.startswith("/"):
            first = "/" + path.strip("/").split("/")[0].lower()
        elif re.match(r"^[a-z]:/", lower):
            first = lower.split("/", 1)[0]
        else:
            first = lower.split("/", 1)[0]
        return first, lower


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rebuild/update ProjectFolderList.txt")
    parser.add_argument("--dry-run", action="store_true", help="Print generated list instead of writing.")
    parser.add_argument("--scan", action="store_true", help="Also scan real folders under Model and ViewController.")
    parser.add_argument("--no-existing", action="store_true", help="Do not seed from current ProjectFolderList.txt.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    builder = ProjectFolderListBuilder(ProjectFolderListBuilder.find_project_root())
    folders = builder.build(include_existing=not args.no_existing, scan_filesystem=args.scan)

    if args.dry_run:
        print("\n".join(folders))
        print(f"\n# {len(folders)} folders")
        return 0

    builder.write(folders)
    print(f"Updated {builder.project_list_path} with {len(folders)} folders.")
    if builder.main_ui_project_list_path != builder.project_list_path:
        print(f"Updated {builder.main_ui_project_list_path} with {len(folders)} folders.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
