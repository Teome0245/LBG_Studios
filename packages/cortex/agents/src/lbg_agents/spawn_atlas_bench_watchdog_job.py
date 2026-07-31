"""Timer core 140 : Atlas bench watchdog (seuil + retry KO + alerte Element)."""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

from lbg_agents.team_job_spawn import load_json_state, save_json_state, truthy


def job_enabled() -> bool:
    return truthy(os.environ.get("LBG_ATLAS_BENCH_WATCHDOG_JOB_ENABLED", "1"))


def state_path() -> Path:
    raw = os.environ.get("LBG_ATLAS_BENCH_WATCHDOG_STATE", "").strip()
    if raw:
        return Path(raw)
    return Path("/var/lib/lbg/atlas_bench_watchdog/state.json")


def cooldown_s() -> float:
    try:
        return max(3600.0, float(os.environ.get("LBG_ATLAS_BENCH_WATCHDOG_COOLDOWN_S", "86400")))
    except ValueError:
        return 86400.0


def repo_root() -> Path:
    return Path(os.environ.get("LBG_IA_MMO_ROOT", "/opt/LBG_IA_MMO"))


def python_bin() -> str:
    return os.environ.get("LBG_BENCH_PYTHON", str(repo_root() / ".venv/bin/python"))


def run_watchdog_subprocess() -> dict[str, Any]:
    root = repo_root()
    script = root / "infra/scripts/atlas_bench_watchdog.py"
    if not script.is_file():
        return {"ok": False, "error": f"script absent: {script}"}
    proc = subprocess.run(
        [python_bin(), str(script)],
        cwd=str(root),
        capture_output=True,
        text=True,
        timeout=int(os.environ.get("LBG_ATLAS_BENCH_WATCHDOG_TIMEOUT_S", "3600")),
        check=False,
    )
    out_tail = (proc.stdout or "")[-4000:]
    try:
        parsed = json.loads(out_tail.strip().split("\n")[-1])
    except (json.JSONDecodeError, IndexError):
        parsed = {"ok": proc.returncode == 0, "raw_tail": out_tail, "stderr": (proc.stderr or "")[-1000:]}
    parsed["exit_code"] = proc.returncode
    return parsed


def run_spawn(*, persist: bool = True) -> dict[str, Any]:
    if not job_enabled():
        return {
            "ok": True,
            "outcome": "skipped",
            "reply": "LBG_ATLAS_BENCH_WATCHDOG_JOB_ENABLED=0",
        }

    st = load_json_state(state_path()) if persist else {}
    last = float(st.get("last_spawn_ts") or 0)
    if last and time.time() - last < cooldown_s():
        return {
            "ok": True,
            "outcome": "cooldown",
            "reply": f"Cooldown actif ({int(cooldown_s())}s)",
        }

    result: dict[str, Any] = {
        "ok": True,
        "agent": "spawn_atlas_bench_watchdog_job",
        "outcome": "ran",
    }
    try:
        wd = run_watchdog_subprocess()
        result["watchdog"] = wd
        oks = int(wd.get("oks_after_retry") or 0)
        min_oks = int(wd.get("min_oks") or os.environ.get("LBG_ATLAS_BENCH_MIN_OKS", "3"))
        result["ok"] = bool(wd.get("ok", oks >= min_oks))
        result["outcome"] = "alert" if wd.get("alert_below_threshold") else "ok"
        result["reply"] = f"Atlas bench watchdog {oks}/{wd.get('total')} (seuil {min_oks})"
        if persist:
            save_json_state(
                state_path(),
                {
                    "last_spawn_ts": time.time(),
                    "last_oks": oks,
                    "last_total": wd.get("total"),
                    "last_alert": wd.get("alert_below_threshold"),
                    "merged_path": wd.get("merged_path"),
                },
            )
    except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
        result["ok"] = False
        result["outcome"] = "error"
        result["error"] = str(exc)
        result["reply"] = f"Échec watchdog bench: {exc}"

    return result


def main() -> int:
    result = run_spawn()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result.get("ok"):
        return 2
    if result.get("outcome") == "alert":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
