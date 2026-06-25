# BiblionOCR Developer Notebook

## 📌 Project Overview

* **MyServer**: Image loading UI (TIFF stack, async)
* **MyPixler**: Image processing + preview tools
* **ImagePreviewDialog**: Interactive preview (crop, compare)
* **Session Manager**: Stores last-used images

---

## 🧠 Architecture Notes

* All image loading is **threaded (QThread)**
* UI updates must occur in **main thread only**
* Pixmap scaling must always use **non-null source**
* Crop operates on **QImage, not QPixmap**
* **Never scale from an already scaled pixmap**

---

## ⚠️ Known Issues

* Zoom slider can desync from pixmap scale (non-compounding rule must be enforced)
* Session manager may return stale paths across environments
* Continue.dev YAML/config sensitive to formatting
* Cross-platform path contamination (Jetson ↔ Windows)

---

## 🔧 Current Stabilization State (CRITICAL)

### ✅ Release Font Workflow

* The cross-platform font refresh task (`release-font-refresh-and-smoke-test`) is now part of the release path
* This is the first release step before any final build packaging
* SessionManager now resolves the repo-local `ViewController/0-MainUI/fonts` path by default

### ✅ Compilation Note

* This release-font step will be reused as a stable release step for **MyTrainer**
* MyTrainer is the final module planned for development, so its release compilation must include the current font installation path

### ✅ MyPixler

* Standalone launch: **WORKING**
* Session image load: **WORKING**
* `start_image_load()` threading: **STABLE**
* `on_image_loaded()` receiving `QImage`: **CONFIRMED**
* RefImg display + `RefImgLE` sync: **WORKING**
* Crop apply from `ImagePreviewDialog` returns a full-resolution QImage in original image coordinates
* Applied crop is displayed directly in the MyPixler right-hand panel without an immediate second scaling pass
* Crop result preserves source image resolution metadata (`dotsPerMeterX`, `dotsPerMeterY`, `devicePixelRatio`, and color space where supported)
* TIFF return/save path now derives DPI from QImage dots-per-meter metadata instead of hard-coding 300 DPI
* Subprocess return-path crop handoff back to MyServer: **CONFIRMED**

### ✅ ImagePreviewDialog

* External module is now **canonical implementation**
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
  * `get_preview_result()` remains available for exact visible-preview output, but MyPixler crop apply intentionally uses `get_result()`

### ⚠️ In Progress

* Zoom interaction (especially right-hand preview)
* MyServer → MyPixler parameter passing
* Session synchronization across systems
* Continued runtime testing of crop DPI/appearance across image formats and Windows ↔ Jetson environments

### ✅ Closed-Loop Crop Return

* MyPixler can run in subprocess mode and write its cropped result to a return file
* MyServer can consume that returned crop and keep the overwrite decision on its side
* The closed-loop smoke test completed successfully with `TEST_OK`

---

## 🧱 System Boundaries (LOCKED)

### MyServer

* Responsibilities:

  * image selection
  * TIFF stack loading
  * navigation
  * launching MyPixler
* ❌ MUST NOT contain:

  * crop logic
  * preview logic
  * image processing

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
  * parameter control (via `params` dict)
  * rendering original vs processed comparison
* Input:

  * `QImage`
  * processor function
* Output:

  * processed `QImage`

---

## 🔧 Current Fixes Applied

* Removed `showRefImg()` duplication (eliminated dual load paths)
* Centralized loading via `start_image_load`
* Fixed eventFilter coordinate mapping (viewport → label → image space)
* Eliminated incorrect `Qt.update()` misuse for params
* Stabilized async image loading lifecycle
* Repaired external `ImagePreviewDialog.py`:

  * single canonical class
  * QImage-based processing
  * non-compounding zoom support
  * proper crop parameter handling
  * editable crop rubberBand with 8 light-blue grip handles
  * crop overlay stays visible until Apply/Cancel
  * right preview refreshes after initial selection and grip-handle resize
  * full-resolution crop result preserves source QImage DPI/resolution metadata
* Removed legacy in-file preview dialog from MyPixler
* Fixed stale `json.load(f)` usage patterns
* Corrected workflow readers pointing to wrong JSON sources

---

## 🎯 Next Safe Runtime Test Steps (ONLY)

1. **MyPixler Zoom Stability Test**

   * Verify:

     * zoom does not compound
     * scaling always uses original pixmap
     * right panel behaves independently

2. **Crop → Zoom Interaction**

   * Crop selection → apply
   * Then zoom result image
   * Confirm:

     * no coordinate drift
     * no pixmap corruption
      * applied crop size equals original pixel dimensions minus cropped-away margins
      * source DPI/resolution metadata is preserved after Apply and after TIFF return/save

3. **MyServer → MyPixler Launch Test**

   * Pass image path explicitly
   * Confirm:

     * overrides session image
     * correct image loads in MyPixler

4. **Session Manager Sync Check**

   * Load image manually
   * Restart MyPixler
   * Confirm:

     * same image restored
     * no stale path fallback

---

## 🚫 High-Risk Files (DO NOT ACCIDENTALLY COMMIT)

* `__pycache__/`
* `*.pyc`
* `.continue/` configs (unless intentional)
* Session files:

  * `Session.json`
  * CSV mirrors (may contain machine-specific paths)
* Generated UI/resource files:

  * `UI_Icons.py` (only if intentionally regenerated)

---

## 🧪 Debug Patterns

Always print:

* `pixmap.isNull()`
* scale factors
* thread lifecycle:

  * start
  * progress
  * finish

Rules:

* Avoid duplicate UI update paths
* Never scale from scaled pixmap
* Never mix QPixmap/QImage responsibilities

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
* Current dev: Windows 10

Rules:

* Maintain **Python 3.8 compatibility**
* Maintain **PyQt5 compatibility**
* Avoid hardcoded absolute paths
* Use `os.path` / `pathlib`

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

* formatting
* debug prints
* minor edits

---

## 🧭 Checkpoint Summary — 2026-06-22

* Branch: `Biblion-Branch1`
* Focus:

  * MyPixler stabilization
  * ImagePreviewDialog correctness
  * async TIFF loading
  * crop/zoom correctness

### Key Stability Wins

* MyPixler standalone load working
* Thread lifecycle stabilized
* Preview dialog unified and functional
* Crop coordinate system fixed

### Remaining Risk Areas

* Zoom behavior (especially right panel)
* Cross-system path handling
* Session manager consistency
* Parameter passing from MyServer

---

## 🗂️ File Ownership

* MyServer → input only
* MyPixler → processing only
* ImagePreviewDialog → preview only

---

## 💡 Personal Workflow Insight

* Switch from “build mode” → “learning mode” when diminishing returns hit
* Debug by isolating systems first (MyPixler → then integration)
* Avoid multi-variable debugging

---

## 🧾 Decision Log

* 2026-06-22: Hybrid AI workflow adopted
* 2026-06-22: External ImagePreviewDialog made canonical
* 2026-06-22: MyServer stripped of crop responsibilities
* 2026-06-22: Threaded image loading stabilized
* 2026-06-22: Developer notebook designated as project memory authority
* 2026-06-22: Commit discipline + checklist introduced
* 2026-06-22: MyPixler standalone crop/apply/zoom milestone validated. Standalone launch, session/manual image load, crop dialog, rubberBand selection, crop apply to right-hand panel, right-panel crop-result zoom/scaling, and left/right zoom combo synchronization are working. Remaining refinement: right-hand crop-result contrast/mono display quality. Next integration target: MyServer → MyPixler launch/path passing.
* 2026-06-22 [Source: Copilot + Max]: Checkpoint commit prepared and executed. Staged files: .gitignore, dev_notebook.md, commit_checklist.md, AIcommitWorkflow.md, ImageLoadWorker.py, TiffStackWorker.py, ImagePreviewDialog.py, MyPixler.py, pycache bytecode removal. Excluded from this commit: MyServer.py, MyServerUI.py, Session.json, Continue.dev config, UI_Icons.py resource churn (held for separate integration/cleanup commits). Debug prints removed. Git hygiene improved. New branch Biblion-Branch2 created for continued integration work. Checkpoint message: "stabilize: checkpoint standalone MyPixler preview/crop/zoom workflow".

---

## 📚 Documentation Classification

### Release-Facing

* update_fonts.py
* update_fonts.txt
* .vscode/tasks.json

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

* No strong standalone reference-only markdowns were identified in the current help bundle subset

## 📅 Last Updated

2026-06-22

---
