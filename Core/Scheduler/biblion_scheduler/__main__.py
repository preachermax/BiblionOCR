"""Launch a persisted project in the Biblion Scheduler desktop workspace."""

from __future__ import annotations

import argparse
from pathlib import Path

from .fixtures import biblionocr_development_plan
from .models import (
    Baseline,
    ProjectSnapshot,
    ScheduleResult,
    WorkflowMappingRole,
    WorkflowReconciliationStatus,
    WorkflowScope,
)
from .scheduler import ScheduleEngine
from .planner import PlanEditor
from .store import SchedulerStore
from .workflow import WorkflowCatalog


DEFAULT_DATABASE = Path.home() / ".biblion-scheduler" / "scheduler.sqlite"
DEFAULT_WORKFLOW_SOURCE = Path(__file__).resolve().parents[3] / "Model/Project/Data/csv/ProjectWorkflow.ods"


def prepare_workspace(
    database_path: str | Path,
    project_id: str = "biblionocr-development",
) -> tuple[ProjectSnapshot, ScheduleResult, Baseline | None]:
    """Load a persisted project, seeding the development plan on first run."""
    path = Path(database_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    with SchedulerStore(path) as store:
        try:
            project = store.load_project(project_id)
        except KeyError:
            seed = biblionocr_development_plan()
            if project_id != seed.id:
                raise
            store.save_project(seed)
            project = store.load_project(project_id)

        result = ScheduleEngine().calculate(
            project_start=project.project_start,
            tasks=project.tasks,
            dependencies=project.dependencies,
            constraints=project.constraints,
            wbs_elements=project.wbs_elements,
            calendar=project.calendar,
            required_finish=project.required_finish,
        )
        store.record_schedule_run(project, result)
        baselines = store.list_baselines(project.id)
        baseline = baselines[-1] if baselines else None
    return project, result, baseline


def parse_args(arguments: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Open a Biblion Scheduler project.")
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE, help="SQLite planner database path")
    parser.add_argument("--project", default="biblionocr-development", help="Persisted project identifier")
    return parser.parse_args(arguments)


def save_workspace(database_path: str | Path, project: ProjectSnapshot, result: ScheduleResult) -> None:
    """Persist one explicitly accepted workspace revision and its calculation."""
    with SchedulerStore(Path(database_path).expanduser()) as store:
        store.save_project(project)
        store.record_schedule_run(project, result)


def workflow_governance_callbacks(database_path: str | Path, project_id: str):
    """Build database-backed commands without exposing SQLite to the Qt view."""
    from .gui import WorkflowActivityMappingResult, WorkflowGovernanceCallbacks

    database = Path(database_path).expanduser()

    def load():
        with SchedulerStore(database) as store:
            return store.workflow_governance_state(project_id)

    def import_source(source: str, scope: WorkflowScope, source_revision: str):
        path = Path(source).expanduser()
        catalog = (
            WorkflowCatalog.from_ods(path, scope)
            if path.suffix.casefold() == ".ods"
            else WorkflowCatalog.from_csv(path, scope)
        )
        with SchedulerStore(database) as store:
            return store.import_workflow_catalog(project_id, catalog, source_revision)

    def approve(record_id: str):
        with SchedulerStore(database) as store:
            return store.approve_workflow_record(record_id)

    def set_status(record_id: str, status: WorkflowReconciliationStatus) -> None:
        with SchedulerStore(database) as store:
            store.set_workflow_record_status(record_id, status)

    def map_task(
        workflow_id: str,
        task_id: str,
        role: WorkflowMappingRole,
        parent_wbs_id: str,
        project: ProjectSnapshot,
    ) -> WorkflowActivityMappingResult:
        editor = PlanEditor(project)
        with SchedulerStore(database) as store:
            workflow = store.load_governed_workflow(workflow_id)
            editor.assign_task_to_wbs(
                task_id,
                parent_wbs_id,
                name=workflow.milestone_name,
                sequence=workflow.sequence,
            )
            store.save_project(editor.project)
            store.record_schedule_run(editor.project, editor.result)
            mapping = store.map_workflow_to_task(project_id, workflow_id, task_id, role)
        return WorkflowActivityMappingResult(mapping, editor.project, editor.result)

    return WorkflowGovernanceCallbacks(
        str(DEFAULT_WORKFLOW_SOURCE), load, import_source, approve, set_status, map_task
    )


def main(arguments: list[str] | None = None) -> int:
    options = parse_args(arguments)
    project, result, baseline = prepare_workspace(options.database, options.project)
    from .gui import launch_workspace

    return launch_workspace(
        project,
        result,
        baseline,
        lambda revised_project, revised_result: save_workspace(options.database, revised_project, revised_result),
        workflow_governance_callbacks(options.database, project.id),
        save_workspace,
        options.database,
    )


if __name__ == "__main__":
    raise SystemExit(main())
