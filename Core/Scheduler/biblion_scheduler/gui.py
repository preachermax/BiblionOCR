"""Desktop-native Qt workspace for inspecting a calculated schedule."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, replace
from datetime import date, timedelta
from pathlib import Path
import re
from typing import Callable, Mapping

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QCloseEvent, QPainter, QPen, QPolygonF
from PyQt5.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QAction,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QStyle,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QTreeWidget,
    QTreeWidgetItem,
    QTreeWidgetItemIterator,
    QVBoxLayout,
    QWidget,
)

from .models import (
    Baseline,
    Dependency,
    DependencyType,
    DurationUnit,
    GovernedWorkflow,
    ProgressStatus,
    ProjectSnapshot,
    ScheduleResult,
    Task,
    WBSElement,
    WorkflowGovernanceState,
    WorkflowImportRecord,
    WorkflowMappingRole,
    WorkflowReconciliationStatus,
    WorkflowScope,
    WorkflowSourceSnapshot,
    WorkflowTaskMapping,
)
from .help_content import HELP_TOPICS, help_topic, search_help_topics
from .planner import PlanEditor
from .scheduler import ScheduleEngine


ROW_HEIGHT = 30
HEADER_HEIGHT = 38
DAY_WIDTH = 18
LEVEL_1_COLOR = QColor("#0f766e")
LEVEL_2_COLOR = QColor("#d97706")
LEVEL_3_COLOR = QColor("#2563eb")
COMPLETE_COLOR = QColor("#15803d")
NOT_STARTED_COLOR = QColor("#94a3b8")
PLANNED_TRACK_COLOR = QColor("#ffffff")
WBS_CODE_COLUMN = 0
WBS_NAME_COLUMN = 1
WBS_PLANNED_START_COLUMN = 9
WBS_PLANNED_FINISH_COLUMN = 10
WBS_UNITS_COLUMN = 15
WBS_NUMERIC_COLUMNS = {2, 7, 8, 11, 14, 16, 17}
WBS_FILLABLE_COLUMNS = {
    WBS_NAME_COLUMN,
    WBS_PLANNED_START_COLUMN,
    WBS_PLANNED_FINISH_COLUMN,
    WBS_UNITS_COLUMN,
}
SCHEDULE_NUMERIC_COLUMNS = {7, 9, 10, 13, 16, 17}


def natural_code_key(code: str) -> tuple[tuple[int, object], ...]:
    return tuple(
        (0, int(part)) if part.isdigit() else (1, part.casefold())
        for part in re.split(r"([0-9]+)", code)
        if part
    )


def optional_date(value: str) -> date | None:
    text = value.strip()
    return date.fromisoformat(text) if text else None


def date_text(value: date | None) -> str:
    return value.isoformat() if value else ""


@dataclass(frozen=True)
class TimelineRow:
    kind: str
    id: str
    depth: int

    @property
    def level(self) -> int:
        if self.kind == "task":
            return 3
        return 1 if self.depth == 0 else 2


@dataclass(frozen=True)
class RelationshipFields:
    predecessors: str
    successors: str
    logic: str


@dataclass(frozen=True)
class WorkflowActivityMappingResult:
    mapping: WorkflowTaskMapping
    project: ProjectSnapshot
    result: ScheduleResult


@dataclass(frozen=True)
class WorkflowGovernanceCallbacks:
    default_source: str
    load: Callable[[], WorkflowGovernanceState]
    import_source: Callable[[str, WorkflowScope, str], WorkflowSourceSnapshot]
    approve: Callable[[str], GovernedWorkflow]
    set_status: Callable[[str, WorkflowReconciliationStatus], None]
    map_task: Callable[
        [str, str, WorkflowMappingRole, str, ProjectSnapshot],
        WorkflowActivityMappingResult,
    ]


class WBSTreeWidgetItem(QTreeWidgetItem):
    """Sort WBS codes numerically while retaining normal text sorting elsewhere."""

    def __lt__(self, other: QTreeWidgetItem) -> bool:
        tree = self.treeWidget()
        column = tree.sortColumn() if tree is not None else WBS_CODE_COLUMN
        if column == WBS_CODE_COLUMN:
            return natural_code_key(self.text(column)) < natural_code_key(other.text(column))
        if column in WBS_NUMERIC_COLUMNS:
            return self._number(self.text(column)) < self._number(other.text(column))
        return self.text(column).casefold() < other.text(column).casefold()

    @staticmethod
    def _number(value: str) -> float:
        match = re.search(r"-?[0-9]+(?:\.[0-9]+)?", value.replace(",", ""))
        return float(match.group()) if match else float("-inf")


class ScheduleTableWidgetItem(QTableWidgetItem):
    """Compare schedule cells by a typed key and stable hierarchy position."""

    def __init__(self, text: str, sort_key: object) -> None:
        super().__init__(text)
        self._sort_key = sort_key

    def __lt__(self, other: QTableWidgetItem) -> bool:
        if isinstance(other, ScheduleTableWidgetItem):
            return self._sort_key < other._sort_key
        return super().__lt__(other)


def relationship_fields(project: ProjectSnapshot, row: TimelineRow) -> RelationshipFields:
    """Project task relationships onto an activity or enclosing WBS summary."""
    task_by_id = {task.id: task for task in project.tasks}
    element_by_id = {element.id: element for element in project.wbs_elements}

    if row.kind == "task":
        enclosed_ids = {row.id}
    else:
        enclosed_ids = set()
        for task in project.tasks:
            element_id = task.wbs_id
            while element_id is not None:
                if element_id == row.id:
                    enclosed_ids.add(task.id)
                    break
                element_id = element_by_id[element_id].parent_id

    incoming = [
        edge for edge in project.dependencies
        if edge.successor_id in enclosed_ids and edge.predecessor_id not in enclosed_ids
    ]
    outgoing = [
        edge for edge in project.dependencies
        if edge.predecessor_id in enclosed_ids and edge.successor_id not in enclosed_ids
    ]
    if row.kind == "task":
        incoming = [edge for edge in project.dependencies if edge.successor_id == row.id]
        outgoing = [edge for edge in project.dependencies if edge.predecessor_id == row.id]

    predecessors = ", ".join(task_by_id[edge.predecessor_id].name for edge in incoming) or "Project Start"
    successors = ", ".join(task_by_id[edge.successor_id].name for edge in outgoing) or "Project Finish"
    boundary_edges = (*incoming, *outgoing)
    logic = "; ".join(
        f"{task_by_id[edge.predecessor_id].name} {edge.dependency_type.value} "
        f"{task_by_id[edge.successor_id].name}"
        f"{' ' + format(edge.lag_days, '+d') + 'd' if edge.lag_days else ''}"
        for edge in boundary_edges
    ) or "—"
    return RelationshipFields(predecessors, successors, logic)


def wbs_sequences(project: ProjectSnapshot, element_id: str) -> str:
    """Return unique descendant activity sequences in stable task order."""
    element_by_id = {element.id: element for element in project.wbs_elements}
    sequences: list[str] = []
    for task in project.tasks:
        current_id = task.wbs_id
        while current_id is not None:
            if current_id == element_id:
                if task.sequence and task.sequence not in sequences:
                    sequences.append(task.sequence)
                break
            current_id = element_by_id[current_id].parent_id
    return ", ".join(sequences)


def timeline_rows(project: ProjectSnapshot) -> tuple[TimelineRow, ...]:
    """Return WBS summaries and activities in stable hierarchical order."""
    children: dict[str | None, list[WBSElement]] = defaultdict(list)
    tasks_by_wbs: dict[str | None, list[Task]] = defaultdict(list)
    for element in project.wbs_elements:
        children[element.parent_id].append(element)
    for task in project.tasks:
        tasks_by_wbs[task.wbs_id].append(task)
    for siblings in children.values():
        siblings.sort(key=lambda element: natural_code_key(element.code))

    rows: list[TimelineRow] = []

    def append_element(element: WBSElement, depth: int) -> None:
        rows.append(TimelineRow("summary", element.id, depth))
        rows.extend(TimelineRow("task", task.id, depth + 1) for task in tasks_by_wbs[element.id])
        for child in children[element.id]:
            append_element(child, depth + 1)

    for root in children[None]:
        append_element(root, 0)
    rows.extend(TimelineRow("task", task.id, 0) for task in tasks_by_wbs[None])
    return tuple(rows)


class GanttCanvas(QWidget):
    """Paint-only timeline; schedule data remains owned by the domain engine."""

    def __init__(
        self,
        project: ProjectSnapshot,
        result: ScheduleResult,
        baseline: Baseline | None = None,
        rows: tuple[TimelineRow, ...] | None = None,
    ) -> None:
        super().__init__()
        self._project = project
        self._result = result
        self._baseline = baseline
        self._rows = rows if rows is not None else timeline_rows(project)
        self._task_row = {row.id: index for index, row in enumerate(self._rows) if row.kind == "task"}
        timeline_dates = [value for item in result.tasks.values() for value in (item.start, item.finish)]
        timeline_dates.extend(
            value
            for task in project.tasks
            for value in (task.actual_start, task.actual_finish)
            if value is not None
        )
        timeline_dates.extend(
            value
            for summary in result.wbs_summaries.values()
            for value in (summary.start, summary.finish, summary.actual_start, summary.actual_finish)
            if value is not None
        )
        if not timeline_dates:
            timeline_dates.append(result.project_start)
        self._first_date = min(timeline_dates)
        self._last_date = max(timeline_dates)
        labels = [task.name for task in project.tasks]
        labels.extend(f"{element.code}  {element.name}" for element in project.wbs_elements)
        longest_label = max(
            (self.fontMetrics().horizontalAdvance(label) for label in labels),
            default=self.fontMetrics().horizontalAdvance(project.name),
        )
        self.setMinimumSize(
            self._day_count * DAY_WIDTH + longest_label + 36,
            HEADER_HEIGHT + len(self._rows) * ROW_HEIGHT,
        )

    def set_rows(self, rows: tuple[TimelineRow, ...]) -> None:
        self._rows = rows
        self._task_row = {row.id: index for index, row in enumerate(rows) if row.kind == "task"}
        self.update()

    @property
    def _day_count(self) -> int:
        return (self._last_date - self._first_date).days + 1

    def _x_for_date(self, value: date) -> int:
        return (value - self._first_date).days * DAY_WIDTH

    def _row_y(self, task_id: str) -> int:
        return HEADER_HEIGHT + self._task_row[task_id] * ROW_HEIGHT

    def _dependency_x_coordinates(self, edge: Dependency) -> tuple[int, int]:
        predecessor = self._result.tasks[edge.predecessor_id]
        successor = self._result.tasks[edge.successor_id]
        predecessor_date = (
            predecessor.start
            if edge.dependency_type in (DependencyType.START_TO_START, DependencyType.START_TO_FINISH)
            else predecessor.finish
        )
        successor_date = (
            successor.finish
            if edge.dependency_type in (DependencyType.FINISH_TO_FINISH, DependencyType.START_TO_FINISH)
            else successor.start
        )
        source_x = self._x_for_date(predecessor_date)
        target_x = self._x_for_date(successor_date)
        if edge.dependency_type in (DependencyType.FINISH_TO_START, DependencyType.FINISH_TO_FINISH):
            source_x += DAY_WIDTH - 2
        else:
            source_x += 2
        if edge.dependency_type in (DependencyType.FINISH_TO_FINISH, DependencyType.START_TO_FINISH):
            target_x += DAY_WIDTH - 2
        else:
            target_x += 2
        return source_x, target_x

    def paintEvent(self, _event: object) -> None:  # noqa: N802 - Qt callback
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#ffffff"))
        self._draw_calendar(painter)
        self._draw_bars(painter)
        self._draw_labels(painter)
        self._draw_dependencies(painter)
        painter.end()

    def _draw_calendar(self, painter: QPainter) -> None:
        painter.setFont(self.font())
        current = self._first_date
        for offset in range(self._day_count):
            x = offset * DAY_WIDTH
            if current.weekday() >= 5:
                painter.fillRect(x, 0, DAY_WIDTH, self.height(), QColor("#f3f4f6"))
            painter.setPen(QPen(QColor("#d1d5db")))
            painter.drawLine(x, 0, x, self.height())
            if current.weekday() == 0 or offset == 0:
                painter.setPen(QPen(QColor("#334155")))
                painter.drawText(QRectF(x + 2, 2, 90, 16), Qt.AlignLeft | Qt.AlignVCenter, current.strftime("%d %b"))
            current += timedelta(days=1)
        painter.setPen(QPen(QColor("#64748b"), 1))
        painter.drawLine(0, HEADER_HEIGHT, self.width(), HEADER_HEIGHT)
        for row in range(len(self._rows) + 1):
            painter.drawLine(0, HEADER_HEIGHT + row * ROW_HEIGHT, self.width(), HEADER_HEIGHT + row * ROW_HEIGHT)

    def _draw_dependencies(self, painter: QPainter) -> None:
        painter.setPen(QPen(QColor("#64748b"), 1.2))
        for edge in self._project.dependencies:
            source_x, target_x = self._dependency_x_coordinates(edge)
            source_y = self._row_y(edge.predecessor_id) + ROW_HEIGHT // 2
            target_y = self._row_y(edge.successor_id) + ROW_HEIGHT // 2
            direction = 1 if target_x >= source_x else -1
            elbow_x = target_x - direction * 8
            painter.drawLine(source_x, source_y, elbow_x, source_y)
            painter.drawLine(elbow_x, source_y, elbow_x, target_y)
            painter.drawLine(elbow_x, target_y, target_x, target_y)
            painter.drawText(QRectF(elbow_x - 18, min(source_y, target_y), 36, 16), Qt.AlignCenter, edge.dependency_type.value)
            arrow = QPolygonF([
                QPointF(target_x, target_y),
                QPointF(target_x - direction * 6, target_y - 4),
                QPointF(target_x - direction * 6, target_y + 4),
            ])
            painter.setBrush(QColor("#64748b"))
            painter.drawPolygon(arrow)

    def _draw_bars(self, painter: QPainter) -> None:
        for row_number, row in enumerate(self._rows):
            y = HEADER_HEIGHT + row_number * ROW_HEIGHT
            if row.kind == "summary":
                summary = self._result.wbs_summaries[row.id]
                if summary.start is None or summary.finish is None:
                    continue
                start_x = self._x_for_date(summary.start) + 2
                width = max(DAY_WIDTH - 4, (summary.finish - summary.start).days * DAY_WIDTH + DAY_WIDTH - 4)
                outline = LEVEL_1_COLOR if row.level == 1 else LEVEL_2_COLOR
                self._draw_progress_bar(
                    painter,
                    QRectF(start_x, y + 6, width, 12),
                    summary.progress_percent,
                    outline,
                )
                continue

            task_id = row.id
            item = self._result.tasks[task_id]
            start_x = self._x_for_date(item.start) + 2
            width = max(DAY_WIDTH - 4, (item.finish - item.start).days * DAY_WIDTH + DAY_WIDTH - 4)
            if self._baseline and task_id in self._baseline.tasks:
                planned = self._baseline.tasks[task_id]
                base_x = self._x_for_date(planned.start) + 2
                base_width = max(DAY_WIDTH - 4, (planned.finish - planned.start).days * DAY_WIDTH + DAY_WIDTH - 4)
                painter.fillRect(base_x, y + 19, base_width, 4, QColor("#94a3b8"))
            if item.task.duration_days == 0:
                center_x = start_x + DAY_WIDTH // 2 - 2
                diamond = QPolygonF([
                    QPointF(center_x, y + 7), QPointF(center_x + 7, y + 14),
                    QPointF(center_x, y + 21), QPointF(center_x - 7, y + 14),
                ])
                progress = 100 if item.task.status is ProgressStatus.COMPLETE else item.task.progress_percent
                painter.setBrush(COMPLETE_COLOR if progress > 0 else PLANNED_TRACK_COLOR)
                painter.setPen(QPen(NOT_STARTED_COLOR, 1))
                painter.drawPolygon(diamond)
            else:
                outline = QColor("#dc2626") if item.is_critical else NOT_STARTED_COLOR
                progress = 100 if item.task.status is ProgressStatus.COMPLETE else item.task.progress_percent
                self._draw_progress_bar(painter, QRectF(start_x, y + 6, width, 12), progress, outline)

    @staticmethod
    def _progress_width(width: float, progress_percent: float) -> float:
        return width * max(0.0, min(100.0, progress_percent)) / 100

    @classmethod
    def _draw_progress_bar(
        cls,
        painter: QPainter,
        bounds: QRectF,
        progress_percent: float,
        outline: QColor,
    ) -> None:
        painter.setBrush(PLANNED_TRACK_COLOR)
        painter.setPen(QPen(outline, 1.5))
        painter.drawRoundedRect(bounds, 2, 2)
        progress_width = cls._progress_width(bounds.width(), progress_percent)
        if progress_width > 0:
            painter.fillRect(
                QRectF(bounds.x(), bounds.y(), progress_width, bounds.height()),
                COMPLETE_COLOR,
            )
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(outline, 1.5))
            painter.drawRoundedRect(bounds, 2, 2)

    def _draw_labels(self, painter: QPainter) -> None:
        element_by_id = {element.id: element for element in self._project.wbs_elements}
        label_font = painter.font()
        if label_font.pointSize() > 0:
            label_font.setPointSize(max(7, label_font.pointSize() - 2))
        painter.setFont(label_font)
        for row_number, row in enumerate(self._rows):
            y = HEADER_HEIGHT + row_number * ROW_HEIGHT
            if row.kind == "summary":
                summary = self._result.wbs_summaries[row.id]
                if summary.finish is None:
                    continue
                label_x = self._x_for_date(summary.finish) + DAY_WIDTH + 4
                element = element_by_id[row.id]
                label = f"{element.code}  {element.name}"
                painter.setPen(LEVEL_1_COLOR if row.level == 1 else LEVEL_2_COLOR)
            else:
                item = self._result.tasks[row.id]
                label_x = self._x_for_date(item.finish) + DAY_WIDTH + 4
                label = item.task.name
                painter.setPen(QColor("#1f2937"))
            painter.drawText(
                QRectF(label_x, y + 18, painter.fontMetrics().horizontalAdvance(label) + 4, 10),
                Qt.AlignLeft | Qt.AlignVCenter,
                label,
            )
            if row.kind == "task" and any(
                constraint.task_id == row.id for constraint in self._project.constraints
            ):
                start_x = self._x_for_date(self._result.tasks[row.id].start) + 2
                painter.setPen(QPen(QColor("#b45309")))
                painter.drawText(QRectF(start_x - 12, y + 18, 12, 10), Qt.AlignCenter, "!")


class TaskEditorDialog(QDialog):
    """Edit activity plan and actual fields."""

    def __init__(
        self,
        task: Task,
        project: ProjectSnapshot,
        parent: QWidget | None = None,
        creating: bool = False,
    ) -> None:
        super().__init__(parent)
        self._creating = creating
        self._calendar = project.calendar
        self._wbs_code = task.wbs_code
        self._original_wbs_id = task.wbs_id
        self._is_milestone = task.duration_days == 0
        self._task_id = task.id
        self._project_tasks = project.tasks
        self.setWindowTitle("Add Activity" if creating else "Edit Activity")
        layout = QFormLayout(self)
        self._id = QLineEdit(task.id)
        self._id.setReadOnly(not creating)
        self._id.setPlaceholderText("Stable identifier, for example reader-review")
        self._name = QLineEdit(task.name)
        self._duration = QSpinBox()
        self._duration.setRange(0, 10000)
        self._duration.setValue(task.duration_days)
        self._duration.setReadOnly(not creating)
        self._duration.setToolTip(
            "Enter an estimate, or set planned start and finish to calculate it"
            if creating else "Calculated from planned start and finish when both dates are set"
        )
        self._duration_unit = QComboBox()
        self._duration_unit.addItem("Days", DurationUnit.DAYS)
        self._duration_unit.addItem("Hours", DurationUnit.HOURS)
        self._duration_unit.setCurrentIndex(self._duration_unit.findData(task.duration_unit))
        self._duration_unit.currentIndexChanged.connect(self._update_durations)
        self._planned_start = QLineEdit(date_text(task.planned_start))
        self._planned_finish = QLineEdit(date_text(task.planned_finish))
        self._actual_start = QLineEdit(date_text(task.actual_start))
        self._actual_finish = QLineEdit(date_text(task.actual_finish))
        self._actual_duration = QSpinBox()
        self._actual_duration.setRange(-1, 10000)
        self._actual_duration.setSpecialValueText("Not available")
        self._actual_duration.setReadOnly(True)
        for field in (self._planned_start, self._planned_finish, self._actual_start, self._actual_finish):
            field.setPlaceholderText("YYYY-MM-DD")
            field.textChanged.connect(self._update_durations)
        self._progress = QSpinBox()
        self._progress.setRange(0, 100)
        self._progress.setSuffix("%")
        self._progress.setValue(task.progress_percent)
        self._page_progress = QSpinBox()
        self._page_progress.setRange(0, 100)
        self._page_progress.setSuffix("%")
        self._page_progress.setValue(task.page_percent_complete)
        self._sequence = QLineEdit(task.sequence)
        self._sequence.setPlaceholderText("Workflow sequence, for example SCAN")
        self._wbs = QComboBox()
        self._wbs.addItem("Unassigned", None)
        for element in project.wbs_elements:
            self._wbs.addItem(f"{element.code}  {element.name}", element.id)
        selected = self._wbs.findData(task.wbs_id)
        self._wbs.setCurrentIndex(max(0, selected))
        self._relationship_table = QTableWidget(0, 3)
        self._relationship_table.setHorizontalHeaderLabels(["Predecessor", "Relationship", "Lead / Lag"])
        self._relationship_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._relationship_table.setMinimumHeight(130)
        self._relationship_table.setColumnWidth(0, 220)
        self._relationship_table.setColumnWidth(1, 110)
        predecessor_controls = QWidget()
        relationship_layout = QHBoxLayout(predecessor_controls)
        relationship_layout.setContentsMargins(0, 0, 0, 0)
        add_relationship = QPushButton("Add predecessor")
        add_relationship.clicked.connect(lambda: self._add_relationship_row())
        remove_relationship = QPushButton("Remove predecessor")
        remove_relationship.clicked.connect(self._remove_relationship_row)
        relationship_layout.addWidget(add_relationship)
        relationship_layout.addWidget(remove_relationship)
        relationship_layout.addStretch(1)
        for edge in project.dependencies:
            if edge.successor_id == task.id:
                self._add_relationship_row(edge)
        self._successor_table = QTableWidget(0, 3)
        self._successor_table.setHorizontalHeaderLabels(["Successor", "Relationship", "Lead / Lag"])
        self._successor_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._successor_table.setMinimumHeight(130)
        self._successor_table.setColumnWidth(0, 220)
        self._successor_table.setColumnWidth(1, 110)
        successor_controls = QWidget()
        successor_layout = QHBoxLayout(successor_controls)
        successor_layout.setContentsMargins(0, 0, 0, 0)
        add_successor = QPushButton("Add successor")
        add_successor.clicked.connect(lambda: self._add_successor_row())
        remove_successor = QPushButton("Remove successor")
        remove_successor.clicked.connect(self._remove_successor_row)
        successor_layout.addWidget(add_successor)
        successor_layout.addWidget(remove_successor)
        successor_layout.addStretch(1)
        for edge in project.dependencies:
            if edge.predecessor_id == task.id:
                self._add_successor_row(edge)
        layout.addRow("ID", self._id)
        layout.addRow("Name", self._name)
        layout.addRow("Planned start", self._planned_start)
        layout.addRow("Planned finish", self._planned_finish)
        layout.addRow("Planned duration (calculated)", self._duration)
        layout.addRow("Duration units", self._duration_unit)
        layout.addRow("Actual start", self._actual_start)
        layout.addRow("Actual finish", self._actual_finish)
        layout.addRow("Actual duration (calculated)", self._actual_duration)
        layout.addRow("Progress complete", self._progress)
        layout.addRow("Pages complete", self._page_progress)
        layout.addRow("Workflow sequence", self._sequence)
        layout.addRow("WBS", self._wbs)
        layout.addRow("Predecessor relationships", self._relationship_table)
        layout.addRow("", predecessor_controls)
        layout.addRow("Successor relationships", self._successor_table)
        layout.addRow("", successor_controls)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        help_button = buttons.addButton(QDialogButtonBox.Help)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        if isinstance(parent, ScheduleWorkspace):
            help_button.clicked.connect(lambda: parent.show_help("activities"))
        layout.addRow(buttons)
        self._update_durations()

    def _add_relationship_row(self, edge: Dependency | None = None) -> None:
        row = self._relationship_table.rowCount()
        self._relationship_table.insertRow(row)
        predecessor = QComboBox()
        for candidate in self._project_tasks:
            if candidate.id != self._task_id:
                predecessor.addItem(candidate.name, candidate.id)
        relationship = QComboBox()
        for dependency_type in DependencyType:
            relationship.addItem(dependency_type.value, dependency_type)
        lag = QSpinBox()
        lag.setRange(-10000, 10000)
        lag.setSuffix(" days")
        lag.setToolTip("Negative values are lead; positive values are lag")
        if edge is not None:
            predecessor.setCurrentIndex(max(0, predecessor.findData(edge.predecessor_id)))
            relationship.setCurrentIndex(max(0, relationship.findData(edge.dependency_type)))
            lag.setValue(edge.lag_days)
        self._relationship_table.setCellWidget(row, 0, predecessor)
        self._relationship_table.setCellWidget(row, 1, relationship)
        self._relationship_table.setCellWidget(row, 2, lag)

    def _remove_relationship_row(self) -> None:
        row = self._relationship_table.currentRow()
        if row >= 0:
            self._relationship_table.removeRow(row)

    def _add_successor_row(self, edge: Dependency | None = None) -> None:
        row = self._successor_table.rowCount()
        self._successor_table.insertRow(row)
        successor = QComboBox()
        for candidate in self._project_tasks:
            if candidate.id != self._task_id:
                successor.addItem(candidate.name, candidate.id)
        relationship = QComboBox()
        for dependency_type in DependencyType:
            relationship.addItem(dependency_type.value, dependency_type)
        lag = QSpinBox()
        lag.setRange(-10000, 10000)
        lag.setSuffix(" days")
        lag.setToolTip("Negative values are lead; positive values are lag")
        if edge is not None:
            successor.setCurrentIndex(max(0, successor.findData(edge.successor_id)))
            relationship.setCurrentIndex(max(0, relationship.findData(edge.dependency_type)))
            lag.setValue(edge.lag_days)
        self._successor_table.setCellWidget(row, 0, successor)
        self._successor_table.setCellWidget(row, 1, relationship)
        self._successor_table.setCellWidget(row, 2, lag)

    def _remove_successor_row(self) -> None:
        row = self._successor_table.currentRow()
        if row >= 0:
            self._successor_table.removeRow(row)

    def _update_durations(self) -> None:
        try:
            planned_start = optional_date(self._planned_start.text())
            planned_finish = optional_date(self._planned_finish.text())
            actual_start = optional_date(self._actual_start.text())
            actual_finish = optional_date(self._actual_finish.text())
        except ValueError:
            return
        if planned_start is not None and planned_finish is not None and planned_finish >= planned_start:
            duration = ScheduleEngine._inclusive_working_duration(planned_start, planned_finish, self._calendar) or 0
            if self._duration_unit.currentData() is DurationUnit.HOURS:
                duration *= 8
            self._duration.setValue(0 if self._is_milestone and planned_start == planned_finish else duration)
        if actual_start is not None and actual_finish is not None and actual_finish >= actual_start:
            duration = ScheduleEngine._inclusive_working_duration(actual_start, actual_finish, self._calendar) or 0
            if self._duration_unit.currentData() is DurationUnit.HOURS:
                duration *= 8
            self._actual_duration.setValue(0 if self._is_milestone and actual_start == actual_finish else duration)
        else:
            self._actual_duration.setValue(-1)

    def edited_task(self) -> Task:
        wbs_id = self._wbs.currentData()
        return Task(
            self._id.text().strip(),
            self._name.text().strip(),
            self._duration.value(),
            wbs_id,
            self._progress.value(),
            self._page_progress.value(),
            self._sequence.text().strip(),
            optional_date(self._planned_start.text()),
            optional_date(self._planned_finish.text()),
            optional_date(self._actual_start.text()),
            optional_date(self._actual_finish.text()),
            self._duration_unit.currentData(),
            self._wbs_code if wbs_id == self._original_wbs_id else "",
        )

    def edited_dependencies(self) -> tuple[Dependency, ...]:
        dependencies: list[Dependency] = []
        for row in range(self._relationship_table.rowCount()):
            predecessor = self._relationship_table.cellWidget(row, 0)
            relationship = self._relationship_table.cellWidget(row, 1)
            lag = self._relationship_table.cellWidget(row, 2)
            dependencies.append(Dependency(
                predecessor.currentData(),
                self._id.text().strip(),
                relationship.currentData(),
                lag.value(),
            ))
        return tuple(dependencies)

    def edited_relationships(self) -> tuple[Dependency, ...]:
        relationships = list(self.edited_dependencies())
        for row in range(self._successor_table.rowCount()):
            successor = self._successor_table.cellWidget(row, 0)
            relationship = self._successor_table.cellWidget(row, 1)
            lag = self._successor_table.cellWidget(row, 2)
            relationships.append(Dependency(
                self._id.text().strip(),
                successor.currentData(),
                relationship.currentData(),
                lag.value(),
            ))
        return tuple(relationships)


class WBSElementDialog(QDialog):
    """Create or edit one WBS summary item."""

    def __init__(
        self,
        project: ProjectSnapshot,
        element: WBSElement | None = None,
        parent: QWidget | None = None,
        initial_code: str = "",
        initial_parent_id: str | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit Summary Item" if element else "Add Summary Item")
        layout = QFormLayout(self)
        self._id = QLineEdit(element.id if element else "")
        self._id.setPlaceholderText("Stable identifier, for example myreader")
        self._id.setReadOnly(element is not None)
        self._code = QLineEdit(element.code if element else initial_code)
        self._code.setPlaceholderText("WBS code, for example 1.3.2")
        self._name = QLineEdit(element.name if element else "")
        self._planned_start = QLineEdit(date_text(element.planned_start) if element else "")
        self._planned_finish = QLineEdit(date_text(element.planned_finish) if element else "")
        self._duration_unit = QComboBox()
        self._duration_unit.addItem("Days", DurationUnit.DAYS)
        self._duration_unit.addItem("Hours", DurationUnit.HOURS)
        self._duration_unit.setCurrentIndex(self._duration_unit.findData(
            element.duration_unit if element else DurationUnit.DAYS
        ))
        self._planned_start.setPlaceholderText("YYYY-MM-DD; blank uses activity rollup")
        self._planned_finish.setPlaceholderText("YYYY-MM-DD; blank uses activity rollup")
        self._parent = QComboBox()
        self._parent.addItem("Top level", None)
        for candidate in project.wbs_elements:
            if element is None or candidate.id != element.id:
                self._parent.addItem(f"{candidate.code}  {candidate.name}", candidate.id)
        selected = self._parent.findData(element.parent_id if element else initial_parent_id)
        self._parent.setCurrentIndex(max(0, selected))
        layout.addRow("ID", self._id)
        layout.addRow("WBS code", self._code)
        layout.addRow("Summary name", self._name)
        layout.addRow("Parent", self._parent)
        layout.addRow("Planned start override", self._planned_start)
        layout.addRow("Planned finish override", self._planned_finish)
        layout.addRow("Duration units", self._duration_unit)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        help_button = buttons.addButton(QDialogButtonBox.Help)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        if isinstance(parent, ScheduleWorkspace):
            help_button.clicked.connect(lambda: parent.show_help("wbs"))
        layout.addRow(buttons)

    def wbs_element(self) -> WBSElement:
        return WBSElement(
            self._id.text().strip(),
            self._code.text().strip(),
            self._name.text().strip(),
            self._parent.currentData(),
            optional_date(self._planned_start.text()),
            optional_date(self._planned_finish.text()),
            self._duration_unit.currentData(),
        )


class NewWBSDialog(QDialog):
    """Collect the identity and start date for a blank WBS document."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("New WBS")
        layout = QFormLayout(self)
        self._id = QLineEdit()
        self._id.setPlaceholderText("Stable identifier, for example new-publication")
        self._name = QLineEdit()
        self._name.setPlaceholderText("Project or publication name")
        self._project_start = QLineEdit(date.today().isoformat())
        self._project_start.setPlaceholderText("YYYY-MM-DD")
        layout.addRow("Project ID", self._id)
        layout.addRow("WBS name", self._name)
        layout.addRow("Project start", self._project_start)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Create")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def project(self) -> ProjectSnapshot:
        project_id = self._id.text().strip()
        name = self._name.text().strip()
        start_text = self._project_start.text().strip()
        if not project_id:
            raise ValueError("Project ID is required.")
        if not name:
            raise ValueError("WBS name is required.")
        try:
            project_start = date.fromisoformat(start_text)
        except ValueError as error:
            raise ValueError("Project start must use YYYY-MM-DD.") from error
        return ProjectSnapshot(project_id, name, project_start, ())


class SchedulerHelpDialog(QDialog):
    """Searchable in-application guide for planning concepts and operations."""

    def __init__(self, parent: QWidget | None = None, topic_id: str = "getting-started") -> None:
        super().__init__(parent)
        self.setWindowTitle("Biblion Scheduler Help")
        self.resize(900, 640)
        layout = QVBoxLayout(self)
        search = QLineEdit()
        search.setPlaceholderText("Search help")
        search.setClearButtonEnabled(True)
        layout.addWidget(search)
        splitter = QSplitter(Qt.Horizontal)
        self._topics = QListWidget()
        self._topics.setMinimumWidth(220)
        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(True)
        splitter.addWidget(self._topics)
        splitter.addWidget(self._browser)
        splitter.setSizes([240, 660])
        layout.addWidget(splitter)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.close)
        layout.addWidget(buttons)
        search.textChanged.connect(self._filter_topics)
        self._topics.currentItemChanged.connect(self._display_topic)
        self._filter_topics("")
        self.show_topic(topic_id)

    def _filter_topics(self, query: str) -> None:
        selected_id = self._topics.currentItem().data(Qt.UserRole) if self._topics.currentItem() else None
        topics = search_help_topics(query)
        self._topics.clear()
        for topic in topics:
            item = QListWidgetItem(topic.title)
            item.setData(Qt.UserRole, topic.id)
            self._topics.addItem(item)
        if not topics:
            self._browser.setHtml("<h2>No matching topics</h2><p>Try a broader search.</p>")
            return
        matching_row = next(
            (row for row in range(self._topics.count()) if self._topics.item(row).data(Qt.UserRole) == selected_id),
            0,
        )
        self._topics.setCurrentRow(matching_row)

    def _display_topic(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        if current is not None:
            self._browser.setHtml(help_topic(current.data(Qt.UserRole)).html)

    def show_topic(self, topic_id: str) -> None:
        for row in range(self._topics.count()):
            if self._topics.item(row).data(Qt.UserRole) == topic_id:
                self._topics.setCurrentRow(row)
                return


class WorkflowGovernancePage(QWidget):
    """Review imported workflow evidence before it becomes Scheduler authority."""

    def __init__(
        self,
        project: ProjectSnapshot,
        callbacks: WorkflowGovernanceCallbacks,
        parent: QWidget | None = None,
        project_changed: Callable[[ProjectSnapshot, ScheduleResult], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self._callbacks = callbacks
        self._project = project
        self._project_changed = project_changed
        self._state = WorkflowGovernanceState((), (), (), (), ())
        layout = QVBoxLayout(self)

        import_controls = QHBoxLayout()
        self._source = QLineEdit(callbacks.default_source)
        self._source.setPlaceholderText("ProjectWorkflow.ods or exported workflow CSV")
        browse = QPushButton(self.style().standardIcon(QStyle.SP_DialogOpenButton), "")
        browse.setToolTip("Choose workflow source")
        browse.clicked.connect(self._choose_source)
        self._scope = QComboBox()
        self._scope.addItem("Project workflow", WorkflowScope.PROJECT)
        self._scope.addItem("Page workflow", WorkflowScope.PAGE)
        self._revision = QLineEdit()
        self._revision.setPlaceholderText("Source revision")
        import_button = QPushButton(self.style().standardIcon(QStyle.SP_DialogApplyButton), "Import")
        import_button.clicked.connect(self._import_source)
        import_controls.addWidget(QLabel("Source"))
        import_controls.addWidget(self._source, 1)
        import_controls.addWidget(browse)
        import_controls.addWidget(self._scope)
        import_controls.addWidget(self._revision)
        import_controls.addWidget(import_button)
        layout.addLayout(import_controls)

        snapshot_controls = QHBoxLayout()
        snapshot_controls.addWidget(QLabel("Snapshot"))
        self._snapshots = QComboBox()
        self._snapshots.currentIndexChanged.connect(self._populate_records)
        snapshot_controls.addWidget(self._snapshots, 1)
        refresh = QPushButton(self.style().standardIcon(QStyle.SP_BrowserReload), "")
        refresh.setToolTip("Refresh workflow governance records")
        refresh.clicked.connect(self.refresh)
        snapshot_controls.addWidget(refresh)
        layout.addLayout(snapshot_controls)

        self._records = QTableWidget(0, 9)
        self._records.setObjectName("workflowReconciliationTable")
        self._records.setHorizontalHeaderLabels([
            "Status", "WBS", "Sequence", "Description", "Milestone", "Method", "Module", "Source Row", "Workflow ID",
        ])
        self._records.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._records.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._records.setSelectionMode(QAbstractItemView.SingleSelection)
        self._records.verticalHeader().setVisible(False)
        self._records.setColumnWidth(0, 90)
        self._records.setColumnWidth(1, 90)
        self._records.setColumnWidth(2, 90)
        self._records.setColumnWidth(3, 300)
        self._records.setColumnWidth(4, 190)
        self._records.itemSelectionChanged.connect(self._update_actions)
        layout.addWidget(self._records, 1)

        mapping_fields = QHBoxLayout()
        self._mapping_name = QLineEdit()
        self._mapping_name.setReadOnly(True)
        self._mapping_sequence = QLineEdit()
        self._mapping_sequence.setReadOnly(True)
        mapping_fields.addWidget(QLabel("Milestone Name"))
        mapping_fields.addWidget(self._mapping_name, 1)
        mapping_fields.addWidget(QLabel("Sequence"))
        mapping_fields.addWidget(self._mapping_sequence)
        layout.addLayout(mapping_fields)

        actions = QHBoxLayout()
        self._approve = QPushButton(self.style().standardIcon(QStyle.SP_DialogApplyButton), "Approve")
        self._approve.clicked.connect(self._approve_selected)
        self._ignore = QPushButton(self.style().standardIcon(QStyle.SP_DialogCancelButton), "Ignore")
        self._ignore.clicked.connect(self._ignore_selected)
        self._task = QComboBox()
        for task in project.tasks:
            self._task.addItem(task.name, task.id)
        self._parent_wbs = QComboBox()
        for element in sorted(project.wbs_elements, key=lambda item: natural_code_key(item.code)):
            self._parent_wbs.addItem(f"{element.code}  {element.name}", element.id)
        self._next_wbs_code = QLabel()
        self._task.currentIndexChanged.connect(self._update_next_wbs_code)
        self._parent_wbs.currentIndexChanged.connect(self._update_next_wbs_code)
        self._role = QComboBox()
        for role in WorkflowMappingRole:
            self._role.addItem(role.value.replace("_", " ").title(), role)
        self._map = QPushButton("Map to activity")
        self._map.clicked.connect(self._map_selected)
        actions.addWidget(self._approve)
        actions.addWidget(self._ignore)
        actions.addStretch(1)
        actions.addWidget(QLabel("Activity"))
        actions.addWidget(self._task)
        actions.addWidget(QLabel("Parent WBS"))
        actions.addWidget(self._parent_wbs)
        actions.addWidget(self._next_wbs_code)
        actions.addWidget(self._role)
        actions.addWidget(self._map)
        layout.addLayout(actions)

        self._summary = QLabel()
        layout.addWidget(self._summary)
        self._update_next_wbs_code()
        self.refresh()

    def _update_next_wbs_code(self) -> None:
        parent_id = self._parent_wbs.currentData()
        task_id = self._task.currentData()
        if parent_id is None or task_id is None:
            self._next_wbs_code.setText("Next WBS: —")
            return
        try:
            code = PlanEditor(self._project).next_task_wbs_code(parent_id, task_id)
        except (ValueError, KeyError):
            self._next_wbs_code.setText("Next WBS: unavailable")
            return
        self._next_wbs_code.setText(f"Next WBS: {code}")

    def refresh(self, snapshot_id: str | None = None) -> None:
        selected_snapshot = snapshot_id or self._snapshots.currentData()
        try:
            self._state = self._callbacks.load()
        except (OSError, ValueError, KeyError) as error:
            QMessageBox.warning(self, "Workflow Governance", str(error))
            return
        self._snapshots.blockSignals(True)
        self._snapshots.clear()
        for snapshot in self._state.snapshots:
            label = (
                f"{snapshot.scope.value.title()} · {snapshot.source_revision} · "
                f"{snapshot.imported_at.date().isoformat()} · {snapshot.checksum[:10]}"
            )
            self._snapshots.addItem(label, snapshot.id)
        self._snapshots.blockSignals(False)
        index = self._snapshots.findData(selected_snapshot)
        self._snapshots.setCurrentIndex(index if index >= 0 else 0)
        self._populate_records()

    def _populate_records(self) -> None:
        snapshot_id = self._snapshots.currentData()
        records = [record for record in self._state.records if record.snapshot_id == snapshot_id]
        task_by_id = {task.id: task for task in self._project.tasks}
        codes_by_workflow: dict[str, list[str]] = defaultdict(list)
        for mapping in self._state.mappings:
            task = task_by_id.get(mapping.task_id)
            if task is not None and task.wbs_code and task.wbs_code not in codes_by_workflow[mapping.workflow_id]:
                codes_by_workflow[mapping.workflow_id].append(task.wbs_code)
        for codes in codes_by_workflow.values():
            codes.sort(key=natural_code_key)
        self._records.setRowCount(len(records))
        for row_number, record in enumerate(records):
            payload = record.payload
            values = (
                record.status.value,
                ", ".join(codes_by_workflow.get(record.workflow_id or "", ())),
                payload.get("sequence", ""),
                payload.get("description", ""),
                payload.get("milestone_name", ""),
                payload.get("method", ""),
                payload.get("module", "") or payload.get("source_module", ""),
                str(record.source_row),
                record.workflow_id or "",
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 0:
                    item.setData(Qt.UserRole, record.id)
                    item.setForeground(self._status_color(record.status))
                self._records.setItem(row_number, column, item)
        status_counts: dict[str, int] = defaultdict(int)
        for record in records:
            status_counts[record.status.value] += 1
        counts = ", ".join(f"{name}: {count}" for name, count in sorted(status_counts.items()))
        self._summary.setText(
            f"{len(records)} staged records{f' · {counts}' if counts else ''} · "
            f"{len(self._state.mappings)} approved task mappings · {len(self._state.audit_events)} audit events"
        )
        self._update_actions()

    def _selected_record(self) -> WorkflowImportRecord | None:
        row = self._records.currentRow()
        if row < 0:
            return None
        record_id = self._records.item(row, 0).data(Qt.UserRole)
        return next((record for record in self._state.records if record.id == record_id), None)

    def _update_actions(self) -> None:
        record = self._selected_record()
        payload = record.payload if record is not None else {}
        self._mapping_name.setText(payload.get("milestone_name", ""))
        self._mapping_sequence.setText(payload.get("sequence", ""))
        self._approve.setEnabled(
            record is not None
            and record.status not in {
                WorkflowReconciliationStatus.APPROVED,
                WorkflowReconciliationStatus.CONFLICT,
            }
        )
        self._ignore.setEnabled(
            record is not None
            and record.status not in {
                WorkflowReconciliationStatus.APPROVED,
                WorkflowReconciliationStatus.IGNORED,
            }
        )
        self._map.setEnabled(
            record is not None
            and record.status is WorkflowReconciliationStatus.APPROVED
            and record.workflow_id is not None
            and self._task.count() > 0
            and self._parent_wbs.count() > 0
        )

    def _choose_source(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose Workflow Source",
            self._source.text(),
            "Workflow sources (*.ods *.csv)",
        )
        if path:
            self._source.setText(path)

    def _import_source(self) -> None:
        source = self._source.text().strip()
        revision = self._revision.text().strip()
        if not source or not revision:
            QMessageBox.information(self, "Import Workflow", "Source and source revision are required.")
            return
        try:
            snapshot = self._callbacks.import_source(source, self._scope.currentData(), revision)
        except (OSError, RuntimeError, ValueError, KeyError) as error:
            QMessageBox.warning(self, "Import Workflow", str(error))
            return
        self.refresh(snapshot.id)

    def _approve_selected(self) -> None:
        record = self._selected_record()
        if record is None:
            return
        try:
            self._callbacks.approve(record.id)
        except (OSError, ValueError, KeyError) as error:
            QMessageBox.warning(self, "Approve Workflow", str(error))
            return
        self.refresh(record.snapshot_id)

    def _ignore_selected(self) -> None:
        record = self._selected_record()
        if record is None:
            return
        try:
            self._callbacks.set_status(record.id, WorkflowReconciliationStatus.IGNORED)
        except (OSError, ValueError, KeyError) as error:
            QMessageBox.warning(self, "Ignore Workflow", str(error))
            return
        self.refresh(record.snapshot_id)

    def _map_selected(self) -> None:
        record = self._selected_record()
        if record is None or record.workflow_id is None:
            return
        try:
            mapped = self._callbacks.map_task(
                record.workflow_id,
                self._task.currentData(),
                self._role.currentData(),
                self._parent_wbs.currentData(),
                self._project,
            )
        except (OSError, ValueError, KeyError) as error:
            QMessageBox.warning(self, "Map Workflow", str(error))
            return
        self._project = mapped.project
        task = next(task for task in mapped.project.tasks if task.id == mapped.mapping.task_id)
        QMessageBox.information(
            self,
            "Workflow Mapped",
            "Workflow Governance item mapped successfully.\n\n"
            f"Milestone: {record.payload.get('milestone_name', '')}\n"
            f"Activity: {task.name}\n"
            f"WBS: {task.wbs_code}\n"
            f"Role: {mapped.mapping.role.value.replace('_', ' ').title()}",
        )
        if self._project_changed is not None:
            self._project_changed(mapped.project, mapped.result)
            return
        self.refresh(record.snapshot_id)

    @staticmethod
    def _status_color(status: WorkflowReconciliationStatus) -> QColor:
        return {
            WorkflowReconciliationStatus.APPROVED: QColor("#15803d"),
            WorkflowReconciliationStatus.CHANGED: QColor("#b45309"),
            WorkflowReconciliationStatus.CONFLICT: QColor("#b91c1c"),
            WorkflowReconciliationStatus.IGNORED: QColor("#64748b"),
            WorkflowReconciliationStatus.MAPPED: QColor("#1d4ed8"),
            WorkflowReconciliationStatus.NEW: QColor("#111827"),
        }[status]


class ScheduleWorkspace(QMainWindow):
    """Split grid/Gantt desktop view for a calculated project snapshot."""

    def __init__(
        self,
        project: ProjectSnapshot,
        result: ScheduleResult,
        baseline: Baseline | None = None,
        save_callback: Callable[[ProjectSnapshot, ScheduleResult], None] | None = None,
        workflow_callbacks: WorkflowGovernanceCallbacks | None = None,
        save_as_callback: Callable[[Path, ProjectSnapshot, ScheduleResult], None] | None = None,
        save_path: str | Path | None = None,
    ) -> None:
        super().__init__()
        self._editor = PlanEditor(project)
        self._result = result
        self._baseline = baseline
        self._save_callback = save_callback
        self._save_as_callback = save_as_callback
        self._save_path = Path(save_path).expanduser() if save_path is not None else None
        self._saved_project = project
        self._workflow_callbacks = workflow_callbacks
        self._table: QTableWidget | None = None
        self._wbs_tree: QTreeWidget | None = None
        self._summary_clipboard: tuple[str, WBSElement] | None = None
        self._wbs_filters: dict[int, str] = {}
        self._wbs_sort_column = WBS_CODE_COLUMN
        self._wbs_sort_order = Qt.AscendingOrder
        self._schedule_sort_column = 0
        self._schedule_sort_order = Qt.AscendingOrder
        self._gantt_canvas: GanttCanvas | None = None
        self._selection_source = "schedule"
        self._help_dialog: SchedulerHelpDialog | None = None
        self.setWindowTitle(f"Biblion Scheduler — {project.name}")
        self.resize(1280, 720)
        toolbar = self.addToolBar("Plan")
        self._edit_action = QAction(self.style().standardIcon(QStyle.SP_FileDialogDetailedView), "Edit selected item", self)
        self._edit_action.setToolTip("Edit the selected summary or activity")
        self._edit_action.triggered.connect(self._edit_selected_task)
        toolbar.addAction(self._edit_action)
        self._save_action = QAction(self.style().standardIcon(QStyle.SP_DialogSaveButton), "&Save", self)
        self._save_action.setToolTip("Save the current project plan")
        self._save_action.setShortcut("Ctrl+S")
        self._save_action.setEnabled(save_callback is not None)
        self._save_action.triggered.connect(self._save)
        self._save_as_action = QAction("Save &As...", self)
        self._save_as_action.setToolTip("Save the current project plan to another database")
        self._save_as_action.setShortcut("Ctrl+Shift+S")
        self._save_as_action.setEnabled(save_as_callback is not None)
        self._save_as_action.triggered.connect(self._save_as)
        toolbar.addAction(self._save_action)
        help_action = QAction(self.style().standardIcon(QStyle.SP_DialogHelpButton), "Help", self)
        help_action.setToolTip("Open Biblion Scheduler help")
        help_action.setShortcut("F1")
        help_action.triggered.connect(lambda: self.show_help())
        toolbar.addAction(help_action)
        file_menu = self.menuBar().addMenu("&File")
        self._new_wbs_action = file_menu.addAction("&New WBS...")
        self._new_wbs_action.setShortcut("Ctrl+N")
        self._new_wbs_action.setEnabled(save_as_callback is not None)
        self._new_wbs_action.triggered.connect(self._new_wbs)
        file_menu.addSeparator()
        file_menu.addAction(self._save_action)
        file_menu.addAction(self._save_as_action)
        edit_menu = self.menuBar().addMenu("&Edit")
        self._undo_action = edit_menu.addAction("&Undo")
        self._undo_action.setShortcut("Ctrl+Z")
        self._undo_action.triggered.connect(self._undo)
        self._redo_action = edit_menu.addAction("&Redo")
        self._redo_action.setShortcut("Ctrl+Shift+Z")
        self._redo_action.triggered.connect(self._redo)
        edit_menu.addSeparator()
        edit_menu.addAction(self._edit_action)
        edit_menu.addSeparator()
        self._copy_summary_action = edit_menu.addAction("Copy WBS Element")
        self._copy_summary_action.triggered.connect(self._copy_selected_wbs_element)
        self._cut_summary_action = edit_menu.addAction("Cut WBS Element")
        self._cut_summary_action.triggered.connect(self._cut_selected_wbs_element)
        self._paste_summary_action = edit_menu.addAction("Paste WBS Element")
        self._paste_summary_action.triggered.connect(self._paste_wbs_element)
        edit_menu.addSeparator()
        self._delete_wbs_action = edit_menu.addAction("Delete WBS Element")
        self._delete_wbs_action.triggered.connect(self._delete_selected_wbs_element)
        edit_menu.aboutToShow.connect(self._update_edit_actions)
        wbs_menu = self.menuBar().addMenu("&WBS")
        add_wbs_action = wbs_menu.addAction("Add summary item")
        add_wbs_action.triggered.connect(lambda: self._add_wbs_element())
        wbs_menu.addAction("Insert summary above", lambda: self._add_wbs_element("above"))
        wbs_menu.addAction("Insert summary below", lambda: self._add_wbs_element("below"))
        self._add_activity_action = wbs_menu.addAction("Add activity item")
        self._add_activity_action.triggered.connect(self._add_activity)
        wbs_menu.addAction(self._edit_action)
        wbs_menu.addSeparator()
        wbs_menu.addAction(self._copy_summary_action)
        wbs_menu.addAction(self._cut_summary_action)
        wbs_menu.addAction(self._paste_summary_action)
        wbs_menu.addAction(self._delete_wbs_action)
        wbs_menu.aboutToShow.connect(self._update_edit_actions)
        help_menu = self.menuBar().addMenu("&Help")
        help_menu.addAction(help_action)
        help_menu.addSeparator()
        about_action = help_menu.addAction("About Biblion Scheduler")
        about_action.triggered.connect(self._show_about)
        self._render()

    def show_help(self, topic_id: str = "getting-started") -> None:
        if self._help_dialog is None:
            self._help_dialog = SchedulerHelpDialog(self, topic_id)
        else:
            self._help_dialog.show_topic(topic_id)
        self._help_dialog.show()
        self._help_dialog.raise_()
        self._help_dialog.activateWindow()

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "About Biblion Scheduler",
            "<h2>Biblion Scheduler</h2>"
            "<p>A standalone WBS and schedule-planning workspace for BiblionOCR development.</p>"
            "<p>Plans remain separate from BiblionOCR execution and project data.</p>",
        )

    def _render(self) -> None:
        project = self._editor.project
        result = self._editor.result
        root = QWidget()
        layout = QVBoxLayout(root)
        title = QLabel(f"{project.name}  •  Forecast finish: {result.project_finish.isoformat()}")
        title.setStyleSheet("font-weight: 600; padding: 6px 2px;")
        layout.addWidget(title)
        tabs = QTabWidget()
        schedule_page = QWidget()
        schedule_layout = QHBoxLayout(schedule_page)
        schedule_layout.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter(Qt.Horizontal)
        table = self._build_grid(project, result)
        table.doubleClicked.connect(self._edit_selected_task)
        table.itemSelectionChanged.connect(lambda: self._set_selection_source("schedule"))
        table.setContextMenuPolicy(Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(lambda position: self._show_schedule_context_menu(table, position))
        table.horizontalHeader().setSectionsClickable(True)
        table.horizontalHeader().setSortIndicatorShown(True)
        table.horizontalHeader().setSortIndicator(
            self._schedule_sort_column,
            self._schedule_sort_order,
        )
        table.horizontalHeader().sectionClicked.connect(self._sort_schedule)
        table.sortItems(self._schedule_sort_column, self._schedule_sort_order)
        self._table = table
        canvas = GanttCanvas(project, result, self._baseline, self._schedule_rows_from_table(table))
        self._gantt_canvas = canvas
        timeline = QScrollArea()
        timeline.setWidget(canvas)
        timeline.setWidgetResizable(False)
        timeline.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        splitter.addWidget(table)
        splitter.addWidget(timeline)
        splitter.setSizes([620, 660])
        table.verticalScrollBar().valueChanged.connect(timeline.verticalScrollBar().setValue)
        timeline.verticalScrollBar().valueChanged.connect(table.verticalScrollBar().setValue)
        schedule_layout.addWidget(splitter)
        tabs.addTab(schedule_page, "Schedule")
        tabs.addTab(self._build_wbs_page(project, result), "WBS Summary")
        if self._workflow_callbacks is not None:
            tabs.addTab(
                WorkflowGovernancePage(
                    project,
                    self._workflow_callbacks,
                    self,
                    self._adopt_governance_project,
                ),
                "Workflow Governance",
            )
        layout.addWidget(tabs)
        self.setCentralWidget(root)

    def _build_wbs_page(self, project: ProjectSnapshot, result: ScheduleResult) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        controls = QHBoxLayout()
        add_button = QPushButton(self.style().standardIcon(QStyle.SP_FileDialogNewFolder), "Add summary")
        add_button.setToolTip("Add a WBS summary item")
        add_button.clicked.connect(lambda: self._add_wbs_element())
        add_activity_button = QPushButton(self.style().standardIcon(QStyle.SP_FileIcon), "Add activity")
        add_activity_button.setToolTip("Add an activity to the selected WBS summary item")
        add_activity_button.clicked.connect(self._add_activity)
        edit_button = QPushButton(self.style().standardIcon(QStyle.SP_FileDialogDetailedView), "Edit summary")
        edit_button.setToolTip("Edit the selected WBS summary item")
        edit_button.clicked.connect(self._edit_selected_wbs_element)
        delete_button = QPushButton(self.style().standardIcon(QStyle.SP_TrashIcon), "Delete summary")
        delete_button.setToolTip("Delete the selected empty WBS summary item")
        delete_button.clicked.connect(self._delete_selected_wbs_element)
        controls.addWidget(add_button)
        controls.addWidget(add_activity_button)
        controls.addWidget(edit_button)
        controls.addWidget(delete_button)
        controls.addStretch(1)
        layout.addLayout(controls)
        tree = self._build_wbs_tree(project, result)
        tree.setObjectName("wbsSummaryTree")
        tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        tree.setSelectionBehavior(QAbstractItemView.SelectItems)
        tree.itemDoubleClicked.connect(lambda _item, _column: self._edit_selected_wbs_element())
        tree.itemSelectionChanged.connect(lambda: self._set_selection_source("wbs"))
        tree.setContextMenuPolicy(Qt.CustomContextMenu)
        tree.customContextMenuRequested.connect(lambda position: self._show_wbs_context_menu(tree, position))
        header = tree.header()
        header.setSectionsClickable(True)
        header.setSortIndicatorShown(True)
        header.setContextMenuPolicy(Qt.CustomContextMenu)
        header.customContextMenuRequested.connect(lambda position: self._show_wbs_header_menu(tree, position))
        header.sortIndicatorChanged.connect(self._remember_wbs_sort)
        tree.setSortingEnabled(True)
        tree.sortItems(self._wbs_sort_column, self._wbs_sort_order)
        self._apply_wbs_filters(tree)
        self._wbs_tree = tree
        layout.addWidget(tree)
        return page

    def _selected_wbs_element(self) -> WBSElement | None:
        if self._wbs_tree is None or self._wbs_tree.currentItem() is None:
            return None
        element_id = self._wbs_tree.currentItem().data(0, Qt.UserRole)
        return next((element for element in self._editor.project.wbs_elements if element.id == element_id), None)

    def _set_selection_source(self, source: str) -> None:
        self._selection_source = source

    def _selected_wbs_for_command(self) -> WBSElement | None:
        if self._selection_source == "schedule" and self._table is not None and self._table.currentRow() >= 0:
            identity = self._table.item(self._table.currentRow(), 0).data(Qt.UserRole)
            if identity[0] == "summary":
                return next(
                    (element for element in self._editor.project.wbs_elements if element.id == identity[1]),
                    None,
                )
            return None
        return self._selected_wbs_element()

    def _selected_task_for_command(self) -> Task | None:
        if self._selection_source != "schedule" or self._table is None or self._table.currentRow() < 0:
            return None
        identity = self._table.item(self._table.currentRow(), 0).data(Qt.UserRole)
        if identity[0] != "task":
            return None
        return next((task for task in self._editor.project.tasks if task.id == identity[1]), None)

    def _update_edit_actions(self) -> None:
        has_summary = self._selected_wbs_for_command() is not None
        self._undo_action.setEnabled(self._editor.can_undo)
        self._redo_action.setEnabled(self._editor.can_redo)
        self._copy_summary_action.setEnabled(has_summary)
        self._cut_summary_action.setEnabled(has_summary)
        self._paste_summary_action.setEnabled(self._summary_clipboard is not None)
        self._delete_wbs_action.setEnabled(has_summary)

    def _show_wbs_context_menu(self, tree: QTreeWidget, position: object) -> None:
        item = tree.itemAt(position)
        if item is not None:
            tree.setCurrentItem(item)
        tree.setFocus()
        self._update_edit_actions()
        menu = QMenu(self)
        add_menu = menu.addMenu("Add Item")
        add_menu.addAction("Summary Above", lambda: self._add_wbs_element("above"))
        add_menu.addAction("Summary Below", lambda: self._add_wbs_element("below"))
        add_menu.addAction("Child Summary Item", lambda: self._add_wbs_element())
        add_menu.addAction("Activity Item", self._add_activity)
        menu.addAction("Edit Item", self._edit_selected_wbs_element)
        menu.addSeparator()
        menu.addAction("Fill Down", lambda: self._fill_down_wbs_column(tree.columnAt(position.x())))
        menu.addSeparator()
        copy_action = menu.addAction("Copy Item", self._copy_selected_wbs_element)
        cut_action = menu.addAction("Cut Item", self._cut_selected_wbs_element)
        paste_action = menu.addAction("Paste Item", self._paste_wbs_element)
        copy_action.setEnabled(self._copy_summary_action.isEnabled())
        cut_action.setEnabled(self._cut_summary_action.isEnabled())
        paste_action.setEnabled(self._paste_summary_action.isEnabled())
        menu.addSeparator()
        menu.addAction(self._undo_action)
        menu.addAction(self._redo_action)
        menu.addSeparator()
        delete_action = menu.addAction("Delete Item", self._delete_selected_wbs_element)
        delete_action.setEnabled(self._delete_wbs_action.isEnabled())
        menu.addSeparator()
        menu.addAction(self._save_action)
        menu.addAction(self._save_as_action)
        menu.exec_(tree.viewport().mapToGlobal(position))

    def _show_wbs_header_menu(self, tree: QTreeWidget, position: object) -> None:
        column = tree.header().logicalIndexAt(position)
        if column < 0:
            return
        heading = tree.headerItem().text(column).replace(" •", "")
        menu = QMenu(self)
        menu.addAction(f"Sort {heading} ascending", lambda: tree.sortItems(column, Qt.AscendingOrder))
        menu.addAction(f"Sort {heading} descending", lambda: tree.sortItems(column, Qt.DescendingOrder))
        menu.addSeparator()
        menu.addAction(f"Filter {heading}...", lambda: self._set_wbs_filter(tree, column, heading))
        clear_column = menu.addAction(f"Clear {heading} filter", lambda: self._clear_wbs_filter(tree, column))
        clear_column.setEnabled(column in self._wbs_filters)
        clear_all = menu.addAction("Clear all filters", lambda: self._clear_all_wbs_filters(tree))
        clear_all.setEnabled(bool(self._wbs_filters))
        menu.exec_(tree.header().mapToGlobal(position))

    def _remember_wbs_sort(self, column: int, order: Qt.SortOrder) -> None:
        self._wbs_sort_column = column
        self._wbs_sort_order = order

    def _set_wbs_filter(self, tree: QTreeWidget, column: int, heading: str) -> None:
        value, accepted = QInputDialog.getText(
            self,
            f"Filter {heading}",
            "Contains:",
            text=self._wbs_filters.get(column, ""),
        )
        if not accepted:
            return
        text = value.strip()
        if text:
            self._wbs_filters[column] = text.casefold()
        else:
            self._wbs_filters.pop(column, None)
        self._apply_wbs_filters(tree)

    def _clear_wbs_filter(self, tree: QTreeWidget, column: int) -> None:
        self._wbs_filters.pop(column, None)
        self._apply_wbs_filters(tree)

    def _clear_all_wbs_filters(self, tree: QTreeWidget) -> None:
        self._wbs_filters.clear()
        self._apply_wbs_filters(tree)

    def _apply_wbs_filters(self, tree: QTreeWidget) -> None:
        headers = tree.headerItem()
        for column in range(tree.columnCount()):
            heading = headers.text(column).replace(" •", "")
            headers.setText(column, f"{heading} •" if column in self._wbs_filters else heading)

        def update_visibility(item: QTreeWidgetItem) -> bool:
            child_visible = any(update_visibility(item.child(index)) for index in range(item.childCount()))
            direct_match = all(
                text in item.text(column).casefold()
                for column, text in self._wbs_filters.items()
            )
            visible = direct_match or child_visible
            item.setHidden(not visible)
            if child_visible:
                item.setExpanded(True)
            return visible

        for index in range(tree.topLevelItemCount()):
            update_visibility(tree.topLevelItem(index))

    def _fill_down_wbs_column(self, column: int) -> None:
        tree = self._wbs_tree
        if tree is None or column not in WBS_FILLABLE_COLUMNS:
            QMessageBox.information(
                self,
                "Fill Down",
                "Fill Down supports Element, Planned Start, Planned Finish, and Units. "
                "WBS codes are unique and roll-up columns are calculated.",
            )
            return
        selected_item_ids = {id(item) for item in tree.selectedItems()}
        ordered_items: list[QTreeWidgetItem] = []
        iterator = QTreeWidgetItemIterator(tree)
        while iterator.value():
            if id(iterator.value()) in selected_item_ids and not iterator.value().isHidden():
                ordered_items.append(iterator.value())
            iterator += 1
        if len(ordered_items) < 2:
            QMessageBox.information(self, "Fill Down", "Select at least two cells in one WBS column.")
            return
        value = ordered_items[0].text(column)
        element_by_id = {element.id: element for element in self._editor.project.wbs_elements}
        try:
            replacements = tuple(
                self._wbs_element_with_value(element_by_id[item.data(0, Qt.UserRole)], item, column, value)
                for item in ordered_items[1:]
            )
            self._editor.replace_wbs_elements(replacements)
        except (ValueError, KeyError) as error:
            QMessageBox.warning(self, "Cannot Fill Down", str(error))
            return
        self._after_plan_edit(f"Filled {len(replacements)} WBS cells down.")

    @staticmethod
    def _wbs_element_with_value(
        element: WBSElement,
        item: QTreeWidgetItem,
        column: int,
        value: str,
    ) -> WBSElement:
        if column == WBS_NAME_COLUMN:
            return replace(element, name=value.strip())
        if column == WBS_PLANNED_START_COLUMN:
            planned_start = optional_date(value)
            planned_finish = element.planned_finish or optional_date(item.text(WBS_PLANNED_FINISH_COLUMN))
            return replace(element, planned_start=planned_start, planned_finish=planned_finish)
        if column == WBS_PLANNED_FINISH_COLUMN:
            planned_start = element.planned_start or optional_date(item.text(WBS_PLANNED_START_COLUMN))
            planned_finish = optional_date(value)
            return replace(element, planned_start=planned_start, planned_finish=planned_finish)
        if column == WBS_UNITS_COLUMN:
            return replace(element, duration_unit=DurationUnit(value))
        raise ValueError("The selected WBS column cannot be filled down.")

    def _show_schedule_context_menu(self, table: QTableWidget, position: object) -> None:
        item = table.itemAt(position)
        if item is not None:
            table.selectRow(item.row())
        table.setFocus()
        self._update_edit_actions()
        menu = QMenu(self)
        menu.addAction(self._edit_action)
        if self._selected_wbs_for_command() is not None:
            menu.addAction(self._add_activity_action)
            menu.addSeparator()
            menu.addAction(self._copy_summary_action)
            menu.addAction(self._cut_summary_action)
            menu.addAction(self._paste_summary_action)
            menu.addSeparator()
            menu.addAction(self._undo_action)
            menu.addAction(self._redo_action)
            menu.addSeparator()
            menu.addAction(self._delete_wbs_action)
        menu.exec_(table.viewport().mapToGlobal(position))

    def _sort_schedule(self, column: int) -> None:
        table = self._table
        if table is None:
            return
        order = (
            Qt.DescendingOrder
            if column == self._schedule_sort_column and self._schedule_sort_order == Qt.AscendingOrder
            else Qt.AscendingOrder
        )
        self._schedule_sort_column = column
        self._schedule_sort_order = order
        table.horizontalHeader().setSortIndicator(column, order)
        table.sortItems(column, order)
        if self._gantt_canvas is not None:
            self._gantt_canvas.set_rows(self._schedule_rows_from_table(table))

    @staticmethod
    def _schedule_rows_from_table(table: QTableWidget) -> tuple[TimelineRow, ...]:
        rows: list[TimelineRow] = []
        for row_number in range(table.rowCount()):
            item = table.item(row_number, 0)
            kind, identity = item.data(Qt.UserRole)
            depth = item.data(Qt.UserRole + 1)
            rows.append(TimelineRow(kind, identity, depth))
        return tuple(rows)

    def _cut_selected_wbs_element(self) -> None:
        element = self._selected_wbs_for_command()
        if element is None:
            QMessageBox.information(self, "Cut WBS Element", "Select a WBS summary item to cut.")
            return
        self._summary_clipboard = ("cut", element)
        self.statusBar().showMessage(f"Cut {element.code} {element.name}; select its new parent and paste.")

    def _copy_selected_wbs_element(self) -> None:
        element = self._selected_wbs_for_command()
        if element is None:
            QMessageBox.information(self, "Copy WBS Element", "Select a WBS summary item to copy.")
            return
        self._summary_clipboard = ("copy", element)
        self.statusBar().showMessage(f"Copied {element.code} {element.name}; select a parent and paste.")

    def _paste_wbs_element(self) -> None:
        if self._summary_clipboard is None:
            return
        target = self._selected_wbs_for_command()
        parent_id = target.id if target is not None else None
        operation, clipboard_element = self._summary_clipboard
        try:
            if operation == "cut":
                current = next(
                    element for element in self._editor.project.wbs_elements
                    if element.id == clipboard_element.id
                )
                self._editor.replace_wbs_element(replace(current, parent_id=parent_id))
                self._summary_clipboard = None
                message = "WBS element moved."
            else:
                self._editor.add_wbs_element(self._copied_wbs_element(clipboard_element, parent_id))
                message = "WBS element copied."
        except (ValueError, KeyError, StopIteration) as error:
            QMessageBox.warning(self, "Cannot Paste WBS Element", str(error))
            return
        self._after_plan_edit(message)

    def _undo(self) -> None:
        if not self._editor.can_undo:
            return
        self._editor.undo()
        self._after_plan_edit("Edit undone.")

    def _redo(self) -> None:
        if not self._editor.can_redo:
            return
        self._editor.redo()
        self._after_plan_edit("Edit redone.")

    def _copied_wbs_element(self, source: WBSElement, parent_id: str | None) -> WBSElement:
        element_ids = {element.id for element in self._editor.project.wbs_elements}
        copy_number = 1
        element_id = f"{source.id}-copy"
        while element_id in element_ids:
            copy_number += 1
            element_id = f"{source.id}-copy-{copy_number}"

        element_by_id = {element.id: element for element in self._editor.project.wbs_elements}
        code_prefix = element_by_id[parent_id].code if parent_id is not None else ""
        used_codes = {element.code for element in self._editor.project.wbs_elements}
        code_number = 1
        code = f"{code_prefix}.{code_number}" if code_prefix else str(code_number)
        while code in used_codes:
            code_number += 1
            code = f"{code_prefix}.{code_number}" if code_prefix else str(code_number)
        return replace(source, id=element_id, code=code, name=f"{source.name} Copy", parent_id=parent_id)

    def _add_wbs_element(self, placement: str | None = None) -> None:
        selected = self._selected_wbs_for_command()
        if placement is not None and selected is None:
            QMessageBox.information(
                self,
                "Insert Summary Item",
                "Select a WBS summary row before inserting above or below it.",
            )
            return
        initial_code = ""
        initial_parent_id = selected.id if selected is not None else None
        if placement is not None and selected is not None:
            initial_parent_id = selected.parent_id
            try:
                initial_code = self._sibling_insertion_code(selected.code, placement)
            except ValueError as error:
                QMessageBox.warning(self, "Cannot Insert Summary Item", str(error))
                return
        dialog = WBSElementDialog(
            self._editor.project,
            parent=self,
            initial_code=initial_code,
            initial_parent_id=initial_parent_id,
        )
        if dialog.exec_() != QDialog.Accepted:
            return
        try:
            element = dialog.wbs_element()
            if placement is None:
                self._editor.add_wbs_element(element)
            else:
                self._editor.insert_wbs_element(element)
        except (ValueError, KeyError) as error:
            QMessageBox.warning(self, "Invalid Summary Item", str(error))
            return
        self._after_plan_edit("Summary item added.")

    @staticmethod
    def _sibling_insertion_code(selected_code: str, placement: str) -> str:
        if placement not in {"above", "below"}:
            raise ValueError(f"Unknown WBS insertion placement: {placement}")
        prefix, separator, number = selected_code.rpartition(".")
        if not number.isdigit() or int(number) < 1:
            raise ValueError(f"WBS code is not a numeric outline code: {selected_code}")
        insertion_number = int(number) + (1 if placement == "below" else 0)
        return f"{prefix}{separator}{insertion_number}" if separator else str(insertion_number)

    def _add_activity(self) -> None:
        selected_wbs = self._selected_wbs_for_command()
        initial = Task("new-activity", "New activity", 1, selected_wbs.id if selected_wbs else None)
        dialog = TaskEditorDialog(initial, self._editor.project, self, creating=True)
        dialog._id.clear()
        dialog._name.clear()
        if dialog.exec_() != QDialog.Accepted:
            return
        try:
            task = dialog.edited_task()
            self._editor.add_task_with_relationships(task, dialog.edited_relationships())
        except (ValueError, KeyError) as error:
            QMessageBox.warning(self, "Invalid Activity", str(error))
            return
        self._after_plan_edit("Activity added.")

    def _edit_selected_wbs_element(self) -> None:
        element = self._selected_wbs_for_command()
        if element is None:
            QMessageBox.information(self, "Edit Summary Item", "Select a WBS summary item to edit.")
            return
        self._edit_wbs_element(element)

    def _edit_wbs_element(self, element: WBSElement) -> None:
        dialog = WBSElementDialog(self._editor.project, element, self)
        if dialog.exec_() != QDialog.Accepted:
            return
        try:
            self._editor.replace_wbs_element(dialog.wbs_element())
        except (ValueError, KeyError) as error:
            QMessageBox.warning(self, "Invalid Summary Item", str(error))
            return
        self._after_plan_edit("Summary item changed.")

    def _delete_selected_wbs_element(self) -> None:
        element = self._selected_wbs_for_command()
        if element is None:
            QMessageBox.information(self, "Delete Summary Item", "Select a WBS summary item to delete.")
            return
        answer = QMessageBox.question(
            self,
            "Delete Summary Item",
            f"Delete {element.code}  {element.name}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        try:
            self._editor.remove_wbs_element(element.id)
        except (ValueError, KeyError) as error:
            QMessageBox.warning(self, "Cannot Delete Summary Item", str(error))
            return
        self._after_plan_edit("Summary item deleted.")

    def _after_plan_edit(self, message: str) -> None:
        self._render()
        self._update_edit_actions()
        self.statusBar().showMessage(f"{message} Save to keep this revision.")

    def _adopt_governance_project(
        self,
        project: ProjectSnapshot,
        result: ScheduleResult,
    ) -> None:
        self._editor = PlanEditor(project)
        self._result = result
        self._saved_project = project
        self._render()
        self._update_edit_actions()
        self.statusBar().showMessage("Workflow mapped and activity WBS assignment saved.", 5000)

    def _edit_selected_task(self) -> None:
        if self._table is None or self._table.currentRow() < 0:
            QMessageBox.information(self, "Edit Schedule Item", "Select a summary or activity to edit.")
            return
        identity = self._table.item(self._table.currentRow(), 0).data(Qt.UserRole)
        if identity[0] == "summary":
            element = next(element for element in self._editor.project.wbs_elements if element.id == identity[1])
            self._edit_wbs_element(element)
            return
        task = next(task for task in self._editor.project.tasks if task.id == identity[1])
        dialog = TaskEditorDialog(task, self._editor.project, self)
        if dialog.exec_() != QDialog.Accepted:
            return
        try:
            self._editor.replace_task_with_relationships(dialog.edited_task(), dialog.edited_relationships())
        except (ValueError, KeyError) as error:
            QMessageBox.warning(self, "Invalid Activity", str(error))
            return
        self._after_plan_edit("Activity changed.")

    def _save(self) -> bool:
        if self._save_callback is None:
            return False
        try:
            self._save_callback(self._editor.project, self._editor.result)
        except (OSError, ValueError, KeyError) as error:
            QMessageBox.critical(self, "Save Failed", str(error))
            return False
        self._saved_project = self._editor.project
        self.statusBar().showMessage("Plan saved.", 5000)
        return True

    def _save_as(self) -> bool:
        if self._save_as_callback is None:
            return False
        initial_path = str(self._save_path or (Path.home() / "biblion-scheduler.sqlite"))
        selected_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Biblion Scheduler Project As",
            initial_path,
            "SQLite databases (*.sqlite *.db);;All files (*)",
        )
        if not selected_path:
            return False
        path = Path(selected_path).expanduser()
        if not path.suffix:
            path = path.with_suffix(".sqlite")
        try:
            self._save_as_callback(path, self._editor.project, self._editor.result)
        except (OSError, ValueError, KeyError) as error:
            QMessageBox.critical(self, "Save As Failed", str(error))
            return False
        self._save_path = path
        self._save_callback = lambda project, result: self._save_as_callback(path, project, result)
        self._saved_project = self._editor.project
        self._save_action.setEnabled(True)
        self.statusBar().showMessage(f"Plan saved as {path}.", 5000)
        return True

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 - Qt callback
        if self._editor.project == self._saved_project:
            event.accept()
            return
        buttons = QMessageBox.Discard | QMessageBox.Cancel
        if self._save_callback is not None or self._save_as_callback is not None:
            buttons |= QMessageBox.Save
        answer = QMessageBox.warning(
            self,
            "Unsaved WBS Changes",
            "The current WBS has unsaved changes. Save before closing?",
            buttons,
            QMessageBox.Save if buttons & QMessageBox.Save else QMessageBox.Cancel,
        )
        if answer == QMessageBox.Cancel:
            event.ignore()
            return
        if answer == QMessageBox.Save:
            saved = self._save() if self._save_callback is not None else self._save_as()
            if not saved:
                event.ignore()
                return
        event.accept()

    def _new_wbs(self) -> None:
        save_as_callback = self._save_as_callback
        if save_as_callback is None:
            return
        if self._editor.project != self._saved_project:
            buttons = QMessageBox.Discard | QMessageBox.Cancel
            if self._save_callback is not None:
                buttons |= QMessageBox.Save
            answer = QMessageBox.warning(
                self,
                "Unsaved WBS Changes",
                "Save changes to the current WBS before creating a new one?",
                buttons,
                QMessageBox.Save if self._save_callback is not None else QMessageBox.Cancel,
            )
            if answer == QMessageBox.Cancel:
                return
            if answer == QMessageBox.Save and not self._save():
                return
        dialog = NewWBSDialog(self)
        if dialog.exec_() != QDialog.Accepted:
            return
        try:
            project = dialog.project()
            result = PlanEditor(project).result
        except ValueError as error:
            QMessageBox.warning(self, "Cannot Create WBS", str(error))
            return
        initial_directory = self._save_path.parent if self._save_path is not None else Path.home()
        selected_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save New WBS",
            str(initial_directory / f"{project.id}.sqlite"),
            "SQLite databases (*.sqlite *.db);;All files (*)",
        )
        if not selected_path:
            return
        path = Path(selected_path).expanduser()
        if not path.suffix:
            path = path.with_suffix(".sqlite")
        try:
            save_as_callback(path, project, result)
        except (OSError, ValueError, KeyError) as error:
            QMessageBox.critical(self, "New WBS Failed", str(error))
            return
        self._editor = PlanEditor(project)
        self._result = self._editor.result
        self._baseline = None
        self._workflow_callbacks = None
        self._save_path = path
        self._save_callback = lambda revised, revised_result: save_as_callback(
            path, revised, revised_result
        )
        self._saved_project = project
        self._summary_clipboard = None
        self._wbs_filters.clear()
        self._wbs_sort_column = WBS_CODE_COLUMN
        self._wbs_sort_order = Qt.AscendingOrder
        self._selection_source = "schedule"
        self.setWindowTitle(f"Biblion Scheduler — {project.name}")
        self._render()
        self._update_edit_actions()
        self.statusBar().showMessage(f"New WBS created at {path}.", 5000)

    @staticmethod
    def _build_wbs_tree(project: ProjectSnapshot, result: ScheduleResult) -> QTreeWidget:
        tree = QTreeWidget()
        tree.setHeaderLabels([
            "WBS", "Element", "Level", "Sequence", "Predecessor", "Successor", "Logic", "Progress", "Pages",
            "Planned Start", "Planned Finish", "Planned Duration", "Actual Start", "Actual Finish",
            "Actual Duration", "Units", "Activities", "Milestones", "Status",
        ])
        tree.setAlternatingRowColors(True)
        items: dict[str, QTreeWidgetItem] = {}
        depth_by_id = {
            row.id: row.depth for row in timeline_rows(project) if row.kind == "summary"
        }
        for element in project.wbs_elements:
            summary = result.wbs_summaries[element.id]
            depth = depth_by_id[element.id]
            relationships = relationship_fields(project, TimelineRow("summary", element.id, depth))
            item = WBSTreeWidgetItem([
                element.code,
                element.name,
                "Level 1 - Project/Phase" if depth == 0 else "Level 2 - Summary/Work Package",
                wbs_sequences(project, element.id),
                relationships.predecessors,
                relationships.successors,
                relationships.logic,
                f"{summary.progress_percent:.1f}%",
                f"{summary.page_percent_complete:.1f}%",
                summary.start.isoformat() if summary.start else "",
                summary.finish.isoformat() if summary.finish else "",
                str(summary.planned_duration_days) if summary.planned_duration_days is not None else "",
                date_text(summary.actual_start),
                date_text(summary.actual_finish),
                str(summary.actual_duration_days) if summary.actual_duration_days is not None else "",
                element.duration_unit.value,
                str(summary.activity_count),
                str(summary.milestone_count),
                f"{summary.status.value}{' / Critical' if summary.has_critical_work else ''}",
            ])
            if summary.has_critical_work:
                for column in range(tree.columnCount()):
                    item.setForeground(column, QColor("#b91c1c"))
            items[element.id] = item
            item.setData(0, Qt.UserRole, element.id)

        for element in project.wbs_elements:
            item = items[element.id]
            if element.parent_id:
                items[element.parent_id].addChild(item)
            else:
                tree.addTopLevelItem(item)
        tree.setColumnWidth(0, 90)
        tree.setColumnWidth(1, 280)
        tree.expandAll()
        return tree

    @staticmethod
    def _build_grid(project: ProjectSnapshot, result: ScheduleResult) -> QTableWidget:
        rows = timeline_rows(project)
        table = QTableWidget(len(rows), 19)
        table.setHorizontalHeaderLabels([
            "WBS", "Activity", "Type", "Sequence", "Predecessor", "Successor", "Logic", "Duration", "Units",
            "Progress", "Pages", "Planned Start", "Planned Finish", "Planned Duration",
            "Actual Start", "Actual Finish", "Actual Duration", "Float", "Status",
        ])
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.verticalHeader().setVisible(False)
        table.setColumnWidth(0, 65)
        table.setColumnWidth(1, 205)
        element_by_id = {element.id: element for element in project.wbs_elements}
        task_by_id = {task.id: task for task in project.tasks}
        wbs_code_by_id = {element.id: element.code for element in project.wbs_elements}
        for row_number, timeline_row in enumerate(rows):
            relationships = relationship_fields(project, timeline_row)
            if timeline_row.kind == "summary":
                element = element_by_id[timeline_row.id]
                summary = result.wbs_summaries[element.id]
                values = (
                    element.code,
                    f"{'    ' * timeline_row.depth}{element.name}",
                    "Level 1 - Project/Phase" if timeline_row.level == 1 else "Level 2 - Summary/Work Package",
                    "",
                    relationships.predecessors,
                    relationships.successors,
                    relationships.logic,
                    str(summary.planned_duration_days) if summary.planned_duration_days is not None else "",
                    element.duration_unit.value,
                    f"{summary.progress_percent:.1f}%",
                    f"{summary.page_percent_complete:.1f}%",
                    summary.start.isoformat() if summary.start else "",
                    summary.finish.isoformat() if summary.finish else "",
                    str(summary.planned_duration_days) if summary.planned_duration_days is not None else "",
                    date_text(summary.actual_start),
                    date_text(summary.actual_finish),
                    str(summary.actual_duration_days) if summary.actual_duration_days is not None else "",
                    "",
                    f"{summary.status.value}{' / Critical' if summary.has_critical_work else ''}",
                )
                identity = ("summary", element.id)
                is_critical = summary.has_critical_work
                is_summary = True
            else:
                task = task_by_id[timeline_row.id]
                item = result.tasks[task.id]
                values = (
                    task.wbs_code or wbs_code_by_id.get(task.wbs_id, ""),
                    f"{'    ' * timeline_row.depth}{task.name}",
                    "Level 3 - Milestone" if task.scheduled_duration_days == 0 else "Level 3 - Activity",
                    task.sequence,
                    relationships.predecessors,
                    relationships.successors,
                    relationships.logic,
                    str(task.duration_days),
                    task.duration_unit.value,
                    f"{task.progress_percent}%",
                    f"{task.page_percent_complete}%",
                    date_text(task.planned_start or item.start),
                    date_text(task.planned_finish or item.finish),
                    str(task.duration_days),
                    date_text(task.actual_start),
                    date_text(task.actual_finish),
                    (
                        str(
                            (ScheduleEngine._inclusive_working_duration(task.actual_start, task.actual_finish, project.calendar) or 0)
                            * (8 if task.duration_unit is DurationUnit.HOURS else 1)
                        )
                        if task.actual_start is not None and task.actual_finish is not None else ""
                    ),
                    str(item.total_float_days),
                    f"{task.status.value}{' / Critical' if item.is_critical else ''}",
                )
                identity = ("task", task.id)
                is_critical = item.is_critical
                is_summary = False
            for column, value in enumerate(values):
                if column == 0:
                    sort_key: object = row_number
                elif column in SCHEDULE_NUMERIC_COLUMNS:
                    sort_key = (WBSTreeWidgetItem._number(value), row_number)
                else:
                    sort_key = (value.strip().casefold(), row_number)
                cell = ScheduleTableWidgetItem(value, sort_key)
                if is_summary:
                    font = cell.font()
                    font.setBold(True)
                    cell.setFont(font)
                    cell.setBackground(QColor("#f3f4f6"))
                if is_critical:
                    cell.setForeground(QColor("#b91c1c"))
                if column == 0:
                    cell.setData(Qt.UserRole, identity)
                    cell.setData(Qt.UserRole + 1, timeline_row.depth)
                table.setItem(row_number, column, cell)
            table.setRowHeight(row_number, ROW_HEIGHT)
        return table


def launch_workspace(
    project: ProjectSnapshot,
    result: ScheduleResult,
    baseline: Baseline | None = None,
    save_callback: Callable[[ProjectSnapshot, ScheduleResult], None] | None = None,
    workflow_callbacks: WorkflowGovernanceCallbacks | None = None,
    save_as_callback: Callable[[Path, ProjectSnapshot, ScheduleResult], None] | None = None,
    save_path: str | Path | None = None,
) -> int:
    """Show a workspace for caller-supplied schedule data."""
    application = QApplication.instance() or QApplication([])
    application.setApplicationName("Biblion Scheduler")
    application.setDesktopFileName("biblion-scheduler")
    window = ScheduleWorkspace(
        project,
        result,
        baseline,
        save_callback,
        workflow_callbacks,
        save_as_callback,
        save_path,
    )
    window.show()
    return application.exec_()
