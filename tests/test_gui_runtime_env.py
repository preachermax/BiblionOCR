import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
MAINUI_DIR = REPO_ROOT / "ViewController" / "0-MainUI"
if str(MAINUI_DIR) not in sys.path:
    sys.path.insert(0, str(MAINUI_DIR))

import helpers.gui_runtime_env as gui_runtime_env
from launchers.restore_desktop_launchers import CANONICAL_MODULES


class GuiRuntimeEnvTests(unittest.TestCase):
    def test_sanitized_process_still_installs_qt_runtime_policy(self) -> None:
        with patch.dict(os.environ, {gui_runtime_env._SANITIZED_MARKER: "1"}, clear=True):
            with patch.object(gui_runtime_env, "install_default_qt_font_policy") as install_policy:
                gui_runtime_env.sanitize_current_process_and_reexec()

        install_policy.assert_called_once_with()

    def test_myserver_desktop_identity_matches_generated_launcher(self) -> None:
        class FakeCoreApplication:
            application_name = None

            @classmethod
            def setApplicationName(cls, value):
                cls.application_name = value

        class FakeQtCore:
            QCoreApplication = FakeCoreApplication

        class FakeApplication:
            def setApplicationDisplayName(self, value):
                self.display_name = value

            def setDesktopFileName(self, value):
                self.desktop_file_name = value

        app = FakeApplication()
        with patch.object(gui_runtime_env.sys, "argv", [str(MAINUI_DIR / "MyServer.py")]):
            gui_runtime_env._prepare_qt_application_identity(FakeQtCore)
            gui_runtime_env._apply_qt_application_identity(app)

        self.assertEqual(FakeCoreApplication.application_name, "MyServer.py")
        self.assertEqual(app.display_name, "My Server")
        self.assertEqual(app.desktop_file_name, "My Server")

    def test_deferred_mylexer_has_no_desktop_identity_policy(self) -> None:
        class FakeApplication:
            def setApplicationName(self, _value):
                raise AssertionError("MyLexer identity must remain untouched")

        with patch.object(gui_runtime_env.sys, "argv", [str(MAINUI_DIR / "MyLexer.py")]):
            gui_runtime_env._apply_qt_application_identity(FakeApplication())

    def test_runtime_icons_match_generated_launcher_icons(self) -> None:
        for module_name, _label, icon_name in CANONICAL_MODULES:
            if module_name == "MyLexer":
                self.assertNotIn(module_name, gui_runtime_env._QT_APPLICATION_ICONS)
                continue
            self.assertEqual(gui_runtime_env._QT_APPLICATION_ICONS[module_name], icon_name)
            self.assertTrue(Path(gui_runtime_env._application_icon_path(module_name)).is_file())

    def test_application_icon_policy_overrides_top_level_window_icons(self) -> None:
        class FakeIcon:
            def __init__(self, path):
                self.path = path

            def isNull(self):
                return False

        class FakeQtGui:
            QIcon = FakeIcon

        class FakeObject:
            def __init__(self, _parent=None):
                pass

        class FakeEvent:
            Show = 1

        class FakeQtCore:
            QObject = FakeObject
            QEvent = FakeEvent

        class FakeWindow:
            def isWindow(self):
                return True

            def setWindowIcon(self, icon):
                self.icon = icon

        class FakeApplication:
            def __init__(self):
                self.existing_window = FakeWindow()

            def setWindowIcon(self, icon):
                self.icon = icon

            def topLevelWidgets(self):
                return [self.existing_window]

            def installEventFilter(self, event_filter):
                self.event_filter = event_filter

        class ShowEvent:
            def type(self):
                return FakeEvent.Show

        app = FakeApplication()
        with patch.object(gui_runtime_env.sys, "argv", [str(MAINUI_DIR / "MyResolver.py")]):
            gui_runtime_env._apply_qt_application_icon_policy(app, FakeQtCore, FakeQtGui)

        shown_window = FakeWindow()
        app.event_filter.eventFilter(shown_window, ShowEvent())

        self.assertEqual(Path(app.icon.path).name, "BiblionResolver2.png")
        self.assertIs(app.existing_window.icon, app.icon)
        self.assertIs(shown_window.icon, app.icon)

    def test_windows_application_identity_is_set_before_qt_startup(self) -> None:
        calls = []
        fake_ctypes = SimpleNamespace(
            windll=SimpleNamespace(
                shell32=SimpleNamespace(
                    SetCurrentProcessExplicitAppUserModelID=calls.append,
                )
            )
        )
        with patch.object(gui_runtime_env.sys, "platform", "win32"):
            with patch.dict(sys.modules, {"ctypes": fake_ctypes}):
                gui_runtime_env._set_windows_app_user_model_id("MyResolver")

        self.assertEqual(calls, ["preachermax.BiblionOCR.MyResolver"])

    def test_linux_without_qt_im_module_sets_xim(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(gui_runtime_env.sys, "platform", "linux"):
                with patch.object(gui_runtime_env.os, "execve", side_effect=AssertionError("execve")) as execve_mock:
                    with self.assertRaises(AssertionError):
                        gui_runtime_env.sanitize_current_process_and_reexec()

        self.assertTrue(execve_mock.called)
        env = execve_mock.call_args.args[2]
        self.assertEqual(env.get("QT_IM_MODULE"), "xim")

    def test_linux_overrides_existing_qt_im_module(self) -> None:
        with patch.dict(os.environ, {"QT_IM_MODULE": "ibus"}, clear=True):
            with patch.object(gui_runtime_env.sys, "platform", "linux"):
                with patch.object(gui_runtime_env.os, "execve", side_effect=AssertionError("execve")) as execve_mock:
                    with self.assertRaises(AssertionError):
                        gui_runtime_env.sanitize_current_process_and_reexec()

        self.assertTrue(execve_mock.called)
        env = execve_mock.call_args.args[2]
        self.assertEqual(env.get("QT_IM_MODULE"), "xim")


if __name__ == "__main__":
    unittest.main()
