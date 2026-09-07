from __future__ import annotations

import argparse
import importlib.util
import os
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
PYRIGHT_ATTRIBUTE_DIRECTIVE = b"# pyright: reportAttributeAccessIssue=false\n"


@dataclass(frozen=True)
class GeneratedFile:
    tool: str
    source: str
    target: str
    prefix: bytes = b""


GENERATED_FILES = (
    GeneratedFile("pyuic5", "Developer/QtDesignerUI/MainUI.ui", "ViewController/0-MainUI/helpers/MainUI.py"),
    GeneratedFile("pyuic5", "Developer/QtDesignerUI/MyBoxerUI.ui", "ViewController/1-PreProcess/MyBoxerUI.py"),
    GeneratedFile("pyuic5", "Developer/QtDesignerUI/MyExplorerUI.ui", "ViewController/0-MainUI/MyExplorerUI.py"),
    GeneratedFile("pyuic5", "Developer/QtDesignerUI/MyGlypherUI.ui", "ViewController/1-PreProcess/MyGlypherUI.py"),
    GeneratedFile("pyuic5", "Developer/QtDesignerUI/MyGrounderUI.ui", "ViewController/2-TrainTesseract/MyGrounderUI.py"),
    GeneratedFile("pyuic5", "Developer/QtDesignerUI/MyLauncherUI.ui", "ViewController/archives/MyLauncherUI.py"),
    GeneratedFile("pyuic5", "Developer/QtDesignerUI/MyLexerUI.ui", "ViewController/3-Process/MyLexerUI.py"),
    GeneratedFile("pyuic5", "Developer/QtDesignerUI/MorphologyDialogUI.ui", "ViewController/0-MainUI/helpers/MorphologyDialogUI.py"),
    GeneratedFile("pyuic5", "Developer/QtDesignerUI/MyPixlerGVUI.ui", "ViewController/archives/moved_candidates/0-MainUI/MyPixlerGVUI.py"),
    GeneratedFile("pyuic5", "Developer/QtDesignerUI/MyPixlerUI.ui", "ViewController/1-PreProcess/MyPixlerUI.py"),
    GeneratedFile("pyuic5", "Developer/QtDesignerUI/MyReaderUI.ui", "ViewController/2-TrainTesseract/MyReaderUI.py"),
    GeneratedFile("pyuic5", "Developer/QtDesignerUI/MyResolverUI.ui", "ViewController/3-Process/MyResolverUI.py"),
    GeneratedFile("pyuic5", "Developer/QtDesignerUI/MyScannerUI.ui", "ViewController/0-MainUI/MyScannerUI.py"),
    GeneratedFile("pyuic5", "Developer/QtDesignerUI/MyServerUI.ui", "ViewController/0-MainUI/MyServerUI.py"),
    GeneratedFile("pyuic5", "Developer/QtDesignerUI/MyTrainerUI.ui", "ViewController/2-TrainTesseract/MyTrainerUI.py"),
    GeneratedFile("pyuic5", "Developer/QtDesignerUI/MyVersifierUI.ui", "ViewController/3-Process/MyVersifierUI.py"),
    GeneratedFile("pyuic5", "Developer/QtDesignerUI/MyWriterUI.ui", "ViewController/4-PostProcess/MyWriterUI.py"),
    GeneratedFile("pyuic5", "Developer/QtDesignerUI/PageVerseCrossReferenceUI.ui", "ViewController/utilities/0-MainUI/helpers/PageVerseCrossReferenceUI.py"),
    GeneratedFile("pyuic5", "Developer/QtDesignerUI/VersifyTextUI.ui", "ViewController/utilities/0-MainUI/helpers/VersifyTextUI.py"),
    GeneratedFile("pyuic5", "Developer/QtDesignerUI/ProjectCreationWizardDialogUI.ui", "ViewController/0-MainUI/helpers/ProjectCreationWizardDialogUI.py"),
    GeneratedFile(
        "pyuic5",
        "Developer/QtDesignerUI/MyPixlerPageWorkflowWizardUI.ui",
        "ViewController/1-PreProcess/MyPixlerPageWorkflowWizardUI.py",
        PYRIGHT_ATTRIBUTE_DIRECTIVE,
    ),
    GeneratedFile("pyrcc5", "ViewController/0-MainUI/helpers/UI_Icons.qrc", "ViewController/0-MainUI/helpers/UI_Icons.py"),
)


def _command(item: GeneratedFile, temporary_target: Path) -> list[str]:
    if item.tool == "pyuic5":
        return [
            sys.executable,
            "-m",
            "PyQt5.uic.pyuic",
            "-x",
            item.source,
            "-o",
            str(temporary_target),
            "--resource-suffix=",
        ]
    return [sys.executable, "-m", "PyQt5.pyrcc_main", item.source, "-o", str(temporary_target)]


def _generate(item: GeneratedFile, temporary_target: Path) -> bytes:
    subprocess.run(
        _command(item, temporary_target),
        cwd=REPOSITORY_ROOT,
        check=True,
    )
    return item.prefix + temporary_target.read_bytes()


def _replace_if_changed(target: Path, content: bytes, check_only: bool) -> str:
    if target.is_file() and target.read_bytes() == content:
        return "unchanged"
    if check_only:
        return "stale"

    target.parent.mkdir(parents=True, exist_ok=True)
    mode = stat.S_IMODE(target.stat().st_mode) if target.exists() else 0o644
    with tempfile.NamedTemporaryFile(
        dir=target.parent,
        prefix=f".{target.name}.",
        suffix=".tmp",
        delete=False,
    ) as temporary_file:
        temporary_file.write(content)
        temporary_name = Path(temporary_file.name)
    try:
        os.chmod(temporary_name, mode)
        os.replace(temporary_name, target)
    finally:
        temporary_name.unlink(missing_ok=True)
    return "updated"


def _validate_prerequisites() -> None:
    required_modules = {
        "pyuic5": "PyQt5.uic.pyuic",
        "pyrcc5": "PyQt5.pyrcc_main",
    }
    missing_tools = sorted(
        tool
        for tool, module_name in required_modules.items()
        if importlib.util.find_spec(module_name) is None
    )
    missing_sources = [item.source for item in GENERATED_FILES if not (REPOSITORY_ROOT / item.source).is_file()]
    if missing_tools:
        raise RuntimeError(f"Missing required command(s): {', '.join(missing_tools)}")
    if missing_sources:
        raise RuntimeError("Missing source file(s): " + ", ".join(missing_sources))


def update_generated_files(check_only: bool = False) -> int:
    _validate_prerequisites()
    counts = {"updated": 0, "unchanged": 0, "stale": 0}

    with tempfile.TemporaryDirectory(prefix="biblion-ui-") as temporary_directory:
        temporary_root = Path(temporary_directory)
        for index, item in enumerate(GENERATED_FILES):
            temporary_target = temporary_root / f"generated-{index}.py"
            content = _generate(item, temporary_target)
            target = REPOSITORY_ROOT / item.target
            status = _replace_if_changed(target, content, check_only)
            counts[status] += 1
            print(f"{status.upper():9} {item.target}")

    print(
        f"Summary: {counts['updated']} updated, {counts['unchanged']} unchanged, "
        f"{counts['stale']} stale"
    )
    return 1 if counts["stale"] else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate Qt UI/resource modules without rewriting unchanged targets."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="report stale generated files without updating them",
    )
    arguments = parser.parse_args()
    try:
        return update_generated_files(check_only=arguments.check)
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())