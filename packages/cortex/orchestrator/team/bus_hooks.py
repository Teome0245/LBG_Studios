"""Hooks bus inter-agents Team — ADR 0019 Vague 3.

Émet des messages structurés (consult/gap/propose/ack/verify_result)
sans faire du chat LLM le bus d'exécution.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from team import messages as team_messages
from team.plan_schema import VALID_MESSAGE_KINDS

logger = logging.getLogger("agents.team.bus_hooks")

# Personas / agents métier (from_agent / to_agent)
AGENT_THEMIS = "themis"
AGENT_ARGUS = "argus"
AGENT_HEPHAISTOS = "hephaistos"
AGENT_IRIS = "iris"
AGENT_HERMES = "hermes"
AGENT_PYGMALION = "pygmalion"
AGENT_DEDALE = "dedale"
AGENT_LYRA = "lyra"
AGENT_CHOEUR = "choeur"
AGENT_VULCAN = "vulcan"
AGENT_ATLAS = "atlas"

OWNER_TO_AGENT: dict[str, str] = {
    "iris": AGENT_IRIS,
    "hermes": AGENT_HERMES,
    "pygmalion": AGENT_PYGMALION,
    "hephaistos": AGENT_HEPHAISTOS,
    "argus": AGENT_ARGUS,
    "dedale": AGENT_DEDALE,
    "pm": AGENT_THEMIS,
    "themis": AGENT_THEMIS,
    "choeur": AGENT_CHOEUR,
    "vulcan": AGENT_VULCAN,
    "atlas": AGENT_ATLAS,
}

ROLE_TO_AGENT: dict[str, str] = {
    "pm": AGENT_THEMIS,
    "qa": AGENT_ARGUS,
    "ops": AGENT_HEPHAISTOS,
    "dev_godot": AGENT_IRIS,  # affiné via context persona
    "dev_game": AGENT_DEDALE,
    "admin_infra": AGENT_ATLAS,
    "player_ia": AGENT_CHOEUR,
}


def bus_hooks_enabled() -> bool:
    return os.environ.get("LBG_TEAM_BUS_HOOKS", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def agent_for_owner(owner: str) -> str:
    return OWNER_TO_AGENT.get((owner or "").strip().lower(), AGENT_THEMIS)


def agent_for_role(role: str, *, context: dict[str, object] | None = None) -> str:
    ctx = context or {}
    persona = str(ctx.get("godot_dev_persona") or "").lower()
    if persona == "hermes":
        return AGENT_HERMES
    if persona == "iris":
        return AGENT_IRIS
    if ctx.get("infographiste_ia"):
        return AGENT_PYGMALION
    if ctx.get("core3_build"):
        return "vulcan"
    return ROLE_TO_AGENT.get((role or "").strip(), AGENT_THEMIS)


def safe_append(
    *,
    from_agent: str,
    to_agent: str,
    kind: str,
    payload: dict[str, object] | None = None,
    task_id: str = "",
    actor_id: str = "system:team_bus",
) -> dict[str, object] | None:
    if not bus_hooks_enabled():
        return None
    k = (kind or "").strip().lower()
    if k not in VALID_MESSAGE_KINDS:
        logger.warning("bus kind invalide ignoré: %s", kind)
        return None
    try:
        msg = team_messages.append_message(
            from_agent=from_agent,
            to_agent=to_agent,
            kind=k,
            payload=payload or {},
            task_id=task_id,
            actor_id=actor_id,
        )
        return msg.to_dict()
    except Exception as exc:  # noqa: BLE001
        logger.warning("bus append failed: %s", exc)
        return None


def emit_consult_round(*, task_id: str, specialists: list[str], actor_id: str = "system:team_autoconsult") -> int:
    n = 0
    for agent in specialists:
        if safe_append(
            from_agent=AGENT_THEMIS,
            to_agent=agent,
            kind="consult",
            payload={"topic": "autoconsult_round", "ask": "sonde + gaps"},
            task_id=task_id,
            actor_id=actor_id,
        ):
            n += 1
    return n


def emit_gaps(
    *,
    task_id: str,
    gaps: list[dict[str, Any]],
    actor_id: str = "system:team_autoconsult",
    limit: int = 20,
) -> int:
    n = 0
    for item in gaps[:limit]:
        owner = str(item.get("owner") or "pm")
        to_agent = agent_for_owner(owner)
        if safe_append(
            from_agent=to_agent,
            to_agent=AGENT_THEMIS,
            kind="gap",
            payload={
                "owner": owner,
                "track": str(item.get("track") or ""),
                "gap": str(item.get("gap") or "")[:500],
            },
            task_id=task_id,
            actor_id=actor_id,
        ):
            n += 1
    return n


def emit_propose_followup(
    *,
    parent_task_id: str,
    child_task_id: str,
    to_agent: str,
    role: str,
    objective: str,
    from_agent: str = AGENT_THEMIS,
    actor_id: str = "system:team_bus",
) -> dict[str, object] | None:
    return safe_append(
        from_agent=from_agent,
        to_agent=to_agent,
        kind="propose",
        payload={
            "child_task_id": child_task_id,
            "role": role,
            "objective": (objective or "")[:400],
        },
        task_id=parent_task_id,
        actor_id=actor_id,
    )


def emit_ack_spawn(
    *,
    parent_task_id: str,
    child_task_ids: list[str],
    from_agent: str = AGENT_THEMIS,
    actor_id: str = "system:team_bus",
) -> dict[str, object] | None:
    if not child_task_ids:
        return None
    return safe_append(
        from_agent=from_agent,
        to_agent=AGENT_LYRA,
        kind="ack",
        payload={"spawned": list(child_task_ids)[:20], "count": len(child_task_ids)},
        task_id=parent_task_id,
        actor_id=actor_id,
    )


def emit_verify_result(
    *,
    task_id: str,
    from_agent: str,
    ok: bool,
    summary: str,
    actor_id: str = "system:team_bus",
) -> dict[str, object] | None:
    msg = safe_append(
        from_agent=from_agent,
        to_agent=AGENT_THEMIS,
        kind="verify_result",
        payload={"ok": ok, "summary": (summary or "")[:400]},
        task_id=task_id,
        actor_id=actor_id,
    )
    # Learning après verify (Vague 4) — pattern ok/fail
    try:
        from team import memory as team_memory

        if team_memory.memory_enabled():
            team_memory.append_learning(
                agent_id=from_agent or AGENT_THEMIS,
                summary=f"verify {'ok' if ok else 'fail'} — {(summary or '')[:200]}",
                kind="verify_result",
                tags=["verify", "ok" if ok else "fail"],
                task_id=task_id,
                meta={"ok": ok},
            )
    except Exception as exc:  # noqa: BLE001
        logger.debug("verify memory skip: %s", exc)
    return msg


def gaps_by_owner_lines(gaps: list[dict[str, Any]], *, limit: int = 12) -> list[str]:
    by: dict[str, list[str]] = {}
    for item in gaps[:limit]:
        owner = str(item.get("owner") or "pm")
        by.setdefault(owner, []).append(str(item.get("gap") or ""))
    lines: list[str] = []
    for owner, glist in sorted(by.items()):
        agent = agent_for_owner(owner)
        lines.append(f"  · {owner}/{agent}: {glist[0][:160]}" + (f" (+{len(glist)-1})" if len(glist) > 1 else ""))
    return lines


def format_bus_aware_summary(
    *,
    title: str,
    probes: list[dict[str, Any]] | None = None,
    gaps: list[dict[str, Any]] | None = None,
    followup_ids: list[str] | None = None,
    bus_emitted: int = 0,
    memory_lines: list[str] | None = None,
    extra_checklist: list[str] | None = None,
) -> str:
    from team.human_summary import format_validation_summary

    checklist: list[str] = [
        f"{len(gaps or [])} gap(s) détecté(s)",
        f"{len(followup_ids or [])} followup(s) spawné(s)",
        f"{bus_emitted} message(s) bus émis",
    ]
    if gaps:
        checklist.append("Gaps par owner :")
        checklist.extend(gaps_by_owner_lines(gaps))
    if memory_lines:
        checklist.append("Mémoire équipe (top) :")
        checklist.extend(f"  · {m}" for m in memory_lines[:4])
    if extra_checklist:
        checklist.extend(extra_checklist)
    return format_validation_summary(title=title, probes=probes or [], checklist=checklist)


def emit_spawned_followups(
    *,
    parent_task_id: str,
    child_task_ids: list[str],
    from_agent: str,
    actor_id: str = "system:team_bus",
    verify_summary: str | None = None,
    verify_ok: bool = False,
) -> int:
    """Propose + ack (+ verify optionnel) pour une liste de tâches filles."""
    from team import store as team_store

    n = 0
    for cid in child_task_ids:
        child = team_store.get_task(cid)
        if child is None:
            continue
        if emit_propose_followup(
            parent_task_id=parent_task_id,
            child_task_id=child.id,
            to_agent=agent_for_role(child.role, context=child.context),
            role=child.role,
            objective=child.objective,
            from_agent=from_agent,
            actor_id=actor_id,
        ):
            n += 1
    if child_task_ids:
        if emit_ack_spawn(
            parent_task_id=parent_task_id,
            child_task_ids=child_task_ids,
            from_agent=from_agent,
            actor_id=actor_id,
        ):
            n += 1
    if verify_summary is not None:
        if emit_verify_result(
            task_id=parent_task_id,
            from_agent=from_agent,
            ok=verify_ok,
            summary=verify_summary,
            actor_id=actor_id,
        ):
            n += 1
    return n


def maybe_record_round_memory(
    *,
    gaps_count: int,
    ok: bool,
    task_id: str,
) -> None:
    if not bus_hooks_enabled():
        return
    try:
        from team import memory as team_memory

        if not team_memory.memory_enabled():
            return
        summary = (
            f"Autoconsult {'OK' if ok else 'gaps'} — {gaps_count} gap(s)"
            if gaps_count or not ok
            else "Autoconsult vert — aucun gap"
        )
        team_memory.append_learning(
            agent_id=AGENT_THEMIS,
            summary=summary,
            kind="autoconsult_round",
            tags=["autoconsult", "ok" if ok else "gaps"],
            task_id=task_id,
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("memory record skip: %s", exc)
