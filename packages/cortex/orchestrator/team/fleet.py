"""Agrégat Fleet — supervision anti-sprawl (plan_combler_gaps_agentiques § A2/A4).

Vue unique : agents déclarés + présence, file Team, jobs Cowork, L2 pending, flags agentiques.
"""

from __future__ import annotations

import os
import time
from collections import Counter
from typing import Any


def _truthy(raw: str) -> bool:
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _chat_agentic_flags() -> dict[str, Any]:
    intents_raw = os.environ.get("LBG_CHAT_AGENTIC_INTENTS", "").strip()
    intents = [p.strip() for p in intents_raw.split(",") if p.strip()] if intents_raw else []
    return {
        "LBG_CHAT_AGENTIC": _truthy(os.environ.get("LBG_CHAT_AGENTIC", "0")),
        "LBG_CHAT_AGENTIC_INTENTS": intents,
        "note": "Global off par défaut ; opt-in prefer_agentic ou allowlist intents (phase C).",
    }


def _jobs_metrics() -> dict[str, Any]:
    try:
        from services import jobs as svc_jobs
    except Exception as exc:
        return {"ok": False, "error": str(exc), "by_status": {}, "total": 0}

    try:
        jobs = svc_jobs.list_jobs()
    except Exception as exc:
        return {
            "ok": False,
            "error": str(exc),
            "runner_enabled": svc_jobs.runner_enabled(),
            "by_status": {},
            "total": 0,
        }

    by_status = Counter(str(j.status or "?") for j in jobs)
    waiting = [j for j in jobs if j.status == "waiting_approval"]
    recent = sorted(jobs, key=lambda j: float(j.updated_ts or j.created_ts or 0), reverse=True)[:12]
    return {
        "ok": True,
        "runner_enabled": svc_jobs.runner_enabled(),
        "total": len(jobs),
        "by_status": dict(by_status),
        "waiting_approval_count": len(waiting),
        "waiting_approval": [
            {
                "id": j.id,
                "objective": (j.objective or "")[:120],
                "actor_id": j.actor_id,
                "updated_ts": j.updated_ts,
            }
            for j in waiting[:20]
        ],
        "recent": [
            {
                "id": j.id,
                "status": j.status,
                "objective": (j.objective or "")[:100],
                "n_steps": len(j.steps or []),
                "updated_ts": j.updated_ts,
            }
            for j in recent
        ],
    }


def _team_task_metrics() -> dict[str, Any]:
    from team import store as team_store

    if not team_store.team_enabled():
        return {"ok": False, "enabled": False, "by_status": {}, "total": 0, "l2_pending": []}

    tasks = team_store.list_tasks(limit=500)
    by_status = Counter(str(t.status or "?") for t in tasks)
    l2_pending: list[dict[str, Any]] = []
    for t in tasks:
        st = str(t.status or "")
        needs = bool(t.approval_required) and st in ("review", "queued", "waiting_approval")
        if st == "review" or needs:
            l2_pending.append(
                {
                    "id": t.id,
                    "role": t.role,
                    "status": t.status,
                    "objective": (t.objective or "")[:120],
                    "actor_id": t.actor_id,
                    "approval_required": bool(t.approval_required),
                    "updated_ts": t.updated_ts,
                }
            )
    l2_pending.sort(key=lambda r: float(r.get("updated_ts") or 0), reverse=True)
    return {
        "ok": True,
        "enabled": True,
        "total": len(tasks),
        "by_status": dict(by_status),
        "l2_pending_count": len(l2_pending),
        "l2_pending": l2_pending[:40],
    }


def _agents_fleet() -> list[dict[str, Any]]:
    from team.agent_registry import list_agents_summary
    from team import presence as team_presence

    declared = list_agents_summary()
    snap: dict[str, Any] = {}
    try:
        snap = team_presence.snapshot(mode="live")
    except Exception:
        snap = {"agents": []}
    by_id: dict[str, dict[str, Any]] = {}
    for a in snap.get("agents") or []:
        if isinstance(a, dict) and a.get("agent_id"):
            by_id[str(a["agent_id"])] = a

    out: list[dict[str, Any]] = []
    for d in declared:
        aid = str(d.get("agent_id") or "")
        live = by_id.get(aid) or {}
        out.append(
            {
                "agent_id": aid,
                "display_name": d.get("display_name") or live.get("display_name") or aid,
                "role": d.get("role") or live.get("role"),
                "persona": d.get("persona"),
                "subproject": d.get("subproject"),
                "capabilities": d.get("capabilities") or [],
                "owner_timer": d.get("owner_timer"),
                "status": live.get("status") or "idle",
                "location": live.get("location"),
                "host_hint": live.get("host_hint"),
                "current_action": live.get("current_action"),
                "task_id": live.get("task_id"),
                "approval_required": live.get("approval_required"),
                "awaiting_human_approval": live.get("awaiting_human_approval"),
                "awaiting_run": live.get("awaiting_run"),
                "presence": bool(live),
            }
        )
    # Agents présents mais absents du registre (ne pas perdre la vue)
    known = {str(a.get("agent_id") or "") for a in out}
    for aid, live in by_id.items():
        if aid in known:
            continue
        out.append(
            {
                "agent_id": aid,
                "display_name": live.get("display_name") or aid,
                "role": live.get("role"),
                "status": live.get("status") or "idle",
                "location": live.get("location"),
                "host_hint": live.get("host_hint"),
                "current_action": live.get("current_action"),
                "task_id": live.get("task_id"),
                "presence": True,
                "orphan": True,
            }
        )
    out.sort(key=lambda a: (str(a.get("status") or ""), str(a.get("display_name") or "")))
    return out


def _campus_brief() -> dict[str, Any]:
    try:
        from team import campus_conductor

        st = campus_conductor.status()
        return {
            "ok": bool(st.get("ok")),
            "busy_agent_count": st.get("busy_agent_count"),
            "queued_count": st.get("queued_count"),
            "decision": st.get("decision"),
            "mission": st.get("mission"),
            "failed_agents": st.get("failed_agents") or [],
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _lessons_meta() -> dict[str, Any]:
    try:
        from team import lessons_learned

        return lessons_learned.meta_status()
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def fleet_snapshot() -> dict[str, Any]:
    """Snapshot unique pour Pilot Fleet / métriques A4."""
    agents = _agents_fleet()
    by_agent_status = Counter(str(a.get("status") or "?") for a in agents)
    team = _team_task_metrics()
    jobs = _jobs_metrics()
    last_pilot: dict[str, Any] = {}
    try:
        from team import ops_health_pilot

        last_pilot = ops_health_pilot.last_run()
    except Exception as exc:
        last_pilot = {"ok": False, "error": str(exc)}
    mission_brief: dict[str, Any] = {"ok": False}
    try:
        from team import smoke_lan_mission

        mission_brief = smoke_lan_mission.mission_brief()
    except Exception as exc:
        mission_brief = {"ok": False, "error": str(exc)}
    mission_slice = mission_brief.get("mission") if isinstance(mission_brief, dict) else None
    last_pyg: dict[str, Any] = {}
    try:
        from team import pygmalion_assets_pilot

        last_pyg = pygmalion_assets_pilot.last_run()
    except Exception as exc:
        last_pyg = {"ok": False, "error": str(exc)}
    return {
        "ok": True,
        "ts": time.time(),
        "docs": [
            "docs/plan_combler_gaps_agentiques.md",
            "docs/lbg_agentic_os.md",
            "docs/runbook_ops_health_pilot.md",
        ],
        "agents": agents,
        "agents_count": len(agents),
        "agents_by_status": dict(by_agent_status),
        "orphan_agents": [a for a in agents if a.get("orphan")],
        "team": team,
        "jobs": jobs,
        "campus": _campus_brief(),
        "lessons": _lessons_meta(),
        "ops_health_pilot": {"last_run": last_pilot},
        "pygmalion_assets_pilot": {"last_run": last_pyg},
        "smoke_lan_mission": mission_brief,
        "flags": {
            "chat_agentic": _chat_agentic_flags(),
            "team_enabled": _truthy(os.environ.get("LBG_TEAM_ENABLED", "1")),
            "jobs_runner": jobs.get("runner_enabled"),
            "jobs_l2_notify": _truthy(os.environ.get("LBG_JOBS_L2_NOTIFY", "1")),
        },
        "metrics": {
            "agents_busy": by_agent_status.get("busy", 0),
            "agents_review": by_agent_status.get("review", 0),
            "agents_failed": by_agent_status.get("failed", 0),
            "team_l2_pending": team.get("l2_pending_count", 0),
            "jobs_waiting_approval": jobs.get("waiting_approval_count", 0),
            "jobs_total": jobs.get("total", 0),
            "jobs_by_status": jobs.get("by_status") or {},
            "team_by_status": team.get("by_status") or {},
            "ops_health_last_decision": last_pilot.get("decision"),
            "mission_status": (mission_slice or {}).get("status") if isinstance(mission_slice, dict) else None,
            "mission_days_ok": (mission_slice or {}).get("days_ok") if isinstance(mission_slice, dict) else None,
            "pygmalion_last_comfy_ok": last_pyg.get("comfy_ok"),
            "pygmalion_last_l2": last_pyg.get("l2_task_id"),
        },
    }
