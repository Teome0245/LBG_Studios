from __future__ import annotations

import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[2] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import m10_craft_runtime as craft  # noqa: E402
import quest_hub_runtime as quests  # noqa: E402
from backend.services import session_quest_enrich as enrich  # noqa: E402
from core3_bridge_state import clear_state_cache, player_items_path, save_json_doc  # noqa: E402


@pytest.fixture(autouse=True)
def _bridge_tmp(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    bridge = tmp_path / "bridge"
    monkeypatch.setenv("LBG_CORE3_IA_BRIDGE_DIR", str(bridge))
    craft._players.clear()  # type: ignore[attr-defined]
    quests._players.clear()  # type: ignore[attr-defined]
    clear_state_cache()


def test_inventory_persists_across_runtime_reload() -> None:
    craft.reset_player("Lia")
    out = craft.craft_combine("Lia", "ration_compacte")
    assert out["ok"] is True
    craft._players.clear()  # type: ignore[attr-defined]

    inv = craft.inventory_payload("Lia")
    ids = {str(row.get("id")) for row in inv["inventory"] if isinstance(row, dict)}
    assert "ration_compacte" in ids
    assert inv["persisted"] is True
    assert inv.get("core3_live") is False
    assert inv.get("source") == "core3_bridge_inventory"


def test_inventory_prefers_core3_lua_dump_when_online() -> None:
    save_json_doc(
        player_items_path(),
        {
            "source": "core3_lua_inventory_v1",
            "players": {
                "Lia": {
                    "online": True,
                    "zone": "tatooine",
                    "inventory_count": 1,
                    "skills": ["artisan_rue_r1"],
                    "inventory": [
                        {
                            "id": "foraged_fruit",
                            "name": "Fruit de forage",
                            "qty": 3,
                            "icon": "ration",
                            "template": "object/tangible/food/foraged/edible_berry.iff",
                        }
                    ],
                }
            },
        },
    )
    inv = craft.inventory_payload("local")
    assert inv["core3_live"] is True
    assert inv["source"] == "core3_lua_inventory"
    assert inv["core3_player"] == "Lia"
    ids = {str(row.get("id")): row for row in inv["inventory"] if isinstance(row, dict)}
    assert ids["foraged_fruit"]["qty"] == 3
    skills = craft.player_skills_payload("local")
    assert skills["core3_live"] is True
    assert "artisan_rue_r1" in skills["skills"]


def test_inventory_ignores_offline_core3_dump() -> None:
    craft.reset_player("local")
    save_json_doc(
        player_items_path(),
        {
            "source": "core3_lua_inventory_v1",
            "players": {
                "Lia": {"online": False, "inventory": [], "inventory_count": 0, "skills": []},
            },
        },
    )
    inv = craft.inventory_payload("local")
    assert inv["core3_live"] is False
    assert inv["source"] == "core3_bridge_inventory"
    ids = {str(row.get("id")) for row in inv["inventory"] if isinstance(row, dict)}
    assert "scrap_metal" in ids


def test_quest_status_persists_and_emits_bridge_state() -> None:
    quests.reset_player("Lia")
    accepted = quests.accept_quest("Lia", "lh_delivery_starport")
    assert accepted["ok"] is True
    progressed = quests.progress_quest("Lia", "lh_delivery_starport", step_id="pickup")
    assert progressed["ok"] is True
    quests._players.clear()  # type: ignore[attr-defined]

    status = quests.status_payload("Lia")
    assert status["persisted"] is True
    active = status.get("active") or []
    assert active and active[0]["id"] == "lh_delivery_starport"

    snapshot = quests.quest_state_payload("Lia")
    rows = snapshot.get("quest_states") or []
    assert any(str(row.get("quest_id")) == "lh_delivery_starport" for row in rows if isinstance(row, dict))


def test_session_quest_enrich_prefers_status_and_inventory(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get_json(path: str, *, timeout_s: float = 2.5) -> dict[str, object]:
        del timeout_s
        if path.startswith("/v1/quests/status"):
            return {
                "ok": True,
                "active": [
                    {
                        "id": "lh_delivery_starport",
                        "title": "Livraison au spatioport",
                        "objective": "Porter le colis au spatioport",
                        "progress_steps": [{"id": "pickup", "done": True}, {"id": "deliver", "done": False}],
                    }
                ],
                "credits": 72,
            }
        if path.startswith("/v1/inventory"):
            return {"ok": True, "inventory": [{"id": "ration_compacte", "qty": 1}]}
        return {}

    monkeypatch.setattr(enrich, "_get_json", fake_get_json)
    monkeypatch.setattr(enrich, "fetch_quest_states", lambda timeout_s=2.5: [])

    out = enrich.merge_quest_into_session_summary({"player_name": "Lia"}, actor_id="character:Lia", force=True)
    ss = out["session_summary"]
    assert ss["tracked_quest"] == "lh_delivery_starport"
    assert "progress=1/2" in ss["quest_snapshot"]
    assert ss["player_note"] == "player:Lia inv:1"
    assert ss["session_mood"] == "credits:72"


def test_hunt_meute_requires_victory() -> None:
    quests.reset_player("Lia")
    quests.load_templates()
    quests.accept_quest("Lia", "lh_hunt_chacal")
    assert quests.progress_quest("Lia", "lh_hunt_chacal", step_id="exit")["ok"] is True
    blocked = quests.progress_quest("Lia", "lh_hunt_chacal", step_id="meute")
    assert blocked["ok"] is False
    assert blocked["error"] == "hunt_required"


def test_claim_hunt_quest_after_victory() -> None:
    from hunt_yard_bridge import session_reset, session_run  # noqa: E402

    quests.reset_player("Lia")
    quests.load_templates()
    quests.accept_quest("Lia", "lh_hunt_chacal")
    assert quests.progress_quest("Lia", "lh_hunt_chacal", step_id="exit")["ok"] is True
    session_reset(seed=1)
    run = session_run(max_ticks=120)
    assert run.get("status") == "victory"
    claim = quests.claim_hunt_quest_progress("Lia")
    assert claim["ok"] is True
    status = quests.status_payload("Lia")
    active = status.get("active") or []
    assert active
    steps = active[0].get("progress_steps") or []
    meute = next((s for s in steps if isinstance(s, dict) and s.get("id") == "meute"), None)
    assert meute is not None
    assert meute.get("done") is True
