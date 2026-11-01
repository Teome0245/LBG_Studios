"""Tests unitaires pour le Replay Chronologique & Timeline Synaptique Pilot Web (Phase 3 Ticket 5.1)."""

from __future__ import annotations

import time

from fastapi.testclient import TestClient

from api.v1.routes.pilot.status import _brain_timeline_buffer
from main import app

client = TestClient(app)


def test_brain_timeline_record_and_scrub_offset() -> None:
    _brain_timeline_buffer.clear()
    now = time.time()

    # 1. Enregistre un événement passé à T - 300s (-5 minutes : alerte tempête de sable)
    r_past = client.post(
        "/v1/pilot/brain/timeline",
        json={
            "pole_key": "world",
            "tag": "Météo Scrapaltai",
            "message": "Tempête de sable détectée — repli des binômes IA vers la Cantina",
            "level": "boost",
            "cognitive_load": 0.85,
            "gauges": {"confidence": 68.0, "curiosity": 55.0, "stress": 45.0, "fatigue": 20.0},
            "ts": now - 300.0,
        },
    )
    assert r_past.status_code == 200
    assert r_past.json()["ok"] is True

    # 2. Enregistre un événement présent à T - 2s
    r_now = client.post(
        "/v1/pilot/brain/timeline",
        json={
            "pole_key": "cortex",
            "tag": "Orchestrateur",
            "message": "Cycle nominal de supervision",
            "level": "normal",
            "cognitive_load": 0.42,
            "gauges": {"confidence": 82.0, "curiosity": 70.0, "stress": 12.0, "fatigue": 14.0},
            "ts": now - 2.0,
        },
    )
    assert r_now.status_code == 200

    # 3. Scrubber positionné à -300s (-5 minutes) : doit reconstituer l'impulsion de tempête
    r_scrub = client.get("/v1/pilot/brain/timeline?window_sec=900&offset_sec=-300")
    assert r_scrub.status_code == 200
    body = r_scrub.json()
    assert body["ok"] is True
    assert body["buffer_size"] >= 2
    snap = body["snapshot"]
    assert snap is not None
    assert snap["pole_key"] == "world"
    assert "Tempête de sable" in snap["message"]
    assert snap["cognitive_load"] == 0.85


def test_world_event_automatically_feeds_brain_timeline() -> None:
    _brain_timeline_buffer.clear()
    r_evt = client.post(
        "/v1/pilot/world/events",
        json={
            "source": "prime_hub",
            "bot_name": "Nix",
            "event_type": "decision",
            "message": "Nix négocie un troc d'eau avec Lia à La Perle",
            "target_pole": "world",
        },
    )
    assert r_evt.status_code == 200

    r_tl = client.get("/v1/pilot/brain/timeline")
    assert r_tl.status_code == 200
    data = r_tl.json()
    assert data["buffer_size"] == 1
    assert "Nix négocie un troc" in data["snapshot"]["message"]

