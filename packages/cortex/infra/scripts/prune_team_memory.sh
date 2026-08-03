#!/usr/bin/env bash
# Héphaïstos — prune mémoire équipe (ADR 0019 Vague 4).
# Usage (140, orch up) :
#   bash infra/scripts/prune_team_memory.sh
#   LBG_TEAM_MEMORY_MAX_ENTRIES=200 bash infra/scripts/prune_team_memory.sh
set -euo pipefail

ORCH="${LBG_ORCHESTRATOR_URL:-http://127.0.0.1:8010}"
MAX_ENTRIES="${LBG_TEAM_MEMORY_MAX_ENTRIES:-500}"
MAX_AGE="${LBG_TEAM_MEMORY_MAX_AGE_DAYS:-30}"

curl -sS -X POST "${ORCH}/v1/team/memory/prune" \
  -H 'Content-Type: application/json' \
  -d "{\"max_entries\": ${MAX_ENTRIES}, \"max_age_days\": ${MAX_AGE}}"
echo
