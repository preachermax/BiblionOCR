# 🔐 BiblionOCR Commit Checklist

## 📌 Purpose

Ensure every commit represents a **stable, intentional state** and does not introduce hidden regressions across MyServer, MyPixler, and ImagePreviewDialog.

---

## 🧠 Pre-Commit Mental Check

* [ ] Am I committing **working behavior**, not just code changes?
* [ ] Did I test the **actual runtime path**, not just isolated functions?
* [ ] Am I solving **one problem at a time**?

---

## 🧪 Runtime Validation (Required)

### Core Systems

* [ ] MyPixler launches **standalone**
* [ ] Default session image loads correctly
* [ ] `RefImgLE` updates with correct filename

### Image Loading

* [ ] `start_image_load()` fires correctly
* [ ] Worker thread completes without:

  * `QThread destroyed` errors
  * orphaned threads
* [ ] `on_image_loaded()` receives valid `QImage`

### Crop / Preview

* [ ] Rubber band selection works
* [ ] Crop coordinates print correctly
* [ ] Preview dialog:

  * Left = original
  * Right = processed
* [ ] Apply updates **correct panel only**

### Zoom

* [ ] Zoom does not:

  * distort aspect ratio
  * compound scaling
* [ ] Always scales from **original pixmap**

---

## 🔗 Boundary Integrity Check

### MyServer

* [ ] No crop logic exists
* [ ] Only handles:

  * image loading
  * navigation
  * launching MyPixler

### MyPixler

* [ ] Owns:

  * crop
  * preview dialog
  * processing logic

### ImagePreviewDialog

* [ ] Single canonical implementation
* [ ] Accepts:

  * `QImage`
  * processor function
* [ ] Uses **params dict (not Qt update)**

---

## ⚠️ High-Risk File Check (DO NOT ACCIDENTALLY COMMIT)

* [ ] `__pycache__/`
* [ ] `*.pyc`
* [ ] `.continue/` configs (unless intentional)
* [ ] Session files with local paths:

  * `Session.json`
  * CSV mirrors
* [ ] Large generated files:

  * `UI_Icons.py` (only if intentionally regenerated)

---

## 📂 Git Hygiene

* [ ] `.gitignore` is respected
* [ ] No unintended deleted files:

  * especially config files
* [ ] No environment-specific paths hardcoded

---

## 🧾 Notebook Sync Rule

Update `dev_notebook.md` ONLY if:

* [ ] Behavior changed
* [ ] Bug fixed
* [ ] New issue discovered
* [ ] Architecture clarified

DO NOT update for:

* formatting
* debug prints
* minor edits

Release-facing changes should also confirm the shared font install path is still valid after `update_fonts.py` runs, especially before the final MyTrainer compilation.

---

## 🏷️ Commit Message Format

Use structured messages:

```bash
stabilize: confirmed MyPixler standalone load
fix: crop preview panel routing
debug: added thread lifecycle tracing
wip: zoom slider behavior investigation
```

---

## 🔒 Final Authority Rule

> Only the developer triggers commits.

AI tools may:

* suggest changes
* prepare edits

But commits are:

* reviewed
* validated
* approved

by the developer only.

---

## 🎯 Final Check

* [ ] System is stable
* [ ] No duplicate UI update paths
* [ ] No thread lifecycle issues
* [ ] No cross-boundary responsibility violations
* [ ] Release font path has been refreshed for the current compiled build
* [ ] MyTrainer release notes match the current font installation workflow

---

## 📅 Last Reviewed

2026-06-22

---

## ✅ Change Validation Checklist

Use this checklist after updates to the release-font workflow, SessionManager, or release documentation.

### Release Font Workflow

* [ ] `update_fonts.py` completes successfully
* [ ] `update_fonts.py` installs `FROMVS.ttf` into the project-local `ViewController/0-MainUI/fonts` path
* [ ] `release-font-refresh-and-smoke-test` runs in sequence without manual intervention

### SessionManager Font Resolution

* [ ] `SessionManager.resolve_font_path('FROMVS')` finds the repo-local font path by default
* [ ] `SessionManager.build_workflow_font('FROMVS', ...)` returns a valid QFont family and size
* [ ] Existing callers still work when `module_dir` is passed explicitly

### Release / Compilation Docs

* [ ] `dev_notebook.md` shows release-font workflow before compilation note
* [ ] `README_HELP_SYSTEM.md` reflects the release workflow coverage note
* [ ] `PROJECT_ARCHITECTURE.md` and `DEPENDENCIES_AND_RELATIONSHIPS.md` still describe MyTrainer release expectations

### Smoke / Runtime Safety

* [ ] `smoke_test_server_to_pixler.py` still prints `TEST_OK`
* [ ] MyPixler standalone launch still works after the SessionManager change
* [ ] No new environment-specific font warnings appear during startup

### One-Time Trial Run Order

1. Run `update_fonts.py`
2. Run `release-font-refresh-and-smoke-test`
3. Confirm `SessionManager.resolve_font_path('FROMVS')` resolves the repo-local font path
4. Confirm the smoke test still ends with `TEST_OK`

The trial run can be used to verify the workflow once, but the final go/no-go decision remains with the developer.

### Trial Run Result

* `update_fonts.py` completed successfully and refreshed `FROMVS.ttf` into `ViewController/0-MainUI/fonts`
* `smoke_test_server_to_pixler.py` completed successfully with `TEST_OK`
* `SessionManager.resolve_font_path('FROMVS')` resolved the repo-local font path by default
* `smoke_test_server_pixler_return_loop.py` completed successfully with `TEST_OK`
* MyServer consumed the returned crop and preserved the overwrite decision in the server-side flow
