#!/usr/bin/env bash
# G4 cutover — Godot = autorité publique ; Python hub_runtime = lab peel :8797
#
# Ports après cutover :
#   Godot WS   :8787
#   Godot HTTP :8789  (proxy → Python :8797)
#   Python lab :8797
#
# Usage:
#   bash packages/cortex/infra/scripts/cutover_prime_hub_g4_246.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORTEX_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
STUDIOS_ROOT="$(cd "${CORTEX_ROOT}/../.." && pwd)"
HOST="${LBG_PRIME_HOST:-192.168.0.246}"
REMOTE="lbg@${HOST}"
GODOT_DIR="${LBG_PRIME_HUB_DIR:-/opt/lbg-prime-hub}"
PY_PORT=8797
WS_PORT=8787
HTTP_PORT=8789
HUB="${STUDIOS_ROOT}/packages/prime-hub"
BUILDINGS_SRC="${STUDIOS_ROOT}/packages/prime-client/assets/maps/lost_heaven_buildings.json"

[[ -x "${HUB}/tools/godot" ]] || { echo "ERR: run packages/prime-hub/scripts/fetch_godot.sh" >&2; exit 1; }
[[ -f "${BUILDINGS_SRC}" ]] || { echo "ERR: missing buildings json" >&2; exit 1; }

GODOT_REAL="$(readlink -f "${HUB}/tools/godot")"
GODOT_NAME="$(basename "$GODOT_REAL")"

echo "==> G4 cutover on ${HOST}"

echo "==> 1/4 hub_runtime → lab :${PY_PORT}"
ssh -o BatchMode=yes -o ConnectTimeout=12 "${REMOTE}" bash -s <<REMOTE
set -euo pipefail
UNIT=/etc/systemd/system/lbg-hub-runtime.service
sudo cp -a "\$UNIT" "\${UNIT}.bak-g4-\$(date +%Y%m%d%H%M%S)"
# Port lab + WS public annoncé = Godot
sudo sed -i 's/LBG_HUB_RUNTIME_PORT=8787/LBG_HUB_RUNTIME_PORT=${PY_PORT}/' "\$UNIT"
sudo sed -i 's|LBG_HUB_WS_PUBLIC=ws://192.168.0.246:8787/ws|LBG_HUB_WS_PUBLIC=ws://192.168.0.246:${WS_PORT}/ws|' "\$UNIT"
# Si déjà 8797, sed no-op OK
if ! grep -q "LBG_HUB_RUNTIME_PORT=${PY_PORT}" "\$UNIT"; then
  echo "Environment=LBG_HUB_RUNTIME_PORT=${PY_PORT}" | sudo tee -a "\$UNIT" >/dev/null
fi
sudo systemctl daemon-reload
sudo systemctl restart lbg-hub-runtime.service
systemctl is-active lbg-hub-runtime
ok=0
for i in 1 2 3 4 5 6 7 8 9 10; do
  if curl -sf "http://127.0.0.1:${PY_PORT}/healthz" | head -c 200; then
    echo
    ok=1
    break
  fi
  sleep 1
done
[[ "\$ok" -eq 1 ]] || { echo "ERR: hub_runtime :${PY_PORT} pas prêt" >&2; exit 1; }
REMOTE

echo "==> 2/4 sync prime-hub + bind WS :${WS_PORT}"
ssh -o BatchMode=yes "${REMOTE}" \
  "sudo mkdir -p '${GODOT_DIR}/tools' '${GODOT_DIR}/data' && sudo chown -R lbg:lbg '${GODOT_DIR}'"
rsync -az --delete \
  --exclude '.godot/' --exclude 'tools/' --exclude 'data/' \
  "${HUB}/" "${REMOTE}:${GODOT_DIR}/"
ssh -o BatchMode=yes "${REMOTE}" "mkdir -p '${GODOT_DIR}/data' '${GODOT_DIR}/tools'"
rsync -az "${BUILDINGS_SRC}" "${REMOTE}:${GODOT_DIR}/data/lost_heaven_buildings.json"
rsync -az "$GODOT_REAL" "${REMOTE}:${GODOT_DIR}/tools/${GODOT_NAME}"
ssh -o BatchMode=yes "${REMOTE}" \
  "ln -sfn '${GODOT_DIR}/tools/${GODOT_NAME}' '${GODOT_DIR}/tools/godot' && chmod +x '${GODOT_DIR}/tools/godot' '${GODOT_DIR}/tools/${GODOT_NAME}'"

ssh -o BatchMode=yes "${REMOTE}" bash -s <<REMOTE
set -euo pipefail
sudo tee /etc/systemd/system/lbg-prime-hub.service >/dev/null <<EOF
[Unit]
Description=LBG Prime Hub (Godot headless) — autorité publique G4
After=network.target lbg-hub-runtime.service
Wants=lbg-hub-runtime.service

[Service]
Type=simple
User=lbg
WorkingDirectory=${GODOT_DIR}
Environment=LBG_PRIME_HUB_WS_PORT=${WS_PORT}
Environment=LBG_PRIME_HUB_HTTP_PORT=${HTTP_PORT}
Environment=LBG_HUB_BUILDINGS_JSON=${GODOT_DIR}/data/lost_heaven_buildings.json
Environment=LBG_HUB_AUTH_UPSTREAM=http://127.0.0.1:${PY_PORT}
Environment=LBG_HUB_HTTP_UPSTREAM=http://127.0.0.1:${PY_PORT}
ExecStart=${GODOT_DIR}/tools/godot --headless --path ${GODOT_DIR} res://scenes/server_main.tscn
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now lbg-prime-hub.service
sudo systemctl restart lbg-prime-hub.service
sleep 3
systemctl is-active lbg-prime-hub
curl -sf "http://127.0.0.1:${HTTP_PORT}/healthz"
echo
REMOTE

echo "==> 3/4 smoke"
curl -sf "http://${HOST}:${HTTP_PORT}/healthz" | head -c 400; echo
curl -sf "http://${HOST}:${HTTP_PORT}/v1/inventory?player=Voyageur" | head -c 160; echo
curl -sf "http://${HOST}:${PY_PORT}/healthz" | head -c 120; echo

echo "==> 4/4 listen"
ssh -o BatchMode=yes "${REMOTE}" "ss -ltn | grep -E ':8787|:8788|:8789|:8797' || true"

echo
echo "OK G4 — WS ws://${HOST}:${WS_PORT}/ws · HTTP http://${HOST}:${HTTP_PORT} · Python lab :${PY_PORT}"
