"""Tests unitaires — character_layer (sans Orch runtime)."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Import direct du module overlay
_OVERLAY = Path(__file__).resolve().parents[1]
if str(_OVERLAY) not in sys.path:
    sys.path.insert(0, str(_OVERLAY))

import character_layer as cl  # noqa: E402


class CharacterLayerTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        root = Path(self._tmpdir.name)
        self.pack = root / "pack.json"
        self.dials = root / "dials.json"
        self.phrases = root / "catch.jsonl"
        # Use knowledge pack as base
        src = (
            Path(__file__).resolve().parents[3]
            / "knowledge"
            / "character"
            / "compagnon_v1.json"
        )
        if not src.is_file():
            src = _OVERLAY / "character" / "compagnon_v1.json"
        self.pack.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        os.environ["LBG_CHARACTER_PACK_PATH"] = str(self.pack)
        os.environ["LBG_CHARACTER_DIALS_PATH"] = str(self.dials)
        os.environ["LBG_CHARACTER_CATCHPHRASES_PATH"] = str(self.phrases)
        os.environ["LBG_CHARACTER_LAYER"] = "1"
        cl._pack_cache = None
        cl._pack_mtime = None

    def tearDown(self) -> None:
        self._tmpdir.cleanup()
        for k in (
            "LBG_CHARACTER_PACK_PATH",
            "LBG_CHARACTER_DIALS_PATH",
            "LBG_CHARACTER_CATCHPHRASES_PATH",
            "LBG_CHARACTER_LAYER",
        ):
            os.environ.pop(k, None)
        cl._pack_cache = None
        cl._pack_mtime = None

    def test_load_pack_and_defaults(self) -> None:
        pack = cl.load_pack(force=True)
        self.assertEqual(pack.get("id"), "compagnon_v1")
        d = cl.default_dials(pack)
        self.assertIn("piquant", d)
        self.assertGreaterEqual(d["politesse"], 0.5)

    def test_prod_caps_clamp_ego(self) -> None:
        d = cl.clamp_dials({"ego": 0.95, "piquant": 0.9}, lab=False)
        self.assertLessEqual(d["ego"], 0.55)
        self.assertLessEqual(d["piquant"], 0.5)

    def test_lab_allows_higher_ego(self) -> None:
        d = cl.clamp_dials({"ego": 0.7}, lab=True)
        self.assertGreaterEqual(d["ego"], 0.7)

    def test_format_block_contains_worldview(self) -> None:
        block = cl.format_character_block(lab=True, prompt="salut")
        self.assertIn("Caractère Compagnon", block)
        self.assertIn("Worldview", block)

    def test_format_block_fills_context_journal(self) -> None:
        journal: list = []
        block = cl.format_character_block(
            lab=True, prompt="salut", causerie=True, journal=journal
        )
        self.assertTrue(block)
        ids = [b.get("id") for b in journal]
        self.assertIn("character_pack", ids)
        self.assertIn("dials", ids)
        pack = next(b for b in journal if b["id"] == "character_pack")
        self.assertIn("compagnon", str(pack.get("summary") or "").lower())

    def test_ego_toaster_trigger(self) -> None:
        nudge = cl.ego_nudge_for_prompt("Tu n'es qu'un grille-pain")
        self.assertTrue(nudge)
        self.assertIn("fierté", nudge.lower())

    def test_reshape_blacklist(self) -> None:
        out = cl.reshape_blacklist("En tant qu'IA, je peux t'aider. Suite utile.")
        self.assertIsNotNone(out)
        self.assertNotIn("en tant qu'ia", out.lower())

    def test_catchphrase_remember(self) -> None:
        ok = cl.remember_catchphrase("On mesure, toujours.", tags=["ops"])
        self.assertTrue(ok)
        phrases = cl.list_catchphrases(limit=20)
        self.assertTrue(any("mesure" in p.lower() for p in phrases))

    def test_save_load_dials(self) -> None:
        saved = cl.save_dials({"humour": 0.6, "densite": 0.2}, lab=True)
        self.assertAlmostEqual(saved["humour"], 0.6)
        loaded = cl.load_dials(lab=True)
        self.assertAlmostEqual(loaded["humour"], 0.6)

    def test_voice_smoke_cases(self) -> None:
        cases = cl.voice_smoke_cases()
        self.assertGreaterEqual(len(cases), 8)
        ids = {c["id"] for c in cases}
        self.assertIn("V2_ego_toaster", ids)
        self.assertIn("V6_causerie_open", ids)
        self.assertIn("V7_causerie_continuity", ids)
        self.assertIn("V8_causerie_feedback", ids)
        self.assertIn("V9_greeting_presence", ids)
        self.assertIn("V10_plan_delivery", ids)
        self.assertIn("V11_presence_brief", ids)
        self.assertIn("V12_presence_report", ids)
        v7 = next(c for c in cases if c["id"] == "V7_causerie_continuity")
        self.assertEqual(v7.get("criterion"), "C1")


if __name__ == "__main__":
    unittest.main()
