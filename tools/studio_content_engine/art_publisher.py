"""art_publisher.py — Générateur et Module de Publication Autonome DeviantArt & Pinterest.

Fonctionnalités :
1. Génération d'Art Packs haute fidélité (DeviantArt 4K 16:9 + Pinterest 2:3 Vertical).
2. Authentification interactive et sauvegarde des cookies Netscape.
3. Téléversement automatique via Playwright headless (comme TikTok / YouTube).
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
import sys
import time
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("art_publisher")

ENGINE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ENGINE_DIR.parents[1]
ASSETS_DIR = ENGINE_DIR / "assets"
COMPAGNON_DIR = ASSETS_DIR / "compagnon"
COMPAGNON_MEDIUM_DIR = ASSETS_DIR / "compagnon_medium"
COMPAGNON_CLOSEUP_DIR = ASSETS_DIR / "compagnon_closeup"

OUTPUT_DIR = ENGINE_DIR / "art_drops"
DEVIANTART_DIR = OUTPUT_DIR / "deviantart"
PINTEREST_DIR = OUTPUT_DIR / "pinterest"

DEVIANTART_COOKIES = ENGINE_DIR / "deviantart_cookies.txt"
PINTEREST_COOKIES = ENGINE_DIR / "pinterest_cookies.txt"

# Couleurs canoniques LBG Studios
C_BG_DARK = (10, 14, 24, 255)
C_CYAN_NEON = (0, 240, 255, 255)
C_AMBER_CANTINA = (255, 115, 13, 255)
C_WHITE = (245, 250, 255, 255)
C_MUTED = (140, 165, 190, 255)
C_CARD_BG = (16, 24, 40, 235)
C_CARD_BORDER = (0, 240, 255, 140)
C_EMERALD = (0, 255, 163, 255)
C_CRIMSON = (255, 75, 100, 255)


def get_font(size: int, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Charge une police système adaptée."""
    if mono:
        candidates = [
            "/usr/share/fonts/liberation/LiberationMono-Bold.ttf" if bold else "/usr/share/fonts/liberation/LiberationMono-Regular.ttf",
            "/usr/share/fonts/Adwaita/AdwaitaMono-Bold.ttf" if bold else "/usr/share/fonts/Adwaita/AdwaitaMono-Regular.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/Adwaita/AdwaitaSans-Regular.ttf",
            "/usr/share/fonts/noto/NotoSans-Bold.ttf" if bold else "/usr/share/fonts/noto/NotoSans-Regular.ttf",
        ]

    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def draw_cyber_grid(draw: ImageDraw.ImageDraw, width: int, height: int, step: int = 80, color: tuple[int, int, int, int] = (20, 32, 52, 90)) -> None:
    for x in range(0, width, step):
        draw.line([(x, 0), (x, height)], fill=color, width=1)
    for y in range(0, height, step):
        draw.line([(0, y), (width, y)], fill=color, width=1)


def draw_glow_rect(
    base_img: Image.Image,
    box: list[int],
    radius: int = 16,
    fill: tuple[int, int, int, int] = C_CARD_BG,
    outline: tuple[int, int, int, int] = C_CARD_BORDER,
    width: int = 2,
    glow_color: tuple[int, int, int, int] = (0, 240, 255, 40),
) -> None:
    x0, y0, x1, y1 = box
    glow_pad = 12
    glow_layer = Image.new("RGBA", (x1 - x0 + glow_pad * 2, y1 - y0 + glow_pad * 2), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glow_layer)
    g_draw.rounded_rectangle([glow_pad, glow_pad, glow_layer.width - glow_pad, glow_layer.height - glow_pad], radius=radius, outline=glow_color, width=6)
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(6))
    base_img.paste(glow_layer, (x0 - glow_pad, y0 - glow_pad), glow_layer)

    draw = ImageDraw.Draw(base_img)
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill, outline=outline, width=width)


# ==============================================================================
# 1. GÉNÉRATEURS D'IMAGES
# ==============================================================================

def generate_deviantart_character_sheet(out_path: Path) -> Path:
    w, h = 3840, 2160
    img = Image.new("RGBA", (w, h), (8, 12, 22, 255))
    draw = ImageDraw.Draw(img)
    draw_cyber_grid(draw, w, h, step=100, color=(16, 26, 44, 110))

    for i in range(-5, 15):
        draw.line([(i * 400, 0), (i * 400 + 1200, h)], fill=(14, 22, 38, 50), width=2)

    draw_glow_rect(img, [120, 80, w - 120, 240], radius=16, fill=(12, 18, 32, 240), outline=C_CYAN_NEON, width=2)
    f_title = get_font(52, bold=True)
    f_sub = get_font(28, mono=True)
    draw.text((160, 110), "LIA 01 // NEURAL COMPANION // CHARACTER DESIGN & 3D TURNAROUND", fill=C_WHITE, font=f_title)
    draw.text((160, 180), "SPECIFICATION SHEET • VRM 1.0 HUMANOID ARMATURE • GODOT 4.6 & THREE-VRM RUNTIME • LBG STUDIOS", fill=C_CYAN_NEON, font=f_sub)

    neutral_p = COMPAGNON_DIR / "neutral.png"
    if neutral_p.exists():
        lia_full = Image.open(neutral_p).convert("RGBA")
        ratio = 1550 / lia_full.height
        new_w = int(lia_full.width * ratio)
        lia_full = lia_full.resize((new_w, 1550), Image.Resampling.LANCZOS)
        shadow = Image.new("RGBA", (new_w + 40, 1590), (0, 0, 0, 0))
        s_draw = ImageDraw.Draw(shadow)
        s_draw.ellipse([40, 1500, new_w, 1570], fill=(0, 0, 0, 180))
        shadow = shadow.filter(ImageFilter.GaussianBlur(15))
        img.paste(shadow, (700, 420), shadow)
        img.paste(lia_full, (720, 420), lia_full)

    explain_p = COMPAGNON_DIR / "explain.png"
    if explain_p.exists():
        lia_exp = Image.open(explain_p).convert("RGBA")
        ratio = 1250 / lia_exp.height
        new_w = int(lia_exp.width * ratio)
        lia_exp = lia_exp.resize((new_w, 1250), Image.Resampling.LANCZOS)
        img.paste(lia_exp, (200, 680), lia_exp)

    draw_glow_rect(img, [1800, 300, 3700, 1980], radius=24, fill=(11, 16, 28, 245), outline=C_CYAN_NEON, width=2)
    f_section = get_font(36, bold=True)
    draw.text((1850, 340), "FACIAL EXPRESSIONS & MORPH TARGETS", fill=C_WHITE, font=f_section)

    expressions = [
        ("joy.png", "JOIE / CONVIVIALITÉ", "Morph: Frown=0.0, Smile=1.0\nYeux cyan émissifs 480nm\nRéponse empathique"),
        ("think.png", "RÉFLEXION / COGNITION", "Morph: Brows_Inner=0.6\nAnalyse requête MiniMind\nCalcul d'inférence Q4"),
        ("talk_a.png", "PAROLE SYNCHRONISÉE", "Morph: Aa=0.85, Phonème A\nLip-sync RMS temps réel\nCadence 30.00 FPS"),
    ]

    for idx, (fname, title, desc) in enumerate(expressions):
        cx = 1860 + idx * 600
        cy = 430
        draw_glow_rect(img, [cx, cy, cx + 550, cy + 620], radius=16, fill=(16, 24, 40, 220), outline=C_MUTED, width=1)
        face_p = COMPAGNON_CLOSEUP_DIR / fname
        if face_p.exists():
            f_img = Image.open(face_p).convert("RGBA")
            f_img = f_img.resize((380, 380), Image.Resampling.LANCZOS)
            img.paste(f_img, (cx + 85, cy + 20), f_img)
        f_expr_title = get_font(24, bold=True)
        f_expr_desc = get_font(20, mono=True)
        draw.text((cx + 30, cy + 420), title, fill=C_CYAN_NEON, font=f_expr_title)
        draw.text((cx + 30, cy + 470), desc, fill=C_MUTED, font=f_expr_desc)

    draw_glow_rect(img, [1860, 1120, 2750, 1920], radius=18, fill=(14, 20, 34, 230), outline=C_AMBER_CANTINA, width=2)
    draw.text((1900, 1150), "HARDWARE & NEURAL SPECS", fill=C_AMBER_CANTINA, font=f_section)

    specs = [
        ("Modèle d'IA embarqué", "MiniMind 25M SFT (Inférence locale < 5 ms)"),
        ("Moteur Graphique", "Godot Engine 4.6 (Simulation) + Three-VRM"),
        ("Squelette 3D", "Humanoid standard 55 os + Spring bones"),
        ("Fréquence d'affichage", "30.00 FPS garantis déterministes"),
        ("Revêtement cutané", "Matcap PBR Cyber-Android (titane & polymère)"),
        ("Système d'autorité", "Headless Linux Debian 12 / Proxmox R720"),
        ("Coût d'infrastructure", "0.00 € Cloud (100% On-Premise LAN)"),
    ]
    f_spec_k = get_font(22, bold=True)
    f_spec_v = get_font(22, mono=True)
    for s_idx, (k, v) in enumerate(specs):
        sy = 1230 + s_idx * 90
        draw.text((1900, sy), f"• {k} :", fill=C_WHITE, font=f_spec_k)
        draw.text((1900, sy + 32), f"  {v}", fill=C_CYAN_NEON, font=f_spec_v)

    draw_glow_rect(img, [2800, 1120, 3650, 1500], radius=18, fill=(14, 20, 34, 230), outline=C_MUTED, width=1)
    draw.text((2840, 1150), "COLOR SCHEME PALETTE", fill=C_WHITE, font=f_section)

    swatches = [
        ("#00F0FF", "Neural Cyan", C_CYAN_NEON),
        ("#FF730D", "Cantina Amber", C_AMBER_CANTINA),
        ("#00FFA3", "Matrix Emerald", C_EMERALD),
        ("#D0D7DE", "Titanium Alloy", (208, 215, 222, 255)),
        ("#0A0E17", "Carbon Dark", (10, 14, 23, 255)),
    ]
    for p_idx, (hex_c, name_c, col) in enumerate(swatches):
        px = 2840 + p_idx * 155
        py = 1240
        draw.rounded_rectangle([px, py, px + 120, py + 120], radius=12, fill=col, outline=C_WHITE, width=2)
        f_swatch = get_font(18, mono=True, bold=True)
        draw.text((px, py + 140), hex_c, fill=C_WHITE, font=f_swatch)
        f_swatch_n = get_font(16)
        draw.text((px, py + 170), name_c, fill=C_MUTED, font=f_swatch_n)

    draw_glow_rect(img, [2800, 1540, 3650, 1920], radius=18, fill=(14, 20, 34, 230), outline=C_CYAN_NEON, width=1)
    f_repo_t = get_font(28, bold=True)
    f_repo_l = get_font(24, mono=True)
    draw.text((2840, 1580), "LBG STUDIOS // PROJET OPEN SOURCE", fill=C_WHITE, font=f_repo_t)
    draw.text((2840, 1640), "GitHub : https://github.com/Teome0245/LBG_Studios", fill=C_CYAN_NEON, font=f_repo_l)
    draw.text((2840, 1700), "YouTube : https://www.youtube.com/@lbg-p8k", fill=C_AMBER_CANTINA, font=f_repo_l)
    draw.text((2840, 1760), "DeviantArt : https://www.deviantart.com/teome245", fill=C_WHITE, font=f_repo_l)
    draw.text((2840, 1830), "Made with Godot Engine 4.6 • Three-VRM • Python • Blender", fill=C_MUTED, font=get_font(20))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG", optimize=True)
    return out_path


def generate_deviantart_lost_heaven_concept(out_path: Path) -> Path:
    w, h = 3840, 2160
    img = Image.new("RGBA", (w, h), (14, 18, 30, 255))
    draw = ImageDraw.Draw(img)

    for y in range(int(h * 0.7)):
        t = y / (h * 0.7)
        r = int(18 + t * 180)
        g = int(24 + t * 80)
        b = int(55 + (1 - t) * 60)
        draw.line([(0, y), (w, y)], fill=(r, g, b, 255), width=1)

    sun1_pos = (2800, 700)
    sun1_r = 180
    for sr in range(sun1_r + 40, sun1_r - 1, -1):
        alpha = int(80 * (1 - (sr - sun1_r) / 40)) if sr > sun1_r else 240
        draw.ellipse([sun1_pos[0] - sr, sun1_pos[1] - sr, sun1_pos[0] + sr, sun1_pos[1] + sr], fill=(255, 180, 50, alpha))

    sun2_pos = (3150, 850)
    sun2_r = 110
    for sr in range(sun2_r + 30, sun2_r - 1, -1):
        alpha = int(70 * (1 - (sr - sun2_r) / 30)) if sr > sun2_r else 230
        draw.ellipse([sun2_pos[0] - sr, sun2_pos[1] - sr, sun2_pos[0] + sr, sun2_pos[1] + sr], fill=(255, 100, 30, alpha))

    dune_layers = [
        (int(h * 0.58), (90, 40, 20, 255), 350, 0.0012),
        (int(h * 0.65), (60, 25, 15, 255), 450, 0.0018),
        (int(h * 0.72), (35, 15, 12, 255), 550, 0.0025),
        (int(h * 0.80), (18, 12, 18, 255), 650, 0.0035),
    ]
    for base_y, col, amp, freq in dune_layers:
        points = [(0, h)]
        for x in range(0, w + 10, 40):
            dy = int(math.sin(x * freq) * amp * 0.5 + math.cos(x * freq * 0.5) * amp * 0.3)
            points.append((x, base_y + dy))
        points.append((w, h))
        draw.polygon(points, fill=col)

    vap_x = 900
    vap_base_y = 1850
    draw.polygon([(vap_x - 140, vap_base_y), (vap_x + 140, vap_base_y), (vap_x + 90, vap_base_y - 250), (vap_x - 90, vap_base_y - 250)], fill=(25, 28, 36, 255))
    draw.rectangle([vap_x - 45, vap_base_y - 1200, vap_x + 45, vap_base_y - 250], fill=(30, 34, 44, 255))
    for fin_y in range(vap_base_y - 1100, vap_base_y - 350, 90):
        draw.polygon([(vap_x - 180, fin_y + 30), (vap_x + 180, fin_y + 30), (vap_x + 120, fin_y), (vap_x - 120, fin_y)], fill=(40, 46, 58, 255))
    draw.ellipse([vap_x - 80, vap_base_y - 1300, vap_x + 80, vap_base_y - 1180], fill=(45, 52, 65, 255))
    draw.line([(vap_x, vap_base_y - 1300), (vap_x, vap_base_y - 1420)], fill=(120, 140, 160, 255), width=6)
    draw.ellipse([vap_x - 12, vap_base_y - 800, vap_x + 12, vap_base_y - 776], fill=C_CYAN_NEON)

    cantina_x = 2100
    cantina_base_y = 1680
    draw.rounded_rectangle([cantina_x, cantina_base_y - 320, cantina_x + 450, cantina_base_y], radius=30, fill=(20, 16, 22, 255), outline=C_AMBER_CANTINA, width=8)
    draw.rectangle([cantina_x + 120, cantina_base_y - 240, cantina_x + 330, cantina_base_y], fill=(255, 140, 20, 230))
    f_cantina = get_font(32, bold=True)
    draw.text((cantina_x + 80, cantina_base_y - 380), "CANTINA LA PERLE", fill=C_AMBER_CANTINA, font=f_cantina)

    think_p = COMPAGNON_DIR / "think.png"
    if think_p.exists():
        lia_t = Image.open(think_p).convert("RGBA")
        ratio = 1100 / lia_t.height
        new_w = int(lia_t.width * ratio)
        lia_t = lia_t.resize((new_w, 1100), Image.Resampling.LANCZOS)
        img.paste(lia_t, (180, 1050), lia_t)

    draw_glow_rect(img, [120, 80, 1500, 280], radius=16, fill=(10, 14, 24, 230), outline=C_CYAN_NEON, width=2)
    f_title = get_font(48, bold=True)
    f_sub = get_font(24, mono=True)
    draw.text((160, 110), "LOST HEAVEN OUTPOST // SECTOR 04", fill=C_WHITE, font=f_title)
    draw.text((160, 180), "ATMOSPHERIC HUMIDITY: 0.08% • CONDENSATION YIELD: 42L/H • 60 TPS LIVE", fill=C_CYAN_NEON, font=f_sub)
    draw.text((160, 220), "STAR WARS GALAXIES SPIRITUAL SUCCESSOR • GODOT 4.6 PERSISTENT WORLD", fill=C_MUTED, font=f_sub)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG", optimize=True)
    return out_path


def generate_pinterest_mmo_architecture(out_path: Path) -> Path:
    w, h = 1080, 1620
    img = Image.new("RGBA", (w, h), (10, 14, 26, 255))
    draw = ImageDraw.Draw(img)
    draw_cyber_grid(draw, w, h, step=60, color=(16, 24, 40, 100))

    draw_glow_rect(img, [60, 60, w - 60, 280], radius=20, fill=(14, 20, 36, 245), outline=C_CYAN_NEON, width=2)
    draw.rounded_rectangle([90, 85, 450, 125], radius=10, fill=C_CYAN_NEON)
    f_badge = get_font(20, bold=True, mono=True)
    draw.text((110, 93), "ARCHITECTURE MMO INDÉ", fill=(10, 14, 24, 255), font=f_badge)

    f_title = get_font(42, bold=True)
    f_sub = get_font(24)
    draw.text((90, 145), "0€ DE FRAIS SERVEUR", fill=C_WHITE, font=f_title)
    draw.text((90, 210), "Comment héberger un monde 3D sans abonnement Cloud", fill=C_MUTED, font=f_sub)

    pillars = [
        ("1. GODOT 4.6 HEADLESS (60 TPS)", "Moteur physique déterministe, NavigationServer3D natif.\nConsomme seulement 85 Mo de RAM par instance.", C_CYAN_NEON),
        ("2. PERSISTANCE SQLITE WAL", "Écriture instantanée en Write-Ahead Log.\nZéro latence réseau, zéro coût de base managée.", C_AMBER_CANTINA),
        ("3. AGENTS PNJ MINIMIND 25M", "Micro-modèle neuronal local ultra-optimisé.\nInférence CPU 56 tok/s sans GPU coûteux.", C_EMERALD),
    ]

    for idx, (p_title, p_desc, p_col) in enumerate(pillars):
        cy0 = 320 + idx * 230
        cy1 = cy0 + 195
        draw_glow_rect(img, [60, cy0, 680, cy1], radius=16, fill=(16, 24, 44, 235), outline=p_col, width=2)
        f_pt = get_font(26, bold=True)
        f_pd = get_font(20)
        draw.text((90, cy0 + 25), p_title, fill=p_col, font=f_pt)
        draw.text((90, cy0 + 75), p_desc, fill=C_WHITE, font=f_pd)

    point_p = COMPAGNON_DIR / "point.png"
    if point_p.exists():
        lia_pt = Image.open(point_p).convert("RGBA")
        ratio = 1100 / lia_pt.height
        new_w = int(lia_pt.width * ratio)
        lia_pt = lia_pt.resize((new_w, 1100), Image.Resampling.LANCZOS)
        img.paste(lia_pt, (500, 340), lia_pt)

    draw_glow_rect(img, [60, 1050, w - 60, 1340], radius=18, fill=(12, 18, 32, 245), outline=C_MUTED, width=1)
    f_stat_h = get_font(24, bold=True)
    draw.text((90, 1075), "MÉTRIQUES DE PRODUCTION RÉELLES :", fill=C_WHITE, font=f_stat_h)

    stats = [
        ("Joueurs & PNJ simultanés", "36 PNJ autonomes + bots de test"),
        ("Uptime serveur continu", "88+ heures sans fuite mémoire"),
        ("Facture mensuelle AWS/GCP", "0.00 € / mois (serveur reconditionné)"),
    ]
    f_sk = get_font(22, bold=True)
    f_sv = get_font(22, mono=True)
    for s_idx, (k, v) in enumerate(stats):
        sy = 1130 + s_idx * 60
        draw.text((90, sy), f"✔ {k} :", fill=C_MUTED, font=f_sk)
        draw.text((520, sy), v, fill=C_CYAN_NEON, font=f_sv)

    cta_box = [60, 1380, w - 60, 1540]
    draw.rounded_rectangle(cta_box, radius=24, fill=C_CYAN_NEON)
    f_cta_main = get_font(32, bold=True)
    f_cta_sub = get_font(22, mono=True)
    draw.text((120, 1415), "LIRE LE CODE SUR GITHUB ➜", fill=(10, 14, 24, 255), font=f_cta_main)
    draw.text((120, 1475), "github.com/Teome0245/LBG_Studios", fill=(10, 14, 24, 220), font=f_cta_sub)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG", optimize=True)
    return out_path


def generate_pinterest_vrm_companion(out_path: Path) -> Path:
    w, h = 1080, 1620
    img = Image.new("RGBA", (w, h), (10, 14, 26, 255))
    draw = ImageDraw.Draw(img)
    draw_cyber_grid(draw, w, h, step=60, color=(16, 24, 40, 100))

    draw_glow_rect(img, [60, 60, w - 60, 280], radius=20, fill=(14, 20, 36, 245), outline=C_CYAN_NEON, width=2)
    draw.rounded_rectangle([90, 85, 420, 125], radius=10, fill=C_AMBER_CANTINA)
    f_badge = get_font(20, bold=True, mono=True)
    draw.text((110, 93), "TUTORIEL VRM & 3D WEBGL", fill=(10, 14, 24, 255), font=f_badge)

    f_title = get_font(40, bold=True)
    f_sub = get_font(24)
    draw.text((90, 145), "AVATAR 3D INTERACTIF", fill=C_WHITE, font=f_title)
    draw.text((90, 210), "Animations faciales, Lip-sync & Inférence IA en direct", fill=C_CYAN_NEON, font=f_sub)

    cards = [
        ("joy.png", "JOIE", "Bouche souriante, yeux pétillants"),
        ("think.png", "RÉFLEXION", "Posture attentive, analyse NLP"),
        ("talk_o.png", "PHONÈME O", "Lip-sync audio temps réel"),
        ("explain.png", "EXPLICATION", "Gestuelle mains ouvertes"),
    ]

    for idx, (img_name, title, desc) in enumerate(cards):
        col = idx % 2
        row = idx // 2
        x0 = 60 + col * 490
        y0 = 310 + row * 410
        x1 = x0 + 470
        y1 = y0 + 390
        draw_glow_rect(img, [x0, y0, x1, y1], radius=16, fill=(16, 24, 44, 235), outline=C_CYAN_NEON, width=1)

        face_p = COMPAGNON_MEDIUM_DIR / img_name
        if not face_p.exists():
            face_p = COMPAGNON_DIR / img_name
        if face_p.exists():
            f_img = Image.open(face_p).convert("RGBA")
            f_img = f_img.resize((260, 260), Image.Resampling.LANCZOS)
            img.paste(f_img, (x0 + 105, y0 + 15), f_img)

        f_t = get_font(24, bold=True)
        f_d = get_font(18)
        draw.text((x0 + 30, y0 + 290), title, fill=C_AMBER_CANTINA, font=f_t)
        draw.text((x0 + 30, y0 + 330), desc, fill=C_WHITE, font=f_d)

    draw_glow_rect(img, [60, 1160, w - 60, 1340], radius=18, fill=(12, 18, 32, 245), outline=C_MUTED, width=1)
    f_tech = get_font(22, mono=True)
    draw.text((90, 1190), "• Format Standardisé : VRM 1.0 (GLTF 2.0)", fill=C_WHITE, font=f_tech)
    draw.text((90, 1240), "• Rendu Déterministe : Three.js + WebSocket", fill=C_CYAN_NEON, font=f_tech)
    draw.text((90, 1290), "• Lip-sync : Analyse RMS des phonèmes audio", fill=C_AMBER_CANTINA, font=f_tech)

    cta_box = [60, 1380, w - 60, 1540]
    draw.rounded_rectangle(cta_box, radius=24, fill=C_AMBER_CANTINA)
    f_cta_main = get_font(32, bold=True)
    f_cta_sub = get_font(22, mono=True)
    draw.text((120, 1415), "TÉLÉCHARGER LE CODE & MODÈLE ➜", fill=(10, 14, 24, 255), font=f_cta_main)
    draw.text((120, 1475), "github.com/Teome0245/LBG_Studios", fill=(10, 14, 24, 220), font=f_cta_sub)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG", optimize=True)
    return out_path


# ==============================================================================
# 2. PARSING COOKIES & PLAYWRIGHT UPLOADERS
# ==============================================================================

def _parse_netscape_cookies(cookie_file: Path) -> list[dict[str, Any]]:
    cookies = []
    if not cookie_file.exists():
        return cookies

    with open(cookie_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) >= 7:
                domain, flag, path, secure, expires, name, value = parts[:7]
                cookie_dict: dict[str, Any] = {
                    "name": name,
                    "value": value,
                    "domain": domain,
                    "path": path,
                    "secure": secure.upper() == "TRUE",
                }
                try:
                    exp_ts = int(expires)
                    if exp_ts > 0:
                        cookie_dict["expires"] = exp_ts
                except ValueError:
                    pass
                cookies.append(cookie_dict)
    return cookies


def upload_deviantart_native(
    image_path: Path,
    title: str,
    description: str,
    tags: list[str],
    cookie_file: Path = DEVIANTART_COOKIES,
    headless: bool = True,
) -> dict[str, Any]:
    """Publie une création sur DeviantArt via Playwright."""
    if not image_path.exists():
        return {"status": "error", "error": f"Image introuvable : {image_path}"}

    cookies = _parse_netscape_cookies(cookie_file)
    if not cookies:
        return {"status": "needs_auth", "error": f"Fichier de cookies absent : {cookie_file}"}

    logger.info("Démarrage Playwright pour upload DeviantArt : %s", image_path.name)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, args=["--no-sandbox", "--disable-dev-shm-usage"])
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        )
        context.add_cookies(cookies)
        page = context.new_page()

        try:
            logger.info("Navigation vers DeviantArt Submit...")
            page.goto("https://www.deviantart.com/submit/", wait_until="domcontentloaded", timeout=45000)
            time.sleep(4)

            # Vérification de connexion
            if "login" in page.url.lower():
                return {"status": "needs_auth", "error": "Session DeviantArt expirée ou invalide"}

            # Injection du fichier image
            file_input = page.locator("input[type='file']").first
            if file_input.count() > 0:
                file_input.set_input_files(str(image_path.resolve()))
                logger.info("Image injectée dans DeviantArt, attente du traitement...")
                time.sleep(6)
            else:
                return {"status": "error", "error": "Sélecteur d'upload file introuvable sur DeviantArt"}

            # Remplissage du Titre
            title_input = page.locator("input[placeholder*='title' i], input[data-testid='title-input']").first
            if title_input.count() > 0:
                title_input.fill(title)

            # Remplissage de la Description
            desc_area = page.locator("div[contenteditable='true'], textarea[placeholder*='description' i]").first
            if desc_area.count() > 0:
                desc_area.fill(description)

            # Tags
            tag_input = page.locator("input[placeholder*='tag' i]").first
            if tag_input.count() > 0:
                for t in tags[:10]:
                    tag_input.fill(t)
                    tag_input.press("Enter")
                    time.sleep(0.3)

            # Clic sur Publier
            submit_btn = page.locator("button:has-text('Submit Now'), button:has-text('Publish')").first
            if submit_btn.count() > 0:
                logger.info("Clic sur 'Submit Now' DeviantArt...")
                submit_btn.click()
                time.sleep(6)
                return {"status": "success", "platform": "deviantart", "image": str(image_path)}
            else:
                logger.warning("Bouton Submit non détecté, formulaire prérempli.")
                return {"status": "staged", "platform": "deviantart", "image": str(image_path)}

        except Exception as e:
            logger.exception("Erreur upload DeviantArt : %s", e)
            return {"status": "error", "error": str(e)}
        finally:
            browser.close()


def upload_pinterest_native(
    image_path: Path,
    title: str,
    description: str,
    destination_url: str,
    board_name: str,
    cookie_file: Path = PINTEREST_COOKIES,
    headless: bool = True,
) -> dict[str, Any]:
    """Publie une épingle sur Pinterest via Playwright."""
    if not image_path.exists():
        return {"status": "error", "error": f"Image introuvable : {image_path}"}

    cookies = _parse_netscape_cookies(cookie_file)
    if not cookies:
        return {"status": "needs_auth", "error": f"Fichier de cookies absent : {cookie_file}"}

    logger.info("Démarrage Playwright pour upload Pinterest : %s", image_path.name)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, args=["--no-sandbox", "--disable-dev-shm-usage"])
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        )
        context.add_cookies(cookies)
        page = context.new_page()

        try:
            logger.info("Navigation vers Pinterest Pin Creation...")
            page.goto("https://www.pinterest.com/pin-creation-tool/", wait_until="domcontentloaded", timeout=45000)
            time.sleep(4)

            if "login" in page.url.lower():
                return {"status": "needs_auth", "error": "Session Pinterest expirée ou invalide"}

            # Injection du fichier image
            file_input = page.locator("input[type='file']").first
            if file_input.count() > 0:
                file_input.set_input_files(str(image_path.resolve()))
                logger.info("Image injectée dans Pinterest, attente...")
                time.sleep(5)
            else:
                return {"status": "error", "error": "Sélecteur d'upload file introuvable sur Pinterest"}

            # Remplissage Titre
            title_input = page.locator("input[id*='storyboard-selector-title'], input[placeholder*='titre' i], input[placeholder*='title' i]").first
            if title_input.count() > 0:
                title_input.fill(title)

            # Remplissage Description
            desc_area = page.locator("div[contenteditable='true'], textarea[placeholder*='description' i]").first
            if desc_area.count() > 0:
                desc_area.fill(description)

            # Remplissage Lien de destination
            link_input = page.locator("input[placeholder*='lien' i], input[placeholder*='link' i]").first
            if link_input.count() > 0:
                link_input.fill(destination_url)

            # Clic Publier
            pub_btn = page.locator("button:has-text('Publier'), button:has-text('Publish')").first
            if pub_btn.count() > 0:
                logger.info("Clic sur 'Publier' Pinterest...")
                pub_btn.click()
                time.sleep(6)
                return {"status": "success", "platform": "pinterest", "image": str(image_path)}
            else:
                return {"status": "staged", "platform": "pinterest", "image": str(image_path)}

        except Exception as e:
            logger.exception("Erreur upload Pinterest : %s", e)
            return {"status": "error", "error": str(e)}
        finally:
            browser.close()


# ==============================================================================
# 3. MÉTADONNÉES & CLI
# ==============================================================================

def generate_metadata_and_guide() -> None:
    metadata = {
        "deviantart": [
            {
                "file": "01_lia_character_sheet_4k.png",
                "title": "Lia 01 - Cybernetic Android Companion Character Sheet [LBG Studios]",
                "category": "Digital Art > Concept Art > Character Design",
                "tags": [
                    "godotengine",
                    "vrm",
                    "characterdesign",
                    "cyberpunk",
                    "conceptart",
                    "3dart",
                    "blender",
                    "threejs",
                    "indiegamedev",
                    "android",
                    "scifi",
                ],
                "description": (
                    "Complete character turnaround and technical specification sheet for Lia (Unit LIA-01), "
                    "the neural AI companion of the open-source MMO project developed by LBG Studios.\n\n"
                    "• Engine: Godot 4.6 & Three-VRM\n"
                    "• Armature: Standard VRM Humanoid 1.0 with spring bones hair dynamics\n"
                    "• Cognitive Engine: MiniMind 25M edge neural SFT running locally\n"
                    "• Shading: PBR Cybernetic skin with cyan emissive ocular matrix (480nm)\n\n"
                    "🔗 Open-Source Repository: https://github.com/Teome0245/LBG_Studios\n"
                    "📺 Video Devlogs: https://www.youtube.com/@lbg-p8k\n\n"
                    "Made with Blender, Godot Engine and Python."
                ),
            },
            {
                "file": "02_lost_heaven_concept_4k.png",
                "title": "Lost Heaven Outpost - Desert Vaporators & Cantina Concept Art",
                "category": "Digital Art > Concept Art > Environments",
                "tags": [
                    "starwarsgalaxies",
                    "conceptart",
                    "environmentart",
                    "scifi",
                    "desert",
                    "godot4",
                    "mmorpg",
                    "tatooine",
                    "gamedev",
                    "cyberpunk",
                ],
                "description": (
                    "Atmospheric sci-fi concept art of the Lost Heaven outpost, located in the Scrapaltai desert basin. "
                    "Inspired by the rugged frontier of Star Wars Galaxies (SWG) and the cybernetic dust of Gunnm.\n\n"
                    "Featuring the massive GX-8 moisture vaporator with thermoelectric refrigeration coils, "
                    "the amber neon arch of the Cantina 'La Perle', and the twin suns twilight horizon.\n\n"
                    "• Simulation: Godot 4.6 headless server on LAN\n"
                    "• Open-source codebase: https://github.com/Teome0245/LBG_Studios\n"
                    "• YouTube Channel: https://www.youtube.com/@lbg-p8k"
                ),
            },
        ],
        "pinterest": [
            {
                "file": "01_mmo_architecture_0euro_pin.png",
                "title": "Comment faire tourner un MMO avec 0€ de frais de serveur ? (Godot 4 + SQLite WAL)",
                "board": "Game Development & Architecture",
                "destination_url": "https://github.com/Teome0245/LBG_Studios",
                "description": (
                    "Découvrez comment héberger un monde MMO 3D persistant sans payer le moindre centime d'abonnement cloud AWS ou GCP. "
                    "Architecture complète : serveur headless Godot 4.6 (60 TPS déterministes, 85 Mo de RAM), persistance locale en SQLite WAL, "
                    "et agents PNJ autonomes propulsés par un micro-modèle IA MiniMind 25M. Code source 100% open-source sur GitHub !"
                ),
                "keywords": ["game dev", "godot engine", "mmo", "architecture logicielle", "python", "indie game", "serveur de jeu"],
            },
            {
                "file": "02_vrm_companion_avatar_pin.png",
                "title": "Créer un Avatar 3D VRM interactif en Python & Three-VRM (Tutoriel Game Dev)",
                "board": "3D Character Design & VRM",
                "destination_url": "https://github.com/Teome0245/LBG_Studios",
                "description": (
                    "Tutoriel complet pour intégrer un avatar 3D humanoïde au format VRM dans une application WebGL ou un jeu vidéo. "
                    "Gestion des morph targets émotionnels (joie, réflexion, parole), synchronisation labiale (lip-sync RMS) "
                    "et pilotage en direct via FastAPI et des LLM locaux. Téléchargez le modèle et les scripts sur notre dépôt GitHub."
                ),
                "keywords": ["vrm", "avatar 3d", "threejs", "blender", "character design", "python", "tutoriel dev"],
            },
        ],
    }

    meta_path = OUTPUT_DIR / "METADATA.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)


def run_generation() -> None:
    logger.info("=== Génération des Art Packs DeviantArt & Pinterest ===")
    DEVIANTART_DIR.mkdir(parents=True, exist_ok=True)
    PINTEREST_DIR.mkdir(parents=True, exist_ok=True)

    generate_deviantart_character_sheet(DEVIANTART_DIR / "01_lia_character_sheet_4k.png")
    generate_deviantart_lost_heaven_concept(DEVIANTART_DIR / "02_lost_heaven_concept_4k.png")
    generate_pinterest_mmo_architecture(PINTEREST_DIR / "01_mmo_architecture_0euro_pin.png")
    generate_pinterest_vrm_companion(PINTEREST_DIR / "02_vrm_companion_avatar_pin.png")
    generate_metadata_and_guide()
    logger.info("Génération terminée avec succès.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Art Publisher — DeviantArt & Pinterest Automation")
    parser.add_argument("--generate", action="store_true", help="Génère tous les visuels 4K et verticaux")
    parser.add_argument("--deviantart", action="store_true", help="Publie sur DeviantArt")
    parser.add_argument("--pinterest", action="store_true", help="Publie sur Pinterest")
    parser.add_argument("--all", action="store_true", help="Génère et publie sur toutes les plateformes")
    args = parser.parse_args()

    if args.generate or args.all or len(sys.argv) == 1:
        run_generation()

    meta_file = OUTPUT_DIR / "METADATA.json"
    if not meta_file.exists():
        generate_metadata_and_guide()

    with open(meta_file, "r", encoding="utf-8") as f:
        meta = json.load(f)

    if args.deviantart or args.all:
        for da_item in meta.get("deviantart", []):
            img_p = DEVIANTART_DIR / da_item["file"]
            res = upload_deviantart_native(img_p, da_item["title"], da_item["description"], da_item["tags"])
            print("DeviantArt Result:", json.dumps(res, indent=2))

    if args.pinterest or args.all:
        for pin_item in meta.get("pinterest", []):
            img_p = PINTEREST_DIR / pin_item["file"]
            res = upload_pinterest_native(img_p, pin_item["title"], pin_item["description"], pin_item["destination_url"], pin_item["board"])
            print("Pinterest Result:", json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
