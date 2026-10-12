"""Tests — presence_report (Phase C2)."""

from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_OVERLAY = Path(__file__).resolve().parents[1]
if str(_OVERLAY) not in sys.path:
    sys.path.insert(0, str(_OVERLAY))

import presence_report as pr  # noqa: E402


_FAKE = {
    "ok": True,
    "bots": [
        {
            "name": "Nix",
            "presence_dials": {"chaleur": 0.72, "initiative": 0.65},
            "presence_line": "Voyageur te salue franchement — chaleur haute.",
            "actions_at_m": {"12": {"action": "escort"}, "35": {"action": "ignore"}},
        },
        {
            "name": "Mira",
            "presence_dials": {"chaleur": 0.35, "initiative": 0.55},
            "presence_line": "Voyageur reste à distance, ton mesuré.",
            "actions_at_m": {"12": {"action": "greet"}},
        },
    ],
}


class PresenceReportTests(unittest.TestCase):
    def test_detect(self) -> None:
        self.assertTrue(pr.wants_presence_report("résultat smoke présence"))
        self.assertTrue(pr.wants_presence_report("retour terrain Lost Heaven"))
        self.assertTrue(pr.wants_presence_report("Nix vs Mira sur le hub"))
        self.assertFalse(pr.wants_presence_report("bonjour"))
        self.assertFalse(pr.wants_presence_report("teste présence Nix chaleur haute"))

    def test_format_causerie(self) -> None:
        text = pr.format_presence_causerie(_FAKE)
        self.assertIn("Nix", text)
        self.assertIn("Mira", text)
        self.assertIn("escort", text)
        self.assertNotIn("{", text)  # pas de dump JSON
        self.assertNotRegex(text, r"(?i)\bAgir\b")

    def test_attach(self) -> None:
        async def _run() -> dict:
            with patch.dict("os.environ", {"LBG_COMPAGNON_PRESENCE_REPORT": "1"}):
                with patch.object(pr, "fetch_presence_dials", return_value=_FAKE):
                    return await pr.attach_presence_report_if_needed(
                        {"content": "x"},
                        prompt="retour hub présence",
                        lab=True,
                    )

        out = asyncio.run(_run())
        self.assertEqual(out.get("source"), "presence_report")
        self.assertTrue(out.get("presence_report", {}).get("ok"))
        self.assertIn("escort", out["content"])


if __name__ == "__main__":
    unittest.main()
