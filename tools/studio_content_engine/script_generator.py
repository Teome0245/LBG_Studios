"""script_generator.py — Générateur de scripts viraux Tech / IA pour Shorts / TikTok / Reels.

Structure optimisée pour le format court (20 - 45 secondes) :
1. Hook (3s) : Accroche immédiate anti-scroll.
2. Problem (5-8s) : Douleur dev / coût cloud / complexité.
3. Solution (10-15s) : Architecture locale 0 €, outillage open-source.
4. Call to Action (3-5s) : Like, follow, repo LBG Studios.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)

OLLAMA_HOST_110 = os.environ.get("LBG_OLLAMA_110", "http://192.168.0.110:11434")
OLLAMA_HOST_111 = os.environ.get("LBG_OLLAMA_111", "http://192.168.0.111:11434")
DEFAULT_MODEL = os.environ.get("LBG_CONTENT_MODEL", "qwen2.5:3b")

SYSTEM_PROMPT = """Tu es Lia, créatrice de contenu tech et ingénieure IA chez La Boite à Geek (LBG Studios).
Ton objectif est de créer un script vidéo vertical (TikTok, YouTube Shorts, Reels) à la fois captivant, ultra concret et éducatif.
Durée cible : 45 à 55 secondes (environ 120 à 150 mots, répartis en 6 à 8 phrases fluides et percutantes).

Consignes de contenu :
1. Donne des INFORMATIONS RÉELLES et CONCRÈTES : cite des technologies précises (ex: Godot 4.6 headless, NavigationServer3D, SQLite en mode WAL, Piper TTS ONNX, Ollama local, WebSockets, Linux, FastAPI).
2. Donne des CHIFFRES et MÉTRIQUES mesurables (ex: 60 ticks/seconde, 1.2 Go de RAM, 45 ms de latence, 0€ de facture cloud).
3. Explique concrètement comment l'architecture fonctionne, sans rester dans des généralités marketing creuses.
4. RÈGLE ABSOLUE DE SÉCURITÉ : Ne jamais divulguer de secrets industriels, mots de passe, tokens, clés d'API ou adresses IP privées.

Structure en 6 à 8 phrases :
- Phrase 1 (Hook percutant) : Une question contre-intuitive ou un constat choc.
- Phrase 2 (Contexte & Cas d'usage) : Ce qu'on cherche à accomplir concrètement en production.
- Phrase 3 (Le problème classique) : Pourquoi les solutions cloud ou monolithiques échouent ou coûtent une fortune.
- Phrase 4 (L'architecture choisie) : Les composants open-source exacts déployés.
- Phrase 5 (Le mécanisme technique) : Comment les briques communiquent et s'articulent.
- Phrase 6 (Le résultat mesuré) : Métrique tangible de performance, fluidité ou consommation.
- Phrase 7 (Call to Action) : Invitation à poser ses questions et explorer nos repos GitHub open source.

Tu DOIS répondre UNIQUEMENT avec un objet JSON valide au format suivant (sans backticks markdown) :
{
  "title": "Titre court percutant",
  "category": "IA Locale / Godot / Architecture",
  "hook": "Phrase 1 d'accroche",
  "problem": "Explication du problème",
  "solution": "Explication technique détaillée de la solution",
  "metrics": "Les chiffres et résultats mesurés",
  "cta": "Appel à l'action",
  "sentences": [
    "Phrase 1 (Hook).",
    "Phrase 2 (Contexte).",
    "Phrase 3 (Problème classique).",
    "Phrase 4 (Stack open source).",
    "Phrase 5 (Mécanisme technique).",
    "Phrase 6 (Résultat mesuré).",
    "Phrase 7 (Call to action)."
  ]
}
"""

FALLBACK_SCRIPTS = [
    {
        "title": "Arrête de payer des API Cloud pour tes Agents IA",
        "category": "Architecture IA Locale",
        "hook": "Arrête immédiatement de dépenser des centaines d'euros chaque mois en tokens d'API pour faire tourner tes agents d'automatisation.",
        "problem": "Dès que tes agents analysent des données ou tournent en boucle, chaque requête Claude ou OpenAI grignote ta marge et crée un goulot d'étranglement réseau.",
        "solution": "Chez LBG Studios, nos agents tournent 100% en local grâce à Ollama sur cartes RTX grand public, couplés au moteur vocal Piper en ONNX.",
        "metrics": "Bilan : zéro latence externe, aucune dépendance cloud et une facture mensuelle strictement égale à zéro euro.",
        "cta": "Abonne-toi pour découvrir nos pipelines d'automatisation et retrouve tout le code source sur notre GitHub.",
        "sentences": [
            "Arrête immédiatement de dépenser des centaines d'euros chaque mois en tokens d'API pour faire tourner tes agents d'automatisation.",
            "En environnement de test ou de veille continue, faire des milliers d'appels LLM par jour devient rapidement un gouffre financier.",
            "Le piège classique, c'est de croire qu'un agent autonome a obligatoirement besoin d'un modèle cloud géant pour exécuter des scripts simples.",
            "Chez LBG Studios, nous combinons des petits modèles spécialisés 3 à 14 milliards de paramètres via Ollama et un synthétiseur Piper en temps réel.",
            "Les requêtes s'exécutent en moins de 200 millisecondes sur notre réseau local, avec une confidentialité absolue pour nos données.",
            "Résultat : nous générons des automatisations complètes 24 heures sur 24 pour un coût d'infrastructure de zéro euro.",
            "Abonne-toi pour découvrir nos benchmarks d'ingénierie et viens tester nos outils directement sur notre GitHub.",
        ],
    },
    {
        "title": "Comment faire tourner 10 Bots IA dans Godot 4 sans cluster",
        "category": "Godot 4 & Simulation",
        "hook": "Tu pensais que simuler des dizaines de joueurs IA dans un monde 3D dynamique demandait un serveur dédié surpuissant ?",
        "problem": "La majorité des architectures traditionnelles séparent le serveur logique du moteur de rendu, ce qui multiplie les allers-retours réseau et sature la mémoire.",
        "solution": "Grâce au mode headless natif de Godot 4.6 et à son NavigationServer 3D multithreadé, le calcul spatial se fait au plus près des données.",
        "metrics": "Nous faisons tourner 10 agents autonomes à 60 ticks par seconde avec moins de 1.5 Go de RAM consommée.",
        "cta": "Dis-moi en commentaire quel comportement de PNJ tu veux voir modélisé et retrouve nos scripts sur notre GitHub.",
        "sentences": [
            "Tu pensais que simuler des dizaines de joueurs IA dans un monde 3D dynamique demandait un serveur dédié surpuissant ?",
            "Dans notre projet MMO, nous devions animer des dizaines de créatures et de compagnons autonomes naviguant sur un terrain complexe.",
            "L'erreur courante est d'utiliser un backend Python ou Node.js qui recalcule laborieusement des coordonnées de maillage sans accélération matérielle.",
            "Chez LBG Studios, nous exploitons Godot 4.6 en mode headless directement sur un serveur Linux compact.",
            "Son NavigationServer 3D calcule les trajectoires d'évitement de foule en multithread natif pendant qu'un bus WebSocket diffuse l'état du monde.",
            "Nos benchmarks confirment une cadence stable de 60 ticks par seconde avec seulement 1,2 gigaoctet de mémoire vive mobilisée.",
            "Dis-moi en commentaire quel type d'intelligence artificielle tu souhaites intégrer dans tes jeux et rejoins notre communauté GitHub.",
        ],
    },
    {
        "title": "Pourquoi Godot 4 Headless bat les serveurs traditionnels",
        "category": "Architecture Serveur MMO",
        "hook": "Pourquoi de plus en plus de studios indépendants abandonnent les serveurs dédiés en C++ sur-mesure au profit de Godot headless ?",
        "problem": "Développer un serveur logique sans moteur physique oblige à recoder manuellement les collisions, la ligne de vue et les volumes spatiaux.",
        "solution": "En compilant Godot 4 avec l'option headless, on obtient un binaire ultra léger qui gère nativement la physique et les raycasts sans aucun affichage.",
        "metrics": "Zéro overhead GPU, démarrage instantané en 400 millisecondes et synchronisation parfaite avec le client de jeu.",
        "cta": "Abonne-toi pour voir notre stack temps réel en action et télécharge l'architecture complète sur notre GitHub.",
        "sentences": [
            "Pourquoi de plus en plus de studios indépendants abandonnent les serveurs dédiés en C++ sur-mesure au profit de Godot headless ?",
            "Quand on développe un jeu multijoueur spatial, la synchronisation des boîtes de collision entre le serveur et le client devient vite un cauchemar.",
            "Recoder un moteur de raycast et de physique dans un serveur web classique entraîne d'inévitables désynchronisations et une latence inutile.",
            "Avec Godot 4 en mode headless, le serveur partage exactement les mêmes scènes, maillages et nœuds physiques que les clients.",
            "Le moteur tourne sans interface graphique, traite la boucle de tick autoritaire et communique avec les joueurs via WebSockets ultra rapides.",
            "Bilan sur nos tests de charge : moins de 5 pourcent d'utilisation CPU par zone et une empreinte mémoire inférieure à 400 mégaoctets.",
            "Abonne-toi pour suivre nos tests d'infrastructure et retrouve tous nos patrons d'architecture sur notre GitHub.",
        ],
    },
]


def _match_fallback_script(topic: str | None) -> dict[str, Any]:
    """Sélectionne ou génère le script canonique le plus pertinent pour le sujet."""
    if not topic:
        return dict(FALLBACK_SCRIPTS[0])

    topic_lower = topic.lower()
    if any(k in topic_lower for k in ["godot", "headless", "serveur", "multijoueur", "mmo", "tick"]):
        return dict(FALLBACK_SCRIPTS[2])
    if any(k in topic_lower for k in ["bot", "pnj", "nav", "navigation", "simul"]):
        return dict(FALLBACK_SCRIPTS[1])

    # Générateur de secours dynamique structuré pour les sujets inédits
    clean_title = topic[:60].strip()
    return {
        "title": clean_title,
        "category": "Tech & Dev Local",
        "hook": f"Tu veux savoir comment maîtriser {clean_title} sans dépendre d'outils propriétaires fermés ?",
        "problem": "La plupart des solutions imposent des abonnements exorbitants, verrouillent totalement tes données et créent des latences inutiles.",
        "solution": f"En appliquant les méthodes d'ingénierie 100% locale de LBG Studios, nous construisons des architectures ouvertes, modulaires et sans frais récurrents.",
        "metrics": "Zéro euro de facture mensuelle et une maîtrise absolue de ton code et de tes données.",
        "cta": "Abonne-toi pour découvrir la suite et récupère l'ensemble de nos architectures open source.",
        "sentences": [
            f"Tu veux savoir comment maîtriser {clean_title} sans dépendre d'outils propriétaires fermés ?",
            "Dans beaucoup d'entreprises, la tentation est grande de brancher directement des API tierces sans mesurer l'impact sur les coûts à long terme.",
            "Très vite, la facture explose, les dépendances s'accumulent et la moindre panne de réseau paralyse toute la chaîne d'outils.",
            f"Chez LBG Studios, nous développons des architectures locales et robustes pour traiter {clean_title} de manière autonome.",
            "Nos briques logicielles s'exécutent sur notre propre matériel, garantissant une réactivité maximale et une sécurité totale.",
            "Résultat : nous obtenons des performances de pointe sans jamais dépendre du moindre abonnement cloud payant.",
            "Abonne-toi pour découvrir nos astuces d'ingénierie et rejoins notre communauté GitHub pour tester nos projets.",
        ],
    }


def inject_signature_intro(data: dict[str, Any]) -> dict[str, Any]:
    """Injecte l'intro signature canonique au début de chaque script."""
    title = data.get("title", "le sujet du jour")
    signature = f"Bonjour, je suis Lia, l'IA de La Boite à Geek ! Aujourd'hui je vous présente : {title}."

    sentences = list(data.get("sentences", []))
    # Ne pas doubler si l'intro est déjà présente
    if not any("je suis lia" in s.lower() for s in sentences):
        sentences.insert(0, signature)
        data["sentences"] = sentences
        data["signature_intro"] = signature
    return data


def generate_tech_script(topic: str | None = None, model: str = DEFAULT_MODEL) -> dict[str, Any]:
    """Génère un script structuré via Ollama local ou utilise le fallback canonique."""
    if not topic:
        return inject_signature_intro(dict(FALLBACK_SCRIPTS[0]))

    prompt = f"Génère un script vidéo court TikTok/Shorts de 45 à 55 secondes (6 à 8 phrases concrètes et chiffrées) en français sur le sujet : '{topic}'."

    hosts_and_models = [
        (OLLAMA_HOST_111, "qwen2.5:3b"),
        (OLLAMA_HOST_111, "lbg-compagnon-e4b-v1:latest"),
        (OLLAMA_HOST_110, "huihui_ai/gemma-4-abliterated:12b"),
    ]
    for host, mod in hosts_and_models:
        try:
            logger.info("Tentative de génération script sur %s avec %s (délai: 12s)...", host, mod)
            with httpx.Client(timeout=12.0) as client:
                res = client.post(
                    f"{host}/api/generate",
                    json={
                        "model": mod,
                        "system": SYSTEM_PROMPT,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.7, "num_ctx": 2048},
                    },
                )
                if res.status_code == 200:
                    raw_text = res.json().get("response", "").strip()
                    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
                    if match:
                        data = json.loads(match.group(0))
                        if "sentences" in data and len(data["sentences"]) >= 5:
                            logger.info("Script enrichi généré avec succès par %s (%s) (%d phrases) !", host, mod, len(data["sentences"]))
                            return inject_signature_intro(data)
        except Exception as e:
            logger.warning("Échec génération sur %s (%s) : %s", host, mod, e)

    logger.info("Sélection du script canonique adapté au sujet : '%s'...", topic)
    return inject_signature_intro(_match_fallback_script(topic))


if __name__ == "__main__":
    script = generate_tech_script("Comment créer son propre Second Brain avec Obsidian et RAG")
    print(json.dumps(script, indent=2, ensure_ascii=False))
