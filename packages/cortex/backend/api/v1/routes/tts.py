"""Route API v1 TTS — Synthèse vocale & Lip-Sync Visèmes VRM."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.tts_service import (
    check_tts_health,
    get_available_voices,
    synthesize_speech,
    tts_enabled,
    tts_provider,
    tts_upstream_url,
)

router = APIRouter()


class TtsStatusResponse(BaseModel):
    ok: bool
    enabled: bool
    provider: str
    upstream_url: str | None = None
    detail: str | None = None
    supported_languages: list[str] = ["fr", "en"]


class TtsSynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Texte à synthétiser")
    voice: str = Field(default="fr_FR-siwis-medium", description="Identifiant de la voix")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Facteur de vitesse")


class VisemeFrame(BaseModel):
    time_offset: float
    duration: float
    viseme: str
    weight: float


class TtsSynthesizeResponse(BaseModel):
    ok: bool
    text: str
    voice: str
    provider: str
    audio_b64: str
    format: str = "audio/wav"
    duration_sec: float
    visemes: list[VisemeFrame]


@router.get("", response_model=TtsStatusResponse)
@router.get("/", response_model=TtsStatusResponse)
@router.get("/health", response_model=TtsStatusResponse)
async def get_tts_status() -> dict[str, Any]:
    health = await check_tts_health()
    return {
        "ok": bool(health.get("ok")),
        "enabled": tts_enabled(),
        "provider": tts_provider(),
        "upstream_url": tts_upstream_url() or None,
        "detail": health.get("detail") or health.get("error"),
        "supported_languages": ["fr", "en"],
    }


@router.get("/voices")
async def get_voices() -> dict[str, Any]:
    return {
        "ok": True,
        "voices": get_available_voices(),
        "default_voice": "fr_FR-siwis-medium",
    }


@router.post("/synthesize", response_model=TtsSynthesizeResponse)
async def post_synthesize(req: TtsSynthesizeRequest) -> dict[str, Any]:
    if not tts_enabled():
        raise HTTPException(status_code=503, detail="tts_disabled")

    try:
        res = await synthesize_speech(text=req.text, voice=req.voice, speed=req.speed)
        return res
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        msg = str(exc)
        code = 503 if "disabled" in msg else 502
        raise HTTPException(status_code=code, detail=msg) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"tts_error: {exc}") from exc
