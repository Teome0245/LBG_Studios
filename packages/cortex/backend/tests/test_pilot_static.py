from pathlib import Path

import pytest
from backend.main import resolve_pilot_static_dir


def test_resolve_pilot_static_prefers_dist_in_auto(tmp_path: Path) -> None:
    root = tmp_path / "pilot_web"
    dist = root / "dist"
    dist.mkdir(parents=True)
    (root / "index.html").write_text("<html>src</html>", encoding="utf-8")
    (dist / "index.html").write_text("<html>dist</html>", encoding="utf-8")
    assert resolve_pilot_static_dir(root, "auto") == dist
    assert resolve_pilot_static_dir(root, "source") == root
    assert resolve_pilot_static_dir(root, "dist") == dist


def test_resolve_pilot_static_falls_back_without_dist(tmp_path: Path) -> None:
    root = tmp_path / "pilot_web"
    root.mkdir()
    (root / "index.html").write_text("<html>src</html>", encoding="utf-8")
    assert resolve_pilot_static_dir(root, "auto") == root
    assert resolve_pilot_static_dir(root, "dist") == root


def test_resolve_pilot_static_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from config import get_settings

    root = tmp_path / "pilot_web"
    dist = root / "dist"
    dist.mkdir(parents=True)
    (dist / "index.html").write_text("<html>dist</html>", encoding="utf-8")
    monkeypatch.setenv("LBG_PILOT_STATIC", "source")
    get_settings.cache_clear()
    assert resolve_pilot_static_dir(root) == root
    monkeypatch.setenv("LBG_PILOT_STATIC", "auto")
    get_settings.cache_clear()
    assert resolve_pilot_static_dir(root) == dist
