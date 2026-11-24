"""Endpoint FastAPI pour la topologie Second Brain et le graphe de connaissances en direct (LBG Studios).

Combine :
1. Le graphe de l'Organisme Gladys (Infra, Machines .10/.143/.140/.110/.111/.246/.54, Services, Agents & Connaissances)
2. Le graphe de lore MMO (docs/lore/, Planètes, Villes, PNJ, Factions, Mécaniques)
3. La flotte en direct des Joueurs IA connectés sur Godot Hub (.246:8787)
4. Les sondes de disponibilité live des machines et services Gladys.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import httpx
from fastapi import APIRouter, Query

from config import get_settings

router = APIRouter(tags=["pilot-topology"])


async def _probe_tcp_port(host: str, port: int, timeout: float = 0.25) -> bool:
    """Sonde rapide non-bloquante pour vérifier si un port TCP est ouvert."""
    try:
        _, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)
        writer.close()
        await writer.wait_closed()
        return True
    except Exception:
        return False


@router.get("/topology")
async def get_pilot_topology(domain: str | None = Query(None, description="Filtre de domaine : 'all', 'gladys' ou 'mmo'")):
    """Renvoie la topologie de graphe (nœuds et arêtes) complète ou filtrée par domaine,

    enrichie en temps réel par les Joueurs IA actifs (:8787) et le statut des organes Gladys.
    """
    cortex_root = Path(__file__).resolve().parents[5]
    assets_mmo = cortex_root / "pilot_web" / "assets" / "topology_data.json"
    assets_gladys = cortex_root / "pilot_web" / "assets" / "gladys_topology_data.json"

    all_nodes: dict[str, Any] = {}
    all_edges: list[dict[str, Any]] = []

    # 1. Chargement des données statiques MMO
    if assets_mmo.exists():
        try:
            with open(assets_mmo, encoding="utf-8") as f:
                data_mmo = json.load(f)
                for nid, n in data_mmo.get("nodes", {}).items():
                    n_copy = dict(n)
                    n_copy.setdefault("domain", "mmo")
                    all_nodes[nid] = n_copy
                for e in data_mmo.get("edges", []):
                    all_edges.append(dict(e))
        except Exception:
            pass

    # 2. Chargement des données statiques Organisme Gladys
    if assets_gladys.exists():
        try:
            with open(assets_gladys, encoding="utf-8") as f:
                data_gladys = json.load(f)
                for nid, n in data_gladys.get("nodes", {}).items():
                    n_copy = dict(n)
                    n_copy.setdefault("domain", "gladys")
                    all_nodes[nid] = n_copy
                for e in data_gladys.get("edges", []):
                    all_edges.append(dict(e))
        except Exception:
            pass

    # 3. Sondes temps réel des organes & machines Gladys
    probe_targets: list[tuple[str, str, int]] = []
    for nid, node in all_nodes.items():
        if node.get("domain") == "gladys" and "probe_port" in node:
            host = node.get("host") or "127.0.0.1"
            # Si le host est local et qu'on est sur la machine .140
            if host in ("127.0.0.1", "localhost") and node.get("id") == "cortex_140":
                host = "127.0.0.1"
            probe_targets.append((nid, host, int(node["probe_port"])))

    live_gladys_count = 0
    if probe_targets:
        probe_coros = [_probe_tcp_port(host, port) for _, host, port in probe_targets]
        results = await asyncio.gather(*probe_coros, return_exceptions=True)
        for (nid, _, _), res in zip(probe_targets, results, strict=False):
            is_up = bool(res is True)
            if is_up:
                live_gladys_count += 1
            all_nodes[nid]["is_live"] = is_up
            all_nodes[nid]["status"] = "online" if is_up else "offline"

    # Marquer les connaissances, l'organisme, les domaines et les skills comme statut nominal
    for nid, node in all_nodes.items():
        if node.get("domain") == "gladys":
            if node.get("type") in ("organism", "knowledge", "incarnation", "skill", "domain"):
                node["is_live"] = True
                node["status"] = "online"
            elif "is_live" not in node:
                node["is_live"] = False
                node["status"] = "standby"

    # 4. Interrogation temps réel du Hub Godot .246:8787 (MMO Bots)
    settings = get_settings()
    hub_url = settings.prime_hub_base()
    live_bots_count = 0

    try:
        async with httpx.AsyncClient(timeout=1.2) as client:
            resp = await client.get(f"{hub_url}/v1/bots")
            if resp.status_code == 200:
                payload = resp.json()
                bots = payload.get("bots", [])
                for b in bots:
                    name = str(b.get("name") or b.get("entity_key") or "?").strip()
                    if not name:
                        continue
                    live_bots_count += 1
                    bot_id = f"bot_{name.lower()}"
                    play_mode = str(b.get("play_mode") or "hub")
                    goal = str(b.get("goal") or "")
                    quest_id = str(b.get("quest_id") or "")
                    pos = b.get("pos") or []
                    linked_agent = str(b.get("linked_studio_display") or "")

                    # Nœud dynamique pour le joueur IA
                    all_nodes[bot_id] = {
                        "id": bot_id,
                        "title": f"🤖 {name}",
                        "type": "bot",
                        "domain": "mmo",
                        "path": f"hub://246:8787/bots/{name}",
                        "play_mode": play_mode,
                        "goal": goal,
                        "quest_id": quest_id,
                        "pos": pos,
                        "linked_studio": linked_agent,
                        "is_live": True,
                        "status": "online",
                        "links_to": ["scrapaltai"],
                    }

                    # Arête de présence sur Scrapaltai (Lost Heaven)
                    all_edges.append({
                        "source": bot_id,
                        "target": "scrapaltai",
                        "relation": "in_world",
                    })

                    # Arêtes dynamiques selon l'activité
                    if "survey" in quest_id or goal == "hunt" or "sample" in goal:
                        all_nodes[bot_id]["links_to"].append("bio_ingenierie")
                        all_edges.append({"source": bot_id, "target": "bio_ingenierie", "relation": "engaged_in"})
                    elif goal == "market" or "craft" in play_mode:
                        all_nodes[bot_id]["links_to"].append("craft_artisanat")
                        all_edges.append({"source": bot_id, "target": "craft_artisanat", "relation": "engaged_in"})
                    elif goal == "train" or goal == "quest_accept":
                        all_nodes[bot_id]["links_to"].append("villes_politique")
                        all_edges.append({"source": bot_id, "target": "villes_politique", "relation": "engaged_in"})
    except Exception:
        # Dégradation propre si le hub est temporairement inaccessible
        pass

    # 5. Filtrage selon le domaine demandé
    requested_domain = (domain or "all").lower().strip()
    if requested_domain in ("gladys", "mmo"):
        filtered_nodes = {nid: n for nid, n in all_nodes.items() if n.get("domain") == requested_domain}
        filtered_edges = [
            e for e in all_edges
            if e.get("source") in filtered_nodes and e.get("target") in filtered_nodes
        ]
        out_nodes = filtered_nodes
        out_edges = filtered_edges
    else:
        out_nodes = all_nodes
        out_edges = all_edges

    return {
        "nodes": out_nodes,
        "edges": out_edges,
        "broken_links": [],
        "domain": requested_domain,
        "live_bots_count": live_bots_count,
        "live_gladys_count": live_gladys_count,
        "total_gladys_services": len(probe_targets),
    }
