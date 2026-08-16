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
BASE_IMAGE_DIR = SOURCE_DIR / "theme_base" / "img"
SCHEMA_VERSION = 1

THEMES = {
    "classic": {
        "name": "Classic",
        "accent": "#8F8F91",
        "colors": {
            "#302F2F": "#F0F0F0",
            "#201F1F": "#FFFFFF",
            "#3A3939": "#B8B8B8",
            "#4A4949": "#A0A0A0",
            "#2A2929": "#E2E2E2",
            "#605F5F": "#B0B0B0",
            "#3d8ec9": "#8F8F91",
            "#78879b": "#9A9B9E",
            "#48576b": "#D5D5D7",
            "#626873": "#DADADC",
            "#4a4a4a": "#C8C8CA",
            "#484846": "#D0D0D2",
            "#403F3F": "#A8A8A8",
            "#393838": "#B8B8B8",
            "#5A5959": "#C0C0C0",
            "#6A6969": "#909090",
            "#6c6c6c": "#A0A0A0",
            "#787876": "#C8C8C8",
            "#808080": "#888888",
            "#b1b1b1": "#303030",
            "#bbb": "#303030",
            "#777777": "#777777",
            "#727272": "#A0A0A0",
            "#a8a8a8": "#C0C0C0",
            "#AAA": "#A0A0A0",
            "#AAAAAA": "#A0A0A0",
            "#444444": "#707070",
            "#444": "#808080",
        },
        "words": {
            "silver": "#303030",
            "white": "#FFFFFF",
            "black": "#202020",
            "lightblue": "#C8C8CA",
            "dimgray": "#D0D0D0",
            "darkgray": "#A0A0A0",
        },
    },
    "dark_blue": {
        "name": "Dark Blue",
        "accent": "#3D8EC9",
        "colors": {},
        "words": {},
    },
    "tigers": {
        "name": "Tigers",
        "accent": "#FFA02F",
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
        },
        "words": {
            "lightblue": "#FFA02F",
            "dimgray": "#294C73",
            "darkgray": "#365F87",
        },
    },
    "tide": {
        "name": "Tide",
        "accent": "#9E1B32",
        "colors": {
            "#302F2F": "#FFFFFF",
            "#201F1F": "#F7F7F7",
            "#3A3939": "#D3D3D3",
            "#4A4949": "#B8B8B8",
            "#2A2929": "#EFEFEF",
            "#605F5F": "#C5C5C5",
            "#3d8ec9": "#9E1B32",
            "#78879b": "#7A1426",
            "#48576b": "#F0DDE1",
            "#626873": "#E8C8CE",
            "#4a4a4a": "#D9D9D9",
            "#484846": "#E5E5E5",
            "#403F3F": "#B8B8B8",
            "#393838": "#D3D3D3",
            "#5A5959": "#C5C5C5",
            "#6A6969": "#A8A8A8",
            "#6c6c6c": "#A8A8A8",
            "#787876": "#D8D8D8",
            "#808080": "#808080",
            "#b1b1b1": "#2A2A2A",
            "#bbb": "#2A2A2A",
            "#727272": "#A0A0A0",
            "#a8a8a8": "#C0C0C0",
        },
        "words": {
            "silver": "#2A2A2A",
            "white": "#FFFFFF",
            "black": "#1A1A1A",
            "lightblue": "#E8C8CE",
            "dimgray": "#D8D8D8",
            "darkgray": "#A8A8A8",
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


def _recolor_image(source_path: Path, output_path: Path, accent: str) -> None:
    target_rgb = tuple(int(accent[index:index + 2], 16) / 255 for index in (1, 3, 5))
    target_hue, target_saturation, _ = colorsys.rgb_to_hsv(*target_rgb)
    image = Image.open(source_path).convert("RGBA")
    pixels = []
    for red, green, blue, alpha in image.getdata():
        hue, saturation, value = colorsys.rgb_to_hsv(red / 255, green / 255, blue / 255)
        if alpha and saturation >= 0.18:
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
                _recolor_image(source_image, output_image, theme["accent"])

    default_text = f"/* Native Qt Default theme; schema v{SCHEMA_VERSION}. */\n"
    default_dir = SOURCE_DIR / "default"
    if default_dir.exists():
        shutil.rmtree(default_dir)
    (default_dir / "img").mkdir(parents=True)
    (default_dir / "style.qss").write_text(default_text, encoding="utf-8")
    (THEME_DIR / "default.qss").write_text(default_text, encoding="utf-8")

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "selectors": selectors,
        "themes": {
            "default": {"name": "Default", "native": True},
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