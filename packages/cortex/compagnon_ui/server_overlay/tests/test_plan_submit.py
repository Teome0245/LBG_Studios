"""Tests — plan_submit (D6.5 livraison Team)."""

from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

_OVERLAY = Path(__file__).resolve().parents[1]
if str(_OVERLAY) not in sys.path:
    sys.path.insert(0, str(_OVERLAY))

for mod in (
    "src",
    "src.http_timeouts",
    "src.settings",
    "src.services",
    "src.services.team_proxy",
    "src.services.campus_recall",
    "src.services.team_actions",
    "src.services.chat_intent",
):
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()

# chat_intent réel depuis overlay
import chat_intent as ci  # noqa: E402

sys.modules["src.services.chat_intent"] = ci

import plan_submit as ps  # noqa: E402


_PLAN_MD = """## Objectif
Transposer la présence studio en zone d'entraînement MMORPG.

## Phases
1. D6.5 greeting — done quand smoke V9 vert — Compagnon
2. Dials présence hub — done quand smoke 30 s — Iris
3. Boucle Compagnon↔hub — done quand brief mandate — Hermès

## Prochaine action concrète
Déployer A1/A3 et rejouer le fil humain.
"""


class PlanSubmitTests(unittest.TestCase):
    def test_wants_submit_on_soumettre(self) -> None:
        self.assertTrue(
            ps.wants_team_plan_submit(
                "prépare le plan d'action pour le soumettre au studio et commence"
            )
        )
        # Formulation naturelle du smoke humain (sans le verbe « soumettre »)
        self.assertTrue(
            ps.wants_team_plan_submit(
                "Prépare le plan d'action présence → zone d'entraînement MMORPG "
                "pour le studio"
            )
        )
        self.assertFalse(ps.wants_team_plan_submit("prépare juste un plan sans rien"))
        self.assertFalse(ps.wants_team_plan_submit("bonjour ça va ?"))
        # « pour le studio » seul (pas de plan) → pas de spawn
        self.assertFalse(ps.wants_team_plan_submit("discutons pour le studio"))

    def test_wants_submit_go_ahead_sticky(self) -> None:
        ctx = [
            {
                "role": "user",
                "content": "prépare le plan et soumets-le au studio",
            },
            {"role": "assistant", "content": "…"},
        ]
        self.assertTrue(ps.wants_team_plan_submit("allons y", ctx))
        self.assertFalse(ps.wants_team_plan_submit("allons y", None))

    def test_looks_like_plan(self) -> None:
        self.assertTrue(ps.looks_like_plan_content(_PLAN_MD))
        self.assertFalse(
            ps.looks_like_plan_content("Je peux structurer ce plan d'action pour le studio.")
        )
        self.assertFalse(ps.looks_like_plan_content("Allons-y. Je te suis."))

    def test_build_objective_mentions_hermes(self) -> None:
        obj = ps.build_mission_objective("soumets au studio", _PLAN_MD)
        self.assertIn("Hermès", obj)
        self.assertIn("PLAN COMPAGNON", obj)
        self.assertIn("Objectif", obj)

    def test_attach_spawns_mission(self) -> None:
        fake_data = {
            "ok": True,
            "mission": {"id": "m-plan-1", "objective": "x", "status": "open"},
            "created": [{"task_id": "t1", "role": "hermes"}],
            "act": {},
        }

        async def _run() -> dict:
            with patch.dict(
                "os.environ",
                {"LBG_COMPAGNON_PLAN_SUBMIT": "1"},
            ):
                with patch.object(
                    ps,
                    "submit_plan_mission",
                    new=AsyncMock(return_value=fake_data),
                ):
                    with patch(
                        "src.services.team_proxy._format_campus_mission",
                        return_value="**Mission Campus lancée**\n- **mission_id** : `m-plan-1`",
                    ):
                        with patch(
                            "src.services.campus_recall.campus_snapshot_from_mission_data",
                            return_value={
                                "mission_id": "m-plan-1",
                                "task_ids": ["t1"],
                            },
                        ):
                            with patch(
                                "src.services.team_actions.fetch_tasks_by_ids",
                                new=AsyncMock(return_value=[]),
                            ):
                                with patch(
                                    "src.services.team_actions.approval_payload_from_tasks",
                                    return_value=None,
                                ):
                                    return await ps.attach_team_plan_if_needed(
                                        {"content": _PLAN_MD, "response": _PLAN_MD},
                                        prompt=(
                                            "prépare le plan d'action pour le "
                                            "soumettre au studio"
                                        ),
                                        lab=True,
                                    )

        out = asyncio.run(_run())
        self.assertTrue(out.get("plan_submit", {}).get("ok"))
        self.assertEqual(out["plan_submit"]["mission_id"], "m-plan-1")
        self.assertIn("Mission Campus", out["content"])
        self.assertIn(_PLAN_MD.split("\n", 1)[0], out["content"])

    def test_attach_skips_without_submit_intent(self) -> None:
        async def _run() -> dict:
            with patch.dict("os.environ", {"LBG_COMPAGNON_PLAN_SUBMIT": "1"}):
                return await ps.attach_team_plan_if_needed(
                    {"content": _PLAN_MD},
                    prompt="donne-moi juste ton avis sur O1",
                    lab=True,
                )

        out = asyncio.run(_run())
        self.assertIsNone(out.get("plan_submit"))
        self.assertEqual(out["content"], _PLAN_MD)


if __name__ == "__main__":
    unittest.main()
