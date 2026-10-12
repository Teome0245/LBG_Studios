"""Tests mémoire agent — format + offline (sans orch réseau)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "agents" / "src"))

from lbg_agents.memory_recall import (  # noqa: E402
    build_memory_recall_payload,
    extract_evolution_seed,
    format_memory_recall_reply,
    load_recent_lessons,
    run_memory_recall,
    score_lesson_for_evolution,
)
from lbg_agents.status_intent import classify_status_intent  # noqa: E402


def test_format_reply_synthetic() -> None:
    signals = {
        "self_reachable": True,
        "self_enabled": True,
        "identity": {
            "display_name": "Cortex",
            "mode": "studio",
            "studio": "lyra",
            "mmo": "lia",
        },
        "drives": {"curiosity": 0.8, "tension": 0.1, "confidence": 0.7},
        "intent": {"primary": "monitor"},
        "pending_will_count": 2,
        "goals_active_count": 1,
        "memory_refs": {"lessons_count": 3, "last_lesson_id": "lesson_x"},
        "lessons_total": 3,
        "lessons_path": "/tmp/lessons.json",
        "recent_lessons": [
            {
                "id": "lesson_x",
                "agent_role": "qa",
                "pattern": "Toujours relancer le smoke après patch Jobs L2",
            }
        ],
    }
    reply = format_memory_recall_reply(signals)
    assert "Mémoire agent" in reply
    assert "lia" in reply
    assert "lesson_x" in reply
    assert "pas la RAM" in reply.lower() or "≠" in reply or "RAM" in reply
    assert "STUDIO" in reply
    assert "Jobs L2" in reply or "évolution" in reply.lower()


def test_score_and_extract_seed_prefers_jobs_l2() -> None:
    lessons = [
        {"id": "a", "agent_role": "pm", "pattern": "Relire le lore MMO"},
        {"id": "b", "agent_role": "ops", "pattern": "Surveiller waiting_approval Jobs L2 chaque matin"},
        {"id": "c", "agent_role": "qa", "pattern": "IMAP dry-run trompeur"},
    ]
    score_b, theme_b = score_lesson_for_evolution(lessons[1])
    score_a, _ = score_lesson_for_evolution(lessons[0])
    assert theme_b == "jobs_l2"
    assert score_b > score_a
    seed = extract_evolution_seed({"recent_lessons": lessons, "lessons_total": 3})
    assert seed is not None
    assert seed["theme"] == "jobs_l2"
    assert seed["auto_promote"] is False
    assert "Jobs L2" in seed["text"] or "waiting" in seed["text"].lower() or "L2" in seed["text"]


def test_build_payload_includes_studio_offer(monkeypatch, tmp_path: Path) -> None:
    path = tmp_path / "lessons_learned.json"
    path.write_text(
        json.dumps(
            {
                "lessons": [
                    {
                        "id": "lan1",
                        "agent_role": "ops",
                        "pattern": "Diff inventaire LAN apparus/disparus à notifier",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("LBG_TEAM_LESSONS_PATH", str(path))
    monkeypatch.setenv("LBG_ORCHESTRATOR_URL", "http://127.0.0.1:9")
    payload = build_memory_recall_payload(context={})
    assert payload["auto_promote"] is False
    assert payload["evolution_seed"] is not None
    assert payload["studio_offer"]["offer"] is True
    assert len(payload["studio_offer"]["intents"]) == 3
    labels = {i["label"] for i in payload["studio_offer"]["intents"]}
    assert labels == {"Team L1", "En parler", "Ignorer"}


def test_load_recent_lessons_from_tmp(tmp_path, monkeypatch) -> None:
    path = tmp_path / "lessons_learned.json"
    path.write_text(
        json.dumps(
            {
                "lessons": [
                    {"id": "a", "agent_role": "pm", "pattern": "old"},
                    {"id": "b", "agent_role": "qa", "pattern": "new"},
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("LBG_TEAM_LESSONS_PATH", str(path))
    recent, total, used = load_recent_lessons(limit=1)
    assert total == 2
    assert used == str(path)
    assert len(recent) == 1
    assert recent[0]["id"] == "b"


def test_run_memory_recall_offline(monkeypatch) -> None:
    monkeypatch.setenv("LBG_ORCHESTRATOR_URL", "http://127.0.0.1:9")
    monkeypatch.setenv("LBG_BACKEND_URL", "http://127.0.0.1:9")
    out = run_memory_recall(
        actor_id="u:test",
        text="montre ce que tu retiens (mémoire agent)",
        context={},
    )
    assert out["ok"] is True
    assert out["agent"] == "memory_recall"
    assert "mémoire" in out["reply"].lower()
    assert out["status"]["kind"] == "memory_recall"


def test_status_intent_memory_vs_vm() -> None:
    intent, conf = classify_status_intent("montre ta mémoire agent")
    assert intent == "memory_recall"
    assert conf >= 0.9
    intent2, _ = classify_status_intent("sonde la mémoire RAM des VM 246")
    assert intent2 != "memory_recall"
