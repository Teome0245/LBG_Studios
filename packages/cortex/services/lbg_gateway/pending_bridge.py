"""Pont optionnel gateway → ia_bridge/pending.jsonl (Phase 3 v0).

Rate-limit + coalescence des ``move_to`` joueur (ex. Teome) pour éviter de
saturer la file consommée par Lua / ZB-2 inject (actions IA bloquées).
"""

from __future__ import annotations

import os
import threading
import time
from pathlib import Path

ZONE = "tatooine"

_lock = threading.Lock()
# player -> (ts, x, y, z)
_last_move: dict[str, tuple[float, float, float, float]] = {}


def pending_path() -> Path | None:
    raw = os.environ.get("LBG_GATEWAY_PENDING_FILE", "").strip()
    if not raw:
        return None
    return Path(raw)


def inject_enabled() -> bool:
    return os.environ.get("LBG_GATEWAY_INJECT_MOVE", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def inject_player_name() -> str:
    return os.environ.get("LBG_GATEWAY_INJECT_PLAYER", "Teome").strip() or "Teome"


def _min_interval_s() -> float:
    try:
        # Défaut plus lent : laisse la file IA (Lia/Nix) respirer.
        return max(0.2, float(os.environ.get("LBG_GATEWAY_INJECT_MOVE_MIN_INTERVAL_S", "1.2")))
    except ValueError:
        return 1.2


def _min_delta() -> float:
    try:
        return max(0.0, float(os.environ.get("LBG_GATEWAY_INJECT_MOVE_MIN_DELTA", "2.5")))
    except ValueError:
        return 2.5


def _coalesce_enabled() -> bool:
    return os.environ.get("LBG_GATEWAY_INJECT_MOVE_COALESCE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def append_line(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(line.rstrip("\n"))
        f.write("\n")


def _drop_player_move_to(path: Path, player: str) -> None:
    """Ne conserve qu'un seul move_to par joueur : retire les lignes existantes."""
    if not path.is_file():
        return
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return
    lines = raw.splitlines()
    prefix = f"move_to|{player}|"
    kept = [ln for ln in lines if not ln.startswith(prefix)]
    if len(kept) == len(lines):
        return
    try:
        path.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")
    except OSError:
        return


def inject_move_to(path: Path, player: str, x: float, y: float, z: float, note: str = "godot") -> None:
    """Format ia_bridge : action|player|zone|x|y|z|message (coords cellule / planète)."""
    pname = (player or "").strip() or inject_player_name()
    now = time.time()
    key = pname
    with _lock:
        prev = _last_move.get(key)
        if prev is not None:
            pts, px, py, pz = prev
            dt = now - pts
            dist = ((x - px) ** 2 + (y - py) ** 2 + (z - pz) ** 2) ** 0.5
            # Skip écriture si trop fréquent ET déplacement négligeable.
            if dt < _min_interval_s() and dist < _min_delta():
                return
            # Intervalle trop court mais position a bougé : coalesce (remplace) sans spam.
            if dt < _min_interval_s() and not _coalesce_enabled():
                return
        _last_move[key] = (now, x, y, z)
        line = f"move_to|{pname}|{ZONE}|{x:.2f}|{y:.2f}|{z:.2f}|{note}"
        if _coalesce_enabled():
            _drop_player_move_to(path, pname)
        append_line(path, line)
