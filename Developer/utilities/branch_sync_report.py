#!/usr/bin/env python3
"""Generate a branch sync report for master, windows-development, and ubuntu_development.

This script is intentionally Git-only and platform-neutral so it can run from
both Windows and Ubuntu checkouts.
"""

from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import subprocess
import sys
from typing import List, Tuple


def run_git(repo: pathlib.Path, args: List[str]) -> str:
    command = ["git", "-C", str(repo)] + args
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        stderr = completed.stderr.strip()
        stdout = completed.stdout.strip()
        message = stderr or stdout or "unknown git error"
        raise RuntimeError(f"git {' '.join(args)} failed: {message}")
    return completed.stdout.strip()


def remote_ref(remote: str, branch: str) -> str:
    return f"{remote}/{branch}"


def ensure_remote_branch_exists(repo: pathlib.Path, remote: str, branch: str) -> None:
    ref = f"refs/remotes/{remote}/{branch}"
    result = subprocess.run(
        ["git", "-C", str(repo), "show-ref", "--verify", "--quiet", ref],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"missing remote branch '{remote}/{branch}'. Run fetch and verify branch naming."
        )


def ahead_behind(repo: pathlib.Path, left: str, right: str) -> Tuple[int, int]:
    raw = run_git(repo, ["rev-list", "--left-right", "--count", f"{left}...{right}"])
    parts = raw.split()
    if len(parts) != 2:
        raise RuntimeError(f"unexpected rev-list output for {left}...{right}: {raw}")
    return int(parts[0]), int(parts[1])


def unique_commits(repo: pathlib.Path, branch: str, other: str, max_count: int) -> List[str]:
    raw = run_git(
        repo,
        [
            "log",
            "--oneline",
            "--no-merges",
            f"--max-count={max_count}",
            branch,
            "--not",
            other,
        ],
    )
    if not raw:
        return []
    return raw.splitlines()


def build_report(
    repo: pathlib.Path,
    remote: str,
    master_branch: str,
    windows_branch: str,
    ubuntu_branch: str,
    max_commits: int,
) -> str:
    master_ref = remote_ref(remote, master_branch)
    windows_ref = remote_ref(remote, windows_branch)
    ubuntu_ref = remote_ref(remote, ubuntu_branch)

    for branch in [master_branch, windows_branch, ubuntu_branch]:
        ensure_remote_branch_exists(repo, remote, branch)

    run_git(repo, ["fetch", remote, "--prune"])

    windows_behind_master, windows_ahead_master = ahead_behind(repo, master_ref, windows_ref)
    ubuntu_behind_master, ubuntu_ahead_master = ahead_behind(repo, master_ref, ubuntu_ref)

    windows_only_vs_ubuntu, ubuntu_only_vs_windows = ahead_behind(repo, windows_ref, ubuntu_ref)

    windows_unique = unique_commits(repo, windows_ref, ubuntu_ref, max_commits)
    ubuntu_unique = unique_commits(repo, ubuntu_ref, windows_ref, max_commits)

    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    lines: List[str] = []
    lines.append("# Branch Sync Status")
    lines.append("")
    lines.append(f"Generated: {now}")
    lines.append(f"Repository: {repo}")
    lines.append(f"Remote: {remote}")
    lines.append("")
    lines.append("## Source Of Truth")
    lines.append("")
    lines.append(f"- Canonical branch: `{master_ref}`")
    lines.append("- Development branches should stay aware of each other and rebase/merge intentionally.")
    lines.append("")
    lines.append("## Master Divergence")
    lines.append("")
    lines.append("| Branch | Ahead Of Master | Behind Master |")
    lines.append("| --- | ---: | ---: |")
    lines.append(f"| `{windows_ref}` | {windows_ahead_master} | {windows_behind_master} |")
    lines.append(f"| `{ubuntu_ref}` | {ubuntu_ahead_master} | {ubuntu_behind_master} |")
    lines.append("")
    lines.append("## Cross-Branch Divergence")
    lines.append("")
    lines.append(
        f"- Commits only in `{windows_ref}` (not in `{ubuntu_ref}`): **{windows_only_vs_ubuntu}**"
    )
    lines.append(
        f"- Commits only in `{ubuntu_ref}` (not in `{windows_ref}`): **{ubuntu_only_vs_windows}**"
    )
    lines.append("")

    lines.append(f"## Sample Commits In `{windows_ref}` Only")
    lines.append("")
    if windows_unique:
        for item in windows_unique:
            lines.append(f"- {item}")
    else:
        lines.append("- None")
    lines.append("")

    lines.append(f"## Sample Commits In `{ubuntu_ref}` Only")
    lines.append("")
    if ubuntu_unique:
        for item in ubuntu_unique:
            lines.append(f"- {item}")
    else:
        lines.append("- None")
    lines.append("")

    lines.append("## Operator Notes")
    lines.append("")
    lines.append("- If a branch is behind master, fast-forward/rebase before starting major work.")
    lines.append(
        "- If both development branches have unique commits, schedule an explicit reconciliation pass and verify behavior on both platforms."
    )
    lines.append("- Keep PRs targeted at master, with branch-sync checks before and after merge.")
    lines.append("")

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a branch sync markdown report.")
    parser.add_argument("--repo", default=".", help="Path to repository root")
    parser.add_argument("--remote", default="origin", help="Git remote name")
    parser.add_argument("--master", default="master", help="Canonical source branch")
    parser.add_argument("--windows", default="windows-development", help="Windows dev branch")
    parser.add_argument("--ubuntu", default="ubuntu_development", help="Ubuntu dev branch")
    parser.add_argument(
        "--out",
        default="docs/development/BRANCH_SYNC_STATUS.md",
        help="Output markdown path relative to repo",
    )
    parser.add_argument(
        "--max-commits",
        type=int,
        default=10,
        help="How many unique commits to list per branch",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = pathlib.Path(args.repo).resolve()
    out_path = repo / args.out

    try:
        report = build_report(
            repo=repo,
            remote=args.remote,
            master_branch=args.master,
            windows_branch=args.windows,
            ubuntu_branch=args.ubuntu,
            max_commits=args.max_commits,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
