from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


WRITER_DIR = Path(__file__).resolve().parents[1] / "ViewController" / "4-PostProcess"
if str(WRITER_DIR) not in sys.path:
    sys.path.insert(0, str(WRITER_DIR))


def _load_writer_module():
    module_path = WRITER_DIR / "MyWriter.py"
    spec = importlib.util.spec_from_file_location("test_mywriter_runtime", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _TextEdit:
    def toPlainText(self) -> str:
        return "Matthew 1:1 Publication text"


class _StatusBar:
    def showMessage(self, _message: str, _timeout: int) -> None:
        pass


class MyWriterModuleExportTests(unittest.TestCase):
    def test_exports_module_sources_to_writer_owned_project_folders(self) -> None:
        module = _load_writer_module()
        with tempfile.TemporaryDirectory() as directory:
            writer = SimpleNamespace(
                current_project_root=directory,
                current_project_name="Test Project",
                filename="",
                ui=SimpleNamespace(textEdit=_TextEdit()),
                statusBar=lambda: _StatusBar(),
            )

            esword_path = module.Main._export_bible_module_source(
                writer, "e-Sword", "Esword", ".bblx.txt", "utf-8"
            )
            theword_path = module.Main._export_bible_module_source(
                writer, "theWord", "TheWord", ".nt", "utf-8-sig"
            )

            self.assertEqual("Matthew 1:1 Publication text", Path(esword_path).read_text(encoding="utf-8"))
            self.assertEqual("Matthew 1:1 Publication text", Path(theword_path).read_text(encoding="utf-8-sig"))
            self.assertTrue(Path(theword_path).read_bytes().startswith(b"\xef\xbb\xbf"))


if __name__ == "__main__":
    unittest.main()