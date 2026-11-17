#!/usr/bin/env python3
"""deploy_showcase_ovh.py — Déploiement automatique du site vitrine sur OVHcloud.

Permet à Gladys de déployer les fichiers statiques de packages/showcase-web/public
vers l'hébergement web mutualisé OVH (Cluster 029 - laboiteageek.fr) via FTP/FTPS.

Usage :
  python3 deploy_showcase_ovh.py check
  python3 deploy_showcase_ovh.py deploy [--backup]
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from ftplib import FTP, FTP_TLS
from pathlib import Path

DEFAULT_FTP_HOST = "ftp.cluster029.hosting.ovh.net"
DEFAULT_TARGET_DIR = "www"

SHOWCASE_DIR = Path(__file__).resolve().parents[3] / "showcase-web" / "public"
if not SHOWCASE_DIR.is_dir():
    # Fallback chemin alternatif
    SHOWCASE_DIR = Path(__file__).resolve().parents[2] / "showcase-web" / "public"

ENV_PATHS = [
    Path("/etc/lbg/ovh_ftp.env"),
    Path("/etc/lbg/ovh.env"),
    Path(__file__).resolve().parent / "ovh_ftp.env",
    Path(__file__).resolve().parent / "ovh.env",
    Path.home() / ".config" / "lbg" / "ovh_ftp.env",
]


def load_ftp_credentials() -> dict[str, str]:
    """Charge les identifiants FTP OVH depuis l'environnement ou les fichiers de configuration."""
    creds = {
        "host": os.getenv("OVH_FTP_HOST", DEFAULT_FTP_HOST).strip(),
        "user": os.getenv("OVH_FTP_USER", "").strip(),
        "password": os.getenv("OVH_FTP_PASSWORD", "").strip(),
        "port": os.getenv("OVH_FTP_PORT", "21").strip(),
        "target_dir": os.getenv("OVH_FTP_TARGET_DIR", DEFAULT_TARGET_DIR).strip(),
    }

    if creds["user"] and creds["password"]:
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
                        if k in ("OVH_FTP_USER", "ftp_user"):
                            creds["user"] = v
                        elif k in ("OVH_FTP_PASSWORD", "ftp_password"):
                            creds["password"] = v
                        elif k in ("OVH_FTP_HOST", "ftp_host"):
                            creds["host"] = v
                        elif k in ("OVH_FTP_PORT", "ftp_port"):
                            creds["port"] = v
                        elif k in ("OVH_FTP_TARGET_DIR", "ftp_target_dir"):
                            creds["target_dir"] = v
                        elif k in ("OVH_FTP_USER_ALT", "ftp_user_alt"):
                            creds["user_alt"] = v
                        elif k in ("OVH_FTP_PASSWORD_ALT", "ftp_password_alt"):
                            creds["password_alt"] = v
                if creds["user"] and creds["password"]:
                    break
            except Exception:
                pass

    return creds


def connect_ftp(creds: dict[str, str]) -> FTP:
    """Établit la connexion FTP/FTPS avec l'hébergement OVH (avec fallback multi-comptes)."""
    host = creds["host"]
    port = int(creds.get("port", 21))

    candidates = [
        (creds["user"], creds["password"]),
    ]
    if creds.get("user_alt") and creds.get("password_alt"):
        candidates.append((creds["user_alt"], creds["password_alt"]))

    last_err = None
    for user, password in candidates:
        if not user or not password:
            continue
        try:
            ftp = FTP_TLS()
            ftp.connect(host, port, timeout=20)
            ftp.login(user, password)
            ftp.prot_p()
            return ftp
        except Exception:
            try:
                ftp = FTP()
                ftp.connect(host, port, timeout=20)
                ftp.login(user, password)
                return ftp
            except Exception as e:
                last_err = e

    raise last_err or ValueError("Aucun identifiant FTP valide configuré.")


def cmd_check(args: argparse.Namespace) -> int:
    """Vérifie la connexion FTP et liste le contenu actuel du dossier web OVH."""
    creds = load_ftp_credentials()
    if not creds["user"] or not creds["password"]:
        print("❌ Identifiants FTP non configurés.")
        print("Veuillez renseigner OVH_FTP_USER et OVH_FTP_PASSWORD dans /etc/lbg/ovh_ftp.env.")
        print(f"Hôte par défaut : {DEFAULT_FTP_HOST}")
        return 1

    print(f"📡 Test de connexion FTP vers {creds['host']} (Utilisateur: {creds['user']})...")
    try:
        ftp = connect_ftp(creds)
        print("✅ Connexion FTP établie avec succès !")
        
        target = creds["target_dir"]
        try:
            ftp.cwd(target)
            print(f"📂 Répertoire de publication trouvé : /{target}")
        except Exception:
            print(f"ℹ️ Répertoire /{target} non trouvé, utilisation de la racine.")

        files = []
        ftp.retrlines("LIST", files.append)
        print(f"\nFichiers distants actuels ({len(files)} éléments) :")
        for f in files[:10]:
            print(f"  {f}")
        if len(files) > 10:
            print(f"  ... et {len(files) - 10} autres éléments.")

        ftp.quit()
        return 0
    except Exception as e:
        print(f"❌ Échec de la connexion FTP : {e}")
        return 1


def upload_directory(ftp: FTP, local_dir: Path) -> int:
    """Envoie récursivement un dossier local vers le répertoire courant distant."""
    count = 0
    for item in local_dir.rglob("*"):
        if item.is_file():
            rel_path = item.relative_to(local_dir)
            remote_dirs = rel_path.parts[:-1]
            filename = rel_path.parts[-1]

            # Navigation / création des sous-dossiers
            current_depth = 0
            for d in remote_dirs:
                try:
                    ftp.cwd(d)
                except Exception:
                    ftp.mkd(d)
                    ftp.cwd(d)
                current_depth += 1

            # Upload binaire du fichier
            with open(item, "rb") as fp:
                ftp.storbinary(f"STOR {filename}", fp)
            print(f"  ⬆️ Publié : {rel_path} ({round(item.stat().st_size / 1024, 1)} Ko)")
            count += 1

            # Retour au niveau initial
            for _ in range(current_depth):
                ftp.cwd("..")

    return count


def cmd_deploy(args: argparse.Namespace) -> int:
    """Déploie l'ensemble du site vitrine sur l'hébergement OVH."""
    if not SHOWCASE_DIR.is_dir():
        print(f"❌ Dossier source introuvable : {SHOWCASE_DIR}")
        return 1

    creds = load_ftp_credentials()
    if not creds["user"] or not creds["password"]:
        print("❌ Identifiants FTP non configurés dans /etc/lbg/ovh_ftp.env.")
        return 1

    print("🚀 Démarrage du déploiement du site vitrine LBG Studios...")
    print(f"Source locale  : {SHOWCASE_DIR}")
    print(f"Cible distante : {creds['host']}:/{creds['target_dir']}")

    try:
        ftp = connect_ftp(creds)
        target = creds["target_dir"]
        try:
            ftp.cwd(target)
        except Exception:
            ftp.mkd(target)
            ftp.cwd(target)

        # Upload
        total = upload_directory(ftp, SHOWCASE_DIR)
        ftp.quit()

        print(f"\n🎉 Déploiement terminé avec succès ! ({total} fichiers mis en ligne)")
        print("Le nouveau site est en ligne sur : https://laboiteageek.fr/")
        return 0
    except Exception as e:
        print(f"\n❌ Erreur lors du déploiement : {e}")
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Déploiement du site vitrine LBG Studios sur OVHcloud")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("check", help="Tester la connexion FTP OVH")
    sub.add_parser("status", help="Alias pour check")
    sub.add_parser("deploy", help="Déployer les fichiers sur le web OVH")

    args = parser.parse_args()

    if args.command in ("check", "status"):
        return cmd_check(args)
    elif args.command == "deploy":
        return cmd_deploy(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
