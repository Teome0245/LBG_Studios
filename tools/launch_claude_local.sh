#!/usr/bin/env bash
# launch_claude_local.sh — Lanceur Claude Code CLI branché sur Ollama local (.110)
# Coût : 0 € | Pas de limite de tokens Anthropic | Confidentialité totale

set -euo pipefail

OLLAMA_HOST="${LBG_OLLAMA_110:-http://192.168.0.110:11434}"
DEFAULT_MODEL="${LBG_CODER_MODEL:-huihui_ai/qwen3-coder-abliterated:30b}"
CLAUDE_BIN="/home/lbg/.local/bin/claude"

if [[ ! -x "$CLAUDE_BIN" ]]; then
    echo "❌ Erreur : binaire Claude introuvable dans $CLAUDE_BIN"
    exit 1
fi

echo "=========================================================="
echo "⚡ Gladys Worker : Claude Code CLI sur Ollama local (0€)"
echo "   Endpoint : $OLLAMA_HOST"
echo "   Modèle   : $DEFAULT_MODEL"
echo "=========================================================="

# Export des variables pour détourner les appels vers Ollama
export ANTHROPIC_BASE_URL="$OLLAMA_HOST"
export ANTHROPIC_API_KEY="ollama-local-no-key"
export CLAUDE_CODE_MODEL="$DEFAULT_MODEL"

# Lancement avec options permissives adaptées à l'environnement autonome
exec "$CLAUDE_BIN" "$@"
