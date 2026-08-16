from __future__ import annotations

import os
import sys
import tempfile
import unittest
import importlib.util
from pathlib import Path
from unittest import mock

from PyQt5 import QtCore as qtc
from PyQt5 import QtWidgets as qtw

from Core.myexplorer_picker import build_myexplorer_selection_command, run_myexplorer_selection
from Core.workflow_wizard_actions import (
    _ensure_module_menu_shortcuts,
    _explorer_get_save_file_name,
    install_workflow_wizard_menu_actions,
)


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

        both_command, _ = build_myexplorer_selection_command(
            "Select Input",
            tempfile.gettempdir(),
            "both",
        )
        self.assertIn("--select-dir", both_command)
        self.assertIn("--select-file", both_command)

    def test_picker_wait_keeps_qt_event_loop_responsive(self) -> None:
        heartbeat = []

        class FakeProcess:
            finished = False

            def __init__(self, command):
                output_path = command[command.index("--output-file") + 1]

                def finish():
                    heartbeat.append("processed")
                    Path(output_path).write_text("/tmp/project", encoding="utf-8")
                    self.finished = True

                qtc.QTimer.singleShot(20, finish)

            def poll(self):
                return 0 if self.finished else None

        with mock.patch("Core.myexplorer_picker.subprocess.Popen", FakeProcess):
            selected = run_myexplorer_selection("Open Project", tempfile.gettempdir(), "directory")

        self.assertEqual("/tmp/project", selected)
        self.assertEqual(["processed"], heartbeat)

    def test_picker_waits_for_child_exit_after_selection_is_written(self) -> None:
        events = []

        class FakeProcess:
            exited = False

            def __init__(self, command):
                output_path = command[command.index("--output-file") + 1]

                def write_selection():
                    Path(output_path).write_text("/tmp/project", encoding="utf-8")
                    events.append("selection-written")

                def exit_process():
                    self.exited = True
                    events.append("child-exited")

                qtc.QTimer.singleShot(10, write_selection)
                qtc.QTimer.singleShot(30, exit_process)

            def poll(self):
                return 0 if self.exited else None

        with mock.patch("Core.myexplorer_picker.subprocess.Popen", FakeProcess):
            selected = run_myexplorer_selection("Open Project", tempfile.gettempdir(), "directory")
            events.append("caller-resumed")

        self.assertEqual("/tmp/project", selected)
        self.assertEqual(["selection-written", "child-exited", "caller-resumed"], events)

    def test_save_file_picker_uses_myexplorer_with_both_selectors(self) -> None:
        with mock.patch(
            "Core.workflow_wizard_actions.run_myexplorer_selection",
            return_value=tempfile.gettempdir(),
        ) as picker:
            selected, selected_filter = _explorer_get_save_file_name(
                caption="Save OCR Text",
                directory=os.path.join(tempfile.gettempdir(), "page.txt"),
            )

        self.assertEqual(os.path.join(tempfile.gettempdir(), "page.txt"), selected)
        self.assertEqual("", selected_filter)
        picker.assert_called_once_with("Save OCR Text", tempfile.gettempdir(), "both")

    def test_designer_owns_caller_enabled_file_and_folder_buttons(self) -> None:
        module_path = MAIN_UI_DIR / "MyExplorerUI.py"
        spec = importlib.util.spec_from_file_location("test_myexplorer_ui", module_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        window = qtw.QMainWindow()
        ui = module.Ui_Explorer()
        ui.setupUi(window)
        self.assertEqual("Select Folder", ui.selectFolderButton.text())
        self.assertEqual("Select File", ui.selectFileButton.text())
        self.assertFalse(ui.selectFolderButton.isVisible())
        self.assertFalse(ui.selectFileButton.isVisible())

        runtime_source = (MAIN_UI_DIR / "MyExplorer.py").read_text(encoding="utf-8")
        self.assertIn("self.selectFolderButton.setEnabled(self.select_mode and self.allow_folder_selection)", runtime_source)
        self.assertIn("self.selectFileButton.setEnabled(self.select_mode and self.allow_file_selection)", runtime_source)
        self.assertIn("if self.select_mode and self.start_dir and os.path.isdir(self.start_dir):", runtime_source)
        self.assertIn("if not self.isVisible():", runtime_source)
        self.assertIn("QtCore.QTimer.singleShot(0, self._size_tree_columns)", runtime_source)
        self.assertIn("self.model.directoryLoaded.connect", runtime_source)
        self.assertIn("QtWidgets.QStyle.PM_ScrollBarExtent", runtime_source)
        self.assertIn("proportions = (0.48, 0.13, 0.17)", runtime_source)
        self.assertIn("available_width - assigned_width", runtime_source)

        window.close()

    def test_myexplorer_does_not_install_close_confirmation(self) -> None:
        explorer = qtw.QMainWindow()
        other_module = qtw.QMainWindow()
        with mock.patch("Core.workflow_wizard_actions._install_close_confirmation") as install_close:
            install_workflow_wizard_menu_actions(
                explorer,
                "MyExplorer",
                include_project_wizard=False,
                include_page_wizard=False,
            )
            install_close.assert_not_called()

            install_workflow_wizard_menu_actions(
                other_module,
                "MyServer",
                include_project_wizard=False,
                include_page_wizard=False,
            )
            install_close.assert_called_once_with(other_module)

        explorer.close()
        other_module.close()

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

        self.assertEqual("", ui.Image.text())
        self.assertEqual("", ui.OCRText.placeholderText())

        runtime_source = (MAIN_UI_DIR / "MyServer.py").read_text(encoding="utf-8")
        self.assertNotIn("self.run_child_module('MyExplorer.py', project_path)", runtime_source)
        self.assertIn('color: #c7c7c7; background: transparent;', runtime_source)

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