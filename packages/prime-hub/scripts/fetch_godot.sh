#!/usr/bin/env bash
# Télécharge Godot 4.6.x Linux x86_64 dans tools/
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TOOLS="$ROOT/tools"
VER="${GODOT_VERSION:-4.6.3-stable}"
ARCHIVE="Godot_v${VER}_linux.x86_64.zip"
BASE_URL="${GODOT_URL:-https://github.com/godotengine/godot/releases/download/${VER}}"
mkdir -p "$TOOLS"
cd "$TOOLS"
if [[ -x "$TOOLS/godot" ]]; then
  echo "OK: $TOOLS/godot déjà présent"
  "$TOOLS/godot" --version || true
  exit 0
fi
echo "Téléchargement $BASE_URL/$ARCHIVE …"
if ! curl -fL --retry 3 -o "$ARCHIVE" "$BASE_URL/$ARCHIVE"; then
  echo "Échec download. Pose manuellement un binaire Godot 4.6 dans $TOOLS/godot" >&2
  exit 1
fi
unzip -o "$ARCHIVE"
BIN=$(ls -1 Godot_v*_linux.x86_64 2>/dev/null | head -1 || true)
if [[ -z "${BIN:-}" ]]; then
  echo "Binaire introuvable dans l'archive" >&2
  exit 1
fi
ln -sfn "$TOOLS/$BIN" "$TOOLS/godot"
chmod +x "$TOOLS/$BIN"
echo "OK: $($TOOLS/godot --version)"
