"""Timer core 140 : sonde guest mur INFRA LAN → tâche équipe ``ops`` si warn/critical (L1)."""

from __future__ import annotations

import json
import os
import time
import urllib.error
from pathlib import Path
from typing import Any

from lbg_agents.guest_metrics_probe import (
    disk_crit_pct,
    disk_warn_pct,
    load_crit_ratio,
    load_warn_ratio,
    probe_guest_metrics_wall,
)
from lbg_agents.infra_guest_remediation import build_guest_remediation_plan
from lbg_agents.team_job_spawn import (
    create_and_run_team_task,
    load_json_state,
    save_json_state,
    task_run_summary,
    truthy,
)


def job_enabled() -> bool:
    return truthy(os.environ.get("LBG_TEAM_OPS_GUEST_JOB_ENABLED", "1"))


def spawn_actor_id() -> str:
    return os.environ.get("LBG_TEAM_OPS_GUEST_JOB_ACTOR_ID", "system:team_ops_guest").strip()


def state_path() -> Path:
    raw = os.environ.get("LBG_TEAM_OPS_GUEST_JOB_STATE", "").strip()
    if raw:
        return Path(raw)
    return Path("/var/lib/lbg/team_ops_guest/state.json")


def cooldown_s(outcome: str) -> float:
    if outcome == "critical":
        try:
            return max(300.0, float(os.environ.get("LBG_TEAM_OPS_GUEST_COOLDOWN_CRITICAL_S", "900")))
        except ValueError:
            return 900.0
    try:
        return max(600.0, float(os.environ.get("LBG_TEAM_OPS_GUEST_COOLDOWN_WARN_S", "1800")))
    except ValueError:
        return 1800.0


def default_objective(outcome: str, stressed_labels: list[str]) -> str:
    custom = os.environ.get("LBG_TEAM_OPS_GUEST_JOB_OBJECTIVE", "").strip()
    if custom:
        return custom
    who = ", ".join(stressed_labels[:4]) if stressed_labels else "mur INFRA LAN"
    return (
        f"Sonde guest mur INFRA LAN — alerte {outcome} ({who}) "
        "(disk/load — remédiation consultative L1)"
    )


def _should_spawn(outcome: str, st: dict[str, Any]) -> bool:
    if outcome == "ok":
        return truthy(os.environ.get("LBG_TEAM_OPS_GUEST_SPAWN_ON_OK", "0"))
    last = float(st.get("last_spawn_ts") or 0)
    last_outcome = str(st.get("last_spawn_outcome") or "")
    if last and time.time() - last < cooldown_s(outcome):
        if outcome == last_outcome or outcome == "critical":
            return False
        # escalade warn → critical autorisée après cooldown critical
        if outcome == "critical" and last_outcome == "warn":
            return time.time() - last >= cooldown_s("critical")
        return False
    return True


def _signature(wall: dict[str, Any]) -> str:
    parts: list[str] = []
    for row in wall.get("stressed") or wall.get("hosts") or []:
        if not isinstance(row, dict):
            continue
        if str(row.get("outcome") or "") not in {"warn", "critical"} and row.get("ok"):
            continue
        parts.append(
            f"{row.get('id')}:{row.get('outcome')}:{row.get('disk_percent')}:{row.get('load1')}"
        )
    return "|".join(parts)


def run_spawn(*, persist: bool = True) -> dict[str, Any]:
    if not job_enabled():
        return {
            "ok": True,
            "outcome": "skipped",
            "reply": "LBG_TEAM_OPS_GUEST_JOB_ENABLED=0",
            "spawned": False,
            "task_id": None,
        }

    wall = probe_guest_metrics_wall()
    plan = build_guest_remediation_plan(wall)
    outcome = str(wall.get("outcome") or ("critical" if not wall.get("ok") else "ok"))
    st = load_json_state(state_path()) if persist else {}
    stressed_labels = [
        str(h.get("label") or h.get("id"))
        for h in (wall.get("stressed") or [])
        if isinstance(h, dict)
    ]

    result: dict[str, Any] = {
        "ok": True,
        "agent": "spawn_team_ops_guest_job",
        "outcome": outcome,
        "guest_metrics": wall,
        "remediation_plan": plan,
        "thresholds": {
            "disk_warn": disk_warn_pct(),
            "disk_crit": disk_crit_pct(),
            "load_warn_ratio": load_warn_ratio(),
            "load_crit_ratio": load_crit_ratio(),
        },
        "spawned": False,
        "task_id": None,
    }

    sig = _signature(wall)
    # Anti-spam : même signature sous cooldown → skip (déjà couvert par _should_spawn)
    if persist and sig and sig == st.get("last_signature") and not _should_spawn(outcome, st):
        result["reply"] = f"Sonde {outcome} — signature inchangée / cooldown"
        st["last_check_ts"] = time.time()
        st["last_outcome"] = outcome
        save_json_state(state_path(), st)
        return result

    if _should_spawn(outcome, st):
        try:
            payload = create_and_run_team_task(
                role="ops",
                objective=default_objective(outcome, stressed_labels),
                actor_id=spawn_actor_id(),
                context={
                    "_team_ops_guest_spawn": True,
                    "ops_kind": "guest_metrics",
                    "guest_metrics": wall,
                    "remediation_plan": plan,
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
                        "last_signature": sig,
                        "last_alerts": wall.get("alerts") or [],
                    },
                )
        except (urllib.error.URLError, OSError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
            result["ok"] = False
            result["error"] = str(exc)
            result["reply"] = f"Échec playbook ops guest : {exc}"
    else:
        result["reply"] = f"Sonde {outcome} — pas de nouvelle tâche ops (OK ou cooldown)"

    if persist and not result.get("spawned"):
        st["last_check_ts"] = time.time()
        st["last_outcome"] = outcome
        st["last_signature"] = sig
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
