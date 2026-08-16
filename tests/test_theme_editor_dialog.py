from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from PyQt5 import QtCore as qtc
from PyQt5 import QtWidgets as qtw


HELPERS_DIR = Path(__file__).resolve().parents[1] / "ViewController" / "0-MainUI" / "helpers"
if str(HELPERS_DIR.parent) not in sys.path:
    sys.path.insert(0, str(HELPERS_DIR.parent))

from helpers.Dialogs.ThemeEditorDialog import (
    ThemeEditorDialog,
    ThemePreferences,
    customized_stylesheet,
    load_theme_preferences,
    safe_theme_overrides,
    save_theme_preferences,
)


def test_designer_edit_menu_owns_edit_themes_action() -> None:
    ui_path = Path(__file__).resolve().parents[1] / "Developer" / "QtDesignerUI" / "MyServerUI.ui"
    root = ET.parse(ui_path).getroot()
    edit_menu = root.find(".//widget[@name='menuEdit']")
    assert edit_menu is not None
    assert "actionEditThemes" in [item.get("name") for item in edit_menu.findall("addaction")]

    action = root.find(".//action[@name='actionEditThemes']")
    assert action is not None
    assert action.find("./property[@name='text']/string").text == "Edit Themes..."


def test_dialog_shows_theme_boundaries_to_the_user() -> None:
    application = qtw.QApplication.instance() or qtw.QApplication([])
    dialog = ThemeEditorDialog(ThemePreferences())
    dialog.show()
    application.processEvents()

    visible_text = " ".join(label.text() for label in dialog.findChildren(qtw.QLabel) if label.isVisible())
    assert "primary theme colors are locked" in visible_text
    assert "New themes must be created elsewhere" in visible_text
    assert [dialog.theme_combo.itemText(index) for index in range(dialog.theme_combo.count())] == [
        "Default",
        "Classic",
        "Dark Blue",
        "Tigers",
        "Tide",
    ]
    dialog.close()


def test_theme_preferences_round_trip_through_settings(tmp_path) -> None:
    settings = qtc.QSettings(str(tmp_path / "theme.ini"), qtc.QSettings.IniFormat)
    expected = ThemePreferences("tide", "Large", "Compact", "Rounded", "Extra Large")
    save_theme_preferences(expected, settings)
    assert load_theme_preferences(settings) == expected


def test_invalid_persisted_values_fall_back_to_safe_defaults(tmp_path) -> None:
    settings = qtc.QSettings(str(tmp_path / "theme.ini"), qtc.QSettings.IniFormat)
    settings.beginGroup("theme_editor")
    for key in ("theme_id", "text_size", "density", "corner_style", "slider_size"):
        settings.setValue(key, "user supplied css")
    settings.endGroup()

    assert load_theme_preferences(settings) == ThemePreferences()


def test_safe_overrides_change_no_colors_and_keep_slider_handles_square() -> None:
    preferences = ThemePreferences("tigers", "Large", "Spacious", "Rounded", "Extra Large")
    overrides = safe_theme_overrides(preferences)

    assert not re.search(r"\b(?:color|background|border-color)\s*:", overrides, re.IGNORECASE)
    assert "width: 18px; height: 18px" in overrides
    assert "QSlider:horizontal { min-height: 26px; }" in overrides
    assert "QSlider:vertical { min-width: 26px; }" in overrides
    assert "#0C2340" in customized_stylesheet(preferences)
    assert "#FFA02F" in customized_stylesheet(preferences)