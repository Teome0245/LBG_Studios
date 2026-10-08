#!/usr/bin/env bash
# Smoke P5b — telegraph boss sparse sur prime-hub :8787
# Usage: bash tools/smoke_p5b_boss_telegraph_hub.sh [HUB_BASE]
set -euo pipefail
BASE="${1:-http://192.168.0.246:8787}"
BASE="${BASE%/}"
export BASE

echo "== list beasts / find boss =="
BOSS_JSON="$(curl -sS --max-time 12 "$BASE/v1/world/beasts")"
echo "$BOSS_JSON" | python3 -c '
import sys, json
d = json.load(sys.stdin)
assert d.get("ok") is True, d
beasts = d.get("beasts") or []
assert beasts, d
bosses = [b for b in beasts if b.get("is_boss")]
assert bosses, {"hint": "no boss spawned", "count": len(beasts), "ids": [b.get("beast_id") for b in beasts]}
b = bosses[0]
assert float(b.get("telegraph_s") or 0) > 0, b
print("ok boss=", b.get("name"), "beast_id=", b.get("beast_id"), "pos=", b.get("pos"), "telegraph_s=", b.get("telegraph_s"))
open("/tmp/p5b_boss.json","w").write(json.dumps(b))
'

echo "== force telegraph =="
python3 - <<'PY'
import json, urllib.request, os
base = os.environ["BASE"].rstrip("/")
b = json.load(open("/tmp/p5b_boss.json"))
pos = b.get("pos") or [0, 0, 0]
body = json.dumps({"x": pos[0], "z": pos[2], "radius_m": 200, "bosses_only": True}).encode()
req = urllib.request.Request(
    f"{base}/v1/world/beast/telegraph",
    data=body,
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(req, timeout=20) as resp:
    d = json.load(resp)
assert d.get("ok") is True, d
assert d.get("goal") == "telegraph", d
assert "frémit" in str(d.get("ambient", "")), d
print("ok telegraph", d.get("beast_name"), "until=", d.get("telegraph_until"))
open("/tmp/p5b_boss_key.txt", "w").write(str(d.get("entity_key", "")))
PY

echo "== snapshot goal=telegraph =="
KEY="$(cat /tmp/p5b_boss_key.txt)"
curl -sS --max-time 10 "$BASE/v1/world/beasts" | python3 -c '
import sys, json, os
d = json.load(sys.stdin)
key = open("/tmp/p5b_boss_key.txt").read().strip()
rows = d.get("beasts") or []
hit = next((b for b in rows if b.get("entity_key")==key), None)
assert hit is not None, (key, [b.get("entity_key") for b in rows])
assert hit.get("goal") == "telegraph", hit
assert hit.get("is_boss") is True, hit
print("ok snapshot goal=", hit.get("goal"), "ambient=", (hit.get("ambient") or "")[:60])
'

echo "SMOKE_P5B_BOSS_TELEGRAPH_HUB_OK"
