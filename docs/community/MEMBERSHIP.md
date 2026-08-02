# Membership Approval Workflow

This document describes the operational path for permitting repository membership for developers and content creators.

## Purpose

BiblionOCR distinguishes between people who need code-facing repository access and people who need an approved path for content submission.

That distinction should be enforced by a reviewed backend record, not by informal chat or memory.

## Backend Components

The membership mechanism uses these repository-controlled components:

- `.github/ISSUE_TEMPLATE/developer-membership.yml`
- `.github/ISSUE_TEMPLATE/content-creator-membership.yml`
- `.github/membership-registry.json`
- `.github/workflows/validate-membership-registry.yml`

## Roles

- `developer`: code, tests, tooling, architecture, or engineering documentation contributors
- `content_creator`: editorial, design, media, dataset, or publication-facing contributors
- `maintainer`: trusted repository operators with elevated stewardship responsibility

## Access Levels

- `curated_intake`: content arrives through a reviewed intake path rather than broad repo write access
- `pull_request_only`: contributions happen through pull requests only
- `triage`: limited GitHub management access without direct code-writing authority
- `write`: normal write access for trusted developers
- `maintain`: maintainer-grade repository management access
- `admin`: repository administration access

## Approval Path

1. A contributor opens the matching GitHub issue form.
2. A maintainer reviews identity, contribution fit, and policy requirements.
3. If approved, a maintainer updates `.github/membership-registry.json` in a pull request.
4. The registry validation workflow checks the entry shape and role-to-access rules.
5. After review, the pull request is merged and any matching GitHub permission change can be applied.

## Registry Entry Requirements

Each approved member entry should include:

- `github_username`
- `role`
- `access_level`
- `status`
- `approved_by`
- `approved_at`
- `request_issue`

`request_issue` should point back to the GitHub issue that captured the original request.

## Role Guardrails

- `content_creator` entries should only use `curated_intake` or `pull_request_only`
- `developer` entries should not use `curated_intake`
- `maintainer` entries should only use `maintain` or `admin`

These rules are validated by the workflow in `.github/workflows/validate-membership-registry.yml`.

## Recommended Operational Rule

Do not grant GitHub access first and document it later.

The registry update and the permission decision should be part of the same reviewed change sequence so the public repository has an auditable approval trail.

## Related Documents

- [README.md](README.md)
- [../../CONTRIBUTING.md](../../CONTRIBUTING.md)
- [../../CONTENT_POLICY.md](../../CONTENT_POLICY.md)