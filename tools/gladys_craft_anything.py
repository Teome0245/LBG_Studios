#!/usr/bin/env python3
"""
gladys_craft_anything.py — Outil d'orchestration Craft Anything pour Gladys (O1/O2).
Intégration souveraine 0€ : étude de cibles, ingénierie inverse et génération Godot 4.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

DEFAULT_BACKEND = os.environ.get("LBG_CRAFT_BACKEND", "Ollama 110 (Gladys)")
TIMEOUT_SECS = int(os.environ.get("LBG_CRAFT_TIMEOUT_SECS", "1800"))
CRAFT_CLI = shutil_which = os.environ.get("LBG_CRAFT_CLI", "/home/lbg/.local/bin/craft-anything-cli")


def run_craft_cmd(args: list[str], *, capture_json: bool = False) -> dict | int:
    """Exécute une commande craft-anything-cli avec le timeout Gladys configuré (1800s)."""
    if not os.path.exists(CRAFT_CLI):
        print(f"❌ Erreur : binaire introuvable dans {CRAFT_CLI}", file=sys.stderr)
        return 1

    cmd = [CRAFT_CLI] + args
    print(f"⚡ [Gladys Craft Engine] Exécution : {' '.join(cmd)}")

    try:
        if capture_json:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_SECS, check=True)
            return json.loads(res.stdout)
        else:
            return subprocess.run(cmd, timeout=TIMEOUT_SECS).returncode
    except subprocess.TimeoutExpired:
        print(f"❌ Timeout dépassé ({TIMEOUT_SECS}s)", file=sys.stderr)
        return 124
    except Exception as exc:
        print(f"❌ Erreur d'exécution : {exc}", file=sys.stderr)
        return 1


def cmd_doctor() -> int:
    """Vérifie l'état de l'infrastructure Craft Anything."""
    return run_craft_cmd(["doctor"])


def cmd_rebuild(target: str, request: str, *, engine: str = "godot", project_folder: str | None = None, deep: bool = False) -> int:
    """Lance une session d'étude et de reconstruction vers Godot 4."""
    args = ["rebuild", target, request, "--build-with", engine, "--backend", DEFAULT_BACKEND]
    if deep:
        args.append("--deep")
    else:
        args.append("--clean-room")
    if project_folder:
        args.extend(["--project-folder", project_folder, "--existing", "edit"])

    return run_craft_cmd(args)


def cmd_triage(path: str) -> int:
    """Analyse un binaire ou un asset logiciel."""
    return run_craft_cmd(["triage", path])


def main() -> int:
    parser = argparse.ArgumentParser(description="Outil Craft Anything pour l'organisme Gladys (LBG Studios)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # doctor
    subparsers.add_parser("doctor", help="Diagnostic complet des sondes, MCP et backends IA")

    # triage
    p_triage = subparsers.add_parser("triage", help="Inspection rapide d'un fichier ou binaire")
    p_triage.add_argument("path", help="Chemin du fichier à analyser")

    # rebuild / improve
    p_rebuild = subparsers.add_parser("rebuild", help="Étudier une cible ou améliorer un projet existant")
    p_rebuild.add_argument("target", help="URL, chemin exécutable ou dossier cible ('-' si aucun)")
    p_rebuild.add_argument("request", help="Consigne de reconstruction ou d'amélioration")
    p_rebuild.add_argument("--engine", default="godot", help="Moteur cible (défaut: godot)")
    p_rebuild.add_argument("--project-folder", default=None, help="Dossier d'un projet existant à modifier")
    p_rebuild.add_argument("--deep", action="store_true", help="Activer le mode deep (inspection interne du binaire)")

    args = parser.parse_args()

    if args.command == "doctor":
        return cmd_doctor()
    elif args.command == "triage":
        return cmd_triage(args.path)
    elif args.command == "rebuild":
        return cmd_rebuild(args.target, args.request, engine=args.engine, project_folder=args.project_folder, deep=args.deep)

    return 0


if __name__ == "__main__":
    sys.exit(main())
