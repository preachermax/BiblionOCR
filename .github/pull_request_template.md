# Pull Request Summary

## What Changed

Describe the change scope clearly.

## Why This Change

Explain the requirement/problem this PR addresses.

## Agent-Managed Checklist Path (Agent-Only)

Checklist reference:

- [Developer/documentation/DEVELOPMENT_ROUTINE_CHECKLIST_ONE_PAGE.md](Developer/documentation/DEVELOPMENT_ROUTINE_CHECKLIST_ONE_PAGE.md)

Use this section only for agent-managed implementation work.

Required confirmations (agent path):

- [ ] I completed the development checklist before opening this PR.
- [ ] Automated checks required by the checklist were run for touched files.
- [ ] Manual UI checks were completed for changed interaction surfaces.
- [ ] UI lock-step was verified for all changed UI surfaces (`.ui` and generated `UI.py`).
- [ ] Workflow wizard policy gates were verified for affected modules.

## Developer PR-Only Path

Use this section for non-agent developer submissions.

Required confirmations (developer path):

- [ ] I completed the Developer Workflow Wizard and resolved every mandatory pre-PR gate.
- [ ] The wizard reported PR ELIGIBLE, and I included its evidence summary below.
- [ ] I am submitting a pull request only (no direct commit/resync operations on protected branches).
- [ ] I request Copilot/agent review first, then repository owner/maintainer review and approval.

Human developers must run `.venv/bin/python -m Developer.Developer` and paste the generated **Developer Wizard Evidence** block below. A developer PR is not eligible for review until the repository check accepts that block.

## Developer Wizard Evidence

Replace this placeholder with the complete **Developer Wizard Evidence** block copied from the wizard.

Developer Wizard Gate: NOT PROVIDED
Developer Wizard Gate Version: NOT PROVIDED

## Validation Evidence

List key command outputs and manual checks performed.

## Risk Notes

Describe any residual risk, deferred follow-up, or test gaps.
