#!/usr/bin/env bash
# Smoke contrat client P5 — hotbar hunt-yard (HTTP) sans Godot client
# Simule le flux main.gd : reset → run → claim au POI meute.
set -euo pipefail
BASE="${1:-http://192.168.0.246:8787}"
BASE="${BASE%/}"
PLAYER="${2:-hotbar_smoke_$$}"

sleep 9
echo "== density has hunt_yard zone =="
curl -sS --max-time 8 "$BASE/v1/world/combat-density" | python3 -c '
import sys, json
d = json.load(sys.stdin)
z = next(x for x in d.get("zones") or [] if x.get("engage_surface") == "hunt_yard")
assert z.get("poi_id") == "poi:lh_hunt_chacal"
print("ok zone", z.get("id"), "r=", z.get("radius_m"))
'

echo "== hotbar flow =="
curl -sS --max-time 30 -X POST "$BASE/v1/hunt-yard/reset" -H 'Content-Type: application/json' -d '{"seed":1}' >/dev/null
curl -sS --max-time 120 -X POST "$BASE/v1/hunt-yard/run" \
  -H 'Content-Type: application/json' \
  -d "{\"max_ticks\":350,\"player\":\"$PLAYER\"}" | python3 -c '
import sys, json
d = json.load(sys.stdin)
assert d.get("status") == "victory", d
print("ok victory tick=", d.get("tick"))
'
sleep 9
curl -sS --max-time 30 -X POST "$BASE/v1/hunt-yard/claim-quest" \
  -H 'Content-Type: application/json' \
  -d "{\"player\":\"$PLAYER\",\"quest_id\":\"lh_hunt_chacal\"}" | python3 -c '
import sys, json
d = json.load(sys.stdin)
assert d.get("ok") is True, d
print("ok claim", d.get("step_id"))
'

echo "SMOKE_P5_CLIENT_HUNT_CONTRACT_OK"
