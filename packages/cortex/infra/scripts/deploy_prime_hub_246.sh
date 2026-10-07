#!/usr/bin/env bash
# Déploie packages/prime-hub sur .246 (G5 : HTTP+WS unifiés :8787, peel natif).
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
QUESTS_SRC="${HUB}/data/quests_lbg_templates.json"
[[ -f "${QUESTS_SRC}" ]] || QUESTS_SRC="${CORTEX_ROOT}/content/world/quests_lbg_templates.json"

HOST="${LBG_PRIME_HOST:-192.168.0.246}"
REMOTE="lbg@${HOST}"
REMOTE_DIR="${LBG_PRIME_HUB_DIR:-/opt/lbg-prime-hub}"

[[ -f "${HUB}/project.godot" ]] || { echo "ERR: missing ${HUB}" >&2; exit 1; }
[[ -f "${BUILDINGS_SRC}" ]] || { echo "ERR: missing ${BUILDINGS_SRC}" >&2; exit 1; }
[[ -x "${HUB}/tools/godot" ]] || { echo "ERR: run packages/prime-hub/scripts/fetch_godot.sh first" >&2; exit 1; }

mkdir -p "$(dirname "$UNIT_LOCAL")"
cat >"$UNIT_LOCAL" <<EOF
[Unit]
Description=LBG Prime Hub (Godot headless) lbg-ws/2 G5 native peel
After=network.target

[Service]
Type=simple
User=lbg
WorkingDirectory=${REMOTE_DIR}
Environment=LBG_PRIME_HUB_WS_PORT=8787
Environment=LBG_PRIME_HUB_HTTP_PORT=8787
Environment=LBG_PRIME_HUB_STATE_DIR=${REMOTE_DIR}/data
Environment=LBG_HUB_STATE_DIR=${REMOTE_DIR}/data
Environment=LBG_HUB_WS_PUBLIC=ws://${HOST}:8787/ws
Environment=LBG_HUB_BUILDINGS_JSON=${REMOTE_DIR}/data/lost_heaven_buildings.json
Environment=LBG_HUB_QUESTS_JSON=${REMOTE_DIR}/data/quests_lbg_templates.json
Environment=LBG_HUB_LLM_BASE_URL=http://192.168.0.110:11434
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
  --exclude 'data/accounts.json' \
  --exclude 'data/players_state.json' \
  --exclude 'data/player_positions.json' \
  --exclude 'data/hunt_yard_session.pkl' \
  "${HUB}/" "${REMOTE}:${REMOTE_DIR}/"

ssh -o BatchMode=yes "${REMOTE}" "mkdir -p '${REMOTE_DIR}/data' '${REMOTE_DIR}/tools'"
rsync -az "${BUILDINGS_SRC}" "${REMOTE}:${REMOTE_DIR}/data/lost_heaven_buildings.json"
[[ -f "${QUESTS_SRC}" ]] && rsync -az "${QUESTS_SRC}" "${REMOTE}:${REMOTE_DIR}/data/quests_lbg_templates.json"

# Migrer état peel Python → Godot si absent côté prime-hub
ssh -o BatchMode=yes "${REMOTE}" bash -s <<'MIGRATE'
set -euo pipefail
D=/opt/lbg-prime-hub/data
P=/opt/lbg-hub-runtime/data
for f in accounts.json players_state.json; do
  if [[ ! -f "$D/$f" && -f "$P/$f" ]]; then
    cp -a "$P/$f" "$D/$f"
    echo "migrated $f from hub-runtime"
  fi
done
MIGRATE

rsync -az "$GODOT_REAL" "${REMOTE}:${REMOTE_DIR}/tools/${GODOT_NAME}"
# Cour de chasse P5a — moteur Python (tools/ exclu du rsync principal pour garder le binaire Godot)
[[ -f "${HUB}/tools/hunt_yard.py" ]] && rsync -az "${HUB}/tools/hunt_yard.py" "${REMOTE}:${REMOTE_DIR}/tools/hunt_yard.py"
ssh -o BatchMode=yes "${REMOTE}" \
  "ln -sfn '${REMOTE_DIR}/tools/${GODOT_NAME}' '${REMOTE_DIR}/tools/godot' && chmod +x '${REMOTE_DIR}/tools/godot' '${REMOTE_DIR}/tools/${GODOT_NAME}'"

scp -o BatchMode=yes "$UNIT_LOCAL" "${REMOTE}:/tmp/lbg-prime-hub.service"

echo "==> systemd on ${HOST} (stop Python peel if present)"
ssh -o BatchMode=yes -o ConnectTimeout=12 "${REMOTE}" bash -s <<REMOTE
set -euo pipefail
# Libérer :8787 — Godot unifié prend tout
sudo systemctl stop lbg-hub-runtime.service 2>/dev/null || true
sudo systemctl disable lbg-hub-runtime.service 2>/dev/null || true
# Ancien HTTP :8789 plus nécessaire
sudo systemctl stop lbg-prime-hub.service 2>/dev/null || true
sudo install -m 644 /tmp/lbg-prime-hub.service /etc/systemd/system/lbg-prime-hub.service
sudo systemctl daemon-reload
sudo systemctl enable --now lbg-prime-hub.service
sudo systemctl restart lbg-prime-hub.service
sleep 4
systemctl is-active lbg-prime-hub
curl -sf http://127.0.0.1:8787/healthz
echo
REMOTE

echo "==> Smoke LAN"
curl -sf "http://${HOST}:8787/healthz" | head -c 500
echo
curl -sf "http://${HOST}:8787/v1/inventory?player=Voyageur" | head -c 200
echo
curl -sf -X POST "http://${HOST}:8787/v1/auth/guest" -H 'Content-Type: application/json' -d '{"player_name":"Voyageur"}' | head -c 250
echo
echo "OK — G5 unified :8787 peel native · Python hub-runtime OFF"
