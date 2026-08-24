#!/usr/bin/env bash
# Recentre les joueurs IA (Lia/Nix/Mira/Kael) sur Lost Heaven — one-shot via sidecar :8791
# Prefer switch_zone (sort de l'interieur ME). Lia est une joueuse libre (pas de confinement cantina).
# Usage :
#   bash infra/scripts/recenter_ia_bots_lh_once.sh
#   bash infra/scripts/recenter_ia_bots_lh_once.sh --bots=mira,nix
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SIDECAR="${LBG_CORE3_SIDECAR_URL:-http://192.168.0.246:8791}"
BOTS="${BOTS:-mira,nix,lia}"

for arg in "$@"; do
  case "$arg" in
    --bots=*) BOTS="${arg#--bots=}" ;;
    --sidecar=*) SIDECAR="${arg#--sidecar=}" ;;
  esac
done

export LBG_CORE3_SIDECAR_URL="$SIDECAR"
export BOTS
export PYTHONPATH="${ROOT}/agents/src:${PYTHONPATH:-}"

cd "$ROOT"
python3 - <<'PY'
import json, os
import urllib.request

from lbg_agents.core3_places import bot_spawn
from lbg_agents.core3_players import get_ai_player

base = os.environ["LBG_CORE3_SIDECAR_URL"].rstrip("/")
bots = [b.strip().lower() for b in os.environ.get("BOTS", "mira,nix").split(",") if b.strip()]
results = {}
for pid in bots:
    try:
        player = get_ai_player(pid)
    except Exception as e:
        results[pid] = {"ok": False, "error": str(e)}
        continue
    x, y, z = bot_spawn(pid)
    # pending : x est | y nord | z hauteur (Lua switch_zone mappe vers Core3 x, height, north)
    lines = [
        f"switch_zone|{player.firstname}|tatooine|{x:g}|{y:g}|{z:g}|lost_heaven",
        f"move_to|{player.firstname}|tatooine|{x:g}|{y:g}|{z:g}|hub_walk_home",
    ]
    outs = []
    for line in lines:
        parts = line.split("|")
        body = {
            "action": parts[0],
            "player": player.firstname,
            "zone": "tatooine",
            "x": float(parts[3]),
            "y": float(parts[4]),
            "z": float(parts[5]),
            "message": parts[6],
            "raw_line": line,
        }
        req = urllib.request.Request(
            f"{base}/v1/enqueue",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            outs.append(json.loads(resp.read().decode()))
    results[pid] = {"ok": True, "target": {"x": x, "y": y, "z": z}, "enqueue": outs}
print(json.dumps(results, ensure_ascii=False, indent=2))
PY
