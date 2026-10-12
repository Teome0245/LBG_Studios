"""Tests analyse d'images Compagnon (vision_ask)."""

from __future__ import annotations

import base64

import pytest
from fastapi.testclient import TestClient

from services import vision_ask as va


def _tiny_png_b64() -> str:
    # PNG 1x1 transparent
    raw = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )
    return base64.b64encode(raw).decode("ascii")


def test_normalize_images_data_uri() -> None:
    b64 = _tiny_png_b64()
    out = va.normalize_images([f"data:image/png;base64,{b64}"])
    assert len(out) == 1
    assert out[0] == b64


def test_normalize_images_rejects_empty() -> None:
    with pytest.raises(ValueError, match="aucune"):
        va.normalize_images([])


@pytest.mark.asyncio
async def test_vision_ask_calls_ollama(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_VISION_LLM_MODEL", "llava:latest")
    monkeypatch.setenv("LBG_VISION_LLM_BASE_URL", "http://192.168.0.110:11434")
    monkeypatch.setenv("LBG_VISION_LLM_TIMEOUT", "60")

    class _Resp:
        status_code = 200
        text = ""

        def json(self) -> dict:
            return {"message": {"role": "assistant", "content": "Un pixel vert."}}

    class _Client:
        last_url = ""
        last_json: dict | None = None

        def __init__(self, *a: object, **k: object) -> None:
            pass

        async def __aenter__(self) -> _Client:
            return self

        async def __aexit__(self, *a: object) -> None:
            return None

        async def post(self, url: str, json: dict | None = None) -> _Resp:
            _Client.last_url = url
            _Client.last_json = json
            return _Resp()

    monkeypatch.setattr(va.httpx, "AsyncClient", _Client)
    out = await va.vision_ask(prompt="Que vois-tu ?", images=[_tiny_png_b64()], profile="compagnon")
    assert out["source"] == "vision"
    assert "pixel" in out["content"].lower()
    assert _Client.last_url.endswith("/api/chat")
    assert isinstance(_Client.last_json, dict)
    assert "think" not in _Client.last_json  # llava: pas de champ think
    user_msg = _Client.last_json["messages"][-1]
    assert user_msg["images"]


def test_pilot_vision_ask_route(monkeypatch: pytest.MonkeyPatch) -> None:
    from main import app

    async def _fake(**kwargs: object) -> dict:
        return {
            "role": "assistant",
            "content": "ok vision",
            "source": "vision",
            "model": "llava:latest",
            "provider": "ollama",
            "latency": 0.1,
        }

    monkeypatch.setattr("services.vision_ask.vision_ask", _fake)
    client = TestClient(app)
    r = client.post(
        "/v1/pilot/vision-ask",
        json={"prompt": "test", "images": [_tiny_png_b64()], "profile": "compagnon"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True
    assert body["response"]["content"] == "ok vision"
