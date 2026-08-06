# BiblionOCR Development Routine Playbook

This document captures the practical development routine we have been using so changes stay consistent, testable, and easy to review.

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

1. Static/problem checks on touched files.
2. `py_compile` on touched Python files.
3. Focused runtime smoke checks for changed launch paths.

Example compile check:

```bash
python3 -m py_compile <edited_file_1.py> <edited_file_2.py>
```

## 5) Launcher and Module Launch Standards

1. Launch actions must be deterministic and discoverable from both button and menu paths.
2. Missing module scripts should fail with clear user-visible messages.
3. Do not add single-instance limits unless explicitly required.
4. Allow parallel module launches where system resources permit.

## 6) Workflow Wizard Governance Standard

Canonical policy:

1. `MyServer`: Project Workflow Wizard + Page Workflow Wizard
2. All other modules: Page Workflow Wizard only

Enforcement pattern:

1. Shared enforcement in `Core/workflow_wizard_actions.py`.
2. Explicit module call-site arguments to prevent policy drift.
3. UI artifacts aligned to the same rule.

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
4. Critical runtime path is smoke-tested.
5. Commit scope excludes unrelated artifacts.
6. Branch sync status is confirmed.

## 10) Quick Failure Triage Checklist

If behavior is wrong after a change:

1. Re-check call-site wiring.
2. Re-check shared policy injector behavior.
3. Re-check `.ui` vs `UI.py` drift.
4. Re-run focused compile and smoke tests.
5. Inspect only deltas in edited files before broad changes.

---

Maintainer note: prefer repeatable routines over ad-hoc fixes. Most regressions in this codebase have come from policy drift between runtime code, UI definitions, and generated UI artifacts.
