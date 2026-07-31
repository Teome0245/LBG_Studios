#!/usr/bin/env python3
"""Distribue le handoff Prime LBG / Godot / TreFiles minimal à l'équipe virtuelle."""

from __future__ import annotations

import json
import os
import sys

# Allow import from agents package when run from repo root
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "agents", "src"))

from lbg_agents.team_job_spawn import create_and_run_team_task, task_run_summary

HANDOFF_DOC = "docs/handoff_prime_lbg_godot_2026-07-14.md"
ACTOR = os.environ.get("LBG_TEAM_HANDOFF_ACTOR", "system:handoff_prime_lbg")

TASKS: list[dict] = [
    {
        "role": "pm",
        "objective": (
            "Brief handoff Prime LBG — ADR 0016, jalons Godot M10-M12, client SWG en transition. "
            f"Intégrer au brief réunification Thémis. Doc: {HANDOFF_DOC}"
        ),
        "context": {
            "handoff_prime_lbg": True,
            "handoff_doc": HANDOFF_DOC,
            "reunification_brief": True,
            "pm_include_plan": True,
            "pm_include_structure": True,
        },
    },
    {
        "role": "dev_game",
        "objective": (
            "Handoff Dédale — smoke craft artisan Prime 246 post TreFiles minimal, "
            "hub artisan LBG, backlog core3_cleanup phase 1. ADR 0016."
        ),
        "context": {"handoff_prime_lbg": True, "handoff_doc": HANDOFF_DOC},
    },
    {
        "role": "dev_godot",
        "objective": (
            "Handoff Iris — spec M10 UI talents+craft prime-client, lecture sidecar :8791. ADR 0016."
        ),
        "context": {"handoff_prime_lbg": True, "godot_dev_track": "iris", "handoff_doc": HANDOFF_DOC},
    },
    {
        "role": "dev_godot",
        "objective": (
            "Handoff Hermès — spec réseau Godot-Core3 M12, lbg-ws/2, remplacement login SOE. ADR 0016."
        ),
        "context": {"handoff_prime_lbg": True, "godot_dev_track": "hermes", "handoff_doc": HANDOFF_DOC},
    },
    {
        "role": "player_ia",
        "objective": (
            "Handoff Chœur — valider monde Prime 246 après TreFiles minimal, bots craft, sidecar 8791."
        ),
        "context": {"handoff_prime_lbg": True, "handoff_doc": HANDOFF_DOC},
    },
    {
        "role": "ops",
        "objective": (
            "Handoff Héphaïstos — documenter TreFiles minimal 246, rollback script, surveiller disque."
        ),
        "context": {"handoff_prime_lbg": True, "handoff_doc": HANDOFF_DOC},
    },
    {
        "role": "qa",
        "objective": (
            "Handoff Argus — smokes LAN Prime 246 boot+sidecar, Godot mirror, craft (coordination Dédale)."
        ),
        "context": {"handoff_prime_lbg": True, "godot_supervisor": True, "handoff_doc": HANDOFF_DOC},
    },
    {
        "role": "dev_game",
        "objective": (
            "Handoff Pygmalion — sprites overhead Lia/Nix/Mira et icônes craft pour prime-client Godot."
        ),
        "context": {"handoff_prime_lbg": True, "sprites_2d": True, "handoff_doc": HANDOFF_DOC},
    },
]


def main() -> int:
    dry = "--dry-run" in sys.argv
    orch = os.environ.get("LBG_ORCHESTRATOR_URL", "http://127.0.0.1:8010")
    results: list[dict] = []

    if dry:
        for t in TASKS:
            print(f"[dry-run] {t['role']}: {t['objective'][:80]}…")
        print(f"OK dry-run — {len(TASKS)} tâches")
        return 0

    print(f"Handoff Prime LBG → {orch}")
    for t in TASKS:
        role = t["role"]
        print(f"=== {role} ===")
        try:
            payload = create_and_run_team_task(
                role=role,
                objective=t["objective"],
                actor_id=ACTOR,
                context=t.get("context") or {},
            )
            summary = task_run_summary(payload)
            summary["role"] = role
            results.append(summary)
            print(f"  task_id={summary.get('task_id')} status={summary.get('task_status')} ok={summary.get('task_ok')}")
        except Exception as exc:
            print(f"  FAIL: {exc}", file=sys.stderr)
            results.append({"role": role, "error": str(exc), "ok": False})

    out = {"ok": all(r.get("task_ok") is not False for r in results if "error" not in r), "tasks": results}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
