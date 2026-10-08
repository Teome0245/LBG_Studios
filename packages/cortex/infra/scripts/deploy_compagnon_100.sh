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
SELF_GROUNDING="${UI_ROOT}/server_overlay/companion_self_grounding.py"
ECOSYSTEM_GROUNDING="${UI_ROOT}/server_overlay/ecosystem_grounding.py"
RAG_GROUNDING="${UI_ROOT}/server_overlay/rag_grounding.py"
RAG_PACKAGE="${CORTEX_ROOT}/orchestrator/services/rag"
DESKTOP_DISPATCH="${UI_ROOT}/server_overlay/desktop_dispatch.py"
DESKTOP_APPROVAL="${UI_ROOT}/server_overlay/desktop_approval.py"
ROUTING_OVERLAY="${UI_ROOT}/server_overlay/routing.json"
LOCAL_LLM_OVERLAY="${UI_ROOT}/server_overlay/local_llm_provider.py"
REFLECTION_OVERLAY="${UI_ROOT}/server_overlay/reflection_router.py"
CHAT_INTENT="${UI_ROOT}/server_overlay/chat_intent.py"
PLAN_SUBMIT="${UI_ROOT}/server_overlay/plan_submit.py"
MISSION_WATCH_INTENT="${UI_ROOT}/server_overlay/mission_watch_intent.py"
OPENCLAW_MARKERS="${UI_ROOT}/server_overlay/openclaw_markers.py"
TEAM_ROUTING="${UI_ROOT}/server_overlay/team_routing.py"
TOOL_LOOP_OVERLAY="${UI_ROOT}/server_overlay/tool_loop.py"
OLLAMA_AUDIT_OVERLAY="${UI_ROOT}/server_overlay/ollama_audit.py"
CORE_ROUTER_OVERLAY="${UI_ROOT}/server_overlay/core.py"
TEAM_PROXY_OVERLAY="${UI_ROOT}/server_overlay/team_proxy.py"
INFRA_LAN_INTENT="${UI_ROOT}/server_overlay/infra_lan_intent.py"
CHARACTER_LAYER="${UI_ROOT}/server_overlay/character_layer.py"
CHARACTER_API="${UI_ROOT}/server_overlay/character_api.py"
CHARACTER_PACK="${UI_ROOT}/server_overlay/character/compagnon_v1.json"
KNOWLEDGE_PACK="${CORTEX_ROOT}/knowledge/character/compagnon_v1.json"
SPONTANEITY_LAYER="${UI_ROOT}/server_overlay/spontaneity.py"
SPONTANEITY_API="${UI_ROOT}/server_overlay/spontaneity_api.py"
TTS_LAYER="${UI_ROOT}/server_overlay/tts.py"
TTS_API="${UI_ROOT}/server_overlay/tts_api.py"

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

if [[ -f "${SELF_GROUNDING}" ]]; then
  echo "==> Overlay companion_self_grounding (P1 Self prompt) → backend"
  rsync -az "${SELF_GROUNDING}" \
    "${REMOTE}:${REMOTE_DIR}/backend/src/services/companion_self_grounding.py"
fi

if [[ -f "${ECOSYSTEM_GROUNDING}" ]]; then
  echo "==> Overlay ecosystem_grounding (P2 REGISTRE-lite) → backend"
  rsync -az "${ECOSYSTEM_GROUNDING}" \
    "${REMOTE}:${REMOTE_DIR}/backend/src/services/ecosystem_grounding.py"
fi

if [[ -f "${RAG_GROUNDING}" ]]; then
  echo "==> Overlay rag_grounding (P3 RAG) → backend"
  rsync -az "${RAG_GROUNDING}" \
    "${REMOTE}:${REMOTE_DIR}/backend/src/services/rag_grounding.py"
fi

if [[ -d "${RAG_PACKAGE}" ]]; then
  echo "==> Package services/rag (embeddings + store + ingest) → backend"
  rsync -az --delete \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude 'README.md' \
    "${RAG_PACKAGE}/" \
    "${REMOTE}:${REMOTE_DIR}/backend/src/services/rag/"
fi

# Knowledge RAG (facts + lessons + character) — monté via ./backend:/app
KNOWLEDGE_DIR="${CORTEX_ROOT}/knowledge"
if [[ -d "${KNOWLEDGE_DIR}" ]]; then
  echo "==> Knowledge RAG (rag_facts + lessons + character) → backend/knowledge"
  ssh "${REMOTE}" "mkdir -p ${REMOTE_DIR}/backend/knowledge/character"
  rsync -az \
    "${KNOWLEDGE_DIR}/rag_facts.jsonl" \
    "${KNOWLEDGE_DIR}/lessons_learned.json" \
    "${REMOTE}:${REMOTE_DIR}/backend/knowledge/"
  if [[ -f "${KNOWLEDGE_PACK}" ]]; then
    rsync -az "${KNOWLEDGE_PACK}" \
      "${REMOTE}:${REMOTE_DIR}/backend/knowledge/character/compagnon_v1.json"
  fi
fi

if [[ -f "${ROUTING_OVERLAY}" ]]; then
  echo "==> Overlay routing LLM local → backend config/routing.json"
  rsync -az "${ROUTING_OVERLAY}" \
    "${REMOTE}:${REMOTE_DIR}/backend/src/config/routing.json"
fi

if [[ -f "${LOCAL_LLM_OVERLAY}" ]]; then
  echo "==> Overlay LocalLLMProvider (messages + gemma-4-abliterated:e2b .111) → backend"
  rsync -az "${LOCAL_LLM_OVERLAY}" \
    "${REMOTE}:${REMOTE_DIR}/backend/src/providers/local_llm_provider.py"
fi

if [[ -f "${DESKTOP_DISPATCH}" ]]; then
  echo "==> Overlay desktop_dispatch → backend"
  rsync -az "${DESKTOP_DISPATCH}" \
    "${REMOTE}:${REMOTE_DIR}/backend/src/services/desktop_dispatch.py"
fi

if [[ -f "${REFLECTION_OVERLAY}" ]]; then
  echo "==> Overlay reflection_router (disk/hôtes → team Héphaïstos) → backend"
  rsync -az "${REFLECTION_OVERLAY}" \
    "${REMOTE}:${REMOTE_DIR}/backend/src/services/reflection_router.py"
fi

if [[ -f "${CHAT_INTENT}" ]]; then
  echo "==> Overlay chat_intent (identité / causerie ≠ Team) → backend"
  rsync -az "${CHAT_INTENT}" \
    "${REMOTE}:${REMOTE_DIR}/backend/src/services/chat_intent.py"
fi

if [[ -f "${PLAN_SUBMIT}" ]]; then
  echo "==> Overlay plan_submit (D6.5 plan → mission Campus) → backend"
  rsync -az "${PLAN_SUBMIT}" \
    "${REMOTE}:${REMOTE_DIR}/backend/src/services/plan_submit.py"
fi

if [[ -f "${MISSION_WATCH_INTENT}" ]]; then
  echo "==> Overlay mission_watch_intent (retour clôture Team) → backend"
  rsync -az "${MISSION_WATCH_INTENT}" \
    "${REMOTE}:${REMOTE_DIR}/backend/src/services/mission_watch_intent.py"
fi

if [[ -f "${TEAM_ROUTING}" ]]; then
  echo "==> Overlay team_routing (campus conceptuel ≠ Team live) → backend"
  rsync -az "${TEAM_ROUTING}" \
    "${REMOTE}:${REMOTE_DIR}/backend/src/services/team_routing.py"
fi

if [[ -f "${OPENCLAW_MARKERS}" ]]; then
  echo "==> Overlay openclaw_markers (pas de spawn sur « faire évoluer » causerie) → backend"
  rsync -az "${OPENCLAW_MARKERS}" \
    "${REMOTE}:${REMOTE_DIR}/backend/src/services/openclaw_markers.py"
fi

if [[ -f "${TOOL_LOOP_OVERLAY}" ]]; then
  echo "==> Overlay tool_loop (audit studio → team_status d'abord) → backend"
  rsync -az "${TOOL_LOOP_OVERLAY}" \
    "${REMOTE}:${REMOTE_DIR}/backend/src/services/tool_loop.py"
fi

if [[ -f "${OLLAMA_AUDIT_OVERLAY}" ]]; then
  echo "==> Overlay ollama_audit (heavy=.110 via PROBE_OLLAMA_HEAVY) → backend"
  rsync -az "${OLLAMA_AUDIT_OVERLAY}" \
    "${REMOTE}:${REMOTE_DIR}/backend/src/services/ollama_audit.py"
fi

if [[ -f "${CORE_ROUTER_OVERLAY}" ]]; then
  echo "==> Overlay core.py (/ask agent shortcuts) → backend"
  rsync -az "${CORE_ROUTER_OVERLAY}" \
    "${REMOTE}:${REMOTE_DIR}/backend/src/routers/core.py"
fi

if [[ -f "${TEAM_PROXY_OVERLAY}" ]]; then
  echo "==> Overlay team_proxy (brief Infra LAN + spawn lecture seule) → backend"
  rsync -az "${TEAM_PROXY_OVERLAY}" \
    "${REMOTE}:${REMOTE_DIR}/backend/src/services/team_proxy.py"
fi

if [[ -f "${INFRA_LAN_INTENT}" ]]; then
  echo "==> Overlay infra_lan_intent (mémoire agent ≠ RAM/disk) → backend"
  rsync -az "${INFRA_LAN_INTENT}" \
    "${REMOTE}:${REMOTE_DIR}/backend/src/services/infra_lan_intent.py"
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

# Character layer (pack + dials API)
PACK_SRC=""
if [[ -f "${KNOWLEDGE_PACK}" ]]; then
  PACK_SRC="${KNOWLEDGE_PACK}"
elif [[ -f "${CHARACTER_PACK}" ]]; then
  PACK_SRC="${CHARACTER_PACK}"
fi
if [[ -f "${CHARACTER_LAYER}" ]]; then
  echo "==> Overlay character_layer → backend"
  rsync -az "${CHARACTER_LAYER}" \
    "${REMOTE}:${REMOTE_DIR}/backend/src/services/character_layer.py"
fi
if [[ -n "${PACK_SRC}" ]]; then
  echo "==> Character pack compagnon_v1.json → backend config (+ services/character)"
  ssh "${REMOTE}" "mkdir -p ${REMOTE_DIR}/backend/src/config/character ${REMOTE_DIR}/backend/src/services/character /var/lib/lbg/character"
  rsync -az "${PACK_SRC}" \
    "${REMOTE}:${REMOTE_DIR}/backend/src/config/character/compagnon_v1.json"
  rsync -az "${PACK_SRC}" \
    "${REMOTE}:${REMOTE_DIR}/backend/src/services/character/compagnon_v1.json"
fi
if [[ -f "${CHARACTER_API}" ]]; then
  echo "==> Overlay character_api → backend"
  rsync -az "${CHARACTER_API}" \
    "${REMOTE}:${REMOTE_DIR}/backend/src/routers/character_api.py"
  ssh "${REMOTE}" bash -s <<'PATCH'
set -euo pipefail
FACTORY=/opt/orchestrateur/backend/src/app/factory.py
if [[ -f "$FACTORY" ]] && ! grep -q 'character_api' "$FACTORY"; then
  python3 - <<'PY'
from pathlib import Path
p = Path("/opt/orchestrateur/backend/src/app/factory.py")
text = p.read_text()
imp = "from src.routers.character_api import router as character_api_router\n"
inc = "    app.include_router(character_api_router)\n"
if "character_api_router" not in text:
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
    print("factory.py: character_api router wired")
else:
    print("factory.py: already wired")
PY
else
  echo "factory.py: character_api already present or missing factory"
fi
PATCH
fi

if [[ -f "${SPONTANEITY_LAYER}" ]]; then
  echo "==> Overlay spontaneity → backend"
  rsync -az "${SPONTANEITY_LAYER}" \
    "${REMOTE}:${REMOTE_DIR}/backend/src/services/spontaneity.py"
  ssh "${REMOTE}" "mkdir -p /var/lib/lbg/spontaneity"
fi
if [[ -f "${SPONTANEITY_API}" ]]; then
  echo "==> Overlay spontaneity_api → backend"
  rsync -az "${SPONTANEITY_API}" \
    "${REMOTE}:${REMOTE_DIR}/backend/src/routers/spontaneity_api.py"
  ssh "${REMOTE}" bash -s <<'PATCH'
set -euo pipefail
FACTORY=/opt/orchestrateur/backend/src/app/factory.py
if [[ -f "$FACTORY" ]] && ! grep -q 'spontaneity_api' "$FACTORY"; then
  python3 - <<'PY'
from pathlib import Path
p = Path("/opt/orchestrateur/backend/src/app/factory.py")
text = p.read_text()
imp = "from src.routers.spontaneity_api import router as spontaneity_api_router\n"
inc = "    app.include_router(spontaneity_api_router)\n"
if "spontaneity_api_router" not in text:
    needle = "from src.routers.character_api import router as character_api_router\n"
    if needle in text:
        text = text.replace(needle, needle + imp, 1)
    else:
        needle_team = "from src.routers.team import router as team_router\n"
        if needle_team in text:
            text = text.replace(needle_team, needle_team + imp, 1)
        else:
            text = imp + text
    needle2 = "    app.include_router(character_api_router)\n"
    if needle2 in text:
        text = text.replace(needle2, needle2 + inc, 1)
    else:
        needle_team2 = "    app.include_router(team_router)\n"
        if needle_team2 in text:
            text = text.replace(needle_team2, needle_team2 + inc, 1)
        else:
            text = text.replace("    app.include_router(core_router)\n", "    app.include_router(core_router)\n" + inc, 1)
    p.write_text(text)
    print("factory.py: spontaneity_api router wired")
else:
    print("factory.py: already wired")
PY
else
  echo "factory.py: spontaneity_api already present or missing factory"
fi
PATCH
fi

if [[ -f "${TTS_LAYER}" ]]; then
  echo "==> Overlay tts → backend"
  rsync -az "${TTS_LAYER}" \
    "${REMOTE}:${REMOTE_DIR}/backend/src/services/tts.py"
fi
if [[ -f "${TTS_API}" ]]; then
  echo "==> Overlay tts_api → backend"
  rsync -az "${TTS_API}" \
    "${REMOTE}:${REMOTE_DIR}/backend/src/routers/tts_api.py"
  ssh "${REMOTE}" bash -s <<'PATCH'
set -euo pipefail
FACTORY=/opt/orchestrateur/backend/src/app/factory.py
ENVF=/opt/orchestrateur/.env
# Env TTS (Edge DeniseNeural + fallback Piper) — idempotent
REQ=/opt/orchestrateur/backend/requirements.txt
if [[ -f "$REQ" ]] && ! grep -qiE '^edge-tts([=<>]|$)' "$REQ"; then
  echo 'edge-tts>=6.1.0' >> "$REQ"
  echo "requirements.txt: edge-tts added"
fi
if [[ -f "$ENVF" ]]; then
  grep -q '^LBG_TTS_ENABLED=' "$ENVF" || echo 'LBG_TTS_ENABLED=1' >> "$ENVF"
  grep -q '^LBG_TTS_PROVIDER=' "$ENVF" || echo 'LBG_TTS_PROVIDER=edge' >> "$ENVF"
  grep -q '^LBG_TTS_FALLBACK=' "$ENVF" || echo 'LBG_TTS_FALLBACK=piper' >> "$ENVF"
  grep -q '^LBG_EDGE_VOICE=' "$ENVF" || echo 'LBG_EDGE_VOICE=fr-FR-DeniseNeural' >> "$ENVF"
  grep -q '^LBG_PIPER_URL=' "$ENVF" || echo 'LBG_PIPER_URL=http://192.168.0.111:8098' >> "$ENVF"
  grep -q '^LBG_PIPER_VOICE=' "$ENVF" || echo 'LBG_PIPER_VOICE=fr_FR-siwis-medium' >> "$ENVF"
fi
if [[ -f "$FACTORY" ]] && ! grep -q 'tts_api' "$FACTORY"; then
  python3 - <<'PY'
from pathlib import Path
p = Path("/opt/orchestrateur/backend/src/app/factory.py")
text = p.read_text()
imp = "from src.routers.tts_api import router as tts_api_router\n"
inc = "    app.include_router(tts_api_router)\n"
if "tts_api_router" not in text:
    needle = "from src.routers.spontaneity_api import router as spontaneity_api_router\n"
    if needle in text:
        text = text.replace(needle, needle + imp, 1)
    else:
        needle_ch = "from src.routers.character_api import router as character_api_router\n"
        if needle_ch in text:
            text = text.replace(needle_ch, needle_ch + imp, 1)
        else:
            needle_team = "from src.routers.team import router as team_router\n"
            if needle_team in text:
                text = text.replace(needle_team, needle_team + imp, 1)
            else:
                text = imp + text
    needle2 = "    app.include_router(spontaneity_api_router)\n"
    if needle2 in text:
        text = text.replace(needle2, needle2 + inc, 1)
    else:
        needle_ch2 = "    app.include_router(character_api_router)\n"
        if needle_ch2 in text:
            text = text.replace(needle_ch2, needle_ch2 + inc, 1)
        else:
            needle_team2 = "    app.include_router(team_router)\n"
            if needle_team2 in text:
                text = text.replace(needle_team2, needle_team2 + inc, 1)
            else:
                text = text.replace("    app.include_router(core_router)\n", "    app.include_router(core_router)\n" + inc, 1)
    p.write_text(text)
    print("factory.py: tts_api router wired")
else:
    print("factory.py: already wired")
PY
else
  echo "factory.py: tts_api already present or missing factory"
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
  curl -fsS -m 90 -X POST "http://${REMOTE_HOST}:5174/api/ask" \
    -H 'Content-Type: application/json' \
    -d '{"prompt":"dis moi quelque chose d interessant sur toi","mode":"auto","profile":"compagnon","agent":"team"}' \
    | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('response') or {}; c=(r.get('content') or ''); print('identity', 'fallback' if 'compétence exacte' in c else 'ok', (r.get('source') or r.get('model') or '')[:40], c[:100].replace(chr(10),' '))"
  curl -fsS "http://${REMOTE_HOST}:5174/api/character/" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print('character', d.get('ok'), d.get('pack_id'), 'dials', len(d.get('dials') or {}))"
  curl -fsS "http://${REMOTE_HOST}:5174/api/spontaneity/" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print('spontaneity', d.get('ok'), 'enabled', d.get('enabled'), 'seeds', len(d.get('evolution_seeds') or []))"
  curl -fsS "http://${REMOTE_HOST}:5174/api/tts/health" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print('tts', d.get('ok'), 'enabled', d.get('enabled'), 'voice', d.get('voice'))"
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
