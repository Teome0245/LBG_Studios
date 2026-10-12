"""Sonde Google Cast / Nest Mini (read-only Eureka) + annonce TTS optionnelle.

Le Nest Mini (.75 « Séjour ») expose le protocole Cast (ports 8008/8009/8443).
- ``probe_cast_speaker`` : HTTP ``/setup/eureka_info`` — toujours disponible.
- ``announce_cast_text`` : nécessite ``pychromecast`` (optionnel) + URL audio
  (Piper local ou Google TTS) — L2 / dry-run par défaut.
"""

from __future__ import annotations

import os
import urllib.parse
from typing import Any

import httpx


def cast_hosts_from_env() -> list[str]:
    raw = os.environ.get("LBG_CAST_SPEAKER_HOSTS", "").strip()
    if raw:
        return [h.strip() for h in raw.split(",") if h.strip()]
    single = os.environ.get("LBG_NEST_MINI_HOST", "192.168.0.75").strip()
    return [single] if single else []


def cast_probe_enabled() -> bool:
    raw = os.environ.get("LBG_CAST_PROBE_ENABLED", "1").strip().lower()
    return raw in ("1", "true", "yes", "on")


def _timeout_s() -> float:
    try:
        return max(0.5, float(os.environ.get("LBG_CAST_PROBE_TIMEOUT_S", "2.0").strip()))
    except ValueError:
        return 2.0


def probe_cast_speaker(host: str, *, timeout_s: float | None = None) -> dict[str, Any]:
    """Lit Eureka info (Cast) — pas d’auth."""
    host = (host or "").strip()
    if not host:
        return {"ok": False, "error": "empty_host"}
    t = _timeout_s() if timeout_s is None else timeout_s
    urls = [
        f"http://{host}:8008/setup/eureka_info",
        f"https://{host}:8443/setup/eureka_info",
    ]
    last_err = ""
    for url in urls:
        try:
            with httpx.Client(timeout=t, verify=False, follow_redirects=True) as client:
                r = client.get(url)
            if r.status_code >= 400:
                last_err = f"HTTP {r.status_code}"
                continue
            data = r.json()
            if not isinstance(data, dict):
                last_err = "invalid_json"
                continue
            name = str(data.get("name") or "").strip() or host
            return {
                "ok": True,
                "host": host,
                "url": url,
                "name": name,
                "label": f"cast:{name}",
                "role": "cast",
                "device_hint": "google-cast",
                "ip_address": data.get("ip_address") or host,
                "mac_address": data.get("mac_address"),
                "locale": data.get("locale"),
                "ssid": data.get("ssid"),
                "connected": data.get("connected"),
                "build_version": data.get("build_version"),
                "cast_build_revision": data.get("cast_build_revision"),
                "uptime": data.get("uptime"),
                "source": "cast_eureka",
            }
        except Exception as exc:  # noqa: BLE001
            last_err = f"{type(exc).__name__}: {exc}"
    return {"ok": False, "host": host, "error": last_err or "unreachable", "role": "cast"}


def probe_cast_speakers(hosts: list[str] | None = None) -> dict[str, Any]:
    if not cast_probe_enabled():
        return {"ok": True, "skipped": True, "reason": "LBG_CAST_PROBE_ENABLED=0", "speakers": []}
    targets = hosts if hosts is not None else cast_hosts_from_env()
    speakers = [probe_cast_speaker(h) for h in targets]
    n_ok = sum(1 for s in speakers if s.get("ok"))
    return {
        "ok": n_ok > 0 or not targets,
        "n_ok": n_ok,
        "n_hosts": len(targets),
        "speakers": speakers,
    }


def google_tts_audio_url(text: str, *, lang: str = "fr") -> str:
    """URL audio Google Translate TTS (usage lab ; quota non garanti)."""
    q = urllib.parse.quote(text[:200])
    return (
        f"https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob"
        f"&tl={urllib.parse.quote(lang)}&q={q}"
    )


def announce_cast_text(
    text: str,
    *,
    host: str | None = None,
    dry_run: bool = True,
    audio_url: str | None = None,
) -> dict[str, Any]:
    """Cast un clip audio sur le Nest (nécessite pychromecast)."""
    target = (host or (cast_hosts_from_env() or [""])[0]).strip()
    if not target:
        return {"ok": False, "error": "no_cast_host"}
    msg = (text or "").strip()
    if not msg:
        return {"ok": False, "error": "empty_text"}
    url = audio_url or google_tts_audio_url(msg)
    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "host": target,
            "text": msg,
            "audio_url": url,
            "hint": "Réel : dry_run=False + pip install pychromecast",
        }
    try:
        import pychromecast
        from pychromecast.controllers.media import MediaController
    except ImportError:
        return {
            "ok": False,
            "host": target,
            "error": "pychromecast_missing",
            "hint": "pip install pychromecast (venv agents)",
        }
    try:
        casts, browser = pychromecast.get_listed_chromecasts(friendly_names=None, discovery_timeout=5)
        chosen = None
        for c in casts or []:
            try:
                if str(getattr(c, "host", None) or getattr(getattr(c, "socket_client", None), "host", "")) == target:
                    chosen = c
                    break
                # fallback IP via status
                ip = getattr(getattr(c, "status", None), "host", None) or getattr(c, "host", None)
                if ip == target:
                    chosen = c
                    break
            except Exception:
                continue
        if chosen is None and casts:
            # Match by known IP via cast_info
            for c in casts:
                info = getattr(c, "cast_info", None)
                if info and str(getattr(info, "host", "")) == target:
                    chosen = c
                    break
        if chosen is None:
            try:
                browser.stop_discovery()
            except Exception:
                pass
            return {"ok": False, "host": target, "error": "cast_not_found_on_lan"}
        chosen.wait(timeout=8)
        mc: MediaController = chosen.media_controller
        mc.play_media(url, "audio/mp3")
        mc.block_until_active(timeout=10)
        try:
            browser.stop_discovery()
        except Exception:
            pass
        return {"ok": True, "dry_run": False, "host": target, "text": msg, "audio_url": url}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "host": target, "error": f"{type(exc).__name__}: {exc}"}


def format_cast_probe_text(probe: dict[str, Any]) -> str:
    if probe.get("skipped"):
        return "Cast / Nest : sonde désactivée"
    lines = [f"Cast / Nest — {probe.get('n_ok', 0)}/{probe.get('n_hosts', 0)} OK"]
    for s in probe.get("speakers") or []:
        if not isinstance(s, dict):
            continue
        mark = "OK" if s.get("ok") else "KO"
        lines.append(
            f"  • {s.get('name') or s.get('host')} ({s.get('host')}) — {mark}"
            + (f" locale={s.get('locale')}" if s.get("locale") else "")
        )
        if s.get("error"):
            lines.append(f"      {s.get('error')}")
    return "\n".join(lines)
