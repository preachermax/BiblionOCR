from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5 import QtWidgets as qtw

from Core.project_tracking import ProjectWorkflowTracker


ROOT_DIR = Path(__file__).resolve().parents[1]
MYPIXLER_DIR = ROOT_DIR / "ViewController" / "1-PreProcess"
if str(MYPIXLER_DIR) not in sys.path:
    sys.path.insert(0, str(MYPIXLER_DIR))

from MyPixlerPageWorkflowWizard import MyPixlerPageWorkflowWizardDialog
from MyPixlerPageWorkflowWizardUI import Ui_MyPixlerPageWorkflowWizardDialog


FRONT_COMPLETED_THROUGH_INDEXING = {
    "src_pages_front_matter_staged",
    "src_pages_front_matter_extracted",
    "front_matter_pages_extracted_for_tif",
    "front_matter_pages_converted_to_tif",
    "front_matter_tif_pages_indexed",
}


class TrackerStub:
    def __init__(self):
        self.completed = set(FRONT_COMPLETED_THROUGH_INDEXING)

    def _load_project_context(self, _project_root):
        return {"CurrentProjectPage": 1, "CurrentSourceSection": "Front Matter"}

    def load_tracking_state(self, _project_root):
        return {
            "page_milestones": {
                "1": {
                    name: {"complete": True}
                    for name in self.completed
                }
            }
        }

    def record_page_milestone(
        self,
        _project_root,
        _page_number,
        milestone_name,
        module_name=None,
        details=None,
    ):
        self.completed.add(milestone_name)
        return self.load_tracking_state(_project_root)


class PixlerWindowStub(qtw.QMainWindow):
    def __init__(self, project_root):
        super().__init__()
        self.current_project_root = str(project_root)
        self.workflow_tracker = TrackerStub()
        self.clip_calls = 0
        self.refreshed_project_root = ""

    def _workflow_definition_root(self):
        return str(ROOT_DIR)

    def _shared_active_project_root(self):
        return self.current_project_root

    def clip(self):
        self.clip_calls += 1
        return True

    def _refresh_project_status(self, project_root):
        self.refreshed_project_root = project_root


def test_generated_mypixler_workflow_ui_defines_every_worksheet_step() -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    shell = qtw.QDialog()
    ui = Ui_MyPixlerPageWorkflowWizardDialog()

    ui.setupUi(shell)

    assert ui.step_stack.count() == 30
    assert ui.workflow_step_01_page is not None
    assert ui.workflow_step_30_page is not None
    shell.close()
    app.processEvents()


def test_mypixler_wizard_records_success_and_advances_to_next_sequence(tmp_path) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    owner = PixlerWindowStub(tmp_path)
    dialog = MyPixlerPageWorkflowWizardDialog(owner)
    completed = []
    dialog.stepCompleted.connect(completed.append)

    assert dialog.ui.step_navigation.count() == 7
    assert dialog.ui.step_navigation.currentRow() == 5
    assert dialog.ui.step_stack.currentIndex() == 5
    assert dialog.ui.workflow_progress_bar.value() == 71
    assert dialog.ui.run_step_button.text() == "Run MI2C"
    assert dialog.ui.run_step_button.isEnabled()

    dialog.run_current_step()

    assert owner.clip_calls == 1
    assert completed == ["front_matter_tif_pages_clipped"]
    assert dialog.ui.step_navigation.currentRow() == 6
    assert dialog.ui.step_stack.currentIndex() == 6
    assert dialog.ui.workflow_progress_bar.value() == 86
    assert dialog.ui.run_step_button.text() == "Run MC2E"
    assert owner.refreshed_project_root == str(tmp_path)
    dialog.close()
    owner.close()
    app.processEvents()
