#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VM_HOST="${LBG_CORE_VM_HOST:-192.168.0.140}"
VM_USER="${LBG_CORE_VM_USER:-lbg}"
echo "=== Install lbg-team-campus-conductor-job → ${VM_USER}@${VM_HOST} (timer 5min) ==="
scp -q \
  "${ROOT_DIR}/infra/systemd/lbg-team-campus-conductor-job.service" \
  "${ROOT_DIR}/infra/systemd/lbg-team-campus-conductor-job.timer" \
  "${VM_USER}@${VM_HOST}:/tmp/"
ssh "${VM_USER}@${VM_HOST}" "bash -s" <<'EOF'
set -euo pipefail
sudo mkdir -p /var/lib/lbg/team_campus_conductor
sudo chown lbg:lbg /var/lib/lbg/team_campus_conductor
sudo cp /tmp/lbg-team-campus-conductor-job.service /tmp/lbg-team-campus-conductor-job.timer /etc/systemd/system/
ENV_FILE=/etc/lbg-ia-mmo.env
touch_env() {
  local key="$1" val="$2"
  if grep -q "^${key}=" "$ENV_FILE" 2>/dev/null; then
    sudo sed -i "s|^${key}=.*|${key}=${val}|" "$ENV_FILE"
  else
    echo "${key}=${val}" | sudo tee -a "$ENV_FILE" >/dev/null
  fi
}
sudo touch "$ENV_FILE"
touch_env LBG_TEAM_CAMPUS_CONDUCTOR_ENABLED 1
touch_env LBG_TEAM_CAMPUS_CONDUCTOR_MAX_BUSY 4
touch_env LBG_TEAM_CAMPUS_CONDUCTOR_MAX_STARTS 2
touch_env LBG_TEAM_CAMPUS_CONDUCTOR_ROLES "qa,ops,pm,admin_infra,dev_game,dev_godot"
touch_env LBG_TEAM_CAMPUS_CONDUCTOR_JOB_ENABLED 1
touch_env LBG_TEAM_CAMPUS_CONDUCTOR_COFFEE_FILL 1
touch_env LBG_TEAM_CAMPUS_CONDUCTOR_COFFEE_MIN 3
touch_env LBG_TEAM_CAMPUS_CONDUCTOR_COFFEE_MAX_SPAWN 1
touch_env LBG_TEAM_CAMPUS_CONDUCTOR_COFFEE_COOLDOWN_S 1800
sudo systemctl daemon-reload
sudo systemctl enable lbg-team-campus-conductor-job.timer
sudo systemctl restart lbg-team-campus-conductor-job.timer
# Relance orchestrateur pour charger ENABLED + déclaration Lyra
sudo systemctl restart lbg-orchestrator || true
sleep 2
systemctl is-active lbg-team-campus-conductor-job.timer
systemctl list-timers 'lbg-team-campus-conductor*' --no-pager
curl -sf http://127.0.0.1:8010/v1/team/campus/status | head -c 400; echo
EOF
echo "OK — campus conductor 5min · docs/plan_campus_conductor.md"
