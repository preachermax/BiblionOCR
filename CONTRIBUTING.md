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

## Recommended GitHub Settings

The repository owner should use GitHub controls that match this policy:

- branch protection on `master`
- pull-request review before merge
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