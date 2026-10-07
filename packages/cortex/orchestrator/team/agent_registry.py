"""Registre central des agents studio — introspection (declarations JSON)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


def _declarations_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "agents" / "declarations"


@lru_cache(maxsize=1)
def load_agent_declarations() -> list[dict[str, Any]]:
    root = _declarations_dir()
    if not root.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data.setdefault("_source_file", path.name)
                out.append(data)
        except (OSError, json.JSONDecodeError):
            continue
    return out


def agent_by_id(agent_id: str) -> dict[str, Any] | None:
    for decl in load_agent_declarations():
        if str(decl.get("agent_id") or "") == agent_id:
            return decl
    return None


def agents_for_role(role: str) -> list[dict[str, Any]]:
    return [d for d in load_agent_declarations() if str(d.get("role") or "") == role]


def list_agents_summary() -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for decl in load_agent_declarations():
        mmo_play = decl.get("mmo_play") if isinstance(decl.get("mmo_play"), dict) else {}
        row: dict[str, Any] = {
            "agent_id": decl.get("agent_id"),
            "display_name": decl.get("display_name"),
            "role": decl.get("role"),
            "persona": decl.get("persona"),
            "subproject": decl.get("subproject"),
            "account_login": decl.get("account_login") or decl.get("persona"),
            "mmo_player": decl.get("mmo_player"),
            "studio_member": decl.get("studio_member"),
            "linked_studio_agent_id": decl.get("linked_studio_agent_id"),
            "linked_studio_display": decl.get("linked_studio_display"),
            "capabilities": [
                c.get("id") if isinstance(c, dict) else c
                for c in (decl.get("capabilities") or [])
            ],
            "owner_timer": decl.get("owner_timer"),
        }
        if mmo_play:
            # Lien doux Studio → compte/perso IG (ne remplace pas le login persona Studio)
            row["mmo_account_login"] = mmo_play.get("account_login")
            row["mmo_player"] = mmo_play.get("mmo_player") or row.get("mmo_player")
            row["bridge_agent_id"] = mmo_play.get("bridge_agent_id")
        summary.append(row)
    return summary
