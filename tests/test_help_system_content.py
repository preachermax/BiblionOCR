import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELP_SYSTEM_PATH = ROOT / "ViewController" / "0-MainUI" / "helpers" / "HelpSystem.py"


def _load_help_system():
    spec = importlib.util.spec_from_file_location("help_system_content_test", HELP_SYSTEM_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_myserver_help_documents_current_project_source_workflow() -> None:
    help_system = _load_help_system()
    help_text = "\n".join(help_system.PROGRAM_HELP["MyServer"].values())

    for expected_text in (
        "RIS import",
        "project details",
        "project settings",
        "milestones",
        "project folders",
        "PDF or multipage TIFF",
        "worker thread",
        "pdf_acq_src_image",
        "tif_acq_src_image",
        "source_images/provenance",
    ):
        assert expected_text in help_text


def test_mypixler_help_documents_shared_source_reader() -> None:
    help_system = _load_help_system()
    help_text = "\n".join(help_system.PROGRAM_HELP["MyPixler"].values())

    for expected_text in (
        "active project's PDF or multipage TIFF source document",
        "Display Source Document",
        "Dock, float, hide, and reopen",
        "Restore the active project source document at startup",
        "reader is for reference",
        "Fit to Width",
        "restores the main window's original size",
    ):
        assert expected_text in help_text