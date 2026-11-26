"""Skill Gladys Appris : gladys_opnsense_manager.

Superviseur & pilote pare-feu OPNsense (https://192.168.0.20) via API REST officielle :
- L0 (lecture) : santé système/passerelles/services, paquets bloqués, baux DHCP, alias.
- L2 (HIGH) : ajout/retrait d'IP dans un alias pare-feu avec rechargement contrôlé.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
import ssl
import sys
from typing import Any
import urllib.error
import urllib.request

DEFAULT_URL = "https://192.168.0.20"
DEFAULT_VAULT = Path.home() / ".config" / "lbg" / "opnsense_secrets.json"


def vault_path() -> Path:
    raw = os.environ.get("LBG_OPNSENSE_SECRETS_FILE", "").strip()
    return Path(raw) if raw else DEFAULT_VAULT


def init_vault() -> int:
    vp = vault_path()
    vp.parent.mkdir(parents=True, exist_ok=True)
    if vp.is_file():
        print(f"✦ Trousseau OPNsense déjà existant : {vp}")
        return 0
    template = {
        "url": DEFAULT_URL,
        "key": "",
        "secret": "",
        "verify_ssl": False,
    }
    vp.write_text(json.dumps(template, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    vp.chmod(0o600)
    print(f"✦ Trousseau OPNsense initialisé (chmod 600) : {vp}")
    print("  • Colle `key` et `secret` générés dans OPNsense > Système > Accès > Utilisateurs.")
    return 0


def load_config() -> dict[str, Any]:
    cfg: dict[str, Any] = {
        "url": os.environ.get("LBG_OPNSENSE_URL", DEFAULT_URL).strip() or DEFAULT_URL,
        "key": os.environ.get("LBG_OPNSENSE_KEY", "").strip(),
        "secret": os.environ.get("LBG_OPNSENSE_SECRET", "").strip(),
        "verify_ssl": False,
    }
    vp = vault_path()
    if vp.is_file():
        try:
            raw = json.loads(vp.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                for k in ("url", "key", "secret", "verify_ssl"):
                    if k in raw and raw[k] not in (None, ""):
                        cfg[k] = raw[k]
        except Exception:
            pass
    cfg["url"] = str(cfg["url"]).rstrip("/")
    return cfg


def api_call(
    endpoint: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    timeout_s: int = 10,
) -> tuple[bool, Any]:
    cfg = load_config()
    key = str(cfg.get("key") or "").strip()
    secret = str(cfg.get("secret") or "").strip()
    if not key or not secret:
        return False, f"Clés API manquantes dans {vault_path()} (lance --init-vault puis renseigne key/secret)"

    url = f"{cfg['url']}{endpoint}"
    token = base64.b64encode(f"{key}:{secret}".encode("utf-8")).decode("ascii")
    headers = {
        "Authorization": f"Basic {token}",
        "Accept": "application/json",
    }
    data_bytes = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data_bytes = json.dumps(payload).encode("utf-8")

    ctx = ssl.create_default_context()
    if not cfg.get("verify_ssl", False):
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=timeout_s) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return True, json.loads(body) if body.strip() else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:200]
        return False, f"HTTP {exc.code}: {detail}"
    except Exception as exc:
        return False, str(exc)


def show_status() -> int:
    print("✦ Contrôle OPNsense (192.168.0.20) :")
    ok_sys, sys_data = api_call("/api/core/firmware/info")
    if not ok_sys:
        print(f"  ❌ Erreur API OPNsense : {sys_data}", file=sys.stderr)
        return 1

    prod_ver = sys_data.get("product_version") or sys_data.get("product", {}).get("product_version", "?")
    print(f"  • Version OPNsense : {prod_ver}")

    ok_gw, gw_data = api_call("/api/routes/gateway/status")
    if ok_gw and isinstance(gw_data, dict):
        items = gw_data.get("items") or []
        if items:
            print("  • Passerelles :")
            for gw in items:
                name = gw.get("name", "?")
                status = gw.get("status_translated") or gw.get("status", "?")
                delay = gw.get("delay", "-")
                icon = "✅" if "online" in str(status).lower() or status == "none" else "⚠️"
                print(f"    {icon} {name:<16} : {status} (latence {delay})")

    ok_svc, svc_data = api_call("/api/core/service/search", method="POST", payload={"current": 1, "rowCount": 50})
    if ok_svc and isinstance(svc_data, dict):
        rows = svc_data.get("rows") or []
        running = sum(1 for r in rows if str(r.get("running")) in ("1", "true", "True"))
        stopped = [r.get("name", "?") for r in rows if str(r.get("running")) not in ("1", "true", "True")]
        print(f"  • Services actifs : {running}/{len(rows)}")
        if stopped:
            print(f"  • Services arrêtés : {', '.join(stopped[:10])}")
    return 0


def show_blocked(limit: int = 15) -> int:
    ok, data = api_call(f"/api/diagnostics/firewall/log?limit={max(limit * 3, 50)}")
    if not ok:
        print(f"Erreur lecture logs pare-feu : {data}", file=sys.stderr)
        return 1

    entries = data if isinstance(data, list) else []
    blocked = [e for e in entries if str(e.get("action", "")).lower() == "block"]
    if not blocked:
        print("✦ Aucun paquet bloqué récent dans les logs OPNsense.")
        return 0

    print(f"✦ {min(len(blocked), limit)} derniers paquets bloqués sur OPNsense :")
    for e in blocked[:limit]:
        ts = e.get("__timestamp__", "")
        src = e.get("src", "?")
        dst = e.get("dst", "?")
        dstport = e.get("dstport", "")
        proto = e.get("protoname", "")
        iface = e.get("interface", "")
        label = e.get("label", "")
        dst_str = f"{dst}:{dstport}" if dstport else dst
        print(f"  • [{ts}] ({iface}) {src} -> {dst_str} [{proto}] ({label})")
    return 0


def show_leases() -> int:
    ok, data = api_call("/api/dhcpv4/leases/searchLease", method="POST", payload={"current": 1, "rowCount": 100})
    if not ok:
        ok, data = api_call("/api/kea/leases4/search", method="POST", payload={"current": 1, "rowCount": 100})
    if not ok:
        print(f"Erreur lecture baux DHCP : {data}", file=sys.stderr)
        return 1

    rows = data.get("rows", []) if isinstance(data, dict) else []
    print(f"✦ Baux DHCP actifs sur OPNsense ({len(rows)}) :")
    for r in rows[:40]:
        ip = r.get("address", "?")
        host = r.get("hostname") or "(sans nom)"
        mac = r.get("mac") or r.get("hwaddr", "")
        print(f"  • {ip:<16} | {host:<24} | {mac}")
    return 0


def show_aliases() -> int:
    ok, data = api_call("/api/firewall/alias/searchItem", method="POST", payload={"current": 1, "rowCount": 100})
    if not ok:
        print(f"Erreur lecture alias : {data}", file=sys.stderr)
        return 1
    rows = data.get("rows", []) if isinstance(data, dict) else []
    print(f"✦ Alias pare-feu OPNsense ({len(rows)}) :")
    for r in rows:
        print(f"  • {r.get('name', '?'):<24} ({r.get('type', '?')}) — {r.get('description', '')}")
    return 0


def mutate_alias(alias_name: str, address: str, *, delete: bool = False) -> int:
    action = "delete" if delete else "add"
    ok, data = api_call(f"/api/firewall/alias_util/{action}/{alias_name}", method="POST", payload={"address": address})
    if not ok:
        print(f"Erreur modification alias '{alias_name}': {data}", file=sys.stderr)
        return 1
    api_call("/api/firewall/alias/reconfigure", method="POST", payload={})
    verb = "retirée de" if delete else "ajoutée à"
    print(f"✦ Adresse `{address}` {verb} l'alias OPNsense `{alias_name}` (rechargé).")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Skill Gladys : OPNsense Firewall Manager")
    parser.add_argument("--init-vault", action="store_true", help="Initialiser le trousseau API chmod 600")
    parser.add_argument("--status", action="store_true", help="Santé OPNsense, passerelles et services")
    parser.add_argument("--blocked", action="store_true", help="Afficher les derniers paquets bloqués")
    parser.add_argument("--leases", action="store_true", help="Lister les baux DHCP actifs")
    parser.add_argument("--aliases", action="store_true", help="Lister les alias pare-feu")
    parser.add_argument("--alias-add", nargs=2, metavar=("ALIAS", "IP"), help="Ajouter une IP à un alias (L2)")
    parser.add_argument("--alias-del", nargs=2, metavar=("ALIAS", "IP"), help="Retirer une IP d'un alias (L2)")
    parser.add_argument("--limit", type=int, default=15, help="Nombre d'entrées à afficher")

    args = parser.parse_args()
    if args.init_vault:
        return init_vault()
    if args.status:
        return show_status()
    if args.blocked:
        return show_blocked(limit=args.limit)
    if args.leases:
        return show_leases()
    if args.aliases:
        return show_aliases()
    if args.alias_add:
        return mutate_alias(args.alias_add[0], args.alias_add[1], delete=False)
    if args.alias_del:
        return mutate_alias(args.alias_del[0], args.alias_del[1], delete=True)
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
