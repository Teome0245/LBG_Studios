"""Domaines contextuels de connaissances Gladys (Silos ciblés LBG Studios).

Permet de charger uniquement les faits et leçons d'un domaine précis
(compagnon, mmo_prime, infra_lan, showcase_web) afin d'éviter la surcharge de contexte
et d'économiser les tokens de l'orchestrateur et des agents.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DOMAINS_DIR = Path(__file__).resolve().parent
KNOWN_DOMAINS = ("compagnon", "mmo_prime", "infra_lan", "showcase_web")


def list_domains() -> list[str]:
    """Retourne la liste des identifiants de domaines disponibles."""
    res: list[str] = []
    for p in DOMAINS_DIR.glob("*.json"):
        res.append(p.stem)
    return sorted(res) or list(KNOWN_DOMAINS)


def load_domain(domain_id: str) -> dict[str, Any] | None:
    """Charge le dictionnaire de connaissances d'un domaine donné."""
    clean_id = domain_id.strip().lower()
    path = DOMAINS_DIR / f"{clean_id}.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def format_domain_block(domain_id: str, *, max_chars: int = 2000) -> str:
    """Formate un bloc de prompt concis pour le domaine ciblé."""
    data = load_domain(domain_id)
    if not data:
        return ""
    name = data.get("name") or domain_id
    lines: list[str] = [
        f"[Silo Connaissances Gladys — Domaine : {name}]",
        "Faits clés :",
    ]
    for fact in data.get("facts") or []:
        lines.append(f"- {str(fact).strip()}")
    lessons = data.get("lessons") or []
    if lessons:
        lines.append("Leçons retenues :")
        for les in lessons:
            if isinstance(les, dict):
                lid = les.get("id") or ""
                summary = les.get("summary") or ""
                prefix = f"{lid} — " if lid else ""
                lines.append(f"- {prefix}{summary}")
            else:
                lines.append(f"- {str(les).strip()}")
    full = "\n".join(lines).strip()
    if len(full) <= max_chars:
        return full
    return full[: max_chars - 40].rstrip() + "\n… [silo tronqué — budget]"
