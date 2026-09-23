"""Compagnon — analyse d'images via Ollama vision (.110)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ._common import LOG
from ._models import OkEnvelope, VisionAskBody

router = APIRouter(tags=["pilot-vision"])


@router.post("/vision-ask", response_model=OkEnvelope)
async def pilot_vision_ask(payload: VisionAskBody) -> dict[str, object]:
    """Analyse multimodale pour le Compagnon (`POST /v1/pilot/vision-ask`).

    Corps : ``prompt`` + ``images`` (data URI ou base64). Modèle défaut :
    ``LBG_VISION_LLM_MODEL`` (abliterated 27b sur ``.110``).
    """
    from services.vision_ask import vision_ask

    try:
        response = await vision_ask(
            prompt=payload.prompt or "",
            images=list(payload.images or []),
            profile=payload.profile,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        LOG.warning("pilot.vision-ask failed: %s", exc)
        return {
            "ok": False,
            "error": str(exc),
            "response": {
                "role": "assistant",
                "content": f"Analyse image impossible : {exc}",
                "source": "error",
                "model": None,
                "provider": "ollama",
            },
        }
    except Exception as exc:
        LOG.exception("pilot.vision-ask unexpected")
        raise HTTPException(status_code=502, detail=f"{type(exc).__name__}: {exc}") from exc

    return {"ok": True, "response": response}
