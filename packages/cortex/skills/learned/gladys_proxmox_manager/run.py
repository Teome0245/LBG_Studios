"""Skill Gladys Appris : gladys_proxmox_manager.

Superviseur & pilote Proxmox VE (lbgr720 / 192.168.0.201) via SSH par clé :
- L0 (lecture) : inventaire hôte/RAM/stockages/LXC/VM, backups (backup-temp/local), snapshots.
- L2 (HIGH) : sauvegarde vzdump zstd, création de snapshot, start/shutdown/reboot contrôlé.
  Aucune commande destructive (destroy/purge) n'est exposée.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys

PVE_HOST = "192.168.0.201"
_VMID_RE = re.compile(r"^\d{2,5}$")
_SAFE_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]{2,40}$")


def run_pve(remote_cmd: str, timeout_s: int = 30) -> tuple[int, str, str]:
    cmd = [
        "ssh",
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=5",
        f"root@{PVE_HOST}",
        remote_cmd,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return 124, "", f"Timeout après {timeout_s}s"
    except Exception as exc:
        return 1, "", str(exc)


def detect_kind(vmid: str) -> str | None:
    """Retourne 'lxc', 'qemu' ou None selon le VMID."""
    rc, _, _ = run_pve(f"pct status {vmid} >/dev/null 2>&1")
    if rc == 0:
        return "lxc"
    rc2, _, _ = run_pve(f"qm status {vmid} >/dev/null 2>&1")
    if rc2 == 0:
        return "qemu"
    return None


def show_inventory() -> int:
    rc, out, err = run_pve(
        "echo '=== HOTE ==='; hostname; uptime; free -h | head -n 3; "
        "echo '=== STOCKAGES ==='; pvesm status; "
        "echo '=== LXC ==='; pct list; "
        "echo '=== VM ==='; qm list"
    )
    if rc != 0:
        print(f"Erreur accès Proxmox {PVE_HOST}: {err}", file=sys.stderr)
        return 1
    print(f"✦ Inventaire Proxmox ({PVE_HOST}) :")
    print(out.strip())
    return 0


def show_backups(vmid: str = "") -> int:
    if vmid and not _VMID_RE.match(vmid):
        print(f"VMID invalide: {vmid}", file=sys.stderr)
        return 1
    vmid_flag = f" --vmid {vmid}" if vmid else ""
    remote = (
        f"for st in backup-temp local; do "
        f"echo \"--- Stockage: $st ---\"; "
        f"pvesm list $st --content backup{vmid_flag} 2>/dev/null || true; "
        f"done"
    )
    rc, out, err = run_pve(remote)
    if rc != 0:
        print(f"Erreur lecture backups: {err}", file=sys.stderr)
        return 1
    title = f"CT/VM {vmid}" if vmid else "tous les CT/VM"
    print(f"✦ Sauvegardes Proxmox ({title}) :")
    print(out.strip())
    return 0


def show_snapshots(vmid: str) -> int:
    if not _VMID_RE.match(vmid):
        print(f"VMID invalide: {vmid}", file=sys.stderr)
        return 1
    kind = detect_kind(vmid)
    if not kind:
        print(f"CT/VM {vmid} introuvable sur {PVE_HOST}", file=sys.stderr)
        return 1
    tool = "pct" if kind == "lxc" else "qm"
    rc, out, err = run_pve(f"{tool} listsnapshot {vmid}")
    if rc != 0:
        print(f"Erreur lecture snapshots {vmid}: {err}", file=sys.stderr)
        return 1
    print(f"✦ Snapshots {kind.upper()} {vmid} :")
    print(out.strip())
    return 0


def create_snapshot(vmid: str, snap_name: str) -> int:
    if not _VMID_RE.match(vmid) or not _SAFE_NAME_RE.match(snap_name):
        print("Paramètres invalides (VMID ou nom snapshot).", file=sys.stderr)
        return 1
    kind = detect_kind(vmid)
    if not kind:
        print(f"CT/VM {vmid} introuvable sur {PVE_HOST}", file=sys.stderr)
        return 1
    tool = "pct" if kind == "lxc" else "qm"
    rc, out, err = run_pve(f"{tool} snapshot {vmid} {snap_name}", timeout_s=120)
    if rc != 0:
        print(f"Échec snapshot {vmid}/{snap_name}: {err}", file=sys.stderr)
        return 1
    print(f"✦ Snapshot `{snap_name}` créé avec succès sur {kind.upper()} {vmid}.")
    if out.strip():
        print(out.strip())
    return 0


def run_backup(vmid: str, storage: str = "backup-temp") -> int:
    if not _VMID_RE.match(vmid) or not _SAFE_NAME_RE.match(storage):
        print("Paramètres invalides (VMID ou stockage).", file=sys.stderr)
        return 1
    # Vérifier que le stockage cible est actif (anti-saturation pve-root)
    rc_s, out_s, _ = run_pve(f"pvesm status -storage {storage} 2>/dev/null || true")
    if rc_s != 0 or "active" not in out_s:
        print(f"Refus sécurité : le stockage `{storage}` n'est pas actif sur {PVE_HOST}.", file=sys.stderr)
        return 1
    rc, out, err = run_pve(
        f"vzdump {vmid} --storage {storage} --mode snapshot --compress zstd",
        timeout_s=600,
    )
    if rc != 0:
        print(f"Échec vzdump {vmid} -> {storage}: {err}", file=sys.stderr)
        return 1
    print(f"✦ Sauvegarde vzdump terminée pour {vmid} vers `{storage}` (zstd).")
    tail = "\n".join(out.strip().splitlines()[-8:])
    if tail:
        print(tail)
    return 0


def power_action(action: str, vmid: str) -> int:
    if action not in ("start", "shutdown", "reboot") or not _VMID_RE.match(vmid):
        print("Action autorisée : start | shutdown | reboot + VMID valide.", file=sys.stderr)
        return 1
    kind = detect_kind(vmid)
    if not kind:
        print(f"CT/VM {vmid} introuvable sur {PVE_HOST}", file=sys.stderr)
        return 1
    tool = "pct" if kind == "lxc" else "qm"
    rc, out, err = run_pve(f"{tool} {action} {vmid}", timeout_s=60)
    if rc != 0:
        print(f"Échec {tool} {action} {vmid}: {err}", file=sys.stderr)
        return 1
    print(f"✦ Action `{action}` exécutée sur {kind.upper()} {vmid}.")
    if out.strip():
        print(out.strip())
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Skill Gladys : Proxmox VE Manager (lbgr720)")
    parser.add_argument("--inventory", action="store_true", help="Inventaire hôte, RAM, stockages, LXC et VMs")
    parser.add_argument("--backups", nargs="?", const="", metavar="VMID", help="Lister les sauvegardes (optionnel: VMID)")
    parser.add_argument("--snapshots", type=str, metavar="VMID", help="Lister les snapshots d'un CT/VM")
    parser.add_argument("--snapshot", nargs=2, metavar=("VMID", "NAME"), help="Créer un snapshot (L2)")
    parser.add_argument("--backup", type=str, metavar="VMID", help="Lancer un backup vzdump zstd (L2)")
    parser.add_argument("--storage", type=str, default="backup-temp", help="Stockage cible pour --backup")
    parser.add_argument("--power", nargs=2, metavar=("ACTION", "VMID"), help="start|shutdown|reboot sur un CT/VM (L2)")

    args = parser.parse_args()
    if args.inventory:
        return show_inventory()
    if args.backups is not None:
        return show_backups(args.backups)
    if args.snapshots:
        return show_snapshots(args.snapshots)
    if args.snapshot:
        return create_snapshot(args.snapshot[0], args.snapshot[1])
    if args.backup:
        return run_backup(args.backup, storage=args.storage)
    if args.power:
        return power_action(args.power[0], args.power[1])
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
