#!/usr/bin/env python3
"""Re-spawn M11 ciblé CODE — Thémis contrat + Hermès LoginPanel/LbgAuthClient (forge write_files)."""

from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "agents", "src"))

ACTOR = os.environ.get("LBG_TEAM_M11_CODE_ACTOR", "system:spawn_m11_code_cursor")

PRIME = os.environ.get(
    "LBG_PRIME_CLIENT_ROOT",
    "/home/sdesh/projects/new_mmo/prime-client",
)

DOCS = {
    "client_only": "new_mmo/prime-client/docs/CLIENT_ONLY_GODOT.md",
    "human_player": "new_mmo/prime-client/docs/HUMAN_PLAYER.md",
    "bridge_spec": "docs/core3_zone_bridge_spec.md",
    "godot_live": "docs/jalon_godot_client_live_team.md",
    "m11_jalon": "docs/jalon_m11_login_lbg.md",
    "m12_schemas": "docs/schemas/lbg-ws/",
    "adr": "new_mmo/lbg-mmo/docs/adr/0016-prime-axe-lbg-talents-artisanat.md",
}

TASKS: list[dict] = [
    {
        "role": "pm",
        "objective": (
            "Thémis — ÉCRIRE le contrat M11↔M12 (pas un brief stub). "
            "Remplacer la section stub dans docs/jalon_m11_login_lbg.md : "
            "session_token, ws_url, your_character_id, messages login / select_character / enter_zone, "
            "erreurs auth_failed / character_in_use / session_expired, policy kick_other. "
            "Réf. core3_zone_bridge_spec.md §2 + client.zone_command_v2.schema.json. "
            "Contrainte write_files=1. Output : deliverables[] avec chemin jalon."
        ),
        "context": {
            "handoff_m11_m12": True,
            "m11_code_respawn": True,
            "godot_dev_track": "themis_contract",
            "m11_contract_write": True,
            "write_files": True,
            "pm_write_docs": True,
            "docs": DOCS,
        },
    },
    {
        "role": "dev_godot",
        "objective": (
            "Hermès M11 CODE — ÉCRIRE les fichiers (pas pm_stub). Chemins explicites : "
            f"{PRIME}/scripts/LbgAuthClient.gd ; "
            f"{PRIME}/scenes/ui/login_panel.tscn ; "
            f"{PRIME}/scripts/login_panel.gd ; "
            "compléter LBG_IA_MMORPG/LBG_IA_MMO/docs/jalon_m11_login_lbg.md. "
            "Contraintes : write_files=1, forge_gdscript=1, iris_forge_auto_apply=1. "
            "Sans lbgemu / sans retail / sans soe_handshake bloquant. "
            "Schémas client.login + zone_command_v2. Output : deliverables[] + probes m11_login."
        ),
        "context": {
            "handoff_m11_m12": True,
            "m11_code_respawn": True,
            "godot_dev_persona": "hermes",
            "godot_dev_track": "m11_login",
            "m11_login_forge": True,
            "subproject": "godot_hermes",
            "prime_client_root": PRIME,
            "write_files": True,
            "forge_gdscript": True,
            "iris_forge": True,
            "iris_forge_auto_apply": True,
            "forge_auto_apply": True,
            "docs": DOCS,
        },
    },
]


def main() -> int:
    dry = "--dry-run" in sys.argv
    if dry:
        for t in TASKS:
            track = (t.get("context") or {}).get("godot_dev_track", "")
            print(f"[dry-run] {t['role']} [{track}]: {t['objective'][:120]}…")
        print(f"OK dry-run — {len(TASKS)} tâche(s)")
        return 0

    from lbg_agents.team_job_spawn import create_and_run_team_task, task_run_summary

    orch = os.environ.get("LBG_ORCHESTRATOR_URL", "http://192.168.0.140:8010")
    os.environ.setdefault("LBG_ORCHESTRATOR_URL", orch)
    print(f"Spawn M11 CODE → {orch}")
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
            print(
                f"  task_id={summary.get('task_id')} "
                f"status={summary.get('task_status')} ok={summary.get('task_ok')}"
            )
            tr = summary.get("task_result") or {}
            if tr.get("deliverables"):
                print(f"  deliverables={tr.get('deliverables')}")
            if tr.get("human_summary"):
                print(f"  summary={(tr.get('human_summary') or '')[:300]}")
        except Exception as exc:
            print(f"  FAIL: {exc}", file=sys.stderr)
            results.append({"role": role, "track": track, "error": str(exc), "ok": False})

    out = {
        "ok": all(r.get("task_ok") is not False for r in results if "error" not in r)
        and not any("error" in r for r in results),
        "tasks": [
            {
                "role": r.get("role"),
                "track": r.get("track"),
                "task_id": r.get("task_id"),
                "task_status": r.get("task_status"),
                "task_ok": r.get("task_ok"),
                "error": r.get("error"),
                "deliverables": (r.get("task_result") or {}).get("deliverables"),
            }
            for r in results
        ],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
