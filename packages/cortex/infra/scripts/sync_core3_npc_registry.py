#!/usr/bin/env python3
"""Fusionne les pilotes Core3 du catalogue dans agents/.../npc_registry.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "content/core3/core3_npc_catalog.json"
REGISTRY = ROOT / "agents/src/lbg_agents/npc_registry.json"

sys.path.insert(0, str(ROOT / "agents/src"))
from lbg_agents.world_display import HUB_CITY, PLANET_DISPLAY, lore_label  # noqa: E402

ROLE_FROM_MOBILE = {
    "bartender": ("vendor", f"barman {HUB_CITY}", "chaleureux"),
    "trainer_brawler": ("trainer", "instructeur combat", "professionnel"),
    "trainer_marksman": ("trainer", "instructeur tireur", "professionnel"),
    "trainer_scout": ("trainer", "instructeur éclaireur", "professionnel"),
    "trainer_medic": ("trainer", "instructeur médecin", "chaleureux"),
    "trainer_artisan": ("trainer", "instructeur artisan", "professionnel"),
    "trainer_entertainer": ("trainer", "instructeur artiste", "creatif"),
    "trainer_politician": ("trainer", "instructeur politique", "professionnel"),
    "informant_npc_lvl_1": ("informant", "informateur", "pragmatique"),
    "mos_espa_police_officer": ("guard", f"officier police {HUB_CITY}", "professionnel"),
    "scientist": ("scribe", "scientifique", "pedagogue"),
    "commoner_old": ("citizen", "habitant", "chaleureux"),
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _entry_from_slot(slot: dict, roster: dict, profiles: dict) -> dict | None:
    pid = str(slot.get("pilot_id", "")).strip()
    if not pid or not pid.startswith("npc:core3_"):
        return None
    name = str(slot.get("display_name", pid)).strip()
    binding = slot.get("binding") or {}
    mobile = str(binding.get("mobile_template", "")).strip()
    role, summary_role, tone = ROLE_FROM_MOBILE.get(
        mobile, ("npc", f"citoyen {PLANET_DISPLAY}", "professionnel")
    )
    prof_id = str(slot.get("profile_id", roster.get("profile_id", ""))).strip()
    prof = profiles.get(prof_id) if prof_id else {}
    hint = ""
    if isinstance(prof, dict):
        llm = prof.get("llm") or {}
        if isinstance(llm, dict):
            hint = str(llm.get("system_hint", "")).strip()[:200]
    loc_raw = str(roster.get("location_id", "tatooine")).replace("_", " ")
    loc = lore_label(loc_raw)
    if loc.lower() in ("tatooine", "scrapaltai"):
        loc = PLANET_DISPLAY
    summary = lore_label(f"{summary_role} — {roster.get('description', '')}")[:220]
    if hint:
        summary = lore_label(f"{summary} | {hint}")[:220]
    entry = {
        "id": pid,
        "name": name,
        "role": role,
        "race_id": "race:human",
        "zone": f"{HUB_CITY} — {loc}",
        "faction": f"Civils {PLANET_DISPLAY}",
        "tone": tone,
        "summary": summary,
        "goals": ["repondre au joueur en restant dans son role LBG (Scrapaltai / Lost Heaven)"],
        "constraints": [
            "pas de metier Terre1 (forgeron village, auberge fantasy)",
            "reponses courtes",
            "ne jamais dire Tatooine ni Mos Eisley (canon ADR 0009)",
            f"pilot_id={pid}",
        ],
        "core3_source": "core3_npc_catalog.json",
    }
    # Pilotes space / Aviation civile — labels truth-guard Chœur
    if "pilot_" in pid:
        track = "civil"
        for key in ("alliance", "freelance", "imperial"):
            if f"_{key}_" in pid:
                track = key
                break
        entry["role"] = "pilot_trainer"
        entry["faction"] = "Aviation civile Lost Heaven"
        entry["pilot_track"] = track
        entry["summary"] = f"instructeur pilote {track} — {roster.get('description', '')}"[:220]
        if hint:
            entry["summary"] = f"{entry['summary']} | {hint}"
        entry["zone"] = (
            "Lost Heaven — Scrapaltai" if track == "imperial" or "lost" in loc.lower() else f"Mos Eisley — {loc}"
        )
    return entry


def main() -> int:
    cat = _load(CATALOG)
    reg = _load(REGISTRY)
    profiles = cat.get("profiles") or {}
    existing = {str(n.get("id", "")).strip() for n in reg.get("npcs") or [] if isinstance(n, dict)}
    added = 0
    updated = 0
    by_id: dict[str, dict] = {}
    for n in reg.get("npcs") or []:
        if isinstance(n, dict) and n.get("id"):
            by_id[str(n["id"])] = n

    for roster in cat.get("rosters") or []:
        if not isinstance(roster, dict):
            continue
        for slot in roster.get("slots") or []:
            if not isinstance(slot, dict):
                continue
            ent = _entry_from_slot(slot, roster, profiles)
            if ent is None:
                continue
            eid = ent["id"]
            if eid in by_id:
                by_id[eid].update({k: v for k, v in ent.items() if k != "id"})
                updated += 1
            else:
                by_id[eid] = ent
                added += 1

    reg["npcs"] = sorted(by_id.values(), key=lambda x: str(x.get("id", "")))
    REGISTRY.write_text(json.dumps(reg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[sync_core3_npc_registry] +{added} ~{updated} → {REGISTRY} ({len(reg['npcs'])} npcs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
