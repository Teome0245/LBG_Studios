"""Tests unitaires — world_notif_prefs (B1)."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

_OVERLAY = Path(__file__).resolve().parents[1]
if str(_OVERLAY) not in sys.path:
    sys.path.insert(0, str(_OVERLAY))

import world_notif_prefs as wnp  # noqa: E402


class WorldNotifPrefsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self._path = Path(self._tmpdir.name) / "prefs.json"
        os.environ["LBG_WORLD_NOTIF_PREFS_PATH"] = str(self._path)
        wnp._STATE = dict(wnp._DEFAULTS)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()
        os.environ.pop("LBG_WORLD_NOTIF_PREFS_PATH", None)
        wnp._STATE = dict(wnp._DEFAULTS)

    def test_defaults_all_on(self) -> None:
        p = wnp.load_prefs()
        self.assertTrue(p["world_marking"])
        self.assertTrue(p["companion_social"])
        self.assertTrue(p["ops_jobs"])

    def test_save_and_filter_world_marking(self) -> None:
        wnp.save_prefs({"world_marking": False})
        events = [
            {"kind": "boss_defeated", "text": "Boss tombé"},
            {"kind": "companion.escort", "text": "Nix escorte"},
            {"kind": "scrap_fall", "text": "Ferraille"},
        ]
        out = wnp.filter_events(events)
        kinds = [e["kind"] for e in out]
        self.assertNotIn("boss_defeated", kinds)
        self.assertNotIn("scrap_fall", kinds)
        self.assertIn("companion.escort", kinds)

    def test_filter_companion_social_off(self) -> None:
        wnp.save_prefs({"companion_social": False})
        events = [
            {"kind": "companion.escort", "text": "escort"},
            {"kind": "boss_defeated", "text": "boss"},
        ]
        out = wnp.filter_events(events)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "boss_defeated")

    def test_ops_jobs_not_in_world_stream_filter(self) -> None:
        """ops_jobs est réservé initiatives — ne filtre pas les events monde."""
        wnp.save_prefs({"ops_jobs": False, "world_marking": True})
        events = [{"kind": "boss_defeated", "text": "boss"}]
        out = wnp.filter_events(events)
        self.assertEqual(len(out), 1)

    def test_category_for_event(self) -> None:
        self.assertEqual(
            wnp.category_for_event({"kind": "companion.escort"}),
            "companion_social",
        )
        self.assertEqual(
            wnp.category_for_event({"kind": "event.activate.scrap_fall"}),
            "world_marking",
        )


if __name__ == "__main__":
    unittest.main()
