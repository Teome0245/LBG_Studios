from __future__ import annotations

from enum import Enum
from typing import Any

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
    # Causes de tension (signaux réels) — pour status / UI
    tension_causes: list[str] = Field(default_factory=list)


class ProactiveAction(BaseModel):
    kind: ActionKind = ActionKind.observe
    mode: str = "proactif_leger"
    message: str = "Observation légère."
    cause: str | None = None


class HybridProactiveEngine:
    """Tension = max(pression signaux, plafond silence).

    Le silence seul ne dépasse plus ~0.45 — d’où les toasts « tension »
    absurdes sans vrai problème. Disque / AD / orch poussent réellement.
    """

    # Silence : 2 h → ~0.45 (jamais toast « élevé » seul)
    SILENCE_TENSION_CAP = 0.45
    SILENCE_SECONDS_FOR_CAP = 7200.0

    def __init__(self) -> None:
        self.state = ProactiveState()

    def reset(self) -> None:
        self.state = ProactiveState()

    def observe_user_turn(self, text: str, decide_ctx: dict[str, object] | None = None) -> None:
        self.state.silence_seconds_est = 0.0
        self.state.curiosite = min(1.0, max(0.0, self.state.curiosite + 0.05))
        # Léger bump conversation — pas de mode autonome
        if text and len(text) > 20:
            self.state.tension = min(0.4, max(0.0, self.state.tension + 0.02))
        if decide_ctx:
            self.apply_signals(decide_ctx)

    def tick_silence(self, dt: float) -> None:
        dt = max(0.0, float(dt or 0.0))
        self.state.silence_seconds_est += dt
        self.state.curiosite = min(1.0, self.state.curiosite + min(0.15, dt / 1800.0))
        # Ne plus empiler la tension au plafond 1.0 sur le silence seul
        silence_t = min(
            self.SILENCE_TENSION_CAP,
            self.state.silence_seconds_est / self.SILENCE_SECONDS_FOR_CAP * self.SILENCE_TENSION_CAP,
        )
        if silence_t > self.state.tension:
            self.state.tension = silence_t
        self._refresh_mode()

    def apply_signals(self, signals: dict[str, Any] | None) -> list[str]:
        """Recalcule tension depuis signaux infra/disk. Retourne les causes actives."""
        signals = signals if isinstance(signals, dict) else {}
        causes: list[str] = []
        pressure = 0.0

        silence_t = min(
            self.SILENCE_TENSION_CAP,
            float(self.state.silence_seconds_est or 0.0)
            / self.SILENCE_SECONDS_FOR_CAP
            * self.SILENCE_TENSION_CAP,
        )
        if silence_t >= 0.3:
            causes.append("silence")
            pressure = max(pressure, silence_t)

        disk = signals.get("disk_root_used_pct")
        if isinstance(disk, (int, float)):
            if disk >= 90:
                causes.append(f"disk_critical:{int(disk)}")
                pressure = max(pressure, 0.95)
            elif disk >= 80:
                causes.append(f"disk_high:{int(disk)}")
                pressure = max(pressure, 0.82)

        if (
            signals.get("desktop_agent_down")
            or signals.get("ad_agent_down")
            or (signals.get("desktop_agent_reachable") is False and signals.get("ad_agent_reachable") is False)
        ):
            causes.append("desktop_agent_down")
            pressure = max(pressure, 0.70)

        if signals.get("orchestrator_reachable") is False:
            causes.append("orch_down")
            pressure = max(pressure, 0.9)

        if signals.get("mmo_sidecar_reachable") is False:
            causes.append("mmo_down")
            pressure = max(pressure, 0.7)

        pending = signals.get("jobs_waiting_approval")
        if isinstance(pending, (int, float)) and pending >= 1:
            causes.append(f"jobs_l2:{int(pending)}")
            pressure = max(pressure, min(0.8, 0.55 + 0.1 * float(pending)))

        self.state.tension = max(0.0, min(1.0, pressure))
        self.state.tension_causes = causes
        self._refresh_mode()
        return causes

    def _refresh_mode(self) -> None:
        if self.state.tension >= 0.75:
            self.state.mode = "autonome"
        elif self.state.tension >= 0.45:
            self.state.mode = "proactif_avance"
        else:
            self.state.mode = "proactif_leger"

    def cooldown_decay(self) -> None:
        self.state.tension = max(0.0, self.state.tension - 0.15)
        self.state.curiosite = max(0.0, self.state.curiosite - 0.08)
        if self.state.tension_causes and self.state.tension < 0.5:
            # Les causes restent jusqu’au prochain apply_signals
            pass
        self._refresh_mode()

    def decide(self, decide_ctx: dict[str, object] | None = None) -> ProactiveAction:
        if decide_ctx:
            self.apply_signals(decide_ctx)
        causes = list(self.state.tension_causes or [])
        primary = causes[0] if causes else None

        if self.state.mode == "autonome":
            msg = self._message_for_causes(causes, level="autonome")
            return ProactiveAction(
                kind=ActionKind.autonomous_nudge,
                mode=self.state.mode,
                message=msg,
                cause=primary,
            )
        if self.state.tension >= 0.45 or self.state.curiosite >= 0.6:
            msg = self._message_for_causes(causes, level="plan")
            return ProactiveAction(
                kind=ActionKind.plan,
                mode=self.state.mode,
                message=msg,
                cause=primary,
            )
        return ProactiveAction(
            kind=ActionKind.observe,
            mode=self.state.mode,
            message="Observation légère, aucun déclenchement autonome.",
            cause=None,
        )

    @staticmethod
    def _message_for_causes(causes: list[str], *, level: str) -> str:
        joined = " ".join(causes)
        if any(c.startswith("disk_") for c in causes):
            pct = ""
            for c in causes:
                if c.startswith("disk_"):
                    pct = c.split(":")[-1] if ":" in c else ""
                    break
            if level == "autonome":
                return (
                    f"Disque root à {pct}% — selfcheck L1 puis remédiation "
                    "remontée en L2 (Pilot Jobs, pas de purge auto)."
                )
            return f"Disque root à {pct}% — plan selfcheck + escalade L2 conseillé."
        if "desktop_agent_down" in causes or "ad_agent_down" in causes:
            return "Agent desktop injoignable — sonde L1 (dry-run)."
        if "orch_down" in causes:
            return "Orchestrateur Cortex injoignable — sonde health."
        if any(c.startswith("jobs_l2") for c in causes):
            return "Jobs L2 en attente — revue Pilot Jobs conseillée."
        if "silence" in joined:
            return (
                "Silence prolongé (aucune alerte infra) — "
                "je propose une action concrète : mails récents, selfcheck LAN ou revue Pilot Jobs L2."
            )
        if level == "autonome":
            return "Tension signalée — proposition d’action autonome read-only."
        return "Plan léger conseillé pour clarifier l’objectif."
