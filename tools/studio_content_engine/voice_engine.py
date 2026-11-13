"""voice_engine.py — Synthèse vocale Piper TTS locale (.111:8098) et calage temporel des sous-titres.

- Envoie les phrases du script au sidecar Piper TTS.
- Concatène les fichiers WAV en un seul flux audio continu.
- Génère les métadonnées temporelles exactes pour chaque phrase et mot.
- Génère un fichier .ass stylisé (format TikTok / Shorts) pour l'incrustation vidéo.
"""

from __future__ import annotations

import asyncio
import io
import json
import logging
import os
import re
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

PIPER_URL = os.environ.get("LBG_PIPER_URL", "http://192.168.0.111:8098/v1/tts")
# Par défaut : Voix Vivienne Multilingual Neural (ultra-fluide, diction parfaite, 0€)
DEFAULT_VOICE = os.environ.get("LBG_STUDIO_VOICE", "fr-FR-VivienneMultilingualNeural")
DEFAULT_LENGTH_SCALE = float(os.environ.get("LBG_STUDIO_VOICE_SPEED", "0.92"))
INITIAL_SILENCE_SEC = float(os.environ.get("LBG_STUDIO_INITIAL_SILENCE", "2.0"))


# Dictionnaire de correction phonétique pour la voix française (GitHub -> Guite Heube, etc.)
PHONETIC_ORAL_RULES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bgithub\b", re.IGNORECASE), "Guite Heube"),
    (re.compile(r"\bopen source\b", re.IGNORECASE), "opène source"),
    (re.compile(r"\bapi\b", re.IGNORECASE), "A P I"),
    (re.compile(r"\bllm\b", re.IGNORECASE), "L L M"),
    (re.compile(r"\bframework\b", re.IGNORECASE), "fraimwork"),
]


def phonetic_for_speech(text: str) -> str:
    """Adapte les termes techniques anglophones pour une prononciation naturelle en français."""
    spoken = text
    for pattern, replacement in PHONETIC_ORAL_RULES:
        spoken = pattern.sub(replacement, spoken)
    return spoken


@dataclass
class SentenceCue:
    text: str
    start: float
    end: float
    duration: float
    words: list[str]


async def _synthesize_edge_tts(text: str, voice: str, out_path: Path) -> float:
    """Synthétise une phrase via Edge TTS Neural (Vivienne) et convertit en WAV 22050 Hz."""
    import edge_tts

    tmp_mp3 = out_path.with_suffix(".mp3")
    comm = edge_tts.Communicate(text, voice)
    await comm.save(str(tmp_mp3))

    # Conversion en WAV pcm_s16le 22050 Hz mono pour le pipeline RMS / sync
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(tmp_mp3), "-ar", "22050", "-ac", "1", str(out_path)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if tmp_mp3.exists():
        tmp_mp3.unlink()

    with wave.open(str(out_path), "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return float(frames) / float(rate)


def _synthesize_piper(
    text: str,
    out_path: Path,
    url: str = PIPER_URL,
    voice: str = "fr_FR-upmc-medium",
    length_scale: float = DEFAULT_LENGTH_SCALE,
) -> float:
    """Synthétise une phrase via Piper TTS local (.111:8098)."""
    payload: dict[str, Any] = {
        "text": text,
        "voice": voice,
        "length_scale": length_scale,
    }
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
        return float(frames) / float(rate)


def synthesize_sentence(
    text: str,
    out_path: Path,
    url: str = PIPER_URL,
    voice: str = DEFAULT_VOICE,
    length_scale: float = DEFAULT_LENGTH_SCALE,
) -> float:
    """Synthétise une phrase via le moteur approprié (Edge Neural ou Piper local)."""
    # Si la voix est un modèle Edge Neural (ex: fr-FR-VivienneMultilingualNeural)
    if "neural" in voice.lower() or voice.startswith("fr-FR-"):
        try:
            return asyncio.run(_synthesize_edge_tts(text, voice, out_path))
        except Exception as e:
            logger.warning(
                "Échec Edge TTS (%s) : %s. Repli sur Piper local (fr_FR-upmc-medium)...",
                voice,
                e,
            )
            return _synthesize_piper(
                text,
                out_path,
                url=url,
                voice="fr_FR-upmc-medium",
                length_scale=length_scale,
            )

    # Sinon : Piper TTS local par défaut
    return _synthesize_piper(
        text, out_path, url=url, voice=voice, length_scale=length_scale
    )


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
        spoken_text = phonetic_for_speech(clean_text)
        dur = synthesize_sentence(
            spoken_text, part_file, voice=voice, length_scale=length_scale
        )
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
    logger.info(
        "Audio complet assemblé sans clipping : %s (durée: %.2fs)",
        final_audio_path,
        total_duration,
    )
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
    """Génère un fichier de sous-titres .ass au format TikTok ultra dynamique mot-à-mot.

    Chaque mot prononcé s'illumine en direct en jaune néon pop (Karaoké CapCut / TikTok)
    pour capter en permanence l'attention du spectateur.
    """
    ass_content = """[Script Info]
Title: LBG Studios TikTok Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: TikTokDefault,Liberation Sans,68,&H00FFFFFF,&H0000FFFF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,6,2,2,60,60,400,1
Style: TikTokHighlight,Liberation Sans,72,&H0000FFFF,&H00FFFFFF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,7,3,2,60,60,400,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    for cue in cues:
        words = cue.words
        n_words = len(words)
        if not words:
            continue

        # Découpage en blocs d'impact de 3 à 5 mots pour éviter les lignes trop larges
        max_words_per_chunk = 4
        chunks = []
        for i in range(0, n_words, max_words_per_chunk):
            sub_words = words[i : i + max_words_per_chunk]
            # Calcul du timing proportionnel dans la phrase
            t_chunk_start = cue.start + (cue.duration * (i / max(1, n_words)))
            t_chunk_end = cue.start + (
                cue.duration * (min(n_words, i + max_words_per_chunk) / max(1, n_words))
            )
            chunks.append((sub_words, t_chunk_start, t_chunk_end))

        for chunk_words, t_start, t_end in chunks:
            chunk_duration = max(0.1, t_end - t_start)
            # Pondération par longueur des mots pour un timing oral naturel
            weights = [max(2, len(re.sub(r"[^\w]", "", w))) for w in chunk_words]
            total_weight = sum(weights)

            cur_word_t = t_start
            for w_idx, active_word in enumerate(chunk_words):
                w_dur = chunk_duration * (weights[w_idx] / max(1, total_weight))
                w_start_str = format_ass_time(cur_word_t)
                w_end_str = format_ass_time(cur_word_t + w_dur)
                cur_word_t += w_dur

                # Assembler le texte avec le mot actif surligné en jaune néon pop
                rendered_words = []
                for j, word in enumerate(chunk_words):
                    clean_w = word.upper()
                    if j == w_idx:
                        # Mot actif : Jaune néon éclatant (&H0000FFFF&) avec pop de taille (+14%)
                        rendered_words.append(
                            r"{\c&H0000FFFF&\b1\fscx114\fscy114}"
                            + clean_w
                            + r"{\rTikTokDefault}"
                        )
                    else:
                        rendered_words.append(clean_w)

                line_text = " ".join(rendered_words)
                ass_content += f"Dialogue: 0,{w_start_str},{w_end_str},TikTokDefault,,0,0,0,,{line_text}\n"

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

    return out_path
