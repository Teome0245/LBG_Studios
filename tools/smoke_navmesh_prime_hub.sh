#!/usr/bin/env bash
# Smoke ticket 2.3 — navmesh NavigationServer3D sur prime-hub
# Usage: bash tools/smoke_navmesh_prime_hub.sh [HUB_BASE]
set -euo pipefail
BASE="${1:-http://192.168.0.246:8787}"
BASE="${BASE%/}"

echo "== healthz navmesh =="
curl -sS --max-time 8 "$BASE/healthz" | python3 -c '
import sys, json
d = json.load(sys.stdin)
assert d.get("ok") is True, d
nav = d.get("navmesh") or {}
assert nav.get("ok") is True, nav
assert nav.get("engine") == "NavigationServer3D", nav
assert int(nav.get("polygons") or 0) > 0, nav
assert int(nav.get("regions") or 0) >= 1, nav
assert int(nav.get("budget_per_tick") or 0) == 0, nav
print("ok engine=", nav.get("engine"), "polys=", nav.get("polygons"),
      "bake_ms=", nav.get("bake_ms"), "queries=", nav.get("path_queries"))
'

echo "== /v1/navmesh stats =="
curl -sS --max-time 8 "$BASE/v1/navmesh" | python3 -c '
import sys, json
d = json.load(sys.stdin)
assert d.get("ok") is True, d
print("ok bounds=", d.get("bounds"), "last_query_us=", d.get("last_query_us"))
'

echo "== trace navmesh plaza → board =="
curl -sS --max-time 8 "$BASE/v1/dev/navmesh/probe?fx=4749&fz=-737&tx=4939&tz=-932" | python3 -c '
import sys, json
d = json.load(sys.stdin)
assert d.get("ok") is True, d
assert d.get("source") == "navmesh", d
assert int(d.get("count") or 0) > 2, d
wps = d.get("waypoints") or []
print("ok source=", d.get("source"), "waypoints=", d.get("count"), "arrive=", wps[-1])
'

echo "== fallback hors bornes (dunes) =="
curl -sS --max-time 8 "$BASE/v1/dev/navmesh/probe?fx=4749&fz=-737&tx=9000&tz=9000" | python3 -c '
import sys, json
d = json.load(sys.stdin)
assert d.get("source") == "grid_fallback", d
print("ok fallback source=", d.get("source"))
'

echo "SMOKE_NAVMESH_PRIME_HUB_OK"
