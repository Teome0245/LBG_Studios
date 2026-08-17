#!/usr/bin/env bash
# Smoke missions hub — board / accept / gate / progress / complete sur :8791
# Joueur IA : LBG_M10_STUB_PLAYER=Lia|Nix bash …
set -euo pipefail

SIDECAR="${LBG_SIDECAR_HTTP:-http://192.168.0.246:8791}"
SIDECAR="${SIDECAR%/}"
PLAYER="${LBG_M10_STUB_PLAYER:-local}"
QUEST="${LBG_QUEST_SMOKE_ID:-lh_delivery_starport}"
GIVER="${LBG_QUEST_GIVER:-npc:core3_daan_oth}"

echo "=== Smoke quest hub (Lost Heaven) ==="
echo "sidecar: ${SIDECAR}"
echo "player:  ${PLAYER}"

curl -sfS --max-time 8 "${SIDECAR}/healthz" >/dev/null || {
  echo "FAIL: /healthz" >&2
  exit 1
}

tmp="$(mktemp)"
accept_out="$(mktemp)"
early="$(mktemp)"
complete_out="$(mktemp)"
trap 'rm -f "${tmp}" "${accept_out}" "${early}" "${complete_out}"' EXIT

# Reset d'abord — board filtre les missions déjà rendues (P2b rotation)
curl -sfS --max-time 10 -X POST "${SIDECAR}/v1/quests/reset" \
  -H 'Content-Type: application/json' \
  -d "{\"player\":\"${PLAYER}\"}" >/dev/null

curl -sfS --max-time 10 \
  "${SIDECAR}/v1/quests/board?giver=${GIVER}&player=${PLAYER}" -o "${tmp}" || {
  echo "FAIL: GET /v1/quests/board" >&2
  exit 2
}

QUEST_ID="${QUEST}" python3 - "${tmp}" <<'PY'
import json, os, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
quests = d.get("quests") or []
if not isinstance(quests, list) or not quests:
    raise SystemExit("FAIL: board vide")
qid = os.environ.get("QUEST_ID", "lh_delivery_starport")
by_id = {str(q.get("id")): q for q in quests if isinstance(q, dict)}
ids = list(by_id)
if qid not in by_id:
    raise SystemExit(f"FAIL: {qid} absent ({ids[:5]})")
# P2b — objectifs terrain : chaînes progress sur board
for need in ("lh_escort_gate_clinic", "lh_enquete_marche"):
    row = by_id.get(need)
    if row is None:
        raise SystemExit(f"FAIL: {need} absent après reset")
    prog = row.get("progress") or []
    if not isinstance(prog, list) or len(prog) < 2:
        raise SystemExit(f"FAIL: {need} progress insuffisant: {prog}")
    for step in prog:
        if not isinstance(step, dict) or not step.get("poi"):
            raise SystemExit(f"FAIL: {need} étape sans poi: {step}")
print(f"OK board — {len(quests)} offres (+ progress terrain escort/enquête)")
PY

http_a="$(curl -sS -o "${accept_out}" -w '%{http_code}' --max-time 10 \
  -X POST "${SIDECAR}/v1/quests/accept" \
  -H 'Content-Type: application/json' \
  -d "{\"player\":\"${PLAYER}\",\"quest_id\":\"${QUEST}\",\"giver_id\":\"${GIVER}\"}" || true)"
[[ "${http_a}" == "200" ]] || { echo "FAIL accept ${http_a} $(head -c 200 ${accept_out})"; exit 6; }
echo "OK accept — ${QUEST}"

http_e="$(curl -sS -o "${early}" -w '%{http_code}' --max-time 10 \
  -X POST "${SIDECAR}/v1/quests/complete" \
  -H 'Content-Type: application/json' \
  -d "{\"player\":\"${PLAYER}\",\"quest_id\":\"${QUEST}\"}" || true)"
python3 - <<PY
import json
d=json.load(open("${early}", encoding="utf-8"))
assert d.get("ok") is False and d.get("error")=="objectives_incomplete", d
print("OK gate — complete bloqué sans objectifs")
PY

curl -sfS --max-time 10 -X POST "${SIDECAR}/v1/quests/progress" \
  -H 'Content-Type: application/json' \
  -d "{\"player\":\"${PLAYER}\",\"quest_id\":\"${QUEST}\",\"step_id\":\"pickup\"}" >/dev/null
curl -sfS --max-time 10 -X POST "${SIDECAR}/v1/quests/progress" \
  -H 'Content-Type: application/json' \
  -d "{\"player\":\"${PLAYER}\",\"quest_id\":\"${QUEST}\",\"step_id\":\"deliver\"}" >/dev/null

http_c="$(curl -sS -o "${complete_out}" -w '%{http_code}' --max-time 10 \
  -X POST "${SIDECAR}/v1/quests/complete" \
  -H 'Content-Type: application/json' \
  -d "{\"player\":\"${PLAYER}\",\"quest_id\":\"${QUEST}\"}" || true)"
[[ "${http_c}" == "200" ]] || { echo "FAIL complete ${http_c} $(head -c 200 ${complete_out})"; exit 7; }
python3 - <<PY
import json
d=json.load(open("${complete_out}", encoding="utf-8"))
assert d.get("ok") is True, d
assert "${QUEST}" in (d.get("completed") or []), d
print(f"OK complete — ${QUEST} +{(d.get('reward_applied') or {}).get('credits_gained', 0)} Cr")
print("OK quest hub smoke player=${PLAYER} (board + gate + progress + complete)")
PY
