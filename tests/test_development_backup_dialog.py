from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from PyQt5 import QtWidgets as qtw

from Developer.extension_manager_dialog import DeveloperExtensionManagerDialog
from Developer.extension_registry import ExtensionRegistry
from Developer.utilities.development_backup_dialog import DevelopmentBackupDialog


ROOT = Path(__file__).resolve().parents[1]
DEVELOPER_ACTION_NAMES = {
    "actionDeveloper",
    "actionDevelopment_Backup",
    "actionDevelopment_Restore",
    "actionProduction_Backup_Restore",
}


def test_myserver_exposes_no_developer_actions_or_handlers() -> None:
    designer_root = ET.parse(ROOT / "Developer" / "QtDesignerUI" / "MyServerUI.ui").getroot()
    action_names = {action.get("name") for action in designer_root.findall(".//action")}
    assert DEVELOPER_ACTION_NAMES.isdisjoint(action_names)

    generated_ui = (ROOT / "ViewController" / "0-MainUI" / "MyServerUI.py").read_text(encoding="utf-8")
    runtime = (ROOT / "ViewController" / "0-MainUI" / "MyServer.py").read_text(encoding="utf-8")
    assert not any(action_name in generated_ui for action_name in DEVELOPER_ACTION_NAMES)
    assert "_install_backup_restore_actions" not in runtime
    assert "open_development_backup_dialog" not in runtime
    assert "open_development_restore_dialog" not in runtime
    assert "DeveloperServices" not in runtime


def test_developer_helper_copies_snapshot_and_writes_manifest(tmp_path) -> None:
    application = qtw.QApplication.instance() or qtw.QApplication([])
    source = tmp_path / "BiblionOCR"
    source.mkdir()
    (source / "README.md").write_text("snapshot", encoding="utf-8")
    ignored = source / ".venv"
    ignored.mkdir()
    (ignored / "ignored.txt").write_text("ignored", encoding="utf-8")

    snapshot = tmp_path / "snapshot"
    payload = snapshot / source.name
    snapshot.mkdir()
    dialog = DevelopmentBackupDialog(workspace_root=source)
    dialog.copy_tree(source, payload)
    dialog.write_manifest(snapshot, source, payload)

    assert (payload / "README.md").read_text(encoding="utf-8") == "snapshot"
    assert not (payload / ".venv").exists()
    manifest = json.loads((snapshot / "backup_manifest.json").read_text(encoding="utf-8"))
    assert manifest["module"] == "Developer.utilities.development_backup_dialog"
    assert Path(manifest["payload_dir"]) == payload.resolve()
    assert dialog.find_restore_payload(snapshot) == payload
    dialog.close()
    assert application is qtw.QApplication.instance()


def test_developer_services_extension_install_load_and_uninstall(tmp_path) -> None:
    application = qtw.QApplication.instance() or qtw.QApplication([])
    registry = ExtensionRegistry(install_root=tmp_path / "installed-extensions")
    bundled = registry.bundled_extensions()

    assert [extension.extension_id for extension in bundled] == ["developer-services"]
    assert [service.service_id for service in bundled[0].services] == ["backup-restore"]
    assert not registry.is_installed("developer-services")

    installed = registry.install("developer-services")
    assert installed.name == "Developer Services"
    assert registry.is_installed("developer-services")
    service_class = registry.load_service("developer-services", "backup-restore")
    assert service_class.__name__ == "DevelopmentBackupDialog"

    manager = DeveloperExtensionManagerDialog(registry)
    assert manager.extension_list.count() == 1
    assert manager.service_list.count() == 1
    assert manager.install_button.isEnabled() is False
    assert manager.uninstall_button.isEnabled() is True
    assert manager.open_button.isEnabled() is True
    manager.close()

    registry.uninstall("developer-services")
    assert not registry.is_installed("developer-services")
    with pytest.raises(ValueError):
        registry.uninstall("../../outside")
    assert application is qtw.QApplication.instance()