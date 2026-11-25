"""Périmètre plateforme Atlas — LLM dual (110 heavy / 111 light) + runtime (140/141/143/245/246).

246 = prime-hub Godot G5+ ``:8787/healthz`` (pas Core3 gateway/sidecar).
245 PreCU = optionnel (sandbox).
143 = VM Omarchy + mains (absorbe l'ex-CT .142 détruit).
"""

from __future__ import annotations

import json
import os
import socket
import urllib.error
import urllib.request
from typing import Any

from team.ollama_audit import audit_ollama_lan
from team.llm_model_probe import audit_dialogue_fast_cloud


def _host_ip(env_key: str, default: str) -> str:
    raw = os.environ.get(env_key, default).strip()
    return raw.split(":")[0].split("/")[0]


def admin_infra_perimeter() -> list[str]:
    """Hôtes obligatoires Atlas (front legacy .112 et ex-CT .142 hors périmètre)."""
    return ["110", "111", "140", "141", "143", "245", "246"]


def platform_host_specs() -> list[dict[str, Any]]:
    ip110 = _host_ip("LBG_LAN_HOST_LLM_HEAVY", _host_ip("LBG_LAN_HOST_FRONT", "192.168.0.110"))
    ip111 = _host_ip(
        "LBG_LAN_HOST_LLM_LIGHT",
        os.environ.get("LBG_REASON_LIGHT_BASE_URL", "http://192.168.0.111:11434")
        .replace("http://", "")
        .replace("https://", "")
        .split(":")[0]
        or "192.168.0.111",
    )
    ip140 = _host_ip("LBG_LAN_HOST_CORE", "192.168.0.140")
    ip141 = _host_ip("LBG_LAN_HOST_EXECUTOR", "192.168.0.141")
    raw_hands_url = (
        os.environ.get("LBG_AGENT_OMARCHY_URL", "").strip()
        or os.environ.get("LBG_AGENT_HANDS_URL", "").strip()
        or "http://192.168.0.143:5005"
    )
    # Garde-fou anti-résidu .142:6001 (CT détruit → absorbé par Omarchy .143:5005)
    if "192.168.0.142" in raw_hands_url or ":6001" in raw_hands_url:
        raw_hands_url = "http://192.168.0.143:5005"
    ip143 = _host_ip(
        "LBG_LAN_HOST_HANDS",
        raw_hands_url.replace("http://", "").replace("https://", "").split(":")[0]
        or "192.168.0.143",
    )
    if ip143 == "192.168.0.142":
        ip143 = "192.168.0.143"
    ip245 = _host_ip("LBG_LAN_HOST_PRECU", _host_ip("LBG_LAN_HOST_MMO_SERVER", "192.168.0.245"))
    ip246 = _host_ip("LBG_LAN_HOST_CORE3_PRIME", _host_ip("LBG_LAN_HOST_MMO", "192.168.0.246"))

    # G5+ : prime-hub Godot unifié HTTP+WS :8787 (/healthz). Ancien :8765 + sidecar :8791 = Core3 OFF.
    hub_base = (
        os.environ.get("LBG_PRIME_HUB_URL", "").strip()
        or os.environ.get("LBG_TEAM_GODOT_GATEWAY_URL", "").strip()
        or f"http://{ip246}:8787"
    ).rstrip("/")
    hub_health = f"{hub_base}/healthz"
    orch_url = os.environ.get("LBG_ORCHESTRATOR_URL", f"http://{ip140}:8010").strip().rstrip("/")

    # .112 décommissionné — sonde uniquement si LBG_ATLAS_PROBE_FRONT_LEGACY=1 (rollback).
    probe_front_legacy = os.environ.get("LBG_ATLAS_PROBE_FRONT_LEGACY", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )

    specs: list[dict[str, Any]] = [
        {
            "id": "llm_heavy_110",
            "label": "Ollama heavy (CT 110 / .110)",
            "host": ip110,
            "perimeter_id": "110",
            "role": "llm_heavy",
            "required": True,
            "ollama_primary": True,
            "ollama_tier": "heavy",
            "probes": [
                {"kind": "ollama_tags", "url": f"http://{ip110}:11434/api/tags"},
            ],
        },
        {
            "id": "llm_light_111",
            "label": "Ollama light (NUC CT / .111)",
            "host": ip111,
            "perimeter_id": "111",
            "role": "llm_light",
            "required": True,
            "ollama_primary": False,
            "ollama_tier": "light",
            "probes": [
                {"kind": "ollama_tags", "url": f"http://{ip111}:11434/api/tags"},
            ],
        },
        {
            "id": "core_140",
            "label": "Core orchestrateur + Pilot Nginx",
            "host": ip140,
            "perimeter_id": "140",
            "role": "orchestrator_team",
            "required": True,
            "probes": [
                {
                    "kind": "http",
                    "url": orch_url + "/healthz",
                },
                {
                    "kind": "http",
                    "url": os.environ.get("LBG_PILOT_URL", f"http://{ip140}:8080").rstrip("/") + "/",
                },
                {
                    "kind": "team_wsl_health",
                    "url": orch_url + "/v1/team/wsl/health",
                },
            ],
        },
        {
            "id": "executor_141",
            "label": "LAN executor CT (poll Team WSL — remplace poste .10)",
            "host": ip141,
            "perimeter_id": "141",
            "role": "lan_executor",
            "required": True,
            "probes": [
                {"kind": "tcp", "port": 22},
                {"kind": "team_wsl_bridge", "url": orch_url + "/v1/team/wsl/health"},
            ],
        },
        {
            "id": "hands_143",
            "label": "LAN hands / Omarchy VM (agent_ia_linux :5005 — import_face_parts / fichiers)",
            "host": ip143,
            "perimeter_id": "143",
            "role": "lan_hands",
            "required": True,
            "probes": [
                {"kind": "tcp", "port": 22},
                {
                    "kind": "http",
                    "url": raw_hands_url.rstrip("/") + "/healthz",
                },
            ],
        },
        {
            "id": "precu_245",
            "label": "PreCU sandbox / MMO HTTP",
            "host": ip245,
            "perimeter_id": "245",
            "role": "precu_runtime",
            # Sandbox PreCU : OFF volontaire ≠ périmètre Atlas KO (cf. perimeter_has_ko).
            "required": False,
            "probes": [
                {"kind": "http", "url": f"http://{ip245}:8050/healthz"},
            ],
        },
        {
            "id": "prime_246",
            "label": "Prime hub Godot G5+ (:8787)",
            "host": ip246,
            "perimeter_id": "246",
            "role": "prime_runtime",
            "required": True,
            "probes": [
                {"kind": "http", "url": hub_health},
            ],
        },
    ]

    if probe_front_legacy:
        ip112 = _host_ip("LBG_LAN_HOST_FRONT_LEGACY", "192.168.0.112")
        specs.append(
            {
                "id": "front_legacy_112",
                "label": "Front legacy .112 (décommissionné — opt-in)",
                "host": ip112,
                "perimeter_id": "112",
                "role": "front_legacy",
                "required": False,
                "probes": [
                    {"kind": "http", "url": f"http://{ip112}:8080/"},
                ],
            }
        )

    return specs


def _probe_tcp(host: str, port: int, *, timeout: float = 3.0) -> dict[str, Any]:
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return {"host": host, "port": port, "ok": True, "kind": "tcp"}
    except OSError as exc:
        return {"host": host, "port": port, "ok": False, "kind": "tcp", "error": str(exc)[:160]}


def _probe_team_wsl_health(url: str, *, timeout: float = 4.0) -> dict[str, Any]:
    probe = _probe_http(url, timeout=timeout)
    if not probe.get("ok"):
        return {**probe, "kind": "team_wsl_health", "enabled": False, "skills": 0}
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        enabled = bool(data.get("enabled", True))
        skills = data.get("skills_allowlist") or []
        return {
            **probe,
            "kind": "team_wsl_health",
            "enabled": enabled,
            "skills": len(skills) if isinstance(skills, list) else 0,
            "pending": data.get("pending"),
            "ok": enabled and bool(skills),
        }
    except (json.JSONDecodeError, OSError, urllib.error.URLError, TimeoutError) as exc:
        return {**probe, "kind": "team_wsl_health", "ok": False, "parse_error": str(exc)[:120]}


def _probe_team_wsl_bridge(url: str, *, timeout: float = 4.0) -> dict[str, Any]:
    """Pont WSL actif côté orchestrateur (complète la sonde TCP SSH du CT executor)."""
    probe = _probe_team_wsl_health(url, timeout=timeout)
    probe["kind"] = "team_wsl_bridge"
    return probe


def _probe_http(url: str, *, timeout: float = 4.0) -> dict[str, Any]:
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json,text/html,*/*"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(512).decode("utf-8", errors="replace")
            return {
                "url": url,
                "ok": 200 <= resp.status < 300,
                "status": resp.status,
                "body_preview": body[:160],
            }
    except urllib.error.HTTPError as exc:
        return {"url": url, "ok": False, "status": exc.code, "error": str(exc)[:160]}
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        return {"url": url, "ok": False, "status": None, "error": str(exc)[:160]}


def _probe_ollama_tags(url: str, *, timeout: float = 6.0) -> dict[str, Any]:
    probe = _probe_http(url, timeout=timeout)
    if not probe.get("ok"):
        return {**probe, "kind": "ollama_tags", "model_count": 0, "model_names": []}
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        models = data.get("models") if isinstance(data, dict) else []
        names: list[str] = []
        if isinstance(models, list):
            for m in models:
                if isinstance(m, dict) and m.get("name"):
                    names.append(str(m["name"]))
        return {
            **probe,
            "kind": "ollama_tags",
            "model_count": len(names),
            "model_names": names[:24],
        }
    except (json.JSONDecodeError, OSError, urllib.error.URLError, TimeoutError) as exc:
        return {**probe, "kind": "ollama_tags", "model_count": 0, "model_names": [], "parse_error": str(exc)[:120]}


def check_light_111_swap(host: str = "192.168.0.111", *, timeout: float = 4.0) -> dict[str, Any]:
    """Sonde l'état swap/mémoire du CT 111 (NUC ollama-light) sous la gouvernance d'Atlas."""
    import subprocess

    cmd = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=3",
        f"root@{host}",
        "free -b | awk '/^Mem:/{print \"mem_total=\"$2\" mem_avail=\"$7} /^Swap:/{print \"swap_total=\"$2\" swap_used=\"$3}'",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if proc.returncode != 0:
            return {"ok": False, "error": (proc.stderr or "").strip()[:160], "host": host}
        mem_total = mem_avail = swap_total = swap_used = 0
        for line in proc.stdout.splitlines():
            for kv in line.strip().split():
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    if k == "mem_total":
                        mem_total = int(v or 0)
                    elif k == "mem_avail":
                        mem_avail = int(v or 0)
                    elif k == "swap_total":
                        swap_total = int(v or 0)
                    elif k == "swap_used":
                        swap_used = int(v or 0)
        swap_pct = round(100.0 * swap_used / swap_total, 1) if swap_total else 0.0
        avail_pct = round(100.0 * mem_avail / mem_total, 1) if mem_total else 0.0
        sticky = bool(swap_pct >= 85.0 and avail_pct >= 15.0)
        return {
            "ok": True,
            "host": host,
            "swap_used_b": swap_used,
            "swap_total_b": swap_total,
            "swap_used_pct": swap_pct,
            "mem_avail_pct": avail_pct,
            "sticky_swap": sticky,
            "status": "critical" if swap_pct >= 90.0 else ("warn" if swap_pct >= 50.0 else "ok"),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:160], "host": host}


def remediate_light_111_swap(
    *,
    host: str = "192.168.0.111",
    proxmox_host: str = "192.168.0.200",
    dry_run: bool = False,
    timeout: float = 12.0,
) -> dict[str, Any]:
    """Remédiation du swap saturé sur CT 111 (Atlas admin_infra).

    Action:
    1. Redémarre lbg-laya-serve.service sur CT 111 (libère immédiatement le swap collé sans toucher à Ollama).
    2. S'assure que vm.swappiness=10 est appliqué sur l'hôte Proxmox 192.168.0.200 (CT unprivileged = RO).
    3. Vérifie l'état de libération du swap après intervention.
    """
    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "agent": "Atlas",
            "role": "admin_infra",
            "action": "remediate_light_111_swap",
            "steps": [
                f"ssh root@{host} 'systemctl restart lbg-laya-serve'",
                f"ssh root@{proxmox_host} 'sysctl -w vm.swappiness=10 && echo vm.swappiness=10 > /etc/sysctl.d/99-swappiness.conf'",
            ],
            "note": "Dry-run : aucune commande exécutée.",
        }

    import subprocess

    results: list[dict[str, Any]] = []

    # 1. Restart lbg-laya-serve sur 111
    restart_cmd = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=5",
        f"root@{host}",
        "systemctl restart lbg-laya-serve",
    ]
    try:
        proc = subprocess.run(restart_cmd, capture_output=True, text=True, timeout=timeout)
        restart_ok = proc.returncode == 0
        results.append({
            "step": "restart_laya_serve",
            "target": host,
            "ok": restart_ok,
            "error": (proc.stderr or "").strip()[:160] if not restart_ok else "",
        })
    except Exception as exc:
        results.append({"step": "restart_laya_serve", "target": host, "ok": False, "error": str(exc)[:160]})

    # 2. Fix swappiness sur l'hôte Proxmox
    swp_cmd = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=5",
        f"root@{proxmox_host}",
        "sysctl -w vm.swappiness=10; echo 'vm.swappiness=10' > /etc/sysctl.d/99-swappiness.conf",
    ]
    try:
        proc = subprocess.run(swp_cmd, capture_output=True, text=True, timeout=timeout)
        results.append({
            "step": "set_swappiness_proxmox",
            "target": proxmox_host,
            "ok": proc.returncode == 0,
        })
    except Exception as exc:
        results.append({"step": "set_swappiness_proxmox", "target": proxmox_host, "ok": False, "error": str(exc)[:160]})

    # 3. Re-sonde après remédiation
    post_check = check_light_111_swap(host=host, timeout=5.0)

    overall_ok = all(bool(r.get("ok")) for r in results) and (
        float(post_check.get("swap_used_pct", 100.0) or 0) < 50.0 if post_check.get("ok") else True
    )
    return {
        "ok": overall_ok,
        "agent": "Atlas",
        "role": "admin_infra",
        "action": "remediate_light_111_swap",
        "steps": results,
        "post_check": post_check,
        "summary": (
            f"Remédiation swap 111 par Atlas : {'SUCCÈS' if overall_ok else 'ATTENTION'} — "
            f"swap used={post_check.get('swap_used_pct', '?')}% (mem avail={post_check.get('mem_avail_pct', '?')}%)"
        ),
    }


def audit_platform_host(spec: dict[str, Any]) -> dict[str, Any]:
    probes_out: list[dict[str, Any]] = []
    for probe in spec.get("probes") or []:
        if not isinstance(probe, dict):
            continue
        url = str(probe.get("url") or "")
        kind = str(probe.get("kind") or "http")
        host = str(spec.get("host") or "")
        if kind == "ollama_tags":
            probes_out.append(_probe_ollama_tags(url))
        elif kind == "tcp":
            probes_out.append(_probe_tcp(host, int(probe.get("port") or 22)))
        elif kind == "team_wsl_health":
            probes_out.append(_probe_team_wsl_health(url))
        elif kind == "team_wsl_bridge":
            probes_out.append(_probe_team_wsl_bridge(url))
        else:
            probes_out.append({**_probe_http(url), "kind": kind})
    ok = all(bool(p.get("ok")) for p in probes_out) if probes_out else False
    return {
        "id": spec.get("id"),
        "label": spec.get("label"),
        "host": spec.get("host"),
        "perimeter_id": spec.get("perimeter_id"),
        "role": spec.get("role"),
        "required": bool(spec.get("required", True)),
        "ok": ok,
        "probes": probes_out,
        "ollama_primary": bool(spec.get("ollama_primary")),
        "ollama_tier": spec.get("ollama_tier"),
    }


def audit_admin_infra_platform() -> dict[str, Any]:
    """Audit multi-hôtes Atlas — dual LLM 110/111 + runtime + Groq dialogue fast."""
    ip111 = _host_ip(
        "LBG_LAN_HOST_LLM_LIGHT",
        os.environ.get("LBG_REASON_LIGHT_BASE_URL", "http://192.168.0.111:11434")
        .replace("http://", "")
        .replace("https://", "")
        .split(":")[0]
        or "192.168.0.111",
    )
    hosts = [audit_platform_host(spec) for spec in platform_host_specs()]
    ollama = audit_ollama_lan()
    dialogue_fast = audit_dialogue_fast_cloud(probe=True)
    required_hosts = [h for h in hosts if h.get("required", True)]
    host_ok = sum(1 for h in required_hosts if h.get("ok"))
    hosts_total = len(required_hosts)
    gaps: list[str] = []
    for h in hosts:
        if h.get("required", True) and not h.get("ok"):
            gaps.append(f"{h.get('perimeter_id')}: {h.get('id')} probe KO")
        elif not h.get("required", True) and not h.get("ok"):
            gaps.append(f"optional-{h.get('perimeter_id')}: {h.get('id')} probe KO")
    if ollama.get("gaps"):
        for g in ollama["gaps"]:
            gaps.append(f"ollama-config: {g}")
    for g in dialogue_fast.get("gaps") or []:
        gaps.append(f"dialogue-fast-groq: {g}")
    for w in dialogue_fast.get("warnings") or []:
        gaps.append(f"dialogue-fast-groq-warning: {w}")

    recommendations: list[str] = list(ollama.get("recommendations") or [])
    recommendations.extend(dialogue_fast.get("recommendations") or [])
    if not any(h.get("id") == "llm_light_111" and h.get("ok") for h in hosts):
        recommendations.append(
            "111 light KO — vérifier CT ollama-light sur Proxmox 200 ; router/json basculent en failover 110."
        )
    if not any(h.get("id") == "llm_heavy_110" and h.get("ok") for h in hosts):
        recommendations.append("110 heavy KO — vérifier CT 110 ollama-110 sur Proxmox 201.")
    if not any(h.get("id") == "executor_141" and h.get("ok") for h in hosts):
        recommendations.append(
            "141 executor : vérifier CT lbg-executor (SSH :22) et service lbg-lan-executor (poll Team WSL)."
        )
    if not any(h.get("id") == "hands_143" and h.get("ok") for h in hosts):
        recommendations.append(
            "143 hands (Omarchy) : vérifier VM lbg-omarchy sur Proxmox 201 (SSH :22) et lbg-omarchy-agent :5005/healthz."
        )
    if not any(h.get("id") == "precu_245" and h.get("ok") for h in hosts):
        recommendations.append(
            "245 PreCU (optionnel) : sandbox éteint ou healthz :8050 down — hors alerte périmètre."
        )
    if not any(h.get("id") == "prime_246" and h.get("ok") for h in hosts):
        recommendations.append(
            "246 Prime : vérifier lbg-prime-hub :8787/healthz (Godot G5+ unifié)."
        )
    if host_ok < hosts_total:
        recommendations.append("Périmètre Atlas incomplet — corriger les sondes critiques avant bench long.")

    ip140 = _host_ip("LBG_LAN_HOST_CORE", "192.168.0.140")
    orch_url = os.environ.get("LBG_ORCHESTRATOR_URL", f"http://{ip140}:8010").strip().rstrip("/")
    topology = {
        "llm_heavy": "192.168.0.110:11434 (CT ollama, code=qwen3-coder-abliterated:30b, pm/dialogue=gemma-4-abliterated:12b-qat, forge=E4b-qat)",
        "llm_light": "192.168.0.111:11434 (NUC CT, Clean qwen3.5:2B / Fast qwen3.5:0.8B)",
        "pilot": "192.168.0.140:8080 (Nginx Pilot canonique — proxy API locale)",
        "lan_executor": "192.168.0.141 (CT lbg-executor — poll /v1/team/wsl/poll, remplace WSL .10)",
        "lan_hands": "192.168.0.143 (VM lbg-omarchy — agent_ia_linux :5005, inbox /var/lib/lbg-hands/inbox)",
        "front_legacy": "décommissionné (.112 retiré — Pilot Nginx = .140:8080)",
        "routing": "LBG_REASON_LIGHT_BASE_URL → 111 ; LBG_REASON_LOCAL_BASE_URL → 110",
        "wsl_bridge": f"{orch_url}/v1/team/wsl/health",
    }

    # Sonde swap / mémoire CT 111 sous la gouvernance d'Atlas
    swap_111 = check_light_111_swap(ip111)
    if swap_111.get("ok"):
        if swap_111.get("sticky_swap") or float(swap_111.get("swap_used_pct", 0) or 0) >= 80.0:
            gaps.append(f"111-swap: swap saturé ({swap_111.get('swap_used_pct')}%) sur CT 111 (ollama-light)")
            recommendations.append(
                "Atlas remédiation swap 111 : redémarrer lbg-laya-serve sur CT 111 (libère ~2 Go de swap collé) "
                "et s'assurer que vm.swappiness=10 sur Proxmox .200."
            )

    return {
        "ok": host_ok == hosts_total
        and bool(ollama.get("ok", False) or not ollama.get("error"))
        and bool(dialogue_fast.get("ok", True) or dialogue_fast.get("skipped")),
        "track": "admin_infra_platform",
        "perimeter": admin_infra_perimeter(),
        "hosts_ok": host_ok,
        "hosts_total": hosts_total,
        "hosts": hosts,
        "topology": topology,
        "ollama_primary": ollama,
        "dialogue_fast_groq": dialogue_fast,
        "light_111_swap": swap_111,
        "gaps": gaps,
        "recommendations": recommendations,
    }
