"""User-facing help topics for the standalone Scheduler."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HelpTopic:
    id: str
    title: str
    keywords: tuple[str, ...]
    html: str

    @property
    def searchable_text(self) -> str:
        return " ".join((self.title, *self.keywords, self.html)).casefold()


HELP_TOPICS = (
    HelpTopic(
        "getting-started",
        "Getting Started",
        ("first launch", "database", "open", "tabs", "new wbs", "from scratch"),
        """
        <h2>Getting Started</h2>
        <p>Biblion Scheduler opens the persisted BiblionOCR development plan. On first launch it creates a local SQLite database and seeds the initial plan.</p>
        <p>Choose <b>File &gt; New WBS</b> or press <b>Ctrl+N</b> to create a separate WBS from scratch. Enter its stable project ID, display name, and start date, then select a SQLite database. The new blank WBS becomes the active session and Save target.</p>
        <ol>
          <li>Review activities and dates on the <b>Schedule</b> tab.</li>
          <li>Review phase and module roll-ups on the <b>WBS Summary</b> tab.</li>
          <li>Edit an activity only when its estimate or WBS assignment is understood.</li>
          <li>Use <b>Save</b> to preserve an accepted revision.</li>
        </ol>
        <p>Closing with unsaved changes displays a warning. Choose Save to preserve the current revision, Discard to close without it, or Cancel to return to the workspace. A failed or cancelled save keeps the Scheduler open.</p>
        """,
    ),
    HelpTopic(
        "wbs",
        "Work Breakdown Structure",
        ("wbs", "hierarchy", "phase", "module", "summary", "roll-up", "cut", "copy", "paste", "progress", "pages", "sort", "filter", "fill down"),
        """
        <h2>Work Breakdown Structure</h2>
        <p>The WBS organizes the project into outcomes, phases, modules, and smaller planning packages. Each WBS element is displayed as a calculated summary item; it does not determine dates by itself.</p>
                <ol>
                    <li><b>Level 1 - Project/Phase:</b> top-level WBS scope, shown in teal.</li>
                    <li><b>Level 2 - Summary/Work Package:</b> descendant WBS planning packages, shown in amber.</li>
                    <li><b>Level 3 - Activity or Milestone:</b> scheduled work, with milestones represented by zero duration.</li>
                </ol>
        <p>Each activity or milestone may be assigned to one WBS element. The WBS Summary rolls descendant dates and counts into every parent element.</p>
        <ul>
                    <li><b>Planned Start/Finish</b> roll up from descendants unless a summary override is entered.</li>
                    <li><b>Planned Duration</b> is recalculated in working days from the planned dates.</li>
                    <li><b>Actual Start</b> is the earliest descendant actual start.</li>
                    <li><b>Actual Finish</b> appears when every descendant has an actual finish; actual duration is then recalculated.</li>
                    <li><b>Progress</b> and <b>Pages</b> are duration-weighted averages of all descendant activities. Milestones carry one unit of weight.</li>
                      <li><b>Status</b> is Not Started at 0%, Complete at 100%, and In Progress between those values.</li>
          <li><b>Critical work</b> means at least one descendant is critical.</li>
        </ul>
                <p>Click a column header to sort sibling items; WBS code is the default sort and uses numeric code segments. Right-click a header to sort explicitly, filter that column, or clear filters. A matching descendant keeps its ancestor path visible, and a dot marks each filtered header.</p>
                <p>Right-click a WBS element for Add Item, Edit Item, Fill Down, Copy Item, Cut Item, Paste Item, Undo, Redo, and Delete Item. Add Item can insert a summary above or below the selected sibling, add a child summary, or add an activity. Inserting at an occupied outline number shifts that sibling and every following sibling by one; descendant codes receive the same branch-prefix change. Stable IDs, hierarchy links, and activity assignments do not change.</p>
                <p>Paste places a summary beneath the selected WBS element. Cut preserves the stable ID and moves the existing branch; copy creates a new empty summary with a unique ID and code. These clipboard and delete commands apply to WBS summaries, not activities.</p>
                <p>To repeat a value, select at least two cells in one column and choose <b>Fill Down</b>. The top selected item supplies the value. Fill Down supports Element, Planned Start, Planned Finish, and Units, and the entire operation is one undoable edit. WBS codes and calculated roll-up columns cannot be filled.</p>
                <p>Use <b>Add activity</b> on the WBS Summary tab or <b>Add Item &gt; Activity Item</b> in its context menu to create scheduled work beneath the selected WBS element. The activity editor accepts its stable ID, dates, duration units, progress, workflow sequence, and predecessor/successor relationships before the activity is added atomically.</p>
                <p>A summary cannot be deleted while it has child summaries or assigned activities; move or remove those items first.</p>
        """,
    ),
    HelpTopic(
        "activities",
        "Activities and Milestones",
        ("task", "activity", "milestone", "duration", "edit", "progress", "pages", "sequence"),
        """
        <h2>Activities and Milestones</h2>
        <p>An activity has a duration of one or more working days. A milestone has zero duration and marks a decision, handoff, approval, or completion point.</p>
        <p>Select an activity and use <b>Edit selected item</b>, or double-click its row. You may change its name, planned start/finish, actual start/finish, duration units, WBS assignment, workflow sequence, progress percent, page percent complete, predecessors, successors, relationship types, and lead/lag values.</p>
        <p>Duration units may be days or hours. Biblion Scheduler uses an eight-hour working day; hour durations are rounded up to whole working days for date scheduling. Planned and actual duration values recalculate from their dates in the selected unit. Float and critical status remain calculated.</p>
        <p>An actual finish automatically marks an activity 100% complete. Summary actual values and status then update from descendant activities.</p>
        <p>Every activity and WBS summary uses its planned span as a clear outlined track. Green progress overlays that track in proportion to completion: an unstarted item remains clear, an in-progress item is partially green, and a completed item is fully green. Compact labels sit below the relationship route so dependency lines remain visible.</p>
        """,
    ),
    HelpTopic(
        "dependencies",
        "Dependencies and Lead/Lag",
        ("fs", "ss", "ff", "sf", "predecessor", "successor", "lead", "lag"),
        """
        <h2>Dependencies and Lead/Lag</h2>
        <p>Dependencies express schedule logic between predecessor and successor activities.</p>
        <ul>
          <li><b>FS</b>: successor starts after predecessor finishes.</li>
          <li><b>SS</b>: successor start is related to predecessor start.</li>
          <li><b>FF</b>: successor finish is related to predecessor finish.</li>
          <li><b>SF</b>: successor finish is related to predecessor start.</li>
        </ul>
        <p>Positive lag delays the relationship in working days. Negative lag is lead and permits overlap. Circular dependencies are rejected.</p>
        <p>The activity editor provides separate predecessor and successor tables. Each relationship accepts FS, FF, SF, or SS and a signed Lead / Lag value: use a negative number for lead and a positive number for lag.</p>
        <p>The Schedule grid shows predecessor, successor, and logic columns for every activity. WBS summary relationships are calculated from activity dependencies that cross the summary boundary. Project Start and Project Finish identify open network endpoints.</p>
        <p>Click any Schedule column header to sort ascending; click it again to reverse the order. The default order follows the WBS Summary's natural outline order, so numeric segments place 1.2 before 1.10. Quantitative columns use numeric comparisons. The Gantt rows follow every grid sort so labels and bars remain aligned.</p>
        <p>Gantt dependency lines originate at the predecessor start or finish required by the relationship and terminate with an arrowhead at the corresponding successor start or finish.</p>
        """,
    ),
    HelpTopic(
        "constraints",
        "Constraints and Deadlines",
        ("constraint", "deadline", "required finish", "violation", "calendar"),
        """
        <h2>Constraints and Deadlines</h2>
        <p>Constraints model required date boundaries such as Start No Earlier Than, Finish No Later Than, Must Start On, and Must Finish On.</p>
        <p>A required project finish drives the backward pass and can produce negative float. Constraint warnings should be resolved by correcting logic, estimates, or approved dates rather than editing calculated dates.</p>
        """,
    ),
    HelpTopic(
        "critical-path",
        "Critical Path and Float",
        ("critical", "float", "early", "late", "forecast"),
        """
        <h2>Critical Path and Float</h2>
        <p>Red activities are critical. Delaying them can delay the project finish. Float is the available working-day movement between an activity's early and late dates.</p>
        <p>Negative float indicates that the current network cannot meet the required finish date. Review predecessors, estimates, calendars, and constraints before changing the deadline.</p>
        """,
    ),
    HelpTopic(
        "saving-baselines",
        "Saving and Baselines",
        ("save", "sqlite", "baseline", "revision", "reopen"),
        """
        <h2>Saving and Baselines</h2>
        <p><b>Save</b> writes the current project inputs, including WBS edits, and a reproducible calculation record to the active SQLite database. Use the File menu, <b>Ctrl+S</b>, the toolbar, or the WBS context menu.</p>
        <p><b>Save As</b> writes the current session to another SQLite database. That database becomes the active Save target for the rest of the session. Use the File menu, <b>Ctrl+Shift+S</b>, or the WBS context menu. Launch the Scheduler with that database to reopen the saved plan.</p>
        <p><b>New WBS</b> creates and immediately saves a blank WBS document with no summaries or activities. Unsaved changes in the current document must be saved or explicitly discarded before the session changes.</p>
        <p>Closing the Scheduler also checks the current project against its last saved revision. Save completes before closeout; Cancel or a failed save leaves the window open.</p>
        <p>A baseline is an approved, append-only date snapshot used for comparison. Editing the current plan does not rewrite an existing baseline. Capture a baseline only after durations and relationships have been reviewed.</p>
        """,
    ),
    HelpTopic(
        "workflow-evidence",
        "BiblionOCR Workflow Evidence",
        ("csv", "ods", "workflow", "source row", "module", "traceability"),
        """
        <h2>BiblionOCR Workflow Evidence</h2>
        <p>The ProjectWorkflow.ods project and page workflow sheets, or their manually exported CSV files, describe module steps, methods, milestones, and handoffs. They are read-only planning evidence until explicitly reconciled and approved.</p>
        <p>The Scheduler registers immutable source revisions by checksum and classifies staged records as new, mapped, changed, ignored, or conflicting. Approval creates a stable Scheduler workflow identity. One workflow may map to several activities, and one activity may map to several workflows.</p>
        <p>Use the <b>Workflow Governance</b> tab to select a project or page scope, enter an explicit source revision, and import the workbook. Review one snapshot at a time, then approve or ignore each staged row. The WBS column shows the persisted outline codes of all activities mapped to each workflow. The selected row's Milestone Name and Sequence fields are shown above the mapping controls. To map an approved row, select the activity, its parent WBS element, and the informational, implements, or milestone role. The next available direct-child WBS number is previewed and assigned to the activity automatically.</p>
        <p>Mapping makes the governed Milestone Name the activity name and makes the governed Sequence the activity workflow sequence. A success summary confirms the milestone, activity, assigned WBS code, and mapping role. Schedule displays both mapped values, while WBS Summary rolls descendant sequences into its Sequence column.</p>
        <p>Approved decisions cannot be reclassified. Conflicting rows remain blocked until a governed workflow identity is explicitly selected by a future conflict-resolution command.</p>
        <p>The activity's generated WBS number, parent assignment, milestone name, and sequence are saved with the mapping and remain stable when the project is reopened. The Scheduler does not infer durations or dependencies from worksheet order. Workflow mappings preserve scope and provenance but never create schedule logic automatically.</p>
        """,
    ),
    HelpTopic(
        "troubleshooting",
        "Troubleshooting",
        ("problem", "error", "missing", "reset", "launch", "pyqt"),
        """
        <h2>Troubleshooting</h2>
        <ul>
          <li><b>Application does not open:</b> run it from the Scheduler directory and verify PyQt5 is installed in the active Python environment.</li>
          <li><b>Edit is rejected:</b> check required names, WBS references, dependency cycles, and constraint dates.</li>
          <li><b>Saved change is missing:</b> confirm the same database and project identifier were used on both launches.</li>
          <li><b>Unexpected dates:</b> inspect working days, holidays, dependency type, lag, constraints, and required finish.</li>
        </ul>
        """,
    ),
    HelpTopic(
        "current-scope",
        "Current Scope",
        ("limitations", "future", "editing", "standalone"),
        """
        <h2>Current Scope</h2>
        <p>The workspace edits activity names, dates, durations, units, WBS assignments, workflow sequence, completion percentages, and predecessor/successor relationships. WBS summaries can be created, edited, moved, copied, and deleted. Workflow source revisions can be imported, reviewed, approved, ignored, and mapped to activities. A dedicated constraint editor, bulk reconciliation, and explicit conflict-resolution command are not yet available.</p>
        <p>The Scheduler plans BiblionOCR development. It does not execute BiblionOCR modules or modify an OCR project.</p>
        """,
    ),
)


def help_topic(topic_id: str) -> HelpTopic:
    for topic in HELP_TOPICS:
        if topic.id == topic_id:
            return topic
    raise KeyError(f"Unknown help topic: {topic_id}")


def search_help_topics(query: str) -> tuple[HelpTopic, ...]:
    terms = tuple(term for term in query.casefold().split() if term)
    if not terms:
        return HELP_TOPICS
    return tuple(topic for topic in HELP_TOPICS if all(term in topic.searchable_text for term in terms))
