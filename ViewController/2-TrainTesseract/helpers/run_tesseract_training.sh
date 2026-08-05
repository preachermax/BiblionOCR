#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PROJECT_ROOT="${1:-${REPO_ROOT}}"
LANGUAGE_CODE="${2:-${BIBLION_TRAINING_LANGUAGE:-feg}}"
TRAINING_ROOT="${BIBLION_TRAINING_ROOT:-${PROJECT_ROOT}/Model/Project/Training/Tesseract}"
GROUND_TRUTH_DIR="${BIBLION_TRAINING_GROUND_TRUTH_DIR:-${TRAINING_ROOT}/data/${LANGUAGE_CODE}-ground-truth}"
WORDLIST_DIR="${BIBLION_TRAINING_WORDLIST_DIR:-${TRAINING_ROOT}/wordlists/${LANGUAGE_CODE}}"
CONFIG_DIR="${BIBLION_TRAINING_CONFIG_DIR:-${TRAINING_ROOT}/configs/${LANGUAGE_CODE}}"
LOG_DIR="${BIBLION_TRAINING_LOG_DIR:-${TRAINING_ROOT}/logs/${LANGUAGE_CODE}}"
PLOT_DIR="${BIBLION_TRAINING_PLOT_DIR:-${TRAINING_ROOT}/plots/${LANGUAGE_CODE}}"
MODEL_DIR="${BIBLION_TRAINING_MODEL_DIR:-${TRAINING_ROOT}/models/${LANGUAGE_CODE}}"
SCRIPT_DIR_TARGET="${BIBLION_TRAINING_SCRIPT_DIR:-${TRAINING_ROOT}/scripts}"
TESSTRAIN_DIR="${BIBLION_TRAINING_TESSSTRAIN_DIR:-${TRAINING_ROOT}/tesstrain}"
TESSERACT_BIN="${TESSERACT_BIN:-$(command -v tesseract || true)}"
TESSDATA_DIR="${TESSDATA_PREFIX:-${BIBLION_TESSDATA_DIR:-/usr/share/tesseract-ocr/5/tessdata}}"

mkdir -p \
  "${TRAINING_ROOT}" \
  "${GROUND_TRUTH_DIR}" \
  "${WORDLIST_DIR}" \
  "${CONFIG_DIR}" \
  "${LOG_DIR}" \
  "${PLOT_DIR}" \
  "${MODEL_DIR}" \
  "${SCRIPT_DIR_TARGET}" \
  "${TESSTRAIN_DIR}"

printf 'Training workspace: %s\n' "${TRAINING_ROOT}"
printf 'Language code: %s\n' "${LANGUAGE_CODE}"
printf 'Tesseract binary: %s\n' "${TESSERACT_BIN:-not found}"
printf 'Tessdata directory: %s\n' "${TESSDATA_DIR}"
printf 'Ground truth directory: %s\n' "${GROUND_TRUTH_DIR}"
printf 'Wordlist directory: %s\n' "${WORDLIST_DIR}"
printf 'Config directory: %s\n' "${CONFIG_DIR}"
printf 'Log directory: %s\n' "${LOG_DIR}"
printf 'Plot directory: %s\n' "${PLOT_DIR}"
printf 'Model directory: %s\n' "${MODEL_DIR}"

if [[ -z "${TESSERACT_BIN}" ]]; then
  printf 'Tesseract was not found on PATH. Install tesseract-ocr 5.0+ before training.\n' >&2
  exit 2
fi

if [[ -n "${TRAINING_COMMAND:-}" ]]; then
  printf 'Launching configured training command...\n'
  exec bash -lc "${TRAINING_COMMAND}"
fi

if [[ -n "${TESSTRAIN_SH:-}" && -x "${TESSTRAIN_SH}" ]]; then
  printf 'Launching TESSTRAIN_SH=%s\n' "${TESSTRAIN_SH}"
  exec "${TESSTRAIN_SH}" "$@"
fi

if command -v tesstrain.sh >/dev/null 2>&1; then
  printf 'Launching tesstrain.sh from PATH...\n'
  exec tesstrain.sh "$@"
fi

printf 'No training entrypoint was found. Set TRAINING_COMMAND or TESSTRAIN_SH to your tesstrain wrapper.\n' >&2
exit 2