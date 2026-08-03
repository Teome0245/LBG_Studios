#!/usr/bin/env bash
# Smokes owner Godot / LAN (A2 — PLAN_MMO_O2).
# Usage:
#   bash infra/scripts/smoke_godot_owners.sh
#   BUNDLE=godot_login bash infra/scripts/smoke_godot_owners.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BUNDLE="${BUNDLE:-godot_client}"
cd "$ROOT"
if [[ -f .venv/bin/activate ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi
export PYTHONPATH="${ROOT}/orchestrator${PYTHONPATH:+:$PYTHONPATH}"
python3 - <<PY
from team.owner_smokes import run_owner_smokes
import json, os, sys
bundle = os.environ.get("BUNDLE", "godot_client")
out = run_owner_smokes(bundle=bundle)
print(json.dumps(out, ensure_ascii=False, indent=2))
sys.exit(0 if out.get("ok") else 1)
PY
