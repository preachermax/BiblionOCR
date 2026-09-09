from __future__ import annotations

import os
import csv
import shutil
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple


WORKFLOW_DIRECTORY = os.path.join("Model", "Project", "Data", "csv")
PAGE_WORKFLOW_FILENAME = "page_workflow.csv"
PAGE_MILESTONES_FILENAME = "page_workflow_milestones.csv"


@dataclass(frozen=True)
class PageWorkflowStep:
    sequence: str
    description: str
    milestone_name: str
    page_section: str
    module: str
    ui_trigger: str
    method: str
    dialog_ui: str
    notes: str
    workflow_source: str
    complete_destination: str
    workflow_handshake: str


@dataclass(frozen=True)
class PageWorkflowMilestone:
    number: int
    name: str
    language: str
    progress_percent: float
    override_allowed: bool
    module: str


def page_workflow_path(root: str) -> str:
    return os.path.join(os.path.abspath(root), WORKFLOW_DIRECTORY, PAGE_WORKFLOW_FILENAME)


def page_workflow_milestones_path(root: str) -> str:
    return os.path.join(os.path.abspath(root), WORKFLOW_DIRECTORY, PAGE_MILESTONES_FILENAME)


def load_page_workflow(root: str) -> Tuple[List[PageWorkflowStep], Dict[str, str]]:
    rows = _read_csv_rows(page_workflow_path(root))
    if not rows:
        return [], {}

    header = _header_indexes(rows[0])
    steps: List[PageWorkflowStep] = []
    notes: Dict[str, str] = {}
    for row in rows[1:]:
        sequence = _value(row, header, "Sequence")
        if sequence.lower().startswith("note "):
            notes[sequence] = _value_at(row, 1)
            continue
        if not sequence or not _value(row, header, "MilestoneName"):
            continue
        steps.append(
            PageWorkflowStep(
                sequence=sequence,
                description=_value(row, header, "Description"),
                milestone_name=_value(row, header, "MilestoneName"),
                page_section=_value(row, header, "PageSections"),
                module=_value(row, header, "Module"),
                ui_trigger=_value(row, header, "UITrigger"),
                method=_value(row, header, "Method"),
                dialog_ui=_value(row, header, "DialogUi"),
                notes=_value(row, header, "Notes"),
                workflow_source=_value(row, header, "DefaultWorkFlowSource"),
                complete_destination=_value(row, header, "DefaultCompleteDestination"),
                workflow_handshake=_value(row, header, "DefaultWorklowHandshake"),
            )
        )
    return steps, notes


def load_page_workflow_milestones(root: str) -> List[PageWorkflowMilestone]:
    rows = _read_csv_rows(page_workflow_milestones_path(root))
    if not rows:
        return []

    header = _header_indexes(rows[0])
    milestones: List[PageWorkflowMilestone] = []
    for row in rows[1:]:
        name = _value(row, header, "MilestoneName")
        if not name:
            continue
        try:
            number = int(float(_value(row, header, "MilestoneNum")))
        except (TypeError, ValueError):
            continue
        milestones.append(
            PageWorkflowMilestone(
                number=number,
                name=name,
                language=_value(row, header, "Language"),
                progress_percent=_parse_percent(_value(row, header, "PageProgress%")),
                override_allowed=_value(row, header, "Override").upper() == "Y",
                module=_value(row, header, "Module"),
            )
        )
    return milestones


def select_page_workflow_step(
    root: str,
    module: str,
    method: str,
    page_section: str,
    completed_milestones: Iterable[str] = (),
) -> PageWorkflowStep | None:
    steps, _ = load_page_workflow(root)
    normalized_section = _normalize_page_section(page_section)
    completed = {str(name).strip() for name in completed_milestones}
    candidates = [
        step
        for step in steps
        if step.module == module
        and step.method == method
        and _normalize_page_section(step.page_section) == normalized_section
    ]
    return next((step for step in candidates if step.milestone_name not in completed), None)


def resolve_page_workflow_path(root: str, configured_path: str) -> str:
    relative_path = str(configured_path or "").strip().lstrip(":/\\")
    if not relative_path:
        return ""
    return os.path.normpath(os.path.join(os.path.abspath(root), relative_path))


def advance_page_workflow_files(
    root: str,
    step: PageWorkflowStep,
    stage_source: bool = False,
) -> Tuple[str, str, str]:
    workflow_source = resolve_page_workflow_path(root, step.workflow_source)
    complete_destination = resolve_page_workflow_path(root, step.complete_destination)
    workflow_handshake = resolve_page_workflow_path(root, step.workflow_handshake)

    if stage_source:
        _copy_directory_contents(workflow_source, complete_destination)
    if not _directory_has_files(complete_destination):
        raise FileNotFoundError(
            f"Workflow step {step.sequence} produced no files in {complete_destination}"
        )
    _copy_directory_contents(complete_destination, workflow_handshake)
    if os.path.normcase(os.path.abspath(workflow_source)) != os.path.normcase(
        os.path.abspath(complete_destination)
    ):
        _clear_directory_contents(workflow_source)
    return workflow_source, complete_destination, workflow_handshake


def _read_csv_rows(path: str) -> List[List[str]]:
    if not os.path.isfile(path):
        return []
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as handle:
            return [row for row in csv.reader(handle) if any(value.strip() for value in row)]
    except (OSError, csv.Error):
        return []


def _copy_directory_contents(source_dir: str, destination_dir: str) -> None:
    if not source_dir or not destination_dir or not os.path.isdir(source_dir):
        return
    if os.path.normcase(os.path.abspath(source_dir)) == os.path.normcase(os.path.abspath(destination_dir)):
        return
    os.makedirs(destination_dir, exist_ok=True)
    for name in os.listdir(source_dir):
        source = os.path.join(source_dir, name)
        destination = os.path.join(destination_dir, name)
        if os.path.isdir(source) and not os.path.islink(source):
            shutil.copytree(source, destination, dirs_exist_ok=True)
        else:
            shutil.copy2(source, destination)


def _clear_directory_contents(workflow_dir: str) -> None:
    if not workflow_dir or not os.path.isdir(workflow_dir):
        return
    for name in os.listdir(workflow_dir):
        path = os.path.join(workflow_dir, name)
        if os.path.isdir(path) and not os.path.islink(path):
            shutil.rmtree(path)
        else:
            os.remove(path)


def _directory_has_files(path: str) -> bool:
    if not path or not os.path.isdir(path):
        return False
    return any(filenames for _root, _directories, filenames in os.walk(path))


def _header_indexes(header: Sequence[str]) -> Dict[str, int]:
    indexes: Dict[str, int] = {}
    for index, name in enumerate(header):
        normalized = str(name or "").strip()
        if normalized and normalized not in indexes:
            indexes[normalized] = index
    return indexes


def _value(row: Sequence[str], header: Dict[str, int], name: str) -> str:
    index = header.get(name)
    return _value_at(row, index) if index is not None else ""


def _value_at(row: Sequence[str], index: int) -> str:
    if index < 0 or index >= len(row):
        return ""
    return str(row[index] or "").strip()


def _parse_percent(value: str) -> float:
    try:
        return float(str(value or "0").strip().rstrip("%"))
    except ValueError:
        return 0.0


def _normalize_page_section(value: str) -> str:
    compact = "".join(character for character in str(value or "").lower() if character.isalnum())
    aliases = {
        "front": "front",
        "frontmatter": "front",
        "frontsection": "front",
        "middle": "middle",
        "middlematter": "middle",
        "middlesection": "middle",
        "middlesections": "middle",
        "scripture": "verse",
        "verse": "verse",
        "versesection": "verse",
        "versesections": "verse",
        "back": "back",
        "backmatter": "back",
        "backsection": "back",
    }
    return aliases.get(compact, compact)