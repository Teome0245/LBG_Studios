"""Tests — spontaneity (validation, feedback, évolution ; sans Ollama)."""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

_OVERLAY = Path(__file__).resolve().parents[1]
if str(_OVERLAY) not in sys.path:
    sys.path.insert(0, str(_OVERLAY))

import spontaneity as sp  # noqa: E402
import time  # noqa: E402


class SpontaneityTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        root = Path(self._tmpdir.name)
        self.state = root / "state.json"
        os.environ["LBG_SPONTANEITY_STATE_PATH"] = str(self.state)
        os.environ["LBG_SPONTANEITY_ENABLED"] = "1"
        sp.reset_state_for_tests()

    def tearDown(self) -> None:
        self._tmpdir.cleanup()
        for k in ("LBG_SPONTANEITY_STATE_PATH", "LBG_SPONTANEITY_ENABLED"):
            os.environ.pop(k, None)

    def test_spice_mode_hard_vs_soft(self) -> None:
        self.assertEqual(sp.spice_mode_for({"offerType": "garde", "kind": "x"}), "message_only")
        self.assertEqual(sp.spice_mode_for({"id": "studio:morning:2026-09-29"}), "message_only")
        self.assertEqual(sp.spice_mode_for({"id": "jobs:idle", "kind": "studio"}), "full")
        self.assertEqual(sp.spice_mode_for({"id": "self:curiosity", "kind": "self_drive"}), "full")

    def test_validate_rejects_forbidden(self) -> None:
        bad = sp._validate_proposal(
            {
                "message": "On wipe le disque server maintenant.",
                "intents": [{"id": "x", "label": "Wipe", "sourceText": "rm -rf /"}],
            },
            fallback={"intents": [{"id": "mail", "label": "Mails", "sourceText": "regarde mes mails récents"}]},
            mode="full",
        )
        self.assertIsNone(bad)

    def test_validate_message_only_keeps_intents(self) -> None:
        intents = [{"id": "morning_brief", "label": "Brief", "sourceText": "fais mon brief du matin"}]
        ok = sp._validate_proposal(
            {
                "message": "Le studio s'éveille — on compile le brief lecture seule ?",
                "themes": ["matin", "brief"],
                "intents": [{"id": "hack", "label": "Hack", "sourceText": "fais un truc bizarre"}],
            },
            fallback={"intents": intents},
            mode="message_only",
        )
        self.assertIsNotNone(ok)
        assert ok is not None
        self.assertEqual(ok["intents"][0]["id"], "morning_brief")
        self.assertIn("éveille", ok["message"])

    def test_feedback_evolves_themes_and_seeds(self) -> None:
        with patch.object(sp, "_push_will_to_self", return_value={"ok": True, "will_id": "evo:test"}):
            snap = sp.record_feedback(
                offer_id="self:curiosity",
                kind="accept",
                themes=["veille", "craft"],
                message="Et si on peaufinait le toast spontané ?",
                evolution_seed="Ajouter un dial spontanéité côté Character",
            )
        self.assertTrue(snap["ok"])
        self.assertGreaterEqual(float(snap["theme_scores"].get("veille") or 0), 1.0)
        texts = [s.get("text") for s in snap["evolution_seeds"]]
        self.assertTrue(any("dial spontanéité" in str(t) for t in texts))
        self.assertTrue(any(p.get("will_id") == "evo:test" for p in (snap.get("promoted") or [])))

        snap2 = sp.record_feedback(
            offer_id="self:curiosity",
            kind="dismiss",
            themes=["veille"],
            message="noop",
        )
        self.assertLess(float(snap2["theme_scores"].get("veille") or 0), float(snap["theme_scores"]["veille"]))

    def test_promote_skips_low_score(self) -> None:
        with sp._lock:
            st = sp.load_state()
            st["evolution_seeds"] = [{"text": "Idée trop faible pour promouvoir encore", "score": 0.2, "ts": time.time()}]
            sp.persist_state(st)
        with patch.object(sp, "_push_will_to_self") as push:
            out = sp.promote_ready_seeds()
            push.assert_not_called()
        self.assertEqual(out.get("promoted"), [])

    def test_propose_falls_back_without_llm(self) -> None:
        offer = {
            "offer": True,
            "id": "jobs:idle",
            "message": "Silence studio — une piste ?",
            "kind": "studio",
            "offerType": "opportunite",
            "intents": [
                {"id": "selfcheck", "label": "Selfcheck", "sourceText": "fais un diagnostic infra selfcheck LAN"}
            ],
        }

        async def _run() -> dict:
            with patch.object(sp, "_call_llm", new=AsyncMock(return_value=(None, 12.0, "error"))):
                return await sp.propose_spontaneous(offer)

        out = asyncio.run(_run())
        self.assertTrue(out["ok"])
        self.assertFalse(out["spontaneous"])
        self.assertEqual(out["message"], offer["message"])

    def test_propose_applies_llm(self) -> None:
        offer = {
            "offer": True,
            "id": "self:curiosity",
            "message": "Curiosité haute — Team L1 ?",
            "kind": "self_drive",
            "offerType": "studio",
            "intents": [
                {
                    "id": "team_l1_smoke",
                    "label": "Team L1 smoke",
                    "sourceText": "team smoke self companion",
                    "teamSpawn": True,
                }
            ],
        }
        llm = {
            "message": "Et si on inventait un toast qui surprend sans casser Agir ?",
            "themes": ["spontane", "toast"],
            "intents": [
                {
                    "id": "team_evo",
                    "label": "Team L1 idée",
                    "sourceText": "team micro evolution toast spontane",
                    "teamSpawn": True,
                    "teamObjective": "Proposer 1 micro-évolution toast spontané Compagnon (5 lignes).",
                }
            ],
            "evolution_seed": "Moteur spontané → seeds Character",
        }

        async def _run() -> dict:
            with patch.object(sp, "_call_llm", new=AsyncMock(return_value=(llm, 40.0, "ollama_light"))):
                return await sp.propose_spontaneous(offer)

        out = asyncio.run(_run())
        self.assertTrue(out["spontaneous"])
        self.assertIn("surprend", out["message"])
        self.assertEqual(out["intents"][0]["id"], "team_evo")
        self.assertTrue(self.state.is_file())


if __name__ == "__main__":
    unittest.main()
