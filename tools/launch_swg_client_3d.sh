#!/usr/bin/env bash
# Lance le Client SWG Pre-CU 3D en Godot 4
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN="${PROJECT_ROOT}/packages/prime-hub/tools/Godot_v4.6.3-stable_linux.x86_64"

if [ ! -f "$BIN" ]; then
    BIN="godot"
fi

echo "[LBG] Lancement du Client SWG Pre-CU 3D (Lost Heaven)..."
exec "$BIN" --path "${PROJECT_ROOT}/packages/swg-client" "$@"

