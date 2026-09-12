#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SCHEDULER_ROOT="${REPO_ROOT}/Core/Scheduler"

if [[ -x "${REPO_ROOT}/.venv/bin/python" ]]; then
  PYTHON_BIN="${REPO_ROOT}/.venv/bin/python"
else
  PYTHON_BIN="/usr/bin/python3"
fi

cd "${SCHEDULER_ROOT}"
exec "${PYTHON_BIN}" -m biblion_scheduler "$@"