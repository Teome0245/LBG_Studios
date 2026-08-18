"""Export session assistant Pilot (validation serveur, sans persistance)."""

from __future__ import annotations

from fastapi import APIRouter

from services.session_summary_export import build_assistant_session_export, build_mmo_bridge_context

from ._models import AssistantSessionExportBody

router = APIRouter()

@router.post("/assistant/session-summary/export", tags=["pilot"])
async def pilot_assistant_session_summary_export(body: AssistantSessionExportBody) -> dict[str, object]:
    """
    Valide et tronque un résumé volontaire (notes, historique court, session_summary MMO).
    Ne stocke rien côté serveur — complète l’export 100 % navigateur du Pilot `#/assistant`.
    """
    payload: dict[str, object] = {}
    if body.notes is not None:
        payload["notes"] = body.notes
    if body.history is not None:
        payload["history"] = body.history
    if body.session_summary is not None:
        payload["session_summary"] = body.session_summary
    if body.mmo_bridge is not None:
        payload["mmo_bridge"] = body.mmo_bridge
    export = build_assistant_session_export(payload)
    return {"ok": True, "export": export}


@router.post("/assistant/session-summary/mmo-bridge", tags=["pilot"])
async def pilot_assistant_session_summary_mmo_bridge(body: AssistantSessionExportBody) -> dict[str, object]:
    """
    Valide un résumé volontaire et retourne un context_patch prêt pour chat/route (pont MMO).
    Ne persiste rien côté serveur.
    """
    payload: dict[str, object] = {}
    if body.notes is not None:
        payload["notes"] = body.notes
    if body.history is not None:
        payload["history"] = body.history
    if body.session_summary is not None:
        payload["session_summary"] = body.session_summary
    if body.mmo_bridge is not None:
        payload["mmo_bridge"] = body.mmo_bridge
    export = build_assistant_session_export(payload)
    context_patch = build_mmo_bridge_context(export)
    return {
        "ok": True,
        "export": export,
        "context_patch": context_patch,
        "hint": "Fusionnez context_patch dans le contexte assistant ou route Pilot.",
    }
