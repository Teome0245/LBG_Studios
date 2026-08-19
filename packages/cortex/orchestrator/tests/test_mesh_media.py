"""Tests connecteur mesh Pygmalion (TRELLIS.2)."""

from __future__ import annotations

from pathlib import Path

import pytest

from team.mesh_media import (
    mesh_from_comfyui_images,
    mesh_gen_backend,
    mesh_gen_enabled,
    probe_mesh_worker,
    submit_image_to_mesh,
)


def test_mesh_gen_disabled_by_default() -> None:
    assert mesh_gen_enabled() is False


def test_probe_mesh_skipped_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LBG_MESH_GEN_ENABLED", raising=False)
    out = probe_mesh_worker()
    assert out.get("skipped") is True


def test_submit_mesh_skipped_when_disabled(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    img = tmp_path / "x.png"
    img.write_bytes(b"\x89PNG\r\n")
    monkeypatch.delenv("LBG_MESH_GEN_ENABLED", raising=False)
    out = submit_image_to_mesh(img)
    assert out.get("skipped") is True


def test_mesh_from_comfyui_empty() -> None:
    out = mesh_from_comfyui_images([])
    assert out.get("skipped") is True


def test_default_backend_is_huggingface() -> None:
    assert mesh_gen_backend() == "huggingface"


def test_huggingface_submit_missing_gradio_client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Si gradio_client n'est pas installé, retour propre."""
    monkeypatch.setenv("LBG_MESH_GEN_ENABLED", "1")
    monkeypatch.setenv("LBG_MESH_GEN_BACKEND", "huggingface")
    img = tmp_path / "test.png"
    img.write_bytes(b"\x89PNG\r\n")

    import importlib
    import team.mesh_media as _mod

    _orig = _mod._submit_huggingface

    def _patched(image_path, *, output_name, resolution, target_tris):
        return {"ok": False, "error": "gradio_client manquant — pip install gradio_client", "backend": "huggingface"}

    monkeypatch.setattr(_mod, "_submit_huggingface", _patched)
    out = submit_image_to_mesh(img)
    assert out["ok"] is False
    assert "gradio_client" in out["error"]
