#!/usr/bin/env bash
# Smoke combat open-world — POST /v1/world/beast/engage près meute
set -euo pipefail
BASE="${1:-http://192.168.0.246:8787}"
BASE="${BASE%/}"
PLAYER="beast_eng_$$"

sleep 9
# Coords POI hunt (combat_density)
X=5985
Z=-1120

echo "== engage near hunt =="
curl -sS --max-time 20 -X POST "$BASE/v1/world/beast/engage" \
  -H 'Content-Type: application/json' \
  -d "{\"player\":\"$PLAYER\",\"x\":$X,\"z\":$Z,\"radius_m\":90}" | python3 -c '
import sys, json
d = json.load(sys.stdin)
assert d.get("ok") is True, d
assert d.get("loot"), d
print("ok beast=", d.get("beast_name"), "loot=", d.get("loot"), "left=", d.get("beast_count"))
'

echo "== far away → no_beast =="
curl -sS --max-time 15 -X POST "$BASE/v1/world/beast/engage" \
  -H 'Content-Type: application/json' \
  -d "{\"player\":\"${PLAYER}_far\",\"x\":100,\"z\":100,\"radius_m\":20}" | python3 -c '
import sys, json
d = json.load(sys.stdin)
assert d.get("ok") is False, d
assert d.get("error") == "no_beast_in_range", d
print("ok gate no_beast_in_range")
'

echo "SMOKE_BEAST_ENGAGE_HUB_OK"
