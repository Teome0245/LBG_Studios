"""Playbook Ops Health Pilot — perception → diagnostic → décision → notify → L2 → lesson.

Dry-run par défaut : aucune notif Slack, aucune tâche L2 créée.
Live (dry_run=false) : notify sur KO (défaut), spawn L2 + push HITL, lesson.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any


def state_path() -> Path:
    raw = os.environ.get("LBG_OPS_HEALTH_PILOT_STATE", "").strip()
    if raw:
        return Path(raw)
    return Path("/var/lib/lbg/ops_health_pilot/state.json")


def _load_state() -> dict[str, Any]:
    path = state_path()
    try:
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        pass
    return {}


def _save_state(data: dict[str, Any]) -> None:
    path = state_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass


def last_run() -> dict[str, Any]:
    st = _load_state()
    last = st.get("last_run")
    return last if isinstance(last, dict) else {}


def _perimeter_ok(platform: dict[str, Any]) -> bool:
    try:
        from team.admin_infra_element import perimeter_has_ko

        return not perimeter_has_ko(platform)
    except Exception:
        hosts = platform.get("hosts") if isinstance(platform.get("hosts"), list) else []
        for h in hosts:
            if isinstance(h, dict) and h.get("ok") is False:
                return False
        return True


def _format_summary(platform: dict[str, Any], *, perimeter_ok: bool) -> str:
    hosts = platform.get("hosts") if isinstance(platform.get("hosts"), list) else []
    required = [h for h in hosts if isinstance(h, dict) and h.get("required", True)]
    req_ok = sum(1 for h in required if h.get("ok"))
    lines = [
        f"ops_health_pilot · périmètre={'OK' if perimeter_ok else 'KO'}",
        f"requis={req_ok}/{len(required)} · hosts={len(hosts)} · perimeter={platform.get('perimeter') or []}",
    ]
    for h in hosts[:12]:
        if not isinstance(h, dict):
            continue
        required_h = bool(h.get("required", True))
        if h.get("ok"):
            mark = "OK"
        elif required_h:
            mark = "KO"
        else:
            mark = "OFF"  # optionnel éteint volontairement (ex. PreCU 245)
        lines.append(f"  [{mark}] {h.get('perimeter_id')} {h.get('label')} ({h.get('host')})")
    return "\n".join(lines)


def _pilot_base_url() -> str:
    return (
        os.environ.get("LBG_PILOT_PUBLIC_URL", "").strip()
        or os.environ.get("LBG_BACKEND_SELF_URL", "http://192.168.0.140:8000").rstrip("/")
    )


def _find_open_remediation_task() -> dict[str, Any] | None:
    """Évite le sprawl : réutiliser une remédiation ops_health encore ouverte."""
    try:
        from team import store as team_store

        for t in team_store.list_tasks(role="ops", limit=80):
            ctx = t.context if isinstance(t.context, dict) else {}
            if not ctx.get("ops_health_pilot"):
                continue
            if t.status in ("done", "failed", "cancelled"):
                continue
            return {
                "id": t.id,
                "status": t.status,
                "approval_required": bool(t.approval_required),
                "objective": t.objective,
            }
    except Exception:
        return None
    return None


def _notify_resolve(notify: bool | None, *, dry_run: bool) -> bool:
    """notify=None → auto : True en live, False en dry-run."""
    if notify is not None:
        return bool(notify)
    return not dry_run


def run_ops_health_pilot(
    *,
    dry_run: bool = True,
    notify: bool | None = None,
    spawn_l2_remediation: bool = True,
    actor_id: str = "pilot:ops_health",
    include_smoke: bool = False,
    persist: bool = True,
) -> dict[str, Any]:
    """Exécute le pilote ops. ``dry_run=True`` = simulation complète sans effets."""
    started = time.time()
    steps: list[dict[str, Any]] = []
    do_notify = _notify_resolve(notify, dry_run=dry_run)

    # 1. Perception
    from team.admin_infra_platform import audit_admin_infra_platform

    platform = audit_admin_infra_platform()
    steps.append(
        {
            "id": "perception",
            "ok": True,
            "detail": "audit_admin_infra_platform",
            "hosts": len(platform.get("hosts") or []) if isinstance(platform, dict) else 0,
        }
    )

    # 2. Diagnostic
    smoke: dict[str, Any] = {"ok": True, "skipped": True, "reason": "include_smoke=false"}
    if include_smoke:
        try:
            from team.roles import _run_qa_smoke_script

            smoke = _run_qa_smoke_script()
            if not isinstance(smoke, dict):
                smoke = {"ok": False, "error": "smoke_non_dict"}
        except Exception as exc:
            smoke = {"ok": False, "error": str(exc)}
    steps.append(
        {
            "id": "diagnostic",
            "ok": bool(smoke.get("ok", True)),
            "skipped": bool(smoke.get("skipped")),
            "smoke": {
                k: smoke.get(k)
                for k in ("ok", "skipped", "error", "reason", "exit_code")
                if k in smoke
            },
        }
    )

    # 3. Décision
    perimeter_ok = _perimeter_ok(platform if isinstance(platform, dict) else {})
    smoke_ok = bool(smoke.get("ok", True)) or bool(smoke.get("skipped"))
    decision = "healthy" if (perimeter_ok and smoke_ok) else "remediate"
    summary = _format_summary(
        platform if isinstance(platform, dict) else {}, perimeter_ok=perimeter_ok
    )
    steps.append(
        {
            "id": "decision",
            "ok": True,
            "decision": decision,
            "perimeter_ok": perimeter_ok,
            "smoke_ok": smoke_ok,
        }
    )

    # 4. Remédiation L2 (avant notify pour inclure task_id dans le message)
    remediation: dict[str, Any] = {"ok": True, "skipped": True}
    rem_task_id: str | None = None
    if decision == "remediate" and spawn_l2_remediation:
        existing = _find_open_remediation_task()
        if existing:
            rem_task_id = str(existing["id"])
            remediation = {
                "ok": True,
                "skipped": False,
                "deduped": True,
                "task_id": rem_task_id,
                "status": existing.get("status"),
                "approval_required": True,
            }
        elif dry_run:
            remediation = {
                "ok": True,
                "skipped": True,
                "reason": "dry_run",
                "would_create": {
                    "role": "ops",
                    "approval_required": True,
                    "objective": "Remédiation Ops Health Pilot — corriger hôtes KO (allowlist)",
                },
            }
        else:
            try:
                from team import store as team_store

                task = team_store.create_task(
                    role="ops",
                    objective=(
                        "Remédiation Ops Health Pilot — corriger hôtes KO du périmètre LAN "
                        "(actions allowlist uniquement, pas de shell libre)"
                    ),
                    actor_id=actor_id,
                    approval_required=True,
                    context={
                        "ops_health_pilot": True,
                        "ops_kind": "remediation",
                        "parent_playbook": "ops_health_pilot",
                        "perimeter_ok": perimeter_ok,
                        "platform_gaps": (
                            platform.get("gaps") if isinstance(platform, dict) else None
                        ),
                        "human_summary": summary[:500],
                    },
                )
                rem_task_id = task.id
                remediation = {
                    "ok": True,
                    "skipped": False,
                    "deduped": False,
                    "task_id": task.id,
                    "status": task.status,
                    "approval_required": True,
                }
                # HITL Slack / Element (B4)
                try:
                    from lbg_agents.ops_notify import send_l2_pending

                    hitl = send_l2_pending(
                        {
                            "id": task.id,
                            "role": task.role,
                            "objective": task.objective,
                            "status": task.status,
                            "actor_id": task.actor_id,
                            "approval_required": True,
                        }
                    )
                    remediation["hitl"] = hitl
                except Exception as exc:
                    remediation["hitl"] = {"ok": False, "error": str(exc)}
            except Exception as exc:
                remediation = {"ok": False, "skipped": False, "error": str(exc)}
    steps.append({"id": "remediation_l2", **remediation})

    # 5. Notification (B2) — après L2 pour lien tâche
    notify_out: dict[str, Any] = {"ok": True, "skipped": True}
    should_notify = do_notify and decision == "remediate"
    if should_notify and not dry_run:
        try:
            from lbg_agents.ops_notify import send_text

            pilot = _pilot_base_url()
            task_bit = (
                f"\n• tâche L2 : {rem_task_id}\n• approve : Pilot {pilot}/pilot/#/team?task={rem_task_id}"
                if rem_task_id
                else f"\n• Fleet : {pilot}/pilot/#/team/fleet"
            )
            msg = (
                "🚨 Ops Health Pilot — périmètre KO\n"
                f"{summary}"
                f"{task_bit}"
            )
            notify_out = send_text(msg)
            if not isinstance(notify_out, dict):
                notify_out = {"ok": True, "raw": notify_out}
            notify_out["skipped"] = False
        except Exception as exc:
            notify_out = {"ok": False, "error": str(exc), "skipped": False}
    elif dry_run and do_notify:
        notify_out = {
            "ok": True,
            "skipped": True,
            "reason": "dry_run",
            "would_notify": decision == "remediate",
            "would_include_task": rem_task_id,
        }
    elif decision == "healthy":
        notify_out = {"ok": True, "skipped": True, "reason": "healthy"}
    steps.append({"id": "notify", **notify_out})

    # 6. Lesson (B5)
    lesson: dict[str, Any] = {"ok": True, "skipped": True}
    if not dry_run and decision == "remediate":
        try:
            from team import lessons_learned

            refs = ["ops_health_pilot", "plan_combler_gaps_agentiques"]
            if rem_task_id:
                refs.append(f"task:{rem_task_id}")
            entry = lessons_learned.append_lesson(
                agent_role="ops",
                pattern="ops_health_pilot perimeter KO",
                context=summary[:800],
                failure_or_success="failure",
                do_not_repeat="Ne pas ignorer un hôte KO du périmètre sans remédiation L2.",
                refs=refs,
            )
            lesson = {
                "ok": True,
                "skipped": False,
                "lesson_id": (entry or {}).get("id") if isinstance(entry, dict) else None,
            }
        except Exception as exc:
            lesson = {"ok": False, "skipped": False, "error": str(exc)}
    elif dry_run:
        lesson = {"ok": True, "skipped": True, "reason": "dry_run"}
    steps.append({"id": "lesson", **lesson})

    elapsed_ms = int((time.time() - started) * 1000)
    out: dict[str, Any] = {
        "ok": True,
        "playbook": "ops_health_pilot",
        "dry_run": dry_run,
        "notify": do_notify,
        "decision": decision,
        "perimeter_ok": perimeter_ok,
        "summary": summary,
        "remediation_task_id": rem_task_id,
        "steps": steps,
        "platform": {
            "perimeter": platform.get("perimeter") if isinstance(platform, dict) else None,
            "gaps": platform.get("gaps") if isinstance(platform, dict) else None,
            "hosts_ok": (
                platform.get("hosts_ok")
                if isinstance(platform, dict) and platform.get("hosts_ok") is not None
                else sum(
                    1
                    for h in (platform.get("hosts") or [] if isinstance(platform, dict) else [])
                    if isinstance(h, dict) and h.get("required", True) and h.get("ok")
                )
            ),
            "hosts_total": (
                platform.get("hosts_total")
                if isinstance(platform, dict) and platform.get("hosts_total") is not None
                else sum(
                    1
                    for h in (platform.get("hosts") or [] if isinstance(platform, dict) else [])
                    if isinstance(h, dict) and h.get("required", True)
                )
            ),
        },
        "elapsed_ms": elapsed_ms,
        "docs": ["docs/plan_combler_gaps_agentiques.md", "docs/runbook_ops_health_pilot.md"],
    }

    if persist:
        _save_state(
            {
                "last_run": {
                    "ts": time.time(),
                    "dry_run": dry_run,
                    "decision": decision,
                    "perimeter_ok": perimeter_ok,
                    "remediation_task_id": rem_task_id,
                    "elapsed_ms": elapsed_ms,
                    "summary": summary[:400],
                }
            }
        )
    return out
