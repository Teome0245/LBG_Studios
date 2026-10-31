from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from main import app
from services import stt_service

client = TestClient(app)


def test_stt_health_default():
    response = client.get("/v1/stt")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["enabled"] is True
    assert "provider" in data
    assert "supported_languages" in data
    assert "fr" in data["supported_languages"]


def test_stt_disabled(monkeypatch):
    monkeypatch.setenv("LBG_STT_ENABLED", "0")
    response = client.get("/v1/stt")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert data["enabled"] is False

    # POST should return 503
    fake_audio = BytesIO(b"RIFF\x24\x00\x00\x00WAVEfmt ")
    files = {"file": ("test.wav", fake_audio, "audio/wav")}
    res_post = client.post("/v1/stt", files=files)
    assert res_post.status_code == 503


def test_stt_mock_transcribe(monkeypatch):
    monkeypatch.setenv("LBG_STT_ENABLED", "1")
    monkeypatch.setenv("LBG_STT_MOCK", "1")

    fake_audio = BytesIO(b"RIFF\x24\x00\x00\x00WAVEfmt test data")
    files = {"file": ("test.wav", fake_audio, "audio/wav")}
    response = client.post("/v1/stt", files=files, data={"language": "fr"})
    assert response.status_code == 200
    data = response.json()
    assert "text" in data
    assert data["provider"] == "mock"
    assert data["language"] == "fr"


def test_stt_empty_audio_raises_400(monkeypatch):
    monkeypatch.setenv("LBG_STT_ENABLED", "1")
    monkeypatch.setenv("LBG_STT_MOCK", "1")

    empty_audio = BytesIO(b"")
    files = {"file": ("empty.wav", empty_audio, "audio/wav")}
    response = client.post("/v1/stt", files=files)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_stt_upstream_whisper_call(monkeypatch):
    monkeypatch.setenv("LBG_STT_ENABLED", "1")
    monkeypatch.setenv("LBG_STT_URL", "http://192.168.0.111:9000/v1/audio/transcriptions")

    class MockResponse:
        status_code = 200

        def json(self):
            return {"text": "Bonjour Compagnon, quel est l'état du serveur ?"}

    class MockClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        async def post(self, url, files=None, data=None):
            return MockResponse()

    monkeypatch.setattr("httpx.AsyncClient", lambda **kwargs: MockClient())

    result = await stt_service.transcribe_audio_bytes(b"dummy_wav_bytes", "test.wav", "fr")
    assert result["text"] == "Bonjour Compagnon, quel est l'état du serveur ?"
    assert result["language"] == "fr"
    assert result["provider"] == "whisper"
