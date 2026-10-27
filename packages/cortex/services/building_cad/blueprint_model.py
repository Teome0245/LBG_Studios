"""blueprint_model.py — Spécification et modèle de données CAD pour les bâtiments Lost Heaven / MMO.

Inspiré de l'approche CADCraft / CAO paramétrique :
Représentation vectorielle exacte (empreinte au sol, cloisons, portes, pièces praticables, étages).
Prévu pour être généré par un agent Studio (LLM/MCP) ou par règles procédurales,
puis compilé directement en collisions AABB/navmesh pour prime-hub et rendu prime-client.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class DoorSpec:
    """Ouverture de porte sur un mur."""
    offset_m: float  # Distance depuis le début du mur (start) jusqu'au bord gauche de la porte
    width_m: float = 1.2
    height_m: float = 2.4
    is_exterior: bool = False
    leads_to_room: str | None = None


@dataclass
class WindowSpec:
    """Ouverture de fenêtre sur un mur extérieur."""
    offset_m: float  # Distance depuis start
    width_m: float = 1.4
    height_m: float = 1.5
    sill_height_m: float = 1.0  # Hauteur d'allège


@dataclass
class WallSegment:
    """Mur ou cloison 2D projeté verticalement."""
    id: str
    start: tuple[float, float]  # (x, z) relatif au centre du bâtiment
    end: tuple[float, float]    # (x, z) relatif au centre du bâtiment
    thickness_m: float = 0.25
    height_m: float = 3.2
    is_exterior: bool = False
    material: str = "concrete_scrap"
    doors: list[DoorSpec] = field(default_factory=list)
    windows: list[WindowSpec] = field(default_factory=list)

    @property
    def length_m(self) -> float:
        import math
        dx = self.end[0] - self.start[0]
        dz = self.end[1] - self.start[1]
        return math.sqrt(dx * dx + dz * dz)


@dataclass
class RoomSpec:
    """Pièce fermée praticable par les joueurs et PNJ."""
    id: str
    name: str
    purpose: str  # ex: "main_hall", "backroom", "vault", "office", "dorm"
    floor_index: int
    polygon: list[tuple[float, float]]  # Points (x, z) relatifs
    area_m2: float = 0.0
    ambient_audio: str | None = None


@dataclass
class FloorSpec:
    """Étage complet d'un bâtiment."""
    floor_index: int
    elevation_m: float  # y relatif
    height_m: float     # hauteur sous plafond
    rooms: list[RoomSpec] = field(default_factory=list)
    walls: list[WallSegment] = field(default_factory=list)


@dataclass
class BuildingBlueprint:
    """Blueprint architectural complet d'un bâtiment Lost Heaven."""
    id: str
    kind: str  # "cantina", "warehouse", "bank", "clinic", "hab", "dock"
    label: str
    world_pos: tuple[float, float, float]  # (X, Y, Z) dans l'univers MMO
    footprint_width_m: float
    footprint_depth_m: float
    floors: list[FloorSpec] = field(default_factory=list)
    roof_style: str = "flat"  # "flat", "industrial_pitched", "scrap_dome"
    rotation_deg: float = 0.0
    schema_version: int = 1
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_height_m(self) -> float:
        return sum(f.height_m for f in self.floors)

    def to_dict(self) -> dict[str, Any]:
        """Convertit l'instance en dictionnaire compatible JSON."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BuildingBlueprint:
        """Désérialise un dictionnaire JSON en BuildingBlueprint."""
        floors_data = data.get("floors", [])
        parsed_floors = []
        for f in floors_data:
            rooms = [RoomSpec(**r) for r in f.get("rooms", [])]
            walls = []
            for w in f.get("walls", []):
                doors = [DoorSpec(**d) for d in w.get("doors", [])]
                windows = [WindowSpec(**win) for win in w.get("windows", [])]
                w_copy = dict(w)
                w_copy["doors"] = doors
                w_copy["windows"] = windows
                w_copy["start"] = tuple(w_copy["start"])
                w_copy["end"] = tuple(w_copy["end"])
                walls.append(WallSegment(**w_copy))
            parsed_floors.append(
                FloorSpec(
                    floor_index=f["floor_index"],
                    elevation_m=f["elevation_m"],
                    height_m=f["height_m"],
                    rooms=rooms,
                    walls=walls,
                )
            )

        return cls(
            id=data["id"],
            kind=data["kind"],
            label=data["label"],
            world_pos=tuple(data["world_pos"]),
            footprint_width_m=float(data["footprint_width_m"]),
            footprint_depth_m=float(data["footprint_depth_m"]),
            floors=parsed_floors,
            roof_style=data.get("roof_style", "flat"),
            rotation_deg=float(data.get("rotation_deg", 0.0)),
            schema_version=int(data.get("schema_version", 1)),
            description=data.get("description", ""),
            metadata=data.get("metadata", {}),
        )

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def to_legacy_hub_entry(self) -> dict[str, Any]:
        """Génère l'entrée compatible avec lost_heaven_buildings.json et HubCollision."""
        main_door = None
        # Recherche la première porte extérieure du RDC (floor 0)
        if self.floors:
            for w in self.floors[0].walls:
                if w.is_exterior and w.doors:
                    d = w.doors[0]
                    # Déterminer la face selon les coordonnées du mur
                    sx, sz = w.start
                    ex, ez = w.end
                    hw = self.footprint_width_m * 0.5
                    hd = self.footprint_depth_m * 0.5
                    face = "south"
                    if abs(sz - (-hd)) < 0.5 and abs(ez - (-hd)) < 0.5:
                        face = "north"
                    elif abs(sz - hd) < 0.5 and abs(ez - hd) < 0.5:
                        face = "south"
                    elif abs(sx - (-hw)) < 0.5 and abs(ex - (-hw)) < 0.5:
                        face = "west"
                    elif abs(sx - hw) < 0.5 and abs(ex - hw) < 0.5:
                        face = "east"

                    main_door = {
                        "face": face,
                        "width_m": round(d.width_m, 1),
                        "depth_m": round(max(3.0, d.width_m * 1.5), 1),
                        "apron_m": 2.5,
                    }
                    break

        return {
            "id": self.id,
            "kind": self.kind,
            "label": self.label,
            "x": round(self.world_pos[0], 1),
            "z": round(self.world_pos[2], 1),
            "size_m": round(max(self.footprint_width_m, self.footprint_depth_m), 1),
            "essential": self.metadata.get("essential", False),
            "floors_count": len(self.floors),
            "cad_blueprint_ref": f"blueprints/{self.id.replace(':', '_')}.json",
            "door": main_door,
        }
