#!/usr/bin/env bash
# Smoke escorte hub — selftest headless + sonde HTTP optionnelle :8787
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HUB="${ROOT}/packages/prime-hub"
GODOT="${HUB}/tools/godot"
if [[ ! -x "${GODOT}" ]]; then
  GODOT="$(command -v godot || true)"
fi
[[ -n "${GODOT}" && -x "${GODOT}" ]] || { echo "FAIL: godot introuvable" >&2; exit 1; }

echo "=== Escort selftest (headless) ==="
"${GODOT}" --headless --path "${HUB}" -s res://tools/escort_selftest.gd
echo "OK escort_selftest"

HUB_URL="${LBG_PRIME_HUB:-http://192.168.0.246:8787}"
HUB_URL="${HUB_URL%/}"
if curl -sfS --connect-timeout 2 --max-time 4 "${HUB_URL}/healthz" >/dev/null 2>&1; then
  echo "=== Escort HTTP live ${HUB_URL} ==="
  PLAYER="${LBG_ESCORT_PLAYER:-EscortSmoke}"
  code="$(curl -sS -o /tmp/escort_snap.json -w '%{http_code}' --max-time 8 \
    "${HUB_URL}/v1/quests/escort?player=${PLAYER}" || true)"
  if [[ "${code}" == "200" ]]; then
    head -c 400 /tmp/escort_snap.json; echo
    echo "OK escort HTTP snapshot"
  else
    echo "WARN escort endpoint HTTP ${code} (deploy prime-hub requis pour live)"
  fi
else
  echo "SKIP live hub (${HUB_URL} unreachable)"
fi

echo "SMOKE_ESCORT_HUB_OK"
