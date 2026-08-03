"""Tests Iris L3 — allowlist apply après smoke."""

from __future__ import annotations

from pathlib import Path

import pytest

from team.iris_gdscript_forge import IrisForgePatch
from team.iris_l3 import (
    DEFAULT_L3_ALLOWLIST,
    filter_patches_for_l3_apply,
    iris_forge_l3_enabled,
    path_allowed_l3,
    should_auto_apply_l3,
)


def test_default_allowlist_covers_m9_paths() -> None:
    assert "scripts/minimap_hud.gd" in DEFAULT_L3_ALLOWLIST
    assert "config/waypoints.json" in DEFAULT_L3_ALLOWLIST
    assert path_allowed_l3("scripts/minimap_hud.gd")
    assert not path_allowed_l3("addons/evil/hack.gd")
    assert not path_allowed_l3("../etc/passwd")
    assert not path_allowed_l3("scripts/secret_credentials.gd")


def test_filter_rejects_outside_allowlist() -> None:
    patches = [
        IrisForgePatch(
            gap="ok",
            target_rel="scripts/minimap_hud.gd",
            patch_kind="template",
            description="x",
            track="m9b",
            staging_path="/tmp/a",
        ),
        IrisForgePatch(
            gap="bad",
            target_rel="scripts/unknown_world.gd",
            patch_kind="template",
            description="x",
            track="m9b",
            staging_path="/tmp/b",
        ),
    ]
    allowed, rejected = filter_patches_for_l3_apply(patches)
    assert len(allowed) == 1
    assert allowed[0].target_rel == "scripts/minimap_hud.gd"
    assert any(r["reason"] == "not_in_l3_allowlist" for r in rejected)


def test_should_auto_apply_l3_requires_smoke(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_IRIS_FORGE_L3", "1")
    assert iris_forge_l3_enabled()
    assert should_auto_apply_l3(smoke_ok=True) is True
    assert should_auto_apply_l3(smoke_ok=False) is False


def test_l3_off_no_apply_without_legacy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_IRIS_FORGE_L3", "0")
    assert should_auto_apply_l3(smoke_ok=True) is False
    assert should_auto_apply_l3(smoke_ok=True, explicit_auto_apply=True) is True


def test_forge_pipeline_l3_applies_allowlisted(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("LBG_IRIS_FORGE_ENABLED", "1")
    monkeypatch.setenv("LBG_IRIS_FORGE_L3", "1")
    monkeypatch.setenv("LBG_IRIS_FORGE_AUTO_APPLY", "0")
    monkeypatch.setenv("LBG_IRIS_FORGE_SMOKE_REQUIRED", "0")  # skip smoke script
    monkeypatch.setenv("LBG_IRIS_FORGE_STAGING_DIR", str(tmp_path / "staging"))
    monkeypatch.setenv("LBG_PRIME_CLIENT_ROOT", str(tmp_path / "prime"))
    monkeypatch.setenv("LBG_IRIS_FORGE_LLM", "0")
    (tmp_path / "prime").mkdir()

    from team.iris_llm_forge import forge_with_llm_and_smoke

    out = forge_with_llm_and_smoke(
        ["scripts/minimap_hud.gd absent (minimap_script)"],
        task_id="t-l3",
        track="m9b",
        persona="iris",
    )
    assert out["smoke_ok"] is True
    assert out["l3"]["enabled"] is True
    assert out["autonomy"] == "L3"
    assert out["applied_count"] >= 1
    assert (tmp_path / "prime" / "scripts" / "minimap_hud.gd").is_file()
