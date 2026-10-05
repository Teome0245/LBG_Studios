"""Retrieve sémantique → chunks / bloc prompt."""

from __future__ import annotations

import logging
from typing import Any

from .config import rag_enabled, top_k
from .embeddings import EmbedError, embed_text
from .format import format_rag_block
from .store import RagChunk, search

logger = logging.getLogger("lbg.rag.retrieve")


async def retrieve_chunks(
    query: str,
    *,
    k: int | None = None,
) -> list[RagChunk]:
    """Top-k chunks pour une requête. [] si désactivé / erreur."""
    if not rag_enabled():
        return []
    q = (query or "").strip()
    if not q:
        return []
    try:
        emb = await embed_text(q)
        return await search(emb, k=k if k is not None else top_k())
    except EmbedError as exc:
        logger.debug("RAG embed skip: %s", exc)
        return []
    except Exception as exc:
        logger.debug("RAG retrieve skip: %s", exc)
        return []


async def retrieve_for_prompt(
    query: str,
    *,
    k: int | None = None,
) -> str:
    """Bloc formaté prêt à concaténer au system prompt."""
    chunks = await retrieve_chunks(query, k=k)
    return format_rag_block(chunks)


def retrieve_stats(chunks: list[RagChunk]) -> dict[str, Any]:
    return {
        "n": len(chunks),
        "kinds": sorted({c.source_kind for c in chunks}),
        "ids": [c.source_id for c in chunks],
        "scores": [round(c.score, 4) for c in chunks],
    }
