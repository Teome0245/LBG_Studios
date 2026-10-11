"""Garde-fous : plan autonomie ≠ plan lore Scrapaltai / handoff bureau."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_OVERLAY = Path(__file__).resolve().parents[1]
if str(_OVERLAY) not in sys.path:
    sys.path.insert(0, str(_OVERLAY))

import team_autonomy_plan as tap  # noqa: E402


USER_MSG_AUTONOMY = (
    "j'utilise Cursor pour developer ton backend, ta reflexion, bien que tu sois connecter "
    "sur un LLM, pour le moment c'est Cursor qui traite la majeur partie. il faudrait "
    "preparer un plan avec la Team pour pouvoir faire plus de choses sans soliciter Cursor. "
    "tu peux voir ce que tu peux faire dans ce sens ?"
)

USER_MSG_SCRAPALTAI = (
    "oui complétement, il faudrait voir la répartition des factions sur scrapaltai, "
    "permettre qu'elle évolu, et commencer à créer deux autres ville (POI) pour répartir "
    "des PNJ de chaque factions ? tu peux prepaprer un plan dan ce sens et le soumettre "
    "au bureau/Team ?"
)

USER_MSG_CORRECTION = (
    "Non, mauvais livrable. Prépare un plan game design Scrapaltai : (1) répartition "
    "actuelle des factions, (2) règles d’évolution, (3) 2 nouvelles villes/POI + répartition "
    "PNJ par faction. Soumets ce plan au studio/Team — pas un plan Cursor/LAN."
)


class TestTeamAutonomyPlan(unittest.TestCase):
    def test_wants_real_autonomy_plan(self) -> None:
        self.assertTrue(tap.wants_team_autonomy_plan(USER_MSG_AUTONOMY))
        self.assertTrue(
            tap.wants_team_autonomy_plan("préparer un plan avec la Team sans Cursor")
        )

    def test_rejects_scrapaltai_faction_plan(self) -> None:
        self.assertFalse(tap.wants_team_autonomy_plan(USER_MSG_SCRAPALTAI))

    def test_rejects_correction_after_bad_livrable(self) -> None:
        """« pas un plan Cursor/LAN » ne doit pas re-déclencher le plan figé."""
        self.assertFalse(tap.wants_team_autonomy_plan(USER_MSG_CORRECTION))

    def test_liste_agents_still_false(self) -> None:
        self.assertFalse(tap.wants_team_autonomy_plan("liste tes agents"))

    def test_format_has_phases(self) -> None:
        text = tap.format_team_autonomy_plan()
        self.assertIn("Phase A", text)
        self.assertIn("team:", text)
        self.assertIn("recolle", text.lower())


if __name__ == "__main__":
    unittest.main()
