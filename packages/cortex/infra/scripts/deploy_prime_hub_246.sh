#!/usr/bin/env bash
# Déploie packages/prime-hub sur .246 (G4 : WS 8787 / HTTP 8789 — Python lab 8797).
#
# Usage:
#   bash packages/cortex/infra/scripts/deploy_prime_hub_246.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORTEX_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
STUDIOS_ROOT="$(cd "${CORTEX_ROOT}/../.." && pwd)"
HUB="${STUDIOS_ROOT}/packages/prime-hub"
BUILDINGS_SRC="${STUDIOS_ROOT}/packages/prime-client/assets/maps/lost_heaven_buildings.json"
UNIT_LOCAL="${CORTEX_ROOT}/infra/systemd/lbg-prime-hub.service"

HOST="${LBG_PRIME_HOST:-192.168.0.246}"
REMOTE="lbg@${HOST}"
REMOTE_DIR="${LBG_PRIME_HUB_DIR:-/opt/lbg-prime-hub}"

[[ -f "${HUB}/project.godot" ]] || { echo "ERR: missing ${HUB}" >&2; exit 1; }
[[ -f "${BUILDINGS_SRC}" ]] || { echo "ERR: missing ${BUILDINGS_SRC}" >&2; exit 1; }
[[ -x "${HUB}/tools/godot" ]] || { echo "ERR: run packages/prime-hub/scripts/fetch_godot.sh first" >&2; exit 1; }

mkdir -p "$(dirname "$UNIT_LOCAL")"
cat >"$UNIT_LOCAL" <<EOF
[Unit]
Description=LBG Prime Hub (Godot headless) lbg-ws/2
After=network.target

[Service]
Type=simple
User=lbg
WorkingDirectory=${REMOTE_DIR}
Environment=LBG_PRIME_HUB_WS_PORT=8787
Environment=LBG_PRIME_HUB_HTTP_PORT=8789
Environment=LBG_HUB_BUILDINGS_JSON=${REMOTE_DIR}/data/lost_heaven_buildings.json
Environment=LBG_HUB_AUTH_UPSTREAM=http://127.0.0.1:8797
Environment=LBG_HUB_HTTP_UPSTREAM=http://127.0.0.1:8797
ExecStart=${REMOTE_DIR}/tools/godot --headless --path ${REMOTE_DIR} res://scenes/server_main.tscn
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

GODOT_REAL="$(readlink -f "${HUB}/tools/godot")"
GODOT_NAME="$(basename "$GODOT_REAL")"

echo "==> Sync prime-hub → ${REMOTE}:${REMOTE_DIR}"
ssh -o BatchMode=yes -o ConnectTimeout=12 "${REMOTE}" \
  "sudo mkdir -p '${REMOTE_DIR}/tools' '${REMOTE_DIR}/data' && sudo chown -R lbg:lbg '${REMOTE_DIR}'"

rsync -az --delete \
  --exclude '.godot/' \
  --exclude 'tools/' \
  --exclude 'data/' \
  "${HUB}/" "${REMOTE}:${REMOTE_DIR}/"

ssh -o BatchMode=yes "${REMOTE}" "mkdir -p '${REMOTE_DIR}/data' '${REMOTE_DIR}/tools'"
rsync -az "${BUILDINGS_SRC}" "${REMOTE}:${REMOTE_DIR}/data/lost_heaven_buildings.json"
rsync -az "$GODOT_REAL" "${REMOTE}:${REMOTE_DIR}/tools/${GODOT_NAME}"
ssh -o BatchMode=yes "${REMOTE}" \
  "ln -sfn '${REMOTE_DIR}/tools/${GODOT_NAME}' '${REMOTE_DIR}/tools/godot' && chmod +x '${REMOTE_DIR}/tools/godot' '${REMOTE_DIR}/tools/${GODOT_NAME}'"

scp -o BatchMode=yes "$UNIT_LOCAL" "${REMOTE}:/tmp/lbg-prime-hub.service"

echo "==> systemd on ${HOST}"
ssh -o BatchMode=yes -o ConnectTimeout=12 "${REMOTE}" bash -s <<REMOTE
set -euo pipefail
sudo install -m 644 /tmp/lbg-prime-hub.service /etc/systemd/system/lbg-prime-hub.service
sudo systemctl daemon-reload
sudo systemctl enable --now lbg-prime-hub.service
sudo systemctl restart lbg-prime-hub.service
sleep 3
systemctl is-active lbg-prime-hub
curl -sf http://127.0.0.1:8789/healthz
echo
REMOTE

echo "==> Smoke LAN"
curl -sf "http://${HOST}:8789/healthz" | head -c 400
echo
echo "OK — WS :8787 · HTTP :8789 · Python lab :8797"
