#!/usr/bin/env bash
# Sur VM 140 : dry → contrôle → réel (map) + spawn CODE + notify Element.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export LBG_ORCHESTRATOR_URL="${LBG_ORCHESTRATOR_URL:-http://127.0.0.1:8010}"
export LBG_TEAM_SPAWN_STATE="${LBG_TEAM_SPAWN_STATE:-/var/lib/lbg/spawn_lh_state.json}"
export LBG_PRIME_CLIENT_ROOT="${LBG_PRIME_CLIENT_ROOT:-/opt/new_mmo/prime-client}"
export LBG_PROJECT_03_ROOT="${LBG_PROJECT_03_ROOT:-/opt/LBG_Project_03}"
MAP="${ROOT}/infra/scripts/spawn_team_lost_heaven_map.sh"
CODE="${ROOT}/infra/scripts/spawn_team_lost_heaven_code.sh"

run_map_phase() {
  local phase="$1"
  if [[ "${NOTIFY:-1}" == "1" ]]; then
    bash "$MAP" --phase="$phase" --notify-element
  else
    bash "$MAP" --phase="$phase"
  fi
}

RUN_ID="$(date +%Y%m%d%H%M%S)-$$"
export LBG_TEAM_SPAWN_RUN_ID="${LBG_TEAM_SPAWN_RUN_ID:-$RUN_ID}"
echo "=== Lost Heaven pipeline 140 run_id=${LBG_TEAM_SPAWN_RUN_ID} ==="
run_map_phase dry
run_map_phase control
run_map_phase real
echo "=== Lost Heaven CODE (write_files) ==="
bash "$CODE"
if command -v python3 >/dev/null && [[ -d "${LBG_PROJECT_03_ROOT}/lbg_agents" ]]; then
  (cd "${LBG_PROJECT_03_ROOT}" && PYTHONPATH="${LBG_PROJECT_03_ROOT}:${PYTHONPATH:-}" python3 -m lbg_agents.matrix_notify) || true
fi
echo "OK pipeline 140 — valider L2 ops/dev_game dans Element si en attente."
