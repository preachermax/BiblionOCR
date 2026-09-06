from __future__ import annotations

from pathlib import Path

from launchers.restore_desktop_launchers import build_generated_launchers, main


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_generated_launchers_include_ubuntu_taskbar_identity() -> None:
    launchers = build_generated_launchers(REPO_ROOT)

    expected = {
        "My Server.desktop": "MyServer.py",
        "Biblion Explorer.desktop": "MyExplorer.py",
        "Biblion Scanner.desktop": "MyScanner.py",
        "Biblion Boxer.desktop": "MyBoxer.py",
        "Biblion Glypher.desktop": "MyGlypher.py",
        "Biblion Grounder.desktop": "MyGrounder.py",
        "Biblion Launcher.desktop": "MyLauncher.py",
        "Biblion Pixler.desktop": "MyPixler.py",
        "Biblion Reader.desktop": "MyReader.py",
        "Biblion Resolver.desktop": "MyResolver.py",
        "Biblion Trainer.desktop": "MyTrainer.py",
        "Biblion Versifier.desktop": "MyVersifier.py",
        "Biblion Writer.desktop": "MyWriter.py",
    }
    for desktop_file, startup_wm_class in expected.items():
        entry = launchers[desktop_file]
        assert "StartupNotify=true" in entry
        assert f"StartupWMClass={startup_wm_class}" in entry


def test_deferred_mylexer_launcher_remains_unchanged() -> None:
    entry = build_generated_launchers(REPO_ROOT)["Biblion Lexer.desktop"]

    assert "StartupNotify=" not in entry
    assert "StartupWMClass=" not in entry


def test_restore_keeps_only_greek_aliases_on_desktop(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        [
            "restore_desktop_launchers.py",
            "--repo-root",
            str(REPO_ROOT),
            "--home",
            str(tmp_path),
        ],
    )

    assert main() == 0

    generated = build_generated_launchers(REPO_ROOT)
    desktop_names = {path.name for path in (tmp_path / "Desktop").glob("*.desktop")}
    preferred_names = {name for name in generated if name.startswith("βιϐλιον ")}
    application_names = {
        path.name for path in (tmp_path / ".local" / "share" / "applications").glob("*.desktop")
    }

    assert len(desktop_names) == 14
    assert desktop_names == preferred_names
    assert set(generated) <= application_names