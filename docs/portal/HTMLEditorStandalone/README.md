# HTML Editor Standalone Bundle

This folder contains the portable HTML editor bundle prepared from the BiblionOCR desktop project so it can be copied into the Biblion Portal Django project.

## Included Files

- `HTMLeditor.py`: main editor controller and runtime behavior
- `HTMLeditorUI.py`: compiled PyQt UI module used by the editor at runtime
- `HTMLeditor.ui`: original Qt Designer source for the editor dialog
- `gui_runtime_env.py`: GUI environment sanitizer used before Qt starts

## Run

From this folder:

```bash
python HTMLeditor.py
```

## Requirements

- Python 3
- `PyQt5`
- Optional but recommended on Linux for richer HTML rendering paths: `PyQtWebEngine`

## Standalone Status

Yes. The editor can run from this folder as a standalone bundle as long as those Python dependencies are available.

The preview harness and portal feed files are not required for the editor itself.

## Notes For Portal Migration

- `HTMLeditor.py` imports sibling files only, so it is portable as a small folder.
- If you edit `HTMLeditor.ui` in Qt Designer, re-run `pyuic5` to regenerate `HTMLeditorUI.py`.
- The JSON export format is intended as a transport/storage format for later portal integration.
