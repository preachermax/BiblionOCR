# BiblionOCR Developer Notebook

## 📌 Project Overview

* **MyServer**: Main runtime UI/controller for OCR workflow and project creation wiring
* **Core Engine**: Intended home for project creation state machine + RIS compliance system
* **EventBus**: In-memory event propagation system
* **SQLiteEventStore**: Persistent event log target, append-only by design
* **MyPixler**: Image processing + preview tools
* **ImagePreviewDialog**: Interactive preview (crop, compare)
* **Session Manager**: Stores and restores persistent session state

---

## 🧠 Architecture Notes

* All image loading is **threaded (QThread)**
* UI updates must occur in **main thread only**
* Pixmap scaling must always use **non-null source**
* Crop operates on **QImage, not QPixmap**
* **Never scale from an already scaled pixmap**
* Project creation is being moved toward an **event-sourced Core Engine model**
* The long-term target is:

  * UI gathers input
  * MyServer wires dependencies and routes signals
  * Core Engine owns project lifecycle logic
  * EventBus dispatches events
  * SQLiteEventStore persists events

---

## ⚠️ Critical UI / Import Correction

### ✅ Actual Current Runtime Model

* `ViewController/0-MainUI/MyServer.py` defines the runtime `MainWindow` class
* `ViewController/0-MainUI/MyServerUI.py` defines the generated `Ui_MainUI` class used by MyServer
* `ViewController/0-MainUI/MainUI.py` is also a generated UI file and does **not** define:

  * `MainWindow`
  * `MainUI`
  * `RISDialogController`

### ❌ Do Not Reintroduce

* Do **not** use:

  * `from MainUI import MainWindow`
  * `from MainUI import MainUI`
  * `from MainUI import RISDialogController`

These imports caused recent startup tracebacks because those names do not exist in `MainUI.py`.

### ✅ Current Fix

* `MyServer.py` no longer imports `MainWindow` from `MainUI.py`
* `MyServer.py` uses its own `MainWindow` class
* `MyServer.py` compiles after this correction

---

## ⚙️ Project Creation / Engine Integration State

### ✅ Current Working State

* The **New Project** action can create a project successfully
* Missing UI helper methods were added to `MainWindow`:

  * `get_project_name()`
  * `get_project_purpose()`
  * `get_intent()`
  * `collect_new_project_payload()`

* `on_new_project_clicked()` now:

  * collects required RIS payload fields from dialogs
  * handles Cancel cleanly
  * reports success/failure with message boxes

### ✅ Project Creation Location

* New projects should be created under the user Projects folder:

  * Windows target: `C:/Users/Max/Projects`
  * Code target: `os.path.join(os.path.expanduser("~"), "Projects")`

* The previously created project was corrected:

  * moved from `Model/Project/Erasmus1516`
  * moved to `C:/Users/Max/Projects/Erasmus1516`

* The project registry was normalized to:

  * `C:/Users/Max/Projects/_registry.json`

### ⚠️ Temporary Architecture Drift

* `MyServer.py` currently still contains local definitions for:

  * `ProjectState`
  * `ProjectCreationEngine`
  * `EventBus`
  * `ProjectReplayEngine`
  * `RISDialogController`

* The intended target is to move these responsibilities into `Core/` and keep `MyServer.py` as wiring only
* Do not remove the local definitions until `Core/` is fully validated and wired

---

## 📡 Event System Notes

### Intended Event Format

* Events should follow this shape:

  * `event`: event name
  * `timestamp`: event time
  * `state`: project engine state
  * `project_name`: active project name, if any
  * `metadata`: event metadata dict

### Current Status

* `EventBus` dispatch works in memory
* `SQLiteEventStore` exists in `Core/event_store.py`
* SQLite append exists
* SQLite event loading/replay is not yet complete

---

## ⚠️ Known Issues

* Zoom slider can desync from pixmap scale (non-compounding rule must be enforced)
* Session manager may return stale paths across environments
* Continue.dev YAML/config sensitive to formatting
* Cross-platform path contamination (Jetson ↔ Windows)
* `MyServer.py` still has too much project-creation business logic
* `Core/engine.py` currently has a debug side effect: `print("ENGINE MODULE LOADING")`
* `Core/__init__.py` / `Core` imports must be validated before switching `MyServer.py` to Core imports
* Event replay from SQLite is not yet implemented

---

## 🔧 Current Stabilization State (CRITICAL)

### ✅ Release Font Workflow

* The cross-platform font refresh task (`release-font-refresh-and-smoke-test`) is part of the release path
* This is the first release step before any final build packaging
* SessionManager resolves the repo-local `ViewController/0-MainUI/fonts` path by default

### ✅ ProjectFolderList Maintenance

* `ProjectFolderList.py` regenerates both:

  * `ProjectFolderList.txt`
  * `ViewController/0-MainUI/ProjectFolderList.txt`

* Deprecated references are excluded or redirected:

  * `Model/Utilities` → `Model/Project/Utilities`
  * `Model/Developer` → `Model/Project/Utilities`

* Explicitly excluded:

  * external/system font paths
  * Tesseract install paths
  * home/user profile paths
  * `Model/Project/Utilities/Reference`

* Required `ViewController/0-MainUI` files and selected module folders are explicitly restored during regeneration

### ✅ MyServer Project Creation

* New project action no longer crashes on missing helper methods
* Project creation target is now `~/Projects`
* `Erasmus1516` has been moved to `C:/Users/Max/Projects/Erasmus1516`
* `_registry.json` now lives under `C:/Users/Max/Projects`

### ✅ MyPixler

* Standalone launch: **WORKING**
* Session image load: **WORKING**
* `start_image_load()` threading: **STABLE**
* `on_image_loaded()` receiving `QImage`: **CONFIRMED**
* RefImg display + `RefImgLE` sync: **WORKING**
* Crop apply from `ImagePreviewDialog` returns a full-resolution QImage in original image coordinates
* Applied crop is displayed directly in the MyPixler right-hand panel without an immediate second scaling pass
* Crop result preserves source image resolution metadata (`dotsPerMeterX`, `dotsPerMeterY`, `devicePixelRatio`, and color space where supported)
* TIFF return/save path derives DPI from QImage dots-per-meter metadata instead of hard-coding 300 DPI
* Subprocess return-path crop handoff back to MyServer: **CONFIRMED**

### ✅ ImagePreviewDialog

* External module is the **canonical implementation**
* Constructor stabilized (no multi-parent / param conflicts)
* Crop coordinates:

  * correctly mapped
  * converted to original image space

* Preview behavior:

  * Left = original
  * Right = processed

* Crop apply:

  * left mouse drag creates a crop rubberBand on the left/original preview
  * rubberBand remains visible after mouse release
  * 8 light-blue grip handles allow crop adjustment before Apply
  * grip-handle release updates the right/processed preview
  * Apply hides the rubberBand/handles and returns the processed crop to MyPixler
  * correctly updates **processed (right) panel**

* Resolution behavior:

  * crop coordinates are mapped from zoomed display space back to original image pixels
  * preview zoom is display-only and does not determine the applied crop's pixel size
  * `get_result()` returns the full-resolution processed crop
  * QImage resolution metadata is copied from the source image through the crop result

---

## 🧱 System Boundaries (LOCKED)

### MyServer

* Responsibilities:

  * UI startup
  * dependency wiring
  * signal routing
  * event subscription
  * image selection
  * TIFF stack loading
  * navigation
  * launching MyPixler

* ❌ MUST NOT contain long-term:

  * crop logic
  * preview logic
  * image processing
  * project lifecycle state-machine logic
  * RIS generation logic
  * persistent event replay logic

---

### Core Engine

* Responsibilities:

  * project lifecycle state machine
  * validation
  * RIS generation
  * project filesystem writing
  * event emission

* ❌ MUST NOT contain:

  * UI imports
  * direct widget manipulation
  * PyQt dependencies

---

### EventBus

* Responsibilities:

  * dispatch events
  * notify subscribers

* ❌ MUST NOT:

  * mutate project state
  * perform business logic

---

### SQLiteEventStore

* Responsibilities:

  * append event records
  * later: load event records for replay

* ❌ MUST NOT:

  * own project state transitions
  * manipulate UI

---

### MyPixler

* Responsibilities:

  * image processing
  * crop logic
  * preview dialog control
  * session integration

---

### ImagePreviewDialog

* Responsibilities:

  * interactive preview UI
  * parameter control via `params` dict
  * rendering original vs processed comparison

* Input:

  * `QImage`
  * processor function

* Output:

  * processed `QImage`

---

## 🎯 Next Safe Development Steps

1. **Core Import Stabilization**

   * Remove debug side effect from `Core/engine.py`
   * Confirm `Core.engine.ProjectCreationEngine` can be imported cleanly
   * Confirm `Core.event_bus.EventBus` can be imported cleanly
   * Confirm `Core.event_store.SQLiteEventStore` can be imported cleanly

2. **Move Project Logic Out of MyServer**

   * Make `Core/engine.py` the single source of truth for `ProjectCreationEngine`
   * Remove duplicate `ProjectCreationEngine` from `MyServer.py` only after Core is fully validated
   * Keep `MyServer.py` as wiring/controller only

3. **SQLite Event Replay**

   * Add event loading to `SQLiteEventStore`
   * Create or stabilize `ProjectReplayEngine` under `Core/`
   * Reconstruct project state from event history

4. **UI Event Subscription Layer**

   * Subscribe UI handlers to EventBus events
   * Replace console-only event feedback with status/output UI updates
   * Keep UI changes reactive and main-thread safe

5. **Regression Test New Project Flow**

   * Create another test project
   * Confirm it appears under `C:/Users/Max/Projects`
   * Confirm registry updates as a JSON array
   * Confirm no project is created under `Model/Project`

---

## 🚫 High-Risk Files (DO NOT ACCIDENTALLY COMMIT)

* `__pycache__/`
* `*.pyc`
* `.continue/` configs unless intentional
* Session files:

  * `Session.json`
  * CSV mirrors that may contain machine-specific paths

* Generated UI/resource files:

  * `UI_Icons.py` only if intentionally regenerated
  * `MyServerUI.py` only if intentionally regenerated from Qt Designer
  * `MyPixlerUI.py` only if intentionally regenerated from Qt Designer

---

## 🧪 Debug Patterns

Always print/check:

* `pixmap.isNull()`
* scale factors
* thread lifecycle:

  * start
  * progress
  * finish

* project creation path:

  * `self.project_engine.base_path`
  * final project path
  * `_registry.json` path

Rules:

* Avoid duplicate UI update paths
* Never scale from scaled pixmap
* Never mix QPixmap/QImage responsibilities
* Never import runtime classes from generated UI files unless the class is verified to exist
* Avoid hardcoded absolute paths; use `os.path.expanduser("~")`, `os.path`, or `pathlib`

---

## 🧩 Tooling Strategy

* ChatGPT → architecture, debugging, root-cause reasoning
* Continue.dev → codebase-aware validation and refactoring
* Copilot → inline coding + commit assistance
* Git → state control and rollback safety
* `dev_notebook.md` → single source of truth

---

## 🖥️ Development Environment Strategy

* Target system: Jetson Nano (Ubuntu 20, Python 3.8, PyQt5)
* Current dev: Windows 10 / Windows path model
* Current Windows user project root: `C:/Users/Max/Projects`

Rules:

* Maintain **Python 3.8 compatibility** where practical
* Maintain **PyQt5 compatibility**
* Avoid hardcoded absolute paths
* Use `os.path` / `pathlib`
* Use `os.path.expanduser("~")` for user-relative project storage

---

## 🔁 AI-Assisted Workflow (LOCKED)

### Development Loop

1. ChatGPT → define change
2. Implement locally
3. Run runtime test
4. Validate with Continue.dev
5. Commit locally
6. Update notebook ONLY if state changed

---

## 🧾 Notebook Update Rule

Update ONLY when:

* behavior changes
* bug fixed
* architecture clarified
* new issue discovered

DO NOT update for:

* formatting only
* debug prints only
* minor edits that do not alter project state

---

## 🧭 Checkpoint Summary — 2026-06-26

* Focus:

  * Project creation path correction
  * MyServer import cleanup
  * ProjectFolderList stabilization
  * Core/EventBus architecture clarification

### Key Stability Wins

* `MyServer.py` no longer imports missing classes from `MainUI.py`
* `MainWindow` helper methods for new project creation now exist
* New projects target `C:/Users/Max/Projects`
* Existing `Erasmus1516` project moved to the correct external project folder
* Project registry moved/normalized under `C:/Users/Max/Projects/_registry.json`
* `ProjectFolderList.py` excludes external/system paths and `Model/Project/Utilities/Reference`
* `ProjectFolderList.py` preserves required ViewController/MainUI references

### Remaining Risk Areas

* `MyServer.py` still contains duplicate Core-style classes
* `Core/engine.py` and `MyServer.py` engine behavior are not yet unified
* SQLite replay support is incomplete
* Generated UI files should not be hand-edited casually
* Cross-system path handling remains important

---

## 🗂️ File Ownership

* MyServer → runtime UI/controller + wiring only
* Core Engine → project creation lifecycle, RIS, filesystem write, event emission
* EventBus → dispatch only
* SQLiteEventStore → append/load persistent events
* MyPixler → processing only
* ImagePreviewDialog → preview/crop dialog only
* ProjectFolderList.py → curated project inventory generator

---

## 💡 Personal Workflow Insight

* Switch from “build mode” → “learning mode” when diminishing returns hit
* Debug by isolating systems first (MyPixler → then integration)
* Avoid multi-variable debugging
* Stabilize imports before changing architecture
* Confirm exact file ownership before moving logic

---

## 🧾 Decision Log

* 2026-06-22: Hybrid AI workflow adopted
* 2026-06-22: External ImagePreviewDialog made canonical
* 2026-06-22: MyServer stripped of crop responsibilities
* 2026-06-22: Threaded image loading stabilized
* 2026-06-22: Developer notebook designated as project memory authority
* 2026-06-22: Commit discipline + checklist introduced
* 2026-06-22: MyPixler standalone crop/apply/zoom milestone validated
* 2026-06-26: Corrected ChatGPT 5.5 notebook drift: `MainUI.py` does not provide `MainWindow`, `MainUI`, or `RISDialogController`
* 2026-06-26: Removed invalid `MainUI`/`Core` imports from `MyServer.py` startup path
* 2026-06-26: Added missing New Project input helper methods to `MainWindow`
* 2026-06-26: Corrected new project destination to `C:/Users/Max/Projects`
* 2026-06-26: Moved `Erasmus1516` from `Model/Project` to `C:/Users/Max/Projects`
* 2026-06-26: ProjectFolderList generator updated to include required ViewController references while excluding external/system paths and `Model/Project/Utilities/Reference`

---

## 📚 Documentation Classification

### Release-Facing

* update_fonts.py
* update_fonts.txt
* `.vscode/tasks.json`

### Compilation Docs

* dev_notebook.md
* commit_checklist.md
* AIcommitWorkflow.md
* PROJECT_ARCHITECTURE.md
* DEPENDENCIES_AND_RELATIONSHIPS.md

### HelpSystem-Facing

* README_HELP_SYSTEM.md
* HELP_INTEGRATION_GUIDE.md
* QUICK_REFERENCE.md
* PROJECT_ARCHITECTURE.md
* DEPENDENCIES_AND_RELATIONSHIPS.md

### Development-Facing

* dev_notebook.md
* commit_checklist.md
* AIcommitWorkflow.md

### Reference-Only / Supporting

* PROJECT_CREATION_ARCHITECTURE.md
* PROJECT_SPEC.md

---

## 📅 Last Updated

2026-06-26

---