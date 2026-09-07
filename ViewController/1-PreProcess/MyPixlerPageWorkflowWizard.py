from __future__ import annotations

import os

from PyQt5 import QtCore as qtc
from PyQt5 import QtWidgets as qtw

from Core.page_workflow import load_page_workflow
from Core.project_tracking import ProjectWorkflowTracker
from MyPixlerPageWorkflowWizardUI import Ui_MyPixlerPageWorkflowWizardDialog


DESIGNER_STEP_KEYS = (
    ("FrontSection", "SSHF", "src_pages_front_matter_staged", "actionstage_pdf"),
    ("FrontSection", "ES2F", "src_pages_front_matter_extracted", "actionextract_pdf"),
    ("FrontSection", "EF4T", "front_matter_pages_extracted_for_tif", "actionpdf_for_tiff"),
    ("FrontSection", "4T2T", "front_matter_pages_converted_to_tif", "actionpdf_to_tiff"),
    ("FrontSection", "2T2I", "front_matter_tif_pages_indexed", "actiontiff_to_mono"),
    ("FrontSection", "MI2C", "front_matter_tif_pages_clipped", "clip"),
    ("FrontSection", "MC2E", "front_matter_tif_pages_erased", "eraser"),
    ("MiddleSections", "SSHM", "src_pages_middle_matter_staged", "actionstage_pdf"),
    ("MiddleSections", "ES2M", "src_pages_middle_matter_extracted", "actionextract_pdf"),
    ("MiddleSections", "EM2B", "middle_matter_pages_extracted_to_books", "actionextract_pdf"),
    ("MiddleSections", "EB4T", "middle_matter_pages_extracted_for_tif", "actionpdf_for_tiff"),
    ("MiddleSections", "4T2T", "middle_matter_pages_converted_to_tif", "actionpdf_to_tiff"),
    ("MiddleSections", "2T2I", "middle_matter_tif_pages_indexed", "actiontiff_to_mono"),
    ("MiddleSections", "MI2C", "middle_matter_tif_pages_clipped", "clip"),
    ("MiddleSections", "MC2E", "middle_matter_tif_pages_erased", "eraser"),
    ("VerseSections", "SSHV", "src_pages_verses_staged", "actionstage_pdf"),
    ("VerseSections", "ES2V", "src_pages_verses_extracted", "actionextract_pdf"),
    ("VerseSections", "EV2B", "verse_pages_extracted_to_books", "actionextract_pdf"),
    ("VerseSections", "EB4T", "verse_books_pages_extracted_for_tif", "actionpdf_for_tiff"),
    ("VerseSections", "4T2T", "verse_books_pages_converted_to_tif", "actionpdf_to_tiff"),
    ("VerseSections", "2T2I", "verse_books_tif_pages_indexed", "actiontiff_to_mono"),
    ("VerseSections", "MI2C", "back_matter_tif_pages_clipped", "clip"),
    ("VerseSections", "MC2E", "verse_books_tif_pages_erased", "eraser"),
    ("BackSection", "SSHB", "src_pages_back_matter_staged", "actionstage_pdf"),
    ("BackSection", "ES2B", "src_pages_back_matter_extracted", "actionextract_pdf"),
    ("BackSection", "EB4T", "back_matter_pages_extracted_for_tif", "actionpdf_for_tiff"),
    ("BackSection", "4T2T", "back_matter_pages_converted_to_tif", "actionpdf_to_tiff"),
    ("BackSection", "2T2I", "back_matter_tif_pages_indexed", "actiontiff_to_mono"),
    ("BackSection", "MI2C", "back_matter_tif_pages_clipped", "clip"),
    ("BackSection", "MC2E", "back_matter_tif_pages_erased", "eraser"),
)


def _normalize_section(value: str) -> str:
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
        "scriptural": "verse",
        "verse": "verse",
        "versesection": "verse",
        "versesections": "verse",
        "back": "back",
        "backmatter": "back",
        "backsection": "back",
    }
    return aliases.get(compact, compact)


class MyPixlerPageWorkflowWizardDialog(qtw.QDialog):
    stepCompleted = qtc.pyqtSignal(str)

    def __init__(self, pixler_window, parent=None):
        super().__init__(parent or pixler_window)
        self.pixler_window = pixler_window
        self.ui = Ui_MyPixlerPageWorkflowWizardDialog()
        self.ui.setupUi(self)
        self.workflow_tracker = getattr(pixler_window, "workflow_tracker", ProjectWorkflowTracker())
        self.project_root = self._active_project_root()
        self.page_number, self.source_section = self._active_page_context()
        self.steps = self._load_steps()
        self.applicable_indexes = [
            index
            for index, step in enumerate(self.steps)
            if _normalize_section(step.page_section) == _normalize_section(self.source_section)
        ]
        self._configure_pages()
        self._connect_signals()
        self.refresh_progress(select_next=True)

    def _active_project_root(self) -> str:
        project_root = str(getattr(self.pixler_window, "current_project_root", "") or "").strip()
        shared_root = getattr(self.pixler_window, "_shared_active_project_root", None)
        if not project_root and callable(shared_root):
            project_root = str(shared_root() or "").strip()
        return os.path.abspath(project_root) if project_root else ""

    def _active_page_context(self):
        if not self.project_root:
            return 1, "Front Matter"
        context = self.workflow_tracker._load_project_context(self.project_root)
        page_number = max(
            1,
            int(context.get("CurrentProjectPage", context.get("ProjectPageNumber", 1)) or 1),
        )
        return page_number, str(context.get("CurrentSourceSection", "Front Matter") or "Front Matter")

    def _load_steps(self):
        definition_root = self.pixler_window._workflow_definition_root()
        steps, _notes = load_page_workflow(definition_root)
        module_steps = [step for step in steps if step.module == "MyPixler"]
        loaded_keys = tuple(
            (step.page_section, step.sequence, step.milestone_name, step.method)
            for step in module_steps
        )
        if loaded_keys != DESIGNER_STEP_KEYS:
            raise RuntimeError(
                "MyPixler page workflow UI is out of sync with page_workflow.csv. "
                "Update MyPixlerPageWorkflowWizardUI.ui and DESIGNER_STEP_KEYS together."
            )
        if self.ui.step_stack.count() != len(module_steps):
            raise RuntimeError(
                f"MyPixler page workflow UI defines {self.ui.step_stack.count()} pages "
                f"for {len(module_steps)} worksheet steps."
            )
        return module_steps

    def _configure_pages(self) -> None:
        self.ui.context_label.setText(
            f"Page {self.page_number} | Source section: {self.source_section} | "
            f"{len(self.applicable_indexes)} MyPixler steps"
        )
        for index, step in enumerate(self.steps):
            summary = getattr(self.ui, f"step_{index + 1:02d}_summary_label")
            summary.setText(
                "\n".join(
                    (
                        f"Sequence: {step.sequence}",
                        f"Milestone: {step.milestone_name}",
                        f"Section: {step.page_section}",
                        f"Action: {step.method}",
                        f"Dialog: {step.dialog_ui or 'None'}",
                        "",
                        step.description,
                        "",
                        f"Source: {step.workflow_source or 'Interactive image'}",
                        f"Destination: {step.complete_destination or 'Interactive image'}",
                        f"Handshake: {step.workflow_handshake or 'None'}",
                    )
                )
            )
        self.ui.step_navigation.clear()
        for index in self.applicable_indexes:
            step = self.steps[index]
            item = qtw.QListWidgetItem()
            item.setData(qtc.Qt.UserRole, index)
            self.ui.step_navigation.addItem(item)

    def _connect_signals(self) -> None:
        self.ui.step_navigation.currentRowChanged.connect(self._show_navigation_row)
        self.ui.back_button.clicked.connect(lambda: self._move_navigation(-1))
        self.ui.next_button.clicked.connect(lambda: self._move_navigation(1))
        self.ui.run_step_button.clicked.connect(self.run_current_step)
        self.ui.close_button.clicked.connect(self.accept)

    def _completed_milestones(self) -> set[str]:
        if not self.project_root:
            return set()
        state = self.workflow_tracker.load_tracking_state(self.project_root)
        page_state = state.get("page_milestones", {}).get(str(self.page_number), {})
        if not isinstance(page_state, dict):
            return set()
        return {
            name
            for name, value in page_state.items()
            if isinstance(value, dict) and value.get("complete")
        }

    def _first_pending_index(self, completed: set[str]):
        return next(
            (
                index
                for index in self.applicable_indexes
                if self.steps[index].milestone_name not in completed
            ),
            None,
        )

    def refresh_progress(self, select_next=False) -> None:
        completed = self._completed_milestones()
        first_pending_index = self._first_pending_index(completed)
        completed_count = sum(
            self.steps[index].milestone_name in completed
            for index in self.applicable_indexes
        )
        total_count = len(self.applicable_indexes)
        progress = int(round((completed_count * 100) / total_count)) if total_count else 0
        self.ui.workflow_progress_bar.setValue(progress)

        pending_row = None
        for row, index in enumerate(self.applicable_indexes):
            step = self.steps[index]
            is_complete = step.milestone_name in completed
            prefix = "[Done]" if is_complete else "[Next]" if index == first_pending_index else "[Pending]"
            self.ui.step_navigation.item(row).setText(
                f"{prefix} {step.sequence}: {step.description}"
            )
            if index == first_pending_index:
                pending_row = row

        if total_count == 0:
            self.ui.step_status_label.setText(
                f"No MyPixler workflow rows match source section {self.source_section}."
            )
        elif first_pending_index is None:
            self.ui.step_status_label.setText(
                f"MyPixler workflow complete for page {self.page_number} ({self.source_section})."
            )
        else:
            step = self.steps[first_pending_index]
            self.ui.step_status_label.setText(
                f"Next required step: {step.sequence} - {step.description}"
            )

        if select_next and pending_row is not None:
            self.ui.step_navigation.setCurrentRow(pending_row)
        elif self.ui.step_navigation.currentRow() < 0 and total_count:
            self.ui.step_navigation.setCurrentRow(0)
        self._update_controls(first_pending_index)

    def _show_navigation_row(self, row: int) -> None:
        if row < 0 or row >= len(self.applicable_indexes):
            return
        self.ui.step_stack.setCurrentIndex(self.applicable_indexes[row])
        self._update_controls(self._first_pending_index(self._completed_milestones()))

    def _update_controls(self, first_pending_index) -> None:
        row = self.ui.step_navigation.currentRow()
        selected_index = self.applicable_indexes[row] if 0 <= row < len(self.applicable_indexes) else None
        self.ui.back_button.setEnabled(row > 0)
        self.ui.next_button.setEnabled(0 <= row < len(self.applicable_indexes) - 1)
        self.ui.run_step_button.setEnabled(
            bool(self.project_root)
            and selected_index is not None
            and selected_index == first_pending_index
        )
        if selected_index is not None:
            step = self.steps[selected_index]
            self.ui.run_step_button.setText(f"Run {step.sequence}")

    def _move_navigation(self, offset: int) -> None:
        target = self.ui.step_navigation.currentRow() + int(offset)
        if 0 <= target < self.ui.step_navigation.count():
            self.ui.step_navigation.setCurrentRow(target)

    def run_current_step(self) -> None:
        row = self.ui.step_navigation.currentRow()
        if row < 0 or row >= len(self.applicable_indexes):
            return
        index = self.applicable_indexes[row]
        completed_before = self._completed_milestones()
        if index != self._first_pending_index(completed_before):
            return

        step = self.steps[index]
        method = getattr(self.pixler_window, step.method, None)
        if not callable(method):
            qtw.QMessageBox.warning(
                self,
                "MyPixler Page Workflow",
                f"Method {step.method} is not available for sequence {step.sequence}.",
            )
            return

        self.ui.run_step_button.setEnabled(False)
        self.ui.step_status_label.setText(f"Running {step.sequence}: {step.description}")
        qtw.QApplication.processEvents()
        result = method()

        completed_after = self._completed_milestones()
        if result is True and step.milestone_name not in completed_after:
            self.workflow_tracker.record_page_milestone(
                self.project_root,
                self.page_number,
                step.milestone_name,
                module_name="MyPixler",
                details={"source": "MyPixlerPageWorkflowWizard"},
            )
            completed_after = self._completed_milestones()

        if step.milestone_name in completed_after:
            self.stepCompleted.emit(step.milestone_name)
            self.refresh_progress(select_next=True)
            refresh_status = getattr(self.pixler_window, "_refresh_project_status", None)
            if callable(refresh_status):
                refresh_status(self.project_root)
        else:
            self.ui.step_status_label.setText(
                f"{step.sequence} was not completed. Finish its dialog to advance the workflow."
            )
            self._update_controls(self._first_pending_index(completed_after))
