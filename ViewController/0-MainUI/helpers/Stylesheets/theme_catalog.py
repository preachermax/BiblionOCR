from __future__ import annotations

import json
from pathlib import Path


THEME_DIR = Path(__file__).resolve().parent
MANIFEST_PATH = THEME_DIR / "theme_manifest.json"


def _manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


THEME_IDS = tuple(_manifest()["themes"])


def get_theme(theme_id: str) -> dict:
    normalized = str(theme_id or "default").strip().lower().replace(" ", "_")
    themes = _manifest()["themes"]
    if normalized not in themes:
        raise ValueError(f"Unknown project theme: {theme_id}")
    return {"id": normalized, **themes[normalized]}


def load_stylesheet(theme_id: str) -> str:
    theme = get_theme(theme_id)
    if theme["native"]:
        return ""
    stylesheet = (THEME_DIR / f"{theme['id']}.qss").read_text(encoding="utf-8")
    asset_root = (THEME_DIR / "src" / theme["id"] / "img").as_posix()
    return stylesheet.replace("@ASSET_ROOT@", asset_root)