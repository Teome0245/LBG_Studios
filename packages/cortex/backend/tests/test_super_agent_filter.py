"""Tests unitaires pour SuperAgentRouter & FilteredSessionEvent."""

from services.super_agent_filter import (
    EventPriority,
    SuperAgentRouter,
    WorkerDomain,
)


def test_super_agent_router_initialization():
    router = SuperAgentRouter()
    status = router.get_team_status()
    assert "code" in status
    assert "game" in status
    assert "studio" in status
    assert "ops" in status
    assert status["code"]["last_event"] == "idle"


def test_event_filtering_and_sanitization():
    router = SuperAgentRouter()
    raw_event = {
        "v": 1,
        "event": "session.tool_pre",
        "agent": "cline_coder",
        "session_id": "sess_123",
        "summary": "Compiling with token secret_token_123456789abcdef in command",
        "detail": {"arg": "bearer 987654321fedcba"},
    }

    filtered = router.filter_and_route_event(raw_event)
    assert filtered is not None
    assert filtered.domain == WorkerDomain.CODE
    assert filtered.priority == EventPriority.NORMAL
    assert "[REDACTED_SECRET]" in filtered.summary
    assert "secret_token_123456789abcdef" not in filtered.summary
    assert "[REDACTED_SECRET]" in filtered.clean_detail["arg"]


def test_approval_requirement_and_critical_priority():
    router = SuperAgentRouter()
    raw_event = {
        "v": 1,
        "event": "session.approval_needed",
        "agent": "opencode",
        "approval_id": "appr_789",
        "summary": "Supprimer le répertoire cache ?",
    }

    filtered = router.filter_and_route_event(raw_event)
    assert filtered is not None
    assert filtered.requires_human_approval is True
    assert filtered.approval_id == "appr_789"
    assert filtered.priority == EventPriority.CRITICAL


def test_domain_isolation_no_leak():
    router = SuperAgentRouter()
    # Événement pour le code
    router.filter_and_route_event({
        "event": "code.build",
        "agent": "cline",
        "summary": "Build successful",
    })
    # Événement pour le jeu
    router.filter_and_route_event({
        "event": "mmo.tick",
        "agent": "godot_hub",
        "summary": "Simulating tick 42",
    })

    code_ctx = router.get_worker_context(WorkerDomain.CODE)
    game_ctx = router.get_worker_context(WorkerDomain.GAME)
    studio_ctx = router.get_worker_context(WorkerDomain.STUDIO)

    assert len(code_ctx) == 1
    assert code_ctx[0]["summary"] == "Build successful"

    assert len(game_ctx) == 1
    assert game_ctx[0]["summary"] == "Simulating tick 42"

    # Aucune fuite dans le contexte Studio
    assert len(studio_ctx) == 0


def test_invalid_event_rejection():
    router = SuperAgentRouter()
    assert router.filter_and_route_event({}) is None
    assert router.filter_and_route_event(None) is None  # type: ignore
    assert router.filter_and_route_event({"event": ""}) is None
