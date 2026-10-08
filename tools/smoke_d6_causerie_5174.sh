#!/usr/bin/env bash
# Smoke D6 — V6→V7→V8 causerie sur Compagnon :5174 (même conversation_id)
# Usage: bash tools/smoke_d6_causerie_5174.sh [BASE]
set -euo pipefail
BASE="${1:-http://192.168.0.100:5174}"
BASE="${BASE%/}"
python3 - "$BASE" <<'PY'
import json, re, sys, uuid, urllib.request
BASE = sys.argv[1].rstrip("/")
cid = f"smoke-d6-v6v8-{uuid.uuid4().hex[:8]}"
cases = json.load(urllib.request.urlopen(f"{BASE}/api/character/voice-smoke", timeout=15))["cases"]
wanted = ("V6_causerie_open", "V7_causerie_continuity", "V8_causerie_feedback")
by_id = {c["id"]: c for c in cases}
v6v8 = [by_id[i] for i in wanted]
banned_ops = re.compile(r"(dry-run|deploy_[a-z]|Agir\b|\.143\b)", re.I)
identity_reset = re.compile(
    r"(quel est (ton|votre) objectif|je suis une IA générique|présente[- ]toi comme)",
    re.I,
)
replies = []
for c in v6v8:
    body = json.dumps({
        "prompt": c["prompt"],
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
    with urllib.request.urlopen(req, timeout=180) as resp:
        d = json.load(resp)
    r = d.get("response") or {}
    text = str(r.get("content") or r.get("response") or r.get("raw") or "")
    model = str(r.get("model_used") or r.get("model") or r.get("source") or "")
    replies.append((c["id"], text, model))
    print(f"== {c['id']} model={model} len={len(text)} ==")
    print(text[:280].replace("\n", " "))
    print()

t6, m6 = replies[0][1], replies[0][2]
assert len(t6) > 60, f"V6 too short: {t6!r}"
assert "Que veux-tu faire ?" not in t6, f"V6 empty reflection: {t6}"
ops = banned_ops.findall(t6)
assert not ops, f"V6 ops leak {ops}: {t6[:240]}"
t7 = replies[1][1]
assert len(t7) > 40, t7
assert not identity_reset.search(t7), f"V7 reset {t7[:200]}"
t8 = replies[2][1]
assert len(t8) > 80, f"V8 thin: {t8}"
print("SMOKE_D6_V6V8 OK", "cid=", cid, "model=", m6)
PY
