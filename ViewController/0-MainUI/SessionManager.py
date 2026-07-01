import os
import json
import platform
from typing import Any, Callable, Dict, Iterable, List, Optional, Union

from PyQt5 import QtGui as qtg

JSONItem = Dict[str, Any]
SessionDict = Dict[str, JSONItem]
SettingMap = Dict[str, Union[str, Callable[[Any], None]]]


def normalize_path(path: str) -> str:
    return os.path.abspath(os.path.expanduser(path))


class SessionManager:
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

    def build_workflow_font(self, font_name: str, point_size: int = 20, module_dir: Optional[str] = None) -> qtg.QFont:
        font_family = self.register_application_font(font_name, module_dir)
        font = qtg.QFont(font_family)
        font.setPointSize(point_size)
        return font
