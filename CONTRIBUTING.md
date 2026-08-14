# Contributing to BiblionOCR

BiblionOCR accepts contributions from two different contributor groups:

- developers, who contribute code, tests, build changes, and architecture or developer documentation
- content creators, who contribute text, images, video, datasets, design assets, and other creative or editorial material

These two groups do not follow the same intake path.

## Access Model

- Developers should contribute through GitHub using pull requests.
- Direct pushes to `master` should remain disabled.
- Maintainers should require review before merging changes that affect runtime code, packaging, release assets, or repository policy.
- Content creators should not be given broad write access to the main code repository unless they are also acting as maintainers.
- Content submissions should be reviewed separately for provenance, copyright, redistribution rights, and publication suitability before they are merged into the public repo.

## Cross-Repository Role Policy

- `BiblionOCR-C++`: no developer-intake path; code changes are maintainer-governed.
- `BiblionOCR-Qt6`: developer-intake path is enabled through pull requests and reviewed membership approvals.
- `BiblionOCR`, `BiblionOCR-PyQt6`, and `BiblionOCR-C++`: content-creator intake is supported for approved content consumption/publication workflows.
- Content-creator intake does not automatically grant broad code write access.

## Membership Intake Mechanism

Repository membership is tracked through a GitHub-native approval path:

- Developer membership requests should be filed with the `Developer Membership Request` issue form.
- Content-creator membership requests should be filed with the `Content Creator Membership Request` issue form.
- Approved memberships should be recorded in `.github/membership-registry.json`.
- Membership-registry changes should happen by pull request so CODEOWNERS review and workflow validation both apply.

The registry is the backend record of which accounts were explicitly permitted, for which role, and under what access level.

## Authentication Expectations

- Use a personal GitHub account protected by MFA.
- If this project is moved under a GitHub organization, enforce organization-wide 2FA.
- Developers who receive repository write access should use the least privilege needed for their role.

## Developer Contributions

Developer contributions include changes such as:

- source code
- tests
- build scripts
- architecture documentation
- development documentation
- repository automation

By submitting a pull request for original work, you represent that:

- you have the right to contribute the material
- the contribution is compatible with the license and policy of the affected files
- you intend the contribution to be distributed under the same license terms that apply to the files you changed

For original BiblionOCR code, that normally means Apache-2.0 unless a different file- or directory-level notice applies.

## Required Pre-PR Checklist Policy

The full development checklist (including commit and resync operations) is an agent-owned operating routine.

Developer contributors use a PR-only intake path and do not execute the full checklist routine.

Required checklist:

- [docs/development/DEVELOPMENT_ROUTINE_CHECKLIST_ONE_PAGE.md](docs/development/DEVELOPMENT_ROUTINE_CHECKLIST_ONE_PAGE.md)

Policy requirements:

- full checklist execution is required for agent-managed implementation work
- commit and resync operations are agent-managed operations
- developers are limited to pull request generation for proposed changes
- UI lock-step checks are required whenever UI behavior/menu/actions changed
- workflow wizard policy gates must be verified for affected modules

## Module-Scoped Change-Set Workflow (Recommended)

For runtime/UI refactors that can regress behavior across modules, contributors should follow a module-scoped change-set workflow.

Workflow reference:

- [docs/development/CHANGESET_PROMPT_PACK_2026-08-07.md](docs/development/CHANGESET_PROMPT_PACK_2026-08-07.md)

Recommended operating pattern:

1. Work one module per change set unless maintainers explicitly request grouped rollout.
2. Keep Qt Designer lock-step: edit `Developer/QtDesignerUI/*.ui` source first, then regenerate paired `ViewController/**/*UI.py`.
3. Preserve existing custom context-menu defaults unless the change request explicitly says otherwise.
4. Run full-workspace Problems checks before clean claims, and report both full-workspace and in-scope counts.
5. Keep intentionally deferred modules out of scope until maintainers explicitly re-open them.

## Local Planning Docs (Do Not Commit)

Personal planning material that is useful to an individual maintainer but not intended as shared developer documentation should stay out of git.

Use these ignored locations for local-only planning assets:

1. `docs/development/local/`
2. `Developer/local/`

Examples of local-only material:

1. personal prompt packs and prompt experiments
2. private release-planning notes or legal-hygiene drafts
3. maintainer-only scratch checklists and working memos that are not ready for shared developer use

If a document benefits other developers, move it out of the local folders and commit it through normal review.

Maintainer review may block or request changes when a PR does not demonstrate checklist completion.

## Shared Cross-Platform Tooling Policy

If a development script is required by either Windows or Ubuntu development workflows, it must be treated as shared tooling and remain portable across branches.

Shared tooling requirements:

1. Place shared scripts in tracked repo paths (current standard: `Developer/utilities/`).
2. Register the script in `Developer/utilities/shared_tools_manifest.json`.
3. Keep shared tools out of ignored local-only paths.
4. Ensure `Developer/utilities/verify_shared_dev_tools.py` passes.

Local-only scripts may exist in ignored paths such as `Developer/local/`, but those scripts must not be prerequisites for branch sync, validation, CI, or routine development on either platform.

Policy reference:

- [docs/development/SHARED_DEV_TOOLS_POLICY.md](docs/development/SHARED_DEV_TOOLS_POLICY.md)

## PR Review Order And Exceptions

For non-Dependabot pull requests, required order is:

1. Agent review first.
2. Repository owner/maintainer review and approval second.

Dependabot exception:

- Dependabot pull requests may be processed through Resync by the agent.

## Content Creator Contributions

Content creator contributions include changes such as:

- written editorial material
- documentation intended for publication
- screenshots and promotional graphics
- photographs, illustrations, and other image assets
- audio or video assets
- OCR training or reference content

Content submissions require a higher review bar because copyright, trademark, privacy, and redistribution rights may differ from software licensing.

Before content is accepted, the contributor should be able to state:

- who created the content
- whether the content is fully original, adapted, or third-party
- what license or permission covers the content
- whether redistribution in a public GitHub repository is allowed
- whether attribution, notice retention, or downstream restrictions apply

See [CONTENT_POLICY.md](CONTENT_POLICY.md) for the required content standards.

Content-creator membership approvals should normally use `curated_intake` or `pull_request_only` access in `.github/membership-registry.json`. Broad write access is intentionally not the default path for this group.

## Inbound Rights Policy

This repository currently follows a practical inbound-equals-outbound model for accepted original contributions:

- code contributions are accepted under the license terms that apply to the modified files
- separately licensed third-party material remains under its original license
- content contributions should only be accepted when the repository has clear rights to publish and redistribute them

If the project later adopts a formal CLA or DCO workflow, that policy should be added here and enforced in pull requests.

## What Not to Submit

Do not submit:

- secrets, tokens, or credentials
- proprietary third-party code without redistribution rights
- licensed stock media unless the license explicitly allows public redistribution in this repository
- generated caches, local environment files, or machine-specific artifacts
- large binary assets that are not needed in the public repository

## Review Expectations

- Runtime code changes should be reviewed by a maintainer familiar with the affected subsystem.
- Security-sensitive changes should be reviewed before merge.
- Content and publication assets should be reviewed for provenance and public redistribution rights.
- Changes that affect licensing or policy should be reviewed carefully before merge.
- Pull requests should include checklist evidence aligned with [docs/development/DEVELOPMENT_ROUTINE_CHECKLIST_ONE_PAGE.md](docs/development/DEVELOPMENT_ROUTINE_CHECKLIST_ONE_PAGE.md).

## Recommended GitHub Settings

The repository owner should use GitHub controls that match this policy:

- branch protection on `master`
- pull-request review before merge
- required status check: `Enforce PR Checklist`
- required status check: `Branch Sync Visibility`
- required status check: `Validate Shared Dev Tools`
- least-privilege team access
- CODEOWNERS review for sensitive paths
- MFA for accounts with write access
- issue forms enabled for developer and content-creator membership intake
- membership approvals recorded in `.github/membership-registry.json`

## Related Documents

- [README.md](README.md)
- [LICENSE](LICENSE)
- [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md)
- [CONTENT_POLICY.md](CONTENT_POLICY.md)
- [docs/community/MEMBERSHIP.md](docs/community/MEMBERSHIP.md)
