# Shared Development Tools Policy

## Problem

Windows and Ubuntu development can diverge if required scripts live only in ignored local paths.

## Rule

If a script is required by either platform for routine development, validation, or branch synchronization, that script must:

1. Live in `Developer/utilities/` (or another tracked shared path).
2. Be listed in `Developer/utilities/shared_tools_manifest.json`.
3. Be committed to `master` through a pull request.
4. Not be gitignored.

## Local-Only Tools

- Local experiments belong in ignored paths such as `Developer/local/`.
- Local-only tooling must never be required for Ubuntu or Windows branch workflows.

## Automation

This policy is enforced by:

- Script: `Developer/utilities/verify_shared_dev_tools.py`
- CI workflow: `.github/workflows/validate-shared-dev-tools.yml`

The CI check fails if a required shared tool is missing, untracked, or ignored.

## Practical Branch Guidance

- Shared tooling becomes available on Ubuntu once merged to `master` and pulled there.
- Do not rely on `.vscode` tasks as the distribution mechanism, since local editor settings may be ignored or machine-specific.
- Prefer CLI entry points in tracked scripts and document them in repo docs.
