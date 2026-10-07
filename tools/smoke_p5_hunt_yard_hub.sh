#!/usr/bin/env bash
# Smoke P5a — cour de chasse sur prime-hub :8787
# Usage: bash tools/smoke_p5_hunt_yard_hub.sh [HUB_BASE]
set -euo pipefail
BASE="${1:-http://192.168.0.246:8787}"
BASE="${BASE%/}"
PLAYER="hunt_smoke_$$"
# TickGate C11 cooldown partagé (player=local sur run sans body player)
sleep 9

echo "== healthz =="
curl -sS --max-time 8 "$BASE/healthz" | python3 -c '
import sys, json
d = json.load(sys.stdin)
assert d.get("ok") is True, d
print("ok phase=", d.get("phase"))
'

echo "== reset yard =="
curl -sS --max-time 30 -X POST "$BASE/v1/hunt-yard/reset" \
  -H 'Content-Type: application/json' \
  -d '{"seed":1}' | python3 -c '
import sys, json
d = json.load(sys.stdin)
assert d.get("ok") is not False, d
assert d.get("status") == "ongoing", d
assert d.get("quest_id") == "lh_hunt_chacal", d
print("ok seed=", d.get("seed"), "players=", len(d.get("players") or []))
'

echo "== run until victory =="
curl -sS --max-time 120 -X POST "$BASE/v1/hunt-yard/run" \
  -H 'Content-Type: application/json' \
  -d "{\"max_ticks\":350,\"player\":\"$PLAYER\"}" | python3 -c '
import sys, json
d = json.load(sys.stdin)
assert d.get("status") == "victory", d
assert int(d.get("kills") or 0) == 5, d
print("ok victory tick=", d.get("tick"), "kills=", d.get("kills"))
'

echo "== claim meute =="
sleep 9
curl -sS --max-time 30 -X POST "$BASE/v1/hunt-yard/claim-quest" \
  -H 'Content-Type: application/json' \
  -d "{\"player\":\"$PLAYER\",\"quest_id\":\"lh_hunt_chacal\"}" | python3 -c '
import sys, json
d = json.load(sys.stdin)
assert d.get("ok") is True, d
assert d.get("step_id") == "meute", d
assert (d.get("hunt") or {}).get("status") == "victory", d
print("ok claim step=", d.get("step_id"), "ready=", d.get("ready_to_turn_in"))
'

echo "== progress meute sans victory → hunt_required =="
# Joueur distinct + reset yard (évite 429 tick_busy du claim précédent)
GATE_PLAYER="${PLAYER}_gate"
curl -sS --max-time 15 -X POST "$BASE/v1/hunt-yard/reset" -H 'Content-Type: application/json' -d '{"seed":2}' >/dev/null
curl -sS --max-time 15 -X POST "$BASE/v1/quests/accept" \
  -H 'Content-Type: application/json' \
  -d "{\"player\":\"$GATE_PLAYER\",\"quest_id\":\"lh_hunt_chacal\"}" >/dev/null || true
sleep 9
curl -sS --max-time 15 -X POST "$BASE/v1/quests/progress" \
  -H 'Content-Type: application/json' \
  -d "{\"player\":\"$GATE_PLAYER\",\"quest_id\":\"lh_hunt_chacal\",\"step_id\":\"meute\"}" | python3 -c '
import sys, json
d = json.load(sys.stdin)
assert d.get("ok") is False, d
assert d.get("error") == "hunt_required", d
print("ok gate hunt_required")
'

echo "SMOKE_P5_HUNT_YARD_HUB_OK"
