"""
Routes racine historiquement inline dans `app/factory.py` : /history, /models, /ask, /brain.
"""

from __future__ import annotations

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
    result = await llm_router.dispatch(
        prompt,
        mode=mode,
        profile=body.profile,
        conversation_id=body.conversation_id,
        agent=agent,
        model=model,
    )
    out = ensure_dispatch_dict(result)
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
    return fetch_world_stream(since=since, limit=limit)


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

