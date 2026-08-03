"""Bus messages inter-agents Team (ADR 0019) — table SQLite team_messages."""

from __future__ import annotations

import json
import time
import uuid
from typing import Any

from team.plan_schema import TeamMessage, sanitize_payload, validate_message_fields
from team import store as team_store

_MESSAGES_SCHEMA = """
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


def messages_enabled() -> bool:
    return team_store.team_enabled()


def ensure_schema() -> None:
    conn = team_store.get_connection()
    conn.executescript(_MESSAGES_SCHEMA)
    conn.commit()


def _row_to_message(row: Any) -> TeamMessage:
    raw = row["payload_json"] or "{}"
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    return TeamMessage(
        id=row["id"],
        from_agent=row["from_agent"],
        to_agent=row["to_agent"],
        kind=row["kind"],
        payload=payload,
        task_id=row["task_id"] or "",
        created_ts=float(row["created_ts"]),
        actor_id=row["actor_id"] or "system:team",
    )


def append_message(
    *,
    from_agent: str,
    to_agent: str,
    kind: str,
    payload: dict[str, object] | None = None,
    task_id: str = "",
    actor_id: str = "system:team",
) -> TeamMessage:
    fa, ta, k = validate_message_fields(from_agent=from_agent, to_agent=to_agent, kind=kind)
    ensure_schema()
    msg_id = str(uuid.uuid4())
    now = time.time()
    clean_payload = sanitize_payload(payload or {})
    tid = (task_id or "").strip()
    conn = team_store.get_connection()
    conn.execute(
        """
        INSERT INTO team_messages (
            id, from_agent, to_agent, kind, payload_json, task_id, actor_id, created_ts
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            msg_id,
            fa,
            ta,
            k,
            json.dumps(clean_payload, ensure_ascii=False),
            tid,
            (actor_id or "system:team").strip() or "system:team",
            now,
        ),
    )
    conn.commit()
    return TeamMessage(
        id=msg_id,
        from_agent=fa,
        to_agent=ta,
        kind=k,
        payload=clean_payload,
        task_id=tid,
        created_ts=now,
        actor_id=(actor_id or "system:team").strip() or "system:team",
    )


def list_messages(
    *,
    task_id: str | None = None,
    kind: str | None = None,
    from_agent: str | None = None,
    to_agent: str | None = None,
    limit: int = 100,
) -> list[TeamMessage]:
    ensure_schema()
    clauses: list[str] = []
    params: list[Any] = []
    if task_id:
        clauses.append("task_id = ?")
        params.append(task_id.strip())
    if kind:
        clauses.append("kind = ?")
        params.append(kind.strip().lower())
    if from_agent:
        clauses.append("from_agent = ?")
        params.append(from_agent.strip())
    if to_agent:
        clauses.append("to_agent = ?")
        params.append(to_agent.strip())
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    params.append(max(1, min(int(limit), 500)))
    conn = team_store.get_connection()
    rows = conn.execute(
        f"SELECT * FROM team_messages{where} ORDER BY created_ts DESC LIMIT ?",
        params,
    ).fetchall()
    return [_row_to_message(r) for r in rows]


def get_message(message_id: str) -> TeamMessage | None:
    mid = (message_id or "").strip()
    if not mid:
        return None
    ensure_schema()
    conn = team_store.get_connection()
    row = conn.execute("SELECT * FROM team_messages WHERE id = ?", (mid,)).fetchone()
    if row is None:
        return None
    return _row_to_message(row)
