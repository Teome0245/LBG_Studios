"""lost_heaven_presets.py — Bibliothèque de presets de bâtiments Lost Heaven.

Fournit des modèles prêts pour le level design et le spawn de bâtiments
respectant l'échelle spatiale, les hitboxes et l'esthétique dieselpunk/scrap de Lost Heaven.
"""

from __future__ import annotations

from .blueprint_model import BuildingBlueprint
from .procedural_architect import build_cantina_blueprint, build_warehouse_blueprint


def get_default_lost_heaven_blueprints() -> list[BuildingBlueprint]:
    """Retourne l'ensemble des blueprints standards générés pour la ville de Lost Heaven."""
    return [
        build_cantina_blueprint(
            building_id="poi:lost_heaven_cantina",
            world_pos=(5028.3, 0.0, -784.1),
            width_m=32.0,
            depth_m=24.0,
            label="La Perle de Scrapaltai",
        ),
        build_warehouse_blueprint(
            building_id="poi:lost_heaven_warehouse_dock",
            world_pos=(4850.0, 0.0, -920.0),
            width_m=36.0,
            depth_m=28.0,
            label="Dépôt et Ferraille Nord",
        ),
    ]


def get_blueprint_by_kind(kind: str, building_id: str, world_pos: tuple, width_m: float, depth_m: float, label: str) -> BuildingBlueprint:
    """Instancie un blueprint paramétré selon le type demandé."""
    if kind == "warehouse":
        return build_warehouse_blueprint(building_id=building_id, world_pos=world_pos, width_m=width_m, depth_m=depth_m, label=label)
    # Défaut / cantina
    return build_cantina_blueprint(building_id=building_id, world_pos=world_pos, width_m=width_m, depth_m=depth_m, label=label)
