# Architectural Truth Table

Date: 2026-08-07
Source basis: direct repository evidence only
Companion documents:

- docs/architecture/BiblionOCR_Architectural_Evidence_Review.md
- docs/development/PROJECT_SPEC.md
- docs/architecture/PROJECT_CREATION_ARCHITECTURE.md

## Status Legend

- Implemented: verified directly in source code.
- Documented: described in docs, not yet confirmed in source for full semantics.
- Emerging: partially implemented, direction is clear but not complete.
- Planned: described future state with no direct current implementation evidence.
- Historical: older behavior retained for compatibility or transition.
- Contradictory: sources or code paths disagree in a way that affects architecture claims.

## Truth Table

| Concept | Status | Evidence | Notes |
| --- | --- | --- | --- |
| System | Documented | docs/architecture/BiblionOCR_Architectural_Evidence_Review.md | Vocabulary is defined at architecture level; not a code object. |
| Workspace | Documented | docs/architecture/BiblionOCR_Architectural_Evidence_Review.md | Defined conceptually as dev tree boundary. |
| Project | Implemented | Core/engine.py | Project path creation and structure generation are implemented. |
| Module | Implemented | ViewController/0-MainUI, ViewController/1-PreProcess, ViewController/2-TrainTesseract, ViewController/3-Process, ViewController/4-PostProcess | Module layout exists as executable runtime surfaces. |
| UI Surface | Implemented | ViewController/0-MainUI/MyServer.py, ViewController/0-MainUI/MyServerUI.py | Qt UI is active and wired. |
| Workflow | Emerging | Core/workflow_wizard_actions.py | Wizard orchestration is present and staged, but not fully unified as a single engine contract. |
| Process | Emerging | Core/workflow_wizard_actions.py, ViewController module runtime files | Multiple executable module operations exist; process taxonomy is not fully normalized in code contracts. |
| Stage | Emerging | Core/state.py, Core/workflow_wizard_actions.py | Explicit stage/state values exist for project creation and wizard flows. |
| Artifact | Implemented | Core/engine.py | Project artifacts and manifests are generated and written. |
| Reference Data | Implemented | Core/engine.py, Core/project_database.py | Manifest/template data and project DB defaults are used at runtime. |
| Session | Implemented | ViewController/0-MainUI/helpers/SessionManager.py | Session.json read/write and active project/workflow state accessors are implemented. |
| Event | Implemented | Core/engine.py, Core/event_bus.py | Event emission and subscription are active with persistent-store bridge support. |
| RIS | Implemented | Core/engine.py, Core/ris.py | RIS capture/finalize responsibilities are implemented in Core/ris.py and consumed by engine. |
| ProjectCreationEngine | Implemented | Core/engine.py, ViewController/0-MainUI/MyServer.py | MyServer now wires to Core ProjectCreationEngine instead of local fallback class definitions. |
| EventBus | Implemented | Core/event_bus.py, ViewController/0-MainUI/MyServer.py | MyServer now wires to Core EventBus implementation; schema normalization is enforced in Core path. |
| SQLite persistence | Implemented | Core/event_store.py | Append, filtered reads, replay ordering, and coarse state reconstruction helpers are implemented. |
| MyServer | Emerging | ViewController/0-MainUI/MyServer.py | Project-engine and event-bus fallback classes were removed; wiring-only direction is stronger, but controller surface still contains broader runtime responsibilities. |
| MyLauncher | Implemented | ViewController/0-MainUI/MyLauncher.py | Launcher surface exists and participates in workflow entry patterns. |
| Project administration ownership | Implemented | ViewController/0-MainUI/MyServer.py, docs/architecture/BiblionOCR_Architectural_Evidence_Review.md | New Project and Project Settings ownership is centralized in MyServer. |
| Workflow Wizard | Implemented | Core/workflow_wizard_actions.py | Shared install/open action patterns and module page workflow entry are implemented. |

## Verified Architectural Deltas Against PROJECT_SPEC v2.0

1. MyServer wiring-only invariant is not fully satisfied.

- Fallback engine/event-bus classes were removed, but MyServer still carries non-trivial runtime surface area beyond strict dependency wiring.

1. Event-sourced truth as authoritative state model is not yet proven globally.

- Events are emitted and persisted, but current code also writes direct artifacts/registries and session state independently.

1. SQLite event-store replay capability is now implemented in the current store class.

- Core/event_store.py now provides list_events(), replay(), and reconstruct_project_state().

1. Dedicated RIS module contract is now implemented.

- Core/ris.py now provides capture_provenance() and finalize_ris(), and Core/engine.py delegates to them.

1. Canonical UI package naming and widget access rule are now aligned with runtime.

- PROJECT_SPEC now reflects MyServer.py and MyServerUI.py, and widget access via self.ui.<widget_name>.

## Priority Normalization Steps

1. Remove or quarantine duplicate ProjectCreationEngine/EventBus definitions from MyServer.
2. Move RIS generation/validation responsibilities into Core/ris.py with explicit tested API.
3. Add replay/read APIs to Core/event_store.py and define authoritative reconstruction contract.
4. Publish one canonical event schema and enforce it at emit boundaries.
5. Continue reducing MyServer controller surface toward stricter wiring-only contract.
6. Track intentionally unresolved deltas in an explicit transitional exceptions register.

## Transitional Exceptions Register

| Exception ID | Exception | Status | Owner | Exit Criteria | Target |
| --- | --- | --- | --- | --- | --- |
| EX-01 | MyServer is broader than strict dependency wiring and still hosts mixed orchestration/runtime responsibilities. | Accepted transitional exception | Maintainer + Copilot | Extract remaining non-controller responsibilities into dedicated Core/helpers services and shrink MyServer to orchestration boundary. | 2026-09 architecture pass |
| EX-02 | Event-sourced truth is active but not yet the sole authoritative state model across all runtime persistence paths. | Accepted transitional exception | Maintainer + Copilot | Define and implement authoritative reconstruction policy where durable state derives from event replay/projections, with explicit exceptions documented per subsystem. | 2026-09 architecture pass |

## Recommendation

Treat this truth table as the baseline reconciliation artifact.
Update architecture docs only after each contradiction is either:

- resolved in code, or
- explicitly accepted as an intentional transitional exception.

Companion execution ledger:

- docs/architecture/ARCHITECTURE_NORMALIZATION_TASKS_2026-08-07.md
