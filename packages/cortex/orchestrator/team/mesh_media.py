"""Backend MEDIA — connecteur image→mesh (TRELLIS.2) pour Pygmalion."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx


def mesh_gen_enabled() -> bool:
    return os.environ.get("LBG_MESH_GEN_ENABLED", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def mesh_gen_base_url() -> str:
    return os.environ.get("LBG_MESH_GEN_BASE_URL", "http://192.168.0.10:8190").strip().rstrip("/")


def mesh_gen_backend() -> str:
    return os.environ.get("LBG_MESH_GEN_BACKEND", "trellis2").strip().lower() or "trellis2"


def mesh_gen_default_resolution() -> int:
    raw = os.environ.get("LBG_MESH_GEN_RESOLUTION", "512").strip()
    try:
        return max(256, min(1536, int(raw)))
    except ValueError:
        return 512


def mesh_gen_timeout_s() -> float:
    raw = os.environ.get("LBG_MESH_GEN_TIMEOUT_S", "900").strip()
    try:
        return max(60.0, float(raw))
    except ValueError:
        return 900.0


def probe_mesh_worker() -> dict[str, Any]:
    if not mesh_gen_enabled():
        return {"ok": False, "skipped": True, "reason": "LBG_MESH_GEN_ENABLED=0"}
    base = mesh_gen_base_url()
    try:
        with httpx.Client(timeout=httpx.Timeout(8.0)) as client:
            r = client.get(f"{base}/healthz")
            ok = r.status_code == 200
            body: dict[str, Any] = {}
            if r.headers.get("content-type", "").startswith("application/json"):
                parsed = r.json()
                if isinstance(parsed, dict):
                    body = parsed
            return {
                "ok": ok,
                "url": f"{base}/healthz",
                "status": r.status_code,
                "backend": mesh_gen_backend(),
                **body,
            }
    except Exception as exc:
        return {"ok": False, "url": base, "backend": mesh_gen_backend(), "error": str(exc)}


def submit_image_to_mesh(
    image_path: str | Path,
    *,
    output_name: str = "pygmalion_asset",
    resolution: int | None = None,
    simplify_tris: int | None = None,
) -> dict[str, Any]:
    """Envoie une image au worker mesh (TRELLIS.2) et retourne le GLB produit."""
    if not mesh_gen_enabled():
        return {"ok": False, "skipped": True, "reason": "LBG_MESH_GEN_ENABLED=0"}

    probe = probe_mesh_worker()
    if not probe.get("ok"):
        return {"ok": False, "error": "worker mesh injoignable", "probe": probe}

    path = Path(image_path)
    if not path.is_file():
        return {"ok": False, "error": f"image introuvable: {path}"}

    res = resolution if resolution is not None else mesh_gen_default_resolution()
    tris = simplify_tris
    if tris is None:
        raw = os.environ.get("LBG_MESH_GEN_TARGET_TRIS", "8000").strip()
        try:
            tris = int(raw)
        except ValueError:
            tris = 8000

    base = mesh_gen_base_url()
    timeout = mesh_gen_timeout_s()
    mime = "image/png" if path.suffix.lower() == ".png" else "application/octet-stream"

    try:
        with httpx.Client(timeout=httpx.Timeout(timeout)) as client:
            files = {"file": (path.name, path.read_bytes(), mime)}
            data = {
                "output_name": output_name,
                "resolution": str(res),
                "target_tris": str(tris),
                "backend": mesh_gen_backend(),
            }
            r = client.post(f"{base}/v1/mesh/image-to-glb", files=files, data=data)
            r.raise_for_status()
            payload = r.json()
            if not isinstance(payload, dict):
                return {"ok": False, "error": "réponse worker invalide", "raw": payload}
            payload.setdefault("ok", bool(payload.get("glb_path") or payload.get("glb")))
            payload.setdefault("backend", mesh_gen_backend())
            payload.setdefault("input_image", str(path))
            return payload
    except Exception as exc:
        return {"ok": False, "error": str(exc), "base_url": base, "input_image": str(path)}


def mesh_from_comfyui_images(
    images: list[str],
    *,
    gap_label: str = "asset",
    resolution: int | None = None,
) -> dict[str, Any]:
    """Prend la première image ComfyUI et lance image→mesh."""
    if not images:
        return {"ok": False, "skipped": True, "reason": "aucune image ComfyUI"}
    slug = "".join(ch if ch.isalnum() else "_" for ch in gap_label.lower())[:48].strip("_") or "asset"
    return submit_image_to_mesh(
        images[0],
        output_name=slug,
        resolution=resolution,
    )
