#!/usr/bin/env bash
# Diagnostic superviseur Godot (Argus) — sidecar 246, miroir M1, lbg-ws/2, ZB-0.
#
# Usage (poste dev ou VM 140 avec /etc/lbg-ia-mmo.env) :
#   bash infra/scripts/diag_godot_supervisor.sh
#   bash infra/scripts/diag_godot_supervisor.sh --json
#
# Depuis poste dev — SSH direct sur VM core 140 (env LAN + sidecar 246 joignable) :
#   bash infra/scripts/diag_godot_supervisor.sh --ssh
#
# Depuis poste dev via orchestrateur 140 (code déjà déployé côté orch) :
#   LBG_ORCHESTRATOR_URL=http://192.168.0.140:8010 bash infra/scripts/diag_godot_supervisor.sh --remote
#
# One-liner copier-coller (poste dev → 140) :
#   ssh -o ConnectTimeout=8 lbg@192.168.0.140 'set -a; . /etc/lbg-ia-mmo.env; set +a; cd /opt/LBG_IA_MMO/orchestrator && PYTHONPATH=. /opt/LBG_IA_MMO/.venv/bin/python3 -c "import json,os; os.environ.setdefault(\"LBG_TEAM_GODOT_SOE_M3\",\"0\"); os.environ.setdefault(\"LBG_TEAM_GODOT_SOE_M5\",\"0\"); os.environ.setdefault(\"LBG_TEAM_GODOT_GATEWAY_SMOKE\",\"0\"); from team.godot_supervisor import execute_godot_supervisor; from team.models import TeamTask; t=TeamTask(id=\"diag\",role=\"qa\",objective=\"diag\",status=\"running\",priority=\"normal\",approval_required=False,actor_id=\"system:diag_godot_supervisor\",context={\"godot_mode\":\"full\"}); o=execute_godot_supervisor(t); print(o.get(\"human_summary\") or json.dumps(o,ensure_ascii=False,indent=2))"'

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
JSON_OUT=0
REMOTE=0
SSH_MODE=0
for arg in "$@"; do
  case "$arg" in
    --json) JSON_OUT=1 ;;
    --remote) REMOTE=1 ;;
    --ssh) SSH_MODE=1 ;;
  esac
done

ORCH="${LBG_ORCHESTRATOR_URL:-http://192.168.0.140:8010}"
CORE_HOST="${LBG_CORE_VM_HOST:-192.168.0.140}"
CORE_USER="${LBG_CORE_VM_USER:-lbg}"
REMOTE_ROOT="${LBG_IA_MMO_REMOTE_ROOT:-/opt/LBG_IA_MMO}"
PY="${ROOT_DIR}/orchestrator/.venv/bin/python"
[[ -x "${PY}" ]] || PY="python3"

read -r -d '' DIAG_PY <<'PY' || true
import json, os
os.environ.setdefault("LBG_TEAM_GODOT_SOE_M3", "0")
os.environ.setdefault("LBG_TEAM_GODOT_SOE_M5", "0")
os.environ.setdefault("LBG_TEAM_GODOT_GATEWAY_SMOKE", "0")
from team.godot_supervisor import execute_godot_supervisor
from team.models import TeamTask

task = TeamTask(
    id="diag-godot-supervisor",
    role="qa",
    objective="Diagnostic superviseur Godot",
    status="running",
    priority="normal",
    approval_required=False,
    actor_id="system:diag_godot_supervisor",
    context={"godot_mode": "full"},
)
out = execute_godot_supervisor(task)
print(json.dumps(out, ensure_ascii=False, indent=2))
PY

run_local() {
  cd "${ROOT_DIR}/orchestrator"
  PYTHONPATH=. "${PY}" -c "${DIAG_PY}"
}

run_ssh() {
  ssh -o ConnectTimeout=10 -o BatchMode=yes "${CORE_USER}@${CORE_HOST}" "bash -s" <<EOF
set -euo pipefail
if [[ -f /etc/lbg-ia-mmo.env ]]; then
  set -a
  # shellcheck disable=SC1091
  source /etc/lbg-ia-mmo.env
  set +a
fi
cd "${REMOTE_ROOT}/orchestrator"
export PYTHONPATH=.
exec "${REMOTE_ROOT}/.venv/bin/python3" -c $(printf '%q' "${DIAG_PY}")
EOF
}

run_remote() {
  curl -sf --max-time 120 -X POST "${ORCH}/v1/team/tasks" \
    -H "Content-Type: application/json" \
    -d '{"role":"qa","objective":"Diagnostic superviseur Godot","actor_id":"system:diag_godot_supervisor","context":{"godot_supervisor":true,"godot_mode":"full"}}' \
    | "${PY}" -c "import json,sys; print(json.load(sys.stdin)['id'])" \
    | while read -r tid; do
        curl -sf --max-time 180 -X POST "${ORCH}/v1/team/tasks/${tid}/run"
      done
}

if [[ "${SSH_MODE}" == "1" ]]; then
  OUT="$(run_ssh)"
elif [[ "${REMOTE}" == "1" ]]; then
  OUT="$(run_remote)"
else
  if [[ -f /etc/lbg-ia-mmo.env ]]; then
    set -a
    # shellcheck disable=SC1091
    source /etc/lbg-ia-mmo.env
    set +a
  fi
  OUT="$(run_local)"
fi

if [[ "${JSON_OUT}" == "1" ]]; then
  echo "${OUT}"
  exit 0
fi

echo "${OUT}" | "${PY}" -c "
import json, sys
d = json.load(sys.stdin)
print('=== Diagnostic superviseur Godot ===')
print('ok:', d.get('ok'), '| sidecar_ok:', d.get('sidecar_ok'))
print('blocking:', d.get('blocking_failed') or [])
print('advisory:', d.get('advisory_failed') or [])
print()
hs = d.get('human_summary') or ''
if hs:
    print(hs)
else:
    for t in d.get('tracks') or []:
        mark = 'OK' if t.get('ok') or t.get('skipped') else 'KO'
        print(f'  [{mark}] {t.get(\"track\")}')
"

OK="$(echo "${OUT}" | "${PY}" -c "
import json, sys
d = json.load(sys.stdin)
blocking = d.get('blocking_failed') or []
advisory = d.get('advisory_failed') or []
if d.get('ok'):
    print(0)
elif not blocking and advisory:
    print(3)  # advisory seulement — executor WSL traite comme succès
else:
    print(1)
" 2>/dev/null || echo 1)"
exit "${OK}"
