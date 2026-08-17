#!/usr/bin/env python3
"""Migration phase 1 : posts PNJ catalogue ME → Lost Heaven (outdoor cell=0).

Conserve les roster_id (compat ia_bridge_screenplay.lua). Met a jour service_post,
binding.post/home et leisure_patrol outdoor autour du hub LH.

Usage :
  python3 migrate_npc_catalog_me_to_lh.py
  python3 migrate_npc_catalog_me_to_lh.py --catalog /path/to/core3_npc_catalog.json --dry-run
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

DEFAULT_CATALOG = (
    Path(__file__).resolve().parents[5]
    / "LBG_IA_MMORPG"
    / "LBG_IA_MMO"
    / "content"
    / "core3"
    / "core3_npc_catalog.json"
)

# Core3 outdoor : x, y (plan), z (hauteur), heading, cell
LH_POSTS: dict[str, dict[str, Any]] = {
    "roster:mos_eisley_cantina_barman": {
        "x": 4939,
        "y": -802,
        "z": 32,
        "heading": 180,
        "cell": 0,
        "location_id": "lost_heaven_cantina_bar",
        "description": "La Perle de Scrapaltai — comptoir (outdoor phase 1, cell TBD)",
    },
    "roster:mos_entertainer_trainer": {
        "x": 4939,
        "y": -802,
        "z": 32,
        "heading": 180,
        "cell": 0,
        "location_id": "lost_heaven_cantina_bar",
        "description": "Instructeur entertainer — La Perle LH (outdoor phase 1)",
    },
    "roster:mos_trainer_brawler": {
        "x": 4939,
        "y": -672,
        "z": 32,
        "heading": 180,
        "cell": 0,
        "location_id": "loc:lost_heaven_training_hall",
        "description": "Hall entrainement LH — triplon brawler (outdoor phase 1)",
    },
    "roster:mos_trainer_marksman": {
        "x": 4955,
        "y": -685,
        "z": 32,
        "heading": 200,
        "cell": 0,
        "location_id": "loc:lost_heaven_training_hall",
        "description": "Hall entrainement LH — triplon marksman (outdoor phase 1)",
    },
    "roster:mos_trainer_scout": {
        "x": 4923,
        "y": -685,
        "z": 32,
        "heading": 160,
        "cell": 0,
        "location_id": "loc:lost_heaven_training_hall",
        "description": "Hall entrainement LH — triplon scout (outdoor phase 1)",
    },
    "roster:mos_trainer_medic": {
        "x": 4939,
        "y": -658,
        "z": 32,
        "heading": 0,
        "cell": 0,
        "location_id": "loc:lost_heaven_training_hall",
        "description": "Hall entrainement LH — triplon medic (outdoor phase 1)",
    },
    "roster:mos_trainer_politician": {
        "x": 4955,
        "y": -658,
        "z": 32,
        "heading": 20,
        "cell": 0,
        "location_id": "loc:lost_heaven_training_hall",
        "description": "Hall entrainement LH — triplon politician (outdoor phase 1)",
    },
    "roster:mos_trainer_artisan": {
        "x": 5069,
        "y": -802,
        "z": 32,
        "heading": 270,
        "cell": 0,
        "location_id": "loc:lost_heaven_training_hall",
        "description": "Atelier artisan LH (outdoor phase 1)",
    },
    "roster:mos_eisley_quest_giver": {
        "x": 4809,
        "y": -737,
        "z": 32,
        "heading": 90,
        "cell": 0,
        "location_id": "loc:lost_heaven_hub",
        "description": "Donneur de quete — plaza Lost Heaven (migration ME)",
    },
}

LH_LEISURE_PATROL = [
    {"x": 4749, "y": -737, "z": 32},
    {"x": 4809, "y": -802, "z": 32},
    {"x": 4939, "y": -802, "z": 32},
    {"x": 4809, "y": -932, "z": 32},
]


def _post_dict(cfg: dict[str, Any]) -> dict[str, Any]:
    return {k: cfg[k] for k in ("x", "y", "z", "heading", "cell") if k in cfg}


def _apply_post(target: dict[str, Any], post: dict[str, Any]) -> None:
    for key, val in post.items():
        target[key] = val


def _migrate_binding(binding: dict[str, Any], post: dict[str, Any]) -> None:
    if not isinstance(binding, dict):
        return
    for key in ("post", "home"):
        if key in binding and isinstance(binding[key], dict):
            _apply_post(binding[key], post)
    if "cantina" in binding:
        binding.pop("cantina", None)
    if "leisure_patrol" in binding:
        binding["leisure_patrol"] = copy.deepcopy(LH_LEISURE_PATROL)


def migrate_catalog(doc: dict[str, Any]) -> list[str]:
    changes: list[str] = []
    rosters = doc.get("rosters")
    if not isinstance(rosters, list):
        return changes
    for roster in rosters:
        if not isinstance(roster, dict):
            continue
        rid = str(roster.get("roster_id") or "")
        cfg = LH_POSTS.get(rid)
        if not cfg:
            continue
        post = _post_dict(cfg)
        if roster.get("service_post"):
            _apply_post(roster["service_post"], post)
        if cfg.get("description"):
            roster["description"] = cfg["description"]
        if cfg.get("location_id"):
            roster["location_id"] = cfg["location_id"]
        for slot in roster.get("slots") or []:
            if not isinstance(slot, dict):
                continue
            binding = slot.get("binding")
            if isinstance(binding, dict):
                _migrate_binding(binding, post)
        changes.append(rid)
    meta = doc.setdefault("migration_meta", {})
    if isinstance(meta, dict):
        meta["me_to_lh_outdoor"] = {
            "phase": 1,
            "applied": True,
            "rosters": changes,
            "hub_anchor": {"x": 4749, "y": -737, "z": 32},
        }
    return changes


def main() -> None:
    ap = argparse.ArgumentParser(description="Migrate NPC catalog ME → LH outdoor")
    ap.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    path: Path = args.catalog
    if not path.is_file():
        raise SystemExit(f"Catalogue introuvable : {path}")
    doc = json.loads(path.read_text(encoding="utf-8"))
    changed = migrate_catalog(doc)
    print(f"Rosters migres ({len(changed)}):")
    for rid in changed:
        print(f"  - {rid}")
    if args.dry_run:
        print("(dry-run — fichier non ecrit)")
        return
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK → {path}")


if __name__ == "__main__":
    main()
