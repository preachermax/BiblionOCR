# Architecture Normalization Tasks

Date: 2026-08-07
Source: docs/architecture/ARCHITECTURAL_TRUTH_TABLE_2026-08-07.md
Purpose: convert contradiction findings into executable architecture tasks.

## Execution Rules

1. Work one architecture task at a time.
2. Keep MyLexer out of scope unless explicitly requested.
3. Preserve current runtime behavior while extracting and normalizing ownership.
4. Complete full workspace Problems checks before closing a task.
5. Every task closure must include file-level evidence and acceptance check output.

## Task Ledger

| ID | Priority | Area | Status | Owner | Scope Files | Acceptance Checks |
| --- | --- | --- | --- | --- | --- | --- |
| AN-01 | P0 | Remove duplicate engine and event bus fallback classes from MyServer runtime surface | Closed | Maintainer + Copilot | ViewController/0-MainUI/MyServer.py, Core/engine.py, Core/event_bus.py | No fallback ProjectCreationEngine/EventBus class definitions remain in MyServer; MyServer uses Core imports only; startup smoke passes for MyServer; full Problems count is zero. |
| AN-02 | P0 | Promote RIS responsibilities into dedicated Core/ris.py API | Closed | Maintainer + Copilot | Core/ris.py, Core/engine.py, tests/*ris* | Core/ris.py contains generation and validation API used by Core/engine.py; RIS hash and lock semantics preserved; tests or smoke checks confirm unchanged output fields. |
| AN-03 | P1 | Add replay/read contract to SQLiteEventStore and define authoritative reconstruction path | Closed | Maintainer + Copilot | Core/event_store.py, Core/engine.py, Core/state.py, docs/architecture/* | Store supports append plus read/replay queries; reconstruction contract documented; at least one replay smoke test demonstrates event-to-state reconstruction path. |
| AN-04 | P1 | Canonical event schema enforcement at emit boundaries | Closed | Maintainer + Copilot | Core/engine.py, Core/event_bus.py, Core/event_store.py | Emitted events are validated against one schema; malformed events are rejected or normalized; documentation updated with final contract. |
| AN-05 | P2 | Reconcile UI naming and widget access rules with actual runtime pattern | Closed | Maintainer + Copilot | docs/development/PROJECT_SPEC.md, ViewController/0-MainUI/MyServer.py, ViewController/0-MainUI/MyServerUI.py | Spec and code agree on canonical runtime object model and widget access pattern; no contradictory claims remain in architecture docs. |
| AN-06 | P2 | Establish explicit transitional exceptions register | Closed | Maintainer + Copilot | docs/architecture/ARCHITECTURAL_TRUTH_TABLE_2026-08-07.md, docs/architecture/BiblionOCR_Architectural_Evidence_Review.md | Any intentionally unresolved contradiction is listed as accepted exception with owner and exit criteria. |

## Per-Task Closure Template

Use this record before marking a task Closed.

- Task ID:
- Date:
- Files changed:
- Behavior impact:
- Acceptance checks run:
- Full workspace Problems total:
- In-scope Problems total:
- Residual risk:
- Evidence links:

## Suggested Execution Order

1. AN-01
2. AN-02
3. AN-04
4. AN-03
5. AN-05
6. AN-06

## Why This Order

- AN-01 and AN-02 remove ownership ambiguity first.
- AN-04 standardizes emitted truth structure before replay work expands.
- AN-03 becomes safer after schema normalization.
- AN-05 and AN-06 finalize the spec-to-runtime contract and exception governance.

## Evidence Anchors

- docs/architecture/ARCHITECTURAL_TRUTH_TABLE_2026-08-07.md
- docs/architecture/BiblionOCR_Architectural_Evidence_Review.md
- docs/development/PROJECT_SPEC.md
- Core/engine.py
- Core/event_bus.py
- Core/event_store.py
- Core/ris.py
- ViewController/0-MainUI/MyServer.py

## Closure Records

- Task ID: AN-01
- Date: 2026-08-07
- Files changed:
  Core/event_bus.py; ViewController/0-MainUI/MyServer.py
- Behavior impact:
  MyServer no longer defines local fallback ProjectCreationEngine/EventBus classes; runtime now uses Core-owned EventBus and CoreProjectCreationEngine wiring only; Core EventBus now supports unsubscribe for worker lifecycle symmetry.
- Acceptance checks run:
  `rg -n "class ProjectCreationEngine|class EventBus|class RISDialogController|CoreProjectCreationEngine|from Core.event_bus import EventBus|self.event_bus = EventBus\(" ViewController/0-MainUI/MyServer.py Core/event_bus.py`; `python3 -m py_compile Core/event_bus.py ViewController/0-MainUI/MyServer.py ViewController/0-MainUI/helpers/ProjectCreationWorker.py`; `QT_QPA_PLATFORM=offscreen timeout 12s .venv/bin/python ViewController/0-MainUI/MyServer.py`
- Full workspace Problems total:
  16 (all from docs/development/PROJECT_SPEC.md markdown lint; out of AN-01 scope)
- In-scope Problems total:
  0
- Residual risk:
  docs/development/PROJECT_SPEC.md remains lint-noisy and can mask unrelated new doc warnings during future global scans.
- Evidence links:
  docs/architecture/ARCHITECTURAL_TRUTH_TABLE_2026-08-07.md; Core/event_bus.py; ViewController/0-MainUI/MyServer.py

- Task ID: AN-02
- Date: 2026-08-07
- Files changed:
  Core/ris.py; Core/engine.py
- Behavior impact:
  Core/ris.py now owns RIS capture/finalize logic with required-field validation, lock flag, metadata stamp, and deterministic hash; Core/engine.py delegates to these helpers while preserving payload semantics.
- Acceptance checks run:
  `python3 -m py_compile Core/ris.py Core/engine.py ViewController/0-MainUI/MyServer.py ViewController/0-MainUI/helpers/ProjectCreationWorker.py`; `QT_QPA_PLATFORM=offscreen timeout 12s .venv/bin/python ViewController/0-MainUI/MyServer.py`
- Full workspace Problems total:
  16 (all from docs/development/PROJECT_SPEC.md markdown lint; out of AN-02 scope)
- In-scope Problems total:
  0
- Residual risk:
  No dedicated automated unit test file currently exercises Core/ris.py directly; behavior parity is validated by compile and bounded startup smoke.
- Evidence links:
  Core/ris.py; Core/engine.py; docs/architecture/ARCHITECTURAL_TRUTH_TABLE_2026-08-07.md

- Task ID: AN-04
- Date: 2026-08-07
- Files changed:
  Core/event_bus.py; Core/engine.py; Core/event_store.py; docs/architecture/ARCHITECTURE_NORMALIZATION_TASKS_2026-08-07.md
- Behavior impact:
  Canonical event schema enforcement now occurs at all Core emit boundaries using a shared normalizer. Invalid events are rejected with ValueError; metadata and project_name are normalized when possible; non-canonical top-level keys are stripped before downstream dispatch/persistence.
- Acceptance checks run:
  `python3 -m py_compile Core/event_bus.py Core/event_store.py Core/engine.py ViewController/0-MainUI/MyServer.py ViewController/0-MainUI/helpers/ProjectCreationWorker.py`; `QT_QPA_PLATFORM=offscreen timeout 12s .venv/bin/python ViewController/0-MainUI/MyServer.py`
- Full workspace Problems total:
  16 (all from docs/development/PROJECT_SPEC.md markdown lint; out of AN-04 scope)
- In-scope Problems total:
  0
- Residual risk:
  Existing out-of-scope documentation lint in docs/development/PROJECT_SPEC.md still appears in full-workspace scans and may obscure unrelated documentation regressions.
- Evidence links:
  Core/event_bus.py; Core/event_store.py; Core/engine.py; docs/architecture/ARCHITECTURAL_TRUTH_TABLE_2026-08-07.md

- Task ID: AN-03
- Date: 2026-08-07
- Files changed:
  Core/event_store.py; docs/architecture/ARCHITECTURAL_TRUTH_TABLE_2026-08-07.md; docs/architecture/ARCHITECTURE_NORMALIZATION_TASKS_2026-08-07.md
- Behavior impact:
  SQLiteEventStore now provides explicit read/replay contract via list_events(), replay(), and reconstruct_project_state(); replayed rows are normalized to canonical event schema.
- Acceptance checks run:
  `python3 -m py_compile Core/event_store.py Core/event_bus.py Core/engine.py`; `python3 - <<'PY' ... SQLiteEventStore replay/reconstruct smoke ... PY`; `QT_QPA_PLATFORM=offscreen timeout 12s .venv/bin/python ViewController/0-MainUI/MyServer.py`
- Full workspace Problems total:
  16 (all from docs/development/PROJECT_SPEC.md markdown lint; out of AN-03 scope)
- In-scope Problems total:
  0
- Residual risk:
  Reconstruction helper currently emits a coarse milestone snapshot; richer domain reconstruction is still a future extension.
- Evidence links:
  Core/event_store.py; docs/architecture/ARCHITECTURAL_TRUTH_TABLE_2026-08-07.md; docs/architecture/ARCHITECTURE_NORMALIZATION_TASKS_2026-08-07.md

- Task ID: AN-05
- Date: 2026-08-07
- Files changed:
  docs/development/PROJECT_SPEC.md; docs/architecture/ARCHITECTURAL_TRUTH_TABLE_2026-08-07.md
- Behavior impact:
  PROJECT_SPEC now reflects the runtime UI object model and naming contract (MyServer.py + MyServerUI.py; widget access via self.ui.<widget_name>) and removes prior contradictory statements.
- Acceptance checks run:
  `rg -n "self\.ui\.ui\.|self\.ui\.[A-Za-z_][A-Za-z0-9_]*" ViewController/0-MainUI/MyServer.py`; `get_errors` on docs/development/PROJECT_SPEC.md and architecture docs.
- Full workspace Problems total:
  0
- In-scope Problems total:
  0
- Residual risk:
  Controller-surface breadth remains a separately tracked architectural concern under transitional exceptions.
- Evidence links:
  docs/development/PROJECT_SPEC.md; ViewController/0-MainUI/MyServer.py; ViewController/0-MainUI/MyServerUI.py; docs/architecture/ARCHITECTURAL_TRUTH_TABLE_2026-08-07.md

- Task ID: AN-06
- Date: 2026-08-07
- Files changed:
  docs/architecture/ARCHITECTURAL_TRUTH_TABLE_2026-08-07.md; docs/architecture/BiblionOCR_Architectural_Evidence_Review.md; docs/architecture/ARCHITECTURE_NORMALIZATION_TASKS_2026-08-07.md
- Behavior impact:
  Added an explicit transitional exceptions register with named exceptions, owners, and exit criteria so unresolved architecture deltas are governed rather than implicit.
- Acceptance checks run:
  `get_errors` on docs/architecture/ARCHITECTURAL_TRUTH_TABLE_2026-08-07.md and docs/architecture/BiblionOCR_Architectural_Evidence_Review.md.
- Full workspace Problems total:
  0
- In-scope Problems total:
  0
- Residual risk:
  Exception closure depends on future code extraction and event-authority work in upcoming architecture passes.
- Evidence links:
  docs/architecture/ARCHITECTURAL_TRUTH_TABLE_2026-08-07.md; docs/architecture/BiblionOCR_Architectural_Evidence_Review.md; docs/architecture/ARCHITECTURE_NORMALIZATION_TASKS_2026-08-07.md
