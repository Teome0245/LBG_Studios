#!/usr/bin/env python3
"""Re-spawn Lost Heaven CODE — Hermès/Iris write_files (docs + deliverables)."""

from __future__ import annotations

import importlib.util
import json
import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

ACTOR = os.environ.get("LBG_TEAM_LH_CODE_ACTOR", "system:spawn_lost_heaven_code")

PRIME = os.environ.get(
    "LBG_PRIME_CLIENT_ROOT",
    "/home/sdesh/projects/new_mmo/prime-client",
)
HTTP = os.environ.get("LBG_GATEWAY_HTTP", "http://192.168.0.246:8765")

DOCS = {
    "retail_layout": f"{PRIME}/docs/RETAIL_CITY_LAYOUT.md",
    "map_textures": f"{PRIME}/docs/MAP_TEXTURES_AND_RETAIL.md",
    "human_player": f"{PRIME}/docs/HUMAN_PLAYER.md",
    "handoff": "LBG_IA_MMORPG/LBG_IA_MMO/docs/HANDOFF_SPAWN_LOST_HEAVEN_MAP.md",
}

TASKS: list[dict] = [
    {
        "role": "dev_godot",
        "objective": (
            "Hermès LH CODE — ÉCRIRE la doc PNJ serveur (pas audit). "
            f"Sections dans {PRIME}/docs/RETAIL_CITY_LAYOUT.md (PNJ serveur) ; "
            "vérifier export tools/retail/export_server_npcs_lost_heaven.sh. "
            "Contraintes : lh_code_respawn=1, write_files=1. "
            "Output : deliverables[] + recommendation."
        ),
        "context": {
            "lh_code_respawn": True,
            "lost_heaven_map": True,
            "godot_dev_persona": "hermes",
            "godot_dev_track": "lh_server_npcs",
            "subproject": "godot_hermes",
            "prime_client_root": PRIME,
            "gateway_http": HTTP,
            "write_files": True,
            "lh_code_forge": True,
            "docs": DOCS,
        },
    },
    {
        "role": "dev_godot",
        "objective": (
            "Hermès LH CODE — ÉCRIRE doc Launchpad/WSL dans HUMAN_PLAYER.md "
            "(chemin WSL, sync J:, verify_launchpad, WS 50000). "
            "write_files=1 · deliverables[]."
        ),
        "context": {
            "lh_code_respawn": True,
            "godot_dev_persona": "hermes",
            "godot_dev_track": "launchpad_wsl_sync",
            "subproject": "godot_hermes",
            "prime_client_root": PRIME,
            "write_files": True,
            "lh_code_forge": True,
            "docs": DOCS,
        },
    },
    {
        "role": "dev_godot",
        "objective": (
            "Iris LH CODE — ÉCRIRE recommandation fond LH dans MAP_TEXTURES_AND_RETAIL.md "
            "(procédural vs texture planète). write_files=1 · deliverables[]."
        ),
        "context": {
            "lh_code_respawn": True,
            "godot_dev_persona": "iris",
            "godot_dev_track": "lh_retail_map",
            "subproject": "godot_iris",
            "prime_client_root": PRIME,
            "write_files": True,
            "lh_code_forge": True,
            "docs": DOCS,
        },
    },
    {
        "role": "dev_godot",
        "objective": (
            "Iris LH CODE — ÉCRIRE checklist habillage dans RETAIL_CITY_LAYOUT.md "
            "(habillage_lost_heaven.sh, sprites overhead). write_files=1 · deliverables[]."
        ),
        "context": {
            "lh_code_respawn": True,
            "godot_dev_track": "lh_habillage",
            "subproject": "godot_iris",
            "prime_client_root": PRIME,
            "write_files": True,
            "lh_code_forge": True,
            "docs": DOCS,
        },
    },
]


def main() -> int:
    dry = "--dry-run" in sys.argv
    if dry:
        for t in TASKS:
            track = (t.get("context") or {}).get("godot_dev_track", "")
            print(f"[dry-run] {t['role']} [{track}]: {t['objective'][:110]}…")
        print(f"OK dry-run — {len(TASKS)} tâche(s)")
        return 0

    _spawn_path = os.path.join(_ROOT, "agents", "src", "lbg_agents", "team_job_spawn.py")
    spec = importlib.util.spec_from_file_location("team_job_spawn", _spawn_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"impossible de charger {_spawn_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    create_and_run_team_task = mod.create_and_run_team_task
    task_run_summary = mod.task_run_summary

    orch = os.environ.get("LBG_ORCHESTRATOR_URL", "http://192.168.0.140:8010")
    os.environ.setdefault("LBG_ORCHESTRATOR_URL", orch)
    print(f"Spawn Lost Heaven CODE → {orch}")
    print(f"prime_client_root={PRIME}")

    results: list[dict] = []
    for t in TASKS:
        role = t["role"]
        track = (t.get("context") or {}).get("godot_dev_track", "")
        print(f"=== {role} / {track} ===")
        try:
            payload = create_and_run_team_task(
                role=role,
                objective=t["objective"],
                actor_id=ACTOR,
                context=t.get("context") or {},
            )
            summary = task_run_summary(payload)
            summary["role"] = role
            summary["track"] = track
            results.append(summary)
            tr = summary.get("task_result") or {}
            print(
                f"  task_id={summary.get('task_id')} "
                f"status={summary.get('task_status')} ok={summary.get('task_ok')}"
            )
            if tr.get("deliverables"):
                print(f"  deliverables={tr.get('deliverables')}")
        except Exception as exc:
            print(f"  FAIL: {exc}", file=sys.stderr)
            results.append({"role": role, "track": track, "error": str(exc), "ok": False})

    out = {
        "ok": all(r.get("task_ok") for r in results if "error" not in r)
        and not any("error" in r for r in results),
        "tasks": results,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
