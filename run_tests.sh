#!/usr/bin/env bash
set -euo pipefail

# Run from project root (directory containing this script)
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# Pick a Python executable
PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "ERROR: Python not found on PATH."
  exit 1
fi

# Create and activate a venv (local, reproducible)
VENV_DIR="${ROOT_DIR}/.venv"
if [[ ! -d "$VENV_DIR" ]]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

# Upgrade tooling
python -m pip install --upgrade pip setuptools wheel

# Install runtime dependencies
if [[ -f "requirements.txt" ]]; then
  python -m pip install -r requirements.txt
else
  python -m pip install requests beautifulsoup4
fi

# Install test dependencies
python -m pip install pytest pytest-mock

# Run all tests
pytest