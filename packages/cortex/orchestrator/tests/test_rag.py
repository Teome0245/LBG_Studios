"""Tests RAG v1 — format, store mémoire, ingest parsers, grounding overlay."""

from __future__ import annotations

import asyncio
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

ORCH = Path(__file__).resolve().parents[1]
if str(ORCH) not in sys.path:
    sys.path.insert(0, str(ORCH))

from services.rag import format as rag_format  # noqa: E402
from services.rag import ingest as rag_ingest  # noqa: E402
from services.rag.embeddings import cosine_similarity  # noqa: E402
from services.rag.store import RagChunk, reset_memory_for_tests, search, upsert_chunk  # noqa: E402


class CosineTests(unittest.TestCase):
    def test_identical(self) -> None:
        v = [1.0, 0.0, 0.0]
        self.assertAlmostEqual(cosine_similarity(v, v), 1.0)

    def test_orthogonal(self) -> None:
        self.assertAlmostEqual(cosine_similarity([1, 0], [0, 1]), 0.0)


class FormatTests(unittest.TestCase):
    def test_empty(self) -> None:
        self.assertEqual(rag_format.format_rag_block([]), "")

    def test_budget_truncates(self) -> None:
        chunks = [
            RagChunk("a", "lesson", "x" * 200),
            RagChunk("b", "lesson", "y" * 200),
        ]
        block = rag_format.format_rag_block(chunks, budget=180)
        self.assertIn("Contexte récupéré", block)
        self.assertLessEqual(len(block), 180)


class MemoryStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_memory_for_tests()
        self._env = patch.dict("os.environ", {"DATABASE_URL": ""}, clear=False)
        self._env.start()

    def tearDown(self) -> None:
        self._env.stop()
        reset_memory_for_tests()

    def test_upsert_and_search(self) -> None:
        async def _run() -> None:
            await upsert_chunk(
                source_id="l1",
                source_kind="lesson",
                content="Ne jamais clôturer une mission si smoke rouge",
                embedding=[1.0, 0.0, 0.0],
                metadata={"k": 1},
            )
            await upsert_chunk(
                source_id="l2",
                source_kind="lesson",
                content="Autre sujet sans rapport",
                embedding=[0.0, 1.0, 0.0],
            )
            hits = await search([0.9, 0.1, 0.0], k=2)
            self.assertGreaterEqual(len(hits), 1)
            self.assertEqual(hits[0].source_id, "l1")

        asyncio.run(_run())

    def test_upsert_idempotent(self) -> None:
        async def _run() -> None:
            await upsert_chunk(
                source_id="l1",
                source_kind="lesson",
                content="v1",
                embedding=[1.0, 0.0],
            )
            await upsert_chunk(
                source_id="l1",
                source_kind="lesson",
                content="v2",
                embedding=[1.0, 0.0],
            )
            hits = await search([1.0, 0.0], k=5)
            same = [h for h in hits if h.source_id == "l1"]
            self.assertEqual(len(same), 1)
            self.assertEqual(same[0].content, "v2")

        asyncio.run(_run())


class IngestParserTests(unittest.TestCase):
    def test_load_lessons_from_knowledge(self) -> None:
        items = rag_ingest.load_lesson_items()
        # Le fichier monorepo knowledge/lessons_learned.json existe
        self.assertGreater(len(items), 0)
        self.assertTrue(all(i.source_kind == "lesson" for i in items))
        self.assertTrue(any("smoke" in i.content.lower() for i in items))

    def test_load_knowledge_facts_and_character(self) -> None:
        items = rag_ingest.load_knowledge_snippets()
        self.assertGreaterEqual(len(items), 15)
        ids = {i.source_id for i in items}
        self.assertTrue(any(i.startswith("fact_") for i in ids))
        self.assertIn("character_compagnon_v1", ids)
        self.assertTrue(all(i.source_kind in {"knowledge", "philosophy"} for i in items))

    def test_load_experiences_missing_ok(self) -> None:
        with patch.dict("os.environ", {"LBG_JOBS_MEMORY_PATH": "/tmp/no_such_exp.jsonl"}, clear=False):
            items = rag_ingest.load_experience_items()
        self.assertEqual(items, [])

    def test_load_experiences_file(self) -> None:
        import tempfile

        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "id": "e1",
                        "goal": "réparer disque",
                        "outcome": "failed",
                        "problem": "plein",
                        "resolution": "prune",
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            path = f.name
        with patch.dict("os.environ", {"LBG_JOBS_MEMORY_PATH": path}, clear=False):
            items = rag_ingest.load_experience_items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].source_id, "e1")
        self.assertIn("réparer", items[0].content)


class RetrieveFlagTests(unittest.TestCase):
    def test_disabled_returns_empty(self) -> None:
        from services.rag.retrieve import retrieve_chunks

        async def _run() -> None:
            with patch.dict("os.environ", {"LBG_RAG_ENABLED": "0"}, clear=False):
                chunks = await retrieve_chunks("montre ta mémoire")
            self.assertEqual(chunks, [])

        asyncio.run(_run())

    def test_enabled_uses_embed_and_search(self) -> None:
        from services.rag.retrieve import retrieve_for_prompt

        async def _run() -> None:
            reset_memory_for_tests()
            await upsert_chunk(
                source_id="l1",
                source_kind="lesson",
                content="leçon smoke rouge",
                embedding=[1.0, 0.0, 0.0],
            )
            with patch.dict("os.environ", {"LBG_RAG_ENABLED": "1", "DATABASE_URL": ""}, clear=False):
                with patch(
                    "services.rag.retrieve.embed_text",
                    new=AsyncMock(return_value=[1.0, 0.0, 0.0]),
                ):
                    block = await retrieve_for_prompt("smoke QA")
            self.assertIn("Contexte récupéré", block)
            self.assertIn("smoke", block.lower())

        asyncio.run(_run())


if __name__ == "__main__":
    unittest.main()
