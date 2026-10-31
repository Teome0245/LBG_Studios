from backend.main import app
from fastapi.testclient import TestClient


def test_pilot_world_events_flow() -> None:
    client = TestClient(app)

    # 1. Post a world cognitive decision event
    post_res = client.post(
        "/v1/pilot/world/events",
        json={
            "source": "prime_hub",
            "bot_name": "Nix",
            "event_type": "decision",
            "message": "Joueur IA [Nix] : objectif « reconnaissance » vers Dunes de l'Est",
            "target_pole": "world",
            "metadata": {"origin": "outpost_zalem", "confidence": 0.88},
        },
    )
    assert post_res.status_code == 200
    data = post_res.json()
    assert data["ok"] is True
    assert data["event"]["bot_name"] == "Nix"
    assert "Dunes" in data["event"]["message"]
    assert data["event"]["target_pole"] == "world"

    # 2. Get world events list
    get_res = client.get("/v1/pilot/world/events?limit=5")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["ok"] is True
    assert isinstance(get_data["events"], list)
    assert any(e.get("bot_name") == "Nix" for e in get_data["events"])

    # 3. Check player-ia/runtime includes events
    runtime_res = client.get("/v1/pilot/player-ia/runtime")
    assert runtime_res.status_code == 200
    runtime_data = runtime_res.json()
    assert runtime_data["ok"] is True
    assert "events" in runtime_data
    assert any(e.get("bot_name") == "Nix" for e in runtime_data["events"])
