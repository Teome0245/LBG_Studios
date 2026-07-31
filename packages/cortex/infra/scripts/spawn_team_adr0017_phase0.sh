#!/usr/bin/env bash
# ADR 0017 Phase 0 — sidecar :8791 catalogue skills + panneau M10 live (pas de rewrite Core3).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export LBG_ORCHESTRATOR_URL="${LBG_ORCHESTRATOR_URL:-http://192.168.0.140:8010}"
exec python3 "${ROOT}/infra/scripts/spawn_team_adr0017_phase0.py" "$@"
