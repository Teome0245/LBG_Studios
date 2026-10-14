#!/usr/bin/env bash
# Smoke show La Perle — selftest headless + sonde HTTP :8787
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HUB="${ROOT}/packages/prime-hub"
GODOT="${HUB}/tools/godot"
if [[ ! -x "${GODOT}" ]]; then
  GODOT="$(command -v godot || true)"
fi
[[ -n "${GODOT}" && -x "${GODOT}" ]] || { echo "FAIL: godot introuvable" >&2; exit 1; }

echo "=== Show selftest (headless) ==="
"${GODOT}" --headless --path "${HUB}" -s res://tools/show_selftest.gd
echo "OK show_selftest"

HUB_URL="${LBG_PRIME_HUB:-http://192.168.0.246:8787}"
HUB_URL="${HUB_URL%/}"
if curl -sfS --connect-timeout 2 --max-time 4 "${HUB_URL}/healthz" >/dev/null 2>&1; then
  echo "=== Show HTTP ${HUB_URL} ==="
  code="$(curl -sS -o /tmp/show_snap.json -w '%{http_code}' --max-time 8 \
    "${HUB_URL}/v1/show/status" || true)"
  if [[ "${code}" == "200" ]]; then
    head -c 400 /tmp/show_snap.json; echo
    echo "OK show HTTP snapshot"
  else
    echo "WARN show endpoint HTTP ${code} (deploy prime-hub requis)"
  fi
else
  echo "SKIP live hub"
fi
echo "SMOKE_SHOW_HUB_OK"
