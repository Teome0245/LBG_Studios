"""A3 — Studio Brain court (Company Brain LBG).

Pack facts + 5 leçons + pointeur character — injecté en LAB ops uniquement.
Budget ~4 Ko ; troncature marquée si dépassement.
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

_lock = threading.RLock()
_cache: dict[str, Any] | None = None
_cache_mtime: float | None = None

DEFAULT_MAX_CHARS = 4000


def studio_brain_enabled() -> bool:
    raw = (os.getenv("LBG_STUDIO_BRAIN") or "1").strip().lower()
    return raw not in ("0", "false", "no", "off")


def _pack_candidates() -> list[Path]:
    here = Path(__file__).resolve()
    out: list[Path] = []
    env = (os.getenv("LBG_STUDIO_BRAIN_PATH") or "").strip()
    if env:
        out.append(Path(env))
    out.append(here.parent / "character" / "studio_brain_v1.json")
    out.append(here.parent.parent.parent / "knowledge" / "studio_brain_v1.json")
    for parent in here.parents:
        cand = parent / "knowledge" / "studio_brain_v1.json"
        if cand.is_file():
            out.append(cand)
            break
    out.append(Path("/opt/orchestrateur/backend/src/config/character/studio_brain_v1.json"))
    out.append(Path("/opt/orchestrateur/backend/knowledge/studio_brain_v1.json"))
    return out


def pack_path() -> Path | None:
    for cand in _pack_candidates():
        if cand.is_file():
            return cand
    return None


def load_pack() -> dict[str, Any]:
    global _cache, _cache_mtime
    with _lock:
        p = pack_path()
        if p is None:
            return {}
        try:
            mtime = p.stat().st_mtime
        except OSError:
            return _cache or {}
        if _cache is not None and _cache_mtime == mtime:
            return _cache
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            _cache = data if isinstance(data, dict) else {}
            _cache_mtime = mtime
            return _cache
        except Exception:
            return _cache or {}


def format_studio_brain_block(*, max_chars: int | None = None) -> str:
    """Bloc injecté system prompt — LAB ops. '' si désactivé / vide."""
    if not studio_brain_enabled():
        return ""
    pack = load_pack()
    if not pack:
        return ""
    budget = int(max_chars if max_chars is not None else pack.get("max_chars") or DEFAULT_MAX_CHARS)
    # Plancher bas si budget explicite (tests) ; sinon ≥500 pour un bloc utile.
    floor = 120 if max_chars is not None else 500
    budget = max(floor, min(budget, 8000))

    lines: list[str] = [
        "[Studio Brain LBG — faits courts, ne pas inventer hors de cette liste]",
        f"Pack : {pack.get('id') or 'studio_brain_v1'} · character → {pack.get('character_pack') or 'compagnon_v1'}",
        "Faits :",
    ]
    for fact in pack.get("facts") or []:
        t = str(fact).strip()
        if t:
            lines.append(f"- {t}")
    lessons = pack.get("lessons") or []
    if lessons:
        lines.append("Leçons (≤5) :")
        for les in lessons[:5]:
            if isinstance(les, dict):
                lid = str(les.get("id") or "").strip()
                summary = str(les.get("summary") or "").strip()
                if summary:
                    prefix = f"{lid} — " if lid else ""
                    lines.append(f"- {prefix}{summary}")
            else:
                t = str(les).strip()
                if t:
                    lines.append(f"- {t}")

    text = "\n".join(lines).strip()
    if len(text) <= budget:
        return text
    # Troncature avec marqueur
    cut = text[: budget - 48].rstrip()
    return cut + "\n… [studio_brain tronqué — budget]"
