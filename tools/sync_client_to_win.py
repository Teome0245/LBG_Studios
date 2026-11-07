#!/usr/bin/env python3
"""Synchronisation unifiée des clients Godot (swg-client et prime-client) vers Windows SDS .10."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

STUDIOS_ROOT = Path(__file__).resolve().parents[1]

CLIENT_TARGETS = {
    "swg": {
        "name": "SWG Pre-CU 3D Client",
        "local_base": STUDIOS_ROOT / "packages/swg-client",
        "remote_base": "J:/swgemu/clients/swg-client",
        "files": [
            "scripts/swg_species_system.gd",
            "scripts/swg_species_dialog.gd",
            "scripts/swg_player_controller_3d.gd",
            "scripts/swg_faction_system.gd",
            "scripts/swg_faction_dialog.gd",
            "scripts/swg_datapad_panel.gd",
            "scripts/swg_creature_lair_3d.gd",
            "scripts/swg_missions_terminal_dialog.gd",
            "scripts/swg_chat_box.gd",
            "scripts/swg_target_frame.gd",
            "scripts/swg_crafting_panel.gd",
            "scripts/swg_inventory_paperdoll.gd",
            "scripts/swg_audio_synthesizer.gd",
            "scripts/swg_asset_pipeline.gd",
            "scripts/swg_radial_menu.gd",
            "scripts/swg_world_3d.gd",
            "tools/swg_client_3d_selftest.gd",
        ],
    },
    "prime": {
        "name": "Prime Client 2D",
        "local_base": STUDIOS_ROOT / "packages/prime-client",
        "remote_base": "J:/swgemu/clients/prime-client",
        "files": [
            "scripts/swg_faction_system.gd",
            "scripts/swg_faction_dialog.gd",
            "scripts/swg_species_system.gd",
            "scripts/swg_species_dialog.gd",
            "scripts/swg_datapad_panel.gd",
            "scripts/entity.gd",
            "scripts/swg_target_frame.gd",
            "scripts/swg_chat_box.gd",
            "scripts/swg_crafting_panel.gd",
            "scripts/swg_inventory_paperdoll.gd",
            "scripts/swg_audio_synthesizer.gd",
            "scripts/main.gd",
            "scripts/client_ui_dialogue.gd",
            "tools/client_modular_selftest.gd",
        ],
    },
}


def sync_target(target_key: str, endpoint: str, *, dry_run: bool = False) -> tuple[int, int]:
    cfg = CLIENT_TARGETS[target_key]
    print(f"\n=== Synchronisation {cfg['name']} ({target_key}) -> {cfg['remote_base']} ===")
    local_base = Path(cfg["local_base"])
    remote_base = str(cfg["remote_base"]).rstrip("/")
    files = cfg["files"]

    ok_count = 0
    err_count = 0

    for rel_path in files:
        local_p = local_base / rel_path
        remote_p = f"{remote_base}/{rel_path}"

        if not local_p.is_file():
            print(f"[SKIP] Fichier local introuvable : {local_p}")
            err_count += 1
            continue

        if dry_run:
            print(f"[DRY] {rel_path} -> {remote_p}")
            ok_count += 1
            continue

        try:
            content = local_p.read_text(encoding="utf-8")
            payload = {
                "action": "write_file",
                "parameters": {
                    "path": remote_p,
                    "content": content,
                },
            }
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                status = res_data.get("status", "written")
                print(f"[OK] {rel_path} -> {remote_p} ({status})")
                ok_count += 1
        except Exception as exc:
            print(f"[ERR] {rel_path}: {exc}")
            err_count += 1

    return ok_count, err_count


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronisation des clients Godot vers Windows SDS .10")
    parser.add_argument(
        "--client",
        choices=["swg", "prime", "all"],
        default="all",
        help="Client à synchroniser (swg, prime ou all)",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("LBG_WIN_AGENT_HOST", "http://192.168.0.10:5005"),
        help="URL de l'agent FastAPI Windows (défaut: http://192.168.0.10:5005)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simuler sans envoyer les requêtes HTTP",
    )
    args = parser.parse_args()

    endpoint = f"{args.host.rstrip('/')}/execute"
    targets = ["swg", "prime"] if args.client == "all" else [args.client]

    total_ok = 0
    total_err = 0

    for t in targets:
        ok, err = sync_target(t, endpoint, dry_run=args.dry_run)
        total_ok += ok
        total_err += err

    print(f"\nTotal: {total_ok} succès, {total_err} erreur(s)")
    return 1 if total_err > 0 else 0


if __name__ == "__main__":
    sys.exit(main())

