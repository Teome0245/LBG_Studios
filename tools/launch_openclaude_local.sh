#!/usr/bin/env bash
# launch_openclaude_local.sh — Lanceur OpenClaude CLI branché sur Ollama local (.110)
# Coût : 0 € | Pas de quota Cloud | Qwen3 MoE 30B abliterated
# Usage : tools/launch_openclaude_local.sh [-p "prompt"] [fichiers...]

set -euo pipefail

OLLAMA_HOST="${LBG_OLLAMA_110:-http://192.168.0.110:11434}"
DEFAULT_MODEL="${LBG_CODER_MODEL:-lbg-qwen3-coder:30b}"
OPENCLAUDE_BIN="$(which openclaude 2>/dev/null || echo "/home/lbg/.local/share/mise/installs/node/26.8.1/bin/openclaude")"

if [[ ! -x "$OPENCLAUDE_BIN" ]]; then
    echo "❌ Erreur : binaire openclaude introuvable."
    exit 1
fi

export CLAUDE_CODE_USE_OPENAI=1
export OPENAI_BASE_URL="${OLLAMA_HOST}/v1"
export OPENAI_API_KEY="ollama"
export OPENAI_MODEL="${DEFAULT_MODEL}"
export OPENCLAUDE_OLLAMA_NUM_CTX="${OPENCLAUDE_OLLAMA_NUM_CTX:-16384}"

echo "=========================================================="
echo "⚡ Gladys Worker : OpenClaude CLI sur Ollama local (0€)"
echo "   Endpoint : ${OLLAMA_HOST}/v1"
echo "   Modèle   : ${DEFAULT_MODEL}"
echo "=========================================================="

exec "$OPENCLAUDE_BIN" "$@"
