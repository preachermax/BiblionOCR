# Print And Exit Menu Support

## Purpose

The 0-MainUI module family now has a shared pattern for wiring print-related menu actions and module exit actions without duplicating the full MyServer implementation in every controller.

## Shared Runtime Helper

The shared controller-side helper lives at:

`ViewController/0-MainUI/print_menu_support.py`

It provides a small adapter layer around `print_handlerUI.ProjectPrintHandler` and handles:

- binding module-specific `actionPrint_*` actions to the correct live image or text surface
- routing `actionPrint_Preview` to the most recently used or currently available print target
- binding `actionExit` to `close()` when the UI exposes that action
- showing consistent empty-state messages when nothing is loaded

## Current Module Coverage

Modules using shared print menu support:

- `MyScanner.py`
- `MyReader.py`
- `MyGlypher.py`
- `MyVersifier.py`
- `MyWriter.py`
- `MyPixler.py`
- `MyBoxer.py`

Modules with controller-side `actionExit` support added separately:

- `MyServer.py`
- `MyGrounder.py`
- `MyLauncher.py`
- `MyLexer.py`
- `MyTrainer.py`

Modules intentionally excluded from `actionExit` rollout in this pass:

- `MyExplorer.py`
- `MyResolver.py`

## MyServer Exception

`MyServer.py` remains the source implementation for the full print flow.

It still owns its native print logic directly instead of delegating that flow to `print_menu_support.py`, because it already had a concrete print implementation with active-target tracking and preview behavior.

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
  ViewController/0-MainUI/print_menu_support.py \
  ViewController/0-MainUI/MyServer.py \
  ViewController/0-MainUI/MyScanner.py \
  ViewController/0-MainUI/MyReader.py \
  ViewController/0-MainUI/MyGlypher.py \
  ViewController/0-MainUI/MyVersifier.py \
  ViewController/0-MainUI/MyWriter.py \
  ViewController/0-MainUI/MyPixler.py \
  ViewController/0-MainUI/MyBoxer.py \
  ViewController/0-MainUI/MyGrounder.py \
  ViewController/0-MainUI/MyLauncher.py \
  ViewController/0-MainUI/MyLexer.py \
  ViewController/0-MainUI/MyTrainer.py
```
