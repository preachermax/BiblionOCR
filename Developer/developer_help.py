from __future__ import annotations

from PyQt5 import QtGui as qtg
from PyQt5 import QtWidgets as qtw


DEVELOPER_HELP = {
    "title": "BiblionOCR Developer Workflow",
    "description": """DEVELOPER WORKFLOW OVERVIEW

The Developer Workflow Wizard turns the BiblionOCR development checklist into a guided working record. It is intended for human developers collaborating with GitHub Copilot as a design and implementation partner.

THE WORKFLOW

1. Frame the change and its observable outcome.
2. Anchor the investigation in a file, symbol, failure, command, or test.
3. State one local hypothesis and a cheap check that could disprove it.
4. Bound intended files and protect unrelated worktree changes.
5. Plan the smallest coherent edit and its first focused validation.
6. Satisfy the mandatory pre-PR evidence gate and record the next action.

Copilot can inspect code, challenge assumptions, implement changes, and run available validation. The human developer remains responsible for requirements, product decisions, review, licensing decisions, and release approval.

The planning stages leave design and implementation choices to the developer. The pre-PR gate is deliberately strict: the wizard reports PR ELIGIBLE only after every universal requirement passes with evidence and every conditional requirement either passes or has a written Not applicable justification.

The wizard does not edit source code, execute tests, commit changes, or send information to Copilot automatically.""",
    "requirements": """DEVELOPER REQUIREMENTS

Human developers must use this wizard in place of manually tracking the development checklist. The planning fields are intentionally open-ended, but the following pre-PR requirements are mandatory.

UNIVERSAL GATES - PASS WITH EVIDENCE

1. Requirement and scope are explicit
2. Unrelated worktree changes are preserved
3. Problems baseline and final totals are recorded
4. Focused automated checks pass
5. Canonical launcher smoke expectations are satisfied
6. Final diff and staged scope are clean
7. Branch and remote synchronization status are recorded
8. Residual risks and next action are recorded
9. Contribution will proceed through PR review

Universal gates cannot be marked Not applicable.

CONDITIONAL GATES - PASS OR JUSTIFIED NOT APPLICABLE

1. Designer UI, generated Python, and runtime wiring are in lockstep
2. Workflow Wizard policy and Wizard wording remain correct
3. Page workflow, session state, and handoffs remain correct
4. Removed UI controls have no live runtime references
5. Open-file controls follow the MyExplorer policy
6. Touched code compiles or passes its equivalent static check
7. Changed runtime paths pass smoke tests
8. Changed interaction surfaces pass manual UI review
9. Behavior, help, and development documentation are synchronized
10. Architecture-normalization evidence is synchronized

Not applicable is valid only when the row offers that status and the contribution truly does not touch the named surface. A written factual reason is mandatory. Convenience, lack of time, unavailable evidence, or a failing check are not valid Not applicable reasons.

EVIDENCE STANDARD

Evidence must be specific enough for another developer or reviewer to evaluate. Use exact commands and outcomes for automated checks, full and in-scope totals for Problems, observed behavior for manual checks, file or symbol names for audits, and source/base/remote details for branch status. Do not write only "done," "checked," or "works."

A known failure must remain visible. Repair it before selecting Pass, or leave the gate blocked unless the row is genuinely conditional and unaffected. Never classify an introduced regression as pre-existing.

UI changes must preserve the production Designer/generated/runtime lockstep even though Developer.py and developer_help.py themselves are hand-maintained exceptions.

TERMINOLOGY STANDARD

Consult Developer/documentation/BIBLIONOCR_NOMENCLATURE.md when a module, workflow, process, stage, state field, product, or generated artifact is named informally or ambiguously. Recognized aliases and misspellings help interpret intent, but committed code, UI text, help, tests, commits, and PR evidence must use the canonical term. Ask for clarification when different interpretations would materially change behavior or scope.

PR SUBMISSION REQUIREMENTS

1. Resolve every gate until the wizard reports PR ELIGIBLE.
2. Complete the final handoff and risk notes.
3. Click Copy PR Evidence.
4. Replace the Developer Wizard Evidence placeholder in the PR template with the complete generated block.
5. Submit through a feature branch and pull request; do not update a protected branch directly.
6. Request Copilot/agent review followed by repository owner/maintainer review.
7. Keep the PR open for corrections if automation or review finds insufficient or inaccurate evidence.

PR ELIGIBLE means the local evidence structure is complete. It does not guarantee acceptance, waive review, or authorize a merge. The repository Action checks the versioned declaration and evidence-row count; reviewers assess whether the implementation and evidence are truthful, relevant, and sufficient.""",
    "usage": """USAGE GUIDE

STARTING THE WIZARD

From the repository root run:

    .venv/bin/python -m Developer.Developer

Press F1 or click Help at any point to reopen this guide.

FRAME THE CHANGE

Use a short behavior-oriented title. Name one active module or shared subsystem. Describe what should be observably different when the change is complete, without prescribing code prematurely.

ANCHOR THE INVESTIGATION

Identify the most concrete starting point available: a failing test, traceback, command, file, or symbol. State a falsifiable explanation of the behavior and the cheapest nearby check that could prove it wrong. Give this evidence to Copilot before asking for broad exploration.

BOUND THE CHANGE SET

List expected runtime, UI, generated, test, and documentation files. Explicitly exclude unrelated modified files, runtime session state, archives, and deferred modules. Update the scope when evidence changes ownership of the behavior.

PLAN AND IMPLEMENT

Describe the smallest coherent change that tests the hypothesis and follows existing repository patterns. Define the first executable validation before editing. Ask Copilot to implement through validation and handoff, while reviewing its assumptions and proposed scope.

COMPLETE THE PRE-PR GATE

Each row begins as Not reviewed. Select Pass only after the requirement has been verified, then provide a command/result, observation, or other concrete evidence. Conditional rows also allow Not applicable, but require a specific justification. Universal requirements cannot be waived.

The wizard will not advance to the PR handoff page until every row is valid. Put longer commands, Problems totals, manual UI results, known failures, and platform limitations in Validation Notes. Failed checks are evidence; leave the gate blocked until the failure is repaired or an allowed condition is accurately justified.

Save Draft Report remains available while gates are incomplete. A draft records blockers but does not make a change eligible for review.

HANDOFF

Copy Copilot Brief places a structured prompt on the clipboard. No data is transmitted automatically. Once all gates pass, Copy PR Evidence creates the versioned attestation expected by the repository PR template and enforcement Action. Paste the complete block into the PR body. Save Workflow Report writes the brief, gate evidence, notes, blockers, and handoff to a Markdown file at a location you select.

The repository check confirms the required declaration is present; maintainers and Copilot/agent review assess whether the evidence is credible and sufficient. A PASS declaration does not guarantee approval or replace review.

TROUBLESHOOTING

Next is disabled on a planning page: Complete every required field on that page.

Next is disabled on the pre-PR gate: Resolve every listed blocker. Hover over a requirement for its evidence guidance.

F1 does not open help: Ensure the wizard window has focus and PyQt5 loaded from the project virtual environment.

Report cannot be saved: Select a writable destination and verify filesystem permissions.

Copied brief or PR evidence is stale: Return to the relevant page, update the field or gate, and copy it again from the final page.

Native Qt crash: Reproduce the failure in an isolated subprocess and record its platform, command, and exit code.""",
    "development": """DEVELOPMENT NOTES

OWNERSHIP

Developer/Developer.py owns the wizard, workflow record, Copilot brief, and report generation.

Developer/developer_help.py owns this help content and dialog. The developer UI is hand-maintained and intentionally exempt from the production Designer/generated UI lock-step rule.

Developer/documentation/BIBLIONOCR_NOMENCLATURE.md owns preferred contributor-facing names and recognized aliases. Domain meanings remain governed by docs/development/DESIGN_SPECIFICATION.md, and implementation status remains governed by the architectural truth table.

MAINTENANCE CONTRACT

When DEVELOPMENT_ROUTINE_CHECKLIST_ONE_PAGE.md changes its workflow phases, validation gates, collaboration policy, or handoff requirements, review both Developer.py and developer_help.py in the same change set.

Keep help claims aligned with actual behavior. In particular, distinguish actions performed by the wizard from actions performed by a developer or Copilot. The wizard currently stores no automatic session state and writes only through the user-selected Save Draft Report or Save Workflow Report actions.

PRE-PR CONTRACT

PR_GATE_DEFINITIONS is the local source for universal and conditional gates. evaluate_pr_eligibility requires a recognized final status and non-empty evidence for every definition. build_pr_evidence emits the exact versioned declarations enforced for human-developer PRs by .github/workflows/enforce-pr-checklist.yml.

Changes to gate meaning, version, generated declarations, the PR template, or the enforcement Action must be made and tested together. Repository enforcement can require attestations but cannot prove that a human's evidence is truthful; Copilot/agent and maintainer review remain mandatory.

TESTING

Compile the developer modules and run:

    python -m pytest tests/test_developer_workflow_wizard.py -q

The focused tests verify brief/report content, blocked and eligible gate states, conditional Not applicable handling, generated PR evidence, required help topics, the native Help button, F1 shortcut wiring, and dialog tabs. Also instantiate the wizard with QT_QPA_PLATFORM=offscreen when validating Qt construction.

UI EXTENSION

Keep this tool simple. Add a new wizard stage only when it represents a durable checklist phase. Add contextual explanations here when fields or validation gates change. Avoid dependencies on production helper paths so this tool remains launchable as a package module from the repository root.""",
}


def get_about_html() -> str:
    return """
<h2>BiblionOCR Developer Workflow</h2>
<p>Developer-only workflow guidance for the BiblionOCR project.</p>
<p><b>Purpose:</b> Help human developers collaborate effectively with GitHub Copilot while preserving evidence, scope discipline, validation, and clear handoffs.</p>
<ul>
<li>Framework: PyQt5</li>
<li>License: See the repository LICENSE file</li>
<li>Checklist: Developer/documentation/DEVELOPMENT_ROUTINE_CHECKLIST_ONE_PAGE.md</li>
<li>Source: Developer/Developer.py and Developer/developer_help.py</li>
</ul>
"""


class DeveloperHelpDialog(qtw.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{DEVELOPER_HELP['title']} - Help")
        self.resize(820, 620)

        layout = qtw.QVBoxLayout(self)
        title = qtw.QLabel(DEVELOPER_HELP["title"], self)
        title_font = qtg.QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        self.tabs = qtw.QTabWidget(self)
        for label, key in (
            ("Overview", "description"),
            ("Requirements", "requirements"),
            ("Usage Guide", "usage"),
            ("Development", "development"),
        ):
            content = qtw.QTextEdit(self.tabs)
            content.setObjectName(f"{key}HelpText")
            content.setPlainText(DEVELOPER_HELP[key])
            content.setReadOnly(True)
            self.tabs.addTab(content, label)
        layout.addWidget(self.tabs, 1)

        buttons = qtw.QDialogButtonBox(self)
        self.about_button = buttons.addButton("About", qtw.QDialogButtonBox.ActionRole)
        close_button = buttons.addButton(qtw.QDialogButtonBox.Close)
        self.about_button.clicked.connect(self.show_about)
        close_button.clicked.connect(self.accept)
        layout.addWidget(buttons)

    def show_about(self) -> None:
        qtw.QMessageBox.about(self, "About BiblionOCR Developer Workflow", get_about_html())


def show_developer_help(parent=None) -> None:
    DeveloperHelpDialog(parent).exec_()