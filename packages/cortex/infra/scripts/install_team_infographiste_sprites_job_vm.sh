#!/usr/bin/env bash
# Installe le timer lbg-team-infographiste-sprites-job sur la VM core (140).
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VM_HOST="${LBG_CORE_VM_HOST:-192.168.0.140}"
VM_USER="${LBG_CORE_VM_USER:-lbg}"
echo "=== Install lbg-team-infographiste-sprites-job → ${VM_USER}@${VM_HOST} ==="
scp -q \
  "${ROOT_DIR}/infra/systemd/lbg-team-infographiste-sprites-job.service" \
  "${ROOT_DIR}/infra/systemd/lbg-team-infographiste-sprites-job.timer" \
  "${VM_USER}@${VM_HOST}:/tmp/"
ssh "${VM_USER}@${VM_HOST}" "bash -s" <<'EOF'
set -euo pipefail
sudo mkdir -p /var/lib/lbg/team_infographiste
sudo chown lbg:lbg /var/lib/lbg/team_infographiste
sudo cp /tmp/lbg-team-infographiste-sprites-job.service /tmp/lbg-team-infographiste-sprites-job.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable lbg-team-infographiste-sprites-job.timer
sudo systemctl start lbg-team-infographiste-sprites-job.timer
systemctl is-active lbg-team-infographiste-sprites-job.timer
EOF
echo "OK — actor system:team_infographiste_sprites"
