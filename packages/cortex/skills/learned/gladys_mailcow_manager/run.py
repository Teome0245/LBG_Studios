"""Skill Gladys Appris : gladys_mailcow_manager.

Gestionnaire & Superviseur Mailcow / SOGo (mail.laboiteageeks.fr) :
- Contrôle de santé des conteneurs Mailcow et de la file d'attente Postfix (CT 155 / 192.168.0.155).
- Relève et synthèse des courriers non lus (Dovecot).
- Synthèse intelligente pour le compte-rendu matinal (Morning Brief).
"""

from __future__ import annotations

import argparse
from email.header import decode_header, make_header
from email.parser import BytesParser
from email import policy
import imaplib
import json
import os
from pathlib import Path
import re
import ssl
import subprocess
import sys
from typing import Any
import urllib.request

PVE_HOST = "192.168.0.201"
CTID = "155"
DEFAULT_USER = "sdesharches@laboiteageeks.fr"
DESKTOP_AGENT_URL = os.environ.get("LBG_AGENT_DESKTOP_URL", "http://192.168.0.10:5005").rstrip("/")
ACCOUNTS_FILE = Path(__file__).resolve().parent / "accounts.json"
DEFAULT_VAULT_FILE = Path.home() / ".config" / "lbg" / "mail_secrets.json"


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


def load_accounts() -> list[dict[str, Any]]:
    """Charge le catalogue des 9 boîtes (Mailcow local + 8 externes)."""
    if not ACCOUNTS_FILE.is_file():
        return []
    try:
        data = json.loads(ACCOUNTS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def vault_path() -> Path:
    raw = os.environ.get("LBG_MAIL_SECRETS_FILE", "").strip()
    return Path(raw) if raw else DEFAULT_VAULT_FILE


def load_secrets() -> dict[str, str]:
    """Charge les mots de passe depuis le trousseau local (chmod 600) ou env."""
    secrets: dict[str, str] = {}
    vp = vault_path()
    if vp.is_file():
        try:
            raw = json.loads(vp.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                for k, v in raw.items():
                    if isinstance(v, str) and v.strip():
                        secrets[str(k)] = v.strip()
        except Exception:
            pass
    for acc in load_accounts():
        acc_id = str(acc.get("id") or "")
        env_key = f"LBG_MAIL_PW_{acc_id.upper()}"
        val = os.environ.get(env_key, "").strip()
        if val:
            secrets[acc_id] = val
    return secrets


def init_vault() -> int:
    """Crée un modèle sécurisé (chmod 600) pour renseigner les mots de passe IMAP."""
    vp = vault_path()
    vp.parent.mkdir(parents=True, exist_ok=True)
    existing = load_secrets()
    template: dict[str, str] = {}
    for acc in load_accounts():
        if acc.get("type") == "external_imap":
            acc_id = str(acc.get("id") or "")
            template[acc_id] = existing.get(acc_id, "")
    vp.write_text(json.dumps(template, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    vp.chmod(0o600)
    print(f"✦ Trousseau IMAP initialisé (chmod 600) : {vp}")
    print("  • Renseigne les mots de passe (ou mots de passe d'application pour Gmail) dans ce fichier.")
    return 0


def _decode_hdr(raw: str) -> str:
    if not raw:
        return ""
    try:
        return str(make_header(decode_header(raw)))
    except Exception:
        return raw


def check_imap_account(acc: dict[str, Any], password: str, limit: int = 5) -> dict[str, Any]:
    """Méthode 2 (Secours / Direct) : relève les non lus d'une boîte IMAP SSL."""
    host = str(acc.get("host") or "")
    port = int(acc.get("port") or 993)
    user = str(acc.get("email") or "")
    try:
        ctx = ssl.create_default_context()
        with imaplib.IMAP4_SSL(host, port, ssl_context=ctx, timeout=10) as client:
            client.login(user, password)
            client.select("INBOX", readonly=True)
            typ, data = client.search(None, "UNSEEN")
            if typ != "OK" or not data or not data[0]:
                return {"ok": True, "unseen": 0, "messages": []}
            ids = data[0].split()
            unseen = len(ids)
            recent_ids = list(reversed(ids[-limit:]))
            messages = []
            for msg_id in recent_ids:
                ftyp, fdata = client.fetch(msg_id, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
                if ftyp != "OK" or not fdata:
                    continue
                for part in fdata:
                    if isinstance(part, tuple) and len(part) >= 2 and isinstance(part[1], bytes):
                        parsed = BytesParser(policy=policy.compat32).parsebytes(part[1])
                        messages.append({
                            "date": _decode_hdr(parsed.get("Date", "") or ""),
                            "from": _decode_hdr(parsed.get("From", "") or ""),
                            "subject": _decode_hdr(parsed.get("Subject", "") or ""),
                        })
                        break
            return {"ok": True, "unseen": unseen, "messages": messages}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "unseen": 0, "messages": []}


def show_sync_plan() -> int:
    """Affiche le plan prêt-à-l'emploi pour les Sync Jobs Mailcow (Méthode 1)."""
    accounts = load_accounts()
    secrets = load_secrets()
    print("✦ Plan de synchronisation Mailcow (Méthode 1 — imapsync) :")
    print("  Interface : https://mail.laboiteageeks.fr/admin/ > Configuration > E-Mail > Sync Jobs")
    print(f"  Trousseau local (Méthode 2 secours) : {vault_path()}")
    print()
    for acc in accounts:
        if acc.get("type") != "external_imap":
            continue
        acc_id = str(acc.get("id") or "")
        has_pw = "🔑 Secret présent" if acc_id in secrets else "⚪ Mot de passe à renseigner"
        print(
            f"  • {acc['email']:<34} | {acc['host']}:{acc['port']} (SSL) "
            f"-> Dossier: {acc['destination_folder']:<18} | {has_pw}"
        )
    return 0


def run_multi_fallback(limit: int = 5) -> int:
    """Interroge en direct (Méthode 2) toutes les boîtes ayant un mot de passe configuré."""
    accounts = load_accounts()
    secrets = load_secrets()
    print("✦ Relève multi-boîtes IMAP directe (Méthode 2 / Secours) :")
    any_checked = False
    for acc in accounts:
        if acc.get("type") != "external_imap":
            continue
        acc_id = str(acc.get("id") or "")
        pw = secrets.get(acc_id, "")
        if not pw:
            print(f"  ⚪ {acc['email']:<34} — En attente de mot de passe dans {vault_path()}")
            continue
        any_checked = True
        res = check_imap_account(acc, pw, limit=limit)
        if not res["ok"]:
            print(f"  ❌ {acc['email']:<34} — Erreur IMAP : {res['error']}")
            continue
        print(f"  🟢 {acc['email']:<34} — {res['unseen']} non lu(s)")
        for m in res["messages"]:
            print(f"      ✉️ [{m['date']}] {m['from']} — \"{m['subject']}\"")
    if not any_checked:
        print(f"  ℹ️  Aucun mot de passe configuré. Lance `--init-vault` pour créer {vault_path()}.")
    return 0


def check_thunderbird_desktop(limit: int = 10) -> int:
    """Interroge en lecture seule l'index Thunderbird sur le poste Windows (.10:5005)."""
    data: dict[str, Any] | None = None
    try:
        req = urllib.request.Request(
            f"{DESKTOP_AGENT_URL}/execute",
            data=json.dumps({"action": "read_thunderbird_recent", "params": {"limit": int(limit)}}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
            data = raw.get("result") if isinstance(raw, dict) and "result" in raw else raw
    except Exception:
        print(f"✦ Thunderbird (.10:5005) : poste/agent hors ligne ({DESKTOP_AGENT_URL})")
        return 1

    if not isinstance(data, dict) or not data.get("ok"):
        err = data.get("error", "indisponible") if isinstance(data, dict) else "réponse invalide"
        print(f"✦ Thunderbird (.10:5005) : {err}")
        return 1

    msgs = data.get("messages", [])
    print(f"✦ Thunderbird en direct ({data.get('profile', 'profil')}) — {min(len(msgs), limit)} derniers messages :")
    for m in msgs[:limit]:
        acc = str(m.get("account", "")).replace("@imap.", "@")
        sender = str(m.get("from", "")).removesuffix(" undefined").strip()
        print(f"    ✉️ [{m.get('date', '')}] ({acc}) {sender} — \"{m.get('subject', '')}\"")
    return 0


def generate_brief(user: str = DEFAULT_USER, limit: int = 5) -> int:
    """Génère une synthèse complète avec bascule automatique Méthode 2 si Mailcow est KO."""
    print("=" * 60)
    print("☕ COMPTE-RENDU SERVEUR MAIL & MESSAGERIE GLADYS")
    print("=" * 60)

    health_rc = check_health()
    print()

    if health_rc == 0:
        list_unread(user=user, limit=limit)
    else:
        print("⚠️ Mailcow CT 155 indisponible — bascule automatique sur Méthode 2 (IMAP direct) !")

    print()
    run_multi_fallback(limit=limit)
    print()
    check_thunderbird_desktop(limit=limit)
    print("=" * 60)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Skill Gladys : Mailcow & SOGo Manager")
    parser.add_argument("--health", action="store_true", help="Vérifier la santé des conteneurs Mailcow")
    parser.add_argument("--unread", action="store_true", help="Lister les courriers non lus (Mailcow local)")
    parser.add_argument("--multi", action="store_true", help="Relever en direct les boîtes externes (Méthode 2)")
    parser.add_argument("--thunderbird", action="store_true", help="Lire les derniers mails via Thunderbird (.10:5005)")
    parser.add_argument("--sync-plan", action="store_true", help="Afficher le plan Sync Jobs Mailcow (Méthode 1)")
    parser.add_argument("--init-vault", action="store_true", help="Initialiser le trousseau local chmod 600")
    parser.add_argument("--user", type=str, default=DEFAULT_USER, help=f"Utilisateur cible (défaut: {DEFAULT_USER})")
    parser.add_argument("--limit", type=int, default=10, help="Nombre de messages à afficher")
    parser.add_argument("--brief", action="store_true", help="Générer un compte-rendu complet (avec failover auto)")

    args = parser.parse_args()

    if args.init_vault:
        return init_vault()
    if args.sync_plan:
        return show_sync_plan()
    if args.health:
        return check_health()
    if args.unread:
        return list_unread(user=args.user, limit=args.limit)
    if args.multi:
        return run_multi_fallback(limit=args.limit)
    if args.thunderbird:
        return check_thunderbird_desktop(limit=args.limit)
    return generate_brief(user=args.user, limit=args.limit)


if __name__ == "__main__":
    sys.exit(main())
