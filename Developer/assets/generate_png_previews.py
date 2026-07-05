"""Generate PNG previews and a contact sheet from licensed EPS assets.

This script preserves the EPS files in ``Licensed images`` as the source
archive and regenerates the PNG working set in ``PNG previews`` for review and
tagging.
"""

from pathlib import Path
import math
import shutil
import subprocess

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "Licensed images"
PREVIEW_DIR = ROOT / "PNG previews"
GHOSTSCRIPT = Path(r"C:\Program Files\gs\gs10.00.0\bin\gswin64c.exe")


def render_eps_previews():
    PREVIEW_DIR.mkdir(exist_ok=True)

    for png_file in PREVIEW_DIR.glob("shutterstock_*.png"):
        png_file.unlink()

    for eps_file in sorted(SOURCE_DIR.glob("shutterstock_*.eps")):
        output_file = PREVIEW_DIR / f"{eps_file.stem}.png"
        subprocess.run(
            [
                str(GHOSTSCRIPT),
                "-dSAFER",
                "-dBATCH",
                "-dNOPAUSE",
                "-sDEVICE=pngalpha",
                "-r120",
                f"-sOutputFile={output_file}",
                str(eps_file),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def build_contact_sheet():
    files = sorted(PREVIEW_DIR.glob("shutterstock_*.png"))
    if not files:
        return

    thumb_w = 220
    thumb_h = 220
    label_h = 36
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
        img.thumbnail((thumb_w - 12, thumb_h - 12))
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
            (x + 6, y + thumb_h + 8),
            path.stem.replace("shutterstock_", ""),
            fill="black",
            font=font,
        )

    sheet.save(PREVIEW_DIR / "contact_sheet.png")


def ensure_sample_preview_removed():
    sample = PREVIEW_DIR / "sample_2806729833.png"
    if sample.exists():
        sample.unlink()


def main():
    if not GHOSTSCRIPT.exists():
        raise FileNotFoundError(f"Ghostscript not found: {GHOSTSCRIPT}")

    render_eps_previews()
    ensure_sample_preview_removed()
    build_contact_sheet()


if __name__ == "__main__":
    main()