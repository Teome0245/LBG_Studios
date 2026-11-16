#!/usr/bin/env python3
"""distribute_64k_world.py — Répartition spatiale équilibrée des cités, POIs et routes sur 64 km × 64 km."""
import json
from pathlib import Path

# Définition des décalages (dx, dz) par catégorie / site
SHIFTS = {
    "zalem_city": (-13500.0, 2400.0),       # -4500, 600 -> -18000, 3000
    "zalem_outpost": (-5800.0, -500.0),     # -1200, -500 -> -7000, -1000
    "ksar_nomade": (1050.0, -14350.0),      # 4950, -3650 -> 6000, -18000
    "canyon_epaves": (5350.0, -11750.0),    # 5650, -3250 -> 11000, -15000
    "oasis_al_khali": (11450.0, -7520.0),   # 6550, -2480 -> 18000, -10000
    "guet_dunes": (17350.0, -3620.0),       # 6650, -1380 -> 24000, -5000
    "ferme_humidite": (650.0, -5800.0),     # 3850, -2200 -> 4500, -8000
    "anchor_ridge": (2800.0, 12800.0),      # 4200, 3200 -> 7000, 16000
    "lac_amethyste": (8400.0, 17500.0),     # 5600, 4500 -> 14000, 22000
    "mos_espa": (-11800.0, -3200.0),        # -2200, -800 -> -14000, -4000
    "jawa": (-14400.0, -7800.0),            # -3600, -1200 -> -18000, -9000
    "gouffre_krayt": (-17500.0, 11400.0),   # -4500, 600 -> -22000, 12000
}

def get_shift_for_id(item_id: str) -> tuple[float, float]:
    iid = item_id.lower()
    if "zalem_citadel" in iid or "zalem_industrial" in iid or "zalem_high_foundry" in iid or \
       "zalem_power_station" in iid or "zalem_tech_bazaar" in iid or "zalem_cyber_clinic" in iid or \
       "zalem_iron_cantina" in iid or "zalem_residential" in iid or "zalem_monumental" in iid or \
       "zalem_city" in iid or "zalem_gate_arch" in iid or "zalem_container_stack" in iid or \
       "zalem_bazaar" in iid:
        return SHIFTS["zalem_city"]
    if "zalem_outpost" in iid or "lamp:zalem" in iid or "barrier:zalem" in iid or "prop:zalem_silo" in iid or "prop:zalem_container" in iid:
        return SHIFTS["zalem_outpost"]
    if "ksar" in iid:
        return SHIFTS["ksar_nomade"]
    if "humidite" in iid or "vaporator" in iid or "farm_" in iid:
        return SHIFTS["ferme_humidite"]
    if "anchor" in iid:
        return SHIFTS["anchor_ridge"]
    if "amethyste" in iid or "lac_" in iid:
        return SHIFTS["lac_amethyste"]
    if "mos_espa" in iid:
        return SHIFTS["mos_espa"]
    if "jawa" in iid:
        return SHIFTS["jawa"]
    if "krayt_leviathan" in iid or "krayt_boulders_chasm" in iid:
        return SHIFTS["gouffre_krayt"]
    if "al_khali" in iid:
        return SHIFTS["oasis_al_khali"]
    if "dune_lookout" in iid or "starship_wreck_east" in iid:
        return SHIFTS["guet_dunes"]
    if "salvage_canyon" in iid or "canyon" in iid or "krayt_skeleton" in iid:
        return SHIFTS["canyon_epaves"]
    return (0.0, 0.0)

# 1. Mise à jour de lost_heaven_buildings.json
bld_path = Path("packages/prime-client/assets/maps/lost_heaven_buildings.json")
with open(bld_path, "r", encoding="utf-8") as f:
    bld_data = json.load(f)

for b in bld_data.get("buildings", []):
    dx, dz = get_shift_for_id(b["id"])
    if dx != 0.0 or dz != 0.0:
        b["x"] = round(b["x"] + dx, 1)
        b["z"] = round(b["z"] + dz, 1)

with open(bld_path, "w", encoding="utf-8") as f:
    json.dump(bld_data, f, indent=2, ensure_ascii=False)
print(f"[OK] Updated {len(bld_data['buildings'])} buildings in {bld_path}")

# 2. Mise à jour de lost_heaven_props.json
props_path = Path("packages/prime-client/assets/maps/lost_heaven_props.json")
with open(props_path, "r", encoding="utf-8") as f:
    props_data = json.load(f)

for p in props_data.get("props", []):
    dx, dz = get_shift_for_id(p["id"])
    if dx != 0.0 or dz != 0.0:
        p["x"] = round(p["x"] + dx, 1)
        p["z"] = round(p["z"] + dz, 1)

def make_pt(x: float, z: float) -> dict[str, float]:
    return {"x": round(float(x), 1), "z": round(float(z), 1)}

# Mise à jour des tracés de routes régionales dans props_data["paths"]
for pa in props_data.get("paths", []):
    pid = pa.get("id", "")
    if pid == "highway_outpost_to_zalem_city":
        pa["points"] = [
            make_pt(-7000.0, -1000.0),
            make_pt(-9500.0, -200.0),
            make_pt(-12500.0, 800.0),
            make_pt(-15500.0, 1900.0),
            make_pt(-17300.0, 2900.0)
        ]
    elif pid == "road_lh_to_zalem_sinuous":
        pa["points"] = [
            make_pt(3688.9, -675.9),
            make_pt(1500.0, -680.0),
            make_pt(-500.0, -750.0),
            make_pt(-2500.0, -850.0),
            make_pt(-4500.0, -920.0),
            make_pt(-7000.0, -1000.0)
        ]
    elif pid == "road_lh_east_to_ksar_caravan":
        pa["points"] = [
            make_pt(5813.6, -982.5),
            make_pt(5600.0, -3000.0),
            make_pt(5100.0, -5500.0),
            make_pt(4500.0, -8000.0),
            make_pt(4800.0, -12000.0),
            make_pt(5400.0, -15500.0),
            make_pt(6000.0, -18000.0)
        ]
    elif pid == "road_ksar_to_canyon_alkhali":
        pa["points"] = [
            make_pt(6000.0, -18000.0),
            make_pt(8500.0, -16500.0),
            make_pt(11000.0, -15000.0),
            make_pt(14500.0, -12500.0),
            make_pt(18000.0, -10000.0),
            make_pt(21000.0, -7500.0),
            make_pt(24000.0, -5000.0)
        ]
    elif pid == "road_lh_to_anchor_ridge":
        pa["points"] = [
            make_pt(4749.0, -430.0),
            make_pt(5200.0, 3500.0),
            make_pt(5800.0, 8000.0),
            make_pt(6400.0, 12500.0),
            make_pt(7000.0, 16000.0),
            make_pt(10500.0, 19000.0),
            make_pt(14000.0, 22000.0)
        ]
    elif pid == "road_zalem_to_mos_espa":
        pa["points"] = [
            make_pt(-18000.0, 3000.0),
            make_pt(-16000.0, -500.0),
            make_pt(-14000.0, -4000.0)
        ]
    elif pid == "road_mos_espa_to_jawas":
        pa["points"] = [
            make_pt(-14000.0, -4000.0),
            make_pt(-16000.0, -6500.0),
            make_pt(-18000.0, -9000.0)
        ]
    elif pid == "road_mos_espa_to_krayt":
        pa["points"] = [
            make_pt(-14000.0, -4000.0),
            make_pt(-18000.0, 4000.0),
            make_pt(-22000.0, 12000.0)
        ]
    elif "zalem_" in pid and "highway" not in pid:
        dx, dz = SHIFTS["zalem_city"]
        new_pts = []
        for pt in pa.get("points", []):
            new_pts.append(make_pt(pt["x"] + dx, pt["z"] + dz))
        pa["points"] = new_pts
    elif "cliff_ksar" in pid:
        dx, dz = SHIFTS["ksar_nomade"]
        new_pts = []
        for pt in pa.get("points", []):
            new_pts.append(make_pt(pt["x"] + dx, pt["z"] + dz))
        pa["points"] = new_pts
    elif "cliff_shipwreck" in pid:
        dx, dz = SHIFTS["canyon_epaves"]
        new_pts = []
        for pt in pa.get("points", []):
            new_pts.append(make_pt(pt["x"] + dx, pt["z"] + dz))
        pa["points"] = new_pts

with open(props_path, "w", encoding="utf-8") as f:
    json.dump(props_data, f, indent=2, ensure_ascii=False)
print(f"[OK] Updated {len(props_data['props'])} props and {len(props_data['paths'])} paths in {props_path}")

# 3. Mise à jour de scrapaltai_planet_map.json
map_path = Path("packages/prime-client/assets/maps/scrapaltai_planet_map.json")
with open(map_path, "r", encoding="utf-8") as f:
    map_data = json.load(f)

NEW_COORDS = {
    "city:lost_heaven": (4749.0, -737.0),
    "city:ksar_nomade": (6000.0, -18000.0),
    "city:canyon_epaves": (11000.0, -15000.0),
    "city:oasis_al_khali": (18000.0, -10000.0),
    "city:guet_dunes": (24000.0, -5000.0),
    "city:ferme_humidite": (4500.0, -8000.0),
    "city:avant_poste_zalem": (-7000.0, -1000.0),
    "city:zalem": (-18000.0, 3000.0),
    "city:mos_espa_bazar": (-14000.0, -4000.0),
    "city:camp_ferrailleurs": (-18000.0, -9000.0),
    "city:gouffre_krayt": (-22000.0, 12000.0),
    "city:anchor_ridge": (7000.0, 16000.0),
    "city:lac_amethyste": (14000.0, 22000.0),
}

for s in map_data.get("settlements", []):
    sid = s.get("id")
    if sid in NEW_COORDS:
        s["x"], s["z"] = NEW_COORDS[sid]

with open(map_path, "w", encoding="utf-8") as f:
    json.dump(map_data, f, indent=2, ensure_ascii=False)
print(f"[OK] Updated {len(map_data['settlements'])} settlements in {map_path}")

# 4. Mise à jour de scrapaltai_pois.json
pois_path = Path("packages/prime-client/assets/maps/scrapaltai_pois.json")
with open(pois_path, "r", encoding="utf-8") as f:
    pois_data = json.load(f)

POI_MAP = {
    "poi:lost_heaven": (4749.0, -737.0),
    "poi:ksar_nomade": (6000.0, -18000.0),
    "poi:salvage_canyon": (11000.0, -15000.0),
    "poi:oasis_al_khali": (18000.0, -10000.0),
    "poi:dune_lookout": (24000.0, -5000.0),
    "poi:ferme_humidite": (4500.0, -8000.0),
    "poi:avant_poste_zalem": (-7000.0, -1000.0),
    "poi:zalem": (-18000.0, 3000.0),
    "poi:mos_espa_bazar": (-14000.0, -4000.0),
    "poi:camp_ferrailleurs": (-18000.0, -9000.0),
    "poi:gouffre_krayt": (-22000.0, 12000.0),
    "poi:anchor_ridge": (7000.0, 16000.0),
    "poi:lac_amethyste": (14000.0, 22000.0),
}

for p in pois_data.get("pois", []):
    pid = p.get("id")
    if pid in POI_MAP:
        p["x"], p["z"] = POI_MAP[pid]

with open(pois_path, "w", encoding="utf-8") as f:
    json.dump(pois_data, f, indent=2, ensure_ascii=False)
print(f"[OK] Updated POIs in {pois_path}")

# 5. Mise à jour de catalog_poi.json
cat_path = Path("packages/prime-hub/data/catalog_poi.json")
with open(cat_path, "r", encoding="utf-8") as f:
    cat_data = json.load(f)

for it in cat_data.get("items", []):
    iid = it.get("id")
    if iid in POI_MAP:
        it["x"], it["z"] = POI_MAP[iid]

with open(cat_path, "w", encoding="utf-8") as f:
    json.dump(cat_data, f, indent=2, ensure_ascii=False)
print(f"[OK] Updated catalog_poi.json items")
