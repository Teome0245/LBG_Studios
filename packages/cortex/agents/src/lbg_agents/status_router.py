"""Routeur central — réponses factuelles avant tout LLM dialogue."""

from __future__ import annotations

from typing import Any, Callable

from lbg_agents.godot_status import run_godot_status
from lbg_agents.infographiste_status import run_infographiste_status
from lbg_agents.infra_status import run_infra_status
from lbg_agents.project_status import run_project_status
from lbg_agents.sprites_status import run_sprites_status
from lbg_agents.status_intent import classify_status_intent, is_operational_status_query
from lbg_agents.team_status import run_team_status

_STATUS_HANDLERS: dict[str, Callable[..., dict[str, Any]]] = {
    "infographiste_status": run_infographiste_status,
    "sprites_status": run_sprites_status,
    "godot_status": run_godot_status,
    "team_status": run_team_status,
    "infra_status": run_infra_status,
    "project_status": run_project_status,
}


def resolve_status_intent(text: str, context: dict[str, Any] | None = None) -> tuple[str, float]:
    """Intent explicite dans le contexte ou classification du texte."""
    ctx = context if isinstance(context, dict) else {}
    forced = ctx.get("_factual_status_intent")
    if isinstance(forced, str) and forced.strip() in _STATUS_HANDLERS:
        return forced.strip(), 1.0
    if ctx.get("_force_factual_status") is True:
        intent, conf = classify_status_intent(text)
        if intent != "unknown":
            return intent, conf
        return "project_status", 0.7
    return classify_status_intent(text)


def should_answer_with_factual_status(text: str, context: dict[str, Any] | None = None) -> bool:
    ctx = context if isinstance(context, dict) else {}
    if ctx.get("_skip_factual_status") is True:
        return False
    if ctx.get("_force_factual_status") is True:
        return True
    if isinstance(ctx.get("_factual_status_intent"), str):
        return True
    if is_operational_status_query(text):
        return True
    intent, _ = classify_status_intent(text)
    return intent != "unknown"


def run_factual_status(
    *,
    actor_id: str,
    text: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if not should_answer_with_factual_status(text, context):
        return None
    intent, _conf = resolve_status_intent(text, context)
    handler = _STATUS_HANDLERS.get(intent) or _STATUS_HANDLERS.get("project_status")
    if handler is None:
        return None
    out = handler(actor_id=actor_id, text=text, context=context or {})
    out["status_intent"] = intent
    return out


def try_factual_status_for_dialogue(
    *,
    actor_id: str,
    text: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """
    Réponse au format agent dialogue (invoke) si la question est opérationnelle.
    Évite les hallucinations (JIRA, codes projet fictifs…) sur « Dialoguer » Pilot.
    """
    result = run_factual_status(actor_id=actor_id, text=text, context=context)
    if result is None:
        return None
    reply = result.get("reply") if isinstance(result.get("reply"), str) else ""
    if not reply.strip():
        return None
    intent = str(result.get("status_intent") or result.get("handler") or "factual_status")
    return {
        "ok": True,
        "reply": reply,
        "lines": [ln for ln in reply.splitlines() if ln.strip()],
        "meta": {
            "factual_status": True,
            "status_intent": intent,
            "llm": False,
            "stub": False,
            "source": "deterministic_factual_status",
            "dialogue_profile_resolved": "factual_status",
        },
        "factual_status_payload": {
            "agent": result.get("agent"),
            "status": result.get("status"),
        },
    }
