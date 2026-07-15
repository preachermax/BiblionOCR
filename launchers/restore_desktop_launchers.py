#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import stat
import subprocess
from typing import Dict, Iterable, List, Tuple

LEGACY_REPO_ROOT = "/home/jetson/Projects/BiblionOCR"
GREEK_BRAND = "βιϐλιον"
GREEK_LABEL_ALIASES = {
    "My Server": [f"{GREEK_BRAND} Server"],
}

CANONICAL_MODULES: List[Tuple[str, str, str]] = [
    ("MyServer", "My Server", "BiblionServer.png"),
    ("MyExplorer", "Biblion Explorer", "BiblionExplorer.png"),
    ("MyBoxer", "Biblion Boxer", "BiblionBoxer2.png"),
    ("MyGlypher", "Biblion Glypher", "BiblionGlypher.png"),
    ("MyGrounder", "Biblion Grounder", "BiblionGrounder.png"),
    ("MyLauncher", "Biblion Launcher", "BiblionOCR.png"),
    ("MyLexer", "Biblion Lexer", "BiblionLexer.png"),
    ("MyPixler", "Biblion Pixler", "BiblionPixler1.png"),
    ("MyReader", "Biblion Reader", "BiblionReader2.png"),
    ("MyResolver", "Biblion Resolver", "BiblionResolver2.png"),
    ("MyScanner", "Biblion Scanner", "BiblionScanner1.png"),
    ("MySliders", "Biblion Sliders", "BiblionOCR.png"),
    ("MyTrainer", "Biblion Trainer", "BiblionTrainer1.png"),
    ("MyVersifier", "Biblion Versifier", "BiblionVersifier2.png"),
    ("MyWriter", "Biblion Writer", "BiblionWriter1.png"),
]

LEGACY_LAUNCHERS_TO_REMOVE: List[str] = [
    "BiblionBoxer.desktop",
]


def parse_args() -> argparse.Namespace:
    script_path = Path(__file__).resolve()
    default_repo = script_path.parent.parent

    parser = argparse.ArgumentParser(
        description=(
            "Restore BiblionOCR desktop launchers by rewriting legacy repo paths, "
            "installing bundled .desktop files, and generating canonical module launchers."
        )
    )
    parser.add_argument("--repo-root", default=str(default_repo), help="Repository root path")
    parser.add_argument("--home", default=str(Path.home()), help="Target home path")
    parser.add_argument(
        "--no-desktop-copy",
        action="store_true",
        help="Do not copy launchers to ~/Desktop",
    )
    parser.add_argument(
        "--skip-generated",
        action="store_true",
        help="Skip generating canonical My* desktop launchers",
    )
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def rewrite_paths(content: str, repo_root: str) -> str:
    return content.replace(LEGACY_REPO_ROOT, repo_root)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def install_file(src: Path, dst: Path, mode: int) -> None:
    shutil.copy2(src, dst)
    os.chmod(dst, mode)


def format_desktop_entry(name: str, comment: str, exec_cmd: str, try_exec: str, icon: str, cwd: str) -> str:
    lines = [
        "[Desktop Entry]",
        "Type=Application",
        f"Name={name}",
        f"Comment={comment}",
        "Version=1.0",
        f"Exec={exec_cmd}",
        f"TryExec={try_exec}",
        f"Icon={icon}",
        f"Path={cwd}",
        "Terminal=true",
        "Categories=Utility;",
    ]
    return "\n".join(lines) + "\n"


def greek_label(label: str) -> str:
    if label.startswith("Biblion "):
        return label.replace("Biblion ", f"{GREEK_BRAND} ", 1)
    return label


def greek_label_variants(label: str) -> List[str]:
    variants: List[str] = []
    alias_variants = GREEK_LABEL_ALIASES.get(label, [])
    variants.extend(alias_variants)

    transformed = greek_label(label)
    if transformed != label:
        variants.append(transformed)

    seen = set()
    unique: List[str] = []
    for variant in variants:
        if variant and variant not in seen:
            seen.add(variant)
            unique.append(variant)

    return unique


def build_generated_launchers(repo_root: Path) -> Dict[str, str]:
    launchers: Dict[str, str] = {}
    icons_dir = repo_root / "ViewController" / "0-MainUI" / "Icons"
    module_dir = repo_root / "ViewController" / "0-MainUI"
    launcher_dir = repo_root / "launchers"

    for module, label, icon_name in CANONICAL_MODULES:
        module_file = module_dir / f"{module}.py"
        if not module_file.exists():
            continue

        icon_path = icons_dir / icon_name
        if not icon_path.exists():
            icon_path = icons_dir / "BiblionBoxer2.png"

        sh_wrapper = launcher_dir / f"run-{module.lower()}.sh"
        if sh_wrapper.exists():
            exec_cmd = f"{sh_wrapper} %f"
            try_exec = str(sh_wrapper)
            # Ensure local wrapper script is executable.
            sh_wrapper.chmod(sh_wrapper.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        else:
            exec_cmd = f"/usr/bin/python3 {module_file} %f"
            try_exec = "/usr/bin/python3"

        desktop_name = f"{label}.desktop"
        launchers[desktop_name] = format_desktop_entry(
            name=label,
            comment=f"Launch {label}",
            exec_cmd=exec_cmd,
            try_exec=try_exec,
            icon=str(icon_path),
            cwd=str(repo_root),
        )

        for greek_name in greek_label_variants(label):
            greek_desktop_name = f"{greek_name}.desktop"
            launchers[greek_desktop_name] = format_desktop_entry(
                name=greek_name,
                comment=f"Launch {greek_name}",
                exec_cmd=exec_cmd,
                try_exec=try_exec,
                icon=str(icon_path),
                cwd=str(repo_root),
            )

    return launchers


def refresh_desktop_database(apps_dir: Path) -> None:
    if shutil.which("update-desktop-database"):
        try:
            subprocess.run(["update-desktop-database", str(apps_dir)], check=False)
        except Exception:
            pass


def remove_legacy_launchers(apps_dir: Path, desktop_dir: Path, remove_desktop_copy: bool) -> List[str]:
    removed: List[str] = []
    for file_name in LEGACY_LAUNCHERS_TO_REMOVE:
        app_target = apps_dir / file_name
        if app_target.exists():
            app_target.unlink()
            removed.append(str(app_target))

        if remove_desktop_copy:
            desktop_target = desktop_dir / file_name
            if desktop_target.exists():
                desktop_target.unlink()
                removed.append(str(desktop_target))

    return removed


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    home = Path(args.home).expanduser().resolve()
    apps_dir = home / ".local" / "share" / "applications"
    desktop_dir = home / "Desktop"

    ensure_dir(apps_dir)
    if not args.no_desktop_copy:
        ensure_dir(desktop_dir)

    installed: List[str] = []
    removed = remove_legacy_launchers(apps_dir, desktop_dir, not args.no_desktop_copy)

    for desktop_file in sorted(repo_root.glob("*.desktop")):
        if desktop_file.name in LEGACY_LAUNCHERS_TO_REMOVE:
            continue

        content = rewrite_paths(read_text(desktop_file), str(repo_root))
        temp = apps_dir / f".{desktop_file.name}.tmp"
        write_text(temp, content)

        apps_target = apps_dir / desktop_file.name
        install_file(temp, apps_target, 0o644)
        installed.append(str(apps_target))

        if not args.no_desktop_copy:
            desktop_target = desktop_dir / desktop_file.name
            install_file(temp, desktop_target, 0o755)
            installed.append(str(desktop_target))

        temp.unlink(missing_ok=True)

    if not args.skip_generated:
        generated = build_generated_launchers(repo_root)
        for file_name, content in generated.items():
            apps_target = apps_dir / file_name
            write_text(apps_target, content)
            os.chmod(apps_target, 0o644)
            installed.append(str(apps_target))

            if not args.no_desktop_copy:
                desktop_target = desktop_dir / file_name
                write_text(desktop_target, content)
                os.chmod(desktop_target, 0o755)
                installed.append(str(desktop_target))

    run_myserver = repo_root / "launchers" / "run-myserver.sh"
    if run_myserver.exists():
        run_myserver.chmod(run_myserver.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    refresh_desktop_database(apps_dir)

    print(f"Repository root: {repo_root}")
    print(f"Applications dir: {apps_dir}")
    if not args.no_desktop_copy:
        print(f"Desktop dir: {desktop_dir}")
    if removed:
        print(f"Removed legacy launchers: {len(removed)}")
        for path in removed:
            print(f" - {path}")
    print(f"Installed launcher files: {len(installed)}")
    for path in installed:
        print(f" - {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
