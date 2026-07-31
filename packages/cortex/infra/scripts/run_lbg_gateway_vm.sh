#!/usr/bin/env bash
# Lance lbg_gateway sur la VM Prime (246) — HTTP M11 :8765 + WS lbg-ws/2 :50000.
#
# Défaut produit : 192.168.0.246 (Core3 Prime + snapshots + auth SQL locale).
# Override legacy PreCU : LBG_GATEWAY_SSH_HOST=192.168.0.245 bash …
set -euo pipefail

HOST="${LBG_GATEWAY_SSH_HOST:-192.168.0.246}"
USER="${LBG_GATEWAY_SSH_USER:-lbg}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
REMOTE_DIR="${LBG_GATEWAY_REMOTE_DIR:-/home/lbg/lbg-gateway}"
PUBLIC_HOST="${LBG_GATEWAY_PUBLIC_HOST:-${HOST}}"

echo "[gateway] sync + start on ${USER}@${HOST} (${REMOTE_DIR}) public=${PUBLIC_HOST}"
ssh "${USER}@${HOST}" "mkdir -p ${REMOTE_DIR}"
scp -q "${ROOT}/services/lbg_gateway/main.py" "${USER}@${HOST}:${REMOTE_DIR}/main.py"
scp -q "${ROOT}/services/lbg_gateway/dialogue_ia.py" "${USER}@${HOST}:${REMOTE_DIR}/dialogue_ia.py"
scp -q "${ROOT}/services/lbg_gateway/catalog_context.py" "${USER}@${HOST}:${REMOTE_DIR}/catalog_context.py"
scp -q "${ROOT}/services/lbg_gateway/world_coords.py" "${USER}@${HOST}:${REMOTE_DIR}/world_coords.py"
scp -q "${ROOT}/services/lbg_gateway/zone_players.py" "${USER}@${HOST}:${REMOTE_DIR}/zone_players.py"
scp -q "${ROOT}/services/lbg_gateway/pending_bridge.py" "${USER}@${HOST}:${REMOTE_DIR}/pending_bridge.py"
scp -q "${ROOT}/services/lbg_gateway/roster_filter.py" "${USER}@${HOST}:${REMOTE_DIR}/roster_filter.py"
scp -q "${ROOT}/services/lbg_gateway/lbg_ws2.py" "${USER}@${HOST}:${REMOTE_DIR}/lbg_ws2.py"
scp -q "${ROOT}/services/lbg_gateway/zone_bridge_feed.py" "${USER}@${HOST}:${REMOTE_DIR}/zone_bridge_feed.py"
scp -q "${ROOT}/services/lbg_gateway/auth_sql.py" "${USER}@${HOST}:${REMOTE_DIR}/auth_sql.py"
scp -q "${ROOT}/services/lbg_gateway/auth_sessions.py" "${USER}@${HOST}:${REMOTE_DIR}/auth_sessions.py"
scp -q "${ROOT}/services/lbg_gateway/http_auth.py" "${USER}@${HOST}:${REMOTE_DIR}/http_auth.py"
scp -q "${ROOT}/content/core3/core3_npc_catalog.json" "${USER}@${HOST}:${REMOTE_DIR}/core3_npc_catalog.json"
ssh "${USER}@${HOST}" "mkdir -p ${REMOTE_DIR}/locations"
scp -q "${ROOT}"/content/core3/locations/*.json "${USER}@${HOST}:${REMOTE_DIR}/locations/"

ssh "${USER}@${HOST}" "REMOTE_DIR='${REMOTE_DIR}' PUBLIC_HOST='${PUBLIC_HOST}' bash -s" <<'EOF'
set -euo pipefail
export LBG_GATEWAY_HOST=0.0.0.0
export LBG_GATEWAY_PORT=50000
export LBG_GATEWAY_SNAPSHOTS=/opt/lbg-new-mmo-clean/MMOCoreORB/bin/ia_bridge/npc_snapshots.json
export LBG_GATEWAY_PLAYER_SNAPSHOTS=/opt/lbg-new-mmo-clean/MMOCoreORB/bin/ia_bridge/player_snapshots.json
export LBG_GATEWAY_TRACK_PLAYERS="${LBG_GATEWAY_TRACK_PLAYERS:-Teome,Lia,Nix}"
export LBG_GATEWAY_CATALOG="${REMOTE_DIR}/core3_npc_catalog.json"
export LBG_GATEWAY_LOCATIONS="${REMOTE_DIR}/locations"
export LBG_GATEWAY_ZONE_BRIDGE_LIVE=1
export LBG_GATEWAY_ZONE_BRIDGE_JSON=/opt/lbg-new-mmo-clean/MMOCoreORB/bin/ia_bridge/zone_bridge_live.json
export LBG_GATEWAY_TICK_LIVE_S=0.05
export LBG_GATEWAY_HTTP_AUTH=1
export LBG_GATEWAY_HTTP_HOST=0.0.0.0
export LBG_GATEWAY_HTTP_PORT=8765
export LBG_GATEWAY_PUBLIC_HOST="${PUBLIC_HOST}"
export LBG_GATEWAY_PUBLIC_WS_URL="ws://${PUBLIC_HOST}:50000"
export LBG_ZONE_SESSION_POLICY="${LBG_ZONE_SESSION_POLICY:-kick_other}"
# Sur Prime (246) : MariaDB locale ; sinon host distant
export CORE3_DB_HOST="${CORE3_DB_HOST:-127.0.0.1}"
export CORE3_DB_PORT="${CORE3_DB_PORT:-3306}"
export CORE3_DB_USER="${CORE3_DB_USER:-swgemu}"
export CORE3_DB_NAME="${CORE3_DB_NAME:-swgemu}"
export CORE3_DB_PASS="${CORE3_DB_PASS:-123456}"
export CORE3_DB_SECRET="${CORE3_DB_SECRET:-swgemus3cr37!}"
export LBG_GATEWAY_AUTH_MOCK="${LBG_GATEWAY_AUTH_MOCK:-1}"
export LBG_GATEWAY_GALAXY_ID="${LBG_GATEWAY_GALAXY_ID:-3}"
if [ -f /etc/lbg-ia-mmo.env ]; then
  set -a
  # shellcheck disable=SC1091
  . /etc/lbg-ia-mmo.env
  set +a
fi
export CORE3_DB_HOST="${CORE3_DB_HOST:-127.0.0.1}"
export CORE3_DB_PASS="${CORE3_DB_PASS:-123456}"
export CORE3_DB_SECRET="${CORE3_DB_SECRET:-swgemus3cr37!}"
export LBG_GATEWAY_AUTH_MOCK="${LBG_GATEWAY_AUTH_MOCK:-1}"
export LBG_GATEWAY_PUBLIC_HOST="${PUBLIC_HOST}"
export LBG_GATEWAY_PUBLIC_WS_URL="ws://${PUBLIC_HOST}:50000"
export LBG_GATEWAY_IA_BACKEND_URL="${LBG_GATEWAY_IA_BACKEND_URL:-${MMMORPG_IA_BACKEND_URL:-}}"
export LBG_GATEWAY_IA_BACKEND_TOKEN="${LBG_GATEWAY_IA_BACKEND_TOKEN:-${MMMORPG_IA_BACKEND_TOKEN:-}}"
python3 -m pip install --user -q websockets httpx pymysql 2>/dev/null || pip3 install --user -q websockets httpx pymysql
pkill -f "${REMOTE_DIR}/main.py" 2>/dev/null || true
sudo systemctl stop lbg-gateway 2>/dev/null || true
sleep 0.5
nohup python3 "${REMOTE_DIR}/main.py" >> /tmp/lbg-gateway.log 2>&1 &
sleep 1
ok_ws=0
ok_http=0
if ss -tlnp 2>/dev/null | grep -q ':50000 '; then
  echo "[gateway] OK ws://0.0.0.0:50000 (public ws://${PUBLIC_HOST}:50000)"
  ok_ws=1
else
  echo "[gateway] WARN port 50000 not listening"
fi
if ss -tlnp 2>/dev/null | grep -q ':8765 '; then
  echo "[gateway] OK http://0.0.0.0:8765 (M11 auth → http://${PUBLIC_HOST}:8765)"
  ok_http=1
else
  echo "[gateway] WARN port 8765 not listening"
fi
if [[ "${ok_ws}" != "1" || "${ok_http}" != "1" ]]; then
  tail -40 /tmp/lbg-gateway.log 2>/dev/null || true
fi
EOF
