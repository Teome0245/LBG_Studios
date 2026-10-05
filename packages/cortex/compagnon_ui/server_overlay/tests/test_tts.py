"""Tests unitaires couche TTS proxy (sans réseau Edge/Piper)."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
OVERLAY = HERE.parent
if str(OVERLAY) not in sys.path:
    sys.path.insert(0, str(OVERLAY))

import tts as tts_mod  # noqa: E402


class TestSanitize(unittest.TestCase):
    def test_strip_markdown(self) -> None:
        s = tts_mod.sanitize_for_speech("Hello **world** `x` [a](http://b)\n```\nz\n``` end")
        self.assertNotIn("```", s)
        self.assertNotIn("http", s)
        self.assertIn("world", s)
        self.assertIn("a", s)

    def test_truncate(self) -> None:
        long = ("Mot. " * 200).strip()
        s = tts_mod.sanitize_for_speech(long, limit=100)
        self.assertLessEqual(len(s), 101)
        self.assertTrue(s.endswith("…") or s.endswith("."))


class TestFlags(unittest.TestCase):
    def test_enabled_default(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("LBG_TTS_ENABLED", None)
            self.assertTrue(tts_mod.tts_enabled())
        with mock.patch.dict(os.environ, {"LBG_TTS_ENABLED": "0"}):
            self.assertFalse(tts_mod.tts_enabled())

    def test_piper_url(self) -> None:
        with mock.patch.dict(os.environ, {"LBG_PIPER_URL": "http://192.168.0.111:8098/"}):
            self.assertEqual(tts_mod.piper_base_url(), "http://192.168.0.111:8098")

    def test_provider_default_edge(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("LBG_TTS_PROVIDER", None)
            self.assertEqual(tts_mod.tts_provider(), "edge")
            self.assertEqual(tts_mod.default_voice(), "fr-FR-DeniseNeural")

    def test_provider_piper_voice(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"LBG_TTS_PROVIDER": "piper", "LBG_PIPER_VOICE": "fr_FR-siwis-medium"},
        ):
            self.assertEqual(tts_mod.tts_provider(), "piper")
            self.assertEqual(tts_mod.default_voice(), "fr_FR-siwis-medium")


class TestSynthesizeDispatch(unittest.IsolatedAsyncioTestCase):
    async def test_edge_success(self) -> None:
        async def fake_edge(text: str, *, voice: str | None = None):
            return b"ID3fake", {
                "voice": voice or "fr-FR-DeniseNeural",
                "chars": "5",
                "content_type": "audio/mpeg",
                "provider": "edge",
            }

        with mock.patch.dict(os.environ, {"LBG_TTS_PROVIDER": "edge", "LBG_TTS_ENABLED": "1"}):
            with mock.patch.object(tts_mod, "synthesize_edge", side_effect=fake_edge):
                audio, meta = await tts_mod.synthesize("Salut")
        self.assertEqual(audio[:3], b"ID3")
        self.assertEqual(meta["provider"], "edge")

    async def test_edge_fallback_piper(self) -> None:
        async def boom(text: str, *, voice: str | None = None):
            raise RuntimeError("edge_tts_stream:offline")

        async def fake_piper(text: str, *, voice: str | None = None):
            return b"RIFFwav", {
                "voice": "fr_FR-siwis-medium",
                "chars": "5",
                "content_type": "audio/wav",
                "provider": "piper",
            }

        with mock.patch.dict(
            os.environ,
            {"LBG_TTS_PROVIDER": "edge", "LBG_TTS_FALLBACK": "piper", "LBG_TTS_ENABLED": "1"},
        ):
            with mock.patch.object(tts_mod, "synthesize_edge", side_effect=boom):
                with mock.patch.object(tts_mod, "synthesize_piper", side_effect=fake_piper):
                    audio, meta = await tts_mod.synthesize("Salut")
        self.assertEqual(audio[:4], b"RIFF")
        self.assertEqual(meta["provider"], "piper")
        self.assertEqual(meta.get("fallback_from"), "edge")

    async def test_edge_no_fallback_raises(self) -> None:
        async def boom(text: str, *, voice: str | None = None):
            raise RuntimeError("edge_down")

        with mock.patch.dict(
            os.environ,
            {"LBG_TTS_PROVIDER": "edge", "LBG_TTS_FALLBACK": "none", "LBG_TTS_ENABLED": "1"},
        ):
            with mock.patch.object(tts_mod, "synthesize_edge", side_effect=boom):
                with self.assertRaises(RuntimeError):
                    await tts_mod.synthesize("Salut")


if __name__ == "__main__":
    unittest.main()
