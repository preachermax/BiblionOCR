# BiblionOCR Developer Notebook

## Session Handoff Template (Required For Pause/Exit)

Use this template for every pause, stop, or VS Code close event.

### Session Handoff - YYYY-MM-DD HH:MM

* Scope summary: one sentence describing current task focus.
* Touched files (`git status --short`):
  * file path 1
  * file path 2
* Validation gates:
  * problems/lint: pass or fail with brief note
  * compile: pass or fail with command used
  * smoke: pass or fail with command used
  * manual UI checks: pass or pending with note
* Unresolved blockers/risks:
  * item
* Next immediate action:
  * single next step

## Collaboration Protocol Snapshot (2026-08-07)

1. User will run an extensive manual audit in module order.
2. Default execution mode is one module per change set.
3. Global rollout is opt-in and only done when explicitly requested.
4. MyLexer is a required placeholder and remains intentionally out of scope until the user audit explicitly reaches it.
5. For every cycle, report full-workspace Problems totals and in-scope totals separately before clean claims.

## Reusable Prompt Workflow (Developer Use)

Use the module-scoped prompt workflow to reduce prompt-writing overhead while preserving validation discipline:

* [docs/development/CHANGESET_PROMPT_PACK_2026-08-07.md](docs/development/CHANGESET_PROMPT_PACK_2026-08-07.md)

Quick use pattern:

1. Choose one module from the prompt queue.
2. Apply strict header plus module task plus lean footer.
3. Keep deferred modules out of scope until explicitly re-opened.
4. Report full-workspace Problems count and in-scope Problems count before completion claims.

### Session Handoff - 2026-08-14 13:54

* Scope summary: reviewed and reconciled the origin/master Windows-development change set by removing `MySliders` from the runnable launcher surface, correcting new architecture-doc contradictions, and validating launcher startup paths.
* Touched files (`git status --short`):
  * `D Developer/ViewController/SeparatedDevFiles/0-MainUI/update_UI_Resources.sh`
  * `D Developer/ViewController/SeparatedDevFiles/0-MainUI/update_UI_Resources.txt`
  * `M Developer/ViewController/SeparatedDevFiles/MOVED_FILE_MANIFEST.md`
  * `D Developer/update_UI_Resources.sh`
  * `D Developer/update_UI_Resources.txt`
  * `M ProjectFolderList.txt`
  * `M ViewController/0-MainUI/ProjectFolderList.txt`
  * `M ViewController/0-MainUI/helpers/ProjectFolderList.txt`
  * `M ViewController/0-MainUI/helpers/ScriptureProjectFolderList.txt`
  * `M ViewController/GeneralProjectFolderList.txt`
  * `M ViewController/Model/Project/Data/json/Session.json`
  * `M ViewController/ScriptureProjectFolderList.txt`
  * `M ViewController/utilities/0-MainUI/helpers/ProjectFolderList.py`
  * `M docs/architecture/BIBLION ECOSYSTEM ARCHITECTURE.md`
  * `M docs/architecture/nano/BiblionOCR_Jetson_Nano_Journey_and_Compute_Baseline.md`
  * `M docs/development/DEV_NOTEBOOK.md`
  * `M docs/development/WINDOWS_PERSISTENT_LAUNCHERS.md`
  * `M launchers/restore_desktop_launchers.py`
  * `D launchers/run-mysliders.cmd`
  * `D launchers/run-mysliders.sh`
  * `M tests/test_launcher_entrypoint_compatibility.py`
  * `?? Developer/QtDesignerUI/update_UI_Resources.sh`
  * `?? Developer/QtDesignerUI/update_UI_Resources.txt`
  * `?? docs/development/WINDOWS10_REPO_BACKUP_AND_RECLEAN.md`
  * `?? docs/development/WINDOWS10_WINDOWS_DEVELOPMENT_BRANCH_SETUP.md`
* Validation gates:
  * problems/lint: pass; full-workspace Problems total `0`, in-scope Problems total `0` via `get_errors`.
  * compile: pass via `python3 -m py_compile launchers/restore_desktop_launchers.py tests/test_launcher_entrypoint_compatibility.py`.
  * smoke: pass via `QT_QPA_PLATFORM=offscreen timeout 30s pytest tests/test_launcher_entrypoint_compatibility.py -q` and full `launchers/run-my*.sh` timeout-based startup smoke (`14/14` passing after removal of `run-mysliders.sh`).
  * manual UI checks: not required for this cycle; no `.ui` source, generated `UI.py`, menus, buttons, or wizard interactions changed.
* Unresolved blockers/risks:
  * the worktree still contains unrelated local changes outside this cycle and they should remain out of commit scope unless explicitly requested.
  * `ViewController/Model/Project/Data/json/Session.json` remains runtime-local drift and should stay uncommitted by default.
  * architecture-normalization tracker files were not updated in this cycle because no architecture status/task state changed; this pass corrected internal doc consistency and launcher inventory only.
* Next immediate action:
  * stage only the intended launcher/doc/test files if you want this cycle committed, leaving unrelated local artifacts out of scope.

### Session Handoff - 2026-08-06 23:59

* Scope summary: finalized workflow wizard policy/runtime updates plus agent-owned checklist, PR governance, and cross-repo naming/policy documentation.
* Touched files (`git status --short`):
  * committed scope in commit `2d424eb` (33 files)
  * remaining local runtime artifact: `ViewController/Model/Project/Data/json/Session.json`
* Validation gates:
  * problems/lint: pass on touched docs/templates/workflows
  * compile: pass on touched Python runtime files via `python3 -m py_compile ...`
  * smoke: pass (14/14) with `.venv/bin/python` and `QT_QPA_PLATFORM=offscreen`
  * manual UI checks: pending explicit visual reconfirmation after reopen if runtime/UI edits continue
* Unresolved blockers/risks:
  * local `Session.json` remains intentionally uncommitted runtime noise
* Next immediate action:
  * on reopen, run recovery sequence from checklist section `K` before any new edits

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

## Workflow Wizard Foundation (2026-08-05)

### Phase 1 Scope

* MyLauncher-first wizard-style workflow layer is now in place
* stage order is now derived from numbered `ViewController` folders
* workflow guidance is additive, not destructive: manual launch paths remain intact
* `NumberColumns` update path is now exposed in MyServer and MyScanner and persisted to project metadata

### New Runtime Components

* `ViewController/0-MainUI/helpers/workflow_stack_wizard_dialog.py`
* `ViewController/0-MainUI/helpers/project_column_settings.py`

### Procedural Contract

* this work is treated as a dedicated architecture milestone commit before broader module propagation
* follow-up rollout to remaining modules should happen in separate commits to preserve testability and rollback clarity

### Follow-Up Rollout Completion

* follow-up module rollout is now complete in separate commit `4969da6`
* `Core/workflow_wizard_actions.py` now provides shared runtime action injection for workflow wizard entry points
* the remaining main runtime modules now expose page-workflow entry actions without replacing their existing manual workflows
* project workflow wizard is now scoped to MyServer menu surfaces
* MyLauncher now supports direct CLI wizard startup for project and page modes, including module-scoped page wizard launch routing
* page workflow handlers are now bound explicitly on module windows as module-owned wizard actions

### Test-First Commit Standard

* commits are now gated by automated checks first (`py_compile`, diagnostics, smoke tests)
* manual UI verification is required before commit on changed interaction surfaces
* commit operations are treated as post-test milestones, not test breakpoints

### MyLauncher Interaction Model (Current)

* single left-click on a module button now shows module About/help text in the right panel
* double left-click on a module button launches the selected module
* right-click on module buttons and the left panel opens module-aware context actions (About and Launch)
* right panel is read-only and exposes default text actions plus selected-module About/Launch actions

---

## Launcher Restore and Wrapper Notes (2026-08-02)

* Linux launcher restore now targets icons under `ViewController/0-MainUI/helpers/Icons`
* canonical launcher icon mapping now includes `MyLauncher -> BiblionLauncher.png`
* canonical launcher icon mapping now includes `MyLexer -> BiblionLexer2.png`

* desktop aliases in Greek are required and preserved (for example `βιϐλιον Glypher.desktop`)
* launcher wrappers were repointed: `MyBoxer`, `MyGlypher`, `MyPixler` -> `ViewController/1-PreProcess`
* launcher wrappers were repointed: `MyGrounder`, `MyReader`, `MyTrainer` -> `ViewController/2-TrainTesseract`
* launcher wrappers were repointed: `MyLexer`, `MyResolver`, `MyVersifier` -> `ViewController/3-Process`
* launcher wrappers were repointed: `MyWriter` -> `ViewController/4-PostProcess`

* launcher smoke checks (timeout-based startup probes) were run across canonical `My*` modules to verify non-crashing startup behavior after path and restore fixes

---

## Pre-Structural Modification Checkpoint (Page Workflow Lifecycle)

Before Phase 1 implementation, the architecture plan for page-centric project workflow tracking is captured in:

* `docs/development/PROJECT_PAGE_WORKFLOW_TODO.md`

This checkpoint defines:

* new project database fields for page lifecycle context
* scripture-only project structure strategy
* per-column source page folder model
* status-bar propagation requirements across modules
* SessionManager tracked-field integration scope
* tabbed `ProjectSettingsDialog` redesign with Qt Designer-editable `.ui`

  ---

  ## Project Status and Milestones

* `MyServer` is now the authoritative selector for the active project across the runtime toolchain
* the selected project is persisted through shared session state in `Model/Project/Data/json/Session.json`
* `SessionManager` now exposes active-project helpers so modules can read and publish the same project identity consistently
* `Core/project_tracking.py` now owns the shared workflow milestone model, project-root resolution, persisted tracking state, and weighted progress calculation
* milestone state is persisted per project in `Model/Project/Data/json/ProjectTracking.json`
* `ViewController/0-MainUI/ProjectTrackingDialog.py` is now the common user-facing milestone editor
* the `Milestones` dialog is no longer `MyServer`/`MyPixler` only; the shared controller in `ViewController/0-MainUI/project_status_controller.py` mounts the same project-status surface across the main runtime modules
* the common status surface now includes:

  * current project name
  * module workflow summary
  * weighted overall project progress bar
  * `Milestones` button opening the shared editor dialog

* `MyPixler` follows `MyServer` project selection live while open
* the remaining main windows now read the same active project and expose the same milestone dialog / status-bar workflow surface
* this work turns project progress from inferred, local, and mostly invisible state into a shared, user-visible, and manually editable development contract

  ---

  ## Repository Policy Surface

* public contribution policy is now defined in the repository root through `CONTRIBUTING.md`
* non-code submission and rights screening policy is now defined through `CONTENT_POLICY.md`
* repository review ownership for sensitive paths is now expressed through `.github/CODEOWNERS`
* developer and content-creator intake are intentionally treated as different workflows because software licensing and content redistribution rights are not the same problem

---

## 🌐 Website Prototype Notes

### Current Website Demo State

* `docs/website/` now contains a minimal React + Cytoscape website prototype
* `docs/website/src/App.jsx` is the maintained source version of the demo
* `docs/website/preview.html` is the no-build browser preview for environments without local Node.js
* the public website milestone is now live at `https://biblionocr.onrender.com/`
* the current demo includes:

* static overview graph
* static guiding-principles graph derived from `docs/vision/THE_BIBLION_PROJECT.md`
* node-click selection routed into parent state
* advance, reset, and autoplay sequence controls for the overview graph
* EventBus + EventRunner + EventGraphExecutor wiring for recursive event-graph traversal
* in-memory event logger with per-run `traceId` grouping
* live event log panel and system-state panel
* graph highlighting for both the current active node and previously visited nodes

### Current Layout / Readability Contract

* graph cards now use a single-column layout so the canvas can consume the full card width
* graph nodes use wrapped text inside rounded rectangle geometry rather than circular targets
* the overview graph now uses explicit preset positions across the horizontal axis to avoid vertical scrolling
* the guiding-principles graph also uses preset positions so larger readable targets can fit the available canvas
* GraphView now persists visual visited-node highlighting across an execution run while still emphasizing the current active node
* label readability was validated through the local browser preview before the final website commits were published

### Current Runtime / Instrumentation Contract

* `eventBus.js` is the local publish/subscribe channel for website demo events
* `eventGraph.js` defines the next-event adjacency map used by the runtime traversal layer
* `EventRunner.js` now delegates execution to an injected executor instead of iterating a sequence directly
* `EventGraphExecutor.js` recursively traverses the event graph, emits through the EventBus, and guards against cycles / runaway depth
* `eventLogger.js` records each runtime event with timestamp plus `traceId` so one execution run can be grouped end-to-end
* `stateManager.js` exposes subscribable `activeNode`, `lastEvent`, and `isRunning` state for the React side panels

### Commit / Branch State

* the website prototype landed first on `development` as:

* `e27f513` Add website Cytoscape graph demo
* `c99d010` Refine website graph readability

* the same work was promoted onto `master`, and both branches now reconcile at merge commit `d48a643`

* the event-graph runtime milestone then landed on `development` as:

* `cf5f483` v1.6 complete: event graph execution engine with traceable runtime traversal

  ---

## 🧪 Developer Mode Milestones

### v1.7 Foundation

* `Developer/` now exists as the initial Developer Mode package
* `DeveloperServices` is the sole runtime instrumentation boundary for Developer Mode
* the initial runtime model now tracks observed modules with:

* module name
* current state
* last observed event
* last update timestamp
* status

* lightweight metrics currently include:

* total observed event count
* event count per module

* trace recording currently stores:

* trace identifier
* event name
* source module
* destination module
* timestamp

* the public read-only `DeveloperServices` API now exposes runtime model, modules, individual module state, metrics, traces, and recent events through defensive-copy accessors suitable for future Developer Mode panels
* milestone commit published on `development`:

* `7ca2bfd` v1.7 milestone 7.6: add DeveloperServices instrumentation API

### v1.8 First Visible Developer Panel

* the first visible Developer Mode milestone is intentionally narrow: a Runtime Inspector that proves the architecture boundary instead of expanding feature scope
* `ViewController/Developer/RuntimeInspectorPanel.py` renders module state using only the public `DeveloperServices` API
* the Runtime Inspector now displays:

* registered modules
* standardized runtime status
* last observed event
* last update timestamp
* selected-module detail view

* runtime status is currently normalized to the canonical set:

* `OPEN`
* `CLOSED`
* `OBSERVED`
* `UNKNOWN`

* `DeveloperServices` now publishes runtime updates through an event-driven subscriber model so the Runtime Inspector refreshes without polling
* `MyServer.py` now hosts the first Developer Mode panel through a hidden-by-default `Developer` menu entry
* Runtime Inspector activation is lazy:

* the panel dock is created only when opened
* `DeveloperServices` observation is attached only while the panel is visible
* normal application behavior remains unaffected when Developer Mode is unused

* milestone commit published on `development`:

* `ac2a93c` v1.8: integrate visible Runtime Inspector milestone

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
* `ScanManager` now owns backend selection, but capability normalization is still incomplete and should continue moving away from backend-specific assumptions

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
* `MyServer.__init__()` now uses `Core.Scanner.ScanManager` and the scan wizard path
* Scan wizard values are persisted and restored through `SessionManager`, including backend, device, DPI, mode, source type, duplex, destination folder, and persist format
* `ScanManager` now selects among platform-supported backends in priority order: eSCL / AirScan, SANE, TWAIN, WIA
* All active backends now follow the same persisted-result contract and return numbered TIFF output under the destination folder
* `MyServer.showImage()` displays the saved TIFF, updates the image line edit with the scanned filename, and persists image path/dir through `SessionManager.update()` instead of rewriting `Session.json` directly

### Current Backend State

* **AirScan / eSCL**

* real backend implemented in `Core/Scanner/escl_scanner.py`
* supports mDNS `_uscan` / `_uscans` discovery
* supports direct IP / URL entry in the wizard device field
* falls back to Scapy ARP sweep plus `/eSCL/ScannerCapabilities` probing when mDNS advertisements are missing
* validated against Canon device at `192.168.2.21`

* **WIA**

* working on Windows
* COM initialization moved into thread-local backend calls to fix `CoInitialize has not been called`
* saves TIFF output reliably through the shared scan-result contract

* **TWAIN**

* backend code now exists in `Core/Scanner/twain_scanner.py`
* project-local `twaindsm.dll` loading is supported
* current Canon TS3700 state: 64-bit DSM loads, but no 64-bit TWAIN sources are registered; Canon source artifacts present on this machine remain under the 32-bit `C:\Windows\twain_32` tree
* treat TWAIN as unavailable for the current Canon path until a real 64-bit source or a 32-bit helper runtime is introduced

* **SANE**

* Linux/macOS backend extracted from old `MyServer` commented prototype and moved into `Core/Scanner/sane_scanner.py`
* now uses a defensive split strategy on Linux: safe availability probing, `scanimage`-based enumeration, selective option probing, retry/caching for slow discovery, and AirScan-assisted fallback when `sane-airscan` discovery/acquisition is not self-sufficient
* Jetson Canon TS3700 result: SANE can be presented as a Linux-facing compatibility surface, but the reliable scan transport is still network AirScan/eSCL rather than a stable native SANE acquisition path
* strict USB-only Jetson validation result: with `airscan` removed from both `dll.conf` and `dll.d`, `scanimage -L` returned no devices and `SANE_DEBUG_PIXMA=4` reported `pixma_find_scanners() found 0 devices`, so native USB SANE should be treated as unavailable for the current TS3700 path
* not fully testable on this Windows machine because `python-sane` is not installed here

### Recent Scanner Stabilization

* Scan wizard settings are now persisted through `SessionManager` and restored on reopen
* AirScan is the default backend selection, and backend options are filtered by platform support
* Scan button/menu icon visibility was restored by regenerating the Qt resource module rather than changing the UI asset path
* `actionImageScanner_tb` is now wired to the scan workflow
* `Session.json` normalization was added so legacy dict-shaped files no longer crash startup
* `showImage()` now updates the image filename line edit and persists image path/dir through `SessionManager.update()`
* The scan wizard now blocks unavailable backends and provides a direct IP/URL path for AirScan when automatic discovery fails
* The scan wizard now opens immediately and performs backend/device discovery asynchronously with a visible loading indicator, primarily to avoid long Jetson UI stalls
* `MyScanner.py` now uses the same Core scanner workflow as `MyServer.py`, including backend selection, persisted scan request settings, and threaded scan execution through `ScanManager` + `ScanWorker`
* `MyServer.py` now treats flatbed scanning as its local path and redirects ADF requests into `MyScanner.py`, passing the normalized scan request through `ScannerSession.json` so the user can continue there without re-entering settings
* `QtDesignerUI/MyScannerUI.ui` now owns the visible MyScanner scan entry points again, with MyServer-style `imageScannerbutton`, `actionImageScanner`, and `actionImageScanner_tb` regenerated into `MyScannerUI.py` while `actionScanImage` remains the canonical runtime slot target
* On the Jetson Canon path, SANE-first discovery now retries briefly and can synthesize AirScan-backed fallback entries when `scanimage -L` stays empty
* Selecting one of those SANE fallback entries results in AirScan/eSCL acquisition by IP, which is currently the standardized cross-platform path for this Canon class
* The scan wizard now supports a persisted strict-SANE test mode that disables the app-level AirScan fallback path, and SANE discovery labels now distinguish `[native SANE]` devices from `[AirScan fallback]` entries
* Jetson Ubuntu SANE note: files left inside `/etc/sane.d/dll.d/` still load regardless of extension, so strict USB-only validation must move `airscan` loader files out of `dll.d`, not just rename them in place

### Helper Formatting Pattern

* The current scanner helpers follow the same pragmatic formatting style used elsewhere: short section-divider comments, thin wrapper classes, and simple return dictionaries like `{ "path": ..., "dir": ... }`
* Discovery and acquisition helpers are now routed through `ScanManager`, but capability modeling and backend-specific diagnostics still need cleanup

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

## 🐧 Jetson / Git Operational Notes

### Current Repository Cleanup State

* Local `master` was fast-forwarded to the merged remote `master` after the Branch5 / Branch6 integration work
* Branches `Biblion-Branch1` through `Biblion-Branch6` were deleted from both local and remote
* Duplicate remote names were removed; the repo now standardizes on a single remote: `origin`
* Jetson-facing Git instructions are captured in `docs/development/LOCAL_MASTER_SYNC_AFTER_PR.md`

### Jetson Runtime Constraint

* VS Code on the Jetson is currently too memory-heavy for the user's normal recovery/debug workflow
* The practical support path for Jetson work should assume terminal-first operation rather than editor-first operation
* Git sync and crash diagnosis notes should therefore remain usable from a plain Linux shell

### Desktop Launcher Standardization

* Desktop launchers that call Python directly are not sufficient for crash diagnosis because the terminal can disappear with the process
* The current standard is to launch a small shell wrapper from the `.desktop` entry, run the module from that wrapper, print the exit status, and wait for Enter before closing
* Canonical repo examples now exist for this pattern:

* `JETSON_PERSISTENT_LAUNCHERS.md`
* `launchers/run-myserver.sh`
* `My Server.desktop`

* The wrapper pattern is intended to be replicated across the other desktop modules after validation on `MyServer`

### Windows Launcher Standardization

* Windows traceback-preserving launchers now use the same wrapper principle as the Jetson `.desktop` flow, but with `.cmd` scripts under `launchers/`
* Canonical repo-supported Windows wrappers now exist for the main tracked `My*.py` module entry points, documented in `WINDOWS_PERSISTENT_LAUNCHERS.md`
* `MyScannerWin.py` is intentionally excluded from the repo-supported wrapper set because it was removed from version control and should stay absent unless there is an explicit decision to restore it

### Line Ending Safeguard

* `.gitattributes` now forces LF line endings for `*.sh` and `*.desktop`
* This is specifically to keep Jetson launcher artifacts Linux-safe when they are edited or committed from Windows

---

## ⚠️ Known Issues

* Zoom slider can desync from pixmap scale (non-compounding rule must be enforced)
* Session manager may return stale paths across environments
* Continue.dev YAML/config sensitive to formatting
* Cross-platform path contamination (Jetson ↔ Windows)
* `MyVersifier` now remaps repo-local Windows session paths onto the active local repo root during startup, but other modules may still need the same normalization treatment if they restore machine-specific absolute paths
* Jetson desktop launchers should not point directly at Python if traceback preservation is required; wrapper-based launchers should be treated as the standard path going forward
* `MyServer.py` still has too much project-creation business logic
* `Core/engine.py` now compiles without the prior debug side effect `print("ENGINE MODULE LOADING")`
* `Core/__init__.py` / `Core` imports must be validated before switching `MyServer.py` to Core imports
* Event replay from SQLite is not yet implemented
* Discovery and acquisition remain separate responsibilities by design, but capability normalization between them is still incomplete
* TWAIN is intentionally unavailable for the current Canon TS3700 path because the machine exposes a usable 64-bit DSM but no 64-bit TWAIN source registration
* Canon TS3700 evidence on this machine indicates: 64-bit `twaindsm.dll` can load, but the installed Canon scan package registers WIA/STI files rather than a 64-bit TWAIN source, while Canon TWAIN source artifacts remain under the 32-bit `C:\Windows\twain_32` tree
* Native SANE acquisition remains device-dependent and should still be treated as best-effort until validated against non-AirScan-first hardware
* `Model/Backup Copies/0-MainUI copy/Ui2Py.py` is still a broad regeneration helper; even though its paths now point at the current Windows repo location, targeted `pyuic5` remains the safer default for intentional UI regeneration

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
* include the scripture-specific `Model/Project/Training/Tesseract` scaffold plus the workflow folders used by the OCR/training pipeline
* include NT book-folder template mappings for scriptural `Complete` and `Workflow` destinations, with destination-level selection in the project wizard
* exclude deep image trees and image files themselves

* Current explorer/training cleanup baseline:

* keep the Explorer "Exclude empty folders" toggle in the Designer/UI-generated surface instead of creating it dynamically at runtime
* keep project tracking aligned with MyTrainer workspace milestones, including `training_workspace_ready` and `training_progress_plotted`

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
* Reference-image session restore now persists correctly again through `PixlerSession.json`
* `start_image_load()` threading: **STABLE**
* `on_image_loaded()` receiving `QImage`: **CONFIRMED**
* RefImg display + `RefImgLE` sync: **WORKING**
* Crop apply from `ImagePreviewDialog` returns a full-resolution QImage in original image coordinates
* Applied crop is displayed directly in the MyPixler right-hand panel without an immediate second scaling pass
* Crop result preserves source image resolution metadata (`dotsPerMeterX`, `dotsPerMeterY`, `devicePixelRatio`, and color space where supported)
* Rotate, 90 CW/CCW, 180, deskew, clip, and erase now route through the shared preview/apply workflow instead of mixed legacy paths
* Mono-source TIFF save/overwrite path now preserves bilevel output from the canonical `QImage` rather than the display pixmap
* Legacy click-on-reference-image crop trigger and keep/edit prompt have been disabled; crop entry is now the explicit preview tool path only
* TIFF return/save path derives DPI from QImage dots-per-meter metadata instead of hard-coding 300 DPI
* Subprocess return-path crop handoff back to MyServer: **CONFIRMED**
* Rotate/save smoke test against `greek1516_Page_173.tif` confirmed source mode `1`, output mode `1`, and only `[0, 255]` pixel values in the saved result

### ✅ ImagePreviewDialog

* External module is the **canonical implementation**
* Constructor stabilized (no multi-parent / param conflicts)
* Crop coordinates:

* correctly mapped
* converted to original image space

* Preview behavior:

* Left = original
* Right = processed
* rotate preview now uses a reduced working image during slider drag for responsiveness, then recomputes the settled preview from the full-resolution source on slider release
* mono/bilevel preview rendering now uses a preview-only black/white display conversion instead of relying on Qt's default mono scaling path

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

* Current remaining gap:

* saved rotated mono TIFF output now matches document expectations materially better than preview
* preview has been tuned substantially closer, but still remains slightly lighter/thinner than the final saved result
* remaining work is preview-only calibration in `ImagePreviewDialog.py`, not TIFF processing or save-path correction

---

## ✅ File Intake / Drag-Drop Standardization

* Shared local file URL intake now lives in `ViewController/0-MainUI/LocalFileDrop.py`
* `LocalFileDropMixin` now provides:

* `install_local_file_drop(...)` for standard single-target image/text modules
* `install_local_file_drop_target(...)` for widget-specific routing in multi-pane modules
* shared non-modal drag-capable file pickers for text and image loads
* visible file-load feedback through terminal/status/wait-cursor helpers

* Primary file-open workflows were standardized to the shared non-modal picker path in:

* `MyVersifier`
* `MyReader`
* `MyScanner`
* `MyGrounder`
* `MyGlypher`
* `MyBoxer`
* `MyServer`
* `MyWriter`
* `MyPixler`
* `MyLexer`
* `MyLauncher`

* `MyVersifier` is the special multi-pane case:

* `RefText` was changed in Qt Designer so it is no longer read-only
* `MyVersifierUI.py` was regenerated from `QtDesignerUI/MyVersifierUI.ui`
* drops on `RefText` route to `getRefText(...)`
* drops on `VerseText` route to `getVerseText(...)`
* startup/file-load progress is now visible for long text loads and formatting passes

* Expected behavior after the rollout:

* Windows Explorer drag/drop works on the main intake widgets
* `MyExplorer` can act as a drag source and can also accept external file/folder drops into the project tree with collision-safe copy naming
* shared picker windows can act as drag sources
* dropped files load contents instead of inserting URL text
* `.nt` is treated as a text-file extension

* Constraint to preserve:

* native modal `QFileDialog` is not a reliable drag source back into the parent window on Windows
* keep using the shared non-modal picker path for drag-capable open workflows

* Repository status note:

* `MyScannerWin.py` was intentionally removed from version control and added to `.gitignore`; keep it out of the repo unless there is an explicit reason to restore it

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

* Keep `MyServer` backend-agnostic and continue pushing backend details into `Core/Scanner`
* Add a `mock_backend.py` for no-hardware tests and UI validation
* Add explicit backend diagnostics/capability reporting instead of only device-name lists
* Treat AirScan/eSCL as the default cross-platform transport for network-capable devices unless a future hardware path proves TWAIN or native SANE acquisition is materially better
* Validate `SaneScanner` against future genuinely local/non-AirScan Linux hardware rather than using the Jetson Canon path as the reference implementation
* Decide whether TWAIN should remain best-effort/optional or gain a future 32-bit helper process path

1. **Core / MyServer Unification**

   * Wire `MyServer.py` to use `Core.engine.ProjectCreationEngine`
   * Confirm `Core.event_bus.EventBus` can be imported cleanly
   * Confirm `Core.event_store.SQLiteEventStore` can be imported cleanly
   * Keep local `MyServer.py` engine classes until Core-driven UI project creation is runtime-tested

1. **Move Project Logic Out of MyServer**

   * Make `Core/engine.py` the single source of truth for `ProjectCreationEngine`
   * Remove duplicate `ProjectCreationEngine` from `MyServer.py` only after Core is fully validated
   * Keep `MyServer.py` as wiring/controller only

1. **SQLite Event Replay**

   * Add event loading to `SQLiteEventStore`
   * Create or stabilize `ProjectReplayEngine` under `Core/`
   * Reconstruct project state from event history

1. **UI Event Subscription Layer**

   * Subscribe UI handlers to EventBus events
   * Replace console-only event feedback with status/output UI updates
   * Keep UI changes reactive and main-thread safe

1. **Regression Test New Project Flow**

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
* `docs/development/DEV_NOTEBOOK.md` → active engineering notebook within the authoritative docs library

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

## 📚 Documentation Library Rule

* `docs/` is the authoritative knowledge repository for Biblion
* `docs/development/DEV_NOTEBOOK.md` is the active engineering notebook and replaces legacy lowercase `dev_notebook.md` references
* When older notes mention `dev_notebook.md`, normalize that reference to this file unless the note is explicitly discussing historical file layout
* Architecture-facing references should prefer the current docs library paths over legacy in-module markdown locations when both exist

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
* 2026-07-01: Jetson Canon TS3700 path validated with async scan-dialog loading, AirScan-first discovery, and SANE fallback entries that route final acquisition back through eSCL/AirScan by IP when native SANE transport is not dependable
* 2026-07-02: Shared `LocalFileDrop.py` drag/drop routing and non-modal file picker workflows were standardized across the main image/text modules, with `MyVersifier` using pane-specific target routing and visible load progress
* 2026-07-02: `MyScannerWin.py` was removed from version control and added to `.gitignore`, and should stay absent unless explicitly restored
* 2026-07-02: Windows persistent launcher wrappers were standardized for the tracked `My*.py` entry points and documented in `WINDOWS_PERSISTENT_LAUNCHERS.md`
* 2026-07-02: `MyExplorer.py` was upgraded from an internal-move-only tree to a real external drag/drop tree that can copy dropped files and folders into the project tree
* 2026-07-02: `Model/Backup Copies/0-MainUI copy/Ui2Py.py` was repointed at the current Windows repo paths for rare backup-copy UI regeneration use, but targeted `pyuic5` remains preferred over broad regeneration
* 2026-07-02: `Model/Project/Data/json/VersifierSession.json` was intentionally normalized by removing the duplicate `self.projectname` entry and updating the active Verse/Reference GroundTruth paths to the current Windows repo location
* 2026-07-02: `MyVersifier.py` startup path restore now detects repo-local Windows absolute paths in `VersifierSession.json` and remaps them onto the current local checkout so Jetson startup does not prepend `/home/.../BiblionOCR/` to `C:/...` fragments
* 2026-07-02: Scan wizard gained a persisted strict-SANE toggle that disables app-level AirScan fallback during Jetson USB validation, and SANE device discovery now labels native `scanimage -L` results separately from fallback entries
* 2026-07-02: Jetson strict USB SANE validation for Canon TS3700 failed even with `airscan` removed from both `dll.conf` and `dll.d`; `pixma` loaded but reported `0 devices`, so AirScan/eSCL remains the supported Jetson transport for this model
* 2026-07-03: `ScanWorkflow.py` extracted the shared scan wizard so `MyScanner.py` can use the same Core scanner backend stack as `MyServer.py` without a circular import
* 2026-07-03: `MyServer.py` now redirects ADF scan requests to `MyScanner.py`, while `MyScanner.py` supports both flatbed and ADF requests through the shared scanner workflow
* 2026-07-03: `QtDesignerUI/MyScannerUI.ui` was updated to restore a Designer-owned scan UI contract for `MyScanner`, adding MyServer-style `imageScannerbutton`, `actionImageScanner`, and `actionImageScanner_tb`, then regenerating `MyScannerUI.py` from that source
* 2026-07-04: project documentation was consolidated under `docs/`, and the active developer notebook was renamed to uppercase `docs/development/DEV_NOTEBOOK.md` to match the new library convention
* 2026-07-07: the public Biblion home page went live at `https://biblionocr.onrender.com/`, the Patreon posting flow succeeded against the hosted site URL, and the local weekly queue was tuned and regenerated for the remaining week

---

## 📚 Documentation Classification

### Documentation Root

* `docs/README.md`
* `docs/DOCUMENTATION_ARCHITECTURE.md`
* `docs/PROJECT MANIFESTO.md`

### Architecture-Facing

* `docs/architecture/PROJECT_ARCHITECTURE.md`
* `docs/architecture/PROJECT_CREATION_ARCHITECTURE.md`
* `docs/development/DESIGN_SPECIFICATION.md`
* `docs/development/DEPENDENCIES_AND_RELATIONSHIPS.md`

### HelpSystem-Facing

* `docs/development/README_HELP_SYSTEM.md`
* `docs/development/HELP_INTEGRATION_GUIDE.md`
* `docs/development/QUICK_REFERENCE.md`
* `docs/architecture/PROJECT_ARCHITECTURE.md`
* `docs/development/DEPENDENCIES_AND_RELATIONSHIPS.md`

### Development-Facing

* `docs/development/DEV_NOTEBOOK.md`
* `docs/development/WINDOWS_PERSISTENT_LAUNCHERS.md`
* `docs/development/UBUNTU24_DEV_TOOLS_AND_RESTORE.md`
* `docs/development/LOCAL_MASTER_SYNC_AFTER_PR.md`

### Reference-Only / Supporting

* `docs/development/DESIGN_SPECIFICATION.md`
* `docs/architecture/PROJECT_CREATION_ARCHITECTURE.md`
* `docs/development/PROJECT_SPEC.md`

---

## 🤖 Copilot Familiarization Notes — 2026-06-30

* Current runtime center of gravity is still `ViewController/0-MainUI/MyServer.py`, but project-creation ownership is intended to converge into `Core/engine.py`
* The safest boundary for future edits is: `MyServer.py` wires UI/runtime behavior, `Core/` owns lifecycle logic, and `MyPixler`/`ImagePreviewDialog` own image processing and preview state
* After any project-creation change, the first validation target should be the external project root at `C:/Users/Max/Projects`, the `_registry.json` update path, and ProjectFolderList-driven structure generation
* The highest-risk refactor remains removing duplicate engine/event classes from `MyServer.py` before Core imports, runtime wiring, and replay behavior are fully validated
* The authoritative engineering notebook now lives at `docs/development/DEV_NOTEBOOK.md`; avoid reviving legacy lowercase notebook copies or stale parallel notebook paths
* 2026-07-04: `ProjectFolderList.py` now prunes new-project generation down to runtime-safe `Model/Project/Data/json` plus minimal workflow/training scaffolding, instead of restoring `Data/SQLite`, `Data/csv`, or deep training payloads from older manifests
* 2026-07-04: `Model/Project/Data/esword` remains intentionally preserved in the curated manifest because MyWriter is expected to generate and update those files later
* 2026-07-04: `MyServer` file/directory pickers now share a Projects-root fallback helper, and `actionOpen_Project` launches `MyExplorer` at the selected validated project root so both project browsing entry points start from the same anchor
* 2026-07-04: physically pruned unreferenced workspace folders `Model/Project/Data/Archive`, `Model/Project/Training/tesstrain`, `Model/Project/Training/staged_ground_truth`, and `ViewController/0-MainUI/TessTrainBoxFiles`; retained `Data/csv`, `Data/SQLite`, and `Data/esword` because `csv`/`SQLite` are still referenced by active modules and `esword` is reserved for MyWriter output
* 2026-07-04: offscreen validation against `C:/Users/Max/Projects/Erasmus1516` confirmed `MyExplorer(start_dir=...)` roots the tree at the selected project folder as intended
* 2026-07-04: added `DESIGN_SPECIFICATION.md` to define the repo vocabulary around System, Workspace, Project, Workflow, Process, Stage, Module, Artifact, Session, Event, and Reference Data so future cleanup and MyTrainer discussions use consistent boundaries
* 2026-07-04: `MyPixler` now routes `Denoise` through morphology preview, `Clip` through inverse selection with background fill, and `Erase` through a paint-click preview flow with adjustable brush radius and background-color replacement
* 2026-07-04: active preview dialogs now preserve one comparison contract across the repo: left = original/reference input, right = processed/output result; `MorphologyDialog` was corrected to match `ImagePreviewDialog`
* 2026-07-04: final broad checkpoint commit is expected to bundle outstanding scanner/session/UI/icon resource changes, including `MyScanner`, `Core/Scanner/*`, regenerated UI resources, session JSON updates, and new scan-workflow support files, even though further test-driven cleanup is still expected afterward

---

## 🚀 Milestone — Public Introduction Video v1.0

**Date:** July 2026

## Summary

BiblionOCR reached its first major public-facing milestone with the completion and publication of the **Introduction Video v1.0**. This marks the project's transition from an architecture and development effort into a publicly demonstrable software system.

That public-facing transition is now backed by the repository itself being live on GitHub as a public repository, with contributor intake routed through the documented membership and policy workflow.

The introduction video serves as the project's visual identity and provides a concise overview of the philosophy behind BiblionOCR rather than an exhaustive feature demonstration.

## Production Artifacts

The following production assets were completed:

* Approved production storyboard.
* Production execution sequence.
* Licensed Shutterstock asset organization.
* Narration generation pipeline.
* Kdenlive editing workflow.
* Final public YouTube publication.

Public introduction video:

<https://youtu.be/zrJQzivQwT4>

## Production Lessons Learned

### Narration

* Initial attempts to use OpenAI Text-to-Speech were unsuccessful because the project API did not include access to audio speech models.
* Edge TTS was adopted as the production narration engine for RC1.
* Phonetic spelling was used where necessary to improve pronunciation of "BiblionOCR."

### Video Editing

* DaVinci Resolve could not be used on the current Windows development workstation because of OpenGL compatibility limitations with the installed Intel HD Graphics hardware.
* Kdenlive was adopted as the production editor and performed successfully throughout the remainder of the project.

### Asset Management

A dedicated production asset hierarchy was established under the Developer workspace, including:

* Storyboards
* Narration
* Audio
* Licensed imagery
* Production documentation

Licensed Shutterstock imagery is organized into semantic production categories:

* A — Emergence
* B — Cognition
* C — Systems
* D — Architecture
* E — Identity

## Project Status

The following milestones are complete:

* Developer Services v1.8
* Observable Runtime architecture
* Developer Mode architecture documentation
* Public Introduction Video v1.0
* Public YouTube publication
* Public GitHub repository launch

The repository now contains both the software architecture and the supporting public-facing project identity.

## Next Development Phase

With the public introduction complete, development focus returns to core application capabilities, including:

* Continued Developer Services integration.
* Runtime observability enhancements.
* OCR workflow improvements.
* Scanner integration.
* Architecture visualization.
* Preparation for future Introduction Video revisions as the software evolves.

## Housekeeping Log (2026-07-20)

* Promoted the active checkpoint commit to both `origin/master` and `origin/development`.
* Added tracking for the `Developer/Publisher` tutorial-generation prototype.
* Added ignore rules for machine-local artifacts generated by the Patreon local blog tooling runtime.
* Removed tracked Playwright profile runtime cache/state data from repository history going forward.
* Current intentionally uncommitted local path: `.venv/`.

---

## Session Handoff (2026-08-07) - Process Smoke Test

Scope summary:

* Executed the architecture-normalization checklist lane as an end-to-end smoke test after checklist reflow.

Touched-file list from git status --short:

* M ViewController/Model/Project/Data/json/Session.json
* M docs/development/DEVELOPMENT_ROUTINE_CHECKLIST_ONE_PAGE.md

Validation status by gate:

* problems/lint:
  * in-scope files: clean (0)
  * full workspace: clean (0)
* compile:
  * python3 -m py_compile Core/engine.py Core/event_bus.py Core/event_store.py Core/ris.py ViewController/0-MainUI/MyServer.py
  * result: pass
* smoke tests:
  * QT_QPA_PLATFORM=offscreen timeout 12s .venv/bin/python ViewController/0-MainUI/MyServer.py
  * result: pass (bounded startup)
* manual UI checks:
  * not required for this smoke-test cycle (documentation/process-only delta)

Problems detail:

* full-workspace total count: 0
* in-scope count: 0
* unresolved files: none

Unresolved risks/blockers:

* Session.json remains as runtime-local state drift and should stay out of commit unless explicitly requested.

Next immediate action:

* Commit docs/development/DEVELOPMENT_ROUTINE_CHECKLIST_ONE_PAGE.md as a focused checklist-reflow docs commit if maintainer approves.

---

## Session Handoff (2026-08-08) - Compute Documentation Reflow

Scope summary:

* Reflowed Compute Engine documentation into a lint-clean strategy/contract split and consolidated the Jetson architecture narrative into the architecture docs lane.

Touched-file list from git status --short:

* M docs/development/COMPUTE_ENGINE_ARCHITECTURE.md
* ?? docs/development/COMPUTE_ENGINE_ROADMAP.md
* ?? docs/architecture/nano/BiblionOCR_Intelligent_Compute_and_Jetson_Architecture.md
* M ViewController/Model/Project/Data/json/Session.json (local runtime drift, out of scope)

Validation status by gate:

* problems/lint:
  * in-scope files: clean (0)
  * full workspace: clean (0)
* compile:
  * not required this cycle (docs-only change set; no Python runtime edits)
* smoke tests:
  * not required this cycle (no runtime behavior change)
* manual UI checks:
  * not required this cycle (no UI interaction change)

Problems detail:

* full-workspace total count: 0
* in-scope count: 0
* unresolved files: none

Unresolved risks/blockers:

* Session.json remains modified as runtime-local state and should remain uncommitted unless explicitly requested.

Next immediate action:

* Commit and resync the three compute documentation files as a docs-only batch.

---

## 📅 Last Updated

2026-08-08

---

## Session Handoff (2026-08-13) - MyExplorer-Driven Development Backup/Restore

Scope summary:

* Implemented MyServer development backup/restore governance with MyExplorer as the default folder selector and added MyExplorer File-menu trash/restore actions.

Touched-file list from git status --short (in-scope):

* M Developer/QtDesignerUI/MyExplorerUI.ui
* M Developer/QtDesignerUI/MyServerUI.ui
* M ViewController/0-MainUI/MyExplorer.py
* M ViewController/0-MainUI/MyExplorerUI.py
* M ViewController/0-MainUI/MyServer.py
* M ViewController/0-MainUI/MyServerUI.py

Validation status by gate:

* problems/lint:
  * in-scope files: clean (0)
  * full workspace: clean (0)
* compile:
  * python3 -m py_compile ViewController/0-MainUI/MyServer.py ViewController/0-MainUI/MyExplorer.py ViewController/0-MainUI/MyServerUI.py ViewController/0-MainUI/MyExplorerUI.py
  * result: pass
* smoke tests:
  * QT_QPA_PLATFORM=offscreen timeout 12s .venv/bin/python ViewController/0-MainUI/MyServer.py
  * QT_QPA_PLATFORM=offscreen timeout 12s .venv/bin/python ViewController/0-MainUI/MyExplorer.py --select-dir --start-dir "$PWD" --output-file /tmp/biblion_picker_test.txt --title "Picker Smoke"
  * result: pass (bounded startup; no immediate traceback)
* manual UI checks:
  * Verified generated UI action presence for MyServer and MyExplorer via offscreen runtime object checks.

Problems detail:

* full-workspace total count: 0
* in-scope count: 0
* unresolved files: none

Commit/sync:

* commit: 39f351c
* title: feat(myserver,myexplorer): add explorer-driven backup restore dialogs
* push: origin/master synced (39f351c)

Unresolved risks/blockers:

* Windows recycle-bin restore path is not yet implemented in MyExplorer runtime; currently Linux/macOS have concrete trash-location handling.
* Unrelated working-tree drift remains out of scope (ProjectFolderList and runtime-local Session.json changes).

Next immediate action:

* Start module-by-module standardization of workflow folder-picking dialogs to MyExplorer after maintainer approval of module order.

Windows transition runbooks (2026-08-13):

* docs/development/WINDOWS10_REPO_BACKUP_AND_RECLEAN.md
* docs/development/WINDOWS10_WINDOWS_DEVELOPMENT_BRANCH_SETUP.md
