from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys


HELPERS_DIR = Path(__file__).resolve().parents[1] / "ViewController" / "0-MainUI" / "helpers"
if str(HELPERS_DIR) not in sys.path:
    sys.path.insert(0, str(HELPERS_DIR))

from SessionManager import SessionManager
from LocalFileDrop import LocalFileDropMixin


class CurrentPageLoadProbe(LocalFileDropMixin):
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        self._file_drop_image_handler = None
        self._file_drop_text_handler = None
        self.loaded_paths = []

    def _module_progress_label(self):
        return "MyProbe"

    def begin_visible_file_load(self, _label, _path):
        return None

    def end_visible_file_load(self, _label):
        return None


class SessionManagerCurrentPageTests(unittest.TestCase):
    def test_page_state_records_number_path_and_updating_module_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            session_dir = Path(temp_dir) / "sessions"
            page_path = Path(temp_dir) / "Demo_Page_0012.tif"
            page_path.write_bytes(b"image")
            manager = SessionManager(str(session_dir))

            state = manager.set_active_project_page_state(
                str(page_path),
                module_name="MyServer",
            )

            self.assertEqual(12, state["page_number"])
            self.assertEqual(str(page_path.resolve()), state["page_path"])
            self.assertEqual("MyServer", state["updated_by"])
            self.assertEqual(state, manager.get_active_project_page_state())
            self.assertEqual(12, manager.get_active_project_page())

    def test_explicit_page_number_supports_artifact_names_without_page_digits(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            session_dir = Path(temp_dir) / "sessions"
            page_path = Path(temp_dir) / "current-source.tif"
            page_path.write_bytes(b"image")
            manager = SessionManager(str(session_dir))

            state = manager.set_active_project_page_state(
                str(page_path),
                page_number=7,
                module_name="MyPixler",
            )

            self.assertEqual(7, state["page_number"])
            self.assertEqual("MyPixler", state["updated_by"])

    def test_common_file_handler_records_successful_page_load(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            page_path = Path(temp_dir) / "Book_Page_0004.png"
            page_path.write_bytes(b"image")
            manager = SessionManager(str(Path(temp_dir) / "sessions"))
            probe = CurrentPageLoadProbe(manager)

            probe.run_file_handler_with_feedback(
                "Image file",
                str(page_path),
                lambda path: probe.loaded_paths.append(path),
            )

            self.assertEqual([str(page_path)], probe.loaded_paths)
            self.assertEqual(4, manager.get_active_project_page())
            self.assertEqual("MyProbe", manager.get_active_project_page_state()["updated_by"])

    def test_common_loader_restores_shared_page_through_image_handler(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            page_path = Path(temp_dir) / "Book_Page_0009.tif"
            page_path.write_bytes(b"image")
            manager = SessionManager(str(Path(temp_dir) / "sessions"))
            manager.set_active_project_page_state(str(page_path), module_name="MyServer")
            probe = CurrentPageLoadProbe(manager)
            probe._file_drop_image_handler = probe.loaded_paths.append

            restored = probe.restore_current_project_page()

            self.assertTrue(restored)
            self.assertEqual([str(page_path)], probe.loaded_paths)
            state = manager.get_active_project_page_state()
            self.assertEqual(9, state["page_number"])
            self.assertEqual("MyProbe", state["updated_by"])

    def test_common_file_handler_does_not_record_rejected_or_failed_loads(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            page_path = Path(temp_dir) / "Book_Page_0011.png"
            page_path.write_bytes(b"image")
            manager = SessionManager(str(Path(temp_dir) / "sessions"))
            probe = CurrentPageLoadProbe(manager)

            result = probe.run_file_handler_with_feedback(
                "Image file",
                str(page_path),
                lambda _path: False,
            )
            self.assertFalse(result)
            self.assertEqual("", manager.get_active_project_page_state()["page_path"])

            with self.assertRaisesRegex(RuntimeError, "load failed"):
                probe.run_file_handler_with_feedback(
                    "Image file",
                    str(page_path),
                    lambda _path: (_ for _ in ()).throw(RuntimeError("load failed")),
                )
            self.assertEqual("", manager.get_active_project_page_state()["page_path"])


if __name__ == "__main__":
    unittest.main()