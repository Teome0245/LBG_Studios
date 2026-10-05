"""
Marqueurs OpenClaw / auto-réparation / auto-évolution — source unique.

D6 combo : ne plus matcher « évoluer / évolution » en substring nue
(« tu te sens prêt à faire évoluer ça » ne doit PAS spawn OpenClaw).
"""

from __future__ import annotations

import re

# Phrases intentionnelles seulement (pas « évoluer » nu dans une causerie)
_OPENCLAW_SIGNAL_RE = re.compile(
    r"(?i)("
    r"\bopenclaw\b|"
    r"\blance\s+openclaw\b|"
    r"\bauto[\s-]?r[ée]paration\b|"
    r"\bauto[\s-]?[ée]volution\b|"
    r"\br[ée]pare\s+(?:le|la|les|ce|cette|mon|ma)\b|"
    r"\b[ée]volue\s+(?:le|la|les|ce|cette|le\s+module|le\s+code|le\s+service)\b|"
    r"\bfais\s+[ée]voluer\s+(?:le|la|les|ce|cette)\s+(?:code|module|service|runtime)\b|"
    r"\brepair\b|"
    r"\bevolve\s+(?:the|this|our)\b"
    r")"
)

# Causerie / confirmation humaine → jamais OpenClaw
_CAUSERIE_BLOCK_RE = re.compile(
    r"(?i)("
    r"\bdiscut|"
    r"\bcoll[eè]gues?|"
    r"\bton\s+avis|"
    r"\bpr[êe]t\s+(?:pour|à|a)\s+(?:m['\u2019]?aider|aider)|"
    r"\bm['\u2019]?aider\s+[àa]\s+faire\s+[ée]volu|"
    r"\bque\s+penses?|"
    r"\blyra\b|"
    r"\binventes?"
    r")"
)

OPENCLAW_SIGNAL_SUBSTRINGS: tuple[str, ...] = (
    "openclaw",
    "auto-réparation",
    "auto-reparation",
    "auto-évolution",
    "auto-evolution",
    "lance openclaw",
)


def prompt_has_openclaw_substrings(text: str) -> bool:
    body = text or ""
    if not body.strip():
        return False
    if _CAUSERIE_BLOCK_RE.search(body):
        return False
    if _OPENCLAW_SIGNAL_RE.search(body):
        return True
    low = body.lower()
    return any(s in low for s in OPENCLAW_SIGNAL_SUBSTRINGS)


OPENCLAW_REPAIR_INSTRUCTION_MARKERS: tuple[str, ...] = (
    "répare",
    "repare",
    "réparation",
    "reparation",
    "auto-réparation",
    "auto-reparation",
    "repair",
    "fix",
    "corrige",
    "bug",
    "openclaw",
)

OPENCLAW_EVOLUTION_INSTRUCTION_MARKERS: tuple[str, ...] = (
    "auto-évolution",
    "auto-evolution",
    "évolue le",
    "evolue le",
    "fais évoluer le",
    "fais evoluer le",
    "evolve the",
)


def classify_openclaw_instruction_mode(instruction: str) -> str | None:
    """``repair`` / ``evolution`` si marqueur plan Brain, sinon ``None``."""
    instruction_l = (instruction or "").lower()
    if any(m in instruction_l for m in OPENCLAW_REPAIR_INSTRUCTION_MARKERS):
        return "repair"
    if any(m in instruction_l for m in OPENCLAW_EVOLUTION_INSTRUCTION_MARKERS):
        return "evolution"
    if _OPENCLAW_SIGNAL_RE.search(instruction or ""):
        if re.search(r"(?i)r[ée]par|repair|fix|bug", instruction or ""):
            return "repair"
        return "evolution"
    return None
