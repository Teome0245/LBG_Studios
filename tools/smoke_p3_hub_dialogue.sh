#!/usr/bin/env bash
# Smoke P3 — dialogue + C1 moves + C12 envelope sur prime-hub live (:8787)
# Usage: bash tools/smoke_p3_hub_dialogue.sh [HUB_BASE]
set -euo pipefail
BASE="${1:-http://192.168.0.246:8787}"
BASE="${BASE%/}"

echo "== healthz =="
curl -sS --max-time 8 "$BASE/healthz" | python3 -c '
import sys, json
d = json.load(sys.stdin)
assert d.get("ok") is True, d
assert d.get("service") == "prime_hub", d.get("service")
print("ok phase=", d.get("phase"), "bots=", d.get("bot_count"))
'

echo "== catalog C10 skills =="
curl -sS --max-time 8 "$BASE/catalog?type=skills" | python3 -c '
import sys, json
d = json.load(sys.stdin)
assert d.get("ok") is True, d
assert int(d.get("count") or 0) >= 1, d
print("ok skills=", d.get("count"))
'

echo "== tick-matrix C11 =="
curl -sS --max-time 8 "$BASE/tick-matrix" | python3 -c '
import sys, json
d = json.load(sys.stdin)
assert d.get("ok") is True, d
assert int(d.get("count") or 0) >= 1, d
print("ok actions=", d.get("count"))
'

echo "== P3 dialogue Jax + moves + C12 =="
curl -sS --max-time 30 -X POST "$BASE/v1/dialogue/invoke" \
  -H 'Content-Type: application/json' \
  -d '{
    "actor_id":"prime:smoke_p3",
    "text":"Salut Jax",
    "context":{
      "world_npc_id":"npc:core3_barman_jax",
      "npc_name":"Jax Moro",
      "player":"smoke_p3",
      "session_summary":{"last_npc":"Jax"},
      "history":[
        {"role":"user","content":"Tu as une rumeur ?"},
        {"role":"assistant","content":"Au marché on entend tout."}
      ]
    }
  }' | python3 -c '
import sys, json
d = json.load(sys.stdin)
assert d.get("ok") is True, d
assert (d.get("reply") or "").strip(), d
moves = d.get("suggested_moves") or []
assert 1 <= len(moves) <= 3, moves
meta = d.get("meta") or {}
assert meta.get("suggested_moves_source") == "registry_template", meta
assert meta.get("source") == "prime_hub", meta
assert "structuredContent" in d, list(d.keys())
sc = d["structuredContent"]
assert sc.get("reply") == d.get("reply"), sc
assert d.get("result") == d.get("reply"), d.get("result")
print("ok moves=", [m.get("id") for m in moves], "history_turns=", meta.get("history_turns"))
print("reply:", (d.get("reply") or "")[:160])
'

echo "== P3 Daan ui move =="
curl -sS --max-time 30 -X POST "$BASE/v1/dialogue/invoke" \
  -H 'Content-Type: application/json' \
  -d '{
    "actor_id":"prime:smoke_p3",
    "text":"Bonjour",
    "context":{
      "world_npc_id":"npc:core3_daan_oth",
      "npc_name":"Daan Oth",
      "player":"smoke_p3"
    }
  }' | python3 -c '
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

echo "SMOKE_P3_HUB_OK"
