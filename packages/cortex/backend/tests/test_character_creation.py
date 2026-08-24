"""Tests — Création de personnage (Amas)."""

import pytest
from fastapi.testclient import TestClient

from main import create_app
from services.character_creation import clear_store


@pytest.fixture(autouse=True)
def _reset_store():
    clear_store()
    yield
    clear_store()


@pytest.fixture()
def client():
    return TestClient(create_app())


# ── Mode archétype ──────────────────────────────────────────────

def test_create_archetype(client):
    resp = client.post("/v1/characters", json={
        "mode": "archetype",
        "archetype": "traqueur",
        "customization": {"name": "Kael"},
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Kael"
    assert body["archetype_starter"] == "traqueur"
    assert body["race"] in ("race:fel_rani", "race:varkoon")
    assert body["stats"]["hp"] == 100
    assert body["is_ai"] is False
    assert body["lore_brief"]


def test_create_archetype_missing(client):
    resp = client.post("/v1/characters", json={
        "mode": "archetype",
        "customization": {"name": "Test"},
    })
    assert resp.status_code == 422


# ── Mode empreinte ──────────────────────────────────────────────

def test_create_empreinte(client):
    resp = client.post("/v1/characters", json={
        "mode": "empreinte",
        "empreinte_pnj_id": "npc:core3_kisreudi",
        "customization": {"name": "Iris"},
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["race"] == "race:fel_rani"
    assert body["race_display"] == "Fel'Rani"
    assert "Kisreudi" not in body["name"]


def test_create_empreinte_unknown_pnj(client):
    resp = client.post("/v1/characters", json={
        "mode": "empreinte",
        "empreinte_pnj_id": "npc:nobody",
        "customization": {"name": "Ghost"},
    })
    assert resp.status_code == 404


# ── Mode chaos ──────────────────────────────────────────────────

def test_create_chaos(client):
    resp = client.post("/v1/characters", json={
        "mode": "chaos",
        "customization": {"name": "Rng"},
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["race"].startswith("race:")
    assert body["stats"]["hp"] == 100
    assert "vibré sans guide" in body["lore_brief"]


# ── Joueur IA ───────────────────────────────────────────────────

def test_create_ai_player(client):
    resp = client.post("/v1/characters", json={
        "mode": "archetype",
        "archetype": "soigneur",
        "customization": {"name": "IA-Medic"},
        "is_ai": True,
        "ai_brief": "un soigneur discret qui reste à la clinique",
        "skip_awakening": True,
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["is_ai"] is True
    assert body["origin"]["ai_brief"] == "un soigneur discret qui reste à la clinique"


# ── Validations ─────────────────────────────────────────────────

def test_duplicate_name(client):
    client.post("/v1/characters", json={
        "mode": "chaos",
        "customization": {"name": "Unique"},
    })
    resp = client.post("/v1/characters", json={
        "mode": "chaos",
        "customization": {"name": "Unique"},
    })
    assert resp.status_code == 409


def test_duplicate_name_case_insensitive(client):
    client.post("/v1/characters", json={
        "mode": "chaos",
        "customization": {"name": "Kael"},
    })
    resp = client.post("/v1/characters", json={
        "mode": "chaos",
        "customization": {"name": "kael"},
    })
    assert resp.status_code == 409


def test_max_characters_per_account(client, monkeypatch):
    monkeypatch.setattr("services.character_creation.CHARACTER_CREATE_COOLDOWN_S", 0)
    for i in range(6):
        resp = client.post(
            "/v1/characters",
            json={"mode": "chaos", "customization": {"name": f"Char{i}"}},
            headers={"X-Account-Id": "acct_full"},
        )
        assert resp.status_code == 201

    resp = client.post(
        "/v1/characters",
        json={"mode": "chaos", "customization": {"name": "Char6"}},
        headers={"X-Account-Id": "acct_full"},
    )
    assert resp.status_code == 403


def test_archetype_with_race_id(client):
    resp = client.post("/v1/characters", json={
        "mode": "archetype",
        "archetype": "traqueur",
        "race_id": "race:varkoon",
        "customization": {"name": "Tracker"},
    })
    assert resp.status_code == 201
    assert resp.json()["race"] == "race:varkoon"


def test_archetype_invalid_race(client):
    resp = client.post("/v1/characters", json={
        "mode": "archetype",
        "archetype": "traqueur",
        "race_id": "race:tinkling",
        "customization": {"name": "BadRace"},
    })
    assert resp.status_code == 422


def test_human_create_cooldown(client):
    resp1 = client.post(
        "/v1/characters",
        json={"mode": "chaos", "customization": {"name": "CooldownA"}},
        headers={"X-Account-Id": "acct_cd"},
    )
    assert resp1.status_code == 201
    resp2 = client.post(
        "/v1/characters",
        json={"mode": "chaos", "customization": {"name": "CooldownB"}},
        headers={"X-Account-Id": "acct_cd"},
    )
    assert resp2.status_code == 429


def test_ai_create_no_cooldown(client):
    resp1 = client.post(
        "/v1/characters",
        json={
            "mode": "chaos",
            "customization": {"name": "AiCdA"},
            "is_ai": True,
        },
        headers={"X-Account-Id": "acct_ai_cd"},
    )
    resp2 = client.post(
        "/v1/characters",
        json={
            "mode": "chaos",
            "customization": {"name": "AiCdB"},
            "is_ai": True,
        },
        headers={"X-Account-Id": "acct_ai_cd"},
    )
    assert resp1.status_code == 201
    assert resp2.status_code == 201


def test_name_too_short(client):
    resp = client.post("/v1/characters", json={
        "mode": "chaos",
        "customization": {"name": "X"},
    })
    assert resp.status_code == 422


def test_noyau_created_on_first_character(client):
    resp = client.post("/v1/characters", json={
        "mode": "chaos",
        "customization": {"name": "FirstCore"},
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["noyau_id"].startswith("noyau_")
    assert len(body["particule_seed"]) >= 8


def test_noyau_shared_across_characters(client, monkeypatch):
    monkeypatch.setattr("services.character_creation.CHARACTER_CREATE_COOLDOWN_S", 0)
    r1 = client.post(
        "/v1/characters",
        json={"mode": "chaos", "customization": {"name": "CoreA"}},
        headers={"X-Account-Id": "acct_noyau"},
    )
    r2 = client.post(
        "/v1/characters",
        json={"mode": "chaos", "customization": {"name": "CoreB"}},
        headers={"X-Account-Id": "acct_noyau"},
    )
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["noyau_id"] == r2.json()["noyau_id"]
    assert r1.json()["particule_seed"] == r2.json()["particule_seed"]
