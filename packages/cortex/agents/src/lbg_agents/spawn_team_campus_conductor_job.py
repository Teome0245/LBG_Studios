"""Timer core 140 : tick Campus Conductor (Lyra) — drain file queued."""

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
    return truthy(os.environ.get("LBG_TEAM_CAMPUS_CONDUCTOR_JOB_ENABLED", "1"))


def orchestrator_url() -> str:
    return os.environ.get("LBG_ORCHESTRATOR_URL", "http://127.0.0.1:8010").strip().rstrip("/")


def state_path() -> Path:
    raw = os.environ.get("LBG_TEAM_CAMPUS_CONDUCTOR_JOB_STATE", "").strip()
    if raw:
        return Path(raw)
    return Path("/var/lib/lbg/team_campus_conductor/state.json")


def _api_json(method: str, url: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None
    headers = {"Content-Type": "application/json"}
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw.strip() else {}


def run_spawn(*, persist: bool = True, dry_run: bool = False) -> dict[str, Any]:
    if not job_enabled():
        return {"ok": True, "outcome": "skipped", "agent": "spawn_team_campus_conductor_job"}

    result: dict[str, Any] = {"ok": True, "agent": "spawn_team_campus_conductor_job"}
    try:
        report = _api_json(
            "POST",
            f"{orchestrator_url()}/v1/team/campus/act",
            {"dry_run": dry_run},
        )
        result["report"] = report
        result["outcome"] = report.get("outcome") or report.get("acted_as") or "done"
        result["ok"] = bool(report.get("ok", True))
        # Timer actif mais conductor coupé = file queued bloquée (régression push_secrets).
        if result.get("outcome") == "disabled" or report.get("enabled") is False:
            result["ok"] = False
            result["error"] = (
                "campus conductor disabled — set LBG_TEAM_CAMPUS_CONDUCTOR_ENABLED=1 "
                "on orchestrator (env + drop-in campus-conductor.conf)"
            )
        if persist:
            save_json_state(
                state_path(),
                {
                    "last_tick_ts": time.time(),
                    "last_outcome": result["outcome"],
                    "mode": (report.get("decision") or {}).get("mode"),
                    "started": (report.get("started") or [])[:5],
                    "running_count": report.get("running_count"),
                    "queued_count": report.get("queued_count"),
                },
            )
    except (urllib.error.URLError, OSError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
        result["ok"] = False
        result["outcome"] = "error"
        result["error"] = str(exc)
        if persist:
            st = load_json_state(state_path())
            st["last_error"] = str(exc)
            st["last_error_ts"] = time.time()
            save_json_state(state_path(), st)
    return result


def main() -> None:
    out = run_spawn(persist=True, dry_run=False)
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
