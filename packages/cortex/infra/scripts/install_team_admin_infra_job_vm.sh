#!/usr/bin/env bash
# Installe le timer Atlas admin_infra sur la VM core (140).

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VM_HOST="${LBG_CORE_VM_HOST:-192.168.0.140}"
VM_USER="${LBG_CORE_VM_USER:-lbg}"

echo "=== Install lbg-team-admin-infra-job → ${VM_USER}@${VM_HOST} ==="

scp -q \
  "${ROOT_DIR}/infra/systemd/lbg-team-admin-infra-job.service" \
  "${ROOT_DIR}/infra/systemd/lbg-team-admin-infra-job.timer" \
  "${VM_USER}@${VM_HOST}:/tmp/"

ssh "${VM_USER}@${VM_HOST}" "bash -s" <<'EOF'
set -euo pipefail
sudo mkdir -p /var/lib/lbg/team_admin_infra
sudo chown lbg:lbg /var/lib/lbg/team_admin_infra
sudo cp /tmp/lbg-team-admin-infra-job.service /tmp/lbg-team-admin-infra-job.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable lbg-team-admin-infra-job.timer
sudo systemctl start lbg-team-admin-infra-job.timer
systemctl is-active lbg-team-admin-infra-job.timer
systemctl list-timers lbg-team-admin-infra-job.timer --no-pager
EOF

echo ""
echo "OK — Atlas récurrent visible sur http://192.168.0.110:8080/#/team"
echo "  actor: system:team_admin_infra"
echo "Test manuel :"
echo "  ssh ${VM_USER}@${VM_HOST} 'sudo systemctl start lbg-team-admin-infra-job.service && journalctl -u lbg-team-admin-infra-job -n 20 --no-pager'"
