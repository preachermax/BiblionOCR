import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PREPROCESS_DIR = REPO_ROOT / "ViewController" / "1-PreProcess"
if str(PREPROCESS_DIR) not in sys.path:
    sys.path.insert(0, str(PREPROCESS_DIR))

import MyBoxer as boxer


class MyBoxerWorkflowActionTests(unittest.TestCase):
    def test_workflow_action_methods_are_available(self) -> None:
        self.assertTrue(hasattr(boxer.MainWindow, "actionextract_pdf"))
        self.assertTrue(hasattr(boxer.MainWindow, "actionpdf_for_tiff"))
        self.assertTrue(hasattr(boxer.MainWindow, "actionpdf_to_tiff"))
        self.assertTrue(hasattr(boxer.MainWindow, "actiontiff_to_mono"))
        self.assertTrue(hasattr(boxer.MainWindow, "actionmono_to_png"))
        self.assertTrue(hasattr(boxer.MainWindow, "actiondeskew_mono"))
        self.assertTrue(hasattr(boxer.MainWindow, "actionCrop_Languages"))
        self.assertTrue(hasattr(boxer.MainWindow, "actionCorrect_OCR"))


if __name__ == "__main__":
    unittest.main()
