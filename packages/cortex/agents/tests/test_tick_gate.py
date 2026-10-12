"""C11 TickGate — cooldown / queue → 429 tick_busy."""

from __future__ import annotations

import os

import pytest

from lbg_agents import agent_catalog as ac
from lbg_agents.quest_hub_bot_autonomy import is_tick_busy, playstyle_for_player


@pytest.fixture(autouse=True)
def _reset_gate(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LBG_TICK_GATE", "1")
    monkeypatch.setenv("LBG_TICK_COOLDOWN_S", "10")
    monkeypatch.setenv("LBG_TICK_QUEUE_MAX", "1")
    ac.reset_tick_gate()
    yield
    ac.reset_tick_gate()


def test_http_path_to_action_quest_and_craft() -> None:
    assert ac.http_path_to_action("/v1/quests/accept", {"player": "Lia"}) == "quests/accept"
    assert ac.http_path_to_action("/v1/quests/tip", {}) == "tip_stage"
    assert ac.http_path_to_action("/v1/craft/combine", {}) == "craft/start"
    assert ac.http_path_to_action("/v1/enqueue", {"action": "move_to", "player": "Nix"}) == "move_to"
    assert ac.http_path_to_action("/v1/enqueue", {"action": "say"}) is None
    assert ac.http_path_to_action("/v1/quests/reset", {}) is None


def test_guard_allows_first_mutation_blocks_second() -> None:
    body = {"player": "Lia", "quest_id": "lh_show_perle"}
    assert ac.http_post_tick_guard("/v1/quests/accept", body) is None
    blocked = ac.http_post_tick_guard("/v1/quests/progress", body)
    assert blocked is not None
    code, payload = blocked
    assert code == 429
    assert payload["error"] == "tick_busy"
    assert payload["reason"] == "cooldown"
    assert payload["requires_tick"] is True


def test_guard_per_player_isolation() -> None:
    assert ac.http_post_tick_guard("/v1/quests/accept", {"player": "Lia"}) is None
    assert ac.http_post_tick_guard("/v1/quests/accept", {"player": "Nix"}) is None
    assert ac.http_post_tick_guard("/v1/quests/accept", {"player": "Lia"}) is not None


def test_guard_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_TICK_GATE", "0")
    body = {"player": "Lia"}
    assert ac.http_post_tick_guard("/v1/quests/accept", body) is None
    assert ac.http_post_tick_guard("/v1/quests/accept", body) is None


def test_queries_not_gated() -> None:
    assert ac.http_post_tick_guard("/catalog", {}) is None
    # path GET-only — pas dans POST map
    assert ac.http_path_to_action("/catalog", {}) is None


def test_attach_tick_context() -> None:
    out = ac.attach_tick_context({"ok": True}, "craft/start")
    assert out["tick_cost"] == "mutation"
    assert out["context"]["action"] == "craft/start"


def test_is_tick_busy_helper() -> None:
    assert is_tick_busy({"ok": False, "error": "tick_busy", "http_status": 429})
    assert is_tick_busy({"ok": False, "error": "tick_busy", "reason": "cooldown"})
    assert not is_tick_busy({"ok": True, "reason": "hub_quest_dwell"})
    assert not is_tick_busy({"ok": False, "error": "quest_id_required", "http_status": 400})


def test_playstyle_defaults() -> None:
    assert playstyle_for_player("Lia") == "scene"
    assert playstyle_for_player("Nix") == "prospecteur"


def test_playstyle_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_BOT_PLAYSTYLE_LIA", "artisan")
    assert playstyle_for_player("Lia") == "artisan"
