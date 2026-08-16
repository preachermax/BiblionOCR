import os
import subprocess
import sys
import tempfile
import time

from PyQt5 import QtCore as qtc


def build_myexplorer_selection_command(title, start_dir, selection_kind="file", output_file=""):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    explorer_path = os.path.join(project_root, "ViewController", "0-MainUI", "MyExplorer.py")
    selected_output = output_file or os.path.join(
        tempfile.gettempdir(),
        f"biblion_myexplorer_select_{int(time.time() * 1000)}.txt",
    )
    selection_kind = str(selection_kind or "file").lower()
    modes = []
    if selection_kind in {"directory", "folder", "both"}:
        modes.append("--select-dir")
    if selection_kind in {"file", "both"}:
        modes.append("--select-file")
    if not modes:
        raise ValueError(f"Unsupported MyExplorer selection kind: {selection_kind}")
    command = [
        sys.executable,
        explorer_path,
        *modes,
        "--start-dir",
        str(start_dir or project_root),
        "--output-file",
        selected_output,
        "--title",
        str(title or "MyExplorer"),
    ]
    return command, selected_output


def read_myexplorer_selection(output_file, *, cleanup=True):
    selected_path = ""
    try:
        if os.path.isfile(output_file):
            with open(output_file, "r", encoding="utf-8") as handle:
                selected_path = handle.read().strip()
    except OSError:
        selected_path = ""
    finally:
        if cleanup:
            try:
                if os.path.exists(output_file):
                    os.remove(output_file)
            except OSError:
                pass
    return selected_path


def run_myexplorer_selection(title, start_dir, selection_kind="file"):
    command, output_file = build_myexplorer_selection_command(title, start_dir, selection_kind)
    try:
        process = subprocess.Popen(command)
    except OSError:
        return ""

    application = qtc.QCoreApplication.instance()
    if application is None:
        process.wait()
        return read_myexplorer_selection(output_file)

    waiter = qtc.QEventLoop()

    def check_completion():
        if process.poll() is not None:
            waiter.quit()
            return
        qtc.QTimer.singleShot(100, check_completion)

    qtc.QTimer.singleShot(0, check_completion)
    waiter.exec_()
    return read_myexplorer_selection(output_file)