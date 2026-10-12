#!/usr/bin/env bash
# Smoke B3+B4 — seuils dials × distance + présence différenciée (Nix vs Mira)
# Usage: bash tools/smoke_b3b4_presence_hub.sh [HUB_BASE]
set -euo pipefail
BASE="${1:-http://192.168.0.246:8787}"
BASE="${BASE%/}"

echo "== presence dials + thresholds =="
curl -sS --max-time 15 "$BASE/v1/presence-dials" | python3 -c '
import sys, json
d = json.load(sys.stdin)
assert d.get("ok") is True, d
th = d.get("thresholds") or {}
assert "escort" in th and "ignore" in th, th
bots = d.get("bots") or []
nix = next(b for b in bots if b.get("name") == "Nix")
mira = next(b for b in bots if b.get("name") == "Mira")
nd = nix.get("presence_dials") or {}
md = mira.get("presence_dials") or {}
assert float(nd.get("chaleur", 0)) > float(md.get("chaleur", 0)), (nd, md)
nline = str(nix.get("presence_line") or "")
mline = str(mira.get("presence_line") or "")
assert nline != mline, (nline, mline)
# B3 — à 12 m Nix escort, Mira greet (chaleur basse)
na12 = (nix.get("actions_at_m") or {}).get("12") or {}
ma12 = (mira.get("actions_at_m") or {}).get("12") or {}
assert na12.get("action") == "escort", na12
assert ma12.get("action") in ("greet", "ambient", "tip_ack"), ma12
assert na12.get("action") != ma12.get("action"), (na12, ma12)
# Trop loin → ignore
na35 = (nix.get("actions_at_m") or {}).get("35") or {}
assert na35.get("action") == "ignore", na35
print("ok nix@", na12.get("action"), "mira@", ma12.get("action"))
print("ok lines nix=", nline[:50], "| mira=", mline[:50])
print("SMOKE_B3B4_PRESENCE_HUB_OK")
'
