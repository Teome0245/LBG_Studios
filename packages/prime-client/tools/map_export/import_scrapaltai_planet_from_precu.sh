#!/usr/bin/env bash
# Importe la carte planète Tatooine (bounds Core3 ±6500) depuis World Editor / PreCU 245 → prime-client.
set -euo pipefail

PRIME="$(cd "$(dirname "$0")/../.." && pwd)"
MAPS="${PRIME}/assets/maps"
HOST="${PRECU_HOST:-192.168.0.245}"
USER="${PRECU_USER:-lbg}"
REMOTE="${REMOTE_CORE3:-/home/lbg/swgemu}"

REPO_WE="${REPO_WE:-/home/sdesh/projects/LBG_IA_MMORPG/LBG_IA_MMO/tools/world_editor}"
SRC_SVG=""
SRC_CFG=""

if [[ -f "${REPO_WE}/assets/tatooine_map.svg" ]]; then
  SRC_SVG="${REPO_WE}/assets/tatooine_map.svg"
  SRC_CFG="${REPO_WE}/scrapaltai_map_config.json"
fi

if [[ -z "${SRC_SVG}" ]] && ssh -o ConnectTimeout=8 -o BatchMode=yes "${USER}@${HOST}" "echo ok" 2>/dev/null; then
  TMP="$(mktemp -d)"
  scp -q "${USER}@${HOST}:${REMOTE}/LBG_IA_MMO/tools/world_editor/assets/tatooine_map.svg" "${TMP}/" 2>/dev/null || true
  scp -q "${USER}@${HOST}:${REMOTE}/LBG_IA_MMO/tools/world_editor/scrapaltai_map_config.json" "${TMP}/" 2>/dev/null || true
  if [[ -f "${TMP}/tatooine_map.svg" ]]; then
    SRC_SVG="${TMP}/tatooine_map.svg"
    SRC_CFG="${TMP}/scrapaltai_map_config.json"
  fi
fi

if [[ -z "${SRC_SVG}" ]]; then
  echo "Aucune source carte (repo local ${REPO_WE} ou SSH ${HOST})." >&2
  exit 1
fi

cp -f "${SRC_SVG}" "${MAPS}/scrapaltai_planet_precu.svg"
# Ne pas écraser scrapaltai.svg joueur si déjà présent (version Godot-safe sans feGaussianBlur).
if [[ ! -f "${MAPS}/scrapaltai.svg" ]]; then
  cp -f "${SRC_SVG}" "${MAPS}/scrapaltai.svg"
fi

python3 - <<PY
import json
from pathlib import Path

maps = Path("${MAPS}")
cfg_path = maps / "scrapaltai_map_config.json"
cfg = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.is_file() else {}

bounds = {"min_x": -6500.0, "max_x": 6500.0, "min_z": -6500.0, "max_z": 6500.0}
we_cfg = Path("${SRC_CFG}")
if we_cfg.is_file():
    we = json.loads(we_cfg.read_text(encoding="utf-8"))
    b = we.get("bounds") or {}
    if b:
        bounds = {
            "min_x": float(b.get("minX", -6500)),
            "max_x": float(b.get("maxX", 6500)),
            "min_z": float(b.get("minY", -6500)),
            "max_z": float(b.get("maxY", 6500)),
        }

half = max(abs(bounds["min_x"]), abs(bounds["max_x"]), abs(bounds["min_z"]), abs(bounds["max_z"]))

cfg.update({
    "schema_version": 3,
    "half_size": half,
    "bounds": {
        "minX": bounds["min_x"],
        "maxX": bounds["max_x"],
        "minY": bounds["min_z"],
        "maxY": bounds["max_z"],
    },
    "world_texture": "res://assets/maps/scrapaltai.svg",
    "planet_map_texture": "res://assets/maps/scrapaltai_shard_legacy.png",
    "texture_core3_bounds": bounds,
    "world_texture_source": "precu_world_editor",
    "imported_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
})
cfg.pop("texture", None)
cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("OK", cfg_path, "half_size=", half, "world_texture=scrapaltai.svg")
PY

echo "→ Ouvre Godot une fois pour réimporter scrapaltai.svg (filtres SVG sans feGaussianBlur si échec)."
