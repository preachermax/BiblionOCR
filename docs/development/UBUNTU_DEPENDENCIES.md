# Ubuntu Dependencies For BiblionOCR

Use this on a fresh Ubuntu machine when you want the practical package set for BiblionOCR development, OCR work, and scanner support.

Assumptions:
- target distro: Ubuntu 24
- target repo path: `~/Projects/BiblionOCR`
- package manager: `apt`

## 1. Base System Update

```bash
sudo apt update
sudo apt upgrade -y
sudo apt autoremove -y
```

## 2. Core Developer Tools

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
- `ripgrep`: fast repo searching
- `build-essential`, `pkg-config`, `cmake`: native build support
- `tree`, `jq`, `htop`: inspection and debugging support

## 3. Python Tooling

```bash
sudo apt install -y \
  python3 \
  python3-venv \
  python3-pip \
  python3-dev \
  pipx
```

Optional:

```bash
python3 -m pip install --upgrade pip
```

## 4. Qt / PyQt5 Tooling

These packages matter when editing `.ui` files and regenerating `*UI.py` files.

```bash
sudo apt install -y \
  python3-pyqt5 \
  pyqt5-dev-tools \
  qttools5-dev-tools \
  qttools5-dev \
  qtbase5-dev
```

Quick checks:

```bash
which pyuic5
which pyrcc5
which designer
```

## 5. OCR / Imaging / Scanner Packages

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

Optional but useful:

```bash
sudo apt install -y \
  fontforge \
  gimp \
  libreoffice \
  simple-scan
```

Notes:
- `fontforge` and `gimp` are the two optional third-party open-source desktop tools currently expected by this repo's setup guidance
- `sane-airscan` is useful for AirScan / eSCL network-capable devices
- on Jetson USB-only testing, disabling `airscan` requires moving its file out of `/etc/sane.d/dll.d/`; renaming it to `airscan.disabled` inside that directory does not disable it

Additional Python-facing Ubuntu packages currently expected by the desktop runtime and support tools:

```bash
sudo apt install -y \
  python3-sane \
  python3-scapy \
  python3-zeroconf \
  python3-fontforge \
  python3-enchant \
  python3-reportlab \
  enchant-2
```

Why these matter:
- `python3-sane`: Python bindings for scanner access
- `python3-scapy` and `python3-zeroconf`: network scanner discovery and related tooling
- `python3-fontforge`: font-editing automation used by glyph/font workflows
- `python3-enchant` and `enchant-2`: spelling/dictionary bindings used by text tooling
- `python3-reportlab`: PDF/report generation support used by auxiliary workflows

## 6. GitHub Authentication Helpers

Simple HTTPS credential storage:

```bash
git config --global credential.helper store
```

Better long-term SSH setup:

```bash
ssh-keygen -t ed25519 -C "ubuntu24"
cat ~/.ssh/id_ed25519.pub
ssh -T git@github.com
```

## 7. Optional First Validation

Check the Python UI toolchain:

```bash
python3 -m py_compile \
  ~/Projects/BiblionOCR/ViewController/0-MainUI/MyServer.py \
  ~/Projects/BiblionOCR/ViewController/0-MainUI/MyServerUI.py \
  ~/Projects/BiblionOCR/ViewController/0-MainUI/MyScanner.py \
  ~/Projects/BiblionOCR/ViewController/0-MainUI/MyScannerUI.py
```

## 8. Companion Script

The companion install script lives beside this document:

```text
docs/development/UbuntuDependencies.sh
```

Run it with:

```bash
cd ~/Projects/BiblionOCR
bash docs/development/UbuntuDependencies.sh
```

What the script does, in order:
- updates and upgrades the Ubuntu package set
- installs the core Ubuntu, Python, Qt, OCR, and scanner packages used by this repo
- installs the Ubuntu Python bindings required by the current scanner/network/font/text support stack
- creates a repo-local virtual environment at `.venv` with system site packages enabled
- upgrades `pip` inside that virtual environment
- installs the bundled Image Editor Python requirements from `ViewController/1-PreProcess/ImageEditor/Image-Editor-main/requirements.txt`
- installs `docs/website` npm dependencies when `node` and `npm` are already present with a sufficiently new Node.js version

Useful post-install import probe:

```bash
python3 - <<'PY'
import enchant
import fontforge
import reportlab
import sane
import scapy
import zeroconf
print('ubuntu runtime imports ok')
PY
```

After the script completes, activate the virtual environment with:

```bash
cd ~/Projects/BiblionOCR
source .venv/bin/activate
```