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


## 📠 Scanner Acquisition Architecture

### Design Philosophy

BiblionOCR separates scanner discovery from image acquisition.

Architecture:

    Discovery
        ↓
    Capability Detection
        ↓
    Image Acquisition

Discovery identifies devices. Acquisition retrieves images.

### Discovery Layer

* Scapy (ARP discovery)
* ICMP reachability
* TCP probing
* mDNS / Bonjour (planned)
* SNMP capability detection (planned)
* Existing `NetworkScanner` in `MyServer.py` belongs in this layer, but today it only emits IP/MAC discovery results and does not yet identify scanner protocol capabilities

### Capability Detection Layer

* Capability detection should remain distinct from raw network discovery
* For network scanners, this layer should probe for eSCL/AirScan first, then other advertised protocols
* For local Windows devices, capability selection may depend on OS-accessible backends such as TWAIN or WIA rather than network advertisement alone
* `ScannerManager` should eventually choose a backend from normalized capability data instead of calling WIA directly

### Acquisition Backends

Preferred order:

1. eSCL / AirScan
2. SANE (Linux)
3. TWAIN (Windows)
4. WIA (Windows)
5. Mock backend for tests and UI validation when no hardware is attached

Future implementations should derive from a common `ScannerBackend` interface so MyServer receives a stable scan result contract that preserves the persisted TIFF path used by the existing workflow, with optional in-memory image/metadata when helpful.

### Current Windows Runtime Path

* The active scan entrypoint in `MyServer.py` is `actionScanNetwork()` even though the current behavior is local hardware acquisition, not network image retrieval
* `MyServer.__init__()` instantiates `Core.Scanner.manager.ScannerManager` directly and wires the UI scanner action/button to that path
* `ScannerManager` is currently a thin wrapper around `WIAScanner`; it does not yet select among multiple backends at runtime
* `WIAScanner.acquire(destination_folder)` uses `win32com.client.Dispatch("WIA.CommonDialog")` and `WIA.DeviceManager`, saves a temporary PNG, converts it to grayscale `QImage`, then writes the final numbered TIFF into the scanned folder
* `MyServer` currently displays the saved TIFF by passing `result["path"]` into `showImage()`; this disk-backed TIFF handoff is deliberate design because it fits the existing MyServer workflow
* Because of that current contract, the layered scanner plan should normalize result shape around a persisted TIFF output before broad backend rollout rather than treating file output as legacy behavior

### Helper Formatting Pattern

* The current scanner helpers follow the same pragmatic formatting style used elsewhere: short section-divider comments, thin wrapper classes, and simple return dictionaries like `{ "path": ..., "dir": ... }`
* Discovery and acquisition helpers are present but not yet unified behind a stable backend-selection contract


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
* `collect_new_project_payload()` now opens a guided two-step modal dialog instead of chained text prompts
* The wizard currently supports:

  * step 1: optional provenance import
  * step 2: project details + review summary
  * required-field validation before final submission
  * visible project-name normalization before creation

* `on_new_project_clicked()` now:

  * collects required project/RIS payload fields from the wizard
  * handles Cancel cleanly
  * prompts before replacing an existing project
  * reports success/failure with message boxes

* Supported provenance import formats in the wizard:

  * `project.ris.json`
  * standard RIS text exports such as Primo `.ris`
  * `.txt` provenance files containing RIS, JSON text, or simple key/value pairs
  * `.csv` provenance files with either key/value rows or a header row plus one data row

* Imported provenance metadata is preserved into the final project RIS payload under source-provenance fields when available

### ✅ Project Creation Location

* New projects should be created under the user Projects folder:

  * Windows target: `C:/Users/Max/Projects`
  * Code target: `os.path.join(os.path.expanduser("~"), "Projects")`

* The previously created project was corrected:

  * moved from `Model/Project/Erasmus1516`
  * moved to `C:/Users/Max/Projects/Erasmus1516`

* The project registry was normalized to:

  * `C:/Users/Max/Projects/_registry.json`

* Current manual test staging state:

  * `Erasmus1519` content has replaced `Erasmus1516`
  * `Erasmus1519` has been removed
  * `Erasmus1522` has been removed so it can be recreated through the wizard
  * Windows held an open handle on the `Erasmus1516` root directory, so the successful reset path was: clear `Erasmus1516` contents, then move `Erasmus1519` contents into that existing folder

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
* `Core/engine.py` now compiles without the prior debug side effect `print("ENGINE MODULE LOADING")`
* `Core/__init__.py` / `Core` imports must be validated before switching `MyServer.py` to Core imports
* Event replay from SQLite is not yet implemented
* Scanner backend abstraction layer not yet implemented
* Discovery and acquisition remain separate responsibilities
* eSCL backend pending implementation
* `ScannerManager.acquire_qimage()` is stale relative to `WIAScanner`: it calls `self.wia.acquire_qimage()` without a destination folder, while `WIAScanner.acquire_qimage(destination_folder)` expects one and tries to return `result["image"]` even though `acquire()` currently returns only `path` and `dir`

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

* `Core/engine.py` can now generate new project folder structures from `ProjectFolderList.txt`
* Core treats file entries in `ProjectFolderList.txt` as parent-directory requirements
* Core adds `.gitkeep` placeholders to empty directories so local project Git repos can track the structure
* Core copies the folder list into `src/manifests/ProjectFolderList.txt`
* Core writes a structure rebuild log to `logs/processing/project_folder_list_structure_rebuild.md`
* Core emits `project_structure_created` after folder generation

* Current future-project manifest baseline:

  * include current ViewController runtime files
  * include `Model/Project/Data` csv/json/SQLite folders and file contents
  * include minimal `Model/Project/Images` folder skeleton only
  * exclude deep image trees and image files themselves

* Deprecated references are excluded or redirected:

  * `Model/Utilities` → `Model/Project/Utilities`
  * `Model/Developer` → `Model/Project/Utilities`

* Explicitly excluded:

  * external/system font paths
  * Tesseract install paths
  * home/user profile paths
  * `Model/Project/Utilities/Reference`

* Required `ViewController/0-MainUI` files and selected module folders are explicitly restored during regeneration

### ✅ MyServer / Core Project Creation

* New project action no longer crashes on missing helper methods
* Project creation target is now `~/Projects`
* New projects are required to initialize as local Git repositories
* `Core/engine.py` now supports ProjectFolderList-driven structure generation
* Event-store SQLite lock failures are now treated as non-fatal for project creation
* Project creation temp directories are now unique per run to avoid stale temp-dir collisions
* `Core/engine.py` smoke test confirmed:

  * `.git/` initialization
  * `Model/Project/Data/json`
  * `Model/Project/Images/Workflow/pixler/pixler_pages_cropped`
  * `ViewController/0-MainUI`
  * `src/manifests/ProjectFolderList.txt`
  * `logs/processing/project_folder_list_structure_rebuild.md`

* `Erasmus1516` has been moved to `C:/Users/Max/Projects/Erasmus1516`
* `_registry.json` now lives under `C:/Users/Max/Projects`
* `Erasmus1522` creation was validated successfully with the trimmed manifest through the storeless path

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

1. **Scanner Framework**

   * Create `Core/scanner_manager.py`
   * Create backend modules (`escl_backend.py`, `sane_backend.py`, `twain_backend.py`, `wia_backend.py`)
  * Add a `mock_backend.py` for no-hardware tests and UI validation
   * Separate discovery from acquisition
  * Add an explicit capability-detection step between discovery and backend selection
   * Keep MyServer backend-agnostic

2. **Core / MyServer Unification**

   * Wire `MyServer.py` to use `Core.engine.ProjectCreationEngine`
   * Confirm `Core.event_bus.EventBus` can be imported cleanly
   * Confirm `Core.event_store.SQLiteEventStore` can be imported cleanly
   * Keep local `MyServer.py` engine classes until Core-driven UI project creation is runtime-tested

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
* `Core/engine.py` now supports ProjectFolderList-driven folder generation, but `MyServer.py` and Core engine behavior are not yet fully unified
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
* 2026-06-26: `Core/engine.py` updated to generate project folder structures from `ProjectFolderList.txt`, add `.gitkeep` placeholders, copy the folder list into `src/manifests`, write a structure rebuild log, and emit `project_structure_created`

---

* 2026-06-30: Adopted layered scanner architecture
* 2026-06-30: Scapy designated for discovery only
* 2026-06-30: eSCL/AirScan designated preferred cross-platform acquisition protocol
* 2026-06-30: SANE selected for Linux backend; TWAIN/WIA for Windows
* 2026-06-30: Confirmed current Windows runtime scan path is `MyServer.actionScanNetwork()` → `Core.Scanner.manager.ScannerManager` → `Core.Scanner.wia_scanner.WIAScanner.acquire()` → saved grayscale TIFF
* 2026-06-30: Identified stale `acquire_qimage` helper contract mismatch in the current WIA path
* 2026-06-30: Confirmed existing `NetworkScanner` belongs to discovery only; capability detection must remain a separate layer before backend selection

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

## 🤖 Copilot Familiarization Notes — 2026-06-30

* Current runtime center of gravity is still `ViewController/0-MainUI/MyServer.py`, but project-creation ownership is intended to converge into `Core/engine.py`
* The safest boundary for future edits is: `MyServer.py` wires UI/runtime behavior, `Core/` owns lifecycle logic, and `MyPixler`/`ImagePreviewDialog` own image processing and preview state
* After any project-creation change, the first validation target should be the external project root at `C:/Users/Max/Projects`, the `_registry.json` update path, and ProjectFolderList-driven structure generation
* The highest-risk refactor remains removing duplicate engine/event classes from `MyServer.py` before Core imports, runtime wiring, and replay behavior are fully validated
* There are currently multiple notebook copies in circulation; the repo-tracked notebook should stay intentionally synchronized with the working copy when architecture notes are updated

---

## 📅 Last Updated

2026-06-30

---