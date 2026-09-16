#!/usr/bin/env bash
# Déploie le Compagnon UI (packages/cortex/compagnon_ui) sur CT `.100` → :5174
#
# Usage (depuis la racine LBG_Studios ou packages/cortex) :
#   bash packages/cortex/infra/scripts/deploy_compagnon_100.sh
#   bash packages/cortex/infra/scripts/deploy_compagnon_100.sh --smoke
#
# Prérequis : SSH root@192.168.0.100 ; stack docker /opt/orchestrateur
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORTEX_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
UI_ROOT="${CORTEX_ROOT}/compagnon_ui"
OVERLAY="${UI_ROOT}/server_overlay/router_prompts.py"

REMOTE_USER="${LBG_ORCH_CT100_USER:-root}"
REMOTE_HOST="${LBG_ORCH_CT100_HOST:-192.168.0.100}"
REMOTE="${REMOTE_USER}@${REMOTE_HOST}"
REMOTE_DIR="${LBG_ORCH_CT100_DIR:-/opt/orchestrateur}"
SMOKE=0
[[ "${1:-}" == "--smoke" ]] && SMOKE=1

if [[ ! -d "${UI_ROOT}/src" ]]; then
  echo "ERR: compagnon_ui introuvable: ${UI_ROOT}" >&2
  exit 1
fi

echo "==> Sync Compagnon UI → ${REMOTE}:${REMOTE_DIR}/frontend/"
rsync -az --delete \
  --exclude 'node_modules' \
  --exclude 'dist' \
  --exclude 'server_overlay' \
  --exclude '.env' \
  "${UI_ROOT}/" "${REMOTE}:${REMOTE_DIR}/frontend/"

if [[ -f "${OVERLAY}" ]]; then
  echo "==> Overlay profils Compagnon → backend router_prompts.py"
  rsync -az "${OVERLAY}" \
    "${REMOTE}:${REMOTE_DIR}/backend/src/services/router_prompts.py"
fi

echo "==> Rebuild Docker frontend (+ backend si overlay)"
ssh "${REMOTE}" bash -s <<EOF
set -euo pipefail
cd "${REMOTE_DIR}"
docker compose build frontend backend
docker compose up -d --force-recreate frontend backend
EOF

if [[ "$SMOKE" -eq 1 ]]; then
  echo "==> Smoke Compagnon"
  curl -fsS "http://${REMOTE_HOST}:5174/" >/dev/null && echo "OK  UI :5174"
  for i in 1 2 3 4 5 6 7 8 9 10; do
    if curl -fsS "http://${REMOTE_HOST}:3000/health" >/dev/null 2>&1; then
      echo "OK  API :3000/health"
      break
    fi
    sleep 2
  done
  curl -fsS -X POST "http://${REMOTE_HOST}:5174/api/ask" \
    -H 'Content-Type: application/json' \
    -d '{"prompt":"Bonjour","mode":"auto","profile":"compagnon"}' \
    | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('response') or {}; print('chat', (r.get('content') or '')[:120])"
  echo "==> Smoke Agir (proxy Pilot)"
  curl -fsS -X POST "http://${REMOTE_HOST}:5174/api/pilot/action-proposal" \
    -H 'Content-Type: application/json' \
    -d '{"actor_id":"ui:compagnon","text":"ouvre notepad","context":{}}' \
    | python3 -c "import sys,json; d=json.load(sys.stdin); p=d.get('proposal') or {}; print('agir', d.get('ok'), p.get('capability'), (p.get('summary') or '')[:80])"
fi

echo "OK  Compagnon http://${REMOTE_HOST}:5174/ · API :3000 · Pilot ops http://192.168.0.140:8080/pilot/"
