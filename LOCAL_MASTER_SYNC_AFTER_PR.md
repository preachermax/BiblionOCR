# Sync Local `master` From GitHub After PR Merge

Use this after `Biblion-Branch6` is merged into `master` on GitHub.

These examples are written for a Linux shell on the Jetson.
They assume the repository lives at `/home/max/Projects/BiblionOCR`.

If the repo is somewhere else on that machine, change the `cd` line accordingly.

## Recommended Safe Method

This keeps local `master` aligned with remote `master` and avoids accidental merge commits.

```bash
cd /home/max/Projects/BiblionOCR
git checkout master
git fetch origin --prune
git pull --ff-only origin master
```

## Why This Is Best

- `cd /home/max/Projects/BiblionOCR`
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
cd /home/max/Projects/BiblionOCR
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
cd /home/max/Projects/BiblionOCR
git checkout master
git fetch origin --prune
git pull --ff-only origin master
```

## Optional Cleanup After Merge

If the PR is merged and you no longer need `Biblion-Branch6`, you can clean it up.

### Delete local branch

```bash
cd /home/max/Projects/BiblionOCR
git branch -d Biblion-Branch6
```

### Delete remote branch

```bash
cd /home/max/Projects/BiblionOCR
git push origin --delete Biblion-Branch6
```

## If `pull --ff-only` Fails

That means local `master` has diverged from remote `master`.
In that case:

1. Stop.
2. Inspect `git status` and `git log --oneline --decorate --graph --all`.
3. Decide whether to preserve the local commits or force local `master` to match `origin/master`.

## Minimal Version

If you only want the short version, use this:

```bash
cd /home/max/Projects/BiblionOCR
git checkout master
git fetch origin --prune
git pull --ff-only origin master
```
