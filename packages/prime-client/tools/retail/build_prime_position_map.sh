#!/usr/bin/env bash
# Régénère la carte de positionnement Prime Lost Heaven depuis retail / gabarit ME.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
bash tools/retail/extract_retail_scrapaltai_layout.sh 2>/dev/null || true
python3 tools/retail/apply_mos_eisley_gabarit_lost_heaven.py
bash tools/retail/export_server_npcs_lost_heaven.sh || echo "WARN: export PNJ serveur (0 si aucun spawn LH)"
echo "OK → assets/maps/retail/scrapaltai/lost_heaven_retail_layout.json"
echo "Godot : world_render.position_map dans scrapaltai_map_config.json"
