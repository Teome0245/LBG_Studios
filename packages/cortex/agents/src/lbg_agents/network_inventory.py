"""Inventaire réseau LAN read-only — scan sous-réseau + hôtes connus + sondes HTTP."""

from __future__ import annotations

import ipaddress
import json
import os
import socket
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

from lbg_agents.remote_targets import canonical_role, resolve_host

# Phase 1 : détecter les hôtes vivants (rapide).
_DISCOVERY_PORTS = (22, 80, 443, 445, 161)
# Phase 2 : fingerprint sur hôtes répondants.
_DETAIL_PORTS = (
    22, 23, 80, 443, 445, 161, 3389, 5000, 5001, 548, 8006, 902, 8080, 8443, 11434,
    5005, 6000, 6001, 8010, 8050, 8773, 7733, 8765, 8791, 8792, 8098, 8766,
    44453, 44462, 44463,
)
_PORT_HINTS: dict[int, str] = {
    22: "ssh",
    23: "telnet",
    80: "http",
    443: "https",
    161: "snmp",
    445: "smb",
    3389: "rdp",
    5000: "synology/nas",
    5001: "synology/nas-https",
    548: "afp/nas",
    8006: "proxmox",
    902: "vmware-esxi",
    8080: "http-alt",
    8443: "https-alt",
    11434: "ollama",
    5005: "agent-windows",
    6000: "agent-linux",
    6001: "agent-linux-hands",
    8010: "orchestrator",
    8050: "mmo-http",
    8773: "mmmorpg-internal",
    7733: "mmmorpg-ws",
    8765: "prime-gateway",
    8791: "prime-sidecar",
    8792: "prime-world",
    8098: "piper-tts",
    8766: "mcp",
    44453: "core3-precu-login",
    44462: "core3-precu-status",
    44463: "core3-precu-ping",
}

# Capabilities suggérées par rôle / type d'appareil (croisement avec le registry orchestrateur).
_ROLE_SUGGESTIONS: dict[str, tuple[str, ...]] = {
    "core": ("devops_probe", "network_inventory", "project_pm"),
    "front": ("devops_probe", "npc_dialogue", "network_inventory"),
    "mmo": ("devops_probe", "core3_bot_action", "network_inventory"),
    "precu": ("devops_probe", "network_inventory"),
    "executor": ("devops_probe", "network_inventory"),
    "hands": ("desktop_control", "devops_probe", "network_inventory"),
    "desktop": ("desktop_control", "devops_probe"),
    "ad": ("desktop_control", "devops_probe"),
    "mail": ("devops_probe",),
    "router": ("network_inventory",),
    "switch": ("network_inventory", "devops_probe"),
    "wifi_extender": ("network_inventory",),
    "stb": ("network_inventory",),
    "phone": ("network_inventory",),
    "iot": ("network_inventory",),
    "cast": ("network_inventory",),
    "speaker": ("network_inventory",),
    "console": ("network_inventory",),
    "server": ("devops_probe", "network_inventory"),
    "nas": ("devops_probe",),
    "hypervisor": ("devops_probe", "network_inventory"),
    "lan": ("network_inventory",),
    "discovered": ("devops_probe", "network_inventory"),
}
_HINT_SUGGESTIONS: dict[str, tuple[str, ...]] = {
    "synology/nas": ("devops_probe",),
    "synology-nas": ("devops_probe",),
    "proxmox": ("devops_probe", "network_inventory"),
    "vmware-esxi": ("devops_probe", "network_inventory"),
    "windows": ("desktop_control", "devops_probe"),
    "windows-ad": ("desktop_control", "devops_probe"),
    "windows-server": ("devops_probe",),
    "freebox-routeur": ("network_inventory",),
}
_PORT_SUGGESTIONS: dict[int, tuple[str, ...]] = {
    5005: ("desktop_control",),
    6000: ("devops_probe",),
    6001: ("desktop_control", "devops_probe"),
    8010: ("devops_probe", "project_pm"),
    8020: ("npc_dialogue",),
    8050: ("devops_probe", "core3_bot_action"),
    8055: ("project_pm",),
    8080: ("devops_probe",),
    11434: ("npc_dialogue",),
    7733: ("core3_bot_action",),
    8006: ("devops_probe",),
    902: ("devops_probe",),
    5000: ("devops_probe",),
    5001: ("devops_probe",),
}

_URL_ENV_LABELS: dict[str, tuple[str, str]] = {
    "LBG_AGENT_DESKTOP_URL": ("desktop", "pc-windows"),
    "LBG_AGENT_HANDS_URL": ("hands", "lbg-omarchy"),
    "LBG_AGENT_OMARCHY_URL": ("hands", "lbg-omarchy"),
    "AGENT_WINDOWS_URL": ("desktop", "pc-windows"),
    "AGENT_WINDOWS_PORTABLE_URL": ("desktop", "portable-sds"),
    "AGENT_WINDOWS_PORTABLE_WIFI_URL": ("desktop", "portable-sds-wifi"),
    "AGENT_WINDOWS_SRV_AD_URL": ("ad", "serveur-ad"),
    "AGENT_LINUX_MAIL_URL": ("mail", "serveur-mail"),
    "AGENT_LINUX_IA_URL": ("ia-agent", "agent-linux-ia"),
    "AGENT_LINUX_MMMORPG_URL": ("mmo-agent", "agent-linux-mmo"),
    "AGENT_DEVOPS_VM_URL": ("devops-vm", "devops-vm"),
    "OLLAMA_BASE_URL": ("ollama", "ollama"),
    "LBG_ORCHESTRATOR_URL": ("orchestrator", "orchestrateur"),
    "LBG_MMO_SERVER_URL": ("mmo", "mmo-server"),
}


def _env_bool(key: str, default: bool = True) -> bool:
    raw = os.environ.get(key, "").strip().lower()
    if not raw:
        return default
    return raw in ("1", "true", "yes", "on")


def _scan_timeout_s() -> float:
    try:
        return max(0.15, float(os.environ.get("LBG_NETWORK_SCAN_TIMEOUT_S", "0.45").strip()))
    except ValueError:
        return 0.45


def _scan_workers() -> int:
    try:
        return max(8, min(128, int(os.environ.get("LBG_NETWORK_SCAN_WORKERS", "64").strip())))
    except ValueError:
        return 64


def _scan_cidr() -> str:
    return os.environ.get("LBG_NETWORK_SCAN_CIDR", "192.168.0.0/24").strip() or "192.168.0.0/24"


def _reverse_dns_enabled() -> bool:
    return _env_bool("LBG_NETWORK_REVERSE_DNS", default=True)


def _reverse_dns_timeout_s() -> float:
    try:
        return max(0.2, float(os.environ.get("LBG_NETWORK_REVERSE_DNS_TIMEOUT_S", "1.0").strip()))
    except ValueError:
        return 1.0


def _resolve_hostname(ip: str) -> str | None:
    if not _reverse_dns_enabled():
        return None
    try:
        socket.setdefaulttimeout(_reverse_dns_timeout_s())
        name, _, _ = socket.gethostbyaddr(ip)
        cleaned = (name or "").strip().rstrip(".")
        return cleaned or None
    except OSError:
        return None
    finally:
        socket.setdefaulttimeout(None)


def _resolve_hostnames(devices: list[dict[str, Any]]) -> None:
    if not _reverse_dns_enabled():
        return
    ips = [str(d.get("host") or "") for d in devices if d.get("host")]
    if not ips:
        return
    workers = min(_scan_workers(), max(4, len(ips)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_resolve_hostname, ip): ip for ip in ips}
        names: dict[str, str | None] = {}
        for fut in as_completed(futures):
            ip = futures[fut]
            try:
                names[ip] = fut.result()
            except Exception:
                names[ip] = None
    for d in devices:
        host = str(d.get("host") or "")
        if host and names.get(host):
            d["hostname"] = names[host]


def _suggest_capabilities(device: dict[str, Any]) -> list[str]:
    caps: set[str] = set()
    role = str(device.get("role") or "")
    for cap in _ROLE_SUGGESTIONS.get(role, ()):
        caps.add(cap)
    hint = str(device.get("device_hint") or "")
    for cap in _HINT_SUGGESTIONS.get(hint, ()):
        caps.add(cap)
    label = str(device.get("label") or "").lower()
    if "ad" in label or "windows" in label:
        caps.update(("desktop_control", "devops_probe"))
    if "synology" in label or "nas" in label:
        caps.add("devops_probe")
    for port in device.get("open_ports") or []:
        if isinstance(port, int):
            for cap in _PORT_SUGGESTIONS.get(port, ()):
                caps.add(cap)
    if device.get("reachable"):
        caps.add("network_inventory")
    order = (
        "network_inventory",
        "devops_probe",
        "desktop_control",
        "npc_dialogue",
        "project_pm",
        "core3_bot_action",
    )
    return [c for c in order if c in caps]


def _devices_export_payload(devices: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for d in devices:
        rows.append(
            {
                "host": d.get("host"),
                "hostname": d.get("hostname"),
                "label": d.get("label"),
                "role": d.get("role"),
                "device_hint": d.get("device_hint"),
                "mac": d.get("mac"),
                "vendor": d.get("vendor"),
                "reachable": d.get("reachable"),
                "freebox_active": d.get("freebox_active"),
                "open_ports": d.get("open_ports") or [],
                "action_suggestions": d.get("action_suggestions") or [],
                "source": d.get("source"),
            }
        )
    return rows


def _tcp_reachable(host: str, port: int, timeout_s: float = 1.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout_s):
            return True
    except OSError:
        return False


def _http_probe(url: str, timeout_s: float = 2.5) -> dict[str, Any]:
    try:
        with httpx.Client(timeout=timeout_s, follow_redirects=True) as client:
            r = client.get(url)
        return {"ok": r.status_code < 400, "status_code": r.status_code, "url": url}
    except Exception as e:
        return {"ok": False, "url": url, "error": f"{type(e).__name__}: {e}"}


def _http_fingerprint(host: str, port: int = 80, timeout_s: float = 2.0) -> dict[str, Any]:
    scheme = "https" if port == 443 else "http"
    url = f"{scheme}://{host}:{port}/"
    try:
        with httpx.Client(timeout=timeout_s, follow_redirects=True, verify=False) as client:
            r = client.get(url)
        body = (r.text or "")[:1200].lower()
        server = (r.headers.get("server") or "").strip()
        hint = _hint_from_http(body, server)
        return {
            "ok": True,
            "url": url,
            "status_code": r.status_code,
            "server": server,
            "device_hint": hint,
        }
    except Exception as e:
        return {"ok": False, "url": url, "error": f"{type(e).__name__}: {e}"}


def _hint_from_http(body: str, server: str) -> str | None:
    blob = f"{body} {server.lower()}"
    for needle, label in (
        ("synology", "synology-nas"),
        ("diskstation", "synology-nas"),
        ("proxmox", "proxmox"),
        ("vmware", "vmware-esxi"),
        ("esxi", "vmware-esxi"),
        ("freebox", "freebox-routeur"),
        ("livebox", "livebox-routeur"),
        ("sfr", "box-sfr"),
        ("active directory", "windows-ad"),
        ("windows nt", "windows-server"),
    ):
        if needle in blob:
            return label
    if "nginx" in blob and "ollama" in blob:
        return "front-ollama"
    return None


def _hint_from_ports(open_ports: list[int]) -> str | None:
    if 8006 in open_ports:
        return "proxmox"
    if 902 in open_ports:
        return "vmware-esxi"
    if 5000 in open_ports or 5001 in open_ports:
        return "synology/nas"
    if 161 in open_ports and 80 in open_ports:
        return "switch/ap"
    if 3389 in open_ports and 445 in open_ports:
        return "windows"
    if 445 in open_ports and 3389 not in open_ports:
        return "smb"
    return None


def _role_from_name_vendor(name: str, vendor: str = "") -> tuple[str, str]:
    """Infère un rôle réseau (switch, box, poste, IoT…) depuis Freebox / hostname."""
    label = (name or "").strip() or "hôte"
    n = label.lower()
    v = (vendor or "").lower()
    if any(x in n for x in ("tl-sg", "sg108", "sg105", "switch")) and "nintendo" not in n:
        return "switch", label
    if "tp-link" in v and ("sg" in n or "switch" in n):
        return "switch", label
    if any(x in n for x in ("repete", "répète", "repeater", "extender", "mesh")):
        return "wifi_extender", label
    if "freebox player" in n or ("player" in n and "freebox" in v):
        return "stb", label
    if "freebox" in n and "player" not in n and "repete" not in n:
        return "router", label
    if any(x in n for x in ("phone", "iphone", "redmi", "android", "pixel", "galaxy")):
        return "phone", label
    if any(x in n for x in ("cam", "nest", "lunii", "kindel", "kindle", "esp32", "tasmota")):
        if "nest mini" in n or "google-nest-mini" in n or "nest-mini" in n:
            return "cast", label
        if "nest" in n and "cam" not in n:
            return "cast", label
        return "iot", label
    if "chromecast" in n or "google cast" in n:
        return "cast", label
    if "nintendo" in n or "nintendo" in v:
        return "console", label
    if "nas" in n or "synology" in v or "diskstation" in n:
        return "nas", label
    if any(x in n for x in ("portable", "laptop", "pc-", "pc ", "desktop", "notebook")):
        return "desktop", label
    if "poweredge" in n or ("dell" in v and "r720" in n):
        return "hypervisor", label
    if "proxmox" in v or n.startswith("vm-") or n.startswith("lbg-") or "ct " in n:
        return "server", label
    if "ubuntu" in n or "server" in n:
        return "server", label
    return "lan", label


def _pick_lan_ipv4(ipv4s: list[str], cidr: str = "192.168.0.0/24") -> str | None:
    try:
        net = ipaddress.ip_network(cidr, strict=False)
    except ValueError:
        net = None
    preferred: list[str] = []
    other: list[str] = []
    for raw in ipv4s:
        ip = str(raw or "").strip()
        if not ip or ":" in ip:
            continue
        try:
            addr = ipaddress.ip_address(ip)
        except ValueError:
            continue
        if net and addr in net:
            preferred.append(ip)
        else:
            other.append(ip)
    return (preferred or other or [None])[0]


def _catalog_from_freebox(freebox: dict[str, Any] | None, *, cidr: str) -> list[dict[str, Any]]:
    """Transforme les hôtes Freebox LAN en entrées catalogue (box, switch, postes, IoT…)."""
    if not isinstance(freebox, dict):
        return []
    hosts = freebox.get("lan_hosts") or freebox.get("lan_hosts_sample") or []
    if not isinstance(hosts, list):
        return []
    rows: list[dict[str, Any]] = []
    for h in hosts:
        if not isinstance(h, dict):
            continue
        ipv4s = h.get("ipv4") if isinstance(h.get("ipv4"), list) else []
        host = _pick_lan_ipv4([str(x) for x in ipv4s], cidr=cidr)
        if not host:
            continue
        name = str(h.get("name") or "").strip()
        vendor = str(h.get("vendor") or "").strip()
        role, label = _role_from_name_vendor(name, vendor)
        active = bool(h.get("active"))
        reachable_fb = bool(h.get("reachable"))
        rows.append(
            {
                "host": host,
                "server_id": f"freebox-{host.replace('.', '-')}",
                "role": role,
                "label": label,
                "mac": str(h.get("mac") or "").strip() or None,
                "vendor": vendor or None,
                "device_hint": role,
                "source": "freebox",
                "freebox_active": active,
                "freebox_reachable": reachable_fb,
                # Présence Freebox (Wi-Fi / L2) — complète le scan TCP.
                "reachable": active or reachable_fb,
            }
        )
    return rows


def _state_path() -> Path:
    raw = os.environ.get("LBG_NETWORK_INVENTORY_STATE", "").strip()
    if raw:
        return Path(raw)
    return Path("/var/lib/lbg/network_inventory/state.json")


def _load_state() -> dict[str, Any]:
    path = _state_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_state(state: dict[str, Any]) -> None:
    path = _state_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass


def _host_present(device: dict[str, Any]) -> bool:
    if device.get("reachable") is True:
        return True
    if device.get("freebox_active") is True or device.get("freebox_reachable") is True:
        return True
    return False


def _diff_against_previous(devices: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare à l’instantané précédent : apparus / disparus / toujours présents."""
    prev = _load_state()
    prev_hosts = prev.get("hosts") if isinstance(prev.get("hosts"), dict) else {}
    now_ts = time.time()
    current: dict[str, dict[str, Any]] = {}
    for d in devices:
        host = str(d.get("host") or "").strip()
        if not host:
            continue
        present = _host_present(d)
        current[host] = {
            "label": d.get("label") or d.get("hostname") or host,
            "role": d.get("role") or "lan",
            "mac": d.get("mac"),
            "vendor": d.get("vendor"),
            "reachable": present,
            "last_seen": now_ts if present else (prev_hosts.get(host) or {}).get("last_seen"),
            "open_ports": d.get("open_ports") or [],
            "source": d.get("source"),
        }

    prev_present = {h for h, meta in prev_hosts.items() if isinstance(meta, dict) and meta.get("reachable")}
    curr_present = {h for h, meta in current.items() if meta.get("reachable")}

    appeared = sorted(curr_present - prev_present)
    disappeared = sorted(prev_present - curr_present)
    still = sorted(curr_present & prev_present)

    # Fusion : garder last_seen des absents pour historique court
    merged_hosts = dict(prev_hosts)
    merged_hosts.update(current)
    for h in disappeared:
        if h in merged_hosts and isinstance(merged_hosts[h], dict):
            merged_hosts[h] = {**merged_hosts[h], "reachable": False}

    diff = {
        "appeared": [
            {"host": h, "label": (current.get(h) or {}).get("label"), "role": (current.get(h) or {}).get("role")}
            for h in appeared
        ],
        "disappeared": [
            {
                "host": h,
                "label": (prev_hosts.get(h) or {}).get("label"),
                "role": (prev_hosts.get(h) or {}).get("role"),
            }
            for h in disappeared
        ],
        "still_count": len(still),
        "n_appeared": len(appeared),
        "n_disappeared": len(disappeared),
    }
    _save_state(
        {
            "ts": now_ts,
            "hosts": merged_hosts,
            "last_diff": diff,
            "n_hosts": len(merged_hosts),
            "n_present": len(curr_present),
        }
    )
    return diff


def _format_diff_text(diff: dict[str, Any]) -> str:
    lines = [
        "Changements depuis le dernier scan :",
        f"  + apparus : {diff.get('n_appeared', 0)} · − disparus : {diff.get('n_disappeared', 0)} · "
        f"= stables : {diff.get('still_count', 0)}",
    ]
    for row in diff.get("appeared") or []:
        lines.append(f"  + {row.get('host')} — {row.get('label')} ({row.get('role')})")
    for row in diff.get("disappeared") or []:
        lines.append(f"  − {row.get('host')} — {row.get('label')} ({row.get('role')})")
    if not diff.get("appeared") and not diff.get("disappeared"):
        lines.append("  (aucun changement)")
    return "\n".join(lines)


def _iter_hosts(cidr: str) -> list[str]:
    try:
        net = ipaddress.ip_network(cidr, strict=False)
    except ValueError:
        return []
    return [str(ip) for ip in net.hosts()]


def _scan_ports(hosts: list[str], ports: tuple[int, ...], timeout_s: float, workers: int) -> dict[str, list[int]]:
    """Scan TCP parallèle ; retourne {ip: [ports ouverts]}."""
    if not hosts or not ports:
        return {}
    open_by_host: dict[str, set[int]] = {}
    tasks = [(h, p) for h in hosts for p in ports]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        future_map = {pool.submit(_tcp_reachable, h, p, timeout_s): (h, p) for h, p in tasks}
        for fut in as_completed(future_map):
            host, port = future_map[fut]
            try:
                if fut.result():
                    open_by_host.setdefault(host, set()).add(port)
            except Exception:
                pass
    return {h: sorted(ps) for h, ps in open_by_host.items()}


def _scan_subnet(cidr: str) -> dict[str, list[int]]:
    if not _env_bool("LBG_NETWORK_SCAN_ENABLED", default=True):
        return {}
    hosts = _iter_hosts(cidr)
    if not hosts:
        return {}
    timeout_s = _scan_timeout_s()
    workers = _scan_workers()
    alive = _scan_ports(hosts, _DISCOVERY_PORTS, timeout_s, workers)
    if not alive:
        return {}
    detail_hosts = list(alive.keys())
    detailed = _scan_ports(detail_hosts, _DETAIL_PORTS, timeout_s, workers)
    for host, ports in alive.items():
        detailed.setdefault(host, [])
        for p in ports:
            if p not in detailed[host]:
                detailed[host].append(p)
        detailed[host].sort()
    return detailed


def _parse_known_devices_json() -> list[dict[str, Any]]:
    raw = os.environ.get("LBG_NETWORK_KNOWN_DEVICES", "").strip()
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    out: list[dict[str, Any]] = []
    for row in data:
        if not isinstance(row, dict):
            continue
        host = str(row.get("host") or row.get("ip") or "").strip()
        if not host:
            continue
        out.append(
            {
                "host": host.split(":")[0],
                "server_id": str(row.get("server_id") or row.get("id") or row.get("label") or host),
                "role": str(row.get("role") or "known"),
                "label": str(row.get("label") or row.get("name") or row.get("server_id") or host),
            }
        )
    return out


def _router_host() -> str | None:
    raw = os.environ.get("LBG_NETWORK_ROUTER_HOST", "").strip()
    if not raw:
        return None
    return raw.split(":")[0] or None


def _apply_router_override(known: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Force l'étiquette routeur sur l'IP réelle (Freebox souvent .254, pas .1)."""
    router_ip = _router_host()
    if not router_ip:
        return known
    filtered = [
        row
        for row in known
        if not (row.get("role") == "router" and str(row.get("host") or "") != router_ip)
    ]
    router_row = {
        "host": router_ip,
        "server_id": "router",
        "role": "router",
        "label": "freebox-routeur",
        "device_hint": "freebox-routeur",
        "source": "env_router",
    }
    return [router_row] + filtered


def _known_from_env_urls() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for env_key, (role, label) in _URL_ENV_LABELS.items():
        raw = os.environ.get(env_key, "").strip()
        if not raw:
            continue
        host = urlparse(raw).hostname
        if not host or host in seen:
            continue
        seen.add(host)
        rows.append(
            {
                "host": host,
                "server_id": role,
                "role": role,
                "label": label,
                "source": "env_url",
            }
        )
    return rows


def _topology_probes() -> list[dict[str, Any]]:
    """Sondes HTTP ciblées sur la topologie LBG (core/front/mmo/desktop)."""
    rows: list[dict[str, Any]] = []
    for server_id, role_label in (
        ("core", "core"),
        ("front", "front"),
        ("mmo", "mmo"),
        ("precu", "precu"),
        ("executor", "executor"),
        ("hands", "hands"),
    ):
        host = resolve_host(server_id)
        if not host:
            continue
        rows.append(
            {
                "server_id": server_id,
                "role": role_label,
                "label": f"lbg-{role_label}",
                "host": host,
                "probes": [{"kind": "tcp", "port": 22, "label": "ssh"}],
            }
        )
    http_by_role: dict[str, list[tuple[int, str, str]]] = {
        "core": [
            (8000, "/healthz", "backend"),
            (8010, "/healthz", "orchestrator"),
            (8020, "/healthz", "agent-dialogue"),
            (8055, "/healthz", "agent-pm"),
        ],
        "front": [(8080, "/", "pilot-nginx"), (11434, "/api/tags", "ollama")],
        "mmo": [(8050, "/healthz", "mmo-server"), (7733, "/", "mmmorpg-ws")],
        "precu": [],
        "executor": [],
        "hands": [(5005, "/healthz", "linux-agent")],
    }
    for row in rows:
        host = row["host"]
        role = row["role"]
        for port, path, label in http_by_role.get(role, []):
            row["probes"].append(
                {"kind": "http", "port": port, "path": path, "label": label, "url": f"http://{host}:{port}{path}"}
            )
        if role == "precu":
            for port, label in ((44453, "core3-precu-login"), (44462, "core3-precu-status"), (44463, "core3-precu-ping")):
                row["probes"].append({"kind": "tcp", "port": port, "label": label})
    seen_desktop_hosts: set[str] = set()

    def _add_desktop_row(*, server_id: str, label: str, url: str) -> None:
        u = (url or "").strip().rstrip("/")
        if not u:
            return
        parsed = urlparse(u)
        host = parsed.hostname or ""
        if not host or host in seen_desktop_hosts:
            return
        seen_desktop_hosts.add(host)
        rows.append(
            {
                "server_id": server_id,
                "role": "desktop",
                "label": label,
                "host": host,
                "probes": [{"kind": "http", "url": f"{u}/healthz", "label": "agent-desktop"}],
            }
        )

    # Cibles explicites (pc + portable + …) — source de vérité multi-poste
    raw_targets = os.environ.get("LBG_DESKTOP_TARGETS", "").strip()
    if raw_targets:
        try:
            data = json.loads(raw_targets)
        except json.JSONDecodeError:
            data = None
        if isinstance(data, list):
            for row in data:
                if not isinstance(row, dict):
                    continue
                tid = str(row.get("id") or row.get("target_id") or "desktop").strip() or "desktop"
                label = str(row.get("label") or row.get("name") or tid).strip() or tid
                _add_desktop_row(server_id=f"desktop-{tid}", label=label, url=str(row.get("url") or ""))

    _add_desktop_row(
        server_id="desktop",
        label="pc-windows",
        url=os.environ.get("LBG_AGENT_DESKTOP_URL", "") or os.environ.get("AGENT_WINDOWS_URL", ""),
    )
    _add_desktop_row(
        server_id="desktop-portable",
        label="portable-sds",
        url=os.environ.get("AGENT_WINDOWS_PORTABLE_URL", ""),
    )
    _add_desktop_row(
        server_id="desktop-portable-wifi",
        label="portable-sds-wifi",
        url=os.environ.get("AGENT_WINDOWS_PORTABLE_WIFI_URL", ""),
    )
    return rows


def _merge_catalog(
    known: list[dict[str, Any]],
    topology: list[dict[str, Any]],
    scan: dict[str, list[int]],
    freebox_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    by_ip: dict[str, dict[str, Any]] = {}

    def _upsert(entry: dict[str, Any]) -> None:
        host = str(entry.get("host") or "")
        if not host:
            return
        cur = by_ip.get(host)
        if cur is None:
            by_ip[host] = dict(entry)
            return
        for k, v in entry.items():
            if k == "probes" and isinstance(v, list):
                existing = cur.get("probes") if isinstance(cur.get("probes"), list) else []
                cur["probes"] = existing + v
            elif k == "reachable" and v is True:
                cur["reachable"] = True
            elif v and (k not in cur or not cur.get(k) or cur.get(k) == "discovered" or cur.get(k) == "lan"):
                # Freebox / known enrichissent label+role mieux que « discovered »
                if k in ("label", "role", "device_hint", "mac", "vendor") and cur.get("source") in (
                    "scan",
                    "discovered",
                    None,
                ):
                    cur[k] = v
                elif k not in cur or not cur.get(k):
                    cur[k] = v
            elif v and k in ("freebox_active", "freebox_reachable", "mac", "vendor"):
                cur[k] = v

    for row in known:
        _upsert({**row, "source": row.get("source") or "known"})
    for row in topology:
        _upsert({**row, "source": row.get("source") or "topology"})
    for row in freebox_rows or []:
        _upsert({**row, "source": row.get("source") or "freebox"})

    for host, open_ports in sorted(scan.items(), key=lambda x: ipaddress.ip_address(x[0])):
        port_probes = [
            {"kind": "tcp", "port": p, "label": _PORT_HINTS.get(p, f"tcp-{p}"), "ok": True} for p in open_ports
        ]
        hint = _hint_from_ports(open_ports)
        if host in by_ip:
            entry = by_ip[host]
            entry["reachable"] = True
            entry["open_ports"] = open_ports
            if hint and not entry.get("device_hint"):
                entry["device_hint"] = hint
            existing_probes = entry.get("probe_results") if isinstance(entry.get("probe_results"), list) else []
            if not existing_probes:
                entry["probe_results"] = port_probes
            entry["source"] = entry.get("source") or "scan"
        else:
            role = "discovered"
            label = hint or f"hôte-{host}"
            if hint == "switch/ap":
                role = "switch"
            by_ip[host] = {
                "server_id": f"discovered-{host.replace('.', '-')}",
                "role": role,
                "label": label,
                "host": host,
                "reachable": True,
                "open_ports": open_ports,
                "device_hint": hint,
                "probe_results": port_probes,
                "source": "scan",
            }

    return list(by_ip.values())


def _probe_entry(entry: dict[str, Any]) -> dict[str, Any]:
    host = str(entry.get("host") or "")
    probe_results: list[dict[str, Any]] = []
    if isinstance(entry.get("probe_results"), list):
        probe_results = list(entry["probe_results"])
    host_ok = bool(entry.get("reachable"))
    open_ports = entry.get("open_ports") if isinstance(entry.get("open_ports"), list) else []

    for probe in entry.get("probes") or []:
        if not isinstance(probe, dict):
            continue
        if probe.get("kind") == "http" and isinstance(probe.get("url"), str):
            res = _http_probe(probe["url"])
            probe_results.append({**probe, **res})
            host_ok = host_ok or bool(res.get("ok"))
        elif probe.get("kind") == "tcp" and isinstance(probe.get("port"), int):
            ok = _tcp_reachable(host, int(probe["port"]), _scan_timeout_s())
            probe_results.append({**probe, "ok": ok})
            host_ok = host_ok or ok

    if not host_ok and open_ports:
        host_ok = True

    device_hint = entry.get("device_hint")
    if not device_hint:
        device_hint = _hint_from_ports([int(p) for p in open_ports if isinstance(p, int)])
    if not device_hint and host_ok:
        for port in (80, 443, 8080, 5000, 8006):
            if port in open_ports or any(p.get("port") == port and p.get("ok") for p in probe_results):
                fp = _http_fingerprint(host, port)
                if fp.get("device_hint"):
                    device_hint = fp["device_hint"]
                    probe_results.append({"kind": "http", "port": port, "label": "fingerprint", **fp})
                    break

    device = {
        "server_id": entry.get("server_id"),
        "role": entry.get("role"),
        "label": entry.get("label") or entry.get("server_id") or host,
        "host": host,
        "canonical_role": canonical_role(str(entry.get("server_id") or "")),
        "reachable": host_ok,
        "open_ports": open_ports,
        "device_hint": device_hint,
        "probe_results": probe_results,
        "source": entry.get("source"),
        "mac": entry.get("mac"),
        "vendor": entry.get("vendor"),
        "freebox_active": entry.get("freebox_active"),
        "freebox_reachable": entry.get("freebox_reachable"),
    }
    if device.get("freebox_active") or device.get("freebox_reachable"):
        device["reachable"] = True
    device["action_suggestions"] = _suggest_capabilities(device)
    return device


def _format_devices_text(devices: list[dict[str, Any]], *, scan_cidr: str, n_scanned: int) -> str:
    present = sum(1 for d in devices if _host_present(d))
    lines = [
        f"Inventaire réseau LAN — {present}/{len(devices)} présent(s) — scan {scan_cidr} ({n_scanned} IP)",
        "",
    ]
    for d in devices:
        host = d.get("host", "?")
        label = d.get("label") or d.get("server_id") or "?"
        role = d.get("role") or "?"
        hint = d.get("device_hint")
        reachable = _host_present(d)
        mark = "OK" if reachable else "KO"
        extra = f" [{hint}]" if hint and hint != role else ""
        ports = d.get("open_ports") or []
        hostname = d.get("hostname")
        host_s = f"{host}" + (f" / {hostname}" if hostname else "")
        port_s = f" ports={','.join(str(p) for p in ports)}" if ports else ""
        sugg = d.get("action_suggestions") or []
        sugg_s = f" → caps: {', '.join(sugg)}" if sugg else ""
        lines.append(f"• {label} ({role}) {host_s} — {mark}{extra}{port_s}{sugg_s}")
        for p in d.get("probe_results") or []:
            plabel = p.get("label", p.get("kind", "?"))
            if p.get("kind") == "http":
                st = "OK" if p.get("ok") else "KO"
                code = p.get("status_code", "")
                extra_p = f" HTTP {code}" if code else (f" — {p.get('error')}" if p.get("error") else "")
                lines.append(f"    - {plabel}: {st}{extra_p}")
            elif p.get("kind") == "tcp":
                st = "open" if p.get("ok") else "closed"
                lines.append(f"    - {plabel} :{p.get('port')} {st}")
    return "\n".join(lines)


def run_network_inventory(
    *,
    actor_id: str,
    text: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Scan sous-réseau + Freebox LAN + sondes sur hôtes connus (read-only)."""
    _ = actor_id, text
    ctx = context if isinstance(context, dict) else {}
    cidr = str(ctx.get("network_scan_cidr") or _scan_cidr())
    known = _apply_router_override(_parse_known_devices_json() + _known_from_env_urls())
    topology = _topology_probes()
    scan = _scan_subnet(cidr) if ctx.get("network_scan") is not False else {}

    freebox: dict[str, Any] | None = None
    try:
        from lbg_agents.freebox_client import freebox_enabled, probe_freebox

        if freebox_enabled() and ctx.get("freebox_probe") is not False:
            freebox = probe_freebox(include_lan=bool(ctx.get("freebox_lan", True)))
    except Exception as exc:  # noqa: BLE001 — inventaire TCP reste valide
        freebox = {"ok": False, "error": str(exc)}

    freebox_rows = _catalog_from_freebox(freebox, cidr=cidr)
    catalog = _merge_catalog(known, topology, scan, freebox_rows)
    devices = [_probe_entry(entry) for entry in catalog]
    _resolve_hostnames(devices)
    for d in devices:
        # Présence : scan TCP OU Freebox active
        if d.get("freebox_active") or d.get("freebox_reachable"):
            d["reachable"] = True
        d["action_suggestions"] = _suggest_capabilities(d)
    n_scanned = len(_iter_hosts(cidr))

    nas: dict[str, Any] | None = None
    cast_speakers: dict[str, Any] | None = None
    try:
        from lbg_agents.cast_speaker_client import (
            cast_hosts_from_env,
            format_cast_probe_text,
            probe_cast_speakers,
        )

        if ctx.get("cast_probe") is not False:
            hosts = list(cast_hosts_from_env())
            for d in devices:
                if d.get("role") in ("cast", "speaker", "iot") and d.get("host"):
                    h = str(d["host"])
                    if h not in hosts and (
                        d.get("role") in ("cast", "speaker")
                        or "nest" in str(d.get("label") or "").lower()
                    ):
                        hosts.append(h)
            # Toujours sonder les hôtes Cast connus même si absents du scan
            cast_speakers = probe_cast_speakers(hosts)
            by_cast = {
                str(s.get("host")): s
                for s in (cast_speakers.get("speakers") or [])
                if isinstance(s, dict) and s.get("ok")
            }
            seen_hosts = {str(d.get("host") or "") for d in devices}
            for host, info in by_cast.items():
                if host in seen_hosts:
                    continue
                devices.append(
                    {
                        "server_id": f"cast-{host.replace('.', '-')}",
                        "role": "cast",
                        "label": str(info.get("name") or host),
                        "host": host,
                        "reachable": True,
                        "open_ports": [8008, 8009],
                        "device_hint": "google-cast",
                        "mac": info.get("mac_address"),
                        "source": "cast",
                        "cast": {
                            "name": info.get("name"),
                            "locale": info.get("locale"),
                            "connected": info.get("connected"),
                            "build_version": info.get("build_version"),
                        },
                        "action_suggestions": ["network_inventory"],
                    }
                )
                seen_hosts.add(host)
            for d in devices:
                host = str(d.get("host") or "")
                info = by_cast.get(host)
                if not info:
                    continue
                d["role"] = "cast"
                d["device_hint"] = "google-cast"
                if info.get("name"):
                    d["label"] = str(info["name"])
                if info.get("mac_address"):
                    d["mac"] = info["mac_address"]
                d["cast"] = {
                    "name": info.get("name"),
                    "locale": info.get("locale"),
                    "connected": info.get("connected"),
                    "build_version": info.get("build_version"),
                }
                d["reachable"] = True
                d["action_suggestions"] = _suggest_capabilities(d)
    except Exception as exc:  # noqa: BLE001
        cast_speakers = {"ok": False, "error": str(exc)}

    devices.sort(
        key=lambda d: (
            0 if d.get("source") in ("known", "topology", "env_url", "env_router", "freebox", "cast") else 1,
            ipaddress.ip_address(str(d.get("host") or "0.0.0.0")),
        )
    )

    persist = ctx.get("persist_state") is not False
    diff: dict[str, Any] | None = None
    if persist:
        diff = _diff_against_previous(devices)

    reply = _format_devices_text(devices, scan_cidr=cidr, n_scanned=n_scanned)
    if diff is not None:
        reply = f"{reply}\n\n{_format_diff_text(diff)}"
    try:
        from lbg_agents.freebox_client import format_audit_text

        if isinstance(freebox, dict) and freebox.get("configured") is not False:
            reply = f"{reply}\n\n{format_audit_text(freebox)}"
    except Exception:
        pass
    try:
        from lbg_agents.synology_client import (
            format_nas_probe_text,
            nas_enabled,
            probe_nas,
        )

        if nas_enabled() and ctx.get("nas_probe") is not False:
            nas = probe_nas(include_downloads=bool(ctx.get("nas_downloads", True)))
            reply = f"{reply}\n\n{format_nas_probe_text(nas)}"
    except Exception as exc:  # noqa: BLE001 — inventaire TCP reste valide
        nas = {"ok": False, "error": str(exc)}

    if isinstance(cast_speakers, dict) and cast_speakers.get("speakers") is not None:
        try:
            from lbg_agents.cast_speaker_client import format_cast_probe_text

            reply = f"{reply}\n\n{format_cast_probe_text(cast_speakers)}"
        except Exception:
            pass

    by_role: dict[str, int] = {}
    for d in devices:
        role = str(d.get("role") or "lan")
        by_role[role] = by_role.get(role, 0) + 1

    devices_export = _devices_export_payload(devices)

    return {
        "ok": True,
        "agent": "network_inventory",
        "handler": "network_inventory",
        "devices": devices,
        "devices_export": devices_export,
        "n_devices": len(devices),
        "n_hosts_scanned": n_scanned,
        "scan_cidr": cidr,
        "n_hosts_alive": len(scan),
        "n_present": sum(1 for d in devices if _host_present(d)),
        "by_role": by_role,
        "diff": diff,
        "freebox": freebox,
        "nas": nas,
        "cast_speakers": cast_speakers,
        "reply": reply,
        "source": "lan_scan+freebox+cast+probes",
        "ts": time.time(),
    }
