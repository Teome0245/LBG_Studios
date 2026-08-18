#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VM_HOST="${LBG_CORE_VM_HOST:-192.168.0.140}"
VM_USER="${LBG_CORE_VM_USER:-lbg}"
echo "=== Install lbg-team-evolution-sprint-job → ${VM_USER}@${VM_HOST} (timer 7j) ==="
scp -q \
  "${ROOT_DIR}/infra/systemd/lbg-team-evolution-sprint-job.service" \
  "${ROOT_DIR}/infra/systemd/lbg-team-evolution-sprint-job.timer" \
  "${VM_USER}@${VM_HOST}:/tmp/"
ssh "${VM_USER}@${VM_HOST}" "bash -s" <<'EOF'
set -euo pipefail
sudo mkdir -p /var/lib/lbg/team_evolution
sudo chown lbg:lbg /var/lib/lbg/team_evolution
sudo cp /tmp/lbg-team-evolution-sprint-job.service /tmp/lbg-team-evolution-sprint-job.timer /etc/systemd/system/
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
touch_env LBG_TEAM_EVOLUTION_ENABLED 1
touch_env LBG_TEAM_EVOLUTION_JOB_ENABLED 1
touch_env LBG_TEAM_EVOLUTION_L1_AUTO_RUN 1
touch_env LBG_TEAM_EVOLUTION_JOB_COOLDOWN_S 518400
touch_env LBG_TEAM_EVOLUTION_PLATFORM_AUDIT 1
sudo systemctl daemon-reload
sudo systemctl enable lbg-team-evolution-sprint-job.timer
sudo systemctl restart lbg-team-evolution-sprint-job.timer
systemctl is-active lbg-team-evolution-sprint-job.timer
systemctl list-timers 'lbg-team-evolution-sprint*' --no-pager
EOF
echo "OK — sprint évolution 7j · L1 auto · L2 file Pilot · docs/team_evolution_sprint.md"
