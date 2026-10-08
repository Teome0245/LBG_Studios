"""D6.5 — Intent « retour quand la Team a traité » (sans Agir / dry-run)."""

from __future__ import annotations

import re

_MISSION_WATCH_RE = re.compile(
    r"(?i)\b("
    r"retour\s+quand|"
    r"pr[ée]viens?[-\s]?moi|"
    r"notifie[-\s]?moi|"
    r"ping(?:ue)?[-\s]?moi|"
    r"dis[- ]?moi\s+quand|"
    r"quand\s+(?:la\s+)?team\s+(?:a\s+|aura\s+)?(?:trait|fini|clos|termin)|"
    r"suivi\s+(?:de\s+la\s+)?mission|"
    r"watch\s+mission"
    r")\b"
)


def wants_mission_watch_notify(prompt: str) -> bool:
    text = (prompt or "").strip()
    if not text or len(text) > 280:
        return False
    return bool(_MISSION_WATCH_RE.search(text))


def mission_watch_ack_reply(prompt: str = "") -> str:
    """Réponse déterministe — l'humain qui demande = déjà validé pour le suivi."""
    _ = prompt
    return (
        "OK — je note le suivi. Tu es l'humain : cette demande vaut déjà "
        "pour un retour à la clôture (suivi lecture seule, pas une action Agir). "
        "Dès que la mission Campus est traitée ou plus ouverte, je te préviens "
        "ici (toast + message). Tu peux aussi suivre Pilot `#/team/office`."
    )
