#!/usr/bin/env bash
# Wrapper — handoff Prime LBG vers équipe virtuelle (orchestrateur :8010).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export LBG_ORCHESTRATOR_URL="${LBG_ORCHESTRATOR_URL:-http://127.0.0.1:8010}"
exec python3 "${ROOT}/infra/scripts/spawn_team_prime_lbg_handoff.py" "$@"
