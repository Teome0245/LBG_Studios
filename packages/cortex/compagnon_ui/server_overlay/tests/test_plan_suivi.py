"""Tests — plan_suivi (intent compte rendu)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_OVERLAY = Path(__file__).resolve().parents[1]
if str(_OVERLAY) not in sys.path:
    sys.path.insert(0, str(_OVERLAY))

import plan_suivi as ps  # noqa: E402


class PlanSuiviTests(unittest.TestCase):
    def test_wants(self) -> None:
        self.assertTrue(ps.wants_plan_suivi("où en est le plan d'évolutions ?"))
        self.assertTrue(ps.wants_plan_suivi("suivi du plan"))
        self.assertTrue(ps.wants_plan_suivi("quels tickets bloqués ?"))
        self.assertTrue(ps.wants_plan_suivi("sujets bloquants du plan"))
        self.assertTrue(ps.wants_plan_suivi("compte rendu du plan"))
        self.assertFalse(ps.wants_plan_suivi("bonjour"))
        self.assertFalse(ps.wants_plan_suivi("teste présence Nix"))


if __name__ == "__main__":
    unittest.main()
