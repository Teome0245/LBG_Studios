#!/usr/bin/env python3
"""Helpers spawn équipe — phases dry → contrôle → réel + push ops (Slack + Element)."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Callable

Phase = str  # dry | control | real

PHASE_LABELS = {
    "dry": "DRY-RUN (sondes, pas d'effet serveur)",
    "control": "CONTRÔLE (Argus — compte rendu go/no-go)",
    "real": "RÉEL (L2 ops/dev_game si configuré)",
}


def load_team_job_spawn(root: str) -> tuple[Any, Any, Any]:
    _spawn_path = os.path.join(root, "agents", "src", "lbg_agents", "team_job_spawn.py")
    spec = importlib.util.spec_from_file_location("team_job_spawn", _spawn_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"impossible de charger {_spawn_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.api_json, mod.orchestrator_url, mod.task_run_summary


def merge_context(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    out.update(patch)
    return out


def phase_patch(phase: Phase, *, run_id: str, http_gateway: str, vm: str) -> dict[str, Any]:
    common = {
        "team_spawn_phase": phase,
        "team_spawn_run_id": run_id,
        "element_report": True,
        "lost_heaven_map": True,
    }
    if phase == "dry":
        return merge_context(
            common,
            {
                "devops_dry_run": True,
                "desktop_dry_run": True,
                "opengame_dry_run": True,
                "write_files": False,
                "forge_dry_run": True,
            },
        )
    if phase == "control":
        return merge_context(
            common,
            {
                "devops_dry_run": True,
                "godot_supervisor": True,
                "godot_mode": "full",
                "team_spawn_control": True,
            },
        )
    if phase == "real":
        token = os.environ.get("LBG_DEVOPS_APPROVAL_TOKEN", "").strip() or os.environ.get(
            "LBG_TEAM_APPROVAL_TOKEN", ""
        ).strip()
        patch: dict[str, Any] = {
            "devops_dry_run": False,
            "desktop_dry_run": False,
            "opengame_dry_run": False,
            "write_files": True,
            "forge_real_execution": True,
            "devops_action": {
                "kind": "http_get",
                "url": (
                    f"{http_gateway}/v1/world/npcs_near"
                    "?anchor_x=4749&anchor_z=-737&radius_m=800"
                ),
            },
        }
        if token:
            patch["devops_approval"] = token
        return merge_context(common, patch)
    raise ValueError(f"phase inconnue: {phase}")


def approval_required_for_task(phase: Phase, role: str) -> bool:
    if phase != "real":
        return False
    return role in ("ops", "dev_game")


def create_and_maybe_run_task(
    *,
    api_json: Callable[..., dict[str, Any]],
    orchestrator_url: Callable[[], str],
    task_run_summary: Callable[[dict[str, Any]], dict[str, Any]],
    role: str,
    objective: str,
    actor_id: str,
    context: dict[str, Any],
    phase: Phase,
    auto_run: bool = True,
) -> dict[str, Any]:
    base = orchestrator_url().rstrip("/")
    approval = approval_required_for_task(phase, role)
    created = api_json(
        "POST",
        f"{base}/v1/team/tasks",
        {
            "role": role,
            "objective": objective,
            "actor_id": actor_id,
            "priority": "normal",
            "approval_required": approval,
            "context": context,
        },
    )
    task_id = created.get("id") if isinstance(created, dict) else None
    if not task_id:
        raise ValueError(f"création tâche invalide : {created!r}")

    summary: dict[str, Any] = {
        "task_id": task_id,
        "created": created,
        "ran": None,
        "approval_required": approval,
        "phase": phase,
        "role": role,
    }

    if approval or not auto_run:
        summary["task_status"] = str(created.get("status") or "queued")
        summary["task_ok"] = None
        summary["skipped_run"] = True
        return summary

    approval_token = os.environ.get("LBG_TEAM_APPROVAL_TOKEN", "").strip()
    run_body: dict[str, Any] = {}
    if approval_token:
        run_body["approval_token"] = approval_token
    ran = api_json("POST", f"{base}/v1/team/tasks/{task_id}/run", run_body)
    summary.update(task_run_summary({"task_id": task_id, "created": created, "ran": ran}))
    summary["phase"] = phase
    summary["role"] = role
    return summary


def control_task(*, run_id: str, http_gateway: str, dry_task_ids: list[str]) -> dict[str, Any]:
    ids_line = ", ".join(dry_task_ids[:12]) if dry_task_ids else "(aucun id dry enregistré)"
    return {
        "role": "qa",
        "objective": (
            "Argus — CONTRÔLE phase Lost Heaven / carte / PNJ après dry-run. "
            f"Run spawn `{run_id}`. Tâches dry : {ids_line}. "
            f"Vérifier : GET {http_gateway}/healthz ; "
            f"GET {http_gateway}/v1/world/npcs_near?anchor_x=4749&anchor_z=-737&radius_m=800 ; "
            "supervisor Godot (sidecar 246, lbg-ws/2 readiness). "
            "Livrable obligatoire dans result : status (done|failed), deliverables[], blockers[], "
            "recommendation (go|no-go|go-with-caveats) pour phase RÉELLE. "
            "Ce compte rendu est poussé Element (matrix_notify)."
        ),
        "context": {
            "lost_heaven_map": True,
            "godot_supervisor": True,
            "godot_mode": "full",
            "team_spawn_phase": "control",
            "team_spawn_run_id": run_id,
            "team_spawn_control": True,
            "dry_task_ids": dry_task_ids,
            "gateway_http": http_gateway,
            "element_report": True,
        },
    }


def state_path() -> Path:
    raw = os.environ.get("LBG_TEAM_SPAWN_STATE", "").strip()
    if raw:
        return Path(raw)
    return Path("/tmp/lbg_spawn_lh_state.json")


def load_run_state() -> dict[str, Any]:
    p = state_path()
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_run_state(payload: dict[str, Any]) -> None:
    p = state_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(p)


def format_phase_report(
    *,
    phase: Phase,
    run_id: str,
    results: list[dict[str, Any]],
) -> str:
    lines = [
        f"📋 Lost Heaven — phase {phase.upper()}",
        PHASE_LABELS.get(phase, phase),
        f"run_id: {run_id}",
        "",
    ]
    for r in results:
        role = r.get("role") or "?"
        track = r.get("track") or ""
        tid = r.get("task_id") or "?"
        err = r.get("error")
        if err:
            lines.append(f"❌ {role}{(' / ' + track) if track else ''} — {err}")
            continue
        ok = r.get("task_ok")
        st = r.get("task_status") or "?"
        if r.get("approval_required") or r.get("skipped_run"):
            lines.append(
                f"🔔 L2 en attente — #{tid} [{role}] — valider dans Element puis run"
            )
            continue
        mark = "✅" if ok else "⚠️"
        lines.append(f"{mark} #{tid} [{role}]{(' / ' + track) if track else ''} — {st}")
    lines.append("")
    lines.append("Pilot : #/team · commandes : pending · task <id> · valider <id>")
    return "\n".join(lines)


def push_element_text(message: str) -> dict[str, Any]:
    """Envoie un message ops (Slack + Element backup). ADR 0021."""
    try:
        from lbg_agents.ops_notify import send_text
    except ImportError:
        root = Path(__file__).resolve().parents[2]
        agents_src = root / "agents" / "src"
        if agents_src.is_dir() and str(agents_src) not in sys.path:
            sys.path.insert(0, str(agents_src))
        try:
            from lbg_agents.ops_notify import send_text
        except ImportError as exc:
            return {"ok": False, "skipped": True, "error": f"import ops_notify: {exc}"}

    return send_text(message, channel="ops")


def run_matrix_notify_watchdog() -> dict[str, Any]:
    p03_root = os.environ.get("LBG_PROJECT_03_ROOT", "/home/sdesh/projects/LBG_Project_03").strip()
    if p03_root not in sys.path:
        sys.path.insert(0, p03_root)
    try:
        from lbg_agents.matrix_notify import run_matrix_notify_watchdog as _run
    except ImportError as exc:
        return {"ok": False, "skipped": True, "error": str(exc)}
    return _run(notify=True, bootstrap_if_new=False)


def notify_element_phase(
    *,
    phase: Phase,
    run_id: str,
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    report = format_phase_report(phase=phase, run_id=run_id, results=results)
    push = push_element_text(report)
    notify = run_matrix_notify_watchdog()
    return {"report_chars": len(report), "push": push, "watchdog": notify}


def new_run_id() -> str:
    return os.environ.get("LBG_TEAM_SPAWN_RUN_ID") or uuid.uuid4().hex[:12]


def spawn_tasks_for_phase(
    *,
    tasks: list[dict[str, Any]],
    phase: Phase,
    actor_id: str,
    http_gateway: str,
    vm: str,
    run_id: str,
    only_filter: set[str] | None,
    root: str,
    auto_run: bool = True,
) -> list[dict[str, Any]]:
    api_json, orchestrator_url, task_run_summary = load_team_job_spawn(root)
    patch = phase_patch(phase, run_id=run_id, http_gateway=http_gateway, vm=vm)

    selected = tasks
    if only_filter:
        selected = [
            t
            for t in tasks
            if t["role"] in only_filter
            or (t.get("context") or {}).get("godot_dev_track", "") in only_filter
        ]

    if phase == "control":
        st = load_run_state()
        dry_ids = [
            str(x.get("task_id"))
            for x in (st.get("phases") or {}).get("dry", {}).get("results") or []
            if x.get("task_id")
        ]
        selected = [control_task(run_id=run_id, http_gateway=http_gateway, dry_task_ids=dry_ids)]

    results: list[dict[str, Any]] = []
    for t in selected:
        role = t["role"]
        track = (t.get("context") or {}).get("godot_dev_track", "")
        ctx = merge_context(t.get("context") or {}, patch)
        ctx["team_spawn_track"] = track
        try:
            summary = create_and_maybe_run_task(
                api_json=api_json,
                orchestrator_url=orchestrator_url,
                task_run_summary=task_run_summary,
                role=role,
                objective=t["objective"],
                actor_id=actor_id,
                context=ctx,
                phase=phase,
                auto_run=auto_run,
            )
            summary["track"] = track
            results.append(summary)
        except Exception as exc:
            results.append({"role": role, "track": track, "error": str(exc), "ok": False, "phase": phase})
    return results


def persist_phase(run_id: str, phase: Phase, results: list[dict[str, Any]]) -> None:
    st = load_run_state()
    if st.get("run_id") != run_id:
        st = {"run_id": run_id, "started_ts": time.time(), "phases": {}}
    phases = st.setdefault("phases", {})
    phases[phase] = {"ts": time.time(), "results": results}
    save_run_state(st)
