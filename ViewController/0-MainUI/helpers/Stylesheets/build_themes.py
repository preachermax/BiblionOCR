from __future__ import annotations

import colorsys
import json
import re
import shutil
from pathlib import Path

from PIL import Image


THEME_DIR = Path(__file__).resolve().parent
SOURCE_DIR = THEME_DIR / "src"
SCHEMA_PATH = SOURCE_DIR / "theme_schema.qss.in"
CLASSIC_SCHEMA_PATH = SOURCE_DIR / "classic_legacy.qss.in"
BASE_IMAGE_DIR = SOURCE_DIR / "theme_base" / "img"
SCHEMA_VERSION = 1
CONTROL_ARROW_ASSETS = {
    "up_arrow.png",
    "up_arrow_disabled.png",
    "down_arrow.png",
    "down_arrow_disabled.png",
    "left_arrow.png",
    "left_arrow_disabled.png",
    "right_arrow.png",
    "right_arrow_disabled.png",
    "increase_blue.png",
    "decrease_blue.png",
}

THEMES = {
    "dark_blue": {
        "name": "Dark",
        "accent": "#007ACC",
        "arrow": "#FFFFFF",
        "colors": {
            "#302F2F": "#252526",
            "#201F1F": "#1E1E1E",
            "#3A3939": "#3C3C3C",
            "#4A4949": "#4A4A4A",
            "#2A2929": "#2D2D30",
            "#605F5F": "#565656",
            "#3d8ec9": "#007ACC",
            "#78879b": "#0E639C",
            "#48576b": "#333337",
            "#626873": "#3F3F46",
            "#4a4a4a": "#3C3C3C",
            "#484846": "#2D2D30",
            "#403F3F": "#333333",
            "#393838": "#3C3C3C",
            "#5A5959": "#505050",
            "#6A6969": "#606060",
            "#6c6c6c": "#6A6A6A",
            "#787876": "#707070",
            "#808080": "#858585",
            "#b1b1b1": "#F0F0F0",
            "#bbb": "#F0F0F0",
            "#777777": "#A0A0A0",
            "#727272": "#909090",
            "#a8a8a8": "#D0D0D0",
            "#AAA": "#D0D0D0",
            "#AAAAAA": "#D0D0D0",
            "#444444": "#505050",
            "#444": "#505050",
            "#FEFEFC": "#1E1E1E",
            "#1D1D1B": "#F0F0F0",
            "#BDBDBA": "#3C3C3C",
            "#CFCFCD": "#505050",
            "#F4F4F2": "#F2F2F2",
            "#D8D8D6": "#D0D0D0",
            "#E6E6E4": "#FFFFFF",
        },
        "words": {
            "silver": "#F0F0F0",
            "white": "#FFFFFF",
            "black": "#FFFFFF",
            "lightblue": "#75BEFF",
            "dimgray": "#858585",
            "darkgray": "#A0A0A0",
        },
    },
    "tigers": {
        "name": "Tigers",
        "accent": "#FFA02F",
        "arrow": "#FFA02F",
        "colors": {
            "#302F2F": "#0C2340",
            "#201F1F": "#071526",
            "#3A3939": "#1B365D",
            "#4A4949": "#294C73",
            "#2A2929": "#102B4E",
            "#605F5F": "#365F87",
            "#3d8ec9": "#FFA02F",
            "#78879b": "#D7801A",
            "#48576b": "#1B365D",
            "#626873": "#294C73",
            "#4a4a4a": "#294C73",
            "#484846": "#102B4E",
            "#403F3F": "#1B365D",
            "#393838": "#1B365D",
            "#5A5959": "#365F87",
            "#6A6969": "#476D93",
            "#FEFEFC": "#071526",
            "#1D1D1B": "#F0F0F0",
            "#BDBDBA": "#294C73",
            "#CFCFCD": "#365F87",
            "#F4F4F2": "#F2F2F2",
            "#D8D8D6": "#D0D0D0",
            "#E6E6E4": "#FFA02F",
        },
        "words": {
            "lightblue": "#FFA02F",
            "dimgray": "#294C73",
            "darkgray": "#365F87",
        },
    },
    "tide": {
        "name": "Tide",
        "accent": "#FFFFFF",
        "arrow": "#F2F2F2",
        "colors": {
            "#302F2F": "#9E1B32",
            "#201F1F": "#5C0F1D",
            "#3A3939": "#7A1426",
            "#4A4949": "#6B6C70",
            "#2A2929": "#7A1426",
            "#605F5F": "#B8B8B8",
            "#3d8ec9": "#FFFFFF",
            "#78879b": "#D9D9D9",
            "#48576b": "#55565A",
            "#626873": "#55565A",
            "#4a4a4a": "#6B6C70",
            "#484846": "#7A1426",
            "#403F3F": "#C8C8C8",
            "#393838": "#C8C8C8",
            "#5A5959": "#8A8A8D",
            "#6A6969": "#D0D0D0",
            "#6c6c6c": "#C8C8C8",
            "#787876": "#6B6C70",
            "#808080": "#D0D0D0",
            "#b1b1b1": "#F2F2F2",
            "#bbb": "#F2F2F2",
            "#777777": "#D0D0D0",
            "#727272": "#C8C8C8",
            "#a8a8a8": "#E0E0E0",
            "#AAA": "#E0E0E0",
            "#AAAAAA": "#E0E0E0",
            "#444444": "#C8C8C8",
            "#444": "#C8C8C8",
            "#FEFEFC": "#FFFFFF",
            "#1D1D1B": "#202020",
            "#BDBDBA": "#C8C8C8",
            "#CFCFCD": "#6B6C70",
            "#F4F4F2": "#F2F2F2",
            "#D8D8D6": "#D0D0D0",
            "#E6E6E4": "#F2F2F2",
        },
        "words": {
            "silver": "#F2F2F2",
            "white": "#FFFFFF",
            "black": "#1A1A1A",
            "lightblue": "#FFFFFF",
            "dimgray": "#7A1426",
            "darkgray": "#B8B8B8",
        },
    },
}


def _replace_palette(source: str, theme: dict) -> str:
    rendered = source
    for old, new in sorted(theme["colors"].items(), key=lambda item: -len(item[0])):
        rendered = re.sub(re.escape(old), new, rendered, flags=re.IGNORECASE)
    for old, new in theme["words"].items():
        rendered = re.sub(rf"\b{re.escape(old)}\b", new, rendered, flags=re.IGNORECASE)
    return rendered


def _portable_asset_urls(source: str) -> str:
    def replace(match: re.Match) -> str:
        filename = Path(match.group(1).strip(' "\'')).name
        return f'url("@ASSET_ROOT@/{filename}")'

    return re.sub(r"url\(([^)]+)\)", replace, source)


def _recolor_image(
    source_path: Path,
    output_path: Path,
    accent: str,
    *,
    force_accent: bool = False,
) -> None:
    target_rgb = tuple(int(accent[index:index + 2], 16) / 255 for index in (1, 3, 5))
    target_hue, target_saturation, _ = colorsys.rgb_to_hsv(*target_rgb)
    image = Image.open(source_path).convert("RGBA")
    pixels = []
    for red, green, blue, alpha in image.getdata():
        hue, saturation, value = colorsys.rgb_to_hsv(red / 255, green / 255, blue / 255)
        if alpha and force_accent:
            red, green, blue = (round(channel * 255) for channel in target_rgb)
        elif alpha and saturation >= 0.18:
            new_red, new_green, new_blue = colorsys.hsv_to_rgb(
                target_hue,
                max(target_saturation, saturation * 0.65),
                value,
            )
            red, green, blue = (round(channel * 255) for channel in (new_red, new_green, new_blue))
        pixels.append((red, green, blue, alpha))
    image.putdata(pixels)
    image.save(output_path)


def build_themes() -> None:
    schema = _portable_asset_urls(SCHEMA_PATH.read_text(encoding="utf-8"))
    selector_source = re.sub(r"/\*.*?\*/", "", schema, flags=re.DOTALL)
    selectors = sorted({
        selector.strip()
        for group in re.findall(r"([^{}]+)\{", selector_source)
        for selector in group.split(",")
        if selector.strip()
    })

    for obsolete in (SOURCE_DIR / "dark_orange",):
        if obsolete.exists():
            shutil.rmtree(obsolete)
    obsolete_root = THEME_DIR / "dark_orange.qss"
    if obsolete_root.exists():
        obsolete_root.unlink()

    for theme_id, theme in THEMES.items():
        output_dir = SOURCE_DIR / theme_id
        image_dir = output_dir / "img"
        if output_dir.exists():
            shutil.rmtree(output_dir)
        image_dir.mkdir(parents=True)
        rendered = _replace_palette(schema, theme)
        header = f"/* Generated theme: {theme['name']}; schema v{SCHEMA_VERSION}. */\n"
        (output_dir / "style.qss").write_text(header + rendered, encoding="utf-8")
        (THEME_DIR / f"{theme_id}.qss").write_text(header + rendered, encoding="utf-8")
        for source_image in BASE_IMAGE_DIR.glob("*.png"):
            output_image = image_dir / source_image.name
            if theme_id == "dark_blue":
                shutil.copy2(source_image, output_image)
            else:
                _recolor_image(
                    source_image,
                    output_image,
                    theme["arrow"] if source_image.name in CONTROL_ARROW_ASSETS else theme["accent"],
                    force_accent=source_image.name in CONTROL_ARROW_ASSETS,
                )

    classic_text = CLASSIC_SCHEMA_PATH.read_text(encoding="utf-8").rstrip("\n") + "\n"
    classic_dir = SOURCE_DIR / "classic"
    if classic_dir.exists():
        shutil.rmtree(classic_dir)
    classic_dir.mkdir(parents=True)
    (classic_dir / "style.qss").write_text(classic_text, encoding="utf-8")
    (THEME_DIR / "classic.qss").write_text(classic_text, encoding="utf-8")

    default_text = ""
    default_dir = SOURCE_DIR / "default"
    if default_dir.exists():
        shutil.rmtree(default_dir)
    default_dir.mkdir(parents=True)
    (default_dir / "style.qss").write_text(default_text, encoding="utf-8")
    (THEME_DIR / "default.qss").write_text(default_text, encoding="utf-8")

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "selectors": selectors,
        "themes": {
            "default": {"name": "Default", "native": True},
            "classic": {"name": "Classic", "native": False},
            **{
                theme_id: {"name": theme["name"], "native": False, "accent": theme["accent"]}
                for theme_id, theme in THEMES.items()
            },
        },
    }
    (THEME_DIR / "theme_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    build_themes()