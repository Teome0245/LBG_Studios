#!/usr/bin/env bash
# Active ou désactive le stockage nas-lun-backup sur l'hyperviseur Proxmox .201
# Usage :
#   bash infra/scripts/toggle_proxmox_nas_storage.sh disable
#   bash infra/scripts/toggle_proxmox_nas_storage.sh enable
#   bash infra/scripts/toggle_proxmox_nas_storage.sh status
set -euo pipefail

ACTION="${1:-disable}"
HOST="${LBG_PROXMOX_HOST:-192.168.0.201}"
USER="${LBG_PROXMOX_SSH_USER:-root}"

case "$ACTION" in
  disable)
    echo "[-] Désactivation du stockage nas-lun-backup sur Proxmox ${HOST}..."
    ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new "${USER}@${HOST}" "pvesm set nas-lun-backup --disable 1"
    echo "[+] Stockage nas-lun-backup désactivé avec succès."
    ;;
  enable)
    echo "[+] Activation du stockage nas-lun-backup sur Proxmox ${HOST}..."
    ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new "${USER}@${HOST}" "pvesm set nas-lun-backup --disable 0"
    echo "[+] Stockage nas-lun-backup réactivé avec succès."
    ;;
  status|*)
    ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new "${USER}@${HOST}" "pvesm status | grep nas-lun-backup || echo 'Non trouvé'"
    ;;
esac
