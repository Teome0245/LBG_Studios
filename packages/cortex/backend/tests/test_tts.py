"""test_tts.py — Tests unitaires pour l'API et le service de synthèse vocale / visèmes."""

from fastapi.testclient import TestClient

from main import app
from services import tts_service

client = TestClient(app)


def test_tts_health_default():
    response = client.get("/v1/tts")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["enabled"] is True
    assert "provider" in data
    assert "supported_languages" in data
    assert "fr" in data["supported_languages"]


def test_tts_voices_catalog():
    response = client.get("/v1/tts/voices")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "voices" in data
    assert len(data["voices"]) >= 3
    assert any(v["id"] == "fr_FR-siwis-medium" for v in data["voices"])
    assert data["default_voice"] == "fr_FR-siwis-medium"


def test_tts_viseme_generation_deterministic():
    text = "Bonjour le studio Lost Heaven"
    visemes = tts_service.generate_visemes_from_text(text, speed=1.0)
    assert len(visemes) > 0
    # Vérifie que les morph targets VRM canoniques sont présentes
    valid_visemes = {"aa", "ih", "ou", "ee", "oh"}
    for frame in visemes:
        assert frame["viseme"] in valid_visemes
        assert frame["time_offset"] >= 0.0
        assert frame["duration"] > 0.0
        assert 0.0 < frame["weight"] <= 1.0


def test_tts_synthesize_mock_flow(monkeypatch):
    monkeypatch.setenv("LBG_TTS_ENABLED", "1")
    monkeypatch.setenv("LBG_TTS_MOCK", "1")

    payload = {
        "text": "Bonjour Teome, je suis prête.",
        "voice": "fr_FR-siwis-medium",
        "speed": 1.0,
    }
    response = client.post("/v1/tts/synthesize", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["text"] == payload["text"]
    assert data["voice"] == "fr_FR-siwis-medium"
    assert "audio_b64" in data
    assert len(data["audio_b64"]) > 0
    assert "visemes" in data
    assert len(data["visemes"]) >= 4
    assert data["duration_sec"] > 0.0


def test_tts_disabled(monkeypatch):
    monkeypatch.setenv("LBG_TTS_ENABLED", "0")
    response = client.get("/v1/tts")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert data["enabled"] is False

    # POST should return 503
    payload = {"text": "Test"}
    res_post = client.post("/v1/tts/synthesize", json=payload)
    assert res_post.status_code == 503


def test_tts_empty_text_raises_400(monkeypatch):
    monkeypatch.setenv("LBG_TTS_ENABLED", "1")
    monkeypatch.setenv("LBG_TTS_MOCK", "1")

    payload = {"text": "   "}
    response = client.post("/v1/tts/synthesize", json=payload)
    assert response.status_code == 400
