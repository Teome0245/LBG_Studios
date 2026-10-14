#!/usr/bin/env bash
# Smoke hotbar API — use_item + companion escort
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HUB="${ROOT}/packages/prime-hub"
GODOT="${HUB}/tools/godot"
[[ -x "${GODOT}" ]] || GODOT="$(command -v godot || true)"
[[ -n "${GODOT}" && -x "${GODOT}" ]] || { echo "FAIL: godot" >&2; exit 1; }

echo "=== Hotbar API selftest ==="
"${GODOT}" --headless --path "${HUB}" -s res://tools/hotbar_api_selftest.gd
echo "OK hotbar_api_selftest"

HUB_URL="${LBG_PRIME_HUB:-http://192.168.0.246:8787}"
HUB_URL="${HUB_URL%/}"
if curl -sfS --connect-timeout 2 --max-time 4 "${HUB_URL}/healthz" >/dev/null 2>&1; then
  echo "=== Hotbar HTTP live ==="
  PLAYER="${LBG_HOTBAR_PLAYER:-HotbarSmoke}"
  # seed inventory via tip/credits not needed — use may 400 without item
  code_u="$(curl -sS -o /tmp/hotbar_use.json -w '%{http_code}' --max-time 8 \
    -X POST "${HUB_URL}/v1/inventory/use" -H 'Content-Type: application/json' \
    -d "{\"player\":\"${PLAYER}\"}" || true)"
  echo "use HTTP ${code_u} $(head -c 180 /tmp/hotbar_use.json 2>/dev/null)"
  code_e="$(curl -sS -o /tmp/hotbar_esc.json -w '%{http_code}' --max-time 8 \
    -X POST "${HUB_URL}/v1/companion/escort" -H 'Content-Type: application/json' \
    -d "{\"player\":\"${PLAYER}\",\"duration_s\":12}" || true)"
  if [[ "${code_e}" == "200" ]]; then
    head -c 240 /tmp/hotbar_esc.json; echo
    echo "OK companion escort"
  else
    echo "WARN escort HTTP ${code_e} (deploy requis)"
  fi
else
  echo "SKIP live hub"
fi
echo "SMOKE_HOTBAR_HUB_OK"
