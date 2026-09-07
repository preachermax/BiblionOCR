from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5 import QtWidgets as qtw

if __package__:
    from .developer_help import show_developer_help
else:
    developer_directory = str(Path(__file__).resolve().parent)
    if developer_directory not in sys.path:
        sys.path.insert(0, developer_directory)
    from developer_help import show_developer_help


@dataclass(frozen=True)
class WorkflowRecord:
    title: str
    goal: str
    module: str
    anchor: str
    hypothesis: str
    disconfirming_check: str
    intended_files: str
    excluded_files: str
    implementation: str
    focused_validation: str
    risks: str
    validation_notes: str
    handoff: str


@dataclass(frozen=True)
class GateDefinition:
    key: str
    label: str
    guidance: str
    allow_not_applicable: bool = False


@dataclass(frozen=True)
class GateResult:
    key: str
    label: str
    status: str
    evidence: str


PR_GATE_VERSION = 1
PR_GATE_DEFINITIONS = (
    GateDefinition("scope", "Requirement and scope are explicit", "Record the requirement, intended files, and excluded work."),
    GateDefinition("worktree", "Unrelated worktree changes are preserved", "Cite the final git status review and excluded artifacts."),
    GateDefinition(
        "ui_lockstep",
        "Designer UI, generated Python, and runtime wiring are in lockstep",
        "Cite regeneration and drift checks, or explain why no production UI surface changed.",
        True,
    ),
    GateDefinition(
        "workflow_policy",
        "Workflow Wizard policy and Wizard wording remain correct",
        "Verify MyServer/project/page ownership and no Macro wording, or justify why unaffected.",
        True,
    ),
    GateDefinition(
        "page_state",
        "Page workflow, session state, and handoffs remain correct",
        "Cite focused state/handoff tests, or justify why these contracts are unaffected.",
        True,
    ),
    GateDefinition(
        "removed_controls",
        "Removed UI controls have no live runtime references",
        "Cite reference/signal audits, or state that no controls were removed.",
        True,
    ),
    GateDefinition(
        "file_picker",
        "Open-file controls follow the MyExplorer policy",
        "Cite the picker audit, or state that no open-file surface changed.",
        True,
    ),
    GateDefinition("problems", "Problems baseline and final totals are recorded", "Provide full-workspace total, in-scope total, and unresolved out-of-scope files."),
    GateDefinition(
        "compile",
        "Touched code compiles or passes its equivalent static check",
        "Provide the command and result, or justify a documentation-only change.",
        True,
    ),
    GateDefinition("focused_tests", "Focused automated checks pass", "Provide exact commands and outcomes for the changed behavior."),
    GateDefinition(
        "runtime_smoke",
        "Changed runtime paths pass smoke tests",
        "Provide launch/runtime evidence, or justify why the change has no runtime path.",
        True,
    ),
    GateDefinition(
        "manual_ui",
        "Changed interaction surfaces pass manual UI review",
        "Record observed behavior, or justify why no interaction surface changed.",
        True,
    ),
    GateDefinition("launchers", "Canonical launcher smoke expectations are satisfied", "Cite the launcher matrix result and any known platform limitation."),
    GateDefinition("commit_hygiene", "Final diff and staged scope are clean", "Cite diff/status review; runtime state and unrelated artifacts must be excluded."),
    GateDefinition("branch_status", "Branch and remote synchronization status are recorded", "Identify the source/base branches, remote status, and intended PR target."),
    GateDefinition(
        "documentation",
        "Behavior, help, and development documentation are synchronized",
        "List updated documentation, or justify why the change has no documentation impact.",
        True,
    ),
    GateDefinition(
        "architecture_lane",
        "Architecture-normalization evidence is synchronized",
        "Cite task ledger, truth table, spec, and exception updates, or mark this lane not applicable with a reason.",
        True,
    ),
    GateDefinition("handoff", "Residual risks and next action are recorded", "State remaining risks, deferred work, and the exact next action."),
    GateDefinition("pr_scope", "Contribution will proceed through PR review", "Confirm no direct protected-branch update and request Copilot/agent plus maintainer review."),
)


def _section(title: str, value: str, fallback: str = "Not recorded") -> str:
    return f"## {title}\n\n{value.strip() or fallback}"


def build_copilot_brief(record: WorkflowRecord) -> str:
    return "\n\n".join(
        (
            f"# Copilot Development Brief: {record.title.strip() or 'Untitled change'}",
            _section("Goal", record.goal),
            _section("Active Module", record.module),
            _section("Concrete Anchor", record.anchor),
            _section("Local Hypothesis", record.hypothesis),
            _section("Disconfirming Check", record.disconfirming_check),
            _section("Intended Files", record.intended_files),
            _section("Explicitly Excluded", record.excluded_files, "None identified"),
            _section("Implementation Strategy", record.implementation),
            _section("First Focused Validation", record.focused_validation),
            _section("Risks and Unknowns", record.risks, "None identified"),
            "## Collaboration Instructions\n\n"
            "Act as a design and implementation partner. Inspect the concrete anchor first, state any changed "
            "assumptions, keep edits within the intended scope, preserve unrelated worktree changes, and run the "
            "focused validation immediately after the first substantive edit. Continue through implementation, "
            "verification, and a concise handoff. Do not commit or push unless explicitly requested.",
        )
    ) + "\n"


def evaluate_pr_eligibility(gate_results: list[GateResult]) -> tuple[bool, list[str]]:
    results_by_key = {result.key: result for result in gate_results}
    blockers = []
    for definition in PR_GATE_DEFINITIONS:
        result = results_by_key.get(definition.key)
        if result is None or result.status == "pending":
            blockers.append(f"{definition.label}: not reviewed")
            continue
        if result.status == "not_applicable" and not definition.allow_not_applicable:
            blockers.append(f"{definition.label}: cannot be marked not applicable")
        elif result.status not in {"pass", "not_applicable"}:
            blockers.append(f"{definition.label}: invalid status")
        if not result.evidence.strip():
            suffix = "justification" if result.status == "not_applicable" else "evidence"
            blockers.append(f"{definition.label}: missing {suffix}")
    return not blockers, blockers


def _gate_evidence_lines(gate_results: list[GateResult]) -> str:
    lines = []
    for result in gate_results:
        display_status = "PASS" if result.status == "pass" else "NOT APPLICABLE" if result.status == "not_applicable" else "BLOCKED"
        lines.append(f"- **{display_status} - {result.label}:** {result.evidence.strip() or 'No evidence recorded'}")
    return "\n".join(lines)


def build_pr_evidence(record: WorkflowRecord, gate_results: list[GateResult]) -> str:
    eligible, blockers = evaluate_pr_eligibility(gate_results)
    if not eligible:
        raise ValueError("Pre-PR gate is incomplete: " + "; ".join(blockers))
    return f"""## Developer Wizard Evidence

Developer Wizard Gate: PASS
Developer Wizard Gate Version: {PR_GATE_VERSION}
Change: {record.title.strip() or "Untitled change"}
Module: {record.module.strip() or "Not recorded"}

- [x] I completed the Developer Workflow Wizard and resolved every mandatory pre-PR gate.
- [x] The wizard reported PR ELIGIBLE, and I included its evidence summary below.
- [x] I am submitting a pull request only (no direct commit/resync operations on protected branches).
- [x] I request Copilot/agent review first, then repository owner/maintainer review and approval.

{_gate_evidence_lines(gate_results)}
"""


def build_workflow_report(record: WorkflowRecord, gate_results: list[GateResult]) -> str:
    eligible, blockers = evaluate_pr_eligibility(gate_results)
    gate_status = "PR ELIGIBLE" if eligible else "NOT PR ELIGIBLE"
    blocker_text = "\n".join(f"- {blocker}" for blocker in blockers) or "None"
    return "\n\n".join(
        (
            build_copilot_brief(record).rstrip(),
            f"## Pre-PR Gate\n\n**{gate_status}**\n\nGate version: {PR_GATE_VERSION}",
            f"### Gate Evidence\n\n{_gate_evidence_lines(gate_results)}",
            f"### Blockers\n\n{blocker_text}",
            _section("Validation Notes", record.validation_notes),
            _section("Handoff", record.handoff, "Work remains in progress"),
            f"_Recorded {datetime.now().astimezone().isoformat(timespec='seconds')}_",
        )
    ) + "\n"


class FormPage(qtw.QWizardPage):
    def __init__(self, title: str, subtitle: str, parent=None):
        super().__init__(parent)
        self.setTitle(title)
        self.setSubTitle(subtitle)
        self.form = qtw.QFormLayout(self)
        self.form.setFieldGrowthPolicy(qtw.QFormLayout.AllNonFixedFieldsGrow)

    def add_line(self, label: str, field_name: str, placeholder: str, required: bool = False):
        editor = qtw.QLineEdit(self)
        editor.setPlaceholderText(placeholder)
        self.form.addRow(label, editor)
        self.registerField(field_name + ("*" if required else ""), editor)
        return editor

    def add_text(self, label: str, field_name: str, placeholder: str, required: bool = False):
        editor = qtw.QPlainTextEdit(self)
        editor.setPlaceholderText(placeholder)
        editor.setMinimumHeight(84)
        self.form.addRow(label, editor)
        property_name = b"plainText"
        changed_signal = editor.textChanged
        self.registerField(field_name + ("*" if required else ""), editor, property_name, changed_signal)
        return editor


class PartnershipPage(FormPage):
    def __init__(self, parent=None):
        super().__init__(
            "Frame the change with Copilot",
            "Describe the outcome before discussing implementation. Copilot is most useful when it can challenge a concrete goal.",
            parent,
        )
        self.add_line("Change title", "title", "Short, behavior-oriented title", required=True)
        self.add_line("Active module", "module", "For example: MyPixler or shared project state", required=True)
        self.add_text("Desired outcome", "goal", "What should be observably different when this work is complete?", required=True)

        note = qtw.QLabel(
            "Design-partner practice: give Copilot the goal, constraints, and evidence. Ask it to inspect the owning code, "
            "question weak assumptions, implement the smallest coherent change, and verify the result. The developer "
            "remains responsible for product decisions, review, and release approval.",
            self,
        )
        note.setWordWrap(True)
        note.setObjectName("partnerNote")
        self.form.addRow(note)


class EvidencePage(FormPage):
    def __init__(self, parent=None):
        super().__init__(
            "Anchor the investigation",
            "Start from a file, symbol, failing behavior, command, or test. Form one hypothesis that nearby evidence can disprove.",
            parent,
        )
        self.add_text("Concrete anchor", "anchor", "Exact file, symbol, failure, or reproduction command", required=True)
        self.add_text("Local hypothesis", "hypothesis", "The behavior occurs because...", required=True)
        self.add_text(
            "Cheap disconfirming check",
            "disconfirmingCheck",
            "The smallest test, read, or command that would show the hypothesis is wrong",
            required=True,
        )


class ScopePage(FormPage):
    def __init__(self, parent=None):
        super().__init__(
            "Bound the change set",
            "Name the intended ownership boundary and protect unrelated work already present in the checkout.",
            parent,
        )
        self.add_text("Intended files", "intendedFiles", "Runtime, UI source/generated pair, tests, and docs", required=True)
        self.add_text("Excluded files", "excludedFiles", "Unrelated local changes, runtime state, archives, or deferred modules")
        self.add_text("Risks and unknowns", "risks", "Native crashes, data mutation, cross-module contracts, licensing, or platform behavior")


class ImplementationPage(FormPage):
    def __init__(self, parent=None):
        super().__init__(
            "Plan the smallest testable edit",
            "Prefer the owning abstraction and existing repository patterns. Validation follows the first substantive edit immediately.",
            parent,
        )
        self.add_text(
            "Implementation strategy",
            "implementation",
            "What will change, in what order, and why this is the narrowest coherent approach",
            required=True,
        )
        self.add_text(
            "First focused validation",
            "focusedValidation",
            "A behavior test, narrow pytest target, compile check, or other executable check",
            required=True,
        )


class ValidationPage(qtw.QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Complete the mandatory pre-PR gate")
        self.setSubTitle("Every requirement needs evidence. Conditional requirements may be not applicable only with a written justification.")
        layout = qtw.QVBoxLayout(self)
        self.status_label = qtw.QLabel(self)
        self.status_label.setObjectName("gateStatus")
        layout.addWidget(self.status_label)

        self.gate_table = qtw.QTableWidget(len(PR_GATE_DEFINITIONS), 3, self)
        self.gate_table.setHorizontalHeaderLabels(("Requirement", "Status", "Evidence or N/A justification"))
        self.gate_table.verticalHeader().setVisible(False)
        self.gate_table.setAlternatingRowColors(True)
        self.gate_table.setSelectionMode(qtw.QAbstractItemView.NoSelection)
        header = self.gate_table.horizontalHeader()
        header.setSectionResizeMode(0, qtw.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, qtw.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, qtw.QHeaderView.Stretch)
        self._gate_editors = {}
        for row, definition in enumerate(PR_GATE_DEFINITIONS):
            requirement = qtw.QTableWidgetItem(definition.label)
            requirement.setToolTip(definition.guidance)
            requirement.setFlags(requirement.flags() & ~qtc.Qt.ItemIsEditable)
            self.gate_table.setItem(row, 0, requirement)

            status = qtw.QComboBox(self.gate_table)
            status.addItem("Not reviewed", "pending")
            status.addItem("Pass", "pass")
            if definition.allow_not_applicable:
                status.addItem("Not applicable", "not_applicable")
            status.setToolTip(definition.guidance)
            self.gate_table.setCellWidget(row, 1, status)

            evidence = qtw.QLineEdit(self.gate_table)
            evidence.setPlaceholderText("Command/result, observation, or N/A reason")
            evidence.setToolTip(definition.guidance)
            self.gate_table.setCellWidget(row, 2, evidence)
            self._gate_editors[definition.key] = (definition, status, evidence)
            status.currentIndexChanged.connect(self._gate_changed)
            evidence.textChanged.connect(self._gate_changed)
        layout.addWidget(self.gate_table, 1)

        layout.addWidget(qtw.QLabel("Validation notes and results", self))
        self.notes = qtw.QPlainTextEdit(self)
        self.notes.setPlaceholderText("Commands, outcomes, Problems totals, manual checks, and known failures")
        self.notes.setMaximumHeight(100)
        layout.addWidget(self.notes)
        self.save_draft_button = qtw.QPushButton("Save Draft Report", self)
        layout.addWidget(self.save_draft_button, 0, qtc.Qt.AlignRight)
        self._gate_changed()

    def _gate_changed(self, _value=None) -> None:
        eligible, blockers = evaluate_pr_eligibility(self.gate_results())
        if eligible:
            self.status_label.setText("PR ELIGIBLE: all mandatory gates contain evidence.")
            self.status_label.setStyleSheet("color: #1f653a; font-weight: bold;")
        else:
            self.status_label.setText(f"NOT PR ELIGIBLE: {len(blockers)} blocker(s) remain.")
            self.status_label.setStyleSheet("color: #9b3528; font-weight: bold;")
        self.completeChanged.emit()

    def isComplete(self) -> bool:
        eligible, _blockers = evaluate_pr_eligibility(self.gate_results())
        return eligible

    def gate_results(self) -> list[GateResult]:
        results = []
        for definition in PR_GATE_DEFINITIONS:
            _definition, status, evidence = self._gate_editors[definition.key]
            results.append(GateResult(definition.key, definition.label, str(status.currentData()), evidence.text()))
        return results

    def set_gate_result(self, key: str, status_value: str, evidence_text: str) -> None:
        _definition, status, evidence = self._gate_editors[key]
        index = status.findData(status_value)
        if index < 0:
            raise ValueError(f"Status {status_value!r} is not valid for gate {key!r}")
        status.setCurrentIndex(index)
        evidence.setText(evidence_text)


class HandoffPage(qtw.QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Review and hand off")
        self.setSubTitle("All mandatory gates passed. Copy the evidence block into the PR and retain the complete report.")
        layout = qtw.QVBoxLayout(self)
        self.eligibility_label = qtw.QLabel("PR ELIGIBLE", self)
        self.eligibility_label.setStyleSheet("color: #1f653a; font-size: 16px; font-weight: bold;")
        layout.addWidget(self.eligibility_label)
        self.summary = qtw.QPlainTextEdit(self)
        self.summary.setReadOnly(True)
        self.summary.setLineWrapMode(qtw.QPlainTextEdit.NoWrap)
        layout.addWidget(self.summary, 1)
        layout.addWidget(qtw.QLabel("Handoff status and next action", self))
        self.handoff = qtw.QPlainTextEdit(self)
        self.handoff.setPlaceholderText("What is done, what remains, blockers, and the exact next action")
        self.handoff.setMaximumHeight(100)
        layout.addWidget(self.handoff)

        actions = qtw.QHBoxLayout()
        self.copy_button = qtw.QPushButton("Copy Copilot Brief", self)
        self.copy_pr_button = qtw.QPushButton("Copy PR Evidence", self)
        self.save_button = qtw.QPushButton("Save Workflow Report", self)
        actions.addWidget(self.copy_button)
        actions.addWidget(self.copy_pr_button)
        actions.addWidget(self.save_button)
        actions.addStretch(1)
        layout.addLayout(actions)

    def initializePage(self) -> None:
        wizard = self.wizard()
        if isinstance(wizard, DeveloperWorkflowWizard):
            self.summary.setPlainText(build_copilot_brief(wizard.workflow_record()))


class DeveloperWorkflowWizard(qtw.QWizard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("BiblionOCR Developer Workflow")
        self.setWizardStyle(qtw.QWizard.ModernStyle)
        self.setOption(qtw.QWizard.NoBackButtonOnStartPage)
        self.setOption(qtw.QWizard.HaveHelpButton)
        self.setButtonText(qtw.QWizard.HelpButton, "Help")
        self.resize(840, 650)

        self.partnership_page = PartnershipPage(self)
        self.evidence_page = EvidencePage(self)
        self.scope_page = ScopePage(self)
        self.implementation_page = ImplementationPage(self)
        self.validation_page = ValidationPage(self)
        self.handoff_page = HandoffPage(self)
        for page in (
            self.partnership_page,
            self.evidence_page,
            self.scope_page,
            self.implementation_page,
            self.validation_page,
            self.handoff_page,
        ):
            self.addPage(page)

        self.setButtonText(qtw.QWizard.FinishButton, "Close")
        self.handoff_page.copy_button.clicked.connect(self.copy_copilot_brief)
        self.handoff_page.copy_pr_button.clicked.connect(self.copy_pr_evidence)
        self.handoff_page.save_button.clicked.connect(self.save_workflow_report)
        self.validation_page.save_draft_button.clicked.connect(self.save_workflow_report)
        self.currentIdChanged.connect(self._refresh_handoff)
        self.helpRequested.connect(self.show_help)
        self.help_shortcut = qtw.QShortcut(qtg.QKeySequence.HelpContents, self)
        self.help_shortcut.activated.connect(self.show_help)

        self.setStyleSheet(
            "QWizard { background: #f4f1e8; }"
            "QWizardPage { background: #f4f1e8; }"
            "QLabel#partnerNote { color: #284c45; background: #dce9df; border-left: 4px solid #b65f3a; padding: 10px; }"
            "QLineEdit, QPlainTextEdit { background: #fffdf7; border: 1px solid #9b9a91; padding: 5px; }"
            "QPushButton { padding: 6px 12px; }"
        )

    def _value(self, name: str) -> str:
        value = self.field(name)
        return "" if value is None else str(value)

    def workflow_record(self) -> WorkflowRecord:
        return WorkflowRecord(
            title=self._value("title"),
            goal=self._value("goal"),
            module=self._value("module"),
            anchor=self._value("anchor"),
            hypothesis=self._value("hypothesis"),
            disconfirming_check=self._value("disconfirmingCheck"),
            intended_files=self._value("intendedFiles"),
            excluded_files=self._value("excludedFiles"),
            implementation=self._value("implementation"),
            focused_validation=self._value("focusedValidation"),
            risks=self._value("risks"),
            validation_notes=self.validation_page.notes.toPlainText(),
            handoff=self.handoff_page.handoff.toPlainText(),
        )

    def _refresh_handoff(self, page_id: int) -> None:
        if self.page(page_id) is self.handoff_page:
            self.handoff_page.summary.setPlainText(build_copilot_brief(self.workflow_record()))

    def copy_copilot_brief(self) -> None:
        qtw.QApplication.clipboard().setText(build_copilot_brief(self.workflow_record()))

    def copy_pr_evidence(self) -> None:
        evidence = build_pr_evidence(self.workflow_record(), self.validation_page.gate_results())
        qtw.QApplication.clipboard().setText(evidence)

    def show_help(self) -> None:
        show_developer_help(self)

    def save_workflow_report(self) -> None:
        suggested_name = "-".join(self._value("title").lower().split()) or "development-workflow"
        default_path = Path.home() / f"{suggested_name}.md"
        filename, _selected_filter = qtw.QFileDialog.getSaveFileName(
            self,
            "Save Developer Workflow Report",
            str(default_path),
            "Markdown files (*.md);;All files (*)",
        )
        if not filename:
            return
        report = build_workflow_report(self.workflow_record(), self.validation_page.gate_results())
        try:
            Path(filename).write_text(report, encoding="utf-8")
        except OSError as error:
            qtw.QMessageBox.critical(self, "Unable to save report", str(error))
            return
        qtw.QMessageBox.information(self, "Workflow report saved", filename)


def main() -> int:
    application = qtw.QApplication.instance() or qtw.QApplication(sys.argv)
    application.setApplicationName("BiblionOCR Developer Workflow")
    application.setWindowIcon(qtg.QIcon())
    wizard = DeveloperWorkflowWizard()
    wizard.show()
    return application.exec_()


if __name__ == "__main__":
    raise SystemExit(main())