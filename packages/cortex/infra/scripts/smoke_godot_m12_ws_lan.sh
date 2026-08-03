#!/usr/bin/env bash
# Smoke M12 durci — auth HTTP M11 puis WS login → zone_state/enter_world → move (±1.5 m).
#
# Préfère Python local avec websockets ; sinon exécute le probe sur LBG_GATEWAY_SSH_HOST.
set -euo pipefail

HTTP_BASE="${LBG_GATEWAY_HTTP:-http://192.168.0.246:8765}"
WS_URL="${LBG_GATEWAY_WS:-ws://192.168.0.246:50000}"
USER="${TEOME_USERNAME:-Teome}"
PASS="${TEOME_PASSWORD:-dev}"
SSH_HOST="${LBG_GATEWAY_SSH_HOST:-192.168.0.246}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROBE="${SCRIPT_DIR}/smoke_godot_m12_ws_probe.py"

echo "=== Smoke M12 WS session_token + move ==="

login_json="$(curl -sfS --max-time 15 -X POST "${HTTP_BASE}/v1/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"type\":\"login\",\"username\":\"${USER}\",\"password\":\"${PASS}\"}")"
TOKEN="$(python3 -c "import json,sys; d=json.loads(sys.argv[1]); print(d['session_token'])" "${login_json}")"
CHAR_ID="$(python3 -c "import json,sys; d=json.loads(sys.argv[1]); print(d['characters'][0]['id'])" "${login_json}")"

curl -sfS --max-time 10 -X POST "${HTTP_BASE}/v1/auth/select_character" \
  -H "Authorization: Bearer ${TOKEN}" -H 'Content-Type: application/json' \
  -d "{\"character_id\": ${CHAR_ID}}" >/dev/null
curl -sfS --max-time 10 -X POST "${HTTP_BASE}/v1/auth/enter_zone" \
  -H "Authorization: Bearer ${TOKEN}" -H 'Content-Type: application/json' \
  -d '{"zone":"tatooine"}' >/dev/null

echo "token ok char=${CHAR_ID} — connecting ${WS_URL}"

export TOKEN CHAR_ID WS_URL
export LBG_M12_MOVE_TOL_M="${LBG_M12_MOVE_TOL_M:-1.5}"
export LBG_M12_MOVE_DX="${LBG_M12_MOVE_DX:-2.0}"
export LBG_M12_MOVE_DZ="${LBG_M12_MOVE_DZ:-1.0}"

if python3 -c "import websockets" 2>/dev/null; then
  python3 "${PROBE}"
else
  echo "websockets local absent — probe via ${SSH_HOST}"
  # shellcheck disable=SC2029
  ssh "lbg@${SSH_HOST}" \
    "TOKEN='${TOKEN}' CHAR_ID='${CHAR_ID}' WS_URL='${WS_URL}' \
     LBG_M12_MOVE_TOL_M='${LBG_M12_MOVE_TOL_M}' \
     LBG_M12_MOVE_DX='${LBG_M12_MOVE_DX}' LBG_M12_MOVE_DZ='${LBG_M12_MOVE_DZ}' \
     python3 -" < "${PROBE}"
fi
