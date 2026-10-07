"""Mission L3 bornée — stabiliser smoke / périmètre LAN N jours (plan gaps E2–E4).

Pas d'autonomie libre : budget retries, deadline, cap outils, escalade L2 puis stop.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any


ACTIVE = frozenset({"active", "escalated"})


def state_path() -> Path:
    raw = os.environ.get("LBG_SMOKE_LAN_MISSION_STATE", "").strip()
    if raw:
        return Path(raw)
    return Path("/var/lib/lbg/smoke_lan_mission/state.json")


def _load() -> dict[str, Any]:
    path = state_path()
    try:
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        pass
    return {}


def _save(data: dict[str, Any]) -> None:
    path = state_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass


def get_mission() -> dict[str, Any] | None:
    st = _load()
    m = st.get("mission")
    return m if isinstance(m, dict) else None


def _pilot_base() -> str:
    return (
        os.environ.get("LBG_PILOT_PUBLIC_URL", "").strip()
        or os.environ.get("LBG_BACKEND_URL", "").strip()
        or "http://192.168.0.140:8080"
    ).rstrip("/")


def create_mission(
    *,
    days: int = 3,
    budget_retries: int = 5,
    escalate_after_red: int = 2,
    owner_roles: list[str] | None = None,
    actor_id: str = "pilot:smoke_lan_mission",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Crée (ou refuse si déjà active) une mission L3 bornée."""
    days = max(1, min(int(days), 30))
    budget_retries = max(1, min(int(budget_retries), 50))
    escalate_after_red = max(1, min(int(escalate_after_red), 10))
    owners = owner_roles or ["argus", "hephaistos"]

    existing = get_mission()
    if existing and str(existing.get("status") or "") in ACTIVE:
        return {
            "ok": False,
            "error": "mission_already_active",
            "mission": existing,
        }

    now = time.time()
    mission = {
        "id": uuid.uuid4().hex,
        "kind": "smoke_lan_stabilize",
        "status": "active",
        "objective": f"Stabiliser smoke / périmètre LAN pendant {days} jour(s)",
        "owner_roles": list(owners),
        "actor_id": actor_id,
        "created_ts": now,
        "deadline_ts": now + days * 86400.0,
        "days_target": days,
        "days_ok": 0,
        "budget_retries": budget_retries,
        "retries_used": 0,
        "escalate_after_red": escalate_after_red,
        "consecutive_red": 0,
        "cap_tools": ["ops_health_pilot", "devops_probe"],
        "runs": [],
        "l2_task_id": None,
        "last_decision": None,
        "last_tick_ts": None,
        "updated_ts": now,
    }
    if dry_run:
        return {"ok": True, "dry_run": True, "would_create": mission}

    _save({"mission": mission, "updated_ts": now})
    return {"ok": True, "dry_run": False, "mission": mission}


def cancel_mission(*, reason: str = "cancelled_by_operator") -> dict[str, Any]:
    m = get_mission()
    if not m:
        return {"ok": False, "error": "no_mission"}
    m["status"] = "cancelled"
    m["cancel_reason"] = reason
    m["updated_ts"] = time.time()
    _save({"mission": m, "updated_ts": m["updated_ts"]})
    return {"ok": True, "mission": m}


def _append_run(m: dict[str, Any], run: dict[str, Any]) -> None:
    runs = m.get("runs")
    if not isinstance(runs, list):
        runs = []
    runs.append(run)
    m["runs"] = runs[-40:]


def _maybe_lesson(*, decision: str, summary: str, mission_id: str, escalated: bool) -> dict[str, Any]:
    if decision == "healthy" and not escalated:
        return {"ok": True, "skipped": True, "reason": "healthy"}
    try:
        from team import lessons_learned

        entry = lessons_learned.append_lesson(
            agent_role="ops",
            pattern="smoke_lan_mission tick",
            context=summary[:800],
            failure_or_success="failure" if decision != "healthy" else "success",
            do_not_repeat=(
                "Après N rouges consécutifs, escalader L2 et stopper l'auto (pas de boucle infinie)."
                if escalated
                else "Relancer smoke_lan_mission.tick avec budget retries."
            ),
            refs=["smoke_lan_mission", f"mission:{mission_id}", "plan_combler_gaps_agentiques"],
        )
        return {
            "ok": True,
            "skipped": False,
            "lesson_id": (entry or {}).get("id") if isinstance(entry, dict) else None,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def tick_mission(
    *,
    dry_run: bool = False,
    notify: bool | None = None,
    include_smoke: bool = False,
    actor_id: str | None = None,
) -> dict[str, Any]:
    """Observe (ops_health) → compteurs → retry / escalade L2 / stop (E3)."""
    m = get_mission()
    if not m:
        return {"ok": False, "error": "no_mission"}
    status = str(m.get("status") or "")
    if status not in ACTIVE:
        return {"ok": False, "error": f"mission_not_active:{status}", "mission": m}

    now = time.time()
    if float(m.get("deadline_ts") or 0) and now > float(m["deadline_ts"]):
        if int(m.get("days_ok") or 0) >= int(m.get("days_target") or 1):
            m["status"] = "done"
        else:
            m["status"] = "failed"
            m["fail_reason"] = "deadline_exceeded"
        m["updated_ts"] = now
        if not dry_run:
            _save({"mission": m, "updated_ts": now})
        return {"ok": True, "decision": "deadline", "mission": m, "dry_run": dry_run}

    if status == "escalated":
        return {
            "ok": True,
            "skipped": True,
            "reason": "awaiting_l2",
            "mission": m,
            "decision": "awaiting_l2",
        }

    from team import ops_health_pilot

    do_notify = bool(notify) if notify is not None else (not dry_run)
    pilot = ops_health_pilot.run_ops_health_pilot(
        dry_run=dry_run,
        notify=False,
        spawn_l2_remediation=False,
        include_smoke=include_smoke,
        actor_id=actor_id or str(m.get("actor_id") or "pilot:smoke_lan_mission"),
    )
    decision = str(pilot.get("decision") or "?")
    summary = str(pilot.get("summary") or "")[:500]
    perimeter_ok = decision == "healthy"

    run = {
        "ts": now,
        "decision": decision,
        "dry_run": dry_run,
        "perimeter_ok": perimeter_ok,
        "elapsed_ms": pilot.get("elapsed_ms"),
    }

    escalated = False
    rem_task_id: str | None = None
    hitl: dict[str, Any] | None = None

    if dry_run:
        m["last_decision"] = decision
        m["last_tick_ts"] = now
        return {
            "ok": True,
            "dry_run": True,
            "decision": decision,
            "would_update": {
                "days_ok": m.get("days_ok"),
                "consecutive_red": m.get("consecutive_red"),
                "retries_used": m.get("retries_used"),
            },
            "pilot": {"decision": decision, "summary": summary},
            "mission": m,
        }

    if perimeter_ok:
        m["consecutive_red"] = 0
        # Un succès compte pour au plus 1 jour calendaire (UTC) — timer 3h ≠ 8 days_ok/j.
        day_key = time.strftime("%Y-%m-%d", time.gmtime(now))
        if str(m.get("last_ok_day") or "") != day_key:
            m["days_ok"] = int(m.get("days_ok") or 0) + 1
            m["last_ok_day"] = day_key
        if int(m["days_ok"]) >= int(m.get("days_target") or 1):
            m["status"] = "done"
        run["days_ok"] = m["days_ok"]
        run["last_ok_day"] = m.get("last_ok_day")
    else:
        m["consecutive_red"] = int(m.get("consecutive_red") or 0) + 1
        m["retries_used"] = int(m.get("retries_used") or 0) + 1
        run["consecutive_red"] = m["consecutive_red"]
        run["retries_used"] = m["retries_used"]

        over_budget = int(m["retries_used"]) >= int(m.get("budget_retries") or 1)
        over_red = int(m["consecutive_red"]) >= int(m.get("escalate_after_red") or 1)

        if over_budget or over_red:
            escalated = True
            m["status"] = "escalated"
            m["escalate_reason"] = "budget" if over_budget else "consecutive_red"
            # Spawn L2 via playbook live (une seule fois)
            try:
                rem = ops_health_pilot.run_ops_health_pilot(
                    dry_run=False,
                    notify=do_notify,
                    spawn_l2_remediation=True,
                    include_smoke=include_smoke,
                    actor_id=actor_id or str(m.get("actor_id") or "pilot:smoke_lan_mission"),
                )
                rem_task_id = rem.get("remediation_task_id")
                if isinstance(rem_task_id, str) and rem_task_id:
                    m["l2_task_id"] = rem_task_id
                hitl = None
                for step in rem.get("steps") or []:
                    if isinstance(step, dict) and step.get("id") == "remediation_l2":
                        hitl = step.get("hitl") if isinstance(step.get("hitl"), dict) else None
                        if not rem_task_id:
                            rem_task_id = step.get("task_id")
                            if rem_task_id:
                                m["l2_task_id"] = rem_task_id
                run["escalation"] = {
                    "remediation_task_id": rem_task_id,
                    "hitl": hitl,
                    "decision": rem.get("decision"),
                }
            except Exception as exc:
                run["escalation_error"] = str(exc)[:200]
                # Fallback notify texte
                if do_notify:
                    try:
                        from lbg_agents.ops_notify import send_text

                        send_text(
                            "🚨 Smoke LAN mission — escalade L2\n"
                            f"{summary}\n"
                            f"Mission `{m.get('id')}` · retries={m.get('retries_used')}/"
                            f"{m.get('budget_retries')} · red×{m.get('consecutive_red')}\n"
                            f"Fleet : {_pilot_base()}/pilot/#/team/fleet"
                        )
                    except Exception:
                        pass

    m["last_decision"] = decision
    m["last_tick_ts"] = now
    m["updated_ts"] = now
    _append_run(m, run)
    lesson = _maybe_lesson(
        decision=decision,
        summary=summary or f"decision={decision}",
        mission_id=str(m.get("id") or ""),
        escalated=escalated,
    )
    _save({"mission": m, "updated_ts": now})

    return {
        "ok": True,
        "dry_run": False,
        "decision": "escalated" if escalated else decision,
        "escalated": escalated,
        "remediation_task_id": rem_task_id or m.get("l2_task_id"),
        "lesson": lesson,
        "mission": m,
        "pilot_summary": summary,
        "docs": [
            "docs/plan_combler_gaps_agentiques.md",
            "docs/runbook_ops_health_pilot.md",
        ],
    }


def mission_brief() -> dict[str, Any]:
    """Slice Fleet / dashboard (E4)."""
    m = get_mission()
    if not m:
        return {"ok": True, "active": False, "mission": None}
    now = time.time()
    deadline = float(m.get("deadline_ts") or 0)
    return {
        "ok": True,
        "active": str(m.get("status") or "") in ACTIVE,
        "mission": {
            "id": m.get("id"),
            "status": m.get("status"),
            "objective": m.get("objective"),
            "days_ok": m.get("days_ok"),
            "days_target": m.get("days_target"),
            "retries_used": m.get("retries_used"),
            "budget_retries": m.get("budget_retries"),
            "consecutive_red": m.get("consecutive_red"),
            "escalate_after_red": m.get("escalate_after_red"),
            "last_decision": m.get("last_decision"),
            "l2_task_id": m.get("l2_task_id"),
            "deadline_ts": deadline,
            "deadline_in_h": round((deadline - now) / 3600.0, 1) if deadline else None,
            "owner_roles": m.get("owner_roles"),
            "n_runs": len(m.get("runs") or []) if isinstance(m.get("runs"), list) else 0,
            "updated_ts": m.get("updated_ts"),
        },
    }
