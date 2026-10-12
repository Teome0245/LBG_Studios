"""Store RAG — pgvector si dispo, sinon JSONB + cosine Python, sinon mémoire process."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Sequence

from .config import database_url, embed_dim
from .embeddings import cosine_similarity

logger = logging.getLogger("lbg.rag.store")


@dataclass
class RagChunk:
    source_id: str
    source_kind: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    score: float = 0.0


# --- backend mémoire (tests / sans DATABASE_URL) --------------------------------

_memory: list[dict[str, Any]] = []
_schema_mode: str | None = None  # "vector" | "jsonb" | "memory" | "unavailable"


def reset_memory_for_tests() -> None:
    global _memory, _schema_mode
    _memory = []
    _schema_mode = None


def _vec_literal(embedding: Sequence[float]) -> str:
    return "[" + ",".join(f"{float(x):.8f}" for x in embedding) + "]"


async def _connect():
    import asyncpg

    url = database_url()
    if not url:
        raise RuntimeError("DATABASE_URL vide")
    return await asyncpg.connect(url)


async def _rag_columns(conn) -> set[str]:
    rows = await conn.fetch(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'rag_chunks'
        """
    )
    return {str(r["column_name"]) for r in rows}


async def _ensure_hnsw(conn) -> None:
    try:
        await conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_rag_chunks_embedding_hnsw
            ON rag_chunks USING hnsw (embedding vector_cosine_ops)
            """
        )
    except Exception:
        logger.debug("index hnsw rag_chunks indisponible (ok pour petit corpus)")


async def _create_vector_table(conn, dim: int) -> None:
    await conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS rag_chunks (
          id BIGSERIAL PRIMARY KEY,
          source_id TEXT NOT NULL,
          source_kind TEXT NOT NULL,
          content TEXT NOT NULL,
          metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
          embedding vector({dim}) NOT NULL,
          updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          UNIQUE (source_kind, source_id)
        )
        """
    )
    await _ensure_hnsw(conn)


async def _migrate_jsonb_to_vector(conn, dim: int) -> None:
    """Recrée la table en mode vector (petit corpus v1 — drop + recreate)."""
    logger.info("migration rag_chunks JSONB → vector(%s)", dim)
    await conn.execute("DROP TABLE IF EXISTS rag_chunks")
    await _create_vector_table(conn, dim)


async def ensure_schema(*, force_refresh: bool = False) -> str:
    """Crée tables/index. Retourne le mode: vector | jsonb | memory | unavailable."""
    global _schema_mode
    if _schema_mode is not None and not force_refresh:
        return _schema_mode

    url = database_url()
    if not url:
        _schema_mode = "memory"
        return _schema_mode

    try:
        import asyncpg  # noqa: F401
    except ImportError:
        logger.warning("asyncpg indisponible — RAG store mémoire")
        _schema_mode = "memory"
        return _schema_mode

    dim = embed_dim()
    conn = await _connect()
    try:
        # Tentative pgvector
        try:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        except Exception as exc:
            logger.info("pgvector extension indisponible (%s) — fallback JSONB", exc)
            cols = await _rag_columns(conn)
            if not cols:
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS rag_chunks (
                      id BIGSERIAL PRIMARY KEY,
                      source_id TEXT NOT NULL,
                      source_kind TEXT NOT NULL,
                      content TEXT NOT NULL,
                      metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                      embedding_json JSONB NOT NULL,
                      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                      UNIQUE (source_kind, source_id)
                    )
                    """
                )
            _schema_mode = "jsonb"
            return _schema_mode

        cols = await _rag_columns(conn)
        if not cols:
            await _create_vector_table(conn, dim)
            _schema_mode = "vector"
            return _schema_mode

        if "embedding" in cols and "embedding_json" not in cols:
            await _ensure_hnsw(conn)
            _schema_mode = "vector"
            return _schema_mode

        if "embedding_json" in cols and "embedding" not in cols:
            # Ancienne table JSONB + extension dispo → migrer
            await _migrate_jsonb_to_vector(conn, dim)
            _schema_mode = "vector"
            return _schema_mode

        if "embedding" in cols:
            # Table hybride ou déjà vector : privilégier vector
            await _ensure_hnsw(conn)
            _schema_mode = "vector"
            return _schema_mode

        # Colonnes inattendues : recreer vector
        await _migrate_jsonb_to_vector(conn, dim)
        _schema_mode = "vector"
        return _schema_mode
    except Exception as exc:
        logger.warning("ensure_schema RAG échoué: %s — mémoire", exc)
        _schema_mode = "memory"
        return _schema_mode
    finally:
        await conn.close()


async def force_vector_migration() -> str:
    """Ops : force refresh schéma (après install pgvector)."""
    return await ensure_schema(force_refresh=True)

async def upsert_chunk(
    *,
    source_id: str,
    source_kind: str,
    content: str,
    embedding: Sequence[float],
    metadata: dict[str, Any] | None = None,
) -> None:
    sid = (source_id or "").strip()
    sk = (source_kind or "").strip()
    body = (content or "").strip()
    if not sid or not sk or not body or not embedding:
        return

    mode = await ensure_schema()
    meta = metadata if isinstance(metadata, dict) else {}
    emb = [float(x) for x in embedding]

    if mode == "memory":
        for row in _memory:
            if row["source_id"] == sid and row["source_kind"] == sk:
                row["content"] = body
                row["embedding"] = emb
                row["metadata"] = meta
                row["updated_at"] = time.time()
                return
        _memory.append(
            {
                "source_id": sid,
                "source_kind": sk,
                "content": body,
                "embedding": emb,
                "metadata": meta,
                "updated_at": time.time(),
            }
        )
        return

    conn = await _connect()
    try:
        if mode == "vector":
            await conn.execute(
                """
                INSERT INTO rag_chunks (source_id, source_kind, content, metadata, embedding, updated_at)
                VALUES ($1, $2, $3, $4::jsonb, $5::vector, NOW())
                ON CONFLICT (source_kind, source_id) DO UPDATE SET
                  content = EXCLUDED.content,
                  metadata = EXCLUDED.metadata,
                  embedding = EXCLUDED.embedding,
                  updated_at = NOW()
                """,
                sid,
                sk,
                body,
                json.dumps(meta, ensure_ascii=False),
                _vec_literal(emb),
            )
        else:
            await conn.execute(
                """
                INSERT INTO rag_chunks (source_id, source_kind, content, metadata, embedding_json, updated_at)
                VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, NOW())
                ON CONFLICT (source_kind, source_id) DO UPDATE SET
                  content = EXCLUDED.content,
                  metadata = EXCLUDED.metadata,
                  embedding_json = EXCLUDED.embedding_json,
                  updated_at = NOW()
                """,
                sid,
                sk,
                body,
                json.dumps(meta, ensure_ascii=False),
                json.dumps(emb),
            )
    finally:
        await conn.close()


async def search(
    query_embedding: Sequence[float],
    *,
    k: int = 4,
) -> list[RagChunk]:
    if not query_embedding:
        return []
    mode = await ensure_schema()
    cap = max(1, min(int(k), 12))
    q = [float(x) for x in query_embedding]

    if mode == "memory":
        scored: list[tuple[float, dict[str, Any]]] = []
        for row in _memory:
            score = cosine_similarity(q, row.get("embedding") or [])
            if score > 0:
                scored.append((score, row))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            RagChunk(
                source_id=str(r["source_id"]),
                source_kind=str(r["source_kind"]),
                content=str(r["content"]),
                metadata=dict(r.get("metadata") or {}),
                score=float(s),
            )
            for s, r in scored[:cap]
        ]

    conn = await _connect()
    try:
        if mode == "vector":
            rows = await conn.fetch(
                """
                SELECT source_id, source_kind, content, metadata,
                       1 - (embedding <=> $1::vector) AS score
                FROM rag_chunks
                ORDER BY embedding <=> $1::vector
                LIMIT $2
                """,
                _vec_literal(q),
                cap,
            )
            out: list[RagChunk] = []
            for row in rows:
                meta = row["metadata"]
                if isinstance(meta, str):
                    try:
                        meta = json.loads(meta)
                    except json.JSONDecodeError:
                        meta = {}
                out.append(
                    RagChunk(
                        source_id=str(row["source_id"]),
                        source_kind=str(row["source_kind"]),
                        content=str(row["content"]),
                        metadata=dict(meta) if isinstance(meta, dict) else {},
                        score=float(row["score"] or 0.0),
                    )
                )
            return out

        # JSONB : charge tout (petit corpus v1) + cosine Python
        rows = await conn.fetch(
            "SELECT source_id, source_kind, content, metadata, embedding_json FROM rag_chunks"
        )
        scored_rows: list[tuple[float, Any]] = []
        for row in rows:
            raw = row["embedding_json"]
            if isinstance(raw, str):
                try:
                    raw = json.loads(raw)
                except json.JSONDecodeError:
                    continue
            if not isinstance(raw, list):
                continue
            score = cosine_similarity(q, raw)
            if score > 0:
                scored_rows.append((score, row))
        scored_rows.sort(key=lambda x: x[0], reverse=True)
        out2: list[RagChunk] = []
        for score, row in scored_rows[:cap]:
            meta = row["metadata"]
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except json.JSONDecodeError:
                    meta = {}
            out2.append(
                RagChunk(
                    source_id=str(row["source_id"]),
                    source_kind=str(row["source_kind"]),
                    content=str(row["content"]),
                    metadata=dict(meta) if isinstance(meta, dict) else {},
                    score=float(score),
                )
            )
        return out2
    finally:
        await conn.close()
