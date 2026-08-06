# BiblionOCR Test And Debug Checklist

Date: 2026-08-04

Baseline branch: `master`

Baseline commit: `6746b5d`

Purpose: provide a printable, high-signal checklist for the next large testing and debugging effort after the scripture data foundation, LFS migration, project-governance cleanup, workflow wizard rollout, and branch resynchronization work.

---

## Stop Conditions Before Starting

- Confirm the active branch is `master`.
- Confirm `git status --short` returns no output.
- Confirm `git rev-parse --short HEAD` returns `6746b5d` or a newer agreed baseline.
- Confirm `ubuntu_development` is expected to match `master` for this test cycle:

```bash
git rev-parse master
git rev-parse ubuntu_development
```

- Confirm Git LFS is available:

```bash
git lfs version
git lfs ls-files
```

- Confirm the main scripture DB payloads exist locally:

```bash
ls -lh Model/Project/Data/SQLite
ls -lh Model/Project/Data/esword
```

---

## Execution Order Map

### Finish-to-start sequence (required)

Run these in order and do not skip ahead until each item passes.

1. Stop Conditions Before Starting
2. Phase 1 (all items)
3. Phase 2 item 4 (`MyServer` ownership rules)
4. Phase 2 item 5 (new project creation)
5. Phase 2 item 6 (project settings workflow)
6. Phase 3 item 7 (shared project status surface)
7. Phase 3 item 8 (session persistence)
8. Phase 3 item 9 (weighted progress integrity)
9. Phase 3 item 10 (workflow wizard launch integrity)
10. Phase 3 item 11 (columns-per-page persistence)

### Arbitrary-order pool (run as capacity allows)

These are independent validation passes once the finish-to-start sequence is green.

- Phase 4 items 10 to 12 (scripture foundation and manifest integrity)
- Phase 5 items 13 to 16 (workflow-specific functional passes)
- Phase 6 items 17 to 18 (cross-platform and environment checks)

---

## Phase 1: Fast Failure Scan

Goal: catch import errors, missing files, and startup crashes before deeper workflow testing.

### 1. Python syntax and import sanity

- Run targeted compile checks for recently touched code:

```bash
python3 -m py_compile \
  Core/engine.py \
  Core/project_database.py \
  Core/project_tracking.py \
  ViewController/0-MainUI/MyServer.py \
  ViewController/0-MainUI/helpers/Dialogs/ProjectSettingsDialog.py \
  ViewController/1-PreProcess/MyBoxer.py \
  ViewController/1-PreProcess/MyGlypher.py \
  ViewController/1-PreProcess/MyPixler.py \
  Developer/utilities/scripture_data_parity.py
```

### 2. Runtime launcher smoke checks

- Smoke-test the core windows from the canonical launch paths:
  - `MyServer`
  - `MyBoxer`
  - `MyGlypher`
  - `MyPixler`
  - `MyReader`
  - `MyGrounder`
  - `MyTrainer`
  - `MyLexer`
  - `MyResolver`
  - `MyVersifier`
  - `MyWriter`

- Minimum pass condition:
  - window starts
  - no immediate traceback
  - no missing UI file error
  - no missing shared helper import
  - no crash on empty/default session state

### 3. Immediate regression watch list

- `MyGlypher` line-height slider with empty text field
- `MyServer` startup with cleaned runtime environment
- moved module imports under `ViewController/1-PreProcess`, `2-TrainTesseract`, `3-Process`, `4-PostProcess`
- Qt Designer `.ui` path fallbacks

---

## Phase 2: Project Governance And Creation

Goal: prove the project-administration refactor still behaves correctly.

### 4. MyServer ownership rules

- Verify `New Project` appears only in `MyServer`.
- Verify `Project Settings` appears only in `MyServer`.
- Verify non-server windows do not expose milestone override administration.
- Verify project workflow administration remains anchored in `MyServer` even though workflow entry actions now exist across modules.

### 5. New project creation

- Create one fresh project through `MyServer`.
- Confirm creation completes without traceback.
- Confirm the generated project contains:
  - `Model/Project/Data/sqlite/project_metadata.sqlite`
  - `Model/Project/Data/sqlite/Project Settings.db`
  - `Model/Project/Data/SQLite/<ProjectName>.db` (default project deliverable DB, for example `Erasmus1516.db`)

- Confirm project metadata fields are seeded correctly enough to open the project again.

### 6. Project settings workflow

- Open `Project Settings` from `MyServer`.
- Verify stacked-page navigation works.
- Verify `Project Database`, `RIS Settings`, `Milestone Settings`, and `Module Handshakes` pages are available.
- Change one milestone-related field and confirm save/reload persistence.
- Change one project-database field (for example `ProjectDatabase` or `ProjectFont`) and confirm save/reload persistence.
- Change `NumberColumns` and confirm the saved value survives dialog close/reopen.

---

## Phase 3: Progress, Status, And Session State

Goal: verify the cross-module workflow state is consistent after centralization.

### 7. Shared project status surface

- Open `MyServer` and `MyPixler` against the same project.
- Confirm both show the same active project identity.
- Confirm project progress and page progress render without error.
- Confirm no non-server milestone admin control reappears.

### 8. Session persistence

- Close and reopen the app set.
- Confirm the active project selection persists.
- Confirm missing session JSON does not crash startup.

### 9. Weighted progress integrity

- Use a project with partial workflow data.
- Confirm progress values are:
  - numeric
  - bounded to valid percentages
  - stable across reopen

### 10. Workflow wizard launch integrity

- Open `Project Workflow Wizard` from `MyLauncher`.
- Open `Page Workflow Wizard` from `MyLauncher`.
- Confirm stage order follows numbered `ViewController` folders:
  - `0-MainUI`
  - `1-PreProcess`
  - `2-TrainTesseract`
  - `3-Process`
  - `4-PostProcess`
- Confirm `Run Full Macro` and stage-specific actions launch without traceback.
- Confirm existing manual launch actions still work after using the wizards.
- Open workflow wizard entry actions from these non-launcher windows and confirm they delegate correctly into `MyLauncher`:
  - `MyExplorer`
  - `MyPixler`
  - `MyBoxer`
  - `MyGlypher`
  - `MyReader`
  - `MyGrounder`
  - `MyTrainer`
  - `MyLexer`
  - `MyResolver`
  - `MyVersifier`
  - `MyWriter`

### 11. Columns-per-page persistence

- Open a project in `MyServer` and use `Set Columns Per Page`.
- Confirm the value is written into `project_metadata.sqlite`.
- Open `MyScanner` against the same active project and confirm its `Set Columns Per Page` action updates the same persisted value.
- Confirm `NumberPageBoxes` stays synchronized with `NumberColumns`.
- Confirm project/page status surfaces continue to render normally after the update.

---

## Phase 4: Scripture Data Foundation

Goal: validate the newly standardized scripture reference assets and parity workflow.

### 10. LFS-backed binary payloads

- Confirm these are available locally and not just pointer text in the working tree:
  - `Model/Project/Data/SQLite/FROMVS.db`
  - `Model/Project/Data/SQLite/RMAC.db`
  - `Model/Project/Data/SQLite/TRBible.db`
  - `Model/Project/Data/SQLite/TRBibleWords.db`
  - `Model/Project/Data/SQLite/TRiBible.db`
  - `Model/Project/Data/SQLite/TRiBibleWords.db`
  - `Model/Project/Data/esword/rmac.dctx`

- Check:

```bash
git lfs ls-files
ls -lh Model/Project/Data/SQLite Model/Project/Data/esword
```

### 11. CSV/JSON parity utility

- Run:

```bash
python3 Developer/utilities/scripture_data_parity.py --root . --write-json --force
```

- Pass conditions:
  - no crash on `rmac.csv`
  - no bad delimiter inference on single-column CSVs
  - headered files remain object lists where expected
  - headerless files remain string lists or row arrays as intended

- Spot-check outputs:
  - `Model/Project/Data/json/EnglishProperNames.json`
  - `Model/Project/Data/json/ProperNames.json`
  - `Model/Project/Data/json/FromvsDiacritics.json`
  - `Model/Project/Data/json/FROMVS3_0_PUA_Norm.json`
  - `Model/Project/Data/json/RMAC.json`

### 12. Manifest and folder-list integrity

- Confirm canonical manifest coverage is still correct after any test-driven edits:
  - `ViewController/ScriptureProjectFolderList.txt`
  - `ProjectFolderList.txt`

- If paths move, regenerate:

```bash
python3 ViewController/utilities/0-MainUI/helpers/ProjectFolderList.py
```

### 12b. Branch sync integrity

- After test/debug commits on `master`, preserve the same commit flow by syncing `ubuntu_development` to `master`:

```bash
git push origin master
git push origin master:ubuntu_development
```

- Verify both remote heads are the same commit:

```bash
git ls-remote --heads origin master ubuntu_development
```

---

## Phase 5: Workflow-Specific Functional Passes

Goal: test the highest-risk user-visible operations, not just startup.

### 13. MyBoxer

- Open a project with usable text/image content.
- Verify `Word Box` surfaces still load.
- Verify line/word table interactions do not raise exceptions.
- Verify load/save/export paths still function.
- Verify workflow wizard entry actions are present and non-destructive.

### 14. MyPixler

- Open project images.
- Verify preview and cropping flows.
- Confirm no crash when workflow/session files are sparse or newly created.

### 15. MyResolver and MyVersifier

- Verify they can access the scripture data foundation.
- Confirm no missing-path or empty-db crash at startup.
- Confirm normalization-dependent actions still run.

### 16. Reader / Grounder / Trainer slice

- Verify startup on empty or newly created projects.
- Confirm no zoom, slider, or empty-input crash.
- Confirm training-related directory expectations still match manifest paths.

---

## Phase 6: Cross-Platform / Environment Risk Scan

Goal: avoid rediscovering known environment-specific failures late.

### 17. Linux workspace checks

- Prefer `python3`, not `python`.
- Confirm launcher wrapper scripts still resolve the correct module paths.
- Confirm Snap-hosted VS Code runtime sanitation still prevents GTK/libpthread startup failures.

### 18. Windows compatibility watch list

- Avoid shell-only runtime launches in touched modules.
- Prefer `sys.executable` and `subprocess.Popen([...])` for Python subprocesses.
- Watch for path-case issues around `sqlite` versus `SQLite`.

---

## Triage Rules During Debugging

- Fix startup blockers before behavioral defects.
- Fix project creation and project loading regressions before downstream module polish.
- Fix data-foundation and path-resolution issues before UI cleanup.
- Re-run the narrowest failing command immediately after each fix.
- Do not broaden scope between a first fix and its first focused validation.

---

## Suggested Command Set For The Session

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
git lfs version
git lfs ls-files
python3 -m py_compile Developer/utilities/scripture_data_parity.py
python3 Developer/utilities/scripture_data_parity.py --root . --write-json --force
python3 ViewController/utilities/0-MainUI/helpers/ProjectFolderList.py
```

---

## Sign-Off Checklist

- [ ] branch is still clean
- [ ] no startup traceback in the core `My*` windows tested
- [ ] project creation works end-to-end
- [ ] project settings save and reload correctly
- [ ] progress/status surfaces remain consistent across modules
- [ ] scripture LFS assets are present and usable
- [ ] parity utility runs cleanly
- [ ] no manifest drift remains
- [ ] any new defects are written down as a prioritized follow-up list

---

## Notes For Printing

- Print this checklist as-is for session tracking.
- Mark failures with the exact module, command, traceback, and data path involved.
- After the session, fold results back into `docs/development/DEV_NOTEBOOK.md` or a focused bug-fix PR.
