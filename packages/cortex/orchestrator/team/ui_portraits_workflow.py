"""Track Iris — portraits UI dialogue (PNG sous assets/ui/portraits)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Mapping

from team.prime_client_paths import resolve_prime_client_root


_ROLES_NEEDING_PNG = ("npc_merchant", "npc_civilian", "npc_trainer")
# Interim distinct : merchant/civilian ← bartender ; trainer ← guide (évite clone guide partout)
_SOURCE_BY_ROLE = {
    "npc_merchant": "npc_bartender",
    "npc_civilian": "npc_bartender",
    "npc_trainer": "npc_guide",
}
_SOURCE_FALLBACK = "npc_guide"


def _manifest_path(root: Path) -> Path:
    return root / "config" / "dialogue_portraits.json"


def probe_ui_portraits(ctx: Mapping[str, Any] | None = None) -> dict[str, Any]:
    root = resolve_prime_client_root(ctx)
    manifest = _manifest_path(root)
    gaps: list[str] = []
    checks: dict[str, Any] = {
        "prime_client_root": str(root),
        "manifest_exists": manifest.is_file(),
    }
    svg_keys: list[str] = []
    missing_dirs: list[str] = []

    if not manifest.is_file():
        gaps.append("config/dialogue_portraits.json absent")
        return {
            "kind": "ui_portraits_probe",
            "ok": False,
            "gaps": gaps,
            "checks": checks,
            "prime_client_root": str(root),
        }

    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        gaps.append(f"manifest illisible: {exc}")
        return {
            "kind": "ui_portraits_probe",
            "ok": False,
            "gaps": gaps,
            "checks": checks,
            "prime_client_root": str(root),
        }

    portraits = data.get("portraits") if isinstance(data.get("portraits"), dict) else {}
    for key, rel in portraits.items():
        path_s = str(rel)
        if path_s.endswith(".svg"):
            svg_keys.append(str(key))
        # vérifie existence fichier référencé
        if path_s.startswith("res://"):
            disk = root / path_s.replace("res://", "", 1)
            if not disk.is_file() and path_s.endswith(".png"):
                gaps.append(f"PNG manquant: {key} → {path_s}")

    for role in _ROLES_NEEDING_PNG:
        role_dir = root / "assets" / "ui" / "portraits" / role
        if not role_dir.is_dir() or not (role_dir / "neutral.png").is_file():
            missing_dirs.append(role)
            gaps.append(f"dossier PNG absent: assets/ui/portraits/{role}/neutral.png")

    if svg_keys:
        # ne flag que les clés merchant/civilian/trainer/default liées aux trous UI
        relevant = [k for k in svg_keys if any(r in k for r in _ROLES_NEEDING_PNG) or "default" in k]
        if relevant:
            gaps.append(f"entrées .svg (TextureRect fragile): {', '.join(relevant[:12])}")
        checks["svg_portrait_keys"] = svg_keys

    checks["missing_portrait_dirs"] = missing_dirs
    ok = len(gaps) == 0
    return {
        "kind": "ui_portraits_probe",
        "ok": ok,
        "gaps": gaps,
        "checks": checks,
        "prime_client_root": str(root),
    }


def remediate_ui_portraits(
    ctx: Mapping[str, Any] | None = None,
    *,
    write_files: bool = True,
) -> dict[str, Any]:
    """Copie interim PNG (bartender/guide) + retarget dialogue_portraits.json hors .svg."""
    root = resolve_prime_client_root(ctx)
    probe_before = probe_ui_portraits(ctx)
    actions: list[dict[str, Any]] = []
    if not write_files:
        return {
            "kind": "ui_portraits_remediation",
            "ok": False,
            "skipped": True,
            "reason": "write_files=false",
            "probe_before": probe_before,
            "prime_client_root": str(root),
        }

    for role in _ROLES_NEEDING_PNG:
        src_name = _SOURCE_BY_ROLE.get(role, _SOURCE_FALLBACK)
        src_dir = root / "assets" / "ui" / "portraits" / src_name
        if not src_dir.is_dir():
            src_dir = root / "assets" / "ui" / "portraits" / _SOURCE_FALLBACK
        if not src_dir.is_dir():
            actions.append({"role": role, "error": f"source absente: {src_name}"})
            continue
        dst_dir = root / "assets" / "ui" / "portraits" / role
        dst_dir.mkdir(parents=True, exist_ok=True)
        copied: list[str] = []
        for src in sorted(src_dir.glob("*.png")):
            dst = dst_dir / src.name
            if not dst.is_file():
                shutil.copy2(src, dst)
                copied.append(src.name)
        actions.append({"role": role, "source": src_name, "copied": copied, "dir": str(dst_dir)})

    manifest = _manifest_path(root)
    patched_keys: list[str] = []
    if manifest.is_file():
        data = json.loads(manifest.read_text(encoding="utf-8"))
        portraits = data.setdefault("portraits", {})
        if not isinstance(portraits, dict):
            portraits = {}
            data["portraits"] = portraits
        # ensure PNG entries for merchant/civilian/trainer + default
        mapping = {
            "npc_merchant_neutral": "res://assets/ui/portraits/npc_merchant/neutral.png",
            "npc_merchant_happy": "res://assets/ui/portraits/npc_merchant/happy.png",
            "npc_civilian_neutral": "res://assets/ui/portraits/npc_civilian/neutral.png",
            "npc_civilian_happy": "res://assets/ui/portraits/npc_civilian/happy.png",
            "npc_civilian_sad": "res://assets/ui/portraits/npc_civilian/sad.png",
            "npc_trainer_neutral": "res://assets/ui/portraits/npc_trainer/neutral.png",
            "npc_trainer_angry": "res://assets/ui/portraits/npc_trainer/angry.png",
            "npc_trainer_determined": "res://assets/ui/portraits/npc_trainer/determined.png",
            "npc_default_neutral": "res://assets/ui/portraits/npc_civilian/neutral.png",
        }
        for key, path in mapping.items():
            prev = str(portraits.get(key, ""))
            if prev != path:
                portraits[key] = path
                patched_keys.append(key)
        if patched_keys:
            manifest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            actions.append({"manifest_patched": patched_keys})

    probe_after = probe_ui_portraits(ctx)
    return {
        "kind": "ui_portraits_remediation",
        "ok": bool(probe_after.get("ok")),
        "actions": actions,
        "probe_before": probe_before,
        "probe_after": probe_after,
        "prime_client_root": str(root),
    }


def execute_ui_portraits_workflow(ctx: Mapping[str, Any] | None = None) -> dict[str, Any]:
    ctx = dict(ctx or {})
    write = bool(ctx.get("write_files") or ctx.get("iris_forge") or ctx.get("portrait_ui"))
    # défaut : écrire si gaps
    probe = probe_ui_portraits(ctx)
    rem = None
    if not probe.get("ok"):
        rem = remediate_ui_portraits(ctx, write_files=write if "write_files" in ctx or "iris_forge" in ctx else True)
        probe = rem.get("probe_after") or probe_ui_portraits(ctx)
    return {
        "kind": "ui_portraits_workflow",
        "ok": bool(probe.get("ok")),
        "probe": probe,
        "remediation": rem,
        "prime_client_root": str(resolve_prime_client_root(ctx)),
        "human_summary": (
            "Iris — portraits UI dialogue\n\n"
            f"Root: {resolve_prime_client_root(ctx)}\n"
            f"Probe ok={probe.get('ok')} gaps={probe.get('gaps')}\n"
        ),
    }
