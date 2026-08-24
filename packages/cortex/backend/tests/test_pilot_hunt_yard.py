from fastapi.testclient import TestClient

from backend.main import app
from lbg_agents.hunt_yard import session_reset


def test_hunt_yard_reset_and_tick() -> None:
    session_reset(seed=1)
    client = TestClient(app)
    r = client.post("/v1/pilot/hunt-yard/reset", json={"seed": 3})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["tick"] == 0
    assert len(data["players"]) == 3
    assert {p["id"] for p in data["players"]} == {"lia", "nix", "mira"}
    assert data["status"] == "ongoing"

    t = client.post("/v1/pilot/hunt-yard/tick", json={"n": 12})
    assert t.status_code == 200
    stepped = t.json()
    assert stepped["tick"] == 12
    assert stepped["players"][0]["last_action"] in {"move", "attack", "idle", "heal", "pickup", "use_potion"}

    g = client.get("/v1/pilot/hunt-yard")
    assert g.status_code == 200
    assert g.json()["tick"] == 12


def test_hunt_yard_run_reaches_victory() -> None:
    client = TestClient(app)
    client.post("/v1/pilot/hunt-yard/reset", json={"seed": 1})
    r = client.post("/v1/pilot/hunt-yard/run", json={"max_ticks": 350})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "victory"
    assert data["kills"] == 5
    assert data["loot"] == []
