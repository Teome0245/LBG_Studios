#!/usr/bin/env bash
# Déploie hub_runtime (spike ADR 0026) sur Prime `.246` — // Core3, port 8787.
#
# Usage:
#   bash packages/cortex/infra/scripts/deploy_hub_runtime_246.sh
#   bash packages/cortex/infra/scripts/deploy_hub_runtime_246.sh --smoke
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORTEX_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
UNIT_SRC="${CORTEX_ROOT}/infra/systemd/lbg-hub-runtime.service"
HUB_SRC="${CORTEX_ROOT}/tools/hub_runtime"
TOOLS_INIT="${CORTEX_ROOT}/tools/__init__.py"
BUILDINGS_SRC="${CORTEX_ROOT}/../prime-client/assets/maps/lost_heaven_buildings.json"
PROPS_SRC="${CORTEX_ROOT}/../prime-client/assets/maps/lost_heaven_props.json"
QUESTS_SRC="${CORTEX_ROOT}/content/world/quests_lbg_templates.json"

HOST="${LBG_PRIME_HOST:-192.168.0.246}"
REMOTE="lbg@${HOST}"
REMOTE_DIR="${LBG_HUB_RUNTIME_DIR:-/opt/lbg-hub-runtime}"
PORT="${LBG_HUB_RUNTIME_PORT:-8797}"
SMOKE=0
[[ "${1:-}" == "--smoke" ]] && SMOKE=1

[[ -f "${HUB_SRC}/server.py" ]] || { echo "ERR: missing ${HUB_SRC}/server.py" >&2; exit 1; }
[[ -f "${UNIT_SRC}" ]] || { echo "ERR: missing ${UNIT_SRC}" >&2; exit 1; }
[[ -f "${TOOLS_INIT}" ]] || { echo "ERR: missing ${TOOLS_INIT}" >&2; exit 1; }
[[ -f "${BUILDINGS_SRC}" ]] || { echo "ERR: missing ${BUILDINGS_SRC}" >&2; exit 1; }
[[ -f "${PROPS_SRC}" ]] || { echo "ERR: missing ${PROPS_SRC}" >&2; exit 1; }
[[ -f "${QUESTS_SRC}" ]] || { echo "ERR: missing ${QUESTS_SRC}" >&2; exit 1; }

echo "==> Sync hub_runtime → ${REMOTE}:${REMOTE_DIR}"
ssh -o BatchMode=yes -o ConnectTimeout=12 "${REMOTE}" \
  "sudo mkdir -p '${REMOTE_DIR}/tools/hub_runtime' '${REMOTE_DIR}/data' && sudo chown -R lbg:lbg '${REMOTE_DIR}'"

rsync -az --delete \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  "${HUB_SRC}/" "${REMOTE}:${REMOTE_DIR}/tools/hub_runtime/"
rsync -az "${TOOLS_INIT}" "${REMOTE}:${REMOTE_DIR}/tools/__init__.py"
rsync -az "${BUILDINGS_SRC}" "${REMOTE}:${REMOTE_DIR}/data/lost_heaven_buildings.json"
rsync -az "${PROPS_SRC}" "${REMOTE}:${REMOTE_DIR}/data/lost_heaven_props.json"
rsync -az "${QUESTS_SRC}" "${REMOTE}:${REMOTE_DIR}/data/quests_lbg_templates.json"
scp -o BatchMode=yes -o ConnectTimeout=12 "${UNIT_SRC}" "${REMOTE}:/tmp/lbg-hub-runtime.service"

echo "==> venv + systemd on ${HOST}"
ssh -o BatchMode=yes -o ConnectTimeout=12 "${REMOTE}" bash -s <<REMOTE
set -euo pipefail
cd '${REMOTE_DIR}'
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q 'fastapi>=0.110' 'uvicorn[standard]>=0.27' 'websockets>=12' 'httpx>=0.22'
# agent_catalog déjà sur la VM (sidecar)
test -d /opt/LBG_IA_MMO/agents/src/lbg_agents || {
  echo "WARN: /opt/LBG_IA_MMO/agents/src manquant — catalog HTTP renverra 501" >&2
}
sudo install -m 644 /tmp/lbg-hub-runtime.service /etc/systemd/system/lbg-hub-runtime.service
sudo systemctl daemon-reload
sudo systemctl enable --now lbg-hub-runtime.service
sudo systemctl restart lbg-hub-runtime.service
sleep 3.5
systemctl is-active lbg-hub-runtime
curl -sf "http://127.0.0.1:${PORT}/healthz" | head -c 200
echo
REMOTE

if [[ "$SMOKE" -eq 1 ]]; then
  echo "==> Smoke LAN http://${HOST}:${PORT}"
  curl -sf "http://${HOST}:${PORT}/healthz" | head -c 280
  echo
  curl -sf "http://${HOST}:${PORT}/catalog?type=skills" | head -c 120
  echo
  curl -sf "http://${HOST}:${PORT}/tick-matrix" | head -c 120
  echo
  python3 - <<PY
import json, urllib.request
base = "http://${HOST}:${PORT}"
d = json.load(urllib.request.urlopen(base + "/healthz", timeout=5))
assert d.get("ok") and int(d.get("collision_blocks", 0)) > 0, d
print("OK collision_blocks", d.get("collision_blocks"))
assert int(d.get("bots", 0)) >= 4, d
assert int(d.get("npcs", 0)) >= 12, d
print("OK fleet bots", d.get("bots"), "npcs", d.get("npcs"))
bots = json.load(urllib.request.urlopen(base + "/v1/bots", timeout=5))
assert bots.get("ok") and bots.get("count") >= 4, bots
names = {b.get("name") for b in bots.get("bots") or []}
assert {"Nix", "Lia", "Mira", "Kael"} <= names, names
print("OK /v1/bots", sorted(names))
# move_to Lia
req_m = urllib.request.Request(
    base + "/v1/bots/move_to",
    data=json.dumps({"player": "Lia", "x": 4809.0, "z": -932.0}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
mv = json.load(urllib.request.urlopen(req_m, timeout=5))
assert mv.get("ok"), mv
print("OK move_to Lia", mv.get("target"))
# dialogue PNJ
req_d = urllib.request.Request(
    base + "/v1/dialogue/invoke",
    data=json.dumps({"text":"Bonjour.","context":{"world_npc_id":"npc:core3_daan_oth","npc_name":"Daan Oth"}}).encode(),
    headers={"Content-Type":"application/json"},
    method="POST",
)
dlg = json.load(urllib.request.urlopen(req_d, timeout=25))
assert dlg.get("ok") and dlg.get("reply"), dlg
assert len(dlg.get("suggested_moves") or []) >= 1, dlg
print("OK dialogue Daan", dlg["reply"][:50], "moves", len(dlg["suggested_moves"]))
inv = json.load(urllib.request.urlopen(base + "/v1/inventory?player=Voyageur", timeout=5))
assert inv.get("ok") and inv.get("inventory"), inv
print("OK inventory", len(inv["inventory"]), "persisted", inv.get("persisted"))
board = json.load(urllib.request.urlopen(
    base + "/v1/quests/board?giver=npc:core3_daan_oth&player=Voyageur", timeout=5))
assert board.get("ok") and len(board.get("quests") or []) >= 3, board
print("OK quests board", len(board["quests"]))
# auth guest + accept persist
req = urllib.request.Request(
    base + "/v1/auth/guest",
    data=json.dumps({"player_name": "SmokePersist"}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
guest = json.load(urllib.request.urlopen(req, timeout=5))
assert guest.get("ok") and guest.get("session_token"), guest
print("OK auth guest", guest["characters"][0]["name"])
req2 = urllib.request.Request(
    base + "/v1/quests/accept",
    data=json.dumps({"player": "SmokePersist", "quest_id": "lh_survey_dunes", "giver_id": "npc:core3_daan_oth"}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
acc = json.load(urllib.request.urlopen(req2, timeout=5))
assert acc.get("ok"), acc
print("OK quests accept", acc.get("quest_id"))
st = json.load(urllib.request.urlopen(base + "/v1/quests/status?player=SmokePersist", timeout=5))
assert any(a.get("id") == "lh_survey_dunes" for a in st.get("active") or []), st
print("OK status active", len(st["active"]))
# bots SpaceMolt : play_mode + éventuellement quest_id après quelques ticks serveur
import time
time.sleep(2.5)
bots2 = json.load(urllib.request.urlopen(base + "/v1/bots", timeout=5))
modes = {(b.get("name"), b.get("play_mode"), b.get("quest_id") or "") for b in bots2.get("bots") or []}
print("OK bots play", sorted(modes))
assert any(m[1] in ("quest", "explore", "hub", "social", "") for m in modes), modes
# au moins un bot en quest ou explore (proba haute sur 4 bots)
playish = [m for m in modes if m[1] in ("quest", "explore", "hub", "social")]
assert len(playish) >= 1, modes
# cycle ECONOMY bot Nix (force accept côté API — même board que joueurs IA)
req_nx = urllib.request.Request(
    base + "/v1/quests/accept",
    data=json.dumps({"player": "Nix", "quest_id": "lh_delivery_starport", "giver_id": "npc:core3_daan_oth"}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
acc_nx = json.load(urllib.request.urlopen(req_nx, timeout=5))
assert acc_nx.get("ok"), acc_nx
st_nx = json.load(urllib.request.urlopen(base + "/v1/quests/status?player=Nix", timeout=5))
assert any(a.get("id") == "lh_delivery_starport" for a in st_nx.get("active") or []), st_nx
print("OK Nix quest active", [a.get("id") for a in st_nx.get("active") or []])
PY
  echo "==> Smoke chat WS humain+IA (remote venv)"
  scp -o BatchMode=yes -o ConnectTimeout=12 \
    "${CORTEX_ROOT}/infra/scripts/_hub_chat_smoke.py" \
    "${REMOTE}:/tmp/hub_chat_smoke.py"
  if ssh -o BatchMode=yes -o ConnectTimeout=12 "${REMOTE}" \
    "LBG_HUB_RUNTIME_PORT=${PORT} /opt/lbg-hub-runtime/.venv/bin/python /tmp/hub_chat_smoke.py"; then
    :
  else
    echo "WARN chat WS smoke failed"
  fi
  # Core3 toujours là ?
  if curl -sf -o /dev/null -w "%{http_code}" --connect-timeout 2 "http://${HOST}:8791/healthz" | grep -qE '200|404|401'; then
    echo "OK sidecar :8791 encore joignable (Core3 //)"
  else
    echo "NOTE: sidecar :8791 non testé / down (hors scope hub_runtime)"
  fi
fi

echo "OK hub_runtime on ${HOST}:${PORT}  ws://${HOST}:${PORT}/ws"
echo "Client: packages/prime-client/config/hub_runtime.json → ws_url ws://${HOST}:${PORT}/ws"
