#!/usr/bin/env bash
# Install timer inventaire réseau sur VM 140 (toutes les 30 min).
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
VM_HOST="${VM_HOST:-192.168.0.140}"
VM_USER="${VM_USER:-lbg}"

echo "=== Install lbg-network-inventory-job → ${VM_USER}@${VM_HOST} ==="
scp -q \
  "${ROOT_DIR}/infra/systemd/lbg-network-inventory-job.service" \
  "${ROOT_DIR}/infra/systemd/lbg-network-inventory-job.timer" \
  "${ROOT_DIR}/agents/src/lbg_agents/network_inventory.py" \
  "${ROOT_DIR}/agents/src/lbg_agents/spawn_network_inventory_job.py" \
  "${ROOT_DIR}/agents/src/lbg_agents/freebox_client.py" \
  "${VM_USER}@${VM_HOST}:/tmp/"

ssh "${VM_USER}@${VM_HOST}" 'bash -s' <<'REMOTE'
set -euo pipefail
sudo mkdir -p /var/lib/lbg/network_inventory
sudo chown lbg:lbg /var/lib/lbg/network_inventory
cp /tmp/network_inventory.py /opt/LBG_IA_MMO/agents/src/lbg_agents/network_inventory.py
cp /tmp/spawn_network_inventory_job.py /opt/LBG_IA_MMO/agents/src/lbg_agents/spawn_network_inventory_job.py
cp /tmp/freebox_client.py /opt/LBG_IA_MMO/agents/src/lbg_agents/freebox_client.py
sudo cp /tmp/lbg-network-inventory-job.service /tmp/lbg-network-inventory-job.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable lbg-network-inventory-job.timer
sudo systemctl restart lbg-network-inventory-job.timer
systemctl is-active lbg-network-inventory-job.timer
# Première passe immédiate
sudo systemctl start lbg-network-inventory-job.service
sleep 1
journalctl -u lbg-network-inventory-job -n 20 --no-pager
systemctl list-timers lbg-network-inventory-job.timer --no-pager
REMOTE

echo "OK. Scan toutes les 30 min. Notify : LBG_NETWORK_INVENTORY_NOTIFY=1 dans /etc/lbg-ia-mmo.env"
