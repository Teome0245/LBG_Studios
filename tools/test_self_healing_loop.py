#!/usr/bin/env python3
"""test_self_healing_loop.py — Démonstration de la boucle d'Auto-Évaluation & Auto-Correction de Gladys (0€ Cloud).

Étapes du test :
1. Injection d'une anomalie contrôlée dans un module cible.
2. Auto-évaluation (Diagnostic par test unitaire -> FAIL détecté).
3. Formulation du mandat de réparation par Gladys.
4. Résolution automatique via le modèle de code local (Ollama RTX .110 - qwen2.5-coder).
5. Application du patch et re-test automatique (Contre-expertise CI -> PASS).
6. Rapport d'audit complet.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("gladys_self_healing")

CURRENT_DIR = Path(__file__).resolve().parent
TARGET_FILE = CURRENT_DIR / "sandbox_sample.py"
TEST_FILE = CURRENT_DIR / "test_sandbox_sample.py"
OLLAMA_111 = os.environ.get("LBG_OLLAMA_111", "http://192.168.0.111:11434")
OLLAMA_110 = os.environ.get("LBG_OLLAMA_110", "http://192.168.0.110:11434")
CODER_MODEL = "qwen2.5:3b"


def setup_faulty_module() -> None:
    """Injecte un module avec un bug d'implémentation et son test unitaire strict."""
    # Module avec un bug évident : la formule de distance euclidienne a oublié la racine carrée
    faulty_code = '''"""sandbox_sample.py — Module cible avec anomalie logique injectée."""

def calculate_entity_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calcule la distance 2D entre deux entités du monde."""
    # BUG INJECTÉ : oubli de la racine carrée (renvoie la distance au carré)
    dx = x2 - x1
    dy = y2 - y1
    return (dx ** 2) + (dy ** 2)
'''
    with open(TARGET_FILE, "w", encoding="utf-8") as f:
        f.write(faulty_code)

    # Test unitaire de référence
    test_code = '''"""test_sandbox_sample.py — Test de validation."""
import math
import pytest
from sandbox_sample import calculate_entity_distance

def test_distance_calculation():
    # Distance entre (0, 0) et (3, 4) doit être exactement 5.0 (triangle 3-4-5)
    dist = calculate_entity_distance(0.0, 0.0, 3.0, 4.0)
    assert math.isclose(dist, 5.0, abs_tol=1e-5), f"Distance attendue: 5.0, obtenue: {dist}"

def test_distance_zero():
    dist = calculate_entity_distance(10.0, 20.0, 10.0, 20.0)
    assert math.isclose(dist, 0.0, abs_tol=1e-5)
'''
    with open(TEST_FILE, "w", encoding="utf-8") as f:
        f.write(test_code)


def run_evaluation() -> tuple[bool, str]:
    """Auto-évaluation : exécute le test et capture le verdict."""
    res = subprocess.run(
        [sys.executable, "-m", "pytest", str(TEST_FILE), "-v"],
        capture_output=True,
        text=True,
        cwd=str(CURRENT_DIR),
    )
    passed = (res.returncode == 0)
    output = res.stdout if res.stdout else res.stderr
    return passed, output


def ask_local_coder_fix(faulty_code: str, error_trace: str) -> str:
    """Demande la correction au modèle de code local sur la RTX .110."""
    prompt = f"""Tu es la Main Ouvrière de code de Gladys (LBG Studios).
Un test unitaire a échoué sur le fichier sandbox_sample.py.

CODE SOURCE ACTUEL :
```python
{faulty_code}
```

ERREUR DU TEST UNITAIRE :
```
{error_trace[:1500]}
```

CONSIGNE :
Corrige le code pour que le test unitaire réussisse parfaitement.
Réponds UNIQUEMENT avec le code Python complet et corrigé, encapsulé dans un bloc ```python ... ``` sans aucune explication bavarde autour.
"""
    logger.info("Envoi du mandat au modèle local sur %s (%s)...", OLLAMA_111, CODER_MODEL)
    with httpx.Client(timeout=60.0) as client:
        resp = client.post(
            f"{OLLAMA_111}/v1/chat/completions",
            json={
                "model": CODER_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 1000,
            },
        )
        if resp.status_code != 200:
            raise RuntimeError(f"Erreur Ollama HTTP {resp.status_code}: {resp.text}")

        content = resp.json()["choices"][0]["message"]["content"]

    # Extraction du bloc de code
    import re
    match = re.search(r"```python\s*(.*?)\s*```", content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return content.strip()


def run_self_healing_cycle() -> bool:
    print("\n" + "=" * 70)
    print("🤖 DÉMONSTRATION DU CYCLE D'AUTO-ÉVALUATION & AUTO-CORRECTION GLADYS")
    print("=" * 70)

    # 1. Préparation
    print("\n[Étape 1/5] Injection d'un bug dans le module 'sandbox_sample.py'...")
    setup_faulty_module()

    # 2. Auto-évaluation
    print("\n[Étape 2/5] Auto-évaluation initiale (Exécution des tests de santé)...")
    passed, error_output = run_evaluation()
    if passed:
        print("❌ Échec de la démonstration : le bug n'a pas été détecté.")
        return False

    print("🔍 DIAGNOSTIC GLADYS : Anomalie détectée en production !")
    for line in error_output.splitlines():
        if "FAILED" in line or "AssertionError" in line:
            print(f"   ⚠️  {line}")

    # 3. Formulation du mandat & Résolution
    print("\n[Étape 3/5] Gladys mandate la Main Ouvrière (Ollama RTX .110 : qwen2.5-coder)...")
    with open(TARGET_FILE, "r", encoding="utf-8") as f:
        faulty_code = f.read()

    start_time = time.time()
    try:
        fixed_code = ask_local_coder_fix(faulty_code, error_output)
    except Exception as e:
        logger.error("Échec de communication avec .110 : %s", e)
        return False
    duration = time.time() - start_time
    print(f"⚡ Correction générée en {duration:.2f} secondes (0 € Cloud) !")

    # 4. Application du patch
    print("\n[Étape 4/5] Application du patch autonome sur 'sandbox_sample.py'...")
    with open(TARGET_FILE, "w", encoding="utf-8") as f:
        f.write(fixed_code)

    # 5. Contre-expertise CI
    print("\n[Étape 5/5] Contre-expertise de sécurité (Re-test automatique)...")
    passed_after, final_output = run_evaluation()

    print("\n" + "=" * 70)
    if passed_after:
        print("✅ SUCCÈS TOTAL : La boucle d'auto-évaluation et d'auto-correction a fonctionné !")
        print("   - Diagnostic initial : FAIL (anomalie capturée)")
        print("   - Intervention locale : qwen2.5-coder (.110)")
        print("   - Vérification CI : PASS (100% vert)")
        print("   - Code corrigé :")
        for line in fixed_code.splitlines():
            print(f"     | {line}")
    else:
        print("❌ Échec de la validation après correction.")
        print(final_output)

    print("=" * 70)

    # Nettoyage
    if TARGET_FILE.exists():
        TARGET_FILE.unlink()
    if TEST_FILE.exists():
        TEST_FILE.unlink()

    return passed_after


if __name__ == "__main__":
    success = run_self_healing_cycle()
    sys.exit(0 if success else 1)
