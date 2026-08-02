import os
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Sequence


@dataclass(frozen=True)
class WorkflowMilestone:
    key: str
    label: str
    weight: int


OVERALL_MILESTONES: Sequence[WorkflowMilestone] = (
    WorkflowMilestone("project_ready", "Project initialized", 10),
    WorkflowMilestone("source_acquired", "Source images captured", 15),
    WorkflowMilestone("source_converted", "Source images converted", 20),
    WorkflowMilestone("pages_prepared", "Language pages prepared", 20),
    WorkflowMilestone("lines_prepared", "Line images prepared", 15),
    WorkflowMilestone("ground_truth_started", "Ground truth started", 10),
    WorkflowMilestone("text_outputs_started", "Text outputs started", 10),
)


MODULE_MILESTONES: Dict[str, Sequence[str]] = {
    "MyServer": (
        "project_ready",
        "source_acquired",
        "source_converted",
        "pages_prepared",
    ),
    "MyPixler": (
        "source_acquired",
        "source_converted",
        "pages_prepared",
        "lines_prepared",
        "ground_truth_started",
    ),
}

TRACKING_FILENAME = "ProjectTracking.json"
ACTIVE_PROJECT_ROOT_KEYS = (
    "self.active_project_root",
    "self.project_root",
)


class ProjectWorkflowTracker:
    def __init__(self, workspace_root: Optional[str] = None):
        self.workspace_root = self._normalize_path(workspace_root)

    def tracking_file_path(self, project_root: str) -> str:
        return os.path.join(project_root, "Model", "Project", "Data", "json", TRACKING_FILENAME)

    def ensure_tracking_state(self, project_root: str) -> Dict[str, object]:
        normalized_root = self._normalize_path(project_root)
        if not normalized_root:
            return self._default_tracking_state()

        state = self.load_tracking_state(normalized_root)
        path = self.tracking_file_path(normalized_root)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2)
        return state

    def load_tracking_state(self, project_root: str) -> Dict[str, object]:
        path = self.tracking_file_path(project_root)
        if not os.path.exists(path):
            return self._default_tracking_state()

        try:
            with open(path, "r", encoding="utf-8") as handle:
                raw_state = json.load(handle)
        except (OSError, ValueError, TypeError):
            return self._default_tracking_state()

        return self._normalize_tracking_state(raw_state)

    def record_milestone(
        self,
        project_root: str,
        milestone_key: str,
        module_name: Optional[str] = None,
        details: Optional[Dict[str, object]] = None,
    ) -> Dict[str, object]:
        normalized_root = self._normalize_path(project_root)
        if not normalized_root:
            return self._default_tracking_state()

        state = self.ensure_tracking_state(normalized_root)
        milestones = state.setdefault("milestones", {})
        milestone = milestones.setdefault(milestone_key, {"complete": False})
        milestone.setdefault("label", self._milestone_label(milestone_key))
        milestone.setdefault("weight", self._milestone_weight(milestone_key))
        milestone["complete"] = True
        milestone["completed_at"] = self._utc_now_iso()
        if module_name:
            milestone["updated_by"] = module_name
        if details:
            milestone["details"] = details

        path = self.tracking_file_path(normalized_root)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2)
        return state

    def milestone_rows(self, project_root: str) -> List[Dict[str, object]]:
        normalized_root = self._normalize_path(project_root)
        if not normalized_root:
            return []

        state = self.ensure_tracking_state(normalized_root)
        tracked_milestones = state.get("milestones", {})
        rows = []
        for milestone in OVERALL_MILESTONES:
            tracked_value = tracked_milestones.get(milestone.key, {})
            rows.append(
                {
                    "key": milestone.key,
                    "label": milestone.label,
                    "weight": self._effective_weight(milestone, tracked_value),
                    "complete": self._milestone_complete(
                        normalized_root,
                        milestone.key,
                        tracked_milestones,
                    ),
                    "completed_at": tracked_value.get("completed_at") if isinstance(tracked_value, dict) else None,
                    "updated_by": tracked_value.get("updated_by") if isinstance(tracked_value, dict) else None,
                    "details": tracked_value.get("details") if isinstance(tracked_value, dict) else None,
                }
            )
        return rows

    def update_milestones(
        self,
        project_root: str,
        milestone_updates: Dict[str, Dict[str, object]],
        updated_by: Optional[str] = None,
    ) -> Dict[str, object]:
        normalized_root = self._normalize_path(project_root)
        if not normalized_root:
            return self._default_tracking_state()

        state = self.ensure_tracking_state(normalized_root)
        milestones = state.setdefault("milestones", {})

        for milestone in OVERALL_MILESTONES:
            update = milestone_updates.get(milestone.key)
            if not isinstance(update, dict):
                continue

            target = milestones.setdefault(milestone.key, {})
            previous_complete = bool(target.get("complete", False))

            if "weight" in update:
                try:
                    target["weight"] = max(1, int(update["weight"]))
                except (TypeError, ValueError):
                    target["weight"] = milestone.weight

            if "complete" in update:
                complete = bool(update["complete"])
                target["complete"] = complete
                if complete:
                    if not previous_complete or not target.get("completed_at"):
                        target["completed_at"] = self._utc_now_iso()
                else:
                    target["completed_at"] = None

            if updated_by:
                target["updated_by"] = updated_by

            if "details" in update:
                target["details"] = update.get("details")

            target.setdefault("label", milestone.label)
            target.setdefault("weight", milestone.weight)

        path = self.tracking_file_path(normalized_root)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2)
        return state

    def resolve_project_root(self, *candidate_paths: Optional[str]) -> Optional[str]:
        for candidate in candidate_paths:
            resolved = self._resolve_candidate_root(candidate)
            if resolved:
                return resolved
        return None

    def snapshot(
        self,
        module_name: str,
        project_root: Optional[str] = None,
        candidate_paths: Optional[Iterable[Optional[str]]] = None,
    ) -> Dict[str, object]:
        resolved_root = self._resolve_snapshot_root(project_root, candidate_paths or ())
        if not resolved_root:
            module_keys = tuple(MODULE_MILESTONES.get(module_name, ()))
            return {
                "project_root": None,
                "project_name": "none",
                "overall_percent": 0,
                "overall_completed_count": 0,
                "overall_total_count": len(OVERALL_MILESTONES),
                "overall_next_label": OVERALL_MILESTONES[0].label if OVERALL_MILESTONES else "",
                "completed_labels": [],
                "module_completed_count": 0,
                "module_total_count": len(module_keys),
                "module_next_label": self._module_next_label(module_keys),
            }

        tracking_state = self.ensure_tracking_state(resolved_root)
        tracked_milestones = tracking_state.get("milestones", {})

        milestone_states = [
            {
                "key": milestone.key,
                "label": milestone.label,
                "weight": self._effective_weight(milestone, tracked_milestones.get(milestone.key, {})),
                "complete": self._milestone_complete(
                    resolved_root,
                    milestone.key,
                    tracked_milestones,
                ),
            }
            for milestone in OVERALL_MILESTONES
        ]

        total_weight = sum(item["weight"] for item in milestone_states) or 1
        completed_weight = sum(item["weight"] for item in milestone_states if item["complete"])
        overall_percent = int(round((completed_weight * 100) / total_weight))

        completed_labels = [item["label"] for item in milestone_states if item["complete"]]
        next_overall = next((item for item in milestone_states if not item["complete"]), None)

        module_keys = tuple(MODULE_MILESTONES.get(module_name, ()))
        module_states = [item for item in milestone_states if item["key"] in module_keys]
        next_module = next((item for item in module_states if not item["complete"]), None)

        return {
            "project_root": resolved_root,
            "project_name": os.path.basename(resolved_root),
            "overall_percent": overall_percent,
            "overall_completed_count": len(completed_labels),
            "overall_total_count": len(milestone_states),
            "overall_next_label": next_overall["label"] if next_overall else "Complete",
            "completed_labels": completed_labels,
            "module_completed_count": sum(1 for item in module_states if item["complete"]),
            "module_total_count": len(module_states),
            "module_next_label": next_module["label"] if next_module else "Complete",
            "tracking_file": self.tracking_file_path(resolved_root),
        }

    def _milestone_complete(
        self,
        project_root: str,
        milestone_key: str,
        tracked_milestones: Dict[str, object],
    ) -> bool:
        tracked_value = tracked_milestones.get(milestone_key, {})
        if isinstance(tracked_value, dict) and tracked_value.get("complete"):
            return True
        return self._is_milestone_complete(project_root, milestone_key)

    def _resolve_snapshot_root(
        self,
        project_root: Optional[str],
        candidate_paths: Iterable[Optional[str]],
    ) -> Optional[str]:
        if project_root:
            resolved = self._resolve_candidate_root(project_root)
            if resolved:
                return resolved
        shared_root = self._workspace_active_project_root()
        if shared_root:
            return shared_root
        return self.resolve_project_root(*candidate_paths)

    def _workspace_active_project_root(self) -> Optional[str]:
        session_path = self._workspace_session_path()
        if not session_path or not os.path.exists(session_path):
            return None

        try:
            with open(session_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, ValueError, TypeError):
            return None

        if isinstance(data, list):
            session_values = {}
            for item in data:
                if not isinstance(item, dict):
                    continue
                setting = item.get("Setting")
                if not setting:
                    continue
                session_values[setting] = item.get("CurrentValue")
        elif isinstance(data, dict):
            session_values = data
        else:
            return None

        for key in ACTIVE_PROJECT_ROOT_KEYS:
            resolved = self._resolve_candidate_root(session_values.get(key))
            if resolved:
                return resolved
        return None

    def _workspace_session_path(self) -> Optional[str]:
        if not self.workspace_root:
            return None
        return os.path.join(
            self.workspace_root,
            "Model",
            "Project",
            "Data",
            "json",
            "Session.json",
        )

    def _resolve_candidate_root(self, candidate_path: Optional[str]) -> Optional[str]:
        normalized = self._normalize_path(candidate_path)
        if not normalized:
            return None

        if os.path.isfile(normalized):
            normalized = os.path.dirname(normalized)

        current = normalized
        while current:
            if self._looks_like_project_root(current):
                if self.workspace_root and self._same_path(current, self.workspace_root):
                    return None
                return current
            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent
        return None

    def _looks_like_project_root(self, path: str) -> bool:
        return os.path.isdir(os.path.join(path, "Model", "Project"))

    def _is_milestone_complete(self, project_root: str, milestone_key: str) -> bool:
        detectors = {
            "project_ready": self._project_ready,
            "source_acquired": self._source_acquired,
            "source_converted": self._source_converted,
            "pages_prepared": self._pages_prepared,
            "lines_prepared": self._lines_prepared,
            "ground_truth_started": self._ground_truth_started,
            "text_outputs_started": self._text_outputs_started,
        }
        detector = detectors.get(milestone_key)
        return detector(project_root) if detector else False

    def _project_ready(self, project_root: str) -> bool:
        return os.path.isfile(
            os.path.join(project_root, "Model", "Project", "Data", "json", "Workflow.json")
        )

    def _source_acquired(self, project_root: str) -> bool:
        images_root = os.path.join(project_root, "Model", "Project", "Images")
        return self._has_files_in_named_dirs(images_root, {"Scanned", "pdf_page_files"})

    def _source_converted(self, project_root: str) -> bool:
        source_root = os.path.join(project_root, "Model", "Project", "Images", "Workflow", "Source")
        return self._has_files_in_named_dirs(
            source_root,
            {
                "pdf_pages_2tif",
                "tif_black_white",
                "png_black_white",
                "tif_black_white_deskewed",
                "png_black_white_deskewed",
            },
        )

    def _pages_prepared(self, project_root: str) -> bool:
        greek_root = os.path.join(project_root, "Model", "Project", "Images", "Workflow", "Greek")
        latin_root = os.path.join(project_root, "Model", "Project", "Images", "Workflow", "Latin")
        return self._has_files_with_dir_token(greek_root, "_pages") or self._has_files_with_dir_token(
            latin_root,
            "_pages",
        )

    def _lines_prepared(self, project_root: str) -> bool:
        greek_root = os.path.join(project_root, "Model", "Project", "Images", "Workflow", "Greek")
        latin_root = os.path.join(project_root, "Model", "Project", "Images", "Workflow", "Latin")
        return self._has_files_with_dir_token(greek_root, "_lines") or self._has_files_with_dir_token(
            latin_root,
            "_lines",
        )

    def _ground_truth_started(self, project_root: str) -> bool:
        text_ground_truth = os.path.join(project_root, "Model", "Project", "Text", "GroundTruth")
        if self._directory_has_files(text_ground_truth):
            return True

        greek_root = os.path.join(project_root, "Model", "Project", "Images", "Workflow", "Greek")
        latin_root = os.path.join(project_root, "Model", "Project", "Images", "Workflow", "Latin")
        return self._has_files_with_dir_token(greek_root, "groundtruth") or self._has_files_with_dir_token(
            latin_root,
            "groundtruth",
        )

    def _text_outputs_started(self, project_root: str) -> bool:
        output_dirs = (
            os.path.join(project_root, "Model", "Project", "Text", "Esword"),
            os.path.join(project_root, "Model", "Project", "Text", "TheWord"),
            os.path.join(project_root, "Model", "Project", "Text", "EstablishTruth"),
            os.path.join(project_root, "Model", "Project", "Text", "PriorTruth"),
        )
        return any(self._directory_has_files(path) for path in output_dirs)

    def _has_files_in_named_dirs(self, root_dir: str, directory_names: Iterable[str]) -> bool:
        if not os.path.isdir(root_dir):
            return False

        wanted = {name.lower() for name in directory_names}
        for dirpath, _, filenames in os.walk(root_dir):
            if not filenames:
                continue
            if os.path.basename(dirpath).lower() in wanted:
                return True
        return False

    def _has_files_with_dir_token(self, root_dir: str, token: str) -> bool:
        if not os.path.isdir(root_dir):
            return False

        needle = token.lower()
        for dirpath, _, filenames in os.walk(root_dir):
            if not filenames:
                continue
            relative_dir = os.path.relpath(dirpath, root_dir).lower()
            if needle in relative_dir:
                return True
        return False

    def _directory_has_files(self, path: str) -> bool:
        if not os.path.isdir(path):
            return False

        for _, _, filenames in os.walk(path):
            if filenames:
                return True
        return False

    def _module_next_label(self, module_keys: Sequence[str]) -> str:
        for milestone in OVERALL_MILESTONES:
            if milestone.key in module_keys:
                return milestone.label
        return ""

    def _effective_weight(self, milestone: WorkflowMilestone, tracked_value: object) -> int:
        if isinstance(tracked_value, dict):
            try:
                return max(1, int(tracked_value.get("weight", milestone.weight)))
            except (TypeError, ValueError):
                return milestone.weight
        return milestone.weight

    def _milestone_label(self, milestone_key: str) -> str:
        for milestone in OVERALL_MILESTONES:
            if milestone.key == milestone_key:
                return milestone.label
        return milestone_key

    def _milestone_weight(self, milestone_key: str) -> int:
        for milestone in OVERALL_MILESTONES:
            if milestone.key == milestone_key:
                return milestone.weight
        return 1

    def _default_tracking_state(self) -> Dict[str, object]:
        return {
            "version": 1,
            "milestones": {
                milestone.key: {
                    "label": milestone.label,
                    "weight": milestone.weight,
                    "complete": False,
                    "completed_at": None,
                    "updated_by": None,
                }
                for milestone in OVERALL_MILESTONES
            },
        }

    def _normalize_tracking_state(self, raw_state: object) -> Dict[str, object]:
        state = self._default_tracking_state()
        if not isinstance(raw_state, dict):
            return state

        state["version"] = raw_state.get("version", 1)
        raw_milestones = raw_state.get("milestones", {})
        if not isinstance(raw_milestones, dict):
            return state

        for milestone in OVERALL_MILESTONES:
            existing = raw_milestones.get(milestone.key, {})
            if not isinstance(existing, dict):
                continue
            target = state["milestones"][milestone.key]
            target["label"] = existing.get("label", milestone.label)
            try:
                target["weight"] = max(1, int(existing.get("weight", milestone.weight)))
            except (TypeError, ValueError):
                target["weight"] = milestone.weight
            target["complete"] = bool(existing.get("complete", False))
            target["completed_at"] = existing.get("completed_at")
            target["updated_by"] = existing.get("updated_by")
            if "details" in existing:
                target["details"] = existing.get("details")
        return state

    @staticmethod
    def _utc_now_iso() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    @staticmethod
    def _normalize_path(path: Optional[str]) -> Optional[str]:
        if not isinstance(path, str) or not path.strip():
            return None
        return os.path.abspath(os.path.normpath(path))

    @staticmethod
    def _same_path(left: str, right: str) -> bool:
        return os.path.normcase(os.path.abspath(left)) == os.path.normcase(os.path.abspath(right))