#!/usr/bin/env bash

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}" || exit 1

if [[ -x "${REPO_ROOT}/.venv/bin/python" ]]; then
  PYTHON_BIN="${REPO_ROOT}/.venv/bin/python"
else
  PYTHON_BIN="/usr/bin/python3"
fi

"${PYTHON_BIN}" "${REPO_ROOT}/ViewController/0-MainUI/MyExplorer.py" "$@"
status=$?

echo
echo "MyExplorer exited with status ${status}"
echo "Press Enter to close"
read -r

exit "${status}"
