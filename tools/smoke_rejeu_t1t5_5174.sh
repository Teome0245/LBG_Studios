#!/usr/bin/env bash
# Rejeu court D6 — T1→T5 seulement (causerie / barrière 1.1). Pas T6/T7 plan.
# Usage: bash tools/smoke_rejeu_t1t5_5174.sh [BASE] [TIMEOUT_S]
set -euo pipefail
BASE="${1:-http://192.168.0.100:5174}"
TIMEOUT_S="${2:-300}"
BASE="${BASE%/}"
python3 -u - "$BASE" "$TIMEOUT_S" <<'PY'
import json, re, sys, uuid, urllib.request

BASE = sys.argv[1].rstrip("/")
TIMEOUT_S = int(sys.argv[2])
cid = f"rejeu-t1t5-{uuid.uuid4().hex[:8]}"
banned_ops = re.compile(r"(dry-run|deploy_[a-z]|\.143\b|Agir\b|VS Code|Cline|presence-dials)", re.I)

turns = [
    ("T1_greeting", "Bonjour, comment ça va aujourd’hui ?", "c2_open"),
    ("T2_follow", "bien merci, et toi ?", "c2_open"),
    ("T3_collegues", "Discutons comme collègues du projet", "c2_avis"),
    ("T4_mmo", "On travaille le MMORPG et l’incarnation des joueurs IA", "c1"),
    ("T5_zone", "pour moi l’environnement jeu doit rester une zone d’entraînement des personas, pas un dump ops", "c1"),
]

def ask(prompt: str):
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
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
        d = json.load(resp)
    r = d.get("response") or {}
    text = str(r.get("content") or r.get("response") or r.get("raw") or "")
    src = str(r.get("source") or r.get("model_used") or r.get("model") or "")
    return text, src

results = []
fail = []
for tid, prompt, kind in turns:
    text, src = ask(prompt)
    ops = banned_ops.findall(text)
    print(f"== {tid} src={src} len={len(text)} ops={ops} ==")
    print(text[:240].replace("\n", " "))
    print()
    results.append((tid, kind, text, src, ops))
    if kind == "c2_open" and (ops or "lab_ops" in src.lower() or src in ("tool_loop", "presence_brief")):
        fail.append(f"{tid}: ops/src leak {ops or src}")
    if tid == "T5_zone":
        if src in ("tool_loop", "tool_loop_p2", "presence_brief"):
            fail.append(f"T5 bad source={src}")
        if re.search(r"(?i)presence-dials|dry-run|Agir", text):
            fail.append("T5 ops leak in body")
        if re.search(r"(?i)(quel est (ton|votre) objectif|je suis une IA générique)", text):
            fail.append("T5 C1 continuity fail")

print("--- verdict ---")
print("cid=", cid)
print("FAIL=", fail or "none")
assert not fail, fail
print("SMOKE_REJEU_T1T5_OK")
PY
