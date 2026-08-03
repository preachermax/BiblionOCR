#!/usr/bin/env python3
"""Reconcile files removed from ScriptureProjectFolderList.

Default behavior is safe: archive removed paths instead of deleting them.

Usage examples:
  python ViewController/0-MainUI/helpers/reconcile_scripture_folder_removals.py
  python ViewController/0-MainUI/helpers/reconcile_scripture_folder_removals.py --apply
  python ViewController/0-MainUI/helpers/reconcile_scripture_folder_removals.py --apply --delete
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


DEFAULT_LIST_PATH = Path("ViewController/ScriptureProjectFolderList.txt")


def parse_entries(text: str) -> set[str]:
    entries: set[str] = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        entries.add(line)
    return entries


def load_head_version(repo_root: Path, list_path: Path) -> str:
    rel = list_path.as_posix()
    result = subprocess.run(
        ["git", "show", f"HEAD:{rel}"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Could not read HEAD version for {rel}. "
            "If this file is new, provide --baseline-file."
        )
    return result.stdout


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def archive_root_for(repo_root: Path, relative: Path, stamp: str) -> Path:
    first = relative.parts[0] if relative.parts else ""
    if first == "ViewController":
        return repo_root / "ViewController" / "archives" / "ProjectFolderListRemoved" / stamp
    if first == "Model":
        return repo_root / "Model" / "archives" / "ProjectFolderListRemoved" / stamp
    return repo_root / "archives" / "ProjectFolderListRemoved" / stamp


def unique_target(path: Path) -> Path:
    if not path.exists():
        return path
    idx = 1
    while True:
        candidate = path.with_name(f"{path.name}.{idx}")
        if not candidate.exists():
            return candidate
        idx += 1


def remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Apply archive/delete actions. Default is dry-run.")
    parser.add_argument("--delete", action="store_true", help="Delete removed paths instead of archiving.")
    parser.add_argument(
        "--list-path",
        default=str(DEFAULT_LIST_PATH),
        help="List file to reconcile (default: ViewController/ScriptureProjectFolderList.txt).",
    )
    parser.add_argument(
        "--baseline-file",
        default="",
        help="Optional baseline list file. If omitted, baseline is HEAD version of --list-path.",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root path (default: current working directory).",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    list_path = (repo_root / args.list_path).resolve()

    if not list_path.exists():
        raise FileNotFoundError(f"List file not found: {list_path}")

    current_text = read_text(list_path)
    if args.baseline_file:
        baseline_text = read_text((repo_root / args.baseline_file).resolve())
    else:
        baseline_text = load_head_version(repo_root, Path(args.list_path))

    current_entries = parse_entries(current_text)
    baseline_entries = parse_entries(baseline_text)
    removed_entries = sorted(baseline_entries - current_entries)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    planned: list[str] = []
    skipped: list[str] = []
    missing: list[str] = []

    for entry in removed_entries:
        if "=>" in entry:
            skipped.append(f"SKIP manifest mapping: {entry}")
            continue

        rel_path = Path(entry)
        abs_path = (repo_root / rel_path).resolve()

        # Guard against deleting/moving anything outside the repository root.
        if repo_root not in abs_path.parents and abs_path != repo_root:
            skipped.append(f"SKIP outside repo root: {entry}")
            continue

        if not abs_path.exists():
            missing.append(entry)
            continue

        if args.delete:
            planned.append(f"DELETE {entry}")
            if args.apply:
                remove_path(abs_path)
            continue

        archive_root = archive_root_for(repo_root, rel_path, stamp)
        target = unique_target(archive_root / rel_path)
        planned.append(f"ARCHIVE {entry} -> {target.relative_to(repo_root).as_posix()}")
        if args.apply:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(abs_path), str(target))

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"Mode: {mode}")
    print(f"Baseline entries: {len(baseline_entries)}")
    print(f"Current entries: {len(current_entries)}")
    print(f"Removed entries: {len(removed_entries)}")
    print(f"Planned actions: {len(planned)}")
    print(f"Missing paths: {len(missing)}")
    print(f"Skipped entries: {len(skipped)}")

    if planned:
        print("\nActions:")
        for line in planned:
            print(f"  {line}")

    if missing:
        print("\nMissing (already absent):")
        for entry in missing:
            print(f"  {entry}")

    if skipped:
        print("\nSkipped:")
        for line in skipped:
            print(f"  {line}")

    if not args.apply:
        print("\nNo changes were made. Re-run with --apply to execute.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
