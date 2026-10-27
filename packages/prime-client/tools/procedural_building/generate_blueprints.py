#!/usr/bin/env python3
"""generate_blueprints.py — CLI de génération des blueprints de bâtiments Lost Heaven.

Usage:
  python3 packages/prime-client/tools/procedural_building/generate_blueprints.py [--sync-map]
"""

import argparse
import sys
from pathlib import Path

# Ajouter packages/cortex au PYTHONPATH
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR
while REPO_ROOT.name != "LBG_Studios" and REPO_ROOT.parent != REPO_ROOT:
    REPO_ROOT = REPO_ROOT.parent

sys.path.insert(0, str(REPO_ROOT / "packages" / "cortex"))

from services.building_cad import (
    export_blueprints_to_client,
    get_default_lost_heaven_blueprints,
)


def main():
    parser = argparse.ArgumentParser(description="Génère les blueprints CAO pour Lost Heaven")
    parser.add_argument("--sync-map", action="store_true", help="Met à jour lost_heaven_buildings.json")
    args = parser.parse_args()

    print("[*] Génération des blueprints CAO Lost Heaven...")
    blueprints = get_default_lost_heaven_blueprints()
    for bp in blueprints:
        print(f"  - {bp.id} ({bp.label}) : {bp.footprint_width_m}m x {bp.footprint_depth_m}m, {len(bp.floors)} étage(s)")

    maps_dir = REPO_ROOT / "packages" / "prime-client" / "assets" / "maps"
    written = export_blueprints_to_client(blueprints, client_maps_dir=maps_dir, sync_buildings_json=args.sync_map)
    print(f"[+] {len(written)} blueprints exportés dans {maps_dir / 'blueprints'}")
    if args.sync_map:
        print(f"[+] lost_heaven_buildings.json synchronisé avec les références CAO.")


if __name__ == "__main__":
    main()
