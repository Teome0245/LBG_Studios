"""Super-Agent Event Filter & Task Router (Pentiminax architecture canon).

Garantit :
1. Séparation stricte : Routeur d'interaction humaine vs Workers spécialisés étanches.
2. Contextes isolés : Chaque worker ne reçoit que son sous-ensemble de données, sans fuite de mémoire globale.
3. Filtrage déterministe par code : Validation dure des événements système/session avant toute soumission au LLM.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class WorkerDomain(str, Enum):
    """Domaines de workers étanches."""
    CODE = "code"          # Ex: Cline, OpenCode, exécution de scripts / tests
    GAME = "game"          # Ex: Godot Headless, simulation MMO, navigation
    STUDIO = "studio"      # Ex: Lyra, documentation, orchestration, dialogue
    OPS = "ops"            # Ex: Déploiement LAN, monitoring, santé machines


class EventPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


# Patterns interdits dans les payloads transmis au modèle (sécurité & hygiène contexte)
FORBIDDEN_SECRET_PATTERNS = [
    re.compile(r"(?:api[_-]?key|bearer|token|secret|password|passwd|pwd)[\s:=]+([a-zA-Z0-9_\-\.]{12,})", re.IGNORECASE),
    re.compile(r"-----BEGIN [A-Z ]+ PRIVATE KEY-----"),
    re.compile(r"(?:ssh-rsa|ssh-ed25519) [A-Za-z0-9+/=]+"),
]


@dataclass(frozen=True)
class FilteredSessionEvent:
    """Événement assaini et typé par le code déterministe."""
    v: int
    event: str
    session_id: str
    agent: str
    domain: WorkerDomain
    priority: EventPriority
    summary: str
    clean_detail: dict[str, Any]
    approval_id: str | None = None
    requires_human_approval: bool = False


@dataclass
class WorkerContext:
    """Contexte étanche pour un worker donné."""
    domain: WorkerDomain
    worker_id: str
    max_history_items: int = 20
    history: list[dict[str, Any]] = field(default_factory=list)

    def append_event(self, event: FilteredSessionEvent) -> None:
        """Ajoute l'événement assaini en mémoire locale sans déborder."""
        self.history.append({
            "event": event.event,
            "agent": event.agent,
            "summary": event.summary,
            "priority": event.priority.value,
        })
        if len(self.history) > self.max_history_items:
            self.history.pop(0)

    def get_isolated_prompt_context(self) -> list[dict[str, Any]]:
        """Retourne la vue mémoire pure du worker, sans interférence d'autres domaines."""
        return list(self.history)


class SuperAgentRouter:
    """Routeur principal assurant la médiation humaine et la distribution étanche."""

    def __init__(self) -> None:
        self._workers: dict[WorkerDomain, WorkerContext] = {
            domain: WorkerContext(domain=domain, worker_id=f"worker_{domain.value}")
            for domain in WorkerDomain
        }

    def sanitize_text(self, text: str, max_chars: int = 140) -> str:
        """Tronque et masque les chaînes de caractères sensibles."""
        if not text:
            return ""
        clean = text.strip()
        for pat in FORBIDDEN_SECRET_PATTERNS:
            clean = pat.sub("[REDACTED_SECRET]", clean)
        return clean[:max_chars]

    def filter_and_route_event(self, raw_event: dict[str, Any]) -> FilteredSessionEvent | None:
        """Filtre un événement brut de session par des règles de code déterministe.

        Rejette les événements mal formés ou non autorisés.
        Assainit le résumé et masque les fuites potentielles.
        """
        if not isinstance(raw_event, dict):
            return None

        event_type = str(raw_event.get("event", "")).strip()
        if not event_type:
            return None

        agent_name = str(raw_event.get("agent", "unknown")).lower().strip()
        session_id = str(raw_event.get("session_id", "anon")).strip()

        # 1. Détermination déterministe du domaine worker
        if any(kw in agent_name for kw in ("cline", "opencode", "coder", "syntax")):
            domain = WorkerDomain.CODE
        elif any(kw in agent_name for kw in ("godot", "hub", "prime", "mmo")):
            domain = WorkerDomain.GAME
        elif any(kw in agent_name for kw in ("ops", "deploy", "infra", "smoke")):
            domain = WorkerDomain.OPS
        else:
            domain = WorkerDomain.STUDIO

        # 2. Détermination de la priorité et du besoin d'approbation humaine
        approval_id = raw_event.get("approval_id")
        requires_approval = bool(approval_id) or event_type in (
            "session.approval_needed",
            "session.ask_human",
            "task.destructive_action",
        )

        priority = EventPriority.NORMAL
        if requires_approval or "error" in event_type or "critical" in event_type:
            priority = EventPriority.CRITICAL
        elif "warn" in event_type or "alert" in event_type:
            priority = EventPriority.HIGH
        elif "metric" in event_type or "ping" in event_type:
            priority = EventPriority.LOW

        # 3. Filtrage & nettoyage des métadonnées
        raw_summary = str(raw_event.get("summary") or raw_event.get("message") or event_type)
        clean_summary = self.sanitize_text(raw_summary, max_chars=120)

        # Assainir le detail dict
        raw_detail = raw_event.get("detail")
        clean_detail: dict[str, Any] = {}
        if isinstance(raw_detail, dict):
            for k, v in raw_detail.items():
                if isinstance(v, str):
                    clean_detail[k] = self.sanitize_text(v, max_chars=250)
                elif isinstance(v, (int, float, bool)):
                    clean_detail[k] = v

        filtered = FilteredSessionEvent(
            v=int(raw_event.get("v", 1)),
            event=event_type,
            session_id=session_id,
            agent=agent_name,
            domain=domain,
            priority=priority,
            summary=clean_summary,
            clean_detail=clean_detail,
            approval_id=str(approval_id) if approval_id else None,
            requires_human_approval=requires_approval,
        )

        # 4. Dispatch dans le contexte hermétique du worker ciblé
        worker = self._workers[domain]
        worker.append_event(filtered)

        return filtered

    def get_worker_context(self, domain: WorkerDomain) -> list[dict[str, Any]]:
        """Accès sécurisé à l'historique étanche d'un worker."""
        return self._workers[domain].get_isolated_prompt_context()

    def get_team_status(self) -> dict[str, Any]:
        """Retourne la synthèse de l'état de chaque worker pour l'UI Compagnon."""
        team = {}
        for domain, ctx in self._workers.items():
            last_ev = ctx.history[-1] if ctx.history else None
            team[domain.value] = {
                "worker_id": ctx.worker_id,
                "domain": domain.value,
                "active_items": len(ctx.history),
                "last_event": last_ev.get("event") if last_ev else "idle",
                "last_agent": last_ev.get("agent") if last_ev else "none",
                "last_summary": last_ev.get("summary") if last_ev else "en attente",
                "priority": last_ev.get("priority") if last_ev else "low",
            }
        return team
