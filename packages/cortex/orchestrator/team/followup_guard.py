"""Garde-fous anti-bruit pour followups équipe (cooldown, profondeur, dédup).

Réutilise le pattern cooldown+signature de ``admin_infra_element``.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from team import store as team_store
from team.models import TeamTask

FOLLOWUP_CHILD_FLAGS = (
    "_godot_followup",
    "_m9_followup",
    "_qa_followup",
    "_failure_followup",
)


def is_followup_child(task: TeamTask) -> bool:
    ctx = task.context or {}
    return any(ctx.get(flag) for flag in FOLLOWUP_CHILD_FLAGS)


def followup_depth(task: TeamTask, *, max_hops: int = 12) -> int:
    """Nombre d'ancêtres via ``parent_task_id`` (0 = tâche racine timer)."""
    depth = 0
    seen: set[str] = set()
    current: TeamTask | None = task
    while depth < max_hops and current is not None:
        pid = str((current.context or {}).get("parent_task_id") or "").strip()
        if not pid or pid in seen:
            break
        seen.add(pid)
        parent = team_store.get_task(pid)
        if parent is None:
            break
        depth += 1
        current = parent
    return depth


def max_depth() -> int:
    try:
        return max(0, int(os.environ.get("LBG_TEAM_FOLLOWUP_MAX_DEPTH", "2")))
    except ValueError:
        return 2


def cooldown_s() -> float:
    try:
        return max(60.0, float(os.environ.get("LBG_TEAM_FOLLOWUP_COOLDOWN_S", "3600")))
    except ValueError:
        return 3600.0


def state_path() -> Path:
    raw = os.environ.get(
        "LBG_TEAM_FOLLOWUP_STATE",
        "/var/lib/lbg/team_followup_state.json",
    ).strip()
    return Path(raw)


def _load_state() -> dict[str, Any]:
    path = state_path()
    if path == Path(":memory:"):
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_state(payload: dict[str, Any]) -> None:
    path = state_path()
    if path == Path(":memory:"):
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def _failed_tracks(result: dict[str, Any]) -> list[str]:
    tracks = result.get("tracks") if isinstance(result.get("tracks"), list) else []
    probes = result.get("probes") if isinstance(result.get("probes"), list) else []
    combined = tracks + probes
    failed: list[str] = []
    for item in combined:
        if isinstance(item, dict) and not item.get("ok") and not item.get("skipped"):
            track = str(item.get("track") or "?")
            if track not in failed:
                failed.append(track)
    return sorted(failed)


def _collect_gaps(result: dict[str, Any]) -> list[str]:
    gaps: list[str] = []
    for probe in result.get("probes") or []:
        if not isinstance(probe, dict):
            continue
        nested = probe.get("probes")
        if isinstance(nested, list):
            for sub in nested:
                if isinstance(sub, dict) and not sub.get("ok"):
                    gaps.extend(str(g) for g in (sub.get("gaps") or []))
        elif not probe.get("ok"):
            gaps.extend(str(g) for g in (probe.get("gaps") or []))
    for gap in result.get("gaps") or []:
        if gap:
            gaps.append(str(gap))
    return gaps[:12]


def godot_signature(result: dict[str, Any], *, track: str = "") -> str:
    payload = {
        "family": "godot",
        "kind": result.get("kind"),
        "track": track or result.get("track"),
        "failed_tracks": _failed_tracks(result),
        "gaps": sorted(_collect_gaps(result))[:8],
    }
    return json.dumps(payload, sort_keys=True, ensure_ascii=False)


def m9_signature(result: dict[str, Any], *, track: str) -> str:
    payload = {
        "family": "m9",
        "track": track,
        "gaps": sorted(_collect_gaps(result))[:8],
    }
    return json.dumps(payload, sort_keys=True, ensure_ascii=False)


def _spawn_key(family: str, signature: str) -> str:
    return f"{family}:{signature}"


def is_on_cooldown(family: str, signature: str) -> bool:
    st = _load_state()
    spawns = st.get("spawns") if isinstance(st.get("spawns"), dict) else {}
    entry = spawns.get(_spawn_key(family, signature))
    if not isinstance(entry, dict):
        return False
    last_ts = float(entry.get("ts") or 0)
    return (time.time() - last_ts) < cooldown_s()


def record_spawn(family: str, signature: str, *, parent_task_id: str) -> None:
    st = _load_state()
    spawns = st.get("spawns") if isinstance(st.get("spawns"), dict) else {}
    spawns[_spawn_key(family, signature)] = {
        "ts": time.time(),
        "parent_task_id": parent_task_id,
    }
    st["spawns"] = spawns
    _save_state(st)


def has_open_corrective(
    *,
    family: str,
    signature: str,
    roles: tuple[str, ...] = ("dev_game", "dev_godot"),
) -> bool:
    """True si une tâche corrective équivalente est déjà queued/running/review."""
    for task in team_store.list_tasks(limit=300):
        if task.role not in roles:
            continue
        if task.status not in ("queued", "running", "review"):
            continue
        ctx = task.context or {}
        if ctx.get("_followup_signature") != signature:
            continue
        if ctx.get("_followup_family") != family:
            continue
        return True
    return False


def should_suppress_spawn(
    task: TeamTask,
    *,
    family: str,
    signature: str,
    roles: tuple[str, ...] = ("dev_game", "dev_godot"),
) -> str | None:
    """Retourne la raison du skip, ou ``None`` si le spawn est autorisé."""
    if is_followup_child(task):
        return "followup_child"
    if max_depth() > 0 and followup_depth(task) >= max_depth():
        return "max_depth"
    if is_on_cooldown(family, signature):
        return "cooldown"
    if has_open_corrective(family=family, signature=signature, roles=roles):
        return "open_corrective"
    return None


def followup_context_extras(*, family: str, signature: str) -> dict[str, str]:
    return {
        "_followup_family": family,
        "_followup_signature": signature,
    }
