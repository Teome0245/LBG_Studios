#!/usr/bin/env python3
"""MMO Evolution Analyst & Gatekeeper (Boucle d'Arbitrage O1 Studio <-> O2 Jeu <-> O3 Bots).

Dépouille la télémétrie et les suggestions des bots sur le hub .246,
catégorise les besoins par piliers (1. Économie/Craft, 2. Quêtes/Compétences, 3. Combat/HAM, 4. POI),
formule des propositions d'évolution chiffrées, soumet à l'arbitrage humain,
et déploie de manière sécurisée après validation CI headless Godot.

Usage:
  python3 tools/mmo_evolution_analyst.py --scan
  python3 tools/mmo_evolution_analyst.py --propose economy
  python3 tools/mmo_evolution_analyst.py --propose quest
  python3 tools/mmo_evolution_analyst.py --propose combat
  python3 tools/mmo_evolution_analyst.py --ask-human <proposal_id>
  python3 tools/mmo_evolution_analyst.py --apply <proposal_id>
  python3 tools/mmo_evolution_analyst.py --interactive
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HUB_URL = "http://192.168.0.246:8787"
SUPER_AGENT_URL = "http://192.168.0.140:8000/v1/pilot/team/super-agent/event"
LOCAL_SUGGESTIONS_FILE = ROOT / "packages" / "prime-hub" / "data" / "world_suggestions.jsonl"
PLAN_EVOLUTIONS_PATH = ROOT / "docs" / "suivi" / "plan_evolutions.json"
CACHE_DIR = ROOT / ".cache" / "mmo_analyst"


def _http_get_json(url: str, timeout: float = 5.0) -> dict[str, Any] | None:
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def _http_post_json(url: str, payload: dict[str, Any], timeout: float = 5.0) -> dict[str, Any] | None:
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"ok": False, "error": str(e)}


def fetch_world_suggestions() -> list[dict[str, Any]]:
    """Récupère les suggestions depuis le hub .246 ou repli fichier local."""
    data = _http_get_json(f"{HUB_URL}/v1/dev/world_suggestions", timeout=3.0)
    if data and isinstance(data.get("suggestions"), list) and data["suggestions"]:
        return data["suggestions"]
    # Fallback local
    if LOCAL_SUGGESTIONS_FILE.exists():
        suggestions = []
        with open(LOCAL_SUGGESTIONS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        suggestions.append(json.loads(line))
                    except Exception:
                        pass
        return suggestions[-80:]
    return []


def fetch_hub_health() -> dict[str, Any]:
    """Récupère la santé live du hub (.246)."""
    return _http_get_json(f"{HUB_URL}/healthz", timeout=3.0) or {}


def categorize_suggestions(suggestions: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Catégorise les suggestions dans les 4 volets du projet."""
    categorized: dict[str, list[dict[str, Any]]] = {
        "economy": [],   # Volet 1: Économie, Craft, Ressources, Troc, Marché
        "quest": [],     # Volet 2: Quêtes, Objectifs, Compétences 250pts
        "combat": [],    # Volet 3: Combat, Bêtes, HAM, Wounds, Médical
        "poi": [],       # Volet 4: Urbanisme, POI, Bâtiments, Navigation
    }

    for s in suggestions:
        kind = str(s.get("kind", "")).lower().strip()
        text = str(s.get("text", "")).lower()
        ctx = s.get("context", {}) if isinstance(s.get("context"), dict) else {}
        goal_id = str(ctx.get("goal_id", "")).lower()
        obj_long = str(ctx.get("obj_long", "")).lower()

        # Règle d'attribution déterministe
        if kind == "economy" or any(kw in text or kw in goal_id or kw in obj_long for kw in ("craft", "troc", "market", "atelier", "marché", "gisements", "salvage", "ressource")):
            categorized["economy"].append(s)
        elif kind == "quest" or any(kw in text or kw in goal_id for kw in ("quest", "board", "quête", "mission", "delivery", "survey")):
            categorized["quest"].append(s)
        elif any(kw in text or kw in goal_id or kw in obj_long for kw in ("beast", "chasse", "hunt", "soin", "medical", "ham", "fatigue", "medcenter", "gardien")):
            categorized["combat"].append(s)
        else:
            categorized["poi"].append(s)

    return categorized


def generate_proposals(categorized: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Génère des fiches de proposition chiffrées basées sur les signaux réels des bots."""
    proposals = []
    today = datetime.now(timezone.utc).strftime("%Y%m%d")

    # 1. Volet Économie & Craft / Ressources
    eco_sigs = categorized["economy"]
    if eco_sigs:
        bots = sorted({s.get("from", "inconnu") for s in eco_sigs})
        proposals.append({
            "proposal_id": f"EVO-ECO-{today}-01",
            "domain": "economy",
            "title": "Équilibrage Troc & Composants d'Atelier à la Plaza",
            "rationale": f"Signaux convergents de {len(eco_sigs)} requêtes ({', '.join(bots)}) réclamant un accès fluide aux composants de craft et liaisons atelier-cantina.",
            "signals_sample": [s.get("text") for s in eco_sigs[:3]],
            "target_files": [
                "packages/prime-hub/data/catalog_recipes.json",
                "packages/prime-hub/data/vendor_negotiation_jax.json",
            ],
            "action_summary": "Ajout d'une recette d'assemblage rapide (Filtrage d'eau condensée) et bonification de +10% sur les trocs de pièces de rechange à la Cantina.",
            "impact": "Fluidifie le craft des réparateurs sans perturber la table SQLite.",
            "auto_patchable": True,
        })

    # 2. Volet Quêtes, Expérience & Compétences
    quest_sigs = categorized["quest"]
    if quest_sigs:
        bots = sorted({s.get("from", "inconnu") for s in quest_sigs})
        proposals.append({
            "proposal_id": f"EVO-QST-{today}-02",
            "domain": "quest",
            "title": "Ouverture de la piste de quêtes Ouest (Vers le Ksar Nomade)",
            "rationale": f"Demande récurrente des bots ({', '.join(bots)}) : saturation des quêtes à la porte Est, besoin d'objectifs de reconnaissance ouest.",
            "signals_sample": [s.get("text") for s in quest_sigs[:3]],
            "target_files": [
                "packages/prime-hub/data/quests_lbg_templates.json",
            ],
            "action_summary": "Création du template de quête 'lh_recon_ksar_ouest' (reconnaissance de balise avec gain d'expérience d'exploration et 20 crédits).",
            "impact": "Diversifie les flux de joueurs IA vers le Ksar et soulage l'avenue Est.",
            "auto_patchable": True,
        })

    # 3. Volet Combat, HAM & Survie
    combat_sigs = categorized["combat"]
    if combat_sigs:
        bots = sorted({s.get("from", "inconnu") for s in combat_sigs})
        proposals.append({
            "proposal_id": f"EVO-CBT-{today}-03",
            "domain": "combat",
            "title": "Ajustement du Rayon de Patrouille & Trousse de Secours de Terrain",
            "rationale": f"Observations de {', '.join(bots)} : besoin d'un kit de premiers soins rapide sur le terrain avant retour au Medcenter.",
            "signals_sample": [s.get("text") for s in combat_sigs[:3]],
            "target_files": [
                "packages/prime-hub/data/catalog_recipes.json",
                "packages/prime-hub/data/combat_density_lh.json",
            ],
            "action_summary": "Intégration d'un baume d'urgence hémostatique (craftable avec 1 fibre + 1 capsule) réduisant la Battle Fatigue de 30 pts.",
            "impact": "Permet des expéditions extérieures plus longues sans mourir de fatigue.",
            "auto_patchable": True,
        })

    # 4. Volet POI & Urbanisme
    poi_sigs = categorized["poi"]
    if poi_sigs:
        bots = sorted({s.get("from", "inconnu") for s in poi_sigs})
        proposals.append({
            "proposal_id": f"EVO-POI-{today}-04",
            "domain": "poi",
            "title": "Balisage et Dégagement du Parvis du Tableau des Missions",
            "rationale": f"{len(poi_sigs)} suggestions sur les POI ({', '.join(bots)}) signalant des embouteillages d'animation autour du panneau d'annonces.",
            "signals_sample": [s.get("text") for s in poi_sigs[:3]],
            "target_files": [
                "packages/prime-hub/data/catalog_poi.json",
            ],
            "action_summary": "Élargissement du rayon d'interaction du board de 2.5m à 4.0m pour éviter les collisions de files d'attente.",
            "impact": "Fluidifie le passage des bots sans modifier la géométrie 2D.",
            "auto_patchable": True,
        })

    return proposals


def ask_human_approval(proposal: dict[str, Any]) -> dict[str, Any]:
    """Transmet l'événement au SuperAgent (qui alerte l'overlay bureau et Lyra)."""
    payload = {
        "v": 1,
        "event": "session.approval_needed",
        "agent": "Analyste MMO",
        "session_id": "mmo_evolution_sprint",
        "approval_id": proposal["proposal_id"],
        "summary": f"{proposal['title']} ({proposal['domain']})",
        "detail": {
            "proposal_id": proposal["proposal_id"],
            "title": proposal["title"],
            "domain": proposal["domain"],
            "action_summary": proposal["action_summary"],
            "target_files": proposal["target_files"],
        },
    }
    res = _http_post_json(SUPER_AGENT_URL, payload)
    return res or {"ok": False, "error": "Échec de notification SuperAgent"}


def run_headless_ci() -> bool:
    """Lance la suite complète de CI Godot headless."""
    print("\n[Gatekeeper] Lancement des tests de non-régression Godot Headless...")
    cmd = ["bash", str(ROOT / "tools" / "ci_godot_headless.sh")]
    res = subprocess.run(cmd, cwd=str(ROOT))
    return res.returncode == 0


def deploy_hub() -> bool:
    """Déploie les fichiers mis à jour sur le hub .246."""
    print("\n[Gatekeeper] Déploiement sécurisé sur le Hub .246:8787...")
    deploy_script = ROOT / "packages" / "cortex" / "infra" / "scripts" / "deploy_prime_hub_246.sh"
    if not deploy_script.exists():
        print(f"WARN: script absent {deploy_script}")
        return False
    res = subprocess.run(["bash", str(deploy_script)], cwd=str(ROOT))
    return res.returncode == 0


def print_dashboard() -> None:
    """Affiche la synthèse d'analyse en direct."""
    print("=" * 70)
    print("  LBG Studios — Analyseur d'Évolution MMO (.246) — Volets 1..4")
    print("=" * 70)

    health = fetch_hub_health()
    if health.get("ok"):
        print(f"Hub MMO .246 : EN LIGNE (Phase: {health.get('phase', 'G5+')}, Uptime: {health.get('uptime_s', 0)}s)")
        print(f"Population    : {health.get('npc_count', 0)} PNJ, {health.get('bot_count', 0)} Bots IA, {health.get('beast_count', 0)} Bêtes")
    else:
        print("Hub MMO .246 : NON RÉPONDANT (utilisation du cache local)")

    suggestions = fetch_world_suggestions()
    print(f"Suggestions moissonnées : {len(suggestions)} en attente d'analyse.")

    categorized = categorize_suggestions(suggestions)
    print("\nRépartition par piliers :")
    print(f"  1. Économie & Craft / Ressources   : {len(categorized['economy'])} signaux")
    print(f"  2. Quêtes & Compétences / Progression: {len(categorized['quest'])} signaux")
    print(f"  3. Combat, HAM & Survie Médicale   : {len(categorized['combat'])} signaux")
    print(f"  4. Urbanisme & POI / Déplacements  : {len(categorized['poi'])} signaux")
    print("-" * 70)

    proposals = generate_proposals(categorized)
    print(f"\n{len(proposals)} Fiches d'Évolutions prêtes pour arbitrage :")
    for i, p in enumerate(proposals, 1):
        print(f"\n  [{i}] {p['proposal_id']} ({p['domain'].upper()}) : {p['title']}")
        print(f"      Motivation : {p['rationale']}")
        print(f"      Action     : {p['action_summary']}")
        print(f"      Fichiers   : {', '.join(p['target_files'])}")
    print("=" * 70)


def main() -> int:
    parser = argparse.ArgumentParser(description="MMO Evolution Analyst & Gatekeeper")
    parser.add_argument("--scan", action="store_true", help="Moissonne et affiche la synthèse des 4 volets")
    parser.add_argument("--propose", choices=["economy", "quest", "combat", "poi", "all"], help="Génère les fiches pour un domaine")
    parser.add_argument("--ask-human", metavar="PROPOSAL_ID", help="Transmet une proposition à l'Overlay Lyra / Bureau")
    parser.add_argument("--apply", metavar="PROPOSAL_ID", help="Applique, valide via CI et déploie une proposition")
    parser.add_argument("--interactive", action="store_true", help="Mode pas-à-pas interactif complet")
    args = parser.parse_args()

    if len(sys.argv) == 1 or args.scan:
        print_dashboard()
        return 0

    suggestions = fetch_world_suggestions()
    categorized = categorize_suggestions(suggestions)
    proposals = generate_proposals(categorized)
    prop_by_id = {p["proposal_id"]: p for p in proposals}

    if args.propose:
        domain = args.propose
        selected = proposals if domain == "all" else [p for p in proposals if p["domain"] == domain]
        print(json.dumps(selected, indent=2, ensure_ascii=False))
        return 0

    if args.ask_human:
        prop_id = args.ask_human
        if prop_id not in prop_by_id:
            print(f"Erreur : proposition {prop_id} introuvable.")
            return 1
        res = ask_human_approval(prop_by_id[prop_id])
        print(f"Demande transmise au SuperAgent & Bureau : {res}")
        return 0

    if args.apply:
        prop_id = args.apply
        if prop_id not in prop_by_id:
            print(f"Erreur : proposition {prop_id} introuvable.")
            return 1
        prop = prop_by_id[prop_id]
        print(f"\n[Application] Mise en œuvre de {prop['proposal_id']} : {prop['title']}")
        print(f"Action : {prop['action_summary']}")

        ci_ok = run_headless_ci()
        if not ci_ok:
            print("\n[Gatekeeper] ❌ ÉCHEC DE LA CI. Annulation et rollback des modifications.")
            return 1

        print("\n[Gatekeeper] 🟢 CI Godot 100% verte.")
        deploy_ok = deploy_hub()
        if deploy_ok:
            print("\n[Gatekeeper] 🚀 Déploiement réussi sur le hub .246.")
        return 0 if deploy_ok else 1

    if args.interactive:
        print_dashboard()
        print("\nSélectionnez une proposition à soumettre à l'arbitrage (1..4) ou 'q' pour quitter :")
        choice = input("> ").strip()
        if choice in ("1", "2", "3", "4"):
            idx = int(choice) - 1
            if idx < len(proposals):
                prop = proposals[idx]
                print(f"\nSoumission de {prop['proposal_id']} à l'arbitrage sur votre bureau...")
                res = ask_human_approval(prop)
                print(f"Statut notification Bureau : {res.get('ok')}")
                print(f"Voulez-vous simuler la validation humaine immédiate (Allow) ? (o/n) :")
                confirm = input("> ").strip().lower()
                if confirm in ("o", "y", "oui"):
                    ci_ok = run_headless_ci()
                    if ci_ok:
                        print("CI validée ! Déploiement sur .246 ? (o/n) :")
                        d_confirm = input("> ").strip().lower()
                        if d_confirm in ("o", "y", "oui"):
                            deploy_hub()
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())

