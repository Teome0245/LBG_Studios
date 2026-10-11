"""Tests packaging atomique server_overlay (ticket plan 5.1).

Vérifient : build (manifest + checksum de version), verify (checksum),
apply (rename atomique + marqueur) et rollback (restauration N-1).
Lancement : ``python -m pytest packages/cortex/infra/tests``.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
OVERLAY = ROOT / "packages" / "cortex" / "compagnon_ui" / "server_overlay"
TOOL = ROOT / "packages" / "cortex" / "infra" / "scripts" / "server_overlay_package.py"


def _load_tool():
    spec = importlib.util.spec_from_file_location("server_overlay_package", TOOL)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["server_overlay_package"] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def tool():
    return _load_tool()


def _build(tool, tmp_path: Path):
    return tool.build(OVERLAY, OVERLAY / "overlay.map", tmp_path / "dist")


def test_build_manifest_and_version(tool, tmp_path: Path) -> None:
    out = _build(tool, tmp_path)
    tarball = Path(out["tarball"])
    assert tarball.is_file()
    assert out["files"] >= 30
    assert len(out["package_sha"]) == 64
    assert Path(out["sha256_file"]).is_file()
    # Checksum de version stable pour des sources identiques.
    out2 = tool.build(OVERLAY, OVERLAY / "overlay.map", tmp_path / "dist2")
    assert out["package_sha"] == out2["package_sha"]


def test_map_destinations_unique(tool) -> None:
    entries = tool.read_map(OVERLAY / "overlay.map")
    dests = [d for _s, d in entries]
    assert len(dests) == len(set(dests))


def test_verify_rejects_bad_checksum(tool, tmp_path: Path) -> None:
    out = _build(tool, tmp_path)
    with pytest.raises(SystemExit):
        tool.verify(Path(out["tarball"]), "0" * 64)
    ok = tool.verify(Path(out["tarball"]), out["tarball_sha256"])
    assert ok["ok"] is True
    assert ok["package_sha"] == out["package_sha"]


def test_apply_writes_marker_and_files(tool, tmp_path: Path) -> None:
    out = _build(tool, tmp_path)
    root = tmp_path / "opt"
    dirty = root / "backend/src/services/router_prompts.py"
    dirty.parent.mkdir(parents=True)
    dirty.write_text("# ancienne version\n", encoding="utf-8")

    res = tool.apply(
        Path(out["tarball"]),
        root,
        root / ".backup",
        expected_sha=out["tarball_sha256"],
    )
    assert res["ok"] is True
    assert res["files_applied"] == out["files"]
    assert dirty.read_text(encoding="utf-8") != "# ancienne version\n"

    marker = json.loads((root / tool.DEFAULT_MARKER_NAME).read_text(encoding="utf-8"))
    assert marker["package_sha"] == out["package_sha"]
    assert marker["version"] == out["version"]
    assert Path(res["backup_tarball"]).is_file()


def test_rollback_restores_previous_state(tool, tmp_path: Path) -> None:
    out = _build(tool, tmp_path)
    root = tmp_path / "opt"
    dirty = root / "backend/src/services/router_prompts.py"
    dirty.parent.mkdir(parents=True)
    earlier = "# VERSION-0\n"
    dirty.write_text(earlier, encoding="utf-8")

    res = tool.apply(Path(out["tarball"]), root, root / ".backup")
    created = root / "backend/src/services/plan_suivi.py"
    assert created.is_file()  # n'existait pas avant

    rb = tool.rollback(root, Path(res["backup_tarball"]))
    assert rb["ok"] is True
    assert dirty.read_text(encoding="utf-8") == earlier
    assert not created.is_file()
    assert not (root / tool.DEFAULT_MARKER_NAME).is_file()


def test_status_reads_marker(tool, tmp_path: Path) -> None:
    out = _build(tool, tmp_path)
    root = tmp_path / "opt"
    assert tool.status(root)["ok"] is False
    tool.apply(Path(out["tarball"]), root, root / ".backup")
    st = tool.status(root)
    assert st["ok"] is True
    assert st["package_sha"] == out["package_sha"]
