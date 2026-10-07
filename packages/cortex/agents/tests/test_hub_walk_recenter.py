"""Tests hub_walk_recenter (sans sidecar)."""
from __future__ import annotations

from types import SimpleNamespace

from lbg_agents.hub_walk_recenter import (
    enqueue_walk_home,
    hub_target_for,
    is_far_from_hub,
    plaza_target,
)


def test_hub_target_lia_near_plaza() -> None:
    t = hub_target_for("lia")
    p = plaza_target()
    assert abs(t[0] - p[0]) < 80.0
    assert abs(t[1] - p[1]) < 80.0


def test_is_far_mos_eisley() -> None:
    snap = {"online": True, "x": 3520.0, "y": -4800.0, "z": 5.0}
    assert is_far_from_hub(snap) is True


def test_is_near_plaza() -> None:
    snap = {"online": True, "x": 4749.0, "y": -737.0, "z": 32.0}
    assert is_far_from_hub(snap) is False


def test_enqueue_walk_home_force(monkeypatch) -> None:
    calls: list[dict] = []

    def _enq(player, **kwargs):
        calls.append({"player": getattr(player, "firstname", None), **kwargs})
        return {"ok": True, "outcome": "ok"}

    monkeypatch.setenv("LBG_QUEST_HUB_BOT_MOVEMENT", "walk")
    player = SimpleNamespace(id="lia", firstname="Lia")
    snap = {"online": True, "x": 3520.0, "y": -4800.0, "z": 5.0, "zone": "tatooine"}
    out = enqueue_walk_home(player, snapshot=snap, enqueue=_enq, force=True)
    assert out is not None
    assert out.get("ok") is True
    assert out.get("reason") == "hub_walk_home"
    assert out.get("movement") == "walk"
    assert calls and calls[0]["action"] == "move_to"
    assert calls[0]["message"] == "hub_walk_home"
