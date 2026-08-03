"""Pipeline équipe Pygmalion — sprites 2D Prime (deploy WSL → sync 140)."""

from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path
from typing import Any

from team.inspiration_scan import (
    _train_ssh_identity,
    _wsl_project_dir,
    _wsl_ssh_host,
    _wsl_ssh_port,
    _wsl_ssh_user,
    infographiste_ia_root,
)
from team.prime_client_paths import resolve_prime_client_root


def _prime_client_root() -> Path:
    return resolve_prime_client_root()


def _expected_sprites() -> list[str]:
    raw = os.environ.get(
        "LBG_SPRITES_2D_EXPECTED",
        "player_lia,player_nix,player_mira,player_teome,player_gally,player_kael,"
        "player_bot,npc_default,npc_guard,player_official",
    )
    return [s.strip() for s in raw.split(",") if s.strip()]


def probe_sprites_2d_readiness() -> dict[str, Any]:
    """Sonde L1 — PNG sprites Prime Client présents."""
    root = _prime_client_root()
    units = root / "assets" / "sprites" / "units"
    expected = _expected_sprites()
    present: list[str] = []
    missing: list[str] = []
    for name in expected:
        p = units / f"{name}.png"
        if p.is_file() and p.stat().st_size > 0:
            present.append(name)
        else:
            missing.append(name)
    count = len(present)
    total = len(expected)
    readiness = "pret" if count == total else ("partiel" if count else "absent")
    return {
        "kind": "sprites_2d_probe",
        "ok": count > 0,
        "readiness": readiness,
        "present_count": count,
        "expected_count": total,
        "present": present,
        "missing": missing,
        "units_dir": str(units),
        "prime_client_root": str(root),
    }


def build_wsl_sprites_deploy_cmd() -> str:
    host = _wsl_ssh_host()
    port = _wsl_ssh_port()
    user = _wsl_ssh_user()
    identity = _train_ssh_identity()
    project = _wsl_project_dir()
    remote_shell = f"cd {project} && ./scripts/deploy_sprites_to_prime.sh"
    return (
        f"ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new "
        f"-o ConnectTimeout=20 -i {shlex.quote(identity)} -p {port} "
        f"{user}@{host} {shlex.quote(remote_shell)}"
    )


def _sync_sprites_from_wsl() -> dict[str, Any]:
    """Pull sprites depuis WSL vers le core (140)."""
    host = _wsl_ssh_host()
    port = _wsl_ssh_port()
    user = _wsl_ssh_user()
    identity = _train_ssh_identity()
    local_sprites = os.environ.get(
        "LBG_PRIME_CLIENT_LOCAL_SPRITES",
        "/home/sdesh/projects/new_mmo/prime-client/assets/sprites/units",
    ).strip()
    dest = _prime_client_root() / "assets" / "sprites" / "units"
    dest.mkdir(parents=True, exist_ok=True)
    remote = f"{user}@{host}:{local_sprites}/"
    cmd = (
        f"rsync -a --delete -e "
        f"'ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new "
        f"-i {shlex.quote(identity)} -p {port}' "
        f"{shlex.quote(remote)} {shlex.quote(str(dest))}/"
    )
    try:
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"ok": False, "error": str(e)}
    return {
        "ok": proc.returncode == 0,
        "dest": str(dest),
        "stderr_tail": (proc.stderr or "")[-200:] if proc.returncode else None,
    }


def run_sprites_2d_deploy_step(*, sync_to_core: bool = True) -> dict[str, Any]:
    """Deploy sprites via WSL (poste GPU) puis pull vers core 140."""
    ia = infographiste_ia_root()
    script_ok = ia is not None and (ia / "scripts" / "deploy_sprites_to_prime.sh").is_file()
    cmd = build_wsl_sprites_deploy_cmd()
    timeout = float(os.environ.get("LBG_SPRITES_2D_DEPLOY_TIMEOUT_S", "1800"))
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"ok": False, "error": str(e), "command": cmd}

    sync = None
    if sync_to_core and proc.returncode == 0:
        sync = _sync_sprites_from_wsl()

    probe = probe_sprites_2d_readiness()
    ok = proc.returncode == 0 and (sync is None or bool(sync.get("ok")))
    return {
        "ok": ok,
        "kind": "sprites_2d_deploy",
        "command": cmd,
        "script_local": script_ok,
        "sync": sync,
        "stdout_tail": (proc.stdout or "")[-400:],
        "stderr_tail": (proc.stderr or "")[-200:] if proc.returncode else None,
        "probe_after": probe,
    }


def sprites_deploy_enabled() -> bool:
    return os.environ.get("LBG_SPRITES_2D_DEPLOY_ENABLED", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
