"""Campus Conductor (Lyra) — drain, coffee fill, mission NL, act selon état.

Opt-in : LBG_TEAM_CAMPUS_CONDUCTOR_ENABLED=1
Les runs sont lancés en thread daemon pour ne pas bloquer le tick / HTTP.
"""

from __future__ import annotations

import os
import threading
import time
import uuid
from typing import Any

from team import presence as team_presence
from team import roles as team_roles
from team import store as team_store
from team.models import TeamTask
from team.presence import resolve_presence_agent_id

CONDUCTOR_AGENT_ID = "studio_conductor_lyra"
ACTOR_ID = "system:campus_conductor"
_last_report: dict[str, Any] = {}
_last_mission: dict[str, Any] = {}
_last_decision: dict[str, Any] = {}
_lock = threading.Lock()
_last_coffee_spawn_ts: float = 0.0

_COFFEE_PLAYBOOKS: list[dict[str, Any]] = [
    {
        "agent_ids": ("studio_qa_argus",),
        "role": "qa",
        "objective": "Smoke LAN read-only — healthz + systemd (coffee fill Conductor)",
        "context": {"_campus_coffee_fill": True, "presence_agent_id": "studio_qa_argus"},
        "utility_key": "qa_smoke",
    },
    {
        "agent_ids": ("studio_ops_hephaistos",),
        "role": "ops",
        "objective": "Sonde santé orchestrateur et backend (read-only, coffee fill)",
        "context": {"_campus_coffee_fill": True, "presence_agent_id": "studio_ops_hephaistos"},
        "utility_key": "ops_probe",
    },
    {
        "agent_ids": ("studio_pm_themis",),
        "role": "pm",
        "objective": "Brief court — priorités campus et file Team (coffee fill Lyra)",
        "context": {
            "_campus_coffee_fill": True,
            "presence_agent_id": "studio_pm_themis",
            "reunification_brief": False,
        },
        "utility_key": "pm_brief",
    },
    {
        "agent_ids": ("admin_infra", "studio_admin_atlas"),
        "role": "admin_infra",
        "objective": "Audit rapide infra LLM locale / dual host (coffee fill)",
        "context": {"_campus_coffee_fill": True, "presence_agent_id": "admin_infra"},
        "utility_key": "admin_audit",
    },
]


def coffee_fill_enabled() -> bool:
    return os.environ.get("LBG_TEAM_CAMPUS_CONDUCTOR_COFFEE_FILL", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def coffee_min() -> int:
    try:
        return max(1, int(os.environ.get("LBG_TEAM_CAMPUS_CONDUCTOR_COFFEE_MIN", "3")))
    except ValueError:
        return 3


def coffee_max_spawn() -> int:
    try:
        return max(0, int(os.environ.get("LBG_TEAM_CAMPUS_CONDUCTOR_COFFEE_MAX_SPAWN", "1")))
    except ValueError:
        return 1


def coffee_cooldown_s() -> float:
    try:
        return max(60.0, float(os.environ.get("LBG_TEAM_CAMPUS_CONDUCTOR_COFFEE_COOLDOWN_S", "1800")))
    except ValueError:
        return 1800.0


def coffee_utility_s() -> float:
    try:
        return max(300.0, float(os.environ.get("LBG_TEAM_CAMPUS_CONDUCTOR_COFFEE_UTILITY_S", "21600")))
    except ValueError:
        return 21600.0


def enabled() -> bool:
    return os.environ.get("LBG_TEAM_CAMPUS_CONDUCTOR_ENABLED", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def max_busy() -> int:
    try:
        return max(1, int(os.environ.get("LBG_TEAM_CAMPUS_CONDUCTOR_MAX_BUSY", "4")))
    except ValueError:
        return 4


def max_starts() -> int:
    try:
        return max(0, int(os.environ.get("LBG_TEAM_CAMPUS_CONDUCTOR_MAX_STARTS", "2")))
    except ValueError:
        return 2


def roles_allowlist() -> set[str] | None:
    raw = os.environ.get("LBG_TEAM_CAMPUS_CONDUCTOR_ROLES", "").strip()
    if not raw:
        return None
    return {x.strip() for x in raw.split(",") if x.strip()}


def last_report() -> dict[str, Any]:
    with _lock:
        return dict(_last_report)


def last_mission() -> dict[str, Any]:
    with _lock:
        return dict(_last_mission)


def last_decision() -> dict[str, Any]:
    with _lock:
        return dict(_last_decision)


def _set_report(report: dict[str, Any]) -> None:
    with _lock:
        global _last_report
        _last_report = dict(report)


def _set_mission(mission: dict[str, Any]) -> None:
    with _lock:
        global _last_mission
        _last_mission = dict(mission)


def _set_decision(decision: dict[str, Any]) -> None:
    with _lock:
        global _last_decision
        _last_decision = dict(decision)


def _emit_conductor(status: str, action: str, *, task_id: str | None = None) -> None:
    if not team_presence.enabled():
        return
    try:
        team_presence.emit_payload(
            {
                "schema": team_presence.SCHEMA,
                "agent_id": CONDUCTOR_AGENT_ID,
                "display_name": "Lyra",
                "status": status,
                "current_action": team_presence.sanitize_action(action),
                "location": "zone_core",
                "target_destination": None,
                "task_id": task_id,
                "role": "pm",
                "host_hint": "192.168.0.140",
                "trace_id": None,
                "timestamp": int(time.time()),
                "event": "status_changed",
            }
        )
    except Exception:
        return


def _priority_rank(task: TeamTask) -> int:
    return 0 if str(task.priority or "") == "high" else 1


def _blocked_context(task: TeamTask) -> str | None:
    ctx = task.context or {}
    if ctx.get("cursor_cloud_agent") and task.approval_required and not task.stored_approval_token:
        return "cursor_cloud_agent_needs_L2"
    if (
        ctx.get("core3_build")
        and ctx.get("core3_build_execute")
        and task.approval_required
        and not task.stored_approval_token
    ):
        return "core3_build_needs_L2"
    if ctx.get("player_ia_think") or ctx.get("think_tick"):
        if task.approval_required and not task.stored_approval_token:
            return "player_ia_think_needs_L2"
    return None


def _can_autorun(task: TeamTask) -> tuple[bool, str]:
    if task.status != "queued":
        return False, f"status={task.status}"
    allow = roles_allowlist()
    if allow is not None and task.role not in allow:
        return False, f"role_not_in_allowlist:{task.role}"
    blocked = _blocked_context(task)
    if blocked:
        return False, blocked
    if task.approval_required and not task.stored_approval_token:
        return False, "approval_required"
    return True, "ok"


def running_stale_sec() -> float:
    try:
        return max(60.0, float(os.environ.get("LBG_TEAM_CAMPUS_CONDUCTOR_RUNNING_STALE_SEC", "7200")))
    except ValueError:
        return 7200.0


def _running_tasks() -> list[TeamTask]:
    now = time.time()
    stale = running_stale_sec()
    out: list[TeamTask] = []
    for t in team_store.list_tasks(status="running", limit=200):
        if now - float(t.updated_ts or 0) <= stale:
            out.append(t)
    return out


def _presence_busy_ids() -> set[str]:
    try:
        snap = team_presence.snapshot(mode="live")
    except Exception:
        return set()
    ids: set[str] = set()
    for agent in snap.get("agents") or []:
        if isinstance(agent, dict) and str(agent.get("status") or "") == "busy":
            aid = str(agent.get("agent_id") or "").strip()
            if aid:
                ids.add(aid)
    return ids


def _queued_tasks() -> list[TeamTask]:
    tasks = team_store.list_tasks(status="queued", limit=200)
    tasks.sort(key=lambda t: (_priority_rank(t), float(t.created_ts or t.updated_ts or 0)))
    return tasks


def _busy_agent_ids(running: list[TeamTask]) -> set[str]:
    ids = {resolve_presence_agent_id(t) for t in running}
    ids |= _presence_busy_ids()
    return ids


def _failed_agents(snap: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    snapshot = snap or team_presence.snapshot(mode="live")
    return [
        a
        for a in (snapshot.get("agents") or [])
        if isinstance(a, dict) and str(a.get("status") or "") == "failed"
    ]


def analyze_idle(snap: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    snapshot = snap or team_presence.snapshot(mode="live")
    running = _running_tasks()
    queued = _queued_tasks()
    busy_ids = _busy_agent_ids(running)
    queued_by_agent: dict[str, list[str]] = {}
    for t in queued:
        queued_by_agent.setdefault(resolve_presence_agent_id(t), []).append(t.id)

    notes: list[dict[str, Any]] = []
    for agent in snapshot.get("agents") or []:
        if not isinstance(agent, dict):
            continue
        st = str(agent.get("status") or "")
        if st not in ("idle", "offline"):
            continue
        aid = str(agent.get("agent_id") or "")
        if aid == CONDUCTOR_AGENT_ID:
            continue
        qids = queued_by_agent.get(aid) or []
        if aid in busy_ids:
            reason = "busy_elsewhere"
        elif qids:
            reason = "queued_waiting_slot"
        elif str(agent.get("location") or "") == "zone_coffee":
            reason = "coffee_available"
        else:
            reason = "no_active_task"
        notes.append(
            {
                "agent_id": aid,
                "display_name": agent.get("display_name"),
                "role": agent.get("role"),
                "location": agent.get("location"),
                "reason": reason,
                "queued_task_ids": qids[:5],
            }
        )
    return notes


def _recent_coffee_fill_for_role(role: str, *, within_s: float | None = None) -> bool:
    window = within_s if within_s is not None else coffee_cooldown_s()
    now = time.time()
    for t in team_store.list_tasks(role=role, limit=30):
        ctx = t.context or {}
        if not ctx.get("_campus_coffee_fill"):
            continue
        if now - float(t.created_ts or t.updated_ts or 0) <= window:
            return True
    return False


def _coffee_utility_ok(role: str, utility_key: str) -> tuple[bool, str]:
    window = coffee_utility_s()
    now = time.time()
    for t in team_store.list_tasks(role=role, status="done", limit=40):
        age = now - float(t.updated_ts or t.created_ts or 0)
        if age > window:
            continue
        res = t.result if isinstance(t.result, dict) else {}
        if res.get("ok") is not True:
            continue
        ctx = t.context or {}
        if ctx.get("_campus_coffee_fill") or ctx.get("_campus_mission_id"):
            return False, f"recent_success:{utility_key}"
        if role == "qa" and utility_key == "qa_smoke":
            return False, "recent_qa_ok"
    return True, "ok"


def _coffee_spawn_proposals(
    idle_notes: list[dict[str, Any]],
    *,
    reserved_agents: set[str],
    slots_left: int,
) -> list[dict[str, Any]]:
    global _last_coffee_spawn_ts
    if not coffee_fill_enabled() or slots_left <= 0 or coffee_max_spawn() <= 0:
        return []
    if _last_coffee_spawn_ts and (time.time() - _last_coffee_spawn_ts) < coffee_cooldown_s():
        return []
    coffee_ids = {
        str(n.get("agent_id") or "")
        for n in idle_notes
        if n.get("reason") == "coffee_available"
    }
    if len(coffee_ids) < coffee_min():
        return []

    proposals: list[dict[str, Any]] = []
    for pb in _COFFEE_PLAYBOOKS:
        if len(proposals) >= min(coffee_max_spawn(), slots_left):
            break
        match_id = next((aid for aid in pb["agent_ids"] if aid in coffee_ids and aid not in reserved_agents), None)
        if not match_id:
            continue
        role = str(pb["role"])
        allow = roles_allowlist()
        if allow is not None and role not in allow:
            continue
        if _recent_coffee_fill_for_role(role):
            continue
        util_ok, util_why = _coffee_utility_ok(role, str(pb.get("utility_key") or role))
        if not util_ok:
            continue
        proposals.append(
            {
                "kind": "coffee_fill",
                "agent_id": match_id,
                "role": role,
                "objective": pb["objective"],
                "context": dict(pb["context"]),
                "utility": util_why,
            }
        )
    return proposals


def decide_action(snap: dict[str, Any] | None = None) -> dict[str, Any]:
    snapshot = snap or team_presence.snapshot(mode="live")
    idle_notes = analyze_idle(snapshot)
    failed = _failed_agents(snapshot)
    running = _running_tasks()
    busy_ids = _busy_agent_ids(running)
    busy_count = len(busy_ids)
    slots = max(0, max_busy() - busy_count)
    coffee = sum(1 for n in idle_notes if n.get("reason") == "coffee_available")
    waiting = sum(1 for n in idle_notes if n.get("reason") == "queued_waiting_slot")
    queued_n = len(_queued_tasks())
    mission = last_mission()
    mission_open = bool(
        mission.get("id")
        and mission.get("status") in ("open", "driving")
        and not mission.get("dry_run")
    )

    if failed:
        mode, reason = "triage_failed", f"{len(failed)} agent(s) failed — drain + follow-up"
    elif mission_open and (waiting or queued_n):
        mode, reason = "mission_drive", f"mission {mission.get('id')} — avancer la file"
    elif waiting and slots > 0:
        mode, reason = "drain", f"{waiting} en file avec {slots} slot(s)"
    elif coffee >= coffee_min() and slots > 0 and coffee_fill_enabled():
        mode, reason = "coffee_fill", f"café={coffee} ≥ {coffee_min()}"
    elif busy_count >= max_busy():
        mode, reason = "observe", f"cap busy atteint ({busy_count}/{max_busy()})"
    else:
        mode, reason = "observe", "rien d'urgent — observation"

    decision = {
        "mode": mode,
        "reason": reason,
        "busy_agent_count": busy_count,
        "slots_free": slots,
        "coffee_idle": coffee,
        "queued_waiting": waiting,
        "queued_count": queued_n,
        "failed_count": len(failed),
        "mission_open": mission_open,
        "ts": time.time(),
    }
    _set_decision(decision)
    return decision


def conduct(*, dry_run: bool = False, max_starts_override: int | None = None) -> dict[str, Any]:
    global _last_coffee_spawn_ts
    if not enabled() and not dry_run:
        report = {
            "ok": True,
            "enabled": False,
            "dry_run": dry_run,
            "outcome": "disabled",
            "note": "LBG_TEAM_CAMPUS_CONDUCTOR_ENABLED=0",
        }
        _set_report(report)
        return report

    cap = max_busy()
    starts_budget = max_starts() if max_starts_override is None else max(0, int(max_starts_override))
    running = _running_tasks()
    queued = _queued_tasks()
    busy_ids = _busy_agent_ids(running)
    busy_count = len(busy_ids)
    slots = max(0, cap - busy_count)

    candidates: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    reserved_agents: set[str] = set(busy_ids)

    for task in queued:
        ok, why = _can_autorun(task)
        if not ok:
            skipped.append({"task_id": task.id, "role": task.role, "reason": why})
            continue
        aid = resolve_presence_agent_id(task)
        if aid in reserved_agents:
            skipped.append({"task_id": task.id, "role": task.role, "reason": "agent_busy", "agent_id": aid})
            continue
        if len(candidates) >= slots or len(candidates) >= starts_budget:
            skipped.append(
                {
                    "task_id": task.id,
                    "role": task.role,
                    "reason": "max_busy_reached" if len(candidates) >= slots else "max_starts_tick",
                    "agent_id": aid,
                }
            )
            continue
        candidates.append(
            {
                "task_id": task.id,
                "role": task.role,
                "agent_id": aid,
                "objective": (task.objective or "")[:120],
                "source": "queued",
            }
        )
        reserved_agents.add(aid)

    idle_notes = analyze_idle()
    coffee_proposals = _coffee_spawn_proposals(
        idle_notes,
        reserved_agents=reserved_agents,
        slots_left=min(max(0, slots - len(candidates)), max(0, starts_budget - len(candidates))),
    )

    started: list[dict[str, Any]] = []
    spawned: list[dict[str, Any]] = []
    _emit_conductor(
        "busy",
        f"Audit campus — {busy_count} busy / {len(queued)} queued / "
        f"{len(candidates)} prefill / {len(coffee_proposals)} coffee",
    )

    if not dry_run:
        for c in candidates:
            started.append(dict(c))
            threading.Thread(
                target=_run_task_safe,
                args=(str(c["task_id"]),),
                name=f"campus-conductor-{str(c['task_id'])[:8]}",
                daemon=True,
            ).start()
        for prop in coffee_proposals:
            try:
                task = team_store.create_task(
                    role=str(prop["role"]),
                    objective=str(prop["objective"]),
                    actor_id=ACTOR_ID,
                    priority="normal",
                    approval_required=False,
                    context=dict(prop.get("context") or {}),
                )
                row = {
                    "task_id": task.id,
                    "role": task.role,
                    "agent_id": prop.get("agent_id"),
                    "objective": (task.objective or "")[:120],
                    "source": "coffee_fill",
                }
                spawned.append(row)
                started.append(row)
                _last_coffee_spawn_ts = time.time()
                threading.Thread(
                    target=_run_task_safe,
                    args=(task.id,),
                    name=f"campus-coffee-{task.id[:8]}",
                    daemon=True,
                ).start()
            except Exception as exc:
                skipped.append({"role": prop.get("role"), "reason": f"coffee_spawn_error:{exc}"})
    else:
        spawned = [{**p, "dry_run": True} for p in coffee_proposals]

    if dry_run:
        outcome = "dry_run"
    elif started:
        outcome = "started"
    elif coffee_proposals:
        outcome = "coffee_planned"
    else:
        outcome = "nothing_to_start"

    report: dict[str, Any] = {
        "ok": True,
        "enabled": enabled(),
        "dry_run": dry_run,
        "outcome": outcome,
        "max_busy": cap,
        "max_starts": starts_budget,
        "running_count": len(running),
        "busy_agent_count": busy_count,
        "queued_count": len(queued),
        "slots_free": slots,
        "candidates": candidates,
        "coffee_proposals": coffee_proposals if dry_run else spawned,
        "coffee_fill": {
            "enabled": coffee_fill_enabled(),
            "min_coffee": coffee_min(),
            "max_spawn": coffee_max_spawn(),
            "cooldown_s": coffee_cooldown_s(),
            "utility_s": coffee_utility_s(),
            "coffee_idle": sum(1 for n in idle_notes if n.get("reason") == "coffee_available"),
        },
        "started": started,
        "skipped": skipped[:40],
        "idle_notes": idle_notes,
        "ts": time.time(),
    }
    _set_report(report)
    if started and not dry_run:
        _emit_conductor(
            "busy",
            f"Prefill/coffee {len(started)} — "
            + ", ".join(str(s.get("agent_id") or s.get("role") or "?") for s in started)[:100],
            task_id=started[0].get("task_id"),
        )
    else:
        coffee = sum(1 for n in idle_notes if n.get("reason") == "coffee_available")
        waiting = sum(1 for n in idle_notes if n.get("reason") == "queued_waiting_slot")
        _emit_conductor("idle", f"Campus OK — café={coffee} file={waiting} busy={busy_count}")
    return report


def act(*, dry_run: bool = False, max_starts_override: int | None = None) -> dict[str, Any]:
    if not enabled() and not dry_run:
        return {"ok": True, "enabled": False, "outcome": "disabled", "decision": {"mode": "disabled"}}

    decision = decide_action()
    mode = str(decision.get("mode") or "observe")
    _emit_conductor("busy", f"Mode {mode} — {decision.get('reason')}")

    if mode == "observe":
        report = {
            "ok": True,
            "enabled": enabled(),
            "dry_run": dry_run,
            "outcome": "observe",
            "decision": decision,
            "started": [],
            "ts": time.time(),
        }
        _set_report(report)
        _emit_conductor("idle", f"Observe — {decision.get('reason')}")
        return report

    report = conduct(dry_run=dry_run, max_starts_override=max_starts_override)
    report["decision"] = decision
    report["acted_as"] = mode
    _set_report(report)

    mission = last_mission()
    if mission.get("id") and mission.get("status") in ("open", "driving"):
        mission = dict(mission)
        mission["status"] = "driving"
        mission["last_act_ts"] = time.time()
        mission["last_mode"] = mode
        _set_mission(mission)
    return report


def start_mission(
    objective: str,
    *,
    dry_run: bool = False,
    auto_act: bool = True,
    max_tasks: int = 6,
) -> dict[str, Any]:
    text = (objective or "").strip()
    if not text:
        return {"ok": False, "error": "objective vide"}

    mission_id = str(uuid.uuid4())
    proposals = team_roles.plan_from_objective(text, actor_id=ACTOR_ID)
    created: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    _emit_conductor("busy", f"Mission — {text[:80]}")

    for prop in proposals[: max(1, max_tasks)]:
        role = str(prop.get("role") or "")
        need_l2 = bool(prop.get("approval_required"))
        ctx = dict(prop.get("context") or {})
        ctx["_campus_mission_id"] = mission_id
        ctx["_campus_mission_objective"] = text[:200]
        if need_l2:
            skipped.append({"role": role, "reason": "approval_required", "objective": prop.get("objective")})
            continue
        if role == "player_ia" and (
            ctx.get("think_tick") or "think" in str(prop.get("objective") or "").lower()
        ):
            skipped.append({"role": role, "reason": "player_ia_think_L2"})
            continue
        allow = roles_allowlist()
        if allow is not None and role not in allow:
            skipped.append({"role": role, "reason": f"role_not_in_allowlist:{role}"})
            continue
        row = {"role": role, "objective": str(prop.get("objective") or text)[:400], "context": ctx}
        if dry_run:
            created.append({**row, "dry_run": True})
            continue
        task = team_store.create_task(
            role=role,
            objective=row["objective"],
            actor_id=ACTOR_ID,
            priority=str(prop.get("priority") or "normal"),
            approval_required=False,
            context=ctx,
        )
        created.append({"task_id": task.id, **row})

    mission = {
        "id": mission_id,
        "objective": text,
        "status": "open" if created else "empty",
        "created_ts": time.time(),
        "task_ids": [c.get("task_id") for c in created if c.get("task_id")],
        "dry_run": dry_run,
    }
    _set_mission(mission)

    act_report = None
    if auto_act and created and not dry_run and enabled():
        act_report = act(dry_run=False)
        mission["status"] = "driving"
        _set_mission(mission)
    elif dry_run:
        _emit_conductor("idle", f"Mission dry-run — {len(created)} tâches")
    else:
        _emit_conductor("idle", "Mission sans tâche L1" if not created else f"Mission {len(created)} tâches")

    return {
        "ok": True,
        "mission": mission,
        "proposals": proposals,
        "created": created,
        "skipped": skipped,
        "act": act_report,
        "decision": last_decision(),
    }


def _run_task_safe(task_id: str) -> None:
    try:
        team_roles.run_task(task_id)
    except Exception as exc:
        try:
            team_store.update_task(
                task_id,
                status="failed",
                result={"ok": False, "error": f"campus_conductor_run: {exc}", "kind": "campus_conductor"},
            )
        except Exception:
            return


def status() -> dict[str, Any]:
    snap = team_presence.snapshot(mode="live")
    running = _running_tasks()
    queued = _queued_tasks()
    idle = analyze_idle(snap)
    decision = decide_action(snap)
    return {
        "ok": True,
        "enabled": enabled(),
        "max_busy": max_busy(),
        "max_starts": max_starts(),
        "roles_allowlist": sorted(roles_allowlist() or []),
        "running_count": len(running),
        "busy_agent_count": len(_busy_agent_ids(running)),
        "queued_count": len(queued),
        "decision": decision,
        "mission": last_mission(),
        "coffee_fill": {
            "enabled": coffee_fill_enabled(),
            "min_coffee": coffee_min(),
            "max_spawn": coffee_max_spawn(),
            "cooldown_s": coffee_cooldown_s(),
            "utility_s": coffee_utility_s(),
            "coffee_idle": sum(1 for n in idle if n.get("reason") == "coffee_available"),
        },
        "idle_notes": idle,
        "failed_agents": [
            {
                "agent_id": a.get("agent_id"),
                "display_name": a.get("display_name"),
                "task_id": a.get("task_id"),
            }
            for a in _failed_agents(snap)
        ],
        "last_report": last_report(),
        "conductor_agent_id": CONDUCTOR_AGENT_ID,
        "docs": ["docs/plan_campus_conductor.md", "docs/lbg_agentic_os.md"],
    }
