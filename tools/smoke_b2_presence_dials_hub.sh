#!/usr/bin/env bash
# Smoke B2 — presence_dials joueurs IA sur prime-hub :8787
# Usage: bash tools/smoke_b2_presence_dials_hub.sh [HUB_BASE]
set -euo pipefail
BASE="${1:-http://192.168.0.246:8787}"
BASE="${BASE%/}"

echo "== GET /v1/presence-dials =="
curl -sS --max-time 15 "$BASE/v1/presence-dials" | python3 -c '
import sys, json
d = json.load(sys.stdin)
assert d.get("ok") is True, d
bots = d.get("bots") or []
assert len(bots) >= 1, d
nix = next((b for b in bots if str(b.get("name")) == "Nix"), None)
assert nix, bots
dials = nix.get("presence_dials") or {}
assert float(dials.get("chaleur", 0)) >= 0.6, dials
line = str(nix.get("presence_line") or "")
assert "chaleur" in line.lower() or "salue" in line.lower() or line, line
print("ok nix dials=", dials, "line=", line[:80])
print("SMOKE_B2_PRESENCE_DIALS_HUB_OK count=", len(bots))
'
