"""script_generator.py — Générateur de scripts viraux Tech / IA pour Shorts / TikTok / Reels.

Structure optimisée pour le format court (25 - 40 secondes) :
1. Hook percutant (0-2s) : Phrase choc anti-scroll, problème concret ou chiffre marquant.
2. Problème d'ingénierie (5-8s) : Douleur dev, coût cloud, latence, complexité cachée.
3. Solution & Architecture (12-18s) : Stack locale concrète, composants exacts, mécanisme de fonctionnement.
4. Preuve par les métriques (5-8s) : Chiffres mesurés (RAM, ticks/s, ms de latence, 0€ de facture).
5. Call to Action engageant (3-5s) : Question ouverte pour déclencher les commentaires + GitHub LBG Studios.
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

SYSTEM_PROMPT = """Tu es Lia, l'avatar virtuel, créatrice de contenu tech et ingénieure IA de La Boite à Geek (LBG Studios).
Ton objectif est de générer un script vidéo court pour YouTube Shorts et TikTok, ultra concret, complet et captivant.
Durée cible : 30 à 45 secondes (environ 80 à 110 mots, découpés en 5 à 6 phrases percutantes).

Règles fondamentales de rédaction :
1. HOOK IMMÉDIAT (Phrase 1) : Démarre DIRECTEMENT sur le problème ou une affirmation choc. INTERDICTION formelle de commencer par des salutations ("Bonjour", "Salut", "Aujourd'hui je vous présente", "Bienvenue"). La vidéo doit accrocher dans les 2 premières secondes.
2. ULTRA CONCRET & TECHNIQUE : Parle comme un véritable ingénieur en production. Donne des noms de technologies réelles (ex: Godot 4.6 headless, NavigationServer3D, SQLite WAL, Piper TTS ONNX, FastAPI, Ollama local, WebSockets, Linux) et des chiffres mesurables (ex: 60 ticks/seconde, 1.2 Go de RAM, 35 ms de latence, 0€ de facture cloud). Bannis les phrases vagues de consultant.
3. CONCIS MAIS COMPLET : Explique le « Pourquoi » et le « Comment » en restant direct. Chaque phrase apporte une information technique dense sans remplissage.
4. SIGNATURE & CTA ENGAGEANT (Dernière phrase) : Termine par une phrase fluide intégrant ton prénom Lia, une question ouverte clivante pour forcer les commentaires, et le repo GitHub. (Exemple : "Moi c'est Lia de La Boîte à Geek : toi tu tournes sur quoi ? Dis-le moi en commentaire et retrouve nos sources sur GitHub !").
5. RÈGLE ABSOLUE DE SÉCURITÉ : Ne jamais divulguer de tokens, mots de passe, secrets ou adresses IP internes.
6. LANGUE : Français impeccable, naturel à l'oral.

Tu DOIS répondre UNIQUEMENT avec un objet JSON valide au format suivant (sans backticks markdown) :
{
  "title": "Titre percutant de moins de 65 caractères",
  "category": "Architecture / IA Locale / Godot 4",
  "hook": "Phrase 1 choc sans salutation",
  "problem": "Explication concrète du problème ou coût",
  "solution": "Explication précise des composants open source utilisés",
  "metrics": "Les chiffres et résultats mesurés",
  "cta": "Question pour déclencher des commentaires + signature Lia",
  "sentences": [
    "Phrase 1 (Hook immédiat, accroche choc sans bonjour).",
    "Phrase 2 (Le problème concret : coût, goulot d'étranglement ou complexité).",
    "Phrase 3 (L'architecture précise : stack déployée et mécanisme).",
    "Phrase 4 (Comment ça tourne techniquement sous le capot).",
    "Phrase 5 (Les métriques mesurées : RAM, FPS, latence, 0€).",
    "Phrase 6 (Call to action : question ouverte pour les commentaires + signature Lia + GitHub)."
  ]
}
"""

FALLBACK_SCRIPTS = [
    {
        "title": "Arrête de payer des API Cloud pour tes Agents IA",
        "category": "Architecture IA Locale",
        "hook": "Dépenser 200 euros par mois en tokens d'API pour faire tourner des agents d'automatisation, c'est une aberration technique.",
        "problem": "Dès qu'un agent boucle sur une tâche d'analyse ou de veille, chaque requête vers un modèle cloud payant explose ta facture et crée une latence externe inutile.",
        "solution": "Chez LBG Studios, nos agents tournent à 100% en local grâce à Ollama sur du matériel grand public, couplés au moteur vocal Piper en ONNX.",
        "metrics": "Les requêtes s'exécutent en moins de 150 millisecondes sur notre réseau local, pour une consommation de 1,2 gigaoctet de RAM et une facture de zéro euro.",
        "cta": "Moi c'est Lia : tu payes combien d'API cloud chaque mois ? Dis-le moi en commentaire et retrouve tous nos scripts sur le GitHub de LBG Studios.",
        "sentences": [
            "Dépenser 200 euros par mois en tokens d'API pour faire tourner des agents d'automatisation, c'est une aberration technique.",
            "Dès qu'un agent boucle sur une tâche d'analyse ou de veille, chaque requête vers un modèle cloud payant explose ta facture et crée une latence externe inutile.",
            "Chez LBG Studios, nos agents tournent à 100% en local grâce à Ollama sur du matériel grand public, couplés au moteur vocal Piper en ONNX.",
            "Le routage intelligent envoie les tâches légères sur des modèles 3 milliards et les décisions complexes sur un 14 milliards local.",
            "Les requêtes s'exécutent en moins de 150 millisecondes sur notre réseau local, pour une facture d'infrastructure strictement égale à zéro euro.",
            "Moi c'est Lia : tu payes combien d'API cloud chaque mois ? Dis-le moi en commentaire et retrouve tous nos scripts sur le GitHub de LBG Studios.",
        ],
    },
    {
        "title": "Faire tourner 10 Bots IA dans Godot 4 sans cluster",
        "category": "Godot 4 & Simulation",
        "hook": "Simuler dix joueurs IA dans un monde 3D dynamique sans aucun serveur cloud dédié, c'est totalement possible.",
        "problem": "La majorité des développeurs séparent inutilement le serveur logique du moteur de rendu, ce qui multiplie les allers-retours réseau et consomme des ressources colossales.",
        "solution": "Grâce au mode headless de Godot 4.6 et à son NavigationServer 3D multithreadé, toute la logique spatiale tourne directement sur la machine hôte.",
        "metrics": "Nos dix agents naviguent en temps réel à 60 ticks par seconde avec moins de 800 mégaoctets de mémoire vive mobilisée.",
        "cta": "Moi c'est Lia de La Boîte à Geek : quel comportement de PNJ tu veux voir modélisé ? Réponds en commentaire et teste le code sur notre GitHub !",
        "sentences": [
            "Simuler dix joueurs IA dans un monde 3D dynamique sans aucun serveur cloud dédié, c'est totalement possible.",
            "La majorité des développeurs séparent inutilement le serveur logique du moteur de rendu, ce qui multiplie les allers-retours réseau et consomme des ressources colossales.",
            "Chez LBG Studios, nous compilons Godot 4.6 en mode headless sur un serveur Linux compact pour gérer directement les collisions et la physique.",
            "Son NavigationServer 3D calcule les évitements d'obstacles en multithread natif pendant qu'un bus WebSocket diffuse l'état du monde aux clients.",
            "Nos tests de charge maintiennent une cadence stable de 60 ticks par seconde avec seulement 800 mégaoctets de mémoire vive mobilisée.",
            "Moi c'est Lia de La Boîte à Geek : quel comportement de PNJ tu veux voir modélisé ? Réponds en commentaire et teste le code sur notre GitHub !",
        ],
    },
    {
        "title": "Pourquoi Godot Headless bat les serveurs C++",
        "category": "Architecture Serveur MMO",
        "hook": "Pourquoi réécrire un serveur de jeu multijoueur sur-mesure en C++ quand le mode headless de Godot fait déjà tout le travail ?",
        "problem": "Développer un serveur logique sans moteur physique oblige à recoder manuellement les collisions, les raycasts et les volumes de visibilité.",
        "solution": "Avec Godot 4 en mode headless, le serveur partage exactement le même arbre de scènes et les mêmes maillages 3D que le client joueur.",
        "metrics": "Démarrage en 350 millisecondes, zéro GPU mobilisé et moins de 5 pourcent d'utilisation CPU par zone de jeu.",
        "cta": "Moi c'est Lia : tu préfères un serveur dédié sur-mesure ou un moteur headless ? Donne ton avis en commentaire et viens voir nos sources sur GitHub.",
        "sentences": [
            "Pourquoi réécrire un serveur de jeu multijoueur sur-mesure en C++ quand le mode headless de Godot fait déjà tout le travail ?",
            "Développer un serveur logique sans moteur physique oblige à recoder manuellement les collisions, les raycasts et les volumes de visibilité.",
            "Avec Godot 4 en mode headless, le serveur partage exactement le même arbre de scènes et les mêmes maillages 3D que le client joueur.",
            "Le moteur s'exécute sans interface graphique, arbitre la boucle logique à haute cadence et communique avec les joueurs via WebSockets ultra légers.",
            "Bilan sur nos benchmarks : démarrage en 350 millisecondes, zéro GPU mobilisé et moins de 5 pourcent de processeur par zone.",
            "Moi c'est Lia : tu préfères un serveur dédié sur-mesure ou un moteur headless ? Donne ton avis en commentaire et viens voir nos sources sur GitHub.",
        ],
    },
    {
        "title": "La mort des NPC passifs : des PNJ conscients",
        "category": "Game Design & IA Locale",
        "hook": "Les arbres de dialogue rigides et prévisibles dans les jeux vidéo, c'est officiellement terminé.",
        "problem": "Faire répéter trois répliques statiques en boucle à un PNJ casse totalement l'immersion, alors que brancher une API cloud coûte une fortune et ajoute deux secondes de latence.",
        "solution": "Chez LBG Studios, nous connectons nos PNJ à des micro-LLM locaux quantifiés en 4 bits, interfacés directement avec la boucle logique de Godot 4.",
        "metrics": "Réponse en moins de 120 millisecondes sur notre bus WebSocket local, avec mémoire contextuelle persistante sans dépendre d'internet.",
        "cta": "Moi c'est Lia de La Boîte à Geek : quel genre d'interaction PNJ tu rêves de voir ? Dis-le moi en commentaire et viens tester le projet sur GitHub !",
        "sentences": [
            "Les arbres de dialogue rigides et prévisibles dans les jeux vidéo, c'est officiellement terminé.",
            "Faire répéter trois répliques statiques en boucle à un PNJ casse totalement l'immersion, alors que brancher une API cloud coûte une fortune et ajoute deux secondes de latence.",
            "Chez LBG Studios, nous connectons nos PNJ à des micro-LLM locaux quantifiés en 4 bits, interfacés directement avec la boucle logique de Godot 4.",
            "Chaque personnage possède sa propre mémoire épisodique, ses objectifs dynamiques et perçoit l'environnement 3D en temps réel.",
            "Bilan : des répliques générées en 120 millisecondes sur notre réseau local, pour zéro euro d'abonnement externe.",
            "Moi c'est Lia de La Boîte à Geek : quel genre d'interaction PNJ tu rêves de voir ? Dis-le moi en commentaire et viens tester le projet sur GitHub !",
        ],
    },
    {
        "title": "Génération procédurale de terrain sur Godot 4.6",
        "category": "World Building Procédural",
        "hook": "Construire un monde ouvert infini sans saturer la mémoire vive de ton PC : voici notre recette.",
        "problem": "Placer des millions d'arbres et de rochers manuellement est impossible, et charger tout le maillage d'un coup fait chuter les FPS à zéro.",
        "solution": "En combinant FastNoiseLite multithreadé et le MultiMeshInstance3D de Godot 4.6, les objets sont instanciés sur le GPU en un seul draw call.",
        "metrics": "Plus de 50 000 éléments de décor affichés à 60 images par seconde stables avec moins de 600 mégaoctets de RAM.",
        "cta": "Moi c'est Lia : tu préfères le level design manuel ou la génération procédurale ? Donne ton avis en commentaire et explore nos scripts sur GitHub !",
        "sentences": [
            "Construire un monde ouvert infini sans saturer la mémoire vive de ton PC : voici notre recette.",
            "Placer des millions d'arbres et de rochers manuellement est impossible, et charger tout le maillage d'un coup fait chuter les FPS à zéro.",
            "Chez LBG Studios, nous couplons des générateurs FastNoiseLite en multithread natif aux MultiMeshInstance3D de Godot 4.6.",
            "Le terrain se partitionne en chunks dynamiques et les feuillages sont dessinés par le GPU en une seule passe de rendu.",
            "Résultat : plus de 50 000 éléments affichés à 60 FPS constants pour une empreinte mémoire inférieure à 600 mégaoctets.",
            "Moi c'est Lia : tu préfères le level design manuel ou la génération procédurale ? Donne ton avis en commentaire et explore nos scripts sur GitHub !",
        ],
    },
    {
        "title": "WebSockets vs WebTransport pour un MMO en 2026",
        "category": "Réseau Temps Réel",
        "hook": "Est-ce qu'il faut vraiment abandonner les WebSockets traditionnels pour du WebTransport sur un jeu multijoueur ?",
        "problem": "Le blocage en tête de ligne de TCP sur les WebSockets peut introduire des pics de lag dès qu'un paquet est perdu sur une connexion instable.",
        "solution": "Chez LBG Studios, nous exploitons des flux WebSockets optimisés avec compression binaire MessagePack, tout en préparant le switch vers les canaux non-ordonnés UDP de WebTransport.",
        "metrics": "Paquets compressés à moins de 45 octets par tick de synchronisation avec un ping inférieur à 15 millisecondes.",
        "cta": "Moi c'est Lia : tu es plutôt team WebSocket simple ou WebTransport moderne ? Dis-le moi en commentaire et regarde notre implémentation sur GitHub !",
        "sentences": [
            "Est-ce qu'il faut vraiment abandonner les WebSockets traditionnels pour du WebTransport sur un jeu multijoueur ?",
            "Le blocage en tête de ligne de TCP sur les WebSockets peut introduire des pics de lag dès qu'un paquet est perdu sur une connexion instable.",
            "Chez LBG Studios, nous combinons des WebSockets ultra légers avec une sérialisation binaire MessagePack pour synchroniser nos entités.",
            "Cette couche logicielle permet d'embarquer les états du monde sans surcoût réseau tout en garantissant une compatibilité navigateur totale.",
            "Nos benchmarks relèvent des paquets de moins de 45 octets par tick joueur et une latence réseau inférieure à 15 millisecondes.",
            "Moi c'est Lia : tu es plutôt team WebSocket simple ou WebTransport moderne ? Dis-le moi en commentaire et regarde notre implémentation sur GitHub !",
        ],
    },
]


def clean_title_smart(title: str, max_len: int = 65) -> str:
    """Tronque proprement un titre sans jamais couper au milieu d'un mot."""
    clean = title.strip()
    if len(clean) <= max_len:
        return clean
    truncated = clean[:max_len]
    last_space = truncated.rfind(" ")
    if last_space > 30:
        truncated = truncated[:last_space]
    return truncated.strip()


def _match_fallback_script(topic: str | None) -> dict[str, Any]:
    """Sélectionne ou génère le script canonique le plus pertinent pour le sujet."""
    if not topic:
        return dict(FALLBACK_SCRIPTS[0])

    topic_lower = topic.lower()
    if any(k in topic_lower for k in ["npc", "pnj", "conscient", "dialogue", "mort des"]):
        return dict(FALLBACK_SCRIPTS[3])
    if any(k in topic_lower for k in ["procédural", "terrain", "scatter", "world"]):
        return dict(FALLBACK_SCRIPTS[4])
    if any(k in topic_lower for k in ["websocket", "webtransport", "réseau", "protocole"]):
        return dict(FALLBACK_SCRIPTS[5])
    if any(k in topic_lower for k in ["godot", "headless", "serveur", "multijoueur", "mmo", "tick"]):
        return dict(FALLBACK_SCRIPTS[2])
    if any(k in topic_lower for k in ["bot", "nav", "navigation", "simul"]):
        return dict(FALLBACK_SCRIPTS[1])

    clean_topic = topic.strip()
    if clean_topic.lower().startswith("comment "):
        core_topic = clean_topic[8:].strip()
    elif clean_topic.lower().startswith("pourquoi "):
        core_topic = clean_topic[9:].strip()
    else:
        core_topic = clean_topic

    clean_title = clean_title_smart(clean_topic, max_len=60)
    return {
        "title": clean_title,
        "category": "Tech & Architecture Locale",
        "hook": f"Tu veux exploiter {core_topic} sans dépendre du moindre abonnement cloud payant ?",
        "problem": "La majorité des architectures actuelles imposent des API fermées, des coûts récurrents imprévisibles et une dépendance totale au réseau extérieur.",
        "solution": f"Chez LBG Studios, nous avons développé une approche 100% locale pour maîtriser {core_topic} directement sur notre matériel.",
        "metrics": "Zéro euro de frais cloud par mois, une réactivité immédiate et une confidentialité absolue de tes données de production.",
        "cta": "Moi c'est Lia de La Boîte à Geek : que penses-tu de cette approche 0€ cloud ? Dis-le moi en commentaire et retrouve nos sources sur GitHub !",
        "sentences": [
            f"Tu veux exploiter {core_topic} sans dépendre du moindre abonnement cloud payant ?",
            "La majorité des architectures actuelles imposent des API fermées, des coûts récurrents imprévisibles et une dépendance totale au réseau extérieur.",
            f"Chez LBG Studios, nous avons développé une approche 100% locale pour maîtriser {core_topic} directement sur notre matériel.",
            "En associant des briques open source optimisées et des modèles spécialisés sur machine dédiée, le système tourne sans dépendre d'internet.",
            "Bilan : zéro euro de frais cloud par mois, une réactivité immédiate et une confidentialité absolue de nos données de production.",
            "Moi c'est Lia de La Boîte à Geek : que penses-tu de cette approche 0€ cloud ? Dis-le moi en commentaire et retrouve nos sources sur GitHub !",
        ],
    }


def ensure_lia_signature(data: dict[str, Any]) -> dict[str, Any]:
    """S'assure que Lia est bien identifiée et que le CTA engage la communauté sans bloquer le Hook."""
    sentences = list(data.get("sentences", []))
    if not sentences:
        return data

    # Vérification : si une intro mollassonne est présente en phrase 1, on la purge
    if any(greet in sentences[0].lower() for greet in ["bonjour", "salut", "bienvenue", "aujourd'hui je vous"]):
        # Si la phrase 1 est juste une salutation, la remplacer par le hook
        hook = data.get("hook")
        if hook and hook != sentences[0]:
            sentences[0] = hook

    # S'assurer que le CTA final contient la signature Lia et une incitation au commentaire
    last_idx = len(sentences) - 1
    if not any("lia" in s.lower() for s in sentences):
        sentences[last_idx] = f"Moi c'est Lia de La Boîte à Geek : qu'est-ce que tu en penses ? Dis-le moi en commentaire et retrouve nos sources sur GitHub !"

    data["sentences"] = sentences
    return data


def generate_tech_script(topic: str | None = None, model: str = DEFAULT_MODEL) -> dict[str, Any]:
    """Génère un script structuré via Ollama local ou utilise le fallback canonique."""
    if not topic:
        return ensure_lia_signature(dict(FALLBACK_SCRIPTS[0]))

    prompt = (
        f"Génère un script vidéo court pour YouTube Shorts / TikTok de 30 à 40 secondes "
        f"(5 à 6 phrases percutantes, ultra concrètes et chiffrées sans salutation) en français sur le sujet : '{topic}'."
    )

    hosts_and_models = [
        (OLLAMA_HOST_110, "huihui_ai/qwen3.5-abliterated:9b"),
        (OLLAMA_HOST_110, "huihui_ai/gemma-4-abliterated:12b"),
        (OLLAMA_HOST_111, "lbg-compagnon-e4b-v1:latest"),
        (OLLAMA_HOST_111, "qwen2.5:3b"),
    ]
    for host, mod in hosts_and_models:
        try:
            logger.info("Tentative de génération script sur %s avec %s (délai: 8s)...", host, mod)
            with httpx.Client(timeout=8.0) as client:
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
                        if "sentences" in data and len(data["sentences"]) >= 4:
                            # Titre propre sans troncature brutale
                            if "title" in data:
                                data["title"] = clean_title_smart(data["title"], max_len=65)
                            logger.info("Script enrichi généré avec succès par %s (%s) (%d phrases) !", host, mod, len(data["sentences"]))
                            return ensure_lia_signature(data)
        except Exception as e:
            logger.warning("Échec génération sur %s (%s) : %s", host, mod, e)

    logger.info("Sélection du script canonique adapté au sujet : '%s'...", topic)
    return ensure_lia_signature(_match_fallback_script(topic))


if __name__ == "__main__":
    script = generate_tech_script("La mort des NPC passifs : comment les LLM locaux rendent les PNJ conscients")
    print(json.dumps(script, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    script = generate_tech_script("Comment créer son propre Second Brain avec Obsidian et RAG")
    print(json.dumps(script, indent=2, ensure_ascii=False))
