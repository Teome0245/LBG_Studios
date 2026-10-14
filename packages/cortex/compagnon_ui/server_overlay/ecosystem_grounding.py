"""Ancrage écosystème LBG — REGISTRE-lite pour le chat Compagnon.

Faits stables (hosts / surfaces) — pas de sonde live (Héphaïstos reste sur Agir).
"""

from __future__ import annotations

import re

_ECOSYSTEM_HINTS = re.compile(
    r"(?i)("
    r"\béco[- ]?syst[eè]me\b|\becosysteme\b|"
    r"\bmmo\b|\bprime\b|\bprecu\b|\bpre-cu\b|"
    r"\b246\b|\.246\b|192\.168\.0\.246|"
    r"\.245\b|192\.168\.0\.245|"
    r"\.140\b|192\.168\.0\.140|"
    r"\.100\b|192\.168\.0\.100|"
    r"\bsidecar\b|\bcore3\b|"
    r"\bincarner\b|\bincarnation\b|\bt['\u2019]incarner\b|"
    r"\blia\b|\blyra\b|"
    r"\bregistre\b|\blost\s+heaven\b|\bscrapaltai\b|"
    r"\bgateway\b|\b8792\b|\b8791\b|"
    r"\bpilot\b|\bcompagnon\b|\bstudio\s+lbg\b"
    r")"
)

# Snapshot aligné docs/REGISTRE.md — tenir à jour si adressage change.
_ECOSYSTEM_FACTS = """\
ÉCOSYSTÈME LBG (REGISTRE-lite — ne pas inventer hors de cette liste) :
- Compagnon (présence chat) : http://192.168.0.100:5174/ · API Orch :3000
- Pilot / Cortex (ops, Team, Self) : http://192.168.0.140:8080/ · orch :8010
- Prime monde MMO (écriture) : 192.168.0.246:8787 (prime-hub HTTP+WS) — Core3 / hub_runtime Python = OFF joueur
- PreCU (référence lecture seule) : 192.168.0.245 — ne pas modifier
- LLM local : heavy .110:11434 · light .111:11434 (LAB — pas Groq)
- Incarnations : studio = Lyra/Compagnon · MMO = Lia (Rang 2 persona)
- Mémoire à renforcer côté MMO = Self / leçons / session_summary — pas la RAM des VM
- Source monorepo : LBG_Studios (cortex = O1 Studio · prime-client = O2 Jeu)"""


def wants_ecosystem_context(prompt: str) -> bool:
    return bool(_ECOSYSTEM_HINTS.search(prompt or ""))


def format_ecosystem_grounding() -> str:
    return _ECOSYSTEM_FACTS.strip()
