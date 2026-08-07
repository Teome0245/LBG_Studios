"""Présence Team (Peau) — états normalisés team.presence.v1 + hub WS.

Émission non bloquante depuis le store ; fan-out WebSocket in-process.
"""

from __future__ import annotations

import asyncio
import os
import re
import threading
import time
import uuid
from typing import Any

from team.models import TeamTask
from team.role_aliases import role_display

SCHEMA = "team.presence.v1"
SNAPSHOT_SCHEMA = "team.presence.snapshot.v1"

ZONES: list[dict[str, Any]] = [
    {"id": "zone_core", "label": "Open Space Core (140)", "sort_order": 0},
    {"id": "zone_front", "label": "Front web (.100)", "sort_order": 1},
    {"id": "zone_llm", "label": "Forge LLM (.110 / .111)", "sort_order": 2},
    {"id": "zone_mmo_lab", "label": "Lab SWG (245)", "sort_order": 3},
    {"id": "zone_prime", "label": "Monde Prime (246)", "sort_order": 4},
    {"id": "zone_coffee", "label": "Pause café", "sort_order": 5},
]

ZONE_IDS = frozenset(z["id"] for z in ZONES)

DEFAULT_ZONE_BY_ROLE: dict[str, str] = {
    "admin_infra": "zone_llm",
    "pm": "zone_core",
    "qa": "zone_core",
    "ops": "zone_core",
    "dev_game": "zone_mmo_lab",
    "dev_godot": "zone_prime",
    "player_ia": "zone_prime",
}

# Zone préférée par persona / agent_id (registre)
DEFAULT_ZONE_BY_AGENT: dict[str, str] = {
    "admin_infra": "zone_llm",
    "studio_admin_atlas": "zone_llm",
    "studio_pm_themis": "zone_core",
    "studio_qa_argus": "zone_core",
    "studio_ops_hephaistos": "zone_core",
    "studio_dev_dedale": "zone_mmo_lab",
    "studio_dev_vulcan": "zone_mmo_lab",
    "studio_infographiste_pygmalion": "zone_front",
    "godot_dev_iris": "zone_prime",
    "godot_dev_hermes": "zone_prime",
    "studio_player_ia_choeur": "zone_prime",
    "studio_conductor_lyra": "zone_core",
}

HOST_HINT_BY_ZONE: dict[str, str] = {
    "zone_core": "192.168.0.140",
    "zone_front": "192.168.0.100",
    "zone_llm": "192.168.0.110",
    "zone_mmo_lab": "192.168.0.245",
    "zone_prime": "192.168.0.246",
    "zone_coffee": "192.168.0.140",
}

# Persona par défaut quand une tâche n'a pas de sous-projet (1er = principal du rôle)
DEFAULT_AGENT_BY_ROLE: dict[str, str] = {
    "admin_infra": "admin_infra",
    "pm": "studio_pm_themis",
    "qa": "studio_qa_argus",
    "ops": "studio_ops_hephaistos",
    "dev_game": "studio_dev_dedale",
    "dev_godot": "godot_dev_iris",
    "player_ia": "studio_player_ia_choeur",
}

_SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|token|password|secret|bearer)\s*[:=]\s*\S+"
)

_enabled = os.environ.get("LBG_TEAM_PRESENCE_ENABLED", "1") == "1"
_history_limit = max(10, int(os.environ.get("LBG_TEAM_PRESENCE_HISTORY", "100")))
_min_interval = float(os.environ.get("LBG_TEAM_PRESENCE_MIN_INTERVAL_SEC", "2"))
# Après un échec, l'agent redevient idle (ne reste pas bloqué en rouge)
_failed_ttl = float(os.environ.get("LBG_TEAM_PRESENCE_FAILED_TTL_SEC", "90"))

_lock = threading.RLock()
_agents: dict[str, dict[str, Any]] = {}
_last_emit_ts: dict[str, float] = {}
_last_status: dict[str, str] = {}
_history: list[dict[str, Any]] = []
_clients: set[Any] = set()
_loop: asyncio.AbstractEventLoop | None = None


def enabled() -> bool:
    return _enabled


def bind_loop(loop: asyncio.AbstractEventLoop | None) -> None:
    global _loop
    _loop = loop


def sanitize_action(text: str | None, *, max_len: int = 120) -> str:
    raw = " ".join(str(text or "").split())
    raw = _SECRET_RE.sub(r"\1=***", raw)
    if len(raw) > max_len:
        return raw[: max_len - 1] + "…"
    return raw


def map_task_status(status: str, *, approval_required: bool = False, approved: bool = False) -> str:
    if status == "running":
        return "busy"
    if status == "review":
        return "review"
    if status == "failed":
        return "failed"
    # L2 pas encore approuvée : visible « review » sur le bureau.
    if approval_required and status in ("queued", "waiting_approval") and not approved:
        return "review"
    # L2 approuvée, en attente d'Exécuter : reste review (pastille) mais flag awaiting_run côté payload.
    if approval_required and status in ("queued", "waiting_approval") and approved:
        return "review"
    return "idle"


def task_is_approved(task: TeamTask) -> bool:
    if task.stored_approval_token:
        return True
    ctx = task.context or {}
    return bool(ctx.get("approved"))


def task_awaits_human_approval(task: TeamTask) -> bool:
    if not task.approval_required:
        return False
    if task.status not in ("queued", "review", "waiting_approval"):
        return False
    return not task_is_approved(task)


def task_awaits_run(task: TeamTask) -> bool:
    """Approuvée (jeton stocké) mais pas encore exécutée."""
    if not task.approval_required:
        return False
    if task.status not in ("queued", "review"):
        return False
    return task_is_approved(task)


def _roster() -> list[dict[str, Any]]:
    """Personas registre + Atlas (admin_infra) s'il n'est pas déclaré."""
    try:
        from team.agent_registry import list_agents_summary

        decls = list_agents_summary()
    except Exception:
        decls = []
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for d in decls:
        aid = str(d.get("agent_id") or "").strip()
        if not aid or aid in seen:
            continue
        seen.add(aid)
        out.append(
            {
                "agent_id": aid,
                "display_name": str(d.get("display_name") or aid),
                "role": str(d.get("role") or ""),
                "persona": str(d.get("persona") or ""),
                "subproject": str(d.get("subproject") or "") or None,
            }
        )
    if "admin_infra" not in seen and "studio_admin_atlas" not in seen:
        disp = role_display("admin_infra")
        out.append(
            {
                "agent_id": "admin_infra",
                "display_name": disp.get("alias") or "Atlas",
                "role": "admin_infra",
                "persona": "atlas",
                "subproject": None,
            }
        )
    out.sort(key=lambda x: (x.get("role") or "", x.get("display_name") or ""))
    return out


def _display_for_agent(agent_id: str, role: str) -> str:
    for row in _roster():
        if row["agent_id"] == agent_id:
            return str(row["display_name"])
    return role_display(role).get("alias") or agent_id


def resolve_presence_agent_id(task: TeamTask) -> str:
    """Mappe une tâche Team vers un persona (registre), pas seulement le rôle."""
    ctx = task.context or {}
    explicit = str(ctx.get("presence_agent_id") or ctx.get("agent_id") or "").strip()
    if explicit:
        return explicit

    roster = _roster()
    by_id = {r["agent_id"]: r for r in roster}
    by_persona = {str(r.get("persona") or "").lower(): r["agent_id"] for r in roster if r.get("persona")}
    by_sub = {str(r.get("subproject") or ""): r["agent_id"] for r in roster if r.get("subproject")}

    sub = str(ctx.get("subproject") or "").strip()
    if ctx.get("infographiste_ia") and not sub:
        sub = "infographiste_ia"
    if ctx.get("core3_build") and not sub:
        sub = "core3_build"
    persona = str(ctx.get("godot_dev_persona") or ctx.get("persona") or "").lower()
    if persona == "hermes" and not sub:
        sub = "godot_hermes"
    elif (persona == "iris" or ctx.get("dev_godot_focus")) and not sub:
        sub = "godot_iris"

    if sub and sub in by_sub:
        return by_sub[sub]
    if persona and persona in by_persona:
        return by_persona[persona]

    # Indices dans l'objectif
    blob = f"{task.objective or ''} {json_dumps_safe(ctx)}".lower()
    if "pygmalion" in blob or "infographiste" in blob or "lora" in blob:
        return by_sub.get("infographiste_ia") or by_persona.get("pygmalion") or DEFAULT_AGENT_BY_ROLE.get(task.role, task.role)
    if "vulcan" in blob or "core3" in blob or "zb-0" in blob or "antigravity" in blob:
        return by_sub.get("core3_build") or by_persona.get("vulcan") or DEFAULT_AGENT_BY_ROLE.get(task.role, task.role)
    if "hermès" in blob or "hermes" in blob or "soe" in blob or "lbg-ws" in blob:
        return by_sub.get("godot_hermes") or by_persona.get("hermes") or DEFAULT_AGENT_BY_ROLE.get(task.role, task.role)
    if "iris" in blob or "m9" in blob or "scrapaltai" in blob or "minimap" in blob:
        return by_sub.get("godot_iris") or by_persona.get("iris") or DEFAULT_AGENT_BY_ROLE.get(task.role, task.role)

    default_id = DEFAULT_AGENT_BY_ROLE.get(task.role, task.role)
    if default_id in by_id:
        return default_id
    # premier agent du même rôle
    for r in roster:
        if r.get("role") == task.role:
            return str(r["agent_id"])
    return task.role


def json_dumps_safe(obj: object) -> str:
    try:
        import json

        return json.dumps(obj, ensure_ascii=False)
    except Exception:
        return str(obj)


def infer_zone(task: TeamTask, *, agent_id: str | None = None) -> str:
    ctx = task.context or {}
    explicit = str(ctx.get("presence_zone") or ctx.get("zone") or "").strip()
    if explicit in ZONE_IDS:
        return explicit
    blob = " ".join(
        [
            task.objective or "",
            str(ctx.get("workflow") or ""),
            str(ctx.get("subproject") or ""),
            str(ctx.get("host") or ""),
            str(ctx.get("target_host") or ""),
        ]
    ).lower()
    if any(k in blob for k in ("246", "prime", "godot", "lbg-ws", "scrapaltai", "m9")):
        return "zone_prime"
    if any(k in blob for k in ("245", "core3", "swg", "precu", "vulcan", "zb-")):
        return "zone_mmo_lab"
    if any(k in blob for k in ("ollama", "llm", "110", "111", "lora", "bench", "atlas")):
        return "zone_llm"
    if any(k in blob for k in ("front", ".100", "cockpit", "5174", "8093", "pygmalion", "infographiste")):
        return "zone_front"
    if "café" in blob or "cafe" in blob or "pause" in blob:
        return "zone_coffee"
    aid = agent_id or resolve_presence_agent_id(task)
    if aid in DEFAULT_ZONE_BY_AGENT:
        return DEFAULT_ZONE_BY_AGENT[aid]
    return DEFAULT_ZONE_BY_ROLE.get(task.role, "zone_core")


def _presence_from_task(task: TeamTask, *, event: str = "status_changed") -> dict[str, Any]:
    agent_id = resolve_presence_agent_id(task)
    approved = task_is_approved(task)
    status = map_task_status(
        task.status,
        approval_required=bool(task.approval_required),
        approved=approved,
    )
    location = infer_zone(task, agent_id=agent_id)
    if status == "idle":
        if task.status in ("done", "cancelled"):
            location = "zone_coffee"
        elif task.status == "queued":
            location = DEFAULT_ZONE_BY_AGENT.get(agent_id) or DEFAULT_ZONE_BY_ROLE.get(task.role, "zone_core")
        else:
            location = DEFAULT_ZONE_BY_AGENT.get(agent_id) or DEFAULT_ZONE_BY_ROLE.get(task.role, "zone_core")
    action = sanitize_action(task.objective if status != "idle" else "En attente")
    if status == "idle" and task.status == "queued":
        action = sanitize_action(f"En file — {task.objective}")
    awaits_approval = task_awaits_human_approval(task)
    awaits_run = task_awaits_run(task)
    if awaits_approval:
        action = sanitize_action(f"Validation L2 — {task.objective}")
    elif awaits_run:
        action = sanitize_action(f"Prêt à exécuter — {task.objective}")
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "agent_id": agent_id,
        "display_name": _display_for_agent(agent_id, task.role),
        "status": status,
        "current_action": action,
        "location": location,
        "target_destination": None,
        "task_id": task.id,
        "role": task.role,
        "host_hint": HOST_HINT_BY_ZONE.get(location, "192.168.0.140"),
        "trace_id": (task.trace_id or str(uuid.uuid4())[:12])[:128],
        "event": event,
        "timestamp": int(time.time()),
        "approval_required": bool(task.approval_required),
        "awaiting_human_approval": awaits_approval,
        "awaiting_run": awaits_run,
    }
    return payload


def _idle_agent_row(row: dict[str, Any]) -> dict[str, Any]:
    agent_id = str(row["agent_id"])
    role = str(row.get("role") or "")
    location = DEFAULT_ZONE_BY_AGENT.get(agent_id) or DEFAULT_ZONE_BY_ROLE.get(role, "zone_core")
    return {
        "schema": SCHEMA,
        "agent_id": agent_id,
        "display_name": str(row.get("display_name") or agent_id),
        "status": "idle",
        "current_action": "En attente",
        "location": location,
        "target_destination": None,
        "role": role,
        "host_hint": HOST_HINT_BY_ZONE.get(location, "192.168.0.140"),
        "trace_id": str(uuid.uuid4())[:12],
        "event": "heartbeat",
        "timestamp": int(time.time()),
    }


def _idle_agent(role: str) -> dict[str, Any]:
    """Compat tests / anciens appels : idle pour un rôle technique."""
    aid = DEFAULT_AGENT_BY_ROLE.get(role, role)
    return _idle_agent_row(
        {
            "agent_id": aid,
            "display_name": _display_for_agent(aid, role),
            "role": role,
        }
    )


def _should_emit(agent_id: str, status: str) -> bool:
    now = time.time()
    prev_status = _last_status.get(agent_id)
    last = _last_emit_ts.get(agent_id, 0.0)
    if prev_status != status:
        return True
    return (now - last) >= _min_interval


def _publish_locked(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Update state; return fan-out payloads (empty if throttled)."""
    agent_id = str(payload.get("agent_id") or "")
    if not agent_id:
        return []
    status = str(payload.get("status") or "idle")
    if not _should_emit(agent_id, status):
        _agents[agent_id] = payload
        return []
    old = _agents.get(agent_id)
    if old and old.get("location") != payload.get("location"):
        moving = dict(payload)
        moving["target_destination"] = payload.get("location")
        moving["location"] = old.get("location")
        moving["event"] = "location_changed"
        arrived = dict(payload)
        arrived["target_destination"] = None
        arrived["event"] = "location_changed"
        _agents[agent_id] = arrived
        _history.extend([moving, arrived])
        payloads_for_ws = [moving, arrived]
    else:
        _agents[agent_id] = payload
        _history.append(payload)
        payloads_for_ws = [payload]
    while len(_history) > _history_limit:
        _history.pop(0)
    _last_emit_ts[agent_id] = time.time()
    _last_status[agent_id] = status
    return payloads_for_ws


def emit_payload(payload: dict[str, Any]) -> None:
    if not _enabled:
        return
    try:
        with _lock:
            fanout = _publish_locked(payload)
        for item in fanout:
            _schedule_broadcast({"type": "presence", "payload": item})
    except Exception:
        # Jamais remonter vers le runner Team
        return


def emit_from_task(task: TeamTask, *, event: str = "status_changed") -> None:
    if not _enabled or task is None:
        return
    try:
        emit_payload(_presence_from_task(task, event=event))
    except Exception:
        return


def _maybe_recover_failed_locked(now: float | None = None) -> list[dict[str, Any]]:
    """Passe les failed trop vieux en idle (café) — agents non bloqués."""
    if _failed_ttl <= 0:
        return []
    now = time.time() if now is None else now
    recovered: list[dict[str, Any]] = []
    for aid, payload in list(_agents.items()):
        if str(payload.get("status") or "") != "failed":
            continue
        ts = float(payload.get("timestamp") or 0)
        if (now - ts) < _failed_ttl:
            continue
        idle = dict(payload)
        idle["status"] = "idle"
        idle["current_action"] = "Dispo — triage/relance peut suivre"
        idle["location"] = "zone_coffee"
        idle["target_destination"] = None
        idle["event"] = "status_changed"
        idle["timestamp"] = int(now)
        _agents[aid] = idle
        _last_status[aid] = "idle"
        _last_emit_ts[aid] = now
        recovered.append(idle)
    return recovered


def recover_stale_failed() -> int:
    """Appelable hors lock (snapshot / timer) — broadcast les reprises."""
    if not _enabled:
        return 0
    try:
        with _lock:
            recovered = _maybe_recover_failed_locked()
        for payload in recovered:
            _schedule_broadcast({"type": "presence", "payload": payload})
        return len(recovered)
    except Exception:
        return 0


def snapshot(*, mode: str = "live") -> dict[str, Any]:
    recover_stale_failed()
    with _lock:
        known = dict(_agents)
    agents: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in _roster():
        aid = str(row["agent_id"])
        seen.add(aid)
        if aid in known:
            agents.append(known[aid])
        else:
            agents.append(_idle_agent_row(row))
    # États orphelins (ancien agent_id = rôle technique, system:…)
    for aid, payload in known.items():
        if aid not in seen:
            agents.append(payload)
    return {
        "schema": SNAPSHOT_SCHEMA,
        "agents": agents,
        "zones": list(ZONES),
        "generated_at": int(time.time()),
        "mode": mode,
    }


def history(*, limit: int = 50) -> list[dict[str, Any]]:
    n = max(1, min(limit, _history_limit))
    with _lock:
        return list(_history[-n:])


def rebuild_from_tasks(tasks: list[TeamTask]) -> None:
    """Recalcule l'état depuis les tâches actives (boot / snapshot froid)."""
    now = time.time()
    # Priorité : running > review/L2-queued > queued > failed récent
    def _rank(task: TeamTask) -> int:
        if task.status == "running":
            return 0
        if task.status == "review" or (
            bool(task.approval_required) and task.status in ("queued", "waiting_approval")
        ):
            return 1
        if task.status == "queued":
            return 2
        if task.status == "failed":
            return 3
        return 9

    active_by_agent: dict[str, TeamTask] = {}
    for task in tasks:
        if task.status not in ("running", "review", "failed", "queued", "waiting_approval"):
            continue
        if task.status == "failed" and _failed_ttl > 0 and (now - float(task.updated_ts or 0)) > _failed_ttl:
            continue
        aid = resolve_presence_agent_id(task)
        prev = active_by_agent.get(aid)
        if prev is None:
            active_by_agent[aid] = task
            continue
        pr = _rank(prev)
        tr = _rank(task)
        if tr < pr or (tr == pr and task.updated_ts >= prev.updated_ts):
            active_by_agent[aid] = task
    with _lock:
        _agents.clear()
        for aid, task in active_by_agent.items():
            payload = _presence_from_task(task, event="heartbeat")
            _agents[aid] = payload
            _last_status[aid] = str(payload["status"])
        _maybe_recover_failed_locked(now)


async def register_client(ws: Any) -> None:
    _clients.add(ws)


async def unregister_client(ws: Any) -> None:
    _clients.discard(ws)


async def _broadcast(msg: dict[str, Any]) -> None:
    dead: list[Any] = []
    for ws in list(_clients):
        try:
            await ws.send_json(msg)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _clients.discard(ws)


def _schedule_broadcast(msg: dict[str, Any]) -> None:
    loop = _loop
    if loop is None or not loop.is_running():
        return
    try:
        asyncio.run_coroutine_threadsafe(_broadcast(msg), loop)
    except Exception:
        return


def client_count() -> int:
    return len(_clients)
