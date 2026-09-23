"""Proxies orchestrateur : capabilities, brain, jobs."""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from config import get_settings

from ._common import httpx, orchestrator_base
from ._models import ActionProposalBody, CompanionReviewBody, JobApproveBody, JobCreateBody, OkEnvelope

router = APIRouter()

@router.get("/capabilities", tags=["pilot"], response_model=OkEnvelope)
async def pilot_capabilities() -> dict[str, object]:
    """Proxy vers l’orchestrator : liste des capabilities (même origine que /pilot/)."""
    orch_url = get_settings().orchestrator_base()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{orch_url}/v1/capabilities")
        if r.status_code != 200:
            return {
                "ok": False,
                "error": f"orchestrator HTTP {r.status_code}",
                "body": r.text[:500],
            }
        return {"ok": True, **r.json()}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/action-proposal", tags=["pilot"], response_model=OkEnvelope)
async def pilot_action_proposal(payload: ActionProposalBody) -> dict[str, object]:
    """Proxy same-origin vers l’orchestrator : proposition d'action sans exécution."""
    orch_url = get_settings().orchestrator_base()
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.post(f"{orch_url}/v1/action-proposal", json=payload.model_dump())
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return {"ok": True, **data} if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/companion/review-proposal", tags=["pilot"], response_model=OkEnvelope)
async def pilot_companion_review_proposal(payload: CompanionReviewBody) -> dict[str, object]:
    """Contre-pouvoir Compagnon — revue avant dry-run→réel (Prométhée-gate)."""
    orch_url = get_settings().orchestrator_base()
    try:
        # LLM optionnel peut être lent — timeout large ; défaut déterministe ≈ instantané
        async with httpx.AsyncClient(timeout=45.0) as client:
            r = await client.post(
                f"{orch_url}/v1/companion/review-proposal",
                json=payload.model_dump(),
            )
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return {"ok": True, **data} if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}




@router.get("/orchestrator/brain/status", tags=["pilot"], response_model=OkEnvelope)
async def pilot_proxy_orchestrator_brain_status() -> dict[str, object]:
    """Proxy same-origin vers `GET orchestrator /v1/brain/status` (évite CORS)."""
    orch_url = get_settings().orchestrator_base()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{orch_url}/v1/brain/status")
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return {"ok": True, **data} if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/orchestrator/proactive/status", tags=["pilot"], response_model=OkEnvelope)
async def pilot_proxy_orchestrator_proactive_status() -> dict[str, object]:
    """Proxy same-origin vers `GET orchestrator /v1/proactive/status` (humeur / tension)."""
    orch_url = get_settings().orchestrator_base()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{orch_url}/v1/proactive/status")
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return {"ok": True, **data} if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/orchestrator/self/status", tags=["pilot"], response_model=OkEnvelope)
async def pilot_proxy_orchestrator_self_status(ensure_goals: bool = False) -> dict[str, object]:
    """Proxy `GET /v1/self/status` — slim pour Compagnon (pas de dump goals done)."""
    orch_url = get_settings().orchestrator_base()
    try:
        params = {"ensure_goals": "1" if ensure_goals else "0"}
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(f"{orch_url}/v1/self/status", params=params)
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        if not isinstance(data, dict):
            return {"ok": True, "payload": data}
        state = data.get("state") if isinstance(data.get("state"), dict) else {}
        goals = state.get("goals") if isinstance(state.get("goals"), list) else []
        active = [
            g
            for g in goals
            if isinstance(g, dict) and str(g.get("status") or "").lower() in ("active", "pending", "open")
        ][:5]
        will = state.get("pending_will") if isinstance(state.get("pending_will"), list) else []
        slim_state = {
            "identity": state.get("identity") if isinstance(state.get("identity"), dict) else {},
            "drives": state.get("drives") if isinstance(state.get("drives"), dict) else {},
            "intent": state.get("intent") if isinstance(state.get("intent"), dict) else {},
            "beliefs": state.get("beliefs") if isinstance(state.get("beliefs"), dict) else {},
            "pending_will": will[:8],
            "goals": active,
            "goals_active_count": len(active),
            "goals_total": len(goals),
            "last_tick": state.get("last_tick") if isinstance(state.get("last_tick"), dict) else {},
        }
        return {
            "ok": True,
            "enabled": bool(data.get("enabled")),
            "path": data.get("path"),
            "exists": bool(data.get("exists")),
            "state": slim_state,
            "meta": data.get("meta") if isinstance(data.get("meta"), dict) else {},
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/orchestrator/brain/toggle", tags=["pilot"], response_model=OkEnvelope)
async def pilot_proxy_orchestrator_brain_toggle(payload: dict[str, object]) -> dict[str, object]:
    """Proxy same-origin vers `POST orchestrator /v1/brain/toggle`."""
    orch_url = get_settings().orchestrator_base()
    enabled = payload.get("enabled")
    if not isinstance(enabled, bool):
        raise HTTPException(status_code=400, detail={"error": "bad_request", "hint": "body: {enabled: boolean}"})
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.post(f"{orch_url}/v1/brain/toggle", json={"enabled": enabled})
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return {"ok": True, **data} if isinstance(data, dict) else {"ok": True, "payload": data}
    except HTTPException:
        raise
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/orchestrator/brain/approve", tags=["pilot"], response_model=OkEnvelope)
async def pilot_proxy_orchestrator_brain_approve(payload: dict[str, object]) -> dict[str, object]:
    """Proxy same-origin vers `POST orchestrator /v1/brain/approve`."""
    orch_url = get_settings().orchestrator_base()
    rid = payload.get("request_id")
    if not isinstance(rid, str) or not rid.strip():
        raise HTTPException(status_code=400, detail={"error": "bad_request", "hint": "body: {request_id: string}"})
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.post(f"{orch_url}/v1/brain/approve", json={"request_id": rid.strip()})
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return {"ok": True, **data} if isinstance(data, dict) else {"ok": True, "payload": data}
    except HTTPException:
        raise
    except Exception as e:
        return {"ok": False, "error": str(e)}



@router.post("/jobs", tags=["pilot"], response_model=OkEnvelope)
async def pilot_jobs_create(payload: JobCreateBody) -> dict[str, object]:
    """Proxy same-origin vers `POST orchestrator /v1/jobs` (créer un job autonome)."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(f"{orchestrator_base()}/v1/jobs", json=payload.model_dump())
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return {"ok": True, **data} if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/jobs", tags=["pilot"], response_model=OkEnvelope)
async def pilot_jobs_list(actor_id: str | None = None) -> dict[str, object]:
    """Proxy same-origin vers `GET orchestrator /v1/jobs` (liste, filtre optionnel `actor_id`)."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{orchestrator_base()}/v1/jobs", params={"actor_id": actor_id} if actor_id else None)
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return {"ok": True, **data} if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/jobs/{job_id}", tags=["pilot"], response_model=OkEnvelope)
async def pilot_jobs_get(job_id: str) -> dict[str, object]:
    """Proxy same-origin vers `GET orchestrator /v1/jobs/{id}` (état complet)."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{orchestrator_base()}/v1/jobs/{job_id}")
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return {"ok": True, **data} if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/jobs/{job_id}/approve", tags=["pilot"], response_model=OkEnvelope)
async def pilot_jobs_approve(job_id: str, payload: JobApproveBody) -> dict[str, object]:
    """Proxy same-origin vers `POST orchestrator /v1/jobs/{id}/approve`."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(f"{orchestrator_base()}/v1/jobs/{job_id}/approve", json=payload.model_dump())
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return {"ok": True, **data} if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/jobs/{job_id}/cancel", tags=["pilot"], response_model=OkEnvelope)
async def pilot_jobs_cancel(job_id: str) -> dict[str, object]:
    """Proxy same-origin vers `POST orchestrator /v1/jobs/{id}/cancel`."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(f"{orchestrator_base()}/v1/jobs/{job_id}/cancel")
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return {"ok": True, **data} if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/jobs/{job_id}/advance", tags=["pilot"], response_model=OkEnvelope)
async def pilot_jobs_advance(job_id: str) -> dict[str, object]:
    """Proxy same-origin vers `POST orchestrator /v1/jobs/{id}/advance` (avancer d'une étape)."""
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            r = await client.post(f"{orchestrator_base()}/v1/jobs/{job_id}/advance")
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return {"ok": True, **data} if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/jobs/{job_id}/events", tags=["pilot"])
async def pilot_jobs_events_stream(job_id: str):
    """Proxy same-origin vers l'instance orchestrateur pour le flux SSE des événements."""
    async def event_generator():
        client = httpx.AsyncClient(timeout=3600.0)
        try:
            async with client.stream("GET", f"{orchestrator_base()}/v1/jobs/{job_id}/events") as response:
                async for line in response.aiter_lines():
                    yield line + "\n"
        except Exception as e:
            yield f"data: {json.dumps({'kind': 'stream_error', 'error': str(e)})}\n\n"
        finally:
            await client.aclose()

    return StreamingResponse(event_generator(), media_type="text/event-stream")
