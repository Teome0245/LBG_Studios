#!/usr/bin/env bash
# Extrait snapshot/tatooine.ws depuis le client SWG (TRE) → JSON villes Godot.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRIME="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TRE="${TRE:-/mnt/j/swgemu/StarWarsGalaxies/data_other_00.tre}"
SWG="${SWG_BIN:-${HOME}/.cargo/bin/swg}"
CACHE="${CACHE:-${PRIME}/tools/retail/cache}"
WS_OUT="${CACHE}/snapshot/tatooine.ws"
OUT="${OUT:-${PRIME}/assets/maps/retail/scrapaltai}"

if [[ ! -f "${TRE}" ]]; then
  echo "TRE absent: ${TRE}" >&2
  echo "Override: TRE=/chemin/data_other_00.tre" >&2
  exit 1
fi

mkdir -p "${CACHE}/snapshot"
if [[ ! -f "${WS_OUT}" ]]; then
  echo "→ Extraction TRE (peut prendre ~1 min)…"
  rm -rf "${CACHE}/tre_extract"
  mkdir -p "${CACHE}/tre_extract"
  "${SWG}" tre extract --file "${TRE}" --directory "${CACHE}/tre_extract"
  cp -f "${CACHE}/tre_extract/snapshot/tatooine.ws" "${WS_OUT}"
fi

echo "→ Export layouts JSON…"
python3 "${SCRIPT_DIR}/export_retail_city_layout.py" "${WS_OUT}" -o "${OUT}"

if [[ -d /mnt/j/swgemu/clients/prime-client ]]; then
  rsync -av "${OUT}/" /mnt/j/swgemu/clients/prime-client/assets/maps/retail/scrapaltai/
  echo "→ sync J: assets/maps/retail/scrapaltai"
fi

echo "OK — activer dans Godot : RetailLayoutLayer + Ctrl+Shift+R (voir world_map.gd)"
