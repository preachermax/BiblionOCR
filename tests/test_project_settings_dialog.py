from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5 import QtWidgets as qtw


ROOT_DIR = Path(__file__).resolve().parents[1]
HELPERS_DIR = ROOT_DIR / "ViewController" / "0-MainUI" / "helpers"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(HELPERS_DIR) not in sys.path:
    sys.path.insert(0, str(HELPERS_DIR))

from Dialogs.ProjectSettingsDialog import ProjectSettingsDialog
from SessionManager import SessionManager


def test_dialog_opens_before_ris_table_is_initialized(tmp_path) -> None:
    app = qtw.QApplication.instance() or qtw.QApplication([])
    project_root = tmp_path / "NewProject"
    data_dir = project_root / "Model" / "Project" / "Data"
    settings_db = data_dir / "sqlite" / "Project Settings.db"
    session_dir = data_dir / "json"
    settings_db.parent.mkdir(parents=True)
    session_dir.mkdir(parents=True)
    with sqlite3.connect(settings_db):
        pass

    dialog = ProjectSettingsDialog(
        str(project_root),
        SessionManager(base_dir=str(session_dir)),
    )

    assert dialog.windowTitle() == "Project Settings"
    assert dialog.ris_table.rowCount() > 0
    assert app is not None
    dialog.close()