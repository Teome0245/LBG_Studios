#!/usr/bin/env bash
# Wire C10 catalog + C11 TickGate sur sidecar Prime :8791.
# Usage: bash infra/scripts/wire_sidecar_c10_catalog_246.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
HOST="${LBG_PRIME_HOST:-192.168.0.246}"
SRC="$ROOT/agents/src/lbg_agents/agent_catalog.py"
BOT="$ROOT/agents/src/lbg_agents/quest_hub_bot_autonomy.py"
POI="$ROOT/../prime-client/assets/maps/scrapaltai_pois.json"
PATCH="$ROOT/infra/scripts/patch_sidecar_c11_tick_gate.py"

[[ -f "$SRC" ]] || { echo "missing $SRC" >&2; exit 1; }
[[ -f "$POI" ]] || { echo "missing $POI" >&2; exit 1; }
[[ -f "$BOT" ]] || { echo "missing $BOT" >&2; exit 1; }
[[ -f "$PATCH" ]] || { echo "missing $PATCH" >&2; exit 1; }

scp -o BatchMode=yes -o ConnectTimeout=10 "$SRC" "lbg@${HOST}:/tmp/agent_catalog.py"
scp -o BatchMode=yes -o ConnectTimeout=10 "$BOT" "lbg@${HOST}:/tmp/quest_hub_bot_autonomy.py"
scp -o BatchMode=yes -o ConnectTimeout=10 "$POI" "lbg@${HOST}:/tmp/scrapaltai_pois.json"
scp -o BatchMode=yes -o ConnectTimeout=10 "$PATCH" "lbg@${HOST}:/tmp/patch_sidecar_c11_tick_gate.py"

ssh -o BatchMode=yes -o ConnectTimeout=10 "lbg@${HOST}" bash -s <<'REMOTE'
set -euo pipefail
sudo install -m 644 -o lbg -g lbg /tmp/agent_catalog.py /opt/LBG_IA_MMO/agents/src/lbg_agents/agent_catalog.py
sudo install -m 644 -o lbg -g lbg /tmp/quest_hub_bot_autonomy.py /opt/LBG_IA_MMO/agents/src/lbg_agents/quest_hub_bot_autonomy.py
sudo mkdir -p /opt/LBG_IA_MMO/content/maps
sudo install -m 644 -o lbg -g lbg /tmp/scrapaltai_pois.json /opt/LBG_IA_MMO/content/maps/scrapaltai_pois.json
sudo mkdir -p /etc/systemd/system/lbg-core3-ia-sidecar.service.d
sudo tee /etc/systemd/system/lbg-core3-ia-sidecar.service.d/c10-catalog.conf >/dev/null <<EOF
[Service]
Environment=LBG_M10_CATALOG_PATH=/opt/LBG_IA_MMO/content/core3/m10_skills_catalog.json
Environment=LBG_POI_CATALOG_PATH=/opt/LBG_IA_MMO/content/maps/scrapaltai_pois.json
Environment=LBG_TICK_GATE=1
Environment=LBG_TICK_COOLDOWN_S=8
Environment=LBG_TICK_QUEUE_MAX=1
EOF
PY=/opt/LBG_IA_MMO/tools/core3_ia_sidecar/core3_ia_sidecar.py
if ! grep -q 'http_get_dispatch' "$PY"; then
  echo "ERROR: $PY n'a pas le bloc http_get_dispatch — rejouer le patch sidecar C10." >&2
  exit 2
fi
sudo python3 /tmp/patch_sidecar_c11_tick_gate.py "$PY"
sudo systemctl daemon-reload
sudo systemctl restart lbg-core3-ia-sidecar
sleep 2
systemctl is-active lbg-core3-ia-sidecar
curl -sf "http://127.0.0.1:8791/catalog?type=skills" | head -c 120
echo
# Smoke TickGate : double accept → 429
code1=$(curl -s -o /tmp/t1.json -w '%{http_code}' -X POST "http://127.0.0.1:8791/v1/quests/accept" \
  -H 'Content-Type: application/json' \
  -d '{"player":"TickSmoke","quest_id":"lh_aide_generale","giver_id":"npc:core3_daan_oth"}')
code2=$(curl -s -o /tmp/t2.json -w '%{http_code}' -X POST "http://127.0.0.1:8791/v1/quests/accept" \
  -H 'Content-Type: application/json' \
  -d '{"player":"TickSmoke","quest_id":"lh_survey_dunes","giver_id":"npc:core3_daan_oth"}')
echo "tick_smoke accept1=$code1 accept2=$code2"
python3 - <<'PY'
import json
from pathlib import Path
p = Path("/tmp/t2.json")
if p.is_file():
    data = json.loads(p.read_text() or "{}")
    print("tick_smoke body2", data.get("error"), data.get("reason"))
PY
REMOTE

echo "OK wire C10+C11 TickGate on ${HOST}:8791"
