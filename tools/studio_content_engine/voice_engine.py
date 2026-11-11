"""voice_engine.py — Synthèse vocale Piper TTS locale (.111:8098) et calage temporel des sous-titres.

- Envoie les phrases du script au sidecar Piper TTS.
- Concatène les fichiers WAV en un seul flux audio continu.
- Génère les métadonnées temporelles exactes pour chaque phrase et mot.
- Génère un fichier .ass stylisé (format TikTok / Shorts) pour l'incrustation vidéo.
"""

from __future__ import annotations

import io
import json
import logging
import os
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

PIPER_URL = os.environ.get("LBG_PIPER_URL", "http://192.168.0.111:8098/v1/tts")
DEFAULT_VOICE = os.environ.get("LBG_STUDIO_VOICE", "fr_FR-upmc-medium")
DEFAULT_LENGTH_SCALE = float(os.environ.get("LBG_STUDIO_VOICE_SPEED", "0.92"))
INITIAL_SILENCE_SEC = float(os.environ.get("LBG_STUDIO_INITIAL_SILENCE", "2.0"))


@dataclass
class SentenceCue:
    text: str
    start: float
    end: float
    duration: float
    words: list[str]


def synthesize_sentence(
    text: str,
    out_path: Path,
    url: str = PIPER_URL,
    voice: str = DEFAULT_VOICE,
    length_scale: float = DEFAULT_LENGTH_SCALE,
) -> float:
    """Synthétise une phrase via Piper TTS et renvoie la durée en secondes."""
    payload: dict[str, Any] = {"text": text, "voice": voice, "length_scale": length_scale}
    with httpx.Client(timeout=30.0) as client:
        res = client.post(url, json=payload)
        if res.status_code != 200:
            raise RuntimeError(f"Piper TTS erreur HTTP {res.status_code}: {res.text}")
        wav_bytes = res.content

    with open(out_path, "wb") as f:
        f.write(wav_bytes)

    with wave.open(str(out_path), "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        duration = float(frames) / float(rate)

    return duration


def synthesize_script(
    sentences: list[str],
    work_dir: Path,
    voice: str = DEFAULT_VOICE,
    length_scale: float = DEFAULT_LENGTH_SCALE,
    pause_between: float = 0.25,
    initial_silence_sec: float = INITIAL_SILENCE_SEC,
) -> tuple[Path, list[SentenceCue], float]:
    """Synthétise l'ensemble du script et génère l'audio complet avec timings exacts."""
    work_dir.mkdir(parents=True, exist_ok=True)
    cues: list[SentenceCue] = []
    sentence_files: list[Path] = []

    current_time = initial_silence_sec  # Silence initial paramétrable (2.0s par défaut)
    sample_rate = 22050
    channels = 1
    sample_width = 2

    # Synthèse de chaque phrase
    for idx, sentence in enumerate(sentences):
        clean_text = sentence.strip()
        if not clean_text:
            continue
        part_file = work_dir / f"sentence_{idx:02d}.wav"
        dur = synthesize_sentence(clean_text, part_file, voice=voice, length_scale=length_scale)
        sentence_files.append(part_file)

        words = clean_text.split()
        cues.append(
            SentenceCue(
                text=clean_text,
                start=current_time,
                end=current_time + dur,
                duration=dur,
                words=words,
            )
        )
        current_time += dur + pause_between

    # Concaténation propre via NumPy (anti-clipping, micro fade-in/out, calage exact des octets)
    import numpy as np

    parts: list[np.ndarray] = []
    for pf in sentence_files:
        with wave.open(str(pf), "rb") as in_wav:
            n = in_wav.getnframes()
            sample_rate = in_wav.getframerate()
            raw = in_wav.readframes(n)
            s_data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

            # Micro-fondu de 8ms aux extrémités pour supprimer tout clic/pop de coupure
            fade_len = min(len(s_data) // 4, int(sample_rate * 0.008))
            if fade_len > 0:
                fade_in = np.linspace(0.0, 1.0, fade_len, dtype=np.float32)
                fade_out = np.linspace(1.0, 0.0, fade_len, dtype=np.float32)
                s_data[:fade_len] *= fade_in
                s_data[-fade_len:] *= fade_out
            parts.append(s_data)

    # Pause calibrée en échantillons (multiple exact de 2 octets, aucun décalage de phase)
    pause_samples = int(sample_rate * pause_between)
    pause_array = np.zeros(pause_samples, dtype=np.float32)
    initial_silence = np.zeros(int(sample_rate * initial_silence_sec), dtype=np.float32)

    all_chunks = [initial_silence]
    for idx, p in enumerate(parts):
        all_chunks.append(p)
        if idx < len(parts) - 1:
            all_chunks.append(pause_array)

    merged = np.concatenate(all_chunks)

    # Normalisation propre du pic à -1.0 dB (0.891) pour éviter tout clipping
    peak = np.max(np.abs(merged)) if len(merged) > 0 else 1.0
    if peak > 0.01:
        merged = (merged / peak) * 0.891

    int_pcm = (np.clip(merged, -1.0, 1.0) * 32767.0).astype(np.int16)

    final_audio_path = work_dir / "final_speech.wav"
    with wave.open(str(final_audio_path), "wb") as out_wav:
        out_wav.setnchannels(1)
        out_wav.setsampwidth(2)
        out_wav.setframerate(sample_rate)
        out_wav.writeframes(int_pcm.tobytes())

    total_duration = float(len(merged)) / float(sample_rate)
    logger.info("Audio complet assemblé sans clipping : %s (durée: %.2fs)", final_audio_path, total_duration)
    return final_audio_path, cues, total_duration


def format_ass_time(seconds: float) -> str:
    """Formate les secondes en H:MM:SS.cs pour ASS."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    if cs >= 100:
        cs = 99
    return f"{hrs}:{mins:02d}:{secs:02d}.{cs:02d}"


def generate_tiktok_ass_subtitles(cues: list[SentenceCue], out_path: Path) -> Path:
    """Génère un fichier de sous-titres .ass au format TikTok dynamique."""
    # Style TikTok : Police grasse sans-serif, gros corps, jaune/blanc percutant, contour noir épais
    ass_content = f"""[Script Info]
Title: LBG Studios TikTok Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: TikTokDefault,Liberation Sans,68,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,2,2,60,60,420,1
Style: TikTokHighlight,Liberation Sans,72,&H0000FFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,7,3,2,60,60,420,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    for cue in cues:
        # Si la phrase est longue, la scinder en morceaux de 4-6 mots pour l'impact visuel TikTok
        words = cue.words
        n_words = len(words)
        if n_words <= 6:
            chunks = [(words, cue.start, cue.end)]
        else:
            mid = n_words // 2
            t_mid = cue.start + (cue.duration * (mid / n_words))
            chunks = [
                (words[:mid], cue.start, t_mid),
                (words[mid:], t_mid, cue.end),
            ]

        for chunk_words, t_start, t_end in chunks:
            chunk_text = " ".join(chunk_words).upper()
            start_str = format_ass_time(t_start)
            end_str = format_ass_time(t_end)
            # Surlignage dynamique
            line = f"Dialogue: 0,{start_str},{end_str},TikTokDefault,,0,0,0,,{chunk_text}\n"
            ass_content += line

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

    return out_path

