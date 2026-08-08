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
4. Preserve line endings/whitespace style to avoid accidental large-file rewrites.
5. If whitespace normalization is required, isolate it to a dedicated commit and state why.
6. If the user excludes a module/file from scope, do not include it in default/handoff priority lists.

## C) UI Lock-Step Rule

If UI behavior/menu/actions changed:

1. Update Qt Designer source in `Developer/QtDesignerUI/*.ui`.
2. Regenerate corresponding `ViewController/**/*UI.py` with `pyuic5`.
3. Verify no drift remains between `.ui` and generated `UI.py`.
4. Keep generated UI modules free of local path bootstraps or ad hoc import fixes.
5. If generated UI code needs a shared compatibility shim, put it in a shared repository-level module such as `UI_Icons.py` instead of editing the generated file.
6. If a generated UI export name changes, update the `.ui` class name and the runtime caller together; keep temporary compatibility aliases only until regeneration lands.
7. Treat `Developer/QtDesignerUI/*.ui` as the only editable source of truth for UI text, tooltips, and action labels.
8. Do not hand-edit generated `ViewController/**/*UI.py` text/tooltips; if a generated file was edited, mirror the same change in `.ui` and immediately regenerate.
9. Regenerate only the touched UI pairs first (targeted reflow), then expand to full UI regeneration only if needed.
10. Use the generated-file header (`# Form implementation generated from reading ui file ...`) to map each touched `UI.py` file back to the exact source `.ui` file before reflow.
11. Run drift probes after regeneration for stale phrases (for example old Open/Save labels or pre-MyExplorer tooltip forms), then fix in `.ui` and regenerate again.
12. For paired controls (for example image vs text buttons), verify semantic mapping after bulk replacements so tooltips are not swapped.

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

## E) Page Workflow and Session State Gate

Must be true before commit:

1. Project state carries these fields when present:
   - `CurrentProjectPage`
   - `CurrentProjectMilestone`
   - `CurrentPageMilestone`
2. `SessionManager` persists the active project page and the current project/page milestone fields.
3. Workflow outputs are moved from `Workflow` to `Complete` when a page milestone is completed.
4. A completed page milestone immediately updates the project milestone progress.
5. All modules open on the current project page by default.
6. Handoffs keep the calling module visible while the receiving module opens on the current project page.
7. Reference image pages and reference text pages do not become the current project page.
8. Image/text pairs use the same page number in their filenames when both are present.

## F) Wizard UX Wording Gate

1. Use `Wizard` wording in workflow UI controls and help text.
2. Do not use `Macro` wording for workflow run actions.

## G) Validation Sequence

1. Run a full-workspace Problems scan first and record the total count.
1. Classify Problems into two buckets: pre-existing baseline (outside current scope), and introduced/regressed by the current change set.
1. Repair all introduced/regressed Problems before any clean-status claim.
1. Re-run full-workspace Problems scan and report both counts: total remaining Problems, and remaining in-scope Problems (must be zero).
1. Problems check on touched files.
1. Compile check touched Python files:

```bash
python3 -m py_compile <file1.py> <file2.py> ...
```

1. Run targeted runtime smoke tests for changed launch paths.
1. Run focused manual UI verification for changed menus/buttons/wizard actions.
1. Run a smoketest of every launcher in `launchers/` on the active platform.
1. Confirm the canonical launch paths open cleanly without a traceback for `MyLauncher`, `MyServer`, `MyBoxer`, `MyGlypher`, `MyPixler`, `MyReader`, `MyGrounder`, `MyTrainer`, `MyLexer`, `MyResolver`, `MyVersifier`, and `MyWriter`.
1. Minimum pass condition: window starts, no immediate traceback, no missing UI file error, no missing shared helper import, and no crash on empty/default session state.

## H) Launcher Reliability Gate

1. Button and menu launch paths both work.
2. Missing scripts fail with clear user-facing messages.
3. Parallel module launches remain allowed (system resources permitting).
4. Launcher smoketest coverage includes `run-mylauncher`, `run-myserver`, and every module launcher in `launchers/` on the active platform.
5. Each launcher must start cleanly to a usable window or exit with a clear, non-crashing message.

## I) Commit Hygiene

1. Stage only intended files.
2. Exclude session/runtime noise unless explicitly requested.
3. Use narrow commit message describing behavior change.
4. Re-check staged scope before commit.
5. Do not commit until automated and manual test gates pass.
6. Compare line-change volume to intended behavior change; if disproportionate, investigate before committing.

## J) Sync and Post-Check

1. Push to required branches.
2. Confirm branch parity/rev alignment.
3. Leave short change note in development docs if behavior changed.

## K) Session Handoff Checkpoint (Required Before Pause/Exit)

Record a restart-safe checkpoint before closing VS Code or pausing work.

1. Save current scope summary (one sentence).
2. Save exact touched-file list from `git status --short`.
3. Save validation status by gate:
   - problems/lint
   - compile
   - smoke tests
   - manual UI checks
4. For Problems specifically, record:
   - full-workspace total count
   - in-scope count
   - exact unresolved file list (if any)
5. Save unresolved risks/blockers.
6. Save next immediate action.

Checkpoint location:

1. Append/update in `docs/development/DEV_NOTEBOOK.md` under a dated `Session Handoff` heading.

## L) Reopen Recovery Protocol (Run First After VS Code Reopens)

Before any edits, the agent must regain footing in this exact order:

1. Read this checklist.
2. Read `docs/development/DEVELOPMENT_ROUTINE_PLAYBOOK.md`.
3. Read latest `Session Handoff` entry in `docs/development/DEV_NOTEBOOK.md`.
4. Run `git status --short`.
5. Re-run fast validation context for touched files:
   - problems check
   - compile check for touched Python files
6. Publish a short footing summary (what is done, what remains, and next action), then continue work.

## M) Definition of Done (Fast Pass)

1. Requirement implemented exactly.
2. UI.ui and UI.py in lock-step.
3. Full-workspace Problems scan completed and reported.
4. In-scope Problems count is zero.
5. Touched files pass problems + compile checks.
6. Key runtime path smoke-tested.
7. Manual UI checks pass for changed interactions.
8. Commit excludes unrelated artifacts.
9. Branch sync confirmed.
10. Launcher smoketest passes for all canonical launchers.
