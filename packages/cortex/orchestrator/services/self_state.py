"""Self-State Agency B — projection unique drives / intent / memory_refs.

Opt-in : ``LBG_SELF_STATE_ENABLED=1`` (défaut off).
Path : ``LBG_SELF_STATE_PATH`` (défaut ``/var/lib/lbg/self/state.json``).

Greffe Cortex — pas un second OS. goals[] réservé Phase C (vide ici).
"""

from __future__ import annotations

import json
import os
import threading
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

_lock = threading.RLock()
_cache: dict[str, Any] | None = None


def self_state_enabled() -> bool:
    return os.environ.get("LBG_SELF_STATE_ENABLED", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def self_state_path() -> Path:
    raw = os.environ.get("LBG_SELF_STATE_PATH", "").strip()
    if raw:
        return Path(raw)
    return Path("/var/lib/lbg/self/state.json")


def _now() -> float:
    return float(time.time())


def default_state() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "updated_ts": 0.0,
        "identity": {
            "self_id": "lbg_cortex_self",
            "display_name": "Cortex",
            "mode": "studio",
            "incarnations": {"studio": "lyra", "mmo": "lia"},
        },
        "drives": {
            "curiosity": 0.25,
            "tension": 0.0,
            "stress": 0.2,
            "fatigue": 0.1,
            "confidence": 0.7,
            "social_hunger": 0.0,
        },
        "drives_meta": {
            "scale": "0_1",
            "sources": {
                "curiosity": ["brain.gauges.curiosity", "proactive.curiosite"],
                "tension": ["proactive.tension"],
                "stress": ["brain.gauges.stress"],
                "fatigue": ["brain.gauges.fatigue"],
                "confidence": ["brain.gauges.confidence"],
                "social_hunger": ["lia.silence_players_s"],
            },
            "last_decay_ts": 0.0,
        },
        "intent": {
            "primary": "monitor",
            "narrative": "",
            "horizon": "reflex",
        },
        "goals": [],
        "beliefs": {
            "lan_health": "unknown",
            "orchestrator_ok": None,
            "bible_drift": "unknown",
            "team_backlog_pressure": 0.0,
        },
        "memory_refs": {
            "lessons_path": "packages/cortex/knowledge/lessons_learned.json",
            "lessons_count": 0,
            "lessons_slice_ids": [],
            "last_lesson_id": None,
            "brain_state_path": os.environ.get("LBG_BRAIN_STATE_PATH", "/var/lib/lbg/brain/state.json"),
            "evolution_sprint_path": None,
        },
        "pending_will": [],
        "last_tick": {
            "kind": "none",
            "ts": 0.0,
            "ok": None,
            "summary": "",
        },
    }


def _clamp01(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return float(x)


def _gauge_to_drive(v: object) -> float:
    try:
        return _clamp01(float(v) / 100.0)
    except (TypeError, ValueError):
        return 0.0


def _atomic_write(path: Path, payload: dict[str, Any]) -> str | None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp.replace(path)
        return None
    except Exception as e:
        return f"{type(e).__name__}: {e}"


def _read_file(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _merge_defaults(raw: dict[str, Any]) -> dict[str, Any]:
    base = default_state()
    out = deepcopy(base)
    for key in (
        "schema_version",
        "updated_ts",
        "identity",
        "drives",
        "drives_meta",
        "intent",
        "goals",
        "beliefs",
        "memory_refs",
        "pending_will",
        "last_tick",
    ):
        if key not in raw:
            continue
        val = raw[key]
        if isinstance(val, dict) and isinstance(out.get(key), dict):
            merged = dict(out[key])
            merged.update(val)
            out[key] = merged
        else:
            out[key] = val
    return out


def load_state(*, force_reload: bool = False) -> dict[str, Any]:
    global _cache
    with _lock:
        if _cache is not None and not force_reload:
            return deepcopy(_cache)
        path = self_state_path()
        raw = _read_file(path)
        state = _merge_defaults(raw) if raw else default_state()
        _cache = state
        return deepcopy(state)


def get_state() -> dict[str, Any]:
    return load_state()


def persist_state(state: dict[str, Any]) -> dict[str, Any]:
    global _cache
    with _lock:
        payload = _merge_defaults(state)
        payload["updated_ts"] = _now()
        payload["schema_version"] = 1
        err = _atomic_write(self_state_path(), payload)
        payload["_persist_error"] = err
        _cache = {k: v for k, v in payload.items() if k != "_persist_error"}
        out = deepcopy(_cache)
        if err:
            out["_persist_error"] = err
        return out


def patch_state(patch: dict[str, Any]) -> dict[str, Any]:
    """Merge superficiel par section (drives, intent, beliefs, …)."""
    if not isinstance(patch, dict):
        return get_state()
    with _lock:
        cur = load_state()
        for key, val in patch.items():
            if key.startswith("_"):
                continue
            if isinstance(val, dict) and isinstance(cur.get(key), dict):
                merged = dict(cur[key])
                merged.update(val)
                cur[key] = merged
            else:
                cur[key] = val
        return persist_state(cur)


def sync_from_brain(brain: dict[str, Any]) -> dict[str, Any] | None:
    """Projette gauges 0–100 + intent brain → drives/intent Self (0–1)."""
    if not self_state_enabled():
        return None
    if not isinstance(brain, dict):
        return get_state()
    gauges = brain.get("gauges") if isinstance(brain.get("gauges"), dict) else {}
    drives_patch: dict[str, float] = {}
    for src, dst in (
        ("curiosity", "curiosity"),
        ("stress", "stress"),
        ("fatigue", "fatigue"),
        ("confidence", "confidence"),
    ):
        if src in gauges:
            drives_patch[dst] = _gauge_to_drive(gauges[src])

    intent_primary = str(brain.get("intent") or "").strip() or "monitor"
    narrative = str(brain.get("narrative") or "")
    tick_ok = brain.get("last_tick_ok")
    tick_ts = brain.get("last_tick_ts")
    try:
        tick_ts_f = float(tick_ts) if tick_ts is not None else _now()
    except (TypeError, ValueError):
        tick_ts_f = _now()

    beliefs: dict[str, Any] = {}
    if tick_ok is True:
        beliefs["orchestrator_ok"] = True
        beliefs["lan_health"] = "ok"
    elif tick_ok is False:
        beliefs["orchestrator_ok"] = False
        beliefs["lan_health"] = "degraded"

    patch: dict[str, Any] = {
        "intent": {
            "primary": intent_primary,
            "narrative": narrative[:800],
            "horizon": "reflex",
        },
        "last_tick": {
            "kind": "brain",
            "ts": tick_ts_f,
            "ok": tick_ok if isinstance(tick_ok, bool) else None,
            "summary": (str(brain.get("last_error") or narrative) or "")[:240],
        },
        "memory_refs": {
            "brain_state_path": os.environ.get(
                "LBG_BRAIN_STATE_PATH", "/var/lib/lbg/brain/state.json"
            ),
        },
    }
    if drives_patch:
        patch["drives"] = drives_patch
    if beliefs:
        patch["beliefs"] = beliefs
    return patch_state(patch)


def sync_from_proactive(proactive: dict[str, Any]) -> dict[str, Any] | None:
    """Map tension / curiosite proactive (0–1) → drives."""
    if not self_state_enabled():
        return None
    if not isinstance(proactive, dict):
        return get_state()
    cur = get_state()
    drives = dict(cur.get("drives") or {})
    try:
        tension = _clamp01(float(proactive.get("tension", drives.get("tension", 0.0))))
    except (TypeError, ValueError):
        tension = float(drives.get("tension") or 0.0)
    try:
        curiosite = _clamp01(float(proactive.get("curiosite", 0.0)))
    except (TypeError, ValueError):
        curiosite = 0.0
    prev_c = float(drives.get("curiosity") or 0.0)
    drives["tension"] = tension
    drives["curiosity"] = max(prev_c, curiosite)
    return patch_state(
        {
            "drives": drives,
            "last_tick": {
                "kind": "proactive",
                "ts": _now(),
                "ok": True,
                "summary": str(proactive.get("mode") or "")[:120],
            },
        }
    )


def note_lesson_append(*, lesson_id: str | None, lessons_count: int) -> dict[str, Any] | None:
    """Met à jour memory_refs après append_lesson (no-op si Self off)."""
    if not self_state_enabled():
        return None
    refs: dict[str, Any] = {
        "lessons_count": max(0, int(lessons_count)),
    }
    if lesson_id:
        refs["last_lesson_id"] = str(lesson_id)
    try:
        from team import lessons_learned

        refs["lessons_path"] = str(lessons_learned.lessons_path())
    except Exception:
        pass
    return patch_state({"memory_refs": refs})


def set_team_backlog_pressure(pressure: float) -> dict[str, Any] | None:
    if not self_state_enabled():
        return None
    return patch_state({"beliefs": {"team_backlog_pressure": _clamp01(float(pressure))}})


def _clamp_drive_map(drives: dict[str, Any]) -> dict[str, float]:
    out: dict[str, float] = {}
    for k, v in drives.items():
        try:
            out[str(k)] = _clamp01(float(v))
        except (TypeError, ValueError):
            continue
    return out


def upsert_goal(goal: dict[str, Any]) -> dict[str, Any] | None:
    """Insert ou remplace un goal par id dans ``goals[]``."""
    if not self_state_enabled():
        return None
    if not isinstance(goal, dict) or not str(goal.get("id") or "").strip():
        raise ValueError("goal invalide")
    with _lock:
        st = load_state()
        goals = [g for g in (st.get("goals") or []) if isinstance(g, dict)]
        gid = str(goal["id"])
        replaced = False
        for i, g in enumerate(goals):
            if str(g.get("id") or "") == gid:
                goals[i] = dict(goal)
                replaced = True
                break
        if not replaced:
            goals.append(dict(goal))
        st["goals"] = goals
        return persist_state(st)


def list_goals(*, owner: str = "", status: str = "") -> list[dict[str, Any]]:
    st = get_state()
    goals = [g for g in (st.get("goals") or []) if isinstance(g, dict)]
    if owner:
        goals = [g for g in goals if str(g.get("owner") or "") == owner]
    if status:
        goals = [g for g in goals if str(g.get("status") or "") == status]
    return goals


def expire_stale_goals(*, now: float | None = None) -> dict[str, Any] | None:
    if not self_state_enabled():
        return None
    ts = float(now if now is not None else _now())
    with _lock:
        st = load_state()
        goals = [g for g in (st.get("goals") or []) if isinstance(g, dict)]
        changed = False
        for g in goals:
            if str(g.get("status") or "") != "active":
                continue
            exp = g.get("expires_ts")
            try:
                exp_f = float(exp) if exp is not None else 0.0
            except (TypeError, ValueError):
                exp_f = 0.0
            if exp_f > 0 and ts >= exp_f:
                g["status"] = "expired"
                g["last_action"] = "expired"
                changed = True
        if not changed:
            return deepcopy(st)
        st["goals"] = goals
        return persist_state(st)


def complete_goal(
    goal_id: str,
    *,
    last_action: str | None = None,
    decay_drive: bool = True,
    decay_amount: float = 0.25,
) -> dict[str, Any] | None:
    """Marque goal done + decay optionnel du drive source."""
    if not self_state_enabled():
        return None
    gid = (goal_id or "").strip()
    if not gid:
        raise ValueError("goal_id vide")
    with _lock:
        st = load_state()
        goals = [g for g in (st.get("goals") or []) if isinstance(g, dict)]
        found: dict[str, Any] | None = None
        for g in goals:
            if str(g.get("id") or "") == gid:
                g["status"] = "done"
                if last_action:
                    g["last_action"] = str(last_action)[:120]
                found = g
                break
        if found is None:
            return deepcopy(st)
        if decay_drive:
            from team.goal_policy import origin_drive_key

            key = origin_drive_key(str(found.get("origin") or ""))
            if key:
                drives = dict(st.get("drives") or {})
                try:
                    cur = float(drives.get(key) or 0.0)
                except (TypeError, ValueError):
                    cur = 0.0
                drives[key] = _clamp01(cur - abs(float(decay_amount)))
                st["drives"] = drives
        st["goals"] = goals
        return persist_state(st)


def patch_drives(drives_patch: dict[str, Any]) -> dict[str, Any] | None:
    if not self_state_enabled():
        return None
    if not isinstance(drives_patch, dict):
        return get_state()
    return patch_state({"drives": _clamp_drive_map(drives_patch)})


def bump_drive(key: str, delta: float) -> dict[str, Any] | None:
    if not self_state_enabled():
        return None
    with _lock:
        st = load_state()
        drives = dict(st.get("drives") or {})
        try:
            cur = float(drives.get(key) or 0.0)
        except (TypeError, ValueError):
            cur = 0.0
        drives[str(key)] = _clamp01(cur + float(delta))
        st["drives"] = drives
        return persist_state(st)


def ensure_lia_goals(*, now: float | None = None) -> dict[str, Any] | None:
    """Expire stale + propose goals depuis drives (si ``LBG_LIA_GOALS_ENABLED``)."""
    if not self_state_enabled():
        return None
    from team import goal_policy

    if not goal_policy.lia_goals_enabled():
        return expire_stale_goals(now=now)

    expire_stale_goals(now=now)
    st = get_state()
    drives = st.get("drives") if isinstance(st.get("drives"), dict) else {}
    existing = st.get("goals") if isinstance(st.get("goals"), list) else []
    proposed = goal_policy.propose_lia_goals(
        drives=drives,
        existing_goals=existing,
        now=now,
    )
    for goal in proposed:
        upsert_goal(goal)
    return get_state()


def meta_status() -> dict[str, object]:
    path = self_state_path()
    st = get_state() if path.is_file() or self_state_enabled() else default_state()
    lia_goals_meta: dict[str, object] = {}
    try:
        from team import goal_policy

        lia_goals_meta = goal_policy.meta_status()
    except Exception:
        lia_goals_meta = {"enabled": False}
    return {
        "enabled": self_state_enabled(),
        "path": str(path),
        "exists": path.is_file(),
        "updated_ts": st.get("updated_ts"),
        "intent": (st.get("intent") or {}).get("primary") if isinstance(st.get("intent"), dict) else None,
        "drives": st.get("drives") if self_state_enabled() or path.is_file() else None,
        "lessons_count": (st.get("memory_refs") or {}).get("lessons_count")
        if isinstance(st.get("memory_refs"), dict)
        else None,
        "goals_count": len(st.get("goals") or []) if isinstance(st.get("goals"), list) else 0,
        "lia_goals": lia_goals_meta,
    }


def reset_cache_for_tests() -> None:
    global _cache
    with _lock:
        _cache = None
