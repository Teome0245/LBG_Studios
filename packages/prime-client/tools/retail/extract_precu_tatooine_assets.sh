#!/usr/bin/env bash
# Récupère assets Tatooine utiles depuis PreCU (245) vers prime-client/docs/reference/retail_245/
set -euo pipefail

HOST="${PRECU_HOST:-192.168.0.245}"
USER="${PRECU_USER:-lbg}"
OUT="${OUT:-$(cd "$(dirname "$0")/../.." && pwd)/docs/reference/retail_245}"
REMOTE_CORE3="${REMOTE_CORE3:-/home/lbg/swgemu}"

mkdir -p "${OUT}"

echo "→ Sonde SSH ${USER}@${HOST} …"
if ! ssh -o ConnectTimeout=8 -o BatchMode=yes "${USER}@${HOST}" "echo ok" 2>/dev/null; then
  echo "SSH indisponible. Configure clé ou lance depuis le LAN." >&2
  exit 1
fi

echo "→ POI / contenu serveur (si présent) …"
ssh "${USER}@${HOST}" "test -f ${REMOTE_CORE3}/LBG_IA_MMO/content/core3/world_poi/tatooine.json && cat ${REMOTE_CORE3}/LBG_IA_MMO/content/core3/world_poi/tatooine.json" \
  > "${OUT}/tatooine_world_poi.json" 2>/dev/null || echo "[]" > "${OUT}/tatooine_world_poi.json"

for rel in \
  "LBG_IA_MMO/tools/world_editor/tatooine_map_config.json" \
  "LBG_IA_MMO/tools/world_editor/assets/tatooine_map.svg"; do
  echo "→ ${rel}"
  scp -q "${USER}@${HOST}:${REMOTE_CORE3}/${rel}" "${OUT}/$(basename "$rel")" 2>/dev/null || true
done

echo "→ Inventaire dossiers carte côté Core3 (log seulement) …"
ssh "${USER}@${HOST}" "find ${REMOTE_CORE3} -maxdepth 4 -type f \\( -iname '*tatooine*map*' -o -iname '*minimap*' -o -iname '*.pob' \\) 2>/dev/null | head -40" \
  | tee "${OUT}/_inventory_paths.txt" || true

echo ""
echo "Référence retail copiée dans: ${OUT}"
echo "Pour textures client .tre : extraire sur le poste Windows (SWGEmu install) — pas sur 245."
