"""Phase C1 — Mandat Compagnon → brief hub présence (zone d'entraînement).

« teste présence Nix chaleur haute » → livrable markdown + mission Campus dry-run
bornée (smoke B3/B4), pas d'exécution L2 libre.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any

logger = logging.getLogger("lbg.presence_brief")

# Intent C1 = verbe d'action (teste / brief / smoke) — PAS une causerie design
# qui mentionne seulement « zone d'entraînement » (rejeu T5 → fuite ops).
_PRESENCE_BRIEF_RE = re.compile(
    r"(?i)\b("
    r"teste?\s+(?:la\s+)?pr[ée]sence|"
    r"brief\s+(?:hub\s+)?pr[ée]sence|"
    r"smoke\s+(?:b3|b4|pr[ée]sence)|"
    r"(?:lance|run|fais)\s+(?:un\s+)?(?:brief|smoke)\s+(?:hub\s+)?pr[ée]sence|"
    r"pr[ée]sence\s+(?:de\s+)?(?:nix|lia|mira)\s+(?:chaleur|haute|dials?)|"
    r"chaleur\s+haute|"
    r"dials?\s+(?:nix|pr[ée]sence)"
    r")\b"
)

_PRESENCE_ACTION_RE = re.compile(
    r"(?i)\b("
    r"teste?|brief|smoke|lance|run|fais|valide|mesure|"
    r"dials?|chaleur\s+haute"
    r")\b"
)

_PERSONA_RE = re.compile(
    r"(?i)\b(nix|lia|mira|kael|renn|sola|vulcan|ori|tess|vex)\b"
)


def presence_brief_enabled(*, lab: bool = False) -> bool:
    raw = (os.getenv("LBG_COMPAGNON_PRESENCE_BRIEF") or "").strip().lower()
    if raw in ("0", "false", "no", "off"):
        return False
    if raw in ("1", "true", "yes", "on"):
        return True
    return bool(lab)


def wants_presence_brief(prompt: str) -> bool:
    """True seulement si mandat d'action présence (teste/brief/smoke), pas causerie design."""
    text = (prompt or "").strip()
    if not text or len(text) > 400:
        return False
    if not _PRESENCE_BRIEF_RE.search(text):
        return False
    # Barrière 1.1 : brainstorm design / lore sans verbe d'action → causerie, pas Campus
    try:
        from src.services.chat_intent import is_design_brainstorm
    except ImportError:  # pragma: no cover
        try:
            from chat_intent import is_design_brainstorm  # type: ignore
        except ImportError:
            is_design_brainstorm = None  # type: ignore
    if is_design_brainstorm and is_design_brainstorm(text):
        if not _PRESENCE_ACTION_RE.search(text):
            return False
        # « zone d'entraînement » + design sans teste/brief/smoke explicite → causerie
        if not re.search(
            r"(?i)\b(teste?|brief|smoke|lance|run|fais|valide|mesure)\b",
            text,
        ):
            return False
    return True


def _persona_from_prompt(prompt: str) -> str:
    m = _PERSONA_RE.search(prompt or "")
    return (m.group(1).capitalize() if m else "Nix")


def build_presence_brief_markdown(prompt: str = "") -> str:
    who = _persona_from_prompt(prompt)
    return (
        f"## Objectif\n"
        f"Valider la **zone d'entraînement** Lost Heaven : présence différenciée "
        f"de **{who}** (dials ≠ neutre) sans mutation auto du monde.\n\n"
        f"## Phases\n"
        f"1. **Lecture dials** — `GET http://192.168.0.246:8787/v1/presence-dials` "
        f"(chaleur / initiative de {who}).\n"
        f"2. **Smoke B3/B4** — seuils greet/escort vs ignore "
        f"(`bash tools/smoke_b3b4_presence_hub.sh`).\n"
        f"3. **Observation** — spawn hub : greet + escort si chaleur/initiative "
        f"au-dessus des seuils ; sinon salut seul / silence.\n\n"
        f"## Prochaine action\n"
        f"Lancer le smoke B3/B4 sur `:8787` (dry-run lecture seule) puis noter "
        f"le résultat dans Pilot / ce fil.\n\n"
        f"## Garde-fous\n"
        f"- Pas de LLM libre sur prix / combat.\n"
        f"- Pas d'Agir shell ; mission Campus = brief Team (Hermès) borné.\n"
        f"- Demande humaine : {(prompt or '')[:160]}\n"
    )


def build_mission_objective(prompt: str) -> str:
    who = _persona_from_prompt(prompt)
    return (
        f"Hermès (PM) + Team : brief zone d'entraînement — smoke présence {who} "
        f"(B3/B4 dials). Dry-run / lecture seule hub :8787. "
        f"Demande : {(prompt or '')[:200]}"
    )


async def attach_presence_brief_if_needed(
    result: Any,
    *,
    prompt: str,
    lab: bool = False,
) -> Any:
    """Si intent brief présence → markdown + spawn Campus (réutilise plan_submit)."""
    if not isinstance(result, dict):
        return result
    if not presence_brief_enabled(lab=lab):
        return result
    if not wants_presence_brief(prompt):
        return result
    if result.get("presence_brief") or result.get("campus_meta"):
        return result

    content = build_presence_brief_markdown(prompt)
    out: dict[str, Any] = {
        **result,
        "content": content,
        "response": content,
        "source": "presence_brief",
        "model": "presence_brief",
        "model_used": "presence_brief",
        "presence_brief": {"ok": True, "persona": _persona_from_prompt(prompt)},
    }

    try:
        from src.services.plan_submit import submit_plan_mission
    except ImportError:
        try:
            from plan_submit import submit_plan_mission  # type: ignore
        except ImportError:
            logger.warning("presence_brief: plan_submit unavailable")
            return out

    objective = build_mission_objective(prompt)
    try:
        data = await submit_plan_mission(objective=objective, max_tasks=4)
    except Exception as e:
        logger.warning("presence_brief campus spawn failed: %s", e)
        note = (
            f"\n\n_Brief non persisté côté Team ({e}). "
            "Le markdown reste le livrable — lance le smoke à la main._"
        )
        out["content"] = content + note
        out["response"] = out["content"]
        out["presence_brief"] = {"ok": False, "error": str(e)[:200]}
        return out

    try:
        from src.services.team_proxy import _format_campus_mission
        from src.services.campus_recall import campus_snapshot_from_mission_data

        mission_block = "\n\n" + _format_campus_mission(data, objective)
        snap = campus_snapshot_from_mission_data(data, objective)
    except Exception:
        mission_block = (
            "\n\n**Mission Campus** (brief présence). Suivi : Pilot `#/team/office`."
        )
        snap = {"mission_id": (data.get("mission") or {}).get("id"), "task_ids": []}

    reply = content.rstrip() + mission_block
    out["content"] = reply
    out["response"] = reply
    out["campus_meta"] = snap
    out["presence_brief"] = {
        "ok": data.get("ok", True) is not False,
        "persona": _persona_from_prompt(prompt),
        "mission_id": snap.get("mission_id"),
        "task_ids": list(snap.get("task_ids") or []),
    }
    logger.info(
        "presence_brief ok persona=%s mission=%s",
        out["presence_brief"].get("persona"),
        out["presence_brief"].get("mission_id"),
    )
    return out
