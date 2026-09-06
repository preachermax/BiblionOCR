# Windows 10 Repo Backup and Reclone (master)

Status: operational runbook
Audience: maintainer/operator
Shell: Windows PowerShell

## 1. Purpose

Safely preserve the current local `BiblionOCR` working tree on Windows 10, then create a clean clone aligned to `origin/master`.

This sequence is designed to be reversible.

## 2. Preconditions

- Git is installed and available in PowerShell.
- You know your local repository parent path.
- You are targeting this repository remote:

```text
https://github.com/preachermax/BiblionOCR.git
```

## 3. Set Variables

Open PowerShell and set these values first:

```powershell
$RepoParent = "C:\Users\<you>\Projects"
$RepoName   = "BiblionOCR"
$RepoPath   = Join-Path $RepoParent $RepoName
$Stamp      = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupPath = Join-Path $RepoParent "${RepoName}_backup_$Stamp"
```

## 4. Full Folder Backup (Current Local Repo)

```powershell
if (!(Test-Path $RepoPath)) { throw "Repo not found: $RepoPath" }

robocopy $RepoPath $BackupPath /MIR /R:1 /W:1 /XD ".git\objects\pack\tmp_pack_*" | Out-Null
Write-Host "Backup folder created: $BackupPath"
```

Notes:

- This copies tracked files, untracked files, local scripts, and generated artifacts.
- `/MIR` mirrors content exactly inside the destination backup folder.

## 5. Capture Git Recovery Artifacts

Run these in the original repo before reclone:

```powershell
Set-Location $RepoPath

git status --short                  | Out-File "$BackupPath\git_status_short.txt" -Encoding utf8
git status                          | Out-File "$BackupPath\git_status_full.txt"  -Encoding utf8
git diff                            | Out-File "$BackupPath\git_diff_unstaged.patch" -Encoding utf8
git diff --staged                   | Out-File "$BackupPath\git_diff_staged.patch"   -Encoding utf8
git ls-files --others --exclude-standard | Out-File "$BackupPath\git_untracked_files.txt" -Encoding utf8
git rev-parse HEAD                  | Out-File "$BackupPath\git_head_commit.txt" -Encoding utf8
git branch -vv                      | Out-File "$BackupPath\git_branches.txt" -Encoding utf8
```

Optional all-refs bundle:

```powershell
git bundle create "$BackupPath\repo_all_refs.bundle" --all
```

## 6. Move Existing Repo Aside and Clone Fresh

```powershell
Set-Location $RepoParent

Rename-Item $RepoPath "${RepoName}_pre_reclone_$Stamp"

git clone https://github.com/preachermax/BiblionOCR.git $RepoName
Set-Location (Join-Path $RepoParent $RepoName)
git checkout master
git pull --ff-only origin master
```

## 7. Verify Alignment

```powershell
git status --short
git rev-parse HEAD
git rev-parse origin/master
```

Expected:

- `git status --short` is empty.
- `HEAD` and `origin/master` hashes match.

## 8. Recovery / Rollback

If needed, recover from:

- `$BackupPath`
- `${RepoName}_pre_reclone_$Stamp`

Do not bulk-copy everything back into the fresh clone unless intentional.

## 9. Completion Criteria

- Backup folder exists and contains git artifact files.
- Fresh clone is present at `$RepoPath`.
- Fresh clone `master` is clean and aligned with `origin/master`.
