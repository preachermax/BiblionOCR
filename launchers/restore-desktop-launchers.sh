#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARGET_HOME="${HOME}"
APPS_DIR="${TARGET_HOME}/.local/share/applications"
DESKTOP_DIR="${TARGET_HOME}/Desktop"

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Restore BiblionOCR desktop launchers for the current machine by rewriting
hardcoded repo paths in bundled .desktop files and installing them to:
  - ~/.local/share/applications
  - ~/Desktop

Options:
  --repo-root PATH      Override repository root (default: ${REPO_ROOT})
  --home PATH           Override target home directory (default: ${TARGET_HOME})
  --no-desktop-copy     Skip installing launchers to ~/Desktop
  --help                Show this help text
EOF
}

COPY_TO_DESKTOP=1
while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-root)
      REPO_ROOT="$2"
      shift 2
      ;;
    --home)
      TARGET_HOME="$2"
      shift 2
      ;;
    --no-desktop-copy)
      COPY_TO_DESKTOP=0
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

APPS_DIR="${TARGET_HOME}/.local/share/applications"
DESKTOP_DIR="${TARGET_HOME}/Desktop"

mkdir -p "${APPS_DIR}"
if [[ ${COPY_TO_DESKTOP} -eq 1 ]]; then
  mkdir -p "${DESKTOP_DIR}"
fi

cd "${REPO_ROOT}"

if ! compgen -G "*.desktop" > /dev/null; then
  echo "No .desktop files found in ${REPO_ROOT}" >&2
  exit 1
fi

echo "Restoring launchers from: ${REPO_ROOT}"
echo "Installing to: ${APPS_DIR}"
if [[ ${COPY_TO_DESKTOP} -eq 1 ]]; then
  echo "Installing to: ${DESKTOP_DIR}"
fi

for launcher in *.desktop; do
  tmp="$(mktemp)"
  cp "${launcher}" "${tmp}"

  # Rewrite legacy hardcoded paths to the current repository location.
  sed -i "s|/home/jetson/Projects/BiblionOCR|${REPO_ROOT}|g" "${tmp}"

  install -m 644 "${tmp}" "${APPS_DIR}/${launcher}"
  if [[ ${COPY_TO_DESKTOP} -eq 1 ]]; then
    install -m 755 "${tmp}" "${DESKTOP_DIR}/${launcher}"
  fi

  rm -f "${tmp}"
  echo "Installed: ${launcher}"
done

# Ensure wrapper launcher script is executable when present.
if [[ -f "${REPO_ROOT}/launchers/run-myserver.sh" ]]; then
  chmod +x "${REPO_ROOT}/launchers/run-myserver.sh"
fi

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "${APPS_DIR}" || true
fi

echo "Launcher restore complete."
