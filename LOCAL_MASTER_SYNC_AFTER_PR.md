# Sync Local `master` From GitHub After PR Merge

Use this after `Biblion-Branch6` is merged into `master` on GitHub.

These examples are written for a Linux shell on the Jetson.
They assume the repository lives at `/home/jetson/Projects/BiblionOCR`.

If the repo is somewhere else on that machine, change the `cd` line accordingly.

## Recommended Safe Method

This keeps local `master` aligned with remote `master` and avoids accidental merge commits.

```bash
cd /home/jetson/Projects/BiblionOCR
git checkout master
git fetch origin --prune
git pull --ff-only origin master
```

## Why This Is Best

- `cd /home/jetson/Projects/BiblionOCR`
  Moves into the repository on the Jetson.
- `git checkout master`
  Moves you to the local `master` branch.
- `git fetch origin --prune`
  Updates your local knowledge of the remote branches and removes stale remote refs.
- `git pull --ff-only origin master`
  Fast-forwards local `master` only if it can be updated cleanly.
  It will fail instead of creating an accidental merge commit.

## Stronger Exact-Match Method

Use this only if you want local `master` to become an exact copy of remote `master`, and you are sure there is nothing local on `master` that you need to keep.

```bash
cd /home/jetson/Projects/BiblionOCR
git checkout master
git fetch origin --prune
git reset --hard origin/master
```

## Warning About `reset --hard`

`reset --hard` is destructive.
It discards local changes and local-only commits on `master`.
Do not use it unless you are certain.

## For This Repo

The safest normal flow is:

1. Merge `Biblion-Branch6` into `master` on GitHub by PR.
2. On the local machine, run:

```bash
cd /home/jetson/Projects/BiblionOCR
git checkout master
git fetch origin --prune
git pull --ff-only origin master
```

## Optional Cleanup After Merge

If the PR is merged and you no longer need `Biblion-Branch6`, you can clean it up.

### Delete local branch

```bash
cd /home/jetson/Projects/BiblionOCR
git branch -d Biblion-Branch6
```

### Delete remote branch

```bash
cd /home/jetson/Projects/BiblionOCR
git push origin --delete Biblion-Branch6
```

## If `origin` Does Not Exist Yet

If you see this:

```text
fatal: 'origin' does not appear to be a git repository
```

check the configured remotes first:

```bash
cd /home/jetson/Projects/BiblionOCR
git remote -v
```

If nothing is listed, add `origin`:

```bash
cd /home/jetson/Projects/BiblionOCR
git remote add origin https://github.com/preachermax/BiblionOCR.git
git remote -v
```

If `origin` exists but points to the wrong place, fix it:

```bash
cd /home/jetson/Projects/BiblionOCR
git remote set-url origin https://github.com/preachermax/BiblionOCR.git
git remote -v
```

After that, retry:

```bash
cd /home/jetson/Projects/BiblionOCR
git fetch origin --prune
```

## GitHub Authentication On The Jetson

Once `origin` points to GitHub, you still need GitHub credentials that work from the Jetson.

### Easiest HTTPS Path

Use the GitHub HTTPS remote:

```bash
cd /home/jetson/Projects/BiblionOCR
git remote set-url origin https://github.com/preachermax/BiblionOCR.git
git fetch origin --prune
```

GitHub will not accept your GitHub account password for command-line Git.
When prompted:

- username: your GitHub username
- password: use a GitHub Personal Access Token (PAT), not your normal GitHub password

If you want the Jetson to remember the token:

```bash
git config --global credential.helper store
```

Then the next successful authenticated Git command will save it locally in your home directory.

### Better Long-Term SSH Path

If you do not want to keep using HTTPS prompts, configure an SSH key on the Jetson:

```bash
ssh-keygen -t ed25519 -C "jetson@nano"
cat ~/.ssh/id_ed25519.pub
```

Add that public key to GitHub under SSH keys, then switch the remote:

```bash
cd /home/jetson/Projects/BiblionOCR
git remote set-url origin git@github.com:preachermax/BiblionOCR.git
ssh -T git@github.com
git fetch origin --prune
```

If the SSH test succeeds, future `fetch`, `pull`, and `push` commands can use the key without PAT prompts.

## If `pull --ff-only` Fails

That means local `master` has diverged from remote `master`.
In that case:

1. Stop.
2. Inspect `git status` and `git log --oneline --decorate --graph --all`.
3. Decide whether to preserve the local commits or force local `master` to match `origin/master`.

## Minimal Version

If you only want the short version, use this:

```bash
cd /home/jetson/Projects/BiblionOCR
git checkout master
git fetch origin --prune
git pull --ff-only origin master
```
