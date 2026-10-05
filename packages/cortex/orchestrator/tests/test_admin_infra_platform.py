"""Tests périmètre Atlas admin_infra (110/111/140/141/143/246 ; 245 optionnel). .112 décommissionné."""

from __future__ import annotations

from team.admin_infra_platform import (
    admin_infra_perimeter,
    audit_admin_infra_platform,
    audit_platform_host,
    platform_host_specs,
)


def test_perimeter_excludes_245_by_default(monkeypatch) -> None:
    monkeypatch.delenv("LBG_ATLAS_REQUIRE_PRECU", raising=False)
    assert admin_infra_perimeter() == ["110", "111", "140", "141", "143", "246"]
    ids = {s["perimeter_id"] for s in platform_host_specs()}
    assert {"110", "111", "140", "141", "143", "245", "246"}.issubset(ids)
    assert "112" not in ids


def test_perimeter_includes_245_when_required(monkeypatch) -> None:
    monkeypatch.setenv("LBG_ATLAS_REQUIRE_PRECU", "1")
    assert admin_infra_perimeter() == ["110", "111", "140", "141", "143", "245", "246"]


def test_platform_specs_dual_llm_labels(monkeypatch) -> None:
    monkeypatch.delenv("LBG_ATLAS_PROBE_FRONT_LEGACY", raising=False)
    monkeypatch.delenv("LBG_ATLAS_REQUIRE_PRECU", raising=False)
    specs = {s["id"]: s for s in platform_host_specs()}
    assert specs["llm_heavy_110"]["ollama_tier"] == "heavy"
    assert specs["llm_light_111"]["ollama_tier"] == "light"
    assert "front_legacy_112" not in specs
    assert specs["hands_143"]["required"] is True
    assert specs["precu_245"]["required"] is False
    assert any(p.get("url", "").endswith(":5005/healthz") for p in specs["hands_143"]["probes"])
    assert any(p["url"].endswith(":11434/api/tags") for p in specs["llm_light_111"]["probes"])


def test_precu_required_opt_in(monkeypatch) -> None:
    monkeypatch.setenv("LBG_ATLAS_REQUIRE_PRECU", "1")
    specs = {s["id"]: s for s in platform_host_specs()}
    assert specs["precu_245"]["required"] is True


def test_front_legacy_112_opt_in_only(monkeypatch) -> None:
    monkeypatch.setenv("LBG_ATLAS_PROBE_FRONT_LEGACY", "1")
    specs = {s["id"]: s for s in platform_host_specs()}
    assert specs["front_legacy_112"]["required"] is False
    assert specs["front_legacy_112"]["host"] == "192.168.0.112"


def test_audit_platform_host_marks_ko_on_probe_failure(monkeypatch) -> None:
    def fake_probe(url: str, *, timeout: float = 4.0) -> dict:
        return {"url": url, "ok": False, "error": "down"}

    monkeypatch.setattr("team.admin_infra_platform._probe_http", fake_probe)
    spec = {
        "id": "precu_245",
        "label": "PreCU",
        "host": "192.168.0.245",
        "perimeter_id": "245",
        "role": "precu_runtime",
        "required": False,
        "probes": [{"kind": "http", "url": "http://192.168.0.245:8050/healthz"}],
    }
    out = audit_platform_host(spec)
    assert out["ok"] is False
    assert out["required"] is False
    assert out["perimeter_id"] == "245"


def test_audit_platform_host_tcp_probe(monkeypatch) -> None:
    monkeypatch.setattr(
        "team.admin_infra_platform._probe_tcp",
        lambda host, port, **kw: {"host": host, "port": port, "ok": port == 22, "kind": "tcp"},
    )
    spec = {
        "id": "executor_141",
        "label": "LAN executor",
        "host": "192.168.0.141",
        "perimeter_id": "141",
        "role": "lan_executor",
        "required": True,
        "probes": [{"kind": "tcp", "port": 22}],
    }
    out = audit_platform_host(spec)
    assert out["ok"] is True
    assert out["perimeter_id"] == "141"


def test_audit_admin_infra_platform_structure(monkeypatch) -> None:
    monkeypatch.setenv("LBG_ATLAS_PROBE_FRONT_LEGACY", "0")
    monkeypatch.delenv("LBG_ATLAS_REQUIRE_PRECU", raising=False)
    monkeypatch.setattr(
        "team.admin_infra_platform.audit_ollama_lan",
        lambda **kw: {
            "ok": True,
            "track": "ollama_audit_dual_110_111",
            "recommendations": [],
            "gaps": [],
        },
    )
    monkeypatch.setattr(
        "team.admin_infra_platform.audit_dialogue_fast_cloud",
        lambda **kw: {
            "ok": True,
            "skipped": False,
            "track": "dialogue_fast_groq",
            "gaps": [],
            "warnings": [],
            "recommendations": [],
        },
    )
    monkeypatch.setattr(
        "team.admin_infra_platform.audit_platform_host",
        lambda spec: {
            "id": spec["id"],
            "perimeter_id": spec["perimeter_id"],
            "required": spec.get("required", True),
            "ok": spec["perimeter_id"] in ("110", "111", "140", "141", "143", "246"),
            "probes": [],
        },
    )
    out = audit_admin_infra_platform()
    assert out["track"] == "admin_infra_platform"
    assert out["hosts_total"] == 6
    assert out["hosts_ok"] == 6
    assert out["ok"] is True
    assert "111" in out["perimeter"]
    assert "141" in out["perimeter"]
    assert "143" in out["perimeter"]
    assert "245" not in out["perimeter"]
    assert not any("245" in g for g in out.get("gaps") or [])
    assert not any("245 PreCU" in r for r in out.get("recommendations") or [])
    assert out["topology"]["llm_light"].startswith("192.168.0.111")
