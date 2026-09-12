import os
import unittest
from dataclasses import replace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QCloseEvent, QImage, QPainter
from PyQt5.QtWidgets import QApplication, QDialog, QListWidget, QMenu, QMessageBox, QTabWidget, QTextBrowser, QToolBar, QTreeWidgetItemIterator

from biblion_scheduler import Dependency, DependencyType, DurationUnit, PlanEditor, ProjectSnapshot, Task, WBSElement, WorkflowReconciliationStatus
from biblion_scheduler.__main__ import prepare_workspace, save_workspace, workflow_governance_callbacks
from biblion_scheduler.fixtures import biblionocr_development_plan
from biblion_scheduler.gui import (
    COMPLETE_COLOR,
    DAY_WIDTH,
    GanttCanvas,
    PLANNED_TRACK_COLOR,
    ScheduleWorkspace,
    SchedulerHelpDialog,
    TaskEditorDialog,
    WBSElementDialog,
    relationship_fields,
    timeline_rows,
)


class SchedulerHelpDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = QApplication.instance() or QApplication([])

    def test_topic_selection_and_search(self) -> None:
        dialog = SchedulerHelpDialog(topic_id="wbs")
        topics = dialog.findChild(QListWidget)
        browser = dialog.findChild(QTextBrowser)
        self.assertEqual(topics.count(), 10)
        self.assertEqual(topics.currentItem().text(), "Work Breakdown Structure")
        self.assertIn("Work Breakdown Structure", browser.toPlainText())

        dialog._filter_topics("negative float")

        self.assertEqual(
            [topics.item(row).text() for row in range(topics.count())],
            ["Constraints and Deadlines", "Critical Path and Float"],
        )

    def test_workspace_exposes_help_menu_toolbar_and_f1(self) -> None:
        project = biblionocr_development_plan()
        window = ScheduleWorkspace(project, PlanEditor(project).result)
        toolbar = window.findChild(QToolBar)
        help_actions = [action for action in toolbar.actions() if action.text() == "Help"]

        self.assertEqual(
            [action.text() for action in window.menuBar().actions()],
            ["&File", "&Edit", "&WBS", "&Help"],
        )
        self.assertEqual(len(help_actions), 1)
        self.assertEqual(help_actions[0].shortcut().toString(), "F1")
        file_actions = window.menuBar().actions()[0].menu().actions()
        self.assertEqual(
            [action.text().replace("&", "") for action in file_actions],
            ["New WBS...", "", "Save", "Save As..."],
        )
        self.assertEqual(file_actions[0].shortcut().toString(), "Ctrl+N")
        self.assertEqual(file_actions[2].shortcut().toString(), "Ctrl+S")
        self.assertEqual(file_actions[3].shortcut().toString(), "Ctrl+Shift+S")

        window.show_help("saving-baselines")

        self.assertIsNotNone(window._help_dialog)
        self.assertIn("Saving and Baselines", window._help_dialog._browser.toPlainText())

    def test_save_as_becomes_active_target_for_subsequent_wbs_saves(self) -> None:
        project = biblionocr_development_plan()
        with TemporaryDirectory() as directory:
            original_database = Path(directory) / "original.sqlite"
            selected_database = Path(directory) / "session-copy"
            window = ScheduleWorkspace(
                project,
                PlanEditor(project).result,
                save_callback=lambda revised, result: save_workspace(original_database, revised, result),
                save_as_callback=save_workspace,
                save_path=original_database,
            )
            scanner = next(element for element in project.wbs_elements if element.id == "scanner")
            window._editor.replace_wbs_element(replace(scanner, name="Saved As Scanner"))
            with patch(
                "biblion_scheduler.gui.QFileDialog.getSaveFileName",
                return_value=(str(selected_database), "SQLite databases (*.sqlite *.db)"),
            ):
                window._save_as()

            self.assertEqual(window._save_path, selected_database.with_suffix(".sqlite"))
            revised = next(element for element in window._editor.project.wbs_elements if element.id == "scanner")
            window._editor.replace_wbs_element(replace(revised, name="Saved Again Scanner"))
            window._save()
            reopened, _, _ = prepare_workspace(selected_database.with_suffix(".sqlite"))

        saved_scanner = next(element for element in reopened.wbs_elements if element.id == "scanner")
        self.assertEqual(saved_scanner.name, "Saved Again Scanner")

    def test_new_wbs_creates_blank_active_session_that_can_be_saved_and_reopened(self) -> None:
        project = biblionocr_development_plan()
        with TemporaryDirectory() as directory:
            database = Path(directory) / "from-scratch.sqlite"
            window = ScheduleWorkspace(
                project,
                PlanEditor(project).result,
                save_as_callback=save_workspace,
            )
            blank = ProjectSnapshot(
                "from-scratch",
                "From Scratch",
                date(2026, 9, 14),
                (),
            )
            with (
                patch("biblion_scheduler.gui.NewWBSDialog") as dialog_class,
                patch(
                    "biblion_scheduler.gui.QFileDialog.getSaveFileName",
                    return_value=(str(database), "SQLite databases (*.sqlite *.db)"),
                ),
            ):
                dialog_class.return_value.exec_.return_value = QDialog.Accepted
                dialog_class.return_value.project.return_value = blank
                window._new_wbs()

            self.assertEqual(window._editor.project, blank)
            self.assertEqual(window._wbs_tree.topLevelItemCount(), 0)
            self.assertEqual(window.windowTitle(), "Biblion Scheduler — From Scratch")
            window._editor.add_wbs_element(WBSElement("root", "1", "Root"))
            window._save()
            reopened, _, _ = prepare_workspace(database, "from-scratch")

        self.assertEqual(reopened.wbs_elements, (WBSElement("root", "1", "Root"),))
        self.assertEqual(reopened.tasks, ())

    def test_new_wbs_cancel_preserves_unsaved_current_session(self) -> None:
        project = biblionocr_development_plan()
        window = ScheduleWorkspace(project, PlanEditor(project).result, save_as_callback=save_workspace)
        window._editor.replace_wbs_element(replace(project.wbs_elements[0], name="Unsaved Name"))

        with (
            patch.object(QMessageBox, "warning", return_value=QMessageBox.Cancel),
            patch("biblion_scheduler.gui.NewWBSDialog") as dialog_class,
        ):
            window._new_wbs()

        self.assertEqual(window._editor.project.wbs_elements[0].name, "Unsaved Name")
        dialog_class.assert_not_called()

    def test_close_cancel_keeps_unsaved_wbs_open(self) -> None:
        project = biblionocr_development_plan()
        saved_projects = []
        window = ScheduleWorkspace(
            project,
            PlanEditor(project).result,
            save_callback=lambda revised, _result: saved_projects.append(revised),
        )
        window._editor.replace_wbs_element(replace(project.wbs_elements[0], name="Unsaved Name"))
        event = QCloseEvent()

        with patch.object(QMessageBox, "warning", return_value=QMessageBox.Cancel):
            window.closeEvent(event)

        self.assertFalse(event.isAccepted())
        self.assertEqual(saved_projects, [])

    def test_close_save_persists_unsaved_wbs_before_accepting(self) -> None:
        project = biblionocr_development_plan()
        saved_projects = []
        window = ScheduleWorkspace(
            project,
            PlanEditor(project).result,
            save_callback=lambda revised, _result: saved_projects.append(revised),
        )
        window._editor.replace_wbs_element(replace(project.wbs_elements[0], name="Saved On Close"))
        event = QCloseEvent()

        with patch.object(QMessageBox, "warning", return_value=QMessageBox.Save):
            window.closeEvent(event)

        self.assertTrue(event.isAccepted())
        self.assertEqual(saved_projects[0].wbs_elements[0].name, "Saved On Close")
        self.assertEqual(window._saved_project, window._editor.project)

    def test_close_save_failure_keeps_unsaved_wbs_open(self) -> None:
        project = biblionocr_development_plan()

        def fail_save(_project: ProjectSnapshot, _result: object) -> None:
            raise OSError("database unavailable")

        window = ScheduleWorkspace(
            project,
            PlanEditor(project).result,
            save_callback=fail_save,
        )
        window._editor.replace_wbs_element(replace(project.wbs_elements[0], name="Unsaved Name"))
        event = QCloseEvent()

        with (
            patch.object(QMessageBox, "warning", return_value=QMessageBox.Save),
            patch.object(QMessageBox, "critical"),
        ):
            window.closeEvent(event)

        self.assertFalse(event.isAccepted())
        self.assertNotEqual(window._saved_project, window._editor.project)

    def test_workflow_governance_tab_reconciles_real_ods_without_creating_dependencies(self) -> None:
        with TemporaryDirectory() as directory:
            database = Path(directory) / "scheduler.sqlite"
            project, result, baseline = prepare_workspace(database)
            callbacks = workflow_governance_callbacks(database, project.id)
            window = ScheduleWorkspace(project, result, baseline, workflow_callbacks=callbacks)
            tabs = window.findChild(QTabWidget)
            governance = tabs.widget(2)

            governance._revision.setText("ui-review-r1")
            governance._import_source()

            self.assertEqual(tabs.tabText(2), "Workflow Governance")
            self.assertEqual(governance._records.rowCount(), 8)
            self.assertEqual(governance._records.horizontalHeaderItem(1).text(), "WBS")
            self.assertEqual(governance._records.item(0, 1).text(), "")
            governance._records.selectRow(0)
            self.assertTrue(governance._approve.isEnabled())
            governance._approve_selected()
            governance._records.selectRow(0)
            self.assertEqual(governance._records.item(0, 0).text(), "approved")
            self.assertTrue(governance._map.isEnabled())
            selected_record = governance._selected_record()
            expected_name = selected_record.payload["milestone_name"]
            expected_sequence = selected_record.payload["sequence"]
            self.assertEqual(governance._mapping_name.text(), expected_name)
            self.assertEqual(governance._mapping_sequence.text(), expected_sequence)
            self.assertEqual(governance._parent_wbs.count(), len(project.wbs_elements))
            self.assertEqual(governance._parent_wbs.currentData(), "development")
            self.assertEqual(governance._next_wbs_code.text(), "Next WBS: 1.5")
            with patch.object(QMessageBox, "information") as information:
                governance._map_selected()
            information.assert_called_once()
            self.assertEqual(information.call_args.args[1], "Workflow Mapped")
            self.assertIn(f"Milestone: {expected_name}", information.call_args.args[2])
            self.assertIn(f"Activity: {expected_name}", information.call_args.args[2])
            self.assertIn("WBS: 1.5", information.call_args.args[2])
            self.assertIn("Role: Informational", information.call_args.args[2])
            self.application.processEvents()
            tabs = window.centralWidget().findChild(QTabWidget)
            governance = tabs.widget(2)
            self.assertEqual(governance._records.item(0, 1).text(), "1.5")
            governance._records.selectRow(1)
            governance._ignore_selected()

            state = callbacks.load()
            reopened, _, _ = prepare_workspace(database)

        self.assertEqual(len(state.mappings), 1)
        self.assertEqual(
            next(record.status for record in state.records if record.source_row == 3),
            WorkflowReconciliationStatus.IGNORED,
        )
        self.assertEqual(reopened.dependencies, project.dependencies)
        mapped_activity = next(task for task in reopened.tasks if task.id == "architecture")
        self.assertEqual(mapped_activity.wbs_id, "development")
        self.assertEqual(mapped_activity.wbs_code, "1.5")
        self.assertEqual(mapped_activity.name, expected_name)
        self.assertEqual(mapped_activity.sequence, expected_sequence)
        wbs_iterator = QTreeWidgetItemIterator(window._wbs_tree)
        while wbs_iterator.value() and wbs_iterator.value().data(0, Qt.UserRole) != "development":
            wbs_iterator += 1
        self.assertIn(expected_sequence, wbs_iterator.value().text(3).split(", "))
        schedule_row = next(
            row for row in range(window._table.rowCount())
            if window._table.item(row, 0).data(Qt.UserRole) == ("task", "architecture")
        )
        self.assertEqual(window._table.item(schedule_row, 1).text().strip(), expected_name)
        self.assertEqual(window._table.item(schedule_row, 3).text(), expected_sequence)

    def test_workspace_adds_edits_and_deletes_wbs_summary_items(self) -> None:
        project = biblionocr_development_plan()
        window = ScheduleWorkspace(project, PlanEditor(project).result)
        with patch("biblion_scheduler.gui.WBSElementDialog") as dialog_class:
            dialog_class.return_value.exec_.return_value = QDialog.Accepted
            dialog_class.return_value.wbs_element.return_value = WBSElement(
                "reader", "1.3.2", "MyReader", "workflows"
            )
            window._add_wbs_element()
        self.assertEqual(window._editor.project.wbs_elements[-1].name, "MyReader")

        iterator = QTreeWidgetItemIterator(window._wbs_tree)
        while iterator.value() and iterator.value().data(0, Qt.UserRole) != "reader":
            iterator += 1
        window._wbs_tree.setCurrentItem(iterator.value())
        with patch("biblion_scheduler.gui.WBSElementDialog") as dialog_class:
            dialog_class.return_value.exec_.return_value = QDialog.Accepted
            dialog_class.return_value.wbs_element.return_value = WBSElement(
                "reader", "1.3.2", "MyReader Workflow", "workflows"
            )
            window._edit_selected_wbs_element()
        self.assertEqual(window._editor.project.wbs_elements[-1].name, "MyReader Workflow")

        iterator = QTreeWidgetItemIterator(window._wbs_tree)
        while iterator.value() and iterator.value().data(0, Qt.UserRole) != "reader":
            iterator += 1
        window._wbs_tree.setCurrentItem(iterator.value())
        with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
            window._delete_selected_wbs_element()
        self.assertNotIn("reader", {element.id for element in window._editor.project.wbs_elements})

    def test_workspace_inserts_wbs_above_and_renumbers_following_branches(self) -> None:
        project = biblionocr_development_plan()
        window = ScheduleWorkspace(project, PlanEditor(project).result)
        iterator = QTreeWidgetItemIterator(window._wbs_tree)
        while iterator.value() and iterator.value().data(0, Qt.UserRole) != "core":
            iterator += 1
        window._wbs_tree.setCurrentItem(iterator.value())
        window._selection_source = "wbs"

        with patch("biblion_scheduler.gui.WBSElementDialog") as dialog_class:
            dialog_class.return_value.exec_.return_value = QDialog.Accepted
            dialog_class.return_value.wbs_element.return_value = WBSElement(
                "planning", "1.2", "Planning", "development"
            )
            window._add_wbs_element("above")

        self.assertEqual(dialog_class.call_args.kwargs["initial_code"], "1.2")
        self.assertEqual(dialog_class.call_args.kwargs["initial_parent_id"], "development")
        codes = {element.id: element.code for element in window._editor.project.wbs_elements}
        self.assertEqual(codes["planning"], "1.2")
        self.assertEqual(codes["core"], "1.3")
        self.assertEqual(codes["workflows"], "1.4")
        self.assertEqual(codes["scanner"], "1.4.1")
        self.assertEqual(codes["release"], "1.5")

    def test_wbs_sibling_insertion_codes_cover_above_and_below(self) -> None:
        self.assertEqual(ScheduleWorkspace._sibling_insertion_code("1.3.2", "above"), "1.3.2")
        self.assertEqual(ScheduleWorkspace._sibling_insertion_code("1.3.2", "below"), "1.3.3")
        self.assertEqual(ScheduleWorkspace._sibling_insertion_code("4", "below"), "5")

    def test_workspace_adds_activity_to_selected_wbs_summary(self) -> None:
        project = biblionocr_development_plan()
        window = ScheduleWorkspace(project, PlanEditor(project).result)
        iterator = QTreeWidgetItemIterator(window._wbs_tree)
        while iterator.value() and iterator.value().data(0, Qt.UserRole) != "scanner":
            iterator += 1
        window._wbs_tree.setCurrentItem(iterator.value())
        window._selection_source = "wbs"

        with patch("biblion_scheduler.gui.TaskEditorDialog") as dialog_class:
            dialog_class.return_value.exec_.return_value = QDialog.Accepted
            dialog_class.return_value.edited_task.return_value = Task(
                "scanner-review", "Review scanner workflow", 3, "scanner"
            )
            dialog_class.return_value.edited_relationships.return_value = (
                Dependency("scanner-licensing", "scanner-review"),
            )
            window._add_activity()

        added = window._editor.project.tasks[-1]
        self.assertEqual(added.id, "scanner-review")
        self.assertEqual(added.wbs_id, "scanner")
        self.assertIn("Review scanner workflow", [task.name for task in window._editor.project.tasks])
        self.assertIn(
            Dependency("scanner-licensing", "scanner-review"),
            window._editor.project.dependencies,
        )

    def test_workspace_copies_then_cuts_and_pastes_wbs_elements(self) -> None:
        project = biblionocr_development_plan()
        window = ScheduleWorkspace(project, PlanEditor(project).result)

        def select_element(element_id: str) -> None:
            iterator = QTreeWidgetItemIterator(window._wbs_tree)
            while iterator.value() and iterator.value().data(0, Qt.UserRole) != element_id:
                iterator += 1
            window._wbs_tree.setCurrentItem(iterator.value())

        select_element("scanner")
        window._copy_selected_wbs_element()
        window._paste_wbs_element()
        copied = window._editor.project.wbs_elements[-1]
        self.assertEqual(copied.parent_id, "scanner")
        self.assertEqual(copied.name, "MyScanner Standalone Copy")
        self.assertNotEqual(copied.id, "scanner")

        select_element(copied.id)
        window._cut_selected_wbs_element()
        select_element("release")
        window._paste_wbs_element()
        moved = next(element for element in window._editor.project.wbs_elements if element.id == copied.id)
        self.assertEqual(moved.parent_id, "release")
        self.assertIsNone(window._summary_clipboard)

    def test_context_commands_are_scoped_to_wbs_elements(self) -> None:
        project = biblionocr_development_plan()
        window = ScheduleWorkspace(project, PlanEditor(project).result)

        self.assertEqual(window._copy_summary_action.text(), "Copy WBS Element")
        self.assertEqual(window._cut_summary_action.text(), "Cut WBS Element")
        self.assertEqual(window._paste_summary_action.text(), "Paste WBS Element")
        self.assertEqual(window._undo_action.text().replace("&", ""), "Undo")
        self.assertEqual(window._redo_action.text().replace("&", ""), "Redo")
        self.assertEqual(window._delete_wbs_action.text(), "Delete WBS Element")

    def test_wbs_context_menu_includes_save_commands(self) -> None:
        project = biblionocr_development_plan()
        window = ScheduleWorkspace(
            project,
            PlanEditor(project).result,
            save_callback=lambda _project, _result: None,
            save_as_callback=lambda _path, _project, _result: None,
        )
        captured_menus = []
        with patch.object(QMenu, "exec_", new=lambda menu, _position: captured_menus.append(menu)):
            window._show_wbs_context_menu(window._wbs_tree, QPoint(1, 1))
        context_menu = captured_menus[0]

        self.assertIn("&Save", [action.text() for action in context_menu.actions()])
        self.assertIn("Save &As...", [action.text() for action in context_menu.actions()])

    def test_wbs_tree_defaults_to_natural_wbs_code_sorting(self) -> None:
        project = biblionocr_development_plan()
        project = replace(
            project,
            wbs_elements=project.wbs_elements + (
                WBSElement("scanner-ten", "1.3.1.10", "Tenth", "scanner"),
                WBSElement("scanner-two", "1.3.1.2", "Second", "scanner"),
            ),
        )
        window = ScheduleWorkspace(project, PlanEditor(project).result)
        iterator = QTreeWidgetItemIterator(window._wbs_tree)
        while iterator.value() and iterator.value().data(0, Qt.UserRole) != "scanner":
            iterator += 1
        scanner = iterator.value()

        self.assertEqual(window._wbs_tree.sortColumn(), 0)
        self.assertEqual(
            [scanner.child(index).text(0) for index in range(scanner.childCount())],
            ["1.3.1.2", "1.3.1.10"],
        )

    def test_wbs_filter_keeps_matching_descendant_ancestors_visible(self) -> None:
        project = biblionocr_development_plan()
        window = ScheduleWorkspace(project, PlanEditor(project).result)
        window._wbs_filters[1] = "myscanner"
        window._apply_wbs_filters(window._wbs_tree)
        visibility: dict[str, bool] = {}
        iterator = QTreeWidgetItemIterator(window._wbs_tree)
        while iterator.value():
            visibility[iterator.value().data(0, Qt.UserRole)] = not iterator.value().isHidden()
            iterator += 1

        self.assertTrue(visibility["development"])
        self.assertTrue(visibility["workflows"])
        self.assertTrue(visibility["scanner"])
        self.assertFalse(visibility["architecture"])
        self.assertIn("•", window._wbs_tree.headerItem().text(1))

    def test_wbs_fill_down_is_one_undoable_edit(self) -> None:
        project = biblionocr_development_plan()
        window = ScheduleWorkspace(project, PlanEditor(project).result)
        selected = {}
        iterator = QTreeWidgetItemIterator(window._wbs_tree)
        while iterator.value():
            element_id = iterator.value().data(0, Qt.UserRole)
            if element_id in {"scanner", "release"}:
                selected[element_id] = iterator.value()
            iterator += 1
        selected["scanner"].setSelected(True)
        selected["release"].setSelected(True)

        window._fill_down_wbs_column(1)

        release = next(element for element in window._editor.project.wbs_elements if element.id == "release")
        self.assertEqual(release.name, "MyScanner Standalone")
        window._editor.undo()
        restored = next(element for element in window._editor.project.wbs_elements if element.id == "release")
        self.assertEqual(restored.name, "Verification and Release")

    def test_activity_editor_preserves_sequence_and_completion_values(self) -> None:
        project = biblionocr_development_plan()
        task = Task(
            "tracked", "Tracked activity", 4, "scanner", 45, 30, "SCAN",
            date(2026, 9, 14), date(2026, 9, 17), date(2026, 9, 15), None,
        )
        dialog = TaskEditorDialog(task, project)

        self.assertEqual(dialog.edited_task(), task)
        self.assertEqual(dialog._duration.value(), 4)
        self.assertEqual(dialog._actual_duration.value(), -1)
        dialog._actual_finish.setText("2026-09-18")
        self.assertEqual(dialog._actual_duration.value(), 4)
        dialog._duration_unit.setCurrentIndex(dialog._duration_unit.findData(DurationUnit.HOURS))
        self.assertEqual(dialog._duration.value(), 32)
        self.assertEqual(dialog._actual_duration.value(), 32)
        self.assertEqual(dialog.edited_task().duration_unit, DurationUnit.HOURS)

    def test_activity_editor_edits_relationship_type_and_lead_lag(self) -> None:
        project = biblionocr_development_plan()
        task = next(task for task in project.tasks if task.id == "core-infrastructure")
        dialog = TaskEditorDialog(task, project)

        self.assertEqual(
            dialog.edited_dependencies(),
            (Dependency("architecture-frozen", "core-infrastructure"),),
        )
        relationship = dialog._relationship_table.cellWidget(0, 1)
        lag = dialog._relationship_table.cellWidget(0, 2)
        relationship.setCurrentIndex(relationship.findData(DependencyType.FINISH_TO_FINISH))
        lag.setValue(-2)
        successor_relationship = dialog._successor_table.cellWidget(0, 1)
        successor_lag = dialog._successor_table.cellWidget(0, 2)
        successor_relationship.setCurrentIndex(
            successor_relationship.findData(DependencyType.START_TO_START)
        )
        successor_lag.setValue(3)

        self.assertEqual(
            dialog.edited_dependencies(),
            (Dependency("architecture-frozen", "core-infrastructure", DependencyType.FINISH_TO_FINISH, -2),),
        )
        self.assertEqual(
            dialog.edited_relationships(),
            (
                Dependency("architecture-frozen", "core-infrastructure", DependencyType.FINISH_TO_FINISH, -2),
                Dependency("core-infrastructure", "module-standardization", DependencyType.START_TO_START, 3),
            ),
        )

    def test_wbs_editor_preserves_planned_date_overrides(self) -> None:
        project = biblionocr_development_plan()
        element = WBSElement(
            "dated", "2", "Dated", planned_start=date(2026, 10, 1), planned_finish=date(2026, 10, 9),
            duration_unit=DurationUnit.HOURS,
        )
        dialog = WBSElementDialog(project, element)

        self.assertEqual(dialog.wbs_element(), element)

    def test_gantt_uses_clear_tracks_and_proportional_green_progress(self) -> None:
        project = ProjectSnapshot(
            id="actual-colors",
            name="Actual colors",
            project_start=date(2026, 9, 7),
            wbs_elements=(WBSElement("root", "1", "Root"),),
            tasks=(
                Task(
                    "started", "Started", 5, "root", 40,
                    planned_start=date(2026, 9, 7), planned_finish=date(2026, 9, 11),
                    actual_start=date(2026, 9, 7),
                ),
                Task(
                    "complete", "Complete", 5, "root", 20,
                    planned_start=date(2026, 9, 14), planned_finish=date(2026, 9, 18),
                    actual_start=date(2026, 9, 14), actual_finish=date(2026, 9, 18),
                ),
            ),
        )
        editor = PlanEditor(project)
        canvas = GanttCanvas(editor.project, editor.result)
        image = QImage(canvas.minimumSize(), QImage.Format_ARGB32)
        painter = QPainter(image)
        canvas.render(painter)
        painter.end()
        colors = {
            image.pixelColor(x, y).name()
            for x in range(image.width())
            for y in range(image.height())
        }

        self.assertIn(COMPLETE_COLOR.name(), colors)
        self.assertIn(PLANNED_TRACK_COLOR.name(), colors)
        self.assertEqual(GanttCanvas._progress_width(100, 40), 40)
        self.assertEqual(GanttCanvas._progress_width(100, 100), 100)
        self.assertEqual(GanttCanvas._progress_width(100, 0), 0)

        started_y = 38 + 30 + 12
        self.assertEqual(image.pixelColor(10, started_y).name(), COMPLETE_COLOR.name())
        self.assertEqual(image.pixelColor(70, started_y).name(), PLANNED_TRACK_COLOR.name())

    def test_gantt_canvas_reserves_space_and_renders_bar_labels(self) -> None:
        project = biblionocr_development_plan()
        result = PlanEditor(project).result
        canvas = GanttCanvas(project, result)
        date_grid_width = ((canvas._last_date - canvas._first_date).days + 1) * DAY_WIDTH
        image = QImage(canvas.minimumSize(), QImage.Format_ARGB32)
        painter = QPainter(image)
        canvas.render(painter)
        painter.end()

        self.assertGreater(canvas.minimumWidth(), date_grid_width)
        self.assertFalse(image.isNull())

    def test_timeline_preserves_wbs_hierarchy_and_assigns_three_logical_levels(self) -> None:
        rows = timeline_rows(biblionocr_development_plan())

        self.assertEqual(rows[0].level, 1)
        self.assertTrue(all(row.level == 2 for row in rows if row.kind == "summary" and row.depth > 0))
        self.assertTrue(all(row.level == 3 for row in rows if row.kind == "task"))

    def test_activity_and_summary_rows_expose_dependency_relationships(self) -> None:
        project = biblionocr_development_plan()
        rows = timeline_rows(project)
        activity_row = next(row for row in rows if row.kind == "task" and row.id == "architecture")
        wbs_row = next(row for row in rows if row.kind == "summary" and row.id == "architecture")

        activity = relationship_fields(project, activity_row)
        self.assertEqual(activity.predecessors, "Project Start")
        self.assertIn("Compute engine architecture frozen", activity.successors)
        self.assertIn(" FS ", activity.logic)

        wbs_relationships = relationship_fields(project, wbs_row)
        self.assertEqual(wbs_relationships.predecessors, "Project Start")
        self.assertIn("Core infrastructure", wbs_relationships.successors)

    def test_gantt_dependency_anchors_cover_all_logic_types(self) -> None:
        project = biblionocr_development_plan()
        canvas = GanttCanvas(project, PlanEditor(project).result)
        predecessor = canvas._result.tasks["architecture"]
        successor = canvas._result.tasks["architecture-frozen"]

        expected = {
            DependencyType.FINISH_TO_START: (
                canvas._x_for_date(predecessor.finish) + DAY_WIDTH - 2,
                canvas._x_for_date(successor.start) + 2,
            ),
            DependencyType.FINISH_TO_FINISH: (
                canvas._x_for_date(predecessor.finish) + DAY_WIDTH - 2,
                canvas._x_for_date(successor.finish) + DAY_WIDTH - 2,
            ),
            DependencyType.START_TO_FINISH: (
                canvas._x_for_date(predecessor.start) + 2,
                canvas._x_for_date(successor.finish) + DAY_WIDTH - 2,
            ),
            DependencyType.START_TO_START: (
                canvas._x_for_date(predecessor.start) + 2,
                canvas._x_for_date(successor.start) + 2,
            ),
        }
        for dependency_type, coordinates in expected.items():
            edge = Dependency("architecture", "architecture-frozen", dependency_type)
            self.assertEqual(canvas._dependency_x_coordinates(edge), coordinates)

    def test_schedule_grid_aligns_summary_rows_and_dispatches_summary_edit(self) -> None:
        project = biblionocr_development_plan()
        window = ScheduleWorkspace(project, PlanEditor(project).result)
        table = window._table

        self.assertEqual(table.rowCount(), len(project.wbs_elements) + len(project.tasks))
        self.assertEqual(table.item(0, 2).text(), "Level 1 - Project/Phase")
        self.assertEqual(table.item(0, 0).data(Qt.UserRole), ("summary", project.wbs_elements[0].id))
        self.assertEqual(table.horizontalHeaderItem(8).text(), "Units")
        self.assertEqual(table.horizontalHeaderItem(11).text(), "Planned Start")
        self.assertEqual(table.horizontalHeaderItem(14).text(), "Actual Start")

        table.selectRow(0)
        with patch.object(window, "_edit_wbs_element") as edit_wbs_element:
            window._edit_selected_task()
        edit_wbs_element.assert_called_once_with(project.wbs_elements[0])

    def test_schedule_defaults_to_natural_wbs_order_and_matches_gantt(self) -> None:
        project = ProjectSnapshot(
            id="schedule-wbs-order",
            name="Schedule WBS order",
            project_start=date(2026, 9, 14),
            tasks=(
                Task("tenth-task", "Tenth task", 1, "tenth"),
                Task("second-task", "Second task", 1, "second"),
            ),
            wbs_elements=(
                WBSElement("root", "1", "Root"),
                WBSElement("tenth", "1.10", "Tenth", "root"),
                WBSElement("second", "1.2", "Second", "root"),
            ),
        )
        window = ScheduleWorkspace(project, PlanEditor(project).result)
        table_identities = [
            window._table.item(row, 0).data(Qt.UserRole)
            for row in range(window._table.rowCount())
        ]

        self.assertEqual(
            table_identities,
            [
                ("summary", "root"),
                ("summary", "second"),
                ("task", "second-task"),
                ("summary", "tenth"),
                ("task", "tenth-task"),
            ],
        )
        self.assertEqual(
            [(row.kind, row.id) for row in window._gantt_canvas._rows],
            table_identities,
        )
        self.assertEqual(window._table.horizontalHeader().sortIndicatorSection(), 0)
        self.assertEqual(window._table.horizontalHeader().sortIndicatorOrder(), Qt.AscendingOrder)

    def test_schedule_numeric_sort_reorders_grid_and_gantt_together(self) -> None:
        project = ProjectSnapshot(
            id="schedule-duration-sort",
            name="Schedule duration sort",
            project_start=date(2026, 9, 14),
            tasks=(
                Task("ten", "Ten", 10),
                Task("two", "Two", 2),
                Task("one", "One", 1),
            ),
        )
        window = ScheduleWorkspace(project, PlanEditor(project).result)

        window._sort_schedule(7)

        table_ids = [
            window._table.item(row, 0).data(Qt.UserRole)[1]
            for row in range(window._table.rowCount())
        ]
        self.assertEqual(table_ids, ["one", "two", "ten"])
        self.assertEqual([row.id for row in window._gantt_canvas._rows], table_ids)


if __name__ == "__main__":
    unittest.main()
