#!/usr/bin/env bash
# Sync POI serveur Scrapaltai → assets Godot Prime Client (M9a-3).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PRIME_ROOT="${LBG_PRIME_CLIENT_ROOT:-${ROOT_DIR}/../prime-client}"
if [[ ! -d "${PRIME_ROOT}" ]]; then
  echo "ERROR: prime-client root introuvable: ${PRIME_ROOT}" >&2
  echo "Définir LBG_PRIME_CLIENT_ROOT si la racine diffère." >&2
  exit 2
fi
EDITOR_ROOT="${LBG_WORLD_EDITOR_ROOT:-${ROOT_DIR}/tools/world_editor}"
POI_ONLY="${LBG_SCRAPALTAI_SYNC_POI_ONLY:-1}"

ARGS=(--repo-root "${ROOT_DIR}" --editor-root "${EDITOR_ROOT}" --out "${PRIME_ROOT}")
if [[ "${POI_ONLY}" == "1" ]]; then
  ARGS+=(--poi-only)
fi

echo "=== Sync Scrapaltai POI → ${PRIME_ROOT}/assets/maps ==="
python3 "${ROOT_DIR}/tools/map_export/export_scrapaltai_for_godot.py" "${ARGS[@]}"
echo "OK"
