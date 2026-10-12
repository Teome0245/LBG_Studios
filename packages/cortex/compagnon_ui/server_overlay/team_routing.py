"""Décision de routage Orch UI → Cortex Pilot (Team Campus, .140).

D6 : « campus » / Lyra en causerie conceptuelle → chat LLM, pas Team live.
"""

from __future__ import annotations

import re
from typing import Any

_TEAM_PREFIX_RE = re.compile(r"^\s*(?:team|mission|campus)\s*:\s*(.+)$", re.IGNORECASE | re.DOTALL)

_MENTION_RE = re.compile(r"(?:^|[^\w@])@([a-zA-Z0-9_-]+)")

_TEAM_HANDLES = frozenset(
    {
        "themis",
        "argus",
        "hephaistos",
        "dedale",
        "vulcan",
        "iris",
        "hermes",
        "pygmalion",
        "choeur",
        "lia",
        "nix",
        "mira",
        "superviseur",
        "dialogue",
        "devops",
        "forge",
        "audit",
        "lyra",
    }
)

_TEAM_INTENTS = frozenset(
    {
        "devops_request",
        "system_action",
        "agent_action",
    }
)

# Pas de « campus » nu — trop fréquent en causerie (« c'est quoi le campus »)
_TEAM_TERMS = (
    "campus:",
    "status campus",
    "campus status",
    "mission campus",
    "campus mission",
    "mission:",
    "team:",
    "smoke lan",
    "smoke infra",
    "proxmox",
    "deploy",
    "déploy",
    "deploie",
    "spawn",
    "argus",
    "iris",
    "dédale",
    "dedale",
    "selfcheck",
    "devops_probe",
    "healthz",
)


def strip_team_prefix(prompt: str) -> tuple[str, bool]:
    """Retire un préfixe explicite ``team:`` / ``mission:`` / ``campus:``."""
    m = _TEAM_PREFIX_RE.match(prompt or "")
    if not m:
        return (prompt or "").strip(), False
    return m.group(1).strip(), True


def extract_team_mentions(prompt: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for m in _MENTION_RE.finditer(prompt or ""):
        handle = m.group(1).lower()
        if handle in _TEAM_HANDLES and handle not in seen:
            seen.add(handle)
            found.append(handle)
    return found


def has_team_mention(prompt: str) -> bool:
    return bool(extract_team_mentions(prompt))


def _is_studio_causerie(prompt: str) -> bool:
    try:
        from src.services.chat_intent import is_companion_chat, wants_sticky_causerie
    except ImportError:
        try:
            from chat_intent import is_companion_chat, wants_sticky_causerie  # type: ignore
        except ImportError:
            return False
    return bool(is_companion_chat(prompt) or wants_sticky_causerie(prompt))


def should_route_to_team(*, prompt: str, intent_v2: dict[str, Any], enabled: bool) -> bool:
    if not enabled:
        return False

    try:
        from src.services.multi_block_dispatch import is_numbered_multi_block

        if is_numbered_multi_block(prompt):
            return False
    except Exception:
        pass

    text, forced = strip_team_prefix(prompt)
    if forced and text:
        # Préfixe team: + chat identité → laisser le LLM (reflection le gère aussi)
        if _is_studio_causerie(text):
            return False
        return True
    if has_team_mention(prompt):
        return True
    # Causerie conceptuelle (campus / rôles / avis) → pas de Team live
    if _is_studio_causerie(prompt):
        return False
    intent = str(intent_v2.get("intent") or "")
    conf = float(intent_v2.get("confidence") or 0.0)
    if intent in _TEAM_INTENTS and conf >= 0.55:
        return True
    low = (prompt or "").lower()
    if any(term in low for term in _TEAM_TERMS) and intent not in ("conversation", "lyra_request"):
        return True
    return False
