"""RAG LBG — embeddings Ollama (.111) + pgvector (Postgres RouterIA).

Désactivé par défaut (`LBG_RAG_ENABLED=0`) jusqu'à ingest + pgvector prêts.
"""

from __future__ import annotations

from .config import rag_enabled
from .format import format_rag_block
from .retrieve import retrieve_chunks, retrieve_for_prompt

__all__ = [
    "format_rag_block",
    "rag_enabled",
    "retrieve_chunks",
    "retrieve_for_prompt",
]
