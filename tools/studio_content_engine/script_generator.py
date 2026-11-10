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

SYSTEM_PROMPT = """Tu es un expert créateur de contenu tech pour des vidéos verticales courtes (TikTok, YouTube Shorts, Reels) chez LBG Studios.
Ton objectif est de vulgariser les architectures d'ingénierie avancées, le dev 100% local, les LLM locaux, Godot et l'automatisation.

Format strict requis :
1. Un Hook percutant de 3 secondes (phrase choc, question intrigante).
2. Le problème (pourquoi le cloud ou les solutions classiques coûtent trop cher ou sont bloquantes).
3. La solution technique (architecture concrète, outils open source, 0€ de frais).
4. Un Call to action court et dynamique.

Tu DOIS répondre UNIQUEMENT avec un objet JSON valide au format suivant (sans backticks markdown) :
{
  "title": "Titre court percutant",
  "category": "IA / Dev / Gaming",
  "hook": "Phrase d'accroche",
  "problem": "Explication du problème",
  "solution": "Explication de la solution",
  "cta": "Appel à l'action",
  "sentences": [
    "Phrase 1 du hook.",
    "Phrase 2 du problème.",
    "Phrase 3 de la solution.",
    "Phrase 4 du call to action."
  ]
}
"""

FALLBACK_SCRIPTS = [
    {
        "title": "Arrête de payer des API Cloud pour tes Agents IA",
        "category": "Architecture IA Locale",
        "hook": "Arrête immédiatement de payer des centaines d'euros en tokens d'API pour tes agents IA.",
        "problem": "Chaque appel Claude ou OpenAI grignote ta marge et crée une dépendance totale à des serveurs distants.",
        "solution": "Chez LBG Studios, on fait tourner un modèle 12 milliards de paramètres et un synthétiseur vocal Piper sur notre propre réseau local, pour zéro euro.",
        "cta": "Abonne-toi pour découvrir notre architecture et récupère le code sur notre GitHub.",
        "sentences": [
            "Arrête immédiatement de payer des centaines d'euros en tokens d'API pour tes agents IA.",
            "Chaque appel Claude ou OpenAI grignote ta marge et crée une dépendance totale à des serveurs distants.",
            "Chez LBG Studios, on fait tourner un modèle 12 milliards de paramètres et un synthétiseur vocal Piper sur notre propre réseau local, pour zéro euro.",
            "Abonne-toi pour découvrir notre architecture et récupère le code sur notre GitHub.",
        ],
    },
    {
        "title": "Comment faire tourner 10 Bots IA dans Godot 4",
        "category": "Godot 4 & Simulation",
        "hook": "Tu pensais que faire tourner des joueurs IA dans un monde 3D demandait un cluster de calcul ?",
        "problem": "Les serveurs multijoueurs traditionnels s'effondrent dès que l'IA calcule des navigations spatiales trop lourdes.",
        "solution": "Grâce au mode headless de Godot 4.6 et son NavigationServer 3D, on simule 10 bots autonomes à 60 FPS en consommant moins de 2 gigas de RAM.",
        "cta": "Mets cette vidéo en favori et dis-moi en commentaire quel type de PNJ tu veux voir simuler.",
        "sentences": [
            "Tu pensais que faire tourner des joueurs IA dans un monde 3D demandait un cluster de calcul ?",
            "Les serveurs multijoueurs traditionnels s'effondrent dès que l'IA calcule des navigations spatiales trop lourdes.",
            "Grâce au mode headless de Godot 4.6 et son NavigationServer 3D, on simule 10 bots autonomes à 60 FPS en consommant moins de 2 gigas de RAM.",
            "Mets cette vidéo en favori et dis-moi en commentaire quel type de PNJ tu veux voir simuler.",
        ],
    },
]


def generate_tech_script(topic: str | None = None, model: str = DEFAULT_MODEL) -> dict[str, Any]:
    """Génère un script structuré via Ollama local ou utilise le fallback canonique."""
    if not topic:
        # Sélection aléatoire ou par défaut dans les scripts canons
        return FALLBACK_SCRIPTS[0]

    prompt = f"Génère un script vidéo court TikTok/Shorts percutant en français sur le sujet : '{topic}'."

    hosts_and_models = [
        (OLLAMA_HOST_111, "qwen2.5:3b"),
        (OLLAMA_HOST_111, os.environ.get("LBG_MODEL_111", "huihui_ai/gemma-4-abliterated:E4b-qat")),
        (OLLAMA_HOST_110, model),
    ]
    for host, mod in hosts_and_models:
        try:
            logger.info("Tentative de génération script sur %s avec %s...", host, mod)
            with httpx.Client(timeout=20.0) as client:
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
                    cleaned = re.sub(r"^```json\s*", "", raw_text, flags=re.MULTILINE)
                    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()
                    data = json.loads(cleaned)
                    if "sentences" in data and len(data["sentences"]) >= 3:
                        logger.info("Script généré avec succès par %s (%s) !", host, mod)
                        return data
        except Exception as e:
            logger.warning("Échec génération sur %s (%s) : %s", host, mod, e)

    logger.info("Utilisation du script canonique fallback.")
    fb = dict(FALLBACK_SCRIPTS[0])
    fb["topic_requested"] = topic
    return fb


if __name__ == "__main__":
    script = generate_tech_script("Comment créer son propre Second Brain avec Obsidian et RAG")
    print(json.dumps(script, indent=2, ensure_ascii=False))
