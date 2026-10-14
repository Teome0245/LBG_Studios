"""Tests unitaires — context_journal (A1, sans Orch runtime)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_OVERLAY = Path(__file__).resolve().parents[1]
if str(_OVERLAY) not in sys.path:
    sys.path.insert(0, str(_OVERLAY))

import context_journal as cj  # noqa: E402


class ContextJournalTests(unittest.TestCase):
    def test_empty_journal(self) -> None:
        j = cj.empty_journal()
        self.assertEqual(j["count"], 0)
        self.assertTrue(j["empty"])
        self.assertEqual(j["blocks"], [])

    def test_finalize_lists_blocks(self) -> None:
        blocks = [
            cj.make_block("character_pack", label="Character pack", summary="compagnon_v1", chars=120),
            cj.make_block("dials", label="Dials", summary="densite=0.40", chars=40),
            cj.make_block(
                "world_stream",
                label="World stream",
                summary="2 événements",
                chars=80,
                meta={"events": 2},
            ),
        ]
        j = cj.finalize_journal(blocks)
        self.assertEqual(j["count"], 3)
        self.assertFalse(j["empty"])
        ids = [b["id"] for b in j["blocks"]]
        self.assertEqual(ids, ["character_pack", "dials", "world_stream"])
        self.assertEqual(j["blocks"][2]["meta"]["events"], 2)

    def test_dedupe_same_id(self) -> None:
        blocks = [
            cj.make_block("dials", label="Dials", summary="a"),
            cj.make_block("dials", label="Dials", summary="b"),
        ]
        j = cj.finalize_journal(blocks)
        self.assertEqual(j["count"], 1)
        self.assertEqual(j["blocks"][0]["summary"], "a")

    def test_sanitize_secret_summary(self) -> None:
        b = cj.make_block("memory", label="Mémoire", summary="api_key=sk-secret-xyz")
        self.assertIn("ommis", b["summary"].lower())
        self.assertNotIn("sk-secret", b["summary"])

    def test_attach_on_result(self) -> None:
        result = {"content": "salut", "model": "x", "provider": "local"}
        out = cj.attach_context_journal(
            result,
            [cj.make_block("short_ctx", label="Fil court", summary="2 tours", chars=40)],
        )
        self.assertIn("context_journal", out)
        self.assertEqual(out["context_journal"]["count"], 1)
        self.assertEqual(out["context_journal"]["blocks"][0]["id"], "short_ctx")

    def test_attach_preserves_existing(self) -> None:
        result = {
            "content": "x",
            "context_journal": cj.finalize_journal(
                [cj.make_block("short_circuit", label="Réponse courte", summary="short_social")]
            ),
        }
        out = cj.attach_context_journal(
            result,
            [cj.make_block("dials", label="Dials", summary="x")],
        )
        self.assertEqual(out["context_journal"]["blocks"][0]["id"], "short_circuit")

    def test_truncate_long_summary(self) -> None:
        long = "x" * 400
        b = cj.make_block("rag", label="RAG", summary=long)
        self.assertLessEqual(len(b["summary"]), 160)
        self.assertTrue(b["summary"].endswith("…"))


if __name__ == "__main__":
    unittest.main()
