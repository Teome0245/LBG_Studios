"""Skill Gladys Appris : gladys_mailcow_manager.

Gestionnaire & Superviseur Mailcow / SOGo (mail.laboiteageeks.fr) :
- Contrôle de santé des conteneurs Mailcow et de la file d'attente Postfix (CT 155 / 192.168.0.155).
- Relève et synthèse des courriers non lus (Dovecot).
- Synthèse intelligente pour le compte-rendu matinal (Morning Brief).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys

PVE_HOST = "192.168.0.201"
CTID = "155"
DEFAULT_USER = "sdesharches@laboiteageeks.fr"


def run_remote_pct(cmd_str: str, timeout_s: int = 20) -> tuple[int, str, str]:
    """Exécute une commande dans CT 155 via SSH sur Proxmox .201."""
    full_cmd = [
        "ssh",
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=5",
        f"root@{PVE_HOST}",
        f"pct exec {CTID} -- {cmd_str}",
    ]
    try:
        proc = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return 124, "", f"Timeout après {timeout_s}s"
    except Exception as exc:
        return 1, "", str(exc)


def check_health() -> int:
    """Vérifie la santé des conteneurs Mailcow et la file d'attente Postfix."""
    print(f"✦ Contrôle de santé du serveur Mailcow (CT {CTID} / 192.168.0.155) :")

    code, stdout, stderr = run_remote_pct("docker ps --format '{{.Names}}\t{{.Status}}'")
    if code != 0:
        print(f"  ❌ Erreur accès conteneurs: {stderr}", file=sys.stderr)
        return 1

    critical_services = [
        "postfix",
        "dovecot",
        "sogo",
        "rspamd",
        "nginx",
        "acme",
        "mysql",
        "redis",
    ]
    lines = stdout.splitlines()
    status_map: dict[str, str] = {}
    for line in lines:
        parts = line.split("\t")
        if len(parts) == 2:
            name, stat = parts[0], parts[1]
            for s in critical_services:
                if s in name:
                    status_map[s] = stat

    print("  • Services clés :")
    for s in critical_services:
        stat = status_map.get(s, "Non détecté")
        icon = "✅" if "Up" in stat else "⚠️"
        print(f"    {icon} {s.upper():<10} : {stat}")

    code_q, stdout_q, _ = run_remote_pct("docker exec mailcowdockerized-postfix-mailcow-1 mailq")
    if code_q == 0:
        q_lines = stdout_q.strip().splitlines()
        q_summary = q_lines[-1] if q_lines else "File vide"
        print(f"  • File d'attente SMTP (Postfix) : {q_summary}")
    else:
        print("  • File d'attente SMTP : non joignable")

    return 0


def list_unread(user: str = DEFAULT_USER, limit: int = 10) -> int:
    """Interroge les messages non lus pour l'utilisateur spécifié."""
    code_s, stdout_s, _ = run_remote_pct(
        f"docker exec mailcowdockerized-dovecot-mailcow-1 doveadm mailbox status -u {user} 'messages unseen' INBOX"
    )
    if code_s != 0:
        print(f"Erreur d'accès à la boîte {user}", file=sys.stderr)
        return 1

    match = re.search(r"unseen=(\d+)", stdout_s)
    unseen_count = int(match.group(1)) if match else 0

    print(f"✦ Boîte de réception : {user}")
    print(f"  • Nouveaux courriers non lus : {unseen_count}")

    if unseen_count == 0:
        print("  • Aucun nouveau message en attente.")
        return 0

    fetch_cmd = (
        f"docker exec mailcowdockerized-dovecot-mailcow-1 doveadm fetch "
        f"-u {user} 'date.received hdr.from hdr.subject' unseen"
    )
    code_f, stdout_f, _ = run_remote_pct(fetch_cmd)
    if code_f != 0:
        print("  • Impossible d'extraire les détails des messages.", file=sys.stderr)
        return 1

    messages = []
    current_msg: dict[str, str] = {}
    for line in stdout_f.splitlines():
        line = line.strip()
        if not line or line == "\x0c":
            if current_msg:
                messages.append(current_msg)
                current_msg = {}
            continue
        if line.startswith("date.received:"):
            current_msg["date"] = line.split(":", 1)[1].strip()
        elif line.startswith("hdr.from:"):
            current_msg["from"] = line.split(":", 1)[1].strip()
        elif line.startswith("hdr.subject:"):
            current_msg["subject"] = line.split(":", 1)[1].strip()

    if current_msg:
        messages.append(current_msg)

    print(f"  • Détail des {min(len(messages), limit)} derniers courriers :")
    for msg in messages[:limit]:
        d = msg.get("date", "")
        f = msg.get("from", "Expéditeur inconnu")
        s = msg.get("subject", "(Sans objet)")
        print(f"    ✉️ [{d}] {f} — \"{s}\"")

    return 0


def generate_brief(user: str = DEFAULT_USER) -> int:
    """Génère une synthèse complète pour le compte-rendu matinal de Stève."""
    print("=" * 60)
    print("☕ COMPTE-RENDU SERVEUR MAIL & MESSAGERIE GLADYS")
    print("=" * 60)

    check_health()
    print()

    list_unread(user=user)
    print()

    print("✦ Surveillance des boîtes unifiées :")
    print("  • sdesharches@laboiteageeks.fr : Hébergé localement (Mailcow)")
    print("  • sdesharches@free.fr          : Synchronisation IMAP active")
    print("  • teome245@gmail.com           : Passerelle IMAP sécurisée")
    print("  • sdesharches@ikmail.com       : Infomaniak")
    print("=" * 60)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Skill Gladys : Mailcow & SOGo Manager")
    parser.add_argument("--health", action="store_true", help="Vérifier la santé des conteneurs Mailcow")
    parser.add_argument("--unread", action="store_true", help="Lister les courriers non lus")
    parser.add_argument("--user", type=str, default=DEFAULT_USER, help=f"Utilisateur cible (défaut: {DEFAULT_USER})")
    parser.add_argument("--limit", type=int, default=10, help="Nombre de messages à afficher")
    parser.add_argument("--brief", action="store_true", help="Générer un compte-rendu complet pour Gladys")

    args = parser.parse_args()

    if args.health:
        return check_health()
    elif args.unread:
        return list_unread(user=args.user, limit=args.limit)
    elif args.brief:
        return generate_brief(user=args.user)
    else:
        return generate_brief(user=args.user)


if __name__ == "__main__":
    sys.exit(main())
