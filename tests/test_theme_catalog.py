from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path, PureWindowsPath

STYLESHEET_DIR = (
    Path(__file__).resolve().parents[1]
    / "ViewController"
    / "0-MainUI"
    / "helpers"
    / "Stylesheets"
)
HELPERS_DIR = STYLESHEET_DIR.parent
if str(HELPERS_DIR) not in sys.path:
    sys.path.insert(0, str(HELPERS_DIR))

from Stylesheets import load_project_theme, save_project_theme
from Stylesheets.theme_catalog import (
    THEME_IDS,
    _qt_stylesheet_path,
    apply_theme,
    get_theme,
    load_stylesheet,
)


class ThemeCatalogTests(unittest.TestCase):
    def test_catalog_contains_all_project_themes(self) -> None:
        self.assertEqual(("default", "classic", "dark_blue", "tigers", "tide"), THEME_IDS)
        self.assertEqual("Classic", get_theme("classic")["name"])
        self.assertEqual("Dark", get_theme("dark_blue")["name"])
        self.assertEqual("Tigers", get_theme("tigers")["name"])
        self.assertEqual("", load_stylesheet("default"))

    def test_classic_and_default_preserve_the_pre_catalog_themes(self) -> None:
        classic_source = (STYLESHEET_DIR / "src" / "classic_legacy.qss.in").read_text(
            encoding="utf-8"
        ).rstrip("\n") + "\n"
        self.assertEqual(classic_source, load_stylesheet("classic"))
        self.assertIn("alternate-background-color: #EEEEFF", classic_source)
        self.assertNotIn("QComboBox::drop-down", classic_source)
        self.assertNotIn("font-size:", classic_source)
        self.assertEqual("", load_stylesheet("default"))

    def test_classic_inherits_the_default_application_font_size(self) -> None:
        from PyQt5 import QtWidgets as qtw

        application = qtw.QApplication.instance() or qtw.QApplication([])
        original_font = application.font()
        original_stylesheet = application.styleSheet()
        try:
            apply_theme("default", application)
            default_sizes = (
                qtw.QWidget().font().pointSize(),
                qtw.QTableView().font().pointSize(),
                qtw.QPushButton().font().pointSize(),
            )
            apply_theme("classic", application)
            classic_sizes = (
                qtw.QWidget().font().pointSize(),
                qtw.QTableView().font().pointSize(),
                qtw.QPushButton().font().pointSize(),
            )
            self.assertEqual(default_sizes, classic_sizes)
        finally:
            application.setStyleSheet(original_stylesheet)
            application.setFont(original_font)

    def test_every_theme_preserves_fromvs_as_the_system_ui_font(self) -> None:
        from PyQt5 import QtGui as qtg
        from PyQt5 import QtWidgets as qtw

        application = qtw.QApplication.instance() or qtw.QApplication([])
        original_font = application.font()
        original_stylesheet = application.styleSheet()
        try:
            application.setFont(qtg.QFont("DejaVu Sans", 11))
            for theme_id in THEME_IDS:
                apply_theme(theme_id, application)
                self.assertEqual("FROMVS", application.font().family(), theme_id)
                self.assertEqual(11, application.font().pointSize(), theme_id)
        finally:
            application.setStyleSheet(original_stylesheet)
            application.setFont(original_font)

    def test_slider_orientations_have_equal_geometry(self) -> None:
        stylesheet = (STYLESHEET_DIR / "src" / "theme_schema.qss.in").read_text(encoding="utf-8")

        def declarations(selector: str) -> dict[str, str]:
            match = re.search(rf"{re.escape(selector)}\s*\{{([^}}]+)\}}", stylesheet)
            self.assertIsNotNone(match, selector)
            return {
                name.strip(): value.strip()
                for name, value in re.findall(r"([\w-]+)\s*:\s*([^;]+);", match.group(1))
            }

        horizontal_groove = declarations("QSlider::groove:horizontal")
        vertical_groove = declarations("QSlider::groove:vertical")
        self.assertEqual(horizontal_groove["height"], vertical_groove["width"])

        horizontal_handle = declarations("QSlider::handle:horizontal")
        vertical_handle = declarations("QSlider::handle:vertical")
        self.assertEqual(horizontal_handle["width"], horizontal_handle["height"])
        self.assertEqual(horizontal_handle["width"], vertical_handle["width"])
        self.assertEqual(horizontal_handle["height"], vertical_handle["height"])

    def test_arrows_and_slider_handles_are_highlighted_without_hover(self) -> None:
        schema = (STYLESHEET_DIR / "src" / "theme_schema.qss.in").read_text(encoding="utf-8")

        def block(selector: str) -> str:
            match = re.search(rf"{re.escape(selector)}\s*\{{([^}}]+)\}}", schema)
            self.assertIsNotNone(match, selector)
            return match.group(1)

        expected_scroll_arrows = {
            "QScrollBar::add-line:horizontal": "right_arrow.png",
            "QScrollBar::sub-line:horizontal": "left_arrow.png",
            "QScrollBar::sub-line:vertical": "up_arrow.png",
            "QScrollBar::add-line:vertical": "down_arrow.png",
        }
        for selector, asset_name in expected_scroll_arrows.items():
            normal_state = block(selector)
            self.assertIn(asset_name, normal_state)
            self.assertNotIn("_disabled.png", normal_state)
            self.assertIn("image:", normal_state)
            self.assertNotIn("border-image:", normal_state)
            self.assertIn("background-color: #CFCFCD", normal_state)

        self.assertIn("down_arrow.png", block("QComboBox::down-arrow"))
        self.assertIn("background-color: #CFCFCD", block("QComboBox::drop-down"))
        self.assertIn("background-color: #CFCFCD", block("QAbstractSpinBox:up-button"))
        self.assertIn("background-color: #CFCFCD", block("QAbstractSpinBox:down-button"))
        self.assertIn("#F4F4F2", block("QSlider::handle:horizontal"))
        self.assertIn("#F4F4F2", block("QSlider::handle:vertical"))

        for theme_id in ("dark_blue", "tigers", "tide"):
            stylesheet = load_stylesheet(theme_id)
            self.assertNotIn("#CFCFCD", stylesheet, theme_id)
            self.assertNotIn("#F4F4F2", stylesheet, theme_id)

    def test_styled_themes_share_the_canonical_selector_schema(self) -> None:
        manifest = json.loads((STYLESHEET_DIR / "theme_manifest.json").read_text(encoding="utf-8"))
        expected = set(manifest["selectors"])
        for theme_id in ("dark_blue", "tigers", "tide"):
            stylesheet = load_stylesheet(theme_id)
            without_comments = re.sub(r"/\*.*?\*/", "", stylesheet, flags=re.DOTALL)
            selectors = {
                selector.strip()
                for group in re.findall(r"([^{}]+)\{", without_comments)
                for selector in group.split(",")
                if selector.strip()
            }
            self.assertEqual(expected, selectors, theme_id)

    def test_every_resolved_asset_reference_exists(self) -> None:
        for theme_id in ("dark_blue", "tigers", "tide"):
            stored_stylesheet = (STYLESHEET_DIR / f"{theme_id}.qss").read_text(encoding="utf-8")
            self.assertNotIn("/home/jetson", stored_stylesheet)
            stylesheet = load_stylesheet(theme_id)
            self.assertNotIn("@ASSET_ROOT@", stylesheet)
            for reference in re.findall(r'url\("([^"]+)"\)', stylesheet):
                self.assertNotIn("file:", reference, f"{theme_id}: {reference}")
                self.assertTrue(Path(reference).is_file(), f"{theme_id}: {reference}")

    def test_windows_asset_paths_use_qt_compatible_forward_slashes(self) -> None:
        asset_root = PureWindowsPath("C:/Users/Example User/BiblionOCR/Stylesheets/src/tigers/img")
        stylesheet_path = _qt_stylesheet_path(asset_root)
        self.assertEqual(
            "C:/Users/Example User/BiblionOCR/Stylesheets/src/tigers/img",
            stylesheet_path,
        )
        self.assertNotIn("\\", stylesheet_path)
        self.assertNotIn("file:", stylesheet_path)

    def test_dark_blue_assets_preserve_the_baseline_bytes(self) -> None:
        base_dir = STYLESHEET_DIR / "src" / "theme_base" / "img"
        dark_blue_dir = STYLESHEET_DIR / "src" / "dark_blue" / "img"
        base_assets = {path.name: path.read_bytes() for path in base_dir.glob("*.png")}
        dark_blue_assets = {path.name: path.read_bytes() for path in dark_blue_dir.glob("*.png")}
        self.assertEqual(base_assets, dark_blue_assets)

    def test_tigers_control_arrows_use_orange_glyphs(self) -> None:
        from PIL import Image

        image_dir = STYLESHEET_DIR / "src" / "tigers" / "img"
        expected_orange = (255, 160, 47)
        arrow_assets = (
            "up_arrow.png",
            "down_arrow.png",
            "left_arrow.png",
            "right_arrow.png",
            "increase_blue.png",
            "decrease_blue.png",
        )
        for asset_name in arrow_assets:
            image = Image.open(image_dir / asset_name).convert("RGBA")
            visible_colors = {pixel[:3] for pixel in image.getdata() if pixel[3]}
            self.assertEqual({expected_orange}, visible_colors, asset_name)

    def test_box_scroll_and_slider_outlines_match_each_theme_arrow_color(self) -> None:
        from PIL import Image

        expected_colors = {
            "dark_blue": "#FFFFFF",
            "tigers": "#FFA02F",
            "tide": "#F2F2F2",
        }
        expected_well_colors = {
            "dark_blue": "#505050",
            "tigers": "#365F87",
            "tide": "#6B6C70",
        }
        outlined_selectors = (
            "QComboBox",
            "QAbstractSpinBox",
            "QScrollBar:horizontal",
            "QScrollBar:vertical",
            "QScrollBar::handle:horizontal",
            "QScrollBar::handle:vertical",
            "QSlider::groove:horizontal",
            "QSlider::groove:vertical",
            "QSlider::handle:horizontal",
            "QSlider::handle:vertical",
        )

        for theme_id, expected_hex in expected_colors.items():
            expected_rgb = tuple(int(expected_hex[index:index + 2], 16) for index in (1, 3, 5))
            arrow = Image.open(
                STYLESHEET_DIR / "src" / theme_id / "img" / "down_arrow.png"
            ).convert("RGBA")
            visible_colors = {pixel[:3] for pixel in arrow.getdata() if pixel[3]}
            self.assertEqual({expected_rgb}, visible_colors, theme_id)

            stylesheet = load_stylesheet(theme_id)
            combo_well = re.search(r"QComboBox::drop-down\s*\{([^}]+)\}", stylesheet)
            self.assertIsNotNone(combo_well, theme_id)
            self.assertIn(
                f"background-color: {expected_well_colors[theme_id]}",
                combo_well.group(1),
                theme_id,
            )
            self.assertNotEqual(expected_well_colors[theme_id], expected_hex, theme_id)
            for selector in outlined_selectors:
                match = re.search(
                    rf"(?:^|,)\s*{re.escape(selector)}\s*(?:,|\{{)([^}}]*)\}}",
                    stylesheet,
                    flags=re.MULTILINE,
                )
                self.assertIsNotNone(match, f"{theme_id}: {selector}")
                self.assertRegex(
                    match.group(1),
                    rf"border(?:-color)?:\s*(?:\d+px\s+solid\s+)?{re.escape(expected_hex)}",
                    f"{theme_id}: {selector}",
                )

    def test_project_theme_persists_to_project_metadata(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as project_root:
            self.assertEqual("default", load_project_theme(project_root))
            self.assertEqual("tide", save_project_theme(project_root, "tide"))
            self.assertEqual("tide", load_project_theme(project_root))
            metadata_path = (
                Path(project_root)
                / "Model"
                / "Project"
                / "Data"
                / "sqlite"
                / "project_metadata.json"
            )
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            self.assertEqual("tide", metadata["ProjectTheme"])

    def test_active_legacy_callers_use_the_theme_catalog(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        callers = (
            project_root / "ViewController" / "1-PreProcess" / "MyBoxer.py",
            project_root / "ViewController" / "1-PreProcess" / "MyGlypher.py",
            project_root / "ViewController" / "3-Process" / "MyLexer.py",
        )
        for caller in callers:
            source = caller.read_text(encoding="utf-8")
            self.assertIn("from Stylesheets import apply_theme", source)
            self.assertNotRegex(source, r"Stylesheets/(?:dark_orange|dark_blue|classic)\.qss")
            self.assertIn('apply_theme("tide", app)', source)

    def test_requested_palette_names_and_colors_are_present(self) -> None:
        dark = load_stylesheet("dark_blue")
        tigers = load_stylesheet("tigers")
        tide = load_stylesheet("tide")
        self.assertIn("#0C2340", tigers)
        self.assertIn("#FFA02F", tigers)
        self.assertIn("#9E1B32", tide)
        self.assertIn("#FFFFFF", tide)
        self.assertIn("#5C0F1D", tide)
        self.assertIn("#F2F2F2", tide)
        self.assertIn("#6B6C70", tide)
        self.assertIn("#B8B8B8", tide)
        self.assertNotIn("background-color: #F7F7F7", tide)
        self.assertRegex(
            tide,
            r"QTextEdit#OCRText\s*\{[^}]*background-color:\s*#FFFFFF;[^}]*color:\s*#202020;",
        )
        self.assertRegex(
            tide,
            r"QLabel#Image,\s*QTextEdit#OCRText\s*\{[^}]*background-color:\s*#FFFFFF;",
        )
        self.assertIn("#1E1E1E", dark)
        self.assertIn("#252526", dark)
        self.assertIn("#F0F0F0", dark)
        self.assertIn("#007ACC", dark)
        self.assertFalse((STYLESHEET_DIR / "dark_orange.qss").exists())

        notebook = Path(__file__).resolve().parents[1] / "docs" / "development" / "DEV_NOTEBOOK.md"
        theme_files = [path for path in STYLESHEET_DIR.rglob("*") if path.is_file()]
        theme_text = "\n".join(
            path.read_text(encoding="utf-8", errors="ignore")
            for path in (*theme_files, notebook)
        )
        prohibited_names = ("ala" + "bama", "au" + "burn")
        self.assertFalse(any(name in theme_text.lower() for name in prohibited_names))


if __name__ == "__main__":
    unittest.main()