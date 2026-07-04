# Ubuntu 24 Developer Tools And BiblionOCR Restore

This note is for a clean Ubuntu 24 boot drive where you want a usable developer machine and a local BiblionOCR checkout that matches `origin/master` on GitHub.

Assumptions:
- target local repo path: `~/Projects/BiblionOCR`
- GitHub remote: `https://github.com/preachermax/BiblionOCR.git`
- desired exact branch: `master`

## 1. Base System Update

```bash
sudo apt update
sudo apt upgrade -y
sudo apt autoremove -y
```

## 2. Core Developer Tools

These are the general tools worth having on a fresh Ubuntu 24 development drive.

```bash
sudo apt install -y \
  git \
  curl \
  wget \
  build-essential \
  pkg-config \
  cmake \
  make \
  unzip \
  zip \
  tree \
  ripgrep \
  jq \
  htop \
  nano \
  vim
```

What these are for:
- `git`: clone, fetch, reset, branch work
- `ripgrep`: fast file/text searching
- `build-essential`, `pkg-config`, `cmake`: native build support when Python packages need compilation
- `tree`, `jq`, `htop`: practical inspection/debug tools

## 3. Python Tooling

```bash
sudo apt install -y \
  python3 \
  python3-venv \
  python3-pip \
  python3-dev \
  pipx
```

Optional pip upgrade:

```bash
python3 -m pip install --upgrade pip
```

## 4. Qt / PyQt5 Tools

These matter for BiblionOCR because you are editing `.ui` files and regenerating `*UI.py` files.

```bash
sudo apt install -y \
  python3-pyqt5 \
  pyqt5-dev-tools \
  qttools5-dev-tools \
  qttools5-dev \
  qtbase5-dev
```

Quick check:

```bash
which pyuic5
which pyrcc5
which designer
```

## 5. OCR / Imaging / Scanner Packages

Install these if you want the machine to be useful for OCR and flatbed/network scanning work.

```bash
sudo apt install -y \
  tesseract-ocr \
  tesseract-ocr-eng \
  tesseract-ocr-grc \
  tesseract-ocr-lat \
  sane-utils \
  libsane1 \
  sane-airscan \
  imagemagick
```

Optional but often useful:

```bash
sudo apt install -y \
  gimp \
  libreoffice \
  simple-scan
```

Notes:
- `sane-airscan` is useful for AirScan / eSCL network-capable devices.

## 6. GitHub Authentication

### Simple HTTPS path

```bash
git config --global credential.helper store
```

Then when Git prompts:
- username: your GitHub username
- password: use a GitHub Personal Access Token, not your GitHub password

### Better long-term SSH path

```bash
ssh-keygen -t ed25519 -C "ubuntu24"
cat ~/.ssh/id_ed25519.pub
```

Add that public key to GitHub, then test:

```bash
ssh -T git@github.com
```

If you want the repo remote to use SSH instead of HTTPS:

```bash
git remote set-url origin git@github.com:preachermax/BiblionOCR.git
```

## 7. Fresh Clone That Matches `origin/master`

If the repo does not exist yet on this Ubuntu drive:

```bash
mkdir -p ~/Projects
cd ~/Projects
git clone https://github.com/preachermax/BiblionOCR.git
cd BiblionOCR
git checkout master
git fetch origin --prune
git reset --hard origin/master
```

That gives you a local `master` that matches `origin/master`.

## 8. Force An Existing Local Repo To Match `origin/master`

Use this only if you want the local checkout to become an exact working copy of remote `master` and you do not need local changes.

```bash
cd ~/Projects/BiblionOCR
git remote -v
git remote set-url origin https://github.com/preachermax/BiblionOCR.git
git fetch origin --prune
git checkout master
git reset --hard origin/master
git clean -fd
```

What this does:
- `git fetch origin --prune`: updates remote refs and removes stale ones
- `git checkout master`: puts you on local `master`
- `git reset --hard origin/master`: makes tracked files match GitHub `origin/master`
- `git clean -fd`: removes untracked files and directories

Warning:
- `git reset --hard` is destructive for tracked local changes
- `git clean -fd` is destructive for untracked files/directories
- do not run those if there is anything local you still need

If you also want ignored files removed, that is a stronger cleanup:

```bash
git clean -fdx
```

Only use `-fdx` if you truly want the working tree stripped down to the Git-tracked state.

## 9. Verify The Repo Matches GitHub

```bash
cd ~/Projects/BiblionOCR
git status
git branch -vv
git remote -v
git rev-parse HEAD
git rev-parse origin/master
```

A good result is:
- `git status` shows a clean working tree
- `git rev-parse HEAD` equals `git rev-parse origin/master`

## 10. Optional First BiblionOCR Checks

Syntax/parse check for the main scan modules:

```bash
cd ~/Projects/BiblionOCR
python3 -m py_compile \
  ViewController/0-MainUI/MyServer.py \
  ViewController/0-MainUI/MyServerUI.py \
  ViewController/0-MainUI/MyScanner.py \
  ViewController/0-MainUI/MyScannerUI.py
```

Launch checks:

```bash
cd ~/Projects/BiblionOCR
python3 ViewController/0-MainUI/MyServer.py
```

```bash
cd ~/Projects/BiblionOCR
python3 ViewController/0-MainUI/MyScanner.py
```

## 11. Recommended Working Habit On Ubuntu 24

For this repo, the practical recovery path is still terminal-first:
- keep the repo under `~/Projects/BiblionOCR`
- use `git fetch origin --prune` frequently
- use `git pull --ff-only origin master` for normal safe updates
- use `git reset --hard origin/master` only when you intentionally want exact remote state

Normal safe update flow:

```bash
cd ~/Projects/BiblionOCR
git checkout master
git fetch origin --prune
git pull --ff-only origin master
```
