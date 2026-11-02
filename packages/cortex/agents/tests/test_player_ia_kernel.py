"""Noyau O3 : même agent, deux adapters, mutations dures bloquées."""

from __future__ import annotations

from lbg_agents.player_ia.adapters import GodotHubHttpAdapter, SandboxAdapter, StudioDeskAdapter
from lbg_agents.player_ia.contract import make_action, validate_action
from lbg_agents.player_ia.kernel import PlayerAgentKernel


def test_hard_mutations_are_blocked() -> None:
    for kind in ("SET_PRICE", "DEAL_DAMAGE", "GRANT_LOOT", "COMPLETE_QUEST", "SET_REPUTATION"):
        err = validate_action(make_action(kind, value=1))
        assert err is not None
        assert err["error"] == "hard_mutation_blocked"


def test_trade_price_band() -> None:
    ok = validate_action(make_action("TRADE", listed_price=100, offer_price=110))
    assert ok is None
    bad = validate_action(make_action("TRADE", listed_price=100, offer_price=140))
    assert bad is not None
    assert bad["error"] == "trade_price_out_of_band"


def test_kernel_runs_on_sandbox_without_godot() -> None:
    env = SandboxAdapter()
    env.events = [{"event_id": "event:test", "poi_id": "poi:sandbox_beacon"}]
    kernel = PlayerAgentKernel("nix", playstyle="prospecteur")
    tick = kernel.tick(env)
    assert tick["adapter"] == "sandbox"
    assert tick["ok"] is True
    assert tick["action"]["type"] == "MOVE"
    assert env.positions["nix"] == [8.0, 0.0, 4.0]
    assert kernel.memory.last("act") is not None


def test_same_kernel_on_studio_desk_second_adapter() -> None:
    desk = StudioDeskAdapter(focus_title="LBG Compagnon — Cursor")
    kernel = PlayerAgentKernel("lia", playstyle="studio_desk")
    tick = kernel.tick(desk)
    assert tick["adapter"] == "studio_desk"
    assert tick["ok"] is True
    assert tick["action"]["type"] == "NOTE"
    assert desk.notes and desk.notes[0].startswith("focus:")
    idle_desk = StudioDeskAdapter()
    idle = PlayerAgentKernel("lia", playstyle="studio_desk").tick(idle_desk)
    assert idle["action"]["type"] == "IDLE"


def test_godot_adapter_maps_move_over_http(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    posts: list[tuple[str, dict]] = []

    class _Fake:
        def get(self, url, params=None, timeout=None):  # noqa: ANN001
            class R:
                status_code = 200

                def raise_for_status(self) -> None:
                    return None

                def json(self) -> dict:
                    if "inventory" in url:
                        return {"inventory": [{"id": "scrap_metal", "qty": 1}]}
                    if "events" in url:
                        return {"active": False}
                    return {"ok": True}

            return R()

        def post(self, url, json=None, timeout=None):  # noqa: ANN001
            posts.append((url, json or {}))

            class R:
                status_code = 200
                text = "{}"

                def json(self) -> dict:
                    return {"ok": True, "queued": True}

            return R()

    hub = GodotHubHttpAdapter("http://192.168.0.246:8787", client=_Fake())  # type: ignore[arg-type]
    kernel = PlayerAgentKernel("Nix", playstyle="prospecteur")
    # Pas d'événement → MOVE vers rien / IDLE ; on force un POI via observation sandbox mix
    # En l'absence de POI le kernel IDLE, donc on injecte un event via get_observation monkeypatch
    real_obs = hub.get_observation

    def _obs(agent_id: str) -> dict:
        obs = real_obs(agent_id)
        obs["nearby_pois"] = [{"id": "poi:lh_scrap_pile", "distance": 9.0}]
        return obs

    monkeypatch.setattr(hub, "get_observation", _obs)
    tick = kernel.tick(hub)
    assert tick["adapter"] == "godot_hub"
    assert tick["action"]["type"] == "MOVE"
    assert posts and "/v1/bots/move_to" in posts[0][0]
    assert posts[0][1]["player"] == "Nix"
