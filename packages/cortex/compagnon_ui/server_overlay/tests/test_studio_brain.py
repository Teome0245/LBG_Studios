"""Tests A3 — Studio Brain court."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_OVERLAY = Path(__file__).resolve().parents[1]
if str(_OVERLAY) not in sys.path:
    sys.path.insert(0, str(_OVERLAY))

import studio_brain as sb  # noqa: E402


class StudioBrainTests(unittest.TestCase):
    def setUp(self) -> None:
        sb._cache = None
        sb._cache_mtime = None

    def tearDown(self) -> None:
        sb._cache = None
        sb._cache_mtime = None
        os.environ.pop("LBG_STUDIO_BRAIN", None)
        os.environ.pop("LBG_STUDIO_BRAIN_PATH", None)

    def test_pack_loads_and_has_budget(self) -> None:
        pack = sb.load_pack()
        self.assertTrue(pack, "pack studio_brain_v1 introuvable")
        self.assertEqual(pack.get("id"), "studio_brain_v1")
        self.assertLessEqual(int(pack.get("max_chars") or 4000), 4000)
        self.assertGreaterEqual(len(pack.get("facts") or []), 4)
        self.assertGreaterEqual(len(pack.get("lessons") or []), 1)
        self.assertLessEqual(len(pack.get("lessons") or []), 8)
        self.assertEqual(pack.get("character_pack"), "compagnon_v1")

    def test_format_contains_facts_and_lessons(self) -> None:
        block = sb.format_studio_brain_block()
        self.assertIn("Studio Brain", block)
        self.assertIn("8787", block)
        self.assertIn("compagnon_v1", block)
        self.assertIn("Leçons", block)
        self.assertLessEqual(len(block), 4200)

    def test_disabled_returns_empty(self) -> None:
        os.environ["LBG_STUDIO_BRAIN"] = "0"
        self.assertEqual(sb.format_studio_brain_block(), "")

    def test_truncation_marker(self) -> None:
        fat = {
            "id": "studio_brain_fat",
            "character_pack": "compagnon_v1",
            "max_chars": 200,
            "facts": ["X" * 80 for _ in range(20)],
            "lessons": [{"id": "l%d" % i, "summary": "Y" * 40} for i in range(5)],
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
            json.dump(fat, fh)
            path = fh.name
        try:
            os.environ["LBG_STUDIO_BRAIN_PATH"] = path
            sb._cache = None
            sb._cache_mtime = None
            block = sb.format_studio_brain_block(max_chars=200)
            self.assertIn("tronqué", block)
            self.assertLessEqual(len(block), 220)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_domain_pack_loads_and_formats(self) -> None:
        mmo_pack = sb.load_domain_pack("mmo_prime")
        self.assertTrue(mmo_pack, "pack domain mmo_prime introuvable")
        self.assertEqual(mmo_pack.get("id"), "domain_mmo_prime")
        self.assertIn("prime-hub", str(mmo_pack.get("facts")))

        block = sb.format_studio_brain_block(domain="mmo_prime")
        self.assertIn("Silo O2 MMO Prime", block)
        self.assertIn("8787", block)

    def test_enabled_default(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("LBG_STUDIO_BRAIN", None)
            self.assertTrue(sb.studio_brain_enabled())


if __name__ == "__main__":
    unittest.main()
