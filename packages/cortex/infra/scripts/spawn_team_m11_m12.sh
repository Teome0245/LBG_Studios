#!/usr/bin/env bash
# Spawn parallèle M11 (login Godot) + M12 (lbg-ws/2) — équipe virtuelle.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export LBG_ORCHESTRATOR_URL="${LBG_ORCHESTRATOR_URL:-http://127.0.0.1:8010}"
exec python3 "${ROOT}/infra/scripts/spawn_team_m11_m12.py" "$@"
