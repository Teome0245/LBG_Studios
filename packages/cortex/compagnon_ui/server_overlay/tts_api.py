"""API TTS Compagnon — proxy Edge / Piper.

Routes :
  GET  /tts/          — status (enabled + health upstream)
  GET  /tts/health    — alias health
  POST /tts           — {text, voice?} → audio/mpeg (Edge) ou audio/wav (Piper)
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from src.services.tts import (
    default_voice,
    piper_base_url,
    sanitize_for_speech,
    synthesize,
    tts_enabled,
    tts_fallback,
    tts_health,
    tts_provider,
)

router = APIRouter(tags=["tts"])


class TtsBody(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)
    voice: str | None = None


@router.get("/tts")
@router.get("/tts/")
@router.get("/tts/health")
async def tts_status() -> dict[str, Any]:
    h = await tts_health()
    return {
        "ok": bool(h.get("ok")),
        "enabled": tts_enabled(),
        "provider": tts_provider(),
        "fallback": tts_fallback(),
        "piper_url": piper_base_url(),
        "voice": default_voice(),
        "upstream": h,
    }


@router.post("/tts")
@router.post("/tts/")
async def tts_synthesize(body: TtsBody) -> Response:
    if not tts_enabled():
        raise HTTPException(status_code=503, detail="tts_disabled")
    try:
        audio, meta = await synthesize(body.text, voice=body.voice)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        msg = str(exc)
        code = 503 if "disabled" in msg or "piper_http_503" in msg or "edge_tts_missing" in msg else 502
        raise HTTPException(status_code=code, detail=msg[:300]) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"tts_proxy:{exc}") from exc
    headers = {
        "Cache-Control": "no-store",
        "X-LBG-TTS-Voice": meta.get("voice") or default_voice(),
        "X-LBG-TTS-Chars": meta.get("chars") or str(len(sanitize_for_speech(body.text))),
        "X-LBG-TTS-Provider": meta.get("provider") or tts_provider(),
    }
    if meta.get("fallback_from"):
        headers["X-LBG-TTS-Fallback-From"] = meta["fallback_from"]
    return Response(
        content=audio,
        media_type=meta.get("content_type") or "audio/wav",
        headers=headers,
    )
