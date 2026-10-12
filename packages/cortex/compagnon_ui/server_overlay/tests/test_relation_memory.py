"""Tests — relation_memory (Plan 3.2 Convergence de la mémoire relationnelle jeu ↔ bureau)."""

from __future__ import annotations

import asyncio
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_OVERLAY = Path(__file__).resolve().parents[1]
if str(_OVERLAY) not in sys.path:
    sys.path.insert(0, str(_OVERLAY))

import character_layer as cl  # noqa: E402
import relation_memory as rm  # noqa: E402

_FAKE_RELATIONS = {
    "ok": True,
    "player": "Teome",
    "npc_id": "",
    "count": 3,
    "entries": [
        {
            "npc_id": "npc:core3_barman_jax",
            "npc_name": "Jax Moro",
            "kind": "gift",
            "note": "Pourboire 2 crédits après discussion à La Perle",
            "ts": 1791810000.0,
        },
        {
            "npc_id": "npc:core3_daan_oth",
            "npc_name": "Daan Oth",
            "kind": "quest_accept",
            "note": "A accepté la quête du ferrailleur des dunes",
            "ts": 1791809000.0,
        },
        {
            "npc_id": "companion_nix",
            "npc_name": "Nix",
            "kind": "escort",
            "note": "A escorté Teome près des portes ouest",
            "ts": 1791808000.0,
        },
    ],
    "source": "prime_hub",
    "ticket": "C2",
}


class RelationMemoryTests(unittest.TestCase):
    def test_wants_relation_memory(self) -> None:
        self.assertTrue(rm.wants_relation_memory("quelles sont mes relations avec les pnj ?"))
        self.assertTrue(rm.wants_relation_memory("ce que pense Jax de moi"))
        self.assertTrue(rm.wants_relation_memory("qui me connaît en jeu ?"))
        self.assertTrue(rm.wants_relation_memory("réputation avec Jax à Lost Heaven"))
        self.assertTrue(rm.wants_relation_memory("mémoire relationnelle mmo"))
        self.assertFalse(rm.wants_relation_memory("bonjour"))
        self.assertFalse(rm.wants_relation_memory("ouvre vscode"))

    def test_format_relation_memory_block(self) -> None:
        with patch.object(rm, "fetch_relation_memory", return_value=_FAKE_RELATIONS):
            block = rm.format_relation_memory_block(player="Teome", limit=3)
            self.assertIn("[Mémoire relationnelle in-game (Lost Heaven)", block)
            self.assertIn("Jax Moro", block)
            self.assertIn("Pourboire", block)
            self.assertIn("Daan Oth", block)
            self.assertIn("Nix", block)

    def test_format_relation_report(self) -> None:
        report = rm.format_relation_report(_FAKE_RELATIONS, player="Teome")
        self.assertIn("relations in-game", report)
        self.assertIn("Jax Moro", report)
        self.assertIn("Daan Oth", report)
        self.assertNotIn("{", report)  # Pas de dump JSON brut
        self.assertIn("Teome", report)

    def test_append_relation_memory(self) -> None:
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"ok": True, "count": 4}).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp

        with patch("urllib.request.urlopen", return_value=mock_resp):
            res = rm.append_relation_memory(
                player="Teome",
                npc_id="npc:core3_barman_jax",
                kind="trade",
                note="A payé une tournée générale",
            )
            self.assertTrue(res.get("ok"))
            self.assertEqual(res.get("count"), 4)

    def test_attach_relation_memory_if_needed(self) -> None:
        async def _run() -> dict:
            with patch.object(rm, "fetch_relation_memory", return_value=_FAKE_RELATIONS):
                return await rm.attach_relation_memory_if_needed(
                    {"content": "init"},
                    prompt="quelles sont mes relations avec les PNJ ?",
                    lab=True,
                    player="Teome",
                )

        res = asyncio.run(_run())
        self.assertEqual(res.get("source"), "relation_memory")
        self.assertIn("Jax Moro", str(res.get("content")))
        self.assertTrue(res.get("relation_memory", {}).get("ok"))
        self.assertEqual(res.get("relation_memory", {}).get("entries_count"), 3)

    def test_character_layer_grounding_integration(self) -> None:
        with patch.object(rm, "fetch_relation_memory", return_value=_FAKE_RELATIONS):
            block = cl.format_character_block(lab=True, prompt="discutons du monde")
            self.assertIn("[Mémoire relationnelle in-game", block)
            self.assertIn("Jax Moro", block)


if __name__ == "__main__":
    unittest.main()
