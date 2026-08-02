"""Generate PNG previews and a contact sheet from licensed source assets.

This script preserves the source files in ``Licensed images`` and regenerates
the PNG working set in ``PNG previews`` for review and tagging. Raster assets
are converted directly; EPS files are rendered through Ghostscript when present.
"""

import csv
from pathlib import Path
import math
import re
import subprocess

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "Licensed images"
PREVIEW_DIR = ROOT / "PNG previews"
MANIFEST_PATH = ROOT / "asset_tags.csv"
GHOSTSCRIPT = Path(r"C:\Program Files\gs\gs10.00.0\bin\gswin64c.exe")
RENDER_DPI = 600
MAX_PREVIEW_DIMENSION = 2400
THUMB_RESAMPLE = Image.Resampling.LANCZOS
SUPPORTED_RASTER_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp"}


def iter_preview_pngs():
    return sorted(
        path
        for path in PREVIEW_DIR.glob("*.png")
        if path.name != "contact_sheet.png" and not path.stem.endswith("__raw")
    )


def slugify(value):
    text = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return text or "asset"


def load_manifest_rows():
    with MANIFEST_PATH.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = reader.fieldnames or []
    return fieldnames, rows


def build_preview_filename(row):
    source_file = (row.get("eps_file") or "").strip()
    stem = Path(source_file).stem
    numeric_id = stem.replace("shutterstock_", "")
    category_code = slugify((row.get("category_code") or "").strip()) or "uncategorized"
    tags = [slugify(tag) for tag in (row.get("tags") or "").split(";") if tag.strip()]
    tag_part = "-".join(tags[:3]) if tags else "preview"
    return f"{category_code}_{tag_part}_{numeric_id}.png"


def write_manifest_rows(fieldnames, rows):
    with MANIFEST_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def render_with_ghostscript_tiff(source_file, temp_output):
    subprocess.run(
        [
            str(GHOSTSCRIPT),
            "-dSAFER",
            "-dBATCH",
            "-dNOPAUSE",
            "-sDEVICE=tiff24nc",
            "-dUseCropBox",
            "-dTextAlphaBits=4",
            "-dGraphicsAlphaBits=4",
            "-dDOINTERPOLATE",
            f"-r{RENDER_DPI}",
            f"-sOutputFile={temp_output}",
            str(source_file),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def normalize_image(raw_image, output_file):
    final_image = raw_image.convert("RGB")
    longest_edge = max(final_image.size)
    if longest_edge > MAX_PREVIEW_DIMENSION:
        scale = MAX_PREVIEW_DIMENSION / float(longest_edge)
        resized_size = (
            max(1, int(final_image.width * scale)),
            max(1, int(final_image.height * scale)),
        )
        final_image = final_image.resize(resized_size, THUMB_RESAMPLE)
    final_image.save(output_file, format="PNG")


def render_preview_image(source_file, output_file):
    if source_file.suffix.lower() in SUPPORTED_RASTER_EXTENSIONS:
        with Image.open(source_file) as raw_image:
            normalize_image(raw_image, output_file)
        return

    temp_output = output_file.with_name(f"{output_file.stem}__raw.tiff")
    try:
        render_with_ghostscript_tiff(source_file, temp_output)

        with Image.open(temp_output) as raw_image:
            normalize_image(raw_image, output_file)
    finally:
        temp_output.unlink(missing_ok=True)


def render_source_previews():
    PREVIEW_DIR.mkdir(exist_ok=True)
    fieldnames, rows = load_manifest_rows()
    rows_by_source = {
        (row.get("eps_file") or "").strip(): row
        for row in rows
        if (row.get("eps_file") or "").strip()
    }

    for png_file in PREVIEW_DIR.glob("*.png"):
        if png_file.name == "contact_sheet.png":
            continue
        png_file.unlink()

    source_files = sorted(
        path
        for path in SOURCE_DIR.iterdir()
        if path.is_file() and path.name.startswith("shutterstock_") and path.suffix.lower() in (SUPPORTED_RASTER_EXTENSIONS | {".eps"})
    )

    for source_file in source_files:
        row = rows_by_source.get(source_file.name)
        if row is None:
            continue
        output_file = PREVIEW_DIR / build_preview_filename(row)
        row["png_preview_file"] = output_file.name
        render_preview_image(source_file, output_file)

    write_manifest_rows(fieldnames, rows)


def build_contact_sheet():
    files = iter_preview_pngs()
    if not files:
        return

    thumb_w = 280
    thumb_h = 280
    label_h = 54
    cols = 4
    rows = max(1, math.ceil(len(files) / cols))

    sheet = Image.new(
        "RGB",
        (cols * thumb_w, rows * (thumb_h + label_h)),
        "white",
    )
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    for idx, path in enumerate(files):
        img = Image.open(path).convert("RGB")
        img.thumbnail((thumb_w - 16, thumb_h - 16), THUMB_RESAMPLE)
        x = (idx % cols) * thumb_w
        y = (idx // cols) * (thumb_h + label_h)
        px = x + (thumb_w - img.width) // 2
        py = y + (thumb_h - img.height) // 2
        sheet.paste(img, (px, py))
        draw.rectangle(
            (x, y, x + thumb_w - 1, y + thumb_h + label_h - 1),
            outline="gray",
            width=1,
        )
        draw.text(
            (x + 8, y + thumb_h + 8),
            path.stem,
            fill="black",
            font=font,
        )

    sheet.save(PREVIEW_DIR / "contact_sheet.png")


def ensure_sample_preview_removed():
    sample = PREVIEW_DIR / "sample_2806729833.png"
    if sample.exists():
        sample.unlink()


def main():
    if not SOURCE_DIR.exists():
        raise FileNotFoundError(f"Source folder not found: {SOURCE_DIR}")

    if any(path.suffix.lower() == ".eps" for path in SOURCE_DIR.glob("shutterstock_*")) and not GHOSTSCRIPT.exists():
        raise FileNotFoundError(f"Ghostscript not found: {GHOSTSCRIPT}")

    render_source_previews()
    ensure_sample_preview_removed()
    build_contact_sheet()


if __name__ == "__main__":
    main()