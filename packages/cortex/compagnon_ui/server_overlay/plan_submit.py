"""D6.5 — Persister un plan Compagnon comme mission Campus (Team / Hermès).

Après un livrable markdown, si l'humain demande de soumettre au studio :
spawn `POST /v1/pilot/team/campus/mission` et annexe le suivi Pilot au message.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any

logger = logging.getLogger("lbg.plan_submit")

# Handoff studio/Team — y compris « plan … pour le studio » / « soumettre ce plan »
_TEAM_SUBMIT_RE = re.compile(
    r"(?i)\b("
    r"soumet(?:s|tre)?(?:[- ]?(?:le|la|l|ce|cette))?.{0,40}(?:au\s+)?studio|"
    r"soumet(?:s|tre)?(?:[- ]?(?:le|la|l|ce|cette))?.{0,40}(?:à|a)\s+(?:la\s+)?team|"
    r"passe(?:r)?\s+(?:au\s+)?studio|"
    r"(?:plan|livrable).{0,80}\bpour\s+le\s+studio\b|"
    r"(?:plan|livrable).{0,40}\bau\s+studio\b|"
    r"pour\s+le\s+studio\b|"
    r"au\s+studio\b|"
    r"enregistre(?:r)?\s+(?:le\s+)?plan|"
    r"persiste(?:r)?\s+(?:le\s+)?plan|"
    r"mission\s+(?:campus|team|herm[eè]s)|"
    r"@herm[eè]s|"
    r"d[ée]l[eè]gue(?:r)?\s+(?:au\s+|à\s+(?:la\s+)?)?(?:studio|team)|"
    r"job\s+team|t[aâ]che\s+team"
    r")"
)

# « soumettre ce plan » sans regénérer — plan déjà dans le fil
_SUBMIT_EXISTING_PLAN_RE = re.compile(
    r"(?i)\b("
    r"soumet(?:s|tre)?(?:[- ]?(?:le|la|l|ce|cette))?\s+plan|"
    r"soumet(?:s|tre)?.{0,30}\bau\s+studio|"
    r"envoie(?:r)?\s+(?:le\s+|ce\s+)?plan|"
    r"passe(?:r)?\s+(?:le\s+|ce\s+)?plan"
    r")\b"
)

_META_ONLY_RE = re.compile(
    r"(?i)^\s*("
    r"je\s+peux\s+structurer|il\s+faut\s+formaliser|"
    r"cela\s+implique|allons[- ]?y\.?\s*je\s+te\s+suis"
    r")"
)

_PLAN_SHAPE_RE = re.compile(
    r"(?i)("
    r"^#{1,3}\s|"
    r"\bobjectif\b|"
    r"\bphases?\b|"
    r"\bprochaine\s+action\b|"
    r"^\s*[-*]\s+.+\n\s*[-*]\s+"
    r")",
    re.MULTILINE,
)


def plan_submit_enabled(*, lab: bool = False) -> bool:
    raw = (os.getenv("LBG_COMPAGNON_PLAN_SUBMIT") or "").strip().lower()
    if raw in ("0", "false", "no", "off"):
        return False
    if raw in ("1", "true", "yes", "on"):
        return True
    # Défaut : on en LAB (présence Compagnon), off hors LAB
    return bool(lab)


def wants_team_plan_submit(prompt: str, short_ctx: list | None = None) -> bool:
    """True si ce tour doit persister le plan côté Team Campus."""
    try:
        from src.services.chat_intent import (
            has_pending_work,
            is_go_ahead,
            wants_deliverable_turn,
            wants_plan_delivery,
        )
    except ImportError:
        try:
            from chat_intent import (  # type: ignore
                has_pending_work,
                is_go_ahead,
                wants_deliverable_turn,
                wants_plan_delivery,
            )
        except ImportError:
            return False

    text = (prompt or "").strip()
    if not text:
        return False

    handoff = bool(_TEAM_SUBMIT_RE.search(text))
    # Plan demandé + destinataire studio/Team → persister (même sans « soumettre »)
    if wants_plan_delivery(text) and handoff:
        return True
    if handoff and (wants_deliverable_turn(text, short_ctx) or has_pending_work(short_ctx)):
        return True

    if is_go_ahead(text) and short_ctx:
        for item in list(short_ctx)[-8:]:
            role = ""
            chunk = ""
            if isinstance(item, dict):
                role = str(item.get("role") or "").lower()
                chunk = str(
                    item.get("content") or item.get("prompt") or item.get("text") or ""
                )
            else:
                chunk = str(item or "")
            if role in ("assistant", "ai", "compagnon"):
                continue
            if _TEAM_SUBMIT_RE.search(chunk) and (
                wants_plan_delivery(chunk) or has_pending_work([item])
            ):
                return True
    return False


def looks_like_plan_content(content: str) -> bool:
    """Évite de spawner une mission sur une réponse méta / short_social."""
    text = (content or "").strip()
    if len(text) < 120:
        return False
    if _META_ONLY_RE.search(text):
        return False
    if _PLAN_SHAPE_RE.search(text):
        return True
    # Liste numérotée d'au moins 3 lignes
    numbered = re.findall(r"(?m)^\s*\d+[.)]\s+\S+", text)
    return len(numbered) >= 3


def extract_plan_from_ctx(short_ctx: list | None = None) -> str:
    """Dernier message assistant plan-shaped (sans bloc Mission Campus éventuel)."""
    if not short_ctx:
        return ""
    for item in reversed(list(short_ctx)[-12:]):
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").lower()
        if role not in ("assistant", "ai", "compagnon"):
            continue
        chunk = str(item.get("content") or item.get("text") or "").strip()
        if not chunk:
            continue
        # Retirer un éventuel bloc mission déjà annexé
        chunk = re.split(r"\n\s*\*\*Mission Campus", chunk, maxsplit=1)[0].strip()
        if looks_like_plan_content(chunk):
            return chunk
    return ""


def wants_submit_existing_plan(prompt: str, short_ctx: list | None = None) -> bool:
    """True → soumettre le plan déjà dans le fil, sans repasser par le LLM."""
    text = (prompt or "").strip()
    if not text or not _SUBMIT_EXISTING_PLAN_RE.search(text):
        return False
    return bool(extract_plan_from_ctx(short_ctx))


def build_mission_objective(prompt: str, plan_content: str) -> str:
    """Objectif Campus : Hermès PM + extrait du plan Compagnon."""
    plan = (plan_content or "").strip()
    # Cap raisonnable pour l'objectif mission (pas un roman)
    excerpt = plan[:1800]
    if len(plan) > 1800:
        excerpt = excerpt.rstrip() + "\n…"
    user_bit = re.sub(r"\s+", " ", (prompt or "").strip())[:220]
    return (
        "Hermès (PM) + Team : exécuter / découper le plan studio livré par le Compagnon. "
        f"Demande humaine : {user_bit}. "
        "Owners typiques : Hermès (ordo), Iris/Chœur (présence MMO / P3), "
        "Argus (smokes). Contre-pouvoir L2 inchangé pour writes sensibles.\n\n"
        f"--- PLAN COMPAGNON ---\n{excerpt}"
    )


async def submit_plan_mission(*, objective: str, max_tasks: int = 6) -> dict[str, Any]:
    """POST campus/mission via team_proxy (même canal que les missions Infra)."""
    from src.http_timeouts import httpx_timeout
    from src.settings import get_settings
    from src.services.team_proxy import _post_campus_mission

    settings = get_settings()
    base = str(settings.cortex_pilot_url or "").rstrip("/")
    if not base:
        raise RuntimeError("CORTEX_PILOT_URL non configuré")
    timeout = httpx_timeout(read=float(settings.cortex_pilot_timeout_s))
    return await _post_campus_mission(
        base,
        timeout,
        objective=objective,
        max_tasks=max(1, min(12, int(max_tasks))),
    )


async def attach_team_plan_if_needed(
    result: Any,
    *,
    prompt: str,
    short_ctx: list | None = None,
    lab: bool = False,
) -> Any:
    """Si intent soumettre + contenu plan → spawn mission et enrichit la réponse."""
    if not isinstance(result, dict):
        return result
    if not plan_submit_enabled(lab=lab):
        return result
    if not wants_team_plan_submit(prompt, short_ctx) and not wants_submit_existing_plan(
        prompt, short_ctx
    ):
        return result

    content = str(result.get("content") or result.get("response") or "").strip()
    if not looks_like_plan_content(content):
        # Reprendre le plan déjà présent dans le fil (ex. « soumets ce plan »)
        reused = extract_plan_from_ctx(short_ctx)
        if reused:
            content = reused
            result = {**result, "content": content, "response": content}
        else:
            logger.info(
                "plan_submit skipped: content not plan-shaped (len=%s)", len(content)
            )
            return result

    # Déjà soumis dans ce tour ?
    if result.get("campus_meta") or result.get("plan_submit"):
        return result

    objective = build_mission_objective(prompt, content)
    try:
        data = await submit_plan_mission(objective=objective, max_tasks=6)
    except Exception as e:
        logger.warning("plan_submit campus mission failed: %s", e)
        note = (
            f"\n\n_Plan non persisté côté Team (Pilot injoignable ou erreur) : {e}. "
            "Le markdown ci-dessus reste le livrable chat — réessaie ou ouvre Pilot `#/team`._"
        )
        result = {**result, "content": content + note, "response": content + note}
        result["plan_submit"] = {"ok": False, "error": str(e)[:200]}
        return result

    try:
        from src.services.team_proxy import _format_campus_mission
        from src.services.campus_recall import campus_snapshot_from_mission_data

        mission_block = "\n\n" + _format_campus_mission(data, objective)
        snap = campus_snapshot_from_mission_data(data, objective)
    except Exception:
        mission_block = (
            "\n\n**Mission Campus** lancée (plan Compagnon). Suivi : Pilot `#/team/office`."
        )
        snap = {"mission_id": (data.get("mission") or {}).get("id"), "task_ids": []}

    reply = content.rstrip() + mission_block
    out = {
        **result,
        "content": reply,
        "response": reply,
        "campus_meta": snap,
        "plan_submit": {
            "ok": data.get("ok", True) is not False,
            "mission_id": snap.get("mission_id"),
            "task_ids": list(snap.get("task_ids") or []),
        },
    }

    # Cartes L2 si tâches en attente d'approbation
    try:
        from src.services.team_actions import (
            approval_payload_from_tasks,
            fetch_tasks_by_ids,
        )

        task_ids = list(snap.get("task_ids") or [])
        details = await fetch_tasks_by_ids(task_ids) if task_ids else []
        approval = approval_payload_from_tasks(details)
        if approval:
            out["approval"] = approval
            out["content"] = (
                reply.rstrip()
                + "\n\n**Validation L2 requise** — cartes ci-dessous ou Pilot `#/team/office`."
            )
            out["response"] = out["content"]
    except Exception:
        logger.debug("plan_submit approval attach skipped", exc_info=True)

    logger.info(
        "plan_submit ok mission_id=%s tasks=%s",
        out.get("plan_submit", {}).get("mission_id"),
        len(out.get("plan_submit", {}).get("task_ids") or []),
    )
    return out
