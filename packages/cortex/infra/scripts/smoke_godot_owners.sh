#!/usr/bin/env bash
# Smokes owner Godot / LAN (A2 — PLAN_MMO_O2).
# Usage:
#   bash infra/scripts/smoke_godot_owners.sh
#   BUNDLE=godot_login bash infra/scripts/smoke_godot_owners.sh
#
# Sur CT executor (.141) sans orchestrator local : délègue via SSH vers .140.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BUNDLE="${BUNDLE:-godot_client}"
CORE_HOST="${LBG_CORE_VM_HOST:-192.168.0.140}"
CORE_USER="${LBG_CORE_VM_USER:-lbg}"
REMOTE_ROOT="${LBG_IA_MMO_REMOTE_ROOT:-/opt/LBG_IA_MMO}"

run_local() {
  cd "$ROOT"
  if [[ -f .venv/bin/activate ]]; then
    # shellcheck disable=SC1091
    source .venv/bin/activate
  fi
  export PYTHONPATH="${ROOT}/orchestrator${PYTHONPATH:+:$PYTHONPATH}"
  export BUNDLE
  python3 - <<'PY'
from team.owner_smokes import run_owner_smokes
import json, os, sys
bundle = os.environ.get("BUNDLE", "godot_client")
out = run_owner_smokes(bundle=bundle)
print(json.dumps(out, ensure_ascii=False, indent=2))
sys.exit(0 if out.get("ok") else 1)
PY
}

run_ssh() {
  echo "[executor] pas de module team local — SSH ${CORE_USER}@${CORE_HOST}"
  ssh -o BatchMode=yes -o ConnectTimeout=10 "${CORE_USER}@${CORE_HOST}" \
    "BUNDLE='${BUNDLE}' bash '${REMOTE_ROOT}/infra/scripts/smoke_godot_owners.sh'"
}

if [[ -f "${ROOT}/orchestrator/team/owner_smokes.py" ]]; then
  run_local
elif python3 -c "import team.owner_smokes" 2>/dev/null; then
  run_local
else
  run_ssh
fi
