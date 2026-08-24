"""Réexport voix LBG-IA (orchestrateur → agents)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_agents_voice = Path(__file__).resolve().parents[2] / "agents" / "src" / "lbg_agents" / "lbg_ia_voice.py"
_spec = importlib.util.spec_from_file_location("lbg_ia_voice_standalone", _agents_voice)
assert _spec and _spec.loader
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

apply_voice_to_agent_output = _mod.apply_voice_to_agent_output
try_greeting_response = _mod.try_greeting_response

__all__ = ["apply_voice_to_agent_output", "try_greeting_response"]
