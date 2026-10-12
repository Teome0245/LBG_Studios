"""Timer 140 : inventaire réseau LAN + détection apparus / disparus.

Persiste ``/var/lib/lbg/network_inventory/state.json``.
Sur changement : spawn tâche Héphaïstos (ops) + notify Slack optionnel.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from lbg_agents.network_inventory import run_network_inventory
from lbg_agents.team_job_spawn import (
    create_and_run_team_task,
    load_json_state,
    save_json_state,
    task_run_summary,
    truthy,
)


def job_enabled() -> bool:
    return truthy(os.environ.get("LBG_NETWORK_INVENTORY_JOB_ENABLED", "1"))


def notify_on_change() -> bool:
    return truthy(os.environ.get("LBG_NETWORK_INVENTORY_NOTIFY", "0"))


def spawn_hephaistos_on_change() -> bool:
    return truthy(os.environ.get("LBG_NETWORK_INVENTORY_SPAWN_OPS", "1"))


def spawn_state_path() -> Path:
    raw = os.environ.get("LBG_NETWORK_INVENTORY_SPAWN_STATE", "").strip()
    if raw:
        return Path(raw)
    return Path("/var/lib/lbg/network_inventory/spawn_state.json")


def spawn_cooldown_s() -> float:
    try:
        return max(300.0, float(os.environ.get("LBG_NETWORK_INVENTORY_SPAWN_COOLDOWN_S", "1800")))
    except ValueError:
        return 1800.0


def _slim_inventory(out: dict[str, Any], diff: dict[str, Any]) -> dict[str, Any]:
    """Payload compact pour la tâche Team (évite un second scan)."""
    return {
        "ok": bool(out.get("ok")),
        "n_devices": out.get("n_devices"),
        "n_present": out.get("n_present"),
        "by_role": out.get("by_role"),
        "diff": diff,
        "cast_speakers": out.get("cast_speakers"),
        "reply": out.get("reply"),
        "source": out.get("source"),
        "ts": out.get("ts") or time.time(),
    }


def _maybe_spawn_hephaistos(diff: dict[str, Any], slim: dict[str, Any]) -> dict[str, Any] | None:
    if not spawn_hephaistos_on_change():
        return {"skipped": True, "reason": "LBG_NETWORK_INVENTORY_SPAWN_OPS=0"}
    n_app = int(diff.get("n_appeared") or 0)
    n_dis = int(diff.get("n_disappeared") or 0)
    if n_app == 0 and n_dis == 0:
        return {"skipped": True, "reason": "stable"}
    st = load_json_state(spawn_state_path())
    last = float(st.get("last_spawn_ts") or 0)
    if last and time.time() - last < spawn_cooldown_s():
        return {"skipped": True, "reason": "cooldown", "last_spawn_ts": last}
    objective = (
        f"Héphaïstos — inventaire LAN : +{n_app} apparus / −{n_dis} disparus "
        f"({slim.get('n_present')}/{slim.get('n_devices')} présents)"
    )
    try:
        spawned = create_and_run_team_task(
            role="ops",
            objective=objective,
            actor_id=os.environ.get(
                "LBG_NETWORK_INVENTORY_ACTOR_ID", "system:network_inventory"
            ).strip(),
            context={
                "ops_kind": "network_inventory",
                "_team_network_inventory_spawn": True,
                "presence_agent_id": "studio_ops_hephaistos",
                "network_inventory": slim,
                "network_diff": diff,
            },
            run=True,
            timeout=120,
        )
        summary = task_run_summary(spawned)
        save_json_state(
            spawn_state_path(),
            {
                "last_spawn_ts": time.time(),
                "last_diff": {"n_appeared": n_app, "n_disappeared": n_dis},
                "last_task_id": summary.get("task_id"),
            },
        )
        return {"ok": True, **summary}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


def run_job(*, persist: bool = True) -> dict[str, Any]:
    if not job_enabled():
        return {
            "ok": True,
            "outcome": "skipped",
            "reply": "LBG_NETWORK_INVENTORY_JOB_ENABLED=0",
            "agent": "spawn_network_inventory_job",
        }

    out = run_network_inventory(
        actor_id=os.environ.get("LBG_NETWORK_INVENTORY_ACTOR_ID", "system:network_inventory").strip(),
        text="inventaire réseau LAN (timer)",
        context={
            "persist_state": persist,
            "freebox_lan": True,
            "cast_probe": True,
            "nas_probe": truthy(os.environ.get("LBG_NETWORK_INVENTORY_NAS_PROBE", "0")),
        },
    )
    diff = out.get("diff") if isinstance(out.get("diff"), dict) else {}
    n_app = int(diff.get("n_appeared") or 0)
    n_dis = int(diff.get("n_disappeared") or 0)
    changed = n_app > 0 or n_dis > 0
    slim = _slim_inventory(out, diff)
    result: dict[str, Any] = {
        "ok": bool(out.get("ok")),
        "agent": "spawn_network_inventory_job",
        "outcome": "changed" if changed else "stable",
        "n_devices": out.get("n_devices"),
        "n_present": out.get("n_present"),
        "by_role": out.get("by_role"),
        "diff": diff,
        "cast_speakers": out.get("cast_speakers"),
        "reply": (
            f"Inventaire LAN : {out.get('n_present')}/{out.get('n_devices')} présents — "
            f"+{n_app} / −{n_dis}"
        ),
        "ts": time.time(),
    }

    if changed:
        result["hephaistos_spawn"] = _maybe_spawn_hephaistos(diff, slim)

    if changed and notify_on_change():
        try:
            from lbg_agents.ops_notify import send_text

            lines = [result["reply"], ""]
            for row in diff.get("appeared") or []:
                lines.append(f"+ {row.get('host')} — {row.get('label')} ({row.get('role')})")
            for row in diff.get("disappeared") or []:
                lines.append(f"− {row.get('host')} — {row.get('label')} ({row.get('role')})")
            send_text("\n".join(lines), channel="ops")
            result["notified"] = True
        except Exception as exc:  # noqa: BLE001
            result["notified"] = False
            result["notify_error"] = str(exc)

    return result


def main() -> int:
    out = run_job(persist=True)
    print(json.dumps(out, ensure_ascii=False))
    return 0 if out.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
