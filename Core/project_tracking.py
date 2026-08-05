import os
import json
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Sequence

from .project_database import load_project_database_record


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
    WorkflowMilestone("training_workspace_ready", "Training workspace prepared", 5),
    WorkflowMilestone("training_progress_plotted", "Training progress plotted", 5),
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
    "MyTrainer": (
        "training_workspace_ready",
        "ground_truth_started",
        "text_outputs_started",
        "training_progress_plotted",
    ),
}

MODULE_SEQUENCE: Sequence[str] = (
    "MyServer",
    "MyScanner",
    "MyPixler",
    "MyBoxer",
    "MyGlypher",
    "MyReader",
    "MyGrounder",
    "MyTrainer",
    "MyLexer",
    "MyResolver",
    "MyVersifier",
    "MyWriter",
)

TRACKING_FILENAME = "ProjectTracking.json"
HANDSHAKE_FILENAME = os.path.join(
    "Model",
    "Project",
    "Images",
    "MyServer",
    "Workflow",
    "module_handshakes.csv",
)
ACTIVE_PROJECT_ROOT_KEYS = (
    "self.active_project_root",
    "self.project_root",
)

MODULE_LABOR_FACTORS: Dict[str, float] = {
    "MyServer": 1.2,
    "MyScanner": 1.3,
    "MyPixler": 1.8,
    "MyBoxer": 2.1,
    "MyGlypher": 2.2,
    "MyReader": 1.8,
    "MyGrounder": 2.0,
    "MyTrainer": 2.4,
    "MyLexer": 1.5,
    "MyResolver": 1.6,
    "MyVersifier": 1.7,
    "MyWriter": 1.4,
}


class ProjectWorkflowTracker:
    def __init__(self, workspace_root: Optional[str] = None):
        self.workspace_root = self._normalize_path(workspace_root)
        self._handshake_rows = self._load_handshake_rows()
        self._handshake_milestone_weights = self._build_handshake_weight_map()
        self._handshake_milestone_order = self._build_handshake_order_map()
        self._handshake_milestone_modules = self._build_handshake_module_map()
        self._milestone_catalog = self._build_milestone_catalog()

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
        for sequence_index, (milestone_key, milestone_label, default_weight) in enumerate(self._milestone_catalog, start=1):
            tracked_value = tracked_milestones.get(milestone_key, {})
            module_name = self._module_for_milestone(milestone_key)
            rows.append(
                {
                    "key": milestone_key,
                    "label": milestone_label,
                    "module": module_name,
                    "sequence": sequence_index,
                    "weight": self._effective_weight(default_weight, tracked_value),
                    "complete": self._milestone_complete(
                        normalized_root,
                        milestone_key,
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

        defaults = {key: (label, weight) for key, label, weight in self._milestone_catalog}
        known_keys = set(defaults.keys()) | set(milestones.keys()) | set(milestone_updates.keys())

        for milestone_key in sorted(known_keys):
            update = milestone_updates.get(milestone_key)
            if not isinstance(update, dict):
                continue

            default_label, default_weight = defaults.get(milestone_key, (milestone_key, 1))
            target = milestones.setdefault(milestone_key, {})
            previous_complete = bool(target.get("complete", False))

            if "weight" in update:
                try:
                    target["weight"] = max(1, int(update["weight"]))
                except (TypeError, ValueError):
                    target["weight"] = default_weight

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

            target.setdefault("label", default_label)
            target.setdefault("weight", default_weight)

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
                "project_percent": 0,
                "overall_percent": 0,
                "page_percent": 0,
                "total_pages": 0,
                "completed_pages": 0,
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

        all_milestone_states = [
            {
                "key": milestone_key,
                "label": milestone_label,
                "weight": self._effective_weight(default_weight, tracked_milestones.get(milestone_key, {})),
                "complete": self._milestone_complete(
                    resolved_root,
                    milestone_key,
                    tracked_milestones,
                ),
            }
            for milestone_key, milestone_label, default_weight in self._milestone_catalog
        ]

        milestone_states = [
            {
                "key": milestone.key,
                "label": milestone.label,
                "weight": self._effective_weight(milestone.weight, tracked_milestones.get(milestone.key, {})),
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

        handshake_milestone_states = [
            item for item in all_milestone_states if item["key"] in self._handshake_milestone_weights
        ]
        if handshake_milestone_states:
            handshake_total = sum(item["weight"] for item in handshake_milestone_states) or 1
            handshake_complete = sum(item["weight"] for item in handshake_milestone_states if item["complete"])
            project_percent = int(round((handshake_complete * 100) / handshake_total))
        else:
            project_percent = overall_percent

        completed_labels = [item["label"] for item in milestone_states if item["complete"]]
        next_overall = next((item for item in milestone_states if not item["complete"]), None)

        module_keys = tuple(MODULE_MILESTONES.get(module_name, ()))
        module_states = [item for item in milestone_states if item["key"] in module_keys]
        next_module = next((item for item in module_states if not item["complete"]), None)

        project_context = self._load_project_context(resolved_root)
        total_pages = self._context_total_pages(project_context)
        page_percent = project_percent
        completed_pages = int(round((total_pages * page_percent) / 100)) if total_pages > 0 else 0

        return {
            "project_root": resolved_root,
            "project_name": os.path.basename(resolved_root),
            "project_percent": project_percent,
            "overall_percent": overall_percent,
            "page_percent": page_percent,
            "total_pages": total_pages,
            "completed_pages": completed_pages,
            "overall_completed_count": len(completed_labels),
            "overall_total_count": len(milestone_states),
            "overall_next_label": next_overall["label"] if next_overall else "Complete",
            "completed_labels": completed_labels,
            "module_completed_count": sum(1 for item in module_states if item["complete"]),
            "module_total_count": len(module_states),
            "module_next_label": next_module["label"] if next_module else "Complete",
            "tracking_file": self.tracking_file_path(resolved_root),
            "project_context": project_context,
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
            "training_workspace_ready": self._training_workspace_ready,
            "training_progress_plotted": self._training_progress_plotted,
        }
        detector = detectors.get(milestone_key)
        if detector is None and milestone_key in self._handshake_milestone_weights:
            return self._handshake_milestone_complete(project_root, milestone_key)
        return detector(project_root) if detector else False

    def _training_workspace_ready(self, project_root: str) -> bool:
        return os.path.isdir(os.path.join(project_root, "Model", "Project", "Training", "Tesseract"))

    def _training_progress_plotted(self, project_root: str) -> bool:
        plot_path = os.path.join(
            project_root,
            "Model",
            "Project",
            "Training",
            "Tesseract",
            "plots",
            "feg",
            "training_progress.png",
        )
        return os.path.isfile(plot_path)

    def _project_ready(self, project_root: str) -> bool:
        return os.path.isfile(
            os.path.join(project_root, "Model", "Project", "Data", "json", "Workflow.json")
        )

    def _load_project_context(self, project_root: str) -> Dict[str, object]:
        context = {}

        for candidate_path in (
            os.path.join(project_root, "project_metadata.json"),
            os.path.join(project_root, "Model", "Project", "Data", "json", "project_metadata.json"),
        ):
            if not os.path.isfile(candidate_path):
                continue
            try:
                with open(candidate_path, "r", encoding="utf-8") as handle:
                    loaded = json.load(handle)
            except (OSError, ValueError, TypeError):
                continue
            if isinstance(loaded, dict):
                context = loaded
                break

        if context:
            return self._normalize_project_context(context)

        sqlite_candidates = (
            os.path.join(project_root, "Model", "Project", "Data", "sqlite", "project_metadata.sqlite"),
            os.path.join(project_root, "Model", "Project", "Data", "SQLite", "project_metadata.sqlite"),
            os.path.join(project_root, "project_metadata.sqlite"),
        )
        for sqlite_path in sqlite_candidates:
            if not os.path.isfile(sqlite_path):
                continue
            loaded = load_project_database_record(sqlite_path)
            if isinstance(loaded, dict) and loaded:
                context = loaded
                break

        return self._normalize_project_context(context)

    def _normalize_project_context(self, context: Dict[str, object]) -> Dict[str, object]:
        normalized = dict(context or {})
        if isinstance(normalized.get("ColumnName"), str):
            column_names = [part.strip() for part in normalized["ColumnName"].split(",") if part.strip()]
            if column_names:
                current_column = normalized.get("CurrentColumn")
                try:
                    current_index = max(1, int(current_column)) - 1
                except (TypeError, ValueError):
                    current_index = 0
                if 0 <= current_index < len(column_names):
                    normalized["ActiveColumnName"] = column_names[current_index]
                else:
                    normalized["ActiveColumnName"] = column_names[0]

        if not normalized.get("CurrentLanguage") and normalized.get("Languages"):
            languages = normalized.get("Languages")
            if isinstance(languages, list) and languages:
                normalized["CurrentLanguage"] = str(languages[0])

        return normalized

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
            os.path.join(project_root, "Model", "Project", "Text", "Workflow"),
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

    def _effective_weight(self, default_weight: int, tracked_value: object) -> int:
        if isinstance(tracked_value, dict):
            try:
                return max(1, int(tracked_value.get("weight", default_weight)))
            except (TypeError, ValueError):
                return default_weight
        return default_weight

    def _milestone_label(self, milestone_key: str) -> str:
        for milestone in OVERALL_MILESTONES:
            if milestone.key == milestone_key:
                return milestone.label
        for key, label, _weight in self._milestone_catalog:
            if key == milestone_key:
                return label
        return milestone_key

    def _milestone_weight(self, milestone_key: str) -> int:
        for milestone in OVERALL_MILESTONES:
            if milestone.key == milestone_key:
                return milestone.weight
        if milestone_key in self._handshake_milestone_weights:
            return self._handshake_milestone_weights[milestone_key]
        return 1

    def _default_tracking_state(self) -> Dict[str, object]:
        return {
            "version": 1,
            "milestones": {
                milestone_key: {
                    "label": milestone_label,
                    "weight": milestone_weight,
                    "complete": False,
                    "completed_at": None,
                    "updated_by": None,
                }
                for milestone_key, milestone_label, milestone_weight in self._milestone_catalog
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

        for milestone_key, milestone_label, milestone_weight in self._milestone_catalog:
            existing = raw_milestones.get(milestone_key, {})
            if not isinstance(existing, dict):
                continue
            target = state["milestones"][milestone_key]
            target["label"] = existing.get("label", milestone_label)
            try:
                target["weight"] = max(1, int(existing.get("weight", milestone_weight)))
            except (TypeError, ValueError):
                target["weight"] = milestone_weight
            target["complete"] = bool(existing.get("complete", False))
            target["completed_at"] = existing.get("completed_at")
            target["updated_by"] = existing.get("updated_by")
            if "details" in existing:
                target["details"] = existing.get("details")
        return state

    def _build_milestone_catalog(self) -> List[tuple]:
        catalog = [(m.key, m.label, m.weight) for m in OVERALL_MILESTONES]
        ordered_handshake_keys = sorted(
            self._handshake_milestone_weights.keys(),
            key=lambda key: self._handshake_milestone_order.get(key, 10_000),
        )
        for milestone_key in ordered_handshake_keys:
            if any(existing_key == milestone_key for existing_key, _label, _weight in catalog):
                continue
            catalog.append((milestone_key, self._humanize_milestone_name(milestone_key), self._handshake_milestone_weights[milestone_key]))
        return catalog

    def _build_handshake_order_map(self) -> Dict[str, int]:
        order_map: Dict[str, int] = {}
        for index, row in enumerate(self._handshake_rows):
            milestone_key = row.get("MilestoneName", "").strip()
            if not milestone_key or milestone_key in order_map:
                continue
            order_map[milestone_key] = index
        return order_map

    def _build_handshake_module_map(self) -> Dict[str, str]:
        module_map: Dict[str, str] = {}
        for row in self._handshake_rows:
            milestone_key = row.get("MilestoneName", "").strip()
            if not milestone_key or milestone_key in module_map:
                continue
            output_module = row.get("OutputModule", "").strip()
            input_module = row.get("InputModule", "").strip()
            module_map[milestone_key] = output_module or input_module or "Workflow"
        return module_map

    def _module_for_milestone(self, milestone_key: str) -> str:
        if milestone_key in self._handshake_milestone_modules:
            return self._handshake_milestone_modules[milestone_key]

        for module_name, milestone_keys in MODULE_MILESTONES.items():
            if milestone_key in milestone_keys:
                return module_name
        return "Workflow"

    def _load_handshake_rows(self) -> List[Dict[str, str]]:
        handshake_path = self._resolve_handshake_file_path()
        if not handshake_path or not os.path.isfile(handshake_path):
            return []

        rows: List[Dict[str, str]] = []
        with open(handshake_path, "r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, delimiter=" ", skipinitialspace=True)
            for raw_row in reader:
                if not raw_row:
                    continue
                row = {str(key).strip(): str(value).strip() for key, value in raw_row.items() if key}
                milestone_name = row.get("MilestoneName", "")
                if not milestone_name:
                    continue
                rows.append(row)
        return rows

    def _resolve_handshake_file_path(self) -> Optional[str]:
        candidates = []
        if self.workspace_root:
            candidates.append(os.path.join(self.workspace_root, HANDSHAKE_FILENAME))
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        candidates.append(os.path.join(repo_root, HANDSHAKE_FILENAME))
        candidates.append(os.path.join(os.getcwd(), HANDSHAKE_FILENAME))

        for candidate in candidates:
            if os.path.isfile(candidate):
                return candidate
        return None

    def _build_handshake_weight_map(self) -> Dict[str, int]:
        milestone_scores: Dict[str, float] = {}
        for row in self._handshake_rows:
            key = row.get("MilestoneName", "").strip()
            if not key:
                continue
            in_module = row.get("InputModule", "")
            out_module = row.get("OutputModule", "")
            in_factor = MODULE_LABOR_FACTORS.get(in_module, 1.0)
            out_factor = MODULE_LABOR_FACTORS.get(out_module, 1.0)
            base_score = (in_factor + out_factor) / 2.0

            ui_bonus = 0.15 if row.get("UI_Action", "").strip().upper() == "Y" else 0.0
            manual_bonus = 0.15 if row.get("Override", "").strip().upper() == "N" else 0.0
            milestone_scores[key] = milestone_scores.get(key, 0.0) + max(0.2, base_score + ui_bonus + manual_bonus)

        if not milestone_scores:
            return {}

        total_score = sum(milestone_scores.values()) or 1.0
        weights: Dict[str, int] = {}
        for key, score in milestone_scores.items():
            weights[key] = max(1, int(round((score * 100.0) / total_score)))
        return weights

    def _humanize_milestone_name(self, milestone_key: str) -> str:
        return milestone_key.replace("_", " ").strip().title()

    def _handshake_milestone_complete(self, project_root: str, milestone_key: str) -> bool:
        matching_rows = [row for row in self._handshake_rows if row.get("MilestoneName") == milestone_key]
        if not matching_rows:
            return False
        return any(self._handshake_output_exists(project_root, row.get("OutputPath", "")) for row in matching_rows)

    def _handshake_output_exists(self, project_root: str, output_path: str) -> bool:
        normalized = str(output_path or "").strip()
        if not normalized:
            return False
        if normalized.startswith("~/") or normalized.startswith("/"):
            return False
        candidate = os.path.join(project_root, *normalized.split("/"))
        if os.path.isfile(candidate):
            return True
        if os.path.isdir(candidate):
            return self._directory_has_files(candidate)
        return False

    def _context_total_pages(self, project_context: Dict[str, object]) -> int:
        try:
            number_pages = int(project_context.get("NumberPages", 0) or 0)
        except (TypeError, ValueError):
            number_pages = 0
        try:
            number_columns = int(project_context.get("NumberColumns", 0) or 0)
        except (TypeError, ValueError):
            number_columns = 0

        if number_pages <= 0 and number_columns <= 0:
            return 0
        if number_pages <= 0:
            return max(0, number_columns)
        if number_columns <= 0:
            return max(0, number_pages)
        return max(0, number_pages * number_columns)

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