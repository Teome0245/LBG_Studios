"""Tests sonde Cast / Nest Mini."""

from __future__ import annotations

from unittest.mock import patch

from lbg_agents.cast_speaker_client import announce_cast_text, probe_cast_speaker, probe_cast_speakers


def test_probe_cast_speaker_ok() -> None:
    fake = {
        "name": "Séjour",
        "ip_address": "192.168.0.75",
        "mac_address": "D4:F5:47:16:23:64",
        "locale": "fr",
        "connected": True,
        "build_version": "834495410",
    }

    class _Resp:
        status_code = 200

        def json(self):
            return fake

    class _Client:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get(self, url):
            return _Resp()

    with patch("lbg_agents.cast_speaker_client.httpx.Client", _Client):
        out = probe_cast_speaker("192.168.0.75")
    assert out["ok"] is True
    assert out["name"] == "Séjour"
    assert out["role"] == "cast"
    assert out["mac_address"] == "D4:F5:47:16:23:64"


def test_announce_dry_run() -> None:
    out = announce_cast_text("Bonjour LBG", host="192.168.0.75", dry_run=True)
    assert out["ok"] is True
    assert out["dry_run"] is True
    assert "translate_tts" in out["audio_url"]


def test_probe_cast_speakers_disabled(monkeypatch) -> None:
    monkeypatch.setenv("LBG_CAST_PROBE_ENABLED", "0")
    out = probe_cast_speakers(["192.168.0.75"])
    assert out.get("skipped") is True
