"""Actions Team L2 — pending via orchestrateur, approve/run via Pilot."""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any

import httpx

from src.http_timeouts import httpx_timeout
from src.settings import get_settings

logger = logging.getLogger("lbg.team_actions")

_session_nudge_lock = threading.Lock()
_SESSION_NUDGE_MAX = 200


def _session_nudge_path() -> Path:
    raw = os.environ.get(
        "LBG_L2_SESSION_NUDGE_PATH",
        "/var/lib/lbg/compagnon/l2_session_nudge.json",
    ).strip()
    return Path(raw or "/var/lib/lbg/compagnon/l2_session_nudge.json")


def _load_session_nudges() -> dict[str, float]:
    path = _session_nudge_path()
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        sessions = data.get("sessions") if isinstance(data, dict) else None
        if not isinstance(sessions, dict):
            return {}
        out: dict[str, float] = {}
        for k, v in sessions.items():
            try:
                out[str(k)] = float(v)
            except (TypeError, ValueError):
                continue
        return out
    except Exception:
        return {}


def _save_session_nudges(sessions: dict[str, float]) -> None:
    path = _session_nudge_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    items = sorted(sessions.items(), key=lambda kv: kv[1], reverse=True)[:_SESSION_NUDGE_MAX]
    payload = {"sessions": dict(items), "updated_ts": time.time()}
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def session_l2_already_nudged(conversation_id: str) -> bool:
    cid = (conversation_id or "default").strip() or "default"
    with _session_nudge_lock:
        return cid in _load_session_nudges()


def mark_session_l2_nudged(conversation_id: str) -> None:
    cid = (conversation_id or "default").strip() or "default"
    with _session_nudge_lock:
        sessions = _load_session_nudges()
        sessions[cid] = time.time()
        _save_session_nudges(sessions)


def _pilot_base() -> str:
    settings = get_settings()
    return str(settings.cortex_pilot_url or "").rstrip("/")


def _orchestrator_base() -> str:
    settings = get_settings()
    raw = (
        getattr(settings, "cortex_orchestrator_url", None)
        or os.environ.get("CORTEX_ORCHESTRATOR_URL")
        or ""
    )
    return str(raw).strip().rstrip("/")


def _timeout() -> httpx.Timeout:
    settings = get_settings()
    return httpx_timeout(read=float(settings.cortex_pilot_timeout_s))


def needs_l2_approval(task: dict[str, Any]) -> bool:
    status = str(task.get("status") or "").lower()
    if status == "review":
        return True
    if task.get("approval_required") is True and status in (
        "queued",
        "pending",
        "review",
        "waiting_approval",
        "",
    ):
        ctx = task.get("context") if isinstance(task.get("context"), dict) else {}
        if ctx.get("approved") is True:
            return False
        return True
    return False


def approval_card_from_task(task: dict[str, Any]) -> dict[str, Any] | None:
    tid = str(task.get("id") or task.get("task_id") or "")
    if not tid:
        return None
    if not needs_l2_approval(task) and str(task.get("status") or "") not in ("queued", "review"):
        if not task.get("approval_required"):
            return None
    return {
        "task_id": tid,
        "role": str(task.get("role") or ""),
        "role_label": str(task.get("role_label") or task.get("label") or task.get("role") or ""),
        "objective": str(task.get("objective") or "")[:240],
        "status": str(task.get("status") or ""),
        "approval_required": bool(task.get("approval_required")),
        "needs_token": True,
    }


def approval_payload_from_tasks(tasks: list[dict[str, Any]]) -> dict[str, Any] | None:
    cards: list[dict[str, Any]] = []
    for t in tasks:
        if not isinstance(t, dict):
            continue
        if not needs_l2_approval(t):
            continue
        card = approval_card_from_task(t)
        if card:
            cards.append(card)
    if not cards:
        return None
    return {
        "title": "Validation humaine (L2)",
        "tasks": cards,
        "hint": "Token d'approbation Team — Pilot `#/team/office` ou cartes ci-dessous.",
    }


async def list_pending_approvals(*, limit: int = 20) -> dict[str, Any]:
    """Source de vérité : GET orchestrator /v1/team/pending (aligné Fleet)."""
    orch = _orchestrator_base()
    timeout = _timeout()
    if orch:
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.get(f"{orch}/v1/team/pending", params={"limit": int(limit)})
            if r.status_code < 400:
                data = r.json()
                if isinstance(data, dict) and data.get("ok") is not False:
                    return data
        except Exception as e:
            logger.warning("list_pending via orchestrator failed: %s", e)

    base = _pilot_base()
    if not base:
        return {"ok": False, "error": "CORTEX_ORCHESTRATOR_URL / CORTEX_PILOT_URL non configuré", "tasks": []}
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(f"{base}/v1/pilot/team/tasks", params={"limit": int(limit)})
        if r.status_code >= 400:
            return {"ok": False, "error": f"HTTP {r.status_code}", "tasks": []}
        data = r.json()
        tasks = data.get("tasks") if isinstance(data, dict) else []
        if not isinstance(tasks, list):
            tasks = []
        pending = [t for t in tasks if isinstance(t, dict) and needs_l2_approval(t)]
        payload = approval_payload_from_tasks(pending)
        return {
            "ok": True,
            "count": len(pending),
            "tasks": pending,
            "approval": payload,
        }
    except Exception as e:
        logger.warning("list_pending_approvals failed: %s", e)
        return {"ok": False, "error": f"{type(e).__name__}: {e}", "tasks": []}


async def maybe_attach_session_l2_nudge(
    result: dict[str, Any],
    *,
    conversation_id: str | None,
) -> dict[str, Any]:
    """Une fois par conversation Compagnon : rappel L2 + cartes si pending > 0."""
    if not isinstance(result, dict):
        return result
    cid = (conversation_id or "default").strip() or "default"

    # Déjà signalé dans cette réponse (status / « approbations L2 ») → compte comme le rappel session.
    existing = result.get("approval")
    if isinstance(existing, dict) and existing.get("tasks"):
        if not session_l2_already_nudged(cid):
            mark_session_l2_nudged(cid)
        return result

    if session_l2_already_nudged(cid):
        return result

    pending = await list_pending_approvals(limit=10)
    approval = pending.get("approval") if isinstance(pending, dict) else None
    n = int(pending.get("count") or 0) if isinstance(pending, dict) else 0
    if not approval or n <= 0:
        return result

    mark_session_l2_nudged(cid)
    out = dict(result)
    out["approval"] = approval
    out["l2_session_nudge"] = True
    suffix = (
        f"\n\n*(Rappel session)* **{n} validation(s) L2** en attente — "
        "cartes ci-dessous ou panneau **Approbations L2**."
    )
    content = str(out.get("content") or out.get("response") or "").rstrip()
    out["content"] = content + suffix if content else suffix.strip()
    out["response"] = out["content"]
    return out


async def fetch_tasks_by_ids(task_ids: list[str]) -> list[dict[str, Any]]:
    base = _pilot_base()
    if not base or not task_ids:
        return []
    timeout = _timeout()
    out: list[dict[str, Any]] = []
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            for tid in task_ids[:12]:
                r = await client.get(f"{base}/v1/pilot/team/tasks/{tid}")
                if r.status_code >= 400:
                    continue
                data = r.json()
                if isinstance(data, dict) and data.get("id"):
                    out.append(data)
    except Exception as e:
        logger.warning("fetch_tasks_by_ids failed: %s", e)
    return out


async def approve_task(task_id: str, token: str) -> dict[str, Any]:
    base = _pilot_base()
    if not base:
        return {"ok": False, "error": "CORTEX_PILOT_URL non configuré"}
    timeout = _timeout()
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(
            f"{base}/v1/pilot/team/tasks/{task_id}/approve",
            json={"token": token},
        )
    if r.status_code >= 400:
        return {"ok": False, "error": f"HTTP {r.status_code}: {r.text[:200]}"}
    data = r.json() if r.content else {}
    if isinstance(data, dict):
        data.setdefault("ok", True)
        return data
    return {"ok": True, "raw": data}


async def run_task(task_id: str, token: str | None = None) -> dict[str, Any]:
    base = _pilot_base()
    if not base:
        return {"ok": False, "error": "CORTEX_PILOT_URL non configuré"}
    timeout = _timeout()
    body: dict[str, Any] = {}
    if token:
        body["approval_token"] = token
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(
            f"{base}/v1/pilot/team/tasks/{task_id}/run",
            json=body,
        )
    if r.status_code >= 400:
        return {"ok": False, "error": f"HTTP {r.status_code}: {r.text[:200]}"}
    data = r.json() if r.content else {}
    if isinstance(data, dict):
        data.setdefault("ok", True)
        return data
    return {"ok": True, "raw": data}
