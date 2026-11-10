"""Endpoint FastAPI pour la topologie Second Brain et le graphe de connaissances en direct (LBG Studios).

Combine le graphe de lore statique (docs/lore/) et la flotte en direct des 10 Joueurs IA
connectés sur le serveur Godot Hub autoritaire (.246:8787).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
from fastapi import APIRouter

from config import get_settings

router = APIRouter(tags=["pilot-topology"])


@router.get("/topology")
async def get_pilot_topology():
    """Renvoie la topologie de graphe (nœuds et arêtes) issue du Second Brain docs/lore/

    enrichie en temps réel par les Joueurs IA actifs sur Godot Hub (:8787).
    """
    cortex_root = Path(__file__).resolve().parents[5]
    assets_json = cortex_root / "pilot_web" / "assets" / "topology_data.json"

    graph: dict[str, Any] = {
        "nodes": {},
        "edges": [],
        "broken_links": [],
        "live_bots_count": 0,
    }

    if assets_json.exists():
        try:
            with open(assets_json, encoding="utf-8") as f:
                graph = json.load(f)
        except Exception:
            pass

    nodes = graph.get("nodes", {})
    edges = graph.get("edges", [])

    # Interrogation temps réel du Hub Godot .246:8787
    settings = get_settings()
    hub_url = settings.prime_hub_base()
    live_bots_count = 0

    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
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
                    nodes[bot_id] = {
                        "id": bot_id,
                        "title": f"🤖 {name}",
                        "type": "bot",
                        "path": f"hub://246:8787/bots/{name}",
                        "play_mode": play_mode,
                        "goal": goal,
                        "quest_id": quest_id,
                        "pos": pos,
                        "linked_studio": linked_agent,
                        "is_live": True,
                        "links_to": ["scrapaltai"],
                    }

                    # Arête de présence sur Scrapaltai (Lost Heaven)
                    edges.append({
                        "source": bot_id,
                        "target": "scrapaltai",
                        "relation": "in_world",
                    })

                    # Arêtes dynamiques selon l'activité
                    if "survey" in quest_id or goal == "hunt" or "sample" in goal:
                        nodes[bot_id]["links_to"].append("bio_ingenierie")
                        edges.append({"source": bot_id, "target": "bio_ingenierie", "relation": "engaged_in"})
                    elif goal == "market" or "craft" in play_mode:
                        nodes[bot_id]["links_to"].append("craft_artisanat")
                        edges.append({"source": bot_id, "target": "craft_artisanat", "relation": "engaged_in"})
                    elif goal == "train" or goal == "quest_accept":
                        nodes[bot_id]["links_to"].append("villes_politique")
                        edges.append({"source": bot_id, "target": "villes_politique", "relation": "engaged_in"})
    except Exception:
        # Dégradation propre si le hub est temporairement inaccessible
        pass

    graph["nodes"] = nodes
    graph["edges"] = edges
    graph["live_bots_count"] = live_bots_count

    return graph
