#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/../.." && pwd)"
venv_dir="${repo_root}/.venv"
image_editor_requirements="${repo_root}/ViewController/1-PreProcess/ImageEditor/Image-Editor-main/requirements.txt"
website_dir="${repo_root}/docs/website"

echo "Repository root: ${repo_root}"

echo "Updating Ubuntu package metadata..."
sudo apt update

echo "Upgrading installed packages..."
sudo apt upgrade -y

echo "Removing no-longer-needed packages..."
sudo apt autoremove -y

echo "Installing core developer tools..."
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

echo "Installing Python tooling..."
sudo apt install -y \
  python3 \
  python3-venv \
  python3-pip \
  python3-dev \
  pipx

echo "Installing Qt and PyQt5 tooling..."
sudo apt install -y \
  python3-pyqt5 \
  pyqt5-dev-tools \
  qttools5-dev-tools \
  qttools5-dev \
  qtbase5-dev

echo "Installing OCR, imaging, and scanner packages..."
sudo apt install -y \
  tesseract-ocr \
  tesseract-ocr-eng \
  tesseract-ocr-grc \
  tesseract-ocr-lat \
  sane-utils \
  libsane1 \
  sane-airscan \
  python3-sane \
  python3-scapy \
  python3-zeroconf \
  imagemagick

echo "Installing optional desktop tools..."
sudo apt install -y \
  fontforge \
  python3-fontforge \
  python3-enchant \
  python3-reportlab \
  enchant-2 \
  gimp \
  libreoffice \
  simple-scan

echo "Creating project virtual environment with system site packages..."
python3 -m venv --system-site-packages "${venv_dir}"

echo "Upgrading pip inside the project virtual environment..."
"${venv_dir}/bin/python" -m pip install --upgrade pip

if [[ -f "${image_editor_requirements}" ]]; then
  echo "Installing bundled Image Editor Python requirements..."
  "${venv_dir}/bin/pip" install -r "${image_editor_requirements}"
else
  echo "Skipping Image Editor Python requirements: ${image_editor_requirements} not found."
fi

if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
  node_major="$(node -p "process.versions.node.split('.')[0]")"
  if [[ "${node_major}" -ge 20 ]]; then
    if [[ -f "${website_dir}/package.json" ]]; then
      echo "Installing website npm dependencies..."
      (
        cd "${website_dir}"
        npm install
      )
    else
      echo "Skipping website npm dependencies: ${website_dir}/package.json not found."
    fi
  else
    echo "Skipping website npm dependencies: detected Node.js major version ${node_major}, but the Vite website toolchain needs a newer Node.js release."
  fi
else
  echo "Skipping website npm dependencies: node and npm are not installed on this machine."
fi

echo "Dependency installation complete."
echo "Project virtual environment: ${venv_dir}"
echo "Activate it with: source ${venv_dir}/bin/activate"