#!/usr/bin/env python3
"""Valide les notebooks éphémères LBG + smoke optionnel contre Ollama LAN.

Usage:
  python tools/colab/validate_ephemeral_notebook.py
  python tools/colab/validate_ephemeral_notebook.py --smoke-local
  LBG_SMOKE_BASE_URL=http://192.168.0.110:11434 \\
    LBG_SMOKE_MODEL=huihui_ai/gemma-4-abliterated:12b \\
    python tools/colab/validate_ephemeral_notebook.py --smoke-local
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

try:
    import httpx
except ImportError:  # smoke-local only
    httpx = None  # type: ignore

ROOT = Path(__file__).resolve().parent
NOTEBOOKS = [
    ROOT / "lbg_reason_ephemeral.ipynb",
    ROOT / "lbg_reason_ephemeral_ollama.ipynb",
]
REQUIRED_SNIPPETS = (
    "LBG_REASON_EPHEMERAL_",
    "huihui_ai/qwen3.5-abliterated:9b",
    "ollama",
)


def _cell_text(nb: dict) -> str:
    parts: list[str] = []
    for cell in nb.get("cells") or []:
        src = cell.get("source") or []
        if isinstance(src, list):
            parts.append("".join(src))
        else:
            parts.append(str(src))
    return "\n".join(parts)


def validate_notebook(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        nb = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"{path.name}: JSON invalide ({exc})"]
    if nb.get("nbformat") != 4:
        errors.append(f"{path.name}: nbformat != 4")
    cells = nb.get("cells") or []
    if len(cells) < 4:
        errors.append(f"{path.name}: trop peu de cellules ({len(cells)})")
    text = _cell_text(nb).lower()
    for snip in REQUIRED_SNIPPETS:
        if snip.lower() not in text:
            errors.append(f"{path.name}: snippet manquant « {snip} »")
    return errors


def smoke_local(*, base_url: str, model: str, timeout: float) -> dict:
    """Simule le chemin notebook → Ollama natif /api/chat (think=false)."""
    base = base_url.rstrip("/")
    if base.endswith("/v1"):
        base = base[:-3]
    tags_url = f"{base}/api/tags"
    chat_url = f"{base}/api/chat"
    with httpx.Client(timeout=httpx.Timeout(timeout)) as client:
        tags = client.get(tags_url)
        tags.raise_for_status()
        names = {m.get("name") for m in (tags.json().get("models") or []) if isinstance(m, dict)}
        if model not in names:
            return {
                "ok": False,
                "error": f"modèle {model} absent ; disponibles={sorted(n for n in names if n)[:12]}",
                "tags_url": tags_url,
            }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "Réponds en une phrase courte."},
                {"role": "user", "content": "Dis bonjour LBG smoke notebook."},
            ],
            "stream": False,
            "think": False,
            "options": {"temperature": 0.2, "num_predict": 64},
        }
        resp = client.post(chat_url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        msg = data.get("message") if isinstance(data.get("message"), dict) else {}
        text = str(msg.get("content") or "").strip()
        if not text:
            return {"ok": False, "error": "réponse vide", "raw_keys": list(data.keys())}
        return {"ok": True, "model": model, "base_url": base, "preview": text[:200]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--smoke-local", action="store_true", help="Appel chat Ollama LAN (simule le notebook)")
    args = ap.parse_args()

    errors: list[str] = []
    for path in NOTEBOOKS:
        if not path.exists():
            errors.append(f"manquant: {path.name}")
            continue
        errors.extend(validate_notebook(path))

    if errors:
        print("FAIL validation:")
        for e in errors:
            print(" -", e)
        return 1
    print(f"OK validation ({len(NOTEBOOKS)} notebooks)")

    if not args.smoke_local:
        return 0

    if httpx is None:
        print("FAIL smoke: httpx manquant (pip install httpx ou activer packages/cortex/.venv)")
        return 2

    base = os.environ.get("LBG_SMOKE_BASE_URL", "http://192.168.0.110:11434").strip()
    # Sur LAN / Colab : même famille qwen3.5-abliterated:9b (T4 ~6.5 Go).
    model = os.environ.get(
        "LBG_SMOKE_MODEL",
        "huihui_ai/qwen3.5-abliterated:9b",
    ).strip()
    timeout = float(os.environ.get("LBG_SMOKE_TIMEOUT_S", "90"))
    print(f"Smoke local → {base} model={model}")
    try:
        out = smoke_local(base_url=base, model=model, timeout=timeout)
    except Exception as exc:
        print(f"FAIL smoke: {exc}")
        return 2
    if not out.get("ok"):
        print(f"FAIL smoke: {out}")
        return 2
    print("OK smoke:", out.get("preview"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
