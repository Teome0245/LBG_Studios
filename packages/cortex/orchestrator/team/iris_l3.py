"""Iris L3 — apply auto GDScript sur allowlist après smoke vert.

Niveaux (ADR 0019 / vision Fable) :
- L1 : staging uniquement (défaut)
- L2 : apply avec token humain (tâche Team approval_required)
- L3 : apply auto **uniquement** chemins allowlistés si smoke OK
      et ``LBG_IRIS_FORGE_L3=1`` (concret, plus « optionnel » produit).
"""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath


# Chemins relatifs sous prime-client — seuls appliqués en L3.
# Étendre volontairement ; hors liste = staging only (jamais write auto).
DEFAULT_L3_ALLOWLIST: frozenset[str] = frozenset(
    {
        "scripts/minimap_hud.gd",
        "scripts/waypoint_store.gd",
        "scripts/planet_map_panel.gd",
        "scenes/ui/minimap_hud.tscn",
        "scenes/ui/planet_map_panel.tscn",
        "config/minimap_config.json",
        "config/waypoints.json",
        # Hermès réseau — borné
        "scripts/network_bridge.gd",
        "scripts/player_controller.gd",
        "scenes/ui/login_panel.tscn",
    }
)

# Interdits même si listés par erreur
_L3_DENY_SUFFIXES: tuple[str, ...] = (
    ".env",
    ".pem",
    ".key",
    "credentials",
    "secret",
)
_L3_DENY_PREFIXES: tuple[str, ...] = (
    "../",
    "/",
    "addons/",
    ".godot/",
    "export/",
)


def iris_forge_l3_enabled() -> bool:
    return os.environ.get("LBG_IRIS_FORGE_L3", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def l3_allowlist() -> frozenset[str]:
    raw = os.environ.get("LBG_IRIS_FORGE_L3_ALLOWLIST", "").strip()
    if not raw:
        return DEFAULT_L3_ALLOWLIST
    parts = {p.strip().lstrip("./") for p in raw.split(",") if p.strip()}
    return frozenset(parts) if parts else DEFAULT_L3_ALLOWLIST


def normalize_rel(path: str) -> str:
    p = (path or "").replace("\\", "/").strip().lstrip("./")
    # refuse absolute / traversal
    try:
        pure = PurePosixPath(p)
        if pure.is_absolute() or ".." in pure.parts:
            return ""
        return str(pure)
    except Exception:
        return ""


def path_denied(rel: str) -> str | None:
    low = rel.lower()
    if low.startswith("/") or ".." in PurePosixPath(low).parts:
        return "deny_absolute_or_traversal"
    for pref in _L3_DENY_PREFIXES:
        if not pref or pref in ("/", "../"):
            continue
        if low.startswith(pref.lower()):
            return f"deny_prefix:{pref}"
    for suf in _L3_DENY_SUFFIXES:
        if suf in low:
            return f"deny_pattern:{suf}"
    return None


def path_allowed_l3(rel: str) -> bool:
    norm = normalize_rel(rel)
    if not norm:
        return False
    if path_denied(norm):
        return False
    return norm in l3_allowlist()


def filter_patches_for_l3_apply(patches: list[object]) -> tuple[list[object], list[dict[str, str]]]:
    """Sépare patches appliquables L3 vs refusés.

    Chaque patch doit exposer ``target_rel`` (IrisForgePatch ou dict).
    """
    allowed: list[object] = []
    rejected: list[dict[str, str]] = []
    for p in patches:
        if isinstance(p, dict):
            rel = str(p.get("target_rel") or "")
            skipped = p.get("skipped_reason")
        else:
            rel = str(getattr(p, "target_rel", "") or "")
            skipped = getattr(p, "skipped_reason", None)
        if skipped:
            rejected.append({"target_rel": rel, "reason": f"skipped:{skipped}"})
            continue
        norm = normalize_rel(rel)
        if not norm:
            rejected.append({"target_rel": rel, "reason": "invalid_path"})
            continue
        deny = path_denied(norm)
        if deny:
            rejected.append({"target_rel": norm, "reason": deny})
            continue
        if not path_allowed_l3(rel):
            rejected.append({"target_rel": norm, "reason": "not_in_l3_allowlist"})
            continue
        allowed.append(p)
    return allowed, rejected


def should_auto_apply_l3(*, smoke_ok: bool, explicit_auto_apply: bool | None = None) -> bool:
    """Décide si on applique en mode L3.

    - ``explicit_auto_apply=True`` : legacy ``LBG_IRIS_FORGE_AUTO_APPLY`` (tout, dangereux)
      → on borne quand même à l'allowlist si L3 on ; si L3 off et auto_apply True = L2-like full
        (conservé pour compat, mais L3 flag recommandé).
    - L3 on + smoke OK → apply allowlist only.
    """
    if not smoke_ok:
        return False
    if explicit_auto_apply is True and not iris_forge_l3_enabled():
        # Legacy full auto — caller must still filter; we signal apply
        return True
    if iris_forge_l3_enabled():
        return True
    if explicit_auto_apply is True:
        return True
    return False


def l3_status() -> dict[str, object]:
    return {
        "l3_enabled": iris_forge_l3_enabled(),
        "allowlist": sorted(l3_allowlist()),
        "allowlist_count": len(l3_allowlist()),
        "note": "L3 = write auto allowlist après smoke vert ; hors liste = staging L1",
        "write_policy": {
            "l3_allowlist": "auto après smoke si LBG_IRIS_FORGE_L3=1",
            "complex_gdscript": "Cursor Cloud Agent / humain — write principal hors allowlist (L2)",
            "not_in_scope": "OpenHands / édition repo libre sur 140",
        },
    }
