#!/usr/bin/env bash
# Kick-the-tires check: no accounts, no browser, about one minute.
# Runs the tests, then the offline stages on the example files in a temporary
# folder, so nothing in data/ or results/ is touched.
# Usage: ./scripts/quick_check.sh   (after ./setup.sh)
set -euo pipefail
cd "$(dirname "$0")/.."
PY=.venv/bin/python
[ -x "$PY" ] || { echo "Run ./setup.sh first." >&2; exit 1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export DIDR_WORKBOOK="$TMP/test_cases.xlsx" DIDR_STATE_DIR="$TMP/state" DIDR_RESULTS_DIR="$TMP/results"

echo "== 1/2 Tests"
"$PY" -m pytest tests -q -p no:cacheprovider

echo
echo "== 2/2 Offline stages on examples/design.csv"
"$PY" scripts/pipeline.py init --design examples/design.csv
"$PY" scripts/pipeline.py generate
"$PY" scripts/pipeline.py sample-requests --requests examples/example_requests.csv --target 10 --floor 2
"$PY" scripts/pipeline.py status

echo
echo "Quick check passed."
