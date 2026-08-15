"""Runtime environment helpers for GUI entry points.

When launched from certain sandboxed shells (for example Snap-based editors),
runtime linker variables can point at incompatible libc/libpthread versions.
This module normalizes those variables and re-execs once when needed.
"""

from __future__ import annotations

import os
import sys


_SANITIZED_MARKER = "BIBLION_GUI_ENV_SANITIZED"
_QT_FONT_POLICY_INSTALLED = False
_FONT_DISABLE_ENV = "BIBLION_DISABLE_DEFAULT_QT_FONT"
_FONT_OVERRIDE_ENV = "BIBLION_DEFAULT_QT_FONT"


def sanitize_current_process_and_reexec() -> None:
    """Sanitize process environment and re-exec once if required."""

    if os.environ.get(_SANITIZED_MARKER) == "1":
        return

    env = dict(os.environ)
    changed = False
    snap_contamination_detected = False

    def _strip_snap_paths(var_name: str) -> None:
        nonlocal changed, snap_contamination_detected
        value = env.get(var_name)
        if not value:
            return

        filtered = [segment for segment in value.split(":") if "/snap/" not in segment]
        new_value = ":".join(segment for segment in filtered if segment)

        if new_value == value:
            return

        changed = True
        snap_contamination_detected = True
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
            snap_contamination_detected = True
            env.pop(var_name, None)
            continue

        if isinstance(value, str) and "/snap/" in value and var_name.startswith(("GTK_", "GIO_", "GDK_")):
            changed = True
            snap_contamination_detected = True
            env.pop(var_name, None)

    # Keep system IME behavior by default for multilingual keyboard support.
    # Use BIBLION_QT_IM_MODULE to force a backend in packaged releases.
    # If no backend is configured, choose a stable fallback on Linux to avoid
    # early Qt startup warnings and to keep IME handling predictable across
    # desktop shells and Snap-hosted launches.
    if sys.platform.startswith("linux"):
        requested_im = env.get("BIBLION_QT_IM_MODULE", "").strip()
        if requested_im:
            lowered = requested_im.lower()
            if lowered in ("auto", "system"):
                pass
            elif lowered == "unset":
                if "QT_IM_MODULE" in env:
                    changed = True
                    env.pop("QT_IM_MODULE", None)
            elif env.get("QT_IM_MODULE") != requested_im:
                changed = True
                env["QT_IM_MODULE"] = requested_im
        elif env.get("QT_IM_MODULE", "") != "xim":
            changed = True
            env["QT_IM_MODULE"] = "xim"

    env[_SANITIZED_MARKER] = "1"

    if changed:
        os.execve(sys.executable, [sys.executable] + sys.argv, env)

    os.environ[_SANITIZED_MARKER] = "1"
    install_default_qt_font_policy()


def install_default_qt_font_policy() -> None:
    """Install a shared Qt application-font policy for canonical GUI entrypoints."""

    global _QT_FONT_POLICY_INSTALLED
    if _QT_FONT_POLICY_INSTALLED:
        return

    try:
        from PyQt5 import QtGui as qtg
        from PyQt5 import QtWidgets as qtw
    except Exception:
        return

    original_init = qtw.QApplication.__init__

    def patched_init(app_self, *args, **kwargs):
        original_init(app_self, *args, **kwargs)
        _apply_default_qt_font(app_self, qtg, qtw)

    qtw.QApplication.__init__ = patched_init
    _QT_FONT_POLICY_INSTALLED = True

    existing_app = qtw.QApplication.instance()
    if existing_app is not None:
        _apply_default_qt_font(existing_app, qtg, qtw)


def _apply_default_qt_font(app, qtg, qtw) -> None:
    """Apply the default project font to a QApplication when available."""

    font = _resolve_default_qt_font(qtg)
    if font is None:
        return

    app.setFont(font)
    qtw.QToolTip.setFont(qtg.QFont(font))


def _resolve_default_qt_font(qtg):
    """Resolve the configured default Qt font, preferring the bundled FROMVS.ttf."""

    requested_family = os.environ.get(_FONT_OVERRIDE_ENV, "").strip()
    if os.environ.get(_FONT_DISABLE_ENV, "").strip() == "1":
        return None

    if requested_family.lower() in {"default", "system", "unset"}:
        return None

    font_db = qtg.QFontDatabase()
    available_families = set(font_db.families())

    if requested_family:
        if requested_family not in available_families:
            return None
        return qtg.QFont(requested_family)

    bundled_font_path = os.path.join(os.path.dirname(__file__), "fonts", "FROMVS.ttf")
    if os.path.isfile(bundled_font_path):
        font_id = qtg.QFontDatabase.addApplicationFont(bundled_font_path)
        if font_id != -1:
            loaded_families = qtg.QFontDatabase.applicationFontFamilies(font_id)
            if loaded_families:
                return qtg.QFont(loaded_families[0])

    if "FROMVS" in available_families:
        return qtg.QFont("FROMVS")

    return None
