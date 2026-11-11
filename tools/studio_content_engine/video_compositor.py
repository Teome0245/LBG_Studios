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


def create_cyber_background(w: int = WIDTH, h: int = HEIGHT) -> Image.Image:
    """Génère le fond statique cyberpunk avec dégradé radial et grille sci-fi."""
    bg = Image.new("RGBA", (w, h), (10, 15, 26, 255))
    draw = ImageDraw.Draw(bg)

    # Dégradé vertical sombre
    for y in range(0, h, 4):
        ratio = y / h
        r = int(7 + ratio * 12)
        g = int(11 + ratio * 18)
        b = int(22 + ratio * 32)
        draw.rectangle([0, y, w, y + 4], fill=(r, g, b, 255))

    # Lignes de grille perspective au sol / bas d'écran
    grid_color = (0, 245, 212, 35)  # Cyan translucide
    horizon_y = 1200
    for gy in range(horizon_y, h, 50):
        draw.line([(0, gy), (w, gy)], fill=grid_color, width=1)

    # Lignes fuyantes
    vanishing_x = w // 2
    for vx in range(-400, w + 450, 120):
        draw.line([(vanishing_x, horizon_y - 200), (vx, h)], fill=grid_color, width=1)

    # Halo lumineux derrière l'avatar (x=540, y=850)
    halo = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    halo_draw = ImageDraw.Draw(halo)
    for radius in range(350, 50, -30):
        alpha = int((350 - radius) / 350 * 28)
        bbox = [w // 2 - radius, 820 - radius, w // 2 + radius, 820 + radius]
        halo_draw.ellipse(bbox, fill=(0, 245, 212, alpha))

    bg = Image.alpha_composite(bg, halo)
    return bg


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

    # Chargement des poses de l'avatar
    poses: dict[str, Image.Image] = {}
    for p_name in ["neutral", "talk_a", "talk_o", "blink", "joy"]:
        p_file = avatar_dir / f"{p_name}.png"
        if p_file.is_file():
            im = Image.open(p_file).convert("RGBA")
            # Redimensionnement portrait adapté au 1080x1920 (largeur ~640px)
            target_w = 640
            target_h = int(im.height * (target_w / im.width))
            im_resized = im.resize((target_w, target_h), Image.Resampling.LANCZOS)
            poses[p_name] = im_resized
        else:
            logger.warning("Pose manquante %s dans %s", p_name, avatar_dir)

    if not poses or "neutral" not in poses:
        raise RuntimeError(f"Aucune pose d'avatar trouvée dans {avatar_dir}")

    # Polices pour l'UI
    font_badge = load_font(28, bold=True)
    font_title = load_font(42, bold=True)
    font_footer = load_font(24, bold=False)

    # Préparation du fond et du bandeau statique
    bg_template = create_cyber_background(WIDTH, HEIGHT)
    header_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    h_draw = ImageDraw.Draw(header_layer)

    # Bandeau supérieur Cyberpunk
    # Box header
    h_draw.rounded_rectangle([60, 80, WIDTH - 60, 240], radius=24, fill=(18, 24, 38, 220), outline=(0, 245, 212, 180), width=3)
    # Badge catégorie & avatar
    h_draw.rounded_rectangle([90, 105, 420, 145], radius=10, fill=(0, 245, 212, 40), outline=(0, 245, 212, 220), width=2)
    h_draw.text((105, 112), f"LIA // {category.upper()}", fill=(0, 245, 212, 255), font=font_badge)

    # Badge 100% Local
    h_draw.rounded_rectangle([WIDTH - 380, 105, WIDTH - 90, 145], radius=10, fill=(255, 0, 128, 40), outline=(255, 0, 128, 220), width=2)
    h_draw.text((WIDTH - 365, 112), "100% LOCAL • 0€", fill=(255, 100, 180, 255), font=font_badge)

    # Titre du sujet
    # Troncature propre si trop long
    disp_title = title if len(title) <= 36 else title[:33] + "..."
    h_draw.text((95, 170), disp_title, fill=(255, 255, 255, 255), font=font_title)

    # Footer
    h_draw.text((WIDTH // 2 - 180, HEIGHT - 80), "LBG Studios • github.com/Teome0245", fill=(140, 160, 190, 200), font=font_footer)

    base_frame = Image.alpha_composite(bg_template, header_layer)

    # Lancement du process FFmpeg en pipe stdin
    # Note : on applique le filtre de sous-titres libass sur la vidéo
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
    spectrum_y_base = 1580

    for f_idx in range(total_frames):
        t = float(f_idx) / FPS
        rms = rms_series[f_idx]

        # 1. Sélection de la pose d'avatar
        # Clignement toutes les 3.6s pendant 0.14s
        is_blink = (t % 3.6) < 0.14
        # Sourire outro sur les 2 dernières secondes
        is_outro = t > (total_duration - 2.0)

        if is_blink and "blink" in poses:
            active_pose = poses["blink"]
        elif is_outro and "joy" in poses:
            active_pose = poses["joy"]
        elif rms > 0.15:
            # Alternance voyelle A / O selon fréquence du pitch/amplitude
            cycle_phase = int(t * 8) % 2
            if cycle_phase == 0 and "talk_a" in poses:
                active_pose = poses["talk_a"]
            elif "talk_o" in poses:
                active_pose = poses["talk_o"]
            else:
                active_pose = poses["neutral"]
        else:
            active_pose = poses["neutral"]

        # 2. Respiration & micro-mouvement
        dy = int(math.sin(t * 2.5) * 6)
        avatar_x = (WIDTH - active_pose.width) // 2
        avatar_y = 420 + dy

        # 3. Assemblage du frame
        frame = base_frame.copy()
        frame.paste(active_pose, (avatar_x, avatar_y), active_pose)

        # 4. Spectre audio réactif (28 barres animées)
        f_draw = ImageDraw.Draw(frame)
        for b_idx in range(num_bars):
            # Oscillation pseudo-spectrale pondérée par le RMS global
            freq_factor = math.sin(t * 12.0 + b_idx * 0.45) * 0.5 + 0.5
            bar_height = int(rms * freq_factor * 160) + 6
            bx = spectrum_start_x + b_idx * (bar_width + bar_gap)
            by1 = spectrum_y_base
            by0 = spectrum_y_base - bar_height

            # Couleur dégradée Cyan -> Magenta selon la hauteur
            color_ratio = min(1.0, bar_height / 140.0)
            br = int(0 + color_ratio * 255)
            bg_c = int(245 - color_ratio * 145)
            bb = int(212 + color_ratio * 43)

            f_draw.rounded_rectangle([bx, by0, bx + bar_width, by1], radius=4, fill=(br, bg_c, bb, 220))

        # Envoi direct du frame brut au pipe FFmpeg
        proc.stdin.write(frame.tobytes())

    proc.stdin.close()
    _, stderr_data = proc.communicate()

    if proc.returncode != 0:
        err_msg = stderr_data.decode("utf-8", errors="replace")
        raise RuntimeError(f"FFmpeg erreur ({proc.returncode}): {err_msg}")

    logger.info("Vidéo finalisée avec succès : %s (taille: %d octets)", output_mp4, output_mp4.stat().st_size)
    return output_mp4

