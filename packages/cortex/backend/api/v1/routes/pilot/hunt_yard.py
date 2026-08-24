"""Cour de chasse — sandbox combat Lia / Nix / Mira (sans Core3)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from lbg_agents.hunt_yard import session_reset, session_run, session_snapshot, session_tick

router = APIRouter()


def _seed_from(payload: dict[str, object] | None) -> int:
    if not isinstance(payload, dict):
        return 1
    raw = payload.get("seed")
    try:
        return max(1, min(int(raw), 999_999))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 1


def _n_from(payload: dict[str, object] | None, *, default: int = 1, cap: int = 80) -> int:
    if not isinstance(payload, dict):
        return default
    raw = payload.get("n", payload.get("ticks", default))
    try:
        return max(1, min(int(raw), cap))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


@router.get("/hunt-yard", tags=["pilot"])
async def hunt_yard_get() -> dict[str, object]:
    return session_snapshot()


@router.post("/hunt-yard/reset", tags=["pilot"])
async def hunt_yard_reset(payload: dict[str, object] | None = None) -> dict[str, object]:
    return session_reset(seed=_seed_from(payload))


@router.post("/hunt-yard/tick", tags=["pilot"])
async def hunt_yard_tick(payload: dict[str, object] | None = None) -> dict[str, object]:
    return session_tick(_n_from(payload, default=1, cap=80))


@router.post("/hunt-yard/run", tags=["pilot"])
async def hunt_yard_run(payload: dict[str, object] | None = None) -> dict[str, object]:
    if not isinstance(payload, dict):
        payload = {}
    raw = payload.get("max_ticks", 350)
    try:
        max_ticks = max(10, min(int(raw), 800))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail={"error": "bad_request", "hint": "max_ticks entier"})
    return session_run(max_ticks=max_ticks)
