from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


HELPERS_DIR = Path(__file__).resolve().parents[1] / "ViewController" / "0-MainUI" / "helpers"
if str(HELPERS_DIR) not in sys.path:
	sys.path.insert(0, str(HELPERS_DIR))

from tesseract_wordlist_helper import (
	extract_wordlist_words,
	update_tesseract_wordlist_for_variant,
	update_tesseract_wordlist_from_text,
)


class SharedWordlistUpdateTests(unittest.TestCase):
	def test_extract_words_preserves_greek_and_final_sigma(self) -> None:
		self.assertEqual({"λόγος", "θεός"}, extract_wordlist_words("Λόγος λόγος θεός"))

	def test_text_and_variant_updates_share_unicode_writer(self) -> None:
		with tempfile.TemporaryDirectory() as directory:
			output_path = Path(directory) / "feg.wordlist"
			update_tesseract_wordlist_from_text("Λόγος θεός", output_path=str(output_path))
			update_tesseract_wordlist_for_variant(
				"θεός",
				"κυρίου",
				output_path=str(output_path),
			)

			self.assertEqual(
				["θεός", "κυρίου", "λόγος"],
				output_path.read_text(encoding="utf-8").splitlines(),
			)


if __name__ == "__main__":
	unittest.main()