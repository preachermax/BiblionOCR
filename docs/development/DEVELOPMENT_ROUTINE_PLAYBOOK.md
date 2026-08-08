# BiblionOCR Development Routine Playbook

This document captures the practical development routine we have been using so changes stay consistent, testable, and easy to review.

## 0) Execution Ownership

1. Checklist execution is agent-owned.
2. The user should not need to manually drive checklist steps.
3. When manual validation is unavoidable (for example visual UI behavior), the agent requests only minimal confirmation and records outcomes in a handoff checkpoint.

## 1) Start-of-Task Preflight

1. Confirm the exact requirement in one sentence.
2. Inspect current local state before editing.
3. Identify affected runtime files, UI files, docs, and tests.
4. Preserve unrelated local files (for example session artifacts) unless explicitly asked to include them.

Recommended checks:

```bash
git status --short
```

## 2) Scope Changes Narrowly

1. Make focused edits per requirement slice.
2. Avoid opportunistic refactors in unrelated areas.
3. Prefer shared policy points for cross-module behavior.

Example from current workflow policy:

- Keep shared wizard policy in `Core/workflow_wizard_actions.py`.
- Keep module call sites explicit (page-only for non-MyServer modules).

## 3) Keep UI Artifacts in Lock-Step

When a module menu or action changes, update both:

1. Qt Designer source (`Developer/QtDesignerUI/*.ui`)
2. Generated Python UI (`ViewController/**/**UI.py`)

After UI edits, regenerate module UI files with `pyuic5`.

Core rule:

- No manual divergence between `.ui` and generated `UI.py` for active modules.

## 4) Validate Immediately After Edits

Run lightweight validation first, then smoke test behavior.

1. Full-workspace Problems scan and total-count capture.
2. Baseline-versus-change triage of Problems.
3. Static/problem checks on touched files.
4. `py_compile` on touched Python files.
5. Focused runtime smoke checks for changed launch paths.

Example compile check:

```bash
python3 -m py_compile <edited_file_1.py> <edited_file_2.py>
```

Required Problems policy:

1. Never claim "clean" from touched-file checks alone.
2. A clean claim requires both: in-scope Problems count is zero, and full-workspace Problems totals are explicitly reported.
3. If full-workspace Problems remain outside scope, publish the unresolved file list in the handoff.

## 5) Launcher and Module Launch Standards

1. Launch actions must be deterministic and discoverable from both button and menu paths.
2. Missing module scripts should fail with clear user-visible messages.
3. Do not add single-instance limits unless explicitly required.
4. Allow parallel module launches where system resources permit.

## 6) Workflow Wizard Governance Standard

Canonical policy:

1. `MyServer`: Project Workflow Wizard + Page Workflow Wizard
2. All other modules: Page Workflow Wizard only
3. Prefer `menuProject` for workflow wizard actions when available.
4. If in `menuProject`, do not duplicate in `menuFile`.
5. Use `Wizard` wording, not `Macro`, for workflow run actions.

Enforcement pattern:

1. Shared enforcement in `Core/workflow_wizard_actions.py`.
2. Explicit module call-site arguments to prevent policy drift.
3. UI artifacts aligned to the same rule.
4. Non-MyServer module UI artifacts do not define `Project Workflow Wizard` actions.

Implementation note:

- Page workflow handlers are module-local by default (module-specific stages and milestones).
- Shared project workflow orchestration remains a MyServer-governed responsibility.

## 6b) Test-First Commit Standard

Before every commit:

1. Run automated checks (`py_compile`, targeted diagnostics, and smoke checks).
2. Run focused manual UI verification for changed behaviors.
3. Only commit after both automated and manual gates pass.

## 7) Commit Routine

1. Stage only the intended change set.
2. Exclude runtime/session noise unless requested.
3. Use clear, scoped commit messages.
4. Sync target branches after successful local validation.

Recommended pre-commit check:

```bash
git status --short
```

## 8) Documentation Routine

When behavior changes, update:

1. Help text shown in UI/HelpSystem.
2. Development notes/checklists used by maintainers.
3. Any policy doc affected by architectural decisions.

## 9) Definition of Done

A change is done when all are true:

1. Requirement is implemented exactly.
2. UI source and generated artifacts are in lock-step.
3. Touched files pass problem checks and `py_compile`.
4. In-scope Problems count is zero and full-workspace totals are reported.
5. Critical runtime path is smoke-tested.
6. Manual UI behavior checks pass for changed interaction surfaces.
7. Commit scope excludes unrelated artifacts.
8. Branch sync status is confirmed.

## 10) Quick Failure Triage Checklist

If behavior is wrong after a change:

1. Re-check call-site wiring.
2. Re-check shared policy injector behavior.
3. Re-check `.ui` vs `UI.py` drift.
4. Re-run focused compile and smoke tests.
5. Inspect only deltas in edited files before broad changes.

## 11) Session Handoff And Reopen Recovery

Before pause/exit, the agent writes a restart-safe handoff in `docs/development/DEV_NOTEBOOK.md` containing:

1. one-sentence scope
2. touched-file list from `git status --short`
3. validation gate status (full-workspace problems, in-scope problems, compile, smoke, manual UI)
4. unresolved Problems list (if any)
5. unresolved blockers/risks
6. next immediate action

After VS Code reopens, the agent must run this recovery sequence before making edits:

1. read `docs/development/DEVELOPMENT_ROUTINE_CHECKLIST_ONE_PAGE.md`
2. read this playbook
3. read latest `Session Handoff` entry in `docs/development/DEV_NOTEBOOK.md`
4. run `git status --short`
5. re-run fast validation context for touched files (problems + compile)
6. publish footing summary and continue

---

Maintainer note: prefer repeatable routines over ad-hoc fixes. Most regressions in this codebase have come from policy drift between runtime code, UI definitions, and generated UI artifacts.
