# Print And Exit Menu Support

## Purpose

The 0-MainUI module family now has a shared pattern for wiring print-related menu actions and module exit actions without duplicating the full MyServer implementation in every controller.

## Shared Runtime Helper

The shared controller-side helper lives at:

`ViewController/0-MainUI/helpers/print_menu_support.py`

It provides a small adapter layer around `print_handlerUI.ProjectPrintHandler` and handles:

- binding module-specific `actionPrint_*` actions to the correct live image or text surface
- routing `actionPrint_Preview` to the most recently used or currently available print target
- binding `actionExit` to `close()` when the UI exposes that action
- showing consistent empty-state messages when nothing is loaded

## Current Module Coverage

Modules using shared print menu support:

- `ViewController/0-MainUI/MyScanner.py`
- `ViewController/2-TrainTesseract/MyReader.py`
- `ViewController/1-PreProcess/MyGlypher.py`
- `ViewController/3-Process/MyVersifier.py`
- `ViewController/4-PostProcess/MyWriter.py`
- `ViewController/1-PreProcess/MyPixler.py`
- `ViewController/1-PreProcess/MyBoxer.py`

Modules with controller-side `actionExit` support added separately:

- `ViewController/0-MainUI/MyServer.py`
- `ViewController/2-TrainTesseract/MyGrounder.py`
- `ViewController/0-MainUI/MyLauncher.py`
- `ViewController/3-Process/MyLexer.py`
- `ViewController/2-TrainTesseract/MyTrainer.py`

Modules intentionally excluded from `actionExit` rollout in this pass:

- `ViewController/0-MainUI/MyExplorer.py`
- `ViewController/3-Process/MyResolver.py`

## MyServer Exception

`ViewController/0-MainUI/MyServer.py` remains the source implementation for the full print flow.

It still owns its native print logic directly instead of delegating that flow to `helpers/print_menu_support.py`, because it already had a concrete print implementation with active-target tracking and preview behavior.

Only `actionExit` was added there.

## UI Contract

Controller wiring is only half of the feature.

For a module to expose the behavior in the running UI, its generated UI file must define the matching action names, for example:

- `actionPrint_Ref_Image`
- `actionPrint_Image`
- `actionPrint_Ref_Text`
- `actionPrint_Text`
- `actionPrint_Preview`
- `actionExit`

When a controller uses a guarded `hasattr(...)` check for `actionExit`, the Python side can be shipped before the corresponding `.ui` menu item is added.

## Validation

Targeted compile validation for the rollout used:

```bash
python -m py_compile \
  ViewController/0-MainUI/helpers/print_menu_support.py \
  ViewController/0-MainUI/MyServer.py \
  ViewController/0-MainUI/MyScanner.py \
  ViewController/2-TrainTesseract/MyReader.py \
  ViewController/1-PreProcess/MyGlypher.py \
  ViewController/3-Process/MyVersifier.py \
  ViewController/4-PostProcess/MyWriter.py \
  ViewController/1-PreProcess/MyPixler.py \
  ViewController/1-PreProcess/MyBoxer.py \
  ViewController/2-TrainTesseract/MyGrounder.py \
  ViewController/0-MainUI/MyLauncher.py \
  ViewController/3-Process/MyLexer.py \
  ViewController/2-TrainTesseract/MyTrainer.py
```
