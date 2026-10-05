"""Client Synology DSM WebAPI — lecture (stockage, FileStation, Download Station).

Auth DSM 7.1 : login account+passwd → SID (PAS OAuth Service / pas de PAT requis).
Secrets : LBG_NAS_USER + LBG_NAS_PASSWORD (ou LBG_NAS_TOKEN si PAT un jour).
"""

from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

_DEFAULT_HOST = "192.168.0.51"
_DEFAULT_DSM_URL = "https://192.168.0.51:5001"


def _truthy(raw: str) -> bool:
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def nas_dsm_url() -> str:
    raw = (os.environ.get("LBG_NAS_DSM_URL") or "").strip()
    if raw:
        return raw.rstrip("/")
    host = (os.environ.get("LBG_NAS_HOST") or _DEFAULT_HOST).strip()
    host = host.removeprefix("https://").removeprefix("http://").split("/", 1)[0]
    return f"https://{host.split(':', 1)[0]}:5001"


def nas_user() -> str:
    return (os.environ.get("LBG_NAS_USER") or "lbg").strip() or "lbg"


def nas_password() -> str:
    return (os.environ.get("LBG_NAS_PASSWORD") or "").strip()


def nas_token() -> str:
    """Réserve PAT DSM 7.2+ — non utilisé sur 7.1 pour l’instant."""
    return (os.environ.get("LBG_NAS_TOKEN") or "").strip()


def nas_configured() -> bool:
    return bool(nas_password() or nas_token())


def nas_enabled() -> bool:
    if not nas_configured():
        return False
    return _truthy(os.environ.get("LBG_NAS_ENABLED", "1"))


def nas_verify_ssl() -> bool:
    return _truthy(os.environ.get("LBG_NAS_VERIFY_SSL", "0"))


def _ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    if not nas_verify_ssl():
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _entry(params: dict[str, Any], *, timeout_s: float = 20.0) -> dict[str, Any]:
    """GET /webapi/entry.cgi (ou path API spécifique)."""
    api = str(params.get("api") or "")
    # Download Station legacy path
    if api.startswith("SYNO.DownloadStation"):
        path = "/webapi/DownloadStation/task.cgi" if "Task" in api else "/webapi/entry.cgi"
    else:
        path = "/webapi/entry.cgi"
    url = f"{nas_dsm_url()}{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout_s, context=_ssl_context()) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(raw) if raw else {}
        except json.JSONDecodeError as jexc:
            raise RuntimeError(f"DSM {api}: HTTP {exc.code}") from jexc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"DSM {api}: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError(f"DSM {api}: corps non-objet")
    if not data.get("success"):
        err = data.get("error") or {}
        code = err.get("code") if isinstance(err, dict) else err
        raise RuntimeError(f"DSM {api}: error={code}")
    return data


def login(*, session: str = "FileStation") -> dict[str, Any]:
    if not nas_password():
        raise ValueError("LBG_NAS_PASSWORD manquant")
    data = _entry(
        {
            "api": "SYNO.API.Auth",
            "version": "6",
            "method": "login",
            "account": nas_user(),
            "passwd": nas_password(),
            "session": session,
            "format": "sid",
        }
    )
    result = data.get("data") if isinstance(data.get("data"), dict) else {}
    sid = str(result.get("sid") or "")
    if not sid:
        raise RuntimeError("DSM login: sid absent")
    return {"ok": True, "sid": sid, "session": session, "did": result.get("did")}


def logout(sid: str, *, session: str = "FileStation") -> None:
    try:
        _entry(
            {
                "api": "SYNO.API.Auth",
                "version": "6",
                "method": "logout",
                "session": session,
                "_sid": sid,
            }
        )
    except Exception:  # noqa: BLE001
        return


def storage_load_info(sid: str) -> dict[str, Any]:
    data = _entry(
        {
            "api": "SYNO.Storage.CGI.Storage",
            "version": "1",
            "method": "load_info",
            "_sid": sid,
        }
    )
    return data.get("data") if isinstance(data.get("data"), dict) else {}


def system_utilization(sid: str) -> dict[str, Any]:
    data = _entry(
        {
            "api": "SYNO.Core.System.Utilization",
            "version": "1",
            "method": "get",
            "_sid": sid,
        }
    )
    return data.get("data") if isinstance(data.get("data"), dict) else {}


def filestation_list_shares(sid: str) -> list[dict[str, Any]]:
    data = _entry(
        {
            "api": "SYNO.FileStation.List",
            "version": "2",
            "method": "list_share",
            "_sid": sid,
        }
    )
    result = data.get("data") if isinstance(data.get("data"), dict) else {}
    shares = result.get("shares")
    if not isinstance(shares, list):
        return []
    out: list[dict[str, Any]] = []
    for row in shares:
        if not isinstance(row, dict):
            continue
        out.append(
            {
                "name": str(row.get("name") or ""),
                "path": str(row.get("path") or ""),
                "desc": str(row.get("desc") or ""),
                "readonly": bool(row.get("is_readonly") or row.get("readonly")),
                "privilege": row.get("additional") or row.get("privilege"),
            }
        )
    return out


def downloadstation_list(sid: str) -> list[dict[str, Any]]:
    """Liste les tâches Download Station (peut échouer si package off)."""
    try:
        data = _entry(
            {
                "api": "SYNO.DownloadStation.Task",
                "version": "1",
                "method": "list",
                "additional": "detail,transfer",
                "_sid": sid,
            }
        )
    except RuntimeError:
        return []
    result = data.get("data") if isinstance(data.get("data"), dict) else {}
    tasks = result.get("tasks")
    if not isinstance(tasks, list):
        return []
    out: list[dict[str, Any]] = []
    for t in tasks:
        if not isinstance(t, dict):
            continue
        size = t.get("size")
        add = t.get("additional") if isinstance(t.get("additional"), dict) else {}
        detail = add.get("detail") if isinstance(add.get("detail"), dict) else {}
        if size is None:
            size = detail.get("size")
        out.append(
            {
                "id": t.get("id"),
                "title": str(t.get("title") or ""),
                "status": str(t.get("status") or ""),
                "type": str(t.get("type") or ""),
                "size": size,
                "destination": detail.get("destination"),
            }
        )
    return out


def _summarize_storage(raw: dict[str, Any]) -> dict[str, Any]:
    volumes: list[dict[str, Any]] = []
    for key in ("volumes", "volInfo"):
        rows = raw.get(key)
        if isinstance(rows, list):
            for v in rows:
                if not isinstance(v, dict):
                    continue
                # DSM fields vary by version
                total = v.get("size_total_byte") or v.get("total") or v.get("size", {}).get("total")
                used = v.get("size_used_byte") or v.get("used") or v.get("size", {}).get("used")
                if isinstance(v.get("size"), dict):
                    total = total or v["size"].get("total")
                    used = used or v["size"].get("used")
                try:
                    total_i = int(total) if total is not None else None
                    used_i = int(used) if used is not None else None
                except (TypeError, ValueError):
                    total_i, used_i = None, None
                pct = None
                if total_i and used_i is not None and total_i > 0:
                    pct = round(100.0 * used_i / total_i, 1)
                volumes.append(
                    {
                        "id": v.get("volume") or v.get("id") or v.get("num_id") or v.get("desc"),
                        "status": v.get("status") or v.get("vol_path"),
                        "total_bytes": total_i,
                        "used_bytes": used_i,
                        "used_pct": pct,
                    }
                )
            break
    disks: list[dict[str, Any]] = []
    for key in ("disks", "diskInfo"):
        rows = raw.get(key)
        if isinstance(rows, list):
            for d in rows:
                if not isinstance(d, dict):
                    continue
                disks.append(
                    {
                        "id": d.get("id") or d.get("name") or d.get("num_id"),
                        "status": d.get("status") or d.get("smart_status"),
                        "model": d.get("model") or d.get("diskType"),
                        "temp": d.get("temp") or d.get("temperature"),
                    }
                )
            break
    return {"volumes": volumes, "disks": disks, "raw_keys": sorted(raw.keys())}


def probe_nas(*, include_downloads: bool = True) -> dict[str, Any]:
    if not nas_configured():
        return {
            "ok": False,
            "configured": False,
            "error": "nas_not_configured",
            "hint": "Définir LBG_NAS_PASSWORD dans nas.env.local / lbg.env",
        }
    try:
        sess = login()
        sid = sess["sid"]
        try:
            storage_raw = storage_load_info(sid)
            storage = _summarize_storage(storage_raw)
            util: dict[str, Any] = {}
            try:
                util = system_utilization(sid)
            except RuntimeError as exc:
                util = {"error": str(exc)}
            shares = filestation_list_shares(sid)
            tasks: list[dict[str, Any]] = []
            if include_downloads:
                tasks = downloadstation_list(sid)
            # health heuristic
            vol_warn = any(
                (v.get("used_pct") or 0) >= 85 for v in storage.get("volumes") or []
            )
            return {
                "ok": True,
                "configured": True,
                "host": nas_dsm_url(),
                "user": nas_user(),
                "storage": storage,
                "utilization": {
                    "cpu": util.get("cpu"),
                    "memory": util.get("memory"),
                    "network": util.get("network"),
                }
                if util and "error" not in util
                else util,
                "n_shares": len(shares),
                "shares": shares[:40],
                "n_download_tasks": len(tasks),
                "download_tasks": tasks[:20],
                "volume_warn": vol_warn,
            }
        finally:
            logout(sid)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "configured": True, "error": str(exc)}


def format_nas_probe_text(probe: dict[str, Any]) -> str:
    if not probe.get("configured"):
        return "NAS Synology : non configuré (pas de LBG_NAS_PASSWORD)."
    if probe.get("error") and not probe.get("storage"):
        return f"NAS Synology : erreur — {probe.get('error')}"
    lines = [f"NAS Synology {probe.get('host') or '.51'} (user={probe.get('user')})"]
    for v in (probe.get("storage") or {}).get("volumes") or []:
        pct = v.get("used_pct")
        total = v.get("total_bytes")
        used = v.get("used_bytes")
        size_s = ""
        if total and used is not None:
            size_s = f" — {used / 1e12:.1f}/{total / 1e12:.1f} To"
        mark = "⚠" if (pct or 0) >= 85 else "✓"
        lines.append(f"  {mark} volume {v.get('id')} : {pct}%{size_s} ({v.get('status')})")
    n_disks = len((probe.get("storage") or {}).get("disks") or [])
    if n_disks:
        lines.append(f"  disques : {n_disks}")
    lines.append(f"  FileStation shares : {probe.get('n_shares', 0)}")
    lines.append(f"  Download Station tâches : {probe.get('n_download_tasks', 0)}")
    util = probe.get("utilization") if isinstance(probe.get("utilization"), dict) else {}
    cpu = util.get("cpu") if isinstance(util.get("cpu"), dict) else None
    if cpu and cpu.get("user_load") is not None:
        lines.append(f"  CPU user_load≈{cpu.get('user_load')}%")
    return "\n".join(lines)
