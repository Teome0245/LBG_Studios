"""Présence Agents (D7) — bus events local (SSE + Unix socket) + décisions Allow/Deny.

Opt-in : LBG_SESSION_ISLAND_ENABLED=1
Fail-open : LBG_SESSION_ISLAND_FAIL_OPEN=1 (défaut)
Timeout : LBG_SESSION_ISLAND_APPROVAL_TIMEOUT_S (défaut 60)
Socket : $XDG_RUNTIME_DIR/lbg-presence-agents.sock
"""

from __future__ import annotations

import asyncio
import json
import os
import queue
import socket
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncIterator, Deque

_EVENTS: Deque[dict[str, Any]] = deque(maxlen=200)
_SUBSCRIBERS: list[asyncio.Queue[dict[str, Any] | None]] = []
_LOCK = threading.Lock()
_PENDING: dict[str, "_PendingApproval"] = {}
_SOCKET_SERVER: Any = None
_SOCKET_THREAD: threading.Thread | None = None
_SOCKET_OUTBOX: queue.Queue[dict[str, Any]] = queue.Queue(maxsize=200)


def enabled() -> bool:
    return (os.environ.get("LBG_SESSION_ISLAND_ENABLED") or "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def fail_open() -> bool:
    raw = (os.environ.get("LBG_SESSION_ISLAND_FAIL_OPEN") or "1").strip().lower()
    return raw in {"1", "true", "yes", "on", ""}


def approval_timeout_s() -> float:
    try:
        return max(5.0, float(os.environ.get("LBG_SESSION_ISLAND_APPROVAL_TIMEOUT_S") or "60"))
    except ValueError:
        return 60.0


def socket_path() -> Path:
    runtime = os.environ.get("XDG_RUNTIME_DIR") or f"/tmp/lbg-{os.getuid()}"
    return Path(runtime) / "lbg-presence-agents.sock"


def _truncate(text: str, n: int = 80) -> str:
    s = " ".join(str(text or "").split())
    return s if len(s) <= n else s[: n - 1] + "…"


def emit(
    event: str,
    *,
    session_id: str,
    agent: str = "opencode",
    persona: str | None = None,
    summary: str = "",
    detail: dict[str, Any] | None = None,
    approval_id: str | None = None,
) -> dict[str, Any]:
    """Émet un event (no-op si flag off). Thread-safe."""
    payload = {
        "v": 1,
        "event": event,
        "session_id": session_id,
        "agent": agent,
        "persona": persona,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary": _truncate(summary),
        "detail": detail or {},
        "approval_id": approval_id,
    }
    if not enabled():
        return payload
    with _LOCK:
        _EVENTS.append(payload)
        subs = list(_SUBSCRIBERS)
    for q in subs:
        try:
            q.put_nowait(payload)
        except Exception:
            pass
    _broadcast_socket(payload)
    return payload


def recent(limit: int = 50) -> list[dict[str, Any]]:
    with _LOCK:
        return list(_EVENTS)[-limit:]


def subscribe() -> asyncio.Queue[dict[str, Any] | None]:
    q: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue(maxsize=100)
    with _LOCK:
        _SUBSCRIBERS.append(q)
    return q


def unsubscribe(q: asyncio.Queue[dict[str, Any] | None]) -> None:
    with _LOCK:
        if q in _SUBSCRIBERS:
            _SUBSCRIBERS.remove(q)


async def stream_sse() -> AsyncIterator[str]:
    """Génère des lignes SSE. Envoie d'abord le backlog récent."""
    q = subscribe()
    try:
        for ev in recent(20):
            yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
        while True:
            try:
                item = await asyncio.wait_for(q.get(), timeout=15.0)
            except asyncio.TimeoutError:
                yield ": keepalive\n\n"
                continue
            if item is None:
                break
            yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
    finally:
        unsubscribe(q)


@dataclass
class _PendingApproval:
    approval_id: str
    session_id: str
    created: float = field(default_factory=time.time)
    event: threading.Event = field(default_factory=threading.Event)
    decision: str | None = None
    scope: str | None = None


def request_approval(
    *,
    session_id: str,
    agent: str,
    summary: str,
    detail: dict[str, Any] | None = None,
    persona: str | None = None,
) -> str:
    """Crée une demande Allow/Deny ; retourne approval_id. No-op id si flag off."""
    aid = f"appr-{uuid.uuid4().hex[:10]}"
    if not enabled():
        return aid
    pending = _PendingApproval(approval_id=aid, session_id=session_id)
    with _LOCK:
        _PENDING[aid] = pending
    emit(
        "session.approval_needed",
        session_id=session_id,
        agent=agent,
        persona=persona,
        summary=summary,
        detail=detail,
        approval_id=aid,
    )
    return aid


def wait_decision(approval_id: str, timeout_s: float | None = None) -> dict[str, Any]:
    """Attend une décision. Fail-open → deny soft si timeout."""
    to = approval_timeout_s() if timeout_s is None else float(timeout_s)
    with _LOCK:
        pending = _PENDING.get(approval_id)
    if pending is None:
        return {"decision": "deny", "scope": "once", "reason": "unknown_approval", "timed_out": False}
    ok = pending.event.wait(timeout=to)
    with _LOCK:
        _PENDING.pop(approval_id, None)
    if not ok:
        return {
            "decision": "deny" if fail_open() else "deny",
            "scope": "once",
            "reason": "timeout",
            "timed_out": True,
            "fail_open": fail_open(),
        }
    return {
        "decision": pending.decision or "deny",
        "scope": pending.scope or "once",
        "reason": "user",
        "timed_out": False,
    }


def apply_decision(body: dict[str, Any]) -> dict[str, Any]:
    aid = str(body.get("approval_id") or "").strip()
    decision = str(body.get("decision") or "").strip().lower()
    scope = str(body.get("scope") or "once").strip().lower()
    if decision not in {"allow", "deny"}:
        return {"ok": False, "error": "decision must be allow|deny"}
    if scope not in {"once", "session"}:
        scope = "once"
    with _LOCK:
        pending = _PENDING.get(aid)
        if pending is None:
            return {"ok": False, "error": "unknown or expired approval_id", "approval_id": aid}
        pending.decision = decision
        pending.scope = scope
        pending.event.set()
    return {"ok": True, "approval_id": aid, "decision": decision, "scope": scope}


def new_session_id(prefix: str = "cli") -> str:
    return f"{prefix}-{time.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"


# --- Unix socket (newline JSON) ---

def _broadcast_socket(payload: dict[str, Any]) -> None:
    if not enabled():
        return
    try:
        _SOCKET_OUTBOX.put_nowait(payload)
    except queue.Full:
        pass


def start_socket_server() -> None:
    """Démarre le serveur Unix socket en thread daemon (si enabled)."""
    global _SOCKET_SERVER, _SOCKET_THREAD

    if not enabled():
        return
    if _SOCKET_THREAD and _SOCKET_THREAD.is_alive():
        return

    path = socket_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            path.unlink()
        except OSError:
            pass

    clients: list[socket.socket] = []
    clients_lock = threading.Lock()

    def accept_loop() -> None:
        srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(str(path))
        srv.listen(8)
        srv.settimeout(1.0)
        global _SOCKET_SERVER
        _SOCKET_SERVER = srv
        try:
            while True:
                try:
                    conn, _ = srv.accept()
                    conn.settimeout(0.1)
                    with clients_lock:
                        clients.append(conn)
                except socket.timeout:
                    # drain outbox → clients
                    try:
                        while True:
                            payload = _SOCKET_OUTBOX.get_nowait()
                            line = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
                            dead: list[socket.socket] = []
                            with clients_lock:
                                for c in clients:
                                    try:
                                        c.sendall(line)
                                    except OSError:
                                        dead.append(c)
                                for c in dead:
                                    clients.remove(c)
                                    try:
                                        c.close()
                                    except OSError:
                                        pass
                    except queue.Empty:
                        pass
                except OSError:
                    break
        finally:
            try:
                srv.close()
            except OSError:
                pass
            if path.exists():
                try:
                    path.unlink()
                except OSError:
                    pass

    _SOCKET_THREAD = threading.Thread(target=accept_loop, name="presence-agents-sock", daemon=True)
    _SOCKET_THREAD.start()


def status() -> dict[str, Any]:
    with _LOCK:
        pending_n = len(_PENDING)
        sub_n = len(_SUBSCRIBERS)
        ev_n = len(_EVENTS)
    return {
        "enabled": enabled(),
        "fail_open": fail_open(),
        "approval_timeout_s": approval_timeout_s(),
        "socket_path": str(socket_path()),
        "socket_alive": bool(_SOCKET_THREAD and _SOCKET_THREAD.is_alive()),
        "subscribers": sub_n,
        "pending_approvals": pending_n,
        "events_buffered": ev_n,
    }
