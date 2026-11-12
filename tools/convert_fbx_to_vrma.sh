#!/usr/bin/env bash
# tools/convert_fbx_to_vrma.sh — Pipeline de conversion automatisé Mixamo/DeepMotion FBX -> VRMA (Ticket Compagnon)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONVERTER_DIR="${REPO_ROOT}/tools/fbx2vrma"
DEST_DESKTOP="${REPO_ROOT}/packages/compagnon-desktop/overlay/vrm/animations"
DEST_WEB="${REPO_ROOT}/packages/cortex/compagnon_ui/public/vrm/animations"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <fichier.fbx | dossier_fbx> [--deploy]"
  echo ""
  echo "Exemples :"
  echo "  $0 ~/Downloads/bellydance.fbx"
  echo "  $0 ~/Downloads/mixamo_dances/ --deploy"
  echo ""
  echo "Options :"
  echo "  --deploy : Déploie automatiquement les nouveaux .vrma sur le frontend CT100 (:5174)"
  exit 1
fi

TARGET="$1"
DEPLOY_FLAG=false

if [[ "${2:-}" == "--deploy" || "${3:-}" == "--deploy" ]]; then
  DEPLOY_FLAG=true
fi

# 1. Vérification des prérequis
if [[ ! -d "${CONVERTER_DIR}/node_modules" ]]; then
  echo "[+] Installation des dépendances fbx2vrma..."
  (cd "${CONVERTER_DIR}" && npm install --silent)
fi

# 2. Conversion
echo "[+] Lancement de la conversion FBX -> VRMA..."
mkdir -p "${DEST_DESKTOP}"
mkdir -p "${DEST_WEB}"

BIN_PATH="${CONVERTER_DIR}/FBX2glTF-linux-x64"

if [[ -f "${TARGET}" ]]; then
  FILENAME=$(basename "${TARGET}")
  BASENAME="${FILENAME%.*}"
  OUT_VRMA="${DEST_DESKTOP}/${BASENAME}.vrma"
  
  node "${CONVERTER_DIR}/fbx2vrma-converter.js" -i "${TARGET}" -o "${OUT_VRMA}" --fbx2gltf "${BIN_PATH}"
  cp "${OUT_VRMA}" "${DEST_WEB}/${BASENAME}.vrma"
  echo "[✔] Animation convertie : ${OUT_VRMA} ($(du -h "${OUT_VRMA}" | cut -f1))"
  CONVERTED_FILES=("${BASENAME}.vrma")

elif [[ -d "${TARGET}" ]]; then
  TMP_OUT=$(mktemp -d)
  node "${CONVERTER_DIR}/fbx2vrma-converter.js" -d "${TARGET}" -o "${TMP_OUT}" --fbx2gltf "${BIN_PATH}"
  
  CONVERTED_FILES=()
  for vrma in "${TMP_OUT}"/*.vrma; do
    if [[ -f "$vrma" ]]; then
      b=$(basename "$vrma")
      cp "$vrma" "${DEST_DESKTOP}/$b"
      cp "$vrma" "${DEST_WEB}/$b"
      echo "[✔] Animation par lot : $b ($(du -h "$vrma" | cut -f1))"
      CONVERTED_FILES+=("$b")
    fi
  done
  rm -rf "${TMP_OUT}"
else
  echo "[-] Erreur : '${TARGET}' n'est ni un fichier ni un dossier valide."
  exit 1
fi

# 3. Rappel d'enregistrement dans VRMA_MAP
echo ""
echo "=== Animations prêtes à l'emploi ==="
for f in "${CONVERTED_FILES[@]}"; do
  anim_name="${f%.vrma}"
  echo "  Nom du mouvement : \"${anim_name}\""
  echo "  Fichier : ${f}"
  echo "  À enregistrer dans vrm_pet.js VRMA_MAP si nouveau : ${anim_name}: \"${f}\""
done

# 4. Déploiement CT100 LAN si demandé
if [[ "${DEPLOY_FLAG}" == true ]]; then
  echo ""
  echo "[+] Déploiement vers CT100 (192.168.0.100:5174)..."
  if ssh -o BatchMode=yes -o ConnectTimeout=3 root@192.168.0.100 "docker ps --format '{{.Names}}' | grep -q lbg-frontend" 2>/dev/null; then
    for f in "${CONVERTED_FILES[@]}"; do
      scp -q "${DEST_DESKTOP}/${f}" "root@192.168.0.100:/tmp/${f}"
      ssh root@192.168.0.100 "docker cp /tmp/${f} lbg-frontend:/usr/share/nginx/html/vrm/animations/${f} && rm /tmp/${f}"
      echo "  [✔] ${f} synchronisé sur CT100"
    done
  else
    echo "  [!] CT100 injoignable ou lbg-frontend inactif."
  fi
fi

echo ""
echo "[✔] Traitement terminé avec succès !"

