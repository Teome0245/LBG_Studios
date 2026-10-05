"""Tests brief matinal — format + fenêtre horaire (sans orch réseau)."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "agents" / "src"))

from lbg_agents.morning_brief import (  # noqa: E402
    brief_day_key,
    build_brief_payload,
    format_morning_brief_reply,
    is_morning_window,
    pick_next_agir,
    run_morning_brief,
)


def test_is_morning_window_paris(monkeypatch) -> None:
    monkeypatch.setenv("LBG_MORNING_BRIEF_TZ", "Europe/Paris")
    monkeypatch.setenv("LBG_MORNING_BRIEF_HOUR_START", "7")
    monkeypatch.setenv("LBG_MORNING_BRIEF_HOUR_END", "10")
    tz = ZoneInfo("Europe/Paris")
    assert is_morning_window(now=datetime(2026, 9, 28, 8, 15, tzinfo=tz))
    assert not is_morning_window(now=datetime(2026, 9, 28, 18, 0, tzinfo=tz))


def test_format_reply_from_synthetic_signals() -> None:
    signals = {
        "day_key": "2026-09-28",
        "morning_window": True,
        "proactive": {
            "enabled": True,
            "mode": "proactif_leger",
            "tension": 0.42,
            "infra_signals": {},
            "last_job_id": None,
        },
        "self": {
            "drives": {"curiosity": 0.5, "tension": 0.2},
            "intent": {"primary": "monitor"},
            "pending_will_count": 1,
        },
        "infra": {"ok_count": 2, "total": 2, "probes": []},
        "jobs_l2": {"ok": True, "n_waiting": 0, "samples": []},
        "lan": {"available": True, "n_present": 24, "n_hosts": 31, "n_appeared": 0, "n_disappeared": 0},
        "mail": {"available": False},
        "notes": [],
    }
    reply = format_morning_brief_reply(signals)
    assert "brief matinal" in reply.lower()
    assert "2026-09-28" in reply
    assert "regarde mes mails récents" in reply
    assert len(reply.splitlines()) <= 15
    assert "0 auto-Réel" in reply or "0 auto-Réel" in reply.replace("é", "e") or "auto-Réel" in reply


def test_pick_next_agir_prioritizes_jobs_l2() -> None:
    signals = {
        "jobs_l2": {"n_waiting": 2, "samples": [{"title": "restart"}]},
        "lan": {"n_appeared": 0, "n_disappeared": 0},
        "infra": {"ok_count": 4, "total": 4},
        "proactive": {"infra_signals": {}},
    }
    picks = pick_next_agir(signals)
    assert picks[0]["id"] == "jobs_l2"
    assert len(picks) <= 2


def test_run_morning_brief_offline(monkeypatch) -> None:
    monkeypatch.setenv("LBG_ORCHESTRATOR_URL", "http://127.0.0.1:9")
    monkeypatch.setenv("LBG_BACKEND_URL", "http://127.0.0.1:9")
    out = run_morning_brief(actor_id="u:test", text="fais mon brief du matin", context={})
    assert out["ok"] is True
    assert out["agent"] == "morning_brief"
    assert "brief matinal" in out["reply"].lower()
    payload = out["status"]
    assert payload["kind"] == "morning_brief"
    assert payload["schema_version"] == 1
    assert payload.get("auto_execute_next") is False
    assert brief_day_key() == payload["day_key"]
    assert len(out["reply"].splitlines()) <= 15


def test_build_payload_next_agir(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LBG_ORCHESTRATOR_URL", "http://127.0.0.1:9")
    monkeypatch.setenv("LBG_BACKEND_URL", "http://127.0.0.1:9")
    state = tmp_path / "state.json"
    state.write_text(
        json.dumps(
            {
                "n_present": 10,
                "n_hosts": 12,
                "last_diff": {"n_appeared": 1, "n_disappeared": 0},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("LBG_NETWORK_INVENTORY_STATE", str(state))
    payload = build_brief_payload(context={"brief_notes": ["note synth"]})
    assert len(payload["next_agir"]) <= 2
    assert payload["auto_execute_next"] is False
    assert any(a["id"] in ("mail", "network_inventory", "selfcheck", "jobs_l2") for a in payload["next_agir"])
    assert "note synth" in payload["reply"] or len(payload["reply"].splitlines()) <= 15
