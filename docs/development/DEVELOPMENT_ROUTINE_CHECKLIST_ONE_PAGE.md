# BiblionOCR Development Routine Checklist (One Page)

Use this as a fast, repeatable execution checklist for daily development work.

Execution ownership policy:

1. The coding agent executes this checklist end-to-end.
2. The user is not responsible for performing checklist steps manually.
3. If manual verification is required (for example visual UI checks), the agent requests only the minimum confirmation needed and records the result in the handoff checkpoint.

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
3. Place the wizard action in `menuProject` when available.
4. If placed in `menuProject`, do not duplicate it in `menuFile`.
5. Non-MyServer module UI artifacts contain no `Project Workflow Wizard` action items.
6. Shared enforcement remains active in `Core/workflow_wizard_actions.py`.

## E) Wizard UX Wording Gate

1. Use `Wizard` wording in workflow UI controls and help text.
2. Do not use `Macro` wording for workflow run actions.

## F) Validation Sequence

1. Problems check on touched files.
2. Compile check touched Python files:

```bash
python3 -m py_compile <file1.py> <file2.py> ...
```

1. Run targeted runtime smoke tests for changed launch paths.
2. Run focused manual UI verification for changed menus/buttons/wizard actions.

## G) Launcher Reliability Gate

1. Button and menu launch paths both work.
2. Missing scripts fail with clear user-facing messages.
3. Parallel module launches remain allowed (system resources permitting).

## H) Commit Hygiene

1. Stage only intended files.
2. Exclude session/runtime noise unless explicitly requested.
3. Use narrow commit message describing behavior change.
4. Re-check staged scope before commit.
5. Do not commit until automated and manual test gates pass.

## I) Sync and Post-Check

1. Push to required branches.
2. Confirm branch parity/rev alignment.
3. Leave short change note in development docs if behavior changed.

## J) Session Handoff Checkpoint (Required Before Pause/Exit)

Record a restart-safe checkpoint before closing VS Code or pausing work.

1. Save current scope summary (one sentence).
2. Save exact touched-file list from `git status --short`.
3. Save validation status by gate:
   - problems/lint
   - compile
   - smoke tests
   - manual UI checks
4. Save unresolved risks/blockers.
5. Save next immediate action.

Checkpoint location:

1. Append/update in `docs/development/DEV_NOTEBOOK.md` under a dated `Session Handoff` heading.

## K) Reopen Recovery Protocol (Run First After VS Code Reopens)

Before any edits, the agent must regain footing in this exact order:

1. Read this checklist.
2. Read `docs/development/DEVELOPMENT_ROUTINE_PLAYBOOK.md`.
3. Read latest `Session Handoff` entry in `docs/development/DEV_NOTEBOOK.md`.
4. Run `git status --short`.
5. Re-run fast validation context for touched files:
   - problems check
   - compile check for touched Python files
6. Publish a short footing summary (what is done, what remains, and next action), then continue work.

## L) Definition of Done (Fast Pass)

1. Requirement implemented exactly.
2. UI.ui and UI.py in lock-step.
3. Touched files pass problems + compile checks.
4. Key runtime path smoke-tested.
5. Manual UI checks pass for changed interactions.
6. Commit excludes unrelated artifacts.
7. Branch sync confirmed.
