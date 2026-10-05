#!/usr/bin/env bash
# Export PNJ Prime 246 → lost_heaven_retail_layout.json (npcs serveur)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRIME="$(cd "${SCRIPT_DIR}/../.." && pwd)"
OVERLAY="${PRIME}/assets/maps/retail/scrapaltai/lost_heaven_retail_layout.json"
HTTP_BASE="${LBG_GATEWAY_HTTP:-http://192.168.0.246:8765}"
ANCHOR_X="${LH_ANCHOR_X:-4749}"
ANCHOR_Z="${LH_ANCHOR_Z:--737}"
RADIUS="${LH_NPC_RADIUS:-800}"
HOST="${CORE_HOST:-192.168.0.246}"
USER="${CORE_USER:-lbg}"
REMOTE_SNAP="${REMOTE_SNAP:-/opt/lbg-new-mmo-clean/MMOCoreORB/bin/ia_bridge/npc_snapshots.json}"
CACHE="${PRIME}/tools/retail/cache"
LOCAL="${CACHE}/npc_snapshots_${HOST}.json"

mkdir -p "${CACHE}"

merge_via_python() {
  local snap="$1"
  python3 << PY
import sys
from pathlib import Path
sys.path.insert(0, "${HOME}/projects/LBG_IA_MMORPG/LBG_IA_MMO/services/lbg_gateway")
sys.path.insert(0, "/home/sdesh/projects/LBG_IA_MMORPG/LBG_IA_MMO/services/lbg_gateway")
try:
    from npc_snapshot_export import merge_into_layout_file
except ImportError:
    from services.lbg_gateway.npc_snapshot_export import merge_into_layout_file

n, total = merge_into_layout_file(
    Path("${OVERLAY}"),
    float("${ANCHOR_X}"),
    float("${ANCHOR_Z}"),
    float("${RADIUS}"),
    snap_path=Path("${snap}") if Path("${snap}").is_file() else None,
)
print(f"PNJ serveur zone LH : {n} exportés, {total} npcs total → ${OVERLAY}")
PY
}

if curl -sfS --max-time 8 "${HTTP_BASE}/v1/world/npcs_near?anchor_x=${ANCHOR_X}&anchor_z=${ANCHOR_Z}&radius_m=${RADIUS}" -o "${CACHE}/npcs_near.json" 2>/dev/null; then
  python3 << PY
import json
from pathlib import Path
p = Path("${CACHE}/npcs_near.json")
data = json.loads(p.read_text(encoding="utf-8"))
fresh = data.get("npcs") or []
overlay_path = Path("${OVERLAY}")
overlay = json.loads(overlay_path.read_text(encoding="utf-8")) if overlay_path.is_file() else {
    "schema_version": 1, "zone": "tatooine", "city": "lost_heaven", "buildings": [], "markers": []
}
existing = overlay.get("npcs") if isinstance(overlay.get("npcs"), list) else []
by_id = {str(n.get("id")): n for n in existing if isinstance(n, dict) and str(n.get("source", "")) != "server_npc_snapshots"}
for n in fresh:
    if isinstance(n, dict):
        by_id[str(n["id"])] = n
merged = list(by_id.values())
overlay["npcs"] = merged
counts = overlay.get("counts") if isinstance(overlay.get("counts"), dict) else {}
counts["npcs"] = len(merged)
counts["npcs_server"] = len(fresh)
overlay["counts"] = counts
overlay["server_export"] = {"via": "http", "url": "${HTTP_BASE}/v1/world/npcs_near"}
overlay_path.parent.mkdir(parents=True, exist_ok=True)
overlay_path.write_text(json.dumps(overlay, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"PNJ via HTTP : {len(fresh)} exportés, {len(merged)} total")
PY
elif scp -q "${USER}@${HOST}:${REMOTE_SNAP}" "${LOCAL}" 2>/dev/null; then
  merge_via_python "${LOCAL}"
else
  echo "Échec : API ${HTTP_BASE}/v1/world/npcs_near ou scp ${REMOTE_SNAP}" >&2
  exit 1
fi

if [[ -d /mnt/j/swgemu/clients/prime-client ]]; then
  rsync -a "${OVERLAY}" /mnt/j/swgemu/clients/prime-client/assets/maps/retail/scrapaltai/
fi
