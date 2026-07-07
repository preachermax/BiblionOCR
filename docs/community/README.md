# Community and Contribution Guide

This section is the documentation-library entry point for repository participation, contribution workflow, and public-submission rules.

## Purpose

BiblionOCR distinguishes between two contributor groups:

- developers, who contribute code, tests, architecture, and engineering documentation
- content creators, who contribute editorial, visual, audio, video, dataset, or publication-oriented material

These groups do not follow the same intake path or review standard.

## Primary Repository Policies

The authoritative repo-level policies currently live at the repository root:

- [CONTRIBUTING.md](../../CONTRIBUTING.md)
- [CONTENT_POLICY.md](../../CONTENT_POLICY.md)
- [LICENSE](../../LICENSE)
- [THIRD_PARTY_LICENSES.md](../../THIRD_PARTY_LICENSES.md)

## Working Model

- Developers should contribute through pull requests and normal repository review.
- Content creators should only submit material that the project has clear rights to publish and redistribute.
- Policy, licensing, and release-sensitive areas should remain under maintainer review.
- Membership intake now runs through GitHub issue forms plus the reviewed registry in `.github/membership-registry.json`.

## GitHub Access Guidance

The intended GitHub-side model is:

- least-privilege write access for developers
- review-gated changes for protected branches
- no broad write access for content-only contributors
- MFA for accounts with repository write access

## Membership Backend

The repository now has a concrete backend path for contributor membership:

- developer requests use the `Developer Membership Request` issue form
- content-creator requests use the `Content Creator Membership Request` issue form
- approved accounts are recorded in `.github/membership-registry.json`
- registry changes are validated by GitHub Actions and should remain under maintainer review

See [MEMBERSHIP.md](MEMBERSHIP.md) for the approval workflow.

## Documentation Relationship

Use this directory when documenting participation rules, community process, contributor expectations, or future governance material.

Use the repository-root policy files when you need the actual enforceable repo-facing rules.