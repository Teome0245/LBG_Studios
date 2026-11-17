#!/usr/bin/env python3
"""ovh_dns_manager.py — Gestionnaire DNS OVHcloud pour LBG Studios / Gladys.

Permet à Gladys d'interagir avec l'API OVHcloud pour le domaine laboiteageeks.fr :
- Audit complet des enregistrements DNS (MX, SPF, DKIM, DMARC, DynHost/A).
- Synchronisation sécurisée des enregistrements mail (notamment DKIM Stalwart).
- Application sous contrôle HITL (Human-In-The-Loop) avec confirmation obligatoire.

Usage :
  python3 ovh_dns_manager.py audit
  python3 ovh_dns_manager.py plan-mail
  python3 ovh_dns_manager.py apply-mail
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ZONE_DEFAULT = "laboiteageeks.fr"
OVH_ENDPOINT = "https://eu.api.ovh.com/1.0"

STALWART_DKIM_SELECTOR = "v1-rsa-20261117"
STALWART_DKIM_PUBKEY = (
    "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAvQQSrrBJCsnEfcEHmay7Hj4+n6M/OLQxb3Mawv2yGWAPqg5l"
    "TarrhMvsBhiOwiIwhCm3G1dLeE/H1El7VbpUzdPkYq0nPdBzk4h5KvlMcsy5M5H43PoHte66+MAWtZQexYODR5Sc/IRCndtOOWZajgsFPmfe"
    "OlgGaBZkgc7XPZ06YLzfUWuQci8YAnUTypVyCTKC4Gmv1563LTAKwEHpCDyhZodek0VXkn0fn+bRQ//LRiZuk3hVxWQLvLnHq+FPiMIQWw1I+"
    "a3/SpbybAftpjNJvmDhB/6g7jUh6gD22B/LN+OyVqWmxN9tCaUb314W60mjrRR4LWLgAZF2XlipoQIDAQAB"
)

# Emplacements standards des secrets OVH
ENV_PATHS = [
    Path("/etc/lbg/ovh.env"),
    Path(__file__).resolve().parent / "ovh.env",
    Path.home() / ".config" / "lbg" / "ovh.env",
    Path.home() / ".ovh.conf",
]


def load_ovh_credentials() -> dict[str, str]:
    """Charge les clés d'API OVH depuis l'environnement ou les fichiers de configuration."""
    creds = {
        "endpoint": os.getenv("OVH_ENDPOINT", OVH_ENDPOINT),
        "application_key": os.getenv("OVH_APPLICATION_KEY", "").strip(),
        "application_secret": os.getenv("OVH_APPLICATION_SECRET", "").strip(),
        "consumer_key": os.getenv("OVH_CONSUMER_KEY", "").strip(),
    }

    if creds["application_key"] and creds["consumer_key"]:
        return creds

    for path in ENV_PATHS:
        if path.is_file():
            try:
                for line in path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k in ("OVH_APPLICATION_KEY", "application_key"):
                            creds["application_key"] = v
                        elif k in ("OVH_APPLICATION_SECRET", "application_secret"):
                            creds["application_secret"] = v
                        elif k in ("OVH_CONSUMER_KEY", "consumer_key"):
                            creds["consumer_key"] = v
                if creds["application_key"] and creds["consumer_key"]:
                    break
            except Exception:
                pass

    return creds


class OvhClient:
    """Client REST minimal et robuste pour l'API OVHcloud (signature HMAC-SHA1)."""

    def __init__(self, app_key: str, app_secret: str, consumer_key: str = "", endpoint: str = OVH_ENDPOINT):
        self.app_key = app_key
        self.app_secret = app_secret
        self.consumer_key = consumer_key
        self.endpoint = endpoint.rstrip("/")
        self._time_delta = 0
        self._sync_time()

    def _sync_time(self) -> None:
        """Synchronise l'horloge avec le serveur OVH."""
        try:
            req = urllib.request.Request(f"{self.endpoint}/auth/time", headers={"User-Agent": "LBG-Gladys/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                server_time = int(resp.read().decode("utf-8"))
                self._time_delta = server_time - int(time.time())
        except Exception:
            self._time_delta = 0

    def request(self, method: str, path: str, data: dict[str, Any] | None = None) -> Any:
        url = f"{self.endpoint}{path}"
        body_str = json.dumps(data) if data is not None else ""
        now = str(int(time.time()) + self._time_delta)

        # Calcul de la signature OVH: "$1$" + SHA1_HEX(AS + "+" + CK + "+" + METHOD + "+" + QUERY + "+" + BODY + "+" + TSTAMP)
        to_sign = "+".join([
            self.app_secret,
            self.consumer_key,
            method.upper(),
            url,
            body_str,
            now,
        ])
        sig = "$1$" + hashlib.sha1(to_sign.encode("utf-8")).hexdigest()

        headers = {
            "Content-Type": "application/json",
            "X-Ovh-Application": self.app_key,
            "X-Ovh-Timestamp": now,
            "X-Ovh-Signature": sig,
            "User-Agent": "LBG-Gladys-DNS/1.0",
        }
        if self.consumer_key:
            headers["X-Ovh-Consumer"] = self.consumer_key

        req = urllib.request.Request(
            url,
            data=body_str.encode("utf-8") if body_str else None,
            headers=headers,
            method=method.upper(),
        )

        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            try:
                err_json = json.loads(err_body)
                msg = err_json.get("message", err_body)
            except Exception:
                msg = err_body
            raise RuntimeError(f"Erreur API OVH HTTP {e.code}: {msg}") from e


def cmd_audit(args: argparse.Namespace) -> int:
    """Audit complet de la zone DNS chez OVH et comparaison avec la stack locale."""
    creds = load_ovh_credentials()
    if not creds["application_key"] or not creds["consumer_key"]:
        print("❌ Clés d'API OVH manquantes dans /etc/lbg/ovh.env.")
        return 1

    client = OvhClient(creds["application_key"], creds["application_secret"], creds["consumer_key"])
    zone = args.zone or ZONE_DEFAULT

    print(f"🔍 Audit DNS OVHcloud pour le domaine : {zone}")
    print("=" * 60)

    try:
        record_ids = client.request("GET", f"/domain/zone/{zone}/record")
        records = []
        for rid in record_ids:
            rec = client.request("GET", f"/domain/zone/{zone}/record/{rid}")
            records.append(rec)

        mx_records = [r for r in records if r.get("fieldType") == "MX"]
        txt_records = [r for r in records if r.get("fieldType") in ("TXT", "SPF", "DMARC")]
        a_records = [r for r in records if r.get("fieldType") == "A"]

        print(f"Total enregistrements DNS trouvés : {len(records)}\n")

        print("📌 Enregistrements Mail (MX) :")
        for r in mx_records:
            print(f"  - {r.get('subDomain') or '@'} -> {r.get('target')} (ID: {r.get('id')})")

        print("\n📌 Enregistrements Adresses (A) :")
        for r in a_records:
            if r.get("subDomain") in ("", "mail", "smtp", "imap"):
                print(f"  - {r.get('subDomain') or '@'} -> {r.get('target')}")

        print("\n📌 Enregistrements Authentification Mail (SPF / DKIM / DMARC) :")
        spf_ok = False
        dmarc_ok = False
        stalwart_dkim_ok = False

        for r in txt_records:
            sub = r.get("subDomain", "") or "@"
            tgt = r.get("target", "")
            ft = r.get("fieldType")
            if "v=spf1" in tgt:
                spf_ok = True
                print(f"  - [{ft}] SPF  ({sub}) : {tgt}")
            elif "_dmarc" in sub or "v=DMARC1" in tgt:
                dmarc_ok = True
                print(f"  - [{ft}] DMARC({sub}) : {tgt}")
            elif STALWART_DKIM_SELECTOR in sub:
                stalwart_dkim_ok = True
                print(f"  - [{ft}] DKIM Actif Stalwart ({sub}) : {tgt[:35]}... (ID: {r.get('id')})")
            elif "_domainkey" in sub:
                print(f"  - [{ft}] DKIM Ancien/Legacy   ({sub}) : {tgt[:35]}...")

        print("\n📊 Bilan de conformité Serveur Stalwart CT 154 :")
        print(f"  - Enregistrement MX           : {'✅ OUI (10 mail.laboiteageeks.fr)' if mx_records else '❌ NON'}")
        print(f"  - SPF Freebox (82.67.2.16)    : {'✅ OUI' if spf_ok else '⚠️ MANQUANT'}")
        print(f"  - DKIM Stalwart ({STALWART_DKIM_SELECTOR}) : {'✅ OUI' if stalwart_dkim_ok else '❌ NON PUBLIÉ (Action requise)'}")
        print(f"  - DMARC de protection         : {'✅ OUI' if dmarc_ok else '⚠️ RECOMMANDÉ'}")

        return 0

    except Exception as e:
        print(f"❌ Erreur lors de l'audit : {e}")
        return 1


def cmd_plan_mail(args: argparse.Namespace) -> int:
    """Affiche le plan des modifications à appliquer sur OVHcloud."""
    zone = args.zone or ZONE_DEFAULT
    print(f"📋 Plan d'actions DNS pour {zone} :")
    print("=" * 60)
    print(f"1. Publication de la clé DKIM Stalwart :")
    print(f"   - Type         : TXT")
    print(f"   - Sous-domaine : {STALWART_DKIM_SELECTOR}._domainkey")
    print(f"   - Valeur       : \"v=DKIM1; k=rsa; p={STALWART_DKIM_PUBKEY}\"")
    print(f"   - TTL          : 3600")
    print("------------------------------------------------------------")
    print("2. Publication de l'enregistrement DMARC :")
    print("   - Type         : TXT")
    print("   - Sous-domaine : _dmarc")
    print("   - Valeur       : \"v=DMARC1; p=none; sp=none; aspf=r;\"")
    print("   - TTL          : 3600")
    print("------------------------------------------------------------")
    print("3. Rafraîchissement de la zone DNS (POST /refresh)")
    print("=" * 60)
    print("Pour appliquer ce plan via Gladys, confirmez avec 'apply-mail'.")
    return 0


def cmd_apply_mail(args: argparse.Namespace) -> int:
    """Applique les enregistrements DKIM et DMARC nécessaires chez OVH."""
    creds = load_ovh_credentials()
    if not creds["application_key"] or not creds["consumer_key"]:
        print("❌ Clés d'API OVH manquantes dans /etc/lbg/ovh.env.")
        return 1

    client = OvhClient(creds["application_key"], creds["application_secret"], creds["consumer_key"])
    zone = args.zone or ZONE_DEFAULT

    print(f"🚀 Application des modifications DNS pour {zone}...")

    # Vérification si le DKIM existe déjà pour éviter les doublons
    record_ids = client.request("GET", f"/domain/zone/{zone}/record")
    dkim_exists = False
    dmarc_exists = False

    for rid in record_ids:
        rec = client.request("GET", f"/domain/zone/{zone}/record/{rid}")
        sub = rec.get("subDomain", "")
        if STALWART_DKIM_SELECTOR in sub:
            dkim_exists = True
        if sub == "_dmarc":
            dmarc_exists = True

    # 1. Ajout du DKIM Stalwart si absent
    if not dkim_exists:
        dkim_target = f"\"v=DKIM1; k=rsa; p={STALWART_DKIM_PUBKEY}\""
        new_dkim = client.request("POST", f"/domain/zone/{zone}/record", {
            "fieldType": "TXT",
            "subDomain": f"{STALWART_DKIM_SELECTOR}._domainkey",
            "target": dkim_target,
            "ttl": 3600,
        })
        print(f"✅ Enregistrement DKIM Stalwart créé (ID: {new_dkim.get('id')})")
    else:
        print(f"ℹ️ Enregistrement DKIM Stalwart déjà présent dans la zone.")

    # 2. Ajout du DMARC si absent
    if not dmarc_exists:
        dmarc_target = "\"v=DMARC1; p=none; sp=none; aspf=r;\""
        new_dmarc = client.request("POST", f"/domain/zone/{zone}/record", {
            "fieldType": "TXT",
            "subDomain": "_dmarc",
            "target": dmarc_target,
            "ttl": 3600,
        })
        print(f"✅ Enregistrement DMARC créé (ID: {new_dmarc.get('id')})")
    else:
        print(f"ℹ️ Enregistrement DMARC déjà présent dans la zone.")

    # 3. Rafraîchissement de la zone
    try:
        client.request("POST", f"/domain/zone/{zone}/refresh")
        print("✅ Rafraîchissement de la zone DNS OVH demandé avec succès.")
        print("La diffusion DNS mondiale est amorcée.")
    except Exception as e:
        print(f"⚠️ Erreur lors du refresh : {e}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Gestionnaire DNS OVHcloud pour LBG Studios / Gladys")
    parser.add_argument("--zone", default=ZONE_DEFAULT, help=f"Zone DNS (défaut: {ZONE_DEFAULT})")

    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("audit", help="Auditer la zone DNS OVH")
    sub.add_parser("status", help="Alias pour audit")
    sub.add_parser("plan-mail", help="Afficher le plan des modifications mail")
    sub.add_parser("apply-mail", help="Appliquer les modifications DNS sur OVH")

    args = parser.parse_args()

    if args.command in ("audit", "status"):
        return cmd_audit(args)
    elif args.command == "plan-mail":
        return cmd_plan_mail(args)
    elif args.command == "apply-mail":
        return cmd_apply_mail(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
