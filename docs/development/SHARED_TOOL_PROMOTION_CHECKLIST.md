# Shared Tool Promotion Checklist

Use this checklist when a script moves from local-only or experimental use into required cross-platform development workflow.

## Promotion Trigger

Promote a tool when any of these become true:

1. The script is required for routine development tasks on Windows or Ubuntu.
2. The script is required for branch synchronization, validation, CI, or release operations.
3. The script is referenced by team docs as an expected command for contributors.

## Required Promotion Steps

1. Move the script into a tracked shared path.
2. Confirm the script is platform-neutral (path handling, shell assumptions, Python version compatibility).
3. Add or update usage docs in `docs/development/`.
4. Register the script in `Developer/utilities/shared_tools_manifest.json` with a clear description and platform list.
5. Run shared-tool policy validation locally:

```bash
python Developer/utilities/verify_shared_dev_tools.py --repo .
```

1. If the script changes branch coordination behavior, run branch sync visibility check:

```bash
python Developer/utilities/branch_sync_report.py --repo .
```

1. Include validation evidence in the pull request.
1. Merge through pull request to `master`.
1. Refresh both development branches from updated `master`.

## Non-Promotable Cases

Do not promote scripts that are:

1. machine-specific (hard-coded local-only paths or credentials)
2. temporary one-off investigations
3. private maintainer scratch tooling that is not required for shared workflow

These belong in local ignored paths such as `Developer/local/`.

## Pull Request Checklist Additions

When promoting a tool, the PR should include:

1. Link to this checklist.
2. Confirmation that manifest and validator passed.
3. Notes on any Ubuntu/Windows behavior differences tested.
4. Any follow-up tasks needed before making the tool mandatory.

## Ownership

The contributor promoting the tool owns first-pass compatibility checks.
The maintainer reviewing the pull request owns policy compliance and merge readiness.
