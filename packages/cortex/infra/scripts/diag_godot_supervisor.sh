#!/usr/bin/env bash
# Diagnostic superviseur Godot (Argus) — sidecar 246, miroir M1, lbg-ws/2, ZB-0.
#
# Usage (poste dev ou VM 140 avec /etc/lbg-ia-mmo.env) :
#   bash infra/scripts/diag_godot_supervisor.sh
#   bash infra/scripts/diag_godot_supervisor.sh --json
#
# Depuis poste dev via orchestrateur 140 :
#   LBG_ORCHESTRATOR_URL=http://192.168.0.140:8010 bash infra/scripts/diag_godot_supervisor.sh --remote

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
JSON_OUT=0
REMOTE=0
for arg in "$@"; do
  case "$arg" in
    --json) JSON_OUT=1 ;;
    --remote) REMOTE=1 ;;
  esac
done

ORCH="${LBG_ORCHESTRATOR_URL:-http://192.168.0.140:8010}"
PY="${ROOT_DIR}/orchestrator/.venv/bin/python"
[[ -x "${PY}" ]] || PY="python3"

run_local() {
  cd "${ROOT_DIR}/orchestrator"
  PYTHONPATH=. "${PY}" -c "
import json, os
os.environ.setdefault('LBG_TEAM_GODOT_SOE_M3', '0')
os.environ.setdefault('LBG_TEAM_GODOT_SOE_M5', '0')
os.environ.setdefault('LBG_TEAM_GODOT_GATEWAY_SMOKE', '0')
from team.godot_supervisor import execute_godot_supervisor
from team.models import TeamTask

task = TeamTask(
    id='diag-godot-supervisor',
    role='qa',
    objective='Diagnostic superviseur Godot',
    status='running',
    priority='normal',
    approval_required=False,
    actor_id='system:diag_godot_supervisor',
    context={'godot_mode': 'full'},
)
out = execute_godot_supervisor(task)
print(json.dumps(out, ensure_ascii=False, indent=2))
"
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

if [[ "${REMOTE}" == "1" ]]; then
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

OK="$(echo "${OUT}" | "${PY}" -c "import json,sys; print(1 if json.load(sys.stdin).get('ok') else 0)" 2>/dev/null || echo 0)"
exit $((1 - OK))
