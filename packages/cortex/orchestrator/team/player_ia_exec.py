"""Routage exécution player_ia : docs_only, sonde L1, ou think/tick L2."""

from __future__ import annotations

import os

from team.docs_write_workflow import execute_docs_only_workflow, resolve_docs_only
from team.models import TeamTask
from team.player_ia_probe import probe_player_ia
from team.player_ia_think import execute_player_ia_think, resolve_player_ia_mode


def _threshold_low() -> float:
    raw = os.environ.get("LBG_TEAM_PLAYER_IA_HUMANITY_LOW", "0.40").strip()
    try:
        n = float(raw)
    except ValueError:
        n = 0.40
    return max(0.0, min(n, 1.0))


def _threshold_high() -> float:
    raw = os.environ.get("LBG_TEAM_PLAYER_IA_HUMANITY_HIGH", "0.70").strip()
    try:
        n = float(raw)
    except ValueError:
        n = 0.70
    return max(_threshold_low(), min(n, 1.0))


def _threshold_target() -> str:
    raw = os.environ.get("LBG_TEAM_PLAYER_IA_HUMANITY_TARGET", "medium").strip().lower()
    return raw if raw in {"low", "medium", "high"} else "medium"


def _humanity_hard_fail() -> bool:
    """Par défaut soft : idle/low humanity n'échoue pas la sonde L1 si bots online."""
    raw = os.environ.get("LBG_TEAM_PLAYER_IA_HUMANITY_HARD_FAIL", "0").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _as_float(v: object) -> float | None:
    if isinstance(v, (int, float)):
        return float(v)
    return None


def _score_to_band(score: float | None) -> str:
    if score is None:
        return "low"
    if score >= _threshold_high():
        return "high"
    if score >= _threshold_low():
        return "medium"
    return "low"


def _band_rank(band: str) -> int:
    return {"low": 0, "medium": 1, "high": 2}.get(band, 0)


def _humanity_summary(probe: dict[str, object]) -> dict[str, object]:
    checks = probe.get("checks")
    rows = list(checks) if isinstance(checks, list) else []
    per_player: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, dict) or row.get("kind") != "player_humanity":
            continue
        score = _as_float(row.get("score"))
        band = _score_to_band(score)
        per_player.append(
            {
                "player": str(row.get("player") or ""),
                "score": score,
                "band": band,
                "signals": row.get("signals") if isinstance(row.get("signals"), dict) else {},
            }
        )
    per_player.sort(key=lambda x: str(x.get("player") or ""))
    avg = _as_float(probe.get("humanity_avg"))
    if avg is None and per_player:
        vals = [float(p["score"]) for p in per_player if isinstance(p.get("score"), (int, float))]
        avg = round(sum(vals) / len(vals), 3) if vals else None
    mission_band = _score_to_band(avg)
    target = _threshold_target()
    qa_ok = _band_rank(mission_band) >= _band_rank(target)
    label = "vert" if qa_ok else "à renforcer"
    summary = (
        f"Humanité perçue {label} — avg={avg if avg is not None else 'n/a'} "
        f"band={mission_band} target>={target} "
        f"(low<{_threshold_low():.2f}, high>={_threshold_high():.2f})"
    )
    return {
        "avg": avg,
        "band": mission_band,
        "target": target,
        "qa_ok": qa_ok,
        "thresholds": {"low": _threshold_low(), "high": _threshold_high()},
        "players": per_player,
        "summary": summary,
    }


def _core_online_bots() -> frozenset[str]:
    """Bots qui définissent la connectivité L1 (défaut Lia+Nix+Mira+Kael)."""
    from team.player_ia_probe import required_bot_ids

    return required_bot_ids() or frozenset({"lia", "nix", "mira", "kael"})


def _connectivity_ok(probe: dict[str, object]) -> bool:
    """Hub G5 (:8787) ou sidecar legacy (:8791) + bots cœur online (ignore humanité / truth-guard)."""
    checks = probe.get("checks")
    rows = list(checks) if isinstance(checks, list) else []
    health = any(
        isinstance(c, dict)
        and c.get("kind") in ("hub_healthz", "sidecar_healthz")
        and c.get("ok")
        for c in rows
    )
    if not health:
        return False
    core = _core_online_bots()
    by_player: dict[str, dict[str, object]] = {}
    for c in rows:
        if not isinstance(c, dict) or c.get("kind") != "player_snapshot":
            continue
        name = str(c.get("player") or "").strip().lower()
        if name:
            by_player[name] = c
    if not core:
        return bool(probe.get("ok"))
    # Strict : chaque bot cœur doit être présent ET online (pas seulement ok/skipped).
    return all(bool((by_player.get(bot) or {}).get("online")) for bot in core)


def execute_player_ia(task: TeamTask) -> dict[str, object]:
    # docs_only avant toute sonde Core3 — Chœur peut rédiger markdown/JSON.
    if resolve_docs_only(task):
        return execute_docs_only_workflow(task)
    if resolve_player_ia_mode(task) == "think_tick":
        return execute_player_ia_think(task)
    probe = probe_player_ia(task)
    humanity = _humanity_summary(probe)
    out = dict(probe)
    out["humanity_report"] = humanity
    out["mission_track"] = "player_ia_humanization"

    conn_ok = _connectivity_ok(probe)
    if conn_ok and not humanity["qa_ok"] and not _humanity_hard_fail():
        out["ok"] = True
        out["summary"] = humanity["summary"] + " (advisory — bots online, pas un hard-fail L1)"
        out["humanity_advisory"] = True
    elif conn_ok and not bool(probe.get("ok")):
        # Truth-guard / autres soft gaps : ne pas masquer derrière humanité
        gaps = [
            str(c.get("check_kind") or c.get("kind") or "?")
            for c in (probe.get("checks") or [])
            if isinstance(c, dict) and c.get("ok") is False and c.get("kind") != "player_humanity"
        ]
        out["ok"] = True
        out["summary"] = (
            f"Sonde joueurs IA OK (bots online) — advisory: {', '.join(gaps[:4]) or 'gaps'}"
            f" · {humanity['summary']}"
        )
        out["truth_guard_advisory"] = True
    else:
        out["summary"] = humanity["summary"] if humanity.get("players") else str(probe.get("summary") or "")
        if not conn_ok:
            out["ok"] = False
    return out
