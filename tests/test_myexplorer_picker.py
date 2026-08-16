from __future__ import annotations

import os
import sys
import tempfile
import unittest
import importlib.util
from pathlib import Path

from PyQt5 import QtWidgets as qtw

from Core.myexplorer_picker import build_myexplorer_selection_command
from Core.workflow_wizard_actions import _ensure_module_menu_shortcuts


HELPERS_DIR = Path(__file__).resolve().parents[1] / "ViewController" / "0-MainUI" / "helpers"
MAIN_UI_DIR = HELPERS_DIR.parent
if str(HELPERS_DIR) not in sys.path:
    sys.path.insert(0, str(HELPERS_DIR))

from LocalFileDrop import MyExplorerPickerProcess


class MyExplorerPickerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = qtw.QApplication.instance() or qtw.QApplication([])

    def test_command_uses_myexplorer_file_selection_mode(self) -> None:
        command, output_file = build_myexplorer_selection_command(
            "Open Image",
            tempfile.gettempdir(),
            "file",
        )

        self.assertTrue(command[1].endswith("MyExplorer.py"))
        self.assertIn("--select-file", command)
        self.assertEqual(output_file, command[command.index("--output-file") + 1])

    def test_non_modal_picker_returns_myexplorer_selection(self) -> None:
        selected_paths = []
        picker = MyExplorerPickerProcess(
            "Open Image",
            tempfile.gettempdir(),
            selected_paths.append,
        )
        try:
            with open(picker.output_file, "w", encoding="utf-8") as handle:
                handle.write("/tmp/example.tif")

            picker._finish()

            self.assertEqual(["/tmp/example.tif"], selected_paths)
            self.assertFalse(os.path.exists(picker.output_file))
        finally:
            picker.process.kill()

    def test_myserver_menus_use_myexplorer_and_project_settings(self) -> None:
        module_path = MAIN_UI_DIR / "MyServerUI.py"
        spec = importlib.util.spec_from_file_location("test_myserver_ui", module_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        window = qtw.QMainWindow()
        ui = module.Ui_MainUI()
        ui.setupUi(window)
        _ensure_module_menu_shortcuts(window)

        file_actions = [action.text() for action in ui.menuFile.actions()]
        project_actions = [action.text() for action in ui.menuProject.actions()]
        font_actions = [action.text() for action in ui.menuGlyphs.actions()]
        training_actions = [action.text() for action in ui.menuGround_Truth_2.actions()]
        self.assertIn("MyExplorer", file_actions)
        self.assertIn("Open Image", file_actions)
        self.assertIn("Open Text", file_actions)
        self.assertNotIn("MyExplorer", project_actions)
        self.assertIn("Project Settings", project_actions)
        self.assertEqual(["MyGlypher"], font_actions)
        self.assertIn("MyTrainer", training_actions)
        self.assertNotIn("Update Wordlists", training_actions)
        self.assertNotIn("Setup Training", training_actions)
        self.assertFalse(hasattr(ui, "actionCreate_e_Sword_Bible_Module"))
        self.assertFalse(hasattr(ui, "actionCreate_theWord_Bible_Module"))
        self.assertFalse(hasattr(ui, "actionPreferences"))
        self.assertFalse(hasattr(ui, "actionPrefernces"))

        shortcut_actions = [
            action for action in window.findChildren(qtw.QAction)
            if not action.shortcut().isEmpty()
        ]
        self.assertTrue(shortcut_actions)
        self.assertTrue(all(action.isShortcutVisibleInContextMenu() for action in shortcut_actions))

        self.assertEqual("FROMVS", ui.Image.font().family())
        self.assertIn("Open Image from the File Menu", ui.Image.text())
        self.assertIn("Open Text from the File Menu", ui.OCRText.placeholderText())
        self.assertEqual("#aeb4bc", ui.Image.palette().color(ui.Image.foregroundRole()).name())

        ui.OCRText.setPlainText("Loaded text")
        self.assertEqual("Loaded text", ui.OCRText.toPlainText())

    def test_tif_to_bmp_action_is_in_myglypher_tools(self) -> None:
        module_path = MAIN_UI_DIR.parent / "1-PreProcess" / "MyGlypherUI.py"
        spec = importlib.util.spec_from_file_location("test_myglypher_ui", module_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        window = qtw.QMainWindow()
        ui = module.Ui_Glypher()
        ui.setupUi(window)

        tool_actions = [action.text() for action in ui.menuTools.actions()]
        self.assertIn("Convert tif To bmp", tool_actions)

    def test_wordlist_and_setup_menus_are_owned_by_mytrainer(self) -> None:
        module_path = MAIN_UI_DIR.parent / "2-TrainTesseract" / "MyTrainerUI.py"
        spec = importlib.util.spec_from_file_location("test_mytrainer_ui", module_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        window = qtw.QMainWindow()
        ui = module.Ui_Trainer()
        ui.setupUi(window)

        tool_actions = [action.text() for action in ui.menuTools.actions()]
        wordlist_actions = [action.text() for action in ui.menuUpdate_Wordlists.actions()]
        setup_actions = [action.text() for action in ui.menuSetup_Training.actions()]
        self.assertIn("Update Wordlists", tool_actions)
        self.assertIn("Setup Training", tool_actions)
        self.assertEqual(
            ["Update Greek Wordlist", "Update Hebrew Wordlist", "Update Latin Wordlist"],
            wordlist_actions,
        )
        self.assertEqual(["Select Language Model", "Select Fonts"], setup_actions)

        designer_dir = MAIN_UI_DIR.parents[1] / "Developer" / "QtDesignerUI"
        menu_owners = []
        for ui_path in designer_dir.glob("*.ui"):
            ui_source = ui_path.read_text(encoding="utf-8")
            if "menuUpdate_Wordlists" in ui_source or "menuSetup_Training" in ui_source:
                menu_owners.append(ui_path.name)
        self.assertEqual(["MyTrainerUI.ui"], sorted(menu_owners))

    def test_bible_module_menu_actions_are_owned_by_mywriter(self) -> None:
        designer_dir = MAIN_UI_DIR.parents[1] / "Developer" / "QtDesignerUI"
        action_definition = '<action name="actionCreate_e_Sword_Bible_Module">'
        definition_owners = []
        for ui_path in designer_dir.glob("*.ui"):
            ui_source = ui_path.read_text(encoding="utf-8")
            if action_definition in ui_source:
                definition_owners.append(ui_path.name)
        self.assertEqual(["MyWriterUI.ui"], sorted(definition_owners))

        writer_source = (designer_dir / "MyWriterUI.ui").read_text(encoding="utf-8")
        self.assertIn('<addaction name="actionCreate_e_Sword_Bible_Module"/>', writer_source)
        self.assertIn('<addaction name="actionCreate_theWord_Bible_Module"/>', writer_source)


if __name__ == "__main__":
    unittest.main()