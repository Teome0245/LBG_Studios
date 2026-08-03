"""Sonde L1 Launchpad / distribution client (Hermès owner)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def _repo_roots() -> list[Path]:
    roots: list[Path] = []
    env = os.environ.get("LBG_STUDIOS_ROOT", "").strip()
    if env:
        roots.append(Path(env))
    # cortex/orchestrator/team → parents[3] = packages, [4] = LBG_Studios
    here = Path(__file__).resolve()
    try:
        roots.append(here.parents[4])
    except IndexError:
        pass
    # Deploy path on 140
    roots.append(Path("/opt/LBG_Studios"))
    roots.append(Path("/opt/LBG_IA_MMO"))
    out: list[Path] = []
    seen: set[str] = set()
    for r in roots:
        key = str(r)
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out


def probe_launchpad() -> dict[str, Any]:
    """Vérifie présence sources Launchpad + script verify (read-only)."""
    gaps: list[str] = []
    found_pkg: str | None = None
    found_verify: str | None = None
    for root in _repo_roots():
        pkg = root / "packages" / "launchpad"
        if pkg.is_dir() and ((pkg / "package.json").is_file() or (pkg / "src").is_dir()):
            found_pkg = str(pkg)
            break
    if not found_pkg:
        gaps.append("packages/launchpad absent (sources Electron)")

    for root in _repo_roots():
        verify = root / "packages" / "prime-client" / "tools" / "verify_launchpad_prime.ps1"
        if verify.is_file():
            found_verify = str(verify)
            break
    if not found_verify:
        gaps.append("verify_launchpad_prime.ps1 absent (prime-client/tools)")

    docs_ok = False
    for root in _repo_roots():
        for rel in (
            "packages/cortex/docs/client_dual_launchpad.md",
            "docs/client_dual_launchpad.md",
        ):
            if (root / rel).is_file():
                docs_ok = True
                break
        if docs_ok:
            break
    if not docs_ok:
        gaps.append("doc client_dual_launchpad.md introuvable")

    return {
        "track": "hermes_launchpad",
        "ok": len(gaps) == 0,
        "gaps": gaps,
        "package_path": found_pkg,
        "verify_script": found_verify,
        "owner": "hermes",
        "note": "L1 read-only — build Windows hors E2E 140 ; Hermès owner distribution",
    }
