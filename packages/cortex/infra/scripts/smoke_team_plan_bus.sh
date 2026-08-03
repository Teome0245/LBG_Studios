#!/usr/bin/env bash
# Smoke ADR 0019 — plan + messages (+ optionnel mémoire / campus).
# Usage:
#   bash packages/cortex/infra/scripts/smoke_team_plan_bus.sh
#   LBG_ORCHESTRATOR_URL=http://192.168.0.140:8010 bash ...
set -u
ORCH="${LBG_ORCHESTRATOR_URL:-http://127.0.0.1:8010}"
PILOT="${LBG_PILOT_URL:-http://192.168.0.140:8080}"
OK=0
KO=0

check() {
  local name="$1" code="$2" expect="$3"
  if [[ "$code" == "$expect" ]]; then
    echo "OK  $name  HTTP $code"
    OK=$((OK + 1))
  else
    echo "KO  $name  HTTP $code (attendu $expect)"
    KO=$((KO + 1))
  fi
}

echo "=== Smoke Team plan + bus (ADR 0019) ==="
echo "orch=$ORCH"

code=$(curl -sS -o /tmp/lbg_team_meta.json -w "%{http_code}" --connect-timeout 4 --max-time 15 \
  "$ORCH/v1/team/meta" || echo "000")
check "GET /v1/team/meta" "$code" "200"

code=$(curl -sS -o /tmp/lbg_team_plan.json -w "%{http_code}" --connect-timeout 4 --max-time 60 \
  -X POST "$ORCH/v1/team/plan" -H 'Content-Type: application/json' \
  -d '{"objective":"valide le LAN et brief PM","actor_id":"smoke:adr0019","use_llm":false}' || echo "000")
check "POST /v1/team/plan (heuristic)" "$code" "200"
if [[ "$code" == "200" ]]; then
  python3 - <<'PY'
import json
d=json.load(open("/tmp/lbg_team_plan.json"))
assert d.get("source") in ("heuristic","llm","hybrid"), d
assert isinstance(d.get("proposals"), list) and len(d["proposals"])>=1
print("   source=", d.get("source"), "n=", len(d["proposals"]))
PY
fi

code=$(curl -sS -o /tmp/lbg_team_msg.json -w "%{http_code}" --connect-timeout 4 --max-time 15 \
  -X POST "$ORCH/v1/team/messages" -H 'Content-Type: application/json' \
  -d '{"from_agent":"smoke","to_agent":"themis","kind":"consult","payload":{"topic":"smoke_adr0019"},"task_id":"smoke-task","actor_id":"smoke:adr0019"}' || echo "000")
check "POST /v1/team/messages" "$code" "200"

code=$(curl -sS -o /tmp/lbg_team_msgs.json -w "%{http_code}" --connect-timeout 4 --max-time 15 \
  "$ORCH/v1/team/messages?task_id=smoke-task&limit=5" || echo "000")
check "GET /v1/team/messages" "$code" "200"

code=$(curl -sS -o /tmp/lbg_team_closure.json -w "%{http_code}" --connect-timeout 4 --max-time 15 \
  "$ORCH/v1/team/campus/mission/closure" || echo "000")
check "GET /v1/team/campus/mission/closure" "$code" "200"

# Proxy Pilot (same-origin) si joignable
code=$(curl -sS -o /tmp/lbg_pilot_plan.json -w "%{http_code}" --connect-timeout 4 --max-time 30 \
  -X POST "$PILOT/v1/pilot/team/plan" -H 'Content-Type: application/json' \
  -d '{"objective":"smoke LAN","actor_id":"smoke:adr0019","use_llm":false}' 2>/dev/null || echo "000")
if [[ "$code" == "200" ]]; then
  echo "OK  Pilot proxy /v1/pilot/team/plan  HTTP $code"
  OK=$((OK + 1))
else
  echo "WARN  Pilot proxy plan  HTTP $code (orch direct OK suffit)"
fi

echo
echo "Résumé: OK=$OK KO=$KO"
[[ "$KO" -eq 0 ]]
