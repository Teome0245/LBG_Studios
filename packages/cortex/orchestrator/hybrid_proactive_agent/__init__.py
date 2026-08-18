"""Stub local minimal de hybrid_proactive_agent pour dev/tests orchestrator."""

from .engine import ActionKind, HybridProactiveEngine, ProactiveAction, ProactiveState
from .memory import LongTermMemoryStore, MemoryEntry


def integration_hints(state: ProactiveState, context: dict[str, object] | None = None) -> dict[str, object]:
    return {
        "hybrid_proactive_mode": state.mode,
        "tension": round(float(state.tension), 3),
        "curiosite": round(float(state.curiosite), 3),
        "session_id": (context or {}).get("session_id"),
        "stub": True,
    }
