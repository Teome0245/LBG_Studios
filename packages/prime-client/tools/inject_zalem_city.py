import json

with open("packages/prime-client/assets/maps/lost_heaven_buildings.json") as f:
    bld_data = json.load(f)

existing = {b["id"]: b for b in bld_data.get("buildings", [])}

# Mégalopole de Zalem
zalem_blds = [
    {
        "id": "poi:zalem_citadel_tower",
        "kind": "town_hall",
        "label": "Tour Haute du Conseil de Zalem",
        "x": -4500.0,
        "z": 600.0,
        "size_m": 120.0,
        "essential": True,
        "door": {"face": "east", "width_m": 24.0, "depth_m": 24.0, "apron_m": 16.0}
    },
    {
        "id": "poi:zalem_industrial_starport",
        "kind": "starport_shuttle",
        "label": "Spatioport Fret & Cargos de Zalem",
        "x": -4500.0,
        "z": 200.0,
        "size_m": 110.0,
        "essential": True,
        "door": {"face": "north", "width_m": 26.0, "depth_m": 26.0, "apron_m": 18.0}
    },
    {
        "id": "poi:zalem_high_foundry",
        "kind": "workshop",
        "label": "Hauts-Fourneaux & Fonderie Centrale",
        "x": -4900.0,
        "z": 800.0,
        "size_m": 90.0,
        "essential": True,
        "door": {"face": "east", "width_m": 20.0, "depth_m": 20.0, "apron_m": 12.0}
    },
    {
        "id": "poi:zalem_power_station",
        "kind": "workshop",
        "label": "Centrale Thermique à Fusion",
        "x": -5000.0,
        "z": 450.0,
        "size_m": 75.0,
        "essential": False,
        "door": {"face": "east", "width_m": 16.0, "depth_m": 16.0, "apron_m": 10.0}
    },
    {
        "id": "poi:zalem_tech_bazaar",
        "kind": "market",
        "label": "Grand Bazar Technologique de Zalem",
        "x": -4100.0,
        "z": 600.0,
        "size_m": 85.0,
        "essential": True,
        "door": {"face": "west", "width_m": 22.0, "depth_m": 22.0, "apron_m": 14.0}
    },
    {
        "id": "poi:zalem_cyber_clinic",
        "kind": "clinic",
        "label": "Clinique Cybernétique et Prothèses",
        "x": -4100.0,
        "z": 350.0,
        "size_m": 60.0,
        "essential": True,
        "door": {"face": "west", "width_m": 16.0, "depth_m": 16.0, "apron_m": 10.0}
    },
    {
        "id": "poi:zalem_iron_cantina",
        "kind": "cantina",
        "label": "La Forge d'Acier — Cantina Corporative",
        "x": -4250.0,
        "z": 800.0,
        "size_m": 65.0,
        "essential": True,
        "door": {"face": "south", "width_m": 16.0, "depth_m": 16.0, "apron_m": 10.0}
    },
    {
        "id": "poi:zalem_residential_sector_1",
        "kind": "npc_housing_block",
        "label": "Secteur d'Habitations Étagées Nord",
        "x": -4700.0,
        "z": 1050.0,
        "size_m": 80.0,
        "essential": False,
        "door": {"face": "south", "width_m": 16.0, "depth_m": 16.0, "apron_m": 10.0}
    },
    {
        "id": "poi:zalem_residential_sector_2",
        "kind": "npc_housing_block",
        "label": "Secteur d'Habitations Étagées Est",
        "x": -4300.0,
        "z": 1050.0,
        "size_m": 80.0,
        "essential": False,
        "door": {"face": "south", "width_m": 16.0, "depth_m": 16.0, "apron_m": 10.0}
    },
    {
        "id": "poi:zalem_monumental_gate",
        "kind": "city_gate",
        "label": "Porte Monumentale d'Acier de Zalem",
        "x": -3800.0,
        "z": 500.0,
        "size_m": 50.0,
        "essential": True
    }
]

for b in zalem_blds:
    existing[b["id"]] = b

bld_data["buildings"] = list(existing.values())
with open("packages/prime-client/assets/maps/lost_heaven_buildings.json", "w") as f:
    json.dump(bld_data, f, indent=2)

print("Zalem buildings added -> Total:", len(bld_data["buildings"]))

# Props et décors de la mégalopole de Zalem
with open("packages/prime-client/assets/maps/lost_heaven_props.json") as f:
    prp_data = json.load(f)

existing_p = {p["id"]: p for p in prp_data.get("props", [])}
existing_paths = {p["id"]: p for p in prp_data.get("paths", [])}

zalem_props = [
    # Silos de gaz et métal lourd
    {"id": "prop:zalem_city_silo_1", "kind": "mine_silo", "label": "Silo Cryogénique A", "x": -4950.0, "z": 650.0, "radius_m": 22.0, "z_draw": 4},
    {"id": "prop:zalem_city_silo_2", "kind": "mine_silo", "label": "Silo de Raffinage B", "x": -4950.0, "z": 950.0, "radius_m": 24.0, "z_draw": 4},
    {"id": "prop:zalem_city_silo_3", "kind": "mine_silo", "label": "Cuve Chimique C", "x": -4750.0, "z": 250.0, "radius_m": 18.0, "z_draw": 4},
    # Arches monumentales et piliers d'acier
    {"id": "prop:zalem_gate_arch", "kind": "stone_arch", "label": "Arche d'Acier de Zalem", "x": -3800.0, "z": 500.0, "width_m": 35.0, "rot_deg": 90.0, "z_draw": 6},
    # Conteneurs et parcs de stockage
    {"id": "prop:zalem_container_stack_1", "kind": "cargo_container", "label": "Parc de Fret Alpha", "x": -4350.0, "z": 220.0, "w_m": 22.0, "h_m": 8.0, "yaw_deg": 0.0, "color": "#4a5b6d", "z_draw": 4},
    {"id": "prop:zalem_container_stack_2", "kind": "cargo_container", "label": "Parc de Fret Bêta", "x": -4650.0, "z": 180.0, "w_m": 20.0, "h_m": 8.0, "yaw_deg": 15.0, "color": "#6d5b4a", "z_draw": 4},
    {"id": "prop:zalem_container_stack_3", "kind": "cargo_container", "label": "Dépôt de Duracier", "x": -4800.0, "z": 750.0, "w_m": 18.0, "h_m": 7.0, "yaw_deg": -10.0, "color": "#5a6855", "z_draw": 4},
    # Piles de caisses de haute technologie
    {"id": "prop:zalem_bazaar_crates_1", "kind": "crate_stack", "label": "Composants Électroniques", "x": -4050.0, "z": 620.0, "z_draw": 4},
    {"id": "prop:zalem_bazaar_crates_2", "kind": "crate_stack", "label": "Pièces Mécatroniques", "x": -4150.0, "z": 570.0, "z_draw": 4},
]

for p in zalem_props:
    existing_p[p["id"]] = p

# Grand boulevard et enceinte de Zalem
zalem_paths = [
    # Boulevard Central de Zalem : Porte Est -> Citadelle -> Fonderie
    {
        "id": "path:zalem_grand_boulevard",
        "kind": "road",
        "width_m": 24.0,
        "points": [
            {"x": -3800.0, "z": 500.0},
            {"x": -4100.0, "z": 550.0},
            {"x": -4500.0, "z": 600.0},
            {"x": -4850.0, "z": 650.0}
        ]
    },
    # Avenue du Spatioport
    {
        "id": "path:zalem_avenue_starport",
        "kind": "road",
        "width_m": 18.0,
        "points": [
            {"x": -4500.0, "z": 600.0},
            {"x": -4500.0, "z": 220.0}
        ]
    },
    # Avenue Nord vers les Quartiers Résidentiels
    {
        "id": "path:zalem_avenue_north",
        "kind": "road",
        "width_m": 18.0,
        "points": [
            {"x": -4500.0, "z": 600.0},
            {"x": -4500.0, "z": 1050.0}
        ]
    },
    # Autoroute Commerciale : Avant-poste Zalem -> Porte Monumentale de Zalem
    {
        "id": "path:highway_outpost_to_zalem_city",
        "kind": "road",
        "width_m": 16.0,
        "points": [
            {"x": -1200.0, "z": -500.0},
            {"x": -2000.0, "z": -250.0},
            {"x": -2800.0, "z": 100.0},
            {"x": -3400.0, "z": 350.0},
            {"x": -3800.0, "z": 500.0}
        ]
    },
    # Rempart fortifié d'enceinte de la mégalopole de Zalem
    {
        "id": "path:zalem_perimeter_wall",
        "kind": "fence",
        "width_m": 10.0,
        "closed": True,
        "points": [
            {"x": -3800.0, "z": 450.0},
            {"x": -3800.0, "z": 150.0},
            {"x": -4200.0, "z": -50.0},
            {"x": -4800.0, "z": -50.0},
            {"x": -5200.0, "z": 150.0},
            {"x": -5300.0, "z": 600.0},
            {"x": -5200.0, "z": 1100.0},
            {"x": -4800.0, "z": 1250.0},
            {"x": -4200.0, "z": 1250.0},
            {"x": -3800.0, "z": 800.0},
            {"x": -3800.0, "z": 550.0}
        ]
    }
]

for p in zalem_paths:
    existing_paths[p["id"]] = p

prp_data["props"] = list(existing_p.values())
prp_data["paths"] = list(existing_paths.values())

with open("packages/prime-client/assets/maps/lost_heaven_props.json", "w") as f:
    json.dump(prp_data, f, indent=2)

print("Zalem props and paths added -> Total props:", len(prp_data["props"]), "paths:", len(prp_data["paths"]))
