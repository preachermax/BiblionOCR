import importlib.util
import os
import sys
from pathlib import Path
from unittest import mock

from PyQt5 import QtCore as qtc


ROOT = Path(__file__).resolve().parents[1]
HELPERS_DIR = ROOT / "ViewController" / "0-MainUI" / "helpers"
MYPIXLER_DIR = ROOT / "ViewController" / "1-PreProcess"
if str(HELPERS_DIR) not in sys.path:
	sys.path.insert(0, str(HELPERS_DIR))
if str(MYPIXLER_DIR) not in sys.path:
	sys.path.insert(0, str(MYPIXLER_DIR))

SPEC = importlib.util.spec_from_file_location(
	"test_pixler_handoff_module",
	HELPERS_DIR / "pixler_handoff.py",
)
assert SPEC is not None
assert SPEC.loader is not None
HANDOFF = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HANDOFF)

PIXLER_SPEC = importlib.util.spec_from_file_location(
	"test_pixler_handoff_pixler_module",
	MYPIXLER_DIR / "MyPixler.py",
)
assert PIXLER_SPEC is not None
assert PIXLER_SPEC.loader is not None
MYPIXLER = importlib.util.module_from_spec(PIXLER_SPEC)
PIXLER_SPEC.loader.exec_module(MYPIXLER)


class FakeOwner(qtc.QObject):
	def __init__(self, image_path):
		super().__init__()
		self.imgpath = str(image_path)
		self.shown_paths = []

	def showImage(self, image_path):
		self.shown_paths.append(image_path)


def test_handoff_launches_pixler_with_caller_source_and_return_path(tmp_path) -> None:
	source_path = tmp_path / "page.tif"
	source_path.write_bytes(b"source")
	pixler_script = tmp_path / "MyPixler.py"
	pixler_script.write_text("", encoding="utf-8")
	owner = FakeOwner(source_path)
	controller = HANDOFF.PixlerHandoffController(owner, "MyBoxer", str(pixler_script))

	with mock.patch.object(HANDOFF.subprocess, "Popen", return_value=mock.Mock(pid=42)) as popen:
		assert controller.launch()

	command = popen.call_args.args[0]
	assert command[0] == sys.executable
	assert command[1] == str(pixler_script)
	assert command[2:4] == ["--subprocess-mode", "--return-path"]
	assert command[4] == controller.return_path
	assert command[5:] == ["--caller", "MyBoxer", str(source_path)]
	assert controller.poll_timer.isActive()
	controller.poll_timer.stop()


def test_handoff_overwrites_and_refreshes_calling_module(tmp_path) -> None:
	source_path = tmp_path / "page.tif"
	source_path.write_bytes(b"source")
	return_path = tmp_path / "returned.tif"
	return_path.write_bytes(b"edited")
	owner = FakeOwner(source_path)
	controller = HANDOFF.PixlerHandoffController(owner, "MyGlypher")
	controller.source_path = str(source_path)
	controller.return_path = str(return_path)

	assert controller._overwrite_source()

	assert source_path.read_bytes() == b"edited"
	assert owner.shown_paths == [str(source_path)]


def test_mypixler_parses_caller_neutral_return_contract(tmp_path) -> None:
	source_path = tmp_path / "page.tif"
	return_path = tmp_path / "returned.tif"

	parsed = MYPIXLER.PixlerMain._parse_launch_arguments(
		None,
		[
			"--subprocess-mode",
			"--return-path",
			str(return_path),
			"--caller",
			"MyReader",
			str(source_path),
		],
	)

	assert parsed == (
		str(source_path),
		True,
		str(return_path),
		"MyReader",
	)


def test_live_image_modules_delegate_to_shared_handoff() -> None:
	module_callers = {
		ROOT / "ViewController" / "0-MainUI" / "MyScanner.py": "MyScanner",
		ROOT / "ViewController" / "1-PreProcess" / "MyBoxer.py": "MyBoxer",
		ROOT / "ViewController" / "1-PreProcess" / "MyGlypher.py": "MyGlypher",
		ROOT / "ViewController" / "2-TrainTesseract" / "MyReader.py": "MyReader",
		ROOT / "ViewController" / "3-Process" / "MyLexer.py": "MyLexer",
	}

	for module_path, caller in module_callers.items():
		source = module_path.read_text(encoding="utf-8")
		assert f'launch_pixler_handoff(self, "{caller}", self.imgpath)' in source
