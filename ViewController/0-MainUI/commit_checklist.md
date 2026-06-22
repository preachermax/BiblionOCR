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

---

## 📅 Last Reviewed

2026-06-22

---
