"""Helpers partagés des routes Pilot."""

from __future__ import annotations

import logging
import time

import httpx
from fastapi import HTTPException

from config import get_settings
from models.intents import IntentRequest
from services.orchestrator_client import OrchestratorClient, OrchestratorError

LOG = logging.getLogger("pilot")

__all__ = [
    "LOG",
    "OrchestratorClient",
    "OrchestratorError",
    "httpx",
    "internal_rate_limit_allow",
    "lbg_ia_backend_base_url",
    "mmmorpg_player_id_from_pilot",
    "orchestrator_base",
    "pilot_agent_dialogue_invoke_timeout_s",
    "pilot_lbg_ia_http_timeout_s",
    "require_internal_token",
]


class _TokenBucket:
    __slots__ = ("rps", "burst", "tokens", "last_s")

    def __init__(self, *, rps: float, burst: int) -> None:
        self.rps = float(rps)
        self.burst = int(burst)
        self.tokens = float(burst)
        self.last_s = time.monotonic()


_internal_rl_buckets: dict[str, _TokenBucket] = {}


def mmmorpg_player_id_from_pilot(payload: IntentRequest) -> str | None:
    """Identifiant joueur sur le serveur WS (UUID session), pour commits inventaire / quête côté joueur."""
    ctx = payload.context if isinstance(payload.context, dict) else {}
    for key in ("mmmorpg_player_id", "player_id"):
        v = ctx.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
    aid = (payload.actor_id or "").strip()
    if aid.lower().startswith("player:"):
        rest = aid.split(":", 1)[-1].strip()
        if rest:
            return rest
    return None


def internal_rate_limit_allow(*, key: str) -> bool:
    """
    Rate-limit best-effort pour l'endpoint interne (service→service).
    Activé si `LBG_PILOT_INTERNAL_RL_RPS` et `LBG_PILOT_INTERNAL_RL_BURST` > 0.
    """
    settings = get_settings()
    try:
        rps = float(settings.lbg_pilot_internal_rl_rps or 0)
        burst = int(settings.lbg_pilot_internal_rl_burst or 0)
    except Exception:
        rps, burst = 0.0, 0
    if rps <= 0.0 or burst <= 0:
        return True

    now = time.monotonic()
    b = _internal_rl_buckets.get(key)
    if b is None or b.rps != rps or b.burst != burst:
        b = _TokenBucket(rps=rps, burst=burst)
        _internal_rl_buckets[key] = b

    dt = max(0.0, now - b.last_s)
    b.tokens = min(float(b.burst), b.tokens + dt * b.rps)
    b.last_s = now
    if b.tokens >= 1.0:
        b.tokens -= 1.0
        return True
    return False


def require_internal_token(got: str | None) -> None:
    expected = get_settings().lbg_pilot_internal_token.strip()
    if not expected:
        return
    if not (isinstance(got, str) and got == expected):
        raise HTTPException(
            status_code=401,
            detail={"error": "unauthorized", "hint": "missing/invalid X-LBG-Service-Token"},
        )


def pilot_agent_dialogue_invoke_timeout_s() -> float:
    return get_settings().pilot_agent_dialogue_invoke_timeout_s()


def lbg_ia_backend_base_url() -> str | None:
    return get_settings().lbg_ia_backend_base_url()


def pilot_lbg_ia_http_timeout_s() -> float:
    return get_settings().pilot_lbg_ia_http_timeout_s()


def orchestrator_base() -> str:
    return get_settings().orchestrator_base()
