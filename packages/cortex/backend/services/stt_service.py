"""stt_service.py — Service de transcription vocale (STT / Speech-to-Text).

Supporte :
- Intégration Whisper OpenAI-compatible (ex: faster-whisper ou whisper.cpp sur .111)
- Détection / health check de l'amont STT
- Mode mock / web_speech fallback pour développement local sans GPU
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

LOG = logging.getLogger(__name__)

DEFAULT_WHISPER_URL = "http://192.168.0.111:9000/v1/audio/transcriptions"
DEFAULT_TIMEOUT_SEC = 25.0
MAX_AUDIO_BYTES = 15 * 1024 * 1024  # 15 Mo


def stt_enabled() -> bool:
    return os.environ.get("LBG_STT_ENABLED", "true").lower() in ("1", "true", "yes", "on")


def stt_upstream_url() -> str:
    return os.environ.get("LBG_STT_URL") or os.environ.get("WHISPER_URL") or ""


def stt_provider() -> str:
    url = stt_upstream_url()
    if url:
        return "whisper"
    if os.environ.get("LBG_STT_MOCK", "").lower() in ("1", "true", "yes"):
        return "mock"
    return "web_speech"


async def check_stt_health() -> dict[str, Any]:
    url = stt_upstream_url()
    provider = stt_provider()

    if not stt_enabled():
        return {
            "ok": False,
            "enabled": False,
            "provider": provider,
            "detail": "stt_disabled_by_config",
        }

    if provider == "mock":
        return {
            "ok": True,
            "enabled": True,
            "provider": "mock",
            "detail": "mock_provider_active",
        }

    if not url:
        return {
            "ok": True,
            "enabled": True,
            "provider": "web_speech",
            "detail": "client_web_speech_api_recommended",
        }

    health_url = url.replace("/audio/transcriptions", "/healthz")
    if health_url == url:
        health_url = url.rstrip("/") + "/healthz"

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(health_url)
            return {
                "ok": resp.status_code == 200,
                "enabled": True,
                "provider": "whisper",
                "upstream_url": url,
                "status_code": resp.status_code,
            }
    except Exception as exc:
        return {
            "ok": False,
            "enabled": True,
            "provider": "whisper",
            "upstream_url": url,
            "error": str(exc),
            "fallback": "web_speech",
        }


async def transcribe_audio_bytes(
    audio_bytes: bytes,
    filename: str = "audio.wav",
    language: str = "fr",
) -> dict[str, Any]:
    if not stt_enabled():
        raise RuntimeError("stt_disabled")

    if not audio_bytes:
        raise ValueError("empty_audio_content")

    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise ValueError(f"audio_too_large: max {MAX_AUDIO_BYTES} bytes")

    provider = stt_provider()

    if provider == "mock":
        return {
            "text": "Transcription simulée du message vocal.",
            "language": language,
            "provider": "mock",
            "duration_sec": 1.5,
        }

    url = stt_upstream_url()
    if not url:
        raise RuntimeError("no_upstream_whisper_configured_use_web_speech")

    files = {
        "file": (filename, audio_bytes, "audio/wav"),
    }
    data = {
        "model": "whisper-1",
        "language": language,
    }

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT_SEC) as client:
            resp = await client.post(url, files=files, data=data)
            if resp.status_code != 200:
                raise RuntimeError(f"whisper_error_status_{resp.status_code}: {resp.text[:200]}")
            result = resp.json()
            return {
                "text": result.get("text", "").strip(),
                "language": language,
                "provider": "whisper",
                "raw": result,
            }
    except httpx.RequestError as exc:
        raise RuntimeError(f"whisper_connection_failed: {exc}") from exc
