"""Overrides de prompts système (candidats mutator appliqués en L2).

Fichiers sous ``team/data/prompt_overrides/<target>.txt``.
Jamais d'écriture dans ``agents/declarations/``.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

VALID_TARGETS: frozenset[str] = frozenset({"outcome_judge", "plan_llm"})


def overrides_enabled() -> bool:
    return os.environ.get("LBG_TEAM_PROMPT_OVERRIDES", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def overrides_dir() -> Path:
    raw = os.environ.get("LBG_TEAM_PROMPT_OVERRIDES_DIR", "").strip()
    if raw:
        return Path(raw)
    return Path(__file__).resolve().parent / "data" / "prompt_overrides"


def override_path(target: str) -> Path:
    t = (target or "").strip().lower()
    if t not in VALID_TARGETS:
        raise ValueError(f"target override invalide: {target}")
    return overrides_dir() / f"{t}.txt"


def load_override(target: str) -> str | None:
    if not overrides_enabled():
        return None
    try:
        path = override_path(target)
    except ValueError:
        return None
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return text if len(text) > 40 else None


def write_override(*, target: str, prompt: str, meta: dict | None = None) -> Path:
    text = (prompt or "").strip()
    if len(text) < 40:
        raise ValueError("prompt candidat trop court")
    path = override_path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S")
    header = f"# LBG prompt override target={target} applied={stamp}\n"
    if meta:
        for k, v in list(meta.items())[:8]:
            header += f"# {k}: {v}\n"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(header + text + "\n", encoding="utf-8")
    tmp.replace(path)
    return path


def clear_override(target: str) -> bool:
    path = override_path(target)
    if path.is_file():
        path.unlink()
        return True
    return False


def meta_status() -> dict[str, object]:
    active: dict[str, bool] = {}
    for t in sorted(VALID_TARGETS):
        active[t] = load_override(t) is not None
    return {
        "enabled": overrides_enabled(),
        "dir": str(overrides_dir()),
        "active": active,
    }
