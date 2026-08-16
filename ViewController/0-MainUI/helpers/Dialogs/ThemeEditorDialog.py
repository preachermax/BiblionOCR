from __future__ import annotations

from dataclasses import dataclass

from PyQt5 import QtCore as qtc
from PyQt5 import QtWidgets as qtw

from ..Stylesheets import THEME_IDS, get_theme, load_stylesheet


TEXT_SIZES = {
    "System": None,
    "Small": 9,
    "Standard": 10,
    "Large": 12,
    "Extra Large": 14,
}
DENSITIES = {"Compact": 2, "Comfortable": 4, "Spacious": 6}
CORNER_STYLES = {"Square": 0, "Subtle": 2, "Rounded": 4}
SLIDER_SIZES = {"Standard": 14, "Large": 16, "Extra Large": 18}

SETTINGS_ORGANIZATION = "BiblionOCR"
SETTINGS_APPLICATION = "BiblionOCR"
SETTINGS_GROUP = "theme_editor"


@dataclass(frozen=True)
class ThemePreferences:
    theme_id: str = "default"
    text_size: str = "System"
    density: str = "Comfortable"
    corner_style: str = "Subtle"
    slider_size: str = "Standard"


def _allowed(value, choices, fallback):
    value = str(value)
    return value if value in choices else fallback


def load_theme_preferences(settings=None) -> ThemePreferences:
    settings = settings or qtc.QSettings(SETTINGS_ORGANIZATION, SETTINGS_APPLICATION)
    settings.beginGroup(SETTINGS_GROUP)
    try:
        return ThemePreferences(
            theme_id=_allowed(settings.value("theme_id", "default"), THEME_IDS, "default"),
            text_size=_allowed(settings.value("text_size", "System"), TEXT_SIZES, "System"),
            density=_allowed(settings.value("density", "Comfortable"), DENSITIES, "Comfortable"),
            corner_style=_allowed(settings.value("corner_style", "Subtle"), CORNER_STYLES, "Subtle"),
            slider_size=_allowed(settings.value("slider_size", "Standard"), SLIDER_SIZES, "Standard"),
        )
    finally:
        settings.endGroup()


def save_theme_preferences(preferences: ThemePreferences, settings=None) -> None:
    settings = settings or qtc.QSettings(SETTINGS_ORGANIZATION, SETTINGS_APPLICATION)
    settings.beginGroup(SETTINGS_GROUP)
    try:
        for key, value in preferences.__dict__.items():
            settings.setValue(key, value)
    finally:
        settings.endGroup()
    settings.sync()


def safe_theme_overrides(preferences: ThemePreferences) -> str:
    text_size = TEXT_SIZES[preferences.text_size]
    padding = DENSITIES[preferences.density]
    radius = CORNER_STYLES[preferences.corner_style]
    handle_size = SLIDER_SIZES[preferences.slider_size]
    slider_extent = handle_size + 8

    declarations = []
    if text_size is not None:
        declarations.append(f"QWidget {{ font-size: {text_size}pt; }}")
    declarations.extend([
        (
            "QPushButton, QToolButton, QComboBox, QLineEdit, QSpinBox, "
            f"QDoubleSpinBox {{ padding: {padding}px; border-radius: {radius}px; }}"
        ),
        f"QSlider:horizontal {{ min-height: {slider_extent}px; }}",
        f"QSlider:vertical {{ min-width: {slider_extent}px; }}",
        (
            "QSlider::handle:horizontal, QSlider::handle:vertical "
            f"{{ width: {handle_size}px; height: {handle_size}px; }}"
        ),
    ])
    return "\n".join(declarations)


def customized_stylesheet(preferences: ThemePreferences) -> str:
    base_stylesheet = load_stylesheet(preferences.theme_id)
    return "\n".join(part for part in (base_stylesheet, safe_theme_overrides(preferences)) if part)


def apply_theme_preferences(preferences: ThemePreferences, application=None) -> None:
    application = application or qtw.QApplication.instance()
    if application is not None:
        application.setStyleSheet(customized_stylesheet(preferences))


class ThemeEditorDialog(qtw.QDialog):
    def __init__(self, preferences=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Themes")
        self.setMinimumWidth(460)

        preferences = preferences or load_theme_preferences()
        layout = qtw.QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        intro = qtw.QLabel(
            "Choose an existing theme and adjust safe layout settings. "
            "The primary theme colors are locked and cannot be changed here."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        form = qtw.QFormLayout()
        form.setFieldGrowthPolicy(qtw.QFormLayout.AllNonFixedFieldsGrow)
        self.theme_combo = qtw.QComboBox(self)
        for theme_id in THEME_IDS:
            self.theme_combo.addItem(get_theme(theme_id)["name"], theme_id)
        self.theme_combo.setCurrentIndex(max(0, self.theme_combo.findData(preferences.theme_id)))
        form.addRow("Theme", self.theme_combo)

        self.text_size_combo = self._choice_combo(TEXT_SIZES, preferences.text_size)
        form.addRow("Text size", self.text_size_combo)
        self.density_combo = self._choice_combo(DENSITIES, preferences.density)
        form.addRow("Control spacing", self.density_combo)
        self.corner_combo = self._choice_combo(CORNER_STYLES, preferences.corner_style)
        form.addRow("Corner style", self.corner_combo)
        self.slider_combo = self._choice_combo(SLIDER_SIZES, preferences.slider_size)
        form.addRow("Slider size", self.slider_combo)
        layout.addLayout(form)

        notice = qtw.QLabel("New themes must be created elsewhere. This editor only adjusts existing themes.")
        notice.setObjectName("newThemeNotice")
        notice.setWordWrap(True)
        notice.setFrameShape(qtw.QFrame.StyledPanel)
        notice.setMargin(8)
        layout.addWidget(notice)

        buttons = qtw.QDialogButtonBox(
            qtw.QDialogButtonBox.Save | qtw.QDialogButtonBox.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _choice_combo(self, choices, selected):
        combo = qtw.QComboBox(self)
        combo.addItems(choices)
        combo.setCurrentText(selected)
        return combo

    def preferences(self) -> ThemePreferences:
        return ThemePreferences(
            theme_id=str(self.theme_combo.currentData()),
            text_size=self.text_size_combo.currentText(),
            density=self.density_combo.currentText(),
            corner_style=self.corner_combo.currentText(),
            slider_size=self.slider_combo.currentText(),
        )