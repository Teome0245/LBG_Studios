"""Tests résolution prime-client root + track ui_portraits."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from team import prime_client_paths as pcp
from team.ui_portraits_workflow import execute_ui_portraits_workflow, probe_ui_portraits


def test_resolve_prefers_studios_over_env_new_mmo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    studios = tmp_path / "LBG_Studios" / "packages" / "prime-client"
    studios.mkdir(parents=True)
    (studios / "project.godot").write_text("; mock\n", encoding="utf-8")
    legacy = tmp_path / "new_mmo" / "prime-client"
    legacy.mkdir(parents=True)
    (legacy / "project.godot").write_text("; legacy\n", encoding="utf-8")

    monkeypatch.setenv("LBG_PRIME_CLIENT_ROOT", str(legacy))
    monkeypatch.delenv("LBG_PRIME_ALLOW_LEGACY_NEW_MMO", raising=False)
    monkeypatch.setattr(pcp, "studios_prime_candidates", lambda: [studios])

    got = pcp.resolve_prime_client_root()
    assert got == studios
    assert not pcp.is_legacy_new_mmo_path(got)


def test_resolve_honors_allow_legacy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    studios = tmp_path / "studios" / "prime-client"
    studios.mkdir(parents=True)
    (studios / "project.godot").write_text("; s\n", encoding="utf-8")
    legacy = tmp_path / "new_mmo" / "prime-client"
    legacy.mkdir(parents=True)

    monkeypatch.setenv("LBG_PRIME_CLIENT_ROOT", str(legacy))
    monkeypatch.setenv("LBG_PRIME_ALLOW_LEGACY_NEW_MMO", "1")
    monkeypatch.setattr(pcp, "studios_prime_candidates", lambda: [studios])

    assert pcp.resolve_prime_client_root() == legacy


def test_context_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "custom-prime"
    target.mkdir()
    monkeypatch.delenv("LBG_PRIME_CLIENT_ROOT", raising=False)
    monkeypatch.setattr(pcp, "find_studios_prime_client", lambda: None)
    assert pcp.resolve_prime_client_root({"prime_client_root": str(target)}) == target


def test_ui_portraits_remediation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "prime-client"
    guide = root / "assets" / "ui" / "portraits" / "npc_guide"
    guide.mkdir(parents=True)
    (guide / "neutral.png").write_bytes(b"png")
    (guide / "happy.png").write_bytes(b"png")
    (guide / "determined.png").write_bytes(b"png")
    cfg = root / "config"
    cfg.mkdir(parents=True)
    (cfg / "dialogue_portraits.json").write_text(
        json.dumps(
            {
                "portraits": {
                    "npc_merchant_neutral": "res://assets/sprites/units/npc_merchant.svg",
                    "npc_default_neutral": "res://assets/sprites/units/npc_civilian.svg",
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("team.ui_portraits_workflow.resolve_prime_client_root", lambda ctx=None, **kw: root)

    before = probe_ui_portraits({})
    assert before["ok"] is False

    out = execute_ui_portraits_workflow({"write_files": True})
    assert out["ok"] is True
    assert (root / "assets/ui/portraits/npc_merchant/neutral.png").is_file()
    data = json.loads((cfg / "dialogue_portraits.json").read_text(encoding="utf-8"))
    assert data["portraits"]["npc_merchant_neutral"].endswith(".png")
