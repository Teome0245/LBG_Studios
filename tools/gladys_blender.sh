#!/usr/bin/env bash
# Lance Blender avec le serveur MCP actif (soit sous X11/Wayland actif, soit sous xvfb-run en headless)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HELPER="${SCRIPT_DIR}/blender_headless_mcp.py"

if [[ -n "${DISPLAY:-}" ]]; then
  echo "=== Lancement Blender MCP (Affichage actif: $DISPLAY) ==="
  exec blender --python "${HELPER}" "$@"
else
  echo "=== Lancement Blender MCP (Headless via xvfb-run) ==="
  exec xvfb-run -a blender --python "${HELPER}" "$@"
fi
