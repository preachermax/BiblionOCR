#!/usr/bin/env python3
"""Validate that required shared development tools are tracked and portable.

This check enforces the policy that cross-platform scripts needed by either
Windows or Ubuntu development must be versioned in git and not gitignored.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
from dataclasses import dataclass
from typing import Iterable, List


@dataclass
class ToolEntry:
    path: str
    description: str
    platforms: List[str]


def run_git(repo: pathlib.Path, args: List[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo)] + args,
        capture_output=True,
        text=True,
        check=False,
    )


def is_tracked(repo: pathlib.Path, rel_path: str) -> bool:
    result = run_git(repo, ["ls-files", "--error-unmatch", rel_path])
    return result.returncode == 0


def is_ignored(repo: pathlib.Path, rel_path: str) -> bool:
    result = run_git(repo, ["check-ignore", "-q", rel_path])
    return result.returncode == 0


def load_manifest(repo: pathlib.Path, manifest_rel: str) -> List[ToolEntry]:
    manifest_path = repo / manifest_rel
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    raw_tools = data.get("tools", [])
    if not isinstance(raw_tools, list):
        raise ValueError("Manifest 'tools' must be a list")

    tools: List[ToolEntry] = []
    for idx, item in enumerate(raw_tools):
        if not isinstance(item, dict):
            raise ValueError(f"tools[{idx}] must be an object")
        path = str(item.get("path", "")).strip()
        if not path:
            raise ValueError(f"tools[{idx}] missing non-empty 'path'")
        description = str(item.get("description", "")).strip()
        platforms_raw = item.get("platforms", [])
        if not isinstance(platforms_raw, list) or not platforms_raw:
            raise ValueError(f"tools[{idx}] must define a non-empty 'platforms' list")
        platforms = [str(p).strip().lower() for p in platforms_raw if str(p).strip()]
        tools.append(ToolEntry(path=path, description=description, platforms=platforms))

    return tools


def validate_tools(repo: pathlib.Path, tools: Iterable[ToolEntry]) -> List[str]:
    errors: List[str] = []
    for tool in tools:
        abs_path = repo / tool.path
        if not abs_path.exists():
            errors.append(f"Missing file: {tool.path}")
            continue
        if abs_path.is_dir():
            errors.append(f"Expected file but found directory: {tool.path}")
            continue
        if not is_tracked(repo, tool.path):
            errors.append(f"Not tracked by git: {tool.path}")
        if is_ignored(repo, tool.path):
            errors.append(f"Unexpectedly gitignored: {tool.path}")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate shared dev tools policy")
    parser.add_argument("--repo", default=".", help="Repository root path")
    parser.add_argument(
        "--manifest",
        default="Developer/utilities/shared_tools_manifest.json",
        help="Path to manifest relative to repo root",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = pathlib.Path(args.repo).resolve()

    try:
        tools = load_manifest(repo, args.manifest)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    errors = validate_tools(repo, tools)
    if errors:
        print("Shared dev tools validation failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    print(f"Validated {len(tools)} shared dev tool(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
