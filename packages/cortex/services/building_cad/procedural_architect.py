"""procedural_architect.py — Générateur architectural paramétrique de bâtiments.

Génère des plans 2D/3D praticables avec cloisons, portes d'accès, pièces et ouvertures.
Inspiré des règles de tracé CAO (orthogonalité, dégagement de circulation, seuils).
"""

from __future__ import annotations

from .blueprint_model import (
    BuildingBlueprint,
    DoorSpec,
    FloorSpec,
    RoomSpec,
    WallSegment,
    WindowSpec,
)


def create_perimeter_walls(
    width_m: float,
    depth_m: float,
    height_m: float,
    wall_thickness_m: float = 0.3,
    main_door_face: str = "south",
    main_door_width_m: float = 2.0,
    main_door_height_m: float = 2.4,
    window_interval_m: float = 4.0,
) -> list[WallSegment]:
    """Génère les 4 murs porteurs périphériques avec porte d'entrée et fenêtres régulières."""
    hw = width_m * 0.5
    hd = depth_m * 0.5

    # 4 coins dans le sens horaire : Nord-Ouest, Nord-Est, Sud-Est, Sud-Ouest
    # Repère Godot : -Z = Nord, +Z = Sud, -X = Ouest, +X = Est
    corners = {
        "NW": (-hw, -hd),
        "NE": (hw, -hd),
        "SE": (hw, hd),
        "SW": (-hw, hd),
    }

    wall_defs = [
        # (id, start, end, face, length)
        ("wall_north", corners["NW"], corners["NE"], "north", width_m),
        ("wall_east",  corners["NE"], corners["SE"], "east",  depth_m),
        ("wall_south", corners["SE"], corners["SW"], "south", width_m),
        ("wall_west",  corners["SW"], corners["NW"], "west",  depth_m),
    ]

    walls: list[WallSegment] = []

    for wid, start, end, face, length in wall_defs:
        doors: list[DoorSpec] = []
        windows: list[WindowSpec] = []

        if face == main_door_face:
            # Porte centrée sur cette face
            door_offset = (length - main_door_width_m) * 0.5
            doors.append(
                DoorSpec(
                    offset_m=round(door_offset, 2),
                    width_m=main_door_width_m,
                    height_m=main_door_height_m,
                    is_exterior=True,
                )
            )
            # Fenêtres de chaque côté de la porte si la place le permet
            if door_offset > 3.0:
                windows.append(WindowSpec(offset_m=1.2, width_m=1.4, height_m=1.5, sill_height_m=1.0))
                windows.append(WindowSpec(offset_m=round(length - 2.6, 2), width_m=1.4, height_m=1.5, sill_height_m=1.0))
        else:
            # Mettre des fenêtres régulières
            win_count = max(1, int(length // window_interval_m))
            spacing = length / (win_count + 1)
            for i in range(1, win_count + 1):
                win_offset = i * spacing - 0.7
                windows.append(
                    WindowSpec(
                        offset_m=round(win_offset, 2),
                        width_m=1.4,
                        height_m=1.5,
                        sill_height_m=1.0,
                    )
                )

        walls.append(
            WallSegment(
                id=wid,
                start=start,
                end=end,
                thickness_m=wall_thickness_m,
                height_m=height_m,
                is_exterior=True,
                material="scrap_metal_corrugated",
                doors=doors,
                windows=windows,
            )
        )

    return walls


def build_cantina_blueprint(
    building_id: str = "poi:lost_heaven_cantina",
    world_pos: tuple[float, float, float] = (5028.3, 0.0, -784.1),
    width_m: float = 32.0,
    depth_m: float = 24.0,
    label: str = "La Perle de Scrapaltai",
) -> BuildingBlueprint:
    """Génère une cantina vivante type Lost Heaven :

    - Grande salle publique (bar, piste, tables de pazaak)
    - Arrière-boutique / réserve sécurisée
    - Bureau privé du propriétaire avec sortie dérobée
    """
    height_m = 3.8
    hw = width_m * 0.5
    hd = depth_m * 0.5

    # 1. Murs extérieurs avec entrée au Sud (face à la place)
    ext_walls = create_perimeter_walls(
        width_m=width_m,
        depth_m=depth_m,
        height_m=height_m,
        main_door_face="south",
        main_door_width_m=2.8,
        main_door_height_m=2.6,
    )

    # 2. Cloisons intérieures :
    # Séparation arrière (Nord) à z = -hd + 8.0 m
    # Divisée en 2 pièces : Réserve (Ouest) et Bureau du boss (Est)
    split_z = -hd + 7.5
    int_walls: list[WallSegment] = []

    # Mur longitudinal séparant la salle principale de l'arrière-boutique
    int_walls.append(
        WallSegment(
            id="wall_int_backstage",
            start=(-hw, split_z),
            end=(hw, split_z),
            thickness_m=0.25,
            height_m=height_m,
            is_exterior=False,
            material="metal_partition",
            doors=[
                # Porte d'accès côté bar (Ouest)
                DoorSpec(offset_m=4.0, width_m=1.4, height_m=2.2, is_exterior=False, leads_to_room="storage"),
                # Porte d'accès côté bureau privé (Est)
                DoorSpec(offset_m=width_m - 5.5, width_m=1.2, height_m=2.2, is_exterior=False, leads_to_room="boss_office"),
            ],
        )
    )

    # Mur transversal séparant Réserve et Bureau du boss (à x = 4.0)
    int_walls.append(
        WallSegment(
            id="wall_int_office_divider",
            start=(4.0, -hd),
            end=(4.0, split_z),
            thickness_m=0.25,
            height_m=height_m,
            is_exterior=False,
            material="reinforced_steel",
            doors=[],
        )
    )

    # 3. Pièces déclaratives (polygones au sol)
    rooms = [
        RoomSpec(
            id="room_main_hall",
            name="Salle principale",
            purpose="cantina_hall",
            floor_index=0,
            polygon=[(-hw, split_z), (hw, split_z), (hw, hd), (-hw, hd)],
            area_m2=width_m * (depth_m - 7.5),
            ambient_audio="amb_cantina_chatter",
        ),
        RoomSpec(
            id="room_storage",
            name="Réserve de contrebande",
            purpose="storage",
            floor_index=0,
            polygon=[(-hw, -hd), (4.0, -hd), (4.0, split_z), (-hw, split_z)],
            area_m2=(hw + 4.0) * 7.5,
            ambient_audio="amb_hum_generators",
        ),
        RoomSpec(
            id="room_boss_office",
            name="Bureau feutré du gérant",
            purpose="office",
            floor_index=0,
            polygon=[(4.0, -hd), (hw, -hd), (hw, split_z), (4.0, split_z)],
            area_m2=(hw - 4.0) * 7.5,
            ambient_audio="amb_low_fan",
        ),
    ]

    floor = FloorSpec(
        floor_index=0,
        elevation_m=0.0,
        height_m=height_m,
        rooms=rooms,
        walls=ext_walls + int_walls,
    )

    return BuildingBlueprint(
        id=building_id,
        kind="cantina",
        label=label,
        world_pos=world_pos,
        footprint_width_m=width_m,
        footprint_depth_m=depth_m,
        floors=[floor],
        roof_style="flat",
        description="Cantina emblématique de Lost Heaven avec comptoir de ferrailleur et alcôves de jeu.",
        metadata={
            "essential": False,
            "lore_ref": "docs/world/BIBLE_MMO.md#V13",
            "capacity_players": 40,
        },
    )


def build_warehouse_blueprint(
    building_id: str = "poi:lost_heaven_warehouse_dock",
    world_pos: tuple[float, float, float] = (4850.0, 0.0, -920.0),
    width_m: float = 40.0,
    depth_m: float = 30.0,
    label: str = "Entrepôt Docks & Ferraille",
) -> BuildingBlueprint:
    """Génère un grand entrepôt industriel avec double porte hangar et atelier."""
    height_m = 5.5
    hw = width_m * 0.5
    hd = depth_m * 0.5

    # 1. Murs extérieurs avec grand portail double
    ext_walls = create_perimeter_walls(
        width_m=width_m,
        depth_m=depth_m,
        height_m=height_m,
        main_door_face="south",
        main_door_width_m=4.5,
        main_door_height_m=4.0,
        window_interval_m=6.0,
    )

    # 2. Cloison pour atelier sécurisé / bureau du contremaître au fond à l'Est
    workshop_w = 12.0
    workshop_d = 10.0
    int_walls: list[WallSegment] = [
        # Mur séparant l'atelier (façade Sud de l'atelier)
        WallSegment(
            id="wall_int_workshop_front",
            start=(hw - workshop_w, -hd + workshop_d),
            end=(hw, -hd + workshop_d),
            thickness_m=0.3,
            height_m=height_m,
            doors=[DoorSpec(offset_m=2.0, width_m=1.6, height_m=2.4, is_exterior=False, leads_to_room="workshop")],
        ),
        # Mur séparant l'atelier (façade Ouest de l'atelier)
        WallSegment(
            id="wall_int_workshop_side",
            start=(hw - workshop_w, -hd),
            end=(hw - workshop_w, -hd + workshop_d),
            thickness_m=0.3,
            height_m=height_m,
            doors=[],
        ),
    ]

    rooms = [
        RoomSpec(
            id="room_hangar",
            name="Zone de stockage & quais",
            purpose="hangar",
            floor_index=0,
            polygon=[(-hw, -hd), (hw - workshop_w, -hd), (hw - workshop_w, -hd + workshop_d), (hw, -hd + workshop_d), (hw, hd), (-hw, hd)],
            area_m2=width_m * depth_m - (workshop_w * workshop_d),
            ambient_audio="amb_warehouse_wind",
        ),
        RoomSpec(
            id="room_workshop",
            name="Atelier mécanique & pièces détachées",
            purpose="workshop",
            floor_index=0,
            polygon=[(hw - workshop_w, -hd), (hw, -hd), (hw, -hd + workshop_d), (hw - workshop_w, -hd + workshop_d)],
            area_m2=workshop_w * workshop_d,
            ambient_audio="amb_machinery_clink",
        ),
    ]

    floor = FloorSpec(
        floor_index=0,
        elevation_m=0.0,
        height_m=height_m,
        rooms=rooms,
        walls=ext_walls + int_walls,
    )

    return BuildingBlueprint(
        id=building_id,
        kind="warehouse",
        label=label,
        world_pos=world_pos,
        footprint_width_m=width_m,
        footprint_depth_m=depth_m,
        floors=[floor],
        roof_style="industrial_pitched",
        description="Grand hangar de pièces de rechange et containers sécurisés de Lost Heaven.",
        metadata={"essential": False, "forklift_nav_enabled": True},
    )
