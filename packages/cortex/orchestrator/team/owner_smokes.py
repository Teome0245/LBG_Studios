"""Smokes owner Godot / LAN — registry + exécution pour clôture mission (A2)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

# Bundles nommés → liste d’owners (scripts).
OWNER_BUNDLES: dict[str, tuple[str, ...]] = {
    "godot_client": ("hermes_m11", "hermes_m12", "iris_m9", "iris_m10"),
    "godot_login": ("hermes_m11", "hermes_m12"),
    "godot_m9": ("iris_m9",),
    "godot_m10": ("iris_m10",),
    "godot_craft": ("iris_m10",),
    "lan_qa": ("argus_lan",),
}

OWNER_SCRIPTS: dict[str, str] = {
    "hermes_m11": "infra/scripts/smoke_godot_m11_login_lan.sh",
    "hermes_m12": "infra/scripts/smoke_godot_m12_ws_lan.sh",
    "iris_m9": "infra/scripts/smoke_prime_client_minimap.sh",
    "iris_m10": "infra/scripts/smoke_godot_m10_craft_lan.sh",
    "iris_planet": "infra/scripts/smoke_prime_client_planet_map.sh",
    "hermes_sidecar": "infra/scripts/smoke_godot_sidecar_mirror_lan.sh",
    "argus_lan": "infra/scripts/smoke_vm_lan.sh",
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def owners_for_bundle(bundle: str) -> list[str]:
    key = (bundle or "").strip().lower()
    if key in OWNER_BUNDLES:
        return list(OWNER_BUNDLES[key])
    if key in OWNER_SCRIPTS:
        return [key]
    return list(OWNER_BUNDLES["godot_client"])


def run_owner_smoke(owner: str, *, timeout_s: int | None = None) -> dict[str, Any]:
    script_rel = OWNER_SCRIPTS.get(owner)
    if not script_rel:
        return {"owner": owner, "ok": False, "error": f"owner inconnu: {owner}"}
    root = _repo_root()
    script = root / script_rel
    if not script.is_file():
        return {"owner": owner, "ok": True, "skipped": True, "note": f"script absent: {script_rel}"}
    to = timeout_s
    if to is None:
        try:
            to = int(os.environ.get("LBG_TEAM_OWNER_SMOKE_TIMEOUT_S", "90"))
        except ValueError:
            to = 90
    try:
        proc = subprocess.run(
            ["bash", str(script)],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=to,
            check=False,
            env=os.environ.copy(),
        )
        return {
            "owner": owner,
            "script": script_rel,
            "ok": proc.returncode == 0,
            "exit_code": proc.returncode,
            "stdout_tail": (proc.stdout or "")[-800:],
            "stderr_tail": (proc.stderr or "")[-400:],
        }
    except subprocess.TimeoutExpired:
        return {"owner": owner, "ok": False, "error": f"timeout {to}s", "script": script_rel}
    except OSError as exc:
        return {"owner": owner, "ok": False, "error": str(exc), "script": script_rel}


def run_owner_smokes(
    owners: list[str] | None = None,
    *,
    bundle: str = "godot_client",
) -> dict[str, Any]:
    """Exécute les smokes owner ; ok global si tous les non-skipped passent."""
    selected = owners if owners else owners_for_bundle(bundle)
    results: list[dict[str, Any]] = []
    for owner in selected:
        results.append(run_owner_smoke(owner))
    required = [r for r in results if not r.get("skipped")]
    ok = all(bool(r.get("ok")) for r in required) if required else True
    return {
        "kind": "owner_smokes",
        "bundle": bundle,
        "owners": selected,
        "results": results,
        "ok": ok,
        "smoke_ok": ok,
    }
