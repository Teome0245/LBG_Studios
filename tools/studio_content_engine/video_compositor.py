"""video_compositor.py — Compositeur vidéo 9:16 (1080x1920) pour TikTok / Shorts.

- Pipeline fluide à 30 FPS :
  - Fond Cyberpunk Sci-Fi dynamique avec grille perspective.
  - Avatar 3D (Mia / Lyra) animé en synchronisation labiale sur l'enveloppe RMS audio.
  - Clignements d'yeux procéduraux et micro-mouvements de respiration.
  - Égaliseur / spectre audio néon réagissant en temps réel.
  - En-tête LBG Studios avec badges 100% Local.
  - Sous-titres dynamiques TikTok incrustés via libass.
"""

from __future__ import annotations

import logging
import math
import os
import subprocess
import wave
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

WIDTH = 1080
HEIGHT = 1920
FPS = 30


def load_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Tente de charger une police TTF système moderne, avec fallback standard."""
    font_candidates = [
        "/usr/share/fonts/liberation/LiberationSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/noto/NotoSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    ]
    for p in font_candidates:
        if os.path.isfile(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def get_audio_rms_series(wav_path: Path, fps: int = FPS) -> tuple[np.ndarray, float]:
    """Calcule l'amplitude RMS par frame vidéo à partir du fichier WAV."""
    with wave.open(str(wav_path), "rb") as wf:
        n_frames = wf.getnframes()
        sample_rate = wf.getframerate()
        raw_bytes = wf.readframes(n_frames)

    duration = float(n_frames) / float(sample_rate)
    samples = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0

    total_video_frames = int(math.ceil(duration * fps))
    rms_series = np.zeros(total_video_frames, dtype=np.float32)

    samples_per_frame = sample_rate / fps
    window_samples = int(sample_rate * 0.08)  # fenêtre d'analyse 80ms

    for f_idx in range(total_video_frames):
        center_sample = int(f_idx * samples_per_frame)
        start_s = max(0, center_sample - window_samples // 2)
        end_s = min(len(samples), center_sample + window_samples // 2)
        if end_s > start_s:
            chunk = samples[start_s:end_s]
            rms = np.sqrt(np.mean(chunk**2))
            rms_series[f_idx] = rms

    # Normalisation douce
    max_rms = np.max(rms_series) if len(rms_series) > 0 else 1.0
    if max_rms > 0.01:
        rms_series = np.clip(rms_series / max_rms, 0.0, 1.0)

    return rms_series, duration


def create_dynamic_background(t: float, w: int = WIDTH, h: int = HEIGHT) -> Image.Image:
    """Génère le fond cyberpunk animé avec défilement perspective et particules."""
    bg = Image.new("RGBA", (w, h), (10, 15, 26, 255))
    draw = ImageDraw.Draw(bg)

    # Dégradé vertical sombre
    for y in range(0, h, 8):
        ratio = y / h
        r = int(7 + ratio * 12)
        g = int(11 + ratio * 18)
        b = int(22 + ratio * 32)
        draw.rectangle([0, y, w, y + 8], fill=(r, g, b, 255))

    # Grille perspective au sol DYNAMIQUE qui défile vers l'avant à 30 FPS
    grid_color = (0, 245, 212, 42)
    horizon_y = 1180
    speed_offset = (t * 2.2) % 1.0

    # Lignes horizontales en perspective quadratique
    num_grid_lines = 16
    for k in range(num_grid_lines):
        norm_k = (k + speed_offset) / num_grid_lines
        gy = int(horizon_y + (h - horizon_y) * (norm_k ** 2))
        if horizon_y <= gy < h:
            draw.line([(0, gy), (w, gy)], fill=grid_color, width=1)

    # Lignes fuyantes vers l'horizon
    vanishing_x = w // 2
    for vx in range(-400, w + 450, 110):
        draw.line([(vanishing_x, horizon_y - 200), (vx, h)], fill=grid_color, width=1)

    # Particules d'ambiance néon montantes (effet poussière / embers)
    for p_i in range(24):
        p_x = int((p_i * 47 + math.sin(t * 1.5 + p_i) * 35) % w)
        p_y = int((h - ((t * 65 + p_i * 85) % h)))
        p_size = (p_i % 3) + 2
        p_alpha = int(100 + math.sin(t * 3.0 + p_i) * 60)
        p_col = (0, 245, 212, p_alpha) if p_i % 2 == 0 else (255, 0, 128, p_alpha)
        draw.ellipse([p_x, p_y, p_x + p_size, p_y + p_size], fill=p_col)

    # Halo lumineux central pulsant derrière l'avatar
    halo_pulse = math.sin(t * 2.2) * 0.12 + 0.88
    halo = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    halo_draw = ImageDraw.Draw(halo)
    for radius in range(360, 60, -35):
        r_dyn = int(radius * halo_pulse)
        alpha = int((360 - radius) / 360 * 28)
        bbox = [w // 2 - r_dyn, 820 - r_dyn, w // 2 + r_dyn, 820 + r_dyn]
        halo_draw.ellipse(bbox, fill=(0, 245, 212, alpha))

    bg = Image.alpha_composite(bg, halo)
    return bg


def draw_tech_card(
    draw: ImageDraw.ImageDraw,
    card_type: str,
    t: float,
    rms: float,
    fonts: dict[str, Any],
) -> None:
    """Dessine une carte d'information technologique stylisée à côté de l'avatar."""
    f_title = fonts["card_title"]
    f_body = fonts["card_body"]
    f_badge = fonts["card_badge"]

    x0, y0, x1, y1 = 520, 440, 1020, 920

    if card_type == "alert":
        # CARTE PROBLÈME : Alerte Cloud & Explosion des coûts
        draw.rounded_rectangle([x0, y0, x1, y1], radius=20, fill=(38, 12, 16, 230), outline=(255, 60, 60, 240), width=3)
        # Header
        draw.rounded_rectangle([x0 + 15, y0 + 15, x1 - 15, y0 + 75], radius=10, fill=(255, 60, 60, 40), outline=(255, 80, 80, 200), width=2)
        draw.text((x0 + 35, y0 + 26), "🚨  PIÈGE DES API CLOUD", fill=(255, 90, 90, 255), font=f_title)

        # Bullets
        bullets = [
            ("• Factures tokens imprévisibles", (255, 220, 220, 255)),
            ("• Latence réseau variable (>600ms)", (255, 180, 180, 255)),
            ("• Dépendance et lock-in externe", (255, 180, 180, 255)),
            ("• Confidentialité des données 0%", (255, 140, 140, 255)),
        ]
        cur_y = y0 + 95
        for b_text, b_col in bullets:
            draw.text((x0 + 30, cur_y), b_text, fill=b_col, font=f_body)
            cur_y += 42

        # Jauge rouge d'alerte coût
        draw.text((x0 + 30, cur_y + 10), "COÛT MENSUEL ESTIMÉ :", fill=(255, 100, 100, 255), font=f_badge)
        draw.rounded_rectangle([x0 + 30, cur_y + 45, x1 - 30, cur_y + 80], radius=8, fill=(60, 20, 20, 255), outline=(255, 60, 60, 180), width=2)
        pulse_w = int((x1 - x0 - 64) * (0.85 + math.sin(t * 6.0) * 0.1))
        draw.rounded_rectangle([x0 + 32, cur_y + 47, x0 + 32 + pulse_w, cur_y + 78], radius=6, fill=(255, 40, 40, 255))
        draw.text((x0 + 70, cur_y + 50), "+450 € / MOIS  📈", fill=(255, 255, 255, 255), font=f_badge)

    elif card_type == "stack":
        # CARTE SOLUTION : Architecture 100% Locale
        draw.rounded_rectangle([x0, y0, x1, y1], radius=20, fill=(10, 30, 38, 230), outline=(0, 245, 212, 240), width=3)
        # Header
        draw.rounded_rectangle([x0 + 15, y0 + 15, x1 - 15, y0 + 75], radius=10, fill=(0, 245, 212, 40), outline=(0, 245, 212, 200), width=2)
        draw.text((x0 + 30, y0 + 26), "⚡  STACK 100% LOCALE", fill=(0, 245, 212, 255), font=f_title)

        # 4 Tags technologiques néon
        tags = [
            ("🎮  Godot 4.6 Headless (60 FPS)", (0, 245, 212, 40), (0, 245, 212, 220), (200, 255, 245, 255)),
            ("🧠  Ollama Local (RTX 3060)", (255, 0, 180, 40), (255, 0, 180, 220), (255, 210, 240, 255)),
            ("🗣️  Piper TTS ONNX (30ms)", (0, 245, 212, 40), (0, 245, 212, 220), (200, 255, 245, 255)),
            ("💾  SQLite WAL + WebSockets", (50, 255, 140, 40), (50, 255, 140, 220), (210, 255, 220, 255)),
        ]
        cur_y = y0 + 95
        for tag_text, tag_fill, tag_out, tag_col in tags:
            draw.rounded_rectangle([x0 + 25, cur_y, x1 - 25, cur_y + 48], radius=8, fill=tag_fill, outline=tag_out, width=2)
            draw.text((x0 + 40, cur_y + 10), tag_text, fill=tag_col, font=f_badge)
            cur_y += 62

        # Badge bas
        draw.rounded_rectangle([x0 + 25, cur_y + 8, x1 - 25, cur_y + 54], radius=8, fill=(0, 245, 212, 20), outline=(0, 245, 212, 140), width=1)
        draw.text((x0 + 55, cur_y + 18), "FACTURE CLOUD : 0.00 €  🟢", fill=(0, 245, 212, 255), font=f_badge)

    elif card_type == "metrics":
        # CARTE BENCHMARKS : Performances réelles
        draw.rounded_rectangle([x0, y0, x1, y1], radius=20, fill=(12, 34, 22, 230), outline=(50, 255, 140, 240), width=3)
        # Header
        draw.rounded_rectangle([x0 + 15, y0 + 15, x1 - 15, y0 + 75], radius=10, fill=(50, 255, 140, 40), outline=(50, 255, 140, 200), width=2)
        draw.text((x0 + 25, y0 + 26), "📊  BENCHMARKS EN DIRECT", fill=(50, 255, 140, 255), font=f_title)

        cur_y = y0 + 95
        # Métrique 1 : Ticks serveur
        draw.text((x0 + 30, cur_y), "CADENCE SERVEUR : 60 TICKS/S", fill=(210, 255, 220, 255), font=f_badge)
        draw.rounded_rectangle([x0 + 30, cur_y + 35, x1 - 30, cur_y + 60], radius=6, fill=(20, 50, 30, 255), outline=(50, 255, 140, 180), width=1)
        draw.rounded_rectangle([x0 + 32, cur_y + 37, x1 - 32, cur_y + 58], radius=4, fill=(50, 255, 140, 255))
        draw.text((x1 - 110, cur_y + 36), "100%", fill=(10, 30, 15, 255), font=f_badge)

        # Métrique 2 : RAM
        cur_y += 85
        draw.text((x0 + 30, cur_y), "RAM UTILISÉE : 1.2 GB / 16 GB", fill=(200, 245, 255, 255), font=f_badge)
        draw.rounded_rectangle([x0 + 30, cur_y + 35, x1 - 30, cur_y + 60], radius=6, fill=(15, 35, 45, 255), outline=(0, 245, 212, 180), width=1)
        ram_w = int((x1 - x0 - 64) * 0.15)
        draw.rounded_rectangle([x0 + 32, cur_y + 37, x0 + 32 + ram_w, cur_y + 58], radius=4, fill=(0, 245, 212, 255))
        draw.text((x0 + 45 + ram_w, cur_y + 36), "9.3%", fill=(0, 245, 212, 255), font=f_badge)

        # Métrique 3 : Coût
        cur_y += 85
        draw.text((x0 + 30, cur_y), "DÉPENSE EXTERNE : 0.00 €", fill=(255, 255, 255, 255), font=f_badge)
        draw.rounded_rectangle([x0 + 30, cur_y + 35, x1 - 30, cur_y + 70], radius=8, fill=(50, 255, 140, 30), outline=(50, 255, 140, 220), width=2)
        draw.text((x0 + 65, cur_y + 40), "AUCUN ABONNEMENT  ✅", fill=(50, 255, 140, 255), font=f_title)

    elif card_type == "outro":
        # CARTE OUTRO : GitHub LBG Studios
        draw.rounded_rectangle([x0, y0, x1, y1], radius=20, fill=(34, 12, 30, 230), outline=(255, 0, 180, 240), width=3)
        # Header
        draw.rounded_rectangle([x0 + 15, y0 + 15, x1 - 15, y0 + 75], radius=10, fill=(255, 0, 180, 40), outline=(255, 0, 180, 200), width=2)
        draw.text((x0 + 35, y0 + 26), "⭐  CODE OPEN SOURCE", fill=(255, 100, 220, 255), font=f_title)

        cur_y = y0 + 105
        draw.text((x0 + 30, cur_y), "• GitHub : LBG Studios", fill=(255, 220, 245, 255), font=f_body)
        draw.text((x0 + 30, cur_y + 45), "• github.com/Teome0245", fill=(0, 245, 212, 255), font=f_body)
        draw.text((x0 + 30, cur_y + 90), "• Architectures & scripts 0€", fill=(220, 220, 220, 255), font=f_body)

        # Bouton call to action
        cur_y += 165
        draw.rounded_rectangle([x0 + 25, cur_y, x1 - 25, cur_y + 65], radius=12, fill=(255, 0, 180, 200), outline=(255, 150, 220, 255), width=2)
        draw.text((x0 + 45, cur_y + 16), "ABONNE-TOI & REJOINS-NOUS 🚀", fill=(255, 255, 255, 255), font=f_badge)


def render_video(
    audio_path: Path,
    ass_path: Path,
    output_mp4: Path,
    avatar_dir: Path,
    title: str = "VEILLE TECH DU JOUR",
    category: str = "IA & DEV LOCAL",
) -> Path:
    """Génère et encode la vidéo complète TikTok / Shorts en MP4."""
    output_mp4.parent.mkdir(parents=True, exist_ok=True)
    rms_series, total_duration = get_audio_rms_series(audio_path, fps=FPS)
    total_frames = len(rms_series)

    # Chargement des poses de l'avatar plein pied
    poses: dict[str, Image.Image] = {}
    pose_names = [
        "neutral", "talk_a", "talk_o", "blink", "joy",
        "explain", "explain_talk", "point", "think"
    ]
    for p_name in pose_names:
        p_file = avatar_dir / f"{p_name}.png"
        if p_file.is_file():
            im = Image.open(p_file).convert("RGBA")
            # Redimensionnement plein pied adapté au 1080x1920 (largeur ~860px)
            target_w = 860
            target_h = int(im.height * (target_w / im.width))
            im_resized = im.resize((target_w, target_h), Image.Resampling.LANCZOS)
            poses[p_name] = im_resized
        else:
            logger.warning("Pose manquante %s dans %s", p_name, avatar_dir)

    if not poses or "neutral" not in poses:
        raise RuntimeError(f"Aucune pose d'avatar trouvée dans {avatar_dir}")

    # Polices pour l'UI et les infographies B-Roll
    font_badge = load_font(28, bold=True)
    font_hud = load_font(26, bold=True)
    font_title = load_font(42, bold=True)
    font_footer = load_font(24, bold=False)
    font_card_title = load_font(30, bold=True)
    font_card_body = load_font(24, bold=False)
    font_card_badge = load_font(24, bold=True)
    card_fonts = {
        "card_title": font_card_title,
        "card_body": font_card_body,
        "card_badge": font_card_badge,
    }

    # Préparation du bandeau supérieur statique
    header_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    h_draw = ImageDraw.Draw(header_layer)

    # Bandeau supérieur Cyberpunk
    h_draw.rounded_rectangle([60, 80, WIDTH - 60, 240], radius=24, fill=(18, 24, 38, 220), outline=(0, 245, 212, 180), width=3)
    # Badge catégorie & avatar
    h_draw.rounded_rectangle([90, 105, 420, 145], radius=10, fill=(0, 245, 212, 40), outline=(0, 245, 212, 220), width=2)
    h_draw.text((105, 112), f"LIA // {category.upper()}", fill=(0, 245, 212, 255), font=font_badge)

    # Badge 100% Local
    h_draw.rounded_rectangle([WIDTH - 380, 105, WIDTH - 90, 145], radius=10, fill=(255, 0, 128, 40), outline=(255, 0, 128, 220), width=2)
    h_draw.text((WIDTH - 365, 112), "100% LOCAL • 0€", fill=(255, 100, 180, 255), font=font_badge)

    # Titre du sujet
    disp_title = title if len(title) <= 36 else title[:33] + "..."
    h_draw.text((95, 170), disp_title, fill=(255, 255, 255, 255), font=font_title)

    # Footer
    h_draw.text((WIDTH // 2 - 180, HEIGHT - 80), "LBG Studios • github.com/Teome0245", fill=(140, 160, 190, 200), font=font_footer)

    # Lancement du process FFmpeg en pipe stdin
    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "rawvideo",
        "-vcodec",
        "rawvideo",
        "-s",
        f"{WIDTH}x{HEIGHT}",
        "-pix_fmt",
        "rgba",
        "-r",
        str(FPS),
        "-i",
        "-",  # Stdin raw video
        "-i",
        str(audio_path),  # Audio input
        "-vf",
        f"subtitles='{ass_path}'",  # Burn ASS subtitles
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        "-ar",
        "44100",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        str(output_mp4),
    ]

    logger.info("Encodage FFmpeg en cours vers %s...", output_mp4)
    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    # Rendu des frames
    num_bars = 28
    bar_width = 20
    bar_gap = 12
    spectrum_start_x = (WIDTH - (num_bars * (bar_width + bar_gap))) // 2
    spectrum_y_base = 1760

    # Phasing narratif pour gestuelle corporelle, infographies et badges HUD
    p_intro = 3.6
    p_problem_start = total_duration * 0.22
    p_solution_start = total_duration * 0.44
    p_metrics_start = total_duration * 0.68
    p_outro_start = max(total_duration - 4.5, total_duration * 0.88)

    for f_idx in range(total_frames):
        t = float(f_idx) / FPS
        rms = rms_series[f_idx]
        is_talking = rms > 0.14
        is_blink = ((t + 1.8) % 3.6) < 0.14

        # 1. Sélection de la pose corporelle et faciale
        if is_blink and "blink" in poses and not is_talking:
            active_pose = poses["blink"]
        elif t >= p_outro_start:
            # Outro / Call to Action
            if is_talking and "talk_a" in poses:
                active_pose = poses["talk_a"]
            elif "joy" in poses:
                active_pose = poses["joy"]
            else:
                active_pose = poses["neutral"]
        elif p_metrics_start <= t < p_outro_start:
            # Métriques chiffrées & benchmarks -> pose désignation point
            if "point" in poses:
                active_pose = poses["point"]
            elif is_talking and "talk_a" in poses:
                active_pose = poses["talk_a"]
            else:
                active_pose = poses["neutral"]
        elif p_solution_start <= t < p_metrics_start:
            # Explication de la solution technique -> gestuelle mains ouvertes
            if is_talking and "explain_talk" in poses:
                cycle_phase = int(t * 6) % 2
                active_pose = poses["explain_talk"] if cycle_phase == 0 else poses.get("explain", poses["explain_talk"])
            elif "explain" in poses:
                active_pose = poses["explain"]
            else:
                active_pose = poses["neutral"]
        elif p_problem_start <= t < p_solution_start:
            # Problème / Écueil -> posture réflexion think
            if "think" in poses:
                active_pose = poses["think"]
            elif is_talking and "talk_o" in poses:
                active_pose = poses["talk_o"]
            else:
                active_pose = poses["neutral"]
        else:
            # Intro & Hook
            if is_talking:
                cycle_phase = int(t * 8) % 2
                if cycle_phase == 0 and "talk_a" in poses:
                    active_pose = poses["talk_a"]
                elif "talk_o" in poses:
                    active_pose = poses["talk_o"]
                else:
                    active_pose = poses["neutral"]
            else:
                active_pose = poses["neutral"]

        # 2. Détermination de la carte infographique active & cadrage dynamique
        active_card = None
        if p_problem_start <= t < p_solution_start:
            active_card = "alert"
        elif p_solution_start <= t < p_metrics_start:
            active_card = "stack"
        elif p_metrics_start <= t < p_outro_start:
            active_card = "metrics"
        elif t >= p_outro_start:
            active_card = "outro"

        # Quand une infographie est présente, l'avatar se décale sur la gauche
        if active_card:
            avatar_base_x = 35
        else:
            # Intro & Hook : avatar centré
            avatar_base_x = (WIDTH - active_pose.width) // 2

        # 3. Micro-mouvements corporels (sway latéral + bobbing + tilt de tête réactif)
        dy = int(math.sin(t * 2.2) * 6)
        dx = int(math.sin(t * 1.1) * 8)
        avatar_x = avatar_base_x + dx
        avatar_y = 260 + dy

        # Micro-inclinaison de tête et buste calée sur les syllabes
        tilt_deg = math.sin(t * 3.2) * 1.5 + (rms * 2.2)
        if abs(tilt_deg) > 0.2:
            rendered_pose = active_pose.rotate(tilt_deg, resample=Image.Resampling.BICUBIC, expand=False)
        else:
            rendered_pose = active_pose

        # 4. Assemblage dynamique de la scène
        # Fond cyberpunk dynamique (grille qui défile + particules en mouvement continu)
        bg_dynamic = create_dynamic_background(t, WIDTH, HEIGHT)
        frame = Image.alpha_composite(bg_dynamic, header_layer)
        f_draw = ImageDraw.Draw(frame)

        # 5. Spectre audio réactif EN ARRIÈRE-PLAN
        for b_idx in range(num_bars):
            freq_factor = math.sin(t * 12.0 + b_idx * 0.45) * 0.5 + 0.5
            bar_height = int(rms * freq_factor * 180) + 6
            bx = spectrum_start_x + b_idx * (bar_width + bar_gap)
            by1 = spectrum_y_base
            by0 = spectrum_y_base - bar_height

            color_ratio = min(1.0, bar_height / 150.0)
            br = int(0 + color_ratio * 255)
            bg_c = int(245 - color_ratio * 145)
            bb = int(212 + color_ratio * 43)

            f_draw.rounded_rectangle([bx, by0, bx + bar_width, by1], radius=4, fill=(br, bg_c, bb, 160))

        # 6. Badge HUD narratif dynamique en haut sous le bandeau
        if active_card == "alert":
            hud_text = "⚠️  ÉCUEIL : DÉPENDANCES & COÛTS CLOUD"
            hud_outline = (255, 80, 50, 220)
            hud_fill = (45, 18, 18, 200)
            hud_color = (255, 140, 110, 255)
        elif active_card == "stack":
            hud_text = "⚡  ARCHITECTURE 100% LOCALE • 0€"
            hud_outline = (0, 245, 212, 220)
            hud_fill = (12, 35, 38, 200)
            hud_color = (0, 245, 212, 255)
        elif active_card == "metrics":
            hud_text = "📊  PERFORMANCES & BENCHMARKS RÉELS"
            hud_outline = (50, 255, 140, 220)
            hud_fill = (15, 38, 24, 200)
            hud_color = (120, 255, 180, 255)
        else:
            hud_text = "💡  LBG STUDIOS • INGÉNIERIE IA & JEU"
            hud_outline = (255, 0, 180, 200)
            hud_fill = (38, 14, 30, 200)
            hud_color = (255, 130, 210, 255)

        hud_w = 620
        hud_x0 = (WIDTH - hud_w) // 2
        f_draw.rounded_rectangle([hud_x0, 260, hud_x0 + hud_w, 310], radius=12, fill=hud_fill, outline=hud_outline, width=2)
        f_draw.text((hud_x0 + 25, 272), hud_text, fill=hud_color, font=font_hud)

        # 7. Carte infographique B-Roll à droite
        if active_card:
            draw_tech_card(f_draw, active_card, t, rms, card_fonts)

        # 8. Incrustation de l'avatar 3D plein pied par-dessus l'arrière-plan
        frame.paste(rendered_pose, (avatar_x, avatar_y), rendered_pose)

        # Envoi direct du frame brut au pipe FFmpeg
        proc.stdin.write(frame.tobytes())

    proc.stdin.close()
    _, stderr_data = proc.communicate()

    if proc.returncode != 0:
        err_msg = stderr_data.decode("utf-8", errors="replace")
        raise RuntimeError(f"FFmpeg erreur ({proc.returncode}): {err_msg}")

    logger.info("Vidéo finalisée avec succès : %s (taille: %d octets)", output_mp4, output_mp4.stat().st_size)
    return output_mp4

