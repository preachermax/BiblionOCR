# -*- coding: utf-8 -*-

"""Repository-level compatibility shim for the generated Qt resource module."""

from __future__ import annotations

import importlib.util
import os
import sys


_RESOURCE_PATHS = (
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "ViewController", "0-MainUI", "UI_Icons.py"),
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "ViewController", "0-MainUI", "helpers", "UI_Icons.py"),
)


def _load_resource_module():
    for resource_path in _RESOURCE_PATHS:
        if not os.path.exists(resource_path):
            continue

        spec = importlib.util.spec_from_file_location("biblion_ui_icons", resource_path)
        if spec is None or spec.loader is None:
            continue

        module = importlib.util.module_from_spec(spec)
        sys.modules.setdefault("biblion_ui_icons", module)
        spec.loader.exec_module(module)
        return module

    raise ImportError("Unable to locate a generated UI_Icons resource module")


_RESOURCE_MODULE = _load_resource_module()

for _name in dir(_RESOURCE_MODULE):
    if _name.startswith("_"):
        continue
    globals()[_name] = getattr(_RESOURCE_MODULE, _name)
