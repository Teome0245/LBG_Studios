"""test_building_cad.py — Tests unitaires de la modélisation CAO et génération de bâtiments."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from services.building_cad import (
    BuildingBlueprint,
    DoorSpec,
    FloorSpec,
    RoomSpec,
    WallSegment,
    build_cantina_blueprint,
    build_warehouse_blueprint,
    export_blueprints_to_client,
    get_default_lost_heaven_blueprints,
)


def test_blueprint_serialization_roundtrip():
    wall = WallSegment(
        id="test_wall",
        start=(0.0, 0.0),
        end=(10.0, 0.0),
        thickness_m=0.3,
        height_m=3.0,
        is_exterior=True,
        doors=[DoorSpec(offset_m=4.0, width_m=1.2, height_m=2.1, is_exterior=True)],
    )
    room = RoomSpec(
        id="room_1",
        name="Test Room",
        purpose="lounge",
        floor_index=0,
        polygon=[(0.0, 0.0), (10.0, 0.0), (10.0, 5.0), (0.0, 5.0)],
        area_m2=50.0,
    )
    floor = FloorSpec(floor_index=0, elevation_m=0.0, height_m=3.0, rooms=[room], walls=[wall])
    bp = BuildingBlueprint(
        id="poi:test_building",
        kind="cantina",
        label="Test Building",
        world_pos=(4800.0, 0.0, -750.0),
        footprint_width_m=10.0,
        footprint_depth_m=5.0,
        floors=[floor],
    )

    raw_json = bp.to_json()
    data = json.loads(raw_json)
    assert data["id"] == "poi:test_building"
    assert len(data["floors"]) == 1
    assert len(data["floors"][0]["walls"]) == 1

    restored = BuildingBlueprint.from_dict(data)
    assert restored.id == bp.id
    assert restored.footprint_width_m == 10.0
    assert len(restored.floors[0].walls[0].doors) == 1
    assert restored.floors[0].walls[0].doors[0].width_m == 1.2


def test_cantina_procedural_generation():
    cantina = build_cantina_blueprint(
        building_id="poi:lost_heaven_cantina",
        world_pos=(5028.3, 0.0, -784.1),
        width_m=32.0,
        depth_m=24.0,
    )
    assert cantina.id == "poi:lost_heaven_cantina"
    assert cantina.kind == "cantina"
    assert len(cantina.floors) == 1

    floor = cantina.floors[0]
    # Doit contenir au moins 3 pièces (salle principale, réserve, bureau)
    room_ids = [r.id for r in floor.rooms]
    assert "room_main_hall" in room_ids
    assert "room_storage" in room_ids
    assert "room_boss_office" in room_ids

    # Vérification des murs extérieurs et intérieurs
    exterior_walls = [w for w in floor.walls if w.is_exterior]
    interior_walls = [w for w in floor.walls if not w.is_exterior]
    assert len(exterior_walls) == 4
    assert len(interior_walls) >= 2

    # Doit avoir au moins une porte extérieure
    ext_doors = [d for w in exterior_walls for d in w.doors if d.is_exterior]
    assert len(ext_doors) >= 1

    # Format de transition AABB
    entry = cantina.to_legacy_hub_entry()
    assert entry["id"] == "poi:lost_heaven_cantina"
    assert entry["x"] == 5028.3
    assert entry["door"] is not None
    assert entry["door"]["face"] == "south"


def test_warehouse_procedural_generation():
    warehouse = build_warehouse_blueprint(
        building_id="poi:lost_heaven_warehouse_dock",
        world_pos=(4850.0, 0.0, -920.0),
        width_m=40.0,
        depth_m=30.0,
    )
    assert warehouse.kind == "warehouse"
    assert len(warehouse.floors[0].rooms) == 2
    assert warehouse.total_height_m == 5.5


def test_export_pipeline():
    with TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        blueprints = get_default_lost_heaven_blueprints()
        written = export_blueprints_to_client(blueprints, client_maps_dir=tmp_path, sync_buildings_json=False)

        assert len(written) == len(blueprints)
        for p in written:
            assert p.exists()
            content = json.loads(p.read_text(encoding="utf-8"))
            assert "schema_version" in content
            assert "floors" in content
