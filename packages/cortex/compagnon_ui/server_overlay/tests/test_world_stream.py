"""Tests — world_stream (Plan 3.1 Live World Stream Hub → Compagnon)."""

from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_OVERLAY = Path(__file__).resolve().parents[1]
if str(_OVERLAY) not in sys.path:
    sys.path.insert(0, str(_OVERLAY))

import router_prompts as rp  # noqa: E402
import world_stream as ws  # noqa: E402

_FAKE_STREAM = {
    "ok": True,
    "seq": 3,
    "count": 3,
    "events": [
        {
            "v": 1,
            "seq": 1,
            "kind": "event.activate",
            "text": "Chute de conteneurs de ferraille signalée près des portes !",
            "actor": "Monde",
            "zone": "scrapaltai",
            "detail": {"event_id": "lh_scrap_fall_convoy"},
            "ts": 1791800000.0,
        },
        {
            "v": 1,
            "seq": 2,
            "kind": "companion.escort",
            "text": "Nix a escorté Teome près du hub.",
            "actor": "Nix",
            "zone": "scrapaltai",
            "detail": {"human": "Teome"},
            "ts": 1791800100.0,
        },
        {
            "v": 1,
            "seq": 3,
            "kind": "world.boss_defeated",
            "text": "Un boss a été abattu : Goliath des sables.",
            "actor": "Teome",
            "zone": "scrapaltai",
            "detail": {"beast_id": "boss_goliath"},
            "ts": 1791800200.0,
        },
    ],
    "source": "prime_hub",
}


class WorldStreamTests(unittest.TestCase):
    def setUp(self) -> None:
        try:
            import world_notif_prefs as wnp

            wnp._STATE = dict(wnp._DEFAULTS)
        except Exception:
            pass

    def test_wants_world_stream(self) -> None:
        self.assertTrue(ws.wants_world_stream("quoi de neuf en jeu ?"))
        self.assertTrue(ws.wants_world_stream("qu'est-ce qui se passe à Lost Heaven ?"))
        self.assertTrue(ws.wants_world_stream("événements du monde"))
        self.assertTrue(ws.wants_world_stream("live world stream"))
        self.assertTrue(ws.wants_world_stream("nouvelles du hub"))
        self.assertFalse(ws.wants_world_stream("bonjour"))
        self.assertFalse(ws.wants_world_stream("fais le café"))

    def test_latest_world_highlight_priority(self) -> None:
        best = ws.latest_world_highlight(_FAKE_STREAM, max_age_s=99999999)
        self.assertIsNotNone(best)
        self.assertEqual(best.get("kind"), "world.boss_defeated")
        self.assertIn("Goliath", str(best.get("text")))

    def test_format_world_greeting(self) -> None:
        best = ws.latest_world_highlight(_FAKE_STREAM, max_age_s=99999999)
        greet = ws.format_world_greeting(best, player="Teome")
        self.assertIsNotNone(greet)
        self.assertIn("Goliath", greet)
        self.assertIn("écoute", greet.lower())
        self.assertIn("Lost Heaven", greet)

    def test_format_world_context_block(self) -> None:
        with patch.object(ws, "fetch_world_stream", return_value=_FAKE_STREAM):
            block = ws.format_world_context_block(limit=2)
            self.assertIn("[Derniers événements monde Lost Heaven", block)
            self.assertIn("Goliath", block)
            self.assertIn("Nix a escorté", block)

    def test_format_world_stream_report(self) -> None:
        report = ws.format_world_stream_report(_FAKE_STREAM)
        self.assertIn("faits marquants", report)
        self.assertIn("Goliath", report)
        self.assertIn("Nix a escorté", report)
        self.assertIn("Chute de conteneurs", report)
        self.assertIn("écoute", report.lower())

    def test_short_social_reply_integration(self) -> None:
        # 1. Quand le world stream fournit un event marquant
        with patch.object(ws, "fetch_world_stream", return_value=_FAKE_STREAM):
            with patch.object(
                ws,
                "latest_world_highlight",
                return_value=_FAKE_STREAM["events"][2],
            ):
                reply = rp.short_social_reply("Bonjour")
                self.assertIsNotNone(reply)
                self.assertIn("Goliath", reply)
                self.assertIn("écoute", reply.lower())

        # 2. Quand aucun event n'est disponible (fallback gracieux)
        with patch.object(ws, "latest_world_highlight", return_value=None):
            reply_fallback = rp.short_social_reply("Bonjour")
            self.assertEqual(
                reply_fallback,
                "Salut — ça va de mon côté. Je t'écoute, collègue studio.",
            )

    def test_attach_world_stream_if_needed(self) -> None:
        async def _run() -> dict:
            with patch.object(ws, "fetch_world_stream", return_value=_FAKE_STREAM):
                return await ws.attach_world_stream_if_needed(
                    {"content": "init"},
                    prompt="quoi de neuf en jeu ?",
                    lab=True,
                )

        res = asyncio.run(_run())
        self.assertEqual(res.get("source"), "world_stream")
        self.assertIn("faits marquants", str(res.get("content")))
        self.assertIn("Goliath", str(res.get("content")))
        self.assertTrue(res.get("world_stream", {}).get("ok"))


if __name__ == "__main__":
    unittest.main()
