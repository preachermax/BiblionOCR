from datetime import date
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from biblion_scheduler.__main__ import prepare_workspace
from biblion_scheduler import (
    BiblionOCRAdapter,
    BiblionOCRProjectReference,
    biblionocr_development_plan,
    Constraint,
    ConstraintType,
    Dependency,
    DependencyType,
    DurationUnit,
    PlanEditor,
    ProgressStatus,
    ProjectSnapshot,
    ScheduleEngine,
    ScheduleValidationError,
    Task,
    WBSElement,
    WBSSummary,
    WorkingCalendar,
    SchedulerStore,
    WorkflowCatalog,
    WorkflowLink,
    WorkflowMappingRole,
    WorkflowReconciliationStatus,
    WorkflowScope,
    HELP_TOPICS,
    help_topic,
    search_help_topics,
)


class ScheduleEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = ScheduleEngine()

    def test_empty_wbs_project_uses_project_start_as_forecast_finish(self) -> None:
        project = ProjectSnapshot(
            id="empty-wbs",
            name="Empty WBS",
            project_start=date(2026, 9, 12),
            tasks=(),
        )

        result = PlanEditor(project).result

        self.assertEqual(result.tasks, {})
        self.assertEqual(result.wbs_summaries, {})
        self.assertEqual(result.project_start, date(2026, 9, 14))
        self.assertEqual(result.project_finish, date(2026, 9, 14))

    def test_fs_chain_skips_weekend(self) -> None:
        result = self.engine.calculate(
            project_start=date(2026, 9, 7),  # Monday
            tasks=[
                Task("architecture", "Architecture", 5),
                Task("core", "Core Engine", 3),
                Task("test", "First Test", 2),
            ],
            dependencies=[
                Dependency("architecture", "core"),
                Dependency("core", "test"),
            ],
        )
        self.assertEqual(result.tasks["architecture"].start, date(2026, 9, 7))
        self.assertEqual(result.tasks["architecture"].finish, date(2026, 9, 11))
        self.assertEqual(result.tasks["core"].start, date(2026, 9, 14))
        self.assertEqual(result.tasks["core"].finish, date(2026, 9, 16))
        self.assertEqual(result.tasks["test"].start, date(2026, 9, 17))
        self.assertEqual(result.tasks["test"].finish, date(2026, 9, 18))

    def test_positive_lag_uses_working_days(self) -> None:
        result = self.engine.calculate(
            project_start=date(2026, 9, 7),
            tasks=[Task("a", "A", 1), Task("b", "B", 1)],
            dependencies=[Dependency("a", "b", lag_days=2)],
        )
        self.assertEqual(result.tasks["b"].start, date(2026, 9, 10))

    def test_hour_duration_uses_eight_hour_workdays(self) -> None:
        result = self.engine.calculate(
            project_start=date(2026, 9, 7),
            tasks=(
                Task("hours", "Hourly work", 12, duration_unit=DurationUnit.HOURS),
                Task(
                    "dated-hours", "Dated hourly work", 1,
                    planned_start=date(2026, 9, 9), planned_finish=date(2026, 9, 11),
                    duration_unit=DurationUnit.HOURS,
                ),
            ),
        )

        self.assertEqual(result.tasks["hours"].finish, date(2026, 9, 8))
        self.assertEqual(result.tasks["dated-hours"].task.duration_days, 24)

    def test_milestone_has_zero_duration(self) -> None:
        result = self.engine.calculate(
            project_start=date(2026, 9, 7),
            tasks=[Task("a", "A", 1), Task("m", "Architecture Frozen", 0)],
            dependencies=[Dependency("a", "m")],
        )
        self.assertEqual(result.tasks["m"].start, date(2026, 9, 8))
        self.assertEqual(result.tasks["m"].finish, date(2026, 9, 8))

    def test_holiday_is_not_a_working_day(self) -> None:
        calendar = WorkingCalendar(holidays=frozenset({date(2026, 9, 8)}))
        result = self.engine.calculate(
            project_start=date(2026, 9, 7),
            tasks=[Task("a", "A", 2)],
            calendar=calendar,
        )
        self.assertEqual(result.tasks["a"].finish, date(2026, 9, 9))

    def test_cycle_is_rejected(self) -> None:
        with self.assertRaises(ScheduleValidationError):
            self.engine.calculate(
                project_start=date(2026, 9, 7),
                tasks=[Task("a", "A", 1), Task("b", "B", 1)],
                dependencies=[Dependency("a", "b"), Dependency("b", "a")],
            )

    def test_ss_relationship_allows_overlap(self) -> None:
        result = self.engine.calculate(
            project_start=date(2026, 9, 7),
            tasks=[Task("a", "A", 3), Task("b", "B", 2)],
            dependencies=[Dependency("a", "b", DependencyType.START_TO_START, lag_days=1)],
        )
        self.assertEqual(result.tasks["b"].start, date(2026, 9, 8))
        self.assertEqual(result.tasks["b"].finish, date(2026, 9, 9))

    def test_ff_relationship_aligns_finishes(self) -> None:
        result = self.engine.calculate(
            project_start=date(2026, 9, 7),
            tasks=[Task("a", "A", 3), Task("b", "B", 2)],
            dependencies=[Dependency("a", "b", DependencyType.FINISH_TO_FINISH)],
        )
        self.assertEqual(result.tasks["b"].start, date(2026, 9, 8))
        self.assertEqual(result.tasks["b"].finish, date(2026, 9, 9))

    def test_sf_relationship_uses_predecessor_start(self) -> None:
        result = self.engine.calculate(
            project_start=date(2026, 9, 7),
            tasks=[Task("a", "A", 3), Task("b", "B", 2)],
            dependencies=[Dependency("a", "b", DependencyType.START_TO_FINISH, lag_days=3)],
        )
        self.assertEqual(result.tasks["b"].start, date(2026, 9, 9))
        self.assertEqual(result.tasks["b"].finish, date(2026, 9, 10))

    def test_negative_lag_is_lead(self) -> None:
        result = self.engine.calculate(
            project_start=date(2026, 9, 7),
            tasks=[Task("a", "A", 5), Task("b", "B", 1)],
            dependencies=[Dependency("a", "b", lag_days=-1)],
        )
        self.assertEqual(result.tasks["b"].start, date(2026, 9, 11))

    def test_backward_pass_identifies_critical_path_and_float(self) -> None:
        result = self.engine.calculate(
            project_start=date(2026, 9, 7),
            tasks=[Task("a", "A", 2), Task("b", "B", 3), Task("c", "C", 1), Task("d", "D", 1)],
            dependencies=[Dependency("a", "b"), Dependency("b", "c")],
        )
        self.assertTrue(result.tasks["a"].is_critical)
        self.assertTrue(result.tasks["b"].is_critical)
        self.assertTrue(result.tasks["c"].is_critical)
        self.assertFalse(result.tasks["d"].is_critical)
        self.assertEqual(result.tasks["d"].total_float_days, 5)

    def test_required_finish_produces_negative_float(self) -> None:
        result = self.engine.calculate(
            project_start=date(2026, 9, 7),
            required_finish=date(2026, 9, 9),
            tasks=[Task("a", "A", 5)],
        )
        self.assertEqual(result.tasks["a"].total_float_days, -2)
        self.assertTrue(result.tasks["a"].is_critical)

    def test_wbs_parent_rolls_up_nested_activities_and_milestones(self) -> None:
        result = self.engine.calculate(
            project_start=date(2026, 9, 7),
            wbs_elements=(
                WBSElement("workflow", "1", "OCR Workflow"),
                WBSElement("scanner", "1.1", "MyScanner", "workflow"),
            ),
            tasks=[
                Task("scan", "Acquire pages", 2, "scanner"),
                Task("acquired", "Pages acquired", 0, "scanner"),
            ],
            dependencies=[Dependency("scan", "acquired")],
        )

        module = result.wbs_summaries["scanner"]
        workflow = result.wbs_summaries["workflow"]
        self.assertEqual((module.start, module.finish), (date(2026, 9, 7), date(2026, 9, 9)))
        self.assertEqual((module.activity_count, module.milestone_count), (1, 1))
        self.assertEqual(workflow, WBSSummary(
            element=WBSElement("workflow", "1", "OCR Workflow"),
            start=module.start,
            finish=module.finish,
            activity_count=1,
            milestone_count=1,
            has_critical_work=True,
            planned_duration_days=3,
        ))

    def test_wbs_percent_complete_rolls_up_by_activity_duration(self) -> None:
        result = self.engine.calculate(
            project_start=date(2026, 9, 7),
            wbs_elements=(
                WBSElement("workflow", "1", "Workflow"),
                WBSElement("scanner", "1.1", "Scanner", "workflow"),
            ),
            tasks=(
                Task("scan", "Scan", 3, "scanner", 50, 20, "SCAN"),
                Task("review", "Review", 1, "scanner", 100, 60, "REVIEW"),
            ),
        )

        self.assertEqual(result.wbs_summaries["scanner"].progress_percent, 62.5)
        self.assertEqual(result.wbs_summaries["scanner"].page_percent_complete, 30.0)
        self.assertEqual(result.wbs_summaries["workflow"].progress_percent, 62.5)
        self.assertEqual(result.wbs_summaries["workflow"].page_percent_complete, 30.0)
        self.assertEqual(result.wbs_summaries["workflow"].status, ProgressStatus.IN_PROGRESS)
        self.assertEqual(result.tasks["scan"].task.status, ProgressStatus.IN_PROGRESS)

    def test_planned_dates_recalculate_duration_and_actual_dates_roll_up(self) -> None:
        result = self.engine.calculate(
            project_start=date(2026, 9, 7),
            wbs_elements=(
                WBSElement("workflow", "1", "Workflow"),
                WBSElement("scanner", "1.1", "Scanner", "workflow"),
            ),
            tasks=(
                Task(
                    "scan", "Scan", 99, "scanner", 50, 20, "SCAN",
                    date(2026, 9, 7), date(2026, 9, 11),
                    date(2026, 9, 8), date(2026, 9, 10),
                ),
                Task(
                    "review", "Review", 1, "scanner", 0, 0, "REVIEW",
                    date(2026, 9, 14), date(2026, 9, 14),
                    date(2026, 9, 11), None,
                ),
            ),
            dependencies=(Dependency("scan", "review"),),
        )

        self.assertEqual(result.tasks["scan"].task.duration_days, 5)
        summary = result.wbs_summaries["workflow"]
        self.assertEqual((summary.start, summary.finish, summary.planned_duration_days), (
            date(2026, 9, 7), date(2026, 9, 14), 6,
        ))
        self.assertEqual(summary.actual_start, date(2026, 9, 8))
        self.assertIsNone(summary.actual_finish)
        self.assertIsNone(summary.actual_duration_days)
        self.assertAlmostEqual(summary.progress_percent, 5 / 6 * 100)
        self.assertEqual(summary.status, ProgressStatus.IN_PROGRESS)

        editor = PlanEditor(ProjectSnapshot(
            id="dated",
            name="Dated",
            project_start=date(2026, 9, 7),
            tasks=(Task(
                "scan", "Scan", 99, planned_start=date(2026, 9, 7), planned_finish=date(2026, 9, 11)
            ),),
        ))
        self.assertEqual(editor.project.tasks[0].duration_days, 5)

    def test_completed_actuals_roll_up_finish_duration_and_complete_status(self) -> None:
        result = self.engine.calculate(
            project_start=date(2026, 9, 7),
            wbs_elements=(WBSElement("root", "1", "Root"),),
            tasks=(
                Task(
                    "first", "First", 2, "root", actual_start=date(2026, 9, 7), actual_finish=date(2026, 9, 8)
                ),
                Task(
                    "second", "Second", 1, "root", actual_start=date(2026, 9, 9), actual_finish=date(2026, 9, 11)
                ),
            ),
        )

        summary = result.wbs_summaries["root"]
        self.assertEqual((summary.actual_start, summary.actual_finish), (date(2026, 9, 7), date(2026, 9, 11)))
        self.assertEqual(summary.actual_duration_days, 5)
        self.assertEqual(summary.progress_percent, 100)
        self.assertEqual(summary.status, ProgressStatus.COMPLETE)
        self.assertTrue(all(item.task.progress_percent == 100 for item in result.tasks.values()))

    def test_wbs_planned_date_override_recalculates_summary_duration(self) -> None:
        result = self.engine.calculate(
            project_start=date(2026, 9, 7),
            wbs_elements=(WBSElement(
                "root", "1", "Root", planned_start=date(2026, 9, 7), planned_finish=date(2026, 9, 18)
            ),),
            tasks=(Task("activity", "Activity", 2, "root"),),
        )

        summary = result.wbs_summaries["root"]
        self.assertEqual((summary.start, summary.finish), (date(2026, 9, 7), date(2026, 9, 18)))
        self.assertEqual(summary.planned_duration_days, 10)

    def test_task_rejects_percentages_outside_valid_range(self) -> None:
        with self.assertRaisesRegex(ValueError, "progress percent"):
            Task("task", "Task", 1, progress_percent=101)
        with self.assertRaisesRegex(ValueError, "page percent"):
            Task("task", "Task", 1, page_percent_complete=-1)

    def test_wbs_cycle_is_rejected_by_project_snapshot(self) -> None:
        with self.assertRaisesRegex(ValueError, "WBS elements contain a cycle"):
            ProjectSnapshot(
                id="cyclic-wbs",
                name="Invalid WBS",
                project_start=date(2026, 9, 7),
                tasks=(Task("activity", "Activity", 1, "first"),),
                wbs_elements=(
                    WBSElement("first", "1", "First", "second"),
                    WBSElement("second", "1.1", "Second", "first"),
                ),
            )

    def test_plan_editor_applies_valid_edits_and_rejects_cycles_atomically(self) -> None:
        editor = PlanEditor(ProjectSnapshot(
            id="editable",
            name="Editable plan",
            project_start=date(2026, 9, 7),
            tasks=(Task("first", "First", 1),),
        ))
        editor.add_wbs_element(WBSElement("module", "1", "Module"))
        editor.replace_task(Task("first", "First", 2, "module"))
        editor.add_task(Task("second", "Second", 1, "module"))
        editor.add_dependency(Dependency("first", "second"))

        accepted = editor.project
        self.assertEqual(editor.result.tasks["second"].start, date(2026, 9, 9))
        with self.assertRaises(ScheduleValidationError):
            editor.add_dependency(Dependency("second", "first"))

        self.assertEqual(editor.project, accepted)
        self.assertEqual(editor.project.dependencies, (Dependency("first", "second"),))

    def test_plan_editor_assigns_next_available_activity_wbs_code(self) -> None:
        project = ProjectSnapshot(
            id="activity-wbs-code",
            name="Activity WBS code",
            project_start=date(2026, 9, 7),
            tasks=(
                Task("existing", "Existing", 1, "root", wbs_code="1.2"),
                Task("mapped", "Mapped", 1),
            ),
            wbs_elements=(
                WBSElement("root", "1", "Root"),
                WBSElement("first", "1.1", "First", "root"),
                WBSElement("third", "1.3", "Third", "root"),
            ),
        )
        editor = PlanEditor(project)

        assigned = editor.assign_task_to_wbs(
            "mapped",
            "root",
            name="Publication ready",
            sequence="PUB",
        )

        self.assertEqual(assigned.wbs_id, "root")
        self.assertEqual(assigned.wbs_code, "1.4")
        self.assertEqual(assigned.name, "Publication ready")
        self.assertEqual(assigned.sequence, "PUB")
        self.assertEqual(editor.project.tasks[-1], assigned)

    def test_plan_editor_undoes_and_redoes_accepted_edits(self) -> None:
        original = ProjectSnapshot(
            id="history",
            name="History",
            project_start=date(2026, 9, 7),
            tasks=(Task("first", "First", 1),),
        )
        editor = PlanEditor(original)
        editor.replace_task(Task("first", "Revised", 2))

        self.assertTrue(editor.can_undo)
        self.assertFalse(editor.can_redo)
        editor.undo()
        self.assertEqual(editor.project, original)
        self.assertTrue(editor.can_redo)
        editor.redo()
        self.assertEqual(editor.project.tasks[0], Task("first", "Revised", 2))

        editor.undo()
        editor.replace_task(Task("first", "Alternative", 3))
        self.assertFalse(editor.can_redo)

    def test_plan_editor_replaces_activity_and_incoming_relationships_atomically(self) -> None:
        editor = PlanEditor(ProjectSnapshot(
            id="relationships",
            name="Relationships",
            project_start=date(2026, 9, 7),
            tasks=(Task("a", "A", 2), Task("b", "B", 2), Task("c", "C", 1)),
            dependencies=(Dependency("a", "c"),),
        ))

        editor.replace_task_with_dependencies(
            Task("c", "Revised C", 1),
            (Dependency("b", "c", DependencyType.START_TO_START, -1),),
        )

        self.assertEqual(editor.project.tasks[-1].name, "Revised C")
        self.assertEqual(
            editor.project.dependencies,
            (Dependency("b", "c", DependencyType.START_TO_START, -1),),
        )

    def test_plan_editor_replaces_incoming_and_outgoing_relationships_atomically(self) -> None:
        editor = PlanEditor(ProjectSnapshot(
            id="all-relationships",
            name="All relationships",
            project_start=date(2026, 9, 7),
            tasks=(Task("a", "A", 2), Task("b", "B", 2), Task("c", "C", 1)),
            dependencies=(Dependency("a", "b"), Dependency("b", "c")),
        ))

        editor.replace_task_with_relationships(
            Task("b", "B", 2),
            (
                Dependency("a", "b", DependencyType.FINISH_TO_FINISH, 2),
                Dependency("b", "c", DependencyType.START_TO_START, -1),
            ),
        )

        self.assertEqual(editor.project.dependencies[0].lag_days, 2)
        self.assertEqual(editor.project.dependencies[1].lag_days, -1)

    def test_plan_editor_adds_edits_and_deletes_empty_wbs_summary_items(self) -> None:
        editor = PlanEditor(ProjectSnapshot(
            id="wbs-editing",
            name="WBS editing",
            project_start=date(2026, 9, 7),
            tasks=(Task("activity", "Activity", 1),),
        ))
        editor.add_wbs_element(WBSElement("root", "1", "Root"))
        editor.add_wbs_element(WBSElement("module", "1.1", "Module", "root"))
        editor.replace_wbs_element(WBSElement("module", "1.2", "Renamed Module", "root"))

        self.assertEqual(editor.project.wbs_elements[-1].name, "Renamed Module")
        with self.assertRaisesRegex(ValueError, "with children"):
            editor.remove_wbs_element("root")

        editor.remove_wbs_element("module")
        self.assertEqual(editor.project.wbs_elements, (WBSElement("root", "1", "Root"),))

    def test_plan_editor_inserts_wbs_and_renumbers_following_subtrees(self) -> None:
        project = ProjectSnapshot(
            id="wbs-insertion",
            name="WBS insertion",
            project_start=date(2026, 9, 7),
            tasks=(Task("activity", "Activity", 1, "second-child", wbs_code="1.2.1.1"),),
            wbs_elements=(
                WBSElement("root", "1", "Root"),
                WBSElement("first", "1.1", "First", "root"),
                WBSElement("second", "1.2", "Second", "root"),
                WBSElement("second-child", "1.2.1", "Second child", "second"),
                WBSElement("third", "1.3", "Third", "root"),
            ),
        )
        editor = PlanEditor(project)

        editor.insert_wbs_element(WBSElement("inserted", "1.2", "Inserted", "root"))

        self.assertEqual(
            [(element.id, element.code) for element in editor.project.wbs_elements],
            [
                ("root", "1"),
                ("first", "1.1"),
                ("inserted", "1.2"),
                ("second", "1.3"),
                ("second-child", "1.3.1"),
                ("third", "1.4"),
            ],
        )
        self.assertEqual(editor.project.tasks[0].wbs_id, "second-child")
        self.assertEqual(editor.project.tasks[0].wbs_code, "1.3.1.1")
        editor.undo()
        self.assertEqual(editor.project, project)

    def test_no_later_than_constraint_is_reported(self) -> None:
        result = self.engine.calculate(
            project_start=date(2026, 9, 7),
            tasks=[Task("a", "A", 1), Task("b", "B", 1)],
            dependencies=[Dependency("a", "b")],
            constraints=[Constraint("b", ConstraintType.START_NO_LATER_THAN, date(2026, 9, 7))],
        )
        self.assertEqual(len(result.constraint_violations), 1)
        self.assertEqual(result.constraint_violations[0].task_id, "b")

    def test_sqlite_round_trip_preserves_schedule_inputs(self) -> None:
        project = ProjectSnapshot(
            id="biblion-ocr",
            name="BiblionOCR development",
            project_start=date(2026, 9, 7),
            tasks=(
                Task(
                    "architecture", "Architecture", 2, "design", 75, 40, "ARCH",
                    date(2026, 9, 7), date(2026, 9, 9), date(2026, 9, 7), date(2026, 9, 8),
                ),
                Task("engine", "Engine", 12, "build", 20, 10, "BUILD", duration_unit=DurationUnit.HOURS),
            ),
            wbs_elements=(
                WBSElement("delivery", "1", "Delivery", duration_unit=DurationUnit.HOURS),
                WBSElement("design", "1.1", "Design", "delivery"),
                WBSElement("build", "1.2", "Build", "delivery"),
            ),
            dependencies=(Dependency("architecture", "engine"),),
            constraints=(Constraint("engine", ConstraintType.START_NO_EARLIER_THAN, date(2026, 9, 10)),),
            calendar=WorkingCalendar(holidays=frozenset({date(2026, 9, 8)})),
            external_reference="biblionocr:project/42",
            workflow_links=(
                WorkflowLink(
                    "architecture",
                    WorkflowScope.PROJECT,
                    "Model/Project/Data/csv/project_workflow.csv",
                    ("ARCH", "architecture_ready", "design"),
                    2,
                ),
            ),
        )
        with TemporaryDirectory() as directory:
            with SchedulerStore(Path(directory) / "scheduler.sqlite") as store:
                store.save_project(project)
                loaded = store.load_project(project.id)
        self.assertEqual(loaded, project)

    def test_version_three_database_migrates_without_losing_tasks(self) -> None:
        with TemporaryDirectory() as directory:
            database = Path(directory) / "scheduler.sqlite"
            connection = sqlite3.connect(database)
            connection.executescript(
                """
                CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY);
                INSERT INTO schema_migrations (version) VALUES (1), (2), (3);
                CREATE TABLE projects (id TEXT PRIMARY KEY);
                CREATE TABLE tasks (
                    project_id TEXT NOT NULL,
                    id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    duration_days INTEGER NOT NULL,
                    display_order INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (project_id, id)
                );
                INSERT INTO projects (id) VALUES ('legacy');
                INSERT INTO tasks (project_id, id, name, duration_days) VALUES ('legacy', 'task', 'Legacy task', 2);
                """
            )
            connection.close()

            with SchedulerStore(database):
                pass

            connection = sqlite3.connect(database)
            columns = {row[1] for row in connection.execute("PRAGMA table_info(tasks)")}
            wbs_columns = {row[1] for row in connection.execute("PRAGMA table_info(wbs_elements)")}
            task = connection.execute(
                """SELECT id, name, duration_days, wbs_id,
                      progress_percent, page_percent_complete, workflow_sequence,
                          planned_start, planned_finish, actual_start, actual_finish, duration_unit
                   FROM tasks"""
            ).fetchone()
            version = connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0]
            connection.close()

        self.assertIn("wbs_id", columns)
        self.assertIn("duration_unit", wbs_columns)
        self.assertEqual(task, ("task", "Legacy task", 2, None, 0, 0, "", None, None, None, None, "days"))
        self.assertEqual(version, 10)

    def test_workflow_catalog_preserves_duplicate_rows_and_filters_modules(self) -> None:
        with TemporaryDirectory() as directory:
            workflow_csv = Path(directory) / "page_workflow.csv"
            workflow_csv.write_text(
                "PageSections,Sequence,Description,MilestoneName,Module,Method\n"
                "Verse,SCAN,Acquire pages,pages_acquired,MyScanner,scan\n"
                "Verse,CLEAN,Clean pages,pages_cleaned,MyPixler,clean\n"
                "Verse,CLEAN,Clean pages again,pages_cleaned,MyPixler,clean\n",
                encoding="utf-8",
            )

            catalog = WorkflowCatalog.from_csv(workflow_csv, WorkflowScope.PAGE)

        self.assertEqual(len(catalog.steps), 3)
        self.assertEqual([step.sequence for step in catalog.steps_for_module("mypixler")], ["CLEAN", "CLEAN"])
        duplicate = ("Verse", "CLEAN", "pages_cleaned", "clean")
        self.assertEqual([step.source_row for step in catalog.duplicate_identities()[duplicate]], [3, 4])

    def test_workflow_catalog_reads_governing_ods_sheets(self) -> None:
        workbook = Path(__file__).parents[3] / "Model/Project/Data/csv/ProjectWorkflow.ods"

        project_catalog = WorkflowCatalog.from_ods(workbook, WorkflowScope.PROJECT)
        page_catalog = WorkflowCatalog.from_ods(workbook, WorkflowScope.PAGE)

        self.assertEqual(len(project_catalog.steps), 8)
        self.assertEqual(len(page_catalog.steps), 93)
        self.assertEqual(project_catalog.steps[0].sequence, "ASPF")
        self.assertEqual(page_catalog.steps[0].sequence, "SSHF")
        self.assertEqual(project_catalog.source_path, workbook)

    def test_workflow_governance_import_is_idempotent_and_maps_many_to_many(self) -> None:
        project = ProjectSnapshot(
            id="governed",
            name="Governed development plan",
            project_start=date(2026, 9, 7),
            tasks=(Task("design", "Design", 2), Task("build", "Build", 3)),
        )
        with TemporaryDirectory() as directory:
            workflow_csv = Path(directory) / "project_workflow.csv"
            workflow_csv.write_text(
                "Sequence,Description,MilestoneName,SourceModule,DestinationModule,Method\n"
                "ARCH,Approve architecture,architecture_ready,MyServer,MyScanner,approve\n"
                "BUILD,Implement workflow,implementation_ready,MyScanner,MyServer,build\n",
                encoding="utf-8",
            )
            catalog = WorkflowCatalog.from_csv(workflow_csv, WorkflowScope.PROJECT)
            database = Path(directory) / "scheduler.sqlite"
            with SchedulerStore(database) as store:
                store.save_project(project)
                first = store.import_workflow_catalog(
                    project.id, catalog, "ods-r1", snapshot_id="snapshot-1"
                )
                repeated = store.import_workflow_catalog(project.id, catalog, "ods-r1")
                records = store.list_workflow_import_records(first.id)
                architecture = store.approve_workflow_record(records[0].id, "workflow-architecture")
                implementation = store.approve_workflow_record(records[1].id, "workflow-build")
                first_mapping = store.map_workflow_to_task(
                    project.id, architecture.id, "design", WorkflowMappingRole.IMPLEMENTS
                )
                repeated_mapping = store.map_workflow_to_task(
                    project.id, architecture.id, "design", WorkflowMappingRole.IMPLEMENTS
                )
                store.map_workflow_to_task(project.id, architecture.id, "build")
                store.map_workflow_to_task(project.id, implementation.id, "build")
                mappings = store.list_workflow_task_mappings(project.id)
                approved_records = store.list_workflow_import_records(first.id)
                repeated_approval = store.approve_workflow_record(records[0].id)
                with self.assertRaisesRegex(ValueError, "cannot be reclassified"):
                    store.set_workflow_record_status(
                        records[0].id, WorkflowReconciliationStatus.IGNORED
                    )
                loaded_project = store.load_project(project.id)
                workflow_csv.write_text(
                    "Sequence,Description,MilestoneName,SourceModule,DestinationModule,Method\n"
                    "ARCH,Approve revised architecture,architecture_ready,MyServer,MyScanner,approve\n"
                    "BUILD,Implement workflow,implementation_ready,MyScanner,MyServer,build\n",
                    encoding="utf-8",
                )
                revised_catalog = WorkflowCatalog.from_csv(workflow_csv, WorkflowScope.PROJECT)
                revised = store.import_workflow_catalog(
                    project.id, revised_catalog, "ods-r2", snapshot_id="snapshot-2"
                )
                revised_records = store.list_workflow_import_records(revised.id)
                updated = store.approve_workflow_record(revised_records[0].id)
                store.set_workflow_record_status(
                    revised_records[1].id, WorkflowReconciliationStatus.IGNORED
                )
                audit_events = store.list_workflow_audit_events(project.id)
                governance = store.workflow_governance_state(project.id)

        self.assertEqual(repeated.id, first.id)
        self.assertEqual(len(records), 2)
        self.assertEqual({record.status for record in approved_records}, {
            WorkflowReconciliationStatus.APPROVED,
        })
        self.assertEqual(len(mappings), 3)
        self.assertEqual(first_mapping, repeated_mapping)
        self.assertEqual(repeated_approval, architecture)
        self.assertEqual(loaded_project.dependencies, ())
        self.assertEqual(revised_records[0].status, WorkflowReconciliationStatus.CHANGED)
        self.assertEqual(revised_records[0].workflow_id, architecture.id)
        self.assertEqual(revised_records[1].status, WorkflowReconciliationStatus.MAPPED)
        self.assertEqual(updated.id, architecture.id)
        self.assertEqual(updated.description, "Approve revised architecture")
        self.assertEqual(
            [event.action for event in audit_events].count("imported"),
            2,
        )
        self.assertEqual(
            [event.action for event in audit_events].count("approved"),
            3,
        )
        self.assertEqual(
            [event.action for event in audit_events].count("mapped_to_task"),
            3,
        )
        self.assertEqual(
            [event.action for event in audit_events].count("status_changed"),
            1,
        )
        self.assertEqual([snapshot.id for snapshot in governance.snapshots], ["snapshot-2", "snapshot-1"])
        self.assertEqual(len(governance.records), 4)
        self.assertEqual({workflow.id for workflow in governance.workflows}, {
            "workflow-architecture", "workflow-build",
        })
        self.assertEqual(governance.mappings, mappings)
        self.assertEqual(governance.audit_events, audit_events)

    def test_help_catalog_covers_core_planning_workflows(self) -> None:
        topic_ids = {topic.id for topic in HELP_TOPICS}
        self.assertTrue({
            "getting-started",
            "wbs",
            "activities",
            "dependencies",
            "constraints",
            "critical-path",
            "saving-baselines",
            "workflow-evidence",
            "troubleshooting",
        }.issubset(topic_ids))
        self.assertEqual(help_topic("wbs").title, "Work Breakdown Structure")
        self.assertEqual(
            [topic.id for topic in search_help_topics("negative float")],
            ["constraints", "critical-path"],
        )

    def test_baselines_are_independent_of_later_project_edits(self) -> None:
        initial = ProjectSnapshot(
            id="biblion-ocr",
            name="BiblionOCR development",
            project_start=date(2026, 9, 7),
            tasks=(Task("a", "A", 2), Task("b", "B", 1)),
            dependencies=(Dependency("a", "b"),),
        )
        revised = ProjectSnapshot(
            id="biblion-ocr",
            name="BiblionOCR development",
            project_start=date(2026, 9, 7),
            tasks=(Task("a", "A", 5), Task("b", "B", 1)),
            dependencies=(Dependency("a", "b"),),
        )
        with TemporaryDirectory() as directory:
            with SchedulerStore(Path(directory) / "scheduler.sqlite") as store:
                store.save_project(initial)
                baseline = store.create_baseline(initial, self.engine.calculate(
                    project_start=initial.project_start,
                    tasks=initial.tasks,
                    dependencies=initial.dependencies,
                ), "Approved plan", baseline_id="baseline-1")
                store.save_project(revised)
                reloaded = store.load_baseline("baseline-1")
                self.assertEqual(store.load_project(initial.id), revised)
        self.assertEqual(baseline.tasks["a"].finish, date(2026, 9, 8))
        self.assertEqual(reloaded, baseline)

    def test_schedule_run_hashes_are_reproducible(self) -> None:
        project = ProjectSnapshot(
            id="biblion-ocr",
            name="BiblionOCR development",
            project_start=date(2026, 9, 7),
            tasks=(Task("a", "A", 2), Task("b", "B", 1)),
            dependencies=(Dependency("a", "b"),),
        )
        result = self.engine.calculate(
            project_start=project.project_start,
            tasks=project.tasks,
            dependencies=project.dependencies,
        )
        with TemporaryDirectory() as directory:
            with SchedulerStore(Path(directory) / "scheduler.sqlite") as store:
                store.save_project(project)
                first = store.record_schedule_run(project, result, run_id="run-1")
                second = store.record_schedule_run(project, result, run_id="run-2")
                self.assertEqual(store.load_schedule_run("run-1"), first)
        self.assertEqual(first.input_hash, second.input_hash)
        self.assertEqual(first.output_hash, second.output_hash)

    def test_schedule_run_output_hash_includes_wbs_progress_rollup(self) -> None:
        wbs = (WBSElement("root", "1", "Root"),)
        initial = ProjectSnapshot(
            id="tracked",
            name="Tracked",
            project_start=date(2026, 9, 7),
            tasks=(Task("a", "A", 2, "root", 0, 0, "A"),),
            wbs_elements=wbs,
        )
        progressed = ProjectSnapshot(
            id="tracked",
            name="Tracked",
            project_start=date(2026, 9, 7),
            tasks=(Task("a", "A", 2, "root", 50, 25, "A"),),
            wbs_elements=wbs,
        )
        with TemporaryDirectory() as directory:
            with SchedulerStore(Path(directory) / "scheduler.sqlite") as store:
                store.save_project(initial)
                first = store.record_schedule_run(initial, self.engine.calculate(
                    project_start=initial.project_start,
                    tasks=initial.tasks,
                    wbs_elements=initial.wbs_elements,
                ))
                store.save_project(progressed)
                second = store.record_schedule_run(progressed, self.engine.calculate(
                    project_start=progressed.project_start,
                    tasks=progressed.tasks,
                    wbs_elements=progressed.wbs_elements,
                ))

        self.assertNotEqual(first.input_hash, second.input_hash)
        self.assertNotEqual(first.output_hash, second.output_hash)

    def test_biblionocr_adapter_only_attaches_a_stable_reference(self) -> None:
        project = ProjectSnapshot(
            id="scheduler-project",
            name="Schedule",
            project_start=date(2026, 9, 7),
            tasks=(Task("a", "A", 1),),
        )
        attached = BiblionOCRAdapter.attach_reference(
            project, BiblionOCRProjectReference("ocr-project-42", "rev-9")
        )
        self.assertEqual(attached.external_reference, "biblionocr:ocr-project-42@rev-9")
        self.assertIsNone(project.external_reference)

    def test_biblionocr_development_fixture_runs_end_to_end(self) -> None:
        project = biblionocr_development_plan()
        result = self.engine.calculate(
            project_start=project.project_start,
            tasks=project.tasks,
            dependencies=project.dependencies,
            constraints=project.constraints,
            wbs_elements=project.wbs_elements,
            calendar=project.calendar,
        )
        with TemporaryDirectory() as directory:
            with SchedulerStore(Path(directory) / "scheduler.sqlite") as store:
                store.save_project(project)
                baseline = store.create_baseline(project, result, "Fixture baseline", baseline_id="fixture-base")
                run = store.record_schedule_run(project, result, run_id="fixture-run")
                loaded = store.load_project(project.id)
        self.assertEqual(loaded, project)
        self.assertEqual(baseline.tasks["release-candidate"].finish, result.project_finish)
        self.assertEqual(run.project_finish, result.project_finish)
        self.assertEqual(result.wbs_summaries["development"].activity_count, 13)
        self.assertEqual(result.wbs_summaries["development"].milestone_count, 2)

    def test_workspace_startup_reopens_persisted_project(self) -> None:
        with TemporaryDirectory() as directory:
            database = Path(directory) / "scheduler.sqlite"
            seeded, _, _ = prepare_workspace(database)
            revised = ProjectSnapshot(
                id=seeded.id,
                name="Revised BiblionOCR plan",
                project_start=seeded.project_start,
                tasks=(Task("release", "Release", 2),),
            )
            with SchedulerStore(database) as store:
                store.save_project(revised)

            reopened, result, baseline = prepare_workspace(database)

        self.assertEqual(reopened, revised)
        self.assertEqual(result.tasks["release"].task.duration_days, 2)
        self.assertIsNone(baseline)


if __name__ == "__main__":
    unittest.main()
