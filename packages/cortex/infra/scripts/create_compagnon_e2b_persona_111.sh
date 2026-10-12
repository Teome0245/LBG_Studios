#!/usr/bin/env bash
# Crée lbg-compagnon-e4b-v1 sur Ollama (Modelfile perso, base E4b-qat).
#
# Usage :
#   bash packages/cortex/infra/scripts/create_compagnon_e2b_persona_111.sh
#   bash packages/cortex/infra/scripts/create_compagnon_e2b_persona_111.sh --activate
#
# Défauts : base E4b-qat, host .111 (causerie). Override :
#   LBG_COMPAGNON_PERSONA_TAG=… LBG_COMPAGNON_PERSONA_BASE=… LBG_OLLAMA_LIGHT_HOST=…
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORTEX_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PERSONA_DIR="${CORTEX_ROOT}/infra/llm_persona_e2b"
BASE="${LBG_COMPAGNON_PERSONA_BASE:-huihui_ai/gemma-4-abliterated:E4b-qat}"
TAG="${LBG_COMPAGNON_PERSONA_TAG:-lbg-compagnon-e4b-v1}"
HOST="${LBG_OLLAMA_LIGHT_HOST:-192.168.0.111}"
ACTIVATE=0
[[ "${1:-}" == "--activate" ]] && ACTIVATE=1

python3 "${PERSONA_DIR}/build_modelfile.py" --base "${BASE}" --out "${PERSONA_DIR}/Modelfile"

echo "==> ensure base ${BASE} on ${HOST}"
bash "${CORTEX_ROOT}/infra/scripts/pull_ollama_model_lan.sh" "${BASE}" "http://${HOST}:11434"

echo "==> ollama create ${TAG} @ ${HOST} (CLI SSH)"
scp -q "${PERSONA_DIR}/Modelfile" "root@${HOST}:/tmp/lbg-compagnon-persona.Modelfile"
ssh "root@${HOST}" bash -s <<EOF
set -euo pipefail
ollama create ${TAG} -f /tmp/lbg-compagnon-persona.Modelfile
ollama show ${TAG} | head -40
EOF

echo "==> tags (filtre e4b / e2b / lbg-compagnon)"
curl -sS "http://${HOST}:11434/api/tags" | python3 -c "
import json,sys
for m in json.load(sys.stdin).get('models') or []:
    n=m.get('name') or ''
    if any(x in n.lower() for x in ('e4b','e2b','lbg-compagnon')):
        print(' -', n)
"

if [[ "$ACTIVATE" -eq 1 ]]; then
  REMOTE_USER="${LBG_ORCH_CT100_USER:-root}"
  REMOTE_HOST="${LBG_ORCH_CT100_HOST:-192.168.0.100}"
  echo "==> Activate on .100 env → ${TAG}"
  ssh "${REMOTE_USER}@${REMOTE_HOST}" bash -s <<EOF
set -euo pipefail
ENVF=/opt/orchestrateur/.env
touch "\$ENVF"
upsert() {
  local key="\$1" val="\$2"
  if grep -q "^\${key}=" "\$ENVF"; then
    sed -i "s|^\${key}=.*|\${key}=\${val}|" "\$ENVF"
  else
    echo "\${key}=\${val}" >> "\$ENVF"
  fi
}
upsert LBG_COMPAGNON_LAB_CHAT_MODEL "${TAG}"
upsert LBG_COMPANION_LLM_MODEL "${TAG}"
cd /opt/orchestrateur
docker compose up -d --force-recreate backend
docker compose exec -T backend printenv LBG_COMPAGNON_LAB_CHAT_MODEL LBG_COMPANION_LLM_MODEL || true
EOF
fi

echo "OK ${TAG} (base ${BASE}) — rollback: lbg-compagnon-e2b-v1"
