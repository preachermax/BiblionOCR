import os
import sys


SCRUB_KEYS = (
    "GTK_IM_MODULE",
    "GTK_MODULES",
    "GTK_PATH",
    "GTK_EXE_PREFIX",
    "GTK_IM_MODULE_FILE",
    "GIO_MODULE_DIR",
    "GSETTINGS_SCHEMA_DIR",
    "GI_TYPELIB_PATH",
    "LD_LIBRARY_PATH",
    "LOCPATH",
    "PYTHONHOME",
    "QML2_IMPORT_PATH",
    "QT_ACCESSIBILITY",
    "QT_IM_MODULE",
    "QT_IM_MODULES",
    "QT_LINUX_ACCESSIBILITY_ALWAYS_ON",
    "QT_PLUGIN_PATH",
    "QT_QPA_PLATFORMTHEME",
    "QT_STYLE_OVERRIDE",
)
SNAP_MARKERS = ("/snap/code/", "/var/lib/snapd/")
REEXEC_MARKER = "BIBLION_SANITIZED_GUI_ENV"


def build_sanitized_env(base_env=None):
    updated_env = dict(os.environ if base_env is None else base_env)

    for key in SCRUB_KEYS:
        value = updated_env.get(key)
        if value and any(marker in value for marker in SNAP_MARKERS):
            updated_env.pop(key, None)

    for key in ("QT_IM_MODULE", "QT_IM_MODULES", "GTK_IM_MODULE"):
        value = updated_env.get(key)
        if value and "ibus" in value.lower():
            updated_env.pop(key, None)

    for key in ("QT_ACCESSIBILITY", "QT_LINUX_ACCESSIBILITY_ALWAYS_ON"):
        updated_env.pop(key, None)

    xdg_data_dirs = updated_env.get("XDG_DATA_DIRS")
    if xdg_data_dirs:
        filtered_dirs = [
            entry
            for entry in xdg_data_dirs.split(":")
            if entry and not any(marker in entry for marker in SNAP_MARKERS)
        ]
        if filtered_dirs:
            updated_env["XDG_DATA_DIRS"] = ":".join(filtered_dirs)
        else:
            updated_env.pop("XDG_DATA_DIRS", None)

    return updated_env


def sanitize_current_process_and_reexec():
    if os.environ.get(REEXEC_MARKER) == "1":
        return

    updated_env = build_sanitized_env()
    if updated_env == dict(os.environ):
        return

    updated_env[REEXEC_MARKER] = "1"
    os.execvpe(sys.executable, [sys.executable, *sys.argv], updated_env)
