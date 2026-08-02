"""Runtime environment helpers for GUI entry points.

When launched from certain sandboxed shells (for example Snap-based editors),
runtime linker variables can point at incompatible libc/libpthread versions.
This module normalizes those variables and re-execs once when needed.
"""

from __future__ import annotations

import os
import sys


_SANITIZED_MARKER = "BIBLION_GUI_ENV_SANITIZED"


def sanitize_current_process_and_reexec() -> None:
    """Sanitize process environment and re-exec once if required."""

    if os.environ.get(_SANITIZED_MARKER) == "1":
        return

    env = dict(os.environ)
    changed = False

    def _strip_snap_paths(var_name: str) -> None:
        nonlocal changed
        value = env.get(var_name)
        if not value:
            return

        filtered = [segment for segment in value.split(":") if "/snap/" not in segment]
        new_value = ":".join(segment for segment in filtered if segment)

        if new_value == value:
            return

        changed = True
        if new_value:
            env[var_name] = new_value
        else:
            env.pop(var_name, None)

    for path_var in ("LD_LIBRARY_PATH", "GTK_PATH", "QT_PLUGIN_PATH", "QML2_IMPORT_PATH"):
        _strip_snap_paths(path_var)

    for var_name in ("PYTHONHOME", "PYTHONPATH"):
        if var_name in env:
            changed = True
            env.pop(var_name, None)

    for var_name, value in list(env.items()):
        if var_name.endswith("_VSCODE_SNAP_ORIG"):
            changed = True
            env.pop(var_name, None)
            continue

        if isinstance(value, str) and "/snap/" in value and var_name.startswith(("GTK_", "GIO_", "GDK_")):
            changed = True
            env.pop(var_name, None)

    env[_SANITIZED_MARKER] = "1"

    if changed:
        os.execve(sys.executable, [sys.executable] + sys.argv, env)

    os.environ[_SANITIZED_MARKER] = "1"
