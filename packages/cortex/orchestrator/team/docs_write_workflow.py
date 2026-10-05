"""Workflow docs_only — écriture / vérification markdown+JSON sous allowlist.

Utilisé par Chœur / Iris / Dédale / Thémis quand ``context.docs_only`` est vrai,
pour éviter la sonde Core3 (player_ia) ou les briefs vides.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from team.models import TeamTask

# Relatifs à packages/cortex (parents[2] depuis team/)
_DELIVERABLES_BY_TICKET: dict[str, list[str]] = {
    "C9_C2": [
        "docs/AGENT_SKILL_MMO.md",
        "content/world/relation_memory_schema.json",
    ],
    "C9": ["docs/AGENT_SKILL_MMO.md"],
    "C2": ["content/world/relation_memory_schema.json"],
    "C1": ["docs/design_c1_dialogue_suggestions.md"],
    "C4_C8": [
        "content/world/events/event_lh_scrap_fall_or_meute.json",
        "content/world/poi_lh_scrap_pile.json",
    ],
    "C4": ["content/world/events/event_lh_scrap_fall_or_meute.json"],
    "C8": ["content/world/poi_lh_scrap_pile.json"],
    "plan_72h": ["../../docs/PLAN_72H_CONCURRENTS.md"],
    "C3_C9": ["docs/AGENT_SKILL_MMO.md"],
}

_STUB_MARKDOWN: dict[str, str] = {
    "docs/AGENT_SKILL_MMO.md": (
        "# AGENT_SKILL_MMO — manuel joueurs IA (C9)\n\n"
        "**Date** : {stamp} · **Statut** : stub Team docs_only (Chœur)\n"
        "**Ticket** : BOITE_IDEES §14 C9\n\n"
        "> Stub auto — enrichir depuis CONCURRENTS_IA_MMO + Bible V40–V54.\n\n"
        "## 1. Rôle et personas\n\nÀ rédiger.\n"
    ),
    "docs/design_c1_dialogue_suggestions.md": (
        "# Design C1 — Suggestions dialogue hub\n\n"
        "**Date** : {stamp} · **Statut** : stub Team docs_only (Iris)\n"
        "**Ticket** : BOITE_IDEES §14 C1\n\n"
        "> Stub auto — design only, pas d'implémentation.\n\n"
        "## Objectif\n\n2–3 suggestions + texte libre.\n"
    ),
}

_STUB_JSON: dict[str, dict[str, Any]] = {
    "content/world/relation_memory_schema.json": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "lbg/world/relation_memory",
        "title": "Mémoire relations joueur ↔ PNJ (C2)",
        "description": "Stub Team docs_only — schéma C2.",
        "type": "object",
        "required": ["schema_version", "entries"],
        "properties": {
            "schema_version": {"type": "integer", "const": 1},
            "entries": {"type": "array", "items": {"type": "object"}},
        },
    },
    "content/world/events/event_lh_scrap_fall_or_meute.json": {
        "schema_version": 1,
        "id": "event:lh_scrap_fall_convoy",
        "title": "Chute de ferraille — stub docs_only",
        "status": "stub",
        "ticket": "C4",
    },
    "content/world/poi_lh_scrap_pile.json": {
        "schema_version": 1,
        "id": "poi:lh_scrap_pile",
        "title": "Pile scrap — stub docs_only",
        "status": "stub",
        "ticket": "C8",
    },
}


def _cortex_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _lbg_studios_root() -> Path:
    return Path(__file__).resolve().parents[4]


def resolve_docs_only(task: TeamTask) -> bool:
    ctx = task.context or {}
    if ctx.get("docs_only") is True or ctx.get("pm_write_docs") is True:
        return True
    if str(ctx.get("workflow") or "").strip().lower() in ("docs_only", "docs_write"):
        return True
    obj = (task.objective or "").lower()
    return bool(
        re.search(
            r"\b(docs?\s*only|rédiger?\s+(?:un\s+)?markdown|ecrire\s+(?:un\s+)?markdown|"
            r"écrire\s+(?:un\s+)?markdown|livrable\s*=\s*markdown)\b",
            obj,
            re.I,
        )
    )


def _ticket_key(task: TeamTask) -> str:
    ctx = task.context or {}
    raw = str(ctx.get("concurrents_ticket") or "").strip()
    if raw:
        return raw
    obj = (task.objective or "").lower()
    if "agent_skill" in obj or re.search(r"\bc9\b", obj):
        if re.search(r"\bc2\b", obj) or "mémoire" in obj or "memoire" in obj:
            return "C9_C2"
        return "C9"
    if re.search(r"\bc1\b", obj) or "suggestions dialogue" in obj:
        return "C1"
    if re.search(r"\bc4\b", obj) or re.search(r"\bc8\b", obj):
        return "C4_C8"
    if "72h" in obj or "72 h" in obj:
        return "plan_72h"
    return ""


def _paths_for_task(task: TeamTask) -> list[Path]:
    ticket = _ticket_key(task)
    rels = list(_DELIVERABLES_BY_TICKET.get(ticket) or [])
    ctx = task.context or {}
    extra = ctx.get("docs_paths") or ctx.get("deliverable_paths")
    if isinstance(extra, list):
        rels.extend(str(x).strip() for x in extra if str(x).strip())
    cortex = _cortex_root()
    studios = _lbg_studios_root()
    out: list[Path] = []
    for rel in rels:
        if rel.startswith("../../"):
            out.append((studios / rel[6:]).resolve())
        elif rel.startswith("docs/PLAN_") or rel.startswith("docs/FOCUS_"):
            # Docs racine LBG_Studios
            cand = studios / rel
            out.append(cand if cand.parent.name == "docs" else cortex / rel)
        else:
            out.append(cortex / rel)
    return out


def _auto_write_enabled(task: TeamTask) -> bool:
    ctx = task.context or {}
    if ctx.get("write_files") is False:
        return False
    if ctx.get("write_files") is True or ctx.get("pm_write_docs") is True:
        return True
    return os.environ.get("LBG_TEAM_DOCS_WRITE_ENABLED", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _rel_key(path: Path) -> str | None:
    cortex = _cortex_root()
    try:
        return str(path.resolve().relative_to(cortex)).replace("\\", "/")
    except ValueError:
        return None


def _ensure_file(path: Path, *, auto_write: bool) -> dict[str, Any]:
    out: dict[str, Any] = {"path": str(path), "ok": False, "written": False}
    if path.is_file() and path.stat().st_size > 0:
        out["ok"] = True
        out["already_present"] = True
        out["bytes"] = path.stat().st_size
        return out

    if not auto_write:
        out["error"] = "fichier absent"
        return out

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    rel = _rel_key(path) or ""
    path.parent.mkdir(parents=True, exist_ok=True)

    if rel in _STUB_MARKDOWN:
        path.write_text(_STUB_MARKDOWN[rel].format(stamp=stamp), encoding="utf-8")
    elif rel in _STUB_JSON:
        path.write_text(
            json.dumps(_STUB_JSON[rel], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    elif path.suffix.lower() == ".json":
        path.write_text(
            json.dumps(
                {"schema_version": 1, "status": "stub", "note": f"docs_only {stamp}"},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    else:
        path.write_text(
            f"# {path.stem.replace('_', ' ').title()}\n\n"
            f"**Date** : {stamp} · **Statut** : stub Team docs_only\n\n"
            f"> Stub auto — compléter.\n",
            encoding="utf-8",
        )
    out["ok"] = True
    out["written"] = True
    out["created_file"] = True
    return out


def execute_docs_only_workflow(task: TeamTask) -> dict[str, object]:
    """Vérifie / crée les livrables markdown|JSON — pas de sonde Core3."""
    auto_write = _auto_write_enabled(task)
    paths = _paths_for_task(task)
    ticket = _ticket_key(task)

    if not paths:
        # Fallback : au moins un artefact traçable sous docs/
        fallback = _cortex_root() / "docs" / f"_team_docs_only_{task.role}.md"
        paths = [fallback]

    results = [_ensure_file(p, auto_write=auto_write) for p in paths]
    ok = all(bool(r.get("ok")) for r in results)
    deliverables = [str(r["path"]) for r in results if r.get("ok")]
    written = [str(r["path"]) for r in results if r.get("written")]
    present = [str(r["path"]) for r in results if r.get("already_present")]

    summary_parts = [
        f"docs_only ticket={ticket or 'generic'} rôle={task.role}",
        f"{len(present)} déjà présents",
        f"{len(written)} écrits",
    ]
    if not ok:
        gaps = [str(r.get("path")) for r in results if not r.get("ok")]
        summary_parts.append(f"gaps: {', '.join(gaps[:4])}")

    return {
        "kind": "docs_only_write",
        "ok": ok,
        "docs_only": True,
        "ticket": ticket,
        "role": task.role,
        "auto_write": auto_write,
        "checks": results,
        "deliverables": deliverables,
        "written": written,
        "already_present": present,
        "human_summary": " · ".join(summary_parts),
        "summary": " · ".join(summary_parts),
        "mission_track": "docs_only",
    }
