"""Backend MEDIA — connecteur image→mesh (TRELLIS.2) pour Pygmalion.

Backends supportés (LBG_MESH_GEN_BACKEND) :
  - ``huggingface`` : Space Gradio Microsoft gratuit (0 €, 512³ max).
  - ``trellis2``    : Worker HTTP self-hosted (GPU ≥ 24 Go).
  - ``api``         : API tierce (3D AI Studio, EmpirioLabs…).
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

import httpx

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_HF_SPACE = "microsoft/TRELLIS.2"
_HF_SPACE_URL = "https://microsoft-trellis-2.hf.space"


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
    raw = os.environ.get("LBG_MESH_GEN_BACKEND", "huggingface").strip().lower()
    return raw or "huggingface"


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


def _output_dir() -> Path:
    raw = os.environ.get("LBG_MESH_GEN_OUTPUT_DIR", "").strip()
    if raw:
        return Path(raw)
    return Path(__file__).resolve().parents[2] / "var" / "pygmalion_mesh"


def _hf_token() -> str | None:
    raw = os.environ.get("HF_TOKEN", "").strip()
    return raw or None


# ---------------------------------------------------------------------------
# Probe
# ---------------------------------------------------------------------------

def probe_mesh_worker() -> dict[str, Any]:
    if not mesh_gen_enabled():
        return {"ok": False, "skipped": True, "reason": "LBG_MESH_GEN_ENABLED=0"}

    backend = mesh_gen_backend()

    if backend == "huggingface":
        try:
            with httpx.Client(timeout=httpx.Timeout(10.0)) as client:
                r = client.get(f"{_HF_SPACE_URL}/gradio_api/info")
                ok = r.status_code == 200
                endpoints = []
                if ok:
                    info = r.json()
                    endpoints = list((info.get("named_endpoints") or {}).keys())
                return {
                    "ok": ok,
                    "backend": "huggingface",
                    "space": _HF_SPACE,
                    "endpoints": endpoints,
                    "cost": "0 €",
                }
        except Exception as exc:
            return {"ok": False, "backend": "huggingface", "space": _HF_SPACE, "error": str(exc)}

    # Worker self-hosted ou API tierce
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
            return {"ok": ok, "url": f"{base}/healthz", "status": r.status_code, "backend": backend, **body}
    except Exception as exc:
        return {"ok": False, "url": base, "backend": backend, "error": str(exc)}


# ---------------------------------------------------------------------------
# Backend HuggingFace (gratuit)
# ---------------------------------------------------------------------------

def _submit_huggingface(
    image_path: Path,
    *,
    output_name: str,
    resolution: int,
    target_tris: int,
) -> dict[str, Any]:
    """Appelle le Space Gradio Microsoft TRELLIS.2 via gradio_client (0 €)."""
    try:
        from gradio_client import Client as GradioClient, handle_file  # type: ignore[import-untyped]
    except ImportError:
        return {
            "ok": False,
            "error": "gradio_client manquant — pip install gradio_client",
            "backend": "huggingface",
        }

    res_str = str(min(resolution, 1024))
    if res_str not in ("512", "1024", "1536"):
        res_str = "512"
    dec_target = max(100_000, min(500_000, target_tris * 40))
    tex_size = 2048

    try:
        gc = GradioClient(_HF_SPACE, hf_token=_hf_token())

        gc.predict(api_name="/start_session")
        gc.predict(input=handle_file(str(image_path)), api_name="/preprocess_image")

        gc.predict(
            image=handle_file(str(image_path)),
            seed=42,
            resolution=res_str,
            ss_guidance_strength=7.5,
            ss_guidance_rescale=0.7,
            ss_sampling_steps=12,
            ss_rescale_t=5.0,
            shape_slat_guidance_strength=7.5,
            shape_slat_guidance_rescale=0.5,
            shape_slat_sampling_steps=12,
            shape_slat_rescale_t=3.0,
            tex_slat_guidance_strength=1.0,
            tex_slat_guidance_rescale=0.0,
            tex_slat_sampling_steps=12,
            tex_slat_rescale_t=3.0,
            api_name="/image_to_3d",
        )

        glb_result = gc.predict(
            decimation_target=dec_target,
            texture_size=tex_size,
            api_name="/extract_glb",
        )

        # glb_result = (model3d_path, download_path)
        glb_src: str | None = None
        if isinstance(glb_result, (list, tuple)) and len(glb_result) >= 2:
            glb_src = str(glb_result[1])
        elif isinstance(glb_result, (list, tuple)) and glb_result:
            glb_src = str(glb_result[0])
        elif isinstance(glb_result, str):
            glb_src = glb_result

        if not glb_src or not Path(glb_src).is_file():
            return {
                "ok": False,
                "error": f"GLB introuvable dans la réponse HF: {glb_result!r}",
                "backend": "huggingface",
            }

        out_dir = _output_dir()
        out_dir.mkdir(parents=True, exist_ok=True)
        dest = out_dir / f"{output_name}.glb"
        shutil.copy2(glb_src, dest)

        return {
            "ok": True,
            "backend": "huggingface",
            "space": _HF_SPACE,
            "glb_path": str(dest),
            "glb": str(dest),
            "resolution": res_str,
            "decimation_target": dec_target,
            "input_image": str(image_path),
            "cost": "0 €",
        }
    except Exception as exc:
        return {"ok": False, "backend": "huggingface", "error": str(exc), "input_image": str(image_path)}


# ---------------------------------------------------------------------------
# Backend worker self-hosted
# ---------------------------------------------------------------------------

def _submit_worker(
    image_path: Path,
    *,
    output_name: str,
    resolution: int,
    target_tris: int,
) -> dict[str, Any]:
    base = mesh_gen_base_url()
    timeout = mesh_gen_timeout_s()
    mime = "image/png" if image_path.suffix.lower() == ".png" else "application/octet-stream"
    try:
        with httpx.Client(timeout=httpx.Timeout(timeout)) as client:
            files = {"file": (image_path.name, image_path.read_bytes(), mime)}
            data = {
                "output_name": output_name,
                "resolution": str(resolution),
                "target_tris": str(target_tris),
                "backend": mesh_gen_backend(),
            }
            r = client.post(f"{base}/v1/mesh/image-to-glb", files=files, data=data)
            r.raise_for_status()
            payload = r.json()
            if not isinstance(payload, dict):
                return {"ok": False, "error": "réponse worker invalide", "raw": payload}
            payload.setdefault("ok", bool(payload.get("glb_path") or payload.get("glb")))
            payload.setdefault("backend", mesh_gen_backend())
            payload.setdefault("input_image", str(image_path))
            return payload
    except Exception as exc:
        return {"ok": False, "error": str(exc), "base_url": base, "input_image": str(image_path)}


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

def submit_image_to_mesh(
    image_path: str | Path,
    *,
    output_name: str = "pygmalion_asset",
    resolution: int | None = None,
    simplify_tris: int | None = None,
) -> dict[str, Any]:
    """Envoie une image au backend mesh et retourne le GLB produit."""
    if not mesh_gen_enabled():
        return {"ok": False, "skipped": True, "reason": "LBG_MESH_GEN_ENABLED=0"}

    backend = mesh_gen_backend()

    if backend != "huggingface":
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

    if backend == "huggingface":
        return _submit_huggingface(path, output_name=output_name, resolution=res, target_tris=tris)
    return _submit_worker(path, output_name=output_name, resolution=res, target_tris=tris)


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
