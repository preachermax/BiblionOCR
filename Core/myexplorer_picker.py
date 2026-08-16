import os
import subprocess
import sys
import tempfile
import time


def build_myexplorer_selection_command(title, start_dir, selection_kind="file", output_file=""):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    explorer_path = os.path.join(project_root, "ViewController", "0-MainUI", "MyExplorer.py")
    selected_output = output_file or os.path.join(
        tempfile.gettempdir(),
        f"biblion_myexplorer_select_{int(time.time() * 1000)}.txt",
    )
    mode = "--select-dir" if selection_kind == "directory" else "--select-file"
    command = [
        sys.executable,
        explorer_path,
        mode,
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
        subprocess.run(command, check=False)
    except OSError:
        return ""
    return read_myexplorer_selection(output_file)