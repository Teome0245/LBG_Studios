#!/usr/bin/env bash
# Déploie packages/cortex/pilot_web (+ optionnel code) vers VM 140.
# Par défaut : index + pilot_web (sans mmo/) — n’écrase pas /opt si non demandé.
#
# Usage :
#   bash tools/deploy_cortex_140.sh           # pilot_web only
#   bash tools/deploy_cortex_140.sh --full    # + orchestrator/backend/agents (stage)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CORTEX="$ROOT/packages/cortex"
VM_HOST="${LBG_VM_HOST:-192.168.0.140}"
VM_USER="${LBG_VM_USER:-lbg}"
REMOTE="${LBG_REMOTE_DIR:-/opt/LBG_IA_MMO}"
FULL=0
[[ "${1:-}" == "--full" ]] && FULL=1

if [[ ! -d "$CORTEX/pilot_web" ]]; then
  echo "ERROR: $CORTEX/pilot_web absent — lancer bash tools/sync_from_legacy.sh cortex" >&2
  exit 1
fi

echo "=== deploy cortex pilot_web → ${VM_USER}@${VM_HOST}:${REMOTE}/pilot_web ==="
rsync -az --delete \
  --exclude 'mmo/' \
  --exclude 'audio/' \
  --exclude 'choreographer.html' \
  --exclude 'vrm/' \
  --exclude 'active_choreography.json' \
  --exclude 'nexura_domina_v1.mp3' \
  -e "ssh -o BatchMode=yes" \
  "$CORTEX/pilot_web/" \
  "${VM_USER}@${VM_HOST}:${REMOTE}/pilot_web/"

if [[ "$FULL" -eq 1 ]]; then
  echo "=== deploy orchestrator/backend/agents (rsync) ==="
  for part in orchestrator backend agents; do
    [[ -d "$CORTEX/$part" ]] || continue
    rsync -az --delete \
      --exclude '__pycache__/' --exclude '.venv/' --exclude '*.pyc' \
      -e "ssh -o BatchMode=yes" \
      "$CORTEX/$part/" \
      "${VM_USER}@${VM_HOST}:${REMOTE}/$part/"
  done
  # Owner smokes (A2/P1/P2) — chemins relatifs depuis /opt/.../orchestrator/team/owner_smokes.py
  if [[ -d "$CORTEX/infra/scripts" ]]; then
    echo "=== deploy infra/scripts (smokes Godot / LAN) ==="
    ssh -o BatchMode=yes "${VM_USER}@${VM_HOST}" "mkdir -p '${REMOTE}/infra/scripts'"
    rsync -az \
      -e "ssh -o BatchMode=yes" \
      --include 'smoke_*.sh' --include 'smoke_*.py' --include '*/' --exclude '*' \
      "$CORTEX/infra/scripts/" \
      "${VM_USER}@${VM_HOST}:${REMOTE}/infra/scripts/"
  fi
  echo "Note: redémarrer services systemd sur 140 si besoin (lbg-orchestrator, backend)."
fi

curl -sf -o /dev/null -w "pilot_http:%{http_code}\n" --connect-timeout 5 "http://${VM_HOST}:8080/" || echo "pilot_http:fail"
echo "OK deploy cortex → ${VM_HOST}"
