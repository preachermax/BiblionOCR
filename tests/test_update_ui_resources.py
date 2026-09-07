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