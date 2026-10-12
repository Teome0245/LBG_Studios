#!/usr/bin/env bash
# Smoke C10 POI + densité combat sur prime-hub :8787
# Usage: bash tools/smoke_catalog_poi_hub.sh [HUB_BASE]
set -euo pipefail
BASE="${1:-http://192.168.0.246:8787}"
BASE="${BASE%/}"

echo "== catalog type=poi =="
curl -sS --max-time 8 "$BASE/v1/catalog?type=poi" | python3 -c '
import sys, json
d = json.load(sys.stdin)
assert d.get("ok") is True, d
items = d.get("items") or []
assert int(d.get("count") or 0) >= 1, d
ids = {str(i.get("id")) for i in items if isinstance(i, dict)}
for want in ("poi:lh_hunt_chacal", "poi:player_spawn"):
    assert want in ids, (want, sorted(ids)[:12])
print("ok poi count=", d.get("count"), "hunt=", "poi:lh_hunt_chacal" in ids)
'

echo "== combat-density =="
curl -sS --max-time 8 "$BASE/v1/world/combat-density" | python3 -c '
import sys, json
d = json.load(sys.stdin)
assert d.get("ok") is True, d
zones = d.get("zones") or []
assert len(zones) >= 1, d
hunt = next((z for z in zones if z.get("engage_surface") == "hunt_yard"), None)
assert hunt is not None, zones
assert hunt.get("poi_id") == "poi:lh_hunt_chacal", hunt
print("ok zones=", d.get("count"), "hunt_yard=", hunt.get("id"))
'

echo "SMOKE_CATALOG_POI_HUB_OK"
