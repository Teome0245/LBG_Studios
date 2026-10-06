#!/usr/bin/env python3
"""Génère le wiki hub Lost Heaven MVP (ticket C6) depuis inventaire PNJ + extrait M10.

Usage (depuis monorepo) :

    python packages/cortex/tools/generate_wiki_hub_lost_heaven_mvp.py

Sortie : packages/cortex/docs/wiki_hub_lost_heaven_mvp.md
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # LBG_Studios
INVENTAIRE = ROOT / "docs" / "world" / "INVENTAIRE_PNJ.md"
M10 = ROOT / "packages" / "cortex" / "content" / "m10" / "m10_skills_catalog.json"
OUT = ROOT / "packages" / "cortex" / "docs" / "wiki_hub_lost_heaven_mvp.md"


def _parse_hub_roster(md: str) -> list[tuple[str, str, str, str]]:
    """Extrait la table §1 Hub Lost Heaven — (nom, id, rôle, poi)."""
    rows: list[tuple[str, str, str, str]] = []
    in_section = False
    for line in md.splitlines():
        if line.startswith("## 1. Hub Lost Heaven"):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if not in_section or not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 4:
            continue
        if cells[0] in ("Nom", "-----") or cells[0].startswith("---"):
            continue
        name = re.sub(r"\*+", "", cells[0]).strip()
        npc_id = cells[1].split("/")[0].strip()
        # garder premier id si « a / b »
        npc_id = npc_id.split()[0] if npc_id else ""
        role = re.sub(r"\*+", "", cells[2]).strip()
        poi = cells[3].strip()
        if name and npc_id.startswith("`"):
            npc_id = npc_id.strip("`")
        elif name and "npc:" in cells[1]:
            m = re.search(r"`?(npc:[a-z0-9_]+)`?", cells[1])
            npc_id = m.group(1) if m else cells[1]
        if name and role:
            rows.append((name, npc_id, role, poi))
    return rows


def _m10_extract(data: dict) -> tuple[list[dict], list[dict]]:
    professions = [p for p in (data.get("professions") or []) if isinstance(p, dict)]
    trees = [t for t in (data.get("trees") or []) if isinstance(t, dict)]
    return professions, trees


def render() -> str:
    inventaire = INVENTAIRE.read_text(encoding="utf-8")
    roster = _parse_hub_roster(inventaire)
    m10 = json.loads(M10.read_text(encoding="utf-8"))
    professions, trees = _m10_extract(m10)
    today = date.today().isoformat()

    lines: list[str] = [
        "# Wiki hub — Lost Heaven (MVP généré)",
        "",
        f"**Ticket** : C6 · **Généré** : {today} · **Script** : `packages/cortex/tools/generate_wiki_hub_lost_heaven_mvp.py`",
        "",
        "**Sources** : [`INVENTAIRE_PNJ.md`](../../../docs/world/INVENTAIRE_PNJ.md) §1 · [`m10_skills_catalog.json`](../content/m10/m10_skills_catalog.json)",
        "",
        "> Document **généré** — ne pas éditer à la main. Regenerer via le script. Pas de lore inventé hors inventaire / M10.",
        "",
        "---",
        "",
        "## PNJ hub (extrait inventaire)",
        "",
        "| Nom | Id | Rôle | POI |",
        "|-----|----|------|-----|",
    ]
    for name, npc_id, role, poi in roster:
        lines.append(f"| {name} | `{npc_id}` | {role} | {poi} |")

    lines.extend(
        [
            "",
            f"_Total roster §1 parsé : **{len(roster)}** entrées._",
            "",
            "---",
            "",
            "## Professions M10 (extrait)",
            "",
            "| Id | Nom | Trainers (rôles) |",
            "|----|-----|------------------|",
        ]
    )
    for p in professions:
        tid = p.get("id", "")
        tname = p.get("name", "")
        roles = ", ".join(str(r) for r in (p.get("trainer_roles") or []))
        if tid:
            lines.append(f"| `{tid}` | {tname} | {roles or '—'} |")

    if trees:
        lines.extend(
            [
                "",
                "## Arbres / playstyles UI (extrait M10)",
                "",
                "| Id | Nom | Profession | Blurb |",
                "|----|-----|------------|-------|",
            ]
        )
        for t in trees:
            tid = t.get("id", "")
            if not tid:
                continue
            lines.append(
                f"| `{tid}` | {t.get('name', '')} | `{t.get('profession_id', '')}` | {t.get('blurb', '')} |"
            )

    lines.extend(
        [
            "",
            "---",
            "",
            "## Notes MVP",
            "",
            "- Drift inventaire ↔ registry = fail smoke data (Argus).",
            "- Formation scène = Talen Ress / triplon ; **pas** Kisreudi (V21).",
            "- Wiki = guide joueur data-driven ; Scribe (C5) = chronique session séparée.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    text = render()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(f"Wrote {OUT} ({len(text.splitlines())} lines)")


if __name__ == "__main__":
    main()
