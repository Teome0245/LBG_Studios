from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class ActionKind(str, Enum):
    autonomous_nudge = "autonomous_nudge"
    plan = "plan"
    observe = "observe"


class ProactiveState(BaseModel):
    mode: str = "proactif_leger"
    tension: float = 0.0
    curiosite: float = 0.0
    silence_seconds_est: float = 0.0


class ProactiveAction(BaseModel):
    kind: ActionKind = ActionKind.observe
    mode: str = "proactif_leger"
    message: str = "Observation légère."


class HybridProactiveEngine:
    def __init__(self) -> None:
        self.state = ProactiveState()

    def reset(self) -> None:
        self.state = ProactiveState()

    def observe_user_turn(self, text: str, decide_ctx: dict[str, object] | None = None) -> None:
        self.state.silence_seconds_est = 0.0
        self.state.curiosite = min(1.0, max(0.0, self.state.curiosite + 0.05))
        if text and len(text) > 20:
            self.state.tension = min(1.0, max(0.0, self.state.tension + 0.02))

    def tick_silence(self, dt: float) -> None:
        dt = max(0.0, float(dt or 0.0))
        self.state.silence_seconds_est += dt
        self.state.curiosite = min(1.0, self.state.curiosite + min(0.2, dt / 1200.0))
        self.state.tension = min(1.0, self.state.tension + min(0.15, dt / 1800.0))
        if self.state.tension >= 0.75:
            self.state.mode = "autonome"
        elif self.state.tension >= 0.45:
            self.state.mode = "proactif_avance"
        else:
            self.state.mode = "proactif_leger"

    def cooldown_decay(self) -> None:
        self.state.tension = max(0.0, self.state.tension - 0.15)
        self.state.curiosite = max(0.0, self.state.curiosite - 0.08)
        if self.state.tension < 0.45:
            self.state.mode = "proactif_leger"

    def decide(self, decide_ctx: dict[str, object] | None = None) -> ProactiveAction:
        if self.state.mode == "autonome":
            return ProactiveAction(
                kind=ActionKind.autonomous_nudge,
                mode=self.state.mode,
                message="Relance proactive : tension élevée, proposition d'action autonome.",
            )
        if self.state.tension >= 0.45 or self.state.curiosite >= 0.6:
            return ProactiveAction(
                kind=ActionKind.plan,
                mode=self.state.mode,
                message="Plan léger conseillé pour clarifier l'objectif.",
            )
        return ProactiveAction(
            kind=ActionKind.observe,
            mode=self.state.mode,
            message="Observation légère, aucun déclenchement autonome.",
        )
