# Biblion Scheduler - Core Starter

This portable scheduler implements the first standalone planning slices described in the architecture plan. Its domain engine remains headless and has no Qt or BiblionOCR runtime dependency; the optional PyQt5 workspace displays the calculated plan.

It schedules zero-duration milestones and duration-based tasks using a Monday–Friday working calendar. It supports Finish-to-Start (FS), Start-to-Start (SS), Finish-to-Finish (FF), and Start-to-Finish (SF) predecessor logic, including working-day lead/lag. The returned result includes early and late dates, total float, critical status, and hard-constraint diagnostics. It rejects unknown task references, duplicate dependencies, and cyclic dependency graphs.

Projects may also contain a hierarchical work breakdown structure. Each WBS element has a stable identifier, display code, name, and optional parent. Activities and milestones can be assigned to a WBS element; calculated dates, counts, progress percent, and page percent complete roll up through every ancestor. Completion percentages use activity duration as weight, with zero-duration milestones carrying one unit of weight. WBS structure organizes work, while dependencies and constraints continue to control schedule dates.

The desktop workspace separates the activity Gantt from a WBS Summary view. The logical presentation is Level 1 Project/Phase, Level 2 Summary/Work Package, and Level 3 Activity or zero-duration Milestone. The summary presents that hierarchy with rolled-up start and finish dates, completion percentages, activity and milestone counts, and progress status. Column headers sort sibling items, with natural ascending WBS-code order as the default. A header context menu filters individual columns while retaining the ancestor path to matching descendants. Every Schedule grid column is sortable. Its default order matches the WBS Summary's natural outline order, numeric fields use numeric comparisons, and the Gantt reorders with the grid so each row remains aligned with its bar.

WBS elements are the plan's calculated summary items. The WBS context menu provides Add Item (Summary Above, Summary Below, Child Summary Item, or Activity Item), Edit Item, Fill Down, Copy Item, Cut Item, Paste Item, Undo, Redo, and Delete Item. Inserting above or below uses the selected row's sibling level. If the insertion position is occupied, that sibling and every following sibling shift by one outline number, including the complete code prefix of each descendant branch. Stable IDs, parent links, and activity assignments remain unchanged, and the complete insertion is one undoable edit. Add Activity assigns new scheduled work to the selected WBS element and validates its entered relationships atomically. The structural clipboard and delete commands apply only to WBS summaries. Paste places a summary beneath the selected element. Cut reparents the existing element while preserving its stable ID; copy creates a new empty element with a unique ID and code. Deletion is intentionally blocked while an element has child elements or assigned activities. Fill Down copies Element, Planned Start, Planned Finish, or Units from the top selected item through the selected rows as one undoable edit; unique codes and calculated columns remain protected.

Save and Save As are available from the File menu and WBS context menu; Save is also available on the toolbar. Save writes the complete edited project and calculation record to the active SQLite database. Save As writes the current session to a selected database and makes that database the target of subsequent Save commands. Reopen the Scheduler with that database path to continue the saved WBS session.

Closing a workspace with unsaved changes prompts for Save, Discard, or Cancel. Save must complete successfully before the window closes; Cancel, a cancelled Save As dialog, or a persistence failure leaves the workspace open with its edits intact.

File > New WBS (`Ctrl+N`) creates a separate planning document from scratch. After entering a stable project ID, name, and start date, choose its SQLite database. The blank WBS contains no summaries or activities and becomes the active session and Save target. The workspace asks whether to save, discard, or cancel when the current WBS has unsaved edits.

Select an activity and use the toolbar edit command, or double-click its row, to change its name, planned start/finish, actual start/finish, duration units, WBS assignment, workflow sequence, progress percent, page percent complete, predecessors, successors, relationship type, and lead/lag. Duration units may be days or hours; the date-granular engine converts hours using an eight-hour working day and rounds up partial days. Negative relationship values are lead and positive values are lag. Planned and actual durations recalculate from their date pairs in the selected unit. An actual finish marks the activity complete. Summary actual dates, durations, completion, and status roll up automatically; summary planned dates and duration units may be overridden in the WBS editor. Changes remain in memory until the explicit Save command writes the revised project and calculation record to SQLite. Float and critical status are never directly editable.

The Gantt follows the same recursive order as the WBS. Level 1 Project/Phase tracks use teal outlines, and Level 2 Summary/Work Package tracks use amber outlines. Every summary, activity bar, and milestone diamond has a compact external label. Planned spans have a clear background; green progress overlays each activity or summary track in proportion to its completion percentage. Unstarted work remains clear, in-progress work is partially green, and completed work is fully green. Labels are positioned below the relationship centerline, and dependency lines are painted last so names do not hide them.

Every activity row displays its incoming predecessors, outgoing successors, and FS, FF, SF, or SS logic with any lead/lag. WBS summary relationships are derived from activity dependencies crossing the summary boundary. Dependency lines use the appropriate start/finish endpoints and place arrowheads on successor activities.

Open the searchable Help Center from the Help menu, the toolbar help button, or `F1`. The activity editor also opens its relevant help topic directly. Help covers first launch, WBS roll-ups, activities and milestones, dependency types, constraints, critical path and float, persistence and baselines, workflow evidence, troubleshooting, and current limitations.

## Contents

```text
BiblionScheduler-Core/
├── biblion_scheduler/
│   ├── __init__.py
│   ├── biblionocr.py
│   ├── calendar.py
│   ├── fixtures.py
│   ├── help_content.py
│   ├── models.py
│   ├── planner.py
│   ├── scheduler.py
│   ├── store.py
│   └── workflow.py
└── tests/
    ├── test_help_gui.py
    └── test_scheduler.py
```

## Run the tests

From this directory:

```bash
python3 -m unittest discover -s tests -v
```

## Launch the planner

From this directory:

```bash
python3 -m biblion_scheduler
```

On first run, the launcher seeds the curated BiblionOCR development plan into `~/.biblion-scheduler/scheduler.sqlite`. Later runs reopen the persisted plan rather than replacing local planning changes. An alternate database or persisted project can be selected explicitly:

From MyServer, open **Tools > Biblion Scheduler** or use the calendar button on the module toolbar. Both controls launch the same standalone Scheduler process.

```bash
python3 -m biblion_scheduler --database /path/to/plans.sqlite --project biblionocr-development
```

## Install the desktop launcher

From `Core/Scheduler`, install the standalone Linux launcher with:

```bash
python3 ../../launchers/install_biblionscheduler_launcher.py
```

This installs `Biblion Scheduler.desktop` in the application menu and on the current user's Desktop. The launcher uses the repository `.venv` when available, starts without a terminal window, and derives its paths from the current checkout. Re-run the installer after moving the repository. To remove it, delete `Biblion Scheduler.desktop` from `~/.local/share/applications` and `~/Desktop`.

The scheduler stores planning data only. Its BiblionOCR reference is read-only metadata; opening the planner cannot execute modules or modify a BiblionOCR project.

## WBS population

The acceptance plan currently establishes this first development hierarchy:

```text
1     BiblionOCR Development
1.1   Architecture
1.2   Core Platform
1.3   Module Workflows
1.3.1 MyScanner Standalone
1.4   Verification and Release
```

The hierarchy is intentionally coarse. Module WBS elements and planning activities should be populated incrementally from `Model/Project/Data/csv/ProjectWorkflow.ods` and the architecture documentation. Workflow rows provide identities, descriptions, modules, methods, and milestones, but they do not provide reviewed durations or complete scheduling relationships. The Scheduler must therefore not infer durations or dependencies merely from worksheet row order.

`WorkflowCatalog` reads the named project and page sheets directly from ODS, or reads manually exported CSV files, as read-only planning evidence. `SchedulerStore` registers checksummed source revisions idempotently and stages every row as new, mapped, changed, ignored, or conflicting. Explicit approval creates or updates a stable Scheduler-owned workflow identity. Approved workflows map many-to-many to activities without creating schedule dependencies. Imports, dispositions, approvals, and mappings are retained as append-only governance events.

The **Workflow Governance** tab imports an explicitly named source revision, filters records by immutable snapshot, and provides review commands for approval, ignore, and activity mapping. The source Sequence is a visible reconciliation column and an explicit read-only mapping field alongside Milestone Name. Its WBS column displays the persisted outline codes of all activities mapped to each governed workflow. Mapping an approved workflow requires an existing activity, a parent WBS element, and an informational, implements, or milestone role. The workspace previews and assigns the next available direct-child WBS outline number, maps Milestone Name to the activity name, maps Sequence to the activity sequence, persists the result, and displays a success summary with the milestone, activity, WBS code, and role before refreshing the workspace. Schedule displays the mapped name and sequence; WBS Summary includes a Sequence column that rolls up unique descendant activity sequences. Approval is idempotent and cannot be reversed into an ignored disposition. Unresolved conflicts cannot use the simple approval command because they require an explicit governed workflow identity. Mapping never creates dependency logic.

The current exports contain useful evidence but are not yet complete schedule inputs. In particular, duplicate identities are retained and reported instead of silently merged. Each link records the source path, workflow scope, composite identity, and source row so a planner can review changes when a later CSV export moves or corrects a row.

For each module rollout:

1. Add a module WBS element beneath `Module Workflows`.
2. Map stable workflow rows to activities or zero-duration milestones.
3. Supply reviewed working-day durations.
4. Define explicit predecessor relationships and lead/lag.
5. Verify the module roll-up and its effect on the overall critical path.
6. Capture a baseline only after the plan has been reviewed.

## Intentional boundary

`ScheduleEngine` receives domain objects and returns calculated dates and WBS roll-ups. It does not know about widgets, persistence, or BiblionOCR execution. `PlanEditor` provides atomic WBS, task, dependency, and constraint edits; every accepted edit produces a valid recalculated schedule, and a rejected edit leaves the prior plan unchanged. `SchedulerStore` is a separate, migration-managed SQLite repository: it stores project input snapshots, WBS hierarchy, task assignments, governed workflow evidence and mappings, an optional read-only external reference, append-only baseline date snapshots, audit events, and reproducible calculation hashes. `BiblionOCRAdapter` only attaches a stable BiblionOCR identity/revision; it cannot read, invoke, or rewrite BiblionOCR state. `biblionocr_development_plan()` is the curated first-run and end-to-end acceptance fixture. The next governance increment is explicit conflict resolution and efficient bulk review, followed by actual-progress candidate handling.
