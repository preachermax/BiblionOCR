from __future__ import annotations

import os
import sys
import tempfile
import unittest
import importlib.util
from pathlib import Path
from unittest import mock

from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5 import QtWidgets as qtw

from Core.myexplorer_picker import build_myexplorer_selection_command, run_myexplorer_selection
from Core.workflow_wizard_actions import (
    PAGE_WORKFLOW_WIZARD_ICON,
    PROJECT_WORKFLOW_WIZARD_ICON,
    _ensure_module_menu_shortcuts,
    _explorer_get_save_file_name,
    install_myexplorer_method_aliases,
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

    def test_generated_image_alias_discards_unaccepted_qt_checked_argument(self) -> None:
        calls = []

        class Window:
            def loadRefImg(self):
                calls.append("load")

        window = Window()
        install_myexplorer_method_aliases(window)

        window.open_image_with_myexplorer(True)

        self.assertEqual(["load"], calls)

    def test_generated_image_alias_preserves_arguments_accepted_by_target(self) -> None:
        calls = []

        class Window:
            def loadImage(self, checked):
                calls.append(checked)

        window = Window()
        install_myexplorer_method_aliases(window)

        window.open_image_with_myexplorer(True)

        self.assertEqual([True], calls)

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
        compact_runtime_source = "".join(runtime_source.split())
        self.assertIn(
            "self.selectFolderButton.setEnabled(self.select_modeandself.allow_folder_selection)",
            compact_runtime_source,
        )
        self.assertIn(
            "self.selectFileButton.setEnabled(self.select_modeandself.allow_file_selection)",
            compact_runtime_source,
        )
        self.assertIn(
            "if(self.select_modeandself.start_dirandos.path.isdir(self.start_dir)):",
            compact_runtime_source,
        )
        self.assertIn("ifnotself.isVisible():", compact_runtime_source)
        self.assertIn(
            "QtCore.QTimer.singleShot(0,self._size_tree_columns)",
            compact_runtime_source,
        )
        self.assertIn("self.model.directoryLoaded.connect", compact_runtime_source)
        self.assertIn("QtWidgets.QStyle.PM_ScrollBarExtent", compact_runtime_source)
        self.assertIn("proportions=(0.48,0.13,0.17)", compact_runtime_source)
        self.assertIn("available_width-assigned_width", compact_runtime_source)

        expected_shortcuts = {
            "actionSelect_Folder": "Ctrl+Return",
            "actionOpen_Trash": "Ctrl+Shift+T",
            "actionRestore_From_Trash": "Ctrl+Alt+T",
            "actionRestore_From_Backup": "Ctrl+Alt+B",
            "actionExit": "Ctrl+Q",
            "actionBulk_Rename": "Ctrl+Shift+R",
            "actionNew_folder": "Ctrl+Shift+N",
            "actionCut": "Ctrl+X",
            "actionCopy": "Ctrl+C",
            "actionPaste": "Ctrl+V",
            "actionDelete": "Del",
            "actionMove": "Ctrl+Shift+M",
            "actionUndo": "Ctrl+Z",
            "actionRedo": "Ctrl+Shift+Z",
        }

        for action_name, shortcut in expected_shortcuts.items():
            action = getattr(ui, action_name)
            self.assertEqual(shortcut, action.shortcut().toString())
            self.assertTrue(action.isShortcutVisibleInContextMenu())

        edit_actions = [action.text() for action in ui.menuEdit.actions()]
        self.assertEqual(
            ["New folder", "Cut", "Copy", "Paste", "Delete", "Move", "Undo", "Redo"],
            edit_actions,
        )

        window.close()

    def test_myexplorer_runtime_reuses_edit_actions_and_reverses_file_operations(self) -> None:
        os.environ["BIBLION_GUI_ENV_SANITIZED"] = "1"
        module_path = MAIN_UI_DIR / "MyExplorer.py"
        spec = importlib.util.spec_from_file_location("test_myexplorer_runtime", module_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as temporary_directory:
            window = module.MyFileBrowser(
                start_dir=temporary_directory,
                select_mode=True,
                selection_kind="folder",
            )
            try:
                self.assertEqual(
                    [
                        window.actionNew_folder,
                        window.actionCut,
                        window.actionCopy,
                        window.actionPaste,
                        window.actionDelete,
                        window.actionMove,
                        window.actionUndo,
                        window.actionRedo,
                    ],
                    list(window._edit_actions()),
                )
                self.assertEqual(
                    "Ctrl+Alt+W",
                    window.actionPage_Workflow_Wizard.shortcut().toString(),
                )
                self.assertTrue(
                    window.actionPage_Workflow_Wizard.isShortcutVisibleInContextMenu()
                )

                context_labels = []

                def capture_context_menu(menu, *_args):
                    context_labels.extend(
                        action.text()
                        for action in menu.actions()
                        if not action.isSeparator()
                    )

                with mock.patch.object(
                    module.QtWidgets.QMenu,
                    "exec_",
                    new=capture_context_menu,
                ), mock.patch.object(
                    module,
                    "append_default_context_actions",
                ):
                    window.context_menu(module.QtCore.QPoint(-1, -1))

                for label in (
                    "New folder",
                    "Cut",
                    "Copy",
                    "Paste",
                    "Delete",
                    "Move",
                    "Undo",
                    "Redo",
                ):
                    self.assertIn(label, context_labels)

                created_path = os.path.join(temporary_directory, "created")
                os.mkdir(created_path)
                operation = {
                    "kind": "create",
                    "path": created_path,
                    "stash": window._undo_stash_path(created_path),
                }
                window._record_file_operation(operation)
                window.undo_file_operation()
                self.assertFalse(os.path.exists(created_path))
                self.assertTrue(window.actionRedo.isEnabled())

                window.redo_file_operation()
                self.assertTrue(os.path.isdir(created_path))
                self.assertTrue(window.actionUndo.isEnabled())

                moved_path = os.path.join(temporary_directory, "moved")
                os.rename(created_path, moved_path)
                window._record_file_operation({
                    "kind": "move",
                    "source": created_path,
                    "destination": moved_path,
                })
                window.undo_file_operation()
                self.assertTrue(os.path.isdir(created_path))
                window.redo_file_operation()
                self.assertTrue(os.path.isdir(moved_path))
            finally:
                window.close()

    def test_myexplorer_copy_cut_paste_and_delete_are_undoable(self) -> None:
        os.environ["BIBLION_GUI_ENV_SANITIZED"] = "1"
        module_path = MAIN_UI_DIR / "MyExplorer.py"
        spec = importlib.util.spec_from_file_location("test_myexplorer_file_actions", module_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as temporary_directory:
            window = module.MyFileBrowser(
                start_dir=temporary_directory,
                select_mode=True,
                selection_kind="folder",
            )
            source = os.path.join(temporary_directory, "source.txt")
            Path(source).write_text("content", encoding="utf-8")
            destination_directory = os.path.join(temporary_directory, "destination")
            os.mkdir(destination_directory)
            try:
                with mock.patch.object(window, "_selected_existing_path", return_value=source), mock.patch.object(
                    window, "_current_directory", return_value=destination_directory
                ):
                    window.copy_selected()
                    window.paste_into_current_directory()

                copied_path = os.path.join(destination_directory, "source.txt")
                self.assertTrue(os.path.isfile(copied_path))
                window.undo_file_operation()
                self.assertFalse(os.path.exists(copied_path))
                window.redo_file_operation()
                self.assertTrue(os.path.isfile(copied_path))

                with mock.patch.object(window, "_selected_existing_path", return_value=source), mock.patch.object(
                    window, "_current_directory", return_value=destination_directory
                ):
                    window.cut_selected()
                    window.paste_into_current_directory()

                moved_path = os.path.join(destination_directory, "source (1).txt")
                self.assertFalse(os.path.exists(source))
                self.assertTrue(os.path.isfile(moved_path))
                window.undo_file_operation()
                self.assertTrue(os.path.isfile(source))

                with mock.patch.object(window, "_selected_existing_path", return_value=source), mock.patch.object(
                    module.QtWidgets.QMessageBox,
                    "question",
                    return_value=module.QtWidgets.QMessageBox.Yes,
                ):
                    window.delete_selected()

                self.assertFalse(os.path.exists(source))
                window.undo_file_operation()
                self.assertTrue(os.path.isfile(source))
                window.redo_file_operation()
                self.assertFalse(os.path.exists(source))
            finally:
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

    def test_workflow_wizard_actions_use_transparent_resource_icons(self) -> None:
        import UI_Icons  # noqa: F401

        icons_directory = HELPERS_DIR / "Icons"
        for icon_name in ("stage.png", "wand.png", "wand2.png", "wizard-hat.png"):
            image = qtg.QImage(str(icons_directory / icon_name))
            self.assertFalse(image.isNull(), icon_name)
            self.assertTrue(image.hasAlphaChannel(), icon_name)
            self.assertEqual(0, image.pixelColor(0, 0).alpha(), icon_name)
            alpha_image = image.convertToFormat(qtg.QImage.Format_Alpha8)
            self.assertGreater(
                max(alpha_image.constBits().asstring(alpha_image.byteCount())),
                0,
                icon_name,
            )

        window = qtw.QMainWindow()
        window.menuFile = window.menuBar().addMenu("File")
        window.actionProject_Workflow_Wizard = qtw.QAction(
            "Project Workflow Wizard",
            window,
        )
        with mock.patch(
            "Core.workflow_wizard_actions._install_close_confirmation"
        ):
            install_workflow_wizard_menu_actions(
                window,
                "MyServer",
                include_project_wizard=True,
                include_page_wizard=True,
            )

        self.assertEqual(":/Icons/Icons/wand.png", PAGE_WORKFLOW_WIZARD_ICON)
        self.assertEqual(":/Icons/Icons/wizard-hat.png", PROJECT_WORKFLOW_WIZARD_ICON)
        self.assertFalse(window.actionPage_Workflow_Wizard.icon().isNull())
        self.assertFalse(window.actionProject_Workflow_Wizard.icon().isNull())
        self.assertFalse(
            window.actionPage_Workflow_Wizard.icon().pixmap(32, 32).isNull()
        )
        self.assertFalse(
            window.actionProject_Workflow_Wizard.icon().pixmap(32, 32).isNull()
        )
        self.assertNotEqual(
            window.actionPage_Workflow_Wizard.icon().pixmap(32, 32).toImage(),
            window.actionProject_Workflow_Wizard.icon().pixmap(32, 32).toImage(),
        )
        window.close()

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