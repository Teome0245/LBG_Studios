#!/usr/bin/env bash
# Lost Heaven CODE — Hermès/Iris write_files (docs prime-client).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export LBG_ORCHESTRATOR_URL="${LBG_ORCHESTRATOR_URL:-http://192.168.0.140:8010}"
export LBG_PRIME_CLIENT_ROOT="${LBG_PRIME_CLIENT_ROOT:-/home/sdesh/projects/new_mmo/prime-client}"
exec python3 "${ROOT}/infra/scripts/spawn_team_lost_heaven_code.py" "$@"
