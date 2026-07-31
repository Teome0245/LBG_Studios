#!/usr/bin/env bash
# Sync ponctuel depuis les chemins legacy (lecture → packages/).
# Usage :
#   bash tools/sync_from_legacy.sh cortex
#   bash tools/sync_from_legacy.sh prime
#   bash tools/sync_from_legacy.sh launchpad
#   bash tools/sync_from_legacy.sh all
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LEGACY_CORTEX="${LBG_LEGACY_CORTEX:-/home/sdesh/projects/LBG_IA_MMORPG/LBG_IA_MMO}"
LEGACY_NEW_MMO="${LBG_LEGACY_NEW_MMO:-/home/sdesh/projects/new_mmo}"
TARGET="${1:-}"

rsync_cortex() {
  mkdir -p "$ROOT/packages/cortex"
  rsync -a --delete \
    --exclude '__pycache__/' --exclude '*.pyc' --exclude '.venv/' \
    --exclude 'pilot_web/mmo/' --exclude '**/mmo/' \
    --exclude '.pytest_cache/' --exclude '*.egg-info/' \
    "$LEGACY_CORTEX/orchestrator/" "$ROOT/packages/cortex/orchestrator/"
  rsync -a --delete \
    --exclude '__pycache__/' --exclude '*.pyc' --exclude '.venv/' \
    "$LEGACY_CORTEX/backend/" "$ROOT/packages/cortex/backend/"
  rsync -a --delete \
    --exclude '__pycache__/' --exclude '*.pyc' --exclude '.venv/' \
    "$LEGACY_CORTEX/agents/" "$ROOT/packages/cortex/agents/"
  rsync -a --delete \
    --exclude 'mmo/' --exclude '**/node_modules/' \
    "$LEGACY_CORTEX/pilot_web/" "$ROOT/packages/cortex/pilot_web/"
  rsync -a --delete \
    --exclude '__pycache__/' \
    "$LEGACY_CORTEX/infra/" "$ROOT/packages/cortex/infra/"
  rsync -a --delete \
    --exclude '__pycache__/' \
    "$LEGACY_CORTEX/windows_agent/" "$ROOT/packages/cortex/windows_agent/"
  rsync -a --delete \
    --exclude '__pycache__/' \
    "$LEGACY_CORTEX/linux_agent/" "$ROOT/packages/cortex/linux_agent/"
  # Docs Studio utiles
  mkdir -p "$ROOT/packages/cortex/docs"
  rsync -a \
    --include 'adr/' --include 'adr/***' \
    --include '*.md' --exclude '*' \
    "$LEGACY_CORTEX/docs/" "$ROOT/packages/cortex/docs/" 2>/dev/null || true
  # Fichiers racine utiles
  for f in README.md pytest.ini conftest.py; do
    [[ -f "$LEGACY_CORTEX/$f" ]] && cp -a "$LEGACY_CORTEX/$f" "$ROOT/packages/cortex/$f"
  done
  # Marqueur
  cat > "$ROOT/packages/cortex/LEGACY_SOURCE.md" <<EOF
# Cortex — extrait depuis legacy

Source : \`$LEGACY_CORTEX\`
Date sync : $(date -Iseconds)
Exclu : pilot_web/mmo, mmo_server, mmmorpg_server, web_client
EOF
  echo "OK cortex → packages/cortex"
}

rsync_prime() {
  mkdir -p "$ROOT/packages/prime-client"
  rsync -a --delete \
    --exclude '.godot/' --exclude '.git/' \
    --exclude '**/*.glb' --exclude '**/*.GLB' \
    --exclude 'dist/' --exclude '__pycache__/' \
    "$LEGACY_NEW_MMO/prime-client/" "$ROOT/packages/prime-client/"
  cat > "$ROOT/packages/prime-client/LEGACY_SOURCE.md" <<EOF
# prime-client — extrait depuis legacy

Source : \`$LEGACY_NEW_MMO/prime-client\`
Date sync : $(date -Iseconds)
Serveur produit : Prime 246 (patches :8080, gateway WS)
EOF
  echo "OK prime-client → packages/prime-client"
}

rsync_launchpad() {
  mkdir -p "$ROOT/packages/launchpad"
  rsync -a --delete \
    --exclude 'node_modules/' --exclude 'dist/' --exclude 'out/' \
    --exclude '.git/' --exclude 'test_game_dir/' \
    "$LEGACY_NEW_MMO/launchpad/" "$ROOT/packages/launchpad/"
  cat > "$ROOT/packages/launchpad/LEGACY_SOURCE.md" <<EOF
# launchpad — sources extraites

Source : \`$LEGACY_NEW_MMO/launchpad\`
Date sync : $(date -Iseconds)
Build Windows : npm ci && npm run build:win → J:\\\\swgemu\\\\dist\\\\
EOF
  echo "OK launchpad → packages/launchpad"
}

case "$TARGET" in
  cortex) rsync_cortex ;;
  prime|prime-client) rsync_prime ;;
  launchpad) rsync_launchpad ;;
  all) rsync_cortex; rsync_prime; rsync_launchpad ;;
  *)
    echo "Usage: $0 {cortex|prime|launchpad|all}" >&2
    exit 1
    ;;
esac
