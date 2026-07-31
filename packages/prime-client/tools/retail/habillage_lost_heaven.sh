#!/usr/bin/env bash
# Lost Heaven — gabarit ME + export PNJ + (optionnel) sprites overhead → B:/J:
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRIME="$(cd "${SCRIPT_DIR}/../.." && pwd)"

echo "=== 1/3 Gabarit Mos Eisley → Lost Heaven ==="
python3 "${SCRIPT_DIR}/apply_mos_eisley_gabarit_lost_heaven.py"

echo "=== 2/3 PNJ serveur 246 (zone LH) ==="
bash "${SCRIPT_DIR}/export_server_npcs_lost_heaven.sh" || true

echo "=== 3/3 Sync client ==="
if [[ -d /mnt/j/swgemu/clients/prime-client ]]; then
  rsync -av "${PRIME}/assets/maps/" /mnt/j/swgemu/clients/prime-client/assets/maps/
  rsync -av "${PRIME}/scenes/main.tscn" /mnt/j/swgemu/clients/prime-client/scenes/
fi

echo "OK — Godot : city_id=lost_heaven, Ctrl+Shift+R overlay gabarit"
