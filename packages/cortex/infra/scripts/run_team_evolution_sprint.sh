#!/usr/bin/env bash
# Sprint évolution manuel — bypass cooldown timer (audit full + L1 auto / L2 Pilot).
#
# Usage :
#   bash infra/scripts/run_team_evolution_sprint.sh
#   LBG_ORCHESTRATOR_URL=http://192.168.0.140:8010 bash infra/scripts/run_team_evolution_sprint.sh
#
set -euo pipefail

ORCH="${LBG_ORCHESTRATOR_URL:-http://192.168.0.140:8010}"
ORCH="${ORCH%/}"
ACTOR="${LBG_TEAM_EVOLUTION_JOB_ACTOR_ID:-system:team_evolution_manual}"
OBJECTIVE="${LBG_TEAM_EVOLUTION_OBJECTIVE:-Sprint évolution 7j — audit full infra/Team/LLM/jeu + plan + L1 auto}"
TIMEOUT="${LBG_TEAM_EVOLUTION_ROUND_TIMEOUT_S:-900}"

echo "=== Sprint évolution → ${ORCH} ==="

export OBJECTIVE ACTOR
TASK_JSON="$(curl -sf --max-time 30 -X POST "${ORCH}/v1/team/tasks" \
  -H "Content-Type: application/json" \
  -d "$(python3 -c "
import json, os
print(json.dumps({
    'role': 'pm',
    'objective': os.environ['OBJECTIVE'],
    'actor_id': os.environ['ACTOR'],
    'context': {'evolution_sprint': True, 'reunification_brief': True},
}))
")")"

TASK_ID="$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['id'])" "${TASK_JSON}")"
echo "Task créée : ${TASK_ID}"

RESULT="$(curl -sf --max-time "${TIMEOUT}" -X POST "${ORCH}/v1/team/tasks/${TASK_ID}/run")"
echo "${RESULT}" | python3 -m json.tool 2>/dev/null || echo "${RESULT}"

OK="$(python3 -c "
import json, sys
d = json.loads(sys.argv[1])
res = d.get('result') or {}
print(1 if d.get('status') == 'done' and res.get('ok') is True else 0)
" "${RESULT}" 2>/dev/null || echo 0)"

if [[ "${OK}" == "1" ]]; then
  echo "OK sprint évolution ${TASK_ID}"
  exit 0
fi
echo "ECHEC sprint évolution ${TASK_ID}" >&2
exit 1
