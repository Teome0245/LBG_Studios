"""
Routes racine historiquement inline dans `app/factory.py` : /history, /models, /ask, /brain.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

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

router = APIRouter(tags=["Core"])


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


@router.post("/ask", response_model=AskJSONEnvelope)
@router.post("/ask/", response_model=AskJSONEnvelope)
async def ask(body: AskRequest, llm_router: RouterIA = Depends(get_router_ia)):
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

    result = await llm_router.dispatch(
        prompt,
        mode=mode,
        profile=body.profile,
        conversation_id=body.conversation_id,
        agent=agent,
        model=model,
    )
    payload = ensure_dispatch_dict(result)
    return AskJSONEnvelope(response=payload)


@router.post("/brain", response_model=BrainJSONEnvelope)
async def brain_entry(
    body: BrainRequest,
    bc: BrainController = Depends(get_brain_controller),
):
    result = await bc.brain.handle(body.message)
    return BrainJSONEnvelope.model_validate(ensure_dispatch_dict(result))
