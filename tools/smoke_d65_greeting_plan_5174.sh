#!/usr/bin/env bash
# Smoke D6.5 — V9 greeting + V10 plan delivery sur Compagnon :5174
# Usage: bash tools/smoke_d65_greeting_plan_5174.sh [BASE]
set -euo pipefail
BASE="${1:-http://192.168.0.100:5174}"
BASE="${BASE%/}"
python3 - "$BASE" <<'PY'
import json, re, sys, uuid, urllib.request

BASE = sys.argv[1].rstrip("/")
cid = f"smoke-d65-v9v10-{uuid.uuid4().hex[:8]}"
cases = json.load(urllib.request.urlopen(f"{BASE}/api/character/voice-smoke", timeout=15))["cases"]
by_id = {c["id"]: c for c in cases}
wanted = ("V9_greeting_presence", "V10_plan_delivery")
for wid in wanted:
    assert wid in by_id, f"missing {wid} in voice-smoke"

banned_ops = re.compile(r"(dry-run|deploy_[a-z]|\.143\b|Agir\b)", re.I)
meta_only = re.compile(
    r"(?i)(je peux structurer|le plan doit se concentrer|dis-moi (ce que|comment)|que veux-tu faire)",
)
short_social_trap = re.compile(r"(?i)^\s*(allons[- ]?y\.?\s*)?(je te suis\.?\s*)+$")
plan_markers = re.compile(r"(?i)(objectif|phases?|prochaine action|##\s|1\.|-\s)", re.M)

def ask(prompt: str) -> tuple[str, str, dict]:
    body = json.dumps({
        "prompt": prompt,
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
    return text, model, r

# --- V9 greeting ---
c9 = by_id["V9_greeting_presence"]
t9, m9, r9 = ask(c9["prompt"])
print(f"== V9 model={m9} len={len(t9)} ==")
print(t9[:320].replace("\n", " "))
print()
assert len(t9) > 20, f"V9 too short: {t9!r}"
assert "Que veux-tu faire ?" not in t9, f"V9 empty reflection: {t9}"
ops9 = banned_ops.findall(t9)
assert not ops9, f"V9 ops leak {ops9}: {t9[:240]}"
# Prefer short_social / causerie, not lab_ops wall
src9 = str(r9.get("source") or m9)
assert "lab_ops" not in src9.lower(), f"V9 routed ops: {src9}"

# --- V10 plan (same conversation) ---
c10 = by_id["V10_plan_delivery"]
t10, m10, r10 = ask(c10["prompt"])
print(f"== V10 model={m10} len={len(t10)} ==")
print(t10[:420].replace("\n", " "))
print()
assert len(t10) > 120, f"V10 too short: {t10!r}"
assert not short_social_trap.match(t10.strip()), f"V10 short_social trap: {t10!r}"
assert plan_markers.search(t10), f"V10 missing plan structure: {t10[:300]}"
# Soft: avoid pure meta without artefact
if meta_only.search(t10) and not plan_markers.search(t10):
    raise AssertionError(f"V10 meta-only: {t10[:300]}")

campus = r10.get("campus_meta") or (r10.get("meta") or {}).get("campus_meta") or {}
mid = ""
if isinstance(campus, dict):
    mid = str(campus.get("mission_id") or campus.get("id") or "")
if mid:
    print("ok campus mission_id=", mid)
else:
    print("note: pas de mission_id dans la réponse (Pilot KO ou flag off) — livrable chat OK")

print("SMOKE_D65_V9V10 OK", "cid=", cid, "models=", m9, m10)
PY
