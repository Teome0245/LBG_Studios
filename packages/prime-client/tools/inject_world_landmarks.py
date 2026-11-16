import json

# 1. Update lost_heaven_buildings.json
with open("packages/prime-client/assets/maps/lost_heaven_buildings.json") as f:
    bld_data = json.load(f)

existing_blds = {b["id"]: b for b in bld_data.get("buildings", [])}

new_blds = [
    # Ferme d'Humidité Lars-Val
    {
        "id": "poi:ferme_humidite_dome",
        "kind": "inn",
        "label": "Dôme d'Habitation Lars-Val",
        "x": 3850.0,
        "z": -2200.0,
        "size_m": 38.0,
        "essential": True,
        "door": {"face": "east", "width_m": 12.0, "depth_m": 12.0, "apron_m": 8.0}
    },
    {
        "id": "poi:ferme_humidite_tank",
        "kind": "workshop",
        "label": "Station de Pompage & Cuves",
        "x": 3890.0,
        "z": -2160.0,
        "size_m": 30.0,
        "essential": False,
        "door": {"face": "west", "width_m": 10.0, "depth_m": 10.0, "apron_m": 6.0}
    },
    # Anchor-Ridge (Falaises minières nord)
    {
        "id": "poi:anchor_ridge_mine_hq",
        "kind": "town_hall",
        "label": "QG des Mines d'Anchor-Ridge",
        "x": 4200.0,
        "z": 3200.0,
        "size_m": 58.0,
        "essential": True,
        "door": {"face": "south", "width_m": 16.0, "depth_m": 16.0, "apron_m": 10.0}
    },
    {
        "id": "poi:anchor_ridge_foundry",
        "kind": "workshop",
        "label": "Fonderie de Duracier & Concasseur",
        "x": 4270.0,
        "z": 3230.0,
        "size_m": 48.0,
        "essential": False,
        "door": {"face": "west", "width_m": 14.0, "depth_m": 14.0, "apron_m": 8.0}
    },
    {
        "id": "poi:anchor_ridge_cantina",
        "kind": "cantina",
        "label": "Le Filon Noir — Cantine des Mineurs",
        "x": 4130.0,
        "z": 3170.0,
        "size_m": 35.0,
        "essential": False,
        "door": {"face": "east", "width_m": 10.0, "depth_m": 10.0, "apron_m": 6.0}
    },
    # Lac d'Améthyste
    {
        "id": "poi:lac_amethyste_station",
        "kind": "workshop",
        "label": "Station Hydrique du Lac d'Améthyste",
        "x": 5720.0,
        "z": 4420.0,
        "size_m": 42.0,
        "essential": True,
        "door": {"face": "south", "width_m": 12.0, "depth_m": 12.0, "apron_m": 8.0}
    },
    # Mos Espa Bazar
    {
        "id": "poi:mos_espa_market_dome",
        "kind": "market",
        "label": "Bazar Marchand de Mos Espa",
        "x": -2200.0,
        "z": -800.0,
        "size_m": 56.0,
        "essential": True,
        "door": {"face": "east", "width_m": 18.0, "depth_m": 18.0, "apron_m": 10.0}
    },
    {
        "id": "poi:mos_espa_cantina",
        "kind": "cantina",
        "label": "Taverne de la Faille",
        "x": -2130.0,
        "z": -760.0,
        "size_m": 36.0,
        "essential": False,
        "door": {"face": "south", "width_m": 12.0, "depth_m": 12.0, "apron_m": 6.0}
    },
    {
        "id": "poi:mos_espa_exchange",
        "kind": "bank",
        "label": "Comptoir de Change du Rift",
        "x": -2260.0,
        "z": -840.0,
        "size_m": 32.0,
        "essential": False,
        "door": {"face": "north", "width_m": 10.0, "depth_m": 10.0, "apron_m": 6.0}
    },
    # Camp des Ferrailleurs Jawas
    {
        "id": "poi:jawa_salvage_vault",
        "kind": "workshop",
        "label": "Atelier Troglodyte des Ferrailleurs",
        "x": -3600.0,
        "z": -1200.0,
        "size_m": 40.0,
        "essential": True,
        "door": {"face": "east", "width_m": 12.0, "depth_m": 12.0, "apron_m": 8.0}
    }
]

for b in new_blds:
    existing_blds[b["id"]] = b

bld_data["buildings"] = list(existing_blds.values())
with open("packages/prime-client/assets/maps/lost_heaven_buildings.json", "w") as f:
    json.dump(bld_data, f, indent=2)

print(f"Updated lost_heaven_buildings.json -> total {len(bld_data['buildings'])} buildings")

# 2. Update lost_heaven_props.json
with open("packages/prime-client/assets/maps/lost_heaven_props.json") as f:
    prp_data = json.load(f)

existing_props = {p["id"]: p for p in prp_data.get("props", [])}
existing_paths = {p["id"]: p for p in prp_data.get("paths", [])}

new_props = [
    # Ferme d'Humidité Lars-Val : évaporateurs et citernes
    {"id": "prop:farm_vaporator_1", "kind": "moisture_vaporator", "label": "Condenseur GX-8", "x": 3810.0, "z": -2230.0, "scale": 1.2, "z_draw": 5},
    {"id": "prop:farm_vaporator_2", "kind": "moisture_vaporator", "label": "Condenseur GX-8", "x": 3840.0, "z": -2250.0, "scale": 1.1, "z_draw": 5},
    {"id": "prop:farm_vaporator_3", "kind": "moisture_vaporator", "label": "Condenseur GX-8", "x": 3870.0, "z": -2240.0, "scale": 1.3, "z_draw": 5},
    {"id": "prop:farm_vaporator_4", "kind": "moisture_vaporator", "label": "Condenseur GX-8", "x": 3820.0, "z": -2170.0, "scale": 1.2, "z_draw": 5},
    {"id": "prop:farm_vaporator_5", "kind": "moisture_vaporator", "label": "Condenseur GX-8", "x": 3890.0, "z": -2230.0, "scale": 1.0, "z_draw": 5},
    {"id": "prop:farm_water_cistern", "kind": "oasis_pool", "label": "Citerne souterraine d'eau douce", "x": 3895.0, "z": -2195.0, "radius_m": 12.0, "z_draw": 2},
    {"id": "prop:farm_container_1", "kind": "cargo_container", "label": "Caisse de filtres à saumure", "x": 3830.0, "z": -2170.0, "w_m": 8.0, "h_m": 4.0, "yaw_deg": 15.0, "z_draw": 4},

    # Anchor-Ridge : silos miniers, caisses et rochers
    {"id": "prop:anchor_silo_1", "kind": "mine_silo", "label": "Silo de stockage Duracier A", "x": 4250.0, "z": 3170.0, "radius_m": 16.0, "z_draw": 4},
    {"id": "prop:anchor_silo_2", "kind": "mine_silo", "label": "Silo de stockage Duracier B", "x": 4280.0, "z": 3210.0, "radius_m": 14.0, "z_draw": 4},
    {"id": "prop:anchor_container_1", "kind": "cargo_container", "label": "Conteneur de lingots", "x": 4180.0, "z": 3140.0, "w_m": 14.0, "h_m": 6.0, "yaw_deg": -25.0, "color": "#7a6248", "z_draw": 4},
    {"id": "prop:anchor_container_2", "kind": "cargo_container", "label": "Conteneur de forage", "x": 4210.0, "z": 3130.0, "w_m": 12.0, "h_m": 5.0, "yaw_deg": 10.0, "color": "#524436", "z_draw": 4},
    {"id": "prop:anchor_boulders_1", "kind": "boulder_cluster", "label": "Falaise d'extraction nord", "x": 4140.0, "z": 3260.0, "radius_m": 22.0, "z_draw": 3},
    {"id": "prop:anchor_boulders_2", "kind": "boulder_cluster", "label": "Éperon rocheux minier", "x": 4320.0, "z": 3260.0, "radius_m": 20.0, "z_draw": 3},

    # Lac d'Améthyste : grand bassin et cristaux
    {"id": "prop:lac_amethyste_basin", "kind": "oasis_pool", "label": "Bassin du Lac d'Améthyste", "x": 5600.0, "z": 4500.0, "radius_m": 85.0, "z_draw": 1},
    {"id": "prop:lac_cryst_1", "kind": "crystal_cluster", "label": "Géode d'Améthyste Cristalline", "x": 5510.0, "z": 4520.0, "radius_m": 14.0, "z_draw": 5},
    {"id": "prop:lac_cryst_2", "kind": "crystal_cluster", "label": "Géode d'Améthyste Cristalline", "x": 5680.0, "z": 4570.0, "radius_m": 16.0, "z_draw": 5},
    {"id": "prop:lac_cryst_3", "kind": "crystal_cluster", "label": "Aiguilles de Cristal Pourpre", "x": 5620.0, "z": 4410.0, "radius_m": 12.0, "z_draw": 5},
    {"id": "prop:lac_cryst_4", "kind": "crystal_cluster", "label": "Veine Cristalline du Cratère", "x": 5540.0, "z": 4440.0, "radius_m": 15.0, "z_draw": 5},

    # Mos Espa Bazar : tentes de troc, étals et caisses
    {"id": "prop:mos_espa_tent_1", "kind": "nomad_tent", "label": "Tente des Tissus & Épices", "x": -2160.0, "z": -850.0, "radius_m": 12.0, "cloth_color_1": "#9c3826", "cloth_color_2": "#e2a855", "z_draw": 4},
    {"id": "prop:mos_espa_tent_2", "kind": "nomad_tent", "label": "Étal des Marchands d'Eau", "x": -2190.0, "z": -870.0, "radius_m": 10.0, "cloth_color_1": "#2d6278", "cloth_color_2": "#dfc8a2", "z_draw": 4},
    {"id": "prop:mos_espa_crates_1", "kind": "crate_stack", "label": "Piles de caisses de contrebande", "x": -2240.0, "z": -770.0, "z_draw": 4},

    # Camp des Ferrailleurs Jawas : tentes, carcasse et ferraille
    {"id": "prop:jawa_tent_1", "kind": "nomad_tent", "label": "Tente de troglodytes Jawas", "x": -3560.0, "z": -1180.0, "radius_m": 9.0, "cloth_color_1": "#6a4528", "cloth_color_2": "#3e2412", "z_draw": 4},
    {"id": "prop:jawa_tent_2", "kind": "nomad_tent", "label": "Abri en peaux de bêtes", "x": -3640.0, "z": -1220.0, "radius_m": 8.0, "cloth_color_1": "#5c3d23", "cloth_color_2": "#3e2412", "z_draw": 4},
    {"id": "prop:jawa_crawler_wreck", "kind": "starship_wreck", "label": "Épave de Char des Sables", "x": -3620.0, "z": -1150.0, "length_m": 26.0, "yaw_deg": 35.0, "z_draw": 3},
    {"id": "prop:jawa_scrap_1", "kind": "crate_stack", "label": "Pièces détachées et droïdes", "x": -3580.0, "z": -1230.0, "z_draw": 4},

    # Gouffre du Dragon Krayt : squelette géant et rochers menaçants
    {"id": "prop:krayt_leviathan_chasm", "kind": "krayt_skeleton", "label": "Squelette de Léviathan Ancestral", "x": -4500.0, "z": 600.0, "length_m": 62.0, "width_m": 32.0, "yaw_deg": -15.0, "z_draw": 5},
    {"id": "prop:krayt_boulders_chasm", "kind": "boulder_cluster", "label": "Paroi rocheuse du Gouffre", "x": -4460.0, "z": 640.0, "radius_m": 24.0, "z_draw": 3},
]

for p in new_props:
    existing_props[p["id"]] = p

# Nouvelles pistes routières reliant ces sites
new_paths = [
    # Voie Lost Heaven Porte Sud -> Ferme d'Humidité -> Ksar Nomade
    {
        "id": "path:road_lh_to_humidity_farm",
        "kind": "road",
        "width_m": 10.0,
        "points": [
            {"x": 4749.0, "z": -1180.0},
            {"x": 4450.0, "z": -1500.0},
            {"x": 4150.0, "z": -1850.0},
            {"x": 3850.0, "z": -2200.0},
            {"x": 4200.0, "z": -2900.0},
            {"x": 4750.0, "z": -3450.0},
            {"x": 4950.0, "z": -3650.0}
        ]
    },
    # Voie Ksar Nomade -> Canyon des Épaves -> Oasis Al-Khali -> Guet des Dunes
    {
        "id": "path:road_ksar_to_canyon_alkhali",
        "kind": "road",
        "width_m": 11.0,
        "points": [
            {"x": 4950.0, "z": -3650.0},
            {"x": 5300.0, "z": -3450.0},
            {"x": 5650.0, "z": -3250.0},
            {"x": 6100.0, "z": -2850.0},
            {"x": 6550.0, "z": -2480.0},
            {"x": 6650.0, "z": -1380.0},
            {"x": 6250.0, "z": -1150.0},
            {"x": 5813.6, "z": -982.5}
        ]
    },
    # Voie Ouest : Avant-poste Zalem -> Mos Espa Bazar
    {
        "id": "path:road_zalem_to_mos_espa",
        "kind": "road",
        "width_m": 12.0,
        "points": [
            {"x": -1200.0, "z": -500.0},
            {"x": -1700.0, "z": -650.0},
            {"x": -2200.0, "z": -800.0}
        ]
    },
    # Piste Mos Espa -> Camp des Ferrailleurs Jawas
    {
        "id": "path:road_mos_espa_to_jawas",
        "kind": "road",
        "width_m": 8.0,
        "points": [
            {"x": -2200.0, "z": -800.0},
            {"x": -2850.0, "z": -1000.0},
            {"x": -3600.0, "z": -1200.0}
        ]
    },
    # Piste Mos Espa -> Gouffre du Dragon Krayt
    {
        "id": "path:road_mos_espa_to_krayt",
        "kind": "road",
        "width_m": 8.0,
        "points": [
            {"x": -2200.0, "z": -800.0},
            {"x": -3300.0, "z": -150.0},
            {"x": -4500.0, "z": 600.0}
        ]
    },
    # Voie Nord : Lost Heaven Porte Nord -> Anchor-Ridge -> Lac d'Améthyste
    {
        "id": "path:road_lh_to_anchor_ridge",
        "kind": "road",
        "width_m": 11.0,
        "points": [
            {"x": 4749.0, "z": -408.0},
            {"x": 4600.0, "z": 600.0},
            {"x": 4420.0, "z": 1800.0},
            {"x": 4200.0, "z": 3200.0},
            {"x": 4900.0, "z": 3850.0},
            {"x": 5600.0, "z": 4500.0}
        ]
    }
]

for p in new_paths:
    existing_paths[p["id"]] = p

prp_data["props"] = list(existing_props.values())
prp_data["paths"] = list(existing_paths.values())

with open("packages/prime-client/assets/maps/lost_heaven_props.json", "w") as f:
    json.dump(prp_data, f, indent=2)

print(f"Updated lost_heaven_props.json -> total {len(prp_data['props'])} props, {len(prp_data['paths'])} paths")
