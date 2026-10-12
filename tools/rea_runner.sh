#!/usr/bin/env bash
# tools/rea_runner.sh — Wrapper universel REA (Reverse Engineer Anything)
# Usage:
#   tools/rea_runner.sh                 -> Lance le serveur MCP stdio
#   tools/rea_runner.sh <command> ...   -> Lance une sous-commande REA (ex: analyze-javascript-application ...)

set -euo pipefail

if ! command -v npx >/dev/null 2>&1; then
    echo "[!] Erreur : 'npx' est introuvable. Veuillez installer Node.js." >&2
    exit 1
fi

if [ $# -eq 0 ]; then
    # Mode serveur MCP stdio par défaut
    exec npx -y rea-agents@latest
else
    # Mode CLI spécifique
    exec npx -y rea-agents@latest "$@"
fi
