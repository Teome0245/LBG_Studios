"""Spawn mission Team — veille concurrents C1–C12 (FOCUS_CONCURRENTS_TEAM).

Vague A (défaut) : 4 tâches L1 **explicites** en parallèle (Thémis / Chœur / Iris / Dédale)
+ tag mission campus. Vagues B/C via ``LBG_TEAM_CONCURRENTS_WAVE``.

Le plan NL campus seul dilue les @mentions (coffee-fill) — d’où des tâches ciblées.

Usage::

    LBG_ORCHESTRATOR_URL=http://192.168.0.140:8010 \\
      python -m lbg_agents.spawn_team_concurrents_wave_job

    LBG_TEAM_CONCURRENTS_DRY_RUN=1 python -m lbg_agents.spawn_team_concurrents_wave_job
    LBG_TEAM_CONCURRENTS_WAVE=B python -m lbg_agents.spawn_team_concurrents_wave_job
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
from pathlib import Path
from typing import Any

from lbg_agents.team_job_spawn import (
    cooldown_active,
    create_and_run_team_task,
    load_json_state,
    save_json_state,
    task_run_summary,
    truthy,
)


# (role, objective, context extras)
WAVE_TASKS: dict[str, list[tuple[str, str, dict[str, Any]]]] = {
    "A": [
        (
            "pm",
            "Thémis — Vague A concurrents : 5 lignes next 72h — ordre C1–C12 + owners + ce qui bloque O1 D6. "
            "Lire docs/FOCUS_CONCURRENTS_TEAM.md et BOITE_IDEES §14. Pas de code.",
            {"concurrents_ticket": "plan_72h", "concurrents_wave": "A"},
        ),
        (
            "player_ia",
            "Chœur — Vague A : brouillon AGENT_SKILL_MMO.md (C9) + schéma JSON mémoire relations (C2). "
            "Sources : docs/world/CONCURRENTS_IA_MMO_2026-10.md, Bible V40–V54. "
            "Livrable = markdown/JSON sous docs/ ou content/ — pas de code Core3 ni think player live.",
            {"concurrents_ticket": "C9_C2", "concurrents_wave": "A", "docs_only": True},
        ),
        (
            "dev_godot",
            "Iris — Vague A : design C1 suggestions dialogue hub (2–3 coups typés + free text). "
            "Lister endpoints / UI Godot / fichiers touchés. Pas d’implémentation code. "
            "Réf. FOCUS_CONCURRENTS_TEAM Vague A + Everwhere pattern dans CONCURRENTS doc.",
            {
                "concurrents_ticket": "C1",
                "concurrents_wave": "A",
                "godot_dev_persona": "iris",
                "godot_dev_track": "dialogue_suggestions_design",
                "subproject": "godot_iris",
                "docs_only": True,
            },
        ),
        (
            "dev_game",
            "Dédale — Vague A : stub data C4 (1 event Scrapaltai: meute/scrap/panne) + C8 (1 pile scrap POI). "
            "JSON sous packages/cortex/content/ — schema valid, pas spawn live 246. "
            "Réf. BOITE_IDEES §14 C4/C8.",
            {
                "concurrents_ticket": "C4_C8",
                "concurrents_wave": "A",
                "docs_only": True,
                "subproject": "content_world",
            },
        ),
    ],
    "B": [
        (
            "dev_godot",
            "Iris — Vague B : implémenter C1 suggestions dialogue + C2 world_hint mémoire (1 PNJ hub). "
            "Cline .143 si write hors allowlist. Smoke dialogue. Réf. FOCUS_CONCURRENTS_TEAM Vague B.",
            {
                "concurrents_ticket": "C1_C2",
                "concurrents_wave": "B",
                "godot_dev_persona": "iris",
                "godot_dev_track": "dialogue_suggestions",
                "subproject": "godot_iris",
                "_require_owner_smoke": True,
            },
        ),
        (
            "player_ia",
            "Chœur — Vague B : C3 compagnon IA visible au spawn Lost Heaven (Lia ou Nix) + finaliser "
            "docs AGENT_SKILL_MMO.md (C9). Pas P4 SOE. Réf. FOCUS_CONCURRENTS_TEAM.",
            {"concurrents_ticket": "C3_C9", "concurrents_wave": "B"},
        ),
        (
            "qa",
            "Argus — Vague B : owner smoke dialogue + hunt/inventory si touché. "
            "Block close mission si rouge. Bundle hint: godot_login ou quest_hub.",
            {
                "concurrents_ticket": "smoke_B",
                "concurrents_wave": "B",
                "owner_smoke_bundle": "godot_login",
                "_require_owner_smoke": True,
                "mmo_jalon": True,
            },
        ),
    ],
    "C": [
        (
            "dev_godot",
            "Hermès — Vague C : C10 catalog read-only (skills/recipes/npcs/poi) + C11 tick mutations vs queries "
            "(design+stub :8791). Pattern SpaceMolt. Persona hermes.",
            {
                "concurrents_ticket": "C10_C11",
                "concurrents_wave": "C",
                "godot_dev_persona": "hermes",
                "godot_dev_track": "client_live",
                "subproject": "godot_hermes",
            },
        ),
        (
            "dev_godot",
            "Iris — Vague C : C12 dual result texte + structuredContent sur 1 endpoint dialogue. "
            "Réf. CONCURRENTS SpaceMolt envelope.",
            {
                "concurrents_ticket": "C12",
                "concurrents_wave": "C",
                "godot_dev_persona": "iris",
                "godot_dev_track": "dialogue_dual",
                "subproject": "godot_iris",
            },
        ),
        (
            "dev_game",
            "Dédale — Vague C : C5 chronique Scribe (5–10 lignes) + C7 négociation marchand bornée (1 vendor). "
            "Data + stub HTTP si besoin.",
            {"concurrents_ticket": "C5_C7", "concurrents_wave": "C", "subproject": "content_world"},
        ),
        (
            "qa",
            "Argus — Vague C : valider stubs C10/C12 + présence wiki/data C6 si livré. Smoke owner si endpoints live.",
            {
                "concurrents_ticket": "smoke_C",
                "concurrents_wave": "C",
                "owner_smoke_bundle": "godot_login",
                "_require_owner_smoke": True,
                "mmo_jalon": True,
            },
        ),
    ],
}


def job_enabled() -> bool:
    return truthy(os.environ.get("LBG_TEAM_CONCURRENTS_WAVE_JOB_ENABLED", "1"))


def wave_id() -> str:
    raw = os.environ.get("LBG_TEAM_CONCURRENTS_WAVE", "A").strip().upper()
    return raw if raw in WAVE_TASKS else "A"


def spawn_actor_id() -> str:
    return os.environ.get("LBG_TEAM_CONCURRENTS_WAVE_ACTOR_ID", "system:team_concurrents").strip()


def state_path() -> Path:
    raw = os.environ.get("LBG_TEAM_CONCURRENTS_WAVE_STATE", "").strip()
    if raw:
        return Path(raw)
    return Path("/var/lib/lbg/team_concurrents_wave/state.json")


def cooldown_s() -> float:
    try:
        return max(300.0, float(os.environ.get("LBG_TEAM_CONCURRENTS_WAVE_COOLDOWN_S", "3600")))
    except ValueError:
        return 3600.0


def run_spawn(*, persist: bool = True, run_tasks: bool | None = None) -> dict[str, Any]:
    if not job_enabled():
        return {"ok": True, "outcome": "skipped", "spawned": False}

    wave = wave_id()
    dry_run = truthy(os.environ.get("LBG_TEAM_CONCURRENTS_DRY_RUN", "0"))
    if run_tasks is None:
        run_tasks = truthy(os.environ.get("LBG_TEAM_CONCURRENTS_RUN_TASKS", "1")) and not dry_run

    st = load_json_state(state_path()) if persist else {}
    result: dict[str, Any] = {
        "ok": True,
        "agent": "spawn_team_concurrents_wave_job",
        "wave": wave,
        "dry_run": dry_run,
        "spawned": False,
        "task_ids": [],
        "tasks": [],
    }

    cool_key = f"last_spawn_ts_{wave}"
    if persist and not dry_run and cooldown_active(st, key=cool_key, cooldown_s=cooldown_s()):
        result["outcome"] = "cooldown"
        result["cooldown_key"] = cool_key
        return result

    mid = f"concurrents_wave_{wave}_{int(time.time())}"
    actor = spawn_actor_id()
    specs = WAVE_TASKS[wave]

    if dry_run:
        result["outcome"] = "dry_run"
        result["mission_tag"] = mid
        result["planned"] = [
            {"role": r, "objective": o[:160], "context_keys": sorted(c.keys())} for r, o, c in specs
        ]
        return result

    try:
        for role, objective, extra in specs:
            ctx = {
                "_campus_mission_id": mid,
                "_campus_mission_objective": f"Veille concurrents Vague {wave}",
                "focus": "FOCUS_CONCURRENTS_TEAM",
                **extra,
            }
            payload = create_and_run_team_task(
                role=role,
                objective=objective,
                actor_id=actor,
                context=ctx,
                run=run_tasks,
                timeout=300,
            )
            summary = task_run_summary(payload) if run_tasks else {"task_id": payload.get("task_id")}
            result["tasks"].append({"role": role, **summary})
            tid = summary.get("task_id")
            if tid:
                result["task_ids"].append(tid)

        result["spawned"] = True
        result["mission_tag"] = mid
        result["outcome"] = "ran" if run_tasks else "queued"
        if persist:
            save_json_state(
                state_path(),
                {
                    **st,
                    cool_key: time.time(),
                    "last_wave": wave,
                    "last_mission_tag": mid,
                    "last_task_ids": result["task_ids"],
                },
            )
    except (urllib.error.URLError, OSError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
        result["ok"] = False
        result["outcome"] = "error"
        result["error"] = str(exc)

    return result


def main() -> int:
    result = run_spawn()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 3


if __name__ == "__main__":
    raise SystemExit(main())
