from PyQt5 import QtGui as qtg
from PyQt5 import QtWidgets as qtw
from pathlib import Path

import pytest

from Developer.Developer import (
    PR_GATE_DEFINITIONS,
    DeveloperWorkflowWizard,
    GateResult,
    WorkflowRecord,
    build_copilot_brief,
    build_pr_evidence,
    build_workflow_report,
    evaluate_pr_eligibility,
)
from Developer.developer_help import DEVELOPER_HELP, DeveloperHelpDialog, get_about_html


ROOT = Path(__file__).resolve().parents[1]
NOMENCLATURE_PATH = ROOT / "Developer" / "documentation" / "BIBLIONOCR_NOMENCLATURE.md"


def _record() -> WorkflowRecord:
    return WorkflowRecord(
        title="Repair page selection",
        goal="Open the active project page",
        module="MyPixler",
        anchor="tests/test_pdf_source_workflow.py",
        hypothesis="The stale root is selected before project state loads",
        disconfirming_check="Run the focused PDF source workflow test",
        intended_files="MyPixler.py and its focused test",
        excluded_files="Runtime session JSON",
        implementation="Resolve the project root after state initialization",
        focused_validation="pytest tests/test_pdf_source_workflow.py -q",
        risks="Qt PDF process crash",
        validation_notes="Focused test passed",
        handoff="Ready for manual viewer verification",
    )


def _passing_gates() -> list[GateResult]:
    return [GateResult(gate.key, gate.label, "pass", f"Evidence for {gate.key}") for gate in PR_GATE_DEFINITIONS]


def test_copilot_brief_contains_design_and_validation_context():
    brief = build_copilot_brief(_record())

    assert "# Copilot Development Brief: Repair page selection" in brief
    assert "## Local Hypothesis" in brief
    assert "The stale root is selected before project state loads" in brief
    assert "run the focused validation immediately after the first substantive edit" in brief
    assert "BIBLIONOCR_NOMENCLATURE.md" in brief
    assert "Do not commit or push unless explicitly requested" in brief


def test_workflow_report_records_pr_eligible_gate_evidence():
    report = build_workflow_report(_record(), _passing_gates())

    assert "**PR ELIGIBLE**" in report
    assert "**PASS - Focused automated checks pass:** Evidence for focused_tests" in report
    assert "Focused test passed" in report
    assert "Ready for manual viewer verification" in report


def test_pr_evidence_requires_every_gate_and_written_evidence():
    incomplete = _passing_gates()
    incomplete[-1] = GateResult(incomplete[-1].key, incomplete[-1].label, "pending", "")

    eligible, blockers = evaluate_pr_eligibility(incomplete)

    assert not eligible
    assert any("Contribution will proceed through PR review: not reviewed" in blocker for blocker in blockers)
    with pytest.raises(ValueError, match="Pre-PR gate is incomplete"):
        build_pr_evidence(_record(), incomplete)


def test_conditional_gate_accepts_not_applicable_only_with_justification():
    results = _passing_gates()
    ui_index = next(index for index, result in enumerate(results) if result.key == "ui_lockstep")
    ui_gate = PR_GATE_DEFINITIONS[ui_index]
    results[ui_index] = GateResult(ui_gate.key, ui_gate.label, "not_applicable", "No production UI changed")

    assert evaluate_pr_eligibility(results) == (True, [])
    evidence = build_pr_evidence(_record(), results)
    assert "Developer Wizard Gate: PASS" in evidence
    assert "Developer Wizard Gate Version: 1" in evidence
    assert "**NOT APPLICABLE - Designer UI" in evidence


def test_generated_pr_evidence_matches_template_and_action_contract():
    evidence = build_pr_evidence(_record(), _passing_gates())
    template = (ROOT / ".github" / "pull_request_template.md").read_text(encoding="utf-8")
    action = (ROOT / ".github" / "workflows" / "enforce-pr-checklist.yml").read_text(encoding="utf-8")

    required_declarations = (
        "I completed the Developer Workflow Wizard and resolved every mandatory pre-PR gate.",
        "The wizard reported PR ELIGIBLE, and I included its evidence summary below.",
        "I am submitting a pull request only (no direct commit/resync operations on protected branches).",
        "I request Copilot/agent review first, then repository owner/maintainer review and approval.",
    )
    for declaration in required_declarations:
        assert declaration in evidence
        assert declaration in template
        assert declaration in action
    assert "Developer Wizard Gate: PASS" in evidence
    assert "Developer Wizard Gate Version: 1" in evidence
    assert "Developer Wizard Gate Version:\\s*1" in action
    assert len(PR_GATE_DEFINITIONS) == 19
    assert "minimumGateEvidenceCount = 19" in action
    assert evidence.count("- **PASS - ") == 19


def test_help_content_covers_workflow_copilot_and_maintenance():
    help_text = "\n".join(DEVELOPER_HELP.values())

    for expected_text in (
        "GitHub Copilot as a design and implementation partner",
        "falsifiable explanation",
        "No data is transmitted automatically",
        "PR ELIGIBLE",
        "Not applicable",
        "DEVELOPMENT_ROUTINE_CHECKLIST_ONE_PAGE.md",
        "developer_help.py in the same change set",
    ):
        assert expected_text in help_text
    for gate in PR_GATE_DEFINITIONS:
        assert gate.label in DEVELOPER_HELP["requirements"]
    assert "See the repository LICENSE file" in get_about_html()


def test_nomenclature_defines_canonical_terms_and_is_linked_from_developer_docs():
    nomenclature = NOMENCLATURE_PATH.read_text(encoding="utf-8")
    developer_readme = (ROOT / "Developer" / "README.md").read_text(encoding="utf-8")
    checklist = (
        ROOT / "Developer" / "documentation" / "DEVELOPMENT_ROUTINE_CHECKLIST_ONE_PAGE.md"
    ).read_text(encoding="utf-8")

    for required_term in (
        "Input may be informal; committed output must use canonical terminology.",
        "BiblionOCR",
        "MyServer",
        "MyScanner",
        "BiblionScanner",
        "Project Workflow Wizard",
        "Page Workflow Wizard",
        "current project page",
        "UI lockstep",
        "GitHub Copilot",
        "ODS authority",
        "CSV authority",
        "active workflow definition",
        "project root",
        "repository root",
        "PR ELIGIBLE",
        "commit-worthy Developer content",
    ):
        assert required_term in nomenclature
    assert "lock-tain" in nomenclature
    assert "BIBLIONOCR_NOMENCLATURE.md" in developer_readme
    assert "BIBLIONOCR_NOMENCLATURE.md" in checklist


def test_wizard_exposes_production_style_help():
    application = qtw.QApplication.instance() or qtw.QApplication([])
    wizard = DeveloperWorkflowWizard()

    assert wizard.testOption(qtw.QWizard.HaveHelpButton)
    assert wizard.buttonText(qtw.QWizard.HelpButton) == "Help"
    assert wizard.help_shortcut.key() == qtg.QKeySequence.HelpContents

    dialog = DeveloperHelpDialog(wizard)
    assert dialog.tabs.count() == 4
    assert [dialog.tabs.tabText(index) for index in range(dialog.tabs.count())] == [
        "Overview",
        "Requirements",
        "Usage Guide",
        "Development",
    ]

    assert not wizard.validation_page.isComplete()
    for gate in PR_GATE_DEFINITIONS:
        wizard.validation_page.set_gate_result(gate.key, "pass", f"Evidence for {gate.key}")
    assert wizard.validation_page.isComplete()
    assert wizard.validation_page.status_label.text().startswith("PR ELIGIBLE")
    dialog.close()
    wizard.close()
    application.processEvents()