"""Mission Team Chœur L1 — probe player_ia + owner smoke bundle ``choeur_l1``."""

from __future__ import annotations

import json
import os
import time
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
    return truthy(os.environ.get("LBG_TEAM_CHOEUR_L1_JOB_ENABLED", "1"))


def spawn_actor_id() -> str:
    return os.environ.get("LBG_TEAM_CHOEUR_L1_JOB_ACTOR_ID", "system:team_choeur_l1").strip()


def state_path() -> Path:
    raw = os.environ.get("LBG_TEAM_CHOEUR_L1_JOB_STATE", "").strip()
    if raw:
        return Path(raw)
    return Path("/var/lib/lbg/team_choeur_l1/state.json")


def cooldown_s() -> float:
    try:
        return max(1800.0, float(os.environ.get("LBG_TEAM_CHOEUR_L1_JOB_COOLDOWN_S", "43200")))
    except ValueError:
        return 43200.0


def run_spawn(*, persist: bool = True, run_tasks: bool = True) -> dict[str, Any]:
    if not job_enabled():
        return {"ok": True, "outcome": "skipped", "spawned": False, "agent": "spawn_team_choeur_l1_job"}

    st = load_json_state(state_path()) if persist else {}
    result: dict[str, Any] = {
        "ok": True,
        "agent": "spawn_team_choeur_l1_job",
        "spawned": False,
        "task_ids": [],
    }
    if cooldown_active(st, cooldown_s=cooldown_s()):
        result["outcome"] = "cooldown"
        return result

    mid = f"choeur_l1_{int(time.time())}"
    probe_obj = os.environ.get(
        "LBG_TEAM_CHOEUR_L1_PROBE_OBJECTIVE",
        "Chœur — sonde L1 joueurs IA hub :8787 (V50–V52) + truth guard Bible/M10",
    ).strip()
    qa_obj = os.environ.get(
        "LBG_TEAM_CHOEUR_L1_QA_OBJECTIVE",
        "Argus — owner smokes bundle=choeur_l1 (smoke_choeur_terrain) — preuve V50–V53",
    ).strip()

    probe = create_and_run_team_task(
        role="player_ia",
        objective=probe_obj,
        actor_id=spawn_actor_id(),
        context={
            "_campus_mission_id": mid,
            "owner_smoke_bundle": "choeur_l1",
            "_require_owner_smoke": True,
            "mmo_jalon": True,
            "jalon_id": "choeur_l1",
        },
        run=run_tasks,
    )
    qa = create_and_run_team_task(
        role="qa",
        objective=qa_obj,
        actor_id=spawn_actor_id(),
        context={
            "owner_smoke_bundle": "choeur_l1",
            "_require_owner_smoke": True,
            "_campus_mission_id": mid,
            "mmo_jalon": True,
            "jalon_id": "choeur_l1",
        },
        run=run_tasks,
    )
    p_sum = task_run_summary(probe) if run_tasks else {"task_id": probe.get("id")}
    q_sum = task_run_summary(qa) if run_tasks else {"task_id": qa.get("id")}
    tids = [x for x in (p_sum.get("task_id"), q_sum.get("task_id")) if x]
    result["spawned"] = True
    result["task_ids"] = tids
    result["mission_tag"] = mid
    result["player_ia"] = p_sum
    result["qa"] = q_sum
    result["outcome"] = "done" if (p_sum.get("task_ok") and q_sum.get("task_ok")) else "ran"
    if persist:
        save_json_state(
            state_path(),
            {
                "last_spawn_ts": time.time(),
                "last_mission": mid,
                "last_task_ids": tids,
                "last_outcome": result["outcome"],
            },
        )
    return result


def main() -> int:
    out = run_spawn(persist=True, run_tasks=True)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    if out.get("outcome") == "skipped":
        return 0
    if out.get("outcome") == "cooldown":
        return 0
    return 0 if out.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
