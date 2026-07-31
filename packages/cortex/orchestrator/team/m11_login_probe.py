"""Audit readiness jalon M11 — login LBG Godot (sans retail / SOE)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from team.m9_map_probe import _prime_client_root, _repo_root


def _check_file(path: Path, *, gaps: list[str], label: str, checks: dict[str, Any]) -> bool:
    ok = path.is_file()
    checks[label] = ok
    if not ok:
        gaps.append(f"{label} absent ({path})")
    return ok


def _check_text_contains(path: Path, needle: str, *, gaps: list[str], label: str, checks: dict[str, Any]) -> bool:
    if not path.is_file():
        checks[label] = False
        gaps.append(f"{label} absent ({path.name})")
        return False
    text = path.read_text(encoding="utf-8", errors="ignore")
    ok = needle in text
    checks[label] = ok
    if not ok:
        gaps.append(f"{label} manquant dans {path.name}")
    return ok


def audit_m11_login_readiness() -> dict[str, Any]:
    """M11 — LoginPanel + LbgAuthClient + jalon contrat."""
    root = _repo_root()
    prime = _prime_client_root()
    gaps: list[str] = []
    checks: dict[str, Any] = {}

    jalon = root / "docs/jalon_m11_login_lbg.md"
    _check_file(jalon, gaps=gaps, label="jalon_m11_doc", checks=checks)
    if jalon.is_file():
        text = jalon.read_text(encoding="utf-8", errors="ignore")
        checks["jalon_not_stub"] = "à rédiger par Hermès" not in text.lower()
        if not checks["jalon_not_stub"]:
            gaps.append("jalon_m11 encore stub (à rédiger par Hermès)")
        checks["contrat_m11_m12"] = "session_token" in text and "ws_url" in text and "À compléter par Thémis" not in text
        if not checks["contrat_m11_m12"]:
            gaps.append("contrat M11-M12 incomplet (session_token / ws_url / Thémis)")

    auth = prime / "scripts/LbgAuthClient.gd"
    _check_file(auth, gaps=gaps, label="lbg_auth_client", checks=checks)

    panel_tscn = prime / "scenes/ui/login_panel.tscn"
    _check_file(panel_tscn, gaps=gaps, label="login_panel_tscn", checks=checks)

    panel_gd = prime / "scripts/login_panel.gd"
    _check_file(panel_gd, gaps=gaps, label="login_panel_gd", checks=checks)

    schema = root / "docs/schemas/lbg-ws/client.login.schema.json"
    _check_file(schema, gaps=gaps, label="client_login_schema", checks=checks)

    return {
        "track": "m11_login",
        "ok": len(gaps) == 0,
        "gaps": gaps,
        "checks": checks,
        "prime_client_root": str(prime),
        "deliverables": [
            "docs/jalon_m11_login_lbg.md",
            "scripts/LbgAuthClient.gd",
            "scenes/ui/login_panel.tscn",
            "scripts/login_panel.gd",
            "docs/schemas/lbg-ws/client.login.schema.json",
        ],
    }


def audit_m11_contract_readiness() -> dict[str, Any]:
    """Thémis — section Contrat M11-M12 dans le jalon."""
    root = _repo_root()
    jalon = root / "docs/jalon_m11_login_lbg.md"
    gaps: list[str] = []
    checks: dict[str, Any] = {}

    _check_file(jalon, gaps=gaps, label="jalon_m11_doc", checks=checks)
    if jalon.is_file():
        text = jalon.read_text(encoding="utf-8", errors="ignore")
        for needle, label in (
            ("session_token", "field_session_token"),
            ("ws_url", "field_ws_url"),
            ("select_character", "msg_select_character"),
            ("enter_zone", "msg_enter_zone"),
            ("auth_failed", "err_auth_failed"),
            ("character_in_use", "err_character_in_use"),
            ("kick_other", "policy_kick_other"),
        ):
            ok = needle in text
            checks[label] = ok
            if not ok:
                gaps.append(f"contrat: {needle} absent")
        stub = "À compléter par Thémis" in text
        checks["contrat_not_stub"] = not stub
        if stub:
            gaps.append("contrat M11-M12 encore stub Thémis")

    return {
        "track": "themis_contract",
        "ok": len(gaps) == 0,
        "gaps": gaps,
        "checks": checks,
        "deliverables": ["docs/jalon_m11_login_lbg.md#contrat-m11--m12"],
    }
