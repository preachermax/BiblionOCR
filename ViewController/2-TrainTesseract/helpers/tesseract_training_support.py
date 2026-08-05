from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


DEFAULT_TESSERACT_TESSDATA_CANDIDATES = (
    "/usr/share/tesseract-ocr/5/tessdata",
    "/usr/share/tesseract-ocr/4.00/tessdata",
    "/usr/share/tesseract-ocr/tessdata",
    "/usr/share/tessdata",
    "/usr/local/share/tesseract-ocr/tessdata",
    "/usr/local/share/tessdata",
    r"C:\Program Files\Tesseract-OCR\tessdata",
    r"C:\Program Files (x86)\Tesseract-OCR\tessdata",
)


@dataclass(frozen=True)
class TesseractInstallation:
    binary_path: str
    tessdata_dir: str
    languages: Tuple[str, ...]


@dataclass(frozen=True)
class TrainingWorkspace:
    project_root: Path
    language_code: str
    workspace_root: Path
    data_root: Path
    ground_truth_root: Path
    wordlist_root: Path
    config_root: Path
    log_root: Path
    plot_root: Path
    model_root: Path
    script_root: Path
    tesstrain_root: Path

    @classmethod
    def from_project_root(cls, project_root: str | Path, language_code: str = "feg") -> "TrainingWorkspace":
        project_root_path = Path(project_root).resolve()
        workspace_root = project_root_path / "Model" / "Project" / "Training" / "Tesseract"
        data_root = workspace_root / "data"
        ground_truth_root = data_root / f"{language_code}-ground-truth"
        wordlist_root = workspace_root / "wordlists" / language_code
        config_root = workspace_root / "configs" / language_code
        log_root = workspace_root / "logs" / language_code
        plot_root = workspace_root / "plots" / language_code
        model_root = workspace_root / "models" / language_code
        script_root = workspace_root / "scripts"
        tesstrain_root = workspace_root / "tesstrain"
        return cls(
            project_root=project_root_path,
            language_code=language_code,
            workspace_root=workspace_root,
            data_root=data_root,
            ground_truth_root=ground_truth_root,
            wordlist_root=wordlist_root,
            config_root=config_root,
            log_root=log_root,
            plot_root=plot_root,
            model_root=model_root,
            script_root=script_root,
            tesstrain_root=tesstrain_root,
        )

    @property
    def log_file(self) -> Path:
        return self.log_root / f"{self.language_code}.log"

    @property
    def plot_file(self) -> Path:
        return self.plot_root / "training_progress.png"

    def ensure_directories(self) -> None:
        for directory in (
            self.workspace_root,
            self.data_root,
            self.ground_truth_root,
            self.wordlist_root,
            self.config_root,
            self.log_root,
            self.plot_root,
            self.model_root,
            self.script_root,
            self.tesstrain_root,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    def as_environment(self, installation: Optional[TesseractInstallation] = None) -> Dict[str, str]:
        environment = {
            "BIBLION_TRAINING_ROOT": str(self.workspace_root),
            "BIBLION_TRAINING_LANGUAGE": self.language_code,
            "BIBLION_TRAINING_GROUND_TRUTH_DIR": str(self.ground_truth_root),
            "BIBLION_TRAINING_WORDLIST_DIR": str(self.wordlist_root),
            "BIBLION_TRAINING_CONFIG_DIR": str(self.config_root),
            "BIBLION_TRAINING_LOG_DIR": str(self.log_root),
            "BIBLION_TRAINING_PLOT_DIR": str(self.plot_root),
            "BIBLION_TRAINING_MODEL_DIR": str(self.model_root),
            "BIBLION_TRAINING_SCRIPT_DIR": str(self.script_root),
            "BIBLION_TRAINING_TESSSTRAIN_DIR": str(self.tesstrain_root),
            "BIBLION_TRAINING_LOG_FILE": str(self.log_file),
            "BIBLION_TRAINING_PLOT_FILE": str(self.plot_file),
        }
        if installation:
            environment.update(
                {
                    "TESSERACT_BIN": installation.binary_path,
                    "TESSDATA_PREFIX": installation.tessdata_dir,
                }
            )
        return environment


@dataclass(frozen=True)
class TrainingPoint:
    iteration: int
    value: float
    label: str = "loss"


def discover_tesseract_binary() -> Optional[str]:
    binary_path = shutil.which("tesseract")
    if binary_path:
        return binary_path

    for candidate in (
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ):
        if os.path.exists(candidate):
            return candidate
    return None


def discover_tessdata_dir() -> Optional[str]:
    for candidate in _candidate_tessdata_dirs():
        if os.path.isdir(candidate):
            return candidate
    return None


def discover_tesseract_installation() -> Optional[TesseractInstallation]:
    binary_path = discover_tesseract_binary()
    if not binary_path:
        return None

    tessdata_dir = discover_tessdata_dir() or ""
    languages = discover_tesseract_languages(binary_path)
    return TesseractInstallation(binary_path=binary_path, tessdata_dir=tessdata_dir, languages=languages)


def discover_tesseract_languages(tesseract_binary: Optional[str] = None) -> Tuple[str, ...]:
    binary_path = tesseract_binary or discover_tesseract_binary()
    if not binary_path:
        return ()

    result = subprocess.run(
        [binary_path, "--list-langs"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return ()

    languages: List[str] = []
    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        if not line or line.lower().startswith("list of available languages"):
            continue
        languages.append(line)
    return tuple(sorted(dict.fromkeys(languages)))


def parse_training_progress(log_text: str) -> List[TrainingPoint]:
    iteration_pattern = re.compile(r"(?:iter(?:ation)?|step)\s*[:=]?\s*(\d+)", re.IGNORECASE)
    value_patterns = (
        re.compile(r"(?:loss|objective)\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE),
        re.compile(r"(?:error(?:\s+rate)?)\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE),
    )

    points: List[TrainingPoint] = []
    for raw_line in log_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        iteration_match = iteration_pattern.search(line)
        if not iteration_match:
            continue

        metric_value: Optional[float] = None
        metric_label = "loss"
        for pattern, label in zip(value_patterns, ("loss", "error")):
            value_match = pattern.search(line)
            if value_match:
                metric_value = float(value_match.group(1))
                metric_label = label
                break

        if metric_value is None:
            continue

        points.append(
            TrainingPoint(
                iteration=int(iteration_match.group(1)),
                value=metric_value,
                label=metric_label,
            )
        )

    return points


def load_training_progress(log_path: str | Path) -> List[TrainingPoint]:
    log_file = Path(log_path)
    if not log_file.exists():
        return []

    try:
        log_text = log_file.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    return parse_training_progress(log_text)


def build_training_command_environment(
    project_root: str | Path,
    language_code: str = "feg",
) -> Dict[str, str]:
    workspace = TrainingWorkspace.from_project_root(project_root, language_code=language_code)
    workspace.ensure_directories()
    installation = discover_tesseract_installation()
    environment = workspace.as_environment(installation)
    if installation:
        environment["BIBLION_TESSERACT_BIN"] = installation.binary_path
        environment["BIBLION_TESSDATA_DIR"] = installation.tessdata_dir
        environment["BIBLION_TESSERACT_LANGUAGES"] = ";".join(installation.languages)
    return environment


def _candidate_tessdata_dirs() -> Iterable[str]:
    tessdata_prefix = os.environ.get("TESSDATA_PREFIX", "").strip()
    if tessdata_prefix:
        yield tessdata_prefix

    for candidate in DEFAULT_TESSERACT_TESSDATA_CANDIDATES:
        yield candidate