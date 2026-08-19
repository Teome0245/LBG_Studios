"""Tests cycle de vie ComfyUI (ensure/restart, sans spawn réel)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from comfyui_lifecycle import run_comfyui_lifecycle


def _cfg(values: dict[str, str]):
    def get(key: str) -> str:
        return values.get(key, "")

    return get


def test_status_reports_down(monkeypatch) -> None:
    monkeypatch.setattr("comfyui_lifecycle.probe_comfyui", lambda *a, **k: {"ok": False, "error": "down"})
    out = run_comfyui_lifecycle(
        kind="comfyui_status",
        get_cfg=_cfg({}),
        base_url="http://127.0.0.1:8188",
        dry_run=False,
    )
    assert out["ok"] is True
    assert out["outcome"] == "down"
    assert out["running"] is False


def test_ensure_dry_run_would_start(monkeypatch) -> None:
    monkeypatch.setattr("comfyui_lifecycle.probe_comfyui", lambda *a, **k: {"ok": False})
    out = run_comfyui_lifecycle(
        kind="comfyui_ensure",
        get_cfg=_cfg({"LBG_COMFYUI_ROOT": r"C:\Users\sdesh\ComfyUI"}),
        base_url="http://127.0.0.1:8188",
        dry_run=True,
    )
    assert out["ok"] is True
    assert out["outcome"] == "dry_run"
    assert out["would"] == "start"


def test_ensure_already_running(monkeypatch) -> None:
    monkeypatch.setattr("comfyui_lifecycle.probe_comfyui", lambda *a, **k: {"ok": True})
    out = run_comfyui_lifecycle(
        kind="comfyui_ensure",
        get_cfg=_cfg({}),
        base_url="http://127.0.0.1:8188",
        dry_run=False,
    )
    assert out["ok"] is True
    assert out["outcome"] == "already_running"


def test_restart_dry_run(monkeypatch) -> None:
    monkeypatch.setattr("comfyui_lifecycle.probe_comfyui", lambda *a, **k: {"ok": True})
    out = run_comfyui_lifecycle(
        kind="comfyui_restart",
        get_cfg=_cfg({}),
        base_url="http://127.0.0.1:8188",
        dry_run=True,
    )
    assert out["would"] == "restart"
