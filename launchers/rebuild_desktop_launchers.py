#!/usr/bin/env python3
"""Rebuild tracked Linux desktop launchers for the current local checkout.

This utility rewrites absolute paths in repo-tracked .desktop files so they
match the current machine path (for example /home/max-richey instead of
/home/jetson). This is primarily useful when launcher icons stop displaying
because Icon= points to a non-existent absolute path.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class DesktopSpec:
    filename: str
    python_entrypoint: str | None = None
    wrapper_script: str | None = None


SPECS: tuple[DesktopSpec, ...] = (
    DesktopSpec("Biblion Explorer.desktop", python_entrypoint="ViewController/0-MainUI/MyExplorer.py"),
    DesktopSpec("BiblionBoxer.desktop", python_entrypoint="ViewController/0-MainUI/MyBoxer.py"),
    DesktopSpec("My Server.desktop", wrapper_script="launchers/run-myserver.sh"),
    DesktopSpec("βιϐλιον Explorer.desktop", python_entrypoint="ViewController/0-MainUI/MyExplorer.py"),
    DesktopSpec("βιϐλιον Boxer.desktop", python_entrypoint="ViewController/0-MainUI/MyBoxer.py"),
)


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def build_entry_values(root: Path, spec: DesktopSpec) -> dict[str, str]:
    icon_path = root / "ViewController/0-MainUI/Icons/BiblionBoxer2.png"
    values: dict[str, str] = {
        "Icon": str(icon_path),
        "Path": str(root),
    }

    if spec.wrapper_script:
        wrapper_path = root / spec.wrapper_script
        values["Exec"] = f"{wrapper_path} %f"
        values["TryExec"] = str(wrapper_path)
    elif spec.python_entrypoint:
        script_path = root / spec.python_entrypoint
        values["Exec"] = f"/usr/bin/python3 {script_path} %f"
        values["TryExec"] = "/usr/bin/python3"

    return values


def rewrite_desktop_file(path: Path, values: dict[str, str]) -> tuple[bool, str]:
    original = path.read_text(encoding="utf-8")
    lines = original.splitlines()
    changed = False

    for key, value in values.items():
        prefix = f"{key}="
        replaced = False
        for i, line in enumerate(lines):
            if line.startswith(prefix):
                new_line = f"{prefix}{value}"
                if lines[i] != new_line:
                    lines[i] = new_line
                    changed = True
                replaced = True
                break

        if not replaced:
            insertion_index = find_insertion_index(lines)
            lines.insert(insertion_index, f"{prefix}{value}")
            changed = True

    newline = "\n" if original.endswith("\n") else ""
    updated = "\n".join(lines) + newline
    return changed, updated


def find_insertion_index(lines: list[str]) -> int:
    for i, line in enumerate(lines):
        if line.startswith("Terminal="):
            return i
    return len(lines)


def iter_targets(root: Path, specs: Iterable[DesktopSpec]) -> Iterable[tuple[DesktopSpec, Path]]:
    for spec in specs:
        yield spec, root / spec.filename


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rewrite tracked .desktop launchers with current local absolute paths."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would change without writing files.",
    )
    args = parser.parse_args()

    root = repo_root_from_script()
    missing: list[Path] = []
    updated_count = 0

    for spec, target in iter_targets(root, SPECS):
        if not target.exists():
            missing.append(target)
            continue

        values = build_entry_values(root, spec)
        changed, updated_text = rewrite_desktop_file(target, values)
        if changed:
            updated_count += 1
            action = "would update" if args.dry_run else "updated"
            print(f"{action}: {target}")
            if not args.dry_run:
                target.write_text(updated_text, encoding="utf-8")
        else:
            print(f"unchanged: {target}")

    if missing:
        print("\nmissing targets:")
        for target in missing:
            print(f"- {target}")

    if args.dry_run:
        print(f"\ndry run complete; {updated_count} file(s) would be updated.")
    else:
        print(f"\ncomplete; {updated_count} file(s) updated.")

    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())