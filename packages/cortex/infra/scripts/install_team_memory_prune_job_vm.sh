#!/usr/bin/env bash
# Héphaïstos — installe le timer prune mémoire Team (ADR 0019 Vague 4).
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VM_HOST="${LBG_CORE_VM_HOST:-192.168.0.140}"
VM_USER="${LBG_CORE_VM_USER:-lbg}"

echo "=== Install lbg-team-memory-prune-job → ${VM_USER}@${VM_HOST} (timer 7j) ==="
scp -q \
  "${ROOT_DIR}/infra/systemd/lbg-team-memory-prune-job.service" \
  "${ROOT_DIR}/infra/systemd/lbg-team-memory-prune-job.timer" \
  "${ROOT_DIR}/infra/scripts/prune_team_memory.sh" \
  "${VM_USER}@${VM_HOST}:/tmp/"

ssh "${VM_USER}@${VM_HOST}" "bash -s" <<'EOF'
set -euo pipefail
sudo mkdir -p /opt/LBG_Studios/packages/cortex/infra/scripts
sudo cp /tmp/prune_team_memory.sh /opt/LBG_Studios/packages/cortex/infra/scripts/
sudo chmod +x /opt/LBG_Studios/packages/cortex/infra/scripts/prune_team_memory.sh
sudo cp /tmp/lbg-team-memory-prune-job.service /tmp/lbg-team-memory-prune-job.timer /etc/systemd/system/
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
touch_env LBG_TEAM_MEMORY_ENABLED 1
touch_env LBG_TEAM_MEMORY_MAX_ENTRIES 500
touch_env LBG_TEAM_MEMORY_MAX_AGE_DAYS 30
sudo systemctl daemon-reload
sudo systemctl enable --now lbg-team-memory-prune-job.timer
systemctl list-timers 'lbg-team-memory-prune*' --no-pager || true
EOF
echo "OK — prune mémoire 7j"
