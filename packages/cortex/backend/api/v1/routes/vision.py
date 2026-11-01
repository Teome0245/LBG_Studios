"""Routes REST `/v1/vision` — Vision Contextuelle Ponctuelle sur Demande / Incident (Phase 3 Ticket 1.2)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.vision_service import (
    analyze_window_snippet,
    get_vision_vlm_config,
    is_vision_context_request,
)

router = APIRouter()


class VisionAnalyzeRequest(BaseModel):
    prompt: str = Field(default="Inspecte cette fenêtre active et explique l'erreur éventuelle.")
    image_b64: str | None = Field(default=None)
    window_title: str = Field(default="")
    process_name: str = Field(default="")
    ocr_text: str = Field(default="")
    allow_remote_vlm: bool = Field(default=False)


@router.get("/health")
async def vision_health() -> dict[str, Any]:
    cfg = get_vision_vlm_config()
    return {
        "ok": True,
        "ticket": "1.2",
        **cfg,
    }


@router.post("/analyze")
async def vision_analyze_endpoint(req: VisionAnalyzeRequest) -> dict[str, Any]:
    try:
        res = await analyze_window_snippet(
            image_b64=req.image_b64,
            prompt=req.prompt,
            window_title=req.window_title,
            process_name=req.process_name,
            ocr_text=req.ocr_text,
            allow_remote_vlm=req.allow_remote_vlm,
        )
        res["intent_detected"] = is_vision_context_request(req.prompt)
        return res
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

