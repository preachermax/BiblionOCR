"""Validated editing operations for an in-memory project plan."""

from __future__ import annotations

from dataclasses import replace
import re

from .models import Constraint, Dependency, ProjectSnapshot, ScheduleResult, Task, WBSElement
from .scheduler import ScheduleEngine


class PlanEditor:
    """Apply atomic project edits and reject changes that cannot be scheduled."""

    def __init__(self, project: ProjectSnapshot, engine: ScheduleEngine | None = None) -> None:
        self._engine = engine or ScheduleEngine()
        self._result = self._calculate(project)
        self._project = self._normalized_project(project, self._result)
        self._undo_stack: list[ProjectSnapshot] = []
        self._redo_stack: list[ProjectSnapshot] = []

    @property
    def project(self) -> ProjectSnapshot:
        return self._project

    @property
    def result(self) -> ScheduleResult:
        return self._result

    @property
    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo_stack)

    def undo(self) -> None:
        if not self._undo_stack:
            raise ValueError("There is no edit to undo.")
        previous = self._undo_stack.pop()
        self._redo_stack.append(self._project)
        self._project = previous
        self._result = self._calculate(previous)

    def redo(self) -> None:
        if not self._redo_stack:
            raise ValueError("There is no edit to redo.")
        candidate = self._redo_stack.pop()
        self._undo_stack.append(self._project)
        self._project = candidate
        self._result = self._calculate(candidate)

    def add_wbs_element(self, element: WBSElement) -> None:
        if any(existing.id == element.id for existing in self._project.wbs_elements):
            raise ValueError(f"WBS element already exists: {element.id}")
        self._accept(replace(self._project, wbs_elements=(*self._project.wbs_elements, element)))

    def insert_wbs_element(self, element: WBSElement) -> None:
        """Insert at an outline number, shifting occupied siblings and descendants."""
        if any(existing.id == element.id for existing in self._project.wbs_elements):
            raise ValueError(f"WBS element already exists: {element.id}")
        parent = next(
            (existing for existing in self._project.wbs_elements if existing.id == element.parent_id),
            None,
        )
        if element.parent_id is not None and parent is None:
            raise ValueError("The WBS insertion parent does not exist.")
        prefix = f"{parent.code}." if parent is not None else ""
        match = re.fullmatch(rf"{re.escape(prefix)}([1-9][0-9]*)", element.code)
        if match is None:
            expected = f"{prefix}<number>" if prefix else "<number>"
            raise ValueError(f"Inserted WBS code must be {expected}.")
        insertion_number = int(match.group(1))
        siblings = [
            existing for existing in self._project.wbs_elements
            if existing.parent_id == element.parent_id
        ]
        sibling_numbers: dict[str, int] = {}
        for sibling in siblings:
            sibling_match = re.fullmatch(rf"{re.escape(prefix)}([1-9][0-9]*)", sibling.code)
            if sibling_match is None:
                raise ValueError(f"Sibling WBS code is not a numeric outline code: {sibling.code}")
            sibling_numbers[sibling.id] = int(sibling_match.group(1))

        shifted_prefixes = {
            sibling.code: f"{prefix}{sibling_numbers[sibling.id] + 1}"
            for sibling in siblings
            if sibling_numbers[sibling.id] >= insertion_number
        }

        def shifted_code(code: str) -> str:
            for old_prefix, new_prefix in sorted(
                shifted_prefixes.items(), key=lambda pair: len(pair[0]), reverse=True
            ):
                if code == old_prefix or code.startswith(f"{old_prefix}."):
                    return f"{new_prefix}{code[len(old_prefix):]}"
            return code

        shifted_elements = tuple(
            replace(existing, code=shifted_code(existing.code))
            for existing in self._project.wbs_elements
        )
        shifted_tasks = tuple(
            replace(task, wbs_code=shifted_code(task.wbs_code))
            if task.wbs_code else task
            for task in self._project.tasks
        )
        insertion_index = next(
            (
                index for index, existing in enumerate(self._project.wbs_elements)
                if existing.parent_id == element.parent_id
                and sibling_numbers[existing.id] >= insertion_number
            ),
            len(shifted_elements),
        )
        elements = (*shifted_elements[:insertion_index], element, *shifted_elements[insertion_index:])
        self._accept(replace(self._project, wbs_elements=elements, tasks=shifted_tasks))

    def replace_wbs_element(self, element: WBSElement) -> None:
        if not any(existing.id == element.id for existing in self._project.wbs_elements):
            raise KeyError(f"Unknown WBS element: {element.id}")
        elements = tuple(element if existing.id == element.id else existing for existing in self._project.wbs_elements)
        self._accept(replace(self._project, wbs_elements=elements))

    def replace_wbs_elements(self, replacements: tuple[WBSElement, ...]) -> None:
        replacement_by_id = {element.id: element for element in replacements}
        if len(replacement_by_id) != len(replacements):
            raise ValueError("WBS replacement identifiers must be unique.")
        existing_ids = {element.id for element in self._project.wbs_elements}
        unknown_ids = replacement_by_id.keys() - existing_ids
        if unknown_ids:
            raise KeyError(f"Unknown WBS element: {sorted(unknown_ids)[0]}")
        elements = tuple(replacement_by_id.get(element.id, element) for element in self._project.wbs_elements)
        self._accept(replace(self._project, wbs_elements=elements))

    def remove_wbs_element(self, element_id: str) -> None:
        if any(element.parent_id == element_id for element in self._project.wbs_elements):
            raise ValueError("A WBS element with children cannot be removed.")
        if any(task.wbs_id == element_id for task in self._project.tasks):
            raise ValueError("A WBS element with assigned tasks cannot be removed.")
        elements = tuple(element for element in self._project.wbs_elements if element.id != element_id)
        if len(elements) == len(self._project.wbs_elements):
            raise KeyError(f"Unknown WBS element: {element_id}")
        self._accept(replace(self._project, wbs_elements=elements))

    def add_task(self, task: Task) -> None:
        if any(existing.id == task.id for existing in self._project.tasks):
            raise ValueError(f"Task already exists: {task.id}")
        self._accept(replace(self._project, tasks=(*self._project.tasks, task)))

    def add_task_with_relationships(
        self,
        task: Task,
        relationships: tuple[Dependency, ...],
    ) -> None:
        if any(existing.id == task.id for existing in self._project.tasks):
            raise ValueError(f"Task already exists: {task.id}")
        if any(task.id not in (edge.predecessor_id, edge.successor_id) for edge in relationships):
            raise ValueError("Every new relationship must reference the new activity.")
        self._accept(replace(
            self._project,
            tasks=(*self._project.tasks, task),
            dependencies=(*self._project.dependencies, *relationships),
        ))

    def replace_task(self, task: Task) -> None:
        if not any(existing.id == task.id for existing in self._project.tasks):
            raise KeyError(f"Unknown task: {task.id}")
        tasks = tuple(task if existing.id == task.id else existing for existing in self._project.tasks)
        self._accept(replace(self._project, tasks=tasks))

    def assign_task_to_wbs(
        self,
        task_id: str,
        parent_id: str,
        *,
        name: str | None = None,
        sequence: str | None = None,
    ) -> Task:
        task = next((item for item in self._project.tasks if item.id == task_id), None)
        if task is None:
            raise KeyError(f"Unknown task: {task_id}")
        wbs_code = self.next_task_wbs_code(parent_id, task_id)
        revised = replace(
            task,
            name=name.strip() if name is not None else task.name,
            sequence=sequence.strip() if sequence is not None else task.sequence,
            wbs_id=parent_id,
            wbs_code=wbs_code,
        )
        self.replace_task(revised)
        return revised

    def next_task_wbs_code(self, parent_id: str, exclude_task_id: str | None = None) -> str:
        parent = next((item for item in self._project.wbs_elements if item.id == parent_id), None)
        if parent is None:
            raise KeyError(f"Unknown WBS element: {parent_id}")
        prefix = f"{parent.code}."
        used_numbers: set[int] = set()
        for element in self._project.wbs_elements:
            if element.parent_id == parent_id:
                match = re.fullmatch(rf"{re.escape(prefix)}([1-9][0-9]*)", element.code)
                if match:
                    used_numbers.add(int(match.group(1)))
        for existing in self._project.tasks:
            if existing.id != exclude_task_id and existing.wbs_id == parent_id and existing.wbs_code:
                match = re.fullmatch(rf"{re.escape(prefix)}([1-9][0-9]*)", existing.wbs_code)
                if match:
                    used_numbers.add(int(match.group(1)))
        next_number = 1
        while next_number in used_numbers:
            next_number += 1
        return f"{prefix}{next_number}"

    def replace_task_with_dependencies(
        self,
        task: Task,
        incoming_dependencies: tuple[Dependency, ...],
    ) -> None:
        if not any(existing.id == task.id for existing in self._project.tasks):
            raise KeyError(f"Unknown task: {task.id}")
        if any(edge.successor_id != task.id for edge in incoming_dependencies):
            raise ValueError("Every edited relationship must target the selected activity.")
        tasks = tuple(task if existing.id == task.id else existing for existing in self._project.tasks)
        dependencies = tuple(
            edge for edge in self._project.dependencies if edge.successor_id != task.id
        ) + incoming_dependencies
        self._accept(replace(self._project, tasks=tasks, dependencies=dependencies))

    def replace_task_with_relationships(
        self,
        task: Task,
        relationships: tuple[Dependency, ...],
    ) -> None:
        if not any(existing.id == task.id for existing in self._project.tasks):
            raise KeyError(f"Unknown task: {task.id}")
        if any(task.id not in (edge.predecessor_id, edge.successor_id) for edge in relationships):
            raise ValueError("Every edited relationship must reference the selected activity.")
        tasks = tuple(task if existing.id == task.id else existing for existing in self._project.tasks)
        dependencies = tuple(
            edge for edge in self._project.dependencies
            if task.id not in (edge.predecessor_id, edge.successor_id)
        ) + relationships
        self._accept(replace(self._project, tasks=tasks, dependencies=dependencies))

    def remove_task(self, task_id: str) -> None:
        tasks = tuple(task for task in self._project.tasks if task.id != task_id)
        if len(tasks) == len(self._project.tasks):
            raise KeyError(f"Unknown task: {task_id}")
        dependencies = tuple(
            edge for edge in self._project.dependencies
            if edge.predecessor_id != task_id and edge.successor_id != task_id
        )
        constraints = tuple(item for item in self._project.constraints if item.task_id != task_id)
        workflow_links = tuple(link for link in self._project.workflow_links if link.task_id != task_id)
        self._accept(replace(
            self._project,
            tasks=tasks,
            dependencies=dependencies,
            constraints=constraints,
            workflow_links=workflow_links,
        ))

    def add_dependency(self, dependency: Dependency) -> None:
        self._accept(replace(self._project, dependencies=(*self._project.dependencies, dependency)))

    def remove_dependency(self, dependency: Dependency) -> None:
        dependencies = tuple(edge for edge in self._project.dependencies if edge != dependency)
        if len(dependencies) == len(self._project.dependencies):
            raise KeyError("Unknown dependency.")
        self._accept(replace(self._project, dependencies=dependencies))

    def add_constraint(self, constraint: Constraint) -> None:
        self._accept(replace(self._project, constraints=(*self._project.constraints, constraint)))

    def remove_constraint(self, constraint: Constraint) -> None:
        constraints = tuple(item for item in self._project.constraints if item != constraint)
        if len(constraints) == len(self._project.constraints):
            raise KeyError("Unknown constraint.")
        self._accept(replace(self._project, constraints=constraints))

    def _accept(self, candidate: ProjectSnapshot) -> None:
        result = self._calculate(candidate)
        self._undo_stack.append(self._project)
        self._redo_stack.clear()
        self._project = self._normalized_project(candidate, result)
        self._result = result

    @staticmethod
    def _normalized_project(project: ProjectSnapshot, result: ScheduleResult) -> ProjectSnapshot:
        tasks = tuple(result.tasks[task.id].task for task in project.tasks)
        return replace(project, tasks=tasks) if tasks != project.tasks else project

    def _calculate(self, project: ProjectSnapshot) -> ScheduleResult:
        return self._engine.calculate(
            project_start=project.project_start,
            tasks=project.tasks,
            dependencies=project.dependencies,
            constraints=project.constraints,
            wbs_elements=project.wbs_elements,
            calendar=project.calendar,
            required_finish=project.required_finish,
        )
