from __future__ import annotations

import json
from pathlib import Path, PurePath

from PyQt5 import QtGui as qtg
from PyQt5 import QtWidgets as qtw


THEME_DIR = Path(__file__).resolve().parent
MANIFEST_PATH = THEME_DIR / "theme_manifest.json"
SYSTEM_UI_FONT_PATH = THEME_DIR.parent / "fonts" / "FROMVS.ttf"
_SYSTEM_UI_FONT_FAMILY = None


def _manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


THEME_IDS = tuple(_manifest()["themes"])


def _qt_stylesheet_path(path: PurePath) -> str:
    return path.as_posix().rstrip("/")


def get_theme(theme_id: str) -> dict:
    normalized = str(theme_id or "default").strip().lower().replace(" ", "_")
    themes = _manifest()["themes"]
    if normalized not in themes:
        raise ValueError(f"Unknown project theme: {theme_id}")
    return {"id": normalized, **themes[normalized]}


def load_stylesheet(theme_id: str) -> str:
    theme = get_theme(theme_id)
    stylesheet = (THEME_DIR / f"{theme['id']}.qss").read_text(encoding="utf-8")
    asset_root = _qt_stylesheet_path((THEME_DIR / "src" / theme["id"] / "img").resolve())
    return stylesheet.replace("@ASSET_ROOT@", asset_root)


def apply_system_ui_font(application=None) -> str:
    global _SYSTEM_UI_FONT_FAMILY

    application = application or qtw.QApplication.instance()
    if application is None:
        return "FROMVS"

    if _SYSTEM_UI_FONT_FAMILY is None:
        font_id = qtg.QFontDatabase.addApplicationFont(str(SYSTEM_UI_FONT_PATH))
        families = qtg.QFontDatabase.applicationFontFamilies(font_id) if font_id >= 0 else []
        _SYSTEM_UI_FONT_FAMILY = families[0] if families else "FROMVS"

    font = qtg.QFont(application.font())
    font.setFamily(_SYSTEM_UI_FONT_FAMILY)
    application.setFont(font)
    return _SYSTEM_UI_FONT_FAMILY


def apply_theme(theme_id: str, application=None) -> None:
    application = application or qtw.QApplication.instance()
    if application is None:
        return
    application.setStyleSheet(load_stylesheet(theme_id))
    apply_system_ui_font(application)
