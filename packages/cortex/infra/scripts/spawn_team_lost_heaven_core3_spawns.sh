#!/usr/bin/env bash
# Lost Heaven — spawns Core3 vivants (246) : audit ops + fix content + vérif Godot miroir.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export LBG_ORCHESTRATOR_URL="${LBG_ORCHESTRATOR_URL:-http://192.168.0.140:8010}"
exec python3 "${ROOT}/infra/scripts/spawn_team_lost_heaven_core3_spawns.py" "$@"
