#!/usr/bin/env bash
# Check O1 local : ruff + compileall + pytest backend (quelques secondes).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CORTEX="$ROOT/packages/cortex"
VENV="${LBG_CORTEX_VENV:-$CORTEX/.venv}"

if [[ ! -x "$VENV/bin/python" ]]; then
  echo "venv manquant : $VENV" >&2
  echo "Créer : python3 -m venv packages/cortex/.venv && source packages/cortex/.venv/bin/activate && pip install -e packages/cortex/backend[dev]" >&2
  exit 1
fi

# shellcheck disable=SC1091
source "$VENV/bin/activate"
cd "$CORTEX"

echo "== ruff (backend E/F) =="
if command -v ruff >/dev/null 2>&1; then
  (cd backend && ruff check . --select E,F --ignore E501)
else
  python -m ruff check backend --select E,F --ignore E501
fi

echo "== compileall =="
python -m compileall -q backend orchestrator

echo "== pytest backend =="
python -m pytest backend/tests -q --tb=short

echo "OK check_local"
