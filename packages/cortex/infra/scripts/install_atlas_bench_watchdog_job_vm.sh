#!/usr/bin/env bash
# Installe le timer Atlas bench watchdog sur la VM core (140).

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VM_HOST="${LBG_CORE_VM_HOST:-192.168.0.140}"
VM_USER="${LBG_CORE_VM_USER:-lbg}"

echo "=== Install lbg-atlas-bench-watchdog-job → ${VM_USER}@${VM_HOST} ==="

scp -q \
  "${ROOT_DIR}/infra/systemd/lbg-atlas-bench-watchdog-job.service" \
  "${ROOT_DIR}/infra/systemd/lbg-atlas-bench-watchdog-job.timer" \
  "${VM_USER}@${VM_HOST}:/tmp/"

ssh "${VM_USER}@${VM_HOST}" "bash -s" <<'EOF'
set -euo pipefail
sudo mkdir -p /var/lib/lbg/atlas_bench_watchdog
sudo chown lbg:lbg /var/lib/lbg/atlas_bench_watchdog
sudo cp /tmp/lbg-atlas-bench-watchdog-job.service /tmp/lbg-atlas-bench-watchdog-job.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable lbg-atlas-bench-watchdog-job.timer
sudo systemctl start lbg-atlas-bench-watchdog-job.timer
systemctl is-active lbg-atlas-bench-watchdog-job.timer
systemctl list-timers lbg-atlas-bench-watchdog-job.timer --no-pager
EOF

echo ""
echo "OK — watchdog Atlas bench (seuil + retry KO + Element si < seuil)"
echo "Test manuel :"
echo "  ssh ${VM_USER}@${VM_HOST} 'sudo systemctl start lbg-atlas-bench-watchdog-job.service'"
