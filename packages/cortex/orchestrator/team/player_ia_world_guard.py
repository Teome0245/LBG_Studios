"""Smoke L1 : cohérence Bible / M10 / registry pour le Chœur."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    # packages/cortex/orchestrator/team -> packages/cortex
    # Sur VM 140 : /opt/LBG_IA_MMO (équivalent cortex)
    return Path(__file__).resolve().parents[2]


def _truth_guard_enabled() -> bool:
    raw = os.environ.get("LBG_TEAM_PLAYER_IA_TRUTH_GUARD", "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def _bible_path(root: Path) -> Path:
    """Résout BIBLE_MMO.md (local monorepo ou déploiement VM)."""
    raw = os.environ.get("LBG_BIBLE_MMO_PATH", "").strip()
    if raw:
        return Path(raw)
    candidates = (
        root / "docs" / "world" / "BIBLE_MMO.md",  # VM : /opt/LBG_IA_MMO/docs/world/
        root.parents[1] / "docs" / "world" / "BIBLE_MMO.md",  # monorepo : LBG_Studios/docs/world/
        Path("/opt/LBG_IA_MMO/docs/world/BIBLE_MMO.md"),
    )
    for path in candidates:
        try:
            if path.is_file():
                return path.resolve()
        except OSError:
            continue
    return candidates[0]


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return raw if isinstance(raw, dict) else None


def _check(ok: bool, kind: str, details: dict[str, Any]) -> dict[str, Any]:
    return {"kind": kind, "ok": ok, **details}


def _catalog_checks(root: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    path = root / "content" / "m10" / "m10_skills_catalog.json"
    data = _read_json(path)
    if data is None:
        return [_check(False, "catalog_read", {"path": str(path), "error": "read_failed"})]

    out.append(
        _check(
            int(data.get("schema_version", 0)) >= 3,
            "catalog_schema",
            {"path": str(path), "schema_version": data.get("schema_version")},
        )
    )
    skills = [s for s in (data.get("skills") or []) if isinstance(s, dict)]
    skill_ids = {str(s.get("id")) for s in skills}
    needed_skills = {"prospecteur_r1", "artisan_rue_r1", "medecine_camp_r1", "pilotage_shuttle_r1"}
    out.append(
        _check(
            needed_skills.issubset(skill_ids),
            "catalog_core_skills",
            {"missing": sorted(needed_skills - skill_ids), "count": len(skills)},
        )
    )
    schematics = [s for s in (data.get("schematics") or []) if isinstance(s, dict)]
    schematic_ids = {str(s.get("id")) for s in schematics}
    needed_schematics = {"kit_reparation", "ration_compacte", "bandage_antivenin", "plaque_carapace", "lame_obsidienne"}
    out.append(
        _check(
            needed_schematics.issubset(schematic_ids),
            "catalog_core_schematics",
            {"missing": sorted(needed_schematics - schematic_ids), "count": len(schematics)},
        )
    )
    return out


def _faille_gate_checks(root: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    path = root / "content" / "world" / "faille_progression_gate.json"
    data = _read_json(path)
    if data is None:
        return [_check(False, "faille_gate_read", {"path": str(path), "error": "read_failed"})]
    out.append(_check(int(data.get("schema_version", 0)) >= 1, "faille_gate_schema", {"path": str(path)}))
    events = [e for e in (data.get("events") or []) if isinstance(e, dict)]
    out.append(_check(len(events) == 12, "faille_gate_events_count", {"count": len(events)}))
    ids = {str(e.get("id")) for e in events}
    expected_ids = {f"E{i}" for i in range(1, 13)}
    out.append(_check(ids == expected_ids, "faille_gate_event_ids", {"missing": sorted(expected_ids - ids)}))
    flags = {str(e.get("flag")) for e in events}
    needed_flags = {"intro_deplacement_complete", "lore_indices_faille", "faille_activation_protocol"}
    out.append(_check(needed_flags.issubset(flags), "faille_gate_flags", {"missing": sorted(needed_flags - flags)}))
    return out


def _registry_checks(root: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    path = root / "agents" / "src" / "lbg_agents" / "npc_registry.json"
    data = _read_json(path)
    if data is None:
        return [_check(False, "registry_read", {"path": str(path), "error": "read_failed"})]
    npcs = [n for n in (data.get("npcs") or []) if isinstance(n, dict)]
    by_id = {str(n.get("id")): n for n in npcs if isinstance(n.get("id"), str)}

    kis = by_id.get("npc:scientist_mos", {})
    kis_ok = (
        str(kis.get("race_id")) == "race:fel_rani"
        and str(kis.get("role")) == "scientist"
        and "Lost Heaven" in str(kis.get("zone", ""))
    )
    out.append(_check(kis_ok, "registry_kisreudi", {"race_id": kis.get("race_id"), "zone": kis.get("zone")}))

    pilot_ids = [
        "npc:core3_pilot_alliance_a",
        "npc:core3_pilot_alliance_b",
        "npc:core3_pilot_alliance_c",
        "npc:core3_pilot_freelance_a",
        "npc:core3_pilot_freelance_b",
        "npc:core3_pilot_freelance_c",
        "npc:core3_pilot_imperial_a",
        "npc:core3_pilot_imperial_b",
        "npc:core3_pilot_imperial_c",
    ]
    bad: list[str] = []
    for pid in pilot_ids:
        n = by_id.get(pid, {})
        if not n:
            bad.append(f"{pid}:missing")
            continue
        if str(n.get("faction")) != "Aviation civile Lost Heaven":
            bad.append(f"{pid}:faction")
        if str(n.get("role")) != "pilot_trainer":
            bad.append(f"{pid}:role")
        if "pilot_track" not in n:
            bad.append(f"{pid}:track")
    out.append(_check(not bad, "registry_pilot_labels", {"issues": bad}))
    return out


def _bible_checks(root: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    p = _bible_path(root)
    try:
        txt = p.read_text(encoding="utf-8")
    except Exception:
        return [_check(False, "bible_read", {"path": str(p), "error": "read_failed"})]
    out.append(_check("La Perle de Scrapaltai" in txt, "bible_v13_perle", {"path": str(p)}))
    out.append(_check("T3" in txt and "Tranché" in txt, "bible_t3_status", {"path": str(p)}))
    out.append(_check("N12" in txt and "MJ IA" in txt, "bible_n12_mj", {"path": str(p)}))
    return out


def run_world_truth_guard() -> dict[str, object]:
    if not _truth_guard_enabled():
        return {"kind": "world_truth_guard", "ok": True, "enabled": False, "checks": []}

    root = _repo_root()
    checks: list[dict[str, Any]] = []
    checks.extend(_bible_checks(root))
    checks.extend(_catalog_checks(root))
    checks.extend(_faille_gate_checks(root))
    checks.extend(_registry_checks(root))
    ok = all(bool(c.get("ok")) for c in checks)
    return {"kind": "world_truth_guard", "ok": ok, "enabled": True, "checks": checks}

