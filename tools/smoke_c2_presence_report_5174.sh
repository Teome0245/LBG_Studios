#!/usr/bin/env bash
# Smoke C2 — retour terrain présence → causerie Compagnon :5174
# Usage: bash tools/smoke_c2_presence_report_5174.sh [BASE]
set -euo pipefail
BASE="${1:-http://192.168.0.100:5174}"
BASE="${BASE%/}"
python3 - "$BASE" <<'PY'
import json, sys, urllib.request, uuid

BASE = sys.argv[1].rstrip("/")
cid = f"smoke-c2-presence-{uuid.uuid4().hex[:8]}"
body = json.dumps({
    "prompt": "retour hub présence — Nix vs Mira",
    "mode": "auto",
    "profile": "compagnon",
    "conversation_id": cid,
}).encode()
req = urllib.request.Request(
    f"{BASE}/api/ask",
    data=body,
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(req, timeout=60) as resp:
    d = json.load(resp)
r = d.get("response") or d
text = str(r.get("content") or d.get("content") or "")
src = str(r.get("source") or r.get("model_used") or "")
print("source=", src)
print(text[:320].replace("\n", " | "))
assert "Nix" in text and "Mira" in text, text
assert "escort" in text.lower() or "greet" in text.lower(), text
assert "Agir" not in text and "dry-run" not in text.lower()
assert src == "presence_report" or "chaleur" in text.lower()
print("SMOKE_C2_PRESENCE_REPORT_OK", "cid=", cid)
PY
