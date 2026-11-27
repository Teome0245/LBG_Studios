"""
physical_presence.py — Détecteur de présence physique de Teome via la Freebox (Wi-Fi/LAN).

Permet à Gladys / Lia de savoir en direct si Teome est au bureau / à domicile
en vérifiant la joignabilité de ses terminaux (Sds-Phone, REDMI, PC-Teome .10).
"""

from __future__ import annotations

import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger("lbg.physical_presence")

# Match questions sur la présence réelle de Teome ou l'état physique du réseau
_PHYSICAL_PRESENCE_RE = re.compile(
    r"(?i)\b("
    r"suis[- ]je\s+(?:l[àa]|au\s+bureau|chez\s+moi|[àa]\s+la\s+maison)|"
    r"je\s+suis\s+(?:l[àa]|au\s+bureau|chez\s+moi|[àa]\s+la\s+maison)|"
    r"est[- ]ce\s+que\s+je\s+suis\s+(?:l[àa]|au\s+bureau|chez\s+moi|[àa]\s+la\s+maison)|"
    r"pr[ée]sence\s+(?:physique|teome|bureau|maison)|"
    r"qui\s+est\s+(?:l[àa]|au\s+bureau|[àa]\s+la\s+maison)|"
    r"d[ée]tect(?:eur|ion)\s+de\s+pr[ée]sence|"
    r"t[ée]l[ée]phones?\s+connect[ée]s?|"
    r"appareils?\s+connect[ée]s?|"
    r"wifi\s+freebox|freebox\s+lan|statut\s+freebox|"
    r"nest\s+mini\s+connect[ée]|"
    r"suis[- ]je\s+connect[ée]|"
    r"es[- ]tu\s+au\s+courant\s+que\s+je\s+suis\s+l[àa]"
    r")\b"
)

# Appareils personnels attribués à Teome
_TEOME_DEVICE_PATTERNS = [
    "sds-phone",
    "redmi",
    "teome",
    "pc-sdesharches",
    "6a:42:38:e9:4c:09",
    "be:dd:cd:c1:1c:99",
    "04:7c:16:cd:98:a5",
]

# Cache local de présence (TTL 30 secondes pour fluidité)
_PRESENCE_CACHE: dict[str, Any] = {"timestamp": 0.0, "data": {}}


def _load_freebox_secrets() -> None:
    """Charge automatiquement les secrets Freebox si non configurés dans l'environnement."""
    if os.getenv("LBG_FREEBOX_APP_TOKEN"):
        return
    candidates = [
        Path(__file__).resolve().parents[2] / "infra" / "secrets" / "freebox.env.local",
        Path(__file__).resolve().parents[2] / "infra" / "secrets" / "lbg.env",
        Path("/etc/lbg-ia-mmo.env"),
    ]
    for p in candidates:
        if p.exists():
            try:
                for line in p.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        if k.startswith("LBG_FREEBOX_"):
                            os.environ[k] = v.strip("'\" \t")
                if os.getenv("LBG_FREEBOX_APP_TOKEN"):
                    break
            except Exception as e:
                logger.debug("Erreur lecture secret %s: %s", p, e)


def _get_freebox_client():
    """Import dynamique du client Freebox."""
    _load_freebox_secrets()
    # 1) Essayer import direct local overlay / service
    try:
        from src.services import freebox_client as fb
        return fb
    except ImportError:
        pass
    try:
        import freebox_client as fb  # type: ignore
        return fb
    except ImportError:
        pass
    # 2) Essayer via packages/cortex/agents/src
    agents_src = Path(__file__).resolve().parents[2] / "agents" / "src"
    if agents_src.exists() and str(agents_src) not in sys.path:
        sys.path.insert(0, str(agents_src))
    try:
        import lbg_agents.freebox_client as fb
        return fb
    except ImportError:
        return None


def wants_physical_presence(prompt: str) -> bool:
    """Détecte si l'utilisateur interroge sa présence physique ou le statut LAN Freebox."""
    if not prompt:
        return False
    return bool(_PHYSICAL_PRESENCE_RE.search(prompt))


def get_physical_presence(*, force_refresh: bool = False) -> dict[str, Any]:
    """Interroge la Freebox pour déterminer la présence physique des terminaux de Teome."""
    now = time.monotonic()
    if not force_refresh and (now - _PRESENCE_CACHE["timestamp"]) < 30.0 and _PRESENCE_CACHE["data"]:
        return _PRESENCE_CACHE["data"]

    fb = _get_freebox_client()
    if fb is None or not fb.freebox_configured():
        return {
            "ok": False,
            "error": "freebox_non_configuree",
            "teome_present": False,
            "devices": [],
            "timestamp": time.time(),
        }

    try:
        data = fb.probe_freebox(include_lan=True)
        if not data.get("ok"):
            return {
                "ok": False,
                "error": str(data.get("error") or "sonde_echouee"),
                "teome_present": False,
                "devices": [],
                "timestamp": time.time(),
            }

        hosts = data.get("lan_hosts", [])
        active_teome_devices: list[dict[str, Any]] = []
        nest_mini_active = False
        switch_active = False
        total_active_lan = 0

        for h in hosts:
            is_active = bool(h.get("active") or h.get("reachable"))
            if is_active:
                total_active_lan += 1
            name = str(h.get("name") or "").lower()
            mac = str(h.get("mac") or "").lower()
            ip = h.get("ipv4")
            ip_str = ip[0] if isinstance(ip, list) and ip else str(ip or "")

            if "nest" in name or "d4:f5:47:16:23:64" in mac:
                if is_active:
                    nest_mini_active = True
            if "switch" in name or "ec:c4:0d:bf:7e:bf" in mac:
                if is_active:
                    switch_active = True

            # Détection des terminaux Teome
            is_teome_device = any(
                pat in name or pat in mac for pat in _TEOME_DEVICE_PATTERNS
            )
            if is_teome_device and is_active:
                active_teome_devices.append({
                    "name": h.get("name") or "Terminal Teome",
                    "ip": ip_str,
                    "mac": mac,
                    "vendor": h.get("vendor") or "",
                })

        teome_present = len(active_teome_devices) > 0

        res = {
            "ok": True,
            "teome_present": teome_present,
            "active_devices": active_teome_devices,
            "box_model": data.get("box_model", "Freebox"),
            "total_active_lan": total_active_lan,
            "nest_mini_active": nest_mini_active,
            "switch_active": switch_active,
            "timestamp": time.time(),
        }
        _PRESENCE_CACHE["timestamp"] = now
        _PRESENCE_CACHE["data"] = res
        return res
    except Exception as e:
        logger.warning("Erreur lors de la détection de présence Freebox: %s", e)
        return {
            "ok": False,
            "error": str(e),
            "teome_present": False,
            "devices": [],
            "timestamp": time.time(),
        }


def format_physical_presence_causerie(data: dict[str, Any], prompt: str = "") -> str:
    """Met en forme la télémétrie de présence Freebox en rapport immersif et précis pour Gladys."""
    if not data.get("ok"):
        err = data.get("error", "indisponible")
        return (
            "SENTINELLE FREEBOX : La sonde réseau locale est actuellement inaccessible (%s). "
            "Je ne peux pas confirmer ta présence physique via le Wi-Fi." % err
        )

    present = bool(data.get("teome_present", False))
    devs = data.get("active_devices", [])
    box = data.get("box_model", "Freebox")
    total_active = data.get("total_active_lan", 0)
    nest = bool(data.get("nest_mini_active", False))

    lines = []
    if present:
        dev_names = ", ".join(d["name"] for d in devs)
        lines.append("Oui Teome, je confirme que tu es bien là au bureau !")
        lines.append("- Détection Freebox (%s) : tes terminaux sont connectés en direct (%s)." % (box, dev_names))
    else:
        lines.append("D'après la Freebox (%s), aucun de tes terminaux habituels (Sds-Phone, REDMI, PC-Teome) n'est actif sur le réseau." % box)
        lines.append("- Statut : absent du bureau ou terminaux hors ligne.")

    lines.append("- Écosystème physique : %d appareils connectés sur le LAN." % total_active)
    if nest:
        lines.append("- Ambiance : Google Nest Mini actif sur le réseau (192.168.0.75).")

    return "\n".join(lines)


async def attach_physical_presence_if_needed(
    seed: dict[str, Any],
    *,
    prompt: str = "",
    lab: bool = False,
) -> dict[str, Any]:
    """Injecte la détection de présence physique dans le contexte du Compagnon."""
    data = get_physical_presence()
    report = format_physical_presence_causerie(data, prompt=prompt)

    out = dict(seed)
    out["content"] = report
    out["source"] = "physical_presence"
    out["physical_presence"] = {
        "ok": data.get("ok", False),
        "present": data.get("teome_present", False),
        "devices": [d["name"] for d in data.get("active_devices", [])],
        "total_active": data.get("total_active_lan", 0),
    }
    return out
