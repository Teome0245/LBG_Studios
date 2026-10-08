"""
API équipe virtuelle studio (phase A + ADR 0019 fondation).

- ``POST /v1/team/plan`` : objectif NL → tâches proposées
- ``POST /v1/team/tasks`` : créer une tâche
- ``GET  /v1/team/tasks`` : lister (filtres role/status/actor_id)
- ``GET  /v1/team/tasks/{id}`` : détail
- ``POST /v1/team/tasks/{id}/approve`` : approuver (token)
- ``POST /v1/team/tasks/{id}/run`` : exécuter
- ``POST /v1/team/tasks/{id}/cancel`` : annuler
- ``GET/POST /v1/team/messages`` : bus inter-agents (ADR 0019)
- ``GET/POST /v1/team/memory`` : mémoire équipe JSONL (ADR 0019)
"""

from __future__ import annotations

import os
from dataclasses import asdict

from fastapi import APIRouter, Header, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from team import memory as team_memory
from team import messages as team_messages
from team import presence as team_presence
from team import roles as team_roles
from team import store as team_store
from team.models import VALID_PRIORITIES, VALID_ROLES
from team.plan_schema import VALID_MESSAGE_KINDS
from team.player_ia_think import infer_approval_on_create
from team.role_aliases import enrich_task_view, role_display
from team.subprojects import list_subprojects
from team.agent_registry import list_agents_summary

router = APIRouter(tags=["team"])


class PlanRequest(BaseModel):
    objective: str = Field(..., min_length=1)
    actor_id: str = "pilot:team"
    use_llm: bool | None = None
    include_memory: bool | None = None


class PlanResponse(BaseModel):
    proposals: list[dict[str, object]] = Field(default_factory=list)
    source: str = "heuristic"
    meta: dict[str, object] = Field(default_factory=dict)


class CreateTaskRequest(BaseModel):
    role: str = Field(..., min_length=1)
    objective: str = Field(..., min_length=1)
    actor_id: str = "pilot:team"
    priority: str = "normal"
    approval_required: bool | None = None
    context: dict[str, object] = Field(default_factory=dict)
    approval_token: str | None = None


class ApproveTaskRequest(BaseModel):
    token: str = Field(..., min_length=1)


class RunTaskRequest(BaseModel):
    approval_token: str | None = None


class TaskView(BaseModel):
    id: str
    role: str
    objective: str
    status: str
    priority: str = "normal"
    approval_required: bool = False
    actor_id: str = "pilot:team"
    context: dict[str, object] = Field(default_factory=dict)
    result: dict[str, object] = Field(default_factory=dict)
    trace_id: str = ""
    created_ts: float = 0.0
    updated_ts: float = 0.0
    role_alias: str = ""
    role_title: str = ""
    role_label: str = ""


class TeamMetaResponse(BaseModel):
    roles: list[dict[str, object]] = Field(default_factory=list)
    subprojects: list[dict[str, object]] = Field(default_factory=list)
    agents: list[dict[str, object]] = Field(default_factory=list)
    features: dict[str, object] = Field(default_factory=dict)


class TaskListResponse(BaseModel):
    tasks: list[TaskView] = Field(default_factory=list)


class TeamMessageCreate(BaseModel):
    from_agent: str = Field(..., min_length=1)
    to_agent: str = Field(..., min_length=1)
    kind: str = Field(..., min_length=1)
    payload: dict[str, object] = Field(default_factory=dict)
    task_id: str = ""
    actor_id: str = "pilot:team"


class TeamMemoryCreate(BaseModel):
    agent_id: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    kind: str = "learning"
    tags: list[str] = Field(default_factory=list)
    task_id: str = ""
    meta: dict[str, object] = Field(default_factory=dict)


def _to_view(task: object) -> TaskView:
    data = asdict(task)  # type: ignore[arg-type]
    data.pop("stored_approval_token", None)
    enriched = enrich_task_view(data)
    return TaskView(**{k: enriched[k] for k in TaskView.model_fields if k in enriched})


@router.get("/team/meta", response_model=TeamMetaResponse)
def team_meta() -> TeamMetaResponse:
    specs = team_roles.ROLE_SPECS
    roles: list[dict[str, object]] = []
    for role in sorted(VALID_ROLES):
        disp = role_display(role)
        spec = specs.get(role, {})
        roles.append(
            {
                **disp,
                "capability": spec.get("capability"),
                "autonomy": spec.get("autonomy"),
                "default_objective": spec.get("default_objective"),
            }
        )
    features = {
        "plan_llm": team_store.plan_llm_enabled(),
        "messages": True,
        "memory": team_memory.memory_enabled(),
        "message_kinds": sorted(VALID_MESSAGE_KINDS),
        "adr": "0019",
        "bus_hooks": os.environ.get("LBG_TEAM_BUS_HOOKS", "1").strip().lower()
        in ("1", "true", "yes", "on"),
        "mission_auto_close": os.environ.get("LBG_TEAM_CAMPUS_MISSION_AUTO_CLOSE", "1")
        .strip()
        .lower()
        in ("1", "true", "yes", "on"),
        "iris_l3": __import__("team.iris_l3", fromlist=["l3_status"]).l3_status(),
        "outcome_judge": __import__("team.outcome_judge", fromlist=["meta_status"]).meta_status(),
        "lessons_learned": __import__("team.lessons_learned", fromlist=["meta_status"]).meta_status(),
        "self_state": __import__("services.self_state", fromlist=["meta_status"]).meta_status(),
        "lia_goals": __import__("team.goal_policy", fromlist=["meta_status"]).meta_status(),
        "agent_mutator": __import__("team.agent_mutator", fromlist=["meta_status"]).meta_status(),
        "feature_proposer": __import__("team.feature_proposer", fromlist=["meta_status"]).meta_status(),
        "prompt_overrides": __import__("team.prompt_overrides", fromlist=["meta_status"]).meta_status(),
        "write_paths": {
            "godot_l3_allowlist": "Iris L3 — smoke OK + LBG_IRIS_FORGE_L3=1",
            "godot_complex": "Cursor Cloud Agent / humain (L2 token) — write principal hors allowlist",
            "core3_build": "Vulcan L2 token",
            "note": "Pas d'édition de repo libre type OpenHands sur 140",
        },
    }
    from team import plan_llm as team_plan_llm
    from team import campus_conductor
    from team import evolution_sprint_workflow as evo_sprint
    from team import outcome_judge as team_outcome_judge
    from team import lessons_learned as team_lessons
    from team import agent_mutator as team_mutator
    from team import feature_proposer as team_feature_proposer
    from team import post_judge as team_post_judge

    extras: dict[str, object] = {
        "last_plan": team_plan_llm.last_plan_trace(),
        "mission": campus_conductor.last_mission(),
        "mission_persist_path": campus_conductor.mission_persist_path(),
        "memory_path": str(team_memory.memory_path()),
        "last_evolution_sprint": evo_sprint.last_sprint(),
        "last_judge": team_outcome_judge.last_judge_trace(),
        "last_post_judge": team_post_judge.last_post_judge_trace(),
        "last_mutation": team_mutator.last_mutation_trace(),
        "last_proposal": team_feature_proposer.last_proposal_trace(),
        "lessons_count": team_lessons.lessons_count(),
        "golden_cases": len(team_outcome_judge.list_golden_cases()),
    }
    return TeamMetaResponse(
        roles=roles,
        subprojects=list_subprojects(),
        agents=list_agents_summary(),
        features={**features, **{"traces": extras}},
    )


@router.post("/team/plan", response_model=PlanResponse)
def team_plan(payload: PlanRequest) -> PlanResponse:
    if not team_store.team_enabled():
        raise HTTPException(status_code=503, detail="équipe virtuelle désactivée (LBG_TEAM_ENABLED=0)")
    from team import plan_llm as team_plan_llm

    result = team_plan_llm.plan_objective(
        payload.objective,
        actor_id=payload.actor_id,
        use_llm=payload.use_llm,
        include_memory=payload.include_memory,
    )
    return PlanResponse(
        proposals=list(result.get("proposals") or []),
        source=str(result.get("source") or "heuristic"),
        meta=dict(result.get("meta") or {}),
    )


@router.get("/team/messages")
def team_list_messages(
    task_id: str | None = None,
    kind: str | None = None,
    from_agent: str | None = None,
    to_agent: str | None = None,
    limit: int = 100,
) -> dict[str, object]:
    if not team_store.team_enabled():
        raise HTTPException(status_code=503, detail="équipe virtuelle désactivée")
    msgs = team_messages.list_messages(
        task_id=task_id,
        kind=kind,
        from_agent=from_agent,
        to_agent=to_agent,
        limit=limit,
    )
    return {"messages": [m.to_dict() for m in msgs]}


@router.post("/team/messages")
def team_create_message(payload: TeamMessageCreate) -> dict[str, object]:
    if not team_store.team_enabled():
        raise HTTPException(status_code=503, detail="équipe virtuelle désactivée")
    try:
        msg = team_messages.append_message(
            from_agent=payload.from_agent,
            to_agent=payload.to_agent,
            kind=payload.kind,
            payload=payload.payload,
            task_id=payload.task_id,
            actor_id=payload.actor_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return msg.to_dict()


@router.get("/team/memory")
def team_list_memory(
    agent_id: str | None = None,
    kind: str | None = None,
    tag: str | None = None,
    limit: int = 50,
) -> dict[str, object]:
    if not team_memory.memory_enabled():
        raise HTTPException(status_code=503, detail="mémoire équipe désactivée")
    entries = team_memory.list_learnings(
        agent_id=agent_id, kind=kind, tag=tag, limit=limit
    )
    return {
        "learnings": [e.to_dict() for e in entries],
        "path": str(team_memory.memory_path()),
    }


@router.post("/team/memory")
def team_append_memory(payload: TeamMemoryCreate) -> dict[str, object]:
    try:
        entry = team_memory.append_learning(
            agent_id=payload.agent_id,
            summary=payload.summary,
            kind=payload.kind,
            tags=payload.tags,
            task_id=payload.task_id,
            meta=payload.meta,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return entry.to_dict()


@router.post("/team/tasks", response_model=TaskView)
def team_create_task(payload: CreateTaskRequest) -> TaskView:
    if not team_store.team_enabled():
        raise HTTPException(status_code=503, detail="équipe virtuelle désactivée")
    if payload.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"role invalide: {payload.role}")
    if payload.priority not in VALID_PRIORITIES:
        raise HTTPException(status_code=400, detail=f"priority invalide: {payload.priority}")
    approval = payload.approval_required
    inferred = infer_approval_on_create(payload.role, payload.objective, payload.context)
    if inferred is not None and approval is None:
        approval = inferred
    try:
        task = team_store.create_task(
            role=payload.role,
            objective=payload.objective,
            actor_id=payload.actor_id,
            priority=payload.priority,
            approval_required=approval,
            context=payload.context,
            approval_token=payload.approval_token,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return _to_view(task)


@router.get("/team/tasks", response_model=TaskListResponse)
def team_list_tasks(
    role: str | None = None,
    status: str | None = None,
    actor_id: str | None = None,
    limit: int = 100,
) -> TaskListResponse:
    tasks = team_store.list_tasks(role=role, status=status, actor_id=actor_id, limit=limit)
    return TaskListResponse(tasks=[_to_view(t) for t in tasks])


@router.get("/team/tasks/{task_id}", response_model=TaskView)
def team_get_task(task_id: str) -> TaskView:
    task = team_store.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="tâche introuvable")
    return _to_view(task)


@router.post("/team/tasks/{task_id}/approve", response_model=TaskView)
def team_approve_task(task_id: str, payload: ApproveTaskRequest) -> TaskView:
    task = team_roles.approve_task(task_id, payload.token)
    if task is None:
        raise HTTPException(status_code=404, detail="tâche introuvable")
    return _to_view(task)


@router.post("/team/tasks/{task_id}/run", response_model=TaskView)
def team_run_task(task_id: str, payload: RunTaskRequest | None = None) -> TaskView:
    token = payload.approval_token if payload else None
    task = team_roles.run_task(task_id, approval_token=token)
    if task is None:
        raise HTTPException(status_code=404, detail="tâche introuvable")
    return _to_view(task)


@router.post("/team/tasks/{task_id}/cancel", response_model=TaskView)
def team_cancel_task(task_id: str) -> TaskView:
    task = team_roles.cancel_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="tâche introuvable")
    return _to_view(task)


@router.get("/team/presence/snapshot")
def team_presence_snapshot() -> dict[str, object]:
    """Dernier état connu des agents Team (Peau bureau virtuel)."""
    if not team_presence.enabled():
        raise HTTPException(status_code=503, detail="team presence désactivée")
    return team_presence.snapshot(mode="live")  # type: ignore[return-value]


@router.get("/team/presence/history")
def team_presence_history(limit: int = 50) -> dict[str, object]:
    if not team_presence.enabled():
        raise HTTPException(status_code=503, detail="team presence désactivée")
    return {"events": team_presence.history(limit=limit)}


@router.websocket("/team/presence/ws")
async def team_presence_ws(ws: WebSocket) -> None:
    await ws.accept()
    await team_presence.register_client(ws)
    try:
        await ws.send_json({"type": "snapshot", "payload": team_presence.snapshot(mode="live")})
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await team_presence.unregister_client(ws)


class CursorLaunchBody(BaseModel):
    prompt: str = Field(..., min_length=1)
    repository: str = Field(..., min_length=3)
    model: str | None = None
    dry_run: bool = True
    auto_create_pr: bool = True
    actor_id: str = "pilot:cursor"
    auto_run: bool = False


@router.get("/team/campus/status")
def team_campus_status() -> dict[str, object]:
    from team import campus_conductor

    return campus_conductor.status()  # type: ignore[return-value]


@router.get("/team/fleet")
def team_fleet() -> dict[str, object]:
    """Supervision anti-sprawl — agents, Team L2, jobs, flags (plan gaps A2/A4)."""
    from team import fleet as team_fleet

    return team_fleet.fleet_snapshot()  # type: ignore[return-value]


class OpsHealthPilotBody(BaseModel):
    dry_run: bool = True
    notify: bool | None = None
    spawn_l2_remediation: bool = True
    include_smoke: bool = False
    actor_id: str = "pilot:ops_health"


@router.post("/team/ops_health_pilot")
def team_ops_health_pilot(payload: OpsHealthPilotBody) -> dict[str, object]:
    """Playbook ops health (perception→décision→notify→L2). Dry-run par défaut."""
    if not team_store.team_enabled():
        raise HTTPException(status_code=503, detail="équipe virtuelle désactivée")
    from team import ops_health_pilot

    return ops_health_pilot.run_ops_health_pilot(  # type: ignore[return-value]
        dry_run=payload.dry_run,
        notify=payload.notify,
        spawn_l2_remediation=payload.spawn_l2_remediation,
        include_smoke=payload.include_smoke,
        actor_id=payload.actor_id,
    )


class SmokeLanMissionCreateBody(BaseModel):
    days: int = 3
    budget_retries: int = 5
    escalate_after_red: int = 2
    dry_run: bool = False
    actor_id: str = "pilot:smoke_lan_mission"


class SmokeLanMissionTickBody(BaseModel):
    dry_run: bool = True
    notify: bool | None = None
    include_smoke: bool = False
    actor_id: str | None = None


@router.get("/team/smoke_lan_mission")
def team_smoke_lan_mission_get() -> dict[str, object]:
    """État mission L3 bornée smoke LAN (E2/E4)."""
    from team import smoke_lan_mission

    return smoke_lan_mission.mission_brief()  # type: ignore[return-value]


@router.post("/team/smoke_lan_mission")
def team_smoke_lan_mission_create(payload: SmokeLanMissionCreateBody) -> dict[str, object]:
    """Crée une mission L3 bornée (deadline / budget / escalade)."""
    if not team_store.team_enabled():
        raise HTTPException(status_code=503, detail="équipe virtuelle désactivée")
    from team import smoke_lan_mission

    return smoke_lan_mission.create_mission(  # type: ignore[return-value]
        days=payload.days,
        budget_retries=payload.budget_retries,
        escalate_after_red=payload.escalate_after_red,
        actor_id=payload.actor_id,
        dry_run=payload.dry_run,
    )


@router.post("/team/smoke_lan_mission/tick")
def team_smoke_lan_mission_tick(payload: SmokeLanMissionTickBody) -> dict[str, object]:
    """Tick observe→retry→escalade L2 (E3). Dry-run par défaut."""
    if not team_store.team_enabled():
        raise HTTPException(status_code=503, detail="équipe virtuelle désactivée")
    from team import smoke_lan_mission

    return smoke_lan_mission.tick_mission(  # type: ignore[return-value]
        dry_run=payload.dry_run,
        notify=payload.notify,
        include_smoke=payload.include_smoke,
        actor_id=payload.actor_id,
    )


@router.post("/team/smoke_lan_mission/cancel")
def team_smoke_lan_mission_cancel() -> dict[str, object]:
    from team import smoke_lan_mission

    return smoke_lan_mission.cancel_mission()  # type: ignore[return-value]


class SmokeLanMissionExtendBody(BaseModel):
    extra_days: int | None = None


@router.post("/team/smoke_lan_mission/extend")
def team_smoke_lan_mission_extend(payload: SmokeLanMissionExtendBody | None = None) -> dict[str, object]:
    """Prolonge la deadline mission (jours restants + marge)."""
    if not team_store.team_enabled():
        raise HTTPException(status_code=503, detail="équipe virtuelle désactivée")
    from team import smoke_lan_mission

    body = payload or SmokeLanMissionExtendBody()
    return smoke_lan_mission.extend_mission(extra_days=body.extra_days)  # type: ignore[return-value]


class PygmalionAssetsPilotBody(BaseModel):
    brief: str
    dry_run: bool = True
    notify: bool | None = None
    spawn_l2: bool = True
    propose_comfy_ensure: bool = True
    actor_id: str = "pilot:pygmalion_assets"


@router.post("/team/pygmalion_assets_pilot")
def team_pygmalion_assets_pilot(payload: PygmalionAssetsPilotBody) -> dict[str, object]:
    """Brief Pygmalion → sonde Comfy → tâche L2 (F2). Dry-run par défaut."""
    if not team_store.team_enabled():
        raise HTTPException(status_code=503, detail="équipe virtuelle désactivée")
    from team import pygmalion_assets_pilot

    return pygmalion_assets_pilot.run_pygmalion_assets_pilot(  # type: ignore[return-value]
        brief=payload.brief,
        dry_run=payload.dry_run,
        notify=payload.notify,
        spawn_l2=payload.spawn_l2,
        propose_comfy_ensure=payload.propose_comfy_ensure,
        actor_id=payload.actor_id,
    )


class CampusConductBody(BaseModel):
    dry_run: bool = False
    max_starts: int | None = None


@router.post("/team/campus/conduct")
def team_campus_conduct(payload: CampusConductBody) -> dict[str, object]:
    """Tick Campus Conductor (Lyra) — drain file queued L1."""
    if not team_store.team_enabled():
        raise HTTPException(status_code=503, detail="équipe virtuelle désactivée")
    from team import campus_conductor

    return campus_conductor.conduct(  # type: ignore[return-value]
        dry_run=payload.dry_run,
        max_starts_override=payload.max_starts,
    )


@router.post("/team/campus/act")
def team_campus_act(payload: CampusConductBody) -> dict[str, object]:
    """Lyra décide un mode selon l'état campus puis agit."""
    if not team_store.team_enabled():
        raise HTTPException(status_code=503, detail="équipe virtuelle désactivée")
    from team import campus_conductor

    return campus_conductor.act(  # type: ignore[return-value]
        dry_run=payload.dry_run,
        max_starts_override=payload.max_starts,
    )


class CampusMissionBody(BaseModel):
    objective: str = Field(..., min_length=1)
    dry_run: bool = False
    auto_act: bool = True
    max_tasks: int = 6


@router.post("/team/campus/mission")
def team_campus_mission(payload: CampusMissionBody) -> dict[str, object]:
    """Mission NL → plan → tâches L1 → act optionnel."""
    if not team_store.team_enabled():
        raise HTTPException(status_code=503, detail="équipe virtuelle désactivée")
    from team import campus_conductor

    return campus_conductor.start_mission(  # type: ignore[return-value]
        payload.objective,
        dry_run=payload.dry_run,
        auto_act=payload.auto_act,
        max_tasks=payload.max_tasks,
    )


class CampusMissionRegisterBody(BaseModel):
    """Mission déjà spawnée (timer Chœur / jalon) — pose task_ids pour clôture."""

    id: str = Field(..., min_length=1)
    objective: str = Field(..., min_length=1)
    task_ids: list[str] = Field(default_factory=list)
    kind: str = "choeur_l1"
    require_owner_smoke: bool = True
    status: str = "open"


@router.post("/team/campus/mission/register")
def team_campus_mission_register(payload: CampusMissionRegisterBody) -> dict[str, object]:
    if not team_store.team_enabled():
        raise HTTPException(status_code=503, detail="équipe virtuelle désactivée")
    from team import campus_conductor

    out = campus_conductor.register_mission(
        payload.id,
        payload.objective,
        list(payload.task_ids or []),
        kind=payload.kind,
        require_owner_smoke=payload.require_owner_smoke,
        status=payload.status,
    )
    if not out.get("ok"):
        raise HTTPException(status_code=400, detail=str(out.get("error") or "register_failed"))
    return out  # type: ignore[return-value]


class EvolutionLeadBody(BaseModel):
    """Piste d'évolution (URL TikTok/doc/repo…) — fetch silencieux, pas d'onglet."""

    url: str | None = None
    text: str | None = None
    note: str = ""
    spawn_mission: bool = True
    dry_run: bool = False
    actor_id: str = "compagnon:evolution"
    urls: list[str] | None = None


@router.post("/team/evolution/lead")
def team_evolution_lead(payload: EvolutionLeadBody) -> dict[str, object]:
    """Veille silencieuse : meta URL → brief → mission / tâche evolution_veille."""
    from services import evolution_lead as evo_lead

    if not evo_lead.leads_enabled():
        raise HTTPException(status_code=503, detail="evolution_leads_disabled")
    urls = [u for u in (payload.urls or []) if u]
    if urls:
        out = evo_lead.ingest_leads_batch(
            urls=urls,
            text=payload.text,
            note=payload.note,
            spawn_mission=payload.spawn_mission,
            dry_run=payload.dry_run,
            actor_id=payload.actor_id,
        )
    else:
        out = evo_lead.ingest_lead(
            url=payload.url,
            text=payload.text,
            note=payload.note,
            spawn_mission=payload.spawn_mission,
            dry_run=payload.dry_run,
            actor_id=payload.actor_id,
        )
    if not out.get("ok"):
        raise HTTPException(status_code=400, detail=str(out.get("error") or "lead_failed"))
    return out  # type: ignore[return-value]


@router.get("/team/evolution/leads")
def team_evolution_leads(limit: int = 20) -> dict[str, object]:
    """Dernières pistes d'évolution (jsonl)."""
    from services import evolution_lead as evo_lead

    rows = evo_lead.list_leads(limit=max(1, min(100, int(limit or 20))))
    return {"ok": True, "count": len(rows), "leads": rows}


class CampusMissionCloseBody(BaseModel):
    force: bool = False
    reason: str = ""


@router.post("/team/campus/mission/close")
def team_campus_mission_close(payload: CampusMissionCloseBody | None = None) -> dict[str, object]:
    """Clôture mission Lyra (manuelle ou force). Auto aussi via act/mission_close."""
    if not team_store.team_enabled():
        raise HTTPException(status_code=503, detail="équipe virtuelle désactivée")
    from team import campus_conductor

    body = payload or CampusMissionCloseBody()
    out = campus_conductor.close_mission(force=body.force, reason=body.reason)
    if not out.get("ok"):
        raise HTTPException(status_code=400, detail=str(out.get("error") or "close_failed"))
    return out  # type: ignore[return-value]


@router.get("/team/campus/mission/closure")
def team_campus_mission_closure() -> dict[str, object]:
    """Évalue si la mission courante est clôturable (smoke vert / file terminée)."""
    from team import campus_conductor

    return campus_conductor.evaluate_mission_closure()  # type: ignore[return-value]


class TeamMemoryPruneBody(BaseModel):
    max_entries: int | None = None
    max_age_days: float | None = None


@router.post("/team/memory/prune")
def team_memory_prune(payload: TeamMemoryPruneBody | None = None) -> dict[str, object]:
    body = payload or TeamMemoryPruneBody()
    out = team_memory.prune_learnings(
        max_entries=body.max_entries,
        max_age_days=body.max_age_days,
    )
    if not out.get("ok"):
        raise HTTPException(status_code=503, detail=str(out.get("error") or "prune_failed"))
    return out  # type: ignore[return-value]


@router.get("/team/cursor/health")
def team_cursor_health() -> dict[str, object]:
    from integrations import cursor_agent as cursor

    return cursor.health()  # type: ignore[return-value]


@router.post("/team/cursor/launch")
def team_cursor_launch(payload: CursorLaunchBody) -> dict[str, object]:
    """Crée une tâche Team cursor_cloud_agent (dry-run par défaut)."""
    if not team_store.team_enabled():
        raise HTTPException(status_code=503, detail="équipe virtuelle désactivée")
    from integrations import cursor_agent as cursor

    if payload.dry_run or not cursor.enabled():
        preview = cursor.launch_agent_dry_run(
            prompt=payload.prompt,
            repository=payload.repository,
            model=payload.model,
        )
        return {"ok": True, "dry_run": True, "preview": preview, "health": cursor.health()}

    task = team_store.create_task(
        role="dev_game",
        objective=payload.prompt[:400],
        actor_id=payload.actor_id,
        priority="high",
        approval_required=True,
        context={
            "cursor_cloud_agent": True,
            "workflow": "cursor_cloud_agent",
            "repository": payload.repository,
            "cursor_prompt": payload.prompt,
            "cursor_model": payload.model,
            "auto_create_pr": payload.auto_create_pr,
            "dry_run": False,
        },
    )
    ran = None
    if payload.auto_run and not task.approval_required:
        ran = team_roles.run_task(task.id)
    return {
        "ok": True,
        "dry_run": False,
        "task": enrich_task_view(asdict(ran or task)),
        "health": cursor.health(),
        "note": "approval L2 requise avant run si approval_required",
    }


def _require_wsl_token(x_lbg_wsl_token: str | None = Header(default=None, alias="X-LBG-WSL-TOKEN")) -> None:
    from team import wsl_executor

    if not wsl_executor.enabled():
        raise HTTPException(status_code=503, detail="wsl executor désactivé")
    if not wsl_executor.check_token(x_lbg_wsl_token):
        raise HTTPException(status_code=401, detail="token WSL invalide ou manquant")


class WslEnqueueBody(BaseModel):
    wsl_skill: str = Field(..., min_length=1)
    objective: str = Field(..., min_length=1)
    actor_id: str = "pilot:wsl"
    priority: str = "normal"
    role: str | None = None
    args: list[str] = Field(default_factory=list)
    context: dict[str, object] = Field(default_factory=dict)


class WslPollBody(BaseModel):
    executor_id: str = Field(..., min_length=1)


class WslCompleteBody(BaseModel):
    ok: bool = True
    exit_code: int | None = None
    stdout_tail: str = ""
    stderr_tail: str = ""
    result: dict[str, object] = Field(default_factory=dict)
    executor_id: str = ""


@router.get("/team/wsl/health")
def team_wsl_health(
    x_lbg_wsl_token: str | None = Header(default=None, alias="X-LBG-WSL-TOKEN"),
) -> dict[str, object]:
    _require_wsl_token(x_lbg_wsl_token)
    from team import wsl_executor

    out = wsl_executor.health()
    out["skills"] = wsl_executor.list_skills()
    return out  # type: ignore[return-value]


@router.post("/team/wsl/tasks")
def team_wsl_enqueue(
    payload: WslEnqueueBody,
    x_lbg_wsl_token: str | None = Header(default=None, alias="X-LBG-WSL-TOKEN"),
) -> dict[str, object]:
    """Enqueue une tâche à exécuter sur le poste WSL (pull)."""
    _require_wsl_token(x_lbg_wsl_token)
    from team import wsl_executor

    if not wsl_executor.skill_allowed(payload.wsl_skill):
        raise HTTPException(status_code=400, detail=f"wsl_skill hors allowlist: {payload.wsl_skill}")
    try:
        task = wsl_executor.enqueue_wsl_task(
            wsl_skill=payload.wsl_skill,
            objective=payload.objective,
            actor_id=payload.actor_id,
            priority=payload.priority,
            role=payload.role,
            args=payload.args or None,
            extra_context=payload.context or None,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"ok": True, "task": enrich_task_view(asdict(task))}


@router.post("/team/wsl/poll")
def team_wsl_poll(
    payload: WslPollBody,
    x_lbg_wsl_token: str | None = Header(default=None, alias="X-LBG-WSL-TOKEN"),
) -> dict[str, object]:
    """Claim atomique de la prochaine tâche WSL (queued → running)."""
    _require_wsl_token(x_lbg_wsl_token)
    from team import wsl_executor

    task = wsl_executor.claim_next_wsl_task(executor_id=payload.executor_id)
    if task is None:
        return {"ok": True, "task": None}
    meta = wsl_executor.WSL_SKILLS.get(str((task.context or {}).get("wsl_skill") or ""), {})
    return {
        "ok": True,
        "task": enrich_task_view(asdict(task)),
        "skill_meta": {
            "script": meta.get("script"),
            "cwd": meta.get("cwd", "cortex"),
            "default_args": meta.get("default_args") or [],
        },
    }


@router.post("/team/wsl/tasks/{task_id}/complete")
def team_wsl_complete(
    task_id: str,
    payload: WslCompleteBody,
    x_lbg_wsl_token: str | None = Header(default=None, alias="X-LBG-WSL-TOKEN"),
) -> dict[str, object]:
    """Rapport de fin d'exécution WSL → done/failed."""
    _require_wsl_token(x_lbg_wsl_token)
    from team import wsl_executor

    task = wsl_executor.complete_wsl_task(
        task_id,
        ok=payload.ok,
        exit_code=payload.exit_code,
        stdout_tail=payload.stdout_tail,
        stderr_tail=payload.stderr_tail,
        result=payload.result,
        executor_id=payload.executor_id,
    )
    if task is None:
        raise HTTPException(status_code=404, detail="tâche WSL introuvable ou non complétable")
    return {"ok": True, "task": enrich_task_view(asdict(task))}
