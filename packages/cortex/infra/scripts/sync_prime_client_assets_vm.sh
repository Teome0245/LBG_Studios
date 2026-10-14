#!/usr/bin/env bash
# Sync assets Prime Client (maps + config minimap) vers VM core pour sondes M9.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC="${LBG_PRIME_CLIENT_ROOT:-${ROOT_DIR}/../prime-client}"
if [[ ! -d "${SRC}" ]]; then
  echo "ERROR: prime-client source introuvable: ${SRC}" >&2
  echo "Définir LBG_PRIME_CLIENT_ROOT si la racine diffère." >&2
  exit 2
fi
VM_HOST="${LBG_CORE_VM_HOST:-192.168.0.140}"
VM_USER="${LBG_CORE_VM_USER:-lbg}"
REMOTE="${LBG_PRIME_CLIENT_REMOTE:-/opt/LBG_Studios/packages/prime-client}"
LEGACY_MIRROR="${LBG_PRIME_CLIENT_LEGACY_MIRROR:-/opt/new_mmo/prime-client}"

_sync_one() {
  local dest="$1"
  echo "→ ${VM_USER}@${VM_HOST}:${dest}"
  ssh "${VM_USER}@${VM_HOST}" "mkdir -p ${dest}/assets/maps ${dest}/assets/sprites/units ${dest}/config ${dest}/scripts ${dest}/scenes/ui"
  rsync -a "${SRC}/assets/maps/" "${VM_USER}@${VM_HOST}:${dest}/assets/maps/"
  if [[ -d "${SRC}/assets/sprites/units" ]]; then
    rsync -a "${SRC}/assets/sprites/units/" "${VM_USER}@${VM_HOST}:${dest}/assets/sprites/units/"
  fi
  rsync -a "${SRC}/config/minimap_config.json" "${VM_USER}@${VM_HOST}:${dest}/config/"
  rsync -a "${SRC}/scripts/minimap_hud.gd" "${VM_USER}@${VM_HOST}:${dest}/scripts/"
  rsync -a "${SRC}/scripts/planet_map_panel.gd" "${VM_USER}@${VM_HOST}:${dest}/scripts/"
  rsync -a "${SRC}/scripts/waypoint_store.gd" "${VM_USER}@${VM_HOST}:${dest}/scripts/"
  rsync -a "${SRC}/config/waypoints.json" "${VM_USER}@${VM_HOST}:${dest}/config/"
  rsync -a "${SRC}/scenes/ui/minimap_hud.tscn" "${VM_USER}@${VM_HOST}:${dest}/scenes/ui/"
  rsync -a "${SRC}/scenes/ui/planet_map_panel.tscn" "${VM_USER}@${VM_HOST}:${dest}/scenes/ui/"
  rsync -a "${SRC}/scenes/main.tscn" "${VM_USER}@${VM_HOST}:${dest}/scenes/"
}

echo "=== Sync prime-client assets M9 → ${REMOTE} (canon Studios) ==="
_sync_one "${REMOTE}"
if [[ "${LBG_PRIME_SYNC_LEGACY_MIRROR:-1}" == "1" && -n "${LEGACY_MIRROR}" && "${LEGACY_MIRROR}" != "${REMOTE}" ]]; then
  echo "=== Miroir legacy (compat) → ${LEGACY_MIRROR} ==="
  _sync_one "${LEGACY_MIRROR}"
fi
echo "OK — LBG_PRIME_CLIENT_ROOT=${REMOTE} (canon) ; legacy miroir optionnel ${LEGACY_MIRROR}"
