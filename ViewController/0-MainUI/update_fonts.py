from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
from pathlib import Path


DEFAULT_FONT_NAME = "FROMVS.ttf"
DEFAULT_SOURCE_DIR = Path(__file__).resolve().parent / "fonts"
PROJECT_FONT_DIR = Path(__file__).resolve().parent / "fonts"


def candidate_directories() -> list[Path]:
    directories = [PROJECT_FONT_DIR]
    system_name = platform.system().lower()
    home = Path.home()

    if system_name == "windows":
        local_appdata = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
        directories.append(local_appdata / "Microsoft" / "Windows" / "Fonts")
        return directories

    if system_name == "darwin":
        directories.append(home / "Library" / "Fonts")
        return directories

    directories.extend([
        home / ".local" / "share" / "fonts",
        home / ".fonts",
        Path("/usr/local/share/fonts"),
        Path("/usr/share/fonts/truetype"),
    ])
    return directories


def refresh_font_cache() -> None:
    if platform.system().lower() != "linux":
        return

    try:
        subprocess.run(["fc-cache", "-f", "-v"], check=False)
    except FileNotFoundError:
        pass


def install_font(source: Path, destination_dir: Path) -> bool:
    try:
        destination_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        return False

    destination = destination_dir / source.name
    if source.resolve() == destination.resolve():
        return destination.exists()

    try:
        shutil.copy2(source, destination)
        return True
    except OSError:
        return False


def resolve_source(font_name: str, source_dir: Path) -> Path:
    source = Path(font_name)
    if source.is_file():
        return source

    candidate = source_dir / font_name
    if candidate.is_file():
        return candidate

    raise FileNotFoundError(candidate)


def main() -> int:
    parser = argparse.ArgumentParser(description="Install the BiblionOCR release font into the local font path.")
    parser.add_argument("--font", default=DEFAULT_FONT_NAME, help="Font file name or path")
    parser.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR), help="Directory containing the font file")
    args = parser.parse_args()

    source_dir = Path(args.source_dir).expanduser().resolve()
    source = resolve_source(args.font, source_dir)

    installed = []
    for target_dir in candidate_directories():
        if install_font(source, target_dir):
            installed.append(str(target_dir))

    refresh_font_cache()

    print(f"Installed {source.name} to {len(installed)} location(s).")
    for target in installed:
        print(f"  - {target}")

    return 0 if installed else 1


if __name__ == "__main__":
    raise SystemExit(main())