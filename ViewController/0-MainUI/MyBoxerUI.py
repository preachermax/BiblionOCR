"""Compatibility shim for relocated module.

This keeps legacy imports and launch paths working after moving the real
implementation to ViewController/1-PreProcess.
"""

from pathlib import Path
import runpy

TARGET = Path(__file__).resolve().parents[1] / "1-PreProcess" / "MyBoxerUI.py"

if __name__ == "__main__":
    runpy.run_path(str(TARGET), run_name="__main__")
else:
    globals().update(runpy.run_path(str(TARGET)))
