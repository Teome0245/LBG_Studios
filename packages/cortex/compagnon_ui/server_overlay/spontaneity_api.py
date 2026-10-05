"""API Spontanéité Compagnon — propose + feedback + évolution.

Routes :
  POST /spontaneity/propose
  POST /spontaneity/feedback
  GET  /spontaneity/evolution
  GET  /spontaneity/
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.services.spontaneity import (
    evolution_snapshot,
    promote_ready_seeds,
    propose_spontaneous,
    record_feedback,
    spontaneity_enabled,
)

router = APIRouter(prefix="/spontaneity", tags=["spontaneity"])


class ProposeBody(BaseModel):
    id: str = ""
    message: str = ""
    kind: str = ""
    offerType: str = ""
    intents: list[dict[str, Any]] = Field(default_factory=list)
    primary: dict[str, Any] | None = None
    goal: dict[str, Any] | None = None
    fromSelf: bool = False
    offer: bool = True
    context: dict[str, Any] = Field(default_factory=dict)


class FeedbackBody(BaseModel):
    id: str = ""
    kind: str = "dismiss"  # accept | dismiss
    themes: list[str] = Field(default_factory=list)
    message: str = ""
    evolution_seed: str | None = None


@router.get("/")
async def spontaneity_root() -> dict[str, Any]:
    snap = evolution_snapshot()
    return {
        "ok": True,
        "enabled": spontaneity_enabled(),
        "service": "spontaneity",
        **{k: v for k, v in snap.items() if k != "ok"},
    }


@router.get("/evolution")
async def get_evolution() -> dict[str, Any]:
    return evolution_snapshot()


@router.post("/promote")
async def post_promote(force: bool = False) -> dict[str, Any]:
    """Pousse les seeds prêtes vers Self pending_will (.140)."""
    return promote_ready_seeds(force=force)


@router.post("/propose")
async def post_propose(body: ProposeBody) -> dict[str, Any]:
    offer = body.model_dump()
    return await propose_spontaneous(offer)


@router.post("/feedback")
async def post_feedback(body: FeedbackBody) -> dict[str, Any]:
    return record_feedback(
        offer_id=body.id or "unknown",
        kind=body.kind,
        themes=list(body.themes or []),
        message=body.message or None,
        evolution_seed=body.evolution_seed,
    )
