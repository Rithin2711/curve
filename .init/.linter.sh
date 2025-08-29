#!/usr/bin/env bash
# Gravity Curve - CI Linter Wrapper
# This script is invoked by the CI environment. It must be non-interactive and robust.

set -euo pipefail

# Always run from repository root (script resides under curve/.init)
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Ensure Python and pip are available
if ! command -v python >/dev/null 2>&1; then
  echo "Python not found in CI environment." >&2
  exit 1
fi

if ! command -v pip >/dev/null 2>&1; then
  echo "pip not found in CI environment." >&2
  exit 1
fi

# Try to install flake8 if missing; use user installation to avoid permission issues
if ! command -v flake8 >/dev/null 2>&1; then
  echo "[CI] flake8 not found. Installing to user site-packages..."
  python -m pip install --user flake8
  # Rehash PATH for user base
  USER_BASE="$(python -m site --user-base)"
  USER_BIN="$USER_BASE/bin"
  export PATH="$USER_BIN:$PATH"
fi

# Move into Backend, where .flake8 resides
cd "$REPO_ROOT/Backend"

# Run flake8 using local configuration
echo "[CI] Running flake8..."
flake8
echo "[CI] flake8 completed successfully."
