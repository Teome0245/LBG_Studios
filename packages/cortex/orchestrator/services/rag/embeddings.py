"""Client embeddings Ollama — modèle défaut ``nomic-embed-text`` sur .111."""

from __future__ import annotations

import logging
from typing import Any, Sequence

from .config import embed_base_url, embed_model, embed_timeout_s

logger = logging.getLogger("lbg.rag.embeddings")


class EmbedError(RuntimeError):
    """Échec embedding (réseau, modèle manquant, payload invalide)."""


def _parse_embedding(payload: Any) -> list[float]:
    if not isinstance(payload, dict):
        raise EmbedError("réponse embeddings non-objet")
    emb = payload.get("embedding")
    if isinstance(emb, list) and emb and all(isinstance(x, (int, float)) for x in emb):
        return [float(x) for x in emb]
    # variante OpenAI-compat
    data = payload.get("data")
    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict):
            emb2 = first.get("embedding")
            if isinstance(emb2, list) and emb2:
                return [float(x) for x in emb2]
    raise EmbedError("champ embedding absent ou invalide")


async def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    """Embed une liste de textes. Lève ``EmbedError`` si un seul échoue."""
    out: list[list[float]] = []
    for text in texts:
        out.append(await embed_text(text))
    return out


async def embed_text(text: str) -> list[float]:
    """Embed un texte via ``POST {base}/api/embeddings``."""
    cleaned = (text or "").strip()
    if not cleaned:
        raise EmbedError("texte vide")

    try:
        import httpx
    except ImportError as exc:  # pragma: no cover
        raise EmbedError("httpx indisponible") from exc

    url = f"{embed_base_url()}/api/embeddings"
    model = embed_model()
    timeout = embed_timeout_s()
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(connect=1.5, read=timeout, write=2.0, pool=1.0)
        ) as client:
            resp = await client.post(url, json={"model": model, "prompt": cleaned})
        if resp.status_code != 200:
            raise EmbedError(f"http_{resp.status_code}: {resp.text[:200]}")
        return _parse_embedding(resp.json())
    except EmbedError:
        raise
    except Exception as exc:
        raise EmbedError(f"{type(exc).__name__}: {exc}") from exc


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """Similarité cosinus (fallback store mémoire / sans pgvector)."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        fx = float(x)
        fy = float(y)
        dot += fx * fy
        na += fx * fx
        nb += fy * fy
    if na <= 0.0 or nb <= 0.0:
        return 0.0
    return dot / ((na**0.5) * (nb**0.5))
