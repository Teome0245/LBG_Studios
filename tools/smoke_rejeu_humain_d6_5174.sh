#!/usr/bin/env bash
# Rejeu auto du fil humain D6 (2026-10-08) — proxy feeling C1/C2 + délivrance.
# Usage: bash tools/smoke_rejeu_humain_d6_5174.sh [BASE]
set -euo pipefail
BASE="${1:-http://192.168.0.100:5174}"
BASE="${BASE%/}"
python3 -u - "$BASE" <<'PY'
import json, re, sys, uuid, urllib.request

BASE = sys.argv[1].rstrip("/")
cid = f"rejeu-humain-d6-{uuid.uuid4().hex[:8]}"
banned_ops = re.compile(r"(dry-run|deploy_[a-z]|\.143\b|Agir\b|VS Code|Cline)", re.I)
short_trap = re.compile(r"(?i)^\s*(allons[- ]?y\.?\s*)?(je te suis\.?\s*)+$")
plan_m = re.compile(r"(?i)(objectif|phases?|prochaine action|##\s|1\.|-\s)", re.M)

turns = [
    ("T1_greeting", "Bonjour, comment ça va aujourd’hui ?", "c2_open"),
    ("T2_follow", "bien merci, et toi ?", "c2_open"),
    ("T3_collegues", "Discutons comme collègues du projet", "c2_avis"),
    ("T4_mmo", "On travaille le MMORPG et l’incarnation des joueurs IA", "c1"),
    # Éviter « hub / retour présence » (tool_loop ops) — rester en causerie.
    ("T5_zone", "pour moi l’environnement jeu doit rester une zone d’entraînement des personas, pas un dump ops", "c1"),
    ("T6_plan", "prépare le plan d’action pour le studio et commence", "plan"),
    ("T7_go", "allons y", "go"),
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
    with urllib.request.urlopen(req, timeout=180) as resp:
        d = json.load(resp)
    r = d.get("response") or {}
    text = str(r.get("content") or r.get("response") or r.get("raw") or "")
    src = str(r.get("source") or r.get("model_used") or r.get("model") or "")
    return text, src, r

results = []
for tid, prompt, kind in turns:
    text, src, raw = ask(prompt)
    ops = banned_ops.findall(text)
    print(f"== {tid} src={src} len={len(text)} ops={ops} ==")
    print(text[:280].replace("\n", " "))
    print()
    results.append((tid, kind, text, src, ops))

# --- scores ---
c2_fail = []
for tid, kind, text, src, ops in results:
    if kind == "c2_open":
        if ops or "lab_ops" in src.lower():
            c2_fail.append(f"{tid}: ops leak {ops or src}")
        if "Que veux-tu faire" in text and len(text) < 80:
            c2_fail.append(f"{tid}: empty reflection")
    if kind == "c2_avis":
        # au moins une phrase d’avis / position
        if len(text) < 40:
            c2_fail.append(f"{tid}: too thin")

c1_ok = True
t4 = next(t for t in results if t[0] == "T4_mmo")[2]
t5 = next(t for t in results if t[0] == "T5_zone")[2]
if re.search(r"(?i)(quel est (ton|votre) objectif|je suis une IA générique)", t5):
    c1_ok = False

t6 = next(t for t in results if t[0] == "T6_plan")
t7 = next(t for t in results if t[0] == "T7_go")
plan_ok = bool(plan_m.search(t6[2])) or bool(plan_m.search(t7[2]))
go_trap = bool(short_trap.match(t7[2].strip()))

print("--- verdict ---")
print("C1=", "PASS" if c1_ok else "FAIL")
print("C2=", "PASS" if not c2_fail else f"FAIL {c2_fail}")
print("PLAN=", "PASS" if plan_ok else "FAIL")
print("GO_AHEAD=", "FAIL short_social trap" if go_trap else "PASS")
print("cid=", cid)

assert c1_ok, "C1 continuity fail"
assert not c2_fail, c2_fail
assert plan_ok, f"no plan artefact: t6={t6[2][:200]!r} t7={t7[2][:200]!r}"
assert not go_trap, f"go-ahead trap: {t7[2]!r}"
print("SMOKE_REJEU_HUMAIN_D6_OK")
PY
