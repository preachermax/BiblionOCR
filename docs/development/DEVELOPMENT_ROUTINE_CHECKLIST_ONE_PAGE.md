# BiblionOCR Development Routine Checklist (One Page)

Use this as a fast, repeatable execution checklist for daily development work.

## A) Preflight (Before Editing)

1. Confirm requirement scope in one sentence.
2. Identify target files: runtime, UI.ui, UI.py, docs, tests.
3. Check local state:

```bash
git status --short
```

1. Note unrelated local artifacts that must stay out of commit.

## B) Implementation Discipline

1. Keep edits narrow and task-specific.
2. Apply policy in shared control points first.
3. Avoid unrelated refactors while fixing a scoped issue.

## C) UI Lock-Step Rule

If UI behavior/menu/actions changed:

1. Update Qt Designer source in `Developer/QtDesignerUI/*.ui`.
2. Regenerate corresponding `ViewController/**/*UI.py` with `pyuic5`.
3. Verify no drift remains between `.ui` and generated `UI.py`.

## D) Workflow Wizard Policy Gate

Must be true before commit:

1. MyServer has both:
   - Project Workflow Wizard
   - Page Workflow Wizard
2. All other modules have:
   - Page Workflow Wizard only
3. Shared enforcement remains active in `Core/workflow_wizard_actions.py`.

## E) Validation Sequence

1. Problems check on touched files.
2. Compile check touched Python files:

```bash
python3 -m py_compile <file1.py> <file2.py> ...
```

1. Run targeted runtime smoke tests for changed launch paths.

## F) Launcher Reliability Gate

1. Button and menu launch paths both work.
2. Missing scripts fail with clear user-facing messages.
3. Parallel module launches remain allowed (system resources permitting).

## G) Commit Hygiene

1. Stage only intended files.
2. Exclude session/runtime noise unless explicitly requested.
3. Use narrow commit message describing behavior change.
4. Re-check staged scope before commit.

## H) Sync and Post-Check

1. Push to required branches.
2. Confirm branch parity/rev alignment.
3. Leave short change note in development docs if behavior changed.

## I) Definition of Done (Fast Pass)

1. Requirement implemented exactly.
2. UI.ui and UI.py in lock-step.
3. Touched files pass problems + compile checks.
4. Key runtime path smoke-tested.
5. Commit excludes unrelated artifacts.
6. Branch sync confirmed.
