from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "Developer" / "update_ui_resources.py"


def _load_generator_module():
    specification = importlib.util.spec_from_file_location("update_ui_resources_test", MODULE_PATH)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


def test_identical_generated_content_preserves_target_timestamp(tmp_path) -> None:
    generator = _load_generator_module()
    target = tmp_path / "GeneratedUI.py"
    target.write_bytes(b"generated content\n")
    original_timestamp = 1_700_000_000_000_000_000
    os.utime(target, ns=(original_timestamp, original_timestamp))

    status = generator._replace_if_changed(target, b"generated content\n", check_only=False)

    assert status == "unchanged"
    assert target.stat().st_mtime_ns == original_timestamp


def test_changed_generated_content_replaces_target(tmp_path) -> None:
    generator = _load_generator_module()
    target = tmp_path / "GeneratedUI.py"
    target.write_bytes(b"old content\n")

    status = generator._replace_if_changed(target, b"new content\n", check_only=False)

    assert status == "updated"
    assert target.read_bytes() == b"new content\n"


def test_check_only_reports_stale_without_writing(tmp_path) -> None:
    generator = _load_generator_module()
    target = tmp_path / "GeneratedUI.py"
    target.write_bytes(b"old content\n")

    status = generator._replace_if_changed(target, b"new content\n", check_only=True)

    assert status == "stale"
    assert target.read_bytes() == b"old content\n"


def test_mypixler_ui_uses_canonical_preprocess_target() -> None:
    generator = _load_generator_module()
    mappings = {
        item.source: item.target
        for item in generator.GENERATED_FILES
    }

    assert mappings["Developer/QtDesignerUI/MyPixlerUI.ui"] == (
        "ViewController/1-PreProcess/MyPixlerUI.py"
    )
    assert "ViewController/0-MainUI/MyPixlerUI.py" in generator.RETIRED_GENERATED_TARGETS


def test_retired_generated_target_is_removed_or_reported(tmp_path) -> None:
    generator = _load_generator_module()
    retired_target = tmp_path / "MyPixlerUI.py"
    retired_target.write_text("stale", encoding="utf-8")

    assert generator._remove_retired_target(retired_target, check_only=True) == "stale"
    assert retired_target.exists()
    assert generator._remove_retired_target(retired_target, check_only=False) == "removed"
    assert not retired_target.exists()
    assert generator._remove_retired_target(retired_target, check_only=False) == "absent"