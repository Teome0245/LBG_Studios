#!/usr/bin/env bash
# Preuve phase E (vision Fable §8) — à lancer depuis le poste ou sur 140.
# Usage:
#   LBG_ORCHESTRATOR_URL=http://192.168.0.140:8010 bash infra/scripts/prove_phase_e_140.sh
set -u
ORCH="${LBG_ORCHESTRATOR_URL:-http://127.0.0.1:8010}"
SSH_HOST="${LBG_CORE_VM_HOST:-192.168.0.140}"
SSH_USER="${LBG_CORE_VM_USER:-lbg}"
OK=0
KO=0

mark() {
  local name="$1" pass="$2" detail="${3:-}"
  if [[ "$pass" == "1" ]]; then
    echo "OK  $name  $detail"
    OK=$((OK + 1))
  else
    echo "KO  $name  $detail"
    KO=$((KO + 1))
  fi
}

echo "=== Preuve phase E Team (Fable §8) ==="
echo "orch=$ORCH"

timer_out=$(ssh -o BatchMode=yes -o ConnectTimeout=5 "${SSH_USER}@${SSH_HOST}" \
  'systemctl is-active lbg-team-autoconsult-job.timer; systemctl is-enabled lbg-team-autoconsult-job.timer' 2>/dev/null || echo "fail")
if echo "$timer_out" | grep -qx active && echo "$timer_out" | grep -qx enabled; then
  mark "autoconsult_timer" 1 "active+enabled"
else
  mark "autoconsult_timer" 0 "$timer_out"
fi

state=$(ssh -o BatchMode=yes -o ConnectTimeout=5 "${SSH_USER}@${SSH_HOST}" \
  'python3 -c "import json;d=json.load(open(\"/var/lib/lbg/team_autoconsult/state.json\"));print(int(bool(d.get(\"last_task_ok\"))), d.get(\"last_task_id\",\"\")[:8])"' 2>/dev/null || echo "0 fail")
read -r state_ok state_id <<<"$state"
mark "last_autoconsult_ok" "${state_ok:-0}" "task=${state_id:-?}"

curl -sS -o /tmp/lbg_phase_e_meta.json --connect-timeout 4 --max-time 15 \
  "$ORCH/v1/team/meta" >/dev/null || true

python3 - <<'PY' >/tmp/lbg_phase_e_checks.txt
import json
from pathlib import Path
p = Path("/tmp/lbg_phase_e_meta.json")
if not p.is_file() or p.stat().st_size < 10:
    print("meta 0 empty")
    raise SystemExit
d = json.loads(p.read_text())
ags = d.get("agents") or []
ids = {a.get("agent_id") for a in ags}
feat = d.get("features") or {}
l3 = feat.get("iris_l3") or {}
print("meta_agents", int(len(ags) >= 10 and "studio_admin_atlas" in ids), f"n={len(ags)}")
print("iris_l3", int(bool(l3.get("l3_enabled"))), "")
print("write_paths", int(bool(feat.get("write_paths"))), "")
print("adr0019", int(feat.get("adr") == "0019"), "")
PY

while read -r name pass detail; do
  mark "$name" "$pass" "$detail"
done < /tmp/lbg_phase_e_checks.txt

tok=$(ssh -o BatchMode=yes -o ConnectTimeout=5 "${SSH_USER}@${SSH_HOST}" \
  'grep -E "^LBG_TEAM_APPROVAL_TOKEN=.+" /etc/lbg-ia-mmo.env >/dev/null && echo 1 || echo 0' 2>/dev/null || echo 0)
mark "approval_token_configured" "$tok" ""

echo
echo "Résumé: OK=$OK KO=$KO"
[[ "$KO" -eq 0 ]]
