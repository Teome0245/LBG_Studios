"""Timer 140 : Ops Health Pilot (perception → décision → notify/L2 si live).

Par défaut **dry-run** (`LBG_OPS_HEALTH_PILOT_DRY_RUN=1`) pour déploiement prudent.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from lbg_agents.team_job_spawn import load_json_state, save_json_state, truthy


def job_enabled() -> bool:
    return truthy(os.environ.get("LBG_OPS_HEALTH_PILOT_JOB_ENABLED", "1"))


def dry_run_default() -> bool:
    return truthy(os.environ.get("LBG_OPS_HEALTH_PILOT_DRY_RUN", "1"))


def notify_default() -> bool:
    # En dry-run, notify reste simulé côté playbook ; en live, défaut on.
    if dry_run_default():
        return truthy(os.environ.get("LBG_OPS_HEALTH_PILOT_NOTIFY", "0"))
    return truthy(os.environ.get("LBG_OPS_HEALTH_PILOT_NOTIFY", "1"))


def orchestrator_url() -> str:
    return os.environ.get("LBG_ORCHESTRATOR_URL", "http://127.0.0.1:8010").rstrip("/")


def state_path() -> Path:
    raw = os.environ.get("LBG_OPS_HEALTH_PILOT_JOB_STATE", "").strip()
    if raw:
        return Path(raw)
    return Path("/var/lib/lbg/ops_health_pilot/job_state.json")


def cooldown_s() -> float:
    try:
        return max(600.0, float(os.environ.get("LBG_OPS_HEALTH_PILOT_JOB_COOLDOWN_S", "10800")))
    except ValueError:
        return 10800.0


def cooldown_active(st: dict[str, Any], *, cooldown_s: float) -> bool:
    last = float(st.get("last_spawn_ts") or st.get("last_check_ts") or 0)
    if last <= 0:
        return False
    return (time.time() - last) < cooldown_s


def _post_playbook(*, dry_run: bool, notify: bool) -> dict[str, Any]:
    url = f"{orchestrator_url()}/v1/team/ops_health_pilot"
    body = json.dumps(
        {
            "dry_run": dry_run,
            "notify": notify,
            "spawn_l2_remediation": True,
            "include_smoke": truthy(os.environ.get("LBG_OPS_HEALTH_PILOT_INCLUDE_SMOKE", "0")),
            "actor_id": os.environ.get("LBG_OPS_HEALTH_PILOT_ACTOR_ID", "system:ops_health").strip(),
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
        data = json.loads(raw) if raw else {}
        return data if isinstance(data, dict) else {"ok": False, "error": "non_dict"}


def run_spawn(*, persist: bool = True) -> dict[str, Any]:
    if not job_enabled():
        return {
            "ok": True,
            "outcome": "skipped",
            "reply": "LBG_OPS_HEALTH_PILOT_JOB_ENABLED=0",
            "spawned": False,
        }

    st = load_json_state(state_path()) if persist else {}
    result: dict[str, Any] = {
        "ok": True,
        "agent": "spawn_ops_health_pilot_job",
        "spawned": False,
    }

    if cooldown_active(st, cooldown_s=cooldown_s()):
        result["outcome"] = "cooldown"
        result["reply"] = f"Cooldown actif ({int(cooldown_s())}s)"
        if persist:
            st["last_check_ts"] = time.time()
            save_json_state(state_path(), st)
        return result

    dry = dry_run_default()
    notify = notify_default()
    try:
        payload = _post_playbook(dry_run=dry, notify=notify)
        result["spawned"] = True
        result["playbook"] = payload
        result["outcome"] = "dry_run" if dry else ("remediate" if payload.get("decision") == "remediate" else "healthy")
        result["reply"] = (
            f"ops_health_pilot decision={payload.get('decision')} dry_run={dry} "
            f"task={payload.get('remediation_task_id') or '—'}"
        )
        if persist:
            save_json_state(
                state_path(),
                {
                    "last_spawn_ts": time.time(),
                    "last_check_ts": time.time(),
                    "last_decision": payload.get("decision"),
                    "last_dry_run": dry,
                    "last_task_id": payload.get("remediation_task_id"),
                },
            )
        return result
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:400]
        result["ok"] = False
        result["outcome"] = "http_error"
        result["reply"] = f"HTTP {exc.code}: {body}"
        return result
    except Exception as exc:
        result["ok"] = False
        result["outcome"] = "error"
        result["reply"] = str(exc)
        return result


def main() -> int:
    out = run_spawn(persist=True)
    print(json.dumps(out, ensure_ascii=False))
    return 0 if out.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
