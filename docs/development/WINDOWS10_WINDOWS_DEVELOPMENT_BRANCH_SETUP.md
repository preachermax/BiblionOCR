# Windows 10 Branch Setup: windows-development

Status: operational runbook
Audience: maintainer/operator
Shell: Windows PowerShell

## 1. Purpose

After a clean reclone on Windows 10, create and align a local `windows-development` branch so it mirrors the intended Ubuntu development branch strategy.

## 2. Preconditions

- Fresh clone already completed and aligned to `origin/master`.
- You are inside local `BiblionOCR` repository on Windows 10.

## 3. Enter Repository and Refresh Remotes

```powershell
$RepoParent = "C:\Users\<you>\Projects"
$RepoName   = "BiblionOCR"
Set-Location (Join-Path $RepoParent $RepoName)

git fetch --all --prune
```

## 4. Inspect Available Remote Branches

```powershell
git branch -r
```

Use this to confirm whether `origin/ubuntu-development` exists.

## 5. Create or Reset Local windows-development

Two common modes are provided below.

### Mode A: Mirror `origin/master` baseline

Use this if your Windows development lane should begin from the current production baseline.

```powershell
if (git show-ref --verify --quiet refs/heads/windows-development) {
  git checkout windows-development
  git reset --hard origin/master
} else {
  git checkout -b windows-development origin/master
}
```

### Mode B: Mirror `origin/ubuntu-development` baseline

Use this if your Windows lane should start from Ubuntu dev parity.

```powershell
if (git show-ref --verify --quiet refs/heads/windows-development) {
  git checkout windows-development
  git reset --hard origin/ubuntu-development
} else {
  git checkout -b windows-development origin/ubuntu-development
}
```

## 6. Push and Track Remote windows-development

```powershell
git push -u origin windows-development
```

This creates (or updates) remote `origin/windows-development` and sets upstream tracking.

## 7. Verify Parity State

```powershell
git status --short
git branch -vv
git rev-parse HEAD
```

Optional explicit comparison to target baseline:

```powershell
# Compare against master baseline
git rev-parse origin/master

# Or compare against ubuntu-development baseline
git rev-parse origin/ubuntu-development
```

## 8. Ongoing Sync Routine (Windows Lane)

When you want to re-align `windows-development` to chosen baseline:

```powershell
git fetch --all --prune
git checkout windows-development

# pick one baseline:
# git reset --hard origin/master
# git reset --hard origin/ubuntu-development

git push --force-with-lease origin windows-development
```

Use `--force-with-lease` only when branch history rewrite is intentional.

## 9. Completion Criteria

- Local branch `windows-development` exists.
- Upstream is set to `origin/windows-development`.
- Branch head is aligned to the chosen baseline (`origin/master` or `origin/ubuntu-development`).
