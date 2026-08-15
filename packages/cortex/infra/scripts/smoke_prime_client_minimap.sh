#!/usr/bin/env bash
# Smoke M9b — minimap HUD Prime Client (fichiers + grep scène).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# cortex/infra/scripts → packages/prime-client (sibling)
STUDIOS_PRIME="$(cd "${SCRIPT_DIR}/../../../prime-client" 2>/dev/null && pwd || true)"
STUDIOS_PRIME="${STUDIOS_PRIME:-/home/sdesh/projects/LBG_Studios/packages/prime-client}"

if [[ -n "${LBG_PRIME_CLIENT_ROOT:-}" && -d "${LBG_PRIME_CLIENT_ROOT}" ]]; then
  PRIME_ROOT="${LBG_PRIME_CLIENT_ROOT}"
elif [[ -d "${STUDIOS_PRIME}" ]]; then
  PRIME_ROOT="${STUDIOS_PRIME}"
elif [[ -n "${LBG_NEW_MMO_ROOT:-}" && -d "${LBG_NEW_MMO_ROOT}/prime-client" ]]; then
  PRIME_ROOT="${LBG_NEW_MMO_ROOT}/prime-client"
else
  PRIME_ROOT="${STUDIOS_PRIME}"
fi

echo "=== Smoke M9b minimap (${PRIME_ROOT}) ==="

fail=0
check() {
  if [[ -f "$1" ]]; then
    echo "OK $1"
  else
    echo "KO $1"
    fail=1
  fi
}

check "${PRIME_ROOT}/scripts/minimap_hud.gd"
check "${PRIME_ROOT}/scenes/ui/minimap_hud.tscn"
check "${PRIME_ROOT}/config/minimap_config.json"

if grep -q "minimap_hud" "${PRIME_ROOT}/scenes/main.tscn" 2>/dev/null; then
  echo "OK main.tscn contient minimap_hud"
else
  echo "KO main.tscn sans minimap_hud"
  fail=1
fi

if [[ "${fail}" -ne 0 ]]; then
  exit 2
fi
echo "Smoke M9b minimap OK"
