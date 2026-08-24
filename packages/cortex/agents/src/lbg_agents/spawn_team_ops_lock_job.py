"""Timer core 140 : sonde locks / snapshots vzdump Proxmox → tâche équipe ``ops`` si warn/critical."""

from __future__ import annotations

import json
import os
import time
import urllib.error
from pathlib import Path
from typing import Any

from lbg_agents.proxmox_guest_lock_probe import probe_proxmox_guest_lock_local
from lbg_agents.team_job_spawn import (
    create_and_run_team_task,
    load_json_state,
    save_json_state,
    task_run_summary,
    truthy,
)


def job_enabled() -> bool:
    return truthy(os.environ.get("LBG_TEAM_OPS_LOCK_JOB_ENABLED", "1"))


def spawn_actor_id() -> str:
    return os.environ.get("LBG_TEAM_OPS_LOCK_JOB_ACTOR_ID", "system:team_ops_lock").strip()


def state_path() -> Path:
    raw = os.environ.get("LBG_TEAM_OPS_LOCK_JOB_STATE", "").strip()
    if raw:
        return Path(raw)
    return Path("/var/lib/lbg/team_ops_lock/state.json")


def cooldown_s(outcome: str) -> float:
    if outcome == "critical":
        try:
            return max(300.0, float(os.environ.get("LBG_TEAM_OPS_LOCK_COOLDOWN_CRITICAL_S", "1800")))
        except ValueError:
            return 1800.0
    try:
        return max(600.0, float(os.environ.get("LBG_TEAM_OPS_LOCK_COOLDOWN_WARN_S", "3600")))
    except ValueError:
        return 3600.0


def default_objective(outcome: str, probe: dict[str, Any]) -> str:
    custom = os.environ.get("LBG_TEAM_OPS_LOCK_JOB_OBJECTIVE", "").strip()
    if custom:
        return custom
    locked_n = len(probe.get("locked_guests") or [])
    snap_n = len(probe.get("orphan_snaps") or [])
    return (
        f"Sonde locks Proxmox — alerte {outcome} "
        f"(guests verrouillés={locked_n}, snapshots vzdump orphelins={snap_n} — read-only L1)"
    )


def _should_spawn(outcome: str, st: dict[str, Any]) -> bool:
    if outcome == "ok":
        return truthy(os.environ.get("LBG_TEAM_OPS_LOCK_SPAWN_ON_OK", "0"))
    last = float(st.get("last_spawn_ts") or 0)
    last_outcome = str(st.get("last_spawn_outcome") or "")
    if last and time.time() - last < cooldown_s(outcome):
        if outcome == last_outcome or outcome == "critical":
            return False
    return True


def run_spawn(*, persist: bool = True) -> dict[str, Any]:
    if not job_enabled():
        return {
            "ok": True,
            "outcome": "skipped",
            "reply": "LBG_TEAM_OPS_LOCK_JOB_ENABLED=0",
            "spawned": False,
            "task_id": None,
        }

    probe = probe_proxmox_guest_lock_local()
    outcome = str(probe.get("outcome") or ("critical" if not probe.get("ok") else "ok"))
    st = load_json_state(state_path()) if persist else {}

    result: dict[str, Any] = {
        "ok": True,
        "agent": "spawn_team_ops_lock_job",
        "outcome": outcome,
        "guest_lock": probe,
        "spawned": False,
        "task_id": None,
    }

    if _should_spawn(outcome, st):
        try:
            payload = create_and_run_team_task(
                role="ops",
                objective=default_objective(outcome, probe),
                actor_id=spawn_actor_id(),
                context={
                    "_team_ops_lock_spawn": True,
                    "ops_kind": "proxmox_guest_lock",
                    "proxmox_guest_lock": probe,
                },
            )
            summary = task_run_summary(payload)
            result["spawned"] = True
            result.update(summary)
            result["reply"] = (
                f"Tâche ops {summary['task_id']} "
                f"(status={summary['task_status']}, outcome={outcome})"
            )
            if persist:
                save_json_state(
                    state_path(),
                    {
                        "last_spawn_ts": time.time(),
                        "last_spawn_outcome": outcome,
                        "last_task_id": summary["task_id"],
                        "last_locked_count": len(probe.get("locked_guests") or []),
                        "last_orphan_snaps": len(probe.get("orphan_snaps") or []),
                    },
                )
        except (urllib.error.URLError, OSError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
            result["ok"] = False
            result["error"] = str(exc)
            result["reply"] = f"Échec playbook ops locks : {exc}"
    else:
        result["reply"] = f"Sonde {outcome} — pas de nouvelle tâche ops (OK ou cooldown)"

    if persist and not result.get("spawned"):
        st["last_check_ts"] = time.time()
        st["last_outcome"] = outcome
        st["last_locked_count"] = len(probe.get("locked_guests") or [])
        st["last_orphan_snaps"] = len(probe.get("orphan_snaps") or [])
        save_json_state(state_path(), st)

    return result


def main() -> int:
    result = run_spawn()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result.get("ok"):
        return 3
    if result.get("task_status") == "failed":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
