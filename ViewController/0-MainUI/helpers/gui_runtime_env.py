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
_QT_APPLICATION_IDENTITIES = {
    "MyServer": ("My Server", "My Server"),
    "MyExplorer": ("Biblion Explorer", "Biblion Explorer"),
    "MyBoxer": ("Biblion Boxer", "Biblion Boxer"),
    "MyGlypher": ("Biblion Glypher", "Biblion Glypher"),
    "MyGrounder": ("Biblion Grounder", "Biblion Grounder"),
    "MyLauncher": ("Biblion Launcher", "Biblion Launcher"),
    "MyPixler": ("Biblion Pixler", "Biblion Pixler"),
    "MyReader": ("Biblion Reader", "Biblion Reader"),
    "MyResolver": ("Biblion Resolver", "Biblion Resolver"),
    "MyScanner": ("Biblion Scanner", "Biblion Scanner"),
    "MyTrainer": ("Biblion Trainer", "Biblion Trainer"),
    "MyVersifier": ("Biblion Versifier", "Biblion Versifier"),
    "MyWriter": ("Biblion Writer", "Biblion Writer"),
}
_QT_APPLICATION_ICONS = {
    "MyServer": "BiblionServer.png",
    "MyExplorer": "BiblionExplorer.png",
    "MyBoxer": "BiblionBoxer2.png",
    "MyGlypher": "BiblionGlypher.png",
    "MyGrounder": "BiblionGrounder.png",
    "MyLauncher": "BiblionLauncher.png",
    "MyPixler": "BiblionPixler1.png",
    "MyReader": "BiblionReader2.png",
    "MyResolver": "BiblionResolver2.png",
    "MyScanner": "BiblionScanner1.png",
    "MyTrainer": "BiblionTrainer1.png",
    "MyVersifier": "BiblionVersifier2.png",
    "MyWriter": "BiblionWriter1.png",
}
_WINDOWS_APP_ID_PREFIX = "preachermax.BiblionOCR"


def sanitize_current_process_and_reexec() -> None:
    """Sanitize process environment and re-exec once if required."""

    if os.environ.get(_SANITIZED_MARKER) == "1":
        install_default_qt_font_policy()
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
        from PyQt5 import QtCore as qtc
        from PyQt5 import QtGui as qtg
        from PyQt5 import QtWidgets as qtw
    except Exception:
        return

    original_init = qtw.QApplication.__init__

    def patched_init(app_self, *args, **kwargs):
        _prepare_qt_application_identity(qtc)
        original_init(app_self, *args, **kwargs)
        _apply_qt_application_identity(app_self)
        _apply_qt_application_icon_policy(app_self, qtc, qtg)
        _apply_default_qt_font(app_self, qtg, qtw)

    qtw.QApplication.__init__ = patched_init
    _QT_FONT_POLICY_INSTALLED = True

    existing_app = qtw.QApplication.instance()
    if existing_app is not None:
        _apply_qt_application_identity(existing_app)
        _apply_qt_application_icon_policy(existing_app, qtc, qtg)
        _apply_default_qt_font(existing_app, qtg, qtw)


def _qt_application_identity():
    module_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    identity = _QT_APPLICATION_IDENTITIES.get(module_name)
    if identity is None:
        return None
    desktop_file_name, display_name = identity
    return module_name, desktop_file_name, display_name


def _prepare_qt_application_identity(qtc) -> None:
    """Set platform taskbar identity before QApplication initializes."""

    identity = _qt_application_identity()
    if identity is None:
        return
    module_name, _desktop_file_name, _display_name = identity
    qtc.QCoreApplication.setApplicationName(f"{module_name}.py")
    _set_windows_app_user_model_id(module_name)


def _apply_qt_application_identity(app) -> None:
    """Expose a stable Linux desktop identity for launcher/taskbar matching."""

    identity = _qt_application_identity()
    if identity is None:
        return

    _module_name, desktop_file_name, display_name = identity
    app.setApplicationDisplayName(display_name)
    app.setDesktopFileName(desktop_file_name)


def _set_windows_app_user_model_id(module_name) -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            f"{_WINDOWS_APP_ID_PREFIX}.{module_name}"
        )
    except (AttributeError, OSError):
        pass


def _application_icon_path(module_name):
    icon_name = _QT_APPLICATION_ICONS.get(module_name)
    if icon_name is None:
        return None
    return os.path.join(os.path.dirname(__file__), "Icons", icon_name)


def _apply_qt_application_icon_policy(app, qtc, qtg) -> None:
    identity = _qt_application_identity()
    if identity is None:
        return

    icon_path = _application_icon_path(identity[0])
    if icon_path is None or not os.path.isfile(icon_path):
        return
    icon = qtg.QIcon(icon_path)
    if icon.isNull():
        return

    app.setWindowIcon(icon)
    for window in app.topLevelWidgets():
        window.setWindowIcon(icon)

    if getattr(app, "_biblion_window_icon_filter", None) is not None:
        return

    class WindowIconFilter(qtc.QObject):
        def eventFilter(self, watched, event):
            if event.type() == qtc.QEvent.Show and getattr(watched, "isWindow", lambda: False)():
                watched.setWindowIcon(icon)
            return False

    icon_filter = WindowIconFilter(app)
    app.installEventFilter(icon_filter)
    app._biblion_window_icon_filter = icon_filter


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
