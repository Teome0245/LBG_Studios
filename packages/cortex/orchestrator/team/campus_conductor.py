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
_mission_loaded: bool = False


def mission_persist_path() -> str:
    raw = os.environ.get("LBG_TEAM_MISSION_PATH", "").strip()
    if raw:
        return raw
    db = os.environ.get("LBG_TEAM_DB_PATH", "/var/lib/lbg-ia-mmo/team_tasks.db").strip()
    if db and db != ":memory:":
        from pathlib import Path

        return str(Path(db).with_name("campus_mission.json"))
    return "/var/lib/lbg-ia-mmo/campus_mission.json"


def _load_mission_from_disk() -> dict[str, Any]:
    path = mission_persist_path()
    try:
        import json
        from pathlib import Path

        p = Path(path)
        if not p.is_file():
            return {}
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_mission_to_disk(mission: dict[str, Any]) -> None:
    path = mission_persist_path()
    try:
        import json
        from pathlib import Path

        p = Path(path)
        if p.parent and str(p.parent) not in (".", ""):
            p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(p.suffix + ".tmp")
        payload = dict(mission)
        payload["_persisted_ts"] = time.time()
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(p)
    except Exception:
        return


_COFFEE_PLAYBOOKS: list[dict[str, Any]] = [
    {
        "agent_ids": ("studio_qa_argus",),
        "role": "qa",
        "objective": "Smoke LAN read-only — healthz + systemd (coffee fill Conductor)",
        "context": {"_campus_coffee_fill": True, "presence_agent_id": "studio_qa_argus", "utility_key": "qa_smoke"},
        "utility_key": "qa_smoke",
    },
    {
        "agent_ids": ("studio_qa_argus",),
        "role": "qa",
        "objective": "Owner smokes Godot login M11+M12 (coffee fill — PLAN_MMO_O2 A2)",
        "context": {
            "_campus_coffee_fill": True,
            "presence_agent_id": "studio_qa_argus",
            "owner_smoke_bundle": "godot_login",
            "mmo_jalon": True,
            "utility_key": "qa_godot_owners",
        },
        "utility_key": "qa_godot_owners",
    },
    {
        "agent_ids": ("studio_ops_hephaistos",),
        "role": "ops",
        "objective": "Sonde santé orchestrateur et backend (read-only, coffee fill)",
        "context": {"_campus_coffee_fill": True, "presence_agent_id": "studio_ops_hephaistos", "utility_key": "ops_probe"},
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
            "utility_key": "pm_brief",
        },
        "utility_key": "pm_brief",
    },
    {
        "agent_ids": ("admin_infra", "studio_admin_atlas"),
        "role": "admin_infra",
        "objective": "Audit rapide infra LLM locale / dual host (coffee fill)",
        "context": {"_campus_coffee_fill": True, "presence_agent_id": "admin_infra", "utility_key": "admin_audit"},
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
    global _mission_loaded, _last_mission
    with _lock:
        if not _mission_loaded:
            disk = _load_mission_from_disk()
            if disk and not _last_mission:
                _last_mission = dict(disk)
            _mission_loaded = True
        return dict(_last_mission)


def auto_close_enabled() -> bool:
    return os.environ.get("LBG_TEAM_CAMPUS_MISSION_AUTO_CLOSE", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def last_decision() -> dict[str, Any]:
    with _lock:
        return dict(_last_decision)


def _set_report(report: dict[str, Any]) -> None:
    with _lock:
        global _last_report
        _last_report = dict(report)


def _set_mission(mission: dict[str, Any]) -> None:
    global _last_mission, _mission_loaded
    with _lock:
        _last_mission = dict(mission)
        _mission_loaded = True
    if mission:
        _save_mission_to_disk(mission)
    else:
        try:
            from pathlib import Path

            p = Path(mission_persist_path())
            if p.is_file():
                p.unlink()
        except Exception:
            pass


def _mission_tasks(mission: dict[str, Any]) -> list[TeamTask]:
    ids = [str(x) for x in (mission.get("task_ids") or []) if x]
    out: list[TeamTask] = []
    for tid in ids:
        t = team_store.get_task(tid)
        if t is not None:
            out.append(t)
    return out


def _task_result_ok(task: TeamTask) -> bool | None:
    if task.status == "cancelled":
        return None
    if task.status != "done":
        return False
    res = task.result if isinstance(task.result, dict) else {}
    if "ok" in res:
        return bool(res.get("ok"))
    # done sans champ ok → considéré succès opérationnel
    return True


def block_close_on_smoke_fail() -> bool:
    """A2 — smoke QA/owner rouge : ne pas auto-clôturer (reste ouverte pour reprise)."""
    return os.environ.get("LBG_TEAM_MISSION_BLOCK_CLOSE_ON_SMOKE_FAIL", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _mission_requires_owner_smoke(mission: dict[str, Any], tasks: list[TeamTask]) -> bool:
    if mission.get("require_owner_smoke") or mission.get("_require_owner_smoke"):
        return True
    for t in tasks:
        ctx = t.context if isinstance(t.context, dict) else {}
        if ctx.get("owner_smoke_bundle") or ctx.get("mmo_jalon") or ctx.get("_require_owner_smoke"):
            return True
        if t.role in ("dev_godot",) or str(ctx.get("godot_dev_persona") or ""):
            return True
    return False


def evaluate_mission_closure(mission: dict[str, Any] | None = None) -> dict[str, Any]:
    """Évalue si la mission Lyra peut être clôturée.

    Règles (Vague 4 + A2 PLAN_MMO_O2) :
    - toutes les tâches de la mission sont terminales (done|failed|cancelled)
    - smoke vert : si la mission contient du QA, tous les QA done avec result.ok≠false
    - mission Godot/jalon : QA obligatoire et smoke_ok True
    - smoke rouge + LBG_TEAM_MISSION_BLOCK_CLOSE_ON_SMOKE_FAIL=1 → pas closable
    - sinon (pas de QA) : clôture succès si aucune failed
    - s'il reste des failed → closable avec outcome closed_failed (sauf block smoke)
    """
    m = dict(mission or last_mission())
    mid = str(m.get("id") or "")
    status = str(m.get("status") or "")
    if not mid or status not in ("open", "driving"):
        return {
            "closable": False,
            "reason": "no_open_mission",
            "mission_id": mid or None,
            "status": status or None,
        }
    if m.get("dry_run"):
        return {"closable": False, "reason": "dry_run_mission", "mission_id": mid}

    tasks = _mission_tasks(m)
    if not tasks:
        return {
            "closable": True,
            "outcome": "closed_empty",
            "reason": "aucune tâche liée",
            "mission_id": mid,
            "task_stats": {"total": 0},
            "smoke_ok": None,
        }

    terminal = {"done", "failed", "cancelled"}
    pending = [t for t in tasks if t.status not in terminal]
    done = [t for t in tasks if t.status == "done"]
    failed = [t for t in tasks if t.status == "failed"]
    cancelled = [t for t in tasks if t.status == "cancelled"]
    stats = {
        "total": len(tasks),
        "pending": len(pending),
        "done": len(done),
        "failed": len(failed),
        "cancelled": len(cancelled),
    }

    if pending:
        return {
            "closable": False,
            "reason": f"{len(pending)} tâche(s) encore active(s)",
            "mission_id": mid,
            "task_stats": stats,
            "pending_ids": [t.id for t in pending[:8]],
        }

    qa_tasks = [t for t in tasks if t.role == "qa"]
    need_owner = _mission_requires_owner_smoke(m, tasks)
    smoke_ok: bool | None
    smoke_note: str
    if not qa_tasks:
        if need_owner:
            smoke_ok = False
            smoke_note = "owner_smoke_required_no_qa"
        else:
            smoke_ok = None
            smoke_note = "no_qa_in_mission"
    else:
        bad = [t for t in qa_tasks if _task_result_ok(t) is False]
        if bad:
            smoke_ok = False
            smoke_note = f"qa_not_green:{bad[0].id[:8]}"
        else:
            smoke_ok = True
            smoke_note = "qa_green"
            if need_owner:
                # Exiger au moins un résultat owner_smokes.ok si le bundle était demandé.
                owner_seen = False
                owner_bad = False
                for t in qa_tasks:
                    res = t.result if isinstance(t.result, dict) else {}
                    os_block = res.get("owner_smokes")
                    if isinstance(os_block, dict):
                        owner_seen = True
                        if os_block.get("ok") is False:
                            owner_bad = True
                    elif res.get("smoke_ok") is False:
                        owner_bad = True
                        owner_seen = True
                if owner_bad:
                    smoke_ok = False
                    smoke_note = "owner_smoke_red"
                elif not owner_seen:
                    # QA vert générique sans owner bundle — acceptable si pas de bundle explicite
                    # sur une tâche ; sinon note soft.
                    explicit = any(
                        isinstance(t.context, dict) and t.context.get("owner_smoke_bundle")
                        for t in qa_tasks
                    )
                    if explicit:
                        smoke_ok = False
                        smoke_note = "owner_smoke_missing_in_qa_result"

    if smoke_ok is False and block_close_on_smoke_fail():
        return {
            "closable": False,
            "reason": f"smoke_owner_red:{smoke_note}",
            "mission_id": mid,
            "task_stats": stats,
            "smoke_ok": False,
            "smoke_note": smoke_note,
            "blocked_on_smoke": True,
        }

    if failed or smoke_ok is False:
        return {
            "closable": True,
            "outcome": "closed_failed",
            "reason": smoke_note if smoke_ok is False else f"{len(failed)} failed",
            "mission_id": mid,
            "task_stats": stats,
            "smoke_ok": smoke_ok,
            "smoke_note": smoke_note,
        }

    return {
        "closable": True,
        "outcome": "closed",
        "reason": "toutes tâches terminales" + (f" · {smoke_note}" if smoke_note else ""),
        "mission_id": mid,
        "task_stats": stats,
        "smoke_ok": smoke_ok,
        "smoke_note": smoke_note,
    }


def close_mission(
    *,
    force: bool = False,
    reason: str = "",
    actor_id: str = ACTOR_ID,
) -> dict[str, Any]:
    """Clôture manuelle ou forcée de la mission courante."""
    mission = last_mission()
    mid = str(mission.get("id") or "")
    if not mid:
        return {"ok": False, "error": "aucune mission"}
    if mission.get("status") not in ("open", "driving") and not force:
        return {"ok": False, "error": f"mission déjà {mission.get('status')}", "mission": mission}

    evaluation = evaluate_mission_closure(mission)
    if not evaluation.get("closable") and not force:
        return {"ok": False, "error": evaluation.get("reason") or "not_closable", "evaluation": evaluation}

    outcome = str(evaluation.get("outcome") or ("closed" if force else "closed"))
    if force and not evaluation.get("closable"):
        outcome = "closed_forced"
    closed = dict(mission)
    closed["status"] = outcome
    closed["closed_ts"] = time.time()
    closed["close_reason"] = (reason or str(evaluation.get("reason") or "")).strip()[:300]
    closed["close_evaluation"] = {
        k: evaluation.get(k)
        for k in ("task_stats", "smoke_ok", "smoke_note", "outcome")
        if k in evaluation
    }
    _set_mission(closed)

    try:
        from team import bus_hooks

        bus_hooks.emit_verify_result(
            task_id=mid,
            from_agent=bus_hooks.AGENT_LYRA,
            ok=outcome == "closed",
            summary=f"mission {outcome}: {closed.get('close_reason')}",
            actor_id=actor_id,
        )
        bus_hooks.safe_append(
            from_agent=bus_hooks.AGENT_LYRA,
            to_agent=bus_hooks.AGENT_THEMIS,
            kind="ack",
            payload={"mission_id": mid, "status": outcome, "objective": str(closed.get("objective") or "")[:160]},
            task_id=mid,
            actor_id=actor_id,
        )
    except Exception:
        pass

    try:
        from team import memory as team_memory

        if team_memory.memory_enabled():
            team_memory.append_learning(
                agent_id="lyra",
                summary=f"Mission {outcome} — {str(closed.get('objective') or '')[:120]}",
                kind="mission_close",
                tags=["campus", "mission", outcome],
                task_id=mid,
                meta={"smoke_ok": evaluation.get("smoke_ok"), "stats": evaluation.get("task_stats")},
            )
    except Exception:
        pass

    label = "vert" if outcome == "closed" else outcome
    _emit_conductor("idle", f"Mission clôturée ({label}) — {str(closed.get('objective') or '')[:60]}")
    return {"ok": True, "mission": closed, "evaluation": evaluation}


def maybe_close_mission(*, actor_id: str = ACTOR_ID) -> dict[str, Any] | None:
    """Auto-clôture si critères remplis (flag LBG_TEAM_CAMPUS_MISSION_AUTO_CLOSE)."""
    if not auto_close_enabled():
        return None
    evaluation = evaluate_mission_closure()
    if not evaluation.get("closable"):
        return None
    # Auto : on ferme succès ET échec (file terminée) — pas force sur pending
    return close_mission(force=False, reason=str(evaluation.get("reason") or "auto"), actor_id=actor_id)


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
        if role == "qa" and utility_key in ("qa_smoke", "qa_godot_owners"):
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

    from team import playbook_scores

    # A3 : ordonner les playbooks par score (mémoire + historique)
    ranked = playbook_scores.rank_playbooks(list(_COFFEE_PLAYBOOKS))

    proposals: list[dict[str, Any]] = []
    for pb, score_info in ranked:
        if len(proposals) >= min(coffee_max_spawn(), slots_left):
            break
        if not score_info.get("eligible", True):
            continue
        match_id = next((aid for aid in pb["agent_ids"] if aid in coffee_ids and aid not in reserved_agents), None)
        if not match_id:
            continue
        role = str(pb["role"])
        allow = roles_allowlist()
        if allow is not None and role not in allow:
            continue
        if _recent_coffee_fill_for_role(role):
            continue
        util_key = str(pb.get("utility_key") or role)
        util_ok, util_why = _coffee_utility_ok(role, util_key)
        if not util_ok:
            continue
        ctx = dict(pb["context"])
        ctx["utility_key"] = util_key
        proposals.append(
            {
                "kind": "coffee_fill",
                "agent_id": match_id,
                "role": role,
                "objective": pb["objective"],
                "context": ctx,
                "utility": util_why,
                "utility_key": util_key,
                "playbook_score": score_info.get("score"),
                "playbook_score_why": score_info.get("why"),
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
    closure = evaluate_mission_closure(mission) if mission_open else {"closable": False}

    if failed:
        mode, reason = "triage_failed", f"{len(failed)} agent(s) failed — drain + follow-up"
    elif mission_open and closure.get("closable"):
        mode, reason = "mission_close", f"mission {mission.get('id')} — {closure.get('reason')}"
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
        "mission_closable": bool(closure.get("closable")),
        "mission_close_outcome": closure.get("outcome"),
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
            "playbook_scoring": True,
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

    if mode == "mission_close":
        closed = None if dry_run else maybe_close_mission()
        report = {
            "ok": True,
            "enabled": enabled(),
            "dry_run": dry_run,
            "outcome": "mission_closed" if closed and closed.get("ok") else ("mission_close_dry" if dry_run else "mission_close_skipped"),
            "decision": decision,
            "mission_close": closed or evaluate_mission_closure(),
            "started": [],
            "ts": time.time(),
        }
        _set_report(report)
        if dry_run:
            _emit_conductor("idle", f"Mission close dry-run — {decision.get('reason')}")
        return report

    if mode == "observe":
        # Même en observe : tenter clôture si file terminée hors decide (race)
        closed = None if dry_run else maybe_close_mission()
        report = {
            "ok": True,
            "enabled": enabled(),
            "dry_run": dry_run,
            "outcome": "observe",
            "decision": decision,
            "started": [],
            "mission_close": closed,
            "ts": time.time(),
        }
        _set_report(report)
        _emit_conductor("idle", f"Observe — {decision.get('reason')}")
        return report

    report = conduct(dry_run=dry_run, max_starts_override=max_starts_override)
    report["decision"] = decision
    report["acted_as"] = mode
    closed = None if dry_run else maybe_close_mission()
    if closed:
        report["mission_close"] = closed
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
    finally:
        _maybe_record_coffee_score(task_id)


def _maybe_record_coffee_score(task_id: str) -> None:
    """A3 — enregistre le résultat coffee fill dans la mémoire (best-effort)."""
    try:
        task = team_store.get_task(task_id)
        if task is None:
            return
        ctx = task.context if isinstance(task.context, dict) else {}
        if not ctx.get("_campus_coffee_fill"):
            return
        from team import playbook_scores

        uk = str(ctx.get("utility_key") or "").strip()
        if not uk:
            return
        res = task.result if isinstance(task.result, dict) else {}
        ok = bool(res.get("ok")) if "ok" in res else str(task.status) == "done"
        playbook_scores.record_coffee_outcome(
            utility_key=uk,
            ok=ok,
            role=str(task.role or ""),
            task_id=task_id,
        )
    except Exception:
        return


def status() -> dict[str, Any]:
    snap = team_presence.snapshot(mode="live")
    running = _running_tasks()
    queued = _queued_tasks()
    idle = analyze_idle(snap)
    decision = decide_action(snap)
    closure = evaluate_mission_closure()
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
        "mission_closure": closure,
        "auto_close": auto_close_enabled(),
        "mission_persist_path": mission_persist_path(),
        "coffee_fill": {
            "enabled": coffee_fill_enabled(),
            "min_coffee": coffee_min(),
            "max_spawn": coffee_max_spawn(),
            "cooldown_s": coffee_cooldown_s(),
            "utility_s": coffee_utility_s(),
            "coffee_idle": sum(1 for n in idle if n.get("reason") == "coffee_available"),
            "playbook_scoring": True,
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
        "docs": ["docs/plan_campus_conductor.md", "docs/lbg_agentic_os.md", "docs/adr/0019-team-plan-llm-bus.md"],
    }
