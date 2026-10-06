#!/usr/bin/env bash
# Smoke Vague B C1 — suggested_moves sur agent-dialogue (Jax hub)
# Usage: bash tools/smoke_c1_suggested_moves.sh [PILOT_BASE]
set -euo pipefail
BASE="${1:-http://192.168.0.140:8000}"
BASE="${BASE%/}"

echo "== C1 suggested_moves Jax =="
curl -sS --max-time 90 -X POST "$BASE/v1/pilot/agent-dialogue/invoke" \
  -H 'Content-Type: application/json' \
  -d '{"actor_id":"prime:smoke_c1","text":"Salut Jax","context":{"world_npc_id":"npc:core3_barman_jax","npc_name":"Jax Moro","lyra_engagement":"mmo_persona","_skip_factual_status":true,"session_summary":{"last_npc":"Jax"}}}' \
  | python3 -c '
import sys, json
d = json.load(sys.stdin)
moves = d.get("suggested_moves") or []
meta = d.get("meta") or {}
assert isinstance(moves, list), moves
assert 1 <= len(moves) <= 3, len(moves)
assert meta.get("suggested_moves_source") == "registry_template", meta.get("suggested_moves_source")
for m in moves:
    assert m.get("id") and m.get("label") and m.get("utterance"), m
print("ok moves=", len(moves), [m.get("id") for m in moves])
print("reply:", (d.get("reply") or "")[:160])
'

echo "== C1 Daan ui move present =="
curl -sS --max-time 90 -X POST "$BASE/v1/pilot/agent-dialogue/invoke" \
  -H 'Content-Type: application/json' \
  -d '{"actor_id":"prime:smoke_c1","text":"Bonjour","context":{"world_npc_id":"npc:core3_daan_oth","npc_name":"Daan Oth","lyra_engagement":"mmo_persona","_skip_factual_status":true}}' \
  | python3 -c '
import sys, json
d = json.load(sys.stdin)
moves = d.get("suggested_moves") or []
ids = [m.get("id") for m in moves]
assert "move:daan_offres" in ids, ids
board = next(m for m in moves if m.get("id") == "move:daan_offres")
assert board.get("kind") == "ui", board
assert (board.get("action") or {}).get("name") == "open_mission_board", board
print("ok daan ui move")
'

echo "SMOKE_C1_OK"
