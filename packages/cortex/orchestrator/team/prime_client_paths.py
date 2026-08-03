"""Résolution canonique du root prime-client pour la Team.

Source de vérité : ``LBG_Studios/packages/prime-client``.
Le legacy ``new_mmo`` / ``/opt/new_mmo`` n'est utilisé qu'en fallback explicite
(``LBG_PRIME_ALLOW_LEGACY_NEW_MMO=1``) ou si aucun chemin Studios n'existe.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping


def _truthy(raw: str | None) -> bool:
    return (raw or "").strip().lower() in ("1", "true", "yes", "on")


def allow_legacy_new_mmo() -> bool:
    return _truthy(os.environ.get("LBG_PRIME_ALLOW_LEGACY_NEW_MMO"))


def is_legacy_new_mmo_path(path: Path | str) -> bool:
    s = str(path).replace("\\", "/").lower()
    return "/new_mmo/" in f"/{s.strip('/')}/" or s.rstrip("/").endswith("/new_mmo/prime-client")


def _cortex_root() -> Path:
    # team/prime_client_paths.py → orchestrator → cortex
    return Path(__file__).resolve().parents[2]


def studios_prime_candidates() -> list[Path]:
    """Chemins LBG_Studios (ordre de préférence)."""
    cortex = _cortex_root()
    # .../LBG_Studios/packages/cortex → sibling prime-client
    packages = cortex.parent
    studios = packages.parent
    out: list[Path] = [
        packages / "prime-client",
        studios / "packages" / "prime-client",
        Path("/opt/lbg-studios/packages/prime-client"),
        Path("/opt/LBG_Studios/packages/prime-client"),
        Path("/home/sdesh/projects/LBG_Studios/packages/prime-client"),
    ]
    # Dédup en préservant l'ordre
    seen: set[str] = set()
    uniq: list[Path] = []
    for p in out:
        key = str(p.resolve()) if p.exists() else str(p)
        if key in seen:
            continue
        seen.add(key)
        uniq.append(p)
    return uniq


def legacy_new_mmo_candidates() -> list[Path]:
    new_mmo = os.environ.get("LBG_NEW_MMO_ROOT", "").strip()
    out: list[Path] = []
    if new_mmo:
        out.append(Path(new_mmo) / "prime-client")
    out.extend(
        [
            Path("/opt/new_mmo/prime-client"),
            Path("/home/sdesh/projects/new_mmo/prime-client"),
        ]
    )
    return out


def find_studios_prime_client() -> Path | None:
    for cand in studios_prime_candidates():
        if cand.is_dir() and (cand / "project.godot").is_file():
            return cand
    for cand in studios_prime_candidates():
        if cand.is_dir():
            return cand
    return None


def resolve_prime_client_root(
    ctx: Mapping[str, Any] | None = None,
    *,
    allow_legacy: bool | None = None,
) -> Path:
    """Retourne le dossier prime-client à utiliser pour sondes/deploy Team.

    Priorité :
    1. ``ctx.prime_client_root_override`` / ``ctx.prime_client_root`` (si existe)
    2. ``LBG_PRIME_CLIENT_ROOT`` — **sauf** si legacy new_mmo et qu'un Studios existe
       (sauf ``LBG_PRIME_ALLOW_LEGACY_NEW_MMO=1``)
    3. Premier chemin LBG_Studios existant
    4. Legacy new_mmo (si autorisé ou seul disponible)
    """
    ctx = dict(ctx or {})
    legacy_ok = allow_legacy_new_mmo() if allow_legacy is None else bool(allow_legacy)
    studios = find_studios_prime_client()

    for key in ("prime_client_root_override", "prime_client_root"):
        raw = str(ctx.get(key) or "").strip()
        if not raw:
            continue
        p = Path(raw)
        if not p.is_dir():
            continue
        if is_legacy_new_mmo_path(p) and studios is not None and not legacy_ok:
            return studios
        return p

    env_raw = os.environ.get("LBG_PRIME_CLIENT_ROOT", "").strip()
    if env_raw:
        env_path = Path(env_raw)
        if env_path.is_dir():
            if is_legacy_new_mmo_path(env_path) and studios is not None and not legacy_ok:
                return studios
            return env_path

    if studios is not None:
        return studios

    for cand in legacy_new_mmo_candidates():
        if cand.is_dir():
            return cand

    # Défaut documenté : Studios (même absent — messages d'erreur plus clairs)
    return Path("/home/sdesh/projects/LBG_Studios/packages/prime-client")


def prime_client_root_report(ctx: Mapping[str, Any] | None = None) -> dict[str, Any]:
    root = resolve_prime_client_root(ctx)
    return {
        "prime_client_root": str(root),
        "exists": root.is_dir(),
        "has_project_godot": (root / "project.godot").is_file(),
        "is_legacy_new_mmo": is_legacy_new_mmo_path(root),
        "allow_legacy_new_mmo": allow_legacy_new_mmo(),
        "studios_found": str(find_studios_prime_client()) if find_studios_prime_client() else None,
        "env_LBG_PRIME_CLIENT_ROOT": os.environ.get("LBG_PRIME_CLIENT_ROOT", ""),
    }
