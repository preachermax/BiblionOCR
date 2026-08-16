from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path


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

from Stylesheets.theme_catalog import THEME_IDS, get_theme, load_stylesheet


class ThemeCatalogTests(unittest.TestCase):
    def test_catalog_contains_all_project_themes(self) -> None:
        self.assertEqual(("default", "classic", "dark_blue", "tigers", "tide"), THEME_IDS)
        self.assertEqual("Classic", get_theme("classic")["name"])
        self.assertEqual("Tigers", get_theme("tigers")["name"])
        self.assertEqual("", load_stylesheet("default"))

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

    def test_styled_themes_share_the_canonical_selector_schema(self) -> None:
        manifest = json.loads((STYLESHEET_DIR / "theme_manifest.json").read_text(encoding="utf-8"))
        expected = set(manifest["selectors"])
        for theme_id in ("classic", "dark_blue", "tigers", "tide"):
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
        for theme_id in ("classic", "dark_blue", "tigers", "tide"):
            stored_stylesheet = (STYLESHEET_DIR / f"{theme_id}.qss").read_text(encoding="utf-8")
            self.assertNotIn("/home/jetson", stored_stylesheet)
            stylesheet = load_stylesheet(theme_id)
            self.assertNotIn("@ASSET_ROOT@", stylesheet)
            for reference in re.findall(r'url\("([^"]+)"\)', stylesheet):
                self.assertTrue(Path(reference).is_file(), f"{theme_id}: {reference}")

    def test_dark_blue_assets_preserve_the_baseline_bytes(self) -> None:
        base_dir = STYLESHEET_DIR / "src" / "theme_base" / "img"
        dark_blue_dir = STYLESHEET_DIR / "src" / "dark_blue" / "img"
        base_assets = {path.name: path.read_bytes() for path in base_dir.glob("*.png")}
        dark_blue_assets = {path.name: path.read_bytes() for path in dark_blue_dir.glob("*.png")}
        self.assertEqual(base_assets, dark_blue_assets)

    def test_active_legacy_callers_use_the_theme_catalog(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        callers = (
            project_root / "ViewController" / "1-PreProcess" / "MyBoxer.py",
            project_root / "ViewController" / "1-PreProcess" / "MyGlypher.py",
            project_root / "ViewController" / "3-Process" / "MyLexer.py",
        )
        for caller in callers:
            source = caller.read_text(encoding="utf-8")
            self.assertIn("from Stylesheets import load_stylesheet", source)
            self.assertNotRegex(source, r"Stylesheets/(?:dark_orange|dark_blue|classic)\.qss")
            self.assertIn('load_stylesheet("tide")', source)

    def test_requested_palette_names_and_colors_are_present(self) -> None:
        tigers = load_stylesheet("tigers")
        tide = load_stylesheet("tide")
        self.assertIn("#0C2340", tigers)
        self.assertIn("#FFA02F", tigers)
        self.assertIn("#9E1B32", tide)
        self.assertIn("#FFFFFF", tide)
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