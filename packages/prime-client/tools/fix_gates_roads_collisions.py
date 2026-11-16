#!/usr/bin/env python3
"""fix_gates_roads_collisions.py — Corrige l'ouverture de la Porte Sud à Lost Heaven,
retrace toutes les routes régionales pour ne traverser ni rempart ni falaise,
et génère les polygones de collision des falaises dans scrapaltai_zones.json.
"""
import json
from pathlib import Path

def make_pt(x: float, z: float) -> dict[str, float]:
    return {"x": round(float(x), 1), "z": round(float(z), 1)}

# 1. Mise à jour de lost_heaven_props.json
props_path = Path("packages/prime-client/assets/maps/lost_heaven_props.json")
with open(props_path, "r", encoding="utf-8") as f:
    props_data = json.load(f)

# A. Aménagement de la Porte Sud dans path:lh_perimeter_fence
for pa in props_data.get("paths", []):
    if pa.get("id") == "path:lh_perimeter_fence":
        pts = pa.get("points", [])
        # Remplace le point 14 (qui traversait le sud) par deux piliers de porte avec passage libre
        new_pts = []
        for i, pt in enumerate(pts):
            if i == 14: # Ancien centre sud [4749.0, -1387.8]
                new_pts.append(make_pt(4780.0, -1387.8)) # Pilier Est Porte Sud
                new_pts.append(make_pt(4718.0, -1387.8)) # Pilier Ouest Porte Sud (ouverture de 62m)
            else:
                new_pts.append(pt)
        pa["points"] = new_pts
        break

# B. Enregistrement de gate:south_dunes dans gate_exits
gate_exits = props_data.get("gate_exits", [])
# Supprimer d'éventuels doublons
gate_exits = [g for g in gate_exits if g.get("id") != "gate:south_dunes"]
gate_exits.append({
    "id": "gate:south_dunes",
    "label": "Porte sud — route du Ksar & dunes",
    "building_id": "poi:lost_heaven_gate_south",
    "role": "route_vers_ksar",
    "axis": "z",
    "center": {"x": 4749.0, "z": -1387.8},
    "width_m": 58.0,
    "depth_north_m": 120.0,
    "depth_south_m": 120.0,
    "fence_open_segment_indices": [13, 14]
})
props_data["gate_exits"] = gate_exits

# C. Ajout des props de la Porte Sud
props_list = props_data.get("props", [])
props_list = [p for p in props_list if not p.get("id", "").startswith("prop:lh_gate_south")]
props_list.extend([
    {
        "id": "prop:lh_gate_south_arch",
        "kind": "stone_arch",
        "label": "Arche monumentale de la Porte Sud",
        "x": 4749.0,
        "y": 0.0,
        "z": -1387.8,
        "scale": 1.4,
        "rot_deg": 0.0
    },
    {
        "id": "prop:lh_gate_south_lamp_w",
        "kind": "lamp_post",
        "label": "Lanterne Ouest Porte Sud",
        "x": 4716.0,
        "y": 0.0,
        "z": -1387.8,
        "scale": 1.0,
        "rot_deg": 0.0
    },
    {
        "id": "prop:lh_gate_south_lamp_e",
        "kind": "lamp_post",
        "label": "Lanterne Est Porte Sud",
        "x": 4782.0,
        "y": 0.0,
        "z": -1387.8,
        "scale": 1.0,
        "rot_deg": 0.0
    }
])
props_data["props"] = props_list

# D. Tracés précis des routes pour respecter remparts et falaises
ROADS = {
    # 1. Route Sud : Sort par la Porte Sud de Lost Heaven -> Lars-Val -> Ksar Nomade
    "path:road_lh_to_humidity_farm": [
        make_pt(4749.0, -980.0),    # Place du Marché / sud intérieur
        make_pt(4749.0, -1387.8),   # Passe EXACTEMENT par la Porte Sud
        make_pt(4749.0, -1800.0),   # Sortie franche dans les dunes
        make_pt(4680.0, -3500.0),
        make_pt(4580.0, -5800.0),
        make_pt(4500.0, -8000.0),   # Arrivée Ferme d'Humidité Lars-Val
        make_pt(4800.0, -11500.0),
        make_pt(5300.0, -15000.0),
        make_pt(6000.0, -18000.0)   # Arrivée Ksar Nomade
    ],
    # 2. Route Ouest : Sort par la Porte Ouest de Lost Heaven -> Avant-poste Zalem
    "path:road_lh_to_zalem_sinuous": [
        make_pt(4749.0, -737.0),    # Place centrale Lost Heaven
        make_pt(3688.9, -675.9),    # Passe EXACTEMENT par la Porte Ouest
        make_pt(1500.0, -680.0),
        make_pt(-500.0, -750.0),
        make_pt(-2500.0, -850.0),
        make_pt(-4800.0, -920.0),
        make_pt(-7000.0, -1000.0)   # Arrivée Avant-poste Zalem
    ],
    # 3. Autoroute Inter-cités : Avant-poste Zalem -> Porte Monumentale de Zalem
    "path:highway_outpost_to_zalem_city": [
        make_pt(-7000.0, -1000.0),  # Avant-poste Zalem
        make_pt(-9500.0, -200.0),
        make_pt(-12500.0, 800.0),
        make_pt(-15500.0, 1900.0),
        make_pt(-17300.0, 2900.0),  # Passe EXACTEMENT par la Porte Monumentale de Zalem
        make_pt(-18000.0, 3000.0)   # Grand Boulevard central
    ],
    # 4. Piste Ksar -> Canyon des Épaves -> Oasis Al-Khali -> Guet des Dunes
    # Passe STRICTEMENT au milieu de la gorge du canyon sans toucher les falaises Nord ni Sud
    "path:road_ksar_to_canyon_alkhali": [
        make_pt(6000.0, -18000.0),  # Ksar Nomade
        make_pt(8500.0, -16500.0),
        make_pt(10500.0, -15120.0), # Entrée ouest du canyon
        make_pt(10750.0, -15070.0), # Lit de la gorge (milieu)
        make_pt(11000.0, -15020.0), # Lit de la gorge (milieu)
        make_pt(11250.0, -14960.0), # Lit de la gorge (milieu)
        make_pt(11450.0, -14920.0), # Sortie est du canyon
        make_pt(14500.0, -12500.0),
        make_pt(18000.0, -10000.0), # Oasis d'Al-Khali
        make_pt(21000.0, -7500.0),
        make_pt(24000.0, -5000.0)   # Guet des Dunes / Cargo Ikaros
    ],
    # 5. Piste Caravanière Est : Sort par la Porte Est de Lost Heaven -> Al-Khali
    "path:road_lh_east_to_ksar_caravan": [
        make_pt(4749.0, -737.0),    # Place centrale Lost Heaven
        make_pt(5813.6, -982.5),    # Passe EXACTEMENT par la Porte Est
        make_pt(7500.0, -1500.0),   # Plaine désertique extérieure
        make_pt(11000.0, -3500.0),
        make_pt(15000.0, -6500.0),
        make_pt(18000.0, -10000.0)  # Rejoint l'Oasis d'Al-Khali
    ],
    # 6. Voie Nord : Sort par le Nord intérieur -> Anchor-Ridge -> Lac d'Améthyste
    "path:road_lh_to_anchor_ridge": [
        make_pt(4749.0, -430.0),    # Logements Nord Lost Heaven
        make_pt(5200.0, 3500.0),
        make_pt(5800.0, 8000.0),
        make_pt(6400.0, 12500.0),
        make_pt(7000.0, 16000.0),   # Anchor-Ridge
        make_pt(10500.0, 19000.0),
        make_pt(14000.0, 22000.0)   # Lac d'Améthyste
    ],
    # 7. Voies du Rift Ouest
    "path:road_zalem_to_mos_espa": [
        make_pt(-18000.0, 3000.0),
        make_pt(-16000.0, -500.0),
        make_pt(-14000.0, -4000.0)  # Mos Espa Bazar
    ],
    "path:road_mos_espa_to_jawas": [
        make_pt(-14000.0, -4000.0),
        make_pt(-16000.0, -6500.0),
        make_pt(-18000.0, -9000.0)  # Camp des Ferrailleurs Jawas
    ],
    "path:road_mos_espa_to_krayt": [
        make_pt(-14000.0, -4000.0),
        make_pt(-18000.0, 4000.0),
        make_pt(-22000.0, 12000.0)  # Gouffre du Dragon Krayt
    ]
}

# Remplacement des routes dans props_data["paths"]
for pa in props_data.get("paths", []):
    pid = pa.get("id", "")
    if pid in ROADS:
        pa["points"] = ROADS[pid]

# Supprimer les anciennes routes obsolètes résiduelles (ex: road_ksar_to_zalem_traverse)
props_data["paths"] = [p for p in props_data["paths"] if p.get("id") != "path:road_ksar_to_zalem_traverse"]

with open(props_path, "w", encoding="utf-8") as f:
    json.dump(props_data, f, indent=2, ensure_ascii=False)
print(f"[OK] lost_heaven_props.json mis à jour avec Porte Sud et routes propres.")

# 2. Ajout de poi:lost_heaven_gate_south dans lost_heaven_buildings.json
bld_path = Path("packages/prime-client/assets/maps/lost_heaven_buildings.json")
with open(bld_path, "r", encoding="utf-8") as f:
    bld_data = json.load(f)

blds = bld_data.get("buildings", [])
blds = [b for b in blds if b.get("id") != "poi:lost_heaven_gate_south"]
blds.append({
    "id": "poi:lost_heaven_gate_south",
    "kind": "city_gate",
    "name": "Porte Sud de Lost Heaven",
    "role": "porte_sud_dunes",
    "x": 4749.0,
    "y": 0.0,
    "z": -1387.8,
    "size_m": 48.0,
    "color": "#d98c3b"
})
bld_data["buildings"] = blds

with open(bld_path, "w", encoding="utf-8") as f:
    json.dump(bld_data, f, indent=2, ensure_ascii=False)
print(f"[OK] lost_heaven_buildings.json mis à jour avec poi:lost_heaven_gate_south.")

# 3. Polygones de collision des Falaises dans scrapaltai_zones.json
zones_path = Path("packages/prime-client/assets/maps/scrapaltai_zones.json")
with open(zones_path, "r", encoding="utf-8") as f:
    zones_data = json.load(f)

# Définition des blocs rocheux infranchissables des falaises du Canyon des Épaves
# Le lit praticable de la gorge est à Z entre -14940 et -15040
zones_data["collision"] = [
    {
        "id": "cliff:canyon_epaves_north_wall",
        "kind": "cliff_rock_wall",
        "label": "Falaise rocheuse Nord du Canyon des Épaves",
        "polygon": [
            [10650.0, -14940.0],
            [11350.0, -14750.0],
            [11350.0, -14900.0],
            [10650.0, -15040.0]
        ]
    },
    {
        "id": "cliff:canyon_epaves_south_wall",
        "kind": "cliff_rock_wall",
        "label": "Falaise rocheuse Sud du Canyon des Épaves",
        "polygon": [
            [10650.0, -15090.0],
            [11350.0, -14970.0],
            [11350.0, -15180.0],
            [10650.0, -15250.0]
        ]
    },
    {
        "id": "cliff:ksar_oasis_bluff_wall",
        "kind": "cliff_rock_wall",
        "label": "Paroi rocheuse d'enceinte du Ksar Nomade",
        "polygon": [
            [5700.0, -18150.0],
            [6500.0, -18050.0],
            [6500.0, -18300.0],
            [5700.0, -18300.0]
        ]
    }
]

with open(zones_path, "w", encoding="utf-8") as f:
    json.dump(zones_data, f, indent=2, ensure_ascii=False)
print(f"[OK] scrapaltai_zones.json mis à jour avec les polygones de collision de falaises.")
