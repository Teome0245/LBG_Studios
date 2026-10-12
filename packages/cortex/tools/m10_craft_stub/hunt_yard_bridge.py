"""Pont legacy m10_craft_stub → moteur `lbg_agents.hunt_yard`."""

from __future__ import annotations

import sys
from pathlib import Path

_AGENTS = Path(__file__).resolve().parents[2] / "agents" / "src"
if str(_AGENTS) not in sys.path:
    sys.path.insert(0, str(_AGENTS))

from lbg_agents.hunt_yard import (  # noqa: E402
    session_reset,
    session_run,
    session_snapshot,
    session_tick,
)

__all__ = ["session_reset", "session_run", "session_snapshot", "session_tick"]
