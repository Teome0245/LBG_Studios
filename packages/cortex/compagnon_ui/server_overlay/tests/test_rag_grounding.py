"""Tests overlay rag_grounding."""

from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

_OVERLAY = Path(__file__).resolve().parents[1]
if str(_OVERLAY) not in sys.path:
    sys.path.insert(0, str(_OVERLAY))

import rag_grounding as rg  # noqa: E402


class RagGroundingTests(unittest.TestCase):
    def test_wants_when_enabled(self) -> None:
        with patch.dict("os.environ", {"LBG_RAG_ENABLED": "1"}, clear=False):
            self.assertTrue(rg.wants_rag_context("montre ce que tu retiens"))
            self.assertTrue(rg.wants_rag_context("selon nos leçons apprises"))
            self.assertFalse(rg.wants_rag_context("ouvre notepad"))

    def test_wants_false_when_disabled(self) -> None:
        with patch.dict("os.environ", {"LBG_RAG_ENABLED": "0"}, clear=False):
            self.assertFalse(rg.wants_rag_context("montre ce que tu retiens"))

    def test_load_block_disabled(self) -> None:
        async def _run() -> None:
            with patch.dict("os.environ", {"LBG_RAG_ENABLED": "0"}, clear=False):
                block = await rg.load_rag_block("montre ta mémoire")
            self.assertEqual(block, "")

        asyncio.run(_run())

    def test_load_block_calls_retrieve(self) -> None:
        async def _run() -> None:
            fake = AsyncMock(return_value="Contexte récupéré (RAG) :\n- [lesson:x] y")
            with patch.dict("os.environ", {"LBG_RAG_ENABLED": "1"}, clear=False):
                with patch.object(rg, "_import_retrieve", return_value=fake):
                    block = await rg.load_rag_block("montre ta mémoire agent")
            self.assertIn("Contexte récupéré", block)
            fake.assert_awaited_once()

        asyncio.run(_run())


if __name__ == "__main__":
    unittest.main()
