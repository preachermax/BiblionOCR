import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PREPROCESS_DIR = REPO_ROOT / "ViewController" / "1-PreProcess"
if str(PREPROCESS_DIR) not in sys.path:
    sys.path.insert(0, str(PREPROCESS_DIR))

import MyBoxer as boxer


class MyBoxerLineSpacingTests(unittest.TestCase):
    def test_move_lh_slider_ignores_blank_text(self) -> None:
        instance = boxer.MainWindow.__new__(boxer.MainWindow)
        instance.ui = type("UI", (), {})()
        instance.ui.LHslider = type("Slider", (), {"setEnabled": lambda self, value: None, "setValue": lambda self, value: None})()
        instance.ui.LHlineEdit = type("LineEdit", (), {"text": lambda self: ""})()

        instance.MoveLHSlider()


if __name__ == "__main__":
    unittest.main()
