from __future__ import annotations

import json
import os
import platform
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from PyQt5 import QtCore as qtc
from PyQt5 import QtWidgets as qtw


IGNORED_NAMES = {
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".coverage",
}


class DevelopmentBackupDialog(qtw.QDialog):
    """Developer-only snapshot and staged-restore utility."""

    def __init__(self, workspace_root=None, parent=None):
        super().__init__(parent)
        self.workspace_root = Path(workspace_root or Path(__file__).resolve().parents[2]).resolve()
        self.setWindowTitle("Development Backup and Restore")
        self.setMinimumWidth(520)

        layout = qtw.QVBoxLayout(self)
        description = qtw.QLabel(
            "Create a development snapshot or restore one into a new staged folder. "
            "Restore never replaces the active workspace."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        self.status_label = qtw.QLabel("Ready")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        buttons = qtw.QDialogButtonBox(self)
        self.backup_button = buttons.addButton("Create Backup...", qtw.QDialogButtonBox.ActionRole)
        self.restore_button = buttons.addButton("Stage Restore...", qtw.QDialogButtonBox.ActionRole)
        close_button = buttons.addButton(qtw.QDialogButtonBox.Close)
        self.backup_button.clicked.connect(self.create_backup)
        self.restore_button.clicked.connect(self.stage_restore)
        close_button.clicked.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def development_backup_root(destination_root) -> Path:
        return Path(destination_root) / "BiblionOCR_Backups" / "Development"

    @staticmethod
    def copy_ignore(_current_dir, names):
        return {name for name in names if name in IGNORED_NAMES}

    @staticmethod
    def find_restore_payload(backup_snapshot_dir) -> Path | None:
        snapshot = Path(backup_snapshot_dir)
        preferred = snapshot / "BiblionOCR"
        if preferred.is_dir():
            return preferred
        if not snapshot.is_dir():
            return None
        return next(
            (child for child in snapshot.iterdir() if child.is_dir() and child.name.lower().startswith("biblion")),
            None,
        )

    def default_external_root(self) -> Path:
        user = os.environ.get("USER", "")
        candidates = []
        for base in (Path("/media") / user, Path("/run/media") / user, Path("/mnt")):
            if not base.is_dir():
                continue
            candidates.extend(path for path in base.iterdir() if os.path.ismount(path))

        def disk_size(path):
            try:
                return shutil.disk_usage(path).total
            except OSError:
                return -1

        return max(candidates, key=disk_size) if candidates else Path.home()

    def choose_directory(self, title, start_dir) -> Path | None:
        selected = qtw.QFileDialog.getExistingDirectory(self, title, str(start_dir))
        return Path(selected).resolve() if selected else None

    def copy_tree(self, source_dir, destination_dir) -> None:
        qtw.QApplication.setOverrideCursor(qtc.Qt.WaitCursor)
        self.status_label.setText(f"Copying {source_dir} to {destination_dir}")
        qtw.QApplication.processEvents()
        try:
            shutil.copytree(source_dir, destination_dir, ignore=self.copy_ignore)
        finally:
            qtw.QApplication.restoreOverrideCursor()

    def write_manifest(self, snapshot_dir, source_dir, payload_dir) -> None:
        manifest = {
            "process": "development",
            "module": "Developer.utilities.development_backup_dialog",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "source_dir": str(Path(source_dir).resolve()),
            "payload_dir": str(Path(payload_dir).resolve()),
            "host_platform": platform.platform(),
            "python": sys.version,
        }
        (Path(snapshot_dir) / "backup_manifest.json").write_text(
            json.dumps(manifest, indent=2),
            encoding="utf-8",
        )

    def create_backup(self) -> None:
        source_dir = self.choose_directory("Development Backup: Select source folder", self.workspace_root)
        if source_dir is None:
            return
        destination_root = self.choose_directory(
            "Development Backup: Select destination root",
            self.default_external_root(),
        )
        if destination_root is None:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_dir = self.development_backup_root(destination_root) / f"dev_backup_{timestamp}"
        payload_dir = snapshot_dir / source_dir.name
        response = qtw.QMessageBox.question(
            self,
            "Confirm Development Backup",
            f"Source:\n{source_dir}\n\nSnapshot:\n{snapshot_dir}",
            qtw.QMessageBox.Yes | qtw.QMessageBox.No,
            qtw.QMessageBox.Yes,
        )
        if response != qtw.QMessageBox.Yes:
            return

        try:
            snapshot_dir.mkdir(parents=True, exist_ok=False)
            self.copy_tree(source_dir, payload_dir)
            self.write_manifest(snapshot_dir, source_dir, payload_dir)
        except Exception as exc:
            qtw.QMessageBox.critical(self, "Development Backup Failed", str(exc))
            return
        self.status_label.setText(f"Backup created: {snapshot_dir}")
        qtw.QMessageBox.information(self, "Development Backup Complete", str(snapshot_dir))

    def stage_restore(self) -> None:
        snapshot_dir = self.choose_directory(
            "Development Restore: Select backup snapshot",
            self.development_backup_root(self.default_external_root()),
        )
        if snapshot_dir is None:
            return
        payload_dir = self.find_restore_payload(snapshot_dir)
        if payload_dir is None:
            qtw.QMessageBox.warning(
                self,
                "Development Restore",
                "The selected snapshot has no recognizable BiblionOCR payload.",
            )
            return
        restore_parent = self.choose_directory(
            "Development Restore: Select staging parent folder",
            self.workspace_root.parent,
        )
        if restore_parent is None:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        restore_target = restore_parent / f"BiblionOCR_dev_restore_{timestamp}"
        response = qtw.QMessageBox.question(
            self,
            "Confirm Development Restore",
            f"Payload:\n{payload_dir}\n\nNew staged folder:\n{restore_target}",
            qtw.QMessageBox.Yes | qtw.QMessageBox.No,
            qtw.QMessageBox.Yes,
        )
        if response != qtw.QMessageBox.Yes:
            return

        try:
            self.copy_tree(payload_dir, restore_target)
        except Exception as exc:
            qtw.QMessageBox.critical(self, "Development Restore Failed", str(exc))
            return
        self.status_label.setText(f"Restore staged: {restore_target}")
        qtw.QMessageBox.information(
            self,
            "Development Restore Complete",
            f"Review the staged restore before manual cutover:\n{restore_target}",
        )


def main() -> int:
    application = qtw.QApplication.instance() or qtw.QApplication(sys.argv)
    dialog = DevelopmentBackupDialog()
    dialog.show()
    return application.exec_()


if __name__ == "__main__":
    raise SystemExit(main())