"""Client Freebox OS API — lecture seule (DHCP / LAN browser).

Auth : application token (HMAC-SHA1 challenge) — jamais le mot de passe Freebox.
Doc : https://dev.freebox.fr/sdk/os/
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import ssl
import time
import urllib.error
import urllib.request
from typing import Any

_DEFAULT_HOST = "192.168.0.254"
_APP_ID = "fr.lbg.cortex.freebox"
_APP_NAME = "LBG Cortex"
_APP_VERSION = "1.0.0"
_DEVICE_NAME = "lbg-omarchy"

# Hôtes lab attendus (alignés REGISTRE / LAN_ADRESSAGE_FREEBOX) — MAC en minuscules.
_EXPECTED_LEASES: dict[str, dict[str, str]] = {
    "192.168.0.10": {"mac": "04:7c:16:cd:98:a5", "label": "PC-Teome"},
    "192.168.0.51": {"mac": "00:11:32:40:be:2f", "label": "NAS_LBG"},
    "192.168.0.100": {"mac": "bc:24:11:88:e2:dd", "label": "lbg-web-100"},
    "192.168.0.110": {"mac": "bc:24:11:6b:b8:54", "label": "ollama-110"},
    "192.168.0.111": {"mac": "bc:24:11:bf:8e:ca", "label": "ollama-111"},
    "192.168.0.140": {"mac": "bc:24:11:20:7f:81", "label": "lbg-backend"},
    "192.168.0.141": {"mac": "bc:24:11:59:34:21", "label": "lbg-executor"},
    "192.168.0.143": {"mac": "bc:24:11:43:00:01", "label": "lbg-omarchy"},
    "192.168.0.200": {"mac": "f4:4d:30:67:3f:07", "label": "NUC-PROXMOX"},
    "192.168.0.201": {"mac": "c8:1f:66:bd:e4:3d", "label": "R720-LAN1"},
    "192.168.0.245": {"mac": "00:0c:29:ac:34:c8", "label": "lbg-mmo-precu"},
    "192.168.0.246": {"mac": "bc:24:11:e9:cf:8c", "label": "lbg-mmo-prime"},
    "192.168.0.251": {"mac": "ac:15:a2:02:d0:1d", "label": "TL-SG108E-SW"},
}


def _truthy(raw: str) -> bool:
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def freebox_host() -> str:
    raw = (
        os.environ.get("LBG_FREEBOX_HOST")
        or os.environ.get("LBG_NETWORK_ROUTER_HOST")
        or _DEFAULT_HOST
    ).strip()
    raw = raw.removeprefix("https://").removeprefix("http://").split("/", 1)[0]
    return raw.split(":", 1)[0] or _DEFAULT_HOST


def freebox_app_token() -> str:
    return (os.environ.get("LBG_FREEBOX_APP_TOKEN") or "").strip()


def freebox_configured() -> bool:
    return bool(freebox_app_token())


def freebox_enabled() -> bool:
    """Opt-in inventaire : token présent + LBG_FREEBOX_ENABLED≠0."""
    if not freebox_configured():
        return False
    return _truthy(os.environ.get("LBG_FREEBOX_ENABLED", "1"))


def freebox_app_id() -> str:
    return (os.environ.get("LBG_FREEBOX_APP_ID") or _APP_ID).strip() or _APP_ID


def freebox_verify_ssl() -> bool:
    return _truthy(os.environ.get("LBG_FREEBOX_VERIFY_SSL", "0"))


def discover_api(timeout_s: float = 8.0) -> dict[str, Any]:
    """GET /api_version — pas d'auth."""
    host = freebox_host()
    url = f"https://{host}/api_version"
    ctx = ssl.create_default_context()
    if not freebox_verify_ssl():
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={"Accept": "application/json"}, method="GET")
    with urllib.request.urlopen(req, timeout=timeout_s, context=ctx) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError("api_version: réponse invalide")
    return data


def _api_base(api_meta: dict[str, Any] | None = None) -> tuple[str, str]:
    """Retourne (base_url sans slash final, version maj. ex. v16)."""
    meta = api_meta or discover_api()
    host = freebox_host()
    version = str(meta.get("api_version") or "16.0")
    major = version.split(".", 1)[0] or "16"
    api_base = str(meta.get("api_base_url") or "/api/").strip()
    if not api_base.startswith("/"):
        api_base = "/" + api_base
    if not api_base.endswith("/"):
        api_base += "/"
    https_port = meta.get("https_port")
    # Sur LAN, l'API répond souvent sur 443 ; le port https_port peut être filtré.
    base = f"https://{host}{api_base}v{major}"
    _ = https_port
    return base.rstrip("/"), f"v{major}"


def _ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    if not freebox_verify_ssl():
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _request(
    method: str,
    path: str,
    *,
    json_body: dict[str, Any] | None = None,
    session_token: str | None = None,
    api_meta: dict[str, Any] | None = None,
    timeout_s: float = 15.0,
) -> dict[str, Any]:
    base, _ = _api_base(api_meta)
    path = path if path.startswith("/") else f"/{path}"
    url = f"{base}{path}"
    headers = {"Accept": "application/json"}
    if session_token:
        headers["X-Fbx-App-Auth"] = session_token
    body = None
    if json_body is not None:
        body = json.dumps(json_body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=timeout_s, context=_ssl_context()) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            status = getattr(resp, "status", 200)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        status = exc.code
        try:
            data = json.loads(raw) if raw else {}
        except json.JSONDecodeError as jexc:
            raise RuntimeError(f"Freebox {method} {path}: HTTP {status} corps invalide") from jexc
        if isinstance(data, dict) and not data.get("success"):
            err = data.get("error_code") or data.get("msg") or f"http_{status}"
            raise RuntimeError(f"Freebox {method} {path}: {err}")
        raise RuntimeError(f"Freebox {method} {path}: HTTP {status}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Freebox {method} {path}: {exc}") from exc
    try:
        data = json.loads(raw) if raw else {}
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Freebox {method} {path}: JSON invalide ({status})") from exc
    if not isinstance(data, dict):
        raise RuntimeError(f"Freebox {method} {path}: corps non-objet")
    if not data.get("success"):
        err = data.get("error_code") or data.get("msg") or "unknown"
        raise RuntimeError(f"Freebox {method} {path}: {err}")
    return data


def request_authorization(
    *,
    app_id: str | None = None,
    app_name: str = _APP_NAME,
    app_version: str = _APP_VERSION,
    device_name: str | None = None,
) -> dict[str, Any]:
    """POST /login/authorize/ — déclenche le prompt sur l'écran Freebox."""
    meta = discover_api()
    body = {
        "app_id": app_id or freebox_app_id(),
        "app_name": app_name,
        "app_version": app_version,
        "device_name": device_name or os.environ.get("LBG_FREEBOX_DEVICE_NAME") or _DEVICE_NAME,
    }
    data = _request("POST", "/login/authorize/", json_body=body, api_meta=meta)
    result = data.get("result") if isinstance(data.get("result"), dict) else {}
    return {
        "ok": True,
        "app_token": str(result.get("app_token") or ""),
        "track_id": result.get("track_id"),
        "api_meta": meta,
        "app_id": body["app_id"],
    }


def poll_authorization(
    track_id: int | str,
    *,
    api_meta: dict[str, Any] | None = None,
    timeout_s: float = 180.0,
    interval_s: float = 2.0,
) -> dict[str, Any]:
    """Poll GET /login/authorize/{track_id} jusqu'à granted / denied / timeout."""
    meta = api_meta or discover_api()
    deadline = time.time() + max(5.0, timeout_s)
    last_status = "unknown"
    while time.time() < deadline:
        data = _request("GET", f"/login/authorize/{track_id}", api_meta=meta)
        result = data.get("result") if isinstance(data.get("result"), dict) else {}
        status = str(result.get("status") or "").lower()
        last_status = status or last_status
        if status == "granted":
            return {"ok": True, "status": status, "result": result}
        if status in {"denied", "timeout", "unknown"}:
            return {"ok": False, "status": status, "result": result}
        # pending / pending_timeout…
        time.sleep(interval_s)
    return {"ok": False, "status": "poll_timeout", "last_status": last_status}


def open_session(
    *,
    app_token: str | None = None,
    app_id: str | None = None,
    api_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Challenge + HMAC-SHA1 → session_token."""
    token = (app_token or freebox_app_token()).strip()
    if not token:
        raise ValueError("LBG_FREEBOX_APP_TOKEN manquant")
    aid = app_id or freebox_app_id()
    meta = api_meta or discover_api()
    login = _request("GET", "/login/", api_meta=meta)
    challenge = str((login.get("result") or {}).get("challenge") or "")
    if not challenge:
        raise RuntimeError("Freebox login: challenge absent")
    password = hmac.new(token.encode("utf-8"), challenge.encode("utf-8"), hashlib.sha1).hexdigest()
    sess = _request(
        "POST",
        "/login/session/",
        json_body={"app_id": aid, "password": password},
        api_meta=meta,
    )
    result = sess.get("result") if isinstance(sess.get("result"), dict) else {}
    session_token = str(result.get("session_token") or "")
    if not session_token:
        raise RuntimeError("Freebox session: session_token absent")
    return {
        "ok": True,
        "session_token": session_token,
        "permissions": result.get("permissions") or {},
        "api_meta": meta,
    }


def close_session(session_token: str, *, api_meta: dict[str, Any] | None = None) -> None:
    try:
        _request("POST", "/login/logout/", session_token=session_token, api_meta=api_meta)
    except Exception:  # noqa: BLE001 — best-effort
        return


def list_static_leases(session_token: str, *, api_meta: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    data = _request("GET", "/dhcp/static_lease/", session_token=session_token, api_meta=api_meta)
    result = data.get("result")
    if not isinstance(result, list):
        return []
    out: list[dict[str, Any]] = []
    for row in result:
        if not isinstance(row, dict):
            continue
        mac = str(row.get("mac") or "").strip().lower()
        ip = str(row.get("ip") or "").strip()
        out.append(
            {
                "id": row.get("id"),
                "mac": mac,
                "ip": ip,
                "hostname": str(row.get("hostname") or row.get("comment") or "").strip(),
                "comment": str(row.get("comment") or "").strip(),
                "enabled": row.get("enabled", True),
                "raw": row,
            }
        )
    return out


def list_lan_hosts(session_token: str, *, api_meta: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """LAN browser — interface pub (réseau local)."""
    ifaces = _request("GET", "/lan/browser/interfaces/", session_token=session_token, api_meta=api_meta)
    iface_list = ifaces.get("result") if isinstance(ifaces.get("result"), list) else []
    iface_name = "pub"
    for iface in iface_list:
        if isinstance(iface, dict) and iface.get("name"):
            # Prefer primary / pub
            name = str(iface["name"])
            if name == "pub" or iface.get("primary"):
                iface_name = name
                break
            iface_name = name
    data = _request("GET", f"/lan/browser/{iface_name}/", session_token=session_token, api_meta=api_meta)
    result = data.get("result")
    if not isinstance(result, list):
        return []
    hosts: list[dict[str, Any]] = []
    for row in result:
        if not isinstance(row, dict):
            continue
        l2 = row.get("l2ident") if isinstance(row.get("l2ident"), dict) else {}
        mac = str(l2.get("id") or "").strip().lower()
        names = row.get("names") if isinstance(row.get("names"), list) else []
        primary_name = ""
        for n in names:
            if isinstance(n, dict) and n.get("name"):
                primary_name = str(n["name"])
                break
        addrs = row.get("l3connectivities") if isinstance(row.get("l3connectivities"), list) else []
        ipv4s: list[str] = []
        for a in addrs:
            if not isinstance(a, dict):
                continue
            if str(a.get("af") or "").upper() in {"IPV4", "AF_INET", "4"} or a.get("addr"):
                addr = str(a.get("addr") or "").strip()
                if addr and ":" not in addr:
                    ipv4s.append(addr)
        hosts.append(
            {
                "id": row.get("id"),
                "mac": mac,
                "name": primary_name or str(row.get("primary_name") or ""),
                "reachable": bool(row.get("reachable")),
                "active": bool(row.get("active")),
                "ipv4": ipv4s,
                "vendor": str((row.get("vendor_name") or "")).strip(),
            }
        )
    return hosts


def expected_leases() -> dict[str, dict[str, str]]:
    raw = os.environ.get("LBG_FREEBOX_EXPECTED_LEASES", "").strip()
    if raw:
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                out: dict[str, dict[str, str]] = {}
                for ip, meta in data.items():
                    if isinstance(meta, dict):
                        out[str(ip)] = {
                            "mac": str(meta.get("mac") or "").lower(),
                            "label": str(meta.get("label") or ""),
                        }
                    elif isinstance(meta, str):
                        out[str(ip)] = {"mac": meta.lower(), "label": ""}
                if out:
                    return out
        except json.JSONDecodeError:
            pass
    return dict(_EXPECTED_LEASES)


def audit_static_leases(leases: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare baux Freebox ↔ plan lab (REGISTRE)."""
    by_ip = {str(r.get("ip") or ""): r for r in leases if r.get("ip")}
    expected = expected_leases()
    ok_rows: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    mac_mismatch: list[dict[str, Any]] = []
    for ip, meta in sorted(expected.items(), key=lambda x: x[0]):
        want_mac = meta["mac"]
        label = meta.get("label") or ip
        got = by_ip.get(ip)
        if not got:
            missing.append({"ip": ip, "label": label, "expected_mac": want_mac})
            continue
        got_mac = str(got.get("mac") or "").lower()
        row = {
            "ip": ip,
            "label": label,
            "expected_mac": want_mac,
            "freebox_mac": got_mac,
            "hostname": got.get("hostname") or got.get("comment"),
        }
        if want_mac and got_mac and want_mac != got_mac:
            mac_mismatch.append(row)
        else:
            ok_rows.append(row)
    extra = [
        r
        for ip, r in by_ip.items()
        if ip not in expected and ip.startswith("192.168.0.")
    ]
    return {
        "ok": not missing and not mac_mismatch,
        "n_ok": len(ok_rows),
        "n_missing": len(missing),
        "n_mac_mismatch": len(mac_mismatch),
        "n_extra": len(extra),
        "ok_rows": ok_rows,
        "missing": missing,
        "mac_mismatch": mac_mismatch,
        "extra": [
            {"ip": r.get("ip"), "mac": r.get("mac"), "hostname": r.get("hostname") or r.get("comment")}
            for r in extra
        ],
    }


def probe_freebox(*, include_lan: bool = True) -> dict[str, Any]:
    """Point d'entrée inventaire / smoke — read-only."""
    if not freebox_configured():
        return {
            "ok": False,
            "configured": False,
            "error": "freebox_not_configured",
            "hint": "Définir LBG_FREEBOX_APP_TOKEN (voir authorize_freebox_app.sh)",
        }
    try:
        meta = discover_api()
        sess = open_session(api_meta=meta)
        token = sess["session_token"]
        try:
            leases = list_static_leases(token, api_meta=meta)
            audit = audit_static_leases(leases)
            lan_hosts: list[dict[str, Any]] = []
            if include_lan:
                try:
                    lan_hosts = list_lan_hosts(token, api_meta=meta)
                except Exception as exc:  # noqa: BLE001
                    lan_hosts = []
                    audit = {**audit, "lan_error": str(exc)}
            return {
                "ok": bool(audit.get("ok")),
                "configured": True,
                "box_model": meta.get("box_model_name") or meta.get("box_model"),
                "api_version": meta.get("api_version"),
                "device_name": meta.get("device_name"),
                "permissions": sess.get("permissions") or {},
                "n_leases": len(leases),
                "leases": [
                    {"ip": r.get("ip"), "mac": r.get("mac"), "hostname": r.get("hostname") or r.get("comment")}
                    for r in leases
                ],
                "audit": audit,
                "n_lan_hosts": len(lan_hosts),
                "lan_hosts": lan_hosts,
                "lan_hosts_sample": lan_hosts[:40],
            }
        finally:
            close_session(token, api_meta=meta)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "configured": True, "error": str(exc)}


def format_audit_text(probe: dict[str, Any]) -> str:
    if not probe.get("configured"):
        return "Freebox API : non configurée (pas de LBG_FREEBOX_APP_TOKEN)."
    if probe.get("error") and "audit" not in probe:
        return f"Freebox API : erreur — {probe.get('error')}"
    lines = [
        f"Freebox {probe.get('box_model') or '?'} API {probe.get('api_version') or '?'} — "
        f"{probe.get('n_leases', 0)} bail(s) statique(s)",
    ]
    audit = probe.get("audit") if isinstance(probe.get("audit"), dict) else {}
    lines.append(
        f"Audit lab : OK={audit.get('n_ok', 0)} · manquants={audit.get('n_missing', 0)} · "
        f"MAC≠={audit.get('n_mac_mismatch', 0)} · extra={audit.get('n_extra', 0)}"
    )
    for row in audit.get("missing") or []:
        lines.append(f"  ✗ manquant {row.get('ip')} ({row.get('label')}) MAC {row.get('expected_mac')}")
    for row in audit.get("mac_mismatch") or []:
        lines.append(
            f"  ✗ MAC {row.get('ip')} want={row.get('expected_mac')} got={row.get('freebox_mac')}"
        )
    for row in (audit.get("ok_rows") or [])[:8]:
        lines.append(f"  ✓ {row.get('ip')} {row.get('label')}")
    if len(audit.get("ok_rows") or []) > 8:
        lines.append(f"  … +{len(audit['ok_rows']) - 8} OK")
    return "\n".join(lines)
