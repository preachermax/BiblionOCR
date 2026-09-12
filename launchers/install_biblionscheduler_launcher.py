#!/usr/bin/env python3
"""Install the standalone Biblion Scheduler desktop entry for Linux."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import stat
import subprocess


LAUNCHER_NAME = "Biblion Scheduler.desktop"


def desktop_entry(repo_root: Path) -> str:
    wrapper = repo_root / "launchers" / "run-biblionscheduler.sh"
    icon = repo_root / "ViewController" / "0-MainUI" / "helpers" / "Icons" / "calendar-day.png"
    return "\n".join((
        "[Desktop Entry]",
        "Type=Application",
        "Version=1.0",
        "Name=Biblion Scheduler",
        "Comment=Plan BiblionOCR development with WBS and schedule logic",
        f"Exec={wrapper}",
        f"TryExec={wrapper}",
        f"Icon={icon}",
        f"Path={repo_root / 'Core' / 'Scheduler'}",
        "Terminal=false",
        "StartupNotify=true",
        "StartupWMClass=biblion-scheduler",
        "Categories=Office;ProjectManagement;",
        "Keywords=BiblionOCR;WBS;Gantt;Schedule;Planner;",
        "",
    ))


def mark_trusted(path: Path) -> None:
    if shutil.which("gio"):
        subprocess.run(
            ["gio", "set", str(path), "metadata::trusted", "true"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def install_launcher(repo_root: Path, home: Path, desktop_copy: bool = True) -> tuple[Path, ...]:
    wrapper = repo_root / "launchers" / "run-biblionscheduler.sh"
    if not wrapper.is_file():
        raise FileNotFoundError(f"Scheduler wrapper not found: {wrapper}")
    wrapper.chmod(wrapper.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    content = desktop_entry(repo_root)
    applications_dir = home / ".local" / "share" / "applications"
    applications_dir.mkdir(parents=True, exist_ok=True)
    application_target = applications_dir / LAUNCHER_NAME
    application_target.write_text(content, encoding="utf-8")
    application_target.chmod(0o644)
    installed = [application_target]

    if desktop_copy:
        desktop_dir = home / "Desktop"
        desktop_dir.mkdir(parents=True, exist_ok=True)
        desktop_target = desktop_dir / LAUNCHER_NAME
        desktop_target.write_text(content, encoding="utf-8")
        desktop_target.chmod(0o755)
        mark_trusted(desktop_target)
        installed.append(desktop_target)

    if shutil.which("update-desktop-database"):
        subprocess.run(
            ["update-desktop-database", str(applications_dir)],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    return tuple(installed)


def main(arguments: list[str] | None = None) -> int:
    default_repo = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Install the Biblion Scheduler desktop launcher.")
    parser.add_argument("--repo-root", type=Path, default=default_repo)
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--no-desktop-copy", action="store_true")
    options = parser.parse_args(arguments)
    installed = install_launcher(
        options.repo_root.expanduser().resolve(),
        options.home.expanduser().resolve(),
        desktop_copy=not options.no_desktop_copy,
    )
    for path in installed:
        print(f"Installed: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())