"""Push Slack des tâches Team L2 pending (miroir matrix_notify). ADR 0021 S2."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from lbg_agents.ops_notify import send_l2_pending

_TRUE = ("1", "true", "yes", "on")
DEFAULT_STATE = "/var/lib/lbg/slack_notify_state.json"


def notify_disabled() -> bool:
    return os.environ.get("LBG_SLACK_NOTIFY_DISABLE", "0").strip().lower() in _TRUE


def state_path() -> Path:
    return Path(os.environ.get("LBG_SLACK_NOTIFY_STATE_PATH", DEFAULT_STATE).strip())


def orch_base() -> str:
    return (os.environ.get("LBG_ORCHESTRATOR_URL") or "http://127.0.0.1:8010").rstrip("/")


def _load_state() -> dict[str, Any]:
    path = state_path()
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"notified": {}}


def _save_state(st: dict[str, Any]) -> None:
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def _http_get(url: str) -> tuple[int, dict[str, Any]]:
    req = urllib.request.Request(url, headers={"Accept": "application/json"}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=20.0) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            code = int(resp.status)
    except urllib.error.HTTPError as e:
        code = int(e.code)
        raw = e.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        return 502, {"ok": False, "error": str(e)}
    try:
        parsed = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        parsed = {"raw": raw[:300]}
    return code, parsed if isinstance(parsed, dict) else {"payload": parsed}


def fetch_pending_tasks() -> list[dict[str, Any]]:
    pending: list[dict[str, Any]] = []
    for status in ("review", "queued"):
        code, body = _http_get(f"{orch_base()}/v1/team/tasks?status={status}&limit=50")
        if code >= 400:
            continue
        tasks = body.get("tasks") if isinstance(body.get("tasks"), list) else []
        for t in tasks:
            if not isinstance(t, dict):
                continue
            if status == "review" or t.get("approval_required"):
                pending.append(t)
    return pending


def run_slack_notify(*, force: bool = False) -> dict[str, Any]:
    if notify_disabled():
        return {"ok": True, "skipped": True, "reason": "LBG_SLACK_NOTIFY_DISABLE"}

    st = _load_state()
    notified: dict[str, Any] = st.setdefault("notified", {})
    if not isinstance(notified, dict):
        notified = {}
        st["notified"] = notified

    pending = fetch_pending_tasks()
    sent: list[dict[str, Any]] = []
    skipped = 0
    for task in pending:
        tid = str(task.get("id") or "")
        if not tid:
            continue
        key = f"{tid}:pending"
        if key in notified and not force:
            skipped += 1
            continue
        out = send_l2_pending(task)
        sent.append({"task_id": tid, "out": out})
        if out.get("ok"):
            notified[key] = {"ts": time.time()}

    _save_state(st)
    return {
        "ok": True,
        "pending": len(pending),
        "sent": len(sent),
        "skipped": skipped,
        "results": sent,
    }


def main() -> None:
    import pprint

    pprint.pp(run_slack_notify())


if __name__ == "__main__":
    main()
