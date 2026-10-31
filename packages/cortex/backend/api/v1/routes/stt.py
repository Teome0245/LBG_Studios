"""Route API v1 STT — Transcription vocale / Speech-to-Text."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from services.stt_service import (
    check_stt_health,
    stt_enabled,
    stt_provider,
    stt_upstream_url,
    transcribe_audio_bytes,
)

router = APIRouter()


class SttStatusResponse(BaseModel):
    ok: bool
    enabled: bool
    provider: str
    upstream_url: str | None = None
    detail: str | None = None
    supported_languages: list[str] = ["fr", "en"]


class SttTranscriptionResponse(BaseModel):
    text: str
    language: str = "fr"
    provider: str = "whisper"
    duration_sec: float | None = None


@router.get("", response_model=SttStatusResponse)
@router.get("/", response_model=SttStatusResponse)
@router.get("/health", response_model=SttStatusResponse)
async def get_stt_status() -> dict[str, Any]:
    health = await check_stt_health()
    return {
        "ok": bool(health.get("ok")),
        "enabled": stt_enabled(),
        "provider": stt_provider(),
        "upstream_url": stt_upstream_url() or None,
        "detail": health.get("detail") or health.get("error"),
        "supported_languages": ["fr", "en"],
    }


@router.post("", response_model=SttTranscriptionResponse)
@router.post("/", response_model=SttTranscriptionResponse)
async def post_transcribe(
    file: UploadFile = File(...),
    language: str = Form(default="fr"),
) -> dict[str, Any]:
    if not stt_enabled():
        raise HTTPException(status_code=503, detail="stt_disabled")

    try:
        content = await file.read()
        res = await transcribe_audio_bytes(content, filename=file.filename or "audio.wav", language=language)
        return res
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        msg = str(exc)
        code = 503 if "disabled" in msg or "no_upstream" in msg else 502
        raise HTTPException(status_code=code, detail=msg) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"stt_error: {exc}") from exc
