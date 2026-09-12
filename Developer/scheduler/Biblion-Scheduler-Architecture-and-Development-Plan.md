# Biblion Scheduler

## Architecture and Development Plan

| Document control | Value |
| --- | --- |
| Status | Active draft — implementation alignment reviewed |
| Version | `0.2.0` |
| Date | `2026-09-11` |
| Author(s) | `TBD` |
| Reviewers | `TBD` |
| Decision owner | `TBD` |

---

## 1. Purpose

Biblion Scheduler is a proposed project-planning and project-control subsystem for BiblionOCR. It will model work, logical relationships, calendars, resources, baselines, and actual progress; derive a defensible schedule from that model; and present the result through a Primavera-inspired Gantt interface and complementary schedule views.

The initial implementation will plan the continued development and release work of BiblionOCR itself. This is intentional: BiblionOCR supplies a realistic portfolio of milestones, workflows, hardware constraints, and productization work, rather than a synthetic demonstration project. The design must nevertheless preserve a clean boundary so that Biblion Scheduler can later support other Biblion products—or become a separately deployable application—without inheriting BiblionOCR runtime concerns.

The primary architectural decision is simple:

> The scheduling model and scheduling engine are the product. The Gantt chart is a presentation of calculated schedule state, not the source of scheduling truth.

---

## 2. Goals and non-goals

### 2.1 Goals

- Provide an explicit work-breakdown structure (WBS) for projects, phases, work packages, workflows, tasks, activities, and milestones.
- Represent all four common predecessor/successor relationships—Finish-to-Start (FS), Start-to-Start (SS), Finish-to-Finish (FF), and Start-to-Finish (SF)—with positive lag and negative lag (lead).
- Calculate a reproducible, calendar-aware schedule, including early/late dates, float, critical path, constraint violations, and milestone dates.
- Model resources beyond people: human contributors, AI agents, hardware, software, facilities, and optionally financial resources.
- Preserve approved schedule baselines independently from the current plan and recorded actuals.
- Support BiblionOCR workflow and milestone references without tightly coupling to BiblionOCR execution behavior.
- Deliver a usable, desktop-oriented Gantt view with WBS hierarchy, dependency lines, milestone symbols, critical-path emphasis, baseline overlay, filtering, and practical time scaling.
- Establish auditable persistence, schema migration, validation, and test practices before advanced UI work.

### 2.2 Non-goals for the first releases

- Reproducing the full feature set of Primavera P6, Microsoft Project, or enterprise portfolio-management systems.
- Making the Gantt editor the sole or authoritative scheduling mechanism.
- Replacing BiblionOCR's runtime workflow engine, project database, validation gates, or operational state model.
- Building a distributed multi-user collaboration service, cloud synchronization, timesheets, payroll, procurement, or accounting in the MVP.
- Delivering sophisticated automatic resource leveling before deterministic dependency- and calendar-based scheduling is trustworthy.
- Treating every BiblionOCR execution relationship as a scheduling dependency.

---

## 3. Relationship to BiblionOCR

BiblionOCR remains the execution and application layer. Biblion Scheduler becomes the planning and control layer.

```text
BiblionOCR project / workflow model
        │
        │  explicit adapter and references
        ▼
Biblion Scheduler domain model and engine
        ├── Schedule, WBS, dependencies, calendars
        ├── Resources, baselines, actuals, scenarios
        └── Gantt, network, resource, and report views
```

The scheduler may import or reference BiblionOCR projects, milestones, workflow definitions, module order, and selected status events. It must not own BiblionOCR execution, invoke modules, decide runtime workflow behavior, or directly rewrite BiblionOCR project data. Synchronization is a defined adapter boundary, not an implicit shared-table arrangement.

This distinction is essential because an **execution dependency** (“Reader cannot run until Trainer completes”) may be different from a **planning relationship** (“prepare Reader documentation in parallel with Trainer work”). A user must be able to create either relationship deliberately and understand its effects.

---

## 4. Conceptual model

```text
Project
├── WBS
│   ├── Phase / work package
│   │   ├── Milestone
│   │   ├── Workflow
│   │   │   └── Task
│   │   │       └── Activity
│   │   └── Task
├── Calendars
├── Resources and assignments
├── Dependencies and constraints
├── Baselines
└── Actuals / schedule runs
```

### 4.1 Project

A project is the top-level planning container. It owns the WBS, default calendar, schedule settings, resource pool references, baselines, and schedule-run history. A project has a unique immutable identifier, a name, lifecycle state, time zone, and a configured data date—the date through which actual progress is considered current.

### 4.2 Work Breakdown Structure (WBS)

The WBS is a persistent hierarchy for organizing project scope, not merely visual indentation. Each node has an identifier, parent, code, name, type, display order, and optional owner/description. Summary nodes aggregate descendants; they should not normally carry independently scheduled duration or resource effort.

An initial BiblionOCR WBS may include Architecture, Core Infrastructure, OCR Workflow, Module Standardization, Scanner Productization, Documentation, and Release. Scanner Productization can further contain Licensing, Repository Separation, Qt/PySide6 Migration, Scanner Acquisition, platform backends, AirScan/eSCL, Testing, Packaging, and Release Candidate.

### 4.3 Milestone

A milestone is a zero-duration schedule object and a semantically meaningful event, for example “Compute Engine Architecture Frozen” or “MyScanner Release Candidate.” It may have predecessors, successors, constraints, baseline dates, and actual completion. It answers a practical question: what is preventing this decision or release event?

### 4.4 Workflow

A workflow is a named logical sequence or graph of work, optionally linked to a BiblionOCR workflow definition. It can be represented as a WBS node, a summary object, or a schedulable task depending on the needed level of planning. Workflow links must explicitly declare whether they are informational, imported execution logic, or schedule-driving dependencies.

### 4.5 Task and activity

A task is a schedulable unit of work with an estimated duration, calendar, status, priority, assignments, constraints, dependencies, and calculated dates. An activity is the lowest useful unit of planned execution beneath a task; the model permits task-only plans in the MVP so that decomposition is driven by usefulness, not ceremony.

At minimum, an activity/task record supports:

```text
id, project_id, wbs_id, name, description, type, status, priority
duration, duration_unit, calendar_id
planned/calculated dates, actual dates, percent complete
constraint type/date, notes, external references, revision metadata
```

Calculated dates are derived state. Persisting them for display, audit, or performance is acceptable, but they must never become the authoritative substitute for durations, dependencies, calendars, constraints, and actuals.

### 4.6 Resource and assignment

A resource is a constrained or accountable capability used by work. An assignment joins a resource to an activity/task with units, allocation, role, availability window, and optional cost metadata.

Initial resource classes:

| Class | Examples | Planning use |
| --- | --- | --- |
| Human | project owner, developer, reviewer | availability, allocation, accountability |
| AI agent | Codex, ChatGPT, Copilot | capacity assumptions, role, traceability |
| Hardware | Jetson Nano, scanner, build PC | exclusive or limited-capacity use |
| Software | PySide6, CUDA, Tesseract, test environment | license/environment availability |
| Facility | lab, workspace, test bench | reservation/capacity |
| Financial | budget allocation | future cost-aware planning |

Resources may be reusable, consumable, exclusive, or capacity-limited. In the first resource-aware phase, the engine reports overloads and conflicts rather than silently moving work. Automatic leveling is a later, opt-in policy because it changes dates and must remain explainable.

### 4.7 Calendar

A calendar defines working days, work intervals, holidays, and dated exceptions. Projects have a default calendar; resources and activities may inherit or override it. Calendar evaluation must use the project time zone and consistent duration semantics (for example, working hours rather than elapsed clock hours). The policy for intersecting task and resource calendars is an open decision, but the engine must make the selected rule explicit.

### 4.8 Dependency

A dependency is a first-class record between a predecessor and successor, with relationship type, lag value/unit, provenance, and optional explanation. A dependency cannot duplicate an equivalent active edge and cannot create a directed cycle in the schedule graph.

### 4.9 Constraint

Constraints restrict, but do not replace, logical scheduling. Initial types should include As Soon As Possible, Start No Earlier Than, Start No Later Than, Finish No Earlier Than, Finish No Later Than, Must Start On, and Must Finish On. The UI must visibly distinguish hard constraints from calculated dates and warn when a constraint creates infeasible or negative-float conditions.

### 4.10 Baseline and actual

A baseline is an immutable approved snapshot of selected schedule inputs and results: task duration, start/finish, milestone date, assignments, dependencies/constraints as appropriate, and schedule metadata. Actuals record facts—actual start, actual finish, remaining duration, percent complete, and status—as of a data date. Current forecast is calculated from current logic plus actuals; it is not a baseline overwrite.

---

## 5. Scheduling-engine architecture

The scheduling engine is a pure domain module with no Qt/widget dependency and no direct database/UI ownership.

```text
ScheduleEngine
├── Graph validator and topological ordering
├── Calendar calculator
├── Dependency calculator
├── Constraint evaluator
├── Forward/backward pass and critical-path calculator
├── Resource conflict analyzer
├── Baseline comparator
└── Diagnostics / explanation builder
```

### 5.1 Inputs and outputs

Inputs are a normalized project snapshot: activities/milestones, WBS relationships, calendars, dependencies, constraints, resource assignments/capacities, actuals, project settings, and a selected scenario/baseline context. The engine returns calculated early and late dates, float, critical flags, forecast finish, resource conflicts, constraint violations, unschedulable items, and human-readable diagnostics.

Each execution creates a `schedule_run` with input revision, engine/algorithm version, timestamp, data date, calculation options, output hash, and result diagnostics. Reproducibility is a requirement: the same snapshot and engine version must produce the same result.

### 5.2 Dependency logic

Let predecessor start/finish be `S_p` and `F_p`; successor start/finish be `S_s` and `F_s`; and calendar-aware lag be `L`. The engine applies these relationships:

| Type | Rule | Meaning |
| --- | --- | --- |
| FS | `S_s ≥ F_p + L` | successor starts after predecessor finishes |
| SS | `S_s ≥ S_p + L` | successor starts after predecessor starts |
| FF | `F_s ≥ F_p + L` | successor finishes after predecessor finishes |
| SF | `F_s ≥ S_p + L` | successor finishes after predecessor starts |

Positive lag delays the successor condition. Negative lag is lead and permits overlap. Lag is evaluated using the relationship/calendar policy, not naïve calendar-day arithmetic. Zero-duration milestones are handled as valid nodes. The engine must support combinations of relationships, choose the controlling calculated bound, and surface the controlling predecessor in diagnostics.

### 5.3 Forward pass, backward pass, and critical path

The engine performs a validated forward pass to determine early dates, then a backward pass from the project finish (or configured target) to determine late dates. It calculates early start/finish, late start/finish, total float, free float where meaningful, and critical status. Activities with zero or configured near-zero total float form the critical path/network; multiple critical paths are valid and must be representable.

The initial critical-path calculation is dependency-and-calendar based. Resource leveling effects must not be conflated with critical-path logic until resource scheduling semantics are explicitly implemented and tested.

### 5.4 Actual-progress behavior

Actual start/finish events constrain the forecast. Completed work remains fixed; in-progress work uses actual start plus remaining duration/progress policy; not-started work is scheduled from the data date and applicable logic. The exact policy for percent-complete types (duration, physical, units) is deferred, but one consistent MVP policy must be adopted and documented.

---

## 6. Persistence and data architecture

Scheduling data must not be inserted ad hoc into BiblionOCR `project_metadata` records. The preferred initial design is a dedicated scheduling schema/database associated with a BiblionOCR project, or an independently owned scheduler database with stable external project references.

```text
BiblionOCR project metadata  ── stable identity/reference ──► Scheduler store
                                                             ├── projects / WBS
                                                             ├── activities / milestones
                                                             ├── dependencies / constraints
                                                             ├── calendars / resources / assignments
                                                             ├── actuals / baselines
                                                             └── schedule runs / audit records
```

Recommended initial persistence technology: SQLite with a migration-managed relational schema and repository interfaces. It is appropriate for the desktop, single-user-first scope while preserving transactionality, portability, inspectability, and a path to another relational backend if collaboration later demands it.

Core tables include `projects`, `wbs_nodes`, `activities`, `milestones`, `dependencies`, `constraints`, `calendars`, `calendar_work_periods`, `calendar_exceptions`, `resources`, `resource_assignments`, `actuals`, `baselines`, `baseline_activity_snapshots`, `schedule_runs`, and `audit_events`. Prefer explicit IDs and foreign keys; preserve `created_at`, `updated_at`, actor/source, and revision values. Use immutable baseline and schedule-run records rather than mutable history fields.

Repository interfaces translate persistence records into domain objects. The engine receives domain snapshots, not database cursors or ORM/UI models. Schema migrations and import/export must be versioned.

---

## 7. BiblionOCR integration boundaries

### Allowed integration

- Import BiblionOCR project identity and descriptive metadata through a versioned adapter.
- Reference BiblionOCR milestones, modules, and workflows by stable external identifiers.
- Offer optional workflow-to-schedule mapping with user approval.
- Receive selected read-only execution/status events as actual-progress candidates.
- Navigate from a scheduler item to its BiblionOCR counterpart when an integration is available.

### Prohibited coupling

- No scheduler tables embedded opportunistically in unrelated BiblionOCR metadata fields.
- No Qt view calling BiblionOCR runtime execution code to calculate dates.
- No assumption that BiblionOCR workflow edges are automatically schedule-driving dependencies.
- No direct, unreviewed write-back to BiblionOCR project state.
- No BiblionOCR execution behavior depending on the presence of the Scheduler UI.

Synchronization should be explicit, idempotent, logged, and conflict-aware. Imported items retain their external identity and source revision. A mapping layer determines whether a source update creates, updates, ignores, or flags a scheduling item.

### 7.1 ProjectWorkflow.ods governance transition

`Model/Project/Data/csv/ProjectWorkflow.ods` currently describes BiblionOCR project and page workflows, milestones, module handshakes, inventories, and supporting lookup data. It is broader than a development schedule and remains authoritative for those source definitions until each relevant record has been imported, reconciled, and approved in Biblion Scheduler.

```text
ProjectWorkflow.ods
        │
        ▼
Immutable source snapshot (path, scope, revision, checksum, schema, timestamp)
        │
        ▼
Staged source records (new / mapped / changed / ignored / conflict)
        │
        ▼ explicit human approval
Stable Scheduler workflow identities
        │
        ├── many-to-many WBS/activity/milestone mappings
        └── separately reviewed schedule dependencies and estimates
```

Importing a workbook never creates schedule-driving dependencies or durations from row order. A changed source revision cannot alter an approved Scheduler workflow until its staged record is reviewed. Every import, disposition, approval, and task mapping is append-only audit evidence.

Authority transfers incrementally. Before approval, the ODS record is the source definition and Scheduler stores immutable evidence. After approval, the stable Scheduler workflow identity and its approved revision govern the BiblionOCR development plan; workbook identities remain as provenance and compatibility references. BiblionOCR runtime execution and `ProjectWorkflowTracker` actual-progress events remain outside Scheduler ownership and may only propose, not silently apply, schedule actuals.

Workflow-to-task mappings are many-to-many and declare their role. A mapping explains what scheduled work implements or references; it is not itself a dependency. This permits one workflow to require several development activities and one development activity to support several operational workflows.

---

## 8. User interface direction

The UI is Primavera-inspired in information density and project-control affordances, not a clone of Primavera. Its purpose is to inspect and manage the model the engine calculates.

The primary Gantt workspace contains a WBS/task grid and synchronized timeline. Early functions include collapse/expand hierarchy, calendar-aware time scales (year through day, later hour), task bars, milestone diamonds, dependency arrows, critical-path highlighting, baseline overlays, progress shading, filters, sorting, column configuration, constraint/conflict indicators, and a details inspector.

Direct manipulation—dragging dates, resizing bars, or drawing dependencies—may be supported once it creates validated domain commands and triggers recalculation. It must never edit cached visual coordinates as schedule truth. Before a schedule-changing action is committed, show affected dates, conflicts, and violations where practical.

Secondary views, phased after the primary Gantt, include a dependency/network view, resource utilization and overload view, milestone dashboard, baseline variance report, and schedule diagnostics panel that explains why a date is where it is.

---

## 9. Validation and testing strategy

Validation is an architectural capability, not a release-only activity.

### 9.1 Domain and engine tests

- Unit-test calendar arithmetic across weekends, holidays, exceptions, time zones, and different duration units.
- Table-drive FS, SS, FF, and SF cases with positive/negative lag and zero-duration milestones.
- Test combinations of relationships, constraints, actuals, multiple calendars, and externally imposed project finish targets.
- Test forward/backward pass values, float, single/multiple critical paths, and negative float.
- Reject cycles, dangling references, invalid calendar periods, invalid durations, duplicate dependencies, and impossible hard constraints.
- Use property-based tests where valuable: acyclic graph generation, schedule invariants, and determinism under input ordering.

### 9.2 Persistence and integration tests

- Verify migrations from every supported schema version and enforce foreign-key integrity.
- Round-trip domain snapshots without semantic loss.
- Verify immutable baselines and reproducible schedule runs.
- Test BiblionOCR adapter imports against fixture projects/workflows, including missing and changed external references.
- Ensure synchronization is idempotent and does not mutate BiblionOCR data without explicit authorization.

### 9.3 UI and acceptance tests

- Validate Gantt rendering of hierarchy, dates, bars, diamonds, links, baseline overlays, and critical indicators at all supported zoom levels.
- Test command behavior for edits, undo/redo if supplied, validation prompts, and recalculation.
- Keep a curated BiblionOCR development schedule as an end-to-end acceptance fixture.
- Add accessibility checks for non-color-only indicators, keyboard navigation, labels, and readable dense layouts.
- Perform manual exploratory checks on representative desktop sizes and saved projects.

### 9.4 Reference-oracle strategy

For a small suite of canonical network examples, record independently verified expected results. Where licensing and access permit, compare selected calculations against a recognized scheduling tool or carefully reviewed hand calculations. The goal is not tool emulation; it is confidence that semantics are intentional and stable.

---

## 10. Phased roadmap

### Phase 0 — Architecture foundation

Approve this document; establish domain vocabulary, ownership boundaries, constraint semantics, calendar conventions, persistence decision, and acceptance examples. Produce a small BiblionOCR seed WBS and trace each entity to a stable identifier.

**Exit criterion:** approved decisions and executable acceptance cases for a minimal dependency network.

### Phase 1 — Deterministic scheduling kernel (MVP-1)

Implement domain objects, graph validation, working-day calendar, FS relationships, durations, milestones, forward scheduling, diagnostics, and unit tests. Begin with a three-task chain before adding UI or resource behavior.

**Exit criterion:** a headless engine calculates a reproducible schedule for a persisted sample project and rejects invalid logic.

### Phase 2 — Full dependency and critical-path model

Add SS/FF/SF, lag/lead, constraints, backward pass, float, critical paths, actual-start/finish handling, and schedule-run audit records.

**Exit criterion:** canonical networks calculate verified early/late dates, floats, and critical statuses.

### Phase 3 — Persistence, baseline, and BiblionOCR adapter

Add migration-managed storage, repositories, baseline snapshots/comparison, actuals, import/reference adapter, and a real BiblionOCR development schedule.

**Exit criterion:** baseline variance and re-calculation work across save/reload; BiblionOCR integration is read-only, traceable, and idempotent.

### Phase 4 — Gantt planning workspace

Build the Primavera-inspired WBS/Gantt workspace and details editor on top of engine results. Support hierarchy, critical path, dependency links, milestones, baseline overlay, filters, and schedule diagnostics.

**Exit criterion:** users can create/edit a practical BiblionOCR plan, understand its driving logic, and safely recalculate it.

### Phase 5 — Resource-awareness and reports

Add resource pools, assignment capacity, individual calendars, utilization, and conflict detection. Implement report/export foundations and scenario/what-if support.

**Exit criterion:** conflicts are accurately reported without unexplained automatic date movement.

### Phase 6 — Controlled leveling and product hardening

Evaluate opt-in resource leveling, portfolio capabilities, import/export, packaging, performance, recovery, documentation, and broader standalone-product requirements.

**Exit criterion:** leveling behavior is explainable, testable, reversible, and appropriate for a release candidate.

### 10.1 Implementation alignment as of 2026-09-11

| Phase | Status | Remaining gate |
| --- | --- | --- |
| Phase 0 | In progress | Approve open decisions and canonical governance examples |
| Phase 1 | Complete for initial scope | Continue canonical calendar and milestone cases |
| Phase 2 | Substantially complete | Make actuals/data date constrain forecasts; expand diagnostics |
| Phase 3 | In progress | Add conflict resolution and bulk review, full baseline inputs/variance, and actual-event adapter |
| Phase 4 | Partially implemented ahead of Phase 3 | Add filters, diagnostics, constraint editing, and accessibility checks after governance work |
| Phase 5 | Not started | Resource domain and conflict analysis |
| Phase 6 | Not started | Controlled leveling and release hardening |

The current implementation includes immutable checksummed workflow source snapshots, direct read-only ODS workflow-sheet ingestion, reconciliation statuses, stable approved workflow identities, many-to-many task mappings, append-only workflow governance events, and an initial reconciliation workspace for import, review, approval, ignore, and activity mapping. These capabilities establish the persistence boundary; they do not by themselves declare the imported workbook fully reconciled or make Scheduler authoritative for all BiblionOCR workflow data.

---

## 11. Architectural principles

1. **Model first; presentation second.** UI never owns scheduling truth.
2. **Calculated state is derivable.** Dates, float, and critical status are reproducible outputs, not unexplained edits.
3. **Explicit semantics beat implicit inference.** Dependency, constraint, calendar, and source/provenance choices are stored and visible.
4. **Pure engine boundary.** Scheduling logic is independently testable and has no Qt, database, or BiblionOCR runtime dependency.
5. **Planning and execution are distinct.** Integrate intentionally; do not collapse the two models.
6. **Auditability is a feature.** Preserve baselines, actuals, schedule runs, revisions, and diagnostics.
7. **Resource realism without premature automation.** Report conflicts before automatically resolving them.
8. **Incremental vertical slices.** A correct simple network is more valuable than an attractive but unreliable Gantt chart.
9. **Human architectural authority.** AI-assisted resources may be planned and recorded, but approvals and high-impact scheduling decisions remain explicit.
10. **Portable, evolvable boundaries.** Use interfaces and stable identities so Biblion Scheduler can mature beyond its first host application.

---

## 12. Key risks and mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| UI-first implementation | schedule logic becomes hidden in widgets | make engine tests and headless MVP release gates |
| Ambiguous dependency semantics | incorrect forecasts and loss of trust | document FS/SS/FF/SF/lag rules; use canonical fixtures |
| Cycles and infeasible constraints | uncalculable schedule | validate graph and constraints before each run; provide diagnostics |
| Calendar complexity | subtle date errors | adopt limited, tested calendar scope first; grow deliberately |
| Premature resource leveling | surprising automatic date movement | start with conflict detection and opt-in policy design |
| Tight BiblionOCR coupling | blocks reuse and risks runtime regressions | adapter/repository boundary; no shared ad hoc tables |
| Baseline mutation | destroys comparison value | immutable snapshots and audit records |
| Scope expansion toward enterprise PPM | delays usable product | phase gates and explicit non-goals |
| AI-agent capacity is poorly defined | false precision | treat AI resources as planning assumptions with provenance, not guaranteed throughput |
| Sparse real-world schedule data | weak validation | use the BiblionOCR plan as a living acceptance fixture and document assumptions |

---

## 13. Open decisions

The following decisions should be resolved during Phase 0 and recorded as linked architecture decisions:

1. Will Biblion Scheduler initially be an in-process BiblionOCR subsystem, a separately packaged library/application, or both?
2. What is the authoritative project identity and location for the scheduler store: per-project SQLite, shared scheduler database, or another model?
3. Which calendar governs lag and activity duration when a task, predecessor, and assigned resource have different calendars?
4. Which duration units and working-time conventions are supported in MVP-1 (days only, hours, elapsed durations)?
5. Which constraint types are hard versus advisory, and how should violations affect calculation/approval?
6. Which percent-complete method is used first, and how does it determine remaining duration?
7. Is the project finish date calculated only, or can a target/required finish create negative float?
8. What level of resource capacity is meaningful for AI agents, software licenses, and shared hardware in the first resource phase?
9. Which UI technology and Gantt rendering approach best fit the BiblionOCR desktop architecture after the Qt/PySide6 direction is confirmed?
10. What BiblionOCR events are eligible to propose actual-progress updates, and who approves them?
11. What import/export formats are needed before a standalone release, if any?
12. What audit, backup, and recovery guarantees are required for schedule history?

---

## 14. Initial acceptance statement

The first demonstrable vertical slice is deliberately modest:

```text
Task A — 5 working days
Task B — 3 working days
Task C — 4 working days

A ── FS ──► B ── FS ──► C
```

Given a project calendar and start date, the headless engine calculates the three activities in order, persists sufficient inputs/results to reproduce the calculation, reports any invalid relationship/constraint, and exposes the result to a simple consumer. Only after this slice is correct should the project add calendars of increasing complexity, milestone networks, SS/FF/SF logic, resources, baselines, and the full Gantt workspace.

---

## 15. Approval record

| Decision | Owner | Date | Notes |
| --- | --- | --- | --- |
| Approve architecture direction | `TBD` | `YYYY-MM-DD` | |
| Approve Phase 1 scope | `TBD` | `YYYY-MM-DD` | |
| Approve persistence boundary | `TBD` | `YYYY-MM-DD` | |
| Approve BiblionOCR integration adapter | `TBD` | `YYYY-MM-DD` | |
<!-- End of architecture plan. -->
