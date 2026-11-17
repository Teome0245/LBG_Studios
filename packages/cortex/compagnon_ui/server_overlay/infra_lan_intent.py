"""Heuristiques intent Infra LAN (disk/RAM/Proxmox) — sans dépendances Orch.

Sépare hôte (246 / Prime) des signaux ops, pour ne pas router un sujet MMO /
mémoire agent vers Héphaïstos Cockpit.
"""

from __future__ import annotations

import re

# Signaux ops / storage / Proxmox (forts) — suffisent seuls.
_INFRA_LAN_STRONG_RE = re.compile(
    r"(?i)("
    r"infra\s*lan|proxmox|disk|disque|stockage|local-lvm|"
    r"occupation|espace\s+disque|guest\s*metrics|\bdf\b|"
    r"hephaistos|watchdog\s+infra|thin\s*pool|"
    r"\bnas\b|\bsynology\b|\biscsi\b|\blun\b|\bbackup\b|"
    r"\bram\b|\bswap\b|mémoire\s+(?:vm|hôte|hote|serveur)|"
    r"memoire\s+(?:vm|hôte|hote|serveur)"
    r")"
)

# Ancres hôte — nécessitent un signal ops (sinon : localisation MMO / studio).
_INFRA_LAN_HOST_RE = re.compile(
    r"(?i)("
    r"\bprime\b|\b246\b|\.100\b|\.140\b|\.51\b|\.200\b|\.201\b|"
    r"192\.168\.0\.(?:51|100|140|200|201|246)"
    r")"
)

# Intent ops sur un hôte déjà ancré.
_INFRA_LAN_OPS_RE = re.compile(
    r"(?i)\b("
    r"disk|disque|stockage|ram|swap|charge|load|cpu|"
    r"occupation|espace|utilisation|usage|"
    r"proxmox|sond|supervis|surveill|watchdog|"
    r"état|etat|status|santé|sante|metrics?|"
    r"slack|alerte|notif|notification|cr\b|"
    r"point\s+sur|nettoie|prune|agrand"
    r")\b"
)

# Sujet produit / Self — exclut le brief infra sauf signal storage/RAM fort.
_AGENT_MEMORY_OR_MMO_PRODUCT_RE = re.compile(
    r"(?i)("
    r"\b(ta|ma|sa|notre)\s+(mémoire|memoire)\b|"
    r"\b(mémoire|memoire)\s+(agent|self|équipe|equipe|studio|conversation|leçons?|lessons)\b|"
    r"\b(conscience|écosystème|ecosysteme|ecosystème)\b|"
    r"\b(incarner|incarnation|t['\u2019]incarner)\b|"
    r"\bsession[_\s-]?summary\b|"
    r"\b(self[\s_-]?state|leçons?\s+apprises|lessons[_\s-]?learned)\b|"
    r"\bmmo\b.{0,100}\b(mémoire|memoire|conscience|incarner|incarnation)\b|"
    r"\b(mémoire|memoire|conscience).{0,100}\b(mmo|écosystème|ecosysteme|lbg)\b"
    r")"
)

_MISSION_RE = re.compile(
    r"(?i)\b(mission|propose|spawn|automatiser|planif|créer|creer)\b"
)
_INFRA_LAN_READONLY_RE = re.compile(
    r"(?i)\b("
    r"regard|montre|affiche|combien|occupation|espace|"
    r"utilisation|usage|statut|status|état|etat|check|voir"
    r")\b"
)
_INFRA_LAN_ACTION_RE = re.compile(
    r"(?i)\b("
    r"point\s+sur|surveill|supervis|sond|remediat|remédi|"
    r"alerte|attention|nettoie|prune|agrand|fix|mission|"
    r"spawn|propose|automatiser|planif"
    r")\b"
)


def is_agent_memory_or_mmo_product(text: str) -> bool:
    """True si la demande parle mémoire agent / conscience / incarnation MMO."""
    return bool(_AGENT_MEMORY_OR_MMO_PRODUCT_RE.search(text or ""))


def has_strong_infra_signal(text: str) -> bool:
    return bool(_INFRA_LAN_STRONG_RE.search(text or ""))


# Verbes de déploiement / provisionnement : ne doivent PAS être détournés vers le monitoring Héphaïstos
_PROVISION_OR_DEPLOY_RE = re.compile(
    r"(?i)\b(d[ée]ploy|mettre\s+en\s+(?:place|service)|install|cr[ée]er|provisionn)\b"
)


def wants_infra_lan_brief(text: str) -> bool:
    """True si la demande vise RAM/disk LAN / Proxmox (pas healthz générique).

    Mentionner Prime / .246 seuls (hébergement MMO) ne déclenche pas Héphaïstos.
    """
    body = text or ""
    if _PROVISION_OR_DEPLOY_RE.search(body):
        return False
    if is_agent_memory_or_mmo_product(body) and not has_strong_infra_signal(body):
        return False
    if has_strong_infra_signal(body):
        return True
    if _INFRA_LAN_HOST_RE.search(body) and _INFRA_LAN_OPS_RE.search(body):
        return True
    # « point sur » seul (historique) — seulement avec ancre hôte
    if re.search(r"(?i)point\s+sur", body) and _INFRA_LAN_HOST_RE.search(body):
        return True
    return False


def wants_infra_lan_mission(
    text: str,
    *,
    team_mentions: set[str] | frozenset[str] | list[str] | None = None,
    multi_role_campus: bool = False,
) -> bool:
    """Spawn Campus ops — pas une lecture seule disk/RAM."""
    if multi_role_campus:
        return False
    if not wants_infra_lan_brief(text):
        return False
    body = text or ""
    mentions = {str(m).lower() for m in (team_mentions or [])}
    if "hephaistos" in mentions:
        return True
    if _MISSION_RE.search(body):
        return True
    if _INFRA_LAN_ACTION_RE.search(body):
        return True
    if _INFRA_LAN_READONLY_RE.search(body):
        return False
    return False
