"""Tests — Self + écosystème grounding Compagnon."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_OVERLAY = Path(__file__).resolve().parents[1]
if str(_OVERLAY) not in sys.path:
    sys.path.insert(0, str(_OVERLAY))

import companion_self_grounding as self_g  # noqa: E402
import ecosystem_grounding as eco  # noqa: E402


class EcosystemGroundingTests(unittest.TestCase):
    def test_wants_on_mmo_246_memory(self) -> None:
        text = (
            "le MMO dans lequel tu pourras t'incarner, hébergé sur .246, "
            "renforce ta mémoire et ta conscience de l'écosystème lbg"
        )
        self.assertTrue(eco.wants_ecosystem_context(text))
        block = eco.format_ecosystem_grounding()
        self.assertIn("192.168.0.246", block)
        self.assertIn("8787", block)
        self.assertIn("Lia", block)
        self.assertIn("pas la RAM", block)
        self.assertNotIn(":8792", block)

    def test_no_false_positive_plain_hello(self) -> None:
        self.assertFalse(eco.wants_ecosystem_context("bonjour, comment ça va ?"))


class SelfGroundingTests(unittest.TestCase):
    def test_wants_self_memory(self) -> None:
        self.assertTrue(self_g.wants_self_memory_context("renforce ta mémoire agent"))
        self.assertTrue(self_g.wants_self_memory_context("quelle est ta conscience ?"))
        self.assertFalse(self_g.wants_self_memory_context("ouvre notepad"))

    def test_format_self_full_and_compact(self) -> None:
        payload = {
            "enabled": True,
            "state": {
                "identity": {
                    "display_name": "Cortex",
                    "mode": "studio",
                    "incarnations": {"studio": "lyra", "mmo": "lia"},
                },
                "drives": {"curiosity": 0.75, "tension": 0.0, "social_hunger": 1.0},
                "intent": {"primary": "monitor", "narrative": "veille"},
                "memory_refs": {"lessons_count": 12, "last_lesson_id": "les_abc"},
                "pending_will": [{"id": "w1"}],
                "goals_active_count": 1,
            },
        }
        full = self_g.format_self_grounding(payload)
        self.assertIn("SELF", full)
        self.assertIn("lyra", full)
        self.assertIn("lia", full)
        self.assertIn("12 leçons", full)
        self.assertIn("≠ RAM VM", full)
        compact = self_g.format_self_grounding(payload, compact=True)
        self.assertIn("SELF Cortex", compact)
        self.assertLess(len(compact), 120)

    def test_format_empty(self) -> None:
        self.assertEqual(self_g.format_self_grounding(None), "")
        self.assertEqual(self_g.format_self_grounding({}), "")

    def test_goals_count_filters_done(self) -> None:
        payload = {
            "enabled": True,
            "state": {
                "identity": {"display_name": "Cortex", "mode": "studio"},
                "drives": {"curiosity": 0.5},
                "intent": {"primary": "monitor"},
                "memory_refs": {"lessons_count": 1},
                "pending_will": [],
                "goals": [
                    {"id": "g1", "status": "active"},
                    {"id": "g2", "status": "done"},
                    {"id": "g3", "status": "expired"},
                ],
            },
        }
        full = self_g.format_self_grounding(payload)
        self.assertIn("buts actifs : 1", full)
        self.assertNotIn("buts actifs : 3", full)


if __name__ == "__main__":
    unittest.main()
