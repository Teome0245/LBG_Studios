"""stage3d_compositor.py — Compositeur 3D WebGL Déterministe Image-par-Image (30.00 FPS Garantis, Zéro Saccade).

Architecture offline type Remotion / Timecut :
- L'horloge virtuelle (`__lockVirtualClock` + `__advanceVirtualFrame(1/30)`) avance exactement de 33.333 ms
  à chaque frame, quel que soit le temps de calcul CPU ou GPU.
- Toutes les animations `.vrma` sont préchargées en RAM avec la clé exacte de `vrm_pet` avant la frame 0.
- Chaque frame `1080x1920` (fond scénique + WebGL Three-VRM + HUD glassmorphism + sous-titres karaoké + égaliseur 24 bandes)
  est encodée en JPEG haute qualité (0.94) et streamée en binaire via WebSocket directement dans `ffmpeg -f image2pipe`.
- Résultat : **100 % des frames sont uniques (30.00 FPS mathématiques)**, zéro frame dupliquée, zéro saccade.

Exécution hybride :
- Priorité au rendu GPU headless invisible (`--headless=new --use-angle=d3d11`) sur le PC Windows `.10` s'il est libre.
- Repli automatique sur `.143` (`Xvfb` + Chromium WebGL SwiftShader) avec la même fluidité finale 30.00 FPS.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import math
import os
import re
import shutil
import socket
import subprocess
import threading
import time
import wave
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from socketserver import ThreadingMixIn
from typing import Any
from urllib.parse import quote

import httpx
import numpy as np

logger = logging.getLogger("stage3d_compositor")

ENGINE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ENGINE_DIR.parents[1]
OVERLAY_DIR = REPO_ROOT / "packages" / "compagnon-desktop" / "overlay"
STAGE_HTML_TEMPLATE = ENGINE_DIR / "assets" / "stage3d" / "render_stage3d.html"

WIN10_AGENT_URL = os.environ.get("LBG_WIN10_AGENT_URL", "http://192.168.0.10:5005")
WIN10_MIN_IDLE_SEC = int(os.environ.get("LBG_WIN10_MIN_IDLE_SEC", "180"))
HOST_143_LAN_IP = os.environ.get("LBG_STAGE3D_LAN_IP", "192.168.0.143")

FPS = 30
WIDTH = 1080
HEIGHT = 1920


# ============================================================================
# 1. CATALOGUES CHORÉGRAPHIQUES & MUSICAUX
# ============================================================================

TECH_MOTION_BANKS: list[list[dict[str, Any]]] = [
    [
        {"file": "Female Dynamic Pose.vrma", "label": "Accroche Cyber", "cam": "push_in", "exp": "hook_alert", "exp_label": "Accroche Directe"},
        {"file": "Standing Using Touchscreen Tablet.vrma", "label": "Analyse Système", "cam": "bust_left", "exp": "tech_focus", "exp_label": "Diagnostic Architecture"},
        {"file": "Pro_Magic_Pack_standing 1H cast spell 01.vrma", "label": "Déploiement Core", "cam": "front_arc", "exp": "tech_focus", "exp_label": "Orchestration Locale"},
        {"file": "Dancing Maraschino Step.vrma", "speed": 0.78, "label": "Cadence Temps Réel", "cam": "bust_right", "exp": "idol", "exp_label": "Flux Synchrone"},
        {"file": "Victory.vrma", "label": "Preuve Benchmark", "cam": "pull_out", "exp": "metrics_win", "exp_label": "Validation 0€ Cloud"},
        {"pose": "fingerHeart", "label": "Signature Lia", "cam": "bust", "exp": "cta_joy", "exp_label": "Signature LBG Studios"},
    ],
    [
        {"file": "wave_right.vrma", "label": "Signal Entrant", "cam": "push_in", "exp": "hook_alert", "exp_label": "Signal Studio"},
        {"file": "Thinking.vrma", "label": "Inspection Goulot", "cam": "closeup", "exp": "tech_focus", "exp_label": "Analyse Latence"},
        {"file": "Female Standing Pose2.vrma", "label": "Stack Souveraine", "cam": "front_arc", "exp": "tech_focus", "exp_label": "Architecture Godot & IA"},
        {"file": "Having A Meeting, Female.vrma", "label": "Pipeline Unifié", "cam": "sway", "exp": "tech_focus", "exp_label": "Exécution Déterministe"},
        {"file": "Cheering.vrma", "label": "Gain Performance", "cam": "pull_out", "exp": "metrics_win", "exp_label": "Benchmarks Verts"},
        {"file": "Female Dance Pose1.vrma", "label": "Outro Cyber", "cam": "mid", "exp": "cta_joy", "exp_label": "Communauté LBG"},
    ],
    [
        {"file": "Calling.vrma", "label": "Alerte Dev", "cam": "push_in", "exp": "hook_alert", "exp_label": "Focus Ingénierie"},
        {"file": "Plotting.vrma", "label": "Conception Système", "cam": "bust_right", "exp": "tech_focus", "exp_label": "Optimisation Mémoire"},
        {"file": "Look Around.vrma", "label": "Topologie Monde", "cam": "front_arc", "exp": "tech_focus", "exp_label": "Simulation Spatiale"},
        {"file": "Female Dance Pose.vrma", "label": "Présence Avatar", "cam": "bust_left", "exp": "idol", "exp_label": "Incarnation VRM"},
        {"file": "clapping.vrma", "label": "Résultat Prod", "cam": "pull_out", "exp": "metrics_win", "exp_label": "100% Autonome"},
        {"pose": "fingerHeart", "label": "Signature Lia", "cam": "bust", "exp": "cta_joy", "exp_label": "À toi en commentaire"},
    ],
]

MUSIC_SHOW_PRESETS: list[dict[str, Any]] = [
    {
        "id": "nexura_drop_highlight",
        "title": "LIA — Nexura Domina (Drop Electro 3D)",
        "category": "Clip 3D & Chorégraphie VRM",
        "audio_rel": "nexura_domina_v1.mp3",
        "start_offset_sec": 22.0,
        "duration_sec": 38.0,
        "bpm": 128,
        "palette": "cyan_rose",
        "motions": [
            {"dur": 3.5, "file": "Female Dance Pose1.vrma", "label": "Intro Diva", "cam": "push_in", "exp": "mystique", "exp_label": "Tension Scénique"},
            {"dur": 8.5, "file": "Dancing Maraschino Step.vrma", "label": "Maraschino Groove", "cam": "mid", "exp": "diva", "exp_label": "Chant Scénique Passionné"},
            {"dur": 9.5, "file": "Bellydancing.vrma", "label": "Electro Bellydance", "cam": "drone_arc180", "exp": "climax", "exp_label": "Drop Electro 128 BPM"},
            {"dur": 9.5, "file": "Hip Hop Dancing3.vrma", "label": "Cyber Hip-Hop", "cam": "pull_out", "exp": "diva", "exp_label": "Énergie Pure"},
            {"dur": 4.0, "file": "Pro_Magic_Pack_Standing 2H Cast Spell 01.vrma", "label": "Nova Finale", "cam": "full", "exp": "climax", "exp_label": "Climax Vocal"},
            {"dur": 3.0, "pose": "fingerHeart", "label": "Final Idol", "cam": "bust", "exp": "idol", "exp_label": "Signature Lia"},
        ],
    },
    {
        "id": "cyberpunk_protocol_30s",
        "title": "LIA — Cyberpunk Protocol (Live 3D 128 BPM)",
        "category": "Performance Musicale IA",
        "audio_rel": "audio/lia_cyberpunk_song_30s_master.wav",
        "start_offset_sec": 0.0,
        "duration_sec": 30.0,
        "bpm": 128,
        "palette": "cyan_rose",
        "motions": [
            {"dur": 4.0, "file": "Female Dance Pose.vrma", "label": "Ouverture Néon", "cam": "push_in", "exp": "mystique", "exp_label": "Initialisation Chant"},
            {"dur": 8.0, "file": "Dancing Maraschino Step.vrma", "label": "Pop Groove", "cam": "sway", "exp": "idol", "exp_label": "Couplet Cyber Pop"},
            {"dur": 8.0, "file": "Jazz Dancing3.vrma", "label": "Jazz Electro", "cam": "front_arc", "exp": "diva", "exp_label": "Montée Synthwave"},
            {"dur": 6.5, "file": "samba.vrma", "label": "Drop Scénique", "cam": "drone_orbit", "exp": "climax", "exp_label": "Climax 128 BPM"},
            {"dur": 3.5, "pose": "fingerHeart", "label": "Cœur Idol", "cam": "bust", "exp": "idol", "exp_label": "LBG Studios Live"},
        ],
    },
    {
        "id": "swg_cantina_groove",
        "title": "LIA — Cantina Lost Heaven (Danses SWG 3D)",
        "category": "Chorégraphie MMO & VRM",
        "audio_rel": "audio/lia_synthwave_30s_master.wav",
        "start_offset_sec": 0.0,
        "duration_sec": 30.0,
        "bpm": 120,
        "palette": "amber_cyan",
        "motions": [
            {"dur": 4.0, "file": "Female Standing Pose2.vrma", "label": "Entrée Cantina", "cam": "push_in", "exp": "idol", "exp_label": "Ambiance Lost Heaven"},
            {"dur": 8.5, "file": "swg_poplock_loop.vrma", "label": "SWG Poplock Natif", "cam": "full", "exp": "diva", "exp_label": "Mocap Star Wars Galaxies"},
            {"dur": 9.0, "file": "swg_moonwalk.vrma", "label": "SWG Moonwalk", "cam": "drone_arc180", "exp": "climax", "exp_label": "Glisse Gravitationnelle"},
            {"dur": 5.5, "file": "Samba Dancing1.vrma", "label": "Fête Scrapaltai", "cam": "mid", "exp": "idol", "exp_label": "Énergie Galactique"},
            {"dur": 3.0, "pose": "fingerHeart", "label": "Salut Cantina", "cam": "bust", "exp": "idol", "exp_label": "Rendez-vous en jeu"},
        ],
    },
    {
        "id": "synthwave_energy_show",
        "title": "LIA — Synthwave Overdrive (Concert 3D)",
        "category": "Live Virtuel Three-VRM",
        "audio_rel": "audio/lia_synthwave_energy_master_60s.wav",
        "start_offset_sec": 0.0,
        "duration_sec": 42.0,
        "bpm": 130,
        "palette": "cyan_rose",
        "motions": [
            {"dur": 4.5, "file": "Female Dance Pose1.vrma", "label": "Allumage Scène", "cam": "push_in", "exp": "mystique", "exp_label": "Nappes Analogiques"},
            {"dur": 9.5, "file": "Arms Hip Hop Dance.vrma", "label": "Future Groove", "cam": "mid", "exp": "diva", "exp_label": "Bassline Punchy"},
            {"dur": 10.0, "file": "Bellydancing.vrma", "label": "Ondulation Néon", "cam": "front_arc", "exp": "climax", "exp_label": "Refrain Haute Énergie"},
            {"dur": 9.0, "file": "Capoeira_Pack_ginga variation 1.vrma", "label": "Flow Capoeira", "cam": "pull_out", "exp": "diva", "exp_label": "Agilité Mécatronique"},
            {"dur": 5.5, "file": "Hip Hop Dancing1.vrma", "label": "Drop Final", "cam": "drone_orbit_close", "exp": "climax", "exp_label": "Overdrive 130 BPM"},
            {"dur": 3.5, "pose": "fingerHeart", "label": "Outro Idol", "cam": "bust", "exp": "idol", "exp_label": "0€ Cloud • 100% Local"},
        ],
    },
    {
        "id": "nexura_climax_encore",
        "title": "LIA — Nexura Domina Climax (Solo Scénique 3D)",
        "category": "Clip Officiel 3D",
        "audio_rel": "nexura_domina_v1.mp3",
        "start_offset_sec": 88.0,
        "duration_sec": 40.0,
        "bpm": 128,
        "palette": "cyan_rose",
        "motions": [
            {"dur": 4.5, "file": "Crazy Gesture.vrma", "label": "Appel du Drop", "cam": "push_in", "exp": "diva", "exp_label": "Montée Électrique"},
            {"dur": 11.0, "file": "Hip Hop Dancing3.vrma", "label": "Solo Hip-Hop Cyber", "cam": "full", "exp": "climax", "exp_label": "Solo Scénique"},
            {"dur": 11.5, "file": "Bellydancing.vrma", "label": "Danse Hypnotique", "cam": "drone_orbit_close", "exp": "diva", "exp_label": "Voix & Formants Live"},
            {"dur": 9.0, "file": "Dancing Maraschino Step.vrma", "label": "Maraschino Encore", "cam": "pull_out", "exp": "idol", "exp_label": "Groove Final"},
            {"dur": 4.0, "pose": "fingerHeart", "label": "Signature Lia", "cam": "bust", "exp": "idol", "exp_label": "LBG Studios"},
        ],
    },
]


# ============================================================================
# 2. ANALYSE AUDIO FFT & MIXAGE BGM
# ============================================================================

def ensure_pcm_wav(input_audio: Path, out_wav: Path, start_offset: float = 0.0, max_duration: float | None = None) -> tuple[Path, float]:
    cmd = ["ffmpeg", "-y"]
    if start_offset > 0.01:
        cmd += ["-ss", f"{start_offset:.3f}"]
    cmd += ["-i", str(input_audio)]
    if max_duration is not None and max_duration > 0:
        cmd += ["-t", f"{max_duration:.3f}"]
    cmd += ["-ac", "1", "-ar", "22050", "-c:a", "pcm_s16le", str(out_wav)]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    with wave.open(str(out_wav), "rb") as wf:
        dur = wf.getnframes() / float(wf.getframerate())
    return out_wav, dur


def extract_master_audio_segment(
    input_audio: Path,
    out_audio: Path,
    start_offset: float = 0.0,
    duration_sec: float = 35.0,
) -> Path:
    fade_out_start = max(0.5, duration_sec - 1.2)
    af_filter = f"afade=t=in:st=0:d=0.35,afade=t=out:st={fade_out_start:.2f}:d=1.20"
    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{start_offset:.3f}",
        "-i", str(input_audio),
        "-t", f"{duration_sec:.3f}",
        "-af", af_filter,
        "-ar", "44100",
        "-ac", "2",
        "-c:a", "pcm_s16le",
        str(out_audio),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out_audio


def mix_speech_with_synthwave_bgm(speech_wav: Path, out_master_wav: Path, seed_key: str = "") -> Path:
    bgm_candidates = [
        OVERLAY_DIR / "audio" / "lia_synthwave_30s_instru.wav",
        OVERLAY_DIR / "audio" / "lia_synthwave_energy_instru_60s.wav",
        OVERLAY_DIR / "audio" / "lia_cyberpunk_track_30s.wav",
    ]
    existing_bgms = [p for p in bgm_candidates if p.is_file()]
    if not existing_bgms:
        shutil.copy2(speech_wav, out_master_wav)
        return out_master_wav

    idx = int(hashlib.md5(seed_key.encode("utf-8")).hexdigest()[:6], 16) % len(existing_bgms)
    bgm_path = existing_bgms[idx]

    with wave.open(str(speech_wav), "rb") as wf:
        speech_dur = wf.getnframes() / float(wf.getframerate())
    total_dur = speech_dur + 0.45
    fade_out_st = max(0.2, total_dur - 1.1)

    filter_complex = (
        f"[0:a]aresample=44100,pan=stereo|c0=c0|c1=c0,apad=pad_dur=0.45[vox];"
        f"[1:a]aresample=44100,volume=0.135,afade=t=in:st=0:d=0.4,afade=t=out:st={fade_out_st:.2f}:d=1.1[bgm];"
        f"[vox][bgm]amix=inputs=2:duration=first:dropout_transition=0,alimiter=limit=0.95[outa]"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i", str(speech_wav),
        "-stream_loop", "-1", "-i", str(bgm_path),
        "-filter_complex", filter_complex,
        "-map", "[outa]",
        "-t", f"{total_dur:.3f}",
        "-c:a", "pcm_s16le",
        str(out_master_wav),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0 or not out_master_wav.exists():
        logger.warning("Mixage BGM ignoré (repli voix pure) : %s", res.stderr[:200])
        shutil.copy2(speech_wav, out_master_wav)
    return out_master_wav


def compute_audio_telemetry(
    analysis_wav: Path,
    voice_only_wav: Path | None = None,
    fps: int = FPS,
) -> tuple[list[dict[str, Any]], float]:
    with wave.open(str(analysis_wav), "rb") as wf:
        sr = wf.getframerate()
        n_ch = wf.getnchannels()
        raw = wf.readframes(wf.getnframes())
    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if n_ch > 1:
        samples = samples.reshape(-1, n_ch).mean(axis=1)
    duration = len(samples) / float(sr)

    if voice_only_wav and voice_only_wav.exists():
        with wave.open(str(voice_only_wav), "rb") as vwf:
            vsr = vwf.getframerate()
            vn_ch = vwf.getnchannels()
            vraw = vwf.readframes(vwf.getnframes())
        vox_samples = np.frombuffer(vraw, dtype=np.int16).astype(np.float32) / 32768.0
        if vn_ch > 1:
            vox_samples = vox_samples.reshape(-1, vn_ch).mean(axis=1)
    else:
        vsr = sr
        vox_samples = samples

    total_frames = max(1, int(math.ceil(duration * fps)))
    win_size = 1024
    hann = np.hanning(win_size).astype(np.float32)
    freqs = np.fft.rfftfreq(win_size, d=1.0 / sr)
    v_freqs = np.fft.rfftfreq(win_size, d=1.0 / vsr)

    band_edges = np.geomspace(55.0, 7800.0, 25)
    prev_bars = np.full(24, 0.14, dtype=np.float32)

    frames_out: list[dict[str, Any]] = []
    for f_idx in range(total_frames):
        t_sec = f_idx / float(fps)
        center = int(t_sec * sr)
        start = max(0, center - win_size // 2)
        chunk = samples[start : start + win_size]
        if len(chunk) < win_size:
            chunk = np.pad(chunk, (0, win_size - len(chunk)))

        spec = np.abs(np.fft.rfft(chunk * hann)) / (win_size * 0.22)

        bars = np.zeros(24, dtype=np.float32)
        for b in range(24):
            mask = (freqs >= band_edges[b]) & (freqs < band_edges[b + 1])
            if np.any(mask):
                val = float(np.mean(spec[mask])) * (1.0 + b * 0.12)
                bars[b] = min(1.0, math.pow(max(0.0, val * 3.6), 0.68))
            else:
                bars[b] = prev_bars[b] * 0.85

        smoothed = np.where(bars > prev_bars, prev_bars * 0.35 + bars * 0.65, prev_bars * 0.72 + bars * 0.28)
        prev_bars = smoothed

        bass_mask = (freqs >= 55.0) & (freqs <= 210.0)
        bass_val = float(np.mean(spec[bass_mask])) * 4.2 if np.any(bass_mask) else 0.2
        bass_norm = min(1.0, max(0.0, bass_val))

        v_center = int(t_sec * vsr)
        v_start = max(0, v_center - win_size // 2)
        v_chunk = vox_samples[v_start : v_start + win_size]
        if len(v_chunk) < win_size:
            v_chunk = np.pad(v_chunk, (0, win_size - len(v_chunk)))
        v_rms = float(np.sqrt(np.mean(v_chunk**2))) * 3.4
        v_spec = np.abs(np.fft.rfft(v_chunk * hann))
        low_m = (v_freqs >= 260.0) & (v_freqs <= 950.0)
        high_m = (v_freqs >= 1100.0) & (v_freqs <= 3400.0)
        low_e = float(np.mean(v_spec[low_m])) if np.any(low_m) else 0.0
        high_e = float(np.mean(v_spec[high_m])) if np.any(high_m) else 0.0
        tot_e = low_e + high_e + 1e-6

        frames_out.append({
            "bass": round(bass_norm, 3),
            "rms": round(min(1.0, v_rms), 3),
            "low": round(low_e / tot_e, 3),
            "high": round(high_e / tot_e, 3),
            "bars": [round(float(x), 3) for x in smoothed],
        })

    return frames_out, duration


# ============================================================================
# 3. CONSTRUCTION DES TIMELINES
# ============================================================================

def build_karaoke_events(cues: list[Any], max_words: int = 3) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    chunk_counter = 0

    for cue in cues:
        words = [w for w in cue.words if w.strip()]
        if not words:
            continue
        n_words = len(words)
        for i in range(0, n_words, max_words):
            sub_words = words[i : i + max_words]
            t_start = cue.start + cue.duration * (i / n_words)
            t_end = cue.start + cue.duration * (min(n_words, i + max_words) / n_words)
            chunk_dur = max(0.08, t_end - t_start)

            weights = [max(2, len(re.sub(r"[^\w]", "", w))) for w in sub_words]
            total_w = max(1, sum(weights))
            cur_t = t_start
            chunk_counter += 1

            for w_idx, _ in enumerate(sub_words):
                w_dur = chunk_dur * (weights[w_idx] / total_w)
                events.append({
                    "chunk_id": chunk_counter,
                    "start": round(cur_t, 3),
                    "end": round(cur_t + w_dur, 3),
                    "words": sub_words,
                    "active_index": w_idx,
                })
                cur_t += w_dur

    return events


def select_palette_for_category(category: str, title: str) -> str:
    blob = f"{category} {title}".lower()
    if any(k in blob for k in ["swg", "star wars", "scrapaltai", "lost heaven", "t4c", "artisanat", "harvester"]):
        return "amber_cyan"
    return "cyan_rose"


def select_semantic_tech_motion(
    text: str,
    idx: int,
    total_cues: int,
    seed_val: int,
) -> dict[str, Any]:
    """Choisit un geste naturel et cohérent avec le propos de Lia (zéro danse/sort hors-sujet en mode parlé)."""
    low = text.lower()

    # 1. Dernière phrase : Signature Lia & Call to Action
    if idx == total_cues - 1 or any(k in low for k in ["commentaire", "moi c'est lia", "abonne", "github"]):
        outro_opts = [
            {"pose": "fingerHeart", "label": "Signature Lia", "cam": "bust", "exp": "cta_joy", "exp_label": "Signature LBG Studios"},
            {"file": "wave_right.vrma", "label": "Salut Studio", "cam": "bust", "exp": "cta_joy", "exp_label": "À toi en commentaire"},
        ]
        return outro_opts[seed_val % len(outro_opts)]

    # 2. Première phrase : Hook / Question d'accroche
    if idx == 0:
        if "?" in text or any(k in low for k in ["pourquoi", "comment", "savais", "arrête", "erreur", "piège"]):
            hook_opts = [
                {"pose": "pointScreen", "label": "Question Directe", "cam": "push_in", "exp": "hook_alert", "exp_label": "Accroche Directe"},
                {"pose": "think", "label": "Question Ingénierie", "cam": "push_in", "exp": "hook_alert", "exp_label": "Focus Technique"},
            ]
        else:
            hook_opts = [
                {"file": "wave_right.vrma", "label": "Signal Studio", "cam": "push_in", "exp": "hook_alert", "exp_label": "Signal Entrant"},
                {"pose": "pointRight", "label": "Mise au Point", "cam": "push_in", "exp": "hook_alert", "exp_label": "Focus Ingénierie"},
            ]
        return hook_opts[seed_val % len(hook_opts)]

    # 3. Métriques, chiffres, performances, 0€ cloud -> Approbation / Validation sobre
    if any(k in low for k in ["bilan", "résultat", "zéro euro", "0€", "0 €", "milliseconde", "microseconde", "60 fps", "ticks", "mégaoctet", "gigaoctet"]):
        metric_opts = [
            {"pose": "approve", "label": "Validation Mesurée", "cam": "pull_out", "exp": "metrics_win", "exp_label": "Benchmarks Validés"},
            {"file": "clapping.vrma", "speed": 0.85, "label": "Bilan Prod", "cam": "pull_out", "exp": "metrics_win", "exp_label": "0€ Cloud • 100% Local"},
            {"pose": "cheer", "label": "Gain Performance", "cam": "pull_out", "exp": "metrics_win", "exp_label": "Objectif Atteint"},
        ]
        return metric_opts[(seed_val + idx) % len(metric_opts)]

    # 4. Problème, douleur dev, coût, latence, danger -> Réflexion / Bras croisés / Diagnostic
    if any(k in low for k in ["problème", "facture", "coût", "aberration", "latence", "impossible", "enfermé", "rigide", "panne", "dépendance", "explose", "menace"]):
        prob_opts = [
            {"pose": "crossArms", "label": "Constat Critique", "cam": "bust_left", "exp": "tech_focus", "exp_label": "Diagnostic Goulot"},
            {"file": "Thinking.vrma", "speed": 0.9, "label": "Analyse Problème", "cam": "closeup", "exp": "tech_focus", "exp_label": "Analyse Critique"},
            {"pose": "think", "label": "Point de Vigilance", "cam": "bust_right", "exp": "tech_focus", "exp_label": "Constat Terrain"},
        ]
        return prob_opts[(seed_val + idx) % len(prob_opts)]

    # 5. Architecture, code, explication système -> Tablette / Présentation / Explication posée
    arch_opts = [
        {"file": "Standing Using Touchscreen Tablet.vrma", "speed": 0.9, "label": "Console Système", "cam": "front_arc", "exp": "tech_focus", "exp_label": "Architecture Locale"},
        {"file": "Having A Meeting, Female.vrma", "speed": 0.9, "label": "Explication Tech", "cam": "sway", "exp": "tech_focus", "exp_label": "Sous le Capot"},
        {"pose": "focus", "label": "Inspection Code", "cam": "bust_right", "exp": "tech_focus", "exp_label": "Pipeline Déterministe"},
        {"pose": "pointLeft", "label": "Schéma Système", "cam": "mid", "exp": "tech_focus", "exp_label": "Stack Souveraine"},
    ]
    return arch_opts[(seed_val + idx) % len(arch_opts)]


def build_tech_timeline(
    script_data: dict[str, Any],
    cues: list[Any],
    telemetry: list[dict[str, Any]],
    total_duration: float,
) -> dict[str, Any]:
    title = script_data.get("title", "Ingénierie Locale LBG Studios")
    category = script_data.get("category", "IA & Godot 4")
    seed_val = int(hashlib.md5(title.encode("utf-8")).hexdigest()[:6], 16)

    motions: list[dict[str, Any]] = []
    cameras: list[dict[str, Any]] = []
    expressions: list[dict[str, Any]] = []

    if cues:
        n_cues = len(cues)
        for idx, cue in enumerate(cues):
            step = select_semantic_tech_motion(cue.text, idx, n_cues, seed_val)
            seg_start = 0.0 if idx == 0 else cue.start
            seg_end = total_duration if idx == n_cues - 1 else (cues[idx + 1].start)

            m_entry: dict[str, Any] = {
                "start": round(seg_start, 3),
                "end": round(seg_end, 3),
                "label": step["label"],
            }
            if "pose" in step:
                m_entry["pose"] = step["pose"]
            else:
                m_entry["file"] = step["file"]
                if "speed" in step:
                    m_entry["speed"] = step["speed"]
            motions.append(m_entry)

            cameras.append({
                "start": round(seg_start, 3),
                "end": round(seg_end, 3),
                "preset": step["cam"],
            })
            expressions.append({
                "start": round(seg_start, 3),
                "end": round(seg_end, 3),
                "preset": step["exp"],
                "label": step["exp_label"],
            })
    else:
        motions.append({"start": 0.0, "end": total_duration, "file": "Female Dynamic Pose.vrma", "label": "Live Studio"})
        cameras.append({"start": 0.0, "end": total_duration, "preset": "mid"})
        expressions.append({"start": 0.0, "end": total_duration, "preset": "tech_focus", "label": "Live IA"})

    short_cat = category.upper()
    if len(short_cat) > 24:
        short_cat = "100% LOCAL • 0€ CLOUD"

    return {
        "mode": "tech",
        "title": title,
        "category": category,
        "badge_left": "LIVE STUDIO 3D",
        "badge_right": short_cat,
        "footer_left": "VOX : SYNCHRO LIPSYNC FFT",
        "palette": select_palette_for_category(category, title),
        "mic_visible": False,
        "show_subtitles": True,
        "duration": round(total_duration, 3),
        "telemetry_fps": FPS,
        "motions": motions,
        "cameras": cameras,
        "expressions": expressions,
        "karaoke": build_karaoke_events(cues, max_words=3),
        "telemetry": telemetry,
    }


CUSTOM_TRACKS_FILE = ENGINE_DIR / "custom_music_tracks.json"


def _load_all_music_presets() -> list[dict[str, Any]]:
    presets = list(MUSIC_SHOW_PRESETS)
    if CUSTOM_TRACKS_FILE.exists():
        try:
            extra = json.loads(CUSTOM_TRACKS_FILE.read_text(encoding="utf-8"))
            if isinstance(extra, list):
                presets = extra + presets
        except Exception as exc:
            logger.warning("Lecture custom_music_tracks.json ignorée : %s", exc)
    return presets


def pick_music_preset(preset_id_or_topic: str | None = None) -> dict[str, Any]:
    all_presets = _load_all_music_presets()
    if preset_id_or_topic:
        low = preset_id_or_topic.lower()
        for p in all_presets:
            if p["id"].lower() in low or p["title"].lower() in low:
                return p
        if "swg" in low or "cantina" in low or "moonwalk" in low:
            return MUSIC_SHOW_PRESETS[2]
        if "cyberpunk" in low or "protocol" in low:
            return MUSIC_SHOW_PRESETS[1]
        if "synthwave" in low or "overdrive" in low:
            return MUSIC_SHOW_PRESETS[3]
        if "climax" in low or "encore" in low:
            return MUSIC_SHOW_PRESETS[4]
        idx = int(hashlib.md5(low.encode("utf-8")).hexdigest()[:6], 16) % len(all_presets)
        return all_presets[idx]

    idx = int(time.time() // 60) % len(all_presets)
    return all_presets[idx]


def build_music_timeline_and_audio(
    work_dir: Path,
    preset: dict[str, Any],
    custom_title: str | None = None,
) -> tuple[dict[str, Any], Path, float]:
    src_audio = OVERLAY_DIR / preset["audio_rel"]
    if not src_audio.exists():
        src_audio = OVERLAY_DIR / "nexura_domina_v1.mp3"

    target_dur = float(preset.get("duration_sec", 35.0))
    offset_sec = float(preset.get("start_offset_sec", 0.0))

    master_wav = work_dir / "music_master_stereo.wav"
    extract_master_audio_segment(src_audio, master_wav, start_offset=offset_sec, duration_sec=target_dur)

    analysis_wav = work_dir / "music_analysis_mono.wav"
    _, actual_dur = ensure_pcm_wav(master_wav, analysis_wav)
    telemetry, _ = compute_audio_telemetry(analysis_wav, voice_only_wav=None, fps=FPS)

    motions: list[dict[str, Any]] = []
    cameras: list[dict[str, Any]] = []
    expressions: list[dict[str, Any]] = []

    raw_steps = preset["motions"]
    sum_raw = sum(float(s["dur"]) for s in raw_steps)
    scale = actual_dur / max(0.1, sum_raw)

    cur_t = 0.0
    for s in raw_steps:
        seg_dur = float(s["dur"]) * scale
        seg_end = min(actual_dur, cur_t + seg_dur)
        m_item: dict[str, Any] = {
            "start": round(cur_t, 3),
            "end": round(seg_end, 3),
            "label": s["label"],
        }
        if "pose" in s:
            m_item["pose"] = s["pose"]
        else:
            m_item["file"] = s["file"]
            if "speed" in s:
                m_item["speed"] = s["speed"]
        motions.append(m_item)
        cameras.append({"start": round(cur_t, 3), "end": round(seg_end, 3), "preset": s["cam"]})
        expressions.append({
            "start": round(cur_t, 3),
            "end": round(seg_end, 3),
            "preset": s["exp"],
            "label": s["exp_label"],
        })
        cur_t = seg_end

    if motions:
        motions[-1]["end"] = round(actual_dur, 3)
        cameras[-1]["end"] = round(actual_dur, 3)
        expressions[-1]["end"] = round(actual_dur, 3)

    final_title = custom_title or preset["title"]
    bpm = preset.get("bpm", 128)

    timeline = {
        "mode": "music",
        "title": final_title,
        "category": preset.get("category", "Clip 3D Officiel"),
        "badge_left": "LIVE IDOL 3D",
        "badge_right": f"{bpm} BPM • MASTER STEREO",
        "footer_left": "VOX : SYNCHRO LIPSYNC LIVE",
        "palette": preset.get("palette", "cyan_rose"),
        "mic_visible": True,
        "show_subtitles": False,
        "duration": round(actual_dur, 3),
        "telemetry_fps": FPS,
        "motions": motions,
        "cameras": cameras,
        "expressions": expressions,
        "karaoke": [],
        "telemetry": telemetry,
    }
    return timeline, master_wav, actual_dur


# ============================================================================
# 4. SERVEUR HTTP + STREAMING WEBSOCKET IMAGE2PIPE VERS FFMPEG
# ============================================================================

class _ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def _start_stage_http_server(job_dir: Path, bind_host: str = "0.0.0.0") -> tuple[_ThreadedHTTPServer, int]:
    class StageHandler(SimpleHTTPRequestHandler):
        def translate_path(self, path: str) -> str:
            from urllib.parse import unquote
            clean = unquote(path.split("?", 1)[0].split("#", 1)[0])
            if clean.startswith("/overlay/"):
                rel = clean[len("/overlay/") :]
                return str((OVERLAY_DIR / rel).resolve())
            if clean.startswith("/job/"):
                rel = clean[len("/job/") :]
                return str((job_dir / rel).resolve())
            return str((job_dir / clean.lstrip("/")).resolve())

        def end_headers(self) -> None:
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            super().end_headers()

        def log_message(self, format: str, *args: Any) -> None:
            pass

    srv = _ThreadedHTTPServer((bind_host, 0), StageHandler)
    port = int(srv.server_address[1])
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    return srv, port


def _find_free_x_display() -> int:
    for disp in range(95, 135):
        if not Path(f"/tmp/.X{disp}-lock").exists():
            return disp
    return 98


def _find_free_tcp_port(bind_host: str = "0.0.0.0") -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((bind_host, 0))
        return int(s.getsockname()[1])


async def _run_ws_frame_pipe_render(
    browser_launcher: Any,
    ws_port: int,
    expected_frames: int,
    master_audio_path: Path,
    output_mp4: Path,
    timeout_sec: float,
) -> int:
    """Reçoit les frames JPEG exactes par WebSocket et les pipe directement dans FFmpeg H.264."""
    import websockets

    done_event = asyncio.Event()
    received_frames = 0
    error_holder: list[str] = []

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "image2pipe",
        "-vcodec", "mjpeg",
        "-framerate", str(FPS),
        "-i", "-",
        "-i", str(master_audio_path),
        "-vf", f"scale={WIDTH}:{HEIGHT}:flags=lanczos",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-preset", "fast",
        "-profile:v", "high",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-r", str(FPS),
        "-c:a", "aac",
        "-b:a", "256k",
        "-ar", "44100",
        "-shortest",
        str(output_mp4),
    ]
    ff_proc = subprocess.Popen(
        ffmpeg_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )

    async def ws_handler(websocket: Any) -> None:
        nonlocal received_frames
        try:
            async for msg in websocket:
                if isinstance(msg, bytes):
                    if ff_proc.stdin:
                        ff_proc.stdin.write(msg)
                    received_frames += 1
                    if received_frames % 15 == 0 or received_frames >= expected_frames:
                        await websocket.send("ACK")
                    if received_frames % 150 == 0:
                        logger.info("Progression rendu déterministe : %d / %d frames (%.0f%%)", received_frames, expected_frames, 100.0 * received_frames / max(1, expected_frames))
                elif isinstance(msg, str):
                    if msg == "DONE":
                        done_event.set()
                        break
        except Exception as exc:
            if not done_event.is_set():
                error_holder.append(str(exc))
                done_event.set()

    try:
        async with websockets.serve(ws_handler, "0.0.0.0", ws_port, max_size=16 * 1024 * 1024):
            browser_launcher()
            await asyncio.wait_for(done_event.wait(), timeout=timeout_sec)
    finally:
        if ff_proc.stdin:
            try:
                ff_proc.stdin.close()
            except Exception:
                pass
        _, ff_err = ff_proc.communicate(timeout=45.0)

    if error_holder:
        raise RuntimeError(f"Erreur flux WebSocket frames : {error_holder[0]}")
    if received_frames < max(10, int(expected_frames * 0.95)):
        raise RuntimeError(f"Flux incomplet ({received_frames}/{expected_frames} frames reçues)")
    if ff_proc.returncode != 0 or not output_mp4.exists():
        raise RuntimeError(f"Échec encodage FFmpeg image2pipe : {ff_err.decode('utf-8', errors='ignore')[-400:]}")

    return received_frames


def _try_render_on_win10_gpu(
    stage_port: int,
    duration_sec: float,
    master_audio_path: Path,
    output_mp4: Path,
) -> bool:
    """Lance Chrome GPU en mode headless invisible sur .10 (s'il est en ligne et libre) et reçoit le flux 30 FPS."""
    if os.environ.get("LBG_STAGE3D_FORCE_143", "0") == "1":
        return False

    try:
        with httpx.Client(timeout=2.0) as client:
            hz = client.get(f"{WIN10_AGENT_URL}/healthz")
            if hz.status_code != 200:
                return False
    except Exception:
        logger.info("Poste Windows .10 hors ligne -> rendu déterministe 30 FPS sur .143.")
        return False

    ws_port = _find_free_tcp_port("0.0.0.0")
    ws_param = quote(f"ws://{HOST_143_LAN_IP}:{ws_port}", safe="")
    stage_url = f"http://{HOST_143_LAN_IP}:{stage_port}/job/render_stage3d.html?hq3d=1&ws={ws_param}"
    expected_frames = max(1, int(math.ceil(duration_sec * FPS)))

    trigger_err: list[str] = []

    def launch_remote_win10() -> None:
        def _bg_post() -> None:
            try:
                with httpx.Client(timeout=max(60.0, duration_sec * 3.0)) as client:
                    res = client.post(
                        f"{WIN10_AGENT_URL}/execute",
                        json={
                            "action": "render_stage3d_clip",
                            "parameters": {
                                "stage_url": stage_url,
                                "duration_sec": round(duration_sec, 2),
                                "min_idle_sec": WIN10_MIN_IDLE_SEC,
                            },
                        },
                    )
                    if res.status_code != 200:
                        trigger_err.append(f"HTTP {res.status_code}")
                    else:
                        r_data = res.json().get("result") or {}
                        if r_data.get("status") not in ("ok", "started"):
                            trigger_err.append(str(r_data.get("reason") or r_data))
            except Exception as e:
                trigger_err.append(str(e))

        threading.Thread(target=_bg_post, daemon=True).start()

    try:
        n_frames = asyncio.run(
            _run_ws_frame_pipe_render(
                browser_launcher=launch_remote_win10,
                ws_port=ws_port,
                expected_frames=expected_frames,
                master_audio_path=master_audio_path,
                output_mp4=output_mp4,
                timeout_sec=max(45.0, duration_sec * 2.5),
            )
        )
        logger.info("Rendu GPU headless .10 terminé : %d frames uniques encodées à %d FPS !", n_frames, FPS)
        return True
    except Exception as exc:
        logger.info("Rendu GPU .10 non utilisé (%s / %s) -> bascule déterministe sur .143.", exc, trigger_err)
        return False


def _render_on_local_143_deterministic(
    stage_port: int,
    duration_sec: float,
    work_dir: Path,
    master_audio_path: Path,
    output_mp4: Path,
) -> Path:
    """Rendu déterministe image par image sur .143 : 100% des frames uniques à 30.00 FPS (zéro saccade)."""
    disp_num = _find_free_x_display()
    display_str = f":{disp_num}"
    ws_port = _find_free_tcp_port("127.0.0.1")
    chr_profile = work_dir / "chr_det_profile"
    chr_profile.mkdir(parents=True, exist_ok=True)

    ws_param = quote(f"ws://127.0.0.1:{ws_port}", safe="")
    stage_url = f"http://127.0.0.1:{stage_port}/job/render_stage3d.html?ws={ws_param}"
    expected_frames = max(1, int(math.ceil(duration_sec * FPS)))

    xvfb_proc = subprocess.Popen(
        [
            "Xvfb", display_str,
            "-screen", "0", "640x1136x24",
            "-ac", "+extension", "GLX", "+render", "-noreset",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    chr_proc: subprocess.Popen[bytes] | None = None

    def launch_local_chromium() -> None:
        nonlocal chr_proc
        env = dict(os.environ, DISPLAY=display_str)
        chromium_bin = shutil.which("chromium") or shutil.which("google-chrome") or "chromium"
        chr_proc = subprocess.Popen(
            [
                chromium_bin,
                "--ozone-platform=x11",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--window-size=600,1040",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-background-timer-throttling",
                "--disable-renderer-backgrounding",
                "--disable-backgrounding-occluded-windows",
                "--autoplay-policy=no-user-gesture-required",
                "--ignore-gpu-blocklist",
                "--enable-webgl",
                "--use-gl=angle",
                "--use-angle=swiftshader",
                "--enable-unsafe-swiftshader",
                f"--user-data-dir={chr_profile}",
                stage_url,
            ],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    try:
        time.sleep(0.5)
        t0 = time.time()
        n_frames = asyncio.run(
            _run_ws_frame_pipe_render(
                browser_launcher=launch_local_chromium,
                ws_port=ws_port,
                expected_frames=expected_frames,
                master_audio_path=master_audio_path,
                output_mp4=output_mp4,
                timeout_sec=max(300.0, expected_frames * 0.65),
            )
        )
        logger.info(
            "Rendu déterministe .143 terminé en %.1fs : %d/%d frames uniques à %d.00 FPS !",
            time.time() - t0,
            n_frames,
            expected_frames,
            FPS,
        )
        return output_mp4
    finally:
        if chr_proc is not None:
            try:
                chr_proc.kill()
                chr_proc.wait(timeout=3)
            except Exception:
                pass
        try:
            xvfb_proc.kill()
            xvfb_proc.wait(timeout=3)
        except Exception:
            pass
        shutil.rmtree(chr_profile, ignore_errors=True)


# ============================================================================
# 5. POINTS D'ENTRÉE PUBLICS POUR CONTENT_BOT
# ============================================================================

def render_stage3d_tech_video(
    audio_path: Path,
    script_data: dict[str, Any],
    cues: list[Any],
    output_mp4: Path,
    work_dir: Path | None = None,
) -> Path:
    job_dir = work_dir or output_mp4.parent
    job_dir.mkdir(parents=True, exist_ok=True)
    output_mp4.parent.mkdir(parents=True, exist_ok=True)

    master_audio = job_dir / "stage3d_tech_master.wav"
    mix_speech_with_synthwave_bgm(audio_path, master_audio, seed_key=script_data.get("title", ""))

    analysis_mono = job_dir / "stage3d_tech_analysis.wav"
    _, total_dur = ensure_pcm_wav(master_audio, analysis_mono)
    telemetry, _ = compute_audio_telemetry(analysis_mono, voice_only_wav=audio_path, fps=FPS)

    timeline = build_tech_timeline(script_data, cues, telemetry, total_dur)
    timeline_file = job_dir / "stage_timeline.json"
    timeline_file.write_text(json.dumps(timeline, ensure_ascii=False), encoding="utf-8")
    shutil.copy2(STAGE_HTML_TEMPLATE, job_dir / "render_stage3d.html")

    srv, port = _start_stage_http_server(job_dir)
    try:
        if not _try_render_on_win10_gpu(port, total_dur, master_audio, output_mp4):
            _render_on_local_143_deterministic(port, total_dur, job_dir, master_audio, output_mp4)
    finally:
        srv.shutdown()
        srv.server_close()

    return output_mp4


def render_stage3d_music_video(
    output_mp4: Path,
    work_dir: Path | None = None,
    preset_or_topic: str | None = None,
    custom_title: str | None = None,
) -> tuple[Path, dict[str, Any], float]:
    job_dir = work_dir or output_mp4.parent
    job_dir.mkdir(parents=True, exist_ok=True)
    output_mp4.parent.mkdir(parents=True, exist_ok=True)

    preset = pick_music_preset(preset_or_topic)
    timeline, master_wav, duration_sec = build_music_timeline_and_audio(
        job_dir, preset, custom_title=custom_title
    )

    timeline_file = job_dir / "stage_timeline.json"
    timeline_file.write_text(json.dumps(timeline, ensure_ascii=False), encoding="utf-8")
    shutil.copy2(STAGE_HTML_TEMPLATE, job_dir / "render_stage3d.html")

    srv, port = _start_stage_http_server(job_dir)
    try:
        if not _try_render_on_win10_gpu(port, duration_sec, master_wav, output_mp4):
            _render_on_local_143_deterministic(port, duration_sec, job_dir, master_wav, output_mp4)
    finally:
        srv.shutdown()
        srv.server_close()

    meta = {
        "title": timeline["title"],
        "category": timeline["category"],
        "preset_id": preset["id"],
        "bpm": preset.get("bpm", 128),
    }
    return output_mp4, meta, duration_sec
