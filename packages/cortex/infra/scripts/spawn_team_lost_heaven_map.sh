#!/usr/bin/env bash
# Lost Heaven — carte retail, PNJ serveur 246, gateway, Launchpad — équipe virtuelle.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export LBG_ORCHESTRATOR_URL="${LBG_ORCHESTRATOR_URL:-http://192.168.0.140:8010}"
exec python3 "${ROOT}/infra/scripts/spawn_team_lost_heaven_map.py" "$@"
