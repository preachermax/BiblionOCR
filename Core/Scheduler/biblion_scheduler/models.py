"""Domain records for the initial scheduling kernel."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from math import ceil
from typing import Mapping

from .calendar import WorkingCalendar


class DependencyType(str, Enum):
    """Supported predecessor/successor relationship types."""

    FINISH_TO_START = "FS"
    START_TO_START = "SS"
    FINISH_TO_FINISH = "FF"
    START_TO_FINISH = "SF"


class DurationUnit(str, Enum):
    DAYS = "days"
    HOURS = "hours"


class WorkflowScope(str, Enum):
    PROJECT = "project"
    PAGE = "page"


class WorkflowReconciliationStatus(str, Enum):
    NEW = "new"
    MAPPED = "mapped"
    CHANGED = "changed"
    IGNORED = "ignored"
    CONFLICT = "conflict"
    APPROVED = "approved"


class WorkflowMappingRole(str, Enum):
    INFORMATIONAL = "informational"
    IMPLEMENTS = "implements"
    MILESTONE = "milestone"


@dataclass(frozen=True)
class WorkflowSourceSnapshot:
    """An immutable registration of one imported workflow source revision."""

    id: str
    project_id: str
    source: str
    scope: WorkflowScope
    source_revision: str
    checksum: str
    schema_version: str
    imported_at: datetime


@dataclass(frozen=True)
class GovernedWorkflow:
    """A stable Scheduler-owned workflow identity created through reconciliation."""

    id: str
    project_id: str
    scope: WorkflowScope
    sequence: str
    milestone_name: str
    method: str
    description: str = ""
    module: str = ""
    section: str = ""
    source_module: str = ""
    destination_module: str = ""


@dataclass(frozen=True)
class WorkflowImportRecord:
    """One immutable source row and its current reconciliation disposition."""

    id: str
    snapshot_id: str
    source_row: int
    identity: tuple[str, ...]
    payload: Mapping[str, str]
    status: WorkflowReconciliationStatus = WorkflowReconciliationStatus.NEW
    workflow_id: str | None = None


@dataclass(frozen=True)
class WorkflowTaskMapping:
    """An approved many-to-many association that does not create schedule logic."""

    project_id: str
    workflow_id: str
    task_id: str
    role: WorkflowMappingRole
    approved_at: datetime


@dataclass(frozen=True)
class WorkflowAuditEvent:
    """An append-only record of a workflow governance decision."""

    id: str
    project_id: str
    recorded_at: datetime
    action: str
    entity_type: str
    entity_id: str
    details: Mapping[str, object]


@dataclass(frozen=True)
class WorkflowGovernanceState:
    """The read-only governance projection consumed by desktop clients."""

    snapshots: tuple[WorkflowSourceSnapshot, ...]
    records: tuple[WorkflowImportRecord, ...]
    workflows: tuple[GovernedWorkflow, ...]
    mappings: tuple[WorkflowTaskMapping, ...]
    audit_events: tuple[WorkflowAuditEvent, ...]


class ProgressStatus(str, Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETE = "Complete"


@dataclass(frozen=True)
class WorkflowLink:
    """Trace one planned task to an authoritative workflow export row."""

    task_id: str
    scope: WorkflowScope
    source: str
    identity: tuple[str, ...]
    source_row: int | None = None

    def __post_init__(self) -> None:
        expected_parts = 4 if self.scope is WorkflowScope.PAGE else 3
        if not self.task_id.strip():
            raise ValueError("Workflow link task id is required.")
        if not self.source.strip():
            raise ValueError("Workflow link source is required.")
        if len(self.identity) != expected_parts:
            raise ValueError(f"{self.scope.value} workflow identity requires {expected_parts} parts.")
        if self.source_row is not None and self.source_row < 2:
            raise ValueError("Workflow source rows begin at row 2.")


@dataclass(frozen=True)
class WBSElement:
    """A stable node in a project's work breakdown structure."""

    id: str
    code: str
    name: str
    parent_id: str | None = None
    planned_start: date | None = None
    planned_finish: date | None = None
    duration_unit: DurationUnit = DurationUnit.DAYS

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("WBS element id is required.")
        if not self.code.strip():
            raise ValueError("WBS element code is required.")
        if not self.name.strip():
            raise ValueError("WBS element name is required.")
        if self.parent_id == self.id:
            raise ValueError("A WBS element cannot be its own parent.")
        if (self.planned_start is None) != (self.planned_finish is None):
            raise ValueError("WBS planned start and finish must both be set or both be empty.")
        if self.planned_start and self.planned_finish and self.planned_finish < self.planned_start:
            raise ValueError("WBS planned finish cannot be before planned start.")


@dataclass(frozen=True)
class Task:
    id: str
    name: str
    duration_days: int
    wbs_id: str | None = None
    progress_percent: int = 0
    page_percent_complete: int = 0
    sequence: str = ""
    planned_start: date | None = None
    planned_finish: date | None = None
    actual_start: date | None = None
    actual_finish: date | None = None
    duration_unit: DurationUnit = DurationUnit.DAYS
    wbs_code: str = ""

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Task id is required.")
        if not self.name.strip():
            raise ValueError("Task name is required.")
        if self.wbs_code and self.wbs_id is None:
            raise ValueError("An activity WBS code requires a parent WBS element.")
        if self.duration_days < 0:
            raise ValueError("Task duration cannot be negative.")
        if not 0 <= self.progress_percent <= 100:
            raise ValueError("Task progress percent must be between 0 and 100.")
        if not 0 <= self.page_percent_complete <= 100:
            raise ValueError("Task page percent complete must be between 0 and 100.")
        if (self.planned_start is None) != (self.planned_finish is None):
            raise ValueError("Task planned start and finish must both be set or both be empty.")
        if self.planned_start and self.planned_finish and self.planned_finish < self.planned_start:
            raise ValueError("Task planned finish cannot be before planned start.")
        if self.actual_finish is not None and self.actual_start is None:
            raise ValueError("Task actual finish requires an actual start.")
        if self.actual_start and self.actual_finish and self.actual_finish < self.actual_start:
            raise ValueError("Task actual finish cannot be before actual start.")

    @property
    def status(self) -> ProgressStatus:
        if self.actual_finish is not None or self.progress_percent == 100:
            return ProgressStatus.COMPLETE
        if self.actual_start is None and self.progress_percent == 0:
            return ProgressStatus.NOT_STARTED
        return ProgressStatus.IN_PROGRESS

    @property
    def scheduled_duration_days(self) -> int:
        if self.duration_unit is DurationUnit.HOURS:
            return ceil(self.duration_days / 8)
        return self.duration_days


@dataclass(frozen=True)
class Dependency:
    predecessor_id: str
    successor_id: str
    dependency_type: DependencyType = DependencyType.FINISH_TO_START
    lag_days: int = 0

    def __post_init__(self) -> None:
        if self.predecessor_id == self.successor_id:
            raise ValueError("A task cannot depend on itself.")


class ConstraintType(str, Enum):
    AS_SOON_AS_POSSIBLE = "ASAP"
    START_NO_EARLIER_THAN = "SNET"
    START_NO_LATER_THAN = "SNLT"
    FINISH_NO_EARLIER_THAN = "FNET"
    FINISH_NO_LATER_THAN = "FNLT"
    MUST_START_ON = "MSO"
    MUST_FINISH_ON = "MFO"


@dataclass(frozen=True)
class Constraint:
    task_id: str
    constraint_type: ConstraintType
    constraint_date: date | None = None

    def __post_init__(self) -> None:
        needs_date = self.constraint_type is not ConstraintType.AS_SOON_AS_POSSIBLE
        if not self.task_id.strip():
            raise ValueError("A constraint must reference a task.")
        if needs_date and self.constraint_date is None:
            raise ValueError(f"{self.constraint_type.value} requires a date.")
        if not needs_date and self.constraint_date is not None:
            raise ValueError("ASAP does not accept a constraint date.")


@dataclass(frozen=True)
class ScheduledTask:
    task: Task
    start: date
    finish: date
    late_start: date
    late_finish: date
    total_float_days: int
    is_critical: bool


@dataclass(frozen=True)
class ScheduleResult:
    tasks: Mapping[str, ScheduledTask]
    project_start: date
    project_finish: date
    required_finish: date | None = None
    constraint_violations: tuple["ConstraintViolation", ...] = ()
    wbs_summaries: Mapping[str, "WBSSummary"] = field(default_factory=dict)


@dataclass(frozen=True)
class WBSSummary:
    element: WBSElement
    start: date | None
    finish: date | None
    activity_count: int
    milestone_count: int
    has_critical_work: bool
    progress_percent: float = 0.0
    page_percent_complete: float = 0.0
    status: ProgressStatus = ProgressStatus.NOT_STARTED
    planned_duration_days: int | None = None
    actual_start: date | None = None
    actual_finish: date | None = None
    actual_duration_days: int | None = None


@dataclass(frozen=True)
class ConstraintViolation:
    task_id: str
    constraint: Constraint
    message: str


@dataclass(frozen=True)
class ProjectSnapshot:
    """The complete, persistence-friendly set of inputs for one project."""

    id: str
    name: str
    project_start: date
    tasks: tuple[Task, ...]
    dependencies: tuple[Dependency, ...] = ()
    constraints: tuple[Constraint, ...] = ()
    calendar: WorkingCalendar = field(default_factory=WorkingCalendar)
    required_finish: date | None = None
    external_reference: str | None = None
    wbs_elements: tuple[WBSElement, ...] = ()
    workflow_links: tuple[WorkflowLink, ...] = ()

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Project id is required.")
        if not self.name.strip():
            raise ValueError("Project name is required.")
        if len({task.id for task in self.tasks}) != len(self.tasks):
            raise ValueError("Project task identifiers must be unique.")
        element_by_id = {element.id: element for element in self.wbs_elements}
        if len(element_by_id) != len(self.wbs_elements):
            raise ValueError("WBS element identifiers must be unique.")
        if len({element.code for element in self.wbs_elements}) != len(self.wbs_elements):
            raise ValueError("WBS element codes must be unique.")
        activity_codes = {task.wbs_code for task in self.tasks if task.wbs_code}
        if len(activity_codes) != len([task for task in self.tasks if task.wbs_code]):
            raise ValueError("Activity WBS codes must be unique.")
        if activity_codes & {element.code for element in self.wbs_elements}:
            raise ValueError("WBS outline codes must be unique across summaries and activities.")
        if any(element.parent_id not in element_by_id for element in self.wbs_elements if element.parent_id):
            raise ValueError("Every WBS parent must reference an existing element.")
        if any(task.wbs_id not in element_by_id for task in self.tasks if task.wbs_id):
            raise ValueError("Every task WBS assignment must reference an existing element.")
        if any(
            task.wbs_code and not task.wbs_code.startswith(f"{element_by_id[task.wbs_id].code}.")
            for task in self.tasks
            if task.wbs_id is not None
        ):
            raise ValueError("Every activity WBS code must be beneath its parent WBS element.")
        task_ids = {task.id for task in self.tasks}
        if any(link.task_id not in task_ids for link in self.workflow_links):
            raise ValueError("Every workflow link must reference an existing task.")
        if len({link.task_id for link in self.workflow_links}) != len(self.workflow_links):
            raise ValueError("A task can have only one authoritative workflow link.")
        for element in self.wbs_elements:
            visited = {element.id}
            parent_id = element.parent_id
            while parent_id is not None:
                if parent_id in visited:
                    raise ValueError("WBS elements contain a cycle.")
                visited.add(parent_id)
                parent_id = element_by_id[parent_id].parent_id


@dataclass(frozen=True)
class BaselineTask:
    task_id: str
    start: date
    finish: date


@dataclass(frozen=True)
class Baseline:
    id: str
    project_id: str
    name: str
    captured_at: datetime
    project_start: date
    project_finish: date
    tasks: Mapping[str, BaselineTask]


@dataclass(frozen=True)
class ScheduleRun:
    """An immutable, reproducible record of a calculation."""

    id: str
    project_id: str
    recorded_at: datetime
    engine_version: str
    input_hash: str
    output_hash: str
    project_start: date
    project_finish: date
