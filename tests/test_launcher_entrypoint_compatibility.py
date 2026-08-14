import importlib.util
import os
import sys
import unittest
from contextlib import contextmanager

from PyQt5 import QtWidgets

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


@contextmanager
def _temporary_sys_path(*paths):
    added_paths = []
    for path in paths:
        if path and path not in sys.path:
            sys.path.insert(0, path)
            added_paths.append(path)

    try:
        yield
    finally:
        for path in reversed(added_paths):
            if path in sys.path:
                sys.path.remove(path)


def _load_module(module_name, file_path):
    module_dir = os.path.dirname(file_path)
    shared_helpers_dir = os.path.join(REPO_ROOT, "ViewController", "0-MainUI", "helpers")
    local_helpers_dir = os.path.join(module_dir, "helpers")

    with _temporary_sys_path(module_dir, local_helpers_dir, shared_helpers_dir):
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module


class LauncherEntrypointCompatibilityTests(unittest.TestCase):
    def test_launcher_ui_module_exists(self):
        ui_path = os.path.join(REPO_ROOT, "ViewController", "0-MainUI", "MyLauncherUI.py")
        self.assertTrue(os.path.exists(ui_path), "Launcher UI module should exist")
        module = _load_module("launcher_ui_test_module", ui_path)
        self.assertTrue(hasattr(module, "Ui_MainUI"))

    def test_lexer_ui_exposes_boxer_class(self):
        ui_path = os.path.join(REPO_ROOT, "ViewController", "3-Process", "MyLexerUI.py")
        self.assertTrue(os.path.exists(ui_path), "Lexer UI module should exist")
        module = _load_module("lexer_ui_test_module", ui_path)
        self.assertTrue(hasattr(module, "Ui_Boxer"))

    def test_reader_helper_shim_exists(self):
        helper_path = os.path.join(REPO_ROOT, "ViewController", "0-MainUI", "helpers", "QtCropImage.py")
        self.assertTrue(os.path.exists(helper_path), "QtCropImage helper shim should exist")

    def test_lexer_window_initializes_without_optional_button_widget(self):
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        lexer_path = os.path.join(REPO_ROOT, "ViewController", "3-Process", "MyLexer.py")
        module = _load_module("lexer_window_test_module", lexer_path)
        window = module.MainWindow()
        self.assertTrue(hasattr(window, "ui"))
        app.quit()

    def test_versifier_window_initializes_with_empty_combo_values(self):
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        versifier_path = os.path.join(REPO_ROOT, "ViewController", "3-Process", "MyVersifier.py")
        module = _load_module("versifier_window_test_module", versifier_path)
        window = module.Ui_MainWindow()
        self.assertTrue(hasattr(window, "ui"))
        app.quit()


if __name__ == "__main__":
    unittest.main()
