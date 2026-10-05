"""Persistance SQLite des tâches équipe virtuelle."""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
import uuid
from typing import Any

from team.models import VALID_PRIORITIES, VALID_ROLES, VALID_STATUSES, TeamTask

_SCHEMA = """
CREATE TABLE IF NOT EXISTS team_tasks (
    id TEXT PRIMARY KEY,
    role TEXT NOT NULL,
    objective TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued',
    priority TEXT NOT NULL DEFAULT 'normal',
    approval_required INTEGER NOT NULL DEFAULT 0,
    actor_id TEXT NOT NULL DEFAULT 'system:team',
    context_json TEXT NOT NULL DEFAULT '{}',
    result_json TEXT NOT NULL DEFAULT '{}',
    trace_id TEXT NOT NULL DEFAULT '',
    created_ts REAL NOT NULL,
    updated_ts REAL NOT NULL,
    stored_approval_token TEXT
);
CREATE INDEX IF NOT EXISTS idx_team_tasks_status ON team_tasks(status);
CREATE INDEX IF NOT EXISTS idx_team_tasks_role ON team_tasks(role);
CREATE TABLE IF NOT EXISTS team_messages (
    id TEXT PRIMARY KEY,
    from_agent TEXT NOT NULL,
    to_agent TEXT NOT NULL,
    kind TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    task_id TEXT NOT NULL DEFAULT '',
    actor_id TEXT NOT NULL DEFAULT 'system:team',
    created_ts REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_team_messages_task ON team_messages(task_id);
CREATE INDEX IF NOT EXISTS idx_team_messages_kind ON team_messages(kind);
CREATE INDEX IF NOT EXISTS idx_team_messages_from ON team_messages(from_agent);
CREATE INDEX IF NOT EXISTS idx_team_messages_to ON team_messages(to_agent);
CREATE INDEX IF NOT EXISTS idx_team_messages_ts ON team_messages(created_ts);
"""


def db_path() -> str:
    return os.environ.get("LBG_TEAM_DB_PATH", "/var/lib/lbg-ia-mmo/team_tasks.db").strip()


def team_enabled() -> bool:
    return os.environ.get("LBG_TEAM_ENABLED", "1").strip().lower() in ("1", "true", "yes", "on")


def plan_llm_enabled() -> bool:
    """Vague 2 — off par défaut (heuristique seule en Vague 1)."""
    return os.environ.get("LBG_TEAM_PLAN_LLM", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def reset_for_tests() -> None:
    """Vide la base en mémoire / fichier de test."""
    global _conn
    if _conn is not None:
        try:
            _conn.close()
        except Exception:
            pass
        _conn = None
    path = db_path()
    if path and path != ":memory:" and os.path.isfile(path):
        try:
            os.remove(path)
        except OSError:
            pass


def _connect() -> sqlite3.Connection:
    path = db_path()
    if path == ":memory:":
        conn = sqlite3.connect(":memory:", check_same_thread=False)
    else:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


_conn: sqlite3.Connection | None = None
_db_lock = threading.RLock()


def _safe_commit(conn: sqlite3.Connection) -> None:
    """Commit tolérant aux courses multi-thread (Lyra daemon threads)."""
    try:
        conn.commit()
    except sqlite3.OperationalError as exc:
        if "no transaction is active" not in str(exc).lower():
            raise


def _get_conn() -> sqlite3.Connection:
    global _conn
    with _db_lock:
        if _conn is None:
            _conn = _connect()
            _conn.executescript(_SCHEMA)
            _safe_commit(_conn)
        return _conn


def get_connection() -> sqlite3.Connection:
    """Connexion SQLite partagée (tâches + messages ADR 0019)."""
    return _get_conn()


def _row_to_task(row: sqlite3.Row) -> TeamTask:
    ctx_raw = row["context_json"] or "{}"
    res_raw = row["result_json"] or "{}"
    try:
        context = json.loads(ctx_raw)
    except json.JSONDecodeError:
        context = {}
    try:
        result = json.loads(res_raw)
    except json.JSONDecodeError:
        result = {}
    if not isinstance(context, dict):
        context = {}
    if not isinstance(result, dict):
        result = {}
    return TeamTask(
        id=row["id"],
        role=row["role"],  # type: ignore[arg-type]
        objective=row["objective"],
        status=row["status"],  # type: ignore[arg-type]
        priority=row["priority"],  # type: ignore[arg-type]
        approval_required=bool(row["approval_required"]),
        actor_id=row["actor_id"],
        context=context,
        result=result,
        trace_id=row["trace_id"] or "",
        created_ts=float(row["created_ts"]),
        updated_ts=float(row["updated_ts"]),
        stored_approval_token=row["stored_approval_token"],
    )


def create_task(
    *,
    role: str,
    objective: str,
    actor_id: str = "system:team",
    priority: str = "normal",
    approval_required: bool | None = None,
    context: dict[str, object] | None = None,
    approval_token: str | None = None,
    trace_id: str | None = None,
) -> TeamTask:
    if role not in VALID_ROLES:
        raise ValueError(f"role invalide: {role}")
    if priority not in VALID_PRIORITIES:
        raise ValueError(f"priority invalide: {priority}")
    now = time.time()
    task_id = str(uuid.uuid4())
    ctx = dict(context or {})
    if trace_id:
        ctx.setdefault("trace_id", trace_id)
    need_approval = approval_required if approval_required is not None else False
    # L2 sans jeton → status review dès la création (bureau des validations / presence).
    initial_status = "review" if (need_approval and not approval_token) else "queued"
    conn = _get_conn()
    with _db_lock:
        conn.execute(
            """
            INSERT INTO team_tasks (
                id, role, objective, status, priority, approval_required,
                actor_id, context_json, result_json, trace_id,
                created_ts, updated_ts, stored_approval_token
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, '{}', ?, ?, ?, ?)
            """,
            (
                task_id,
                role,
                objective,
                initial_status,
                priority,
                1 if need_approval else 0,
                actor_id,
                json.dumps(ctx, ensure_ascii=False),
                trace_id or str(ctx.get("trace_id") or ""),
                now,
                now,
                approval_token,
            ),
        )
        _safe_commit(conn)
    task = get_task(task_id)
    if task is not None:
        try:
            from team import presence as team_presence

            team_presence.emit_from_task(task, event="status_changed")
        except Exception:
            pass
    return task  # type: ignore[return-value]


def get_task(task_id: str) -> TeamTask | None:
    """Resolve by full UUID or unambiguous 8+ hex prefix (Element `valider <prefix>`)."""
    tid = (task_id or "").strip()
    if not tid:
        return None
    conn = _get_conn()
    row = conn.execute("SELECT * FROM team_tasks WHERE id = ?", (tid,)).fetchone()
    if row is not None:
        return _row_to_task(row)
    # Préfixe court (ex. 4ae3796a) — match exact sur le début de l'UUID
    compact = tid.lower().replace("-", "")
    if len(compact) < 8 or len(compact) > 32 or not all(c in "0123456789abcdef" for c in compact):
        return None
    rows = conn.execute(
        "SELECT * FROM team_tasks WHERE lower(replace(id, '-', '')) LIKE ? ORDER BY updated_ts DESC LIMIT 5",
        (compact + "%",),
    ).fetchall()
    if len(rows) == 1:
        return _row_to_task(rows[0])
    return None


def list_tasks(
    *,
    role: str | None = None,
    status: str | None = None,
    actor_id: str | None = None,
    limit: int = 100,
) -> list[TeamTask]:
    clauses: list[str] = []
    params: list[Any] = []
    if role:
        clauses.append("role = ?")
        params.append(role)
    if status:
        clauses.append("status = ?")
        params.append(status)
    if actor_id:
        clauses.append("actor_id = ?")
        params.append(actor_id)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    params.append(max(1, min(limit, 500)))
    conn = _get_conn()
    rows = conn.execute(
        f"SELECT * FROM team_tasks{where} ORDER BY updated_ts DESC LIMIT ?",
        params,
    ).fetchall()
    return [_row_to_task(r) for r in rows]


def update_task(
    task_id: str,
    *,
    status: str | None = None,
    result: dict[str, object] | None = None,
    context_patch: dict[str, object] | None = None,
    stored_approval_token: str | None = None,
    clear_approval_token: bool = False,
) -> TeamTask | None:
    task = get_task(task_id)
    if task is None:
        return None
    if status is not None:
        if status not in VALID_STATUSES:
            raise ValueError(f"status invalide: {status}")
        task.status = status  # type: ignore[assignment]
    if result is not None:
        task.result = dict(result)
    if context_patch:
        merged = dict(task.context)
        merged.update(context_patch)
        task.context = merged
    if clear_approval_token:
        task.stored_approval_token = None
    elif stored_approval_token is not None:
        task.stored_approval_token = stored_approval_token
    task.updated_ts = time.time()
    conn = _get_conn()
    with _db_lock:
        conn.execute(
            """
            UPDATE team_tasks SET
                status = ?, result_json = ?, context_json = ?,
                updated_ts = ?, stored_approval_token = ?
            WHERE id = ?
            """,
            (
                task.status,
                json.dumps(task.result, ensure_ascii=False),
                json.dumps(task.context, ensure_ascii=False),
                task.updated_ts,
                task.stored_approval_token,
                task_id,
            ),
        )
        _safe_commit(conn)
    try:
        from team import presence as team_presence

        team_presence.emit_from_task(task, event="status_changed")
    except Exception:
        pass
    return task
