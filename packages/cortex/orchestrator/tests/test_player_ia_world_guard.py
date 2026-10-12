"""Chœur V50–V53 — world_truth_guard offline."""

from __future__ import annotations

from team.player_ia_world_guard import run_world_truth_guard


def test_world_truth_guard_ok_on_monorepo():
    g = run_world_truth_guard()
    assert g.get("kind") == "world_truth_guard"
    assert g.get("enabled") is True
    assert g.get("ok") is True, g
    kinds = {c.get("kind") for c in (g.get("checks") or [])}
    assert "bible_v50_choeur" in kinds
    assert "bible_v53_persona" in kinds
    assert "catalog_schema" in kinds
    assert "inventaire_jax" in kinds
    assert "inventaire_daan" in kinds
    bad = [c for c in (g.get("checks") or []) if not c.get("ok")]
    assert not bad, bad
