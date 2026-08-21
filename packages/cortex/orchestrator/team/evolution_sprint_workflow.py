"""Sprint d'évolution 7j — audit full, plan, L1 auto, L2 file Pilot.

Complète l'autoconsult (santé 12 h) : ici on cherche aussi des opportunités
d'optimisation (capacités, LLM, modules, charge Team) et on les applique
selon le niveau d'autonomie.
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any, Callable

from team import autoconsult_workflow as autoconsult
from team import bus_hooks
from team import store as team_store
from team.agent_registry import list_agents_summary
from team.models import TeamTask
from team.reason_llm import reason_route_matrix
from team.subprojects import list_subprojects

Dispatcher = Callable[..., dict[str, object]]

_L2_RE = re.compile(
    r"\b(restart|reboot|deploy|compiler|build réel|think.?tick|systemd_restart|"
    r"appliquer.?patch|write.?prod|changer.?mod[eè]le)\b",
    re.I,
)
_FORBIDDEN_MODELS = ("gemma3:4b",)

_last_sprint: dict[str, Any] = {}


def evolution_sprint_enabled() -> bool:
    return os.environ.get("LBG_TEAM_EVOLUTION_ENABLED", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def l1_auto_run() -> bool:
    return os.environ.get("LBG_TEAM_EVOLUTION_L1_AUTO_RUN", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def platform_audit_enabled() -> bool:
    return os.environ.get("LBG_TEAM_EVOLUTION_PLATFORM_AUDIT", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def sprint_persist_path() -> str:
    raw = os.environ.get("LBG_TEAM_EVOLUTION_SPRINT_PATH", "").strip()
    if raw:
        return raw
    db = os.environ.get("LBG_TEAM_DB_PATH", "/var/lib/lbg-ia-mmo/team_tasks.db").strip()
    if db and db != ":memory:":
        return str(Path(db).with_name("evolution_sprint.json"))
    return "/var/lib/lbg/team_evolution/last_sprint.json"


def last_sprint() -> dict[str, Any]:
    if _last_sprint:
        return dict(_last_sprint)
    path = Path(sprint_persist_path())
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (OSError, json.JSONDecodeError):
        pass
    return {}


def persist_sprint(report: dict[str, Any]) -> None:
    global _last_sprint
    compact = {
        "ts": report.get("timestamp") or time.time(),
        "task_id": report.get("task_id"),
        "ok": report.get("ok"),
        "gaps_count": report.get("gaps_count"),
        "opportunities_count": report.get("opportunities_count"),
        "opportunities": (report.get("opportunities") or [])[:12],
        "l1_task_ids": report.get("l1_task_ids") or [],
        "l2_task_ids": report.get("l2_task_ids") or [],
        "meta_task_ids": report.get("meta_task_ids") or [],
        "l1_auto_rate": report.get("l1_auto_rate"),
        "human_summary": report.get("human_summary"),
    }
    _last_sprint = dict(compact)
    path = Path(sprint_persist_path())
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(compact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp.replace(path)
    except OSError:
        pass


def resolve_evolution_sprint_workflow(task: TeamTask) -> bool:
    ctx = task.context or {}
    if ctx.get("evolution_sprint") or ctx.get("evolution_round"):
        return True
    text = (task.objective or "").lower()
    keys = (
        "evolution_sprint",
        "sprint évolution",
        "sprint evolution",
        "audit évolution",
        "audit evolution",
        "amélioration continue",
        "amelioration continue",
        "évolution continue",
        "evolution continue",
        "sprint d'évolution",
        "sprint d evolution",
    )
    return any(k in text for k in keys)


def _platform_probe() -> dict[str, Any]:
    if not platform_audit_enabled():
        return {"track": "atlas_platform", "ok": True, "skipped": True, "gaps": []}
    import concurrent.futures

    timeout_s = float(os.environ.get("LBG_TEAM_EVOLUTION_PLATFORM_TIMEOUT_S", "90"))

    def _run() -> dict[str, Any]:
        from team.admin_infra_platform import audit_admin_infra_platform

        out = audit_admin_infra_platform()
        gaps = [str(g) for g in (out.get("gaps") or [])][:12]
        recs = [str(r) for r in (out.get("recommendations") or [])][:8]
        return {
            "track": "atlas_platform",
            "ok": bool(out.get("ok")),
            "gaps": gaps,
            "recommendations": recs,
            "hosts_ok": out.get("hosts_ok"),
            "hosts_total": out.get("hosts_total"),
            "probe": {"ok": out.get("ok"), "hosts_ok": out.get("hosts_ok")},
        }

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(_run).result(timeout=timeout_s)
    except concurrent.futures.TimeoutError:
        return {
            "track": "atlas_platform",
            "ok": False,
            "gaps": [f"timeout audit plateforme >{timeout_s:.0f}s"],
            "timeout": True,
        }
    except Exception as exc:  # noqa: BLE001
        return {"track": "atlas_platform", "ok": False, "gaps": [str(exc)], "error": str(exc)}


def _llm_matrix_probe() -> dict[str, Any]:
    matrix = reason_route_matrix()
    rows: list[dict[str, str]] = []
    gaps: list[str] = []
    opportunities: list[str] = []
    for profile, spec in matrix.items():
        env_key = str(spec.get("env") or "")
        default = str(spec.get("default") or "")
        actual = os.environ.get(env_key, "").strip() if env_key else ""
        effective = actual or default
        rows.append(
            {
                "profile": profile,
                "env": env_key,
                "default": default,
                "actual": actual or "(défaut)",
                "effective": effective,
                "host_class": str(spec.get("host_class") or ""),
            }
        )
        low = effective.lower()
        if any(bad in low for bad in _FORBIDDEN_MODELS):
            gaps.append(f"{profile}: modèle interdit {effective}")
        if actual and actual != default:
            opportunities.append(f"{profile}: env {env_key}={actual} (défaut {default})")
    return {
        "track": "atlas_llm_matrix",
        "ok": len(gaps) == 0,
        "gaps": gaps,
        "opportunities": opportunities,
        "profiles": rows,
    }


def _capabilities_probe() -> dict[str, Any]:
    agents = list_agents_summary()
    missing_timer: list[str] = []
    cap_count = 0
    for a in agents:
        caps = a.get("capabilities") or []
        cap_count += len(caps) if isinstance(caps, list) else 0
        if not a.get("owner_timer"):
            missing_timer.append(str(a.get("agent_id") or a.get("persona") or "?"))
    opportunities = [f"sans timer: {aid}" for aid in missing_timer[:6]]
    return {
        "track": "team_capabilities",
        "ok": True,
        "gaps": [],
        "opportunities": opportunities,
        "agents_count": len(agents),
        "capabilities_count": cap_count,
        "missing_timer": missing_timer,
    }


def _modules_probe() -> dict[str, Any]:
    try:
        from lbg_sa.module_registry import list_modules

        planned = list_modules(status="planned")
        active = list_modules(status="active")
    except Exception as exc:  # noqa: BLE001
        return {"track": "lbg_sa_modules", "ok": False, "gaps": [str(exc)]}
    names = [m.id for m in planned]
    opportunities = [f"module planned: {m.id} ({m.label})" for m in planned[:8]]
    return {
        "track": "lbg_sa_modules",
        "ok": True,
        "gaps": [],
        "opportunities": opportunities,
        "planned": names,
        "active_count": len(active),
        "planned_count": len(planned),
    }


def _team_load_probe() -> dict[str, Any]:
    failed = team_store.list_tasks(status="failed", limit=30)
    review = team_store.list_tasks(status="review", limit=20)
    cutoff = time.time() - 7 * 86400
    recent_failed = [t for t in failed if float(t.updated_ts or 0) >= cutoff]
    by_role: dict[str, int] = {}
    for t in recent_failed:
        by_role[t.role] = by_role.get(t.role, 0) + 1
    gaps: list[str] = []
    for role, n in sorted(by_role.items(), key=lambda kv: -kv[1]):
        if n >= 2:
            gaps.append(f"{role}: {n} tâches failed (7j)")
    opportunities: list[str] = []
    if review:
        opportunities.append(f"{len(review)} tâche(s) L2 en review — file Pilot")
    return {
        "track": "team_load",
        "ok": len(gaps) == 0,
        "gaps": gaps,
        "opportunities": opportunities,
        "failed_7d": len(recent_failed),
        "review_n": len(review),
        "failed_by_role": by_role,
    }


def _subprojects_probe() -> dict[str, Any]:
    subs = list_subprojects()
    frozen = [
        str(s.get("id") or "")
        for s in subs
        if str(s.get("status") or "").lower() in ("etagere", "gelé", "gele", "frozen")
    ]
    return {
        "track": "studio_subprojects",
        "ok": True,
        "gaps": [],
        "opportunities": [f"sous-projet gelé/étagère: {i}" for i in frozen[:6] if i],
        "count": len(subs),
        "frozen": frozen,
    }


def _autonomy_for_text(text: str) -> str:
    return "L2" if _L2_RE.search(text or "") else "L1"


def _owner_role_context(owner: str) -> tuple[str, dict[str, object]]:
    mapping: dict[str, tuple[str, dict[str, object]]] = {
        "iris": ("dev_godot", {"godot_dev_persona": "iris", "godot_dev_track": "m9_full", "subproject": "godot_iris"}),
        "hermes": (
            "dev_godot",
            {"godot_dev_persona": "hermes", "godot_dev_track": "client_live", "subproject": "godot_hermes"},
        ),
        "pygmalion": ("dev_game", {"infographiste_ia": True, "subproject": "infographiste_ia"}),
        "hephaistos": ("ops", {"ops_kind": "m9_prime_sync", "m9_ops_sync": True}),
        "argus": ("qa", {"godot_validation": True}),
        "dedale": ("dev_game", {"subproject": "gameplay", "capability_hint": "prototype_game"}),
        "choeur": ("player_ia", {"player_ia_mode": "probe"}),
        "vulcan": ("dev_game", {"dev_game_persona": "vulcan", "prime_ui_probe": True}),
        "atlas": ("admin_infra", {"admin_infra": True, "subproject": "local_llm_lab"}),
        "pm": ("pm", {"reunification_brief": True}),
        "themis": ("pm", {"reunification_brief": True}),
    }
    return mapping.get(owner, ("pm", {"reunification_brief": True}))


def _retag_evolution_gaps(gaps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in gaps:
        tagged = dict(item)
        track = str(tagged.get("track") or "").lower()
        if "atlas" in track or "llm" in track or "platform" in track or "ollama" in track:
            tagged["owner"] = "atlas"
        elif track == "team_load":
            tagged["owner"] = "argus"
        out.append(tagged)
    return out


def _collect_opportunities(probes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for p in probes:
        track = str(p.get("track") or "unknown")
        owner = (
            "atlas"
            if any(k in track for k in ("atlas", "llm", "admin", "ollama", "platform"))
            else "pm"
            if "module" in track or "subproject" in track or "capabilities" in track
            else "hephaistos"
            if "ops" in track
            else "argus"
            if track.startswith("qa")
            else "pm"
        )
        if "team_load" in track:
            owner = "argus"
        for rec in p.get("recommendations") or []:
            text = str(rec)
            out.append(
                {
                    "kind": "opportunity",
                    "owner": owner,
                    "track": track,
                    "summary": text,
                    "autonomy": _autonomy_for_text(text),
                    "gap": text,
                }
            )
        for opp in p.get("opportunities") or []:
            text = str(opp)
            low = text.lower()
            report_only = any(
                k in low
                for k in (
                    "review",
                    "planned",
                    "sans timer",
                    "gelé",
                    "gele",
                    "étagère",
                    "etagere",
                    "frozen",
                    "env ",
                    "sous-projet",
                )
            )
            out.append(
                {
                    "kind": "opportunity",
                    "owner": owner,
                    "track": track,
                    "summary": text,
                    "autonomy": _autonomy_for_text(text),
                    "gap": text,
                    "spawn": (not report_only) and _autonomy_for_text(text) == "L1",
                }
            )
        if any(bad in str(p.get("gaps") or "").lower() for bad in _FORBIDDEN_MODELS):
            for g in p.get("gaps") or []:
                if any(bad in str(g).lower() for bad in _FORBIDDEN_MODELS):
                    out.append(
                        {
                            "kind": "opportunity",
                            "owner": "atlas",
                            "track": track,
                            "summary": str(g),
                            "autonomy": "L2",
                            "gap": str(g),
                            "spawn": True,
                        }
                    )
    return out


def _spawn_finding(
    *,
    task: TeamTask,
    actor: str,
    owner: str,
    objective: str,
    autonomy: str,
    extra_context: dict[str, object] | None = None,
) -> str | None:
    role, ctx = _owner_role_context(owner)
    context: dict[str, object] = {
        "parent_task_id": task.id,
        "evolution_sprint": True,
        **ctx,
        **(extra_context or {}),
    }
    need_l2 = autonomy == "L2"
    t = team_store.create_task(
        role=role,
        objective=objective[:800],
        actor_id=actor,
        priority="high" if need_l2 else "normal",
        approval_required=need_l2,
        context=context,
    )
    to_agent = bus_hooks.agent_for_owner(owner)
    bus_hooks.emit_propose_followup(
        parent_task_id=task.id,
        child_task_id=t.id,
        to_agent=to_agent,
        role=role,
        objective=t.objective,
        actor_id=actor,
    )
    return t.id


def meta_evolution_enabled() -> bool:
    return os.environ.get("LBG_TEAM_EVOLUTION_META", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _spawn_meta_evolution_tasks(task: TeamTask) -> tuple[list[str], list[str]]:
    """Spawn mutator + feature proposer (L1) ; leurs propres L2 review restent séparés."""
    if not meta_evolution_enabled():
        return [], []
    actor = os.environ.get("LBG_TEAM_EVOLUTION_FOLLOWUP_ACTOR_ID", "system:team_evolution").strip()
    l1: list[str] = []
    l2: list[str] = []
    try:
        mut = team_store.create_task(
            role="qa",
            objective="Évolution méta — forge mutation prompt outcome_judge (golden + candidat L2)",
            actor_id=actor,
            priority="normal",
            approval_required=False,
            context={
                "parent_task_id": task.id,
                "evolution_sprint": True,
                "agent_mutation": True,
                "workflow": "agent_mutator",
                "mutation_target": "outcome_judge",
                "spawn_l2": True,
            },
        )
        l1.append(mut.id)
    except Exception:
        pass
    try:
        prop = team_store.create_task(
            role="pm",
            objective="Évolution méta — Feature Proposer (RFC + auto-evolution + revue L2)",
            actor_id=actor,
            priority="normal",
            approval_required=False,
            context={
                "parent_task_id": task.id,
                "evolution_sprint": True,
                "feature_proposal": True,
                "workflow": "feature_proposer",
                "spawn_l2": True,
                "create_branch": True,
                "dry_run_git": True,  # safe default in sprint ; override via env later
            },
        )
        l1.append(prop.id)
    except Exception:
        pass
    if l1:
        bus_hooks.emit_ack_spawn(
            parent_task_id=task.id,
            child_task_ids=l1,
            actor_id=actor,
        )
    return l1, l2


def _spawn_actions(
    task: TeamTask,
    gaps: list[dict[str, Any]],
    opportunities: list[dict[str, Any]],
) -> tuple[list[str], list[str]]:
    actor = os.environ.get("LBG_TEAM_EVOLUTION_FOLLOWUP_ACTOR_ID", "system:team_evolution").strip()
    l1_ids: list[str] = []
    l2_ids: list[str] = []
    seen_owners_l1: set[str] = set()
    seen_owners_l2: set[str] = set()

    for item in gaps[:12]:
        owner = str(item.get("owner") or "pm")
        if owner in seen_owners_l1:
            continue
        seen_owners_l1.add(owner)
        label = str(item.get("gap") or "gap")
        tid = _spawn_finding(
            task=task,
            actor=actor,
            owner=owner,
            objective=f"Évolution L1 — {owner}: {label}",
            autonomy="L1",
        )
        if tid:
            l1_ids.append(tid)

    for item in opportunities[:12]:
        if item.get("spawn") is False:
            continue
        owner = str(item.get("owner") or "pm")
        autonomy = str(item.get("autonomy") or "L1")
        if autonomy == "L2":
            if owner in seen_owners_l2 or len(l2_ids) >= 4:
                continue
            seen_owners_l2.add(owner)
            label = str(item.get("summary") or item.get("gap") or "opportunité")
            tid = _spawn_finding(
                task=task,
                actor=actor,
                owner=owner,
                objective=f"Évolution L2 — {owner}: {label}",
                autonomy="L2",
            )
            if tid:
                l2_ids.append(tid)
            continue
        if owner in seen_owners_l1 or len(l1_ids) >= 8:
            continue
        seen_owners_l1.add(owner)
        label = str(item.get("summary") or item.get("gap") or "opportunité")
        tid = _spawn_finding(
            task=task,
            actor=actor,
            owner=owner,
            objective=f"Évolution L1 — {owner}: {label}",
            autonomy="L1",
        )
        if tid:
            l1_ids.append(tid)

    if l1_ids or l2_ids:
        bus_hooks.emit_ack_spawn(
            parent_task_id=task.id,
            child_task_ids=l1_ids + l2_ids,
            actor_id=actor,
        )
    return l1_ids, l2_ids


def execute_evolution_sprint_workflow(task: TeamTask, dispatch: Dispatcher) -> dict[str, object]:
    if not evolution_sprint_enabled():
        return {
            "kind": "evolution_sprint_workflow",
            "ok": True,
            "skipped": True,
            "reason": "LBG_TEAM_EVOLUTION_ENABLED=0",
        }

    actor = os.environ.get("LBG_TEAM_EVOLUTION_FOLLOWUP_ACTOR_ID", "system:team_evolution").strip()
    specialists = [
        bus_hooks.AGENT_ARGUS,
        bus_hooks.AGENT_HEPHAISTOS,
        bus_hooks.AGENT_IRIS,
        bus_hooks.AGENT_HERMES,
        bus_hooks.AGENT_PYGMALION,
        bus_hooks.AGENT_DEDALE,
        bus_hooks.AGENT_CHOEUR,
        bus_hooks.AGENT_VULCAN,
        bus_hooks.AGENT_ATLAS,
    ]
    bus_n = bus_hooks.emit_consult_round(task_id=task.id, specialists=specialists, actor_id=actor)

    probes: list[dict[str, Any]] = [
        autoconsult._qa_probe(),
        autoconsult._ops_probe(),
        autoconsult._iris_probe(),
        autoconsult._hermes_probe(),
        autoconsult._launchpad_probe(),
        autoconsult._pygmalion_probe(),
        autoconsult._dedale_probe(),
        autoconsult._choeur_probe(),
        autoconsult._prime_ui_probe(),
        _platform_probe(),
        _llm_matrix_probe(),
        _capabilities_probe(),
        _modules_probe(),
        _team_load_probe(),
        _subprojects_probe(),
    ]

    gaps = _retag_evolution_gaps(autoconsult._collect_gaps(probes))
    opportunities = _collect_opportunities(probes)
    bus_n += bus_hooks.emit_gaps(task_id=task.id, gaps=gaps, actor_id=actor)

    gaps_by_owner: dict[str, list[str]] = {}
    for item in gaps:
        gaps_by_owner.setdefault(str(item.get("owner") or "pm"), []).append(str(item.get("gap") or ""))

    brief = dispatch(
        "agent.pm",
        actor_id=task.actor_id,
        text=task.objective or "Sprint évolution 7j — audit full + plan d'amélioration",
        context={
            "reunification_brief": True,
            "pm_include_plan": True,
            "pm_include_structure": True,
            "evolution_sprint": True,
            "subprojects": list_subprojects(),
            "evolution_probes": [
                {k: p[k] for k in ("track", "ok", "gaps", "opportunities") if k in p} for p in probes
            ],
            "evolution_gaps": gaps[:20],
            "evolution_opportunities": opportunities[:20],
            "agents_roster": list_agents_summary(),
        },
    )

    gap_l1_ids, l2_ids = _spawn_actions(task, gaps, opportunities)
    meta_ids, _meta_l2 = _spawn_meta_evolution_tasks(task)
    l1_ids = list(gap_l1_ids) + list(meta_ids)
    ran_l1: list[dict[str, object]] = []
    if l1_ids and l1_auto_run():
        from team import roles as team_roles

        for fid in l1_ids:
            ft = team_store.get_task(fid)
            if ft and ft.status == "queued" and not ft.approval_required:
                result = team_roles.run_task(fid)
                if result:
                    ran_l1.append({"task_id": fid, "role": result.role, "status": result.status})
                    # Collecter L2 enfants spawnés par mutator/proposer
                    res = result.result if isinstance(result.result, dict) else {}
                    child_l2 = res.get("l2_task_id")
                    if child_l2 and child_l2 not in l2_ids:
                        l2_ids.append(str(child_l2))

    if l1_auto_run():
        if not l1_ids:
            l1_auto_rate = 1.0 if not gaps else 0.0
        else:
            done_n = sum(1 for r in ran_l1 if r.get("status") in ("done", "failed", "blocked"))
            l1_auto_rate = done_n / max(len(l1_ids), 1)
    elif not gap_l1_ids:
        # Méta spawnée mais auto-run off : ne pas pénaliser un sprint sans gaps
        l1_auto_rate = 1.0 if not gaps else 0.0
    else:
        l1_auto_rate = 0.0

    memory_lines: list[str] = []
    try:
        from team import memory as team_memory

        if team_memory.memory_enabled():
            for e in team_memory.top_learnings_for_plan(limit=4):
                memory_lines.append(f"{e.get('agent_id')}: {e.get('summary')}")
    except Exception:
        pass

    ok = len(gaps) == 0
    human_summary = bus_hooks.format_bus_aware_summary(
        title="Thémis — sprint évolution 7j",
        probes=probes,
        gaps=gaps,
        followup_ids=l1_ids + l2_ids,
        bus_emitted=bus_n,
        memory_lines=memory_lines,
        extra_checklist=[
            f"L1 appliqués auto: {len(ran_l1)}/{len(l1_ids)}",
            f"L2 en file Pilot: {len(l2_ids)}",
            f"Méta (mutator/proposer): {len(meta_ids)}",
            f"Opportunités: {len(opportunities)}",
            "Doc docs/team_evolution_sprint.md",
        ],
    )

    bus_hooks.emit_verify_result(
        task_id=task.id,
        from_agent=bus_hooks.AGENT_THEMIS,
        ok=ok,
        summary=f"evolution gaps={len(gaps)} l1={len(l1_ids)} l2={len(l2_ids)}",
        actor_id=actor,
    )
    try:
        from team import memory as team_memory

        if bus_hooks.bus_hooks_enabled() and team_memory.memory_enabled():
            team_memory.append_learning(
                agent_id=bus_hooks.AGENT_THEMIS,
                summary=(
                    f"Sprint évolution {'OK' if ok else 'gaps'} — "
                    f"{len(gaps)} gap(s), {len(opportunities)} opp., L1={len(l1_ids)} L2={len(l2_ids)}"
                ),
                kind="evolution_sprint",
                tags=["evolution", "ok" if ok else "gaps"],
                task_id=task.id,
            )
    except Exception:
        pass

    result: dict[str, object] = {
        "kind": "evolution_sprint_workflow",
        "ok": ok,
        "task_id": task.id,
        "probes": probes,
        "gaps": gaps,
        "gaps_count": len(gaps),
        "gaps_by_owner": gaps_by_owner,
        "opportunities": opportunities,
        "opportunities_count": len(opportunities),
        "brief": brief,
        "l1_task_ids": l1_ids,
        "l2_task_ids": l2_ids,
        "meta_task_ids": meta_ids,
        "followup_task_ids": l1_ids + l2_ids,
        "l1_ran": ran_l1,
        "l1_auto_rate": l1_auto_rate,
        "agents_count": len(list_agents_summary()),
        "bus_messages_emitted": bus_n,
        "human_summary": human_summary,
        "timestamp": time.time(),
    }
    persist_sprint(result)
    return result
