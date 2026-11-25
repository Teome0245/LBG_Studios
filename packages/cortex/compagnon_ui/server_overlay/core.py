"""
Routes racine historiquement inline dans `app/factory.py` : /history, /models, /ask, /brain.
"""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from src.deps import get_brain_controller, get_router_ia
from src.schemas.orchestration import (
    AskJSONEnvelope,
    AskRequest,
    BrainJSONEnvelope,
    BrainRequest,
    ensure_dispatch_dict,
)
from src.services.brain_controller import BrainController
from src.services.history import get_history
from src.services.model_checker import list_models
from src.services.router import RouterIA
from src.services.sse_ask import stream_ask

router = APIRouter(tags=["Core"])

_STREAM_HEADERS = {
    "Cache-Control": "no-cache, no-transform",
    "Connection": "keep-alive",
    # nginx : pas de buffering sur le SSE (le flux part octet par octet)
    "X-Accel-Buffering": "no",
}


@router.get("/history")
async def history(limit: int = 20):
    return await get_history(limit)


@router.get("/chat/conversations")
async def chat_conversations(
    limit: int = 40,
    include_archived: bool = True,
    llm_router: RouterIA = Depends(get_router_ia),
):
    from src.services.conversation_memory import list_conversations_for_ui

    return await list_conversations_for_ui(
        llm_router, limit=limit, include_archived=include_archived
    )


@router.post("/chat/conversations/{conversation_id}/archive")
async def chat_archive(
    conversation_id: str,
    llm_router: RouterIA = Depends(get_router_ia),
):
    from src.services.conversation_memory import archive_conversation_for_ui

    return await archive_conversation_for_ui(llm_router, conversation_id, archived=True)


@router.post("/chat/conversations/{conversation_id}/unarchive")
async def chat_unarchive(
    conversation_id: str,
    llm_router: RouterIA = Depends(get_router_ia),
):
    from src.services.conversation_memory import archive_conversation_for_ui

    return await archive_conversation_for_ui(llm_router, conversation_id, archived=False)


@router.delete("/chat/conversations/{conversation_id}")
async def chat_delete(
    conversation_id: str,
    llm_router: RouterIA = Depends(get_router_ia),
):
    from src.services.conversation_memory import delete_conversation_for_ui

    return await delete_conversation_for_ui(llm_router, conversation_id)


@router.get("/chat/context/{conversation_id}")
async def chat_context(conversation_id: str, llm_router: RouterIA = Depends(get_router_ia)):
    from src.services.conversation_memory import load_conversation_for_ui

    return await load_conversation_for_ui(llm_router, conversation_id)


@router.get("/models")
async def get_models(llm_router: RouterIA = Depends(get_router_ia)):
    return {
        "fast": llm_router.model_fast,
        "balanced": llm_router.model_balanced,
        "smart": llm_router.model_smart,
    }


@router.get("/models/{provider}")
async def get_models_dynamic(provider: str):
    return await list_models(provider)


def _resolve_ask_args(body: AskRequest) -> tuple[str, str | None, str | None, str]:
    """(prompt, agent, model, mode) — raccourcis UI Agent + tier modèle (mutualisé /ask et /ask/stream)."""
    from src.services.team_routing import has_team_mention, strip_team_prefix

    try:
        from src.services.chat_intent import is_companion_chat
    except ImportError:  # pragma: no cover
        def is_companion_chat(_p: str) -> bool:  # type: ignore
            return False

    prompt = body.prompt or ""
    agent = (body.agent or "").strip() or None
    model = (body.model or "").strip() or None

    # Raccourcis UI Agent (sans boutons preset) — préfixes déterministes
    from src.services.desktop_dispatch import wants_desktop_open

    route = (agent or "auto").lower()
    # Desktop (ouvre/lance app) prime sur Team/Diagnostic — même si le sélecteur UI = Team
    if wants_desktop_open(prompt):
        agent = None
    else:
        # @iris / @themis / … → Team Campus même en agent=auto
        if route in ("auto", "") and has_team_mention(prompt):
            route = "team"
        # Sélecteur Agent=Team collé + chat identité → NE PAS préfixer team:
        # (sinon reflection→team_route → agent.fallback « compétences »)
        stripped, already_team = strip_team_prefix(prompt)
        chatty = is_companion_chat(stripped if already_team else prompt)
        if route == "team" and chatty and not has_team_mention(prompt):
            prompt = stripped if already_team else prompt
            agent = None
        elif route == "team" and not prompt.lstrip().lower().startswith("team:"):
            prompt = f"team: {prompt}"
            agent = None
        elif route == "cursor" and not prompt.lstrip().lower().startswith("cursor"):
            prompt = f"cursor: {prompt}"
            agent = None
        elif route == "tools" and "diagnostic" not in prompt.lower():
            prompt = f"fais un diagnostic : {prompt}"
            agent = None
        elif route in ("auto", ""):
            agent = None

    # Mode modèle UI → tier routeur
    mode = body.mode or "auto"
    if model in ("fast", "balanced", "smart"):
        mode = model
        model = None
    elif model == "auto":
        model = None

    return prompt, agent, model, mode


async def _ask_payload(body: AskRequest, llm_router: RouterIA) -> dict:
    prompt, agent, model, mode = _resolve_ask_args(body)
    cid = (body.conversation_id or "default").strip() or "default"

    # Vérification d'une PendingAction en cours pour cette conversation
    try:
        from src.services.pending_actions import (
            clear_pending_action,
            execute_pending_action,
            extract_pending_action_from_assistant_message,
            get_pending_action,
            is_confirmation_affirmative,
            is_confirmation_negative,
            store_pending_action,
        )
    except ImportError:
        try:
            from pending_actions import (  # type: ignore
                clear_pending_action,
                execute_pending_action,
                extract_pending_action_from_assistant_message,
                get_pending_action,
                is_confirmation_affirmative,
                is_confirmation_negative,
                store_pending_action,
            )
        except ImportError:
            get_pending_action = None  # type: ignore

    if get_pending_action:
        pending = get_pending_action(cid)
        if pending:
            if is_confirmation_negative(prompt):
                clear_pending_action(cid)
                return {
                    "ok": True,
                    "content": "Entendu, action annulée. Je reste à votre écoute pour toute autre demande.",
                    "response": "Entendu, action annulée. Je reste à votre écoute pour toute autre demande.",
                    "source": "pending_action_cancelled",
                }
            if is_confirmation_affirmative(prompt):
                clear_pending_action(cid)
                return await execute_pending_action(pending)

    # Phase 3 : Vérification si le prompt déclenche une intention apprise L2
    try:
        from src.services.intent_forge import match_learned_intent
    except ImportError:
        try:
            from intent_forge import match_learned_intent  # type: ignore
        except ImportError:
            match_learned_intent = None  # type: ignore

    matched_learned = match_learned_intent(prompt) if match_learned_intent else None
    if matched_learned and get_pending_action:
        action_name = str(matched_learned.get("action") or "action")
        label = str(matched_learned.get("label") or action_name)
        target_cap = str(matched_learned.get("target_capability") or "capability")
        from pending_actions import PendingAction  # type: ignore

        learned_action = PendingAction(
            action_id=f"act_learned_{action_name}_{int(time.time())}",
            conversation_id=cid,
            action_type="learned_capability",
            label=label,
            summary=f"Exécution de l'action apprise `{label}` (capacité : `{target_cap}`).",
            command=["capability_exec", target_cap],
            context={"action_key": action_name, "target_capability": target_cap},
            button_text=f"Exécuter {label}",
            cancel_text="Annuler",
        )
        store_pending_action(cid, learned_action)
        resp_text = (
            f"J'ai reconnu votre intention **{label}** (action apprise validée L2 ciblant `{target_cap}`). "
            "Souhaitez-vous que je l'exécute ?"
        )
        return {
            "ok": True,
            "content": resp_text,
            "response": resp_text,
            "source": "learned_intent_matched",
            "pending_action": learned_action.to_card_dict(),
        }

    result = await llm_router.dispatch(
        prompt,
        mode=mode,
        profile=body.profile,
        conversation_id=body.conversation_id,
        agent=agent,
        model=model,
    )
    out = ensure_dispatch_dict(result)

    # Enregistrement discret des misses d'intentions si la réponse est un fallback ou conversation standard
    try:
        from src.services.intent_forge import record_intent_miss
    except ImportError:
        try:
            from intent_forge import record_intent_miss  # type: ignore
        except ImportError:
            record_intent_miss = None  # type: ignore

    if record_intent_miss and not matched_learned:
        # On n'enregistre que si ce n'est ni une salutation banale ni une action reconnue
        from chat_intent import is_greeting_chat
        if not is_greeting_chat(prompt) and len(prompt.strip()) > 5:
            record_intent_miss(prompt, conversation_id=cid)

    # Détection si la réponse de l'assistant propose une action avec confirmation
    if get_pending_action:
        resp_content = str(out.get("content") or out.get("response") or "")
        detected_action = extract_pending_action_from_assistant_message(resp_content, cid)
        if detected_action:
            store_pending_action(cid, detected_action)
            out["pending_action"] = detected_action.to_card_dict()

    try:
        from src.services.team_actions import maybe_attach_session_l2_nudge

        attached = await maybe_attach_session_l2_nudge(
            out, conversation_id=body.conversation_id
        )
        if isinstance(attached, dict):
            return attached
    except Exception:
        pass
    return out


@router.post("/chat/pending-action/execute")
async def execute_pending_action_endpoint(body: dict[str, Any]):
    """Exécution directe 1-clic d'une PendingAction en attente."""
    cid = str(body.get("conversation_id") or "default").strip()
    try:
        from src.services.pending_actions import (
            clear_pending_action,
            execute_pending_action,
            get_pending_action,
        )
    except ImportError:
        try:
            from pending_actions import (  # type: ignore
                clear_pending_action,
                execute_pending_action,
                get_pending_action,
            )
        except ImportError:
            return {"ok": False, "error": "Module pending_actions indisponible"}
    pending = get_pending_action(cid)
    if not pending:
        return {"ok": False, "error": "Aucune action en attente pour cette conversation"}
    clear_pending_action(cid)
    return await execute_pending_action(pending)


@router.post("/ask", response_model=AskJSONEnvelope)
@router.post("/ask/", response_model=AskJSONEnvelope)
async def ask(body: AskRequest, llm_router: RouterIA = Depends(get_router_ia)):
    return AskJSONEnvelope(response=await _ask_payload(body, llm_router))


@router.post("/ask/stream")
@router.post("/ask/stream/")
async def ask_stream(body: AskRequest, llm_router: RouterIA = Depends(get_router_ia)):
    """SSE minimal (plan 1.2) — start immédiat, delta* du contenu, done avec la réponse complète."""

    async def _dispatch() -> dict:
        return await _ask_payload(body, llm_router)

    return StreamingResponse(
        stream_ask(_dispatch),
        media_type="text/event-stream",
        headers=_STREAM_HEADERS,
    )


@router.post("/brain", response_model=BrainJSONEnvelope)
async def brain_entry(
    body: BrainRequest,
    bc: BrainController = Depends(get_brain_controller),
):
    result = await bc.brain.handle(body.message)
    return BrainJSONEnvelope.model_validate(ensure_dispatch_dict(result))


@router.get("/world/stream")
@router.get("/world/stream/")
async def world_stream_route(since: int = 0, limit: int = 20):
    """Plan 3.1 — Proxy/cache du Live World Stream Lost Heaven (prime-hub :8787)."""
    try:
        from src.services.world_stream import fetch_world_stream
    except ImportError:
        try:
            from world_stream import fetch_world_stream  # type: ignore
        except ImportError:
            return {"ok": False, "error": "world_stream_unavailable", "events": []}
    data = fetch_world_stream(since=since, limit=limit)
    try:
        from src.services.world_notif_prefs import filter_events
    except ImportError:
        try:
            from world_notif_prefs import filter_events  # type: ignore
        except ImportError:
            filter_events = None  # type: ignore
    if filter_events and isinstance(data, dict) and isinstance(data.get("events"), list):
        data = {**data, "events": filter_events(data["events"])}
    return data


@router.get("/world/notif-prefs")
@router.get("/world/notif-prefs/")
async def world_notif_prefs_get():
    """B1 — préférences rapports monde (greeting / stream)."""
    try:
        from src.services.world_notif_prefs import load_prefs
    except ImportError:
        try:
            from world_notif_prefs import load_prefs  # type: ignore
        except ImportError:
            return {"ok": False, "error": "world_notif_prefs_unavailable"}
    return {"ok": True, "prefs": load_prefs()}


@router.post("/world/notif-prefs")
@router.post("/world/notif-prefs/")
async def world_notif_prefs_post(body: dict[str, Any]):
    """B1 — sync prefs client → serveur (short_social / world_stream)."""
    try:
        from src.services.world_notif_prefs import save_prefs
    except ImportError:
        try:
            from world_notif_prefs import save_prefs  # type: ignore
        except ImportError:
            return {"ok": False, "error": "world_notif_prefs_unavailable"}
    return {"ok": True, "prefs": save_prefs(body if isinstance(body, dict) else {})}


@router.get("/relation-memory")
@router.get("/relation-memory/")
async def relation_memory_route(player: str = "Teome", npc_id: str = ""):
    """Plan 3.2 — Proxy/cache de la mémoire relationnelle MMO (prime-hub :8787)."""
    try:
        from src.services.relation_memory import fetch_relation_memory
    except ImportError:
        try:
            from relation_memory import fetch_relation_memory  # type: ignore
        except ImportError:
            return {"ok": False, "error": "relation_memory_unavailable", "entries": []}
    return fetch_relation_memory(player=player, npc_id=npc_id)


@router.post("/relation-memory/append")
@router.post("/relation-memory/append/")
async def relation_memory_append_route(body: dict[str, Any]):
    """Plan 3.2 — Synchronisation bilatérale d'une note relationnelle vers prime-hub :8787."""
    try:
        from src.services.relation_memory import append_relation_memory
    except ImportError:
        try:
            from relation_memory import append_relation_memory  # type: ignore
        except ImportError:
            return {"ok": False, "error": "relation_memory_unavailable"}
    return append_relation_memory(
        player=str(body.get("player", "Teome")),
        npc_id=str(body.get("npc_id", "")),
        kind=str(body.get("kind", "chat")),
        note=str(body.get("note", "")),
        detail=body.get("detail") if isinstance(body.get("detail"), dict) else None,
    )

