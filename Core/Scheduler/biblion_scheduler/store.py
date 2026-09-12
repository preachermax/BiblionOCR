"""SQLite persistence for scheduler inputs and immutable baseline snapshots."""

from __future__ import annotations

import sqlite3
from hashlib import sha256
import json
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4

from .calendar import WorkingCalendar
from .models import (
    Baseline,
    BaselineTask,
    Constraint,
    ConstraintType,
    Dependency,
    DependencyType,
    DurationUnit,
    GovernedWorkflow,
    ProjectSnapshot,
    ScheduleResult,
    ScheduleRun,
    Task,
    WBSElement,
    WorkflowLink,
    WorkflowAuditEvent,
    WorkflowGovernanceState,
    WorkflowImportRecord,
    WorkflowMappingRole,
    WorkflowReconciliationStatus,
    WorkflowScope,
    WorkflowSourceSnapshot,
    WorkflowTaskMapping,
)
from .workflow import WorkflowCatalog


class SchedulerStore:
    """A small migration-managed SQLite repository.

    Project saves replace only the persisted input snapshot for the selected
    project. Baselines are append-only: this class intentionally exposes no
    update or delete operation for them.
    """

    def __init__(self, database_path: str | Path) -> None:
        self._connection = sqlite3.connect(database_path)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._migrate()

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "SchedulerStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def save_project(self, project: ProjectSnapshot) -> None:
        task_ids = {task.id for task in project.tasks}
        if any(edge.predecessor_id not in task_ids or edge.successor_id not in task_ids for edge in project.dependencies):
            raise ValueError("Every dependency must reference a project task.")
        if any(constraint.task_id not in task_ids for constraint in project.constraints):
            raise ValueError("Every constraint must reference a project task.")
        with self._connection:
            self._connection.execute(
                """INSERT INTO projects (id, name, project_start, required_finish, working_weekdays, external_reference)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET
                       name = excluded.name,
                       project_start = excluded.project_start,
                       required_finish = excluded.required_finish,
                       working_weekdays = excluded.working_weekdays,
                       external_reference = excluded.external_reference""",
                (
                    project.id,
                    project.name,
                    project.project_start.isoformat(),
                    self._date_value(project.required_finish),
                    ",".join(str(day) for day in sorted(project.calendar.working_weekdays)),
                    project.external_reference,
                ),
            )
            for table in ("calendar_holidays", "constraints", "dependencies", "workflow_links", "tasks", "wbs_elements"):
                self._connection.execute(f"DELETE FROM {table} WHERE project_id = ?", (project.id,))
            self._connection.executemany(
                """INSERT INTO wbs_elements
                   (project_id, id, code, name, parent_id, display_order, planned_start, planned_finish,
                    duration_unit)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    (
                        project.id, element.id, element.code, element.name, element.parent_id, order,
                        self._date_value(element.planned_start), self._date_value(element.planned_finish),
                        element.duration_unit.value,
                    )
                    for order, element in enumerate(project.wbs_elements)
                ],
            )
            self._connection.executemany(
                """INSERT INTO tasks
                   (project_id, id, name, duration_days, display_order, wbs_id,
                    progress_percent, page_percent_complete, workflow_sequence,
                          planned_start, planned_finish, actual_start, actual_finish, duration_unit, wbs_code)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    (
                        project.id, task.id, task.name, task.duration_days, order, task.wbs_id,
                        task.progress_percent, task.page_percent_complete, task.sequence,
                        self._date_value(task.planned_start), self._date_value(task.planned_finish),
                        self._date_value(task.actual_start), self._date_value(task.actual_finish),
                        task.duration_unit.value, task.wbs_code,
                    )
                    for order, task in enumerate(project.tasks)
                ],
            )
            self._connection.executemany(
                """INSERT INTO dependencies (project_id, predecessor_id, successor_id, dependency_type, lag_days)
                   VALUES (?, ?, ?, ?, ?)""",
                [
                    (project.id, edge.predecessor_id, edge.successor_id, edge.dependency_type.value, edge.lag_days)
                    for edge in project.dependencies
                ],
            )
            self._connection.executemany(
                """INSERT INTO constraints (project_id, task_id, constraint_type, constraint_date)
                   VALUES (?, ?, ?, ?)""",
                [
                    (project.id, item.task_id, item.constraint_type.value, self._date_value(item.constraint_date))
                    for item in project.constraints
                ],
            )
            self._connection.executemany(
                "INSERT INTO calendar_holidays (project_id, holiday_date) VALUES (?, ?)",
                [(project.id, holiday.isoformat()) for holiday in project.calendar.holidays],
            )
            self._connection.executemany(
                """INSERT INTO workflow_links (project_id, task_id, scope, source, identity_json, source_row)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                [
                    (project.id, link.task_id, link.scope.value, link.source, json.dumps(link.identity), link.source_row)
                    for link in project.workflow_links
                ],
            )
            placeholders = ",".join("?" for _ in task_ids)
            self._connection.execute(
                f"""DELETE FROM workflow_task_mappings
                    WHERE project_id = ? AND task_id NOT IN ({placeholders})""",
                (project.id, *sorted(task_ids)),
            )

    def load_project(self, project_id: str) -> ProjectSnapshot:
        row = self._connection.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if row is None:
            raise KeyError(f"Unknown project: {project_id}")
        wbs_elements = tuple(
            WBSElement(
                item["id"], item["code"], item["name"], item["parent_id"],
                self._parse_date(item["planned_start"]), self._parse_date(item["planned_finish"]),
                DurationUnit(item["duration_unit"]),
            )
            for item in self._connection.execute(
                "SELECT * FROM wbs_elements WHERE project_id = ? ORDER BY display_order", (project_id,)
            )
        )
        tasks = tuple(
            Task(
                item["id"], item["name"], item["duration_days"], item["wbs_id"],
                item["progress_percent"], item["page_percent_complete"], item["workflow_sequence"],
                self._parse_date(item["planned_start"]), self._parse_date(item["planned_finish"]),
                self._parse_date(item["actual_start"]), self._parse_date(item["actual_finish"]),
                DurationUnit(item["duration_unit"]),
                item["wbs_code"],
            )
            for item in self._connection.execute("SELECT * FROM tasks WHERE project_id = ? ORDER BY display_order", (project_id,))
        )
        dependencies = tuple(
            Dependency(item["predecessor_id"], item["successor_id"], DependencyType(item["dependency_type"]), item["lag_days"])
            for item in self._connection.execute("SELECT * FROM dependencies WHERE project_id = ? ORDER BY id", (project_id,))
        )
        constraints = tuple(
            Constraint(
                item["task_id"],
                ConstraintType(item["constraint_type"]),
                self._parse_date(item["constraint_date"]),
            )
            for item in self._connection.execute("SELECT * FROM constraints WHERE project_id = ? ORDER BY id", (project_id,))
        )
        holidays = frozenset(
            self._parse_date(item["holiday_date"])
            for item in self._connection.execute("SELECT holiday_date FROM calendar_holidays WHERE project_id = ?", (project_id,))
        )
        workflow_links = tuple(
            WorkflowLink(
                item["task_id"],
                WorkflowScope(item["scope"]),
                item["source"],
                tuple(json.loads(item["identity_json"])),
                item["source_row"],
            )
            for item in self._connection.execute(
                "SELECT * FROM workflow_links WHERE project_id = ? ORDER BY task_id", (project_id,)
            )
        )
        return ProjectSnapshot(
            id=row["id"],
            name=row["name"],
            project_start=date.fromisoformat(row["project_start"]),
            tasks=tasks,
            wbs_elements=wbs_elements,
            dependencies=dependencies,
            constraints=constraints,
            calendar=WorkingCalendar(frozenset(int(day) for day in row["working_weekdays"].split(",")), holidays),
            required_finish=self._parse_date(row["required_finish"]),
            external_reference=row["external_reference"],
            workflow_links=workflow_links,
        )

    def import_workflow_catalog(
        self,
        project_id: str,
        catalog: WorkflowCatalog,
        source_revision: str,
        schema_version: str = "1",
        snapshot_id: str | None = None,
    ) -> WorkflowSourceSnapshot:
        """Stage an immutable, idempotent workflow source snapshot for review."""
        if not source_revision.strip():
            raise ValueError("Workflow source revision is required.")
        source = str(catalog.source_path)
        checksum = sha256(catalog.source_path.read_bytes()).hexdigest()
        existing = self._connection.execute(
            """SELECT id FROM workflow_source_snapshots
               WHERE project_id = ? AND source = ? AND scope = ? AND checksum = ?""",
            (project_id, source, catalog.scope.value, checksum),
        ).fetchone()
        if existing is not None:
            return self.load_workflow_source_snapshot(existing["id"])
        if self._connection.execute("SELECT 1 FROM projects WHERE id = ?", (project_id,)).fetchone() is None:
            raise KeyError(f"Unknown project: {project_id}")

        snapshot_id = snapshot_id or str(uuid4())
        imported_at = datetime.now(timezone.utc)
        records = []
        for step in catalog.steps:
            identity_json = json.dumps(step.identity)
            payload_json = json.dumps(self._workflow_step_payload(step), sort_keys=True)
            status, workflow_id = self._workflow_reconciliation_match(
                project_id, catalog.scope, identity_json, payload_json
            )
            records.append(
                (
                    str(uuid4()), snapshot_id, step.source_row, identity_json,
                    payload_json, status.value, workflow_id,
                )
            )
        with self._connection:
            self._connection.execute(
                """INSERT INTO workflow_source_snapshots
                   (id, project_id, source, scope, source_revision, checksum, schema_version, imported_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    snapshot_id, project_id, source, catalog.scope.value, source_revision,
                    checksum, schema_version, imported_at.isoformat(),
                ),
            )
            self._connection.executemany(
                """INSERT INTO workflow_import_records
                   (id, snapshot_id, source_row, identity_json, payload_json, status, workflow_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                records,
            )
            self._record_workflow_audit(
                project_id,
                "imported",
                "source_snapshot",
                snapshot_id,
                {
                    "source": source,
                    "source_revision": source_revision,
                    "checksum": checksum,
                    "record_count": len(records),
                },
            )
        return self.load_workflow_source_snapshot(snapshot_id)

    def load_workflow_source_snapshot(self, snapshot_id: str) -> WorkflowSourceSnapshot:
        row = self._connection.execute(
            "SELECT * FROM workflow_source_snapshots WHERE id = ?", (snapshot_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"Unknown workflow source snapshot: {snapshot_id}")
        return WorkflowSourceSnapshot(
            row["id"], row["project_id"], row["source"], WorkflowScope(row["scope"]),
            row["source_revision"], row["checksum"], row["schema_version"],
            datetime.fromisoformat(row["imported_at"]),
        )

    def list_workflow_source_snapshots(self, project_id: str) -> tuple[WorkflowSourceSnapshot, ...]:
        return tuple(
            self.load_workflow_source_snapshot(row["id"])
            for row in self._connection.execute(
                """SELECT id FROM workflow_source_snapshots
                   WHERE project_id = ? ORDER BY imported_at DESC, id DESC""",
                (project_id,),
            )
        )

    def list_workflow_import_records(self, snapshot_id: str) -> tuple[WorkflowImportRecord, ...]:
        return tuple(
            WorkflowImportRecord(
                row["id"], row["snapshot_id"], row["source_row"],
                tuple(json.loads(row["identity_json"])), json.loads(row["payload_json"]),
                WorkflowReconciliationStatus(row["status"]), row["workflow_id"],
            )
            for row in self._connection.execute(
                "SELECT * FROM workflow_import_records WHERE snapshot_id = ? ORDER BY source_row, id",
                (snapshot_id,),
            )
        )

    def approve_workflow_record(
        self,
        record_id: str,
        workflow_id: str | None = None,
    ) -> GovernedWorkflow:
        """Approve one staged row into a stable Scheduler-owned workflow."""
        row = self._connection.execute(
            """SELECT records.*, snapshots.project_id, snapshots.scope
               FROM workflow_import_records AS records
               JOIN workflow_source_snapshots AS snapshots ON snapshots.id = records.snapshot_id
               WHERE records.id = ?""",
            (record_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"Unknown workflow import record: {record_id}")
        if row["status"] == WorkflowReconciliationStatus.APPROVED.value:
            return self.load_governed_workflow(row["workflow_id"])
        if row["status"] == WorkflowReconciliationStatus.CONFLICT.value and workflow_id is None:
            raise ValueError("Conflicting records require an explicit governed workflow identity.")
        payload = json.loads(row["payload_json"])
        workflow_id = workflow_id or row["workflow_id"] or str(uuid4())
        with self._connection:
            self._connection.execute(
                """INSERT INTO governed_workflows
                   (id, project_id, scope, sequence, description, milestone_name, method,
                    module, section, source_module, destination_module)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET
                       sequence = excluded.sequence, description = excluded.description,
                       milestone_name = excluded.milestone_name, method = excluded.method,
                       module = excluded.module, section = excluded.section,
                       source_module = excluded.source_module,
                       destination_module = excluded.destination_module""",
                (
                    workflow_id, row["project_id"], row["scope"], payload["sequence"],
                    payload["description"], payload["milestone_name"], payload["method"],
                    payload["module"], payload["section"], payload["source_module"],
                    payload["destination_module"],
                ),
            )
            self._connection.execute(
                """UPDATE workflow_import_records
                   SET workflow_id = ?, status = ? WHERE id = ?""",
                (workflow_id, WorkflowReconciliationStatus.APPROVED.value, record_id),
            )
            self._record_workflow_audit(
                row["project_id"],
                "approved",
                "workflow_import_record",
                record_id,
                {"workflow_id": workflow_id},
            )
        return self.load_governed_workflow(workflow_id)

    def set_workflow_record_status(
        self,
        record_id: str,
        status: WorkflowReconciliationStatus,
    ) -> None:
        if status in (WorkflowReconciliationStatus.MAPPED, WorkflowReconciliationStatus.APPROVED):
            raise ValueError("Mapped and approved records require an explicit workflow identity.")
        row = self._connection.execute(
            """SELECT snapshots.project_id, records.status
               FROM workflow_import_records AS records
               JOIN workflow_source_snapshots AS snapshots ON snapshots.id = records.snapshot_id
               WHERE records.id = ?""",
            (record_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"Unknown workflow import record: {record_id}")
        if row["status"] == WorkflowReconciliationStatus.APPROVED.value:
            raise ValueError("Approved workflow records cannot be reclassified.")
        with self._connection:
            self._connection.execute(
                "UPDATE workflow_import_records SET status = ?, workflow_id = NULL WHERE id = ?",
                (status.value, record_id),
            )
            self._record_workflow_audit(
                row["project_id"],
                "status_changed",
                "workflow_import_record",
                record_id,
                {"status": status.value},
            )

    def load_governed_workflow(self, workflow_id: str) -> GovernedWorkflow:
        row = self._connection.execute(
            "SELECT * FROM governed_workflows WHERE id = ?", (workflow_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"Unknown governed workflow: {workflow_id}")
        return GovernedWorkflow(
            row["id"], row["project_id"], WorkflowScope(row["scope"]), row["sequence"],
            row["milestone_name"], row["method"], row["description"], row["module"],
            row["section"], row["source_module"], row["destination_module"],
        )

    def list_governed_workflows(self, project_id: str) -> tuple[GovernedWorkflow, ...]:
        return tuple(
            self.load_governed_workflow(row["id"])
            for row in self._connection.execute(
                """SELECT id FROM governed_workflows
                   WHERE project_id = ? ORDER BY scope, sequence, milestone_name, id""",
                (project_id,),
            )
        )

    def map_workflow_to_task(
        self,
        project_id: str,
        workflow_id: str,
        task_id: str,
        role: WorkflowMappingRole = WorkflowMappingRole.IMPLEMENTS,
    ) -> WorkflowTaskMapping:
        if self._connection.execute(
            "SELECT 1 FROM governed_workflows WHERE id = ? AND project_id = ?",
            (workflow_id, project_id),
        ).fetchone() is None:
            raise KeyError(f"Unknown governed workflow: {workflow_id}")
        if self._connection.execute(
            "SELECT 1 FROM tasks WHERE project_id = ? AND id = ?", (project_id, task_id)
        ).fetchone() is None:
            raise KeyError(f"Unknown project task: {task_id}")
        approved_at = datetime.now(timezone.utc)
        with self._connection:
            cursor = self._connection.execute(
                """INSERT INTO workflow_task_mappings
                   (project_id, workflow_id, task_id, role, approved_at)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(project_id, workflow_id, task_id, role) DO NOTHING""",
                (project_id, workflow_id, task_id, role.value, approved_at.isoformat()),
            )
            if cursor.rowcount:
                self._record_workflow_audit(
                    project_id,
                    "mapped_to_task",
                    "governed_workflow",
                    workflow_id,
                    {"task_id": task_id, "role": role.value},
                )
        return next(
            mapping for mapping in self.list_workflow_task_mappings(project_id)
            if mapping.workflow_id == workflow_id and mapping.task_id == task_id and mapping.role is role
        )

    def list_workflow_task_mappings(self, project_id: str) -> tuple[WorkflowTaskMapping, ...]:
        return tuple(
            WorkflowTaskMapping(
                row["project_id"], row["workflow_id"], row["task_id"],
                WorkflowMappingRole(row["role"]), datetime.fromisoformat(row["approved_at"]),
            )
            for row in self._connection.execute(
                """SELECT * FROM workflow_task_mappings
                   WHERE project_id = ? ORDER BY workflow_id, task_id, role""",
                (project_id,),
            )
        )

    def list_workflow_audit_events(self, project_id: str) -> tuple[WorkflowAuditEvent, ...]:
        return tuple(
            WorkflowAuditEvent(
                row["id"], row["project_id"], datetime.fromisoformat(row["recorded_at"]),
                row["action"], row["entity_type"], row["entity_id"],
                json.loads(row["details_json"]),
            )
            for row in self._connection.execute(
                """SELECT * FROM workflow_audit_events
                   WHERE project_id = ? ORDER BY recorded_at, id""",
                (project_id,),
            )
        )

    def workflow_governance_state(self, project_id: str) -> WorkflowGovernanceState:
        snapshots = self.list_workflow_source_snapshots(project_id)
        return WorkflowGovernanceState(
            snapshots=snapshots,
            records=tuple(
                record
                for snapshot in snapshots
                for record in self.list_workflow_import_records(snapshot.id)
            ),
            workflows=self.list_governed_workflows(project_id),
            mappings=self.list_workflow_task_mappings(project_id),
            audit_events=self.list_workflow_audit_events(project_id),
        )

    def create_baseline(self, project: ProjectSnapshot, result: ScheduleResult, name: str, baseline_id: str | None = None) -> Baseline:
        if not name.strip():
            raise ValueError("Baseline name is required.")
        if set(result.tasks) != {task.id for task in project.tasks}:
            raise ValueError("Baseline result must contain exactly the project's tasks.")
        baseline_id = baseline_id or str(uuid4())
        captured_at = datetime.now(timezone.utc)
        with self._connection:
            if self._connection.execute("SELECT 1 FROM projects WHERE id = ?", (project.id,)).fetchone() is None:
                raise KeyError(f"Unknown project: {project.id}")
            self._connection.execute(
                """INSERT INTO baselines (id, project_id, name, captured_at, project_start, project_finish)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (baseline_id, project.id, name, captured_at.isoformat(), result.project_start.isoformat(), result.project_finish.isoformat()),
            )
            self._connection.executemany(
                """INSERT INTO baseline_tasks (baseline_id, task_id, start_date, finish_date)
                   VALUES (?, ?, ?, ?)""",
                [
                    (baseline_id, task_id, item.start.isoformat(), item.finish.isoformat())
                    for task_id, item in result.tasks.items()
                ],
            )
        return self.load_baseline(baseline_id)

    def load_baseline(self, baseline_id: str) -> Baseline:
        row = self._connection.execute("SELECT * FROM baselines WHERE id = ?", (baseline_id,)).fetchone()
        if row is None:
            raise KeyError(f"Unknown baseline: {baseline_id}")
        tasks = {
            item["task_id"]: BaselineTask(item["task_id"], date.fromisoformat(item["start_date"]), date.fromisoformat(item["finish_date"]))
            for item in self._connection.execute("SELECT * FROM baseline_tasks WHERE baseline_id = ? ORDER BY task_id", (baseline_id,))
        }
        return Baseline(
            id=row["id"],
            project_id=row["project_id"],
            name=row["name"],
            captured_at=datetime.fromisoformat(row["captured_at"]),
            project_start=date.fromisoformat(row["project_start"]),
            project_finish=date.fromisoformat(row["project_finish"]),
            tasks=tasks,
        )

    def list_baselines(self, project_id: str) -> tuple[Baseline, ...]:
        return tuple(
            self.load_baseline(row["id"])
            for row in self._connection.execute("SELECT id FROM baselines WHERE project_id = ? ORDER BY captured_at", (project_id,))
        )

    def record_schedule_run(
        self,
        project: ProjectSnapshot,
        result: ScheduleResult,
        engine_version: str = "0.3.0",
        run_id: str | None = None,
    ) -> ScheduleRun:
        """Persist a calculation and stable hashes of its input and output."""
        if set(result.tasks) != {task.id for task in project.tasks}:
            raise ValueError("Schedule run result must contain exactly the project's tasks.")
        run_id = run_id or str(uuid4())
        recorded_at = datetime.now(timezone.utc)
        input_hash = self._digest(self._project_payload(project))
        output_hash = self._digest(self._result_payload(result))
        with self._connection:
            if self._connection.execute("SELECT 1 FROM projects WHERE id = ?", (project.id,)).fetchone() is None:
                raise KeyError(f"Unknown project: {project.id}")
            self._connection.execute(
                """INSERT INTO schedule_runs
                   (id, project_id, recorded_at, engine_version, input_hash, output_hash, project_start, project_finish)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (run_id, project.id, recorded_at.isoformat(), engine_version, input_hash, output_hash,
                 result.project_start.isoformat(), result.project_finish.isoformat()),
            )
            self._connection.executemany(
                """INSERT INTO schedule_run_tasks
                   (run_id, task_id, start_date, finish_date, late_start, late_finish, total_float_days, is_critical)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    (run_id, task_id, item.start.isoformat(), item.finish.isoformat(), item.late_start.isoformat(),
                     item.late_finish.isoformat(), item.total_float_days, int(item.is_critical))
                    for task_id, item in result.tasks.items()
                ],
            )
        return self.load_schedule_run(run_id)

    def load_schedule_run(self, run_id: str) -> ScheduleRun:
        row = self._connection.execute("SELECT * FROM schedule_runs WHERE id = ?", (run_id,)).fetchone()
        if row is None:
            raise KeyError(f"Unknown schedule run: {run_id}")
        return ScheduleRun(
            id=row["id"], project_id=row["project_id"], recorded_at=datetime.fromisoformat(row["recorded_at"]),
            engine_version=row["engine_version"], input_hash=row["input_hash"], output_hash=row["output_hash"],
            project_start=date.fromisoformat(row["project_start"]), project_finish=date.fromisoformat(row["project_finish"]),
        )

    def _migrate(self) -> None:
        with self._connection:
            self._connection.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY)")
            current_version = self._connection.execute("SELECT COALESCE(MAX(version), 0) FROM schema_migrations").fetchone()[0]
            if current_version < 1:
                self._connection.executescript(
                    """
                CREATE TABLE projects (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, project_start TEXT NOT NULL,
                    required_finish TEXT, working_weekdays TEXT NOT NULL, external_reference TEXT
                );
                CREATE TABLE tasks (
                    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    id TEXT NOT NULL, name TEXT NOT NULL, duration_days INTEGER NOT NULL CHECK(duration_days >= 0),
                    PRIMARY KEY (project_id, id)
                );
                CREATE TABLE dependencies (
                    id INTEGER PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    predecessor_id TEXT NOT NULL, successor_id TEXT NOT NULL, dependency_type TEXT NOT NULL,
                    lag_days INTEGER NOT NULL,
                    UNIQUE(project_id, predecessor_id, successor_id, dependency_type, lag_days)
                );
                CREATE TABLE constraints (
                    id INTEGER PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    task_id TEXT NOT NULL, constraint_type TEXT NOT NULL, constraint_date TEXT
                );
                CREATE TABLE calendar_holidays (
                    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    holiday_date TEXT NOT NULL, PRIMARY KEY(project_id, holiday_date)
                );
                CREATE TABLE baselines (
                    id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id), name TEXT NOT NULL,
                    captured_at TEXT NOT NULL, project_start TEXT NOT NULL, project_finish TEXT NOT NULL,
                    UNIQUE(project_id, name)
                );
                CREATE TABLE baseline_tasks (
                    baseline_id TEXT NOT NULL REFERENCES baselines(id), task_id TEXT NOT NULL,
                    start_date TEXT NOT NULL, finish_date TEXT NOT NULL,
                    PRIMARY KEY(baseline_id, task_id)
                );
                """
                )
                self._connection.execute("INSERT INTO schema_migrations (version) VALUES (1)")
            if current_version < 2:
                self._connection.executescript(
                    """
                    CREATE TABLE schedule_runs (
                        id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id), recorded_at TEXT NOT NULL,
                        engine_version TEXT NOT NULL, input_hash TEXT NOT NULL, output_hash TEXT NOT NULL,
                        project_start TEXT NOT NULL, project_finish TEXT NOT NULL
                    );
                    CREATE TABLE schedule_run_tasks (
                        run_id TEXT NOT NULL REFERENCES schedule_runs(id), task_id TEXT NOT NULL,
                        start_date TEXT NOT NULL, finish_date TEXT NOT NULL, late_start TEXT NOT NULL, late_finish TEXT NOT NULL,
                        total_float_days INTEGER NOT NULL, is_critical INTEGER NOT NULL,
                        PRIMARY KEY(run_id, task_id)
                    );
                    """
                )
                self._connection.execute("INSERT INTO schema_migrations (version) VALUES (2)")
            if current_version < 3:
                self._connection.execute("ALTER TABLE tasks ADD COLUMN display_order INTEGER NOT NULL DEFAULT 0")
                self._connection.execute("INSERT INTO schema_migrations (version) VALUES (3)")
            if current_version < 4:
                self._connection.executescript(
                    """
                    CREATE TABLE wbs_elements (
                        project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                        id TEXT NOT NULL, code TEXT NOT NULL, name TEXT NOT NULL, parent_id TEXT,
                        display_order INTEGER NOT NULL DEFAULT 0,
                        PRIMARY KEY (project_id, id), UNIQUE(project_id, code)
                    );
                    ALTER TABLE tasks ADD COLUMN wbs_id TEXT;
                    """
                )
                self._connection.execute("INSERT INTO schema_migrations (version) VALUES (4)")
            if current_version < 5:
                self._connection.executescript(
                    """
                    CREATE TABLE workflow_links (
                        project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                        task_id TEXT NOT NULL, scope TEXT NOT NULL, source TEXT NOT NULL,
                        identity_json TEXT NOT NULL, source_row INTEGER,
                        PRIMARY KEY (project_id, task_id)
                    );
                    """
                )
                self._connection.execute("INSERT INTO schema_migrations (version) VALUES (5)")
            if current_version < 6:
                self._connection.executescript(
                    """
                    ALTER TABLE tasks ADD COLUMN progress_percent INTEGER NOT NULL DEFAULT 0
                        CHECK(progress_percent BETWEEN 0 AND 100);
                    ALTER TABLE tasks ADD COLUMN page_percent_complete INTEGER NOT NULL DEFAULT 0
                        CHECK(page_percent_complete BETWEEN 0 AND 100);
                    ALTER TABLE tasks ADD COLUMN workflow_sequence TEXT NOT NULL DEFAULT '';
                    """
                )
                self._connection.execute("INSERT INTO schema_migrations (version) VALUES (6)")
            if current_version < 7:
                self._connection.executescript(
                    """
                    ALTER TABLE wbs_elements ADD COLUMN planned_start TEXT;
                    ALTER TABLE wbs_elements ADD COLUMN planned_finish TEXT;
                    ALTER TABLE tasks ADD COLUMN planned_start TEXT;
                    ALTER TABLE tasks ADD COLUMN planned_finish TEXT;
                    ALTER TABLE tasks ADD COLUMN actual_start TEXT;
                    ALTER TABLE tasks ADD COLUMN actual_finish TEXT;
                    """
                )
                self._connection.execute("INSERT INTO schema_migrations (version) VALUES (7)")
            if current_version < 8:
                self._connection.executescript(
                    """
                    ALTER TABLE tasks ADD COLUMN duration_unit TEXT NOT NULL DEFAULT 'days';
                    ALTER TABLE wbs_elements ADD COLUMN duration_unit TEXT NOT NULL DEFAULT 'days';
                    """
                )
                self._connection.execute("INSERT INTO schema_migrations (version) VALUES (8)")
            if current_version < 9:
                self._connection.executescript(
                    """
                    CREATE TABLE workflow_source_snapshots (
                        id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                        source TEXT NOT NULL,
                        scope TEXT NOT NULL,
                        source_revision TEXT NOT NULL,
                        checksum TEXT NOT NULL,
                        schema_version TEXT NOT NULL,
                        imported_at TEXT NOT NULL,
                        UNIQUE(project_id, source, scope, checksum)
                    );
                    CREATE TABLE governed_workflows (
                        id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                        scope TEXT NOT NULL,
                        sequence TEXT NOT NULL,
                        description TEXT NOT NULL,
                        milestone_name TEXT NOT NULL,
                        method TEXT NOT NULL,
                        module TEXT NOT NULL,
                        section TEXT NOT NULL,
                        source_module TEXT NOT NULL,
                        destination_module TEXT NOT NULL
                    );
                    CREATE TABLE workflow_import_records (
                        id TEXT PRIMARY KEY,
                        snapshot_id TEXT NOT NULL REFERENCES workflow_source_snapshots(id) ON DELETE CASCADE,
                        source_row INTEGER NOT NULL,
                        identity_json TEXT NOT NULL,
                        payload_json TEXT NOT NULL,
                        status TEXT NOT NULL,
                        workflow_id TEXT REFERENCES governed_workflows(id)
                    );
                    CREATE TABLE workflow_task_mappings (
                        project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                        workflow_id TEXT NOT NULL REFERENCES governed_workflows(id) ON DELETE CASCADE,
                        task_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        approved_at TEXT NOT NULL,
                        PRIMARY KEY(project_id, workflow_id, task_id, role)
                    );
                    CREATE TABLE workflow_audit_events (
                        id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                        recorded_at TEXT NOT NULL,
                        action TEXT NOT NULL,
                        entity_type TEXT NOT NULL,
                        entity_id TEXT NOT NULL,
                        details_json TEXT NOT NULL
                    );
                    """
                )
                self._connection.execute("INSERT INTO schema_migrations (version) VALUES (9)")
            if current_version < 10:
                self._connection.execute(
                    "ALTER TABLE tasks ADD COLUMN wbs_code TEXT NOT NULL DEFAULT ''"
                )
                self._connection.execute("INSERT INTO schema_migrations (version) VALUES (10)")

    @staticmethod
    def _date_value(value: date | None) -> str | None:
        return value.isoformat() if value else None

    @staticmethod
    def _parse_date(value: str | None) -> date | None:
        return date.fromisoformat(value) if value else None

    @staticmethod
    def _digest(value: object) -> str:
        return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    @staticmethod
    def _workflow_step_payload(step: object) -> dict[str, str]:
        return {
            field: str(getattr(step, field))
            for field in (
                "sequence", "description", "milestone_name", "method", "module",
                "section", "source_module", "destination_module",
            )
        }

    def _workflow_reconciliation_match(
        self,
        project_id: str,
        scope: WorkflowScope,
        identity_json: str,
        payload_json: str,
    ) -> tuple[WorkflowReconciliationStatus, str | None]:
        matches = self._connection.execute(
            """SELECT DISTINCT records.workflow_id, records.payload_json
               FROM workflow_import_records AS records
               JOIN workflow_source_snapshots AS snapshots ON snapshots.id = records.snapshot_id
               WHERE snapshots.project_id = ? AND snapshots.scope = ?
                 AND records.identity_json = ? AND records.workflow_id IS NOT NULL
                 AND records.status = ?""",
            (
                project_id, scope.value, identity_json,
                WorkflowReconciliationStatus.APPROVED.value,
            ),
        ).fetchall()
        workflow_ids = {row["workflow_id"] for row in matches}
        if not workflow_ids:
            return WorkflowReconciliationStatus.NEW, None
        if len(workflow_ids) > 1:
            return WorkflowReconciliationStatus.CONFLICT, None
        workflow_id = next(iter(workflow_ids))
        status = (
            WorkflowReconciliationStatus.MAPPED
            if any(row["payload_json"] == payload_json for row in matches)
            else WorkflowReconciliationStatus.CHANGED
        )
        return status, workflow_id

    def _record_workflow_audit(
        self,
        project_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        details: dict[str, object],
    ) -> None:
        self._connection.execute(
            """INSERT INTO workflow_audit_events
               (id, project_id, recorded_at, action, entity_type, entity_id, details_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                str(uuid4()), project_id, datetime.now(timezone.utc).isoformat(), action,
                entity_type, entity_id, json.dumps(details, sort_keys=True),
            ),
        )

    @staticmethod
    def _project_payload(project: ProjectSnapshot) -> dict[str, object]:
        return {
            "id": project.id,
            "name": project.name,
            "project_start": project.project_start.isoformat(),
            "required_finish": SchedulerStore._date_value(project.required_finish),
            "external_reference": project.external_reference,
            "working_weekdays": sorted(project.calendar.working_weekdays),
            "holidays": sorted(day.isoformat() for day in project.calendar.holidays),
            "wbs_elements": [
                (
                    element.id, element.code, element.name, element.parent_id,
                    SchedulerStore._date_value(element.planned_start),
                    SchedulerStore._date_value(element.planned_finish),
                    element.duration_unit.value,
                )
                for element in project.wbs_elements
            ],
            "tasks": sorted(
                (
                    task.id, task.name, task.duration_days, task.wbs_id,
                    task.progress_percent, task.page_percent_complete, task.sequence,
                    SchedulerStore._date_value(task.planned_start), SchedulerStore._date_value(task.planned_finish),
                    SchedulerStore._date_value(task.actual_start), SchedulerStore._date_value(task.actual_finish),
                    task.duration_unit.value, task.wbs_code,
                )
                for task in project.tasks
            ),
            "workflow_links": sorted(
                (link.task_id, link.scope.value, link.source, link.identity, link.source_row)
                for link in project.workflow_links
            ),
            "dependencies": sorted((edge.predecessor_id, edge.successor_id, edge.dependency_type.value, edge.lag_days) for edge in project.dependencies),
            "constraints": sorted((item.task_id, item.constraint_type.value, SchedulerStore._date_value(item.constraint_date)) for item in project.constraints),
        }

    @staticmethod
    def _result_payload(result: ScheduleResult) -> dict[str, object]:
        return {
            "project_start": result.project_start.isoformat(),
            "project_finish": result.project_finish.isoformat(),
            "required_finish": SchedulerStore._date_value(result.required_finish),
            "tasks": [
                (task_id, item.start.isoformat(), item.finish.isoformat(), item.late_start.isoformat(),
                 item.late_finish.isoformat(), item.total_float_days, item.is_critical)
                for task_id, item in sorted(result.tasks.items())
            ],
            "wbs_summaries": [
                (
                    element_id,
                    SchedulerStore._date_value(summary.start),
                    SchedulerStore._date_value(summary.finish),
                    summary.activity_count,
                    summary.milestone_count,
                    summary.has_critical_work,
                    summary.progress_percent,
                    summary.page_percent_complete,
                    summary.status.value,
                    summary.planned_duration_days,
                    SchedulerStore._date_value(summary.actual_start),
                    SchedulerStore._date_value(summary.actual_finish),
                    summary.actual_duration_days,
                )
                for element_id, summary in sorted(result.wbs_summaries.items())
            ],
            "constraint_violations": [
                (item.task_id, item.constraint.constraint_type.value, SchedulerStore._date_value(item.constraint.constraint_date))
                for item in result.constraint_violations
            ],
        }
