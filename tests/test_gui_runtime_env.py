import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
MAINUI_DIR = REPO_ROOT / "ViewController" / "0-MainUI"
if str(MAINUI_DIR) not in sys.path:
    sys.path.insert(0, str(MAINUI_DIR))

import helpers.gui_runtime_env as gui_runtime_env


class GuiRuntimeEnvTests(unittest.TestCase):
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
