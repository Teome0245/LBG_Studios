"""Formatage du bloc prompt RAG."""

from __future__ import annotations

from typing import Sequence

from .config import max_chars
from .store import RagChunk


def format_rag_block(
    chunks: Sequence[RagChunk] | None,
    *,
    budget: int | None = None,
) -> str:
    """Bloc système compact. Vide si aucun chunk."""
    if not chunks:
        return ""
    cap = budget if budget is not None else max_chars()
    lines = ["Contexte récupéré (RAG — faits ancrés, ne pas inventer hors de cette liste) :"]
    used = len(lines[0])
    for ch in chunks:
        kind = (ch.source_kind or "?").strip()
        sid = (ch.source_id or "").strip()[:48]
        body = (ch.content or "").strip().replace("\n", " ")
        if not body:
            continue
        line = f"- [{kind}:{sid}] {body}"
        if used + len(line) + 1 > cap:
            # tronquer le dernier fragment si encore de la place
            remain = cap - used - 1
            if remain > 40:
                lines.append(line[: remain - 1] + "…")
            break
        lines.append(line)
        used += len(line) + 1
    if len(lines) <= 1:
        return ""
    return "\n".join(lines)
