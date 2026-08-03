#!/usr/bin/env bash
set -euo pipefail

# Backward-compatible wrapper. Canonical script lives in Developer/.
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
exec bash "$repo_root/Developer/update_UI_Resources.sh" "$@"
