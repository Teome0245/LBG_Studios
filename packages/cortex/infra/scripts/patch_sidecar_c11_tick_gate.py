#!/usr/bin/env python3
"""Idempotent : injecte ``http_post_tick_guard`` au début de ``do_POST`` du sidecar :8791.

Usage: python3 patch_sidecar_c11_tick_gate.py /path/to/core3_ia_sidecar.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

MARKER = "http_post_tick_guard"

GUARD_BLOCK = '''
            # C11 TickGate — mutations craft/quête/tip/enqueue (SpaceMolt)
            try:
                from lbg_agents import agent_catalog as _tick_cat  # type: ignore
            except ImportError:
                _tick_cat = None
            _tick_body = None
            if _tick_cat is not None and hasattr(_tick_cat, "http_post_tick_guard"):
                try:
                    _tick_body = self._read_json()
                except Exception:
                    _tick_body = {}
                if not isinstance(_tick_body, dict):
                    _tick_body = {}
                self._tick_gate_body = _tick_body
                _guarded = _tick_cat.http_post_tick_guard(path, _tick_body)
                if _guarded is not None:
                    self._tick_gate_body = None
                    _code, _payload = _guarded
                    self._json(int(_code), _payload)
                    return
'''


def _ensure_read_json_cache(text: str) -> str:
    """Fait rejouer le body déjà lu par le TickGate aux handlers ``_read_json()``."""
    if "_read_json_uncached" in text and "_tick_gate_body" in text:
        return text
    m = re.search(r"(\n[ \t]+)def _read_json\(self\)", text)
    if not m:
        raise SystemExit("sidecar: def _read_json introuvable")
    indent = m.group(1)
    wrapper = (
        f"{indent}def _read_json(self):"
        f"{indent}    cached = getattr(self, \"_tick_gate_body\", None)"
        f"{indent}    if cached is not None:"
        f"{indent}        self._tick_gate_body = None"
        f"{indent}        return cached"
        f"{indent}    return self._read_json_uncached()"
        f"{indent}"
        f"{indent}def _read_json_uncached(self)"
    )
    # Replace only the def line (keep the rest of the original method as uncached)
    text = text[: m.start()] + wrapper + text[m.end() :]
    # m.end() points after "def _read_json(self)" — original continues with "(...):\n"
    # Actually m matched "\n    def _read_json(self)" without the rest.
    # Fix: the original was "def _read_json(self) -> dict:" or "def _read_json(self):"
    # Our replace left ") -> dict:" orphaned. Re-read carefully.
    return text


def _ensure_read_json_cache_v2(text: str) -> str:
    if "_read_json_uncached" in text:
        return text
    pattern = re.compile(
        r"^([ \t]+)def _read_json\(self\)(.*)$",
        re.MULTILINE,
    )
    m = pattern.search(text)
    if not m:
        raise SystemExit("sidecar: def _read_json introuvable")
    indent, rest = m.group(1), m.group(2)
    wrapper = (
        f"{indent}def _read_json(self){rest}\n"
        f"{indent}    cached = getattr(self, \"_tick_gate_body\", None)\n"
        f"{indent}    if cached is not None:\n"
        f"{indent}        self._tick_gate_body = None\n"
        f"{indent}        return cached\n"
        f"{indent}    return self._read_json_uncached()\n"
        f"\n"
        f"{indent}def _read_json_uncached(self){rest}\n"
    )
    # Original method body still follows the old def — we need to remove the old
    # def line only and insert wrapper + rename. Simplest: replace def line with
    # uncached def, then insert wrapper before it.
    old_line = m.group(0)
    text = text.replace(
        old_line,
        (
            f"{indent}def _read_json(self){rest}\n"
            f"{indent}    cached = getattr(self, \"_tick_gate_body\", None)\n"
            f"{indent}    if cached is not None:\n"
            f"{indent}        self._tick_gate_body = None\n"
            f"{indent}        return cached\n"
            f"{indent}    return self._read_json_uncached()\n"
            f"\n"
            f"{indent}def _read_json_uncached(self){rest}"
        ),
        1,
    )
    return text


def _inject_guard(text: str) -> str:
    if MARKER in text:
        return text
    patterns = [
        'def do_POST(self) -> None:\n        try:\n            path = self.path.rstrip("/") or "/"\n',
        "def do_POST(self) -> None:\n        try:\n            path = self.path.rstrip('/') or '/'\n",
    ]
    for needle in patterns:
        if needle in text:
            return text.replace(needle, needle + GUARD_BLOCK, 1)
    # Fallback regex
    m = re.search(
        r"def do_POST\(self\).*?:\n[ \t]+try:\n[ \t]+path = self\.path\.rstrip\([^\n]+\)\n",
        text,
    )
    if not m:
        raise SystemExit("sidecar: début do_POST introuvable pour injection TickGate")
    return text[: m.end()] + GUARD_BLOCK + text[m.end() :]


def patch(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    text = _ensure_read_json_cache_v2(original)
    text = _inject_guard(text)
    if text == original:
        return False
    path.write_text(text, encoding="utf-8")
    return True


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: patch_sidecar_c11_tick_gate.py <sidecar.py>", file=sys.stderr)
        raise SystemExit(2)
    target = Path(sys.argv[1])
    if not target.is_file():
        raise SystemExit(f"missing {target}")
    changed = patch(target)
    print(f"patched={changed} path={target}")


if __name__ == "__main__":
    main()
