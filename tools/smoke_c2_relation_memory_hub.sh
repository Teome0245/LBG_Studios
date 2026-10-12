#!/usr/bin/env bash
# Smoke C2 — mémoire relations persistée sur prime-hub :8787
# Usage: bash tools/smoke_c2_relation_memory_hub.sh [HUB_BASE]
set -euo pipefail
BASE="${1:-http://192.168.0.246:8787}"
BASE="${BASE%/}"
PLAYER="c2_rel_$$"

sleep 9

echo "== tip → gift Jax =="
curl -sS --max-time 20 -X POST "$BASE/v1/quests/tip" \
  -H 'Content-Type: application/json' \
  -d "{\"player\":\"$PLAYER\",\"quest_id\":\"lh_show_perle\",\"amount\":2}" | python3 -c '
import sys, json
d = json.load(sys.stdin)
assert d.get("ok") is True, d
print("ok tip credits=", d.get("credits"))
'

echo "== GET relation-memory Jax =="
curl -sS --max-time 10 \
  "$BASE/v1/relation-memory?player=$PLAYER&npc_id=npc:core3_barman_jax" | python3 -c '
import sys, json
d = json.load(sys.stdin)
assert d.get("ok") is True, d
ents = d.get("entries") or []
assert ents, d
kinds = {e.get("kind") for e in ents}
assert "gift" in kinds, ents
print("ok entries=", len(ents), "kinds=", sorted(kinds))
'

echo "== dialogue injecte hint =="
sleep 9
curl -sS --max-time 30 -X POST "$BASE/v1/dialogue/invoke" \
  -H 'Content-Type: application/json' \
  -d "{\"text\":\"bonjour\",\"player\":\"$PLAYER\",\"context\":{\"world_npc_id\":\"npc:core3_barman_jax\",\"player\":\"$PLAYER\",\"npc_name\":\"Jax Moro\"}}" | python3 -c '
import sys, json
d = json.load(sys.stdin)
assert d.get("ok") is True, d
meta = d.get("meta") or {}
hint = str(meta.get("relation_memory_hint") or meta.get("session_memory") or "")
assert "Cadeau" in hint or "tip" in hint.lower() or "Perle" in hint, (hint, meta)
print("ok hint=", hint[:120])
'

echo "== accept quest → Daan =="
sleep 9
curl -sS --max-time 20 -X POST "$BASE/v1/quests/accept" \
  -H 'Content-Type: application/json' \
  -d "{\"player\":\"$PLAYER\",\"quest_id\":\"lh_survey_dunes\",\"giver_id\":\"npc:core3_daan_oth\"}" | python3 -c '
import sys, json
d = json.load(sys.stdin)
assert d.get("ok") is True, d
print("ok accept", d.get("quest_id"))
'

curl -sS --max-time 10 \
  "$BASE/v1/relation-memory?player=$PLAYER&npc_id=npc:core3_daan_oth" | python3 -c '
import sys, json
d = json.load(sys.stdin)
assert d.get("ok") is True, d
ents = d.get("entries") or []
assert any(e.get("kind") == "quest" for e in ents), ents
print("ok daan quest entries=", len(ents))
'

echo "SMOKE_C2_RELATION_MEMORY_HUB_OK"
