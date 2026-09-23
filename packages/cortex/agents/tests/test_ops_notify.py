"""Tests ops_notify — fan-out Slack / Matrix (ADR 0021)."""

from __future__ import annotations

from typing import Any

import lbg_agents.ops_notify as on


def test_resolve_backend_default_both(monkeypatch) -> None:
    monkeypatch.delenv("LBG_OPS_NOTIFY_BACKEND", raising=False)
    assert on.resolve_backend() == "both"


def test_resolve_backend_element_alias(monkeypatch) -> None:
    monkeypatch.setenv("LBG_OPS_NOTIFY_BACKEND", "element")
    assert on.resolve_backend() == "matrix"


def test_send_text_disabled(monkeypatch) -> None:
    monkeypatch.setenv("LBG_OPS_NOTIFY_DISABLE", "1")
    out = on.send_text("hello")
    assert out.get("skipped") is True
    assert out.get("ok") is True


def test_send_text_slack_only(monkeypatch) -> None:
    monkeypatch.setenv("LBG_OPS_NOTIFY_BACKEND", "slack")
    monkeypatch.setenv("LBG_SLACK_WEBHOOK_OPS", "https://hooks.slack.test/xxx")
    monkeypatch.delenv("LBG_OPS_NOTIFY_DISABLE", raising=False)

    calls: list[str] = []

    def fake_slack(msg: str) -> dict[str, Any]:
        calls.append(msg)
        return {"ok": True, "backend": "slack"}

    def fake_matrix(msg: str) -> dict[str, Any]:
        raise AssertionError("matrix ne doit pas être appelé")

    monkeypatch.setattr(on, "send_slack_text", fake_slack)
    monkeypatch.setattr(on, "send_matrix_text", fake_matrix)
    out = on.send_text("alerte KO")
    assert out["ok"] is True
    assert out["results"]["slack"]["ok"] is True
    assert "matrix" not in out["results"]
    assert calls == ["alerte KO"]


def test_send_text_both_fanout(monkeypatch) -> None:
    monkeypatch.setenv("LBG_OPS_NOTIFY_BACKEND", "both")
    monkeypatch.delenv("LBG_OPS_NOTIFY_DISABLE", raising=False)

    monkeypatch.setattr(on, "send_slack_text", lambda m: {"ok": True, "backend": "slack"})
    monkeypatch.setattr(on, "send_matrix_text", lambda m: {"ok": True, "backend": "matrix"})
    out = on.send_text("dual")
    assert out["ok"] is True
    assert out["any_ok"] is True
    assert set(out["results"]) == {"slack", "matrix"}


def test_send_text_both_ok_if_one_backend_works(monkeypatch) -> None:
    monkeypatch.setenv("LBG_OPS_NOTIFY_BACKEND", "both")
    monkeypatch.delenv("LBG_OPS_NOTIFY_DISABLE", raising=False)

    monkeypatch.setattr(
        on,
        "send_slack_text",
        lambda m: {"ok": False, "skipped": True, "backend": "slack", "error": "slack_webhook_missing"},
    )
    monkeypatch.setattr(on, "send_matrix_text", lambda m: {"ok": True, "backend": "matrix"})
    out = on.send_text("backup only")
    assert out["ok"] is True
    assert out["results"]["matrix"]["ok"] is True


def test_send_slack_missing_webhook(monkeypatch) -> None:
    monkeypatch.delenv("LBG_SLACK_WEBHOOK_OPS", raising=False)
    monkeypatch.delenv("LBG_SLACK_WEBHOOK_URL", raising=False)
    out = on.send_slack_text("x")
    assert out.get("skipped") is True
    assert out.get("ok") is False


def test_send_text_respects_max_chars_kwarg(monkeypatch) -> None:
    monkeypatch.setenv("LBG_OPS_NOTIFY_BACKEND", "slack")
    monkeypatch.delenv("LBG_OPS_NOTIFY_DISABLE", raising=False)

    calls: list[str] = []

    def fake_slack(msg: str) -> dict[str, Any]:
        calls.append(msg)
        return {"ok": True, "backend": "slack"}

    monkeypatch.setattr(on, "send_slack_text", fake_slack)
    long_msg = "x" * 200
    out = on.send_text(long_msg, max_chars=50)
    assert out["ok"] is True
    assert len(calls[0]) == 50
