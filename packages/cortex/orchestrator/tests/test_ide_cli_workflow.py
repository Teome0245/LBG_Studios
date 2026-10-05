"""Tests ADR 0025 — ide_cli / run_cli_agent (dry-run)."""

from __future__ import annotations

import os

import pytest

os.environ["LBG_TEAM_DB_PATH"] = ":memory:"
os.environ["LBG_TEAM_IDE_CLI_ENABLED"] = "1"

from team.ide_cli_workflow import (  # noqa: E402
    execute_ide_cli_workflow,
    resolve_ide_cli_workflow,
)
from team.models import TeamTask  # noqa: E402


def test_resolve_ide_cli_from_context() -> None:
    task = TeamTask(
        id="t1",
        role="dev_godot",
        objective="patch UI",
        actor_id="u",
        context={"ide_cli": True, "godot_dev_persona": "iris"},
    )
    assert resolve_ide_cli_workflow(task) is True


def test_resolve_ide_cli_from_objective() -> None:
    task = TeamTask(
        id="t2",
        role="dev_game",
        objective="lance claude sur omarchy pour fixer le smoke",
        actor_id="u",
        context={},
    )
    assert resolve_ide_cli_workflow(task) is True


def test_execute_ide_cli_iris_dry_run(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    def fake_dispatch(routed_to: str, **kwargs):
        captured["routed_to"] = routed_to
        captured["context"] = kwargs.get("context") or {}
        return {
            "ok": True,
            "outcome": "dry_run",
            "kind": "run_cli_agent",
            "app": "claude",
            "reply": "dry-run ok",
        }

    task = TeamTask(
        id="t-iris",
        role="dev_godot",
        objective="Iris — patch dialogue suggestions C1",
        actor_id="u:test",
        context={
            "ide_cli": True,
            "godot_dev_persona": "iris",
            "desktop_dry_run": True,
        },
    )
    out = execute_ide_cli_workflow(task, fake_dispatch)
    assert out["kind"] == "ide_cli_workflow"
    assert out["ok"] is True
    assert out["dry_run"] is True
    assert out["persona"] == "Iris"
    assert out["app"] == "claude"
    assert captured["routed_to"] == "agent.desktop"
    act = (captured["context"].get("desktop_action") or {})
    assert act.get("kind") == "run_cli_agent"
    assert captured["context"].get("desktop_target") == "omarchy"


def test_execute_ide_cli_pygmalion(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_dispatch(routed_to: str, **kwargs):
        return {"ok": True, "outcome": "dry_run", "kind": "run_cli_agent", "reply": "ok"}

    task = TeamTask(
        id="t-pyg",
        role="dev_game",
        objective="Pygmalion — fixer script habillage",
        actor_id="u",
        context={"ide_cli": True, "infographiste_ia": True, "subproject": "infographiste_ia"},
    )
    out = execute_ide_cli_workflow(task, fake_dispatch)
    assert out["persona"] == "Pygmalion"
    assert out["ok"] is True


def test_run_cli_agent_core_dry_run(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib.util
    from pathlib import Path

    # packages/cortex/linux_agent/Agent_IA/core.py
    path = Path(__file__).resolve().parents[2] / "linux_agent" / "Agent_IA" / "core.py"
    assert path.is_file(), path
    spec = importlib.util.spec_from_file_location("linux_agent_core_test", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    monkeypatch.setenv("LBG_LINUX_CLI_AGENT_ENABLED", "0")
    work = tmp_path / "projects" / "LBG_Studios"
    work.mkdir(parents=True)
    monkeypatch.setenv("LBG_LINUX_CLI_AGENT_CWD_ALLOWLIST", str(tmp_path / "projects"))
    out = mod.run_cli_agent(
        app="claude",
        prompt="ajoute un test unitaire",
        cwd=str(work),
        dry_run=True,
    )
    assert out["ok"] is True
    assert out["outcome"] == "dry_run"
    assert out["app"] == "claude"
    assert "claude" in " ".join(str(x) for x in (out.get("argv") or []))
