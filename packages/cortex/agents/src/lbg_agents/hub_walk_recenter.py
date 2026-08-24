"""Recentrage Lost Heaven — marche visible, jamais téléport.

Rappel ponctuel des joueurs IA (et humains listés) vers leurs ancres plaza.
Ne les enferme pas : pas de laisse permanente ; la clôture hub côté client
est désactivée séparément (``enforce_hub_fence=false``).
"""
from __future__ import annotations

import os
import time
from typing import Any, Callable

from lbg_agents.core3_places import LH_ANCHOR_X, LH_ANCHOR_Y, LH_ANCHOR_Z, bot_spawn
from lbg_agents.core3_players import Core3IaPlayer, list_ai_players
from lbg_agents.quest_hub_bot_autonomy import _dist_xz, ensure_walk_mode

# Au-delà : considéré « hors hub » pour un rappel ponctuel
_FAR_M = float(os.environ.get("LBG_HUB_WALK_HOME_FAR_M", "400") or 400)
_ARRIVE_M = float(os.environ.get("LBG_HUB_WALK_HOME_ARRIVE_M", "45") or 45)
# Évite de spam move_to (annule la marche Lua)
_REENQUEUE_S = float(os.environ.get("LBG_HUB_WALK_HOME_REENQUEUE_S", "25") or 25)

_last_enqueue_at: dict[str, float] = {}


def _truthy(raw: str) -> bool:
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def walk_home_on_far_enabled() -> bool:
    """Laisse douce optionnelle (défaut off — recentrage = one-shot / reconnect)."""
    return _truthy(os.environ.get("LBG_HUB_WALK_HOME_ON_FAR", "0"))


def extra_human_names() -> tuple[str, ...]:
    raw = (os.environ.get("LBG_HUB_WALK_HOME_HUMANS") or "Teome").strip()
    if not raw:
        return ()
    return tuple(p.strip() for p in raw.split(",") if p.strip())


def hub_target_for(player_id: str) -> tuple[float, float, float]:
    """Enqueue Lua : (x, nord, hauteur)."""
    return bot_spawn(player_id)


def plaza_target() -> tuple[float, float, float]:
    return (LH_ANCHOR_X, LH_ANCHOR_Y, LH_ANCHOR_Z)


def is_far_from_hub(snap: dict[str, Any], target: tuple[float, float, float] | None = None) -> bool:
    if not isinstance(snap, dict) or not snap.get("online"):
        return False
    dest = target or plaza_target()
    return _dist_xz(snap, dest) >= _FAR_M


def _can_reenqueue(key: str) -> bool:
    last = _last_enqueue_at.get(key.lower(), 0.0)
    return (time.monotonic() - last) >= _REENQUEUE_S


def _mark_enqueue(key: str) -> None:
    _last_enqueue_at[key.lower()] = time.monotonic()


def enqueue_walk_home(
    player: Core3IaPlayer | str,
    *,
    snapshot: dict[str, Any] | None,
    enqueue: Callable[..., dict[str, Any]],
    force: bool = False,
) -> dict[str, Any] | None:
    """Enqueue ``move_to`` marche vers l'ancre LH. ``force`` ignore distance / cooldown."""
    ensure_walk_mode()
    if isinstance(player, str):
        pid = player.strip().lower()
        firstname = player.strip()
        target = hub_target_for(pid) if pid in {"lia", "nix", "mira", "kael"} else plaza_target()
        from types import SimpleNamespace

        player_obj: Any = SimpleNamespace(id=pid, firstname=firstname, actor_id="")
    else:
        player_obj = player
        target = hub_target_for(player.id)

    snap = snapshot if isinstance(snapshot, dict) else {}
    key = str(getattr(player_obj, "firstname", None) or getattr(player_obj, "id", "") or "")
    if not key:
        return None

    dist = _dist_xz(snap, target) if snap else 1.0e9
    if not force:
        if dist < _ARRIVE_M:
            return None
        if dist < _FAR_M and snap.get("online"):
            return None
        if not _can_reenqueue(key):
            return None

    out = enqueue(
        player_obj,
        action="move_to",
        message="hub_walk_home",
        snapshot=snap,
        target_xyz=target,
    )
    out["reason"] = "hub_walk_home"
    out["movement"] = ensure_walk_mode()
    out["dist_m"] = round(dist, 1)
    out["target"] = {"x": target[0], "y": target[1], "z": target[2]}
    _mark_enqueue(key)
    return out


def maybe_walk_home_proactive(
    player: Core3IaPlayer,
    *,
    snapshot: dict[str, Any] | None,
    enqueue: Callable[..., dict[str, Any]],
) -> dict[str, Any] | None:
    if not walk_home_on_far_enabled():
        return None
    return enqueue_walk_home(player, snapshot=snapshot, enqueue=enqueue, force=False)


def recenter_all_ai_players(
    *,
    enqueue: Callable[..., dict[str, Any]] | None = None,
    fetch_snap: Callable[[str], dict[str, Any]] | None = None,
    include_humans: bool = True,
) -> dict[str, Any]:
    """One-shot : marche tous les bots IA (+ humains optionnels) vers LH."""
    from lbg_agents.core3_player_autonomy import enqueue_direct_action, fetch_snapshot

    enq = enqueue or enqueue_direct_action
    snap_fn = fetch_snap or fetch_snapshot
    ensure_walk_mode()

    results: list[dict[str, Any]] = []
    for player in list_ai_players(enabled_only=True):
        snap = snap_fn(player.firstname)
        out = enqueue_walk_home(player, snapshot=snap, enqueue=enq, force=True)
        results.append(
            {
                "player": player.firstname,
                "id": player.id,
                "online": bool(snap.get("online")),
                "ok": bool(out and out.get("ok")),
                "outcome": (out or {}).get("outcome"),
                "dist_m": (out or {}).get("dist_m"),
                "reason": (out or {}).get("reason"),
            }
        )

    if include_humans:
        for name in extra_human_names():
            snap = snap_fn(name)
            out = enqueue_walk_home(name, snapshot=snap, enqueue=enq, force=True)
            results.append(
                {
                    "player": name,
                    "id": name.lower(),
                    "online": bool(snap.get("online")),
                    "ok": bool(out and out.get("ok")),
                    "outcome": (out or {}).get("outcome"),
                    "dist_m": (out or {}).get("dist_m"),
                    "reason": (out or {}).get("reason"),
                    "human": True,
                }
            )

    ok_n = sum(1 for r in results if r.get("ok"))
    return {
        "ok": ok_n > 0,
        "movement": ensure_walk_mode(),
        "count": len(results),
        "ok_count": ok_n,
        "results": results,
    }


def main() -> None:
    out = recenter_all_ai_players()
    print(out)


if __name__ == "__main__":
    main()
