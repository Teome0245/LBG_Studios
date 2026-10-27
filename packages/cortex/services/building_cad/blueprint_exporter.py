"""blueprint_exporter.py — Pipeline d'export et synchronisation des blueprints avec les maps client/serveur.

Exporte les fichiers `.json` détaillés dans `packages/prime-client/assets/maps/blueprints/`
et génère les entrées simplifiées AABB compatibles pour `lost_heaven_buildings.json`.
"""

from __future__ import annotations

import json
from pathlib import Path

from .blueprint_model import BuildingBlueprint


def export_blueprints_to_client(
    blueprints: list[BuildingBlueprint],
    client_maps_dir: Path | None = None,
    sync_buildings_json: bool = False,
) -> list[Path]:
    """Écrit les blueprints sous forme de fichiers JSON dans l'arborescence client Godot."""
    if client_maps_dir is None:
        # Trouver la racine du monorepo
        cur = Path(__file__).resolve()
        # Remonter jusqu'à LBG_Studios
        repo_root = cur
        while repo_root.name != "LBG_Studios" and repo_root.parent != repo_root:
            repo_root = repo_root.parent
        client_maps_dir = repo_root / "packages" / "prime-client" / "assets" / "maps"

    blueprints_dir = client_maps_dir / "blueprints"
    blueprints_dir.mkdir(parents=True, exist_ok=True)

    written_paths: list[Path] = []
    for bp in blueprints:
        safe_name = bp.id.replace(":", "_").replace("/", "_") + ".json"
        out_path = blueprints_dir / safe_name
        out_path.write_text(bp.to_json(indent=2), encoding="utf-8")
        written_paths.append(out_path)

    if sync_buildings_json:
        buildings_path = client_maps_dir / "lost_heaven_buildings.json"
        if buildings_path.exists():
            try:
                data = json.loads(buildings_path.read_text(encoding="utf-8"))
                existing_buildings = data.get("buildings", [])
                existing_by_id = {b["id"]: b for b in existing_buildings if "id" in b}

                for bp in blueprints:
                    entry = bp.to_legacy_hub_entry()
                    if bp.id in existing_by_id:
                        # Mise à jour partielle (préserve lore_ref et autres flags spécifiques)
                        existing_by_id[bp.id].update({
                            "cad_blueprint_ref": entry["cad_blueprint_ref"],
                            "floors_count": entry["floors_count"],
                        })
                        if entry.get("door"):
                            existing_by_id[bp.id]["door"] = entry["door"]
                    else:
                        existing_buildings.append(entry)

                data["buildings"] = existing_buildings
                buildings_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            except Exception as e:
                print(f"[blueprint_exporter] Warning synchro lost_heaven_buildings.json: {e}")

    return written_paths
