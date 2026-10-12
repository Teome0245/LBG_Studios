"""Tests Agency Phase B — Self-State drives sync."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("LBG_TEAM_DB_PATH", ":memory:")

from services import self_state as svc_self  # noqa: E402
from team import lessons_learned  # noqa: E402


@pytest.fixture(autouse=True)
def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    state_path = tmp_path / "self" / "state.json"
    lessons_path = tmp_path / "lessons_learned.json"
    lessons_path.write_text(
        json.dumps({"schema_version": 1, "lessons": []}, ensure_ascii=False),
        encoding="utf-8",
    )
    monkeypatch.setenv("LBG_SELF_STATE_ENABLED", "1")
    monkeypatch.setenv("LBG_SELF_STATE_PATH", str(state_path))
    monkeypatch.setenv("LBG_TEAM_LESSONS_ENABLED", "1")
    monkeypatch.setenv("LBG_TEAM_LESSONS_PATH", str(lessons_path))
    monkeypatch.setenv("LBG_TEAM_DB_PATH", ":memory:")
    svc_self.reset_cache_for_tests()


def test_default_state_schema() -> None:
    st = svc_self.default_state()
    assert st["schema_version"] == 1
    assert st["goals"] == []
    assert "curiosity" in st["drives"]
    assert st["drives_meta"]["scale"] == "0_1"


def test_sync_from_brain_maps_gauges() -> None:
    out = svc_self.sync_from_brain(
        {
            "gauges": {"curiosity": 50.0, "stress": 10.0, "fatigue": 20.0, "confidence": 80.0},
            "intent": "heal",
            "narrative": "services ok",
            "last_tick_ts": 123.0,
            "last_tick_ok": True,
            "last_error": None,
        }
    )
    assert out is not None
    assert out["drives"]["curiosity"] == pytest.approx(0.5)
    assert out["drives"]["stress"] == pytest.approx(0.1)
    assert out["drives"]["confidence"] == pytest.approx(0.8)
    assert out["intent"]["primary"] == "heal"
    assert out["beliefs"]["orchestrator_ok"] is True
    assert out["last_tick"]["kind"] == "brain"
    assert svc_self.self_state_path().is_file()


def test_sync_from_proactive_tension_and_curiosity_max() -> None:
    svc_self.sync_from_brain(
        {
            "gauges": {"curiosity": 20.0, "stress": 0, "fatigue": 0, "confidence": 50},
            "intent": "monitor",
            "narrative": "",
            "last_tick_ok": True,
        }
    )
    out = svc_self.sync_from_proactive({"tension": 0.7, "curiosite": 0.9, "mode": "autonome"})
    assert out is not None
    assert out["drives"]["tension"] == pytest.approx(0.7)
    # max(0.2 brain, 0.9 proactive)
    assert out["drives"]["curiosity"] == pytest.approx(0.9)
    assert out["last_tick"]["kind"] == "proactive"


def test_disabled_skips_persist(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LBG_SELF_STATE_ENABLED", "0")
    path = tmp_path / "off" / "state.json"
    monkeypatch.setenv("LBG_SELF_STATE_PATH", str(path))
    svc_self.reset_cache_for_tests()
    assert svc_self.sync_from_brain({"gauges": {"curiosity": 99}, "intent": "x"}) is None
    assert not path.is_file()


def test_append_lesson_updates_memory_refs() -> None:
    svc_self.persist_state(svc_self.default_state())
    entry = lessons_learned.append_lesson(
        agent_role="pm",
        pattern="Self-State lit les leçons",
        context="agency_b",
        do_not_repeat="ignorer memory_refs",
        refs=["test"],
    )
    st = svc_self.get_state()
    assert st["memory_refs"]["last_lesson_id"] == entry["id"]
    assert st["memory_refs"]["lessons_count"] >= 1


def test_get_self_status_route() -> None:
    # Import app late so env fixture applies
    from main import app  # noqa: WPS433

    svc_self.sync_from_brain(
        {
            "gauges": {"curiosity": 40.0, "stress": 5.0, "fatigue": 5.0, "confidence": 70.0},
            "intent": "monitor",
            "narrative": "tick",
            "last_tick_ok": True,
        }
    )
    client = TestClient(app)
    r = client.get("/v1/self/status")
    assert r.status_code == 200
    data = r.json()
    assert data["enabled"] is True
    assert data["state"]["drives"]["curiosity"] == pytest.approx(0.4)
    assert data["meta"]["enabled"] is True


def test_meta_status_fields() -> None:
    meta = svc_self.meta_status()
    assert meta["enabled"] is True
    assert "path" in meta
    assert meta["goals_count"] == 0


def test_upsert_pending_will_and_route() -> None:
    st = svc_self.upsert_pending_will(
        will_id="evo:abc123",
        title="Ajouter un dial spontanéité",
        summary="Seed test",
        kind="evolution",
        source="spontaneity",
        meta={"score": 1.0},
    )
    assert st is not None
    wills = st.get("pending_will") or []
    assert any(w.get("id") == "evo:abc123" for w in wills if isinstance(w, dict))

    from main import app  # noqa: WPS433

    client = TestClient(app)
    r = client.post(
        "/v1/self/will",
        json={
            "id": "evo:def456",
            "title": "Micro-évolution toast",
            "summary": "via API",
            "kind": "evolution",
            "source": "spontaneity",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    wills2 = (data.get("state") or {}).get("pending_will") or []
    assert any(w.get("id") == "evo:def456" for w in wills2 if isinstance(w, dict))


def test_complete_and_dismiss_pending_will() -> None:
    svc_self.upsert_pending_will(
        will_id="evo:keep1",
        title="Garder",
        kind="evolution",
    )
    svc_self.upsert_pending_will(
        will_id="evo:drop1",
        title="À consommer",
        kind="evolution",
    )
    st = svc_self.complete_pending_will("evo:drop1", reason="done")
    assert st is not None
    ids = {str(w.get("id")) for w in (st.get("pending_will") or []) if isinstance(w, dict)}
    assert "evo:drop1" not in ids
    assert "evo:keep1" in ids

    from main import app  # noqa: WPS433

    client = TestClient(app)
    r = client.post("/v1/self/will/dismiss", json={"will_id": "evo:keep1"})
    assert r.status_code == 200
    wills = (r.json().get("state") or {}).get("pending_will") or []
    assert not any(w.get("id") == "evo:keep1" for w in wills if isinstance(w, dict))


def test_smoke_will_blocked_and_purge(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LBG_SELF_WILL_ALLOW_SMOKE", raising=False)
    with pytest.raises(ValueError, match="smoke"):
        svc_self.upsert_pending_will(
            will_id="evo:smoke1",
            title="Smoke évolution spontanée",
            kind="evolution",
        )
    # Injecte hors upsert (simule état legacy) puis purge
    with svc_self._lock:  # noqa: SLF001
        st = svc_self.load_state()
        st["pending_will"] = [
            {"id": "evo:smoke2", "title": "Via Pilot proxy", "kind": "evolution", "ts": 1.0},
            {"id": "evo:real", "title": "Vraie idée", "kind": "evolution", "ts": 2.0},
            {"id": "morning_brief:2026-09-29", "title": "Brief du matin", "kind": "morning_brief", "ts": 3.0},
        ]
        svc_self.persist_state(st)
    cleaned = svc_self.purge_blocked_pending_wills(day_key="2026-09-30")
    assert cleaned is not None
    ids = {str(w.get("id")) for w in (cleaned.get("pending_will") or []) if isinstance(w, dict)}
    assert "evo:smoke2" not in ids
    assert "morning_brief:2026-09-29" not in ids
    assert "evo:real" in ids
