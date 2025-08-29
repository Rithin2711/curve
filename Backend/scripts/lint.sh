#!/usr/bin/env bash
set -euo pipefail

# Run flake8 ensuring it exists; install in user space if missing to avoid CI failures.
if ! command -v flake8 >/dev/null 2>&1; then
  echo "flake8 not found. Installing to user site-packages..."
  python -m pip install --user flake8
fi

echo "Running flake8..."
flake8
echo "flake8 completed."
