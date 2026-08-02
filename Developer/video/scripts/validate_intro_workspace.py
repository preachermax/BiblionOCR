from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
ASSETS_ROOT = REPO_ROOT / "Developer" / "assets"
VIDEO_ROOT = REPO_ROOT / "video" / "intro_v1"
STORYBOARDS_DIR = VIDEO_ROOT / "storyboards"
AUDIO_DIR = VIDEO_ROOT / "audio"
FONT_PATH = REPO_ROOT / "ViewController" / "0-MainUI" / "fonts" / "FROMVS.ttf"

EXPECTED_CATEGORY_FOLDERS = [
    "A - Darkness abstraction emergence",
    "B - Knowledge thought conceptual structures",
    "C - Technical systems UI data machines",
    "D - Architecture diagrams flow networks",
    "E - Neutral branding background textures",
]

STORYBOARD_CANDIDATES = [
    "intro_storyboard.md",
    "intro_storyboard.docx",
    "intro_storyboard.pptx",
    "storyboard.md",
    "storyboard.docx",
    "storyboard.pptx",
    "storyboard.pdf",
]

NARRATION_CANDIDATES = [
    "narration_placeholder.txt",
    "narration_placeholder.md",
    "narration_placeholder.wav",
    "narration_placeholder.mp3",
    "voiceover_placeholder.txt",
    "voiceover_placeholder.md",
    "voiceover_placeholder.wav",
    "voiceover_placeholder.mp3",
]


@dataclass
class CheckResult:
    label: str
    ok: bool
    detail: str


def find_candidate(base_dir: Path, candidate_names: list[str], fallback_patterns: tuple[str, ...]) -> Path | None:
    for candidate_name in candidate_names:
        candidate_path = base_dir / candidate_name
        if candidate_path.is_file():
            return candidate_path

    for pattern in fallback_patterns:
        for match in sorted(base_dir.glob(pattern)):
            if match.is_file() and match.name.lower() != "readme.md":
                return match

    return None


def check_category_folders() -> list[CheckResult]:
    results: list[CheckResult] = []
    for folder_name in EXPECTED_CATEGORY_FOLDERS:
        folder_path = ASSETS_ROOT / folder_name
        results.append(
            CheckResult(
                label=f"Asset category: {folder_name}",
                ok=folder_path.is_dir(),
                detail=str(folder_path),
            )
        )
    return results


def check_font() -> CheckResult:
    return CheckResult(
        label="Font: FROMVS.ttf",
        ok=FONT_PATH.is_file(),
        detail=str(FONT_PATH),
    )


def check_storyboard(storyboard_override: str | None) -> CheckResult:
    if storyboard_override:
        storyboard_path = (REPO_ROOT / storyboard_override).resolve() if not Path(storyboard_override).is_absolute() else Path(storyboard_override)
        return CheckResult(
            label="Storyboard document",
            ok=storyboard_path.is_file(),
            detail=str(storyboard_path),
        )

    match = find_candidate(
        STORYBOARDS_DIR,
        STORYBOARD_CANDIDATES,
        ("*storyboard*.*", "*.pdf", "*.pptx", "*.docx", "*.md"),
    )
    return CheckResult(
        label="Storyboard document",
        ok=match is not None,
        detail=str(match) if match else f"Searched {STORYBOARDS_DIR} for {', '.join(STORYBOARD_CANDIDATES)} or any non-README storyboard document",
    )


def check_narration_placeholder(narration_override: str | None) -> CheckResult:
    if narration_override:
        narration_path = (REPO_ROOT / narration_override).resolve() if not Path(narration_override).is_absolute() else Path(narration_override)
        return CheckResult(
            label="Narration placeholder",
            ok=narration_path.is_file(),
            detail=str(narration_path),
        )

    match = find_candidate(
        AUDIO_DIR,
        NARRATION_CANDIDATES,
        ("*narrat*.*", "*voiceover*.*", "*placeholder*.*", "*.txt", "*.md", "*.wav", "*.mp3"),
    )
    return CheckResult(
        label="Narration placeholder",
        ok=match is not None,
        detail=str(match) if match else f"Searched {AUDIO_DIR} for {', '.join(NARRATION_CANDIDATES)} or any non-README narration placeholder",
    )


def format_result(result: CheckResult) -> str:
    status = "OK" if result.ok else "MISSING"
    return f"[{status}] {result.label}\n       {result.detail}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the BiblionOCR intro video production workspace."
    )
    parser.add_argument(
        "--storyboard",
        help="Optional relative or absolute path to the expected storyboard document.",
    )
    parser.add_argument(
        "--narration",
        help="Optional relative or absolute path to the expected narration placeholder.",
    )
    args = parser.parse_args()

    results = [
        *check_category_folders(),
        check_font(),
        check_storyboard(args.storyboard),
        check_narration_placeholder(args.narration),
    ]

    missing = [result for result in results if not result.ok]

    print("BiblionOCR Intro Video Workspace Validation")
    print("=" * 43)
    print(f"Repository root: {REPO_ROOT}")
    print(f"Video workspace: {VIDEO_ROOT}")
    print()

    for result in results:
        print(format_result(result))

    print()
    print(f"Summary: {len(results) - len(missing)} passed, {len(missing)} missing")

    if missing:
        print("Missing items:")
        for result in missing:
            print(f"- {result.label}")
        return 1

    print("All required workspace items are present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())