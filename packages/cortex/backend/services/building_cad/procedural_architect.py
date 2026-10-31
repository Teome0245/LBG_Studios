"""procedural_architect.py — Générateur architectural paramétrique de bâtiments.

Génère des plans 2D/3D praticables avec cloisons, portes d'accès, pièces et ouvertures.
Inspiré des règles de tracé CAO (orthogonalité, dégagement de circulation, seuils).
"""

from __future__ import annotations

from .blueprint_model import (
    BuildingBlueprint,
    DoorSpec,
    FloorSpec,
    FurnitureSpec,
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

    # 4. Mobilier fonctionnel et points d'ancrage d'interaction de la Cantina (Ticket 3.1)
    furniture = [
        # Grand comptoir en ferraille de Jax dans la salle principale
        FurnitureSpec(
            id="cantina_bar_counter",
            kind="bar_counter",
            label="Comptoir en ferraille de Jax",
            pos=(0.0, -1.0),
            width_m=8.0,
            depth_m=1.2,
            room_id="room_main_hall",
            interaction_type="drink",
            capacity=4,
        ),
        # 4 tabourets le long du comptoir
        FurnitureSpec(
            id="cantina_stool_1",
            kind="seat",
            label="Tabouret de bar 1",
            pos=(-2.5, 0.4),
            width_m=0.6,
            depth_m=0.6,
            room_id="room_main_hall",
            interaction_type="sit",
            capacity=1,
        ),
        FurnitureSpec(
            id="cantina_stool_2",
            kind="seat",
            label="Tabouret de bar 2",
            pos=(-0.8, 0.4),
            width_m=0.6,
            depth_m=0.6,
            room_id="room_main_hall",
            interaction_type="sit",
            capacity=1,
        ),
        FurnitureSpec(
            id="cantina_stool_3",
            kind="seat",
            label="Tabouret de bar 3",
            pos=(0.8, 0.4),
            width_m=0.6,
            depth_m=0.6,
            room_id="room_main_hall",
            interaction_type="sit",
            capacity=1,
        ),
        FurnitureSpec(
            id="cantina_stool_4",
            kind="seat",
            label="Tabouret de bar 4",
            pos=(2.5, 0.4),
            width_m=0.6,
            depth_m=0.6,
            room_id="room_main_hall",
            interaction_type="sit",
            capacity=1,
        ),
        # Tables d'alcôve pour les négociations et le jeu de dés
        FurnitureSpec(
            id="cantina_table_1",
            kind="cantina_table",
            label="Table d'alcôve Ouest",
            pos=(-8.0, 4.0),
            width_m=2.4,
            depth_m=2.4,
            room_id="room_main_hall",
            interaction_type="sit",
            capacity=4,
        ),
        FurnitureSpec(
            id="cantina_table_2",
            kind="cantina_table",
            label="Table d'alcôve Est",
            pos=(8.0, 4.0),
            width_m=2.4,
            depth_m=2.4,
            room_id="room_main_hall",
            interaction_type="sit",
            capacity=4,
        ),
        # Bureau du gérant / boss
        FurnitureSpec(
            id="cantina_boss_desk",
            kind="office_desk",
            label="Bureau de direction",
            pos=(10.0, -8.0),
            width_m=2.4,
            depth_m=1.2,
            room_id="room_boss_office",
            interaction_type="inspect",
            capacity=1,
        ),
        # Couchette de repos dans l'arrière-salle
        FurnitureSpec(
            id="cantina_bunk_bed",
            kind="bunk_bed",
            label="Couchette de repos",
            pos=(-10.0, -8.0),
            width_m=1.4,
            depth_m=2.4,
            room_id="room_storage",
            interaction_type="rest",
            capacity=2,
        ),
        # Caisse de stockage / réserve
        FurnitureSpec(
            id="cantina_storage_crate",
            kind="storage_crate",
            label="Caisse de contrebande scellée",
            pos=(-5.0, -8.0),
            width_m=1.6,
            depth_m=1.6,
            room_id="room_storage",
            interaction_type="loot",
            capacity=1,
        ),
    ]

    floor = FloorSpec(
        floor_index=0,
        elevation_m=0.0,
        height_m=height_m,
        rooms=rooms,
        walls=ext_walls + int_walls,
        furniture=furniture,
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

    # 4. Mobilier fonctionnel et points d'ancrage d'interaction du Hangar (Ticket 3.1)
    furniture = [
        # Grand établi d'artisanat et découpe ferraille dans l'atelier
        FurnitureSpec(
            id="warehouse_craft_bench",
            kind="craft_bench",
            label="Établi de découpe et soudure lourde",
            pos=(hw - workshop_w * 0.5, -hd + 3.0),
            width_m=4.0,
            depth_m=1.6,
            room_id="room_workshop",
            interaction_type="craft",
            capacity=2,
        ),
        # Pupitre / bureau du contremaître
        FurnitureSpec(
            id="warehouse_foreman_desk",
            kind="office_desk",
            label="Pupitre du contremaître",
            pos=(hw - 2.5, -hd + workshop_d - 2.5),
            width_m=2.2,
            depth_m=1.2,
            room_id="room_workshop",
            interaction_type="inspect",
            capacity=1,
        ),
        # Rayonnages industriels de pièces détachées dans la baie
        FurnitureSpec(
            id="warehouse_storage_rack_north",
            kind="storage_rack",
            label="Rayonnage de carlingues et plaques",
            pos=(-hw * 0.4, -hd + 3.5),
            width_m=6.0,
            depth_m=1.8,
            room_id="room_hangar",
            interaction_type="loot",
            capacity=4,
        ),
        FurnitureSpec(
            id="warehouse_storage_rack_south",
            kind="storage_rack",
            label="Rayonnage de tuyères et réacteurs",
            pos=(-hw * 0.4, hd - 3.5),
            width_m=6.0,
            depth_m=1.8,
            room_id="room_hangar",
            interaction_type="loot",
            capacity=4,
        ),
        # Conteneur lourd de pièces de récupération
        FurnitureSpec(
            id="warehouse_container_central",
            kind="storage_crate",
            label="Conteneur de pièces scellé",
            pos=(0.0, 0.0),
            width_m=3.0,
            depth_m=2.0,
            room_id="room_hangar",
            interaction_type="loot",
            capacity=2,
        ),
    ]

    floor = FloorSpec(
        floor_index=0,
        elevation_m=0.0,
        height_m=height_m,
        rooms=rooms,
        walls=ext_walls + int_walls,
        furniture=furniture,
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
