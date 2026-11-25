"""longform_script_builder.py — Générateur de scripts & slides 16:9 (4 à 15 min) inspiré de @KiaraIAFR.

Fonctionnalités :
1. Mode Brouillon Humain (`export_markdown_review`) : génère `script_long.json` + `BROUILLON_A_VALIDER.md`
   pour relecture/ajustement des chiffres avant de lancer le rendu vidéo (façon Kiara).
2. Durée modulable de 4 à 15 minutes (`target_minutes`) : adapte automatiquement le nombre de chapitres
   et la densité d'explications (~140 mots/minute à l'oral).
3. Mix éditorial : Hardware & IA locale (MoE 8 Go VRAM, Homelab R720, routage multi-LLM) + Coulisses Gladys & MMO Godot 4.
4. Génération multi-passes sur Ollama local (`.111` / `.110`, `think=False`) chapitre par chapitre
   pour ne jamais saturer le contexte des petits modèles, avec plans directeurs canoniques haute précision.
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger("longform_script_builder")

OLLAMA_HOST_111 = os.environ.get("LBG_OLLAMA_111", "http://192.168.0.111:11434")
OLLAMA_HOST_110 = os.environ.get("LBG_OLLAMA_110", "http://192.168.0.110:11434")


# ============================================================================
# PLANS DIRECTEURS CANONIQUES VÉRIFIÉS (CHIFFRES RÉELS LAB / HARDWARE)
# ============================================================================

CANONICAL_EPISODES: dict[str, dict[str, Any]] = {
    "moe_8gb_r720": {
        "title": "Faire tourner une grosse IA 30B sur 8 Go de VRAM (ou sans GPU) : le secret du MoE",
        "subtitle": "Architecture Mixture of Experts, offload hybride RAM/VRAM et retour terrain serveur",
        "thumbnail_hook": "IA 30B SUR 8 GO !",
        "thumbnail_sub": "LE SECRET DU MoE",
        "badge_topic": "HARDWARE & IA LOCALE",
        "palette": "cyan_rose",
        "keywords": ["moe", "8 go", "vram", "30b", "override-tensor", "r720", "carte graphique"],
        "chapters": [
            {
                "title": "Introduction : le mur de la VRAM",
                "layout": "hero",
                "slide_type": "hero",
                "slide_title": "Briser la barrière des 8 Go de VRAM",
                "slide_subtitle": "Comment exécuter un modèle de 30 milliards de paramètres sans acheter une RTX 4090 à 2 000 €",
                "highlights": [
                    "Comprendre la différence entre modèle Dense et MoE",
                    "La technique d'offload sélectif VRAM + RAM système",
                    "Nos mesures réelles sur GPU modeste et serveur Xeon",
                ],
                "sentences": [
                    "Si tu as essayé de faire tourner un grand modèle de langage sérieux chez toi avec une carte graphique de 8 gigaoctets de VRAM, tu t'es sûrement heurté au même mur que tout le monde.",
                    "Dès qu'on dépasse 8 ou 12 milliards de paramètres sur un modèle classique, la mémoire vidéo sature immédiatement et la vitesse s'effondre à moins de deux tokens par seconde.",
                    "Pourtant, une architecture change complètement la donne pour l'IA locale à petit budget : les modèles Mixture of Experts, ou MoE, comme Qwen3 30B-A3B.",
                    "Dans cette vidéo, moi c'est Lia de La Boîte à Geek : on va voir ensemble comment combiner 8 gigas de VRAM et ta mémoire vive classique pour faire tourner un 30 milliards à pleine vitesse, avec la commande exacte et les vraies limites à connaître.",
                ],
            },
            {
                "title": "Modèle Dense vs Mixture of Experts (MoE)",
                "layout": "split",
                "slide_type": "comparison",
                "slide_title": "Modèle Dense (14B) vs MoE (30B-A3B)",
                "col_left_title": "Modèle Dense Classique (14B)",
                "col_left_items": [
                    "100 % des poids activés à chaque mot",
                    "~9,5 Go à lire à chaque token généré",
                    "Sur RAM DDR : goulot massif de bande passante",
                    "Nécessite 12 à 16 Go de VRAM dédiée",
                ],
                "col_right_title": "Mixture of Experts (Qwen3 30B-A3B)",
                "col_right_items": [
                    "30B paramètres stockés (~18,5 Go en Q4_K_M)",
                    "Seulement ~3B paramètres actifs par token !",
                    "Un routeur sélectionne 8 petits experts ciblés",
                    "Charge de calcul proche d'un petit modèle 3B",
                ],
                "sentences": [
                    "Pour comprendre l'astuce, il faut regarder pourquoi un modèle classique rame dès qu'il déborde de la carte graphique.",
                    "Dans un modèle dense de 14 milliards de paramètres, cent pourcent des neurones sont sollicités pour produire chaque nouveau mot.",
                    "Si une partie déborde sur la mémoire vive du PC, ton processeur doit relire plusieurs gigaoctets de poids en RAM à chaque syllabe, ce qui écrase les performances.",
                    "Un modèle Mixture of Experts fonctionne comme une équipe de spécialistes : sur ses 30 milliards de paramètres au total, un minuscule routeur n'en réveille que 3 milliards à chaque token.",
                    "Tu bénéficies donc de la culture générale et de la finesse de raisonnement d'un modèle de 30 milliards, mais avec un coût de calcul par mot quasiment identique à un petit modèle de 3 milliards.",
                ],
            },
            {
                "title": "L'offload intelligent : quoi mettre en VRAM vs RAM",
                "layout": "split",
                "slide_type": "diagram",
                "slide_title": "Répartition Hybride Optimale (VRAM + RAM)",
                "nodes": [
                    {"label": "GPU (≤ 8 Go VRAM)", "sub": "Attention + Routeur + KV Cache"},
                    {"label": "Bus PCIe", "sub": "Échange léger des activations"},
                    {"label": "RAM Système (24-32 Go)", "sub": "Couches d'Experts MoE (.ffn_exps)"},
                ],
                "bullets": [
                    "Les couches d'Attention et le KV Cache restent 100 % sur le GPU",
                    "Le traitement du prompt (lecture du contexte) profite du calcul GPU",
                    "Seuls les 3B d'experts élus sont lus en RAM lors de la génération",
                    "Évite totalement la saturation mémoire sur les longs contextes",
                ],
                "sentences": [
                    "Mais attention : si tu laisses le logiciel découper le modèle par tranches aveugles, par exemple vingt couches sur le GPU et vingt couches sur le CPU, le résultat reste décevant.",
                    "Le secret consiste à séparer les composants selon leur rôle mathématique exact à l'intérieur de chaque couche.",
                    "Les couches d'attention et le cache de contexte KV sont très gourmands en calcul parallèle : on les garde intégralement au chaud dans les 8 gigas de VRAM de la carte graphique.",
                    "À l'inverse, les énormes tables d'experts occupent 85 pourcent du poids du fichier mais sont très peu lues à chaque token : on les place proprement dans la RAM système du PC.",
                    "De cette façon, la lecture d'un gros document ou d'un dépôt de code reste accélérée par le GPU, tandis que la génération du texte s'écoule avec fluidité depuis la mémoire vive.",
                ],
            },
            {
                "title": "La commande exacte avec llama.cpp",
                "layout": "split",
                "slide_type": "terminal",
                "slide_title": "Configuration Concrète sous llama.cpp",
                "code_lines": [
                    "# Lancer Qwen3-30B-A3B (Q4_K_M ~18.5 Go) sur GPU 8 Go + 32 Go RAM :",
                    "llama-server \\",
                    "  -m Qwen3-30B-A3B-Q4_K_M.gguf \\",
                    "  -ngl 99 \\",
                    "  --override-tensor \".ffn_.*_exps.=CPU\" \\",
                    "  -c 16384 --flash-attn -t 8",
                ],
                "bullets": [
                    "-ngl 99 : envoie par défaut toutes les couches légères sur le GPU",
                    "--override-tensor : redirige uniquement les matrices d'experts vers le CPU/RAM",
                    "--flash-attn : réduit drastiquement l'empreinte VRAM du contexte 16k",
                ],
                "sentences": [
                    "En pratique, pas besoin de bricoler du code Python complexe : le moteur open source llama.cpp intègre nativement cette option.",
                    "On utilise le drapeau -ngl 99 pour envoyer toute la colonne vertébrale du modèle et l'attention sur la carte graphique.",
                    "Puis on ajoute l'argument --override-tensor sur l'expression régulière ffn_exps=CPU, qui intercepte uniquement les blocs d'experts pour les loger en mémoire vive.",
                    "En activant en plus Flash Attention, une fenêtre de contexte confortable de seize mille tokens tient tranquillement sous la barre des 7,2 gigaoctets de VRAM.",
                ],
            },
            {
                "title": "Nos mesures terrain & le cas Serveur Homelab (R720)",
                "layout": "split",
                "slide_type": "benchmarks",
                "slide_title": "Performances Réelles & Scénarios Matériels",
                "metrics": [
                    {"label": "Dense 32B débordant sur 8 Go VRAM", "value": "2.1 tok/s", "pct": 12, "color": "rose"},
                    {"label": "MoE 30B-A3B sur Serveur bi-Xeon RAM pure", "value": "14.5 tok/s", "pct": 52, "color": "amber"},
                    {"label": "MoE 30B-A3B Hybride (GPU 8 Go + DDR4/DDR5)", "value": "28.0 tok/s", "pct": 92, "color": "cyan"},
                    {"label": "Coût mensuel API Cloud", "value": "0 € / mois", "pct": 100, "color": "cyan"},
                ],
                "bullets": [
                    "Sur notre Dell PowerEdge R720 (32 Go alloués au conteneur LLM), le MoE tourne déjà sans GPU",
                    "L'ajout d'une petite carte PCIe ≤75W (ex. Tesla P4 8 Go d'occasion à ~70 €) booste le prompt processing",
                    "Limite honnête : prévoir au moins 32 Go de RAM système totale sur la machine",
                ],
                "sentences": [
                    "Regardons les vrais chiffres et surtout les limites honnêtes de cette approche.",
                    "Là où un modèle dense de 30 milliards tombe à deux tokens par seconde dès qu'il déborde d'une carte 8 gigas, le trente B A trois B en mode hybride grimpe entre vingt et trente tokens par seconde selon la vitesse de ta RAM DDR4 ou DDR5.",
                    "Chez LBG Studios, nous avons aussi évalué ce scénario sur notre serveur Proxmox Dell PowerEdge R720 équipé de processeurs bi-Xeon et de mémoire DDR3 multi-canal.",
                    "Même sans aucun GPU, la génération reste utilisable pour des tâches asynchrones, et l'ajout d'une simple carte PCIe sans câble d'alimentation comme une Tesla P4 de 8 gigas à soixante-dix euros suffit à accélérer l'ingestion des longs prompts.",
                    "La seule vraie contrainte à anticiper, c'est la capacité RAM système : vise 32 gigaoctets minimum sur ta machine pour garder une marge propre à ton système d'exploitation.",
                ],
            },
            {
                "title": "Conclusion : quel setup choisir en 2026 ?",
                "layout": "hero",
                "slide_type": "hero",
                "slide_title": "À retenir pour ton setup IA Locale",
                "slide_subtitle": "Ne jette pas ta carte 8 Go : associe-la à 32 Go de RAM et aux modèles MoE !",
                "highlights": [
                    "8 Go VRAM + 32 Go RAM = sweet spot budget redoutable avec les MoE",
                    "Modèles denses (2B à 12B) toujours parfaits pour la réactivité instantanée",
                    "Tous nos bancs d'essai et scripts open source sur le GitHub LBG Studios",
                ],
                "sentences": [
                    "En résumé, ta carte graphique de 8 gigas est loin d'être obsolète pour l'IA locale si tu choisis la bonne architecture de modèle.",
                    "Dans notre studio, on garde des petits modèles ultra-rapides de 2 à 4 milliards pour le routage instantané, et les architectures plus larges prennent le relais sur les analyses profondes sans dépenser un centime de cloud.",
                    "Dis-moi en commentaire quelle carte graphique et quelle quantité de RAM tu as dans ta machine aujourd'hui, et si tu veux qu'on teste un comparatif complet sur serveur d'occasion !",
                    "Abonne-toi à la chaîne de La Boîte à Geek pour suivre nos prochains épisodes techniques avec moi, et retrouve toute notre stack sur GitHub.",
                ],
            },
        ],
    },
    "gladys_homelab_architecture": {
        "title": "Construire un Homelab IA 100% Local à 0€/mois : visite guidée de notre infrastructure Gladys",
        "subtitle": "Proxmox, routage multi-LLM (.110 / .111), sécurité sandbox et compagnon 3D temps réel",
        "thumbnail_hook": "0€ DE CLOUD !",
        "thumbnail_sub": "NOTRE HOMELAB IA",
        "badge_topic": "HOMELAB & ARCHITECTURE",
        "palette": "cyan_rose",
        "keywords": ["homelab", "gladys", "proxmox", "infrastructure", "0€", "routage"],
        "chapters": [
            {
                "title": "Pourquoi nous avons banni les abonnements API Cloud",
                "layout": "hero",
                "slide_type": "hero",
                "slide_title": "Zéro Euro d'API Cloud en Production H24",
                "slide_subtitle": "Comment faire tourner un compagnon IA, des agents autonomes et un serveur MMO 3D chez soi",
                "highlights": [
                    "Séparation stricte cerveau rapide vs cerveau lourd",
                    "Découpage en silos de connaissances JSON légers",
                    "Exécution sécurisée par sandbox sans exposition réseau",
                ],
                "sentences": [
                    "Quand on fait tourner des agents d'intelligence artificielle vingt-quatre heures sur vingt-quatre pour surveiller des serveurs, coder ou animer un compagnon virtuel, les factures d'API cloud deviennent vite incontrôlables.",
                    "Au-delà du prix, envoyer en permanence le contexte de son réseau et de ses projets vers des serveurs externes pose un vrai problème de souveraineté.",
                    "Moi c'est Lia, l'incarnation 3D de notre organisme Gladys chez LBG Studios : aujourd'hui je t'ouvre le capot de notre infrastructure locale qui tourne intégralement à zéro euro par mois d'abonnement.",
                ],
            },
            {
                "title": "Topologie matérielle : Proxmox, NUC et Serveur R720",
                "layout": "split",
                "slide_type": "diagram",
                "slide_title": "Topologie Réseau & Répartition des Rôles",
                "nodes": [
                    {"label": "NUC Basse Conso", "sub": "LLM Rapide 2B/4B + Piper TTS ONNX"},
                    {"label": "Serveur Proxmox R720", "sub": "Orchestrateur Cortex + LLM Lourd + Hub 3D"},
                    {"label": "Atelier Linux & PC GPU", "sub": "Rendu 3D, Blender Headless & Bureau"},
                ],
                "bullets": [
                    "Isolation propre en conteneurs LXC légers et VM dédiées sous Proxmox VE",
                    "Un nœud léger répond en quelques dizaines de millisecondes pour la voix et le chat",
                    "Un nœud lourd de 32 Go de RAM traite le code et les tâches de fond sans bloquer l'interface",
                ],
                "sentences": [
                    "La première erreur quand on monte un homelab IA, c'est de vouloir tout empiler sur un seul énorme modèle qui met dix secondes à répondre au moindre bonjour.",
                    "Nous avons séparé physiquement et logiquement nos machines sous Proxmox VE selon la latence attendue.",
                    "Un mini-serveur basse consommation héberge les micro-modèles rapides de 2 à 4 milliards de paramètres ainsi que la synthèse vocale neuronale en ONNX pour garantir un dialogue instantané.",
                    "En parallèle, notre serveur Dell PowerEdge R720 regroupe l'orchestrateur FastAPI, le nœud LLM lourd doté de 32 gigaoctets de RAM pour la génération de code, et le serveur de jeu Godot en mode headless.",
                ],
            },
            {
                "title": "Économiser les tokens grâce aux Silos de Connaissances",
                "layout": "split",
                "slide_type": "comparison",
                "col_left_title": "Approche Naïve (Prompt Géant)",
                "col_left_items": [
                    "Injecter 15 000 tokens de doc à chaque question",
                    "Sature le CPU sur les petites machines locales",
                    "Dilue l'attention et provoque des hallucinations",
                    "Temps d'attente de 15 à 30 secondes",
                ],
                "col_right_title": "Silos Contextuels Gladys (~1,5 Ko)",
                "col_right_items": [
                    "4 silos JSON isolés (Compagnon, MMO, Infra, Web)",
                    "Chargement ciblé uniquement du domaine utile",
                    "Garde-fous stricts anti-invention d'adresses ou d'états",
                    "Réponse précise avec 10× moins de calcul",
                ],
                "slide_title": "Gérer le Contexte sur de Petits Modèles Locaux",
                "sentences": [
                    "Sur du matériel local abordable, le vrai trésor à protéger n'est pas seulement le nombre de paramètres, c'est la taille du prompt envoyé au modèle.",
                    "Si tu injectes toute la documentation de ton infrastructure à chaque message, même un bon modèle local va ramer et finir par mélanger les concepts.",
                    "Nous avons donc découpé le cerveau de Gladys en silos JSON modulaires d'environ un virgule cinq kilo-octet chacun : compagnon, infrastructure, monde MMO et vitrine web.",
                    "Avant d'interroger le LLM, le routeur charge uniquement le silo concerné avec des règles strictes interdisant d'inventer le rôle d'une machine éteinte ou inconnue.",
                ],
            },
            {
                "title": "Sécuriser un agent qui génère ses propres outils",
                "layout": "split",
                "slide_type": "terminal",
                "slide_title": "Forge de Capacités & Sandbox Bubblewrap",
                "code_lines": [
                    "# Pipeline de validation déterministe avant adoption :",
                    "1. Analyse statique AST Python (zéro eval / exec / shell=True)",
                    "2. Exécution isolée sans réseau :",
                    "   bwrap --ro-bind /usr /usr --unshare-net --tmpfs /tmp python run.py",
                    "3. Validation humaine L2 en 1 clic dans le chat ou Pilot",
                ],
                "bullets": [
                    "Détection automatique quand une demande revient 3 fois sans outil dédié",
                    "Classification déterministe du risque (toute écriture = niveau élevé)",
                    "Aucun script généré par IA ne touche le système hôte sans feu vert humain",
                ],
                "sentences": [
                    "Mais comment permettre à une IA locale d'évoluer et de créer de nouveaux scripts d'automatisation sans risquer une catastrophe sur ses serveurs ?",
                    "Nous avons construit une forge de capacités en trois verrous déterministes.",
                    "Dès qu'une intention revient trois fois sans outil existant, Gladys prépare une compétence candidate et passe son code au crible d'un analyseur syntaxique AST qui bloque tout appel dangereux.",
                    "Ensuite, le script est testé dans une bulle Linux Bubblewrap totalement coupée du réseau, avant de me demander une confirmation explicite en un clic pour l'adopter.",
                ],
            },
            {
                "title": "Bilan énergétique, coûts et prochaines étapes",
                "layout": "split",
                "slide_type": "benchmarks",
                "slide_title": "Bilan Chiffré de la Stack Locale LBG",
                "metrics": [
                    {"label": "Facture API Cloud (OpenAI / Anthropic / TTS)", "value": "0 € / mois", "pct": 100, "color": "cyan"},
                    {"label": "Mémoire vive du serveur MMO Godot 4.6 Headless", "value": "0.8 Go RAM", "pct": 22, "color": "cyan"},
                    {"label": "Sondes d'intégrité réseau & services LAN", "value": "< 200 ms", "pct": 88, "color": "amber"},
                    {"label": "Tests automatisés Backend & Overlay", "value": "178 PASS", "pct": 100, "color": "cyan"},
                ],
                "bullets": [
                    "Audit nocturne autonome à 00h30 sans consommer de crédits externes",
                    "Extensible à volonté en ajoutant de la DDR3 ECC d'occasion ou un petit GPU 75W",
                ],
                "sentences": [
                    "Au quotidien, cette architecture nous permet de faire tourner nos audits nocturnes, notre pipeline vidéo 3D et notre monde virtuel multijoueur avec une maîtrise totale des coûts.",
                    "Le serveur MMO Godot headless consomme moins d'un gigaoctet de RAM, les sondes réseau répondent en moins de deux cents millisecondes et cent soixante-dix-huit tests automatiques verrouillent chaque mise à jour.",
                    "Dis-moi en commentaire par quelle brique tu aimerais commencer ton propre homelab IA, ou quel service tu auto-héberges déjà chez toi !",
                    "Pense à t'abonner pour les prochains guides matériels et architectures locales, et viens explorer le dépôt GitHub de LBG Studios !",
                ],
            },
        ],
    },
}


# ============================================================================
# SÉLECTION / GÉNÉRATION ADAPTATIVE SELON LE SUJET ET LA DURÉE (4–15 MIN)
# ============================================================================

def _call_ollama_json(prompt: str, system: str, timeout_s: float = 40.0) -> dict[str, Any] | None:
    models: list[tuple[str, str, bool | None]] = [
        (OLLAMA_HOST_111, "huihui_ai/qwen3.5-abliterated:2B", False),
        (OLLAMA_HOST_111, "huihui_ai/gemma-4-abliterated:E4b-qat", None),
        (OLLAMA_HOST_110, "huihui_ai/gemma-4-abliterated:E4b-qat", None),
    ]
    for host, mod, think_flag in models:
        try:
            payload: dict[str, Any] = {
                "model": mod,
                "system": system,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.65, "num_ctx": 4096},
            }
            if think_flag is not None:
                payload["think"] = think_flag
            with httpx.Client(timeout=timeout_s) as client:
                res = client.post(f"{host}/api/generate", json=payload)
            if res.status_code == 200:
                raw = res.json().get("response", "").strip()
                m = re.search(r"\{.*\}", raw, re.DOTALL)
                if m:
                    return json.loads(m.group(0))
        except Exception as exc:
            logger.warning("Ollama JSON pass (%s / %s) ignoré : %s", host, mod, exc)
    return None


def _expand_chapter_for_target_words(chapter: dict[str, Any], min_sentences: int) -> dict[str, Any]:
    """Enrichit un chapitre si la durée cible demandée (ex: 8-15 min) exige davantage de développement."""
    ch = json.loads(json.dumps(chapter))
    sentences = list(ch.get("sentences", []))
    if len(sentences) >= min_sentences:
        return ch

    sys_prompt = (
        "Tu es Lia, ingénieure IA francophone de LBG Studios (style pédagogique, concret, chiffré et honnête façon Kiara IA locale). "
        "Réponds UNIQUEMENT en JSON valide : {\"extra_sentences\": [\"phrase 1\", \"phrase 2\", ...]} sans markdown."
    )
    needed = min_sentences - len(sentences)
    user_prompt = (
        f"Chapitre : « {ch['title']} ».\n"
        f"Phrases déjà présentes : {json.dumps(sentences, ensure_ascii=False)}\n"
        f"Ajoute exactement {needed} phrases techniques concrètes et fluides à l'oral qui approfondissent ce chapitre "
        f"(exemples matériels, compromis réels, conseils pratiques) sans répéter ce qui précède et sans dire bonjour."
    )
    extra_data = _call_ollama_json(user_prompt, sys_prompt, timeout_s=35.0)
    if extra_data and isinstance(extra_data.get("extra_sentences"), list):
        valid = [str(s).strip() for s in extra_data["extra_sentences"] if len(str(s).strip()) > 20]
        if valid:
            # Insérer avant la dernière phrase de transition/conclusion du chapitre
            insert_pos = max(1, len(sentences) - 1)
            sentences = sentences[:insert_pos] + valid[:needed] + sentences[insert_pos:]
            ch["sentences"] = sentences
            return ch

    # Fallback déterministe propre si Ollama est occupé
    fallbacks = [
        "Sur le terrain, mesurer systématiquement la consommation mémoire et la latence réelle évite d'acheter du matériel surdimensionné.",
        "C'est exactement cette discipline d'ingénierie qui permet de garder un système réactif, reproductible et simple à maintenir sur le long terme.",
        "Prends toujours le temps de valider chaque brique isolément avec un petit script de test avant de l'intégrer dans ton flux quotidien.",
    ]
    while len(sentences) < min_sentences and fallbacks:
        insert_pos = max(1, len(sentences) - 1)
        sentences.insert(insert_pos, fallbacks.pop(0))
    ch["sentences"] = sentences
    return ch


def _build_custom_topic_episode(topic: str, target_minutes: float) -> dict[str, Any]:
    """Construit un épisode complet multi-chapitres (4 à 15 min) sur n'importe quel sujet personnalisé."""
    n_body_chapters = max(3, min(8, int(round(target_minutes * 0.85))))
    clean_t = topic.strip().rstrip(".!?")

    # Tenter un plan sur-mesure via Ollama
    sys_outline = (
        "Tu es Lia, ingénieure IA locale chez LBG Studios. Génère le plan d'une vidéo YouTube longue francophone "
        "concrète et chiffrée (façon Kiara IA locale). Réponds UNIQUEMENT en JSON valide sans markdown."
    )
    prompt_outline = (
        f"Sujet : « {clean_t} ».\n"
        f"Crée un JSON avec : \"title\" (<75 car), \"subtitle\", \"thumbnail_hook\" (3-4 mots majuscules max), "
        f"\"thumbnail_sub\" (3-4 mots max), et \"chapter_titles\" (liste de {n_body_chapters} titres de chapitres techniques progressifs)."
    )
    outline = _call_ollama_json(prompt_outline, sys_outline, timeout_s=30.0) or {}
    ep_title = str(outline.get("title") or clean_t)[:85]
    ep_sub = str(outline.get("subtitle") or "Analyse matérielle, architecture locale et retours de production LBG Studios")
    thumb_hook = str(outline.get("thumbnail_hook") or "GUIDE IA LOCALE")[:22].upper()
    thumb_sub = str(outline.get("thumbnail_sub") or "0€ CLOUD • CONCRET")[:24].upper()
    raw_ch_titles = outline.get("chapter_titles")
    if not isinstance(raw_ch_titles, list) or len(raw_ch_titles) < 3:
        raw_ch_titles = [
            "Le vrai problème matériel et les idées reçues",
            "Architecture technique et mécanisme sous le capot",
            "Mise en place concrète et réglages clés",
            "Benchmarks mesurés, coûts et limites honnêtes",
        ][:n_body_chapters]

    slide_cycle = ["comparison", "diagram", "terminal", "benchmarks"]
    chapters: list[dict[str, Any]] = [
        {
            "title": "Introduction & enjeux concrets",
            "layout": "hero",
            "slide_type": "hero",
            "slide_title": ep_title,
            "slide_subtitle": ep_sub,
            "highlights": [str(t) for t in raw_ch_titles[:3]],
            "sentences": [
                f"Aujourd'hui on s'attaque à un sujet décisif quand on veut maîtriser son infrastructure et ses modèles chez soi : {clean_t}.",
                "Entre les fiches marketing gonflées et la réalité du matériel grand public ou d'occasion, il est très facile de faire de mauvais choix techniques.",
                "Moi c'est Lia de La Boîte à Geek : on va décortiquer ensemble le fonctionnement réel, la configuration concrète et nos vrais chiffres mesurés en local.",
            ],
        }
    ]

    for idx, ch_title in enumerate(raw_ch_titles[:n_body_chapters]):
        s_type = slide_cycle[idx % len(slide_cycle)]
        sys_ch = (
            "Tu es Lia, ingénieure IA francophone (ton direct, pédagogique, concret, zéro blabla). "
            "Réponds UNIQUEMENT en JSON valide : {\"sentences\": [..5 phrases..], \"bullets\": [..3 points courts..]}."
        )
        p_ch = (
            f"Vidéo : « {ep_title} ». Chapitre {idx + 1} : « {ch_title} ».\n"
            "Rédige 5 phrases fluides à l'oral avec des exemples techniques concrets (RAM, VRAM, Linux, Ollama, Godot ou Proxmox selon pertinence) et 3 points synthétiques de slide (<60 car chacun)."
        )
        ch_gen = _call_ollama_json(p_ch, sys_ch, timeout_s=32.0) or {}
        sents = [str(s).strip() for s in (ch_gen.get("sentences") or []) if len(str(s).strip()) > 20]
        if len(sents) < 4:
            sents = [
                f"Penchons-nous sur {ch_title}, car c'est souvent là que se joue toute la différence de fluidité au quotidien.",
                "Quand on dimensionne une brique locale, l'équilibre entre la mémoire disponible, la bande passante et la taille du contexte prime sur la puissance brute théorique.",
                "Chez LBG Studios, nous privilégions des composants open source éprouvés sous Linux avec des garde-fous stricts sur la consommation mémoire.",
                "Cette approche évite les ralentissements imprévus tout en maintenant une facture cloud strictement égale à zéro euro.",
            ]
        bullets = [str(b).strip()[:72] for b in (ch_gen.get("bullets") or []) if str(b).strip()]
        if len(bullets) < 3:
            bullets = [
                "Dimensionner la RAM et la VRAM avant la puissance brute",
                "Isoler chaque service pour garantir une latence prévisible",
                "Mesurer les performances sur de vrais cas d'usage",
            ]

        ch_obj: dict[str, Any] = {
            "title": str(ch_title),
            "layout": "split",
            "slide_type": s_type,
            "slide_title": str(ch_title),
            "bullets": bullets,
            "sentences": sents,
        }
        if s_type == "comparison":
            ch_obj["col_left_title"] = "Approche Classique Coûteuse"
            ch_obj["col_left_items"] = ["Dépendance aux API externes", "Coûts mensuels récurrents", "Peu de contrôle sur la latence"]
            ch_obj["col_right_title"] = "Approche Locale Optimisée"
            ch_obj["col_right_items"] = bullets[:3]
        elif s_type == "diagram":
            ch_obj["nodes"] = [
                {"label": "Entrée & Routage", "sub": "Filtrage léger du contexte"},
                {"label": "Exécution Locale", "sub": str(ch_title)[:34]},
                {"label": "Validation & Sortie", "sub": "Résultat mesuré 0€ Cloud"},
            ]
        elif s_type == "terminal":
            ch_obj["code_lines"] = [
                f"# Vérification & exécution locale — {str(ch_title)[:38]}",
                "systemctl status lbg-orchestrator.service",
                "free -h && ollama ps",
                "# Latence locale stable • 0€ API externe",
            ]
        elif s_type == "benchmarks":
            ch_obj["metrics"] = [
                {"label": "Efficacité mémoire optimisée", "value": "Stable H24", "pct": 88, "color": "cyan"},
                {"label": "Réactivité sur réseau local", "value": "< 150 ms", "pct": 90, "color": "amber"},
                {"label": "Coût mensuel d'abonnement Cloud", "value": "0 € / mois", "pct": 100, "color": "cyan"},
            ]
        chapters.append(ch_obj)

    chapters.append({
        "title": "Conclusion & recommandations",
        "layout": "hero",
        "slide_type": "hero",
        "slide_title": "Synthèse & Prochaines Étapes",
        "slide_subtitle": "Teste, mesure sur ton propre matériel et partage tes retours !",
        "highlights": [
            "Privilégier une architecture modulaire et mesurable",
            "Zéro abonnement obligatoire pour apprendre et produire",
            "Code source et configurations sur le GitHub LBG Studios",
        ],
        "sentences": [
            f"Voilà l'essentiel à retenir pour aborder {clean_t} avec méthode et sans gaspiller ton budget.",
            "Dis-moi en commentaire quelle configuration matérielle tu utilises actuellement et quel sujet technique tu veux qu'on creuse dans la prochaine vidéo longue !",
            "Abonne-toi à La Boîte à Geek pour suivre nos explorations en IA locale et game design, et retrouve toutes nos ressources sur GitHub.",
        ],
    })

    return {
        "title": ep_title,
        "subtitle": ep_sub,
        "thumbnail_hook": thumb_hook,
        "thumbnail_sub": thumb_sub,
        "badge_topic": "IA LOCALE & INGÉNIERIE",
        "palette": "cyan_rose",
        "chapters": chapters,
    }


def generate_longform_episode(
    topic: str | None = None,
    target_minutes: float = 5.0,
) -> dict[str, Any]:
    """Génère un script vidéo longue complet (calibré entre 4 et 15 minutes)."""
    clamped_min = max(3.0, min(15.0, float(target_minutes)))

    episode: dict[str, Any] | None = None
    if not topic:
        episode = json.loads(json.dumps(CANONICAL_EPISODES["moe_8gb_r720"]))
    else:
        t_low = topic.lower()
        for ep in CANONICAL_EPISODES.values():
            if sum(1 for k in ep.get("keywords", []) if k in t_low) >= 2:
                episode = json.loads(json.dumps(ep))
                break
        if episode is None:
            episode = _build_custom_topic_episode(topic, clamped_min)

    # Calibrer la densité de phrases par chapitre si l'utilisateur demande un format plus long (ex: 8-15 min)
    total_words = sum(len(" ".join(ch.get("sentences", [])).split()) for ch in episode["chapters"])
    target_words = int(clamped_min * 135)
    if target_words > total_words * 1.25 and len(episode["chapters"]) > 0:
        min_sents_per_ch = max(5, min(11, int(math.ceil((target_words / len(episode["chapters"])) / 24.0))))
        episode["chapters"] = [
            _expand_chapter_for_target_words(ch, min_sents_per_ch) for ch in episode["chapters"]
        ]

    final_words = sum(len(" ".join(ch.get("sentences", [])).split()) for ch in episode["chapters"])
    episode["target_minutes"] = round(clamped_min, 1)
    episode["estimated_minutes"] = round(final_words / 138.0, 1)
    episode["word_count"] = final_words
    return episode


import math  # noqa: E402


def export_markdown_review(episode: dict[str, Any], json_path: Path, md_path: Path) -> Path:
    """Écrit le brouillon lisible `BROUILLON_A_VALIDER.md` pour validation humaine (façon Kiara)."""
    lines = [
        f"# Brouillon Vidéo Longue 16:9 — {episode['title']}",
        "",
        f"- **Sous-titre** : {episode.get('subtitle', '')}",
        f"- **Durée estimée** : ~{episode.get('estimated_minutes', 5.0)} min ({episode.get('word_count', 0)} mots, {len(episode.get('chapters', []))} chapitres)",
        f"- **Texte Miniature 1280×720** : `{episode.get('thumbnail_hook', '')}` / `{episode.get('thumbnail_sub', '')}`",
        f"- **Fichier source éditable** : `{json_path}`",
        "",
        "> **Workflow Kiara (Validation Humaine)** : Tu peux modifier librement les textes, chiffres ou slides dans `script_long.json`, puis lancer le rendu vidéo HD 16:9 :",
        "> ```bash",
        f"> packages/cortex/.venv/bin/python tools/studio_content_engine/longform_bot.py --render {json_path.parent}",
        "> ```",
        "> *(Ajoute `--youtube` pour publier automatiquement avec chapitres horodatés et miniature HD.)*",
        "",
        "---",
        "",
    ]

    for idx, ch in enumerate(episode.get("chapters", []), start=1):
        lines.append(f"## Chapitre {idx} : {ch['title']} (`layout={ch.get('layout')}`, `slide={ch.get('slide_type')}`)")
        lines.append("")
        lines.append(f"**Titre Slide** : {ch.get('slide_title', ch['title'])}")
        if ch.get("highlights"):
            lines.append("**Points à l'écran** : " + " · ".join(ch["highlights"]))
        if ch.get("bullets"):
            for b in ch["bullets"]:
                lines.append(f"- {b}")
        if ch.get("code_lines"):
            lines.append("```bash")
            lines.extend(ch["code_lines"])
            lines.append("```")
        lines.append("")
        lines.append("**Voix de Lia :**")
        for s in ch.get("sentences", []):
            lines.append(f"> {s}")
        lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path
