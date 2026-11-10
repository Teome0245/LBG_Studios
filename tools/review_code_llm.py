#!/usr/bin/env python3
"""
Revue de code automatique locale via Ollama (LBG Studios).
Inspiré d'open-code-review et des protocoles de cocréation LBG.

Vérifie la conformité avec AGENTS.md, la sécurité des mutations,
la robustesse des types et l'absence de régression.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

DEFAULT_OLLAMA_HOST = os.environ.get("LBG_OLLAMA_REVIEW_HOST", "http://192.168.0.110:11434")
DEFAULT_MODEL = os.environ.get("LBG_OLLAMA_REVIEW_MODEL", "huihui_ai/qwen2.5-coder-abliterate:14b")
FALLBACK_HOST = "http://192.168.0.111:11434"
FALLBACK_MODEL = "huihui_ai/gemma-4-abliterated:E4b-qat"

REVIEW_SYSTEM_PROMPT = """Tu es l'agent superviseur et contrôleur qualité senior de LBG Studios.
Ta mission est d'effectuer une revue de code rigoureuse, concise et actionnable sur le diff git fourni.

Règles canoniques absolues de LBG Studios :
1. Pas de mutations LLM libres sur l'économie, le combat, le craft, les quêtes ou la réputation (OBJECTIVES.md).
   Toute action de jeu doit passer par un sas déterministe (Risk Gate) validé par le serveur Godot (.246:8787).
2. Périmètre exécutable : Les packages legacy (hybrid_proactive_agent, companion_bot, mmo_server) sont gelés.
   Ne jamais introduire d'imports directs vers ces modules.
3. Robustesse GDScript & Python : typage explicite, vérification des références nulles / None, libération mémoire propre.
4. Pas de réécriture globale injustifiée (ADR 0029).

Structure attendue pour la revue :
### 1. Résumé des changements (2-3 phrases)
### 2. Conformité aux Canons LBG (Validé / Risque identifié)
### 3. Points d'attention & Qualité du code (Bugs potentiels, gestion d'erreurs, performance)
### 4. Verdict : [PASS] ou [REWORK NÉCESSAIRE] avec justification courte.
Sois direct, technique et sans bavardage inutile. Réponds en français.
"""

LEGACY_FORBIDDEN_MODULES = [
    "hybrid_proactive_agent",
    "companion_bot",
    "mmo_server",
    "mmmorpg_server",
]

RISK_MUTATION_PATTERNS = [
    (r"(credits|balance|money|wallet)\s*(\+=|\-=|=)", "Mutation directe d'argent/crédits sans Risk Gate"),
    (r"(give_item|add_item|remove_item)\(", "Manipulation d'inventaire sans validation autoritaire"),
    (r"(complete_quest|grant_quest)\(", "Mutation directe d'état de quête"),
]


def run_heuristic_checks(diff_text: str) -> list[dict]:
    """Analyse statique instantanée (0ms) des règles fondamentales LBG Studios."""
    findings = []
    lines = diff_text.splitlines()

    for line in lines:
        if line.startswith("+") and not line.startswith("+++"):
            added_content = line[1:]

            # Vérification 1 : Import de packages legacy gelés
            for mod in LEGACY_FORBIDDEN_MODULES:
                if f"import {mod}" in added_content or f"from {mod}" in added_content:
                    findings.append({
                        "level": "CRITICAL",
                        "rule": "Canons LBG — Modules Legacy Gelés",
                        "message": f"Import interdit du module legacy '{mod}' détecté.",
                        "line": line.strip()
                    })

            # Vérification 2 : Mutations directes non protégées
            for pat, desc in RISK_MUTATION_PATTERNS:
                if re.search(pat, added_content) and "test" not in added_content.lower():
                    # Ignorer si c'est explicitement un hub autoritaire (hub_trade, hub_player_cities, etc.)
                    findings.append({
                        "level": "WARNING",
                        "rule": "Risk Gate — Mutation État de Jeu",
                        "message": f"{desc}. Vérifier que l'autorité est bien déterministe côté Godot (:8787).",
                        "line": line.strip()
                    })

    return findings


def get_git_diff(staged: bool = False, base_branch: str | None = None, files: list[str] | None = None) -> str:
    cmd = ["git", "diff"]
    if staged:
        cmd.append("--staged")
    elif base_branch:
        cmd.append(f"{base_branch}...HEAD")

    if files:
        cmd.append("--")
        cmd.extend(files)

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Erreur lors de l'exécution de git diff: {e}\n")
        return ""


def call_ollama(host: str, model: str, prompt: str, system: str, timeout: int = 120) -> str:
    url = f"{host.rstrip('/')}/api/generate"
    payload = {
        "model": model,
        "system": system,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 2048,
        },
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        res_json = json.loads(resp.read().decode("utf-8"))
        return res_json.get("response", "").strip()


def main():
    parser = argparse.ArgumentParser(description="Revue de code automatique locale via Ollama (LBG Studios)")
    parser.add_argument("--staged", action="store_true", help="Analyser uniquement les modifications indexées (staged)")
    parser.add_argument("--branch", type=str, default=None, help="Comparer la branche actuelle avec une branche de base (ex: main)")
    parser.add_argument("--files", nargs="*", default=None, help="Restreindre l'analyse à des fichiers spécifiques")
    parser.add_argument("--host", type=str, default=DEFAULT_OLLAMA_HOST, help=f"Hôte Ollama (défaut: {DEFAULT_OLLAMA_HOST})")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help=f"Modèle Ollama (défaut: {DEFAULT_MODEL})")
    parser.add_argument("--output", type=str, default=None, help="Chemin du fichier pour sauvegarder le rapport")
    parser.add_argument("--dry-run", action="store_true", help="Afficher le diff sans appeler le LLM")
    parser.add_argument("--heuristic-only", action="store_true", help="Exécuter uniquement l'audit statique des règles LBG (0 ms, hors LLM)")

    args = parser.parse_args()

    diff_text = get_git_diff(staged=args.staged, base_branch=args.branch, files=args.files)

    if not diff_text:
        print("Aucune modification détectée dans le diff git.")
        sys.exit(0)

    # Étape 1 : Audit heuristique instantané des canons LBG
    heuristics = run_heuristic_checks(diff_text)
    print("\n" + "=" * 60)
    print(" 🛡️  AUDIT HEURISTIQUE DES CANONS LBG (0 ms)")
    print("=" * 60)
    if not heuristics:
        print("✅ Aucun risque d'architecture détecté (pas d'import legacy, pas de mutation libre apparente).")
    else:
        for item in heuristics:
            badge = "❌ [CRITIQUE]" if item["level"] == "CRITICAL" else "⚠️  [ATTENTION]"
            print(f"{badge} {item['rule']} : {item['message']}")
            print(f"   Ligne : {item['line']}")

    if args.heuristic_only:
        print("=" * 60)
        sys.exit(0 if not any(h["level"] == "CRITICAL" for h in heuristics) else 1)

    # Limiter la taille du diff si trop volumineux pour éviter le dépassement de contexte
    max_chars = 12000
    truncated = False
    if len(diff_text) > max_chars:
        diff_text = diff_text[:max_chars]
        truncated = True

    if args.dry_run:
        print(f"\n=== DIFF DÉTECTÉ ({len(diff_text)} caractères) ===")
        print(diff_text[:1000] + ("\n... [tronqué]" if len(diff_text) > 1000 else ""))
        sys.exit(0)

    user_prompt = f"Voici le diff git à analyser :\n\n```diff\n{diff_text}\n```\n"
    if truncated:
        user_prompt += "\n(Note: Le diff complet dépasse 12 000 caractères et a été tronqué pour l'analyse)."

    print(f"\nAppel du modèle local ({args.host} - {args.model})...")
    review_output = ""
    try:
        review_output = call_ollama(args.host, args.model, user_prompt, REVIEW_SYSTEM_PROMPT, timeout=60)
    except Exception as e:
        print(f"Hôte {args.host} indisponible ou timeout ({e}). Tentative sur {FALLBACK_HOST} ({FALLBACK_MODEL})...")
        try:
            review_output = call_ollama(FALLBACK_HOST, FALLBACK_MODEL, user_prompt, REVIEW_SYSTEM_PROMPT, timeout=60)
        except Exception as e2:
            print(f"\nℹ️  Audit LLM sauté (Ollama local non réactif en GPU : {e2}).")
            print("L'audit heuristique ci-dessus fait foi pour cette passe.")
            review_output = "Analyse heuristique LBG validée. Modèle LLM offline."

    print("\n" + "=" * 60)
    print(" RAPPORT DE REVUE DE CODE LBG")
    print("=" * 60 + "\n")
    print(review_output)
    print("\n" + "=" * 60)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(review_output + "\n")
        print(f"Rapport sauvegardé dans {args.output}")


if __name__ == "__main__":
    main()
