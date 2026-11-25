"""Skill Gladys Appris : gladys_adguard_manager.

Gestionnaire DNS AdGuard Home :
- Inspection des requêtes bloquées sur http://192.168.0.53 (via CT 153 sur Proxmox .201)
- Whitelisting / Déblocage d'un domaine sous validation L2.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys

PVE_HOST = "192.168.0.201"
CTID = "153"
ADGUARD_DATA = "/opt/AdGuardHome/data/querylog.json"
ADGUARD_CONF = "/opt/AdGuardHome/AdGuardHome.yaml"
ADGUARD_BIN = "/opt/AdGuardHome/AdGuardHome"

_DOMAIN_RE = re.compile(r"^[a-zA-Z0-9][-a-zA-Z0-9.]{1,253}\.[a-zA-Z]{2,}$")


def list_blocked(limit: int = 10) -> int:
    """Interroge les dernières requêtes bloquées dans querylog.json."""
    cmd = [
        "ssh",
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=5",
        f"root@{PVE_HOST}",
        f"pct exec {CTID} -- tail -n 5000 {ADGUARD_DATA}",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15)
    except Exception as exc:
        print(f"Erreur d'accès à AdGuard Home CT {CTID} sur {PVE_HOST}: {exc}", file=sys.stderr)
        return 1

    lines = proc.stdout.splitlines()
    blocked = []
    seen = set()

    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except Exception:
            continue

        result = data.get("Result", {})
        if result.get("IsFiltered"):
            domain = data.get("QH", "")
            if not domain:
                continue
            client = data.get("IP", "inconnu")
            t_iso = data.get("T", "")
            t_str = t_iso[11:19] if len(t_iso) >= 19 else t_iso
            rules = result.get("Rules", [])
            rule_text = rules[0].get("Text") if rules else f"Règle #{result.get('Reason')}"

            key = (domain, client)
            if key not in seen:
                seen.add(key)
                blocked.append({
                    "domain": domain,
                    "client": client,
                    "time": t_str,
                    "rule": rule_text,
                })
                if len(blocked) >= limit:
                    break

    if not blocked:
        print("✦ Aucun domaine bloqué récemment dans AdGuard Home.")
        return 0

    print(f"✦ Derniers domaines bloqués par AdGuard Home (CT {CTID} / 192.168.0.53) :")
    for b in blocked:
        print(f"  • {b['domain']} (Client: {b['client']}, Heure: {b['time']}, Règle: {b['rule']})")
    return 0


def unblock_domain(domain: str) -> int:
    """Ajoute une règle d'exception dans AdGuard Home et recharge la configuration."""
    clean_domain = domain.strip().lower()
    if not _DOMAIN_RE.match(clean_domain):
        print(f"Erreur: Format de domaine invalide '{domain}'", file=sys.stderr)
        return 1

    rule_line = f"@@||{clean_domain}^$important"

    # Vérification si la règle existe déjà
    check_cmd = [
        "ssh",
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=5",
        f"root@{PVE_HOST}",
        f"pct exec {CTID} -- grep -F '{rule_line}' {ADGUARD_CONF} || true",
    ]
    try:
        proc_check = subprocess.run(check_cmd, capture_output=True, text=True, check=True, timeout=10)
        if rule_line in proc_check.stdout:
            print(f"✦ Le domaine '{clean_domain}' est déjà débloqué (règle existante dans AdGuard).")
            return 0
    except Exception as exc:
        print(f"Erreur vérification règle sur {PVE_HOST}: {exc}", file=sys.stderr)
        return 1

    # Insertion de la règle d'exception dans user_rules:
    remote_script = (
        "set -euo pipefail\n"
        f"cp {ADGUARD_CONF} {ADGUARD_CONF}.bak.$(date +%s)\n"
        f"sed -i \"/^user_rules:/a \\  - '{rule_line}'\" {ADGUARD_CONF}\n"
        f"{ADGUARD_BIN} --check-config\n"
        f"{ADGUARD_BIN} -s reload\n"
    )
    apply_cmd = [
        "ssh",
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=5",
        f"root@{PVE_HOST}",
        f"pct exec {CTID} -- bash -s",
    ]
    try:
        subprocess.run(apply_cmd, input=remote_script, capture_output=True, text=True, check=True, timeout=20)
        print(f"✦ Domaine '{clean_domain}' débloqué avec succès dans AdGuard Home !")
        print(f"  • Règle ajoutée : {rule_line}")
        print(f"  • Configuration vérifiée et rechargée sans coupure DNS.")
        return 0
    except subprocess.CalledProcessError as exc:
        print(f"Erreur lors de l'application de la règle: {exc.stderr}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Erreur d'exécution: {exc}", file=sys.stderr)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Skill Gladys : AdGuard DNS Manager")
    parser.add_argument("--blocked", action="store_true", help="Lister les dernières requêtes bloquées")
    parser.add_argument("--limit", type=int, default=10, help="Nombre de domaines à afficher (défaut: 10)")
    parser.add_argument("--unblock", type=str, metavar="DOMAIN", help="Débloquer / whitelister un domaine")

    args = parser.parse_args()

    if args.unblock:
        return unblock_domain(args.unblock)
    elif args.blocked:
        return list_blocked(args.limit)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
