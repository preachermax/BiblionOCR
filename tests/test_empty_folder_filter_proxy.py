import importlib.util
import os
import sys
from pathlib import Path

from PyQt5 import QtWidgets


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "ViewController" / "0-MainUI" / "helpers" / "LocalFileDrop.py"
SPEC = importlib.util.spec_from_file_location("local_file_drop", MODULE_PATH)
LOCAL_FILE_DROP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LOCAL_FILE_DROP)


def test_exclude_empty_dirs_filters_empty_directories(tmp_path):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    root_dir = tmp_path / "project"
    empty_dir = root_dir / "empty"
    filled_dir = root_dir / "filled"
    empty_dir.mkdir(parents=True)
    filled_dir.mkdir(parents=True)
    (filled_dir / "notes.txt").write_text("hello", encoding="utf-8")

    model = QtWidgets.QFileSystemModel()
    model.setRootPath(str(root_dir))

    proxy = LOCAL_FILE_DROP.EmptyFolderFilterProxyModel()
    proxy.setSourceModel(model)
    proxy.setExcludeEmptyDirs(True)

    source_root_index = model.index(str(root_dir))
    proxy_root_index = proxy.mapFromSource(source_root_index)

    assert proxy.rowCount(proxy_root_index) == 1
    visible_name = proxy.data(proxy.index(0, 0, proxy_root_index))
    assert visible_name == "filled"
    assert proxy.excludeEmptyDirs() is True
