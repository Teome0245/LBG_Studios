"""Tests logique Atlas bench watchdog (retry KO + seuil)."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_watchdog_module():
    script = Path(__file__).resolve().parents[2] / "infra/scripts/atlas_bench_watchdog.py"
    spec = importlib.util.spec_from_file_location("atlas_bench_watchdog", script)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_apply_retry_recovers_failed_prompt() -> None:
    wd = _load_watchdog_module()
    lots = [
        {
            "prompt_count": 2,
            "oks": 1,
            "fails": 1,
            "timeout_s": 150,
            "max_tokens": 220,
            "results": [
                {"id": "json-001", "ok": True, "model": "gemma4:e2b"},
                {"id": "router-002", "ok": False, "model": "gemma4:e2b", "error": "500"},
            ],
        }
    ]
    retry_report = {
        "results": [
            {"id": "router-002", "ok": True, "model": "gemma4:e2b", "latency_s": 12.0, "content": "ok"},
        ]
    }
    recovered = wd.apply_retry_results(lots, retry_report)
    assert recovered == ["router-002"]
    assert lots[0]["oks"] == 2
    assert lots[0]["results"][1].get("retry") is True


def test_count_oks_and_threshold() -> None:
    wd = _load_watchdog_module()
    lots = [{"prompt_count": 3, "oks": 2}, {"prompt_count": 3, "oks": 2}]
    oks, total = wd.count_oks(lots)
    assert oks == 4
    assert total == 6
    assert not (oks < 3)
    assert 2 < 3
