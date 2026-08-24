"""Tests voix conversationnelle LBG-IA."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "agents" / "src"))

from lbg_agents.lbg_ia_voice import (  # noqa: E402
    FIRST_CONTACT_REPLY,
    apply_voice_to_agent_output,
    is_first_turn,
    try_greeting_response,
    unknown_capability_reply,
    wrap_operational_reply,
)


def test_first_turn_greeting() -> None:
    out = try_greeting_response(actor_id="u:1", text="Bonjour", context={})
    assert out is not None
    assert out["reply"] == FIRST_CONTACT_REPLY
    assert out["voice"]["first_contact"] is True


def test_not_greeting_when_history() -> None:
    out = try_greeting_response(
        actor_id="u:1",
        text="Bonjour",
        context={"history": [{"role": "user", "content": "hi"}]},
    )
    assert out is None


def test_wrap_team_status_first_turn() -> None:
    body = "Campus OK — 2 tâches running."
    wrapped = wrap_operational_reply(
        body,
        intent="team_status",
        routed_to="agent.team_status",
        text="compte rendu team",
        context={},
    )
    assert "Parfait, allons-y" in wrapped
    assert "Campus OK" in wrapped
    assert "Équipe virtuelle" in wrapped


def test_unknown_fallback_helpful() -> None:
    reply = unknown_capability_reply("fais quelque chose de vague")
    assert "Équipe" in reply
    assert "Godot" in reply
    assert "vague" in reply


def test_apply_voice_to_fallback_output() -> None:
    out = apply_voice_to_agent_output(
        {"agent": "minimal_stub", "handler": "fallback"},
        intent="unknown",
        routed_to="agent.fallback",
        text="xyz obscure",
        context={"history": [{"role": "user", "content": "a"}]},
    )
    assert isinstance(out.get("reply"), str)
    assert "compétence" in out["reply"].lower() or "Compétence" in out["reply"]
    assert out["remote"]["reply"] == out["reply"]


def test_skip_voice_flag() -> None:
    assert is_first_turn({"_skip_lbg_ia_voice": True}) is False
    out = try_greeting_response(actor_id="u:1", text="Bonjour", context={"_skip_lbg_ia_voice": True})
    assert out is None
