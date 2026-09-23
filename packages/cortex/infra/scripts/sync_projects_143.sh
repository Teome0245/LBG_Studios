#!/usr/bin/env bash
# Synchro miroir projects : WSL (.10) ↔ Omarchy (.143)
# Lab/prod (.100 / .140 / agents) = Git + scripts deploy_* — PAS ce rsync.
#
# Usage :
#   bash packages/cortex/infra/scripts/sync_projects_143.sh status
#   bash packages/cortex/infra/scripts/sync_projects_143.sh from-wsl    # WSL → .143
#   bash packages/cortex/infra/scripts/sync_projects_143.sh to-wsl      # .143 → WSL (prudence)
#   bash packages/cortex/infra/scripts/sync_projects_143.sh dry-from-wsl
#
# Après edit sur .143 : git commit/push, puis deploy lab, ex. :
#   bash packages/cortex/infra/scripts/deploy_compagnon_100.sh --smoke
set -euo pipefail

HOST="${LBG_OMARCHY_HOST:-192.168.0.143}"
USER="${LBG_OMARCHY_USER:-lbg}"
REMOTE="${USER}@${HOST}"
SRC_WSL="${LBG_PROJECTS_WSL:-/home/sdesh/projects}"
DST_REMOTE="${LBG_PROJECTS_143:-/home/lbg/projects}"

RSYNC_EXCLUDES=(
  --exclude '.venv/'
  --exclude '**/.venv/'
  --exclude 'node_modules/'
  --exclude '**/node_modules/'
  --exclude '__pycache__/'
  --exclude '**/.pytest_cache/'
  --exclude '.cache/'
  --exclude '**/Cache/'
  --exclude 'lost+found/'
)

cmd="${1:-status}"

status() {
  echo "=== WSL ${SRC_WSL} ==="
  du -sh "${SRC_WSL}" 2>/dev/null || echo "(absent)"
  echo "=== .143 ${DST_REMOTE} ==="
  ssh -o BatchMode=yes -o ConnectTimeout=8 "${REMOTE}" \
    "df -h ${DST_REMOTE}; du -sh ${DST_REMOTE}; cd ${DST_REMOTE}/LBG_Studios && git status -sb | head -8"
  echo
  echo "Lab/prod : ne pas rsync massif vers .100/.140 — utiliser git + deploy_* (ex. deploy_compagnon_100.sh)."
}

from_wsl() {
  local dry=()
  [[ "${1:-}" == "dry" ]] && dry=(--dry-run -i)
  echo "==> rsync WSL → ${REMOTE}:${DST_REMOTE}/ ${dry[*]:-}"
  rsync -aH --partial --info=stats2 "${dry[@]}" \
    "${RSYNC_EXCLUDES[@]}" \
    --chown=lbg:lbg \
    "${SRC_WSL}/" "${REMOTE}:${DST_REMOTE}/"
}

to_wsl() {
  echo "WARN: écrase/merge vers WSL ${SRC_WSL} — Ctrl+C dans 3s si erreur"
  sleep 3
  rsync -aH --partial --info=stats2 \
    "${RSYNC_EXCLUDES[@]}" \
    "${REMOTE}:${DST_REMOTE}/" "${SRC_WSL}/"
}

case "${cmd}" in
  status) status ;;
  from-wsl) from_wsl ;;
  dry-from-wsl) from_wsl dry ;;
  to-wsl) to_wsl ;;
  *)
    echo "Usage: $0 {status|from-wsl|dry-from-wsl|to-wsl}" >&2
    exit 2
    ;;
esac
