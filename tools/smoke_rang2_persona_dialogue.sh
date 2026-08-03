#!/usr/bin/env bash
# Smoke Rang 2 — session_summary → mmo_persona (Pilot agent-dialogue)
# Usage: bash tools/smoke_rang2_persona_dialogue.sh [PILOT_BASE]
set -euo pipefail
BASE="${1:-http://192.168.0.140:8000}"
BASE="${BASE%/}"

echo "== mmo-bridge =="
curl -sS --max-time 15 -X POST "$BASE/v1/pilot/assistant/session-summary/mmo-bridge" \
  -H 'Content-Type: application/json' \
  -d '{"session_summary":{"tracked_quest":"aide au village","last_npc":"Odo","player_note":"smoke rang2"}}' \
  | python3 -c 'import sys,json; d=json.load(sys.stdin); assert d.get("ok") is True; assert "context_patch" in d; print("ok context_patch keys", sorted((d.get("context_patch") or {}).keys()))'

echo "== agent-dialogue mmo_persona =="
curl -sS --max-time 90 -X POST "$BASE/v1/pilot/agent-dialogue/invoke" \
  -H 'Content-Type: application/json' \
  -d '{"actor_id":"prime:smoke","text":"Bonjour, parle-moi du village et de mon voyage.","context":{"world_npc_id":"npc:odo_guide","npc_name":"Odo","lyra_engagement":"mmo_persona","_skip_factual_status":true,"session_summary":{"tracked_quest":"aide au village","last_npc":"Odo","player_note":"smoke rang2","session_mood":"curious"}}}' \
  | python3 -c 'import sys,json; d=json.load(sys.stdin); m=d.get("meta") or {}; eng=m.get("lyra_engagement_resolved"); reply=(d.get("reply") or "").strip(); assert eng=="mmo_persona", eng; assert reply, "empty reply"; print("ok engagement=", eng); print("reply:", reply[:240])'

echo "SMOKE_RANG2_OK"
