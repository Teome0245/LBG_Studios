#!/usr/bin/env bash
# Statut mission L3 smoke LAN (days_ok / N) — ne force pas le compteur calendaire.
# Usage: bash tools/status_l3_smoke_lan_mission.sh [ORCH_BASE]
set -euo pipefail
BASE="${1:-http://192.168.0.140:8010}"
BASE="${BASE%/}"

echo "== mission =="
curl -sS --max-time 15 "$BASE/v1/team/smoke_lan_mission" | python3 -c '
import sys, json, datetime
d = json.load(sys.stdin)
assert d.get("ok") is True, d
m = d.get("mission") or {}
ok = int(m.get("days_ok") or 0)
target = int(m.get("days_target") or 3)
last = str(m.get("last_ok_day") or "")
today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
print("status=", m.get("status"), "days_ok=", f"{ok}/{target}", "last_ok_day=", last, "decision=", m.get("last_decision"))
print("deadline_in_h=", m.get("deadline_in_h"), "consecutive_red=", m.get("consecutive_red"), "retries=", m.get("retries_used"), "/", m.get("budget_retries"))
if str(m.get("status")) == "done" and ok >= target:
    print("L3_SMOKE_LAN_MISSION_DONE")
elif ok >= target:
    print("L3_SMOKE_LAN_MISSION_DAYS_MET status=", m.get("status"))
elif last == today:
    print("L3_SMOKE_LAN_MISSION_ARMED_WAIT_UTC — tick live après minuit UTC (aujourd hui déjà compté)")
else:
    print("L3_SMOKE_LAN_MISSION_READY_FOR_TICK — POST /v1/team/smoke_lan_mission/tick dry_run=false")
'

echo "== perimeter dry =="
curl -sS --max-time 60 -X POST "$BASE/v1/team/ops_health_pilot" \
  -H 'Content-Type: application/json' -d '{"dry_run":true}' | python3 -c '
import sys, json
d = json.load(sys.stdin)
assert d.get("ok") is True, d
assert d.get("decision") == "healthy", d.get("decision")
print("ok perimeter healthy dry_run")
'
