"""Tests — mission_watch_intent."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_OVERLAY = Path(__file__).resolve().parents[1]
if str(_OVERLAY) not in sys.path:
    sys.path.insert(0, str(_OVERLAY))

import mission_watch_intent as mw  # noqa: E402


class MissionWatchIntentTests(unittest.TestCase):
    def test_detect(self) -> None:
        self.assertTrue(
            mw.wants_mission_watch_notify(
                "nickel, tu peux me faire un retour quand la team a traité ce sujet ?"
            )
        )
        self.assertTrue(mw.wants_mission_watch_notify("préviens-moi à la clôture"))
        self.assertFalse(mw.wants_mission_watch_notify("bonjour"))

    def test_ack_no_agir(self) -> None:
        reply = mw.mission_watch_ack_reply()
        self.assertIn("humain", reply.lower())
        self.assertIn("pas une action agir", reply.lower())
        self.assertNotRegex(reply, r"(?i)\bdeploy_\*")


if __name__ == "__main__":
    unittest.main()
