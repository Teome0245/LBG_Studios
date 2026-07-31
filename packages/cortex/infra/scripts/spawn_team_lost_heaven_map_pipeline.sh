#!/usr/bin/env bash
# Pipeline Lost Heaven : dry → contrôle → réel + Element (à lancer où Matrix/P03 sont configurés, ex. core 140).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export LBG_ORCHESTRATOR_URL="${LBG_ORCHESTRATOR_URL:-http://192.168.0.140:8010}"
SCRIPT="${ROOT}/infra/scripts/spawn_team_lost_heaven_map.sh"
NOTIFY="${NOTIFY:-1}"
run() {
  if [[ "${NOTIFY}" == "1" ]]; then
    bash "${SCRIPT}" "$@" --notify-element
  else
    bash "${SCRIPT}" "$@"
  fi
}
echo "1/3 Dry-run équipe (sondes)…"
run --phase=dry
echo "2/3 Contrôle Argus…"
run --phase=control
echo "3/3 Réel (L2 ops/dev_game — valider dans Element)…"
run --phase=real
echo "OK — voir Element + Pilot #/team (valider <id> pour L2)."
