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
LLM_CHAT_OVERLAY="${UI_ROOT}/server_overlay/llm_chat_phase.py"
DESKTOP_DISPATCH="${UI_ROOT}/server_overlay/desktop_dispatch.py"
DESKTOP_APPROVAL="${UI_ROOT}/server_overlay/desktop_approval.py"
ROUTING_OVERLAY="${UI_ROOT}/server_overlay/routing.json"
LOCAL_LLM_OVERLAY="${UI_ROOT}/server_overlay/local_llm_provider.py"

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

if [[ -f "${LLM_CHAT_OVERLAY}" ]]; then
  echo "==> Overlay llm_chat_phase (LAB local-only + nudges) → backend"
  rsync -az "${LLM_CHAT_OVERLAY}" \
    "${REMOTE}:${REMOTE_DIR}/backend/src/services/llm_chat_phase.py"
fi

if [[ -f "${ROUTING_OVERLAY}" ]]; then
  echo "==> Overlay routing LLM local → backend config/routing.json"
  rsync -az "${ROUTING_OVERLAY}" \
    "${REMOTE}:${REMOTE_DIR}/backend/src/config/routing.json"
fi

if [[ -f "${LOCAL_LLM_OVERLAY}" ]]; then
  echo "==> Overlay LocalLLMProvider (messages + gemma4:e2b) → backend"
  rsync -az "${LOCAL_LLM_OVERLAY}" \
    "${REMOTE}:${REMOTE_DIR}/backend/src/providers/local_llm_provider.py"
fi

if [[ -f "${DESKTOP_DISPATCH}" ]]; then
  echo "==> Overlay desktop_dispatch → backend"
  rsync -az "${DESKTOP_DISPATCH}" \
    "${REMOTE}:${REMOTE_DIR}/backend/src/services/desktop_dispatch.py"
fi

if [[ -f "${DESKTOP_APPROVAL}" ]]; then
  echo "==> Overlay desktop_approval bootstrap → backend"
  rsync -az "${DESKTOP_APPROVAL}" \
    "${REMOTE}:${REMOTE_DIR}/backend/src/routers/desktop_approval.py"
  ssh "${REMOTE}" bash -s <<'PATCH'
set -euo pipefail
FACTORY=/opt/orchestrateur/backend/src/app/factory.py
if [[ -f "$FACTORY" ]] && ! grep -q 'desktop_approval' "$FACTORY"; then
  python3 - <<'PY'
from pathlib import Path
p = Path("/opt/orchestrateur/backend/src/app/factory.py")
text = p.read_text()
imp = "from src.routers.desktop_approval import router as desktop_approval_router\n"
inc = "    app.include_router(desktop_approval_router)\n"
if "desktop_approval_router" not in text:
    # insert import after team_router import
    needle = "from src.routers.team import router as team_router\n"
    if needle in text:
        text = text.replace(needle, needle + imp, 1)
    else:
        text = imp + text
    needle2 = "    app.include_router(team_router)\n"
    if needle2 in text:
        text = text.replace(needle2, needle2 + inc, 1)
    else:
        text = text.replace("    app.include_router(core_router)\n", "    app.include_router(core_router)\n" + inc, 1)
    p.write_text(text)
    print("factory.py: desktop_approval router wired")
else:
    print("factory.py: already wired")
PY
fi
PATCH
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
  echo "==> Smoke desktop-approval bootstrap"
  curl -fsS "http://${REMOTE_HOST}:5174/api/desktop-approval" \
    | python3 -c "import sys,json,hashlib; d=json.load(sys.stdin); t=d.get('token') or ''; print('token', d.get('ok'), 'len', len(t), 'sha', hashlib.sha256(t.encode()).hexdigest()[:12] if t else '-')"
fi

echo "OK  Compagnon http://${REMOTE_HOST}:5174/ · API :3000 · Pilot ops http://192.168.0.140:8080/pilot/"
