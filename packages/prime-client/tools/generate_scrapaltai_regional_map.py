#!/usr/bin/env python3
"""Générateur de la carte régionale canonique de Scrapaltai (64 km × 64 km).

Caractéristiques :
- Échelle 1:1 exacte avec le moteur Core3 / SWG et le serveur prime-hub
- Dimensions : 64 000 m × 64 000 m (4 096 km²), coordonnées [-32000, +32000]
- Résolution : 2048 × 2048 px (1 pixel = 31.25 m)
- Topologie : Globe Sphérique Continu (Seamless World Wrap 360° Est/Ouest et Nord/Sud)
- Reliefs géographiques sculptés calés EXACTEMENT sur les entités en jeu
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 2048, 2048
X_MIN, X_MAX = -32000.0, 32000.0
Z_MIN, Z_MAX = -32000.0, 32000.0
SPAN = 64000.0

def to_px(x: float, z: float) -> tuple[float, float]:
    px = (x - X_MIN) / SPAN * float(W)
    py = (Z_MAX - z) / SPAN * float(H)
    return px, py

def main() -> int:
    print(f"[MapGen] Génération carte régionale Scrapaltai {W}x{H} (64 km × 64 km - 4096 km²)...")

    # 1. Grille normalisée [-1, 1]
    xs = np.linspace(-1.0, 1.0, W, dtype=np.float32)
    zs = np.linspace(1.0, -1.0, H, dtype=np.float32)
    xx, zz = np.meshgrid(xs, zs)

    # 2. Dunes toroïdales périodiques harmonieuses
    dunes = (
        np.sin(xx * 2.0 * math.pi * 8.0) * 0.05 +
        np.cos(zz * 2.0 * math.pi * 6.0) * 0.04 +
        np.sin((xx + zz) * 2.0 * math.pi * 12.0) * 0.03 +
        np.cos((xx - zz) * 2.0 * math.pi * 10.0) * 0.02
    )

    # 3. Masque de fondu doux toroïdal sur les bordures [-1, 1]
    edge_dist_x = np.minimum(xx + 1.0, 1.0 - xx)
    edge_dist_z = np.minimum(zz + 1.0, 1.0 - zz)
    edge_margin = 0.10
    blend_x = np.clip(edge_dist_x / edge_margin, 0.0, 1.0)
    blend_z = np.clip(edge_dist_z / edge_margin, 0.0, 1.0)
    seamless_mask = blend_x * blend_z

    # 4. Falaises de Duracier au Nord (zz > 0.40)
    north_grad = np.clip((zz - 0.35) / 0.55, 0.0, 1.0)
    north_texture = (
        np.sin(xx * 16.0 + zz * 14.0) * 0.16 +
        np.cos(xx * 32.0 - zz * 24.0) * 0.08
    )
    north_cliffs = (north_grad ** 1.3) * (0.85 + north_texture) * seamless_mask

    # 5. Massif Rocheux au Sud (zz < -0.45)
    south_grad = np.clip((-zz - 0.40) / 0.50, 0.0, 1.0)
    south_texture = (
        np.sin(xx * 18.0 - zz * 16.0) * 0.14 +
        np.cos(xx * 36.0 + zz * 28.0) * 0.07
    )
    south_hills = (south_grad ** 1.4) * (0.75 + south_texture) * seamless_mask

    # 6. Grand Rift & Canyons Ouest (xx < -0.10, zz ~ 0.0)
    dist_to_rift = np.abs(zz - (0.04 + 0.12 * np.sin(xx * 4.5)))
    rift_envelope = np.clip((-xx - 0.12) / 0.80, 0.0, 1.0)
    rift_depth = np.clip(1.0 - (dist_to_rift / 0.06), 0.0, 1.0) ** 0.8
    rift_primary = rift_envelope * rift_depth * -0.65 * seamless_mask

    # 7. Plateau de la Mégalopole de Zalem (X = -18 000, Z = 3 000)
    zalem_cx, zalem_cz = -18000.0 / 32000.0, 3000.0 / 32000.0
    dist_zalem = np.sqrt((xx - zalem_cx)**2 + (zz - zalem_cz)**2)
    zalem_plateau = np.clip(1.0 - (dist_zalem / 0.08), 0.0, 1.0) ** 1.2 * 0.28

    # 8. Plateau de Lost Heaven (X = 4749, Z = -737)
    lh_cx, lh_cz = 4749.0 / 32000.0, -737.0 / 32000.0
    dist_lh = np.sqrt((xx - lh_cx)**2 + (zz - lh_cz)**2)
    lh_plateau = np.clip(1.0 - (dist_lh / 0.07), 0.0, 1.0) * 0.15

    # 9. Oasis sacrée du Ksar Nomade (X = 6 000, Z = -18 000)
    oasis_cx, oasis_cz = 6000.0 / 32000.0, -18000.0 / 32000.0
    dist_oasis = np.sqrt((xx - oasis_cx)**2 + (zz - oasis_cz)**2)

    # 10. Oasis d'Al-Khali (X = 18 000, Z = -10 000)
    alkhali_cx, alkhali_cz = 18000.0 / 32000.0, -10000.0 / 32000.0
    dist_alkhali = np.sqrt((xx - alkhali_cx)**2 + (zz - alkhali_cz)**2)

    # 11. Cratère du Lac d'Améthyste (X = 14 000, Z = 22 000)
    lake_cx, lake_cz = 14000.0 / 32000.0, 22000.0 / 32000.0
    dist_lake = np.sqrt((xx - lake_cx)**2 + (zz - lake_cz)**2)
    crater_rim = np.exp(-((dist_lake - 0.055) ** 2) / (2.0 * (0.015**2))) * 0.45
    lake_basin = np.clip(1.0 - (dist_lake / 0.045), 0.0, 1.0) ** 1.5 * -0.55

    # Assemblage de l'élévation composite
    elevation = (
        0.44 + dunes + north_cliffs + south_hills +
        rift_primary + crater_rim + lake_basin +
        lh_plateau + zalem_plateau
    )
    elevation = np.clip(elevation, 0.0, 1.0)

    # 12. Ombrage relief
    dy, dx = np.gradient(elevation * 36.0)
    sun_az = math.radians(315.0)
    sun_alt = math.radians(42.0)
    slope = 0.5 * math.pi - np.arctan(np.sqrt(dx*dx + dy*dy))
    aspect = np.arctan2(-dy, dx)
    shaded = (
        np.sin(sun_alt) * np.sin(slope) +
        np.cos(sun_alt) * np.cos(slope) * np.cos(sun_az - aspect)
    )
    shaded = np.clip(shaded, 0.0, 1.0)

    # 13. Palette couleur sable / désert
    r = 212.0 * shaded * (0.64 + 0.36 * elevation) + 26.0
    g = 162.0 * shaded * (0.58 + 0.42 * elevation) + 16.0
    b = 116.0 * shaded * (0.48 + 0.46 * elevation) + 10.0

    # Teinte sombre pour les failles du Grand Rift
    rift_shadow = (rift_primary < -0.10)
    r[rift_shadow] *= 0.55
    g[rift_shadow] *= 0.45
    b[rift_shadow] *= 0.38

    # Emprise urbaine de la mégalopole de Zalem (teinte bronze / acier industriel)
    zalem_urban = (dist_zalem < 0.055)
    r[zalem_urban] = 165.0 + shaded[zalem_urban] * 35.0
    g[zalem_urban] = 135.0 + shaded[zalem_urban] * 25.0
    b[zalem_urban] = 105.0 + shaded[zalem_urban] * 18.0

    # Lac d'Améthyste
    lake_water = (dist_lake < 0.045)
    r[lake_water] = 28.0 + shaded[lake_water] * 24.0
    g[lake_water] = 84.0 + shaded[lake_water] * 48.0
    b[lake_water] = 145.0 + shaded[lake_water] * 75.0

    lake_rim = (dist_lake >= 0.045) & (dist_lake < 0.058)
    r[lake_rim] = 125.0 + shaded[lake_rim] * 35.0
    g[lake_rim] = 65.0 + shaded[lake_rim] * 25.0
    b[lake_rim] = 160.0 + shaded[lake_rim] * 45.0

    # Oasis Ksar Nomade
    oasis_mask = (dist_oasis < 0.015)
    r[oasis_mask] = 38.0 + shaded[oasis_mask] * 22.0
    g[oasis_mask] = 125.0 + shaded[oasis_mask] * 45.0
    b[oasis_mask] = 115.0 + shaded[oasis_mask] * 48.0

    # Oasis Al-Khali
    alkhali_mask = (dist_alkhali < 0.012)
    r[alkhali_mask] = 36.0 + shaded[alkhali_mask] * 20.0
    g[alkhali_mask] = 118.0 + shaded[alkhali_mask] * 42.0
    b[alkhali_mask] = 110.0 + shaded[alkhali_mask] * 44.0

    img_arr = np.dstack([np.clip(r, 0, 255), np.clip(g, 0, 255), np.clip(b, 0, 255)]).astype(np.uint8)
    base_img = Image.fromarray(img_arr, mode="RGB")
    base_img = base_img.filter(ImageFilter.SMOOTH_MORE)

    draw = ImageDraw.Draw(base_img)

    f_title = ImageFont.truetype("/usr/share/fonts/liberation/LiberationSans-Bold.ttf", 36)
    f_sub = ImageFont.truetype("/usr/share/fonts/liberation/LiberationSans-Regular.ttf", 19)
    f_city = ImageFont.truetype("/usr/share/fonts/liberation/LiberationSans-Bold.ttf", 22)
    f_hub = ImageFont.truetype("/usr/share/fonts/liberation/LiberationSans-Bold.ttf", 26)
    f_outpost = ImageFont.truetype("/usr/share/fonts/liberation/LiberationSans-Bold.ttf", 18)
    f_grid = ImageFont.truetype("/usr/share/fonts/liberation/LiberationSans-Bold.ttf", 15)

    # Réseau Routier Commercial Rouge / Ocre
    routes = [
        # Autoroute Inter-Cités : Lost Heaven -> Avant-poste Zalem -> Mégalopole de Zalem
        [(4749, -737), (3688, -675), (1500, -680), (-500, -750), (-2500, -850), (-4500, -920), (-7000, -1000), (-9500, -200), (-12500, 800), (-15500, 1900), (-18000, 3000)],
        # Piste Sud : Lost Heaven -> Lars-Val -> Ksar Nomade
        [(4749, -737), (5813, -982), (5600, -3000), (5100, -5500), (4500, -8000), (4800, -12000), (5400, -15500), (6000, -18000)],
        # Piste des Épaves et Dunes : Ksar -> Canyon -> Al-Khali -> Guet
        [(6000, -18000), (8500, -16500), (11000, -15000), (14500, -12500), (18000, -10000), (21000, -7500), (24000, -5000)],
        # Voie Nord : Lost Heaven -> Anchor-Ridge -> Lac d'Améthyste
        [(4749, -430), (5200, 3500), (5800, 8000), (6400, 12500), (7000, 16000), (10500, 19000), (14000, 22000)],
        # Voie du Rift : Zalem -> Mos Espa Bazar -> Jawas
        [(-18000, 3000), (-16000, -500), (-14000, -4000), (-16000, -6500), (-18000, -9000)],
        # Voie Krayt : Mos Espa -> Gouffre Krayt
        [(-14000, -4000), (-18000, 4000), (-22000, 12000)],
    ]

    for route in routes:
        pts = [to_px(rx, rz) for rx, rz in route]
        for i in range(len(pts) - 1):
            draw.line([pts[i], pts[i+1]], fill=(145, 52, 28, 130), width=6)
        for i in range(len(pts) - 1):
            draw.line([pts[i], pts[i+1]], fill=(205, 90, 48, 235), width=3)

    # Grille Métrique (tous les 8 000 m de -24 000 à +24 000)
    grid_coords = list(range(-24000, 25000, 8000))
    grid_col = (185, 155, 115, 80)
    axis_col = (215, 180, 135, 130)

    for c in grid_coords:
        gx, _ = to_px(c, 0)
        _, gz = to_px(0, c)
        draw.line([(gx, 45), (gx, H - 45)], fill=grid_col if c != 0 else axis_col, width=1 if c != 0 else 2)
        draw.line([(45, gz), (W - 45, gz)], fill=grid_col if c != 0 else axis_col, width=1 if c != 0 else 2)

        lbl_x = f"{c:+d}m" if c != 0 else "0 (Méridien)"
        lbl_z = f"{c:+d}m" if c != 0 else "0 (Équateur)"
        draw.text((gx + 4, H - 40), lbl_x, font=f_grid, fill=(235, 215, 180, 210))
        draw.text((50, gz - 18), lbl_z, font=f_grid, fill=(235, 215, 180, 210))

    # Bordure Fine de Cadastre
    inset = 35
    draw.rectangle([(inset, inset), (W - inset, H - inset)], outline=(115, 78, 48), width=4)
    draw.rectangle([(inset + 6, inset + 6), (W - inset - 6, H - inset - 6)], outline=(185, 140, 90), width=2)

    # Empreinte urbaine octogonale de la mégalopole de Zalem
    zx, zy = to_px(-18000.0, 3000.0)
    z_rad = 48
    z_pts = []
    for i in range(8):
        a = (float(i) / 8.0) * math.tau + 0.39
        z_pts.append((zx + math.cos(a) * z_rad, zy + math.sin(a) * z_rad))
    draw.polygon(z_pts, fill=(55, 45, 35, 160), outline=(235, 185, 60), width=3)

    # Établissements & Sites Canoniques
    sites = [
        ("zalem", "Zalem (Mégalopole)", -18000.0, 3000.0, "capital", "Capitale Lore · 10 Quartiers Industriels"),
        ("lost_heaven", "Lost Heaven", 4749.0, -737.0, "hub", "Hub Joueur · Spatioport"),
        ("avant_poste_zalem", "Avant-poste Zalem", -7000.0, -1000.0, "outpost", "Garnison de la Passe Ouest"),
        ("ksar_nomade", "Ksar Nomade", 6000.0, -18000.0, "oasis", "Oasis Sacrée du Grand Sud · Troc"),
        ("canyon_epaves", "Canyon des Épaves", 11000.0, -15000.0, "landmark", "Léviathan Krayt & Débris"),
        ("oasis_al_khali", "Oasis d'Al-Khali", 18000.0, -10000.0, "oasis", "Étape des Caravanes & Palmiers"),
        ("guet_dunes", "Guet des Dunes", 24000.0, -5000.0, "outpost", "Vigie Est & Cargo Ikaros"),
        ("ferme_humidite", "Ferme d'Humidité Lars-Val", 4500.0, -8000.0, "farm", "Station de Condensation Centrale"),
        ("anchor_ridge", "Anchor-Ridge", 7000.0, 16000.0, "town", "Mines de Duracier · Falaises Nord"),
        ("lac_amethyste", "Lac d'Améthyste", 14000.0, 22000.0, "landmark", "Cratère d'Impact & Réserve"),
        ("mos_espa_bazar", "Mos Espa Bazar", -14000.0, -4000.0, "bazaar", "Marché Marchand · Sortie Rift"),
        ("camp_ferrailleurs", "Camp des Ferrailleurs", -18000.0, -9000.0, "troglo", "Ateliers Jawas Troglodytes"),
        ("gouffre_krayt", "Gouffre du Dragon Krayt", -22000.0, 12000.0, "danger", "Antre Krayt · Failles Ouest"),
    ]

    for sid, name, sx, sz, stype, sub in sites:
        px, py = to_px(sx, sz)

        if stype == "capital":
            # Zalem (Mégalopole en Or & Acier)
            draw.circle((px, py), 26, fill=(215, 165, 35, 210), outline=(255, 240, 160), width=4)
            draw.circle((px, py), 12, fill=(255, 250, 220), outline=(140, 100, 15), width=2)
            draw.rectangle([(px - 440, py - 26), (px - 34, py + 26)], fill=(28, 22, 12, 235), outline=(235, 185, 55), width=2)
            draw.text((px - 425, py - 22), f"◆ {name}", font=f_hub, fill=(255, 235, 170))
            draw.text((px - 425, py + 4), sub, font=f_sub, fill=(225, 205, 145))

        elif stype == "hub":
            # Lost Heaven (Émeraude)
            draw.circle((px, py), 22, fill=(40, 180, 110, 180), outline=(180, 255, 210), width=3)
            draw.circle((px, py), 10, fill=(230, 255, 240), outline=(20, 100, 60), width=2)
            draw.rectangle([(px + 28, py - 24), (px + 28 + 360, py + 24)], fill=(15, 30, 22, 230), outline=(60, 180, 120), width=2)
            draw.text((px + 38, py - 21), f"★ {name}", font=f_hub, fill=(220, 255, 235))
            draw.text((px + 38, py + 3), sub, font=f_sub, fill=(160, 225, 185))

        elif stype in ("town", "landmark", "oasis"):
            col_fill = (45, 150, 140, 220) if stype == "oasis" else (195, 120, 45, 210)
            col_out = (160, 250, 240) if stype == "oasis" else (255, 210, 160)
            draw.circle((px, py), 13, fill=col_fill, outline=col_out, width=2)
            draw.circle((px, py), 5, fill=(255, 240, 215))
            draw.text((px + 16, py - 11), f"● {name}", font=f_city, fill=(255, 240, 215))
            draw.text((px + 16, py + 9), sub, font=f_sub, fill=(225, 195, 160))

        else:
            draw.circle((px, py), 10, fill=(60, 140, 175, 210), outline=(180, 225, 245), width=2)
            draw.circle((px, py), 4, fill=(240, 250, 255))
            draw.text((px + 14, py - 9), f"○ {name}", font=f_outpost, fill=(225, 240, 250))
            draw.text((px + 14, py + 7), sub, font=f_sub, fill=(175, 205, 220))

    # Cartouche Officiel (64 km × 64 km)
    c_x, c_y, c_w, c_h = 65, H - 310, 750, 240
    draw.rectangle([(c_x, c_y), (c_x + c_w, c_y + c_h)], fill=(22, 16, 12, 245), outline=(185, 145, 95), width=3)
    draw.rectangle([(c_x + 5, c_y + 5), (c_x + c_w - 5, c_y + c_h - 5)], outline=(115, 82, 52), width=1)

    draw.text((c_x + 20, c_y + 14), "SCRAPALTAI — CADASTRE RÉGIONAL JOUABLE", font=f_city, fill=(255, 225, 175))
    draw.text((c_x + 20, c_y + 44), "Mégalopole de Zalem, Bassin de Lost Heaven & Grand Rift", font=f_sub, fill=(215, 185, 145))
    draw.text((c_x + 20, c_y + 72), "• Superficie : 64 000 m × 64 000 m (4 096 km² canon LBG Studios)", font=f_sub, fill=(195, 180, 160))
    draw.text((c_x + 20, c_y + 98), "• Topologie : Globe Sphérique Continu (World Wrap 360°)", font=f_sub, fill=(160, 225, 195))
    draw.text((c_x + 20, c_y + 124), "• Origine centrale (0, 0) · Grille métrique tous les 8 000 m", font=f_sub, fill=(195, 180, 160))
    draw.text((c_x + 20, c_y + 150), "• Moteur prime-hub 192.168.0.246:8787 · Projection directe 1:1", font=f_sub, fill=(195, 180, 160))

    # Échelle graphique (16 km)
    bar_x = c_x + 20
    bar_y = c_y + 198
    bar_len = 512  # 16000 m sur 64000 m
    draw.line([(bar_x, bar_y), (bar_x + bar_len, bar_y)], fill=(245, 225, 185), width=4)
    for seg_m in [0, 4000, 8000, 16000]:
        seg_px = int(seg_m / 64000.0 * 2048.0)
        draw.line([(bar_x + seg_px, bar_y - 6), (bar_x + seg_px, bar_y + 6)], fill=(245, 225, 185), width=2)
        draw.text((bar_x + seg_px - 14, bar_y + 8), f"{seg_m // 1000} km" if seg_m > 0 else "0", font=f_grid, fill=(245, 225, 185))

    # Rose des Vents
    compass_cx, compass_cy = W - 140, H - 140
    draw.circle((compass_cx, compass_cy), 45, outline=(190, 150, 100), width=2)
    draw.polygon([(compass_cx, compass_cy - 48), (compass_cx - 10, compass_cy), (compass_cx + 10, compass_cy)], fill=(230, 200, 100))
    draw.polygon([(compass_cx, compass_cy + 48), (compass_cx - 8, compass_cy), (compass_cx + 8, compass_cy)], fill=(120, 90, 60))
    draw.polygon([(compass_cx + 48, compass_cy), (compass_cx, compass_cy - 8), (compass_cx, compass_cy + 8)], fill=(140, 110, 75))
    draw.polygon([(compass_cx - 48, compass_cy), (compass_cx, compass_cy - 8), (compass_cx, compass_cy + 8)], fill=(140, 110, 75))

    draw.text((compass_cx - 8, compass_cy - 72), "NORD", font=f_grid, fill=(255, 235, 175))
    draw.text((compass_cx - 5, compass_cy + 52), "SUD", font=f_grid, fill=(190, 170, 140))
    draw.text((compass_cx + 52, compass_cy - 8), "EST", font=f_grid, fill=(190, 170, 140))
    draw.text((compass_cx - 78, compass_cy - 8), "OUEST", font=f_grid, fill=(190, 170, 140))

    out_png = Path("packages/prime-client/assets/maps/scrapaltai_planet.png")
    out_jpg = Path("packages/prime-client/assets/maps/scrapaltai_planet.jpg")
    base_img.save(out_png, "PNG")
    base_img.convert("RGB").save(out_jpg, "JPEG", quality=95)
    print(f"[MapGen] Succès ! Carte 32 km sauvegardée dans {out_png} et {out_jpg}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
