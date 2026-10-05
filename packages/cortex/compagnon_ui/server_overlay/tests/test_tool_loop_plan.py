"""Tests — tool_loop plan_tools (overlay)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

_OVERLAY = Path(__file__).resolve().parents[1]
if str(_OVERLAY) not in sys.path:
    sys.path.insert(0, str(_OVERLAY))

for mod in ("src", "src.http_timeouts", "src.settings", "src.services", "src.services.team_proxy"):
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()

import tool_loop as tl  # noqa: E402


class PlanToolsTests(unittest.TestCase):
    def test_studio_audit_prefers_team(self) -> None:
        tools = tl.plan_tools("audit Team, studio — état actuel")
        self.assertIn("team_status", tools)
        self.assertNotIn("ollama_audit", tools)

    def test_ollama_audit_explicit(self) -> None:
        tools = tl.plan_tools("audit Ollama .110 .111")
        self.assertIn("ollama_audit", tools)

    def test_auto_audit_has_team(self) -> None:
        tools = tl.plan_tools("tu pourrais faire un auto audit ?")
        self.assertIn("team_status", tools)


if __name__ == "__main__":
    unittest.main()
