#!/usr/bin/env python3
"""
tools/asset_pipeline/ai_creature_pipeline.py
Orchestrateur de génération IA de créatures et personnages pour Godot 4.

Ce script gère le pipeline complet :
1. Réception du prompt ou concept 2D
2. Appel du moteur 3D (Trellis / Tripo3D / Meshy ou générateur local)
3. Traitement Blender Headless (nettoyage topologique, centrage, auto-rig squelette, animation d'attente)
4. Déploiement direct dans `packages/prime-client/assets/models/`

Usage :
    python3 tools/asset_pipeline/ai_creature_pipeline.py --name krayt_juvenile --prompt "desert lizard alien predator"
"""

import sys
import os
import argparse
import subprocess
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
OUTPUT_DIR = os.path.join(REPO_ROOT, "packages/prime-client/assets/models")


def run_blender_creature_processor(creature_name: str, target_dir: str):
    """Exécute le post-traitement de rigging et animation dans Blender."""
    processor_script = os.path.join(SCRIPT_DIR, "blender_creature_processor.py")
    cmd = [
        "blender", "-b", "-P", processor_script, "--",
        "--name", creature_name,
        "--out-dir", target_dir
    ]
    print(f"[*] Exécution Blender Headless : {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[-] Erreur Blender:\n{result.stderr}")
        return False
    print(result.stdout)
    return True


def generate_creature(name: str, prompt: str, dry_run: bool = False):
    print("=" * 60)
    print(f"  AI Creature Pipeline — Créature : {name}")
    print(f"  Prompt concept : '{prompt}'")
    print(f"  Destination    : {OUTPUT_DIR}")
    print("=" * 60)

    # 1. Vérification de l'environnement
    if subprocess.run(["which", "blender"], capture_output=True).returncode != 0:
        print("[-] Blender n'est pas installé ou introuvable dans le PATH.")
        return False

    # 2. Exécution du processeur Blender (génération, rig, skinning, anims)
    success = run_blender_creature_processor(name, OUTPUT_DIR)
    
    if success:
        target_glb = os.path.join(OUTPUT_DIR, f"{name}.glb")
        if os.path.exists(target_glb):
            size_kb = os.path.getsize(target_glb) / 1024
            print(f"[+] Succès ! Asset généré : {target_glb} ({size_kb:.1f} KB)")
            print(f"[+] Prêt pour instanciation dans Godot prime-client.")
            return True

    return False


def main():
    parser = argparse.ArgumentParser(description="Pipeline de génération de créatures 3D pour LBG Studios")
    parser.add_argument("--name", default="creature_demo", help="Identifiant de la créature")
    parser.add_argument("--prompt", default="alien desert beast with carapace and horns", help="Description conceptuelle")
    parser.add_argument("--dry-run", action="store_true", help="Mode test")
    args = parser.parse_args()

    success = generate_creature(args.name, args.prompt, dry_run=args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

