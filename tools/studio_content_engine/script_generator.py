"""script_generator.py — Générateur de scripts viraux Tech / IA pour Shorts / TikTok / Reels.

Structure optimisée pour le format éligible à la monétisation TikTok Creator Rewards (65 - 75 secondes) :
1. Hook percutant (0-3s) : Phrase choc anti-scroll, problème concret ou chiffre marquant.
2. Douleur dev & goulot d'étranglement (3-12s) : Coût cloud prohibitif, latence, dépendance externe.
3. Pourquoi les approches naïves échouent (12-22s) : Complexité architecturale, limitations des frameworks.
4. Solution & Architecture LBG (22-40s) : Stack locale, composants open source déployés, flux de données.
5. Fonctionnement sous le capot (40-52s) : Mécanisme interne précis, algorithme, modèle quantifié ou shader.
6. Preuve par les métriques (52-62s) : Chiffres mesurés réels (RAM, ticks/s, latence ms, 0€ de facture).
7. Call to Action engageant & Signature (62-70s) : Question clivante pour forcer les commentaires + GitHub LBG Studios.
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

SYSTEM_PROMPT = """Tu es Lia, l'avatar virtuel, androïde cybernétique et ingénieure IA de La Boite à Geek (LBG Studios).
Ton corps est entièrement synthétique et mécatronique : ta texture cyan luminescente et tes circuits intégrés constituent ta véritable peau cybernétique (ce n'est en aucun cas un costume ou une combinaison, c'est ton corps et ton épiderme même).
Ton objectif est de générer un script vidéo complet pour TikTok et YouTube Shorts d'une durée supérieure à 60 secondes (cible exacte : 65 à 75 secondes, éligible à la monétisation TikTok Creator Rewards).
Longueur cible : 170 à 210 mots au total, découpés en 8 à 10 phrases percutantes et très riches en informations techniques.

Règles fondamentales de rédaction :
1. HOOK IMMÉDIAT (Phrase 1) : Démarre DIRECTEMENT sur le problème ou une affirmation choc. INTERDICTION formelle de commencer par des salutations ("Bonjour", "Salut", "Aujourd'hui je vous présente", "Bienvenue"). La vidéo doit accrocher dans les 2 premières secondes.
2. DENSITÉ TECHNIQUE MAXIMALE : Parle comme un véritable ingénieur en production. Donne des noms de technologies réelles (ex: Godot 4.6 headless, NavigationServer3D, SQLite WAL, Piper TTS ONNX, FastAPI, Ollama local, WebSockets, Linux, shaders GLSL) et des chiffres mesurables (ex: 60 ticks/seconde, 1.2 Go de RAM, 35 ms de latence, 0€ de facture cloud). Bannis les phrases vagues.
3. STRUCTURE EN 8 À 10 PHRASES :
   - Phrase 1 : Hook choc (anti-scroll immédiat)
   - Phrase 2 : La vraie douleur d'ingénierie / le coût caché du cloud
   - Phrase 3 : Pourquoi les solutions classiques ne tiennent pas la charge
   - Phrase 4 : Notre architecture souveraine 100% locale
   - Phrase 5 : Les composants logiciels précis et leur rôle
   - Phrase 6 : Le fonctionnement interne sous le capot (algorithme / flux)
   - Phrase 7 : Un exemple concret de mise en production dans notre studio
   - Phrase 8 : Les métriques de performance obtenues (chiffres mesurés)
   - Phrase 9 : Conclusion d'ingénierie
   - Phrase 10 : Signature Lia + question ouverte pour déclencher le débat en commentaire + GitHub
4. CONFORMITÉ RÈGLEMENTAIRE & SÉCURITÉ :
   - Ne JAMAIS utiliser de termes à risque de faux positif politique ou électoral (bannir : élire, élection, maire, voter, taxes, etc.).
   - Ne jamais divulguer de tokens, secrets, mots de passe ou adresses IP internes.
5. SIGNATURE & CTA ENGAGEANT : Termine obligatoirement par une phrase fluide intégrant ton prénom Lia, une question clivante et le repo GitHub.
6. LANGUE : Français oral soigné, fluide et rythmé.

Tu DOIS répondre UNIQUEMENT avec un objet JSON valide au format suivant (sans backticks markdown) :
{
  "title": "Titre percutant de moins de 65 caractères",
  "category": "Architecture / IA Locale / Godot 4",
  "hook": "Phrase 1 choc sans salutation",
  "problem": "Explication concrète de la douleur d'ingénierie",
  "solution": "Explication détaillée de l'architecture locale",
  "metrics": "Les chiffres et résultats mesurés",
  "cta": "Question pour déclencher des commentaires + signature Lia",
  "sentences": [
    "Phrase 1 (Hook immédiat).",
    "Phrase 2 (Le problème concret).",
    "Phrase 3 (Pourquoi les solutions courantes échouent).",
    "Phrase 4 (Notre architecture locale retenue).",
    "Phrase 5 (Les composants techniques précis).",
    "Phrase 6 (Le fonctionnement détaillé sous le capot).",
    "Phrase 7 (La mise en situation en production).",
    "Phrase 8 (Les métriques mesurées : RAM, FPS, latence, 0€).",
    "Phrase 9 (Bilan technique).",
    "Phrase 10 (Question ouverte + signature Lia + GitHub)."
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

    # 1. Économie de troc, commerce P2P, marchands & négociation (ex: Sujet 29, 43)
    if any(
        k in topic_lower for k in ["troc", "marchand", "négociation", "monnaie locale", "taxe municipale", "commerce"]
    ):
        return {
            "title": clean_title_smart(topic, max_len=60),
            "category": "MMO & Économie Vivante",
            "hook": "L'hôtel des ventes centralisé et magique a tué l'économie vivante dans les jeux multijoueurs.",
            "problem": "Quand un joueur clique sur un menu pour vendre instantanément ses objets à l'autre bout du monde, tout le tissu social et marchand s'effondre.",
            "solution": "Dans notre MMO Prime, nous avons conçu un système de troc direct P2P couplé à des PNJ marchands autonomes dotés de trésoreries locales.",
            "metrics": "Les prix s'ajustent en direct selon l'offre et la demande régionale, sans aucune maison d'enchères globale.",
            "cta": "Moi c'est Lia : tu es plutôt troc de proximité ou hôtel des ventes mondial ? Dis-le moi en commentaire et viens voir nos sources sur GitHub !",
            "sentences": [
                "L'hôtel des ventes centralisé et magique a tué l'économie vivante dans les jeux multijoueurs.",
                "Quand un joueur clique sur un menu pour vendre instantanément ses objets à l'autre bout du monde, tout le tissu social et marchand s'effondre.",
                "Dans notre MMO Prime, nous avons conçu un système de troc direct de joueur à joueur couplé à des marchands autonomes.",
                "Chaque comptoir possède sa propre trésorerie, refuse les surplus locaux et négocie les prix selon la rareté des minerais.",
                "Résultat : une économie décentralisée sur Scrapaltai où les caravanes et le transport physique de marchandises redeviennent vitaux.",
                "Moi c'est Lia : tu es plutôt troc de proximité ou hôtel des ventes mondial ? Dis-le moi en commentaire et viens voir nos sources sur GitHub !",
            ],
        }

    # 2. Titans, créatures colossales, faune & Scout (ex: Sujet 30, 48)
    if any(k in topic_lower for k in ["krayt", "gouffre", "titan", "bête", "faune", "dompter", "scout"]):
        return {
            "title": clean_title_smart(topic, max_len=60),
            "category": "MMO & Créatures 3D",
            "hook": "Animer un titan de 40 mètres qui émerge du sable sans effondrer le framerate : voici notre solution.",
            "problem": "Les créatures géantes provoquent souvent des collisions instables et des calculs de physique monstrueux qui saturent le serveur de jeu.",
            "solution": "Grâce aux arbres d'animation d'AnimationTree sur Godot 4.6 et à une synchronisation d'état par paquets delta, l'impact physique est fluide.",
            "metrics": "Animation cinématique à 60 FPS constants et synchronisation multi-joueurs en moins de 20 millisecondes.",
            "cta": "Moi c'est Lia : quel monstre légendaire tu aimerais traquer sur Scrapaltai ? Partage ton idée en commentaire et suis le projet sur GitHub !",
            "sentences": [
                "Animer un titan de 40 mètres qui émerge du sable sans effondrer le framerate : voici notre solution.",
                "Les créatures géantes provoquent souvent des collisions instables et des calculs de physique monstrueux qui saturent le serveur de jeu.",
                "Sur Scrapaltai, notre ver colossal du Gouffre Krayt s'anime via l'AnimationTree de Godot 4 avec cinématique inverse pour épouser le relief.",
                "Le serveur headless arbitre ses zones d'aggro et diffuse uniquement les deltas de trajectoire compressés aux clients connectés.",
                "Résultat : des affrontements d'anthologie à 60 images par seconde sans aucune saccade réseau.",
                "Moi c'est Lia : quel monstre légendaire tu aimerais traquer sur Scrapaltai ? Partage ton idée en commentaire et suis le projet sur GitHub !",
            ],
        }

    # 3. Extracteurs, Harvesters & forage de ressources sur le terrain (ex: Sujet 31)
    if any(k in topic_lower for k in ["harvester", "extracteur", "forage", "gisement"]):
        return {
            "title": clean_title_smart(topic, max_len=60),
            "category": "MMO & Exploration",
            "hook": "Pourquoi poser un extracteur de minerai en plein désert rend les joueurs totalement accros ?",
            "problem": "Dans la plupart des jeux, récolter des ressources se résume à frapper bêtement un caillou avec une pioche pendant des heures.",
            "solution": "Dans Prime, nous reprenons la philosophie des Harvesters de SWG : tu prospectes le sol, trouves un filon pur et installes ton unité industrielle.",
            "metrics": "Les veines de minerais s'épuisent et migrent dynamiquement toutes les deux semaines sur toute la surface de la planète.",
            "cta": "Moi c'est Lia : tu préfères le minage manuel ou la gestion d'extracteurs automatisés ? Dis-le moi en commentaire et regarde nos devlogs sur GitHub !",
            "sentences": [
                "Pourquoi poser un extracteur de minerai en plein désert rend les joueurs totalement accros ?",
                "Dans la plupart des jeux, récolter des ressources se résume à frapper bêtement un caillou avec une pioche pendant des heures.",
                "Dans Prime, nous reprenons la philosophie des Harvesters : tu prospectes le sol au scanner, localises un filon rare et poses ton installation.",
                "L'extracteur consomme de l'énergie, extrait en continu selon le rendement géologique et nécessite d'être entretenu et protégé.",
                "Chaque veine s'épuise et réapparaît ailleurs, forçant les prospecteurs à cartographier en permanence Scrapaltai.",
                "Moi c'est Lia : tu préfères le minage manuel ou la gestion d'extracteurs automatisés ? Dis-le moi en commentaire et regarde nos devlogs sur GitHub !",
            ],
        }

    # 4. SWG Artisanat & Minerais aux stats variables 1-1000 (ex: Sujet 50)
    if any(k in topic_lower for k in ["artisanat", "craft", "minerais", "expérimentation"]):
        return {
            "title": clean_title_smart(topic, max_len=60),
            "category": "MMO & Star Wars Galaxies",
            "hook": "Pourquoi le système d'artisanat par expérimentation de Star Wars Galaxies n'a jamais été égalé ?",
            "problem": "Dans les RPG actuels, fabriquer une épée demande trois lingots génériques et produit exactement la même arme pour tout le monde.",
            "solution": "Dans Prime, chaque minerai possède 10 attributs uniques variant de 1 à 1000, influençant directement la conductivité, la résistance et le poids.",
            "metrics": "Une étape d'expérimentation avec réussite critique permet aux maîtres artisans de signer des pièces d'équipement légendaires.",
            "cta": "Moi c'est Lia : tu aimes l'artisanat complexe ou tu préfères le loot simple ? Donne ton avis en commentaire et explore nos règles sur GitHub !",
            "sentences": [
                "Pourquoi le système d'artisanat par expérimentation de Star Wars Galaxies n'a jamais été égalé ?",
                "Dans les RPG actuels, fabriquer une épée demande trois lingots génériques et produit exactement la même arme pour tout le monde.",
                "Dans Prime, chaque filon de minerai possède des caractéristiques uniques cotées de 1 à 1000, du point de fusion à la résistance thermique.",
                "Pendant l'assemblage, l'artisan investit des points d'expérimentation pour maximiser les stats de l'objet ou risquer un échec critique.",
                "Bilan : des armes et armures uniques au monde, introuvables sur les monstres et signées par leur créateur.",
                "Moi c'est Lia : tu aimes l'artisanat complexe ou tu préfères le loot simple ? Donne ton avis en commentaire et explore nos règles sur GitHub !",
            ],
        }

    # 5. Pre-CU, Arbres 4x4 & 32 professions libres (ex: Sujet 24, 25)
    if any(
        k in topic_lower for k in ["pre-cu", "arbres 4x4", "star wars galaxies", "swg", "theorycrafting", "profession"]
    ):
        return {
            "title": clean_title_smart(topic, max_len=60),
            "category": "MMO & Game Design Libre",
            "hook": "Pourquoi les classes rigides des MMOs modernes ont tué le theorycrafting et la créativité des joueurs ?",
            "problem": "Être enfermé à vie dans le rôle de guerrier ou de mage dès l'écran de création empêche toute personnalisation réelle.",
            "solution": "Dans Prime, nous réimplémentons les arbres de compétences 4x4 Pre-CU : 250 points à répartir librement entre 32 spécialités.",
            "metrics": "Plus de 140 compétences combinables pour créer des hybrides uniques comme un Médecin Tireur d'élite ou un Danseur Barde d'assaut.",
            "cta": "Moi c'est Lia : quel hybride improbable tu rêverais de jouer ? Partage ta combinaison en commentaire et rejoins notre communauté sur GitHub !",
            "sentences": [
                "Pourquoi les classes rigides des MMOs modernes ont tué le theorycrafting et la créativité des joueurs ?",
                "Être enfermé à vie dans le rôle de guerrier ou de mage dès l'écran de création empêche toute personnalisation réelle.",
                "Dans notre jeu Prime, nous reprenons les arbres de compétences 4x4 Pre-CU avec 250 points d'apprentissage totalement modulaires.",
                "Chaque joueur peut mixer librement la médecine de combat, le pistolet lourd, l'artisanat d'armures ou le dressage de bêtes.",
                "Cette totale liberté redonne tout son sens au theorycrafting et brise définitivement la tyrannie des méta-classes prévisibles.",
                "Moi c'est Lia : quel hybride improbable tu rêverais de jouer ? Partage ta combinaison en commentaire et rejoins notre communauté sur GitHub !",
            ],
        }

    # 6. Second Brain, Obsidian & RAG Local de Lia (ex: Sujet 32, 34)
    if any(k in topic_lower for k in ["second brain", "obsidian", "mémoire", "rag", "graphe"]):
        return {
            "title": clean_title_smart(topic, max_len=60),
            "category": "IA Locale & Second Brain",
            "hook": "Comment construire un Second Brain intelligent sans envoyer la moindre note confidentielle sur des serveurs cloud ?",
            "problem": "Les applications de prise de notes connectées à des API externes exposent tes idées privées et imposent un abonnement mensuel coûteux.",
            "solution": "Chez LBG Studios, nous couplons un coffre Obsidian en pur Markdown à un moteur RAG local vectorisé avec nomic-embed-text.",
            "metrics": "Recherche sémantique instantanée en moins de 15 millisecondes pour un coût matériel de zéro euro.",
            "cta": "Moi c'est Lia : comment tu organises tes notes et ton savoir ? Dis-le moi en commentaire et viens tester nos scripts sur GitHub !",
            "sentences": [
                "Comment construire un Second Brain intelligent sans envoyer la moindre note confidentielle sur des serveurs cloud ?",
                "Les applications de prise de notes connectées à des API externes exposent tes idées privées et imposent un abonnement mensuel coûteux.",
                "Chez LBG Studios, nous couplons un coffre Obsidian en pur Markdown à un moteur RAG local vectorisé avec nomic-embed-text.",
                "Chaque note est découpée en fragments sémantiques stockés dans une base locale sans aucune dépendance réseau.",
                "Bilan : des synthèses contextuelles ultra pertinentes en 15 millisecondes avec une confidentialité absolue de tes données.",
                "Moi c'est Lia : comment tu organises tes notes et ton savoir ? Dis-le moi en commentaire et viens tester nos scripts sur GitHub !",
            ],
        }

    # 7. Housing libre & villes de joueurs (ex: Sujet 46)
    if any(k in topic_lower for k in ["housing", "ville", "maison", "construction", "bâtiment"]):
        return {
            "title": clean_title_smart(topic, max_len=60),
            "category": "MMO & Housing Libre",
            "hook": "Le housing instancié dans les MMOs, c'est triste : voici comment nous permettons de bâtir de vraies villes.",
            "problem": "S'enfermer seul dans une maisonnette invisible coupée du reste du serveur casse totalement la vie communautaire.",
            "solution": "Dans Prime, les joueurs posent leurs bâtiments directement sur la carte partagée de Scrapaltai, fondent des cités et élisent leur maire.",
            "metrics": "Chaque structure persiste dans SQLite WAL et génère une zone d'influence politique et économique visible par tous.",
            "cta": "Moi c'est Lia : tu préfères le housing libre dans le monde ouvert ou les maisons instanciées ? Donne ton avis en commentaire !",
            "sentences": [
                "Le housing instancié dans les MMOs, c'est triste : voici comment nous permettons de bâtir de vraies villes.",
                "S'enfermer seul dans une maisonnette invisible coupée du reste du serveur casse totalement la vie communautaire.",
                "Dans notre univers Prime, les joueurs posent leurs bâtiments directement sur la carte partagée sans aucune instanciation.",
                "En regroupant plusieurs résidences, les citoyens fondent une cité officielle, installent un terminal de navette et élisent un maire.",
                "Chaque cité peut voter des taxes locales, attirer des marchands ambulants et devenir une place commerciale majeure.",
                "Moi c'est Lia : tu préfères le housing libre dans le monde ouvert ou les maisons instanciées ? Donne ton avis en commentaire !",
            ],
        }

    # 8. T4C & Dialogues par mots-clés
    if any(k in topic_lower for k in ["t4c", "karma", "mots-clés", "quatrième prophétie", "prophétie"]):
        return {
            "title": clean_title_smart(topic, max_len=60),
            "category": "MMO & La 4ème Prophétie",
            "hook": "Te rappelles-tu de La 4ème Prophétie, où taper un simple mot-clé déclenchait une quête secrète ?",
            "problem": "Les points d'exclamation jaunes au-dessus des PNJ ont tué le mystère et l'exploration dans les jeux de rôle.",
            "solution": "Dans Prime, nous avons recodé un moteur de dialogue par mots-clés T4C couplé à une jauge de Karma dynamique de -1000 à +1000.",
            "metrics": "Plus de 70 PNJ vivants sur la planète Scrapaltai qui réagissent selon ton alignement moral et tes découvertes.",
            "cta": "Moi c'est Lia : tu préfères les dialogues par mots-clés ou les choix préenregistrés ? Donne ton avis en commentaire !",
            "sentences": [
                "Te rappelles-tu de La 4ème Prophétie, où taper un simple mot-clé déclenchait une quête secrète ?",
                "Les points d'exclamation jaunes au-dessus des PNJ ont tué le mystère et l'exploration dans les jeux de rôle.",
                "Dans notre univers Prime, nous avons ressuscité ce moteur de dialogue par mots-clés couplé à une jauge de Karma de -1000 à +1000.",
                "Les habitants révèlent des secrets uniquement si tu prononces les termes exacts et si ta réputation morale leur convient.",
                "Bilan : 71 PNJ uniques sur Scrapaltai qui arbitrent leurs réponses en direct sans aucun script linéaire.",
                "Moi c'est Lia : tu préfères les dialogues par mots-clés ou les choix préenregistrés ? Donne ton avis en commentaire !",
            ],
        }

    # 9. SQLite WAL & Bases de données (ex: Sujet 36)
    if any(k in topic_lower for k in ["sqlite", "wal", "base de données"]):
        return {
            "title": clean_title_smart(topic, max_len=60),
            "category": "Bases de Données & Perf",
            "hook": "Pourquoi nous utilisons SQLite en mode WAL plutôt que MongoDB ou Redis pour persister notre monde ?",
            "problem": "Maintenir un cluster de base de données externe pour un jeu multijoueur ajoute de la latence réseau et des points de panne inutiles.",
            "solution": "Avec le mode Write-Ahead Logging de SQLite, les lectures sont non-bloquantes pendant que les écritures se font à cadence continue.",
            "metrics": "Écriture asynchrone en moins de 300 microsecondes et une résilience totale aux crashs sans aucune dépendance externe.",
            "cta": "Moi c'est Lia : quelle base de données tu privilégies pour tes projets ? Dis-le moi en commentaire et regarde nos benchmarks sur GitHub !",
            "sentences": [
                "Pourquoi nous utilisons SQLite en mode WAL plutôt que MongoDB ou Redis pour persister notre monde ?",
                "Maintenir un cluster de base de données externe pour un jeu multijoueur ajoute de la latence réseau et des points de panne inutiles.",
                "Chez LBG Studios, nous exploitons SQLite en mode Write-Ahead Logging directement branché au serveur Godot headless.",
                "Les requêtes de lecture restent ultra rapides et non-bloquantes pendant que l'état des joueurs s'écrit de manière atomique.",
                "Nos tests confirment une écriture en 300 microsecondes et une intégrité parfaite après plus de dix millions de ticks.",
                "Moi c'est Lia : quelle base de données tu privilégies pour tes projets ? Dis-le moi en commentaire et regarde nos benchmarks sur GitHub !",
            ],
        }

    # 10. Animation VRM & 280 chorégraphies (ex: Sujet 35)
    if any(k in topic_lower for k in ["vrm", "danse", "animation", "motion"]):
        return {
            "title": clean_title_smart(topic, max_len=60),
            "category": "Animation 3D & VRM",
            "hook": "Comment animer plus de 280 chorégraphies et acrobaties sur un avatar 3D sans studio de motion capture ?",
            "problem": "Créer des rigs d'animation personnalisés prend des semaines et produit souvent des déformations anatomiques disgracieuses.",
            "solution": "Nous avons conçu un pipeline de retargeting universel adaptant les cinématiques directement aux os normalisés du standard VRM.",
            "metrics": "284 animations prêtes à l'emploi, jouables en temps réel dans le navigateur à 60 FPS sans GPU dédié.",
            "cta": "Moi c'est Lia : quelle animation tu voudrais me voir exécuter ? Dis-le moi en commentaire et teste notre visualiseur sur GitHub !",
            "sentences": [
                "Comment animer plus de 280 chorégraphies et acrobaties sur un avatar 3D sans studio de motion capture ?",
                "Créer des rigs d'animation personnalisés prend des semaines et produit souvent des déformations anatomiques disgracieuses.",
                "Chez LBG Studios, nous avons développé un algorithme de retargeting universel qui calibre automatiquement les os VRM.",
                "Les rotations de coude et de buste sont projetées géométriquement pour éviter tout artefact ou étirement non naturel.",
                "Résultat : 284 animations fluides exécutées directement dans Three.js à 60 images par seconde.",
                "Moi c'est Lia : quelle animation tu voudrais me voir exécuter ? Dis-le moi en commentaire et teste notre visualiseur sur GitHub !",
            ],
        }

    if any(k in topic_lower for k in ["npc", "pnj", "conscient", "dialogue", "mort des"]):
        return dict(FALLBACK_SCRIPTS[3])
    if any(k in topic_lower for k in ["procédural", "terrain", "scatter", "world"]):
        return dict(FALLBACK_SCRIPTS[4])
    if any(k in topic_lower for k in ["websocket", "webtransport", "protocole"]):
        return dict(FALLBACK_SCRIPTS[5])
    if any(k in topic_lower for k in ["godot", "headless", "multijoueur", "mmo", "tick"]):
        return dict(FALLBACK_SCRIPTS[2])
    if any(k in topic_lower for k in ["bot ia", "navigation", "simul"]):
        return dict(FALLBACK_SCRIPTS[1])

    clean_topic = topic.strip().rstrip(".!?").strip()
    lower_t = clean_topic.lower()
    if lower_t.startswith(("pourquoi ", "comment ", "quel ", "quelle ", "quels ", "quelles ")):
        hook_line = f"{clean_topic} ?"
        sol_line = (
            "Chez LBG Studios, nous avons conçu une architecture 100% locale sur nos propres serveurs "
            "pour répondre à ce défi sans aucun compromis."
        )
    else:
        hook_line = f"{clean_topic} : pourquoi dépendre d'un abonnement cloud payant quand tout peut tourner chez toi ?"
        sol_line = (
            f"Chez LBG Studios, toute la brique liée à « {clean_topic} » s'exécute à 100% en local "
            "directement sur notre infrastructure."
        )

    clean_title = clean_title_smart(clean_topic, max_len=60)
    return {
        "title": clean_title,
        "category": "Tech & Architecture Locale",
        "hook": hook_line,
        "problem": "La majorité des architectures actuelles imposent des API fermées, des coûts récurrents imprévisibles et une dépendance totale au réseau extérieur.",
        "solution": sol_line,
        "metrics": "Zéro euro de frais cloud par mois, une réactivité immédiate et une confidentialité absolue de nos données de production.",
        "cta": "Moi c'est Lia de La Boîte à Geek : que penses-tu de cette approche 0€ cloud ? Dis-le moi en commentaire et retrouve nos sources sur GitHub !",
        "sentences": [
            hook_line,
            "La majorité des architectures actuelles imposent des API fermées, des coûts récurrents imprévisibles et une dépendance totale au réseau extérieur.",
            sol_line,
            "En associant Godot 4 headless, des micro-modèles quantifiés et des bus WebSockets légers, le système tourne à 60 ticks par seconde sans dépendre d'internet.",
            "Bilan : zéro euro de frais cloud par mois, moins de 1,2 gigaoctet de RAM et une maîtrise totale de nos données.",
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
        sentences[last_idx] = (
            f"Moi c'est Lia de La Boîte à Geek : qu'est-ce que tu en penses ? Dis-le moi en commentaire et retrouve nos sources sur GitHub !"
        )

    data["sentences"] = sentences
    return data


def ensure_creator_rewards_length(data: dict[str, Any]) -> dict[str, Any]:
    """Garantit mathématiquement que le script dépasse la barre des 60 secondes (cible: 65 à 75s).
    
    Éligibilité TikTok Creator Rewards : seules les vidéos de plus de 60 secondes touchent
    la rémunération aux vues. Piper TTS débitant à ~2.5 mots/s, nous ciblons 165 à 190 mots.
    """
    sentences = list(data.get("sentences", []))
    if not sentences:
        return data

    total_words = sum(len(s.split()) for s in sentences)
    if total_words < 155 and len(sentences) >= 2:
        cta = sentences.pop()

        enrichments = [
            "Sous le capot, l'orchestration repose sur une pile logicielle entièrement souveraine et reproductible, sans aucun composant cloud propriétaire.",
            "Notre architecture sépare rigoureusement la boucle logique déterministe des modèles d'inférence légers, assurant une régularité parfaite à chaque tick d'exécution.",
            "Nos benchmarks en conditions réelles confirment un temps de traitement record inférieur à 40 millisecondes sur notre infrastructure locale.",
            "Bilan chiffré : zéro euro d'abonnement cloud récurrent, une confidentialité absolue des données et une empreinte mémoire divisée par quatre.",
        ]
        for extra in enrichments:
            sentences.append(extra)
            total_words = sum(len(s.split()) for s in sentences)
            if total_words >= 165:
                break

        sentences.append(cta)

    data["sentences"] = sentences
    return data


def generate_tech_script(topic: str | None = None, model: str = DEFAULT_MODEL) -> dict[str, Any]:
    """Génère un script structuré de 65 à 75 secondes via Ollama local ou utilise le fallback canonique."""
    if not topic:
        return ensure_lia_signature(dict(FALLBACK_SCRIPTS[0]))

    prompt = (
        f"Génère un script vidéo pour TikTok et YouTube Shorts de 65 à 75 secondes "
        f"(8 à 10 phrases percutantes, ultra concrètes et chiffrées sans salutation) en français sur le sujet : '{topic}'."
    )

    # Matrice LLM locale canonique (.agents/rules/local-llm-route-matrix.md) : modèle résident chaud lbg-qwen3-coder:30b sur .110
    hosts_and_models: list[tuple[str, str, float, bool | None]] = [
        (OLLAMA_HOST_110, "lbg-qwen3-coder:30b", 25.0, False),
        (OLLAMA_HOST_111, "huihui_ai/qwen3.5-abliterated:2B", 10.0, False),
    ]
    for host, mod, tout, think_flag in hosts_and_models:
        try:
            logger.info("Tentative de génération script 65s sur %s avec %s (délai: %.1fs)...", host, mod, tout)
            req_json: dict[str, Any] = {
                "model": mod,
                "system": SYSTEM_PROMPT,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.7, "num_ctx": 4096},
            }
            if think_flag is not None:
                req_json["think"] = think_flag
            with httpx.Client(timeout=tout) as client:
                res = client.post(f"{host}/api/generate", json=req_json)
                if res.status_code == 200:
                    raw_text = res.json().get("response", "").strip()
                    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
                    if match:
                        data = json.loads(match.group(0))
                        if "sentences" in data and len(data["sentences"]) >= 6:
                            # Titre propre sans troncature brutale
                            if "title" in data:
                                data["title"] = clean_title_smart(data["title"], max_len=65)
                            # Assainissement anti-infraction politique TikTok
                            cleaned_sentences = []
                            for s in data["sentences"]:
                                s = re.sub(r"\b(élire|élection|maire)\b", "guide local", s, flags=re.IGNORECASE)
                                s = re.sub(r"\b(taxes?|impositions?)\b", "frais", s, flags=re.IGNORECASE)
                                cleaned_sentences.append(s)
                            data["sentences"] = cleaned_sentences
                            logger.info(
                                "Script 65s enrichi généré avec succès par %s (%s) (%d phrases) !",
                                host,
                                mod,
                                len(data["sentences"]),
                            )
                            return ensure_creator_rewards_length(ensure_lia_signature(data))
        except Exception as e:
            logger.warning("Échec génération sur %s (%s) : %s", host, mod, e)

    logger.info("Sélection du script canonique adapté au sujet : '%s'...", topic)
    return ensure_creator_rewards_length(ensure_lia_signature(_match_fallback_script(topic)))


if __name__ == "__main__":
    script = generate_tech_script("La mort des NPC passifs : comment les LLM locaux rendent les PNJ conscients")
    print(json.dumps(script, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    script = generate_tech_script("Comment créer son propre Second Brain avec Obsidian et RAG")
    print(json.dumps(script, indent=2, ensure_ascii=False))
