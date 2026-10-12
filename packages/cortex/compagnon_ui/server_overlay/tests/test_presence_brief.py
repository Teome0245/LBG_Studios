"""Tests — presence_brief (Phase C1)."""

from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

_OVERLAY = Path(__file__).resolve().parents[1]
if str(_OVERLAY) not in sys.path:
    sys.path.insert(0, str(_OVERLAY))

import presence_brief as pb  # noqa: E402


class PresenceBriefTests(unittest.TestCase):
    def test_detect(self) -> None:
        self.assertTrue(pb.wants_presence_brief("teste présence Nix chaleur haute"))
        self.assertTrue(pb.wants_presence_brief("lance un smoke présence B3"))
        self.assertTrue(pb.wants_presence_brief("brief hub présence zone d'entraînement"))
        self.assertFalse(pb.wants_presence_brief("bonjour"))
        self.assertFalse(pb.wants_presence_brief("soumets le plan au studio"))
        # T5 rejeu — causerie design, PAS un mandat brief/smoke
        t5 = (
            "pour moi l'environnement jeu doit rester une zone d'entraînement "
            "des personas, pas un dump ops"
        )
        self.assertFalse(pb.wants_presence_brief(t5), t5)
        self.assertFalse(
            pb.wants_presence_brief(
                "On parle de la zone d'entraînement Lost Heaven et du feeling"
            )
        )

    def test_markdown_shape(self) -> None:
        md = pb.build_presence_brief_markdown("teste présence Lia")
        self.assertIn("Objectif", md)
        self.assertIn("Lia", md)
        self.assertIn("presence-dials", md)
        self.assertIn("smoke_b3b4", md)

    def test_attach_spawns_campus(self) -> None:
        fake_mission = {
            "ok": True,
            "mission": {"id": "m-pres"},
            "created": [{"task_id": "t1"}],
        }

        async def _fake_submit(*, objective: str, max_tasks: int = 4) -> dict:
            _ = objective, max_tasks
            return fake_mission

        async def _run() -> dict:
            with patch.dict("os.environ", {"LBG_COMPAGNON_PRESENCE_BRIEF": "1"}):
                # Forcer le chemin d'import local (pas src.services en unit test).
                import plan_submit as ps

                with patch.object(ps, "submit_plan_mission", new=_fake_submit):
                    # Simuler l'échec des helpers Pilot → bloc mission minimal
                    return await pb.attach_presence_brief_if_needed(
                        {"content": "x"},
                        prompt="teste présence Nix chaleur haute",
                        lab=True,
                    )

        out = asyncio.run(_run())
        self.assertTrue(out.get("presence_brief", {}).get("ok"))
        self.assertEqual(out["presence_brief"].get("persona"), "Nix")
        self.assertIn("Nix", out["content"])
        # Mission id si format helpers absents = encore dans presence_brief
        self.assertTrue(
            out.get("presence_brief", {}).get("mission_id") == "m-pres"
            or "Mission Campus" in out["content"]
            or "m-pres" in str(out.get("campus_meta") or {})
        )


if __name__ == "__main__":
    unittest.main()
