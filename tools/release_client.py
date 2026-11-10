#!/usr/bin/env python3
"""tools/release_client.py — Pipeline de release unifié pour les clients LBG Studios.

Enchaîne :
  1. Validation des tests headless Godot (mode complet ou --quick-check)
  2. Mise à jour de packages/prime-client/assets/build_info.json (horodatage UTC ISO)
  3. Synchronisation vers machine Windows SDS .10 (J:/swgemu/clients/...)
  4. Publication sur le serveur de patches HTTP 192.168.0.246:8080 (Launchpad)

Usage :
  python3 tools/release_client.py --dry-run
  python3 tools/release_client.py --client prime --quick-check
  python3 tools/release_client.py --client swg --no-remote
  python3 tools/release_client.py --all
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
PRIME_CLIENT_DIR = REPO_ROOT / "packages" / "prime-client"
BUILD_INFO_FILE = PRIME_CLIENT_DIR / "assets" / "build_info.json"
CI_GODOT_SCRIPT = REPO_ROOT / "tools" / "ci_godot_headless.sh"
SYNC_SCRIPT = REPO_ROOT / "tools" / "sync_client_to_win.py"
DEPLOY_PATCH_SCRIPT = PRIME_CLIENT_DIR / "tools" / "deploy_prime_client_patch_246.sh"


def log_step(title: str) -> None:
    print(f"\n\033[1;34m===> [RELEASE] {title}\033[0m")


def log_success(msg: str) -> None:
    print(f"\033[1;32m[+] {msg}\033[0m")


def log_error(msg: str) -> None:
    print(f"\033[1;31m[-] {msg}\033[0m", file=sys.stderr)


def run_command(cmd: list[str], dry_run: bool = False) -> bool:
    cmd_str = " ".join(str(c) for c in cmd)
    if dry_run:
        print(f"\033[33m[DRY-RUN] Serait exécuté : {cmd_str}\033[0m")
        return True
    print(f"Exécution : {cmd_str}")
    res = subprocess.run(cmd)
    return res.returncode == 0


def update_build_info(dry_run: bool = False) -> bool:
    if not BUILD_INFO_FILE.exists():
        log_error(f"Fichier build_info introuvable: {BUILD_INFO_FILE}")
        return False

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        data = json.loads(BUILD_INFO_FILE.read_text(encoding="utf-8"))
        old_sync = data.get("synced_at", "inconnu")
        data["synced_at"] = now_iso

        # Compte les fichiers réels du client prime
        total_files = sum(1 for _ in PRIME_CLIENT_DIR.rglob("*") if _.is_file() and not any(p.startswith(".") for p in _.parts))
        data["file_count"] = total_files

        if dry_run:
            print(f"\033[33m[DRY-RUN] build_info.json synced_at : {old_sync} -> {now_iso} (files: {total_files})\033[0m")
        else:
            BUILD_INFO_FILE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            log_success(f"build_info.json mis à jour : {now_iso} (total fichiers: {total_files})")
        return True
    except Exception as exc:
        log_error(f"Erreur mise à jour build_info: {exc}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Pipeline de release unifié LBG Studios")
    parser.add_argument(
        "--client",
        choices=["prime", "swg", "all"],
        default="all",
        help="Client cible pour la release (défaut: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simuler les étapes sans rien modifier ni déployer",
    )
    parser.add_argument(
        "--quick-check",
        action="store_true",
        help="Utiliser la CI Godot rapide (--quick) au lieu des 20 suites",
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Sauter l'étape des tests (non recommandé)",
    )
    parser.add_argument(
        "--no-remote",
        action="store_true",
        help="Ne pas exécuter le déploiement distant rsync/HTTP vers .246:8080",
    )

    args = parser.parse_args()

    print("============================================================")
    print("  LBG Studios — Pipeline de Release & Déploiement Client")
    print(f"  Cible : {args.client.upper()} | Dry-run : {args.dry_run}")
    print("============================================================")

    # 1. Tests headless Godot
    if not args.skip_tests:
        log_step("1/4 — Vérification de la suite de tests Headless Godot")
        ci_cmd = [str(CI_GODOT_SCRIPT)]
        if args.quick_check:
            ci_cmd.append("--quick")

        if not run_command(ci_cmd, dry_run=args.dry_run):
            log_error("Échec des tests headless Godot. Release interrompue.")
            return 1
        log_success("Tests headless validés.")
    else:
        log_step("1/4 — Tests ignorés (--skip-tests)")

    # 2. Mise à jour build_info
    log_step("2/4 — Actualisation des métadonnées de build (build_info.json)")
    if not update_build_info(dry_run=args.dry_run):
        return 1

    # 3. Synchronisation Windows SDS .10
    log_step(f"3/4 — Synchronisation Windows SDS .10 ({args.client})")
    sync_cmd = [sys.executable, str(SYNC_SCRIPT), "--client", args.client]
    if args.dry_run:
        sync_cmd.append("--dry-run")

    if not run_command(sync_cmd, dry_run=False):  # sync_client_to_win gère son propre dry_run
        log_error("Échec de la synchronisation Windows.")
        return 1
    log_success("Synchronisation Windows achevée avec succès.")

    # 4. Publication serveur de patches distant .246:8080 (pour prime ou all)
    if not args.no_remote and args.client in ("prime", "all"):
        log_step("4/4 — Publication serveur de patch Launchpad (.246:8080)")
        if DEPLOY_PATCH_SCRIPT.exists():
            deploy_cmd = ["bash", str(DEPLOY_PATCH_SCRIPT)]
            if not run_command(deploy_cmd, dry_run=args.dry_run):
                log_error("Échec du déploiement patch distant sur 192.168.0.246.")
                return 1
            log_success("Patch publié sur le serveur 192.168.0.246:8080.")
        else:
            log_error(f"Script de déploiement introuvable: {DEPLOY_PATCH_SCRIPT}")
            return 1
    else:
        log_step("4/4 — Déploiement distant omis (--no-remote ou client swg)")

    print("\n============================================================")
    log_success(f"Release {args.client.upper()} terminée avec succès !")
    print("============================================================\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
