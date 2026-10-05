"""Routes Self-State Agency B/C — status + goals Lia."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services import self_state as svc_self


router = APIRouter(tags=["self"])


class SelfStatusResponse(BaseModel):
    enabled: bool
    path: str
    exists: bool
    state: dict[str, object] = Field(default_factory=dict)
    meta: dict[str, object] = Field(default_factory=dict)


class GoalCompleteRequest(BaseModel):
    goal_id: str = Field(..., min_length=1)
    last_action: str | None = None
    decay_drive: bool = True
    decay_amount: float = Field(default=0.25, ge=0.0, le=1.0)


class DriveBumpRequest(BaseModel):
    key: str = Field(..., min_length=1)
    delta: float = Field(..., ge=-1.0, le=1.0)


class WillUpsertRequest(BaseModel):
    id: str = Field(..., min_length=1, max_length=80)
    title: str = Field(..., min_length=1, max_length=160)
    summary: str = Field(default="", max_length=280)
    kind: str = Field(default="evolution", max_length=48)
    source: str = Field(default="spontaneity", max_length=48)
    meta: dict[str, object] = Field(default_factory=dict)


class WillConsumeRequest(BaseModel):
    will_id: str = Field(..., min_length=1, max_length=80)
    reason: str = Field(default="done", max_length=48)


@router.get("/self/status", response_model=SelfStatusResponse)
def self_status(ensure_goals: bool = True) -> SelfStatusResponse:
    if svc_self.self_state_enabled():
        try:
            svc_self.purge_blocked_pending_wills()
        except Exception:
            pass
    if ensure_goals and svc_self.self_state_enabled():
        try:
            svc_self.ensure_lia_goals()
        except Exception:
            pass
    meta = svc_self.meta_status()
    state = svc_self.get_state()
    return SelfStatusResponse(
        enabled=bool(meta.get("enabled")),
        path=str(meta.get("path") or ""),
        exists=bool(meta.get("exists")),
        state=state,
        meta=meta,
    )


@router.post("/self/goals/complete")
def self_goal_complete(payload: GoalCompleteRequest) -> dict[str, object]:
    if not svc_self.self_state_enabled():
        raise HTTPException(status_code=503, detail="self_state disabled")
    try:
        st = svc_self.complete_goal(
            payload.goal_id,
            last_action=payload.last_action,
            decay_drive=payload.decay_drive,
            decay_amount=payload.decay_amount,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"ok": True, "state": st or {}}


@router.post("/self/drives/bump")
def self_drive_bump(payload: DriveBumpRequest) -> dict[str, object]:
    if not svc_self.self_state_enabled():
        raise HTTPException(status_code=503, detail="self_state disabled")
    st = svc_self.bump_drive(payload.key, payload.delta)
    return {"ok": True, "state": st or {}}


@router.post("/self/will")
def self_will_upsert(payload: WillUpsertRequest) -> dict[str, object]:
    """Injecte une envie Self (évolution spontanée / studio) — pas d'auto-Réel."""
    if not svc_self.self_state_enabled():
        raise HTTPException(status_code=503, detail="self_state disabled")
    try:
        st = svc_self.upsert_pending_will(
            will_id=payload.id,
            title=payload.title,
            summary=payload.summary,
            kind=payload.kind,
            source=payload.source,
            meta=dict(payload.meta or {}),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"ok": True, "state": st or {}}


@router.post("/self/will/complete")
def self_will_complete(payload: WillConsumeRequest) -> dict[str, object]:
    """Consomme une envie (retire de pending_will) après Agir / auto L1."""
    if not svc_self.self_state_enabled():
        raise HTTPException(status_code=503, detail="self_state disabled")
    try:
        st = svc_self.complete_pending_will(payload.will_id, reason=payload.reason or "done")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"ok": True, "state": st or {}}


@router.post("/self/will/dismiss")
def self_will_dismiss(payload: WillConsumeRequest) -> dict[str, object]:
    """Ignore une envie (retire de pending_will)."""
    if not svc_self.self_state_enabled():
        raise HTTPException(status_code=503, detail="self_state disabled")
    try:
        st = svc_self.dismiss_pending_will(payload.will_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"ok": True, "state": st or {}}
