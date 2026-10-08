#!/usr/bin/env bash
# Smoke spawn open-world — bêtes densité sur prime-hub :8787
set -euo pipefail
BASE="${1:-http://192.168.0.246:8787}"
BASE="${BASE%/}"

echo "== healthz beast_count =="
curl -sS --max-time 8 "$BASE/healthz" | python3 -c '
import sys, json
d = json.load(sys.stdin)
assert d.get("ok") is True, d
n = int(d.get("beast_count") or 0)
assert n >= 1, d
print("ok beast_count=", n, "bots=", d.get("bot_count"), "npc=", d.get("npc_count"))
'

echo "== density hunt zone =="
curl -sS --max-time 8 "$BASE/v1/world/combat-density" | python3 -c '
import sys, json
d = json.load(sys.stdin)
z = next(x for x in (d.get("zones") or []) if x.get("engage_surface") == "hunt_yard")
assert z.get("poi_id") == "poi:lh_hunt_chacal"
print("ok engage", z.get("id"))
'

echo "SMOKE_BEAST_SPAWN_HUB_OK"
