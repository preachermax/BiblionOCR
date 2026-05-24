import os
import json
from typing import Any, Callable, Dict, Iterable, Optional, Union

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

    def session_path(self, filename: str) -> str:
        return normalize_path(filename) if os.path.isabs(filename) else os.path.join(self.base_dir, filename)

    def load(self, filename: str, keys: Optional[Iterable[str]] = None) -> SessionDict:
        path = self.session_path(filename)
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        session = {item['Setting']: item for item in data}
        if keys is None:
            return session
        return {key: session[key] for key in keys if key in session}

    def values(self, filename: str, keys: Optional[Iterable[str]] = None) -> Dict[str, Any]:
        return {key: item.get('CurrentValue') for key, item in self.load(filename, keys).items()}

    def update(self, filename: str, updates: Dict[str, Any]) -> None:
        path = self.session_path(filename)
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
