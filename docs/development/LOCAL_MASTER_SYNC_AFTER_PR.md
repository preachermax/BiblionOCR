# Sync Local `master` From GitHub After Upstream Update

Use this after `master` has been updated on GitHub and you want the Jetson checkout to match it.

These examples are written for a Linux shell on the Jetson.
They assume the repository lives at `~/Projects/BiblionOCR`.

If the terminal opens in your home directory, use `cd Projects/BiblionOCR`.
If the repo is somewhere else on that machine, change the `cd` line accordingly.

## Recommended Safe Method

This keeps local `master` aligned with remote `master` and avoids accidental merge commits.

```bash
cd Projects/BiblionOCR
git checkout master
git fetch origin --prune
git pull --ff-only origin master
```

## Why This Is Best

- `cd Projects/BiblionOCR`
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
cd Projects/BiblionOCR
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

1. Update `master` on GitHub, whether that happened through a PR merge or a reviewed merge from `development`.
2. On the Jetson, run:

```bash
cd Projects/BiblionOCR
git checkout master
git fetch origin --prune
git pull --ff-only origin master
```

## Optional Cleanup After Update

If the upstream work came from a local feature branch and you no longer need that branch on the Jetson, you can clean it up.

### Delete local branch

```bash
cd Projects/BiblionOCR
git branch -d YOUR_BRANCH_NAME
```

### Delete remote branch

```bash
cd Projects/BiblionOCR
git push origin --delete YOUR_BRANCH_NAME
```

## If `origin` Does Not Exist Yet

If you see this:

```text
fatal: 'origin' does not appear to be a git repository
```

check the configured remotes first:

```bash
cd Projects/BiblionOCR
git remote -v
```

If nothing is listed, add `origin`:

```bash
cd Projects/BiblionOCR
git remote add origin https://github.com/preachermax/BiblionOCR.git
git remote -v
```

If you already have a usable remote but it is named something else, rename it to `origin` instead of adding a duplicate.

For example, if the repo already shows `BiblionOCR`:

```bash
cd Projects/BiblionOCR
git remote rename BiblionOCR origin
git remote -v
```

If both `BiblionOCR` and `BiblionGitHub` exist, rename one of them to `origin` and remove the extra duplicate:

```bash
cd Projects/BiblionOCR
git remote rename BiblionOCR origin
git remote remove BiblionGitHub
git remote -v
```

If `origin` exists but points to the wrong place, fix it:

```bash
cd Projects/BiblionOCR
git remote set-url origin https://github.com/preachermax/BiblionOCR.git
git remote -v
```

After that, retry:

```bash
cd Projects/BiblionOCR
git fetch origin --prune
```

## GitHub Authentication On The Jetson

Once `origin` points to GitHub, you still need GitHub credentials that work from the Jetson.

### Easiest HTTPS Path

Use the GitHub HTTPS remote:

```bash
cd Projects/BiblionOCR
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

#### One-Time PAT Setup Flow

1. In a browser, sign in to GitHub.
2. Open Settings -> Developer settings -> Personal access tokens -> Tokens (classic).
3. Create a token with at least repo access for this repository.
4. Copy the token immediately. GitHub will not show it again.
5. Back on the Jetson, run:

```bash
git config --global credential.helper store
cd Projects/BiblionOCR
git fetch origin --prune
```

6. When Git prompts:

  - username: `preachermax`
  - password: paste the PAT

On Linux, the token paste may not echo any characters to the screen. That is normal.
Press Enter once after pasting.

If the token is accepted, future HTTPS fetch/pull/push commands should reuse the stored credential.

#### If A Bad HTTPS Credential Was Already Saved

If Git keeps reusing a bad token, remove the saved GitHub line from `~/.git-credentials`, then retry the PAT flow:

```bash
sed -i '/github.com/d' ~/.git-credentials
cd Projects/BiblionOCR
git fetch origin --prune
```

### Better Long-Term SSH Path

If you do not want to keep using HTTPS prompts, configure an SSH key on the Jetson:

```bash
ssh-keygen -t ed25519 -C "jetson@nano"
cat ~/.ssh/id_ed25519.pub
```

Add that public key to GitHub under SSH keys, then switch the remote:

```bash
cd Projects/BiblionOCR
git remote set-url origin git@github.com:preachermax/BiblionOCR.git
ssh -T git@github.com
git fetch origin --prune
```

If the SSH test succeeds, future `fetch`, `pull`, and `push` commands can use the key without PAT prompts.

#### One-Time SSH Setup Flow

1. On the Jetson, create the key if it does not already exist:

```bash
ssh-keygen -t ed25519 -C "jetson@nano"
```

2. Show the public key:

```bash
cat ~/.ssh/id_ed25519.pub
```

3. In a browser, sign in to GitHub.
4. Open Settings -> SSH and GPG keys -> New SSH key.
5. Paste the public key and save it.
6. This is correct even for a private repository. GitHub needs your public key so it can verify the matching private key on the Jetson. The public key does not make the repository public, and the private key stays only on the Jetson.
7. Back on the Jetson, test GitHub SSH access:

```bash
ssh -T git@github.com
```

8. If that succeeds, switch this repo to SSH and retry Git:

```bash
cd Projects/BiblionOCR
git remote set-url origin git@github.com:preachermax/BiblionOCR.git
git fetch origin --prune
```

SSH is usually the better long-term Jetson setup because it avoids repeated HTTPS token prompts.

#### What "Public SSH Key" Means Here

- `~/.ssh/id_ed25519.pub` is the public key file. This is the one you copy into GitHub.
- `~/.ssh/id_ed25519` is the private key file. Do not upload this file anywhere.
- GitHub stores the public key and uses it to verify that your Jetson holds the matching private key.
- A public key on GitHub is normal for both public and private repositories.

## If `pull --ff-only` Fails

That means local `master` has diverged from remote `master`.
In that case:

1. Stop.
2. Inspect `git status` and `git log --oneline --decorate --graph --all`.
3. Decide whether to preserve the local commits or force local `master` to match `origin/master`.

## Minimal Version

If you only want the short version, use this:

```bash
cd Projects/BiblionOCR
git checkout master
git fetch origin --prune
git pull --ff-only origin master
```
