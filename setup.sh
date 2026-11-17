#!/usr/bin/env bash
# Creates the virtual environment in .venv and installs everything DIDR needs.
# Usage: ./setup.sh        (then: source .venv/bin/activate)
set -euo pipefail
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"
if ! "$PYTHON" -c 'import sys; sys.exit(sys.version_info < (3, 11))'; then
  echo "DIDR needs Python 3.11 or later; found $("$PYTHON" --version 2>&1)." >&2
  echo "Run again with a newer Python, e.g.: PYTHON=python3.11 ./setup.sh" >&2
  exit 1
fi

"$PYTHON" -m venv .venv
.venv/bin/python -m pip install --upgrade pip --quiet
.venv/bin/python -m pip install -r requirements.txt --quiet
.venv/bin/python -c "import nltk; nltk.download('wordnet', quiet=True)"

echo
echo "Done. Activate the environment with:  source .venv/bin/activate"
