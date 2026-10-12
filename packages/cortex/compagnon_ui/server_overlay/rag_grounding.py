"""Ancrage RAG — injecte fragments sémantiques (leçons / expériences / knowledge).

Best-effort : désactivé par défaut (`LBG_RAG_ENABLED=0`).
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any

logger = logging.getLogger("lbg.rag_grounding")

_RAG_HINTS = re.compile(
    r"(?i)("
    r"\b(ta|ma|sa|notre)\s+(mémoire|memoire)\b|"
    r"\b(mémoire|memoire)\s+(agent|self|équipe|equipe|studio|longue?)\b|"
    r"\b(leçons?\s+apprises|lessons[_\s-]?learned|souvenirs?|expérience[s]?)\b|"
    r"\bce\s+que\s+tu\s+(sais|retiens|connais|te\s+souviens)\b|"
    r"\b(rappelle[- ]toi|selon\s+(nos|tes)\s+leçons)\b|"
    r"\b(rag|contexte\s+récupéré|base\s+de\s+connaissances)\b|"
    r"\b(échecs?\s+passés|ne\s+pas\s+répéter)\b"
    r")"
)


def rag_enabled() -> bool:
    return os.environ.get("LBG_RAG_ENABLED", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def wants_rag_context(prompt: str) -> bool:
    """Heuristique : questions mémoire / leçons / souvenirs → RAG."""
    if not rag_enabled():
        return False
    return bool(_RAG_HINTS.search(prompt or ""))


def _import_retrieve():
    """Import souple : package orch ou overlay déployé sous src.services.rag."""
    try:
        from services.rag.retrieve import retrieve_for_prompt  # type: ignore

        return retrieve_for_prompt
    except ImportError:
        pass
    try:
        from src.services.rag.retrieve import retrieve_for_prompt  # type: ignore

        return retrieve_for_prompt
    except ImportError:
        pass
    # Monorepo : PYTHONPATH=orchestrator
    try:
        from rag.retrieve import retrieve_for_prompt  # type: ignore

        return retrieve_for_prompt
    except ImportError:
        return None


async def load_rag_block(prompt: str, *, force: bool = False) -> str:
    """Retourne le bloc à injecter, ou ''."""
    if not rag_enabled():
        return ""
    if not force and not wants_rag_context(prompt):
        return ""
    retrieve_for_prompt = _import_retrieve()
    if retrieve_for_prompt is None:
        logger.debug("RAG package indisponible (import)")
        return ""
    try:
        block = await retrieve_for_prompt(prompt)
        return block if isinstance(block, str) else ""
    except Exception as exc:
        logger.debug("RAG load failed: %s", exc)
        return ""


def format_rag_grounding(block: str | None) -> str:
    """Passthrough — le formatage est déjà fait côté retrieve."""
    return (block or "").strip()


def rag_debug_meta(block: str) -> dict[str, Any]:
    return {"enabled": rag_enabled(), "chars": len(block or ""), "injected": bool(block)}
