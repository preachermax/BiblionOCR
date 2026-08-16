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
from Core.workflow_wizard_actions import ModulePageWorkflowWizardDialog, apply_active_project_theme
from helpers.Stylesheets import THEME_IDS, apply_theme, save_project_theme


def test_designer_edit_menu_owns_edit_themes_action() -> None:
    ui_path = Path(__file__).resolve().parents[1] / "Developer" / "QtDesignerUI" / "MyServerUI.ui"
    root = ET.parse(ui_path).getroot()
    edit_menu = root.find(".//widget[@name='menuEdit']")
    assert edit_menu is not None
    assert "actionEditThemes" in [item.get("name") for item in edit_menu.findall("addaction")]

    action = root.find(".//action[@name='actionEditThemes']")
    assert action is not None
    assert action.find("./property[@name='text']/string").text == "Edit Themes..."


def test_designer_view_menu_owns_all_project_theme_actions() -> None:
    ui_path = Path(__file__).resolve().parents[1] / "Developer" / "QtDesignerUI" / "MyServerUI.ui"
    root = ET.parse(ui_path).getroot()
    view_menu = root.find(".//widget[@name='menuView']")
    themes_menu = root.find(".//widget[@name='menuThemes']")
    assert view_menu is not None
    assert themes_menu is not None
    assert view_menu.find("./property[@name='title']/string").text == "View"
    assert themes_menu.find("./property[@name='title']/string").text == "Themes"

    expected = {
        "actionThemeDefault": "Default",
        "actionThemeClassic": "Classic",
        "actionThemeDarkBlue": "Dark",
        "actionThemeTigers": "Tigers",
        "actionThemeTide": "Tide",
    }
    assert [item.get("name") for item in themes_menu.findall("addaction")] == list(expected)
    for action_name, label in expected.items():
        action = root.find(f".//action[@name='{action_name}']")
        assert action is not None
        assert action.find("./property[@name='checkable']/bool").text == "true"
        assert action.find("./property[@name='text']/string").text == label


def test_generated_myserver_ui_matches_designer_theme_actions() -> None:
    from MyServerUI import Ui_MainUI

    application = qtw.QApplication.instance() or qtw.QApplication([])
    window = qtw.QMainWindow()
    ui = Ui_MainUI()
    ui.setupUi(window)

    assert ui.menuView.title() == "View"
    assert ui.menuThemes.title() == "Themes"
    assert [action.text() for action in ui.menuThemes.actions()] == [
        "Default",
        "Classic",
        "Dark",
        "Tigers",
        "Tide",
    ]
    assert all(action.isCheckable() for action in ui.menuThemes.actions())
    window.close()


def test_generated_myserver_system_font_remains_fromvs_across_themes() -> None:
    from MyServerUI import Ui_MainUI

    application = qtw.QApplication.instance() or qtw.QApplication([])
    original_font = application.font()
    original_stylesheet = application.styleSheet()
    window = qtw.QMainWindow()
    ui = Ui_MainUI()
    ui.setupUi(window)

    try:
        for theme_id in THEME_IDS:
            apply_theme(theme_id, application)
            assert application.font().family() == "FROMVS"
            assert ui.menuFile.font().family() == "FROMVS"
    finally:
        window.close()
        window.deleteLater()
        qtc.QCoreApplication.sendPostedEvents(None, qtc.QEvent.DeferredDelete)
        application.setStyleSheet(original_stylesheet)
        application.setFont(original_font)


def test_panel_messages_are_owned_by_matched_runtime_overlays() -> None:
    project_root = Path(__file__).resolve().parents[1]
    ui_path = project_root / "Developer" / "QtDesignerUI" / "MyServerUI.ui"
    runtime_path = project_root / "ViewController" / "0-MainUI" / "MyServer.py"
    root = ET.parse(ui_path).getroot()

    image_text = root.find(".//widget[@name='Image']/property[@name='text']/string")
    text_placeholder = root.find(
        ".//widget[@name='OCRText']/property[@name='placeholderText']/string"
    )
    assert image_text is not None and not image_text.text
    assert text_placeholder is not None and not text_placeholder.text

    runtime = runtime_path.read_text(encoding="utf-8")
    assert '"imagePanelOverlay"' in runtime
    assert '"textPanelOverlay"' in runtime
    assert '"FROMVS.ttf",\n            14,' in runtime
    assert runtime.count("overlay.setAlignment(Qt.AlignCenter)") == 1
    assert runtime.count("overlay.setFixedSize(500, 120)") == 1
    assert "geometry.moveCenter(panel.rect().center())" in runtime
    assert "Qt.WA_TransparentForMouseEvents" in runtime
    assert "self.ui.OCRText.textChanged.connect" in runtime
    assert 'overlay_color = "#6B6C70" if theme_id == "tide" else "#c7c7c7"' in runtime


def test_page_workflow_dialog_inherits_active_project_theme(tmp_path) -> None:
    application = qtw.QApplication.instance() or qtw.QApplication([])
    save_project_theme(tmp_path, "tide")

    class SessionManagerStub:
        def get_active_project_root(self):
            return str(tmp_path)

    owner = qtw.QMainWindow()
    owner.session_manager = SessionManagerStub()
    assert apply_active_project_theme(owner) == "tide"

    dialog = ModulePageWorkflowWizardDialog(
        title="Theme Test",
        intro_text="Theme inheritance test",
        stage_plan=[],
        run_stage_callback=lambda _stage: None,
        run_all_callback=lambda: None,
        parent=owner,
    )
    assert dialog.styleSheet() == ""
    assert "#9E1B32" in application.styleSheet()
    assert "#FFFFFF" in application.styleSheet()
    dialog.close()
    owner.close()


def test_workflow_theme_application_uses_window_theme_preferences(tmp_path) -> None:
    application = qtw.QApplication.instance() or qtw.QApplication([])
    save_project_theme(tmp_path, "classic")

    class SessionManagerStub:
        def get_active_project_root(self):
            return str(tmp_path)

    owner = qtw.QMainWindow()
    owner.session_manager = SessionManagerStub()
    applied_themes = []
    owner._apply_project_theme = applied_themes.append

    assert apply_active_project_theme(owner) == "classic"
    assert applied_themes == ["classic"]
    owner.close()
    assert application is qtw.QApplication.instance()


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
        "Dark",
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