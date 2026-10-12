#!/usr/bin/env bash
# Install timer Ops Health Pilot sur VM 140 (dry-run par défaut).
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
VM_HOST="${VM_HOST:-192.168.0.140}"
VM_USER="${VM_USER:-lbg}"

echo "=== Install lbg-ops-health-pilot-job → ${VM_USER}@${VM_HOST} ==="
scp -q \
  "${ROOT_DIR}/infra/systemd/lbg-ops-health-pilot-job.service" \
  "${ROOT_DIR}/infra/systemd/lbg-ops-health-pilot-job.timer" \
  "${VM_USER}@${VM_HOST}:/tmp/"

ssh "${VM_USER}@${VM_HOST}" 'bash -s' <<'REMOTE'
set -euo pipefail
sudo mkdir -p /var/lib/lbg/ops_health_pilot
sudo chown lbg:lbg /var/lib/lbg/ops_health_pilot
sudo cp /tmp/lbg-ops-health-pilot-job.service /tmp/lbg-ops-health-pilot-job.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable lbg-ops-health-pilot-job.timer
sudo systemctl start lbg-ops-health-pilot-job.timer
systemctl is-active lbg-ops-health-pilot-job.timer
systemctl list-timers lbg-ops-health-pilot-job.timer --no-pager
REMOTE

echo "OK. Dry-run par défaut (LBG_OPS_HEALTH_PILOT_DRY_RUN=1)."
echo "Live : mettre LBG_OPS_HEALTH_PILOT_DRY_RUN=0 + NOTIFY=1 dans /etc/lbg-ia-mmo.env puis restart timer."
echo "  ssh ${VM_USER}@${VM_HOST} 'sudo systemctl start lbg-ops-health-pilot-job.service && journalctl -u lbg-ops-health-pilot-job -n 30 --no-pager'"
