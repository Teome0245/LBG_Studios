"""Playbook A1 — jalon client MMO : Hermès audit + Argus owner smokes (PLAN_MMO_O2)."""

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


def job_enabled() -> bool:
    return truthy(os.environ.get("LBG_TEAM_MMO_JALON_JOB_ENABLED", "1"))


def spawn_actor_id() -> str:
    return os.environ.get("LBG_TEAM_MMO_JALON_JOB_ACTOR_ID", "system:team_mmo_jalon").strip()


def state_path() -> Path:
    raw = os.environ.get("LBG_TEAM_MMO_JALON_JOB_STATE", "").strip()
    if raw:
        return Path(raw)
    return Path("/var/lib/lbg/team_mmo_jalon/state.json")


def cooldown_s() -> float:
    try:
        return max(1800.0, float(os.environ.get("LBG_TEAM_MMO_JALON_JOB_COOLDOWN_S", "43200")))
    except ValueError:
        return 43200.0


def jalon_id() -> str:
    return os.environ.get("LBG_TEAM_MMO_JALON_ID", "P1_m12").strip() or "P1_m12"


def owner_smoke_bundle() -> str:
    return os.environ.get("LBG_TEAM_MMO_JALON_SMOKE_BUNDLE", "godot_login").strip() or "godot_login"


def run_spawn(*, persist: bool = True, run_tasks: bool = True) -> dict[str, Any]:
    """Crée tâches Hermès + Argus (owner smokes). Optionnellement les exécute."""
    if not job_enabled():
        return {"ok": True, "outcome": "skipped", "spawned": False}

    st = load_json_state(state_path()) if persist else {}
    result: dict[str, Any] = {
        "ok": True,
        "agent": "spawn_team_mmo_jalon_job",
        "jalon": jalon_id(),
        "spawned": False,
        "task_ids": [],
    }

    if cooldown_active(st, cooldown_s=cooldown_s()):
        result["outcome"] = "cooldown"
        return result

    mid = f"mmo_jalon_{jalon_id()}_{int(time.time())}"
    bundle = owner_smoke_bundle()
    hermes_obj = os.environ.get(
        "LBG_TEAM_MMO_JALON_HERMES_OBJECTIVE",
        "Hermès — jalon P1 M12 : vérifier gateway lbg-ws/2 + Launchpad J: (pas new_mmo) — PLAN_MMO_O2",
    ).strip()
    qa_obj = os.environ.get(
        "LBG_TEAM_MMO_JALON_QA_OBJECTIVE",
        f"Argus — owner smokes bundle={bundle} (M11+M12) — preuve jalon {jalon_id()}",
    ).strip()

    try:
        hermes = create_and_run_team_task(
            role="dev_godot",
            objective=hermes_obj,
            actor_id=spawn_actor_id(),
            context={
                "mmo_jalon": True,
                "_require_owner_smoke": True,
                "godot_dev_persona": "hermes",
                "godot_dev_track": "client_live",
                "subproject": "godot_hermes",
                "_campus_mission_id": mid,
                "jalon_id": jalon_id(),
            },
            run=run_tasks,
        )
        qa = create_and_run_team_task(
            role="qa",
            objective=qa_obj,
            actor_id=spawn_actor_id(),
            context={
                "mmo_jalon": True,
                "owner_smoke_bundle": bundle,
                "_require_owner_smoke": True,
                "_campus_mission_id": mid,
                "jalon_id": jalon_id(),
            },
            run=run_tasks,
        )
        h_sum = task_run_summary(hermes) if run_tasks else {"task_id": hermes.get("id")}
        q_sum = task_run_summary(qa) if run_tasks else {"task_id": qa.get("id")}
        tids = [x for x in (h_sum.get("task_id"), q_sum.get("task_id")) if x]
        result["spawned"] = True
        result["task_ids"] = tids
        result["mission_tag"] = mid
        result["hermes"] = h_sum
        result["qa"] = q_sum
        result["outcome"] = "done" if (h_sum.get("task_ok") and q_sum.get("task_ok")) else "ran"
        if persist:
            save_json_state(
                state_path(),
                {
                    "last_spawn_ts": time.time(),
                    "last_jalon": jalon_id(),
                    "last_task_ids": tids,
                    "last_mission_tag": mid,
                },
            )
    except (urllib.error.URLError, OSError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
        result["ok"] = False
        result["outcome"] = "error"
        result["error"] = str(exc)

    return result


def main() -> int:
    run = truthy(os.environ.get("LBG_TEAM_MMO_JALON_RUN_TASKS", "1"))
    result = run_spawn(run_tasks=run)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 3


if __name__ == "__main__":
    raise SystemExit(main())
