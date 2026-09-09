#!/usr/bin/env bash
# Installe les timers playbooks ops équipe (stockage + Ollama + HW + locks + guest mur) sur VM core 140.
#
# Usage :
#   bash infra/scripts/install_team_ops_jobs_vm.sh
#   LBG_CORE_VM_HOST=192.168.0.140 bash infra/scripts/install_team_ops_jobs_vm.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VM_HOST="${LBG_CORE_VM_HOST:-192.168.0.140}"
VM_USER="${LBG_CORE_VM_USER:-lbg}"

echo "=== Install lbg-team-ops-* → ${VM_USER}@${VM_HOST} ==="

scp -q \
  "${ROOT_DIR}/infra/systemd/lbg-team-ops-storage-job.service" \
  "${ROOT_DIR}/infra/systemd/lbg-team-ops-storage-job.timer" \
  "${ROOT_DIR}/infra/systemd/lbg-team-ops-ollama-job.service" \
  "${ROOT_DIR}/infra/systemd/lbg-team-ops-ollama-job.timer" \
  "${ROOT_DIR}/infra/systemd/lbg-team-ops-hw-job.service" \
  "${ROOT_DIR}/infra/systemd/lbg-team-ops-hw-job.timer" \
  "${ROOT_DIR}/infra/systemd/lbg-team-ops-lock-job.service" \
  "${ROOT_DIR}/infra/systemd/lbg-team-ops-lock-job.timer" \
  "${ROOT_DIR}/infra/systemd/lbg-team-ops-guest-job.service" \
  "${ROOT_DIR}/infra/systemd/lbg-team-ops-guest-job.timer" \
  "${VM_USER}@${VM_HOST}:/tmp/"

ssh "${VM_USER}@${VM_HOST}" "bash -s" <<'EOF'
set -euo pipefail
sudo mkdir -p /var/lib/lbg/team_ops_storage /var/lib/lbg/team_ops_ollama /var/lib/lbg/team_ops_hw /var/lib/lbg/team_ops_lock /var/lib/lbg/team_ops_guest
sudo chown lbg:lbg /var/lib/lbg/team_ops_storage /var/lib/lbg/team_ops_ollama /var/lib/lbg/team_ops_hw /var/lib/lbg/team_ops_lock /var/lib/lbg/team_ops_guest
for u in lbg-team-ops-storage-job lbg-team-ops-ollama-job lbg-team-ops-hw-job lbg-team-ops-lock-job lbg-team-ops-guest-job; do
  sudo cp "/tmp/${u}.service" "/tmp/${u}.timer" /etc/systemd/system/
done
sudo systemctl daemon-reload
sudo systemctl enable lbg-team-ops-storage-job.timer lbg-team-ops-ollama-job.timer lbg-team-ops-hw-job.timer lbg-team-ops-lock-job.timer lbg-team-ops-guest-job.timer
sudo systemctl start lbg-team-ops-storage-job.timer lbg-team-ops-ollama-job.timer lbg-team-ops-hw-job.timer lbg-team-ops-lock-job.timer lbg-team-ops-guest-job.timer
systemctl is-active lbg-team-ops-storage-job.timer lbg-team-ops-ollama-job.timer lbg-team-ops-hw-job.timer lbg-team-ops-lock-job.timer lbg-team-ops-guest-job.timer
systemctl list-timers 'lbg-team-ops-*' --no-pager
EOF

echo ""
echo "OK — tâches visibles sur http://192.168.0.140:8080/#/team"
echo "  actor: system:team_ops_storage | system:team_ops_ollama | system:team_ops_hw | system:team_ops_lock | system:team_ops_guest"
echo "Prérequis SSH guest (depuis 140) :"
echo "  for h in 192.168.0.100 192.168.0.245 192.168.0.246; do ssh -o BatchMode=yes lbg@\$h 'hostname'; done"
echo "Test manuel guest mur :"
echo "  ssh ${VM_USER}@${VM_HOST} 'sudo systemctl start lbg-team-ops-guest-job.service && journalctl -u lbg-team-ops-guest-job -n 40 --no-pager'"
