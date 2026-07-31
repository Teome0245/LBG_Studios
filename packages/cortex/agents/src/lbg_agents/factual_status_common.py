"""Helpers communs pour réponses de statut factuel."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


def orchestrator_base() -> str:
    return os.environ.get("LBG_ORCHESTRATOR_URL", "http://127.0.0.1:8010").rstrip("/")


def fetch_json(url: str, *, timeout: float = 4.0) -> dict[str, Any] | list[Any] | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            return payload if isinstance(payload, (dict, list)) else None
    except (urllib.error.URLError, OSError, TimeoutError, json.JSONDecodeError, ValueError):
        return None


def fetch_team_tasks(*, limit: int = 12, actor_id: str | None = None, role: str | None = None) -> list[dict[str, Any]]:
    base = orchestrator_base()
    params = [f"limit={max(1, min(limit, 50))}"]
    if actor_id:
        params.append(f"actor_id={urllib.parse.quote(actor_id)}")
    if role:
        params.append(f"role={urllib.parse.quote(role)}")
    url = f"{base}/v1/team/tasks?{'&'.join(params)}"
    payload = fetch_json(url)
    if not isinstance(payload, dict):
        return []
    tasks = payload.get("tasks")
    return [t for t in tasks if isinstance(t, dict)] if isinstance(tasks, list) else []


def probe_http_health(url: str, *, timeout: float = 2.5) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            body = resp.read(512).decode("utf-8", errors="replace")
            return {"url": url, "ok": 200 <= resp.status < 300, "status": resp.status, "body_preview": body[:120]}
    except urllib.error.HTTPError as e:
        return {"url": url, "ok": False, "status": e.code, "error": str(e)[:120]}
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        return {"url": url, "ok": False, "status": None, "error": str(e)[:120]}


def status_result(
    *,
    agent: str,
    handler: str,
    actor_id: str,
    reply: str,
    status: dict[str, Any],
    source: str,
) -> dict[str, Any]:
    return {
        "agent": agent,
        "handler": handler,
        "ok": True,
        "actor_id": actor_id,
        "status": status,
        "remote": {"reply": reply, "source": source},
        "reply": reply,
    }
