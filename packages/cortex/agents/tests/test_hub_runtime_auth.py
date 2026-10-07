"""Tests auth + persistance economy."""

from __future__ import annotations

from pathlib import Path

from tools.hub_runtime.auth import HubAuth
from tools.hub_runtime.economy import HubEconomy


def test_auth_register_login_roundtrip(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("LBG_HUB_STATE_DIR", str(tmp_path))
    auth = HubAuth()
    r1 = auth.register_or_login("Teome", "secret")
    assert r1["ok"] and r1["session_token"]
    tok = r1["session_token"]
    assert auth.resolve(tok)["username"] == "Teome"
    bad = auth.register_or_login("Teome", "wrong")
    assert not bad["ok"]
    ok = auth.register_or_login("Teome", "secret")
    assert ok["ok"]
    sel = auth.select_character(ok["session_token"], int(ok["characters"][0]["id"]))
    assert sel["ok"] and "ws_url" in sel
    ent = auth.enter_zone(ok["session_token"], "scrapaltai")
    assert ent["ok"] and ent["your_character_id"] > 0


def test_economy_persists(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("LBG_HUB_STATE_DIR", str(tmp_path))
    eco = HubEconomy()
    eco.accept("PersistMe", "lh_survey_dunes", "npc:core3_daan_oth")
    path = tmp_path / "players_state.json"
    assert path.is_file()
    eco2 = HubEconomy()
    st = eco2.status("PersistMe")
    assert any(a.get("id") == "lh_survey_dunes" for a in st["active"])


def test_spike_local_token_resolves() -> None:
    auth = HubAuth()
    assert auth.resolve("spike-local")["character_id"] == 100001
