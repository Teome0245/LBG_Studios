#!/usr/bin/env bash
# Lance prime-hub headless (G0) — ports 8788 WS / 8789 HTTP
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GODOT="${GODOT_BIN:-}"
if [[ -z "$GODOT" ]]; then
  if [[ -x "$ROOT/tools/godot" ]]; then
    GODOT="$ROOT/tools/godot"
  elif command -v godot >/dev/null 2>&1; then
    GODOT="$(command -v godot)"
  else
    echo "Godot introuvable. Lance: bash scripts/fetch_godot.sh" >&2
    exit 1
  fi
fi
export LBG_PRIME_HUB_WS_PORT="${LBG_PRIME_HUB_WS_PORT:-8788}"
export LBG_PRIME_HUB_HTTP_PORT="${LBG_PRIME_HUB_HTTP_PORT:-8789}"
cd "$ROOT"
exec "$GODOT" --headless --path "$ROOT" res://scenes/server_main.tscn
