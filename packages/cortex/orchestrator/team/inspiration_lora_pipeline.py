"""Pipeline équipe Pygmalion — vision par lots → Kohya → entraînement LoRA."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from team.inspiration_scan import (
    count_sorted_buckets,
    infographiste_ia_root,
    run_lora_train_style,
    run_prepare_styles_sorted,
    run_vision_classify_batch,
)


def _state_path() -> Path:
    raw = os.environ.get("LBG_TEAM_INFOGRAPHISTE_LORA_STATE", "").strip()
    if raw:
        return Path(raw)
    return Path("/var/lib/lbg/team_infographiste/lora_pipeline.json")


def _load_state() -> dict[str, Any]:
    p = _state_path()
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_state(state: dict[str, Any]) -> None:
    p = _state_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        return default


def _truthy(name: str, default: str = "1") -> bool:
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes", "on")


def pipeline_targets() -> dict[str, Any]:
    return {
        "unclassified_target": _int_env("LBG_LORA_VISION_UNCLASSIFIED_TARGET", 200),
        "batch_limit": _int_env("LBG_LORA_VISION_BATCH_LIMIT", 100),
        "min_confidence": float(os.environ.get("LBG_LORA_VISION_MIN_CONF", "0.55")),
        "train_enabled": _truthy("LBG_INFOGRAPHISTE_LORA_TRAIN_ENABLED", "0"),
        "styles_to_train": [
            s.strip()
            for s in os.environ.get(
                "LBG_LORA_TRAIN_STYLES",
                "mmorpg_general,prime_sprite_2d",
            ).split(",")
            if s.strip()
        ],
    }


def _lora_output_exists(root: Path, output_name: str) -> bool:
    for cand in (
        root / "lora" / output_name,
        Path(f"/mnt/b/Infographiste_IA/lora/{output_name}"),
    ):
        if cand.is_file() and cand.stat().st_size > 0:
            return True
    return False


def run_lora_pipeline_step(*, persist_state: bool = True) -> dict[str, Any]:
    """Exécute une étape du pipeline (vision OU prepare OU train)."""
    root = infographiste_ia_root()
    ia_label = str(root) if root else os.environ.get(
        "LBG_INFOGRAPHISTE_WSL_PROJECT", "/home/sdesh/projects/Infographiste_IA"
    )

    cfg = pipeline_targets()
    state = _load_state() if persist_state else {}
    buckets = count_sorted_buckets(root)
    unclassified = int(buckets.get("unclassified") or 0)
    steps: list[dict[str, Any]] = []

    # 1) Vision par lots tant que unclassified > cible
    if unclassified > cfg["unclassified_target"]:
        vision = run_vision_classify_batch(
            limit=cfg["batch_limit"],
            min_confidence=cfg["min_confidence"],
        )
        steps.append({"step": "vision_classify", **vision})
        buckets = count_sorted_buckets(root)
        unclassified = int(buckets.get("unclassified") or 0)

        prep = run_prepare_styles_sorted(min_images=_int_env("LBG_LORA_PREPARE_MIN_IMAGES", 20))
        steps.append({"step": "prepare_styles", **prep})

        out = {
            "ok": bool(vision.get("ok")),
            "phase": "vision_batch",
            "unclassified": unclassified,
            "buckets": buckets,
            "steps": steps,
            "infographiste_ia_root": ia_label,
        }
        if persist_state:
            state.update(
                {
                    "last_phase": "vision_batch",
                    "last_unclassified": unclassified,
                    "batches_total": int(state.get("batches_total") or 0) + 1,
                }
            )
            _save_state(state)
        return out

    # 2) Préparer Kohya si buckets ont bougé
    prep = run_prepare_styles_sorted(min_images=_int_env("LBG_LORA_PREPARE_MIN_IMAGES", 20))
    steps.append({"step": "prepare_styles", **prep})

    # 3) Entraîner LoRA manquants
    trained: list[dict[str, Any]] = []
    if cfg["train_enabled"]:
        for style_id in cfg["styles_to_train"]:
            train_out = run_lora_train_style(style_id, deploy=_truthy("LBG_LORA_TRAIN_DEPLOY", "0"))
            trained.append(train_out)
            steps.append({"step": "train_lora", "style_id": style_id, **train_out})
    else:
        for style_id in cfg["styles_to_train"]:
            meta = _train_pending_meta(root, style_id)
            if meta.get("pending"):
                trained.append({"style_id": style_id, "skipped": True, "reason": "train_disabled", **meta})
        steps.append(
            {
                "step": "train_lora",
                "skipped": True,
                "reason": "LBG_INFOGRAPHISTE_LORA_TRAIN_ENABLED=0 — activer sur poste GPU",
            }
        )

    ok = bool(prep.get("ok")) or any(t.get("ok") for t in trained)
    out = {
        "ok": ok,
        "phase": "prepare_and_train",
        "unclassified": unclassified,
        "buckets": buckets,
        "steps": steps,
        "trained": trained,
        "infographiste_ia_root": ia_label,
    }
    if persist_state:
        state.update({"last_phase": "prepare_and_train", "last_unclassified": unclassified})
        _save_state(state)
    return out


def _train_pending_meta(root: Path, style_id: str) -> dict[str, Any]:
    styles_path = root / "config" / "art_styles.json"
    try:
        doc = json.loads(styles_path.read_text(encoding="utf-8"))
        lora_cfg = (doc.get("styles") or {}).get(style_id, {}).get("lora") or {}
        output_name = str(lora_cfg.get("output_name") or f"{style_id}.safetensors")
    except (OSError, json.JSONDecodeError, AttributeError):
        output_name = f"{style_id}.safetensors"
    pending = not _lora_output_exists(root, output_name)
    return {"output_name": output_name, "pending": pending}
