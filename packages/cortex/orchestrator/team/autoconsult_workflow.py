"""Round autoconsultation — Thémis orchestre les spécialistes (style Fable)."""

from __future__ import annotations

import os
import time
from typing import Any, Callable

from team import bus_hooks
from team import store as team_store
from team.agent_registry import list_agents_summary
from team.infographiste_probe import probe_infographiste_assets
from team.m9_map_probe import audit_m9_full_readiness
from team.m9_remediation import try_m9a_auto_remediate
from team.godot_supervisor import execute_godot_supervisor
from team.models import TeamTask
from team.subprojects import list_subprojects

Dispatcher = Callable[..., dict[str, object]]

_GAMEPLAY_HINTS = (
    "gameplay",
    "bug",
    "quête",
    "quete",
    "combat",
    "npc",
    "forge",
    "opengame",
    "core3",
    "prototype",
)


def autoconsult_enabled() -> bool:
    return os.environ.get("LBG_TEAM_AUTOCONSULT_ENABLED", "1").strip().lower() in ("1", "true", "yes", "on")


def followup_auto_run() -> bool:
    return os.environ.get("LBG_TEAM_AUTOCONSULT_FOLLOWUP_AUTO_RUN", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _qa_probe() -> dict[str, Any]:
    from team import roles as team_roles

    script = os.environ.get("LBG_TEAM_QA_SMOKE_SCRIPT", "").strip()
    if script and os.path.isfile(script):
        return team_roles._run_qa_smoke_script()
    targets = team_roles._qa_health_targets()
    checks = []
    for url in targets[:4]:
        try:
            import httpx

            r = httpx.get(url, timeout=5.0)
            checks.append({"url": url, "ok": r.status_code == 200, "status": r.status_code})
        except Exception as exc:
            checks.append({"url": url, "ok": False, "error": str(exc)})
    ok = all(c.get("ok") for c in checks) if checks else False
    return {"track": "qa_health", "ok": ok, "checks": checks}


def _ops_probe() -> dict[str, Any]:
    """Ops — orch + backend healthz (plus qu'un seul endpoint)."""
    from team import roles as team_roles

    checks: list[dict[str, Any]] = []
    gaps: list[str] = []
    try:
        import httpx
    except ImportError:
        return {"track": "ops_lan", "ok": False, "error": "httpx_missing", "gaps": ["httpx absent"]}

    targets = [
        ("ops_orchestrator", f"{team_roles._orchestrator_url()}/healthz"),
        ("ops_backend", f"{team_roles._backend_url()}/healthz"),
    ]
    for label, url in targets:
        try:
            r = httpx.get(url, timeout=5.0)
            ok = r.status_code == 200
            checks.append({"kind": label, "url": url, "ok": ok, "status": r.status_code})
            if not ok:
                gaps.append(f"{label}: HTTP {r.status_code}")
        except Exception as exc:
            checks.append({"kind": label, "url": url, "ok": False, "error": str(exc)})
            gaps.append(f"{label}: {exc}")
    return {
        "track": "ops_lan",
        "ok": len(gaps) == 0 and bool(checks),
        "checks": checks,
        "gaps": gaps,
    }


def _choeur_probe() -> dict[str, Any]:
    """Chœur — sonde sidecar joueurs IA (:8791)."""
    from team.player_ia_exec import execute_player_ia
    from team.models import TeamTask

    # Via exec : soft-fail humanité / truth-guard si Lia+Nix online.
    fake = TeamTask(
        id="autoconsult-choeur-probe",
        role="player_ia",
        objective="autoconsult choeur probe",
        status="queued",
        actor_id="system:team_autoconsult",
        context={"player_ia_mode": "probe"},
    )
    out = execute_player_ia(fake)
    gaps: list[str] = []
    checks = [c for c in (out.get("checks") or []) if isinstance(c, dict)]
    health_ok = any(c.get("kind") == "sidecar_healthz" and c.get("ok") for c in checks)
    if not out.get("ok"):
        # Ne pas dire « sidecar KO » si healthz répond : souvent bots offline (409).
        default_err = "bots offline (snapshots 409)" if health_ok else "sidecar KO"
        err = out.get("error") or out.get("hint") or default_err
        if str(err) == "sidecar KO" and health_ok:
            err = default_err
        gaps.append(str(err))
        for c in checks:
            if c.get("ok") is False and c.get("kind") not in {"player_humanity", "world_truth_guard", "world_truth_guard_check"}:
                gaps.append(f"{c.get('kind')}: {c.get('error') or c.get('status')}")
    return {
        "track": "choeur_player_ia",
        "ok": bool(out.get("ok")),
        "gaps": gaps[:5],
        "sidecar": out.get("sidecar"),
        "probe": out,
    }


def _prime_ui_probe() -> dict[str, Any]:
    """Prime UI /api/servers (:8792) — readiness jeu (read-only)."""
    base = os.environ.get("LBG_PRIME_UI_URL", "http://192.168.0.246:8792").strip().rstrip("/")
    url = f"{base}/api/servers"
    gaps: list[str] = []
    try:
        import httpx

        r = httpx.get(url, timeout=8.0)
        if r.status_code != 200:
            gaps.append(f"prime_ui HTTP {r.status_code}")
            return {"track": "vulcan_prime_ui", "ok": False, "url": url, "gaps": gaps}
        data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        servers = data if isinstance(data, list) else (data.get("servers") or data.get("items") or [])
        ready = False
        if isinstance(servers, list) and servers:
            for s in servers:
                if isinstance(s, dict) and (s.get("ready") or s.get("status") == "ready"):
                    ready = True
                    break
        elif isinstance(data, dict) and (data.get("ready") or data.get("ok")):
            ready = True
        if not ready and isinstance(servers, list) and not servers:
            gaps.append("prime_ui: aucun serveur listé")
        elif not ready:
            # HTTP 200 sans flag ready explicite = OK soft (surface up)
            ready = True
        return {
            "track": "vulcan_prime_ui",
            "ok": ready and not gaps,
            "url": url,
            "gaps": gaps,
            "servers_n": len(servers) if isinstance(servers, list) else None,
        }
    except Exception as exc:
        return {"track": "vulcan_prime_ui", "ok": False, "url": url, "gaps": [str(exc)], "error": str(exc)}


def _launchpad_probe() -> dict[str, Any]:
    from team.launchpad_probe import probe_launchpad

    return probe_launchpad()


def _iris_probe() -> dict[str, Any]:
    remediation = try_m9a_auto_remediate()
    probe = audit_m9_full_readiness()
    return {"track": "iris_m9", "remediation": remediation, **probe}


def _pygmalion_probe() -> dict[str, Any]:
    fake = TeamTask(
        id="autoconsult",
        role="dev_game",
        objective="autoconsult infographiste",
        context={"infographiste_ia": True},
    )
    return probe_infographiste_assets(fake)


def _hermes_probe() -> dict[str, Any]:
    """Hermès SOE — timeout court pour ne pas bloquer le round autoconsult."""
    import concurrent.futures

    timeout_s = float(os.environ.get("LBG_TEAM_AUTOCONSULT_HERMES_TIMEOUT_S", "45"))

    def _run() -> dict[str, Any]:
        fake = TeamTask(
            id="autoconsult",
            role="dev_godot",
            objective="autoconsult hermes soe gateway",
            context={"godot_mode": "client_live"},
        )
        out = execute_godot_supervisor(fake)
        tracks = out.get("tracks") or []
        gaps: list[str] = []
        for t in tracks:
            if not isinstance(t, dict) or t.get("ok") or t.get("skipped"):
                continue
            label = str(t.get("track") or "hermes")
            detail = t.get("hint") or t.get("error") or "échec sonde"
            gaps.append(f"{label}: {detail}")
        return {"track": "hermes_soe", "ok": bool(out.get("ok")), "gaps": gaps, "probes": tracks}

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            fut = pool.submit(_run)
            return fut.result(timeout=timeout_s)
    except concurrent.futures.TimeoutError:
        return {
            "track": "hermes_soe",
            "ok": False,
            "gaps": [f"timeout sonde Hermès >{timeout_s:.0f}s"],
            "timeout": True,
        }
    except Exception as exc:
        return {"track": "hermes_soe", "ok": False, "gaps": [str(exc)], "error": str(exc)}


def _failed_max_age_s() -> float:
    """Âge max des failed recyclés en gaps Dédale (défaut 24 h). ``0`` = pas de filtre."""
    raw = os.environ.get("LBG_TEAM_AUTOCONSULT_FAILED_MAX_AGE_H", "24").strip()
    try:
        hours = float(raw)
    except ValueError:
        hours = 24.0
    if hours <= 0:
        return 0.0
    return max(1.0, hours) * 3600.0


def _task_age_s(task: TeamTask, *, now: float | None = None) -> float:
    ts = float(task.updated_ts or task.created_ts or 0.0)
    if ts <= 0:
        return 0.0
    return max(0.0, (now if now is not None else time.time()) - ts)


def _dedale_probe() -> dict[str, Any]:
    """Dédale — échecs récents gameplay / forge (hors pipelines Pygmalion/WSL)."""
    recent = team_store.list_tasks(role="dev_game", status="failed", limit=12)
    gaps: list[str] = []
    skipped_stale = 0
    max_age = _failed_max_age_s()
    now = time.time()
    skip_markers = (
        "lora",
        "sprite",
        "infographiste",
        "pygmalion",
        "kohya",
        "wsl",
        "glb godot",
        "pipeline assets",
    )
    for t in recent:
        if max_age > 0 and _task_age_s(t, now=now) > max_age:
            skipped_stale += 1
            continue
        obj = (t.objective or "")[:120]
        blob = f"{obj} {t.context.get('subproject', '')} {t.actor_id or ''}".lower()
        # Les échecs Infographiste/WSL restent chez Pygmalion — ne pas les recycler en gaps Dédale.
        if any(m in blob for m in skip_markers) or t.context.get("lora_pipeline") or t.context.get(
            "sprites_2d_pipeline"
        ) or t.context.get("infographiste_ia"):
            continue
        if t.context.get("subproject") in {"infographiste_ia"}:
            continue
        gaps.append(f"tâche failed {t.id[:8]}: {obj}")
    return {
        "track": "dedale_gameplay",
        "ok": len(gaps) == 0,
        "gaps": gaps[:5],
        "failed_count": len(gaps),
        "skipped_stale": skipped_stale,
        "failed_max_age_h": round(max_age / 3600.0, 2) if max_age > 0 else 0,
    }


def _retag_gameplay_gaps(gaps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Si un gap sonne gameplay, owner = dedale."""
    out: list[dict[str, Any]] = []
    for item in gaps:
        text = f"{item.get('gap', '')} {item.get('track', '')}".lower()
        if any(k in text for k in _GAMEPLAY_HINTS) and item.get("owner") in ("pm", "argus", None):
            tagged = dict(item)
            tagged["owner"] = "dedale"
            out.append(tagged)
        else:
            out.append(item)
    return out


def _collect_gaps(probes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for p in probes:
        track = str(p.get("track") or "unknown")
        owner = (
            "iris"
            if "m9" in track or "iris" in track
            else "hermes"
            if any(
                k in track
                for k in ("hermes", "soe", "sidecar", "mirror", "lbg_ws", "zb0", "gateway", "launchpad")
            )
            else "argus"
            if track.startswith("qa")
            else "hephaistos"
            if track.startswith("ops")
            else "pygmalion"
            if "infograph" in track
            else "choeur"
            if "choeur" in track or "player_ia" in track
            else "vulcan"
            if "vulcan" in track or "prime_ui" in track or "core3" in track
            else "dedale"
            if "dedale" in track or "gameplay" in track
            else "atlas"
            if "admin" in track or "ollama" in track or "llm" in track
            else "pm"
        )
        if p.get("ok"):
            continue
        for g in p.get("gaps") or []:
            gaps.append({"owner": owner, "track": track, "gap": str(g)})
        nested = p.get("probes")
        if isinstance(nested, list):
            for sub in nested:
                if isinstance(sub, dict) and not sub.get("ok"):
                    for g in sub.get("gaps") or []:
                        gaps.append({"owner": owner, "track": sub.get("track", track), "gap": str(g)})
        if not p.get("gaps") and not p.get("ok") and p.get("hint"):
            gaps.append({"owner": owner, "track": track, "gap": str(p["hint"])})
        if not p.get("gaps") and not p.get("ok") and p.get("error"):
            gaps.append({"owner": owner, "track": track, "gap": str(p["error"])})
    return _retag_gameplay_gaps(gaps)


def _spawn_followups(task: TeamTask, gaps: list[dict[str, Any]]) -> list[str]:
    if not gaps or not followup_auto_run():
        return []
    actor = os.environ.get("LBG_TEAM_AUTOCONSULT_FOLLOWUP_ACTOR_ID", "system:team_autoconsult").strip()
    created: list[str] = []
    parent = {"parent_task_id": task.id, "autoconsult_round": True}

    by_owner: dict[str, list[str]] = {}
    for item in gaps[:12]:
        by_owner.setdefault(str(item["owner"]), []).append(str(item["gap"]))

    def _spawn(role: str, objective: str, context: dict[str, object], to_agent: str) -> None:
        t = team_store.create_task(
            role=role,
            objective=objective,
            actor_id=actor,
            context=context,
        )
        created.append(t.id)
        bus_hooks.emit_propose_followup(
            parent_task_id=task.id,
            child_task_id=t.id,
            to_agent=to_agent,
            role=role,
            objective=t.objective,
            actor_id=actor,
        )

    if by_owner.get("iris"):
        _spawn(
            "dev_godot",
            f"Iris — corriger M9 : {by_owner['iris'][0]}",
            {
                **parent,
                "godot_dev_persona": "iris",
                "godot_dev_track": "m9_full",
                "subproject": "godot_iris",
                "iris_forge": True,
            },
            bus_hooks.AGENT_IRIS,
        )
    if by_owner.get("hermes"):
        _spawn(
            "dev_godot",
            f"Hermès — SOE/gateway : {by_owner['hermes'][0]}",
            {
                **parent,
                "godot_dev_persona": "hermes",
                "godot_dev_track": "client_live",
                "subproject": "godot_hermes",
            },
            bus_hooks.AGENT_HERMES,
        )
    if by_owner.get("pygmalion"):
        _spawn(
            "dev_game",
            f"Pygmalion — assets : {by_owner['pygmalion'][0]}",
            {**parent, "infographiste_ia": True, "subproject": "infographiste_ia"},
            bus_hooks.AGENT_PYGMALION,
        )
    if by_owner.get("hephaistos"):
        _spawn(
            "ops",
            f"Héphaïstos — infra : {by_owner['hephaistos'][0]}",
            {**parent, "m9_ops_sync": True, "ops_kind": "m9_prime_sync"},
            bus_hooks.AGENT_HEPHAISTOS,
        )
    if by_owner.get("argus"):
        _spawn(
            "qa",
            f"Argus — re-smoke : {by_owner['argus'][0]}",
            {**parent, "godot_validation": True},
            bus_hooks.AGENT_ARGUS,
        )
    if by_owner.get("dedale"):
        _spawn(
            "dev_game",
            f"Dédale — gameplay : {by_owner['dedale'][0]}",
            {**parent, "subproject": "gameplay", "capability_hint": "prototype_game"},
            bus_hooks.AGENT_DEDALE,
        )
    if by_owner.get("choeur"):
        _spawn(
            "player_ia",
            f"Chœur — sidecar joueurs IA : {by_owner['choeur'][0]}",
            {**parent, "player_ia_mode": "probe"},
            bus_hooks.AGENT_CHOEUR,
        )
    if by_owner.get("vulcan"):
        _spawn(
            "dev_game",
            f"Vulcan — Prime UI / Core3 : {by_owner['vulcan'][0]}",
            {**parent, "dev_game_persona": "vulcan", "prime_ui_probe": True},
            bus_hooks.AGENT_VULCAN,
        )
    if by_owner.get("atlas"):
        _spawn(
            "admin_infra",
            f"Atlas — lab LLM : {by_owner['atlas'][0]}",
            {**parent, "admin_infra": True, "subproject": "local_llm_lab"},
            bus_hooks.AGENT_ATLAS,
        )

    if created:
        bus_hooks.emit_ack_spawn(parent_task_id=task.id, child_task_ids=created, actor_id=actor)

    return created


def execute_autoconsult_workflow(task: TeamTask, dispatch: Dispatcher) -> dict[str, object]:
    if not autoconsult_enabled():
        return {"kind": "autoconsult_workflow", "ok": True, "skipped": True, "reason": "LBG_TEAM_AUTOCONSULT_ENABLED=0"}

    actor = os.environ.get("LBG_TEAM_AUTOCONSULT_FOLLOWUP_ACTOR_ID", "system:team_autoconsult").strip()
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
        _qa_probe(),
        _ops_probe(),
        _iris_probe(),
        _hermes_probe(),
        _launchpad_probe(),
        _pygmalion_probe(),
        _dedale_probe(),
        _choeur_probe(),
        _prime_ui_probe(),
    ]

    gaps = _collect_gaps(probes)
    ok = len(gaps) == 0
    bus_n += bus_hooks.emit_gaps(task_id=task.id, gaps=gaps, actor_id=actor)

    # Synthèse gaps-par-owner (critère phase E)
    gaps_by_owner: dict[str, list[str]] = {}
    for item in gaps:
        gaps_by_owner.setdefault(str(item.get("owner") or "pm"), []).append(str(item.get("gap") or ""))

    brief = dispatch(
        "agent.pm",
        actor_id=task.actor_id,
        text=task.objective or "Round autoconsultation équipe studio",
        context={
            "reunification_brief": True,
            "pm_include_plan": True,
            "pm_include_structure": True,
            "subprojects": list_subprojects(),
            "autoconsult_probes": probes,
            "autoconsult_gaps": gaps[:20],
            "agents_roster": list_agents_summary(),
        },
    )

    followup_ids = _spawn_followups(task, gaps)
    ran_followups: list[dict[str, object]] = []
    if followup_ids and followup_auto_run():
        from team import roles as team_roles

        for fid in followup_ids:
            ft = team_store.get_task(fid)
            if ft and ft.status == "queued":
                result = team_roles.run_task(fid)
                if result:
                    ran_followups.append({"task_id": fid, "role": result.role, "status": result.status})

    followup_auto_rate: float | None
    if not gaps:
        followup_auto_rate = 1.0  # rien à spawn = critère satisfait
    elif followup_ids:
        done_n = sum(1 for r in ran_followups if r.get("status") in ("done", "failed", "blocked"))
        followup_auto_rate = done_n / max(len(followup_ids), 1)
    else:
        followup_auto_rate = 0.0

    memory_lines: list[str] = []
    try:
        from team import memory as team_memory

        if team_memory.memory_enabled():
            for e in team_memory.top_learnings_for_plan(limit=4):
                memory_lines.append(f"{e.get('agent_id')}: {e.get('summary')}")
    except Exception:
        pass

    human_summary = bus_hooks.format_bus_aware_summary(
        title="Thémis — round autoconsultation (Fable)",
        probes=probes,
        gaps=gaps,
        followup_ids=followup_ids,
        bus_emitted=bus_n,
        memory_lines=memory_lines,
        extra_checklist=["Doc docs/vision_equipe_fable_autoconsultation.md", "ADR 0019 Vague 3 bus"],
    )

    bus_hooks.emit_verify_result(
        task_id=task.id,
        from_agent=bus_hooks.AGENT_THEMIS,
        ok=ok,
        summary=f"autoconsult gaps={len(gaps)} followups={len(followup_ids)}",
        actor_id=actor,
    )
    bus_hooks.maybe_record_round_memory(gaps_count=len(gaps), ok=ok, task_id=task.id)

    return {
        "kind": "autoconsult_workflow",
        "ok": ok,
        "probes": probes,
        "gaps": gaps,
        "gaps_count": len(gaps),
        "gaps_by_owner": gaps_by_owner,
        "brief": brief,
        "followup_task_ids": followup_ids,
        "followup_ran": ran_followups,
        "followup_auto_rate": followup_auto_rate,
        "agents_count": len(list_agents_summary()),
        "bus_messages_emitted": bus_n,
        "human_summary": human_summary,
        "timestamp": time.time(),
    }


def resolve_autoconsult_workflow(task: TeamTask) -> bool:
    ctx = task.context
    if ctx.get("autoconsult_round") or ctx.get("autoconsult"):
        return True
    text = (task.objective or "").lower()
    return bool(
        any(k in text for k in ("autoconsult", "autoconsultation", "round fable", "round équipe", "round equipe"))
    )
