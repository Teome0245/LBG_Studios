#!/usr/bin/env bash
# Smoke M11 — login HTTP lbg_gateway → select_character → enter_zone (sans retail).
#
# Usage :
#   bash infra/scripts/smoke_godot_m11_login_lan.sh
#   LBG_GATEWAY_HTTP=http://192.168.0.246:8765 TEOME_PASSWORD='…' bash …
#
set -euo pipefail

HTTP_BASE="${LBG_GATEWAY_HTTP:-http://192.168.0.246:8765}"
USER="${TEOME_USERNAME:-Teome}"
PASS="${TEOME_PASSWORD:-dev}"
ZONE="${LBG_M11_ZONE:-tatooine}"

echo "=== Smoke M11 login HTTP ==="
echo "gateway: ${HTTP_BASE}"
echo "user: ${USER}"

health="$(curl -sfS --max-time 5 "${HTTP_BASE}/health" || true)"
if [[ -z "${health}" ]]; then
  echo "FAIL: /health injoignable sur ${HTTP_BASE}" >&2
  echo "  → déployer gateway Prime : LBG_GATEWAY_SSH_HOST=192.168.0.246 bash infra/scripts/run_lbg_gateway_vm.sh" >&2
  exit 1
fi
echo "health: ${health}"

login_json="$(curl -sfS --max-time 15 -X POST "${HTTP_BASE}/v1/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"type\":\"login\",\"username\":\"${USER}\",\"password\":\"${PASS}\"}" || true)"
if [[ -z "${login_json}" ]]; then
  echo "FAIL: POST /v1/auth/login" >&2
  exit 2
fi
echo "login: ${login_json}"

TOKEN="$(python3 -c "import json,sys; d=json.loads(sys.argv[1]); print(d.get('session_token') or '')" "${login_json}")"
CHAR_ID="$(python3 -c "import json,sys; d=json.loads(sys.argv[1]); cs=d.get('characters') or []; print(cs[0]['id'] if cs else '')" "${login_json}")"
if [[ -z "${TOKEN}" || -z "${CHAR_ID}" ]]; then
  echo "FAIL: session_token ou characters manquant" >&2
  exit 3
fi
echo "token=${TOKEN:0:12}… character_id=${CHAR_ID}"

select_json="$(curl -sfS --max-time 10 -X POST "${HTTP_BASE}/v1/auth/select_character" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H 'Content-Type: application/json' \
  -d "{\"character_id\": ${CHAR_ID}}" || true)"
if [[ -z "${select_json}" ]]; then
  echo "FAIL: POST /v1/auth/select_character" >&2
  exit 4
fi
echo "select: ${select_json}"

enter_json="$(curl -sfS --max-time 10 -X POST "${HTTP_BASE}/v1/auth/enter_zone" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H 'Content-Type: application/json' \
  -d "{\"zone\":\"${ZONE}\"}" || true)"
if [[ -z "${enter_json}" ]]; then
  echo "FAIL: POST /v1/auth/enter_zone" >&2
  exit 5
fi
echo "enter: ${enter_json}"

ENTER_JSON="${enter_json}" python3 -c '
import json, os
enter = json.loads(os.environ["ENTER_JSON"])
assert enter.get("ok") is True, enter
assert enter.get("your_character_id"), enter
assert enter.get("ws_url"), enter
print("OK M11 smoke — your_character_id=", enter["your_character_id"], "ws_url=", enter["ws_url"])
'
