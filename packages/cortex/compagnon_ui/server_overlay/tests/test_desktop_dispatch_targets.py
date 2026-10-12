"""Tests — routage desktop portable-sds / pc (overlay)."""

from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace

_OVERLAY = Path(__file__).resolve().parents[1]
if str(_OVERLAY) not in sys.path:
    sys.path.insert(0, str(_OVERLAY))

# Stubs pour import hors venv Orch (httpx / settings)
sys.modules.setdefault("httpx", types.ModuleType("httpx"))
sys.modules["src.http_timeouts"] = SimpleNamespace(httpx_timeout=lambda **_k: None)
sys.modules["src.settings"] = SimpleNamespace(Settings=object)

import desktop_dispatch as dd  # noqa: E402


class DesktopDispatchTargets(unittest.TestCase):
    def test_infer_open_app_keeps_notepad(self) -> None:
        action = dd.infer_open_app_from_text("ouvre notepad sur PORTABLE-SDS")
        assert action is not None
        self.assertEqual(action["app"], "notepad")
        action_pp = dd.infer_open_app_from_text("ouvre notepad++ sur le portable")
        assert action_pp is not None
        self.assertEqual(action_pp["app"], "notepadpp")

    def test_infer_open_app_vqhd_typo(self) -> None:
        action = dd.infer_open_app_from_text("ouvre vqhd sur mon pc (.10)")
        assert action is not None
        self.assertEqual(action["app"], "vghd")

    def test_infer_portable_sds(self) -> None:
        self.assertEqual(
            dd.infer_desktop_target_id("tu peux ouvrir notepad sur PORTABLE-SDS"),
            "portable",
        )
        self.assertEqual(
            dd.infer_desktop_target_id("ouvre notepad sur le portable"),
            "portable",
        )
        self.assertIsNone(dd.infer_desktop_target_id("ouvre notepad"))

    def test_resolve_portable_fallback_lab(self) -> None:
        settings = SimpleNamespace(
            cortex_agent_desktop_url="",
            agent_windows_url="",
            httpx_agent_execute_read_s=30,
        )
        url, label, tid = dd.resolve_desktop_worker(
            "ouvre notepad sur PORTABLE-SDS",
            settings=settings,
        )
        self.assertEqual(tid, "portable")
        self.assertIn("192.168.0.77", url)
        self.assertIn("portable", label.lower())

    def test_resolve_default_pc(self) -> None:
        settings = SimpleNamespace(
            cortex_agent_desktop_url="http://192.168.0.10:5005",
            agent_windows_url="",
            httpx_agent_execute_read_s=30,
        )
        url, label, tid = dd.resolve_desktop_worker(
            "ouvre notepad sur mon pc",
            settings=settings,
        )
        self.assertEqual(tid, "pc")
        self.assertIn("192.168.0.10", url)


if __name__ == "__main__":
    unittest.main()
