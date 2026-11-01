"""Tests unitaires pour la Vision Contextuelle Ponctuelle (Phase 3 Ticket 1.2)."""

from __future__ import annotations

import base64

from fastapi.testclient import TestClient

from main import app
from services.vision_service import diagnose_text_excerpt, is_vision_context_request

client = TestClient(app)


def test_is_vision_context_request() -> None:
    assert is_vision_context_request("Dis Lyra, regarde mon écran s'il te plaît") is True
    assert is_vision_context_request("Peux-tu regarde cette erreur dans le terminal ?") is True
    assert is_vision_context_request("Inspecte ce bug sur la fenêtre") is True
    assert is_vision_context_request("Bonjour comment vas-tu aujourd'hui ?") is False


def test_diagnose_text_excerpt_patterns() -> None:
    d_import = diagnose_text_excerpt(
        "Traceback: ModuleNotFoundError: No module named 'httpx'",
        window_title="Cursor - main.py",
        process_name="Cursor",
    )
    assert d_import["category"] == "Erreur d'importation Python"
    assert "venv" in d_import["diagnosis_hint"]

    d_godot = diagnose_text_excerpt(
        "SCRIPT ERROR: Assertion failed: Au moins 1 établi requis",
        window_title="Godot Engine",
        process_name="godot",
    )
    assert d_godot["category"] == "Erreur GDScript / Godot Engine"
    assert "ci_godot_headless.sh" in d_godot["diagnosis_hint"]


def test_vision_health_and_analyze_endpoint() -> None:
    r_health = client.get("/v1/vision/health")
    assert r_health.status_code == 200
    data_h = r_health.json()
    assert data_h["ok"] is True
    assert data_h["scope"] == "active_window_only"
    assert data_h["persisted_to_disk"] is False

    # Image PNG minimale 1x1 en base64
    sample_png_b64 = base64.b64encode(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR").decode("ascii")
    r_analyze = client.post(
        "/v1/vision/analyze",
        json={
            "prompt": "Regarde cette erreur dans mon terminal",
            "image_b64": sample_png_b64,
            "window_title": "Terminal — pytest",
            "process_name": "bash",
            "ocr_text": "TypeError: 'NoneType' object is not subscriptable",
            "allow_remote_vlm": False,
        },
    )
    assert r_analyze.status_code == 200
    body = r_analyze.json()
    assert body["ok"] is True
    assert body["intent_detected"] is True
    assert body["persisted_to_disk"] is False
    assert body["purged_from_memory"] is True
    assert body["decoded_bytes"] > 0
    assert body["category"] == "Exception d'exécution sur type ou attribut"
    assert "TypeError" in body["analysis"]

