import os
import json
import csv
import platform
import sqlite3
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Union

from PyQt5 import QtGui as qtg

JSONItem = Dict[str, Any]
SessionDict = Dict[str, JSONItem]
SettingMap = Dict[str, Union[str, Callable[[Any], None]]]

ACTIVE_PROJECT_ROOT_KEYS = (
    'self.active_project_root',
    'self.project_root',
)
ACTIVE_PROJECT_NAME_KEYS = (
    'self.active_project_name',
    'self.project_name',
)
ACTIVE_WORKFLOW_MODULE_KEYS = (
    'self.active_workflow_module',
)
ACTIVE_WORKFLOW_WIZARD_MODE_KEYS = (
    'self.active_workflow_wizard_mode',
)
ACTIVE_WORKFLOW_WIZARD_MODULE_KEYS = (
    'self.active_workflow_wizard_module',
)
ACTIVE_CURRENT_PROJECT_PAGE_KEYS = (
    'self.current_project_page',
)
ACTIVE_CURRENT_PROJECT_MILESTONE_KEYS = (
    'self.current_project_milestone',
)
ACTIVE_CURRENT_PAGE_MILESTONE_KEYS = (
    'self.current_page_milestone',
)


@dataclass(frozen=True)
class RuntimePaths:
    script_dir: str
    project_root: str
    model_dir: str
    data_dir: str
    image_dir: str
    text_dir: str
    train_dir: str
    session_dir: str
    developer_view_dir: str


def normalize_path(path: str) -> str:
    return os.path.abspath(os.path.expanduser(path))


def build_runtime_paths(
    module_file: Optional[str] = None,
    *,
    add_project_root: bool = True,
    add_developer_view: bool = False,
) -> RuntimePaths:
    script_dir = os.path.dirname(os.path.realpath(module_file)) if module_file else os.path.dirname(os.path.abspath(__file__))
    project_root = normalize_path(os.path.join(script_dir, '..', '..'))
    model_dir = os.path.join(project_root, 'Model')
    data_dir = os.path.join(model_dir, 'Data')
    image_dir = os.path.join(model_dir, 'Images')
    text_dir = os.path.join(model_dir, 'Text')
    train_dir = os.path.join(model_dir, 'Training')
    session_dir = os.path.join(data_dir, 'json')
    developer_view_dir = os.path.join(project_root, 'ViewController', 'Developer')

    if add_project_root and project_root not in sys.path:
        sys.path.insert(0, project_root)

    if add_developer_view and developer_view_dir not in sys.path:
        sys.path.insert(0, developer_view_dir)

    return RuntimePaths(
        script_dir=script_dir,
        project_root=project_root,
        model_dir=model_dir,
        data_dir=data_dir,
        image_dir=image_dir,
        text_dir=text_dir,
        train_dir=train_dir,
        session_dir=session_dir,
        developer_view_dir=developer_view_dir,
    )


class SessionManager:
    DEFAULT_PROJECT_FONT = 'FROMVS.ttf'

    @staticmethod
    def runtime_paths_for(
        module_file: Optional[str] = None,
        *,
        add_project_root: bool = True,
        add_developer_view: bool = False,
    ) -> RuntimePaths:
        return build_runtime_paths(
            module_file,
            add_project_root=add_project_root,
            add_developer_view=add_developer_view,
        )

    @staticmethod
    def export_runtime_paths(
        namespace: Dict[str, Any],
        module_file: Optional[str] = None,
        *,
        add_project_root: bool = True,
        add_developer_view: bool = False,
    ) -> RuntimePaths:
        runtime_paths = SessionManager.runtime_paths_for(
            module_file,
            add_project_root=add_project_root,
            add_developer_view=add_developer_view,
        )
        namespace.update(runtime_paths.__dict__)
        return runtime_paths

    def __init__(self, base_dir: Optional[str] = None):
        if base_dir:
            self.base_dir = normalize_path(base_dir)
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.base_dir = os.path.normpath(
                os.path.join(current_dir, '..', '..', 'Model', 'Project', 'Data', 'json')
            )

    def _project_font_dir(self) -> str:
        return os.path.normpath(
            os.path.join(self.base_dir, '..', '..', '..', '..', 'ViewController', '0-MainUI', 'fonts')
        )

    def session_path(self, filename: str) -> str:
        return normalize_path(filename) if os.path.isabs(filename) else os.path.join(self.base_dir, filename)

    def _ensure_session_file(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(path):
            with open(path, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=4)

    def load(self, filename: str, keys: Optional[Iterable[str]] = None) -> SessionDict:
        path = self.session_path(filename)
        self._ensure_session_file(path)
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        normalized_data = self._normalize_session_data(data)
        if normalized_data != data:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(normalized_data, f, indent=4)
        data = normalized_data
        session = {item['Setting']: item for item in data}
        if keys is None:
            return session
        return {key: session[key] for key in keys if key in session}

    def values(self, filename: str, keys: Optional[Iterable[str]] = None) -> Dict[str, Any]:
        return {key: item.get('CurrentValue') for key, item in self.load(filename, keys).items()}

    def get_active_project(self, filename: str = 'Session.json') -> Dict[str, str]:
        values = self.values(filename)

        project_root = ''
        for key in ACTIVE_PROJECT_ROOT_KEYS:
            value = values.get(key)
            if value:
                project_root = normalize_path(str(value))
                break

        project_name = ''
        for key in ACTIVE_PROJECT_NAME_KEYS:
            value = values.get(key)
            if value:
                project_name = str(value).strip()
                break

        if project_root and not project_name:
            project_name = os.path.basename(project_root)

        return {
            'project_root': project_root,
            'project_name': project_name,
            'current_project_page': str(values.get('self.current_project_page', '') or ''),
            'current_project_milestone': str(values.get('self.current_project_milestone', '') or ''),
            'current_page_milestone': str(values.get('self.current_page_milestone', '') or ''),
        }

    def get_active_project_root(self, filename: str = 'Session.json') -> str:
        return self.get_active_project(filename).get('project_root', '')

    def set_active_project(self, project_root: str, filename: str = 'Session.json') -> Dict[str, str]:
        normalized_root = normalize_path(project_root)
        project_name = os.path.basename(normalized_root)
        self.update(
            filename,
            {
                'self.active_project_root': normalized_root,
                'self.active_project_name': project_name,
                'self.project_root': normalized_root,
                'self.project_name': project_name,
            },
        )
        return {
            'project_root': normalized_root,
            'project_name': project_name,
        }

    @staticmethod
    def _coerce_page_number(value: Any, default: int = 1) -> int:
        try:
            page_number = int(value)
        except (TypeError, ValueError):
            page_number = int(default or 1)
        return max(1, page_number)

    @staticmethod
    def _normalize_milestone_text(value: Any) -> str:
        return str(value or '').strip()

    def get_active_project_page(self, filename: str = 'Session.json') -> int:
        values = self.values(filename)
        for key in ACTIVE_CURRENT_PROJECT_PAGE_KEYS:
            value = values.get(key)
            if value not in (None, ''):
                return self._coerce_page_number(value, 1)
        return 1

    def set_active_project_page(self, page_number: Any, filename: str = 'Session.json') -> int:
        normalized_page = self._coerce_page_number(page_number, 1)
        self.update(filename, {'self.current_project_page': normalized_page})
        return normalized_page

    def get_active_project_milestone(self, filename: str = 'Session.json') -> str:
        values = self.values(filename)
        for key in ACTIVE_CURRENT_PROJECT_MILESTONE_KEYS:
            value = values.get(key)
            if value:
                return str(value).strip()
        return ''

    def set_active_project_milestone(self, milestone: Any, filename: str = 'Session.json') -> str:
        normalized_milestone = self._normalize_milestone_text(milestone)
        self.update(filename, {'self.current_project_milestone': normalized_milestone})
        return normalized_milestone

    def get_active_page_milestone(self, filename: str = 'Session.json') -> str:
        values = self.values(filename)
        for key in ACTIVE_CURRENT_PAGE_MILESTONE_KEYS:
            value = values.get(key)
            if value:
                return str(value).strip()
        return ''

    def set_active_page_milestone(self, milestone: Any, filename: str = 'Session.json') -> str:
        normalized_milestone = self._normalize_milestone_text(milestone)
        self.update(filename, {'self.current_page_milestone': normalized_milestone})
        return normalized_milestone

    def get_active_workflow_module(self, filename: str = 'Session.json') -> str:
        values = self.values(filename)
        for key in ACTIVE_WORKFLOW_MODULE_KEYS:
            value = values.get(key)
            if value:
                return str(value).strip()
        return ''

    def set_active_workflow_module(self, module_name: str, filename: str = 'Session.json') -> str:
        normalized_name = str(module_name or '').strip()
        if not normalized_name:
            return ''
        self.update(filename, {'self.active_workflow_module': normalized_name})
        return normalized_name

    def get_active_workflow_wizard_mode(self, filename: str = 'Session.json') -> str:
        values = self.values(filename)
        for key in ACTIVE_WORKFLOW_WIZARD_MODE_KEYS:
            value = values.get(key)
            if value:
                return str(value).strip().lower()
        return ''

    def get_active_workflow_wizard_module(self, filename: str = 'Session.json') -> str:
        values = self.values(filename)
        for key in ACTIVE_WORKFLOW_WIZARD_MODULE_KEYS:
            value = values.get(key)
            if value:
                return str(value).strip()
        return ''

    def set_active_workflow_wizard_context(
        self,
        mode: str,
        module_name: Optional[str] = None,
        filename: str = 'Session.json',
    ) -> Dict[str, str]:
        normalized_mode = str(mode or '').strip().lower()
        if normalized_mode not in {'project', 'page'}:
            return {
                'mode': '',
                'module': '',
            }

        normalized_module = str(module_name or '').strip()
        updates: Dict[str, Any] = {
            'self.active_workflow_wizard_mode': normalized_mode,
        }

        if normalized_module:
            updates['self.active_workflow_wizard_module'] = normalized_module

        self.update(filename, updates)
        return {
            'mode': normalized_mode,
            'module': normalized_module,
        }

    def update(self, filename: str, updates: Dict[str, Any]) -> None:
        path = self.session_path(filename)
        self._ensure_session_file(path)
        session = self.load(filename)
        changed = False

        for key, value in updates.items():
            if key in session:
                if session[key].get('CurrentValue') != value:
                    session[key]['CurrentValue'] = value
                    changed = True
            else:
                session[key] = {
                    'Setting': key,
                    'CurrentValue': value,
                    'DefaultValue': value,
                }
                changed = True

        if changed:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(list(session.values()), f, indent=4)

    def _normalize_session_data(self, data: Any) -> List[JSONItem]:
        if isinstance(data, list):
            normalized_items = []
            for item in data:
                if not isinstance(item, dict):
                    continue
                setting = item.get('Setting')
                if not setting:
                    continue
                normalized_items.append(
                    {
                        'Setting': setting,
                        'CurrentValue': item.get('CurrentValue'),
                        'DefaultValue': item.get('DefaultValue', item.get('CurrentValue')),
                    }
                )
            return normalized_items

        if isinstance(data, dict):
            legacy_key_map = {
                'path': 'self.imgpath',
                'dir': 'self.imgdir',
                'CurrentProjectPage': 'self.current_project_page',
                'CurrentProjectMilestone': 'self.current_project_milestone',
                'CurrentPageMilestone': 'self.current_page_milestone',
            }
            normalized_items = []
            for key, value in data.items():
                setting = legacy_key_map.get(key, key)
                normalized_items.append(
                    {
                        'Setting': setting,
                        'CurrentValue': value,
                        'DefaultValue': value,
                    }
                )
            return normalized_items

        return []

    def load_object(self, filename: str, target: object, mapping: SettingMap) -> None:
        values = self.values(filename)
        for setting_key, setter in mapping.items():
            if setting_key not in values:
                continue
            value = values[setting_key]
            if isinstance(setter, str):
                setattr(target, setter, value)
            else:
                setter(value)

    @staticmethod
    def default_font_install_dirs() -> List[str]:
        home_dir = os.path.expanduser('~')
        system_name = platform.system().lower()

        if system_name == 'windows':
            local_appdata = os.environ.get('LOCALAPPDATA', os.path.join(home_dir, 'AppData', 'Local'))
            windir = os.environ.get('WINDIR', r'C:\Windows')
            return [
                os.path.join(local_appdata, 'Microsoft', 'Windows', 'Fonts'),
                os.path.join(windir, 'Fonts'),
            ]

        return [
            os.path.join(home_dir, '.local', 'share', 'fonts'),
            '/usr/local/share/fonts',
            '/usr/share/fonts/truetype',
        ]

    @staticmethod
    def _font_candidate_names(font_name: str) -> List[str]:
        if not font_name:
            return []

        normalized = font_name.strip()
        lowered = normalized.lower()

        if lowered in {'fromvs', 'fromvs [maxr]'}:
            return ['FROMVS.ttf', 'FROMVS.otf', 'FROMVS [MAXR].ttf', 'FROMVS [MAXR].otf']

        base_name, extension = os.path.splitext(normalized)
        if extension:
            return [normalized]

        return [normalized, f'{normalized}.ttf', f'{normalized}.otf']

    def resolve_font_path(self, font_name: str, module_dir: Optional[str] = None) -> Optional[str]:
        search_dirs = []
        search_dirs.append(self._project_font_dir())
        if module_dir:
            search_dirs.append(os.path.join(module_dir, 'fonts'))
        search_dirs.extend(self.default_font_install_dirs())

        for candidate in self._font_candidate_names(font_name):
            if os.path.isabs(candidate) and os.path.exists(candidate):
                return os.path.normpath(candidate)

            for font_dir in search_dirs:
                font_path = os.path.normpath(os.path.join(font_dir, candidate))
                if os.path.exists(font_path):
                    return font_path

        return None

    def register_application_font(self, font_name: str, module_dir: Optional[str] = None) -> str:
        font_path = self.resolve_font_path(font_name, module_dir)
        if not font_path:
            return font_name

        font_id = qtg.QFontDatabase.addApplicationFont(font_path)
        if font_id == -1:
            return font_name

        families = qtg.QFontDatabase.applicationFontFamilies(font_id)
        if families:
            return families[0]

        return font_name

    @staticmethod
    def _is_user_font_dir(path: str) -> bool:
        normalized = os.path.normpath(path)
        home_dir = os.path.normpath(os.path.expanduser('~'))
        return normalized.startswith(home_dir)

    def install_font_file(self, font_file_path: str, *, prefer_user_scope: bool = True) -> str:
        source_path = os.path.normpath(str(font_file_path or '').strip())
        if not source_path or not os.path.isfile(source_path):
            return ''

        install_dirs = self.default_font_install_dirs()
        if prefer_user_scope:
            install_dirs = sorted(install_dirs, key=lambda path: 0 if self._is_user_font_dir(path) else 1)

        for font_dir in install_dirs:
            try:
                os.makedirs(font_dir, exist_ok=True)
                destination = os.path.normpath(os.path.join(font_dir, os.path.basename(source_path)))
                if os.path.exists(destination):
                    return destination
                shutil.copy2(source_path, destination)
                self._refresh_font_cache_for_dir(font_dir)
                return destination
            except OSError:
                continue

        return ''

    def ensure_project_font_installed(
        self,
        font_name: str,
        module_dir: Optional[str] = None,
        *,
        prefer_user_scope: bool = True,
    ) -> str:
        font_path = self.resolve_font_path(font_name, module_dir)
        if not font_path:
            return ''
        return self.install_font_file(font_path, prefer_user_scope=prefer_user_scope)

    @staticmethod
    def _refresh_font_cache_for_dir(font_dir: str) -> None:
        if platform.system().lower() != 'linux':
            return
        if not shutil.which('fc-cache'):
            return
        try:
            subprocess.run(['fc-cache', '-f', font_dir], check=False, capture_output=True, text=True)
        except OSError:
            return

    def build_workflow_font(self, font_name: str, point_size: int = 20, module_dir: Optional[str] = None) -> qtg.QFont:
        preferred_font = self.get_active_project_font() or str(font_name or "").strip()
        if not preferred_font:
            preferred_font = "FROMVS [MAXR]"

        font_family = self.register_application_font(preferred_font, module_dir)
        font = qtg.QFont(font_family)
        font.setPointSize(point_size)
        return font

    def get_active_project_font(self, filename: str = 'Session.json') -> str:
        active_root = self.get_active_project_root(filename)
        if not active_root:
            return self.DEFAULT_PROJECT_FONT

        sqlite_candidates = (
            os.path.join(active_root, "Model", "Project", "Data", "sqlite", "project_metadata.sqlite"),
            os.path.join(active_root, "Model", "Project", "Data", "SQLite", "project_metadata.sqlite"),
            os.path.join(active_root, "project_metadata.sqlite"),
        )

        for sqlite_path in sqlite_candidates:
            if not os.path.exists(sqlite_path):
                continue
            try:
                with sqlite3.connect(sqlite_path) as conn:
                    cursor = conn.execute("SELECT ProjectFont FROM project_metadata LIMIT 1")
                    row = cursor.fetchone()
                    if row and row[0]:
                        return str(row[0]).strip()
            except sqlite3.Error:
                continue

        json_candidates = (
            os.path.join(active_root, "Model", "Project", "Data", "json", "project_metadata.json"),
            os.path.join(active_root, "project_metadata.json"),
        )
        for json_path in json_candidates:
            if not os.path.exists(json_path):
                continue
            try:
                with open(json_path, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                if isinstance(payload, dict):
                    value = payload.get("ProjectFont")
                    if value:
                        return str(value).strip()
            except (OSError, ValueError, TypeError):
                continue

        return self.DEFAULT_PROJECT_FONT

    def _module_handshakes_path(self, project_root: str) -> str:
        candidates = (
            os.path.join(project_root, "Model", "Project", "Data", "csv", "module_handshakes.csv"),
            os.path.join(project_root, "Model", "Project", "Images", "MyServer", "Workflow", "module_handshakes.csv"),
        )
        for path in candidates:
            if os.path.exists(path):
                return path
        return ""

    def _read_module_handshake_rows(self, project_root: str) -> List[Dict[str, str]]:
        csv_path = self._module_handshakes_path(project_root)
        if not csv_path:
            return []

        rows: List[Dict[str, str]] = []
        try:
            with open(csv_path, "r", encoding="utf-8", newline="") as handle:
                first_line = handle.readline().strip()
                handle.seek(0)

                if "," in first_line:
                    reader = csv.DictReader(handle)
                    for row in reader:
                        if isinstance(row, dict):
                            rows.append({str(k): str(v or "") for k, v in row.items() if k})
                    return rows

                for index, raw_line in enumerate(handle):
                    line = raw_line.strip()
                    if not line:
                        continue
                    if index == 0 and line.lower().startswith("milestonename "):
                        continue

                    parts = line.split()
                    if len(parts) < 8:
                        continue

                    rows.append(
                        {
                            "MilestoneName": parts[0],
                            "UI_Action": parts[1],
                            "Override": parts[2],
                            "Language": parts[3],
                            "InputPath": parts[4],
                            "InputModule": parts[5],
                            "OutputModule": parts[6],
                            "OutputPath": parts[7],
                        }
                    )
        except OSError:
            return []

        return rows

    @staticmethod
    def _to_absolute_project_path(project_root: str, path_value: str) -> str:
        normalized = str(path_value or "").strip()
        if not normalized:
            return ""
        if os.path.isabs(normalized):
            return os.path.normpath(normalized)
        return os.path.normpath(os.path.join(project_root, normalized.lstrip("/\\")))

    @staticmethod
    def _workflow_to_complete_path(path_value: str) -> str:
        normalized = str(path_value or "").strip()
        if not normalized:
            return ""

        replacements = (
            ("/Workflow/", "/Complete/"),
            ("\\Workflow\\", "\\Complete\\"),
            ("/workflow/", "/complete/"),
            ("\\workflow\\", "\\complete\\"),
        )
        for old, new in replacements:
            if old in normalized:
                return normalized.replace(old, new)
        return normalized

    def resolve_receiving_default_input(
        self,
        receiving_module: str,
        preferred_input_modules: Optional[Iterable[str]] = None,
        language_hint: str = "greek",
        *,
        prefer_complete: bool = True,
        filename: str = "Session.json",
    ) -> str:
        module_name = str(receiving_module or "").strip().lower()
        if not module_name:
            return ""

        project_root = self.get_active_project_root(filename)
        if not project_root:
            project_root = os.path.normpath(os.path.join(self.base_dir, "..", "..", "..", ".."))

        rows = self._read_module_handshake_rows(project_root)
        if not rows:
            return ""

        candidates = [
            row for row in rows if str(row.get("OutputModule", "")).strip().lower() == module_name
        ]
        if not candidates:
            return ""

        normalized_language = str(language_hint or "").strip().lower()
        if normalized_language:
            language_filtered = [
                row for row in candidates if str(row.get("Language", "")).strip().lower() == normalized_language
            ]
            if language_filtered:
                candidates = language_filtered

        prioritized: List[Dict[str, str]] = []
        used_ids = set()
        preferred_modules = [str(item).strip().lower() for item in (preferred_input_modules or ()) if str(item).strip()]
        if preferred_modules:
            for preferred in preferred_modules:
                for row in candidates:
                    if str(row.get("InputModule", "")).strip().lower() != preferred:
                        continue
                    row_key = id(row)
                    if row_key in used_ids:
                        continue
                    prioritized.append(row)
                    used_ids.add(row_key)

        for row in candidates:
            row_key = id(row)
            if row_key in used_ids:
                continue
            prioritized.append(row)
            used_ids.add(row_key)

        fallback_path = ""
        for row in prioritized:
            input_path = str(row.get("InputPath", "")).strip()
            if not input_path:
                continue

            path_candidates = []
            if prefer_complete:
                path_candidates.append(self._workflow_to_complete_path(input_path))
            path_candidates.append(input_path)

            for candidate_path in path_candidates:
                absolute_candidate = self._to_absolute_project_path(project_root, candidate_path)
                if not absolute_candidate:
                    continue
                if not fallback_path:
                    fallback_path = absolute_candidate
                if os.path.isdir(absolute_candidate):
                    return absolute_candidate

        return fallback_path
