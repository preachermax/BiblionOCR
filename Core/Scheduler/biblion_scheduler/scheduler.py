"""Dependency-driven, calendar-aware scheduling engine."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from dataclasses import replace
from typing import Iterable

from .calendar import WorkingCalendar
from .models import (
    Constraint,
    ConstraintType,
    ConstraintViolation,
    Dependency,
    DependencyType,
    DurationUnit,
    ProgressStatus,
    ScheduleResult,
    ScheduledTask,
    Task,
    WBSElement,
    WBSSummary,
)


class ScheduleValidationError(ValueError):
    """Raised when project logic cannot produce a valid schedule."""


class ScheduleEngine:
    """Calculate early/late dates, float, and constraint diagnostics.

    Durations and lags are measured in working days. A zero-lag FS relationship
    hands work off on the next working day; zero-lag SS, FF, and SF relationships
    share their respective predecessor boundary.
    """

    def calculate(
        self,
        *,
        project_start: date,
        tasks: Iterable[Task],
        dependencies: Iterable[Dependency] = (),
        constraints: Iterable[Constraint] = (),
        wbs_elements: Iterable[WBSElement] = (),
        calendar: WorkingCalendar | None = None,
        required_finish: date | None = None,
    ) -> ScheduleResult:
        calendar = calendar or WorkingCalendar()
        task_list = [self._task_with_planned_duration(task, calendar) for task in tasks]
        task_by_id = {task.id: task for task in task_list}
        if len(task_by_id) != len(task_list):
            raise ScheduleValidationError("Task identifiers must be unique.")

        constraints_by_task = self._validate_constraints(constraints, task_by_id)
        predecessors, successors, indegree = self._build_graph(list(dependencies), task_by_id)
        ordered_ids = self._topological_order(indegree, successors)
        normalized_project_start = calendar.next_working_day(project_start)
        if not task_by_id:
            wbs_summaries = self._wbs_summaries(tuple(wbs_elements), {}, calendar)
            return ScheduleResult(
                {},
                normalized_project_start,
                normalized_project_start,
                required_finish,
                (),
                wbs_summaries,
            )

        early: dict[str, tuple[date, date]] = {}
        for task_id in ordered_ids:
            task = task_by_id[task_id]
            earliest_start = normalized_project_start
            for dependency in predecessors[task_id]:
                earliest_start = max(
                    earliest_start,
                    self._early_start_bound(dependency, early[dependency.predecessor_id], task, calendar),
                )
            earliest_start = max(
                earliest_start,
                self._earliest_constraint_bound(task, constraints_by_task[task_id], calendar),
            )
            if task.planned_start is not None:
                earliest_start = max(earliest_start, task.planned_start)
            start = calendar.next_working_day(earliest_start)
            early[task_id] = (start, calendar.finish_for_duration(start, task.scheduled_duration_days))

        project_finish = max(finish for _, finish in early.values())
        backward_finish = calendar.previous_working_day(required_finish) if required_finish else project_finish
        late_start: dict[str, date] = {
            task_id: calendar.start_for_finish(backward_finish, task.scheduled_duration_days)
            for task_id, task in task_by_id.items()
        }
        for task_id in reversed(ordered_ids):
            task = task_by_id[task_id]
            candidate = late_start[task_id]
            for dependency in successors[task_id]:
                candidate = min(
                    candidate,
                    self._late_start_bound(
                        dependency,
                        late_start[dependency.successor_id],
                        task_by_id[dependency.successor_id],
                        task,
                        calendar,
                    ),
                )
            candidate = min(candidate, self._latest_constraint_bound(task, constraints_by_task[task_id], calendar))
            late_start[task_id] = candidate

        scheduled = {
            task_id: self._scheduled_task(task, early[task_id], late_start[task_id], calendar)
            for task_id, task in task_by_id.items()
        }
        violations = self._constraint_violations(scheduled, constraints_by_task)
        wbs_summaries = self._wbs_summaries(tuple(wbs_elements), scheduled, calendar)
        return ScheduleResult(
            scheduled,
            normalized_project_start,
            project_finish,
            required_finish,
            tuple(violations),
            wbs_summaries,
        )

    @staticmethod
    def _wbs_summaries(
        elements: tuple[WBSElement, ...],
        scheduled: dict[str, ScheduledTask],
        calendar: WorkingCalendar,
    ) -> dict[str, WBSSummary]:
        element_by_id = {element.id: element for element in elements}
        if len(element_by_id) != len(elements):
            raise ScheduleValidationError("WBS element identifiers must be unique.")
        if any(element.parent_id not in element_by_id for element in elements if element.parent_id):
            raise ScheduleValidationError("Every WBS parent must reference an existing element.")
        assigned: dict[str, list[ScheduledTask]] = defaultdict(list)
        for item in scheduled.values():
            if item.task.wbs_id is None:
                continue
            if item.task.wbs_id not in element_by_id:
                raise ScheduleValidationError("Every task WBS assignment must reference an existing element.")
            element_id: str | None = item.task.wbs_id
            visited: set[str] = set()
            while element_id is not None:
                if element_id in visited:
                    raise ScheduleValidationError("WBS elements contain a cycle.")
                visited.add(element_id)
                assigned[element_id].append(item)
                element_id = element_by_id[element_id].parent_id

        summaries: dict[str, WBSSummary] = {}
        for element in elements:
            items = assigned[element.id]
            total_weight = sum(max(item.task.scheduled_duration_days, 1) for item in items)
            progress_percent = (
                sum(
                    (100 if item.task.actual_finish is not None else item.task.progress_percent)
                    * max(item.task.scheduled_duration_days, 1)
                    for item in items
                ) / total_weight
                if total_weight else 0.0
            )
            statuses = [item.task.status for item in items]
            rolled_start = min((item.start for item in items), default=None)
            rolled_finish = max((item.finish for item in items), default=None)
            planned_start = element.planned_start or rolled_start
            planned_finish = element.planned_finish or rolled_finish
            actual_starts = [item.task.actual_start for item in items if item.task.actual_start is not None]
            actual_finishes = [item.task.actual_finish for item in items if item.task.actual_finish is not None]
            actual_start = min(actual_starts, default=None)
            actual_finish = max(actual_finishes, default=None) if len(actual_finishes) == len(items) and items else None
            duration_multiplier = 8 if element.duration_unit is DurationUnit.HOURS else 1
            planned_duration = ScheduleEngine._inclusive_working_duration(planned_start, planned_finish, calendar)
            actual_duration = ScheduleEngine._inclusive_working_duration(actual_start, actual_finish, calendar)
            summaries[element.id] = WBSSummary(
                element=element,
                start=planned_start,
                finish=planned_finish,
                activity_count=sum(item.task.scheduled_duration_days > 0 for item in items),
                milestone_count=sum(item.task.scheduled_duration_days == 0 for item in items),
                has_critical_work=any(item.is_critical for item in items),
                progress_percent=progress_percent,
                page_percent_complete=(
                    sum(item.task.page_percent_complete * max(item.task.scheduled_duration_days, 1) for item in items) / total_weight
                    if total_weight else 0.0
                ),
                status=(
                    ProgressStatus.COMPLETE
                    if statuses and all(status is ProgressStatus.COMPLETE for status in statuses)
                    else ProgressStatus.IN_PROGRESS
                    if any(status is not ProgressStatus.NOT_STARTED for status in statuses)
                    else ProgressStatus.NOT_STARTED
                ),
                planned_duration_days=planned_duration * duration_multiplier if planned_duration is not None else None,
                actual_start=actual_start,
                actual_finish=actual_finish,
                actual_duration_days=actual_duration * duration_multiplier if actual_duration is not None else None,
            )
        return summaries

    @staticmethod
    def _inclusive_working_duration(
        start: date | None,
        finish: date | None,
        calendar: WorkingCalendar,
    ) -> int | None:
        if start is None or finish is None:
            return None
        return calendar.working_day_difference(start, finish) + 1

    @classmethod
    def _task_with_planned_duration(cls, task: Task, calendar: WorkingCalendar) -> Task:
        progress_percent = 100 if task.actual_finish is not None else task.progress_percent
        if task.planned_start is None or task.planned_finish is None:
            return replace(task, progress_percent=progress_percent) if progress_percent != task.progress_percent else task
        duration_days = 0 if task.scheduled_duration_days == 0 and task.planned_start == task.planned_finish else cls._inclusive_working_duration(
            task.planned_start,
            task.planned_finish,
            calendar,
        )
        duration = (duration_days or 0) * 8 if task.duration_unit is DurationUnit.HOURS else duration_days or 0
        return replace(task, duration_days=duration, progress_percent=progress_percent)

    @staticmethod
    def _scheduled_task(task: Task, early_dates: tuple[date, date], late_start: date, calendar: WorkingCalendar) -> ScheduledTask:
        start, finish = early_dates
        total_float = calendar.working_day_difference(start, late_start)
        return ScheduledTask(
            task=task,
            start=start,
            finish=finish,
            late_start=late_start,
            late_finish=calendar.finish_for_duration(late_start, task.scheduled_duration_days),
            total_float_days=total_float,
            is_critical=total_float <= 0,
        )

    @staticmethod
    def _build_graph(dependencies: list[Dependency], task_by_id: dict[str, Task]):
        predecessors: dict[str, list[Dependency]] = defaultdict(list)
        successors: dict[str, list[Dependency]] = defaultdict(list)
        indegree = {task_id: 0 for task_id in task_by_id}
        seen: set[tuple[str, str, DependencyType, int]] = set()
        for dependency in dependencies:
            if dependency.predecessor_id not in task_by_id or dependency.successor_id not in task_by_id:
                raise ScheduleValidationError("Every dependency must reference existing tasks.")
            key = (dependency.predecessor_id, dependency.successor_id, dependency.dependency_type, dependency.lag_days)
            if key in seen:
                raise ScheduleValidationError("Duplicate dependencies are not allowed.")
            seen.add(key)
            predecessors[dependency.successor_id].append(dependency)
            successors[dependency.predecessor_id].append(dependency)
            indegree[dependency.successor_id] += 1
        return predecessors, successors, indegree

    @staticmethod
    def _validate_constraints(constraints: Iterable[Constraint], task_by_id: dict[str, Task]) -> dict[str, list[Constraint]]:
        result: dict[str, list[Constraint]] = defaultdict(list)
        for constraint in constraints:
            if constraint.task_id not in task_by_id:
                raise ScheduleValidationError("Every constraint must reference an existing task.")
            result[constraint.task_id].append(constraint)
        return result

    @staticmethod
    def _early_start_bound(dependency: Dependency, predecessor: tuple[date, date], successor: Task, calendar: WorkingCalendar) -> date:
        predecessor_start, predecessor_finish = predecessor
        if dependency.dependency_type is DependencyType.FINISH_TO_START:
            # A zero-lag FS handoff is one working-day step after the
            # predecessor finish. Negative lag can therefore overlap work.
            return calendar.add_working_days(predecessor_finish, 1 + dependency.lag_days)
        if dependency.dependency_type is DependencyType.START_TO_START:
            return calendar.add_working_days(predecessor_start, dependency.lag_days)
        if dependency.dependency_type is DependencyType.FINISH_TO_FINISH:
            target_finish = calendar.add_working_days(predecessor_finish, dependency.lag_days)
        else:  # Start-to-Finish
            target_finish = calendar.add_working_days(predecessor_start, dependency.lag_days)
        return calendar.start_for_finish(target_finish, successor.scheduled_duration_days)

    @staticmethod
    def _late_start_bound(
        dependency: Dependency,
        successor_late_start: date,
        successor: Task,
        predecessor: Task,
        calendar: WorkingCalendar,
    ) -> date:
        successor_late_finish = calendar.finish_for_duration(successor_late_start, successor.scheduled_duration_days)
        if dependency.dependency_type is DependencyType.FINISH_TO_START:
            latest_finish = calendar.add_working_days(successor_late_start, -1 - dependency.lag_days)
            return calendar.start_for_finish(latest_finish, predecessor.scheduled_duration_days)
        if dependency.dependency_type is DependencyType.START_TO_START:
            return calendar.add_working_days(successor_late_start, -dependency.lag_days)
        if dependency.dependency_type is DependencyType.FINISH_TO_FINISH:
            latest_finish = calendar.add_working_days(successor_late_finish, -dependency.lag_days)
            return calendar.start_for_finish(latest_finish, predecessor.scheduled_duration_days)
        return calendar.add_working_days(successor_late_finish, -dependency.lag_days)

    @staticmethod
    def _earliest_constraint_bound(task: Task, constraints: list[Constraint], calendar: WorkingCalendar) -> date:
        bound = date.min
        for constraint in constraints:
            constraint_date = constraint.constraint_date
            if constraint.constraint_type in (ConstraintType.START_NO_EARLIER_THAN, ConstraintType.MUST_START_ON):
                bound = max(bound, constraint_date)  # type: ignore[arg-type]
            elif constraint.constraint_type in (ConstraintType.FINISH_NO_EARLIER_THAN, ConstraintType.MUST_FINISH_ON):
                bound = max(bound, calendar.start_for_finish(constraint_date, task.scheduled_duration_days))  # type: ignore[arg-type]
        return bound

    @staticmethod
    def _latest_constraint_bound(task: Task, constraints: list[Constraint], calendar: WorkingCalendar) -> date:
        bound = date.max
        for constraint in constraints:
            constraint_date = constraint.constraint_date
            if constraint.constraint_type in (ConstraintType.START_NO_LATER_THAN, ConstraintType.MUST_START_ON):
                bound = min(bound, constraint_date)  # type: ignore[arg-type]
            elif constraint.constraint_type in (ConstraintType.FINISH_NO_LATER_THAN, ConstraintType.MUST_FINISH_ON):
                bound = min(bound, calendar.start_for_finish(constraint_date, task.scheduled_duration_days))  # type: ignore[arg-type]
        return bound

    @staticmethod
    def _constraint_violations(scheduled: dict[str, ScheduledTask], constraints_by_task: dict[str, list[Constraint]]) -> list[ConstraintViolation]:
        violations: list[ConstraintViolation] = []
        start_constraints = {
            ConstraintType.START_NO_EARLIER_THAN,
            ConstraintType.START_NO_LATER_THAN,
            ConstraintType.MUST_START_ON,
        }
        for task_id, constraints in constraints_by_task.items():
            item = scheduled[task_id]
            for constraint in constraints:
                constraint_date = constraint.constraint_date
                if constraint_date is None:
                    continue
                actual = item.start if constraint.constraint_type in start_constraints else item.finish
                invalid = (
                    constraint.constraint_type is ConstraintType.START_NO_LATER_THAN and actual > constraint_date
                    or constraint.constraint_type is ConstraintType.FINISH_NO_LATER_THAN and actual > constraint_date
                    or constraint.constraint_type is ConstraintType.MUST_START_ON and actual != constraint_date
                    or constraint.constraint_type is ConstraintType.MUST_FINISH_ON and actual != constraint_date
                )
                if invalid:
                    violations.append(
                        ConstraintViolation(
                            task_id,
                            constraint,
                            f"{constraint.constraint_type.value} is violated: calculated {actual.isoformat()}, required {constraint_date.isoformat()}.",
                        )
                    )
        return violations

    @staticmethod
    def _topological_order(indegree: dict[str, int], successors: dict[str, list[Dependency]]) -> list[str]:
        ready = sorted(task_id for task_id, count in indegree.items() if count == 0)
        ordered: list[str] = []
        while ready:
            task_id = ready.pop(0)
            ordered.append(task_id)
            for dependency in sorted(successors[task_id], key=lambda edge: edge.successor_id):
                indegree[dependency.successor_id] -= 1
                if indegree[dependency.successor_id] == 0:
                    ready.append(dependency.successor_id)
                    ready.sort()
        if len(ordered) != len(indegree):
            raise ScheduleValidationError("Dependencies contain a cycle.")
        return ordered
