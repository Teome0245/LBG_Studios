"""Routage intentions via orchestrateur (public + interne)."""

from __future__ import annotations

import time
import uuid

from fastapi import APIRouter, Header, HTTPException, Request

from models.intents import IntentRequest, IntentResponse
from services import metrics as svc_metrics
from services.brain_lyra_sync import merge_brain_lyra_if_configured
from services.lyra_regulator import regulate_lyra_if_configured
from services.mmmorpg_commit import try_commit_dialogue
from services.mmo_lyra_sync import merge_mmo_lyra_if_configured

from ._common import (
    LOG,
    OrchestratorClient,
    OrchestratorError,
    internal_rate_limit_allow,
    mmmorpg_player_id_from_pilot,
    require_internal_token,
)
from ._models import PilotRouteResponse

router = APIRouter()


def _trace_from_request(request: Request) -> str:
    return getattr(request.state, "trace_id", None) or uuid.uuid4().hex


async def pilot_route_impl(*, payload: IntentRequest, trace_id: str) -> dict[str, object]:
    t0 = time.perf_counter()
    svc_metrics.inc("pilot_route_requests_total")
    payload.context.setdefault("_trace_id", trace_id)
    await merge_mmo_lyra_if_configured(payload.context)
    await merge_brain_lyra_if_configured(payload.context)
    await regulate_lyra_if_configured(payload.context)
    lyra_after_merge = payload.context.get("lyra") if isinstance(payload.context, dict) else None
    try:
        client = OrchestratorClient.from_env()
        result: IntentResponse = await client.route_intent(payload)
    except OrchestratorError as e:
        svc_metrics.inc("pilot_route_orchestrator_errors_total")
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        return {"ok": False, "trace_id": trace_id, "elapsed_ms": elapsed_ms, "error": str(e)}

    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    svc_metrics.inc("pilot_route_success_total")
    out = {"ok": True, "trace_id": trace_id, "elapsed_ms": elapsed_ms, "result": result.model_dump()}
    if isinstance(lyra_after_merge, dict):
        meta = lyra_after_merge.get("meta")
        if isinstance(meta, dict) and meta:
            out["lyra_meta"] = meta

    try:
        commit = result.output.get("commit") if isinstance(result.output, dict) else None
        if isinstance(commit, dict):
            npc_id = commit.get("npc_id") or payload.context.get("world_npc_id")
            flags = commit.get("flags") if isinstance(commit.get("flags"), dict) else None
            if isinstance(npc_id, str) and npc_id.strip():
                commit_result = await try_commit_dialogue(
                    trace_id=trace_id,
                    npc_id=npc_id,
                    flags=flags,
                    player_id=mmmorpg_player_id_from_pilot(payload),
                )
                if commit_result is not None:
                    out["commit_result"] = commit_result
    except Exception:
        pass

    return out


@router.post("/route", tags=["pilot"], response_model=PilotRouteResponse)
async def pilot_route_intent_timed(request: Request, payload: IntentRequest) -> PilotRouteResponse:
    """
    Route une intention via l'orchestrator et renvoie aussi une mesure simple de latence.

    But : instrumenter l'UI `/pilot/` sans changer le contrat public `/v1/intents/route`.
    """
    trace_id = _trace_from_request(request)
    return PilotRouteResponse.model_validate(await pilot_route_impl(payload=payload, trace_id=trace_id))


@router.post("/internal/route", tags=["pilot"], response_model=PilotRouteResponse)
async def pilot_route_internal_service(
    request: Request,
    payload: IntentRequest,
    x_lbg_service_token: str | None = Header(default=None, alias="X-LBG-Service-Token"),
    x_lbg_trace_id: str | None = Header(default=None, alias="X-LBG-Trace-Id"),
) -> PilotRouteResponse:
    """
    Endpoint service→service pour le pont `mmmorpg_server` → backend.
    Protégé par token optionnel + rate-limit best-effort.
    """
    require_internal_token(x_lbg_service_token)
    remote = (request.client.host if request.client else "unknown") or "unknown"
    if not internal_rate_limit_allow(key=str(remote)):
        LOG.warning("pilot.internal_route rate_limited (remote=%s)", remote)
        raise HTTPException(status_code=429, detail={"error": "rate_limited", "hint": "slow down"})

    trace_id = (x_lbg_trace_id or "").strip() or _trace_from_request(request)
    world_npc_id = payload.context.get("world_npc_id") if isinstance(payload.context, dict) else None
    actor_id = getattr(payload, "actor_id", None)
    LOG.info(
        "pilot.internal_route start (trace_id=%s remote=%s actor_id=%s world_npc_id=%s)",
        trace_id,
        remote,
        actor_id,
        world_npc_id,
    )
    out = await pilot_route_impl(payload=payload, trace_id=trace_id)
    ok = bool(out.get("ok")) if isinstance(out, dict) else False
    elapsed_ms = out.get("elapsed_ms") if isinstance(out, dict) else None
    if ok:
        LOG.info("pilot.internal_route ok (trace_id=%s elapsed_ms=%s)", trace_id, elapsed_ms)
    else:
        LOG.warning("pilot.internal_route error (trace_id=%s elapsed_ms=%s)", trace_id, elapsed_ms)
    return PilotRouteResponse.model_validate(out)
