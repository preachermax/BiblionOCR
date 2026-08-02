import os

from PyQt5 import QtCore as qtc
from PyQt5 import QtWidgets as qtw
from PyQt5.QtCore import Qt

from Core.project_tracking import ProjectWorkflowTracker
from ProjectTrackingDialog import ProjectTrackingDialog
from SessionManager import SessionManager


class ProjectStatusController:
    DEFAULT_CANDIDATE_ATTRS = (
        "imgpath",
        "imgdir",
        "txtpath",
        "txtdir",
        "refimgpath",
        "refimgdir",
        "imagepath",
        "imagedir",
        "textpath",
        "textdir",
        "reftxtpath",
        "reftxtdir",
        "workflow",
        "session",
        "sourcefile",
        "crossref",
        "pagetextpath",
        "pagetextdir",
        "glyphboxgreekimgpath",
        "glyphboxgreekimgdir",
        "glyphboxlatinimgpath",
        "glyphboxlatinimgdir",
        "lineboximgpath",
        "lineboximgdir",
    )

    def __init__(
        self,
        window,
        module_name,
        session_manager=None,
        candidate_attrs=None,
        refresh_interval_ms=1000,
    ):
        self.window = window
        self.module_name = module_name
        self.session_manager = session_manager or SessionManager()
        self.candidate_attrs = tuple(candidate_attrs or ())
        self.workflow_tracker = ProjectWorkflowTracker(
            workspace_root=self._infer_workspace_root(self.session_manager)
        )

        if not hasattr(self.window, "current_project_root"):
            self.window.current_project_root = None
        if not hasattr(self.window, "current_project_name"):
            self.window.current_project_name = ""

        self._sync_timer = qtc.QTimer(self.window)
        self._sync_timer.timeout.connect(self.sync_active_project)

        self._init_widgets()
        self.refresh_status()
        self._sync_timer.start(refresh_interval_ms)

    def _infer_workspace_root(self, session_manager):
        base_dir = getattr(session_manager, "base_dir", "")
        if not base_dir:
            return None
        return os.path.normpath(
            os.path.join(base_dir, os.pardir, os.pardir, os.pardir, os.pardir)
        )

    def _init_widgets(self):
        self.project_name_status_label = qtw.QLabel("Project: none")
        self.project_name_status_label.setMinimumWidth(180)

        self.workflow_status_label = qtw.QLabel(
            f"{self.module_name} | Project 0/7 | Next: Project initialized"
        )
        self.workflow_status_label.setMinimumWidth(320)

        self.project_overall_status_bar = qtw.QProgressBar()
        self.project_overall_status_bar.setRange(0, 100)
        self.project_overall_status_bar.setValue(0)
        self.project_overall_status_bar.setTextVisible(True)
        self.project_overall_status_bar.setFormat("Project 0%")
        self.project_overall_status_bar.setFixedWidth(140)
        self.project_overall_status_bar.setAlignment(Qt.AlignCenter)

        self.project_tracking_button = qtw.QPushButton("Milestones")
        self.project_tracking_button.setFixedHeight(24)
        self.project_tracking_button.clicked.connect(self.open_tracking_dialog)

        status_bar = self.window.statusBar()
        status_bar.addPermanentWidget(self.project_name_status_label)
        status_bar.addPermanentWidget(self.workflow_status_label)
        status_bar.addPermanentWidget(self.project_overall_status_bar)
        status_bar.addPermanentWidget(self.project_tracking_button)

    def shared_active_project_root(self):
        return self.session_manager.get_active_project_root()

    def candidate_paths(self, candidate_path=None):
        paths = []
        shared_root = self.shared_active_project_root()
        if shared_root:
            paths.append(shared_root)
        if candidate_path:
            paths.append(candidate_path)

        current_root = getattr(self.window, "current_project_root", None)
        if current_root:
            paths.append(current_root)

        for attr_name in self.DEFAULT_CANDIDATE_ATTRS + self.candidate_attrs:
            value = getattr(self.window, attr_name, None)
            if value:
                paths.append(value)
        return tuple(paths)

    def sync_active_project(self):
        shared_root = self.shared_active_project_root()
        if not shared_root:
            return
        if shared_root == getattr(self.window, "current_project_root", None):
            return
        self.refresh_status(shared_root)

    def refresh_status(self, candidate_path=None):
        snapshot = self.workflow_tracker.snapshot(
            self.module_name,
            project_root=getattr(self.window, "current_project_root", None),
            candidate_paths=self.candidate_paths(candidate_path),
        )

        project_root_value = snapshot.get("project_root")
        if project_root_value:
            self.window.current_project_root = project_root_value
            self.window.current_project_name = snapshot.get("project_name", "")

        project_name = snapshot.get("project_name", "none")
        self.project_name_status_label.setText(f"Project: {project_name}")
        self.project_name_status_label.setToolTip(project_root_value or "No active project selected")

        completed_labels = snapshot.get("completed_labels", [])
        completed_text = ", ".join(completed_labels) if completed_labels else "None yet"
        overall_percent = int(snapshot.get("overall_percent", 0))
        overall_next = snapshot.get("overall_next_label", "")
        tooltip = f"Overall {overall_percent}%\nCompleted: {completed_text}\nNext: {overall_next}"

        self.workflow_status_label.setText(self._format_module_workflow_status(snapshot))
        self.workflow_status_label.setToolTip(tooltip)
        self.project_overall_status_bar.setValue(overall_percent)
        self.project_overall_status_bar.setFormat(f"Project {overall_percent}%")
        self.project_overall_status_bar.setToolTip(tooltip)

    def _format_module_workflow_status(self, snapshot):
        module_total = int(snapshot.get("module_total_count", 0))
        module_completed = int(snapshot.get("module_completed_count", 0))
        module_next = snapshot.get("module_next_label", "")

        if module_total > 0:
            if module_next == "Complete":
                return f"{self.module_name} {module_completed}/{module_total} | Complete"
            return f"{self.module_name} {module_completed}/{module_total} | Next: {module_next}"

        overall_completed = int(snapshot.get("overall_completed_count", 0))
        overall_total = int(snapshot.get("overall_total_count", 0))
        overall_next = snapshot.get("overall_next_label", "")
        if overall_next == "Complete":
            return f"{self.module_name} | Project {overall_completed}/{overall_total} | Complete"
        return f"{self.module_name} | Project {overall_completed}/{overall_total} | Next: {overall_next}"

    def resolve_project_root(self, candidate_path=None):
        return self.workflow_tracker.resolve_project_root(*self.candidate_paths(candidate_path))

    def record_milestone(self, milestone_key, candidate_path=None, details=None):
        project_root = self.resolve_project_root(candidate_path)
        if not project_root:
            return None

        self.window.current_project_root = project_root
        self.workflow_tracker.ensure_tracking_state(project_root)
        self.workflow_tracker.record_milestone(
            project_root,
            milestone_key,
            module_name=self.module_name,
            details=details,
        )
        self.refresh_status(project_root)
        return project_root

    def open_tracking_dialog(self):
        project_root = self.resolve_project_root()
        if not project_root:
            qtw.QMessageBox.information(
                self.window,
                "Project Milestones",
                "Select or create a project in MyServer first so milestone state can be edited.",
            )
            return

        self.window.current_project_root = project_root
        self.workflow_tracker.ensure_tracking_state(project_root)
        dialog = ProjectTrackingDialog(self.workflow_tracker, project_root, self.module_name, self.window)
        dialog.exec_()
        self.refresh_status(project_root)