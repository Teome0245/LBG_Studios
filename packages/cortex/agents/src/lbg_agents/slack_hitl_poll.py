"""Poll Slack #lbg-ops — commandes texte HITL L2 (LAN, sans URL publique).

Usage::

    PYTHONPATH=agents/src python -m lbg_agents.slack_hitl_poll
    # ou une passe : LBG_SLACK_HITL_POLL_ONCE=1 python -m lbg_agents.slack_hitl_poll

Prérequis : ``LBG_SLACK_BOT_TOKEN``, ``LBG_SLACK_CHANNEL_OPS``, allowlist.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from lbg_agents.slack_hitl import (
    handle_text_command,
    hitl_enabled,
    reply_in_channel,
    slack_api,
    slack_bot_token,
)
from lbg_agents.ops_notify import slack_channel_ops

_TRUE = ("1", "true", "yes", "on")
DEFAULT_STATE = "/var/lib/lbg/slack_hitl_poll_state.json"


def state_path() -> Path:
    return Path(os.environ.get("LBG_SLACK_HITL_POLL_STATE", DEFAULT_STATE).strip())


def poll_interval_s() -> float:
    try:
        return max(5.0, float(os.environ.get("LBG_SLACK_HITL_POLL_S", "20")))
    except ValueError:
        return 20.0


def _load_state() -> dict[str, Any]:
    try:
        return json.loads(state_path().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_state(st: dict[str, Any]) -> None:
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def fetch_history(*, channel: str, oldest: str = "") -> list[dict[str, Any]]:
    payload: dict[str, Any] = {"channel": channel, "limit": 30}
    if oldest:
        payload["oldest"] = oldest
    out = slack_api("conversations.history", payload)
    if not out.get("ok"):
        return []
    msgs = out.get("messages")
    return [m for m in msgs if isinstance(m, dict)] if isinstance(msgs, list) else []


def process_once() -> dict[str, Any]:
    if not hitl_enabled():
        return {"ok": True, "skipped": True, "reason": "hitl_disabled"}
    if not slack_bot_token():
        return {"ok": False, "skipped": True, "error": "LBG_SLACK_BOT_TOKEN manquant"}
    channel = slack_channel_ops()
    if not channel:
        return {"ok": False, "skipped": True, "error": "LBG_SLACK_CHANNEL_OPS manquant"}

    st = _load_state()
    oldest = str(st.get("oldest_ts") or "")
    seen: set[str] = set(st.get("seen_ts") or [])
    messages = fetch_history(channel=channel, oldest=oldest)
    handled = 0
    errors: list[str] = []
    newest = oldest

    # history est newest-first
    for msg in reversed(messages):
        ts = str(msg.get("ts") or "")
        if not ts or ts in seen:
            continue
        if msg.get("bot_id") or msg.get("subtype"):
            seen.add(ts)
            newest = max(newest, ts) if newest else ts
            continue
        user = str(msg.get("user") or "")
        text = str(msg.get("text") or "")
        result = handle_text_command(text=text, user_id=user)
        seen.add(ts)
        newest = max(newest, ts) if newest else ts
        if result is None:
            continue
        handled += 1
        if result.get("ok"):
            reply = (
                f"✅ `{result.get('short_id')}` — {result.get('action')} OK"
                if result.get("action") == "approve_run"
                else f"⏹ `{result.get('short_id')}` — reject/cancel OK"
            )
        else:
            reply = f"❌ HITL : {result.get('error')}"
            errors.append(str(result.get("error")))
        reply_in_channel(channel, reply, thread_ts=ts)

    # garder seen borné
    seen_list = sorted(seen)[-200:]
    st["seen_ts"] = seen_list
    if newest:
        # remonter légèrement pour ne pas rater overlap
        st["oldest_ts"] = newest
    st["last_poll_ts"] = time.time()
    _save_state(st)
    return {"ok": True, "handled": handled, "scanned": len(messages), "errors": errors}


def main() -> None:
    once = os.environ.get("LBG_SLACK_HITL_POLL_ONCE", "0").strip().lower() in _TRUE
    if once:
        print(json.dumps(process_once(), ensure_ascii=False))
        return
    while True:
        out = process_once()
        print(json.dumps(out, ensure_ascii=False), flush=True)
        time.sleep(poll_interval_s())


if __name__ == "__main__":
    main()
