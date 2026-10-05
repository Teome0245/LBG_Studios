#!/usr/bin/env bash
# Amorce un notebook NotebookLM avec docs canons LBG (poste seulement).
# Prérequis : nlm login OK ; PATH contient ~/.local/bin
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
export PATH="${HOME}/.local/bin:${PATH}"

TITLE="${1:-LBG — bible & design}"
NOTEBOOK_ID="${NOTEBOOK_ID:-}"

SEED_FILES=(
  "${ROOT}/OBJECTIVES.md"
  "${ROOT}/docs/world/BIBLE_MMO.md"
  "${ROOT}/docs/PRIORITES_ACTUELLES.md"
  "${ROOT}/packages/cortex/docs/architecture.md"
  "${ROOT}/packages/cortex/docs/lbg_agentic_os.md"
)

if ! nlm login --check >/dev/null 2>&1; then
  echo "Auth manquante. Lance : WAYLAND_DISPLAY=wayland-1 nlm login" >&2
  exit 1
fi

if [[ -z "${NOTEBOOK_ID}" ]]; then
  echo "Création notebook : ${TITLE}"
  # nlm notebook create prints id / JSON — capture best-effort
  OUT="$(nlm notebook create "${TITLE}" 2>&1)"
  echo "${OUT}"
  NOTEBOOK_ID="$(echo "${OUT}" | rg -o '[a-f0-9-]{20,}' | head -1 || true)"
  if [[ -z "${NOTEBOOK_ID}" ]]; then
    echo "Impossible d'extraire l'ID. Relance avec NOTEBOOK_ID=... $0" >&2
    exit 1
  fi
fi

echo "Notebook : ${NOTEBOOK_ID}"
for f in "${SEED_FILES[@]}"; do
  if [[ -f "${f}" ]]; then
    echo "  + ${f#"${ROOT}/"}"
    nlm source add "${NOTEBOOK_ID}" --file "${f}" || echo "    (échec source, continue)" >&2
  else
    echo "  skip manquant : ${f}" >&2
  fi
done

echo
echo "OK — query : nlm notebook query ${NOTEBOOK_ID} \"Résume les priorités Studio\""
echo "Doc     : packages/cortex/docs/notebooklm_poste.md"
