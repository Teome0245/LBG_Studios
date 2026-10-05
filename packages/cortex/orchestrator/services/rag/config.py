"""Config RAG via env — défauts alignés matrice LLM light (.111)."""

from __future__ import annotations

import os


def _truthy(raw: str | None, default: str = "0") -> bool:
    return (raw if raw is not None else default).strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def rag_enabled() -> bool:
    """Feature flag global. Défaut off (greffe progressive)."""
    return _truthy(os.environ.get("LBG_RAG_ENABLED"), "0")


def database_url() -> str:
    return (os.environ.get("DATABASE_URL") or "").strip()


def embed_base_url() -> str:
    """Host Ollama light pour embeddings (pas le heavy .110)."""
    return (
        os.environ.get("LBG_RAG_EMBED_BASE_URL", "").strip()
        or os.environ.get("LBG_REASON_LIGHT_BASE_URL", "").strip()
        or "http://192.168.0.111:11434"
    ).rstrip("/")


def embed_model() -> str:
    return (
        os.environ.get("LBG_RAG_EMBED_MODEL", "").strip() or "nomic-embed-text"
    )


def embed_dim() -> int:
    try:
        return max(32, min(int(os.environ.get("LBG_RAG_EMBED_DIM", "768")), 4096))
    except ValueError:
        return 768


def top_k() -> int:
    try:
        return max(1, min(int(os.environ.get("LBG_RAG_TOP_K", "4")), 12))
    except ValueError:
        return 4


def max_chars() -> int:
    """Budget caractères du bloc injecté dans le system prompt."""
    try:
        return max(200, min(int(os.environ.get("LBG_RAG_MAX_CHARS", "1500")), 8000))
    except ValueError:
        return 1500


def embed_timeout_s() -> float:
    try:
        return max(1.0, min(float(os.environ.get("LBG_RAG_EMBED_TIMEOUT_S", "8")), 60.0))
    except ValueError:
        return 8.0


def search_timeout_s() -> float:
    try:
        return max(0.5, min(float(os.environ.get("LBG_RAG_SEARCH_TIMEOUT_S", "3")), 30.0))
    except ValueError:
        return 3.0
