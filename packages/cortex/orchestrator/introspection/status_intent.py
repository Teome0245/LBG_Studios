"""Réexport des patterns de statut factuel (sans charger tout le package agents)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_agents_status = Path(__file__).resolve().parents[2] / "agents" / "src" / "lbg_agents" / "status_intent.py"
_spec = importlib.util.spec_from_file_location("lbg_status_intent_standalone", _agents_status)
assert _spec and _spec.loader
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

FACTUAL_STATUS_INTENTS = _mod.FACTUAL_STATUS_INTENTS
classify_status_intent = _mod.classify_status_intent
is_factual_status_intent = _mod.is_factual_status_intent
is_operational_status_query = _mod.is_operational_status_query

__all__ = [
    "FACTUAL_STATUS_INTENTS",
    "classify_status_intent",
    "is_factual_status_intent",
    "is_operational_status_query",
]
