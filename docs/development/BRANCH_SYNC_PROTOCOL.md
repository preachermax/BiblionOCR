# Branch Sync Protocol (Windows + Ubuntu)

## Objective

Keep `origin/master` as the single source of truth while ensuring both development branches know each other's current delta.

## Branches

- Source of truth: `origin/master`
- Windows development: `origin/windows-development`
- Ubuntu development: `origin/ubuntu_development`

## Daily Cadence

1. Run the branch sync report.
2. Review `docs/development/BRANCH_SYNC_STATUS.md`.
3. If either development branch is behind `master`, reconcile before major new work.
4. If both dev branches have unique commits, schedule an explicit merge or cherry-pick decision and note ownership.

## Commands

Cross-platform report command:

```bash
python Developer/utilities/branch_sync_report.py
```

Windows task entry:

- `git-branch-sync-refresh`

## Merge Discipline

- Create feature commits on the platform-specific development branch.
- Open PRs to `master`.
- After `master` changes, refresh both development branches from `master` intentionally.
- Avoid hidden drift: do not allow cross-branch divergence to grow without an owner and a date.

## Decision Rules

- `Ahead of master > 0`: branch has pending work not yet in source of truth.
- `Behind master > 0`: branch must be refreshed before risky refactors.
- Both branches unique at the same time: perform a reconciliation review before release-critical tasks.

## Realistic Policy Limits

The CI policy is intentionally soft-first so normal platform-specific iteration is not blocked.

- Warning threshold, windows behind master: 15 commits
- Warning threshold, ubuntu behind master: 60 commits
- Warning threshold, cross-branch unique commits: 120 commits
- Critical threshold, windows behind master: 40 commits
- Critical threshold, ubuntu behind master: 150 commits
- Critical threshold, cross-branch unique commits: 260 commits

Behavior:

- Warning state: workflow stays green and posts visibility notes in PR comments.
- Critical state: workflow fails and requires explicit reconciliation before merge.
