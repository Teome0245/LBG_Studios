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


@pytest.fixture(autouse=True)
def _bridge_tmp(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    bridge = tmp_path / "bridge"
    monkeypatch.setenv("LBG_CORE3_IA_BRIDGE_DIR", str(bridge))
    craft._players.clear()  # type: ignore[attr-defined]
    quests._players.clear()  # type: ignore[attr-defined]


def test_inventory_persists_across_runtime_reload() -> None:
    craft.reset_player("Lia")
    out = craft.craft_combine("Lia", "ration_compacte")
    assert out["ok"] is True
    craft._players.clear()  # type: ignore[attr-defined]

    inv = craft.inventory_payload("Lia")
    ids = {str(row.get("id")) for row in inv["inventory"] if isinstance(row, dict)}
    assert "ration_compacte" in ids
    assert inv["persisted"] is True


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
