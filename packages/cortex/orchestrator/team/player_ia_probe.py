"""Sonde L1 joueurs IA Core3 Prime (sidecar :8791, VM 246)."""

from __future__ import annotations

import os

import httpx

from team.models import TeamTask
from team.player_ia_world_guard import run_world_truth_guard


def sidecar_base_url() -> str:
    return os.environ.get("LBG_CORE3_SIDECAR_URL", "http://192.168.0.246:8791").strip().rstrip("/")


def managed_bot_ids() -> tuple[str, ...]:
    raw = os.environ.get("LBG_CORE3_IA_BOTS", "lia,nix,mira,kael").strip()
    if not raw:
        return ("lia", "nix")
    return tuple(p.strip().lower() for p in raw.split(",") if p.strip())


def required_bot_ids() -> frozenset[str]:
    # Mira/Kael = optionnels (souvent 409 hors session) — ne pas faire échouer Chœur/Argus.
    raw = os.environ.get("LBG_TEAM_PLAYER_IA_REQUIRED_BOTS", "lia,nix").strip()
    if not raw:
        return frozenset({"lia", "nix"})
    return frozenset(p.strip().lower() for p in raw.split(",") if p.strip())


def _events_sample_limit() -> int:
    raw = os.environ.get("LBG_TEAM_PLAYER_IA_EVENTS_LIMIT", "30").strip()
    try:
        n = int(raw)
    except ValueError:
        n = 30
    return max(5, min(n, 100))


def _score_humanity(events: list[dict[str, object]], player: str) -> dict[str, object]:
    """Heuristique légère: activité sociale, diversité et follow-up."""
    relevant = [
        ev
        for ev in events
        if str(ev.get("actor") or "").strip().lower() == player.lower()
        or str(ev.get("target") or "").strip().lower() == player.lower()
    ]
    if not relevant:
        return {
            "score": 0.0,
            "band": "low",
            "signals": {"social_events": 0, "message_diversity": 0, "followups": 0},
        }
    social_events = len(relevant)
    messages = [
        str(ev.get("message") or ev.get("source_line") or "").strip().lower()
        for ev in relevant
        if str(ev.get("message") or ev.get("source_line") or "").strip()
    ]
    uniq_messages = len(set(messages))
    message_diversity = min(1.0, uniq_messages / max(1, min(len(messages), 8)))
    followups = 0
    for i in range(1, len(relevant)):
        prev_actor = str(relevant[i - 1].get("actor") or "").strip().lower()
        cur_actor = str(relevant[i].get("actor") or "").strip().lower()
        prev_target = str(relevant[i - 1].get("target") or "").strip().lower()
        cur_target = str(relevant[i].get("target") or "").strip().lower()
        if prev_target == player.lower() and cur_actor == player.lower() and prev_actor and cur_target == prev_actor:
            followups += 1
    social_score = min(1.0, social_events / 8.0)
    followup_score = min(1.0, followups / 3.0)
    score = round((0.4 * social_score) + (0.35 * message_diversity) + (0.25 * followup_score), 3)
    band = "high" if score >= 0.7 else ("medium" if score >= 0.4 else "low")
    return {
        "score": score,
        "band": band,
        "signals": {
            "social_events": social_events,
            "message_diversity": round(message_diversity, 3),
            "followups": followups,
        },
    }


def probe_player_ia(task: TeamTask | None = None) -> dict[str, object]:
    """Healthz sidecar + snapshot par bot (read-only, phase D L1)."""
    base = sidecar_base_url()
    bots = list(managed_bot_ids())
    if task and isinstance(task.context.get("player_ia_bots"), list):
        extra = [str(x).strip().lower() for x in task.context["player_ia_bots"] if str(x).strip()]
        if extra:
            bots = extra

    checks: list[dict[str, object]] = []
    health_ok = False
    required = required_bot_ids()

    try:
        with httpx.Client(timeout=httpx.Timeout(12.0)) as client:
            try:
                hr = client.get(f"{base}/healthz")
                health_ok = hr.status_code == 200
                body = hr.json() if hr.content else {}
                if isinstance(body, dict) and body.get("ok") is False:
                    health_ok = False
                checks.append({"kind": "sidecar_healthz", "url": f"{base}/healthz", "ok": health_ok, "status": hr.status_code})
            except httpx.HTTPError as e:
                checks.append({"kind": "sidecar_healthz", "url": f"{base}/healthz", "ok": False, "error": str(e)})

            for bot in bots:
                url = f"{base}/v1/player-snapshot"
                is_required = bot.lower() in required
                try:
                    sr = client.get(url, params={"player": bot.capitalize()})
                    snap_ok = sr.status_code == 200
                    snap: dict[str, object] = {}
                    if sr.content:
                        try:
                            raw = sr.json()
                            if isinstance(raw, dict):
                                inner = raw.get("snapshot")
                                snap = inner if isinstance(inner, dict) else raw
                        except ValueError:
                            snap_ok = False
                    online = bool(snap.get("online") or snap.get("connected"))
                    bot_ok = snap_ok and online
                    entry: dict[str, object] = {
                        "kind": "player_snapshot",
                        "player": bot,
                        "required": is_required,
                        "ok": bot_ok if is_required else True,
                        "online": online,
                        "status": sr.status_code,
                    }
                    if not is_required and not bot_ok:
                        entry["skipped"] = True
                    if snap.get("zone"):
                        entry["zone"] = snap.get("zone")
                    if bot_ok:
                        try:
                            evr = client.get(
                                f"{base}/v1/events",
                                params={"player": bot.capitalize(), "after": "", "limit": str(_events_sample_limit())},
                            )
                            events_payload = evr.json() if evr.content else {}
                            events_raw = events_payload.get("events") if isinstance(events_payload, dict) else []
                            events = [x for x in events_raw if isinstance(x, dict)] if isinstance(events_raw, list) else []
                            humanity = _score_humanity(events, bot)
                            entry["humanity"] = humanity
                            checks.append(
                                {
                                    "kind": "player_humanity",
                                    "player": bot,
                                    "required": is_required,
                                    "ok": True,
                                    "score": humanity["score"],
                                    "band": humanity["band"],
                                    "signals": humanity["signals"],
                                }
                            )
                        except httpx.HTTPError as e:
                            checks.append(
                                {
                                    "kind": "player_humanity",
                                    "player": bot,
                                    "required": is_required,
                                    "ok": False,
                                    "error": str(e),
                                }
                            )
                    checks.append(entry)
                except httpx.HTTPError as e:
                    checks.append(
                        {
                            "kind": "player_snapshot",
                            "player": bot,
                            "required": is_required,
                            "ok": False if is_required else True,
                            "skipped": not is_required,
                            "error": str(e),
                        }
                    )
    except httpx.HTTPError as e:
        return {"kind": "player_ia_probe", "ok": False, "error": str(e), "sidecar": base}

    online_count = sum(
        1 for c in checks if c.get("kind") == "player_snapshot" and c.get("online") and not c.get("skipped")
    )
    required_ok = all(c.get("ok") for c in checks if c.get("kind") == "player_snapshot" and c.get("required"))
    all_ok = health_ok and required_ok
    humanity_scores = [
        float(c.get("score"))
        for c in checks
        if c.get("kind") == "player_humanity" and isinstance(c.get("score"), (int, float))
    ]
    humanity_avg = round(sum(humanity_scores) / len(humanity_scores), 3) if humanity_scores else None
    truth_guard = run_world_truth_guard()
    checks.append(
        {
            "kind": "world_truth_guard",
            "ok": bool(truth_guard.get("ok", False)),
            "enabled": bool(truth_guard.get("enabled", True)),
        }
    )
    if isinstance(truth_guard.get("checks"), list):
        for row in truth_guard["checks"]:
            if isinstance(row, dict):
                entry = dict(row)
                check_kind = str(entry.get("kind") or "unknown")
                entry["kind"] = "world_truth_guard_check"
                entry["check_kind"] = check_kind
                checks.append(entry)

    # Soft par défaut : truth-guard advisory (LBG_TEAM_PLAYER_IA_TRUTH_GUARD_HARD=1 pour hard-fail)
    hard = os.environ.get("LBG_TEAM_PLAYER_IA_TRUTH_GUARD_HARD", "0").strip().lower() in {"1", "true", "yes", "on"}
    if hard:
        all_ok = all_ok and bool(truth_guard.get("ok", False))
    return {
        "kind": "player_ia_probe",
        "ok": all_ok,
        "sidecar": base,
        "target_vm": "246-prime",
        "bots_checked": bots,
        "online_count": online_count,
        "humanity_avg": humanity_avg,
        "checks": checks,
    }
