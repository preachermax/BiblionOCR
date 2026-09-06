import re
import csv
import sys
import os
from pathlib import Path

# Built-in GUI modules for the file picker dialog
import tkinter as tk
from tkinter import filedialog

def prompt_for_file():
    """Launches a native OS file picker to let the user select a Python script."""
    root = tk.Tk()
    root.withdraw()  # Hide the main tiny tkinter window
    root.attributes('-topmost', True)  # Bring the dialog window to the front

    selected_file = filedialog.askopenfilename(
        title="Select your PyQt5 Python Script",
        filetypes=[("Python Files", "*.py"), ("All Files", "*.*")]
    )
    return selected_file

def extract_pyqt5_structure(file_path):
    if not file_path or not os.path.exists(file_path):
        print("Error: No valid target file selected or provided.")
        sys.exit(1)

    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()

    # 1. Find all declared method names
    methods = re.findall(r'def\s+(\w+)\s*\(', code)

    # 2. Extract UI trigger signals
    connections = re.findall(r'(?:self\.)?(\w+)\.(\w+)\.connect\((?:self\.)?(\w+)\)', code)
    trigger_map = {}
    for widget, signal, method in connections:
        trigger_map[method] = f"{widget}.{signal}"

    # 3. Extract keyboard shortcuts
    shortcut_matches = re.findall(r'(?:self\.)?(\w+)\.setShortcut\((?:QKeySequence\()?["\']([^"\']+)["\']', code)
    shortcut_map = {}
    for var_name, shortcut_key in shortcut_matches:
        shortcut_map[var_name] = shortcut_key

    # 4. Map shortcuts back to the method handler via the UI element link
    method_shortcut_map = {}
    for widget, signal, method in connections:
        if widget in shortcut_map:
            method_shortcut_map[method] = shortcut_map[widget]

    # Centralized Routing to Desktop
    output_dir = Path.home() / "Desktop"
    base_name = Path(file_path).stem
    output_csv = output_dir / f"{base_name}_inventory.csv"

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Method Name", "UI Element & Trigger Signal", "Keyboard Shortcut"])

        for method in methods:
            if method != "__init__":
                trigger = trigger_map.get(method, "None (Internal Call / Lifecycle)")
                shortcut = method_shortcut_map.get(method, "None")
                writer.writerow([method, trigger, shortcut])

    print(f"\nSuccess! Generated spreadsheet artifact at: {output_csv}")

if __name__ == "__main__":
    # --- FLEXIBLE ROUTING LOGIC ---
    # 1. Look for terminal/VS Code arguments first
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
        print(f"Processing VS Code active file pipeline: {target_file}")
    # 2. Launch the visual dialog box if run by double-clicking or simple terminal execution
    else:
        print("No file argument detected. Opening graphical file picker...")
        target_file = prompt_for_file()

    extract_pyqt5_structure(target_file)
