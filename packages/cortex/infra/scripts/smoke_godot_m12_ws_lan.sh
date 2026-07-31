#!/usr/bin/env bash
# Smoke M12 — auth HTTP M11 puis WS login+session_token → enter_world / zone_state.
#
# Préfère Python local avec websockets ; sinon exécute sur 192.168.0.245.
set -euo pipefail

HTTP_BASE="${LBG_GATEWAY_HTTP:-http://192.168.0.246:8765}"
WS_URL="${LBG_GATEWAY_WS:-ws://192.168.0.246:50000}"
USER="${TEOME_USERNAME:-Teome}"
PASS="${TEOME_PASSWORD:-dev}"
SSH_HOST="${LBG_GATEWAY_SSH_HOST:-192.168.0.246}"

echo "=== Smoke M12 WS session_token ==="

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

run_ws_probe() {
  TOKEN="${TOKEN}" CHAR_ID="${CHAR_ID}" WS_URL="${WS_URL}" python3 - <<'PY'
import asyncio, json, os
import websockets

async def main():
    url = os.environ["WS_URL"]
    token = os.environ["TOKEN"]
    cid = int(os.environ["CHAR_ID"])
    async with websockets.connect(url, open_timeout=8) as ws:
        await ws.send(json.dumps({"type": "login", "proto": "lbg-ws/2", "session_token": token}))
        raw = await asyncio.wait_for(ws.recv(), timeout=8)
        msg = json.loads(raw)
        assert msg.get("type") == "login_result" and msg.get("success") is True, msg
        await ws.send(json.dumps({"type": "select_character", "proto": "lbg-ws/2", "character_id": cid}))
        for _ in range(5):
            raw = await asyncio.wait_for(ws.recv(), timeout=8)
            msg = json.loads(raw)
            if msg.get("type") in ("enter_world", "zone_state"):
                print(
                    "OK M12 —",
                    msg.get("type"),
                    "your_character_id=",
                    msg.get("your_character_id"),
                    "entities=",
                    len(msg.get("entities") or []),
                )
                return
        raise SystemExit("pas de enter_world/zone_state")

asyncio.run(main())
PY
}

if python3 -c "import websockets" 2>/dev/null; then
  run_ws_probe
else
  echo "websockets local absent — probe via ${SSH_HOST}"
  ssh "lbg@${SSH_HOST}" "TOKEN='${TOKEN}' CHAR_ID='${CHAR_ID}' WS_URL='${WS_URL}' python3 -" <<'PY'
import asyncio, json, os
import websockets

async def main():
    url = os.environ["WS_URL"]
    token = os.environ["TOKEN"]
    cid = int(os.environ["CHAR_ID"])
    async with websockets.connect(url, open_timeout=8) as ws:
        await ws.send(json.dumps({"type": "login", "proto": "lbg-ws/2", "session_token": token}))
        raw = await asyncio.wait_for(ws.recv(), timeout=8)
        msg = json.loads(raw)
        assert msg.get("type") == "login_result" and msg.get("success") is True, msg
        await ws.send(json.dumps({"type": "select_character", "proto": "lbg-ws/2", "character_id": cid}))
        for _ in range(5):
            raw = await asyncio.wait_for(ws.recv(), timeout=8)
            msg = json.loads(raw)
            if msg.get("type") in ("enter_world", "zone_state"):
                print("OK M12 —", msg.get("type"), "your_character_id=", msg.get("your_character_id"), "entities=", len(msg.get("entities") or []))
                return
        raise SystemExit("pas de enter_world/zone_state")

asyncio.run(main())
PY
fi
