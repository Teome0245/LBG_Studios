"""Santé agrégée Pilot et proxies Ollama / LBG_IA."""

from __future__ import annotations

import asyncio
import socket
import time
from typing import Any

from fastapi import APIRouter

from config import get_settings

from ._common import LOG, httpx, lbg_ia_backend_base_url, pilot_lbg_ia_http_timeout_s
from ._models import LbgIaStatusResponse, OkEnvelope, PilotStatusResponse
from world_display import enrich_bot_zone_fields, PLANET_DISPLAY, HUB_CITY

router = APIRouter()


async def _fetch_player_ia_runtime(*, timeout_s: float = 2.0) -> dict[str, Any]:
    """
    Lecture seule sidecar Prime (:8791) — snapshots Lia/Nix/Mira/Kael.
    Distinct de LBG_MMO_SERVER_URL (souvent PreCU / autre service).
    """
    settings = get_settings()
    sidecar = settings.core3_sidecar_base()
    bots = settings.core3_ia_bot_ids()
    out: dict[str, Any] = {
        "ok": False,
        "sidecar_url": sidecar,
        "sidecar_ok": False,
        "conductor_agent_id": "studio_player_ia_choeur",
        "bots": [],
        "online_count": 0,
        "ts": time.time(),
    }
    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            try:
                hr = await client.get(f"{sidecar}/healthz")
                health_body: dict[str, Any] = {}
                if hr.content:
                    try:
                        raw_h = hr.json()
                        if isinstance(raw_h, dict):
                            health_body = raw_h
                    except ValueError:
                        pass
                sidecar_ok = hr.status_code == 200 and health_body.get("ok") is not False
                out["sidecar_ok"] = sidecar_ok
                out["sidecar_status"] = hr.status_code
            except Exception as e:
                out["sidecar_ok"] = False
                out["error"] = str(e)
                return out

            rows: list[dict[str, Any]] = []
            online_count = 0
            for bot in bots:
                display = bot[:1].upper() + bot[1:] if bot else bot
                entry: dict[str, Any] = {
                    "id": bot,
                    "display_name": display,
                    "online": False,
                    "in_world": False,
                    "zone": None,
                    "age_s": None,
                    "ok": False,
                }
                try:
                    sr = await client.get(f"{sidecar}/v1/player-snapshot", params={"player": display})
                    snap: dict[str, Any] = {}
                    if sr.content:
                        try:
                            raw = sr.json()
                            if isinstance(raw, dict):
                                inner = raw.get("snapshot")
                                snap = inner if isinstance(inner, dict) else raw
                        except ValueError:
                            pass
                    online = bool(snap.get("online") or snap.get("connected"))
                    zone = snap.get("zone")
                    age = snap.get("age_s")
                    try:
                        age_f = float(age) if age is not None else None
                    except (TypeError, ValueError):
                        age_f = None
                    # Fresh snapshot + online = « en jeu » ; offline = hors monde (café métier).
                    fresh = age_f is None or age_f < 60.0
                    in_world = online and fresh
                    entry.update(
                        {
                            "online": online,
                            "in_world": in_world,
                            "zone": zone if isinstance(zone, str) else None,
                            "age_s": age_f,
                            "ok": sr.status_code == 200 and online,
                            "status": sr.status_code,
                            "x": snap.get("x"),
                            "y": snap.get("y"),
                            "z": snap.get("z"),
                        }
                    )
                    if online:
                        online_count += 1
                except Exception as e:
                    entry["error"] = str(e)
                rows.append(enrich_bot_zone_fields(entry))

            out["bots"] = rows
            out["online_count"] = online_count
            out["ok"] = bool(out["sidecar_ok"]) and online_count > 0
            out["planet_display"] = PLANET_DISPLAY
            out["hub_city"] = HUB_CITY
            # Compat pastilles historiques Accueil/Jobs
            out["bots_status"] = {
                str(b["id"]): ("online" if b.get("online") else "offline") for b in rows
            }
    except Exception as e:
        LOG.warning("pilot.player_ia_runtime error sidecar=%s err=%s", sidecar, e)
        out["error"] = str(e)
    return out


@router.get("/player-ia/runtime", tags=["pilot"], response_model=OkEnvelope)
async def pilot_player_ia_runtime() -> dict[str, object]:
    """Snapshots joueurs IA Prime (lecture seule) pour le bureau Campus."""
    runtime = await _fetch_player_ia_runtime(timeout_s=2.0)
    return {"ok": True, **runtime}

@router.get("/ollama/tags", tags=["pilot"], response_model=OkEnvelope)
async def pilot_proxy_ollama_tags() -> dict[str, object]:
    """
    Proxy same-origin vers l'instance Ollama (normalement VM 110 sur le port 11434).
    Permet de lister les modèles disponibles via /api/tags.
    """
    ollama_base = get_settings().ollama_base_url.strip().rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{ollama_base}/api/tags")
        if r.status_code != 200:
            return {"ok": False, "error": f"Ollama HTTP {r.status_code}", "body": r.text[:500]}
        try:
            data = r.json()
        except ValueError:
            return {"ok": False, "error": "corps non JSON", "body": r.text[:500]}
        return data if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/status", tags=["pilot"], response_model=PilotStatusResponse)
async def pilot_aggregate_status() -> dict[str, object]:
    """
    Santé agrégée pour l’UI de pilotage : évite au navigateur d’appeler
    l’orchestrator en cross-origin (CORS).
    """
    orch_url = get_settings().orchestrator_base()
    orch_state: str = "unknown"
    orch_detail: str | None = None
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{orch_url}/healthz")
        if r.status_code == 200:
            orch_state = "ok"
        else:
            orch_state = "error"
            orch_detail = f"HTTP {r.status_code}"
    except Exception as e:
        orch_state = "error"
        orch_detail = str(e)

    dialogue_url_raw = get_settings().lbg_agent_dialogue_url.strip()
    dialogue_state: str
    dialogue_detail: str | None = None
    dialogue_probe_url: str | None = None
    dialogue_info: dict[str, object] | None = None

    if not dialogue_url_raw:
        dialogue_state = "skipped"
        dialogue_detail = "LBG_AGENT_DIALOGUE_URL non défini (stub dialogue côté orchestrator)"
    else:
        dialogue_probe_url = dialogue_url_raw.rstrip("/") + "/healthz"
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(dialogue_probe_url)
            if r.status_code == 200:
                dialogue_state = "ok"
                try:
                    raw = r.json()
                    if isinstance(raw, dict):
                        dialogue_info = raw
                    else:
                        dialogue_detail = "healthz: JSON attendu (objet), reçu autre type"
                except Exception:
                    dialogue_detail = "healthz: corps non JSON"
            else:
                dialogue_state = "error"
                dialogue_detail = f"HTTP {r.status_code}"
        except Exception as e:
            dialogue_state = "error"
            dialogue_detail = str(e)

    quests_url_raw = get_settings().lbg_agent_quests_url.strip()
    quests_state: str
    quests_detail: str | None = None
    quests_probe_url: str | None = None
    quests_info: dict[str, object] | None = None

    if not quests_url_raw:
        quests_state = "skipped"
        quests_detail = "LBG_AGENT_QUESTS_URL non défini (stub quests côté orchestrator)"
    else:
        quests_probe_url = quests_url_raw.rstrip("/") + "/healthz"
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(quests_probe_url)
            if r.status_code == 200:
                quests_state = "ok"
                try:
                    raw = r.json()
                    if isinstance(raw, dict):
                        quests_info = raw
                    else:
                        quests_detail = "healthz: JSON attendu (objet), reçu autre type"
                except Exception:
                    quests_detail = "healthz: corps non JSON"
            else:
                quests_state = "error"
                quests_detail = f"HTTP {r.status_code}"
        except Exception as e:
            quests_state = "error"
            quests_detail = str(e)

    combat_url_raw = get_settings().lbg_agent_combat_url.strip()
    combat_state: str
    combat_detail: str | None = None
    combat_probe_url: str | None = None
    combat_info: dict[str, object] | None = None

    if not combat_url_raw:
        combat_state = "skipped"
        combat_detail = "LBG_AGENT_COMBAT_URL non défini (stub combat côté orchestrator)"
    else:
        combat_probe_url = combat_url_raw.rstrip("/") + "/healthz"
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(combat_probe_url)
            if r.status_code == 200:
                combat_state = "ok"
                try:
                    raw = r.json()
                    if isinstance(raw, dict):
                        combat_info = raw
                    else:
                        combat_detail = "healthz: JSON attendu (objet), reçu autre type"
                except Exception:
                    combat_detail = "healthz: corps non JSON"
            else:
                combat_state = "error"
                combat_detail = f"HTTP {r.status_code}"
        except Exception as e:
            combat_state = "error"
            combat_detail = str(e)

    pm_url_raw = get_settings().lbg_agent_pm_url.strip()
    pm_state: str
    pm_detail: str | None = None
    pm_probe_url: str | None = None
    pm_info: dict[str, object] | None = None

    if not pm_url_raw:
        pm_state = "skipped"
        pm_detail = "LBG_AGENT_PM_URL non défini (stub PM côté orchestrator)"
    else:
        pm_probe_url = pm_url_raw.rstrip("/") + "/healthz"
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(pm_probe_url)
            if r.status_code == 200:
                pm_state = "ok"
                try:
                    raw = r.json()
                    if isinstance(raw, dict):
                        pm_info = raw
                    else:
                        pm_detail = "healthz: JSON attendu (objet), reçu autre type"
                except Exception:
                    pm_detail = "healthz: corps non JSON"
            else:
                pm_state = "error"
                pm_detail = f"HTTP {r.status_code}"
        except Exception as e:
            pm_state = "error"
            pm_detail = str(e)

    desktop_url_raw = get_settings().lbg_agent_desktop_url.strip()
    desktop_state: str
    desktop_detail: str | None = None
    desktop_probe_url: str | None = None
    desktop_info: dict[str, object] | None = None

    if not desktop_url_raw:
        desktop_state = "skipped"
        desktop_detail = "LBG_AGENT_DESKTOP_URL non défini (desktop_control indisponible)"
    else:
        desktop_probe_url = desktop_url_raw.rstrip("/") + "/healthz"
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(desktop_probe_url)
            if r.status_code == 200:
                desktop_state = "ok"
                try:
                    raw = r.json()
                    if isinstance(raw, dict):
                        desktop_info = raw
                    else:
                        desktop_detail = "healthz: JSON attendu (objet), reçu autre type"
                except Exception:
                    desktop_detail = "healthz: corps non JSON"
            else:
                desktop_state = "error"
                desktop_detail = f"HTTP {r.status_code}"
        except Exception as e:
            desktop_state = "error"
            desktop_detail = str(e)

    mmo_url_raw = get_settings().lbg_mmo_server_url.strip()
    mmo_state: str
    mmo_detail: str | None = None
    mmo_probe_url: str | None = None

    if not mmo_url_raw:
        mmo_state = "skipped"
        mmo_detail = "LBG_MMO_SERVER_URL non défini (pas de sync Lyra monde)"
    else:
        mmo_probe_url = mmo_url_raw.rstrip("/") + "/healthz"
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(mmo_probe_url)
            if r.status_code == 200:
                mmo_state = "ok"
            else:
                mmo_state = "error"
                mmo_detail = f"HTTP {r.status_code}"
        except Exception as e:
            mmo_state = "error"
            mmo_detail = str(e)

    res = {
        "backend": "ok",
        "orchestrator": orch_state,
        "orchestrator_url": orch_url,
        "orchestrator_detail": orch_detail,
        "agent_dialogue": dialogue_state,
        "agent_dialogue_url": dialogue_url_raw or None,
        "agent_dialogue_health_url": dialogue_probe_url,
        "agent_dialogue_detail": dialogue_detail,
        "agent_dialogue_info": dialogue_info,
        "agent_quests": quests_state,
        "agent_quests_url": quests_url_raw or None,
        "agent_quests_health_url": quests_probe_url,
        "agent_quests_detail": quests_detail,
        "agent_quests_info": quests_info,
        "agent_combat": combat_state,
        "agent_combat_url": combat_url_raw or None,
        "agent_combat_health_url": combat_probe_url,
        "agent_combat_detail": combat_detail,
        "agent_combat_info": combat_info,
        "agent_pm": pm_state,
        "agent_pm_url": pm_url_raw or None,
        "agent_pm_health_url": pm_probe_url,
        "agent_pm_detail": pm_detail,
        "agent_pm_info": pm_info,
        "agent_desktop": desktop_state,
        "agent_desktop_url": desktop_url_raw or None,
        "agent_desktop_health_url": desktop_probe_url,
        "agent_desktop_detail": desktop_detail,
        "agent_desktop_info": desktop_info,
        "mmo_server": mmo_state,
        "mmo_server_url": mmo_url_raw or None,
        "mmo_server_health_url": mmo_probe_url,
        "mmo_server_detail": mmo_detail,
    }

    # Sondes TCP rapides sur le LAN pour l'infra et le jeu (pastilles)
    def check_port(h: str, p: int) -> bool:
        try:
            with socket.create_connection((h, p), timeout=0.8):
                return True
        except Exception:
            return False

    precu_ip = get_settings().lbg_lan_host_precu.split(":")[0]
    prime_ip = get_settings().lbg_lan_host_mmo.split(":")[0]
    front_ip = get_settings().lbg_lan_host_front.split(":")[0]

    res["infra_status"] = {
        "vm140": "ok" if orch_state == "ok" else "error",
        "vm110": "ok" if check_port(front_ip, 11434) else "error",
        "vm245": "ok" if check_port(precu_ip, 3306) else "error",
        "vm246": "ok" if check_port(prime_ip, 8791) else "error",
    }
    res["game_status"] = {
        "precu_game": "ok" if check_port(precu_ip, 44453) else "offline",
        "prime_game": "ok" if check_port(prime_ip, 44553) else "offline",
    }
    # Joueurs IA via sidecar Prime (:8791) — pas LBG_MMO_SERVER_URL (souvent PreCU).
    player_ia = await _fetch_player_ia_runtime(timeout_s=1.8)
    res["player_ia_runtime"] = player_ia
    bots_status = player_ia.get("bots_status") if isinstance(player_ia.get("bots_status"), dict) else {}
    # Compat Accueil/Jobs (au minimum lia/nix/mira)
    res["bots_status"] = {
        "lia": str(bots_status.get("lia") or "offline"),
        "nix": str(bots_status.get("nix") or "offline"),
        "mira": str(bots_status.get("mira") or "offline"),
        "kael": str(bots_status.get("kael") or "offline"),
    }

    # Métriques d'économie et objectifs du Chroniqueur de monde (Option C)
    economy_metrics = {}
    chronicler_metrics = {}
    try:
        from lbg_agents.economy_director import run_economy_director_tick
        from lbg_agents.world_chronicler import run_chronicler_tick
        eco_tick = run_economy_director_tick(dry_run=True)
        chrono_tick = run_chronicler_tick(dry_run=True)
        economy_metrics = {
            "signal_count": eco_tick.get("signal_count", 0),
            "evaluation_count": eco_tick.get("evaluation_count", 0),
            "proposed_actions": eco_tick.get("proposed_actions", [])[:5],
        }
        chronicler_metrics = {
            "active_goal_count": chrono_tick.get("active_goal_count", 0),
            "active_goals": chrono_tick.get("active_goals", [])[:5],
            "roster_hints_count": len(chrono_tick.get("roster_hints", [])),
        }
    except Exception as e:
        economy_metrics = {"error": str(e)}
        chronicler_metrics = {"error": str(e)}

    res["economy_metrics"] = economy_metrics
    res["chronicler_metrics"] = chronicler_metrics

    return res


@router.get("/lbg-ia/status", tags=["pilot"], response_model=LbgIaStatusResponse)
async def pilot_lbg_ia_orchestrator_status() -> dict[str, object]:
    """
    Agrège `GET /metrics` + `GET /monitor/agents` du backend FastAPI **projet LBG_IA** (même réseau/VM).

    Définir `LBG_PILOT_LBGIA_BACKEND_URL` (ou `LBG_IA_BACKEND_URL`) sur ce backend ; le pilot web pilote alors
    le monitoring sans CORS depuis le navigateur.
    """
    base = lbg_ia_backend_base_url()
    if not base:
        return {
            "ok": False,
            "disabled": True,
            "detail": "LBG_PILOT_LBGIA_BACKEND_URL / LBG_IA_BACKEND_URL non défini.",
        }

    timeout = pilot_lbg_ia_http_timeout_s()
    metrics_error = ""
    agents_error = ""

    metrics_data: dict[str, object] | None = None
    agents_data: dict[str, object] | None = None
    metrics_status = 0
    agents_status = 0

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            m_resp, a_resp = await asyncio.gather(
                client.get(f"{base}/metrics"),
                client.get(f"{base}/monitor/agents"),
            )

        metrics_status = int(getattr(m_resp, "status_code", 0))
        agents_status = int(getattr(a_resp, "status_code", 0))

        if metrics_status != 200:
            metrics_error = (getattr(m_resp, "text", "") or "")[:500]

        try:
            if metrics_status == 200:
                raw_m = m_resp.json()
                metrics_data = raw_m if isinstance(raw_m, dict) else {"payload": raw_m}
        except Exception as e:
            metrics_error = str(e)

        if agents_status != 200:
            agents_error = (getattr(a_resp, "text", "") or "")[:500]

        try:
            if agents_status == 200:
                raw_a = a_resp.json()
                agents_data = raw_a if isinstance(raw_a, dict) else {"payload": raw_a}
        except Exception as e:
            agents_error = str(e)

    except Exception as e:
        LOG.warning("pilot.lbg_ia_orchestrator_status error base=%s err=%s", base, e)
        return {"ok": False, "upstream_base": base, "detail": str(e)}

    ok = metrics_status == 200 and agents_status == 200 and metrics_data is not None and agents_data is not None
    out: dict[str, object] = {
        "ok": ok,
        "upstream_base": base,
        "metrics": metrics_data,
        "agents_monitor": agents_data,
    }
    if not ok:
        out["upstream_errors"] = {
            "metrics_http": metrics_status,
            "metrics_detail": metrics_error or None,
            "agents_http": agents_status,
            "agents_detail": agents_error or None,
        }
    return out
