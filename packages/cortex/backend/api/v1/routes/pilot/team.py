"""Proxies équipe orchestrateur (tasks, memory, campus)."""

from __future__ import annotations

from fastapi import APIRouter

from ._common import httpx, orchestrator_base
from ._models import (
    OkEnvelope,
    TeamApproveBody,
    TeamCreateBody,
    TeamMemoryBody,
    TeamMessageBody,
    TeamPlanBody,
    TeamRunBody,
)

router = APIRouter()

@router.get("/team/meta", tags=["pilot"], response_model=OkEnvelope)
async def pilot_team_meta() -> dict[str, object]:
    """Proxy vers `GET orchestrator /v1/team/meta` (alias rôles + sous-projets)."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{orchestrator_base()}/v1/team/meta")
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return {"ok": True, **data} if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/team/plan", tags=["pilot"], response_model=OkEnvelope)
async def pilot_team_plan(payload: TeamPlanBody) -> dict[str, object]:
    """Proxy same-origin vers `POST orchestrator /v1/team/plan` (LLM possible → timeout long)."""
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(f"{orchestrator_base()}/v1/team/plan", json=payload.model_dump())
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return {"ok": True, **data} if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}



@router.get("/team/messages", tags=["pilot"], response_model=OkEnvelope)
async def pilot_team_messages_list(
    task_id: str | None = None,
    kind: str | None = None,
    from_agent: str | None = None,
    to_agent: str | None = None,
    limit: int = 100,
) -> dict[str, object]:
    """Proxy → `GET /v1/team/messages` (bus ADR 0019)."""
    try:
        params: dict[str, object] = {"limit": max(1, min(limit, 500))}
        if task_id:
            params["task_id"] = task_id
        if kind:
            params["kind"] = kind
        if from_agent:
            params["from_agent"] = from_agent
        if to_agent:
            params["to_agent"] = to_agent
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{orchestrator_base()}/v1/team/messages", params=params)
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return {"ok": True, **data} if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/team/messages", tags=["pilot"], response_model=OkEnvelope)
async def pilot_team_messages_create(payload: TeamMessageBody) -> dict[str, object]:
    """Proxy → `POST /v1/team/messages`."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                f"{orchestrator_base()}/v1/team/messages",
                json=payload.model_dump(),
            )
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return {"ok": True, **data} if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/team/memory", tags=["pilot"], response_model=OkEnvelope)
async def pilot_team_memory_list(
    agent_id: str | None = None,
    kind: str | None = None,
    tag: str | None = None,
    limit: int = 50,
) -> dict[str, object]:
    """Proxy → `GET /v1/team/memory`."""
    try:
        params: dict[str, object] = {"limit": max(1, min(limit, 200))}
        if agent_id:
            params["agent_id"] = agent_id
        if kind:
            params["kind"] = kind
        if tag:
            params["tag"] = tag
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{orchestrator_base()}/v1/team/memory", params=params)
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return {"ok": True, **data} if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/team/memory", tags=["pilot"], response_model=OkEnvelope)
async def pilot_team_memory_append(payload: TeamMemoryBody) -> dict[str, object]:
    """Proxy → `POST /v1/team/memory`."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                f"{orchestrator_base()}/v1/team/memory",
                json=payload.model_dump(),
            )
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return {"ok": True, **data} if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/team/tasks", tags=["pilot"], response_model=OkEnvelope)
async def pilot_team_create(payload: TeamCreateBody) -> dict[str, object]:
    """Proxy same-origin vers `POST orchestrator /v1/team/tasks`."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(f"{orchestrator_base()}/v1/team/tasks", json=payload.model_dump())
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return {"ok": True, **data} if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/team/tasks", tags=["pilot"], response_model=OkEnvelope)
async def pilot_team_list(
    role: str | None = None,
    status: str | None = None,
    actor_id: str | None = None,
    limit: int = 100,
) -> dict[str, object]:
    """Proxy same-origin vers `GET orchestrator /v1/team/tasks`."""
    try:
        params: dict[str, object] = {"limit": limit}
        if role:
            params["role"] = role
        if status:
            params["status"] = status
        if actor_id:
            params["actor_id"] = actor_id
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{orchestrator_base()}/v1/team/tasks", params=params)
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return {"ok": True, **data} if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/team/tasks/{task_id}", tags=["pilot"], response_model=OkEnvelope)
async def pilot_team_get(task_id: str) -> dict[str, object]:
    """Proxy same-origin vers `GET orchestrator /v1/team/tasks/{id}`."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{orchestrator_base()}/v1/team/tasks/{task_id}")
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return {"ok": True, **data} if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/team/tasks/{task_id}/approve", tags=["pilot"], response_model=OkEnvelope)
async def pilot_team_approve(task_id: str, payload: TeamApproveBody) -> dict[str, object]:
    """Proxy same-origin vers `POST orchestrator /v1/team/tasks/{id}/approve`."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                f"{orchestrator_base()}/v1/team/tasks/{task_id}/approve",
                json=payload.model_dump(),
            )
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return {"ok": True, **data} if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/team/tasks/{task_id}/run", tags=["pilot"], response_model=OkEnvelope)
async def pilot_team_run(task_id: str, payload: TeamRunBody | None = None) -> dict[str, object]:
    """Proxy same-origin vers `POST orchestrator /v1/team/tasks/{id}/run`."""
    body = payload.model_dump() if payload else {}
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            r = await client.post(
                f"{orchestrator_base()}/v1/team/tasks/{task_id}/run",
                json=body,
            )
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return {"ok": True, **data} if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/team/tasks/{task_id}/cancel", tags=["pilot"], response_model=OkEnvelope)
async def pilot_team_cancel(task_id: str) -> dict[str, object]:
    """Proxy same-origin vers `POST orchestrator /v1/team/tasks/{id}/cancel`."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(f"{orchestrator_base()}/v1/team/tasks/{task_id}/cancel")
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return {"ok": True, **data} if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/team/presence/snapshot", tags=["pilot"], response_model=OkEnvelope)
async def pilot_team_presence_snapshot() -> dict[str, object]:
    """Proxy same-origin vers `GET orchestrator /v1/team/presence/snapshot`."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{orchestrator_base()}/v1/team/presence/snapshot")
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return data if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/team/presence/history", tags=["pilot"], response_model=OkEnvelope)
async def pilot_team_presence_history(limit: int = 50) -> dict[str, object]:
    """Proxy same-origin vers `GET orchestrator /v1/team/presence/history`."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                f"{orchestrator_base()}/v1/team/presence/history",
                params={"limit": max(1, min(limit, 200))},
            )
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return data if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/team/campus/status", tags=["pilot"], response_model=OkEnvelope)
async def pilot_team_campus_status() -> dict[str, object]:
    """Proxy → `GET /v1/team/campus/status` (Lyra)."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(f"{orchestrator_base()}/v1/team/campus/status")
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return data if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/team/fleet", tags=["pilot"], response_model=OkEnvelope)
async def pilot_team_fleet() -> dict[str, object]:
    """Proxy → `GET /v1/team/fleet` (supervision agents / jobs / L2)."""
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(f"{orchestrator_base()}/v1/team/fleet")
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return data if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/team/ops_health_pilot", tags=["pilot"], response_model=OkEnvelope)
async def pilot_team_ops_health_pilot(payload: dict[str, object] | None = None) -> dict[str, object]:
    """Proxy → `POST /v1/team/ops_health_pilot` (dry-run par défaut)."""
    body = payload if isinstance(payload, dict) else {}
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(f"{orchestrator_base()}/v1/team/ops_health_pilot", json=body)
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return data if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/team/smoke_lan_mission", tags=["pilot"], response_model=OkEnvelope)
async def pilot_team_smoke_lan_mission_get() -> dict[str, object]:
    """Proxy → `GET /v1/team/smoke_lan_mission`."""
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(f"{orchestrator_base()}/v1/team/smoke_lan_mission")
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return data if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/team/smoke_lan_mission", tags=["pilot"], response_model=OkEnvelope)
async def pilot_team_smoke_lan_mission_create(payload: dict[str, object] | None = None) -> dict[str, object]:
    """Proxy → `POST /v1/team/smoke_lan_mission`."""
    body = payload if isinstance(payload, dict) else {}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(f"{orchestrator_base()}/v1/team/smoke_lan_mission", json=body)
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return data if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/team/smoke_lan_mission/tick", tags=["pilot"], response_model=OkEnvelope)
async def pilot_team_smoke_lan_mission_tick(payload: dict[str, object] | None = None) -> dict[str, object]:
    """Proxy → `POST /v1/team/smoke_lan_mission/tick`."""
    body = payload if isinstance(payload, dict) else {}
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(f"{orchestrator_base()}/v1/team/smoke_lan_mission/tick", json=body)
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return data if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/team/smoke_lan_mission/cancel", tags=["pilot"], response_model=OkEnvelope)
async def pilot_team_smoke_lan_mission_cancel(payload: dict[str, object] | None = None) -> dict[str, object]:
    """Proxy → `POST /v1/team/smoke_lan_mission/cancel`."""
    _ = payload
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(f"{orchestrator_base()}/v1/team/smoke_lan_mission/cancel", json={})
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return data if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/team/pygmalion_assets_pilot", tags=["pilot"], response_model=OkEnvelope)
async def pilot_team_pygmalion_assets_pilot(payload: dict[str, object] | None = None) -> dict[str, object]:
    """Proxy → `POST /v1/team/pygmalion_assets_pilot`."""
    body = payload if isinstance(payload, dict) else {}
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(f"{orchestrator_base()}/v1/team/pygmalion_assets_pilot", json=body)
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return data if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/team/campus/act", tags=["pilot"], response_model=OkEnvelope)
async def pilot_team_campus_act(payload: dict[str, object] | None = None) -> dict[str, object]:
    """Proxy → `POST /v1/team/campus/act`."""
    body = payload if isinstance(payload, dict) else {}
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(f"{orchestrator_base()}/v1/team/campus/act", json=body)
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return data if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/team/campus/mission", tags=["pilot"], response_model=OkEnvelope)
async def pilot_team_campus_mission(payload: dict[str, object]) -> dict[str, object]:
    """Proxy → `POST /v1/team/campus/mission`."""
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            r = await client.post(f"{orchestrator_base()}/v1/team/campus/mission", json=payload)
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return data if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/team/evolution/lead", tags=["pilot"], response_model=OkEnvelope)
async def pilot_team_evolution_lead(payload: dict[str, object]) -> dict[str, object]:
    """Proxy → `POST /v1/team/evolution/lead` (veille silencieuse, pas d'onglet)."""
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(f"{orchestrator_base()}/v1/team/evolution/lead", json=payload)
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return data if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/team/evolution/leads", tags=["pilot"], response_model=OkEnvelope)
async def pilot_team_evolution_leads(limit: int = 20) -> dict[str, object]:
    """Proxy → `GET /v1/team/evolution/leads`."""
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(
                f"{orchestrator_base()}/v1/team/evolution/leads",
                params={"limit": max(1, min(100, int(limit or 20)))},
            )
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return data if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/team/campus/mission/close", tags=["pilot"], response_model=OkEnvelope)
async def pilot_team_campus_mission_close(payload: dict[str, object] | None = None) -> dict[str, object]:
    """Proxy → `POST /v1/team/campus/mission/close`."""
    body = payload if isinstance(payload, dict) else {}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(f"{orchestrator_base()}/v1/team/campus/mission/close", json=body)
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return data if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/team/campus/mission/closure", tags=["pilot"], response_model=OkEnvelope)
async def pilot_team_campus_mission_closure() -> dict[str, object]:
    """Proxy → `GET /v1/team/campus/mission/closure`."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(f"{orchestrator_base()}/v1/team/campus/mission/closure")
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return data if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/team/memory/prune", tags=["pilot"], response_model=OkEnvelope)
async def pilot_team_memory_prune(payload: dict[str, object] | None = None) -> dict[str, object]:
    """Proxy → `POST /v1/team/memory/prune`."""
    body = payload if isinstance(payload, dict) else {}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(f"{orchestrator_base()}/v1/team/memory/prune", json=body)
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return {"ok": True, **data} if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/team/campus/conduct", tags=["pilot"], response_model=OkEnvelope)
async def pilot_team_campus_conduct(payload: dict[str, object] | None = None) -> dict[str, object]:
    """Proxy → `POST /v1/team/campus/conduct`."""
    body = payload if isinstance(payload, dict) else {}
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(f"{orchestrator_base()}/v1/team/campus/conduct", json=body)
        if r.status_code != 200:
            return {"ok": False, "error": f"orchestrator HTTP {r.status_code}", "body": r.text[:500]}
        data = r.json()
        return data if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}
