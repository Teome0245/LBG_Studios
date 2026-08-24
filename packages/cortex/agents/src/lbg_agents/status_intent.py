"""Détection des questions « où en est-on ? » — routage factuel sans LLM."""

from __future__ import annotations

import re

# Intents servis par des handlers déterministes (jamais remplacés par le LLM intent).
FACTUAL_STATUS_INTENTS = frozenset(
    {
        "infographiste_status",
        "sprites_status",
        "godot_status",
        "team_status",
        "infra_status",
        "project_status",
    }
)

_STATUS_QUERY_RE = re.compile(
    r"(?:"
    r"où\s+(?:en|on)\s+(?:est|êtes|es-t-on)|"
    r"ou\s+en\s+est|"
    r"on\s+en\s+est\s+où|"
    r"quel\s+(?:est\s+)?(?:le\s+)?(?:statut|état|avancement)|"
    r"point\s+(?:sur|d['\u2019])?|"
    r"où\s+en\s+sommes|"
    r"update\s+sur|"
    r"état\s+(?:du|de\s+la|des)|"
    r"etat\s+(?:du|de\s+la|des)|"
    r"avancement\s+(?:du|de\s+la|des)|"
    r"progression\s+(?:du|de\s+la|des)|"
    r"où\s+(?:en|on)\s+(?:va|vont)|"
    r"compte\s+rendu|"
    r"actions?\s+en\s+cours|"
    r"que\s+(?:font|fait|se\s+passe)|"
    r"qu['\u2019]est-ce\s+qui\s+(?:tourne|avance|se\s+passe)"
    r")",
    re.IGNORECASE,
)

_DOMAIN_INFOGRAPHISTE_RE = re.compile(
    r"\b("
    r"lora|lo\s*ra|kohya|infographiste|pygmalion|"
    r"tri(?:age)?\s+d(?:es?)?\s*images?|classif\w*\s+images?|"
    r"styles_sorted|mmorpg_insp|unclassified|inspiration\s+mmorpg|"
    r"entra[îi]nement\s+lora|train(?:ing)?\s+lora|buckets?"
    r")\b",
    re.IGNORECASE,
)

_DOMAIN_SPRITES_RE = re.compile(
    r"\b(sprites?\s*2d|prime_sprite|sprites_2d|player_official|prime\s+client\s+sprites?)\b",
    re.IGNORECASE,
)

_DOMAIN_GODOT_RE = re.compile(
    r"\b("
    r"godot|zb-?0|zb-?1|zone\s*bridge|lbg-?ws|sidecar|soe|"
    r"scrapaltai|minimap|m9[abc]?|prime\s+client|core3|lbg_gateway|"
    r"godot-client|parallel-prime"
    r")\b",
    re.IGNORECASE,
)

_DOMAIN_INFRA_RE = re.compile(
    r"\b("
    r"devops|infra(?:structure)?|smoke|ollama|systemd|healthz|"
    r"orchestrat(?:eur|or)|backend|vm\s*140|stockage|"
    r"réseau|reseau|selfcheck|timer|service\s+lbg|déploiement|deploiement"
    r")\b",
    re.IGNORECASE,
)

_DOMAIN_TEAM_RE = re.compile(
    r"\b("
    r"équipe|equipe|team|team\s+virtuelle|tâches?\s+team|actor\s*system|"
    r"pygmalion\s+(?:team|équipe)|#/team|fil\s+team|campus|conductor|"
    r"agents?\s+(?:virtuel|studio)|fil\s+d(?:e\s+)?attente|"
    r"tâches?\s+(?:en\s+cours|actives?)"
    r")\b",
    re.IGNORECASE,
)

_DOMAIN_PM_RE = re.compile(
    r"\b("
    r"chef\s+de\s+projet|product\s+owner|plan\s+de\s+route|roadmap|"
    r"jalon|milestone|vision\s+produit|projet\s+lbg|étape\s+actuelle|etape\s+actuelle"
    r")\b",
    re.IGNORECASE,
)


def is_operational_status_query(text: str) -> bool:
    """Question opérationnelle (pas du jeu de rôle pur)."""
    t = (text or "").strip()
    if not t:
        return False
    if _STATUS_QUERY_RE.search(t):
        return True
    tl = t.lower()
    if re.search(r"\b(statut|état|etat|avancement)\b", tl) and (
        _DOMAIN_INFOGRAPHISTE_RE.search(tl)
        or _DOMAIN_SPRITES_RE.search(tl)
        or _DOMAIN_GODOT_RE.search(tl)
        or _DOMAIN_INFRA_RE.search(tl)
        or _DOMAIN_TEAM_RE.search(tl)
        or _DOMAIN_PM_RE.search(tl)
    ):
        return True
    return False


def is_factual_status_intent(intent: str) -> bool:
    return intent in FACTUAL_STATUS_INTENTS


def classify_status_intent(text: str) -> tuple[str, float]:
    """Retourne (intent, confidence) ou ('unknown', 0.0)."""
    t = (text or "").strip()
    if not t:
        return ("unknown", 0.0)

    operational = is_operational_status_query(t)
    has_domain = bool(
        _DOMAIN_INFOGRAPHISTE_RE.search(t)
        or _DOMAIN_SPRITES_RE.search(t)
        or _DOMAIN_GODOT_RE.search(t)
        or _DOMAIN_INFRA_RE.search(t)
        or _DOMAIN_TEAM_RE.search(t)
        or _DOMAIN_PM_RE.search(t)
    )
    if not operational and not has_domain:
        return ("unknown", 0.0)

    tl = t.lower()
    if _DOMAIN_INFOGRAPHISTE_RE.search(tl):
        return ("infographiste_status", 0.92)
    if _DOMAIN_SPRITES_RE.search(tl):
        return ("sprites_status", 0.9)
    if _DOMAIN_GODOT_RE.search(tl):
        return ("godot_status", 0.9)
    if _DOMAIN_INFRA_RE.search(tl):
        return ("infra_status", 0.88)
    if _DOMAIN_TEAM_RE.search(tl) and not _DOMAIN_INFOGRAPHISTE_RE.search(tl):
        return ("team_status", 0.88)
    if _DOMAIN_PM_RE.search(tl) or operational:
        return ("project_status", 0.82 if operational else 0.75)
    return ("unknown", 0.0)
