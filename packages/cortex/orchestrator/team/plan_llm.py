"""Plan LLM borné — ADR 0019 Vague 2.

Heuristique = fallback / complément. LLM propose JSON ; validateur code filtre.
Flag : ``LBG_TEAM_PLAN_LLM=1`` (défaut off).
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Callable

from team.models import VALID_ROLES
from team.plan_schema import (
    ALLOWED_PLAN_CONTEXT_KEYS,
    TeamPlanProposal,
    sanitize_plan_proposals,
)
from team.reason_llm import complete_reason, reason_llm_enabled
from team.role_aliases import role_display
from team import store as team_store

logger = logging.getLogger("agents.team.plan_llm")

HeuristicFn = Callable[..., list[dict[str, object]]]

_last_plan_trace: dict[str, Any] = {}


def last_plan_trace() -> dict[str, Any]:
    return dict(_last_plan_trace)


def _record_plan_trace(result: dict[str, Any], *, objective: str) -> None:
    global _last_plan_trace
    _last_plan_trace = {
        "ts": __import__("time").time(),
        "objective_preview": (objective or "")[:160],
        "source": result.get("source"),
        "proposals_count": len(result.get("proposals") or []),
        "meta": {
            k: result.get("meta", {}).get(k)
            for k in ("plan_llm_enabled", "use_llm_requested", "fallback", "merged_count", "heuristic_count")
            if isinstance(result.get("meta"), dict) and k in result["meta"]
        },
        "llm_ok": (result.get("meta") or {}).get("llm", {}).get("ok")
        if isinstance((result.get("meta") or {}).get("llm"), dict)
        else None,
    }


def plan_llm_flag_enabled() -> bool:
    return team_store.plan_llm_enabled()


def _max_proposals() -> int:
    return max(1, min(int(os.environ.get("LBG_TEAM_PLAN_LLM_MAX", "8")), 12))


def _include_memory_default() -> bool:
    return os.environ.get("LBG_TEAM_PLAN_LLM_MEMORY", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def extract_json_object(text: str) -> dict[str, Any] | None:
    """Extrait un objet JSON depuis une réponse LLM (bloc ```json ou brut)."""
    raw = (text or "").strip()
    if not raw:
        return None
    m = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL | re.IGNORECASE)
    if m:
        raw = m.group(1).strip()
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        pass
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        try:
            data = json.loads(raw[start : end + 1])
            return data if isinstance(data, dict) else None
        except json.JSONDecodeError:
            return None
    return None


def _roles_catalog() -> list[dict[str, str]]:
    from team.roles import ROLE_SPECS

    out: list[dict[str, str]] = []
    for role in sorted(VALID_ROLES):
        spec = ROLE_SPECS.get(role, {})
        disp = role_display(role)
        out.append(
            {
                "role": role,
                "alias": str(disp.get("alias") or ""),
                "autonomy": str(spec.get("autonomy") or "L1"),
                "capability": str(spec.get("capability") or ""),
                "default_objective": str(spec.get("default_objective") or ""),
            }
        )
    return out


def _system_prompt() -> str:
    try:
        from team.prompt_overrides import load_override

        ov = load_override("plan_llm")
        if ov:
            return ov
    except Exception:
        pass
    catalog = json.dumps(_roles_catalog(), ensure_ascii=False)
    keys = ", ".join(sorted(ALLOWED_PLAN_CONTEXT_KEYS))
    return (
        "Tu es Thémis (PM) du studio LBG. Tu décomposes un objectif NL en tâches Team.\n"
        "Réponds UNIQUEMENT avec un JSON compact de la forme :\n"
        '{"proposals":[{"role":"qa","objective":"...","priority":"normal",'
        '"autonomy":"L1","approval_required":false,"context":{},"rationale":"..."}]}\n'
        f"Rôles autorisés uniquement : {sorted(VALID_ROLES)}.\n"
        f"Catalogue : {catalog}\n"
        f"Keys context autorisées : {keys}.\n"
        "Règles : max 8 propositions ; autonomie L2 ⇒ approval_required true ; "
        "pas de secrets ; objectifs concrets et actionnables ; "
        "préfère qa pour smokes, ops pour infra, pm pour synthèse, "
        "dev_godot pour Iris/Hermès, admin_infra pour LLM locaux."
    )


def _user_prompt(objective: str, *, memory_snippets: list[dict[str, Any]] | None) -> str:
    parts = [f"Objectif : {objective.strip()}"]
    if memory_snippets:
        parts.append("Learnings récents (mémoire équipe) :")
        parts.append(json.dumps(memory_snippets[:6], ensure_ascii=False))
    try:
        from team import lessons_learned

        lessons = lessons_learned.lessons_slice_for_task(role="pm", objective=objective, limit=4)
        if lessons:
            parts.append("Leçons réflexives (ne pas répéter) :")
            parts.append(json.dumps(lessons, ensure_ascii=False))
    except Exception:
        pass
    parts.append("Propose les tâches JSON.")
    return "\n".join(parts)


def proposal_to_api_dict(p: TeamPlanProposal) -> dict[str, object]:
    from team.roles import ROLE_SPECS

    spec = ROLE_SPECS.get(p.role, {})
    disp = role_display(p.role)
    out: dict[str, object] = {
        "role": p.role,
        "objective": p.objective,
        "priority": p.priority,
        "approval_required": p.approval_required,
        "actor_id": p.actor_id,
        "capability": p.capability or spec.get("capability") or "",
        "autonomy": p.autonomy,
        "context": dict(p.context),
        "rationale": p.rationale,
        "plan_source": "llm",
    }
    for k in ("alias", "title", "label"):
        if k in disp:
            out[k] = disp[k]
    return out


def _norm_key(role: str, objective: str) -> tuple[str, str]:
    obj = re.sub(r"\s+", " ", (objective or "").strip().lower())[:96]
    return (role, obj)


def merge_proposals(
    heuristic: list[dict[str, object]],
    llm: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Union dédupliquée : LLM d'abord, puis heuristique pour rôles/context manquants."""
    merged: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    roles_seen: set[str] = set()

    for src_list, tag in ((llm, "llm"), (heuristic, "heuristic")):
        for raw in src_list:
            role = str(raw.get("role") or "")
            objective = str(raw.get("objective") or "")
            if not role or not objective:
                continue
            key = _norm_key(role, objective)
            if key in seen:
                continue
            # Si même rôle déjà couvert par LLM et entrée heuristique quasi générique, skip
            if tag == "heuristic" and role in roles_seen:
                # garder si context riche (supervisor, tracks…)
                ctx = raw.get("context") if isinstance(raw.get("context"), dict) else {}
                if not ctx:
                    continue
            item = dict(raw)
            item.setdefault("plan_source", tag)
            if tag == "heuristic" and "rationale" not in item:
                item["rationale"] = "heuristique mots-clés"
            merged.append(item)
            seen.add(key)
            roles_seen.add(role)
            if len(merged) >= _max_proposals():
                return merged
    return merged


def call_plan_llm(
    objective: str,
    *,
    actor_id: str = "system:team",
    include_memory: bool | None = None,
    complete_fn: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Appelle le LLM et retourne proposals sanitizées + meta (sans merge)."""
    if not reason_llm_enabled():
        return {"ok": False, "proposals": [], "error": "REASON LLM désactivé", "skipped": True}

    mem: list[dict[str, Any]] = []
    use_mem = _include_memory_default() if include_memory is None else include_memory
    if use_mem:
        try:
            from team import memory as team_memory

            if team_memory.memory_enabled():
                mem = team_memory.top_learnings_for_plan(limit=6)
        except Exception as exc:  # noqa: BLE001
            logger.debug("memory inject skip: %s", exc)

    complete = complete_fn or complete_reason
    profile = os.environ.get("LBG_TEAM_PLAN_LLM_PROFILE", "json").strip() or "json"
    out = complete(
        system=_system_prompt(),
        user=_user_prompt(objective, memory_snippets=mem or None),
        temperature=float(os.environ.get("LBG_TEAM_PLAN_LLM_TEMPERATURE", "0.15")),
        profile=profile,
    )
    if not out.get("ok"):
        return {
            "ok": False,
            "proposals": [],
            "error": str(out.get("error") or "LLM plan failed"),
            "llm_meta": {k: out.get(k) for k in ("model", "tier", "base_url") if k in out},
        }

    parsed = extract_json_object(str(out.get("text") or ""))
    if not parsed:
        return {
            "ok": False,
            "proposals": [],
            "error": "JSON plan introuvable dans la réponse LLM",
            "llm_meta": {"raw_preview": str(out.get("text") or "")[:240]},
        }

    raw_list = parsed.get("proposals")
    validated, errors = sanitize_plan_proposals(raw_list, actor_id=actor_id)
    api = [proposal_to_api_dict(p) for p in validated[: _max_proposals()]]
    return {
        "ok": bool(api),
        "proposals": api,
        "errors": errors,
        "error": None if api else ("aucune proposition valide: " + "; ".join(errors[:5])),
        "llm_meta": {
            "model": out.get("model"),
            "tier": out.get("tier"),
            "memory_injected": len(mem),
            "rejected": len(errors),
        },
    }


def plan_objective(
    objective: str,
    *,
    actor_id: str = "system:team",
    use_llm: bool | None = None,
    include_memory: bool | None = None,
    heuristic_fn: HeuristicFn | None = None,
    complete_fn: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Point d'entrée Vague 2 : heuristique ± LLM → source heuristic|llm|hybrid."""
    from team import roles as team_roles

    heur_fn = heuristic_fn or team_roles.plan_from_objective
    heuristic = list(heur_fn(objective, actor_id=actor_id))
    for h in heuristic:
        h.setdefault("plan_source", "heuristic")
        h.setdefault("rationale", h.get("rationale") or "heuristique mots-clés")

    want_llm = plan_llm_flag_enabled() if use_llm is None else bool(use_llm)
    meta: dict[str, object] = {
        "plan_llm_enabled": plan_llm_flag_enabled(),
        "use_llm_requested": want_llm,
        "heuristic_count": len(heuristic),
    }

    if not want_llm:
        out = {
            "proposals": heuristic,
            "source": "heuristic",
            "meta": meta,
        }
        _record_plan_trace(out, objective=objective)
        return out

    llm_out = call_plan_llm(
        objective,
        actor_id=actor_id,
        include_memory=include_memory,
        complete_fn=complete_fn,
    )
    meta["llm"] = {
        "ok": llm_out.get("ok"),
        "error": llm_out.get("error"),
        "skipped": llm_out.get("skipped"),
        **(llm_out.get("llm_meta") or {}),
    }
    llm_props = list(llm_out.get("proposals") or [])

    if not llm_out.get("ok") or not llm_props:
        meta["fallback"] = "heuristic"
        out = {"proposals": heuristic, "source": "heuristic", "meta": meta}
        _record_plan_trace(out, objective=objective)
        return out

    if not heuristic:
        out = {"proposals": llm_props, "source": "llm", "meta": meta}
        _record_plan_trace(out, objective=objective)
        return out

    merged = merge_proposals(heuristic, llm_props)
    sources = {str(p.get("plan_source") or "") for p in merged}
    if sources == {"llm"}:
        source = "llm"
    elif sources == {"heuristic"}:
        source = "heuristic"
    else:
        source = "hybrid"
    meta["merged_count"] = len(merged)
    out = {"proposals": merged, "source": source, "meta": meta}
    _record_plan_trace(out, objective=objective)
    return out
