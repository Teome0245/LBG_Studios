#!/usr/bin/env python3
"""Génère un Modelfile Ollama pour personnaliser gemma-4-abliterated:E4b-qat.

Pas de LoRA / GPU : SYSTEM + params issus du pack caractère Compagnon.
Tag cible : lbg-compagnon-e4b-v1 (un modèle à la fois).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

DEFAULT_BASE = "huihui_ai/gemma-4-abliterated:E4b-qat"
DEFAULT_TAG = "lbg-compagnon-e4b-v1"


def _cortex_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_pack_path() -> Path:
    return _cortex_root() / "knowledge" / "character" / "compagnon_v1.json"


def build_system_prompt(pack: dict) -> str:
    name = str(pack.get("display_name") or "Compagnon").strip()
    personality = pack.get("personality") if isinstance(pack.get("personality"), dict) else {}
    summary = str(personality.get("summary") or "").strip()
    worldview = [str(x).strip() for x in (personality.get("worldview") or []) if str(x).strip()]
    nots = [str(x).strip() for x in (personality.get("not") or []) if str(x).strip()]
    bl = [str(x).strip() for x in (pack.get("blacklist") or []) if str(x).strip()]
    character = pack.get("character") if isinstance(pack.get("character"), dict) else {}
    dials = character.get("dials_default") if isinstance(character.get("dials_default"), dict) else {}

    lines = [
        f"Tu es {name}, collègue studio LBG (Compagnon) — pas un assistant générique.",
        summary or "Collègue compétent, fier de l'écosystème, jamais soumis ni coach théâtral.",
        "",
        "Règles dures :",
        "- N'invente jamais l'état Team / LAN / jobs / VMs.",
        "- Pas de « En tant qu'IA… », pas de questionnaire en série.",
        "- Engage d'abord (avis / proposition) ; une question seulement si blocage réel.",
        "- Les faits studio longs passent par le RAG / Self — tu ne les mémorises pas dans tes poids.",
    ]
    if worldview:
        lines.append("")
        lines.append("Worldview :")
        for w in worldview[:6]:
            lines.append(f"- {w}")
    if nots:
        lines.append("")
        lines.append("À éviter : " + " ; ".join(nots[:5]))
    if dials:
        lines.append("")
        lines.append(
            "Expression (dials 0–1) : "
            + ", ".join(f"{k}={float(v):.2f}" for k, v in sorted(dials.items()) if isinstance(v, (int, float)))
        )
    if bl:
        lines.append("")
        lines.append("Blacklist (ne pas produire) : " + ", ".join(f"« {x} »" for x in bl[:8]))
    return "\n".join(lines).strip() + "\n"


def render_modelfile(
    *,
    base: str,
    system: str,
    temperature: float = 0.45,
    top_p: float = 0.9,
) -> str:
    # Échapper les guillemets pour le bloc SYSTEM multiligne Ollama
    # Syntaxe : SYSTEM """ ... """
    safe = system.replace('"""', "'''")
    return (
        f"FROM {base}\n"
        f"\n"
        f'SYSTEM """\n'
        f"{safe}"
        f'"""\n'
        f"\n"
        f"PARAMETER temperature {temperature}\n"
        f"PARAMETER top_p {top_p}\n"
        f"PARAMETER num_ctx 8192\n"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Build Modelfile perso Compagnon e2b")
    ap.add_argument("--pack", type=Path, default=default_pack_path())
    ap.add_argument("--base", default=DEFAULT_BASE)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--temperature", type=float, default=0.45)
    args = ap.parse_args()

    pack = json.loads(args.pack.read_text(encoding="utf-8"))
    system = build_system_prompt(pack)
    text = render_modelfile(base=args.base, system=system, temperature=args.temperature)
    out = args.out or (Path(__file__).resolve().parent / "Modelfile")
    out.write_text(text, encoding="utf-8")
    print(f"wrote {out} ({len(text)} bytes)")


if __name__ == "__main__":
    main()
