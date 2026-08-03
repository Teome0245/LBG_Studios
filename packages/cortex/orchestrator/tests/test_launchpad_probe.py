"""Tests sonde Launchpad (Hermès owner)."""

from __future__ import annotations

from pathlib import Path

from team.launchpad_probe import probe_launchpad


def test_probe_launchpad_finds_monorepo_package() -> None:
    out = probe_launchpad()
    # Dans le monorepo Studios, le package doit être trouvé
    studios = Path(__file__).resolve().parents[4]
    if (studios / "packages" / "launchpad").is_dir():
        assert out["ok"] is True
        assert out["package_path"]
        assert out["track"] == "hermes_launchpad"
    else:
        assert "gaps" in out
