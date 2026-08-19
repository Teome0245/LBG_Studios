"""Tests action desktop import_face_parts (dry-run / opt-in)."""

from __future__ import annotations

from lbg_agents.desktop_executor import run_desktop_action


def test_import_face_parts_disabled_by_default(monkeypatch) -> None:
    monkeypatch.delenv("LBG_DESKTOP_FACE_PARTS_ENABLED", raising=False)
    monkeypatch.setenv("LBG_DESKTOP_DRY_RUN", "1")
    out = run_desktop_action(
        actor_id="test",
        text="import",
        action={"kind": "import_face_parts", "character_id": "lyra_assistant"},
        context={"desktop_dry_run": True},
    )
    assert out.get("ok") is False
    assert out.get("outcome") == "feature_disabled"
