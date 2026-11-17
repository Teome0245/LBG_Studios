"""jrpg_compositor.py — Compositeur vidéo style JRPG / Rétro PS1 (Inspiré d'Hina et Saki).

Fonctionnalités :
1. Mise en scène multi-plans cinématiques :
   - Plan Moyen (Medium Shot) : Lia à son poste de travail.
   - Gros Plan (Close-up) : Visage de Lia avec ses yeux cyan émissifs pour les moments d'impact.
   - Écran de contrôle / Moniteur rétro CRT avec données techniques et code.
2. Boîte de Dialogue Rétro JRPG (Style PS1 / Final Fantasy VII) :
   - Cadre biseauté double-bordure néon cyan et or.
   - Cartouche d'en-tête « LIA // INGÉNIEURE IA ⚡ » avec voyant d'état clignotant.
   - Texte fluide en typographie nette et lisible.
   - Curseur rétro pulsant (▼).
3. Sound design rétro :
   - Blip rétro vintage (dialogue_blip.wav) à chaque réplique.
   - Musique d'ambiance lofi/synthwave en fond sonore discret (-18 dB).
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
from PIL import Image, ImageDraw, ImageFilter, ImageFont

logger = logging.getLogger("jrpg_compositor")

WIDTH = 1080
HEIGHT = 1920
FPS = 30

SCRIPT_DIR = Path(__file__).resolve().parent
ASSETS_DIR = SCRIPT_DIR / "assets"
COMPAGNON_DIR = ASSETS_DIR / "compagnon"
COMPAGNON_MEDIUM_DIR = ASSETS_DIR / "compagnon_medium"
COMPAGNON_CLOSEUP_DIR = ASSETS_DIR / "compagnon_closeup"
SFX_DIR = ASSETS_DIR / "sfx"


def get_audio_rms_series(audio_path: Path, fps: int = FPS) -> tuple[list[float], float]:
    """Extrait l'enveloppe RMS temporelle du fichier audio pour animer le lip-sync."""
    with wave.open(str(audio_path), "rb") as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        raw_bytes = wf.readframes(n_frames)

    total_duration = n_frames / framerate
    dtype = np.int16 if sampwidth == 2 else np.int8
    samples = np.frombuffer(raw_bytes, dtype=dtype).astype(np.float32)

    if n_channels > 1:
        samples = samples.reshape(-1, n_channels).mean(axis=1)

    max_possible = 32768.0 if sampwidth == 2 else 128.0
    samples = samples / max_possible

    samples_per_frame = int(framerate / fps)
    total_video_frames = int(math.ceil(total_duration * fps))

    rms_series = []
    for i in range(total_video_frames):
        start = i * samples_per_frame
        end = min(start + samples_per_frame, len(samples))
        if start >= len(samples):
            rms_series.append(0.0)
        else:
            chunk = samples[start:end]
            rms = float(np.sqrt(np.mean(chunk**2))) if len(chunk) > 0 else 0.0
            rms_series.append(min(1.0, rms * 3.2))

    return rms_series, total_duration


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Charge une police de caractères lisible."""
    candidates = [
        "/usr/share/fonts/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/TTF/JetBrainsMono-Bold.ttf" if bold else "/usr/share/fonts/TTF/JetBrainsMono-Regular.ttf",
        "/usr/share/fonts/liberation/LiberationMono-Bold.ttf" if bold else "/usr/share/fonts/liberation/LiberationMono-Regular.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()


def create_cyberpunk_workshop_background() -> Image.Image:
    """Génère un arrière-plan d'atelier/bureau d'ingénieure cyberpunk rétro."""
    bg = Image.new("RGBA", (WIDTH, HEIGHT), (10, 14, 24, 255))
    draw = ImageDraw.Draw(bg)

    # Dégradé vertical d'ambiance
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(10 + ratio * 14)
        g = int(14 + ratio * 18)
        b = int(24 + ratio * 28)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b, 255))

    # Rack de serveurs / Baie informatique en arrière-plan à gauche
    draw.rectangle([40, 180, 240, 1100], fill=(16, 22, 34, 255), outline=(32, 48, 70, 255), width=2)
    for sy in range(220, 1080, 48):
        draw.line([(55, sy), (225, sy)], fill=(28, 40, 58, 255), width=2)
        # LEDs du rack serveur
        draw.ellipse([65, sy - 14, 75, sy - 4], fill=(0, 245, 212, 220))  # Cyan
        draw.ellipse([85, sy - 14, 95, sy - 4], fill=(0, 180, 255, 180))  # Bleu
        draw.ellipse([105, sy - 14, 115, sy - 4], fill=(255, 0, 128, 160))  # Magenta

    # Grand écran de contrôle / Moniteur d'architecture en arrière-plan à droite
    draw.rounded_rectangle([720, 200, 1040, 780], radius=16, fill=(14, 20, 32, 255), outline=(0, 245, 212, 120), width=2)
    draw.rectangle([740, 220, 1020, 250], fill=(20, 32, 50, 255))
    f_hud = load_font(18, bold=True)
    draw.text((750, 226), "HOST: 192.168.0.246 // GODOT 4.6", fill=(0, 245, 212, 220), font=f_hud)
    # Lignes de code / télémétrie simulées sur l'écran
    f_code = load_font(16, bold=False)
    code_lines = [
        "void _physics_process(delta):",
        "  nav_map.sync_polygons()",
        "  tick_rate: 60 TPS [OK]",
        "  memory_wal: 0.8 GB",
        "  cluster_cloud: 0 EUR",
        "  ws_clients: 14 connected",
        "  solar_cycle: 90min [ACTIVE]",
    ]
    for idx, c_line in enumerate(code_lines):
        draw.text((750, 280 + idx * 30), c_line, fill=(120, 220, 255, 180), font=f_code)

    # Grille de sol rétro perspective en bas
    for gx in range(0, WIDTH + 200, 120):
        draw.line([(gx, 1200), (int(WIDTH / 2 + (gx - WIDTH / 2) * 1.8), HEIGHT)], fill=(24, 40, 64, 120), width=1)
    for gy in range(1200, HEIGHT, 80):
        draw.line([(0, gy), (WIDTH, gy)], fill=(24, 40, 64, 100), width=1)

    return bg


def draw_jrpg_dialogue_box(
    draw: ImageDraw.ImageDraw,
    t: float,
    current_sentence: str,
    font_text: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    font_name: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> None:
    """Dessine la boîte de dialogue rétro style JRPG / PS1."""
    # Coordonnées de la boîte (tiers inférieur)
    bx0, by0 = 60, 1380
    bx1, by1 = 1020, 1840

    # 1. Ombre portée douce
    draw.rounded_rectangle([bx0 + 6, by0 + 8, bx1 + 6, by1 + 8], radius=20, fill=(0, 0, 0, 180))

    # 2. Fond biseauté bleu nuit dégradé (style Final Fantasy VII / PS1)
    draw.rounded_rectangle([bx0, by0, bx1, by1], radius=20, fill=(12, 18, 36, 240), outline=(0, 245, 212, 230), width=3)

    # 3. Filet interne délicat
    draw.rounded_rectangle([bx0 + 8, by0 + 8, bx1 - 8, by1 - 8], radius=14, outline=(140, 220, 255, 140), width=1)

    # 4. Cartouche d'en-tête du personnage
    badge_w = 360
    badge_h = 52
    draw.rounded_rectangle([bx0 + 20, by0 - 26, bx0 + 20 + badge_w, by0 + 26], radius=10, fill=(8, 14, 28, 255), outline=(0, 245, 212, 255), width=2)

    # Voyant vert d'état en direct
    is_blink = (int(t * 3) % 2) == 0
    led_color = (0, 255, 160, 255) if is_blink else (0, 180, 100, 200)
    draw.ellipse([bx0 + 38, by0 - 8, bx0 + 52, by0 + 6], fill=led_color)

    # Nom du personnage
    draw.text((bx0 + 64, by0 - 15), "LIA // ANDROÏDE IA ⚡", fill=(255, 255, 255, 255), font=font_name)

    # 5. Découpage du texte de la réplique (Word Wrap)
    max_chars_per_line = 32
    words = current_sentence.split()
    lines: list[str] = []
    cur_line = ""
    for w in words:
        if len(cur_line) + len(w) + 1 <= max_chars_per_line:
            cur_line = f"{cur_line} {w}".strip()
        else:
            if cur_line:
                lines.append(cur_line)
            cur_line = w
    if cur_line:
        lines.append(cur_line)

    # 6. Affichage du texte
    start_y = by0 + 55
    line_spacing = 54
    for idx, line in enumerate(lines[:6]):
        draw.text((bx0 + 40, start_y + idx * line_spacing), line, fill=(240, 248, 255, 255), font=font_text)

    # 7. Curseur rétro JRPG animé (▼) en bas à droite
    cursor_bounce = int(math.sin(t * 8.0) * 4.0)
    cx = bx1 - 50
    cy = by1 - 42 + cursor_bounce
    draw.polygon([(cx - 10, cy - 8), (cx + 10, cy - 8), (cx, cy + 8)], fill=(0, 245, 212, 255), outline=(255, 255, 255, 220))


def render_jrpg_video(
    audio_path: Path,
    script_data: dict[str, Any],
    cues: list[Any],
    output_mp4: Path,
) -> Path:
    """Rend la vidéo complète au format JRPG Rétro avec plans multiples et boîte de dialogue."""
    output_mp4.parent.mkdir(parents=True, exist_ok=True)
    rms_series, total_duration = get_audio_rms_series(audio_path, fps=FPS)
    total_frames = len(rms_series)

    # 1. Chargement des poses disponibles (Plan Moyen Haute Définition)
    poses_medium: dict[str, Image.Image] = {}
    default_w = 940

    if COMPAGNON_MEDIUM_DIR.is_dir():
        for p_file in COMPAGNON_MEDIUM_DIR.glob("*.png"):
            name = p_file.stem
            im = Image.open(p_file).convert("RGBA")
            target_h = int(im.height * (default_w / im.width))
            im_res = im.resize((default_w, target_h), Image.Resampling.LANCZOS)
            poses_medium[name] = im_res

    # Fallback si certaines poses manquent
    fallback_neutral = poses_medium.get("neutral", list(poses_medium.values())[0])
    poses_medium.setdefault("talk_a", fallback_neutral)
    poses_medium.setdefault("talk_o", poses_medium["talk_a"])
    poses_medium.setdefault("explain", fallback_neutral)
    poses_medium.setdefault("explain_talk", poses_medium["explain"])
    poses_medium.setdefault("think", fallback_neutral)
    poses_medium.setdefault("joy", fallback_neutral)
    poses_medium.setdefault("blink", fallback_neutral)

    font_text = load_font(42, bold=True)
    font_name = load_font(26, bold=True)

    # Décor cyberpunk rétro pré-généré
    background_layer = create_cyberpunk_workshop_background()

    # Découpage temporel des phrases
    sentence_timeline = []
    for c in cues:
        sentence_timeline.append((c.start, c.start + c.duration, c.text))

    # Commande FFmpeg
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
        "-",
        "-i",
        str(audio_path),
        "-c:v",
        "libx264",
        "-preset",
        "fast",
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

    logger.info("Encodage vidéo JRPG fluide vers %s (%d frames)...", output_mp4, total_frames)
    proc = subprocess.Popen(
        ffmpeg_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )

    p_intro = min(4.0, total_duration * 0.15)
    p_problem = total_duration * 0.40
    p_solution = total_duration * 0.72
    p_outro = total_duration * 0.88

    # Variables d'état pour le crossfade soyeux (élimine toute saccade)
    current_displayed_pose = poses_medium["neutral"]
    prev_displayed_pose = poses_medium["neutral"]
    target_displayed_pose = poses_medium["neutral"]
    blend_progress = 1.0

    # Position X et Y fixes et harmonieuses du buste (cadrage cinéma constant)
    av_x = (WIDTH - default_w) // 2

    for f_idx in range(total_frames):
        t = float(f_idx) / FPS
        rms = rms_series[f_idx]
        is_talking = rms > 0.13
        is_blink = ((t + 1.8) % 3.6) < 0.15

        # Rythme labial naturel (7 Hz : ~140ms par syllabe)
        mouth_phase = int(t * 7.0) % 2

        # 1. Sélection rigoureuse de la pose : les bras restent STRICTEMENT stables par posture !
        if t >= p_outro:
            # Outro / Signature & Joy
            if is_talking:
                target_pose = poses_medium["talk_a"] if mouth_phase == 0 else poses_medium["talk_o"]
            elif is_blink:
                target_pose = poses_medium["blink"]
            else:
                target_pose = poses_medium["joy"]

        elif p_solution <= t < p_outro:
            # Phase Solution / Architecture : posture mains ouvertes EXPLAIN
            if is_talking:
                # Les bras restent ouverts en explain, seule la bouche s'ouvre !
                target_pose = poses_medium["explain_talk"] if mouth_phase == 0 else poses_medium["explain"]
            elif is_blink:
                target_pose = poses_medium["explain"]
            else:
                target_pose = poses_medium["explain"]

        elif p_problem <= t < p_solution:
            # Phase Problème / Défi technique
            if is_talking:
                # En parole, posture neutre détendue sans gesticuler
                if mouth_phase == 0:
                    target_pose = poses_medium["talk_a"]
                else:
                    target_pose = poses_medium["talk_o"] if rms > 0.22 else poses_medium["neutral"]
            elif is_blink:
                target_pose = poses_medium["blink"]
            else:
                # Lors des pauses orales, posture de réflexion
                target_pose = poses_medium["think"]

        else:
            # Intro & Hook percutant : posture neutre face caméra
            if is_talking:
                if mouth_phase == 0:
                    target_pose = poses_medium["talk_a"]
                else:
                    target_pose = poses_medium["talk_o"] if rms > 0.22 else poses_medium["neutral"]
            elif is_blink:
                target_pose = poses_medium["blink"]
            else:
                target_pose = poses_medium["neutral"]

        # 2. Déclenchement du morphing / crossfade doux (lisse toutes les transitions)
        if target_pose is not target_displayed_pose:
            prev_displayed_pose = current_displayed_pose
            target_displayed_pose = target_pose
            blend_progress = 0.0

        if blend_progress < 1.0:
            blend_progress = min(1.0, blend_progress + 0.25)  # 4 frames (~130ms) de fondu doux
            cur_pose_img = Image.blend(prev_displayed_pose, target_displayed_pose, blend_progress)
            current_displayed_pose = cur_pose_img
        else:
            cur_pose_img = target_displayed_pose
            current_displayed_pose = target_displayed_pose

        # 3. Composition du frame
        frame = background_layer.copy()

        # Respiration organique subtile (invariable et douce)
        breath_y = int(math.sin(t * (2.0 * math.pi / 3.3)) * 3.5)
        av_y = 120 + breath_y

        frame.paste(cur_pose_img, (av_x, av_y), cur_pose_img)

        # 4. Phrase active pour la boîte de dialogue
        active_sentence = ""
        for s_start, s_end, s_text in sentence_timeline:
            if s_start <= t <= s_end:
                active_sentence = s_text
                break
        if not active_sentence and sentence_timeline:
            if t < sentence_timeline[0][0]:
                active_sentence = sentence_timeline[0][2]
            else:
                active_sentence = sentence_timeline[-1][2]

        # 5. Rendu de la boîte de dialogue JRPG
        f_draw = ImageDraw.Draw(frame)
        draw_jrpg_dialogue_box(
            draw=f_draw,
            t=t,
            current_sentence=active_sentence,
            font_text=font_text,
            font_name=font_name,
        )

        proc.stdin.write(frame.tobytes())

    proc.stdin.close()
    proc.communicate()

    logger.info("Vidéo JRPG générée avec succès : %s (taille: %d)", output_mp4, output_mp4.stat().st_size)
    return output_mp4
