"""tts_service.py — Service de synthèse vocale (TTS / Text-to-Speech) & Génération de Visèmes.

Supporte :
- Intégration de serveurs TTS locaux (ex: Piper, Kokoro sur .111 ou Docker)
- Génération déterministe de visèmes VRM (morph targets aa, ih, ou, ee, oh) synchronisés
- Catalogue de voix françaises et multilingues
- Mode mock & recommandation client Web Speech API pour fallback sans latence
"""

from __future__ import annotations

import base64
import logging
import os
import re
from typing import Any

import httpx

LOG = logging.getLogger(__name__)

DEFAULT_TTS_URL = "http://192.168.0.111:5000/v1/audio/speech"
DEFAULT_TIMEOUT_SEC = 15.0

VOICES_CATALOG: list[dict[str, Any]] = [
    {
        "id": "fr_FR-siwis-medium",
        "name": "Siwis (Femme, Expressive)",
        "language": "fr",
        "gender": "female",
        "description": "Voix féminine chaleureuse et fluide, recommandée pour Compagnon Lyra.",
        "is_default": True,
    },
    {
        "id": "fr_FR-upmc-pierre",
        "name": "Pierre (Homme, Atelier)",
        "language": "fr",
        "gender": "male",
        "description": "Voix masculine posée et claire, idéale pour les PNJ et le cockpit.",
        "is_default": False,
    },
    {
        "id": "en_US-lessac-medium",
        "name": "Lessac (English, Female)",
        "language": "en",
        "gender": "female",
        "description": "Standard English female clear voice.",
        "is_default": False,
    },
]


def tts_enabled() -> bool:
    return os.environ.get("LBG_TTS_ENABLED", "true").lower() in ("1", "true", "yes", "on")


def tts_upstream_url() -> str:
    return os.environ.get("LBG_TTS_URL") or os.environ.get("PIPER_URL") or os.environ.get("KOKORO_URL") or ""


def tts_provider() -> str:
    url = tts_upstream_url()
    if url:
        return "piper"
    if os.environ.get("LBG_TTS_MOCK", "").lower() in ("1", "true", "yes"):
        return "mock"
    return "web_speech"


def get_available_voices() -> list[dict[str, Any]]:
    return [v.copy() for v in VOICES_CATALOG]


async def check_tts_health() -> dict[str, Any]:
    url = tts_upstream_url()
    provider = tts_provider()

    if not tts_enabled():
        return {
            "ok": False,
            "enabled": False,
            "provider": provider,
            "detail": "tts_disabled_by_config",
        }

    if provider == "mock":
        return {
            "ok": True,
            "enabled": True,
            "provider": "mock",
            "detail": "mock_tts_provider_active",
        }

    if not url:
        return {
            "ok": True,
            "enabled": True,
            "provider": "web_speech",
            "detail": "client_speech_synthesis_recommended",
        }

    health_url = url.replace("/audio/speech", "/health")
    if health_url == url:
        health_url = url.rstrip("/") + "/health"

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(health_url)
            return {
                "ok": resp.status_code == 200,
                "enabled": True,
                "provider": "piper",
                "upstream_url": url,
                "status_code": resp.status_code,
            }
    except Exception as exc:  # noqa: BLE001
        LOG.warning("Échec check santé TTS %s : %s", url, exc)
        return {
            "ok": False,
            "enabled": True,
            "provider": "piper",
            "upstream_url": url,
            "error": str(exc),
            "detail": "upstream_unreachable_fallback_web_speech",
        }


def generate_visemes_from_text(text: str, speed: float = 1.0) -> list[dict[str, Any]]:
    """Génère une séquence de visèmes VRM synchronisés (aa, ih, ou, ee, oh) à partir d'un texte."""
    clean = re.sub(r"[^\w\s\'-]", "", text).lower()
    words = clean.split()
    if not words:
        return []

    # Cadence moyenne : ~16 caractères / seconde à vitesse 1.0
    effective_speed = max(0.5, min(2.0, speed))
    char_duration = 0.065 / effective_speed

    visemes: list[dict[str, Any]] = []
    current_time = 0.08  # Petit temps de démarrage

    for word in words:
        i = 0
        wlen = len(word)
        while i < wlen:
            ch = word[i]
            # Détection de digrammes et voyelles
            if i + 1 < wlen and word[i : i + 2] in ("ou", "où"):
                visemes.append({
                    "time_offset": round(current_time, 3),
                    "duration": round(char_duration * 1.8, 3),
                    "viseme": "ou",
                    "weight": 0.85,
                })
                current_time += char_duration * 1.8
                i += 2
            elif i + 2 < wlen and word[i : i + 3] == "eau":
                visemes.append({
                    "time_offset": round(current_time, 3),
                    "duration": round(char_duration * 2.0, 3),
                    "viseme": "oh",
                    "weight": 0.90,
                })
                current_time += char_duration * 2.0
                i += 3
            elif i + 1 < wlen and word[i : i + 2] in ("au", "ai", "ei"):
                v = "oh" if word[i : i + 2] == "au" else "ee"
                visemes.append({
                    "time_offset": round(current_time, 3),
                    "duration": round(char_duration * 1.8, 3),
                    "viseme": v,
                    "weight": 0.85,
                })
                current_time += char_duration * 1.8
                i += 2
            elif ch in ("a", "à", "â"):
                visemes.append({
                    "time_offset": round(current_time, 3),
                    "duration": round(char_duration * 1.4, 3),
                    "viseme": "aa",
                    "weight": 0.88,
                })
                current_time += char_duration * 1.4
                i += 1
            elif ch in ("o", "ô"):
                visemes.append({
                    "time_offset": round(current_time, 3),
                    "duration": round(char_duration * 1.4, 3),
                    "viseme": "oh",
                    "weight": 0.85,
                })
                current_time += char_duration * 1.4
                i += 1
            elif ch in ("e", "é", "è", "ê", "ë"):
                visemes.append({
                    "time_offset": round(current_time, 3),
                    "duration": round(char_duration * 1.3, 3),
                    "viseme": "ee",
                    "weight": 0.78,
                })
                current_time += char_duration * 1.3
                i += 1
            elif ch in ("i", "y", "î", "ï"):
                visemes.append({
                    "time_offset": round(current_time, 3),
                    "duration": round(char_duration * 1.2, 3),
                    "viseme": "ih",
                    "weight": 0.82,
                })
                current_time += char_duration * 1.2
                i += 1
            elif ch in ("u", "û", "ü"):
                visemes.append({
                    "time_offset": round(current_time, 3),
                    "duration": round(char_duration * 1.3, 3),
                    "viseme": "ou",
                    "weight": 0.75,
                })
                current_time += char_duration * 1.3
                i += 1
            else:
                # Consonne : avance rapide du curseur
                current_time += char_duration * 0.9
                i += 1
        # Pause inter-mots
        current_time += 0.045 / effective_speed

    return visemes


async def synthesize_speech(
    text: str,
    voice: str = "fr_FR-siwis-medium",
    speed: float = 1.0,
) -> dict[str, Any]:
    """Synthétise la voix et retourne le payload avec audio et visèmes synchronisés."""
    if not tts_enabled():
        raise RuntimeError("tts_disabled")

    clean_text = text.strip()
    if not clean_text:
        raise ValueError("empty_text")

    provider = tts_provider()
    url = tts_upstream_url()
    visemes = generate_visemes_from_text(clean_text, speed=speed)
    total_dur = (visemes[-1]["time_offset"] + visemes[-1]["duration"]) if visemes else 0.5

    if provider == "piper" and url:
        try:
            payload = {
                "text": clean_text,
                "voice": voice,
                "speed": speed,
            }
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT_SEC) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    audio_b64 = base64.b64encode(resp.content).decode("ascii")
                    return {
                        "ok": True,
                        "text": clean_text,
                        "voice": voice,
                        "provider": "piper",
                        "audio_b64": audio_b64,
                        "format": "audio/wav",
                        "duration_sec": round(total_dur, 2),
                        "visemes": visemes,
                    }
                LOG.warning("Erreur amont TTS HTTP %d", resp.status_code)
        except Exception as exc:  # noqa: BLE001
            LOG.warning("Fallback TTS après exception amont: %s", exc)

    # Mode mock / web_speech : retourne les métadonnées et visèmes avec audio mock
    mock_wav_header = b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
    mock_b64 = base64.b64encode(mock_wav_header).decode("ascii")

    return {
        "ok": True,
        "text": clean_text,
        "voice": voice,
        "provider": provider,
        "audio_b64": mock_b64,
        "format": "audio/wav",
        "duration_sec": round(total_dur, 2),
        "visemes": visemes,
    }
