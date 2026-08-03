#!/usr/bin/env bash
# Héphaïstos — crée le path mémoire équipe (ADR 0019 Vague 1).
# Usage (sur 140) : bash infra/scripts/install_team_memory_path_vm.sh
set -euo pipefail

MEM_PATH="${LBG_TEAM_MEMORY_PATH:-/var/lib/lbg-ia-mmo/team_memory.jsonl}"
DIR="$(dirname "$MEM_PATH")"

mkdir -p "$DIR"
touch "$MEM_PATH"
chmod 640 "$MEM_PATH" 2>/dev/null || true

echo "OK mémoire équipe : $MEM_PATH"
echo "Env suggéré : LBG_TEAM_MEMORY_ENABLED=1 LBG_TEAM_MEMORY_PATH=$MEM_PATH"
echo "Plan LLM (Vague 2) reste off : LBG_TEAM_PLAN_LLM=0"
