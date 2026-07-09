#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DEFAULT_PROJECT_ROOT="${REPO_ROOT}"
PROJECT_ROOT="${DEFAULT_PROJECT_ROOT}"
REPO_URL="https://github.com/preachermax/BiblionOCR.git"
REPO_BRANCH="master"
CLONE_IF_MISSING=0

CORE_PACKAGES=(
  git
  curl
  wget
  build-essential
  pkg-config
  cmake
  make
  unzip
  zip
  tree
  ripgrep
  jq
  htop
  nano
  vim
)

PYTHON_PACKAGES=(
  python3
  python3-venv
  python3-pip
  python3-dev
  pipx
)

QT_PACKAGES=(
  python3-pyqt5
  pyqt5-dev-tools
  qttools5-dev-tools
  qttools5-dev
  qtbase5-dev
)

OCR_PACKAGES=(
  tesseract-ocr
  tesseract-ocr-eng
  tesseract-ocr-grc
  tesseract-ocr-lat
  sane-utils
  libsane1
  sane-airscan
  imagemagick
  fontforge
  gimp
  enchant-2
)

PYTHON_RUNTIME_PACKAGES=(
  python3-sane
  python3-fontforge
  python3-opencv
  python3-numpy
  python3-pandas
  python3-enchant
  python3-pil
  python3-requests
  python3-reportlab
  python3-scapy
  python3-scipy
  python3-tifffile
  python3-zeroconf
  libgl1
  libglib2.0-0
)

PIP_PACKAGES=(
  imutils
  pytesseract
  qimage2ndarray
  sqlalchemy
  tiffcapture
)

log() {
  printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Options:
  --project-root PATH   Install or clone into PATH
  --clone               Clone ${REPO_URL} into PATH if PATH does not exist
  --repo-url URL        Override the git remote used with --clone
  --branch NAME         Override the branch used with --clone
  --help                Show this help text

Examples:
  ./launchers/install-biblionocr-ubuntu24.sh
  ./launchers/install-biblionocr-ubuntu24.sh --project-root ~/Projects/BiblionOCR --clone
EOF
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --project-root)
        PROJECT_ROOT="$2"
        shift 2
        ;;
      --clone)
        CLONE_IF_MISSING=1
        shift
        ;;
      --repo-url)
        REPO_URL="$2"
        shift 2
        ;;
      --branch)
        REPO_BRANCH="$2"
        shift 2
        ;;
      --help|-h)
        usage
        exit 0
        ;;
      *)
        printf 'Unknown argument: %s\n\n' "$1" >&2
        usage >&2
        exit 1
        ;;
    esac
  done
}

ensure_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf 'Missing required command: %s\n' "$1" >&2
    exit 1
  fi
}

install_apt_packages() {
  local -a packages=("$@")
  sudo apt install -y "${packages[@]}"
}

ensure_project_checkout() {
  if [[ -d "${PROJECT_ROOT}/.git" ]]; then
    return
  fi

  if [[ -e "${PROJECT_ROOT}" && ! -d "${PROJECT_ROOT}/.git" ]]; then
    printf 'Project root exists but is not a git checkout: %s\n' "${PROJECT_ROOT}" >&2
    exit 1
  fi

  if [[ ${CLONE_IF_MISSING} -ne 1 ]]; then
    printf 'Project root does not exist: %s\n' "${PROJECT_ROOT}" >&2
    printf 'Re-run with --clone to create a fresh checkout.\n' >&2
    exit 1
  fi

  log "Cloning ${REPO_URL} (${REPO_BRANCH}) into ${PROJECT_ROOT}"
  mkdir -p "$(dirname "${PROJECT_ROOT}")"
  git clone --branch "${REPO_BRANCH}" --single-branch "${REPO_URL}" "${PROJECT_ROOT}"
}

main() {
  parse_args "$@"

  ensure_command sudo
  ensure_command apt
  ensure_command python3

  export DEBIAN_FRONTEND=noninteractive

  PROJECT_ROOT="$(realpath -m "${PROJECT_ROOT}")"
  VENV_DIR="${PROJECT_ROOT}/.venv"

  log "Updating Ubuntu package metadata"
  sudo apt update

  log "Installing core developer packages"
  install_apt_packages "${CORE_PACKAGES[@]}"

  ensure_project_checkout

  log "Installing Python tooling"
  install_apt_packages "${PYTHON_PACKAGES[@]}"

  log "Installing Qt and PyQt5 tooling"
  install_apt_packages "${QT_PACKAGES[@]}"

  log "Installing OCR, scanner, and imaging packages"
  install_apt_packages "${OCR_PACKAGES[@]}"

  log "Installing Python runtime packages provided by Ubuntu"
  install_apt_packages "${PYTHON_RUNTIME_PACKAGES[@]}"

  log "Creating or refreshing virtual environment at ${VENV_DIR}"
  python3 -m venv --system-site-packages "${VENV_DIR}"

  # shellcheck disable=SC1091
  . "${VENV_DIR}/bin/activate"

  log "Upgrading pip tooling inside the virtual environment"
  python -m pip install --upgrade pip setuptools wheel

  log "Installing Python packages not covered by Ubuntu packages"
  python -m pip install "${PIP_PACKAGES[@]}"

  log "Running quick dependency checks"
  python - <<'PY'
import importlib.util
import shutil
import sys

modules = [
    "PyQt5",
    "cv2",
    "enchant",
    "fontforge",
    "imutils",
    "numpy",
    "pandas",
    "PIL",
    "pytesseract",
    "qimage2ndarray",
    "requests",
    "reportlab",
    "sane",
    "scapy",
    "scipy",
    "sqlalchemy",
    "tiffcapture",
    "tifffile",
    "zeroconf",
]

missing = [name for name in modules if importlib.util.find_spec(name) is None]
if missing:
    print("Missing Python modules:", ", ".join(missing), file=sys.stderr)
    sys.exit(1)

if shutil.which("tesseract") is None:
    print("tesseract executable not found in PATH", file=sys.stderr)
    sys.exit(1)

print("Python module imports and tesseract lookup succeeded.")
PY

  log "Running quick syntax checks for main entry points"
  (
    cd "${PROJECT_ROOT}"
    python -m py_compile \
      ViewController/0-MainUI/MyServer.py \
      ViewController/0-MainUI/MyServerUI.py \
      ViewController/0-MainUI/MyScanner.py \
      ViewController/0-MainUI/MyScannerUI.py
  )

  log "BiblionOCR Ubuntu 24 dependency installation completed"
  printf '\nNext steps:\n'
  printf '  source %s/bin/activate\n' "${VENV_DIR}"
  printf '  cd %s\n' "${PROJECT_ROOT}"
  printf '  python ViewController/0-MainUI/MyServer.py\n'
}

main "$@"