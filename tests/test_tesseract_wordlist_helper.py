import os
import sys
import tempfile
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
HELPERS_DIR = os.path.join(REPO_ROOT, "ViewController", "0-MainUI", "helpers")
if HELPERS_DIR not in sys.path:
    sys.path.insert(0, HELPERS_DIR)

from tesseract_wordlist_helper import (
    update_tesseract_wordlist_for_variant,
    update_tesseract_wordlist_from_text,
)


class TesseractWordlistHelperTests(unittest.TestCase):
    def test_updates_wordlist_with_unique_words(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "tesseract_wordlist.txt")
            updated_path = update_tesseract_wordlist_from_text(
                "Alpha beta, alpha; gamma",
                project_root=tmpdir,
                output_path=output_path,
            )

            self.assertEqual(updated_path, output_path)
            with open(output_path, "r", encoding="utf-8") as handle:
                stored_words = [line.strip() for line in handle if line.strip()]

            self.assertEqual(stored_words, ["alpha", "beta", "gamma"])

    def test_updates_wordlist_for_variant_words(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "tesseract_wordlist.txt")
            updated_path = update_tesseract_wordlist_for_variant(
                "Alpha",
                "beta",
                project_root=tmpdir,
                output_path=output_path,
            )

            self.assertEqual(updated_path, output_path)
            with open(output_path, "r", encoding="utf-8") as handle:
                stored_words = [line.strip() for line in handle if line.strip()]

            self.assertEqual(stored_words, ["alpha", "beta"])


if __name__ == "__main__":
    unittest.main()
